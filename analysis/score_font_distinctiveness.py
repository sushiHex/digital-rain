"""Score how structurally distinctive each TRAINING font is.

Why: `research/2026-07-31-rank64-redistributes-capacity.md` showed the model's
capacity allocation is malleable and responds to pressure — rank 64 shifted
quality toward hard fonts unprompted (Spearman rho -0.68 on dinov2, p<1e-4).
Applying that pressure deliberately means oversampling structurally distinctive
fonts, which needs a per-font distinctiveness score over the 925-font corpus.

Method: DINOv2-embed a fixed set of telling glyphs per font (the project's
established structural metric, reused from cleanup.models.build_dino_embed_fn),
mean-pool to one vector per font, and score distinctiveness as cosine distance
from the corpus centroid. Fonts far from the centroid are unusual.

VALIDATION is the point of --validate: the same score is computed over the 50
holdout fonts, where `audit_diversity.DISTINCTIVE` independently names which
ones are structurally distinctive. If the score does not rank those highly, it
is not measuring what it claims and must not drive a training run.

Run from the repo root:
  python analysis/score_font_distinctiveness.py --validate
  python analysis/score_font_distinctiveness.py --out research/font_distinctiveness.json
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

from atlas_constants import CHARSET
from eval_checkpoint import crop_cell

# Structurally telling glyphs: mixed case, counters, diagonals, a digit and a
# symbol. Same spirit as audit_diversity's eyeball set, widened a little so one
# unusual letterform cannot dominate the embedding.
TELLING = list("aegRQMW4&osk")


def telling_cells(arr):
    """Crop the telling cells from an atlas ARRAY.

    The single definition of "which cells make a font's vector". Comparability
    between research/font_distinctiveness.json, the pool scores and the
    expansion selector rests on every caller cropping the same cells, so they
    all route through here rather than re-listing TELLING.
    """
    return [crop_cell(arr, CHARSET.index(c)) for c in TELLING if c in CHARSET]


def font_cells(atlas_path):
    """Crop the telling cells from one atlas PNG."""
    return telling_cells(np.asarray(Image.open(atlas_path).convert("RGB")))


def score_dir(atlas_glob, embed_fn, limit=None):
    """font stem -> mean DINOv2 embedding over its telling cells."""
    paths = sorted(glob.glob(atlas_glob))
    if limit:
        paths = paths[:limit]
    out = {}
    for i, p in enumerate(paths):
        stem = os.path.splitext(os.path.basename(p))[0]
        try:
            cells = font_cells(p)
        except Exception as e:
            print(f"  skip {stem}: {type(e).__name__}: {e}")
            continue
        out[stem] = embed_fn(cells).mean(axis=0)
        if (i + 1) % 100 == 0:
            print(f"  embedded {i + 1}/{len(paths)}", flush=True)
    return out


def distinctiveness(embs):
    """Cosine distance from the corpus centroid, per font."""
    names = sorted(embs)
    M = np.stack([embs[n] for n in names])
    M = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-8)
    centroid = M.mean(axis=0)
    centroid /= np.linalg.norm(centroid) + 1e-8
    return {n: float(1.0 - M[i] @ centroid) for i, n in enumerate(names)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--atlas-dir", default="dataset_v2/atlases")
    ap.add_argument("--out", default="research/font_distinctiveness.json")
    ap.add_argument("--limit", type=int, default=None, help="first N fonts (smoke test)")
    ap.add_argument("--validate", action="store_true",
                    help="also score the 50 holdout fonts and check the score ranks "
                         "audit_diversity.DISTINCTIVE highly")
    args = ap.parse_args()

    from cleanup.models import build_dino_embed_fn
    embed_fn = build_dino_embed_fn()

    if args.validate:
        from audit_diversity import DISTINCTIVE
        print("VALIDATION: scoring the 50 holdout fonts")
        h = score_dir("eval_holdout/atlases/*.png", embed_fn)
        d = distinctiveness(h)
        ranked = sorted(d, key=d.get, reverse=True)
        n = len(ranked)
        print(f"\n  {'font':38} {'score':>7} {'rank':>6}  known-distinctive?")
        for name in ranked[:12]:
            known = any(name.startswith(k) for k in DISTINCTIVE)
            print(f"  {name[:38]:38} {d[name]:7.4f} {ranked.index(name)+1:>4}/{n}"
                  f"  {'YES' if known else ''}")
        known_ranks = [ranked.index(x) + 1 for x in ranked
                       if any(x.startswith(k) for k in DISTINCTIVE)]
        if known_ranks:
            print(f"\n  known-distinctive fonts rank at: {sorted(known_ranks)} of {n}")
            print(f"  median rank {np.median(known_ranks):.0f}/{n} "
                  f"(random would be {n/2:.0f})")
        print()

    print(f"scoring training corpus: {args.atlas_dir}")
    embs = score_dir(os.path.join(args.atlas_dir, "*.png"), embed_fn, args.limit)
    d = distinctiveness(embs)
    ranked = sorted(d, key=d.get, reverse=True)
    print(f"\n  {len(d)} fonts scored")
    print("  most distinctive: " + ", ".join(f"{n}({d[n]:.3f})" for n in ranked[:6]))
    print("  least distinctive: " + ", ".join(f"{n}({d[n]:.3f})" for n in ranked[-6:]))

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"telling_chars": "".join(TELLING),
                   "metric": "cosine distance from corpus centroid of mean DINOv2 cell embedding",
                   "scores": d}, f, indent=1)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
