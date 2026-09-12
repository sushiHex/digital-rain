"""Score structural distinctiveness of fonts NOT in the training corpus.

Why: three independent levers (rank 64, distinctiveness oversampling, and the
V5 source swap) all produced the same signature -- gains on hard fonts, matching
losses on easy ones, flat aggregate. That is redistribution at fixed
information. The corpus holds only 93 fonts above p90 distinctiveness out of
925, and the local pool holds thousands more that were filtered out (the corpus
keeps ~37% where comparable work keeps 73%). Adding information, rather than
reweighting it, is the one lever never tested.

This picks the expansion set on MEASURED spread rather than family names.

Two things this gets right that a naive scoring pass would not:

1. **Scores are anchored to the CORPUS centroid**, not a pool-internal one.
   distinctiveness() in score_font_distinctiveness.py centres on whatever set
   it is handed, so scoring the pool alone would produce numbers that look like
   the existing research/font_distinctiveness.json but are not comparable to
   it. Here the centroid is computed from dataset_v2's atlases and every pool
   font is measured against that fixed origin.
2. **Licence provenance is recorded per font.** The corpus is 87.0% OFL (not
   the 97.5% long asserted here -- see
   research/2026-08-08-the-corpus-is-not-97-percent-ofl.md) and
   that underpins the output-licensing position
   (research/2026-07-27-ofl-derivative-work-constraint.md). google-fonts/ofl/
   is licence-verifiable per family; the flat font_pool/ directory is not, so
   its fonts are marked licence-unknown and must not be adopted blindly.

Run from the repo root (long; use a detached runner):
  python analysis/score_pool_distinctiveness.py --font-dir google-fonts/ofl \
      --out research/pool_distinctiveness.json
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import json
import os
import re
from pathlib import Path

import numpy as np

from analysis.score_font_distinctiveness import TELLING, font_cells

_VARIANT = re.compile(r"[-_](Italic|Bold|Light|Thin|Black|Medium|SemiBold|ExtraBold|"
                      r"ExtraLight|BoldItalic|.*Italic)$", re.I)


def corpus_centroid(atlas_dir, embed_fn, limit=None):
    """Unit centroid of the existing corpus, the fixed origin for all scoring."""
    paths = sorted(glob.glob(os.path.join(atlas_dir, "*.png")))
    if limit:
        paths = paths[:limit]
    if not paths:
        raise SystemExit(f"no corpus atlases under {atlas_dir}")
    vecs = []
    for i, p in enumerate(paths):
        try:
            vecs.append(embed_fn(font_cells(p)).mean(axis=0))
        except Exception as e:
            print(f"  skip corpus {os.path.basename(p)}: {type(e).__name__}: {e}")
        if (i + 1) % 200 == 0:
            print(f"  corpus embedded {i + 1}/{len(paths)}", flush=True)
    M = np.stack(vecs)
    M /= np.linalg.norm(M, axis=1, keepdims=True) + 1e-8
    c = M.mean(axis=0)
    return c / (np.linalg.norm(c) + 1e-8), len(vecs)


def pick_one_per_family(font_dir):
    """One representative TTF per family directory, preferring the upright Regular.

    The corpus is one-per-family, so an expansion set must be too or the
    comparison against it is not like-for-like.
    """
    chosen = {}
    for p in sorted(glob.glob(os.path.join(font_dir, "**", "*.ttf"), recursive=True)):
        family = Path(p).parent.name
        stem = Path(p).stem
        # rank: exact Regular best, then any non-variant, then anything
        rank = 0 if stem.endswith("-Regular") else (1 if not _VARIANT.search(stem) else 2)
        if family not in chosen or rank < chosen[family][0]:
            chosen[family] = (rank, p)
    return {Path(p).stem: (fam, p) for fam, (_r, p) in chosen.items()}


def licence_of(path):
    """google-fonts/<ofl|apache|ufl>/... is verifiable; anything else is not."""
    parts = Path(path).as_posix().lower().split("/")
    for lic in ("ofl", "apache", "ufl"):
        if lic in parts:
            return lic
    return "unknown"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--font-dir", default="google-fonts/ofl")
    ap.add_argument("--corpus-atlas-dir", default="dataset_v2/atlases")
    ap.add_argument("--holdout-dir", default="eval_holdout",
                    help="Holdout fonts are EXCLUDED as candidates. Adding one to "
                         "training silently contaminates every future eval.")
    ap.add_argument("--out", default="research/pool_distinctiveness.json")
    ap.add_argument("--limit", type=int, default=None, help="first N candidate fonts")
    ap.add_argument("--corpus-limit", type=int, default=None, help="smoke test only")
    ap.add_argument("--canvas", type=int, default=None)
    args = ap.parse_args()

    from build_dataset import render_atlas, font_supports_charset
    from atlas_constants import CANVAS
    from cleanup.models import build_dino_embed_fn
    canvas = args.canvas or CANVAS

    used = {Path(p).stem for p in glob.glob(os.path.join(args.corpus_atlas_dir, "*.png"))}
    n_corpus_used = len(used)
    # The 50 holdout fonts are NOT in dataset_v2, so they look like fresh
    # candidates. Adding one to training contaminates every future eval
    # silently -- exclude by font file, atlas, and manifest name.
    holdout = set()
    hd = Path(args.holdout_dir)
    for pat in ("fonts/*.ttf", "fonts/*.otf", "atlases/*.png"):
        holdout |= {Path(p).stem for p in glob.glob(str(hd / pat))}
    mf = hd / "manifest.json"
    if mf.exists():
        holdout |= {e["name"] for e in json.load(open(mf, encoding="utf-8"))["fonts"]}
    if not holdout:
        raise SystemExit(f"no holdout fonts found under {hd} -- refusing to run "
                         "without the contamination guard")
    used |= holdout
    print(f"corpus fonts already in use: {n_corpus_used}")
    print(f"holdout fonts excluded:      {len(holdout)}")

    embed_fn = build_dino_embed_fn()
    print(f"computing corpus centroid from {args.corpus_atlas_dir}")
    centroid, n_corpus = corpus_centroid(args.corpus_atlas_dir, embed_fn, args.corpus_limit)
    print(f"  centroid over {n_corpus} corpus fonts")

    candidates = pick_one_per_family(args.font_dir)
    candidates = {s: v for s, v in candidates.items() if s not in used}
    names = sorted(candidates)
    if args.limit:
        names = names[:args.limit]
    print(f"candidate families not in corpus: {len(names)}")

    # Resume: keep anything already scored in a previous run.
    scores = {}
    if os.path.exists(args.out):
        scores = json.load(open(args.out, encoding="utf-8")).get("scores", {})
        print(f"  resuming, {len(scores)} already scored")

    rejected = {"charset": 0, "render": 0}
    for i, stem in enumerate(names):
        if stem in scores:
            continue
        family, path = candidates[stem]
        try:
            if not font_supports_charset(path):
                rejected["charset"] += 1
                continue
            atlas = np.asarray(render_atlas(path, canvas).convert("RGB"))
        except Exception:
            rejected["render"] += 1
            continue
        try:
            from atlas_constants import CHARSET
            from eval_checkpoint import crop_cell
            cells = [crop_cell(atlas, CHARSET.index(c)) for c in TELLING if c in CHARSET]
            v = embed_fn(cells).mean(axis=0)
        except Exception:
            rejected["render"] += 1
            continue
        v = v / (np.linalg.norm(v) + 1e-8)
        scores[stem] = {"score": float(1.0 - v @ centroid), "family": family,
                        "path": Path(path).as_posix(), "licence": licence_of(path)}

        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(names)} scanned, {len(scores)} scored, "
                  f"rejected charset={rejected['charset']} render={rejected['render']}",
                  flush=True)
            _write(args.out, scores, centroid_n=n_corpus, rejected=rejected)

    _write(args.out, scores, centroid_n=n_corpus, rejected=rejected)

    vals = np.array([v["score"] for v in scores.values()])
    if len(vals):
        print(f"\nscored {len(vals)} fonts   rejected charset={rejected['charset']} "
              f"render={rejected['render']}")
        print("  percentiles 10/50/90/99: "
              f"{np.percentile(vals, [10, 50, 90, 99]).round(4)}")
        top = sorted(scores.items(), key=lambda kv: -kv[1]["score"])[:15]
        print("\n  most distinctive candidates:")
        for k, v in top:
            print(f"    {k[:42]:42} {v['score']:.4f}  {v['licence']}")
    print(f"\nwrote {args.out}")


def _write(out, scores, **meta):
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"telling_chars": "".join(TELLING),
                   "metric": "cosine distance from the CORPUS centroid "
                             "(dataset_v2) of mean DINOv2 cell embedding",
                   "note": "comparable to research/font_distinctiveness.json; "
                           "same telling chars, same origin",
                   **meta, "scores": scores}, f, indent=1)


if __name__ == "__main__":
    main()
