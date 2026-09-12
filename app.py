"""Gradio demo for the glyph-conditioned font model.

Runs the same path the eval harness validates: generation_lib builds the
FLUX.2-klein + LoRA pipeline and generates one atlas, then atlas_to_font
vectorizes the fixed 12x8 grid into an OTF/WOFF2.

Defaults to the **Apache-2.0 klein-base-4B** adapter, deliberately. The 9B base
carries the FLUX Non-Commercial Licence, which makes a hosted demo a licensing
problem; the 4B does not. That licence difference is the reason, and it is not
traded against a quality number.

On quality, read the README rather than a figure quoted here. In short: the 9B
leads on the two style metrics; the other four were only ever compared at a
single seed; and NO comparison of two training runs in this repo is
established, because run-to-run variance is large enough to swallow every
effect measured (research/2026-08-13-training-run-variance-measured-at-last.md).
rank 64 costs +1% training time and no extra memory.

The base model must match the adapter. --model is derived from the checkpoint's
train_config.json when it records one, so the two cannot silently diverge.

The checkpoint is not in this repository (training_*/ is gitignored). Point at
one with --checkpoint or the FONTGEN_CHECKPOINT environment variable:

    python app.py                                    # 4B rank-64, Apache-2.0
    python app.py --checkpoint training_glyph_r32_5000/final \
                  --model black-forest-labs/FLUX.2-klein-base-9B
"""
import argparse
import json
import os
import tempfile
import time

import gradio as gr

from atlas_constants import CELL_H, CELL_W, CHARSET

DEFAULT_CHECKPOINT = os.environ.get(
    "FONTGEN_CHECKPOINT", "training_glyph_4b_r64_5000/final"
)
DEFAULT_MODEL = os.environ.get(
    "FONTGEN_MODEL", "black-forest-labs/FLUX.2-klein-base-4B"
)
DEFAULT_TEMPLATE = os.environ.get(
    "FONTGEN_TEMPLATE", "dataset_v2/cache/template.pt"
)

# Populated by main(); read by the click handler.
_config = {"checkpoint": DEFAULT_CHECKPOINT, "template": DEFAULT_TEMPLATE,
           "model": DEFAULT_MODEL}
_pipe = None


def train_config(checkpoint):
    """The checkpoint's train_config.json as a dict, or {}.

    One reader, so base model and rank cannot come from different files. Search
    order matches conditioning_config._search_dirs: the checkpoint dir, then its
    parent (where train_lora_kg.py actually writes it), then the grandparent.
    """
    ckpt = str(checkpoint).rstrip("/\\")
    parent = os.path.dirname(ckpt)
    for d in (ckpt, parent, os.path.dirname(parent)):
        cfg = os.path.join(d, "train_config.json")
        if os.path.isfile(cfg):
            try:
                return json.load(open(cfg, encoding="utf-8"))
            except Exception:
                return {}
    return {}


def resolve_base_model(checkpoint, explicit=None):
    """Base model for a checkpoint: explicit flag, else its own train_config.

    Deriving the base rather than assuming it is the same principle as
    prompt_style in get_pipeline(). NOTE: the 4B and 9B adapters are NOT
    interchangeable-but-silent -- their hidden dims differ (3072 vs 4096), so
    crossing them raises a shape error. An earlier version of this docstring
    claimed it loaded silently and produced garbage; that was asserted without
    testing and is false. The guard still earns its place: it turns a confusing
    shape traceback into the right base, and it protects against
    DIMENSION-COMPATIBLE mismatches -- a different revision, or a distilled
    variant of the same size -- which would be silent.
    """
    return explicit or train_config(checkpoint).get("model") or DEFAULT_MODEL


def get_pipeline():
    """Load the pipeline once, deriving its conditioning from the checkpoint.

    prompt_style and use_template are read from the checkpoint rather than
    hardcoded: evaluating a checkpoint with the prompt it was not trained on
    silently costs real accuracy (research/2026-07-28-reference-char-mismatch.md),
    and the same mismatch would apply here.
    """
    global _pipe
    if _pipe is None:
        from conditioning_config import expected_conditioning
        from generation_lib import load_generation_pipe

        checkpoint = _config["checkpoint"]
        if not os.path.isdir(checkpoint):
            raise FileNotFoundError(
                f"checkpoint not found: {checkpoint}\n"
                "Pass --checkpoint <dir> or set FONTGEN_CHECKPOINT. Trained "
                "weights are not committed to this repository."
            )
        exp = expected_conditioning(checkpoint) or {}
        prompt_style = exp.get("prompt_style") or "trained-short"
        use_template = exp.get("use_template", True)
        if use_template and not os.path.isfile(_config["template"]):
            raise FileNotFoundError(
                f"glyph template not found: {_config['template']}\n"
                "Pass --template-pt <file> or set FONTGEN_TEMPLATE."
            )
        model = _config["model"]
        print(f"[app] checkpoint={checkpoint}  base={model}  "
              f"prompt_style={prompt_style}  use_template={use_template}")
        _pipe = load_generation_pipe(
            checkpoint,
            use_template=use_template,
            template_pt=_config["template"],
            prompt_style=prompt_style,
            model=model,
        )
    return _pipe


# Reference-consistency gate. The model transfers whatever style it is given, so
# two reference glyphs that disagree produce an atlas split along the K-like /
# g-like seam -- a light `H` then bold `amburg`. Identity scores that ABOVE a
# coherent control, so nothing downstream catches it, and the user waits a minute
# for an unusable font. Reading the reference costs milliseconds.
# See research/2026-08-21-the-reference-gate.md.
#
# Measured operating points, cut from the coherent references' own spread:
#
#   percentile  threshold  catches mixed  rejects coherent
#           99      1.875            44%                2%
#           95      1.626            48%                6%
#           90      1.328            54%               10%
#
# The 99th is the default BECAUSE THIS GATE BLOCKS. Going 99 -> 95 buys four
# points of recall for three times the false-positive rate, and a false positive
# here refuses a legitimate user. Recall is also a floor, not a ceiling: the
# label it was measured against includes benign pairings that should pass.
#
# The threshold is PROVISIONAL -- calibrated on the coherent spread, not on
# references a human judged unacceptable. That set does not exist yet.
REFERENCE_GATE_THRESHOLD = 1.875

_GATE_ADVICE = {
    "stroke": "the two glyphs differ in weight -- one is much bolder",
    "slant": "one glyph is slanted and the other upright",
    "fill": "one glyph is far more solid than the other",
    "parts": "one glyph is dotted or inline where the other is solid",
}


def check_reference(ref_path):
    """Score the supplied reference for mutual style agreement.

    Returns (score, message) or (None, None) when the reference cannot be
    scored -- an unexpected layout, or a blank column. Failing OPEN is
    deliberate: this is a convenience guard on a provisional threshold, and it
    must never be the reason a working reference is refused.
    """
    try:
        from analysis.reference_gate import reference_consistency
        from analysis.style_coherence import load_stats
        from conditioning_config import expected_conditioning

        chars = ((expected_conditioning(_config["checkpoint"]) or {})
                 .get("reference_chars") or "Rg")
        rc = reference_consistency(ref_path, load_stats(), chars=chars)
        if not rc:
            return None, None
        worst = max(rc["per_feature"], key=rc["per_feature"].get)
        return rc["distance"], _GATE_ADVICE.get(worst, worst)
    except Exception:
        return None, None          # never block generation on the guard failing


# --- the picker -----------------------------------------------------------
#
# Everything measured on 2026-08-25 describes a flow this app did not have: the
# user types a description, several candidate references are drawn, and they
# pick one. The architecture is measured end to end -- candidates differ (ratio
# 0.518, p=0.0005), two glyphs carry the adherence signal (9/11), and the atlas
# tracks the pick (11/16) -- so the gap was the interface, not the evidence.
#
# The one honest caveat is built in rather than bolted on. Spread runs
# 0.454-3.960 across descriptions, and on EIGHT OF TWELVE no candidate pair
# reaches the distance at which the gate calls two glyphs different styles. On
# those, offering four options is a false promise: re-rolling cannot rescue a
# prompt the model systematically misses.
# `research/2026-08-25-eight-of-twelve-offer-no-real-choice.md`

NARROW_ADVICE = (
    "**These options are much alike.** This model draws this style close to the "
    "same way every seed, so re-rolling is unlikely to give you something "
    "different — try rewording the description instead."
)


def candidate_set_advice(scores, threshold=REFERENCE_GATE_THRESHOLD):
    """(verdict, message) for a set of candidate style vectors.

    `scores` is the list of pairwise style distances between candidates. The cut
    is taken from the gate's own threshold rather than invented: a pair further
    apart than `threshold` is one the gate would call different styles, so a set
    where NO pair reaches it is offering variations the project's own validated
    instrument would call one typeface.
    """
    if not scores:
        return "unknown", ""
    if max(scores) > threshold:
        return "choice", ""
    return "narrow", NARROW_ADVICE


def candidate_spread(paths):
    """Pairwise style distances between candidate references, or [] if unscoreable.

    Fails OPEN like `check_reference`: an advisory must never be the reason a
    usable candidate set is withheld.
    """
    try:
        import itertools

        import numpy as np

        from analysis.style_coherence import load_stats
        from analysis.within_prompt_diversity import style_vector

        stats = load_stats()
        vecs = [v for v in (style_vector(p, stats) for p in paths)
                if v is not None]
        if len(vecs) < 2:
            return []
        return [float(np.linalg.norm(a - b))
                for a, b in itertools.combinations(vecs, 2)]
    except Exception:
        return []


def generate_font(ref_image, font_name, steps, seed, gate_reference=True):
    """Reference image -> atlas -> vectorized OTF/WOFF2."""
    if ref_image is None:
        return "Upload a reference image first.", None, None, None
    font_name = font_name.strip() or "GeneratedFont"

    try:
        from PIL import Image

        from atlas_to_font import build_font, trace_atlas_cells
        from generation_lib import generate_one_atlas

        tmp = tempfile.gettempdir()
        ref_path = os.path.join(tmp, f"{font_name}_ref.png")
        Image.fromarray(ref_image).convert("RGB").save(ref_path)

        # Score the reference BEFORE spending a generation on it -- and before
        # get_pipeline(), which on a cold start loads and quantizes the
        # transformer for several minutes. Gating after that load would save
        # the user nothing, which is what this did on the first attempt.
        score, advice = check_reference(ref_path)
        if score is not None and gate_reference and score > REFERENCE_GATE_THRESHOLD:
            return (
                f"Reference rejected: its two glyphs disagree on style "
                f"({score:.2f} against a {REFERENCE_GATE_THRESHOLD:.2f} "
                f"threshold).\n\nThe model copies whatever style it is given, so "
                f"a reference like this produces a font that changes style "
                f"part-way through a word.\n\nWhat differs: {advice}.\n\n"
                f"Supply two glyphs in the same style, or untick "
                f"“Check reference consistency” to generate anyway.",
                None, None, None,
            )
        gate_note = (f"  Reference consistency {score:.2f}"
                     f" (threshold {REFERENCE_GATE_THRESHOLD:.2f})."
                     if score is not None else "")

        pipe, prompt_embeds, neg_embeds = get_pipeline()

        atlas_path = os.path.join(tmp, f"{font_name}_atlas.png")
        t0 = time.time()
        generate_one_atlas(
            pipe, prompt_embeds, neg_embeds, ref_path, atlas_path,
            steps=int(steps), seed=int(seed),
        )
        gen_time = time.time() - t0

        t1 = time.time()
        atlas = Image.open(atlas_path)
        cells = trace_atlas_cells(atlas)
        # side_bearing defaults to SIDE_BEARING_EM * upm, i.e. exactly the 50
        # this used to pass explicitly. Left implicit so the constant lives in
        # one place. The per-character prior is deliberately NOT enabled here --
        # it measures no better in this pipeline; see build_font's docstring.
        font = build_font(
            cells, CHARSET, CELL_W, CELL_H,
            upm=1000, font_name=font_name,
        )
        trace_time = time.time() - t1

        otf_path = os.path.join(tmp, f"{font_name}.otf")
        font.save(otf_path)
        font.flavor = "woff2"
        woff2_path = os.path.join(tmp, f"{font_name}.woff2")
        font.save(woff2_path)

        drawn = sum(1 for c in cells if c)
        msg = (
            f"{drawn} glyphs in {gen_time:.0f}s (atlas) + {trace_time:.1f}s "
            f"(vectorize). OTF {os.path.getsize(otf_path):,} B, "
            f"WOFF2 {os.path.getsize(woff2_path):,} B." + gate_note
        )
        return msg, atlas_path, otf_path, woff2_path

    except Exception as e:
        import traceback
        return f"Error: {e}\n{traceback.format_exc()}", None, None, None


def _pipeline_blurb():
    """Describe what is actually loaded, rather than a hardcoded 9B/rank-32.

    The demo defaults to the Apache-2.0 4B; saying "9B" regardless would be
    wrong on the default path and misleading about the licence.
    """
    model = _config.get("model") or DEFAULT_MODEL
    short = model.rsplit("/", 1)[-1]
    licence = ("Apache-2.0" if "4B" in short
               else "FLUX Non-Commercial Licence" if "9B" in short else "")
    r = train_config(_config.get("checkpoint", "")).get("rank")
    rank = f"rank-{r} LoRA" if r else "LoRA"
    return (f"**Pipeline:** {short} (qfloat8) + {rank} with glyph-latent channel "
            f"conditioning → Potrace → OTF/WOFF2"
            + (f"  ·  base model licence: {licence}" if licence else ""))


def _header():
    return (
        "# Glyph-Conditioned Font Generator\n"
        "Upload a reference image in the style you want. The model generates a "
        f"{len(CHARSET)}-character atlas, which is vectorized to OTF/WOFF2.\n\n"
        + _pipeline_blurb()
    )


def construct_references(description, paths, out_dir, seed=0):
    """[(treatment, path)] for treatments the generator will not draw.

    No text-to-image model invents a stencil -- sixteen images across three
    mechanisms produced no break. The LoRA does PROPAGATE one it is handed
    (`research/2026-08-28-hand-it-a-stencil-and-it-propagates-one.md`), so for
    those treatments the answer is geometry rather than a better generator.

    The treatment is applied to the most coherent DRAWN candidate, not to a
    neutral font: the generator supplies the style it is good at and geometry
    supplies the treatment it refuses, so "a heavy blackletter stencil" keeps
    its blackletter.

    Fails OPEN, like every other advisory here -- a construction that cannot be
    built must never be the reason the drawn candidates are withheld.
    """
    try:
        from analysis.constructed_reference import build

        out = []
        for name, img in build(description, paths, seed=seed):
            dst = os.path.join(out_dir, f"constructed_{name}.png")
            img.save(dst)
            out.append((name, dst))
        return out
    except Exception:
        return []


def describe_candidates(description, n, seed, progress=gr.Progress()):
    """Description -> n candidate references, with a spread advisory.

    Returns (gallery, status, paths) so the click handler can hold the paths
    for the picker without re-deriving them from the gallery.
    """
    description = (description or "").strip()
    if not description:
        return [], "Describe a style first.", []
    try:
        from analysis.generate_candidate_references import (PROMPT_TEMPLATE,
                                                            REF_CHARS,
                                                            BACKENDS, normalise)
    except Exception as exc:                           # noqa: BLE001
        return [], f"Candidate generation unavailable: {exc}", []

    prompt = PROMPT_TEMPLATE.format(a=REF_CHARS[0], b=REF_CHARS[1],
                                    style=description)
    items = [(f"cand{i}", prompt, int(seed) + i) for i in range(int(n))]
    out_dir = os.path.join(tempfile.gettempdir(), "fontgen_candidates")
    os.makedirs(out_dir, exist_ok=True)

    paths, rejected = [], []
    try:
        for label, img, _secs in BACKENDS["flux2-klein-base"](items, 20):
            norm, reason = normalise(img)
            if norm is None:
                rejected.append(reason)
                continue
            dst = os.path.join(out_dir, f"{label}.png")
            norm.save(dst)
            paths.append(dst)
            progress((len(paths) + len(rejected)) / len(items))
    except Exception as exc:                           # noqa: BLE001
        return [], f"Candidate generation failed: {exc}", []

    if not paths:
        return [], f"No usable candidates ({'; '.join(rejected)}).", []

    # The advisory is computed on the DRAWN candidates only. A constructed
    # reference is not a seed variant, so folding it in would inflate the
    # spread and hide exactly the narrowness the advisory exists to report.
    verdict, advice = candidate_set_advice(candidate_spread(paths))
    msg = f"{len(paths)} candidate(s). Pick one, then Generate Font."
    if rejected:
        msg += f"  {len(rejected)} rejected: {'; '.join(rejected)}."

    built = construct_references(description, paths, out_dir, int(seed))
    if built:
        names = ", ".join(n for n, _ in built)
        paths = paths + [p for _, p in built]
        msg += (f"\n\n**{len(built)} constructed** ({names}), shown last. "
                "No image model will draw these treatments — sixteen attempts "
                "across three mechanisms produced none — so they are built "
                "geometrically onto the most coherent drawn candidate, which "
                "keeps the style you asked for. The model propagates them to "
                "the other 92 glyphs.")
    elif advice:
        msg += "\n\n" + advice
    return paths, msg, paths


def pick_candidate(paths, evt: gr.SelectData):
    """The chosen candidate becomes the reference image."""
    import numpy as np
    from PIL import Image

    if not paths or evt.index is None or evt.index >= len(paths):
        return None
    return np.array(Image.open(paths[evt.index]).convert("RGB"))


with gr.Blocks(title="Glyph-Conditioned Font Generator") as demo:
    header_md = gr.Markdown(_header())

    with gr.Accordion("Start from a description", open=False):
        gr.Markdown(
            "Draw several candidate references from words, pick one, then "
            "generate. On many descriptions the candidates come out much "
            "alike — the app says so rather than implying a choice it cannot "
            "offer."
        )
        with gr.Row():
            desc_input = gr.Textbox(
                label="Describe a style", scale=3,
                placeholder="a chunky slab serif with blunt rectangular serifs")
            n_input = gr.Slider(2, 6, value=4, step=1, label="Candidates")
            desc_seed = gr.Number(label="Seed", value=42, precision=0)
        describe_btn = gr.Button("Draw candidates", variant="secondary")
        candidate_gallery = gr.Gallery(label="Candidates — click one to use it",
                                       columns=4, height=220)
        candidate_status = gr.Textbox(label="Candidates", interactive=False)
        candidate_paths = gr.State([])

    with gr.Row():
        with gr.Column(scale=1):
            ref_input = gr.Image(label="Style Reference", type="numpy")
            with gr.Row():
                name_input = gr.Textbox(label="Font Name", value="MyFont", scale=2)
                steps_input = gr.Slider(10, 35, value=20, step=1, label="Steps")
                seed_input = gr.Number(label="Seed", value=42, precision=0)
            gate_input = gr.Checkbox(
                label="Check reference consistency",
                value=True,
                info="Refuse a reference whose two glyphs disagree on style, "
                     "rather than spending a minute producing a font that "
                     "changes style part-way through a word.",
            )
            generate_btn = gr.Button("Generate Font", variant="primary", size="lg")

        with gr.Column(scale=1):
            status = gr.Textbox(label="Status", interactive=False)
            atlas_preview = gr.Image(label="Generated Atlas")
            with gr.Row():
                otf_download = gr.File(label="Download OTF")
                woff2_download = gr.File(label="Download WOFF2")

    describe_btn.click(
        fn=describe_candidates,
        inputs=[desc_input, n_input, desc_seed],
        outputs=[candidate_gallery, candidate_status, candidate_paths],
    )
    candidate_gallery.select(
        fn=pick_candidate, inputs=[candidate_paths], outputs=[ref_input],
    )

    generate_btn.click(
        fn=generate_font,
        inputs=[ref_input, name_input, steps_input, seed_input, gate_input],
        outputs=[status, atlas_preview, otf_download, woff2_download],
    )

    notes_md = gr.Markdown(
        "### Notes\n"
        "- The first generation loads and quantizes the transformer — expect a "
        "few minutes before the first atlas appears. Later runs reuse it.\n"
        "- Reference images are resized to 512x512; high-contrast letterforms "
        "work best.\n"
        "- Output is glyph outlines only — no kerning, spacing, or hinting. See "
        "the README's Limitations section.\n"
        "- The consistency check reads the two reference glyphs and refuses a "
        "pair that disagrees on style, because the model copies what it is "
        "given and would split the font part-way through a word. Its threshold "
        "is **provisional** — calibrated on the spread of coherent references, "
        "not on references a person judged unacceptable — so it fails OPEN: "
        "anything it cannot score is generated normally."
    )


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT)
    ap.add_argument("--model", default=None,
                    help="Base model. Defaults to the checkpoint's own "
                         "train_config.json, else the Apache-2.0 klein-base-4B. "
                         "Crossing 4B/9B raises a shape error (3072 vs 4096 "
                         "hidden dim); a same-size mismatch would be silent.")
    ap.add_argument("--template-pt", default=DEFAULT_TEMPLATE)
    ap.add_argument("--share", action="store_true", help="public Gradio link")
    args = ap.parse_args()
    _config["checkpoint"] = args.checkpoint
    _config["template"] = args.template_pt
    _config["model"] = resolve_base_model(args.checkpoint, args.model)
    # Re-render now that the real config is known; the module-level value was
    # built against the defaults at import time.
    header_md.value = _header()
    demo.launch(share=args.share)


if __name__ == "__main__":
    main()
