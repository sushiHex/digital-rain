"""Mean ink coverage of a run's generated atlases against holdout ground truth.

WHY THIS EXISTS. Two training runs failed in a way that training loss and the
conditioning guard both missed: the model's global stroke weight shifted. Loss
was healthy -- in one case the lowest of any run. The tell is LPIPS blowing out
while IDENTITY stays ~0.99: letters still correct, drawn at the wrong weight.
CLAUDE.md instructs the reader to diagnose it by comparing mean ink fraction,
so that diagnosis should be a tool rather than a paragraph.

THE POLARITY TRAP, which is the whole reason this is a script. The atlases are
LIGHT glyphs on a DARK ground. Measuring "ink" as dark pixels -- the intuitive
reading, and the one a fresh reader writes first -- returns ~0.93 for every run
and every ground truth. It does not error, it does not look absurd on its own,
and the ratios between runs stay in the right direction, so the mistake survives
review. Ink here is the BRIGHT-pixel fraction. `--invert` measures the other
polarity on purpose, for atlases stored the other way up.

WHAT IT CORRECTED. The values recorded across README.md, CLAUDE.md,
docs/quality-roadmap-v3.md and research/2026-08-05-... were ground truth 0.0712
with 0.0527 (-27%) and 0.0820 (+15%). Measured here over all 50 atlases: ground
truth 0.0652, corpus-expansion@6016 0.0440 (-32.5%), rank64+oversampling 0.0780
(+19.7%). Same directions, same conclusions, different numbers.

  python analysis/measure_ink.py
  python analysis/measure_ink.py --runs glyph_4b_r64_distinct_5000 --json out.json
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import json
import os

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GT_DIR = os.path.join(REPO, "eval_holdout", "atlases")
RUNS_DIR = os.path.join(REPO, "eval_runs")

DEFAULT_RUNS = [
    "glyph_4b_r32_5000",           # the shipped baseline
    "glyph_4b_r64_distinct_5000",  # stacked levers -- over-inked
    "glyph_4b_v3_6016",            # corpus expansion -- collapsed to hairlines
]

THRESHOLD = 128


def ink_fraction(path, invert=False):
    """Fraction of pixels that are glyph rather than ground."""
    with Image.open(path) as im:
        a = np.asarray(im.convert("L"))
    return float((a < THRESHOLD).mean() if invert else (a > THRESHOLD).mean())


def stems(directory):
    return {os.path.splitext(os.path.basename(p))[0]
            for p in glob.glob(os.path.join(directory, "*.png"))}


def mean_ink(directory, names, invert=False):
    present = [n for n in names if os.path.isfile(os.path.join(directory, n + ".png"))]
    if not present:
        return None, 0
    vals = [ink_fraction(os.path.join(directory, n + ".png"), invert) for n in present]
    return float(np.mean(vals)), len(present)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs", nargs="*", default=DEFAULT_RUNS,
                    help="eval_runs/<name> directories to score")
    ap.add_argument("--invert", action="store_true",
                    help="measure DARK pixels as ink (for dark-on-light atlases)")
    ap.add_argument("--json", help="write results here")
    args = ap.parse_args()

    if not os.path.isdir(GT_DIR):
        print(f"missing ground truth: {GT_DIR}", file=_sys.stderr)
        return 2

    gt_names = sorted(stems(GT_DIR))
    gt, n_gt = mean_ink(GT_DIR, gt_names, args.invert)
    if gt is None:
        print(f"no atlases in {GT_DIR}", file=_sys.stderr)
        return 2

    polarity = "dark pixels" if args.invert else "bright pixels"
    print(f"ink = {polarity}, threshold {THRESHOLD}")
    print(f"ground truth  {gt:.4f}   (n={n_gt}, {GT_DIR})\n")

    out = {"ground_truth": round(gt, 4), "n_gt": n_gt,
           "polarity": polarity, "runs": {}}
    missing = []
    for run in args.runs:
        d = os.path.join(RUNS_DIR, run, "generated")
        if not os.path.isdir(d):
            missing.append(run)
            continue
        value, n = mean_ink(d, gt_names, args.invert)
        if value is None:
            missing.append(run)
            continue
        pct = (value / gt - 1) * 100
        flag = "  <-- stroke-weight shift" if abs(pct) >= 10 else ""
        print(f"  {run:<32} {value:.4f}  {pct:+6.1f}%  (n={n}){flag}")
        out["runs"][run] = {"ink": round(value, 4), "pct_vs_gt": round(pct, 1), "n": n}

    for run in missing:
        print(f"  {run:<32} (no generated atlases)")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1)
        print(f"\nwrote {args.json}")

    if not out["runs"]:
        print("\nno runs scored", file=_sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    _sys.exit(main() or 0)
