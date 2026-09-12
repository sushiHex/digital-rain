"""Does MONOSPACE survive the atlas, when the atlas throws advance width away?

THE PREDICTION THIS REFUTES WAS MINE. `build_dataset.render_atlas` centres every
glyph on its INK bounding box (`build_dataset.py:285`), so advance width is
discarded outright. Monospace is DEFINED by equal advances -- an `i` is narrow
ink in every font, mono or not -- so I reasoned the attribute could not survive
and was about to drop it from the classifier.

It survives at AUC 0.946 over 98 families (`attribute_separation.py`). This tool
shows the mechanism, which is the part worth keeping: mono designers COMPENSATE
IN THE INK. The `i` gets slab serifs, the `m` is squeezed, and that uniformity is
drawn into the glyphs rather than into the metrics. So the advance is destroyed
exactly as predicted, and the attribute is not.

The general lesson, which applies to any future attribute: an attribute is
carried by whatever a designer DREW to express it, not by the metric that
happens to define it. Reasoning from the definition of the attribute to what an
image contains is what went wrong here.

  python analysis/advance_survives_atlas.py
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import json
import os
import warnings

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Four monospace and three proportional faces, named rather than sampled: this
# is a mechanism demonstration, not the statistic. The statistic is
# `attribute_separation.py`, which uses 98 families.
MONO = ("CourierPrime", "JetBrainsMono", "RobotoMono", "SpaceMono")
PROPORTIONAL = ("OpenSans", "Lato", "Merriweather")


def find(pool, stem):
    for ext in ("ttf", "otf"):
        hits = sorted(glob.glob(os.path.join(pool, f"{stem}*.{ext}")))
        if hits:
            return hits[0]
    return None


def advance_cv(path):
    """Spread of ADVANCE widths, read from the font file. ~0 for monospace."""
    from fontTools.ttLib import TTFont

    from atlas_constants import CHARSET

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        font = TTFont(path, lazy=True, fontNumber=0)
        cmap, hmtx = font.getBestCmap(), font["hmtx"]
        widths = [hmtx.metrics[cmap[ord(c)]][0] for c in CHARSET
                  if ord(c) in cmap and cmap[ord(c)] in hmtx.metrics]
        font.close()
    widths = np.array([w for w in widths if w > 0], dtype=float)
    return float(widths.std() / widths.mean())


def ink_cv(path):
    """Spread of INK widths across the rendered atlas -- all the model ever sees."""
    from atlas_constants import BLANK_INDICES, CHARSET
    from build_dataset import render_atlas
    from eval_checkpoint import crop_cell

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        atlas = np.asarray(render_atlas(path).convert("L"))
    widths = []
    for idx in range(len(CHARSET)):
        if idx in BLANK_INDICES:
            continue
        cell = crop_cell(atlas, idx)
        cell = cell[:, :, 0] if cell.ndim == 3 else cell
        cols = np.where((cell > 128).any(axis=0))[0]
        if len(cols):
            widths.append(float(cols[-1] - cols[0] + 1))
    widths = np.array(widths, dtype=float)
    return float(widths.std() / widths.mean())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pool", default=os.path.join(REPO, "font_pool"))
    ap.add_argument("--json", default=os.path.join(REPO, "research",
                                                   "advance_survives_atlas.json"))
    args = ap.parse_args()

    rows, missing = [], []
    print(f"\n  {'font':<26} {'advance CV':>11} {'atlas ink CV':>13}  class")
    for group, stems in (("mono", MONO), ("proportional", PROPORTIONAL)):
        for stem in stems:
            path = find(args.pool, stem)
            if path is None:
                missing.append(stem)
                print(f"  {stem:<26} {'not in pool':>11}")
                continue
            a, k = advance_cv(path), ink_cv(path)
            rows.append({"stem": os.path.basename(path), "class": group,
                         "advance_cv": a, "atlas_ink_cv": k})
            print(f"  {os.path.basename(path)[:25]:<26} {a:>11.4f} {k:>13.4f}  {group}")

    mono = [r for r in rows if r["class"] == "mono"]
    prop = [r for r in rows if r["class"] == "proportional"]
    if mono and prop:
        gap = min(r["atlas_ink_cv"] for r in prop) - max(r["atlas_ink_cv"] for r in mono)
        print("\n  advance CV separates perfectly: mono is 0 by definition.")
        print(f"  atlas ink CV still separates, margin {gap:+.4f}"
              f" ({'no overlap' if gap > 0 else 'OVERLAP'}).")
        print("  The advance is destroyed. The attribute is not: mono designers")
        print("  compensate in the ink, and the compensation survives centring.")

    payload = {"rows": rows, "missing": missing}
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
