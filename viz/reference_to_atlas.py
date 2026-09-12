"""Did the style reach the letters the user never saw?

The picker shows a user two glyphs. It hands back ninety-four. This figure is
the test in `analysis/reference_to_atlas_transfer.py` drawn out: each column is
one candidate reference above the atlas it produced.

THE ATLAS STRIP DELIBERATELY EXCLUDES K AND g. The model is conditioned to copy
those two, so showing them would prove only that the conditioning works. Every
letter below is one the user never chose and never saw.

A green frame means that atlas's OWN reference was its nearest match among the
four of its description; red means another candidate's reference was closer.

  python viz/reference_to_atlas.py
"""
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
ATLASES = os.path.join(REPO, "eval_runs", "_transfer_atlases")
RESULT = os.path.join(REPO, "research", "reference_to_atlas_transfer.json")

# Letters shown from each atlas. None is K or g -- see the module docstring.
SHOW = "amber"
N_DESCRIPTIONS = 2          # the two widest-spread, one block each


def strip(path, chars=SHOW):
    """Those letters from an atlas, side by side, cropped to their ink."""
    from atlas_constants import CELL_H, CELL_W, CHARSET, GRID_COLS

    arr = np.asarray(Image.open(path).convert("L"))
    cells = []
    for ch in chars:
        idx = CHARSET.index(ch)
        r, c = idx // GRID_COLS, idx % GRID_COLS
        cells.append(arr[r * CELL_H:(r + 1) * CELL_H, c * CELL_W:(c + 1) * CELL_W])
    row = np.concatenate(cells, axis=1)
    cols = np.where((row > 40).any(axis=0))[0]
    rows = np.where((row > 40).any(axis=1))[0]
    if len(cols) and len(rows):
        row = row[rows.min():rows.max() + 1, cols.min():cols.max() + 1]
    return row


def main():
    if not os.path.isfile(RESULT):
        print(f"missing {RESULT}; run the transfer test first", file=sys.stderr)
        return 2
    res = json.load(open(RESULT, encoding="utf-8"))
    by_desc = {}
    for r in res["rows"]:
        by_desc.setdefault(r["description"], []).append(r)
    order = [d for d in res["descriptions"] if d in by_desc][:N_DESCRIPTIONS]
    if not order:
        print("no scored descriptions", file=sys.stderr)
        return 2

    ncols = max(len(by_desc[d]) for d in order)
    nrows = 2 * len(order)
    fig = plt.figure(figsize=(2.6 * ncols + 1.0, 2.35 * nrows + 1.5),
                     facecolor="white")
    gs = fig.add_gridspec(nrows, ncols, wspace=0.07,
                          height_ratios=[1.25, 0.62] * len(order),
                          hspace=0.46, left=0.035, right=0.985,
                          top=0.795, bottom=0.035)

    for b, desc in enumerate(order):
        rows = sorted(by_desc[desc], key=lambda r: r["candidate"])
        for c, r in enumerate(rows):
            ok = r["ok"]
            edge = "#1a7f37" if ok else "#b3261e"

            ref = os.path.join(REFS, r["candidate"] + ".png")
            ax = fig.add_subplot(gs[2 * b, c])
            ax.set_xticks([])
            ax.set_yticks([])
            if os.path.isfile(ref):
                with Image.open(ref) as im:
                    ax.imshow(np.asarray(im.convert("L")), cmap="gray",
                              vmin=0, vmax=255, aspect="auto")
            for s in ax.spines.values():
                s.set_color(edge)
                s.set_linewidth(2.5)
            ax.set_title(f"seed {42 + c}" + ("" if ok else "   MISS"),
                         fontsize=10.5, pad=5,
                         color="#111111" if ok else "#b3261e")

            atlas = os.path.join(ATLASES, r["candidate"] + ".png")
            ax2 = fig.add_subplot(gs[2 * b + 1, c])
            ax2.set_xticks([])
            ax2.set_yticks([])
            if os.path.isfile(atlas):
                ax2.imshow(strip(atlas), cmap="gray", vmin=0, vmax=255,
                           aspect="auto")
            for s in ax2.spines.values():
                s.set_color(edge)
                s.set_linewidth(2.5)
            ax2.set_xlabel(f"own {r['own_distance']:.2f}   "
                           f"best {r['best_distance']:.2f}",
                           fontsize=9.5, labelpad=5,
                           color="#1a7f37" if ok else "#b3261e")

        # SubplotSpec.get_position(fig) reads the geometry WITHOUT creating an
        # axes. `fig.add_subplot(...).get_position()` does create one, and it
        # lands on top of the first column -- which silently blanked the seed-42
        # reference in the first render of this figure, and in candidate_options
        # before it. Twice is a pattern; hence the comment.
        pos = gs[2 * b, 0].get_position(fig)
        caption = desc.split("-", 1)[1].replace("_", " ").strip()
        fig.text(0.035, pos.y1 + 0.032, f"“{caption}”", fontsize=12.5,
                 ha="left", va="bottom", fontweight="bold", color="#111111")

    fig.text(0.035, 0.965, "Did the style reach the letters nobody chose?",
             fontsize=17, fontweight="bold", ha="left")
    fig.text(0.035, 0.932,
             "Each column: one candidate reference, above the atlas it produced.\n"
             "The strip shows a·m·b·e·r — never K or g, which the model is "
             "conditioned to copy.",
             fontsize=11, ha="left", va="top", color="#444444")
    fig.text(0.035, 0.872,
             f"Green = this atlas's nearest reference was its OWN. "
             f"Overall {res['hits']}/{res['n']}, p={res['p']:.4f}, "
             f"mean rank {res['mean_rank']:.2f} against 2.50 chance.",
             fontsize=11, ha="left", color="#444444")

    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, "reference_to_atlas.png")
    fig.savefig(dest, dpi=140, facecolor="white")
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
