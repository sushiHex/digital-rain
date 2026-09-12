"""Generate candidate two-glyph references from a style DESCRIPTION, and score them.

THE BAKE-OFF. The product concept is that a user describes a style, a model draws
the two reference characters, and the user selects and iterates. Three rounds of
research converged on a shortlist and established that **no benchmark measuring
whether a model can invent a coherent typeface exists**
(`research/2026-08-22-...`, `2026-08-23-...`). So the comparison has to be run
here, with the instrument this project already built and validated:
`analysis/reference_gate.py`, which separates coherent from incoherent references
at r=0.678 and predicts the resulting atlas at rho=0.666.

THE METHOD RULE, from our own data. Generate BOTH glyphs in ONE call, never two.
`research/2026-08-21-two-styles-in-two-styles-out.md` showed the model transfers
whatever style it is given, so two independent generations have no mechanism
forcing agreement while one generation of an image containing both does.

BACKENDS. `flux2-klein-base` and `glm-image` are the two complete local models on
this disk; `--from-dir` ingests images produced anywhere else, which is how a
hosted model or a downloaded checkpoint joins the comparison without this file
growing a client for each.

VALIDATION IS NOT OPTIONAL. A generated image is not guaranteed to contain one
letter per half, and a malformed candidate scored by the gate would return a
confident number about nothing. Every candidate is checked for ink in both
halves and rejected with a reason if it fails. Rejections are REPORTED, not
silently dropped -- a method that produces 80% malformed output has told you
something important, and a bake-off that hid that would be measuring the wrong
thing.

  python analysis/generate_candidate_references.py --backend flux2-klein-base
  python analysis/generate_candidate_references.py --from-dir my_generated/ --name nano-banana
  python analysis/generate_candidate_references.py --score-only
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import json
import os
import subprocess
import time

import numpy as np
from PIL import Image

from atlas_constants import CANVAS

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_ROOT = os.path.join(REPO, "eval_runs", "_candidate_refs")
REAL_REFS = os.path.join(REPO, "eval_runs", "_synthetic_refs", "oracle")
NEED_MB = 12000

# The two characters the SHIPPED references carry. Not "Rg": the holdout renders
# Kg while the checkpoints' conditioning records Rg -- the documented train/eval
# mismatch. Candidates must match the control, or a difference in glyph identity
# would be confounded with a difference in style coherence.
REF_CHARS = "Kg"

# A spread of real typographic styles, in the vocabulary the research says these
# models actually respond to (letterform DESCRIPTIONS, not font names -- naming
# a font both fails and invites reproducing a protected design).
STYLE_PROMPTS = [
    "a heavy geometric sans serif, closed apertures, flat terminals",
    "a high-contrast didone with hairline serifs and vertical stress",
    "a chunky slab serif with blunt rectangular serifs",
    "a humanist sans with open apertures and a calligraphic axis",
    "a condensed grotesque, tight spacing, large x-height",
    "a rounded soft sans with fully rounded stroke ends",
    "a wide low-contrast monospace with prominent spurs",
    "an ultra-light hairline sans, uniform thin strokes",
    "a wedge-serif face with flared, trumpet-shaped terminals",
    "a stencil sans with deliberate breaks in the strokes",
    "an inline face with a white stripe inset within each stroke",
    "a heavy angular blackletter-influenced sans with sharp cut terminals",
]

PROMPT_TEMPLATE = (
    "The capital letter {a} on the left and the lowercase letter {b} on the "
    "right, side by side on a plain solid black background. Two isolated "
    "letterforms only, no other objects, no words. The letters are {style}. "
    "Both letters are drawn in exactly the same typeface, pure white on black, "
    "centred, sharp edges, flat lighting, no shadow, no perspective."
)


def free_vram_mb():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30)
        return int(out.stdout.strip().splitlines()[0])
    except Exception:
        return None


def normalise(img, size=CANVAS):
    """Bring a generated image into the reference format, or explain why not.

    Returns (image, None) on success, (None, reason) on rejection. The reference
    format is light glyphs on a dark ground, square, one glyph per half.
    """
    arr = np.asarray(img.convert("L"), dtype=np.float32)

    # Polarity: the reference format is LIGHT ink on a DARK ground. A model asked
    # for "white on black" may still return the inverse, and scoring an inverted
    # image would measure the background.
    border = np.concatenate([arr[:8].ravel(), arr[-8:].ravel(),
                             arr[:, :8].ravel(), arr[:, -8:].ravel()])
    if border.mean() > 127:
        arr = 255.0 - arr

    ink = arr > 128
    if ink.mean() < 0.002:
        return None, "almost no ink"
    if ink.mean() > 0.60:
        return None, f"ink fraction {ink.mean():.2f} -- not isolated letterforms"

    # One glyph per half. The gate splits into two columns and scores each
    # against its own character, so a candidate with both letters crowded into
    # one half is unscoreable however good it looks.
    h, w = ink.shape
    half = w // 2
    left, right = ink[:, :half].mean(), ink[:, half:].mean()
    if left < 0.001 or right < 0.001:
        return None, f"a half is empty (left {left:.4f}, right {right:.4f})"
    ratio = max(left, right) / max(1e-6, min(left, right))
    if ratio > 8.0:
        return None, f"halves wildly unbalanced ({ratio:.1f}x) -- likely one glyph"

    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="L")
    return out.resize((size, size), Image.LANCZOS), None


def backend_flux2_klein_base(items, steps):
    """FLUX.2-klein-base-4B, plain text-to-image, no LoRA. Apache-2.0, on disk.

    Each item carries its OWN seed, because the product shows a user several
    candidates for one description and lets them pick.
    """
    import torch
    from diffusers import Flux2KleinPipeline

    pipe = Flux2KleinPipeline.from_pretrained(
        "black-forest-labs/FLUX.2-klein-base-4B", torch_dtype=torch.bfloat16)
    pipe = pipe.to("cuda")
    for label, prompt, item_seed in items:
        t0 = time.time()
        img = pipe(prompt=prompt, height=1024, width=1024,
                   num_inference_steps=steps,
                   generator=torch.Generator("cpu").manual_seed(item_seed)).images[0]
        yield label, img, time.time() - t0


def backend_glm_image_int4(items, steps):
    """GLM-Image, Intel AutoRound INT4. MIT, and already on disk at 13 GB.

    TEXT-TO-IMAGE, not the edit path. `GlmImagePipeline.__call__` takes
    `image=None` by default, so the same prompt used for klein-base runs here
    unchanged -- which is what makes this a like-for-like arm rather than a
    different task scored against the same table.

    This also re-measures a stale number. `CLAUDE.md` records ~36 min/image for
    GLM, taken from a bf16 run that was PAGING; 34 GB does not fit a 3090 and
    13 GB does. A survey verdict is a measurement with a date.
    """
    import torch
    from diffusers import GlmImagePipeline

    pipe = GlmImagePipeline.from_pretrained(GLM_INT4, torch_dtype=torch.bfloat16)
    pipe = pipe.to("cuda")
    for label, prompt, item_seed in items:
        t0 = time.time()
        img = pipe(prompt=prompt, height=1024, width=1024,
                   num_inference_steps=steps,
                   generator=torch.Generator("cpu").manual_seed(item_seed)).images[0]
        yield label, img, time.time() - t0


def backend_glm_image_q8(items, steps):
    """GLM-Image bf16 weights, quantised to int8 with quanto at load.

    THE FALLBACK, AND WHY IT EXISTS. `Intel/GLM-Image-int4-AutoRound` is on disk
    at 13 GB and will NOT load: diffusers 0.38 has no `auto-round` quantizer, and
    installing the `auto_round` package does not register one -- the gap is on
    the diffusers side. So the only usable GLM path is the 34 GB bf16 checkout
    quantised at load, which is what `studies/probe_glm_image.py` already does.

    That is also the fair way to re-measure the stale ~36 min/image figure in
    `CLAUDE.md`, which came from a bf16 run that was PAGING.
    """
    import torch
    from diffusers import GlmImagePipeline
    from optimum.quanto import freeze, qint8, quantize

    pipe = GlmImagePipeline.from_pretrained(GLM_BF16, torch_dtype=torch.bfloat16)
    quantize(pipe.transformer, weights=qint8)
    freeze(pipe.transformer)
    pipe = pipe.to("cuda")
    for label, prompt, item_seed in items:
        t0 = time.time()
        img = pipe(prompt=prompt, height=1024, width=1024,
                   num_inference_steps=steps,
                   generator=torch.Generator("cpu").manual_seed(item_seed)).images[0]
        yield label, img, time.time() - t0


def backend_z_image_turbo(items, steps):
    """Z-Image-Turbo, 6B, Apache-2.0. The arm GLM could not be.

    `diffusers` 0.38 ships `ZImagePipeline` natively, so unlike the two GLM
    paths -- one with no quantizer, one that segfaults -- this needs no
    workaround. Turbo is distilled for ~8 steps; `--steps` still applies, but
    20 is wasted on it.
    """
    import torch
    from diffusers import ZImagePipeline

    pipe = ZImagePipeline.from_pretrained(Z_IMAGE, torch_dtype=torch.bfloat16)
    pipe = pipe.to("cuda")
    for label, prompt, item_seed in items:
        t0 = time.time()
        img = pipe(prompt=prompt, height=1024, width=1024,
                   num_inference_steps=steps,
                   generator=torch.Generator("cpu").manual_seed(item_seed)).images[0]
        yield label, img, time.time() - t0


GLM_INT4 = "Intel/GLM-Image-int4-AutoRound"
GLM_BF16 = "zai-org/GLM-Image"
Z_IMAGE = "Tongyi-MAI/Z-Image-Turbo"
BACKENDS = {"flux2-klein-base": backend_flux2_klein_base,
            "glm-image-int4": backend_glm_image_int4,
            "glm-image-q8": backend_glm_image_q8,
            "z-image-turbo": backend_z_image_turbo}


def build_prompts(n=1, seed=42):
    """(label, prompt, seed) per candidate. `n` candidates per style.

    AT n=1 THE LABEL IS UNCHANGED, deliberately. `_synthetic_probe/external/`,
    `attribute_transfer.py` and the twelve atlases all index by the `NN-`
    prefix, so appending a suffix unconditionally would silently break every
    cross-reference to the 2026-08-23 run.
    """
    out = []
    for i, style in enumerate(STYLE_PROMPTS):
        stem = f"{i:02d}-{style.split(',')[0].replace(' ', '_')[:28]}"
        prompt = PROMPT_TEMPLATE.format(a=REF_CHARS[0], b=REF_CHARS[1],
                                        style=style)
        for k in range(n):
            label = stem if n == 1 else f"{stem}__s{k}"
            out.append((label, prompt, seed + k))
    return out


def generate(backend, steps, seed, limit, n=1, out_name=None):
    free = free_vram_mb()
    if free is not None and free < NEED_MB:
        print(f"refusing to start: {free} MiB free, need {NEED_MB}. The 3090 is "
              "shared -- wait, do not evict.", file=_sys.stderr)
        return None
    items = build_prompts(n=n, seed=seed)
    if limit:
        # Limit STYLES, not images: cutting the flat list would give the first
        # style all n candidates and the rest none.
        keep = {lab.split("__")[0] for lab in
                sorted({i[0].split("__")[0] for i in items})[:limit]}
        items = [i for i in items if i[0].split("__")[0] in keep]
    name = out_name or backend
    raw = os.path.join(OUT_ROOT, name, "_raw")
    ok_dir = os.path.join(OUT_ROOT, name)
    os.makedirs(raw, exist_ok=True)

    kept, rejected, times = [], [], []
    for label, img, secs in BACKENDS[backend](items, steps):
        img.save(os.path.join(raw, label + ".png"))
        norm, reason = normalise(img)
        times.append(secs)
        if norm is None:
            rejected.append((label, reason))
            print(f"  {label:<34} {secs:5.1f}s  REJECTED: {reason}", flush=True)
            continue
        norm.save(os.path.join(ok_dir, label + ".png"))
        kept.append(label)
        print(f"  {label:<34} {secs:5.1f}s  ok", flush=True)

    print(f"\n{name}: {len(kept)} usable of {len(kept)+len(rejected)}, "
          f"mean {np.mean(times):.1f}s per image")
    return {"backend": backend, "out_name": name, "n_per_style": n,
            "kept": kept, "rejected": rejected,
            "mean_seconds": float(np.mean(times)) if times else None}


def ingest(from_dir, name):
    """Normalise images produced elsewhere -- a hosted model, or another rig."""
    ok_dir = os.path.join(OUT_ROOT, name)
    os.makedirs(ok_dir, exist_ok=True)
    kept, rejected = [], []
    for p in sorted(glob.glob(os.path.join(from_dir, "*.png"))
                    + glob.glob(os.path.join(from_dir, "*.jpg"))):
        label = os.path.splitext(os.path.basename(p))[0]
        with Image.open(p) as im:
            norm, reason = normalise(im)
        if norm is None:
            rejected.append((label, reason))
            print(f"  {label:<34} REJECTED: {reason}")
            continue
        norm.save(os.path.join(ok_dir, label + ".png"))
        kept.append(label)
    print(f"\n{name}: {len(kept)} usable of {len(kept)+len(rejected)}")
    return {"backend": name, "kept": kept, "rejected": rejected,
            "mean_seconds": None}


def read_as(paths, chars=REF_CHARS):
    """Do the two glyphs actually READ as those characters?

    The gate measures whether the pair AGREES on a style. It cannot tell a K
    from a blob, and two matching blobs would score beautifully -- so coherence
    alone is not evidence of a usable reference. `glyph_classifier.py` is the
    font-invariant instrument for the other half, and it needs no ground truth.
    """
    from analysis.reference_gate import glyph_cells
    from glyph_classifier import classify, load_classifier
    from identity_score import reads_as

    model, idx_to_char = load_classifier(
        os.path.join(REPO, "glyph_classifier.pt"), device="cuda")
    hits = total = 0
    for p in paths:
        cells = [c for c in glyph_cells(p, len(chars)) if c is not None]
        if len(cells) != len(chars):
            continue
        preds = classify(model, idx_to_char, cells)
        hits += sum(bool(reads_as(pr, w, True)) for pr, w in zip(preds, chars))
        total += len(chars)
    return (hits / total) if total else None


def score_all():
    """Every method's candidates, plus the 50 real references as the control."""
    from analysis.reference_gate import reference_consistency
    from analysis.style_coherence import load_stats

    stats = load_stats()
    rows, identity = {}, {}

    real = sorted(glob.glob(os.path.join(REAL_REFS, "*.png")))
    if real:
        vals = [reference_consistency(p, stats, REF_CHARS) for p in real]
        rows["REAL (control)"] = [v["distance"] for v in vals if v]
        identity["REAL (control)"] = read_as(real)

    for d in sorted(glob.glob(os.path.join(OUT_ROOT, "*"))):
        if not os.path.isdir(d) or os.path.basename(d).startswith("_"):
            continue
        name = os.path.basename(d)
        vals = []
        for p in sorted(glob.glob(os.path.join(d, "*.png"))):
            rc = reference_consistency(p, stats, REF_CHARS)
            if rc:
                vals.append(rc["distance"])
        if vals:
            rows[name] = vals
            identity[name] = read_as(sorted(glob.glob(os.path.join(d, "*.png"))))

    if not rows:
        print("nothing to score", file=_sys.stderr)
        return None

    from analysis.reference_gate import REF_TARGET_H  # noqa: F401  (import guard)
    print("\nreference-consistency distance, lower is more coherent\n")
    print(f"  {'method':<22} {'n':>4} {'mean':>8} {'median':>8} {'worst':>8} "
          f"{'reads as Kg':>12}")
    control = rows.get("REAL (control)")
    for name, vals in sorted(rows.items(), key=lambda kv: np.mean(kv[1])):
        v = np.array(vals)
        idn = identity.get(name)
        print(f"  {name:<22} {len(v):>4} {v.mean():>8.3f} "
              f"{np.median(v):>8.3f} {v.max():>8.3f} "
              f"{(f'{idn:.0%}' if idn is not None else '--'):>12}")
    print("\n  Coherence alone is not evidence: the gate cannot tell a K from a")
    print("  blob, and two matching blobs would score well. 'reads as Kg' is the")
    print("  other half, from the font-invariant classifier.")
    if control:
        thr = float(np.percentile(control, 99))
        print(f"\n  gate threshold {thr:.3f} (99th percentile of real references)")
        for name, vals in sorted(rows.items(), key=lambda kv: np.mean(kv[1])):
            if name == "REAL (control)":
                continue
            passed = float(np.mean([v <= thr for v in vals]))
            print(f"    {name:<22} {passed:>5.0%} would pass the gate")
    return ({k: [float(x) for x in v] for k, v in rows.items()}, identity)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--backend", choices=sorted(BACKENDS))
    ap.add_argument("--from-dir", help="ingest images generated elsewhere")
    ap.add_argument("--name", help="method name for --from-dir")
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n", type=int, default=1,
                    help="candidates per style, seeds seed..seed+n-1. The "
                         "product shows several and lets the user pick. At n=1 "
                         "labels are unchanged, so existing runs still match.")
    ap.add_argument("--out-name", help="output subdirectory (default: backend)")
    ap.add_argument("--limit", type=int, help="first N STYLES, not N images")
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--json", default=os.path.join(REPO, "research",
                                                   "candidate_references.json"))
    args = ap.parse_args()

    runs = []
    if args.backend:
        r = generate(args.backend, args.steps, args.seed, args.limit,
                     n=args.n, out_name=args.out_name)
        if r is None:
            return 2
        runs.append(r)
    if args.from_dir:
        if not args.name:
            ap.error("--from-dir needs --name")
        runs.append(ingest(args.from_dir, args.name))
    if not (args.backend or args.from_dir or args.score_only):
        ap.error("pass --backend, --from-dir, or --score-only")

    scored, ident = score_all()
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"ref_chars": REF_CHARS, "prompt_template": PROMPT_TEMPLATE,
                   "styles": STYLE_PROMPTS, "runs": runs,
                   "distances": scored, "reads_as_kg": ident}, fh, indent=1)
    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
