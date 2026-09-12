"""Score holdout fonts for structural distinctiveness, non-circularly.

Why this exists: `research/font_distinctiveness.json` scores the **925 training
fonts** and has ZERO overlap with the 50 holdout fonts, so it cannot supply a
difficulty moderator for holdout analyses. (Its `--validate` mode does score the
holdout, but against a centroid recomputed from the holdout itself, and it
discards the result.)

The moderator must not come from model output. Two ways to get that wrong:

  * conditioning on the BASELINE model's score -- the regression-to-the-mean bug
    corrected in compare_runs.redistribution() (rho -0.253 under a true null);
  * conditioning on the MIDPOINT of the two models -- unbiased only when both
    runs have equal variance, since Cov((a+b)/2, b-a) = (Var(b)-Var(a))/2.

This measures GROUND TRUTH atlases only, against the **frozen training-corpus
centroid**, so it is independent of every model and fixed before any comparison
is run. Call it structural distinctiveness, not difficulty: distance from a
training centroid is a property of the typeface, and whether it predicts model
difficulty is exactly the hypothesis under test, not an assumption.

Ink coverage is reported alongside, because DINOv2 distance from a centroid
rewards near-blank atlases -- the defect that put four hairline instances into
dataset_v3 (CLAUDE.md, "Check generated ink").

  python analysis/score_holdout_distinctiveness.py
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

from analysis.score_font_distinctiveness import telling_cells
from analysis.select_expansion_set import ink_fraction


def embed_dir(atlas_glob, embed_fn, label):
    """{stem: unit-normalized mean telling-cell embedding}, plus ink fractions."""
    vecs, inks = {}, {}
    paths = sorted(glob.glob(atlas_glob))
    if not paths:
        raise SystemExit(f"no atlases matched {atlas_glob}")
    for i, p in enumerate(paths):
        try:
            arr = np.asarray(Image.open(p).convert("RGB"))
            v = embed_fn(telling_cells(arr)).mean(axis=0)
        except Exception as e:
            print(f"  skip {os.path.basename(p)}: {type(e).__name__}: {e}")
            continue
        stem = os.path.splitext(os.path.basename(p))[0]
        vecs[stem] = v / (np.linalg.norm(v) + 1e-8)
        inks[stem] = ink_fraction(arr)
        if (i + 1) % 200 == 0:
            print(f"  {label}: embedded {i + 1}/{len(paths)}", flush=True)
    return vecs, inks


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus-atlas-dir", default="dataset_v2/atlases",
                    help="Defines the FROZEN centroid. Never the holdout.")
    ap.add_argument("--holdout-atlas-dir", default="eval_holdout/atlases")
    ap.add_argument("--out", default="research/holdout_distinctiveness.json")
    args = ap.parse_args(argv)

    from cleanup.models import build_dino_embed_fn
    embed_fn = build_dino_embed_fn()

    print(f"frozen centroid from {args.corpus_atlas_dir} (training corpus)")
    corpus_vecs, _ = embed_dir(os.path.join(args.corpus_atlas_dir, "*.png"),
                               embed_fn, "corpus")
    C = np.stack(list(corpus_vecs.values()))
    centroid = C.mean(axis=0)
    centroid /= np.linalg.norm(centroid) + 1e-8
    print(f"  centroid over {len(C)} training fonts")

    print(f"scoring {args.holdout_atlas_dir} (ground truth atlases)")
    hold_vecs, hold_ink = embed_dir(os.path.join(args.holdout_atlas_dir, "*.png"),
                                    embed_fn, "holdout")

    scores = {k: {"distinctiveness": float(1.0 - v @ centroid),
                  "ink_fraction": round(hold_ink[k], 5)}
              for k, v in hold_vecs.items()}

    # Sanity: the moderator must not be a proxy for "blank".
    d = np.array([s["distinctiveness"] for s in scores.values()])
    ink = np.array([s["ink_fraction"] for s in scores.values()])
    from scipy import stats
    rho, p = stats.spearmanr(d, ink)
    print(f"\n  {len(scores)} holdout fonts scored")
    # NOT "INDEPENDENT" -- that label (used here until 2026-08-08) accepted the
    # null from a non-significant test. At n=50 this has little power, so a
    # p>0.05 is failure to detect a confound, not evidence there isn't one.
    verdict = ("no significant correlation detected (NOT proof of independence "
               f"-- n={len(scores)} has low power)" if p > 0.05
               else "CONFOUNDED -- investigate")
    print(f"  distinctiveness vs ink: Spearman rho={rho:+.3f} p={p:.3f} ({verdict})")
    print(f"  percentiles 10/50/90: {np.percentile(d, [10, 50, 90]).round(4)}")
    top = sorted(scores.items(), key=lambda kv: -kv[1]["distinctiveness"])[:8]
    print("\n  most structurally distinctive holdout fonts:")
    for k, v in top:
        print(f"    {k[:46]:48} {v['distinctiveness']:.4f}  ink {v['ink_fraction']:.4f}")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump({"metric": "cosine distance from the FROZEN training-corpus "
                         "centroid of the mean DINOv2 telling-cell embedding",
               "corpus_atlas_dir": args.corpus_atlas_dir,
               "n_corpus": len(C),
               "note": "computed from GROUND TRUTH atlases only -- independent "
                       "of every model, fixed before any comparison",
               "ink_spearman_rho": float(rho), "ink_spearman_p": float(p),
               "scores": scores},
              open(args.out, "w", encoding="utf-8"), indent=1)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
