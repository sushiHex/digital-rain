"""Measure TRAINING-run variance, and calibrate the comparison gate against it.

The companion to `analysis/seed_variance.py`, which decomposes INFERENCE-seed
variance on one checkpoint. This does the same for runs that differ only in
their TRAINING seed -- the quantity no comparison in this repo had ever had.

WHY IT MATTERS MORE THAN THE MAGNITUDE. `compare_runs.py` pairs by FONT and
treats fonts as independent replicates. Any component of the difference that
shifts every font together is invisible to it, however large. For inference
seeds that main effect is ~90% of run-mean variance. This measures the training
equivalent, and reports what the project's p<0.05 AND r>=0.3 gate does when
handed two runs that differ by nothing at all.

A gate that passes on identical configs is not a gate.

  python analysis/training_variance.py \
      eval_runs/glyph_4b_r32_clean/scores.json \
      eval_runs/glyph_4b_r32_clean_s43/scores.json \
      eval_runs/glyph_4b_r32_clean_s44/scores.json
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import itertools
import json
import os

import numpy as np
from scipy import stats

# Holdout fonts that cannot be scored per-font: identical reference image,
# different ground truth, so any difference there measures the target.
EXCLUDE = ("BitcountGridDoubleInk", "BitcountPropDoubleInk")


def per_font(path, metric):
    """Per-font values for `metric`, or a loud failure.

    `identity` lives in `aggregate` but NOT in `per_font`, so asking for it
    silently produced n_fonts=0, NaN everywhere, and a written-out JSON file
    that looked like a result. Fail instead: a variance tool that reports NaN
    as an answer is worse than one that refuses.
    """
    d = json.load(open(path, encoding="utf-8"))
    table = {f["name"]: f[metric] for f in d["per_font"] if metric in f}
    if not table:
        have = sorted(set(d["per_font"][0]) - {"name"}) if d.get("per_font") else []
        raise SystemExit(
            f"{path}: no per-font values for metric {metric!r}. "
            f"per_font carries {have}. "
            f"({metric!r} may exist only in `aggregate`, which cannot be "
            "decomposed per font.)")
    return table, d["aggregate"].get(metric)


def effect_r(p, n):
    if not (0 < p < 1):
        return float("nan")
    return abs(stats.norm.ppf(p / 2)) / np.sqrt(n)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="scores.json for >=2 SAME-CONFIG runs")
    ap.add_argument("--metric", default="char_acc")
    ap.add_argument("--out", default=None,
                    help="default research/training_variance_<metric>.json, so a "
                         "char_acc run cannot silently overwrite a dinov2 one")
    args = ap.parse_args(argv)
    if args.out is None:
        args.out = f"research/training_variance_{args.metric}.json"

    if len(args.runs) < 2:
        raise SystemExit("need at least two runs")

    tables, means, labels = [], [], []
    for p in args.runs:
        t, agg = per_font(p, args.metric)
        tables.append(t)
        means.append(agg)
        labels.append(os.path.basename(os.path.dirname(p)))

    common = sorted(set.intersection(*(set(t) for t in tables)))
    common = [f for f in common if not f.startswith(EXCLUDE)]
    M = np.array([[t[f] for f in common] for t in tables])   # (runs, fonts)
    n_runs, n_fonts = M.shape

    print(f"metric: {args.metric}   runs: {n_runs}   fonts: {n_fonts} "
          f"(Bitcount pair excluded)\n")
    for lab, row in zip(labels, M):
        print(f"  {lab:<40} mean {row.mean():.4f}")

    run_means = M.mean(axis=1)
    print(f"\nrun-mean spread: min {run_means.min():.4f}  max {run_means.max():.4f}"
          f"  range {np.ptp(run_means):.4f}")
    if n_runs >= 3:
        sd = run_means.std(ddof=1)
        print(f"run-mean SD (n={n_runs}, {n_runs-1} df): {sd:.4f}")
    else:
        # E|X-Y| = 2*sigma/sqrt(pi) for two iid normals
        sd = abs(run_means[0] - run_means[1]) / 1.1284
        print(f"run-mean SD implied by one pair: ~{sd:.4f}  (n=2 -- very wide)")

    print("\n--- what the project's gate does on runs that differ by NOTHING ---")
    rows = []
    for i, j in itertools.combinations(range(n_runs), 2):
        d = M[j] - M[i]
        w = stats.wilcoxon(d, alternative="two-sided")
        r = effect_r(w.pvalue, n_fonts)
        passes = w.pvalue < 0.05 and r >= 0.3
        main_share = d.mean() ** 2 / (d.var(ddof=1) + d.mean() ** 2)
        rows.append({"pair": f"{labels[i]} vs {labels[j]}",
                     "delta_mean": round(float(d.mean()), 4),
                     "p": float(w.pvalue), "r": round(float(r), 3),
                     "passes_gate": bool(passes),
                     "main_effect_share": round(float(main_share), 3)})
        print(f"  {labels[i][-12:]:>12} vs {labels[j][-12:]:<12} "
              f"delta {d.mean():+.4f}  p={w.pvalue:.3g}  r={r:.3f}  "
              f"{'PASSES GATE' if passes else 'no'}   "
              f"main-effect share {main_share:.0%}")

    n_pass = sum(r["passes_gate"] for r in rows)
    print(f"\n  {n_pass} of {len(rows)} identical-config pairs PASS "
          f"the p<0.05 & r>=0.3 gate.")
    if n_pass:
        print("  The gate does not protect against training-run noise.")

    # The largest same-config gap OBSERVED. Deliberately not called a "floor":
    # it is the range of a small sample, so it grows with the number of runs
    # (E[range] ~ 1.69*sigma at n=3, 2.06*sigma at n=4) and guarantees nothing.
    # It is useful as a concrete "two identical runs really did differ by this
    # much", and useless as a threshold. Quote it as evidence, not as a bar.
    gap = max(abs(rows_i["delta_mean"]) for rows_i in rows)
    print(f"\nLARGEST OBSERVED same-config run-mean difference: {gap:.4f}")
    print(f"  (range of {n_runs} runs -- descriptive, NOT a threshold: it grows "
          "with the number of runs and guarantees nothing)")
    if n_runs >= 3:
        lo, hi = (sd * np.sqrt((n_runs - 1) / stats.chi2.ppf(q, n_runs - 1))
                  for q in (0.975, 0.025))
        print(f"  95% CI on the run-mean SD ({n_runs-1} df): "
              f"[{lo:.4f}, {hi:.4f}] -- {hi/lo:.0f}x wide")

    payload = {"_comment": "Training-run variance. Runs differ ONLY in --seed. "
                           "largest_observed_gap is DESCRIPTIVE (the range of a "
                           "small sample), not a threshold. Compare effects "
                           "against run_mean_sd for THIS metric -- never against "
                           "another metric's SD.",
               "metric": args.metric, "n_runs": n_runs, "n_fonts": n_fonts,
               "runs": labels, "run_means": [round(float(x), 4) for x in run_means],
               "run_mean_sd": round(float(sd), 4),
               "largest_observed_gap": round(float(gap), 4),
               "pairs": rows}
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
