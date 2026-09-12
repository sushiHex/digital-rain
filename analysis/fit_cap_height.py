"""Fit the cap height the font builder has to assume.

WHY THERE IS A CONSTANT AT ALL. `build_dataset` renders each font at a
binary-searched pixel size that FITS the 106x160 cell, so the atlas carries a
glyph's shape but not its absolute size in em. `atlas_to_font` therefore cannot
measure cap height; it has to assume one, and scale everything to it. That
constant was `TARGET_CAP_EM = 0.70`, chosen as "typical cap height for a text
face" rather than measured.

WHAT IT COSTS. Every width scales with it. Measured on the holdout, traced ink
came out a median 0.9606 of real ink, and 0.70 / (real median cap) accounts for
roughly 38% of that deficit -- a systematic, uniform size error nothing in cell
space can see.

WHAT IT CANNOT FIX. Cap height varies enormously between fonts (SD ~0.10 em,
range 0.60-1.04 on the holdout). No constant can recover a per-font value the
atlas does not carry. Fitting the constant removes the MEAN bias only; the
spread is an architectural limit of the atlas format, in the same family as the
equal sidebearings and the missing space cell.

MEASUREMENT. Cap height is the yMax of FLAT-TOPPED capitals only. Round caps
(`O C G S Q`) overshoot the cap line by design and would bias the figure up.

  python analysis/fit_cap_height.py
  python analysis/fit_cap_height.py --limit 1200
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import json
import os
import random

import numpy as np
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(REPO, "google-fonts")
LICENCE_DIRS = ("ofl", "apache", "ufl")
HOLDOUT_FONTS = os.path.join(REPO, "eval_holdout", "fonts")
EXCLUSIONS = os.path.join(REPO, "research", "corpus_exclusions.json")

# Flat-topped capitals. Round caps overshoot and would bias the estimate up.
FLAT_CAPS = "HEFTILNM"
MIN_GLYPHS = 4


def superfamily(path_or_stem):
    stem = os.path.splitext(os.path.basename(path_or_stem))[0]
    return stem.split("-")[0].split("[")[0].lower().replace("_", "").replace(" ", "")


def cap_height_em(path):
    """Median yMax of the flat-topped capitals, in em. None if unreadable."""
    try:
        tt = TTFont(path, fontNumber=0, lazy=True)
    except Exception:
        return None
    try:
        upm = tt["head"].unitsPerEm
        if not upm:
            return None
        cmap, glyphset = tt.getBestCmap(), tt.getGlyphSet()
        tops = []
        for ch in FLAT_CAPS:
            gname = cmap.get(ord(ch))
            if not gname or gname not in glyphset:
                continue
            pen = BoundsPen(glyphset)
            try:
                glyphset[gname].draw(pen)
            except Exception:
                continue
            if pen.bounds:
                tops.append(pen.bounds[3] / upm)
        if len(tops) < MIN_GLYPHS:
            return None
        return float(np.median(tops))
    except Exception:
        return None
    finally:
        try:
            tt.close()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--limit", type=int, default=1000, help="0 = all")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--json", help="optionally write the distribution here")
    args = ap.parse_args()

    if not os.path.isdir(HOLDOUT_FONTS):
        print(f"refusing to run: no holdout at {HOLDOUT_FONTS}, so the "
              "superfamily leakage guard cannot be applied", file=_sys.stderr)
        return 2
    held = {superfamily(p) for p in glob.glob(os.path.join(HOLDOUT_FONTS, "*.*"))}
    if not held:
        print("refusing to run: holdout directory is empty", file=_sys.stderr)
        return 2

    excluded = set()
    if os.path.isfile(EXCLUSIONS):
        data = json.load(open(EXCLUSIONS, encoding="utf-8"))
        excluded = {superfamily(s) for s in data.get("exclude_stems", [])}

    paths = []
    for sub in LICENCE_DIRS:
        paths += glob.glob(os.path.join(CORPUS, sub, "**", "*.ttf"), recursive=True)
    total = len(paths)
    paths = [p for p in paths
             if superfamily(p) not in held and superfamily(p) not in excluded]
    print(f"{total} fonts under {'/'.join(LICENCE_DIRS)}; "
          f"{total - len(paths)} dropped by the holdout/licence guards")

    random.Random(args.seed).shuffle(paths)
    if args.limit:
        paths = paths[:args.limit]

    caps = [c for c in (cap_height_em(p) for p in paths) if c]
    if not caps:
        print("no readable cap heights", file=_sys.stderr)
        return 3
    caps = np.array(caps)

    median = float(np.median(caps))
    print(f"\nread {len(caps)} of {len(paths)} sampled fonts")
    print(f"  mean    {caps.mean():.4f} em")
    print(f"  median  {median:.4f} em   <- the fitted constant")
    print(f"  sd      {caps.std():.4f}")
    print(f"  range   {caps.min():.3f} - {caps.max():.3f}")
    for q in (10, 25, 75, 90):
        print(f"  p{q:<2}     {np.percentile(caps, q):.4f}")

    print(f"\n  TARGET_CAP_EM currently 0.70 -> uniform width bias "
          f"{0.70 / median:.4f}")
    print(f"  fitting it to {median:.4f} removes that mean bias.")
    print(f"  It cannot remove the SPREAD (sd {caps.std():.4f}): the atlas is "
          "fit-to-cell,\n  so per-font cap height is not recoverable from it.")

    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"n_fonts": len(caps), "median": round(median, 4),
                       "mean": round(float(caps.mean()), 4),
                       "sd": round(float(caps.std()), 4),
                       "min": round(float(caps.min()), 4),
                       "max": round(float(caps.max()), 4),
                       "flat_caps": FLAT_CAPS}, fh, indent=1)
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
