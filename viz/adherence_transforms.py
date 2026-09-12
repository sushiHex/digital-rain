"""What the adherence measure actually sees: a break, a stripe and a ring.

TWO PANELS, AND THE SECOND IS THE EVIDENCE.

TOP -- the synthetic training data. One real face, transformed four ways. Every
class comes from the SAME source, so the typeface is held constant and only the
treatment differs. That is what makes the negatives HARD: a stencil classifier
whose negatives are Roboto and Lato learns "many pieces", and `parts` alone
cannot tell a break from a stripe from a hollow contour.

BOTTOM -- the real held-out typefaces, which the model never saw, with what it
said about each. Those are the 11 superfamilies the primary was scored on.

The numbers under each class are the features that separate them. The stencil
signature is the counter-intuitive one and was not predicted: erasing bands cuts
the counters OPEN, so a stencil face has FEWER holes than a solid one.

  python viz/adherence_transforms.py
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                        # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.attribute_separation import atlas_path                # noqa: E402
from analysis.synthesize_rare_attributes import (CLASSES, apply_transform,  # noqa: E402
                                                 atlas_cells, draw_params,
                                                 load, vector_from_cells)
from viz._common import OUT, REPO                                   # noqa: E402

SOURCE = "Roboto-Regular"
FALLBACK = "ABeeZee-Regular"
SHOW = "Kgab"                       # glyphs drawn per row
POOL = os.path.join(REPO, "font_pool")

# (stem, true class, what the 94-cell model predicted). From
# research/synthesize_rare_attributes.json -- quoted, not recomputed here.
REAL = [
    ("AllertaStencil-Regular", "stencil", "stencil"),
    ("BigShouldersStencilDisplaySC[wght]", "stencil", "stencil"),
    ("SirinStencil-Regular", "stencil", "stencil"),
    ("BigShouldersInlineDisplaySC[wght]", "inline", "inline"),
    ("BungeeInline-Regular", "inline", "inline"),
    ("FascinateInline-Regular", "inline", "stencil"),
]

FEATURE_NAMES = ("stroke", "slant", "fill", "parts",
                 "width_cv", "aspect", "holes", "hole_area")


def _short(stem, limit=17):
    """Family names like BigShouldersStencilDisplaySC collide with their
    neighbours at this width."""
    name = stem.split("[")[0].split("-")[0]
    return name if len(name) <= limit else name[:limit - 1] + "…"


def char_idx(chars):
    from atlas_constants import CHARSET
    return [CHARSET.index(c) for c in chars]


def strip(arr, indices):
    """The chosen glyph cells of an atlas, side by side, cropped to ink."""
    cells = atlas_cells(arr, indices)
    row = np.concatenate(cells, axis=1)
    cols = np.where((row > 40).any(axis=0))[0]
    rows = np.where((row > 40).any(axis=1))[0]
    if len(cols) and len(rows):
        row = row[rows.min():rows.max() + 1, cols.min():cols.max() + 1]
    return row


def main():
    idx = char_idx(SHOW)
    src = atlas_path(POOL, SOURCE) or atlas_path(POOL, FALLBACK)
    if src is None:
        print(f"no source atlas for {SOURCE} or {FALLBACK}", file=sys.stderr)
        return 2
    arr = load(src)
    params = draw_params(np.random.default_rng(0))

    real = [(stem, t, p, atlas_path(POOL, stem)) for stem, t, p in REAL]
    real = [r for r in real if r[3] is not None]

    fig = plt.figure(figsize=(13, 4.9), facecolor="white")
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.0], hspace=0.95,
                          left=0.045, right=0.988, top=0.74, bottom=0.13)

    # --- TOP: one face, four treatments -----------------------------------
    top = gs[0].subgridspec(1, len(CLASSES), wspace=0.10)
    for i, cls in enumerate(CLASSES):
        ax = fig.add_subplot(top[0, i])
        variant = apply_transform(arr, cls, params)
        ax.imshow(strip(variant, idx), cmap="gray", vmin=0, vmax=255,
                  interpolation="nearest", aspect="auto")
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color("#bbbbbb")
        v = vector_from_cells(atlas_cells(variant, idx), min_cells=1)
        f = dict(zip(FEATURE_NAMES, v))
        ax.set_title(cls.upper(), fontsize=12, fontweight="bold", pad=6,
                     color="#111111" if cls == "solid" else "#8a1c1c")
        ax.set_xlabel(f"parts {f['parts']:.2f}   holes {f['holes']:.2f}\n"
                      f"hole area {f['hole_area']:.3f}",
                      fontsize=9, color="#333333", labelpad=6)

    # --- BOTTOM: real held-out faces, with the verdict ---------------------
    bot = gs[1].subgridspec(1, len(real), wspace=0.10)
    for i, (stem, true, pred, path) in enumerate(real):
        ax = fig.add_subplot(bot[0, i])
        ax.imshow(strip(load(path), idx), cmap="gray", vmin=0, vmax=255,
                  interpolation="nearest", aspect="auto")
        ax.set_xticks([])
        ax.set_yticks([])
        ok = pred == true
        for s in ax.spines.values():
            s.set_color("#1a7f37" if ok else "#b3261e")
            s.set_linewidth(2.0)
        ax.set_title(_short(stem), fontsize=9.5, pad=5,
                     color="#111111")
        ax.set_xlabel(f"true {true}\nsaid {pred}" + ("" if ok else "   MISS"),
                      fontsize=9, labelpad=6,
                      color="#1a7f37" if ok else "#b3261e")

    fig.text(0.045, 0.955,
             "What the adherence measure sees",
             fontsize=17, fontweight="bold", ha="left")
    fig.text(0.045, 0.905,
             "TOP: one real face, transformed four ways — every class from the SAME "
             "source, so only the treatment differs, which is what makes the "
             "negatives hard.",
             fontsize=10.5, ha="left", color="#444444")
    fig.text(0.045, 0.855,
             "BOTTOM: real held-out typefaces the model never saw, with what it said.",
             fontsize=10.5, ha="left", color="#444444")
    fig.text(0.988, 0.855, "94-cell primary:  10/11,  p=0.0059",
             fontsize=11, ha="right", color="#1a7f37", fontweight="bold")

    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, "adherence_transforms.png")
    fig.savefig(dest, dpi=150, facecolor="white")
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
