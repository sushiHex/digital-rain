"""Pre-registered cross-model analysis for the matched multi-seed run.

WRITTEN AND COMMITTED BEFORE THE 9B ARM FINISHED, deliberately. Every prior
comparison in this project was analysed after seeing the numbers, and three of
them turned out to depend on a choice made at analysis time (conditioning a
delta on its baseline; splitting hard/easy on that same baseline; reporting a
lenient identity definition). Fixing the analysis in advance is the cheapest
guard against a fourth.

THE ESTIMAND. The difference between TWO SPECIFIC CHECKPOINTS on this holdout.
Not "4B vs 9B architecture": both checkpoints are single training-seed-42
instances, so replicating inference seeds cannot separate architecture from
training-run luck.

THE DESIGN, fixed here:

1. Average each model over its seeds WITHIN font, then form
   d_font = mean_seeds(9B) - mean_seeds(4B). Fonts are the unit.
2. Primary test: paired Wilcoxon on d_font, plus a seed-blocked bootstrap CI.
   The bootstrap resamples FONTS and SEEDS separately, because the seed main
   effect does not average out across fonts (analysis/seed_variance.py: ~90% of
   a run's holdout-mean variance).
3. Effective n is the number of UNIQUE ground-truth atlases, not 50. Six
   holdout fonts collapse into two byte-identical groups
   (analysis/check_holdout_integrity.py). Duplicates are averaged into one
   observation rather than counted repeatedly.
4. EXCLUDE the Bitcount pair from per-font analysis. BitcountGridDoubleInk and
   BitcountPropDoubleInk share an identical reference image but have different
   ground truth, so the model emits identical output scored against two
   different targets. Any per-font difference there measures the target.
5. Difficulty enters as a CONTINUOUS, frozen, model-independent moderator
   (research/holdout_distinctiveness.json: holdout GT atlases scored against
   the frozen training-corpus centroid). No median split as a primary test --
   it discards information and makes the answer threshold-dependent.
6. Report both the lenient and EXACT identity definitions. Never one alone.

  python analysis/multiseed_compare.py bestofn_4b/scores.json bestofn_9b/scores.json
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import hashlib
import json
import os
from collections import defaultdict

import numpy as np
from scipy import stats

N_BOOT = 10000
EXCLUDE_SHARED_REFERENCE = ("BitcountGridDoubleInk", "BitcountPropDoubleInk")


def per_font_per_seed(path, metric="char_acc_match"):
    """{font: {seed: mean of `metric` over that font's cells}}

    `char_acc_match` is a per-cell boolean, so its font mean is a rate. The
    other recorded metrics (dino_cos, lpips, score, topo_pen) are CONTINUOUS
    and must not be coerced -- an earlier version cast every cell through
    bool(), which silently mapped every non-zero score to 1.0 and made every
    model difference exactly +0.0000 with a nan p-value on those metrics.
    """
    from candidate_gen import parse_candidate_key

    out = defaultdict(dict)
    for key, cells in json.load(open(path, encoding="utf-8")).items():
        font, _model, seed = parse_candidate_key(key)
        vals = [c[metric] for c in cells if c.get(metric) is not None]
        if not vals:
            continue
        out[font][seed] = float(np.mean(
            [bool(v) if isinstance(v, bool) else float(v) for v in vals]))
    return out


def duplicate_groups(atlas_dir):
    """{representative: [fonts sharing a byte-identical atlas]}"""
    import glob

    by_hash = defaultdict(list)
    for p in sorted(glob.glob(os.path.join(atlas_dir, "*.png"))):
        with open(p, "rb") as f:
            by_hash[hashlib.sha256(f.read()).hexdigest()].append(
                os.path.splitext(os.path.basename(p))[0])
    return [names for names in by_hash.values() if len(names) > 1]


def collapse(d_by_font, groups):
    """Average byte-identical fonts into one observation."""
    collapsed = dict(d_by_font)
    for names in groups:
        present = [n for n in names if n in collapsed]
        if len(present) < 2:
            continue
        mean = float(np.mean([collapsed[n] for n in present]))
        for n in present:
            del collapsed[n]
        collapsed[f"{present[0]} (+{len(present) - 1} identical)"] = mean
    return collapsed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scores_a", help="4B scores.json (several seeds)")
    ap.add_argument("scores_b", help="9B scores.json (several seeds)")
    ap.add_argument("--label-a", default="4B")
    ap.add_argument("--label-b", default="9B")
    ap.add_argument("--metric", default="char_acc_match")
    ap.add_argument("--atlas-dir", default="eval_holdout/atlases")
    ap.add_argument("--moderator", default="research/holdout_distinctiveness.json")
    ap.add_argument("--keep-shared-reference", action="store_true",
                    help="Do NOT drop the Bitcount pair. Off by default.")
    args = ap.parse_args(argv)

    A = per_font_per_seed(args.scores_a, args.metric)
    B = per_font_per_seed(args.scores_b, args.metric)
    fonts = sorted(set(A) & set(B))
    if not fonts:
        raise SystemExit("no shared fonts")

    dropped = []
    if not args.keep_shared_reference:
        for f in list(fonts):
            if any(f.startswith(p) for p in EXCLUDE_SHARED_REFERENCE):
                fonts.remove(f)
                dropped.append(f)

    seeds_a = sorted({s for f in fonts for s in A[f]})
    seeds_b = sorted({s for f in fonts for s in B[f]})
    print(f"{args.label_a}: {len(seeds_a)} seeds   {args.label_b}: {len(seeds_b)} seeds"
          f"   fonts {len(fonts)}")
    for f in dropped:
        print(f"  dropped (shared reference image, different GT): {f[:60]}")

    mA = {f: float(np.mean(list(A[f].values()))) for f in fonts}
    mB = {f: float(np.mean(list(B[f].values()))) for f in fonts}
    d = {f: mB[f] - mA[f] for f in fonts}

    groups = duplicate_groups(args.atlas_dir)
    d_c = collapse(d, groups)
    print(f"  collapsed {len(d)} fonts -> {len(d_c)} unique observations "
          f"({len(groups)} duplicate group(s))")

    vals = np.array(list(d_c.values()))
    print(f"\nPRIMARY: mean per-font difference ({args.label_b} - {args.label_a})")
    print(f"  mean {vals.mean():+.4f}   median {np.median(vals):+.4f}   n={len(vals)}")
    if len(vals) >= 10:
        w = stats.wilcoxon(vals, alternative="two-sided")
        print(f"  paired Wilcoxon p={w.pvalue:.4g}")

    # seed-blocked bootstrap: resample fonts AND seeds
    rng = np.random.default_rng(0)
    boot = []
    fl = list(d_c)
    for _ in range(N_BOOT):
        fs = rng.choice(len(fl), len(fl), replace=True)
        sa = rng.choice(seeds_a, len(seeds_a), replace=True)
        sb = rng.choice(seeds_b, len(seeds_b), replace=True)
        acc = []
        for i in fs:
            name = fl[i]
            base = name.split(" (+")[0]
            if base not in A:
                acc.append(d_c[name])
                continue
            a = np.mean([A[base][s] for s in sa if s in A[base]])
            b = np.mean([B[base][s] for s in sb if s in B[base]])
            acc.append(b - a)
        boot.append(np.mean(acc))
    lo, hi = np.percentile(boot, [2.5, 97.5])
    print(f"  bootstrap 95% CI (fonts + seeds resampled): [{lo:+.4f}, {hi:+.4f}]")
    print(f"  -> {'EXCLUDES' if lo > 0 or hi < 0 else 'INCLUDES'} zero")

    # continuous moderator
    if os.path.isfile(args.moderator):
        mod = json.load(open(args.moderator, encoding="utf-8"))["scores"]
        xs, ys = [], []
        for f in fonts:
            if f in mod:
                xs.append(mod[f]["distinctiveness"])
                ys.append(d[f])
        if len(xs) >= 10:
            r, p = stats.spearmanr(xs, ys)
            sl, ic, rr, pp, se = stats.linregress(xs, ys)
            print(f"\nMODERATOR: does the gap grow with structural distinctiveness?")
            print(f"  Spearman rho={r:+.3f} p={p:.4g}   slope={sl:+.4f} (SE {se:.4f}) "
                  f"p={pp:.4g}   n={len(xs)}")
            print("  (frozen, model-independent: GT atlases vs the training-corpus centroid)")
    else:
        print(f"\nMODERATOR: {args.moderator} missing -- run "
              "analysis/score_holdout_distinctiveness.py")

    print("\nESTIMAND REMINDER: this compares two checkpoints, each trained with a"
          "\nsingle training seed. It cannot separate architecture from training luck.")


if __name__ == "__main__":
    main()
