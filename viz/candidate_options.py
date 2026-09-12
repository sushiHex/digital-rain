"""Four candidates for one description — what the user would actually pick from.

THE MEASUREMENT THIS DRAWS. `analysis/within_prompt_diversity.py` scores the
whole set at ratio 0.518 (within 1.302 / between 2.514, permutation p=0.0005):
candidates for one description sit about half as far apart as candidates for
different descriptions. That is the healthy shape -- the words control the style
and the seeds still vary.

WHAT THE AVERAGE HIDES, AND WHY THIS FIGURE EXISTS. Spread runs from 0.454 to
3.960 across the twelve descriptions, an 8.7x range, and it is LOWEST exactly
where the generator is known to fail. `a stencil sans with deliberate breaks`
was recorded as a MISS on 2026-08-23 and has the second-narrowest spread of any
description: the model produces the same solid face every time.

So RE-ROLLING CANNOT RESCUE A PROMPT THE MODEL SYSTEMATICALLY MISSES. The rows
here are ordered by spread so that reads off the page.

Rows are chosen to span the range, not cherry-picked for looks; the spread
figure under each is that description's own mean pairwise style distance.

  python viz/candidate_options.py
"""
import glob
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                        # noqa: E402
from PIL import Image                     # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from viz._common import OUT, REPO         # noqa: E402

REFS = os.path.join(REPO, "eval_runs", "_candidate_refs", "klein-base-n4")
STATS = os.path.join(REPO, "research", "within_prompt_diversity.json")

# (prefix, caption, what the 2026-08-23 note recorded). Chosen to span the
# spread range measured above -- the narrowest, the known miss, a middling one,
# and the widest.
ROWS = [
    ("07", "an ultra-light hairline sans", "reinterpreted as an outline"),
    ("09", "a stencil sans with deliberate breaks", "MISS - came back solid"),
    ("04", "a condensed grotesque", "hit"),
    ("10", "an inline face with a white stripe", "hit"),
]


def main():
    if not os.path.isdir(REFS):
        print(f"no candidates at {REFS}", file=sys.stderr)
        return 2
    spread = {}
    if os.path.isfile(STATS):
        d = json.load(open(STATS, encoding="utf-8"))
        spread = {k.split("-")[0]: v["mean"] for k, v in d["per_style"].items()}

    rows = []
    for prefix, caption, recorded in ROWS:
        paths = sorted(glob.glob(os.path.join(REFS, f"{prefix}-*.png")))
        if paths:
            rows.append((prefix, caption, recorded, paths))
    if not rows:
        print("no matching candidates", file=sys.stderr)
        return 2

    ncols = max(len(p) for *_, p in rows)
    # A dedicated LABEL COLUMN rather than fig.text at guessed coordinates. The
    # first attempt positioned captions by hand and left a dead axes sitting on
    # top of the seed-42 image, which silently hid a quarter of the evidence.
    fig = plt.figure(figsize=(2.35 * ncols + 4.2, 2.5 * len(rows) + 1.3),
                     facecolor="white")
    gs = fig.add_gridspec(len(rows), ncols + 1,
                          width_ratios=[1.5] + [1.0] * ncols,
                          wspace=0.06, hspace=0.30,
                          left=0.012, right=0.988, top=0.845, bottom=0.02)

    for r, (prefix, caption, recorded, paths) in enumerate(rows):
        miss = recorded.startswith("MISS")

        lab = fig.add_subplot(gs[r, 0])
        lab.axis("off")
        s = spread.get(prefix)
        lab.text(0.97, 0.62, f"“{caption}”", fontsize=12.5,
                 ha="right", va="center", fontweight="bold", color="#111111",
                 wrap=True)
        if s is not None:
            lab.text(0.97, 0.44, f"spread {s:.3f}", fontsize=11.5,
                     ha="right", va="center", color="#333333")
        lab.text(0.97, 0.28, recorded, fontsize=11, ha="right", va="center",
                 color="#b3261e" if miss else "#1a7f37")

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
            for sp in ax.spines.values():
                sp.set_color("#b3261e" if miss else "#cccccc")
                sp.set_linewidth(2.5 if miss else 1.0)
            if r == 0:
                ax.set_title(f"seed {42 + c}", fontsize=10.5, pad=5,
                             color="#444444")

    fig.text(0.012, 0.962, "Four candidates for one description",
             fontsize=17, fontweight="bold", ha="left")
    fig.text(0.012, 0.922,
             "Overall the picker works: within-description spread is 0.518 of "
             "between-description spread (p=0.0005).",
             fontsize=11, ha="left", color="#444444")
    fig.text(0.012, 0.884,
             "But spread runs 0.454–3.960 across the twelve, and it is NARROWEST "
             "where the generator is known to fail.\n"
             "Re-rolling cannot rescue a prompt the model systematically misses.",
             fontsize=11, ha="left", va="top", color="#444444")

    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, "candidate_options.png")
    fig.savefig(dest, dpi=140, facecolor="white")
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
