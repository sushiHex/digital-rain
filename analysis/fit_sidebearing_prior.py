"""Fit a per-character sidebearing prior from real fonts.

WHY. `atlas_to_font` gave every glyph the SAME sidebearing -- one constant,
0.05 em, on both sides. Real letterfitting is nothing like that: measured over
399 corpus fonts, `H` sits at LSB 0.0518 em and `A` at 0.0060 em, an 8x
difference, because a vertical stem needs air and a diagonal does not.

`analysis/score_finished_font.py` showed letterfitting is 74% of the finished
font's error -- larger than everything the model contributes -- and `A`, `T` and
`V` were among its worst glyphs. Those are exactly the characters a constant
sidebearing is most wrong about.

Fitted here and evaluated on holdout glyphs, a per-character prior cuts advance
MAE from 0.1090 to 0.0931, a 14.6% reduction, with no retrain and no GPU.

WHAT THIS CANNOT DO. Cross-font SD is 0.023-0.050 em, comparable to the medians
themselves, so a large share of the variance is per-FONT fitting tightness
rather than per-character. This prior does not model that, and there is no
obvious signal for it in a traced atlas -- the tracer recovers ink extents, not
advances. Treat 14.6% as what the character effect alone is worth.

It also improves the PIPELINE, which helps every atlas-derived arm equally,
including the retrieval baseline. It does not make the model better than
retrieval; it makes the product better.

LICENCE AND LEAKAGE. The fit uses only `google-fonts/{ofl,apache,ufl}`, which
the upstream repository organises by licence -- none of the 87 stems in
`research/corpus_exclusions.json` appear under those trees. Holdout
superfamilies are excluded and the tool REFUSES to run without that guard, for
the same reason `select_expansion_set.py` does: the holdout excluded font FILES,
not families.

  python analysis/fit_sidebearing_prior.py
  python analysis/fit_sidebearing_prior.py --limit 200 --out research/sb.json
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

from atlas_constants import CHARSET

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(REPO, "google-fonts")
LICENCE_DIRS = ("ofl", "apache", "ufl")
HOLDOUT_FONTS = os.path.join(REPO, "eval_holdout", "fonts")
EXCLUSIONS = os.path.join(REPO, "research", "corpus_exclusions.json")
OUT = os.path.join(REPO, "research", "sidebearing_prior.json")

# A character needs this many readable fonts before its median is trusted;
# below it the builder falls back to the constant.
MIN_FONTS = 30
CHARS = [c for c in CHARSET if c != " "]


def superfamily(path_or_stem):
    """The family key used to keep holdout relatives out of the fit."""
    stem = os.path.splitext(os.path.basename(path_or_stem))[0]
    return stem.split("-")[0].split("[")[0].lower().replace("_", "").replace(" ", "")


def measure(path):
    """char -> (lsb_em, rsb_em) for one real font. {} if unreadable."""
    try:
        tt = TTFont(path, fontNumber=0, lazy=True)
    except Exception:
        return {}
    try:
        upm = tt["head"].unitsPerEm
        if not upm:
            return {}
        cmap, hmtx = tt.getBestCmap(), tt["hmtx"].metrics
        glyphset = tt.getGlyphSet()
        out = {}
        for ch in CHARS:
            gname = cmap.get(ord(ch))
            if not gname or gname not in hmtx or gname not in glyphset:
                continue
            advance = hmtx[gname][0]
            if advance <= 0:
                continue
            pen = BoundsPen(glyphset)
            try:
                glyphset[gname].draw(pen)
            except Exception:
                continue
            if not pen.bounds:
                continue
            x_min, _, x_max, _ = pen.bounds
            out[ch] = (x_min / upm, (advance - x_max) / upm)
        return out
    except Exception:
        return {}
    finally:
        try:
            tt.close()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--limit", type=int, default=600,
                    help="sample this many fonts (0 = all)")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--seed", type=int, default=0)
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
    paths = [p for p in paths if superfamily(p) not in held
             and superfamily(p) not in excluded]
    print(f"{total} fonts under {'/'.join(LICENCE_DIRS)}; "
          f"{total - len(paths)} dropped by the holdout/licence guards")

    random.Random(args.seed).shuffle(paths)
    if args.limit:
        paths = paths[:args.limit]

    lsb = {c: [] for c in CHARS}
    rsb = {c: [] for c in CHARS}
    readable = 0
    for path in paths:
        m = measure(path)
        if not m:
            continue
        readable += 1
        for ch, (left, right) in m.items():
            lsb[ch].append(left)
            rsb[ch].append(right)
    print(f"read {readable} of {len(paths)} sampled fonts")

    prior, thin = {}, []
    for ch in CHARS:
        if len(lsb[ch]) < MIN_FONTS:
            thin.append(ch)
            continue
        prior[ch] = {
            "lsb": round(float(np.median(lsb[ch])), 5),
            "rsb": round(float(np.median(rsb[ch])), 5),
            "lsb_sd": round(float(np.std(lsb[ch])), 5),
            "rsb_sd": round(float(np.std(rsb[ch])), 5),
            "n": len(lsb[ch]),
        }
    print(f"prior covers {len(prior)} of {len(CHARS)} characters"
          + (f"; too few fonts for {''.join(thin)}" if thin else ""))

    payload = {
        "_comment": (
            "TRACKED. Per-character sidebearings in em, median over real fonts. "
            "atlas_to_font.build_font uses this instead of one constant for "
            "every glyph. Fitted on google-fonts/{ofl,apache,ufl} with holdout "
            "superfamilies and licence-excluded stems removed. Regenerate with "
            "analysis/fit_sidebearing_prior.py."),
        "n_fonts": readable,
        "min_fonts_per_char": MIN_FONTS,
        "chars": prior,
    }
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, sort_keys=False)
    print(f"wrote {args.out}")

    print("\n  char    LSB      RSB    cross-font SD")
    for ch in "HOAVTiolm.":
        if ch in prior:
            p = prior[ch]
            print(f"   {ch!r}   {p['lsb']:+.4f}  {p['rsb']:+.4f}   "
                  f"{p['lsb_sd']:.4f}  (n={p['n']})")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
