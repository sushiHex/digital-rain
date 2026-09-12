"""Two generators, one description, four seeds each.

THE BAR THAT MATTERS IS A YES/NO. The klein-base generator cannot draw a
stencil: four seeds of "a stencil sans with deliberate breaks" produced four
solid faces, and re-rolling cannot rescue it because that description's spread
is second-narrowest of twelve. The question a second arm exists to answer is
not "which scores higher" but **does ANY candidate show a break?**

Everything else about an arm -- coherence, identity, spread -- is a number that
can be argued over. A break is visible or it is not.

  python viz/arm_comparison.py
  python viz/arm_comparison.py --prompt 07
"""
import argparse
import glob
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                        # noqa: E402
from PIL import Image                     # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from viz._common import OUT, REPO         # noqa: E402

ROOT = os.path.join(REPO, "eval_runs", "_candidate_refs")
ARMS = [("klein-base-n4", "FLUX.2-klein-base-4B", "~25 s"),
        ("zimage-n4", "Z-Image-Turbo", "~29 s")]
DEFAULT_PROMPT = "09"
CAPTIONS = {"09": "a stencil sans with deliberate breaks",
            "07": "an ultra-light hairline sans",
            "10": "an inline face with a white stripe"}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    args = ap.parse_args()

    rows = []
    for arm, label, speed in ARMS:
        paths = sorted(glob.glob(os.path.join(ROOT, arm, f"{args.prompt}-*.png")))
        if paths:
            rows.append((label, speed, paths))
    if not rows:
        print(f"no candidates for prompt {args.prompt}", file=sys.stderr)
        return 2

    ncols = max(len(p) for *_, p in rows)
    fig = plt.figure(figsize=(2.55 * ncols + 3.6, 2.75 * len(rows) + 1.55),
                     facecolor="white")
    gs = fig.add_gridspec(len(rows), ncols + 1,
                          width_ratios=[1.35] + [1.0] * ncols,
                          wspace=0.05, hspace=0.16,
                          left=0.012, right=0.988, top=0.80, bottom=0.02)

    for r, (label, speed, paths) in enumerate(rows):
        lab = fig.add_subplot(gs[r, 0])
        lab.axis("off")
        lab.text(0.96, 0.60, label, fontsize=13, ha="right", va="center",
                 fontweight="bold", color="#111111")
        lab.text(0.96, 0.42, f"{speed} per image", fontsize=11, ha="right",
                 va="center", color="#444444")
        for c in range(ncols):
            ax = fig.add_subplot(gs[r, c + 1])
            ax.set_xticks([])
            ax.set_yticks([])
            if c >= len(paths):
                ax.axis("off")
                continue
            with Image.open(paths[c]) as im:
                ax.imshow(np.asarray(im.convert("L")), cmap="gray",
                          vmin=0, vmax=255, aspect="auto")
            for s in ax.spines.values():
                s.set_color("#cccccc")
            if r == 0:
                ax.set_title(f"seed {42 + c}", fontsize=10.5, pad=5,
                             color="#444444")

    caption = CAPTIONS.get(args.prompt, args.prompt)
    fig.text(0.012, 0.955, f"Two generators, one description: “{caption}”",
             fontsize=17, fontweight="bold", ha="left")
    fig.text(0.012, 0.905,
             "The bar is a yes/no, not a score: does ANY candidate show what "
             "the words asked for?\nEight seeds, two independent models, one "
             "prompt.",
             fontsize=11.5, ha="left", va="top", color="#444444")

    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, f"arm_comparison_{args.prompt}.png")
    fig.savefig(dest, dpi=140, facecolor="white")
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
