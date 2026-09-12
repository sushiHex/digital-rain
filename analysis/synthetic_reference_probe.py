"""Does the generator survive a reference that did not come from one real font?

THE PRODUCT QUESTION. Every reference this project has evaluated was rendered
from the target font's own TTF. The product concept is different: the user
describes a style, a generative model draws the two reference characters, the
user selects and iterates. There is then no target font -- which is exactly why
the retrieval baseline stops being a near-solution, since "hand back the nearest
TRAINING font" answers a question nobody asked.

That only matters if the generator still works. This probe answers the narrow,
decisive part: **given a reference whose two glyphs do NOT agree on a style,
does the model still emit 94 identity-correct, mutually coherent letterforms?**

WHY IT NEEDS NO GROUND TRUTH, AND WHY THAT IS THE POINT. char_acc, DINOv2,
LPIPS, R-ACC and composite all compare against a GT atlas rendered from the
target font. In the product there is no target font, so none of them can score
it. Two things survive, and both are used here:

  identity   glyph_classifier.py -- a font-invariant 94-class CNN trained with
             holdout families excluded. It asks "is this cell the right letter"
             without knowing what font it should have been.
  coherence  the spread of ink fraction across the 94 cells of ONE atlas.

             READ IT ONLY AS A PAIRED, BETWEEN-ARM DIFFERENCE. The absolute
             value is ~0.43 and is dominated by which LETTERS these are -- `.`
             and `M` legitimately differ enormously -- not by style coherence.
             That letter component is identical across arms, because every arm
             draws the same 94 characters, so the oracle-vs-arm delta is
             interpretable while the raw number is not.

ARMS (see analysis/build_synthetic_references.py):
  oracle     the shipped reference, verbatim. Control.
  mixed      K and g from DIFFERENT superfamilies -- the failure mode a
             text-to-image model actually has.
  perturbed  same face, right glyph slanted and weight-shifted. Subtler.
  external   real generated references, if any were supplied.

READ THE RESULT HONESTLY. A large identity drop on `mixed` means the concept
needs the human select-and-iterate loop to be doing real work. A small drop
means the model tolerates disagreeing references, and the benchmark problem
becomes tractable. Either answer is worth having; neither is assumed.

  python analysis/synthetic_reference_probe.py --limit 12
  python analysis/synthetic_reference_probe.py --score-only
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

from atlas_constants import BLANK_INDICES, CHARSET

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(REPO, "eval_runs", "_synthetic_refs")
OUT = os.path.join(REPO, "eval_runs", "_synthetic_probe")
CLASSIFIER = os.path.join(REPO, "glyph_classifier.pt")

# The ADAPTER directory, not the run directory: PeftModel.from_pretrained wants
# the folder holding adapter_config.json, and the run root only holds
# checkpoint-* subfolders. conditioning_config resolves from either.
CHECKPOINT = os.path.join("training_glyph_4b_r32_5000", "checkpoint-5000")
MODEL_4B = "black-forest-labs/FLUX.2-klein-base-4B"
ARMS = ("oracle", "mixed", "perturbed", "external")

NEED_MB = 12000          # match the runners' VRAM gate
DRAWN = [i for i in range(len(CHARSET)) if i not in BLANK_INDICES]


def free_vram_mb():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30)
        return int(out.stdout.strip().splitlines()[0])
    except Exception:
        return None


def generate(limit, steps, seed, arms=ARMS):
    """Generate every arm's atlases with ONE loaded pipeline."""
    from conditioning_config import expected_conditioning
    from generation_lib import generate_one_atlas, load_generation_pipe

    free = free_vram_mb()
    if free is not None and free < NEED_MB:
        print(f"refusing to start: {free} MiB free, need {NEED_MB}. "
              "The 3090 is shared -- wait, do not evict.", file=_sys.stderr)
        return None

    # Derive conditioning FROM THE CHECKPOINT. Hardcoding it is how
    # candidate_gen.py mis-conditioned every candidate it ever produced.
    cond = expected_conditioning(CHECKPOINT)
    print(f"conditioning: prompt_style={cond['prompt_style']} "
          f"ref_chars={cond['reference_chars']} use_template={cond['use_template']}")

    pipe, prompt_embeds, neg_embeds = load_generation_pipe(
        CHECKPOINT,
        use_template=cond["use_template"],
        template_pt=cond["template_pt"],
        model=MODEL_4B,
        reference_chars=cond["reference_chars"],
        prompt_style=cond["prompt_style"],
    )

    made = {}
    for arm in arms:
        arm_dir = os.path.join(REFS, arm)
        refs = sorted(glob.glob(os.path.join(arm_dir, "*.png")))
        if limit:
            refs = refs[:limit]
        if not refs:
            continue
        os.makedirs(os.path.join(OUT, arm), exist_ok=True)
        made[arm] = []
        for i, ref in enumerate(refs, 1):
            name = os.path.splitext(os.path.basename(ref))[0]
            dst = os.path.join(OUT, arm, name + ".png")
            if os.path.isfile(dst):
                made[arm].append(name)
                continue
            t0 = time.time()
            # Same seed for every arm and font: the arms must differ by the
            # REFERENCE only. A per-font seed would fold the style lottery
            # (SD 0.0248 on the seed main effect alone) into the comparison.
            generate_one_atlas(pipe, prompt_embeds, neg_embeds, ref, dst,
                               steps=steps, seed=seed)
            made[arm].append(name)
            print(f"  {arm:<10} [{i}/{len(refs)}] {name[:34]:<36} "
                  f"{time.time()-t0:5.1f}s", flush=True)
    return made


def score():
    """Identity and coherence, both without any ground truth."""
    from eval_checkpoint import crop_cell
    from glyph_classifier import classify_conf, load_classifier
    from identity_score import reads_as

    if not os.path.isfile(CLASSIFIER):
        print(f"missing classifier at {CLASSIFIER}", file=_sys.stderr)
        return None
    model, idx_to_char = load_classifier(CLASSIFIER, device="cuda")

    per_font = {}
    for arm in ARMS:
        paths = sorted(glob.glob(os.path.join(OUT, arm, "*.png")))
        if not paths:
            continue
        per_font[arm] = {}
        for p in paths:
            name = os.path.splitext(os.path.basename(p))[0]
            with Image.open(p) as im:
                atlas = np.asarray(im.convert("RGB"))
            cells = [crop_cell(atlas, i) for i in DRAWN]
            preds = classify_conf(model, idx_to_char, cells)

            exact = lenient = 0
            for idx, (ch, _conf) in zip(DRAWN, preds):
                want = CHARSET[idx]
                exact += (ch == want)
                lenient += bool(reads_as(ch, want, True))
            conf = float(np.mean([c for _, c in preds]))

            # Coherence: ink is the BRIGHT fraction -- these atlases are light
            # glyphs on a dark ground (analysis/measure_ink.py documents why
            # the intuitive reading returns ~0.93 and looks plausible).
            inks = np.array([(c[:, :, 0] > 128).mean() for c in cells])
            per_font[arm][name] = {
                "identity_exact": exact / len(DRAWN),
                "identity_lenient": lenient / len(DRAWN),
                "mean_confidence": conf,
                "ink_mean": float(inks.mean()),
                "ink_cv": float(inks.std() / inks.mean()) if inks.mean() else None,
            }
    return per_font


def report(per_font):
    from analysis.compare_runs import paired_wilcoxon

    print("\nGT-free scores. identity = font-invariant classifier; "
          "ink CV = within-atlas coherence (lower is better)\n")
    print(f"  {'arm':<11} {'identity':>9} {'lenient':>9} {'conf':>7} "
          f"{'ink CV':>8} {'n':>4}")
    keys = ("identity_exact", "identity_lenient", "mean_confidence", "ink_cv")
    for arm in ARMS:
        rows = per_font.get(arm)
        if not rows:
            continue
        m = {k: float(np.mean([r[k] for r in rows.values() if r[k] is not None]))
             for k in keys}
        print(f"  {arm:<11} {m['identity_exact']:>9.4f} "
              f"{m['identity_lenient']:>9.4f} {m['mean_confidence']:>7.3f} "
              f"{m['ink_cv']:>8.4f} {len(rows):>4}")

    base = per_font.get("oracle") or {}
    if not base:
        return []
    print("\npaired Wilcoxon against the oracle arm, by font "
          "(gate p<0.05 AND r>=0.3)")
    print(f"  {'arm':<11} {'metric':<18} {'p':>9} {'r':>7}  verdict")
    out = []
    for arm in ARMS:
        if arm == "oracle" or not per_font.get(arm):
            continue
        shared = sorted(set(base) & set(per_font[arm]))
        if len(shared) < 5:
            continue
        for metric in ("identity_exact", "identity_lenient", "ink_cv"):
            a = [base[f][metric] for f in shared]
            b = [per_font[arm][f][metric] for f in shared]
            if any(v is None for v in a + b):
                continue
            res = paired_wilcoxon(a, b)
            sig = res.p < 0.05 and res.effect_r >= 0.3
            worse = (np.mean(b) < np.mean(a)) if metric != "ink_cv" \
                else (np.mean(b) > np.mean(a))
            verdict = ("SIG - " + ("WORSE than oracle" if worse else
                                   "better than oracle")) if sig else "no difference"
            print(f"  {arm:<11} {metric:<18} {res.p:>9.4f} "
                  f"{res.effect_r:>7.3f}  {verdict}")
            out.append({"arm": arm, "metric": metric, "p": res.p,
                        "effect_r": res.effect_r, "n": len(shared),
                        "significant": sig, "worse_than_oracle": bool(worse)})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--arms", nargs="*", default=list(ARMS),
                    help="generate only these arms (scoring still reads all)")
    ap.add_argument("--json", default=os.path.join(REPO, "research",
                                                   "synthetic_reference_probe.json"))
    args = ap.parse_args()

    if not args.score_only:
        if generate(args.limit, args.steps, args.seed, args.arms) is None:
            return 2

    per_font = score()
    if not per_font:
        print("nothing scored", file=_sys.stderr)
        return 3
    comparisons = report(per_font)

    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"checkpoint": CHECKPOINT, "model": MODEL_4B,
                   "steps": args.steps, "seed": args.seed,
                   "comparisons": comparisons, "per_font": per_font}, fh, indent=1)
    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
