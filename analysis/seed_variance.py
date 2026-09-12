"""How much of a run's holdout score is the seed, and what does that cost?

The project's headline comparisons are SINGLE-SEED: one run of model A against
one run of model B, tested with a paired Wilcoxon over the 50 fonts. That test
pairs by font and treats fonts as independent replicates, so it cannot see a
seed effect that shifts *every* font together -- and with one seed per model,
that effect is perfectly confounded with the model difference.

This measures the confound directly, using several seeds of ONE model, where
every difference is noise by construction. A two-way (font x seed)
decomposition separates:

  * the SEED main effect  -- a run is globally lucky or unlucky; does NOT
    average out over fonts, so it sets the floor on a single-seed comparison;
  * the font x seed residual -- averages out as 1/sqrt(n_fonts).

Measured on the four 4B seeds in bestofn_4b/: the seed main effect is SD 0.0248
and accounts for **91%** of the variance of a run's holdout mean. A single-seed
model comparison therefore carries SE ~0.037, against an observed 4B->9B
char_acc gap of 0.0457 -- about 1.2 SE, i.e. not resolvable. The paired
Wilcoxon on the same data reports p=0.0001 because it is answering a different
question (is B better on more fonts than A) than the one being asked (is model
B better than model A).

  python analysis/seed_variance.py bestofn_4b/scores.json --observed-gap 0.0457
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
from collections import defaultdict

import numpy as np

Z80 = 2.8   # z(0.975) + z(0.80), the usual 80%-power multiplier


def per_font_per_seed(scores_path, metric="char_acc_match"):
    """{font: {seed: score}} from a candidate_gen-style scores.json.

    IMPORTS the reader rather than carrying its own copy. This function used to
    duplicate it, including the `bool()` coercion that
    analysis/multiseed_compare.py fixed on 2026-08-08 and
    tests/test_multiseed_compare.py pins: bool(0.87) is True, so every
    continuous metric collapsed to 1.0 and this tool reported SD 0.0000 with
    gap/SE = inf for `--metric dino_cos`, exit 0. Two copies of a reader means
    a fix lands in one of them.
    """
    from analysis.multiseed_compare import per_font_per_seed as _read
    return _read(scores_path, metric)


def decompose(matrix):
    """Two-way (font x seed) variance components for an n_fonts x n_seeds array.

    Returns var_seed (the main effect common to all fonts) and var_resid.
    Uses the standard random-effects EMS identity; var_seed is clamped at 0
    because an unbiased estimator can go negative on small samples.
    """
    n_f, n_s = matrix.shape
    gm = matrix.mean()
    font_eff = matrix.mean(1) - gm
    seed_eff = matrix.mean(0) - gm
    resid = matrix - gm - font_eff[:, None] - seed_eff[None, :]

    ms_seed = n_f * (seed_eff ** 2).sum() / (n_s - 1)
    ms_resid = (resid ** 2).sum() / ((n_f - 1) * (n_s - 1))
    return max((ms_seed - ms_resid) / n_f, 0.0), ms_resid


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scores", nargs="?", default="bestofn_4b/scores.json",
                    help="scores.json holding SEVERAL SEEDS OF ONE MODEL")
    ap.add_argument("--observed-gap", type=float, default=0.0457,
                    help="Cross-model difference to size against.")
    ap.add_argument("--metric", default="char_acc_match")
    args = ap.parse_args(argv)

    per = per_font_per_seed(args.scores, args.metric)
    fonts = sorted(per)
    seeds = sorted({s for f in per for s in per[f]})
    M = np.array([[per[f][s] for s in seeds] for f in fonts])
    n_f, n_s = M.shape
    if n_s < 2:
        raise SystemExit(f"{args.scores} has {n_s} seed(s); need >=2")

    var_seed, var_resid = decompose(M)
    run_var = var_seed + var_resid / n_f
    print(f"{args.scores}: {n_f} fonts x {n_s} seeds of ONE model "
          f"(all variation is noise)\n")
    print(f"  seed means            : {np.round(M.mean(0), 4)}")
    print(f"  SD, seed MAIN effect  : {np.sqrt(var_seed):.4f}  "
          "(shifts every font together; does NOT average out)")
    print(f"  SD, font x seed resid : {np.sqrt(var_resid):.4f}  "
          f"(averages out as 1/sqrt({n_f}))")
    print(f"  SD of a run's mean    : {np.sqrt(run_var):.4f}  "
          f"({var_seed / run_var:.0%} of it the seed main effect)\n")

    print(f"sizing against an observed gap of {args.observed_gap:.4f}:")
    print(f"{'seeds/model':>12} {'SE(diff)':>10} {'gap/SE':>8} {'min det @80%':>14}")
    for k in (1, 2, 4, 6, 8, 12):
        se = np.sqrt(2 * run_var / k)
        print(f"{k:>12} {se:>10.4f} {args.observed_gap / se:>8.1f} {Z80 * se:>14.4f}")
    print("\nA single-seed A/B cannot separate 'model B is better' from "
          "'run B drew a\nlucky seed'. The paired Wilcoxon in compare_runs.py "
          "pairs by FONT, so it is\nblind to this term -- its p-value answers a "
          "different question.")


if __name__ == "__main__":
    main()
