"""Paired Wilcoxon signed-rank comparison between two eval runs.

Replaces cell-bootstrap with a well-powered paired test on per-font means.
Round 2 adversarial finding: cell-bootstrap on 4,700 cells is overconfident
(effective n is the 50 fonts, not 4,700 cells). Paired Wilcoxon at n=50 has
~80% power to detect Cohen's d >= 0.4.

Reports composite/char_acc/racc/dinov2/lpips, plus IDENTITY when both runs
were scored with `eval_checkpoint --identity`.

Usage:
  python analysis/compare_runs.py <run_a/per_cell.json> <run_b/per_cell.json>
  python -m analysis.compare_runs <run_a/per_cell.json> <run_b/per_cell.json>
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import datetime
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy import stats

from eval_checkpoint import METRIC_WEIGHTS, compute_composite

MIN_NONZERO_PAIRS = 10           # below this, two-sided p<0.05 is unreachable in practice
USE_APPROX_AT = 20               # >= 20 nonzero pairs: normal approximation is fine
EFFECT_R_MEDIUM = 0.3            # Cohen 1988: <0.1 trivial, 0.1-0.3 small, 0.3-0.5 medium, >0.5 large


@dataclass
class WilcoxonResult:
    median_a: float
    median_b: float
    median_delta: float           # median(b - a); 0 when most pairs tie
    W: float                       # scipy.stats.wilcoxon statistic
    p: float                       # p-value (exact for n<20, approx otherwise)
    effect_r: float                # |z| / sqrt(n_nonzero)
    n_nonzero: int                 # pairs after dropping zero-diff entries
    # Direction of the effect, +1 if B is larger, -1 if A is larger, 0 if
    # undetermined. NOT derivable from median_delta: on a near-ceiling metric
    # like identity, 40 of 50 fonts tie exactly and the median delta is 0.0
    # while the test is still highly significant. Taken from the mean of the
    # nonzero differences, which is what the signed-rank test actually ranks.
    direction: int
    mean_delta_nonzero: float     # mean(b - a) over non-tied pairs; the magnitude
                                  # behind `direction`, reportable when d_med is 0


def per_font_metrics(records):
    """Aggregate per-cell records into one row per font."""
    by_font = defaultdict(list)
    for r in records:
        by_font[r["font"]].append(r)
    out = {}
    for font, rs in by_font.items():
        lpips = float(np.mean([r["lpips"] for r in rs]))
        racc = float(np.mean([1.0 if r["racc_match"] else 0.0 for r in rs]))
        dino = float(np.mean([r["dinov2"] for r in rs]))
        cacc = float(np.mean([float(r["char_acc_match"]) for r in rs]))
        row = {
            "lpips": lpips,
            "racc": racc,
            "dinov2": dino,
            "char_acc": cacc,
            "composite": float(compute_composite(lpips, racc, dino)),
        }
        # IDENTITY, when both runs carry it (eval_checkpoint --identity). This
        # is the axis the project treats as primary -- char_acc is STYLE
        # FIDELITY and is provably blind to identity-only regressions (see
        # research/2026-07-28-reference-char-mismatch.md, where a real bug
        # showed p=0.948 on char_acc and p<1e-6 on identity). Averaged over
        # GT-gated cells only; a font with none is left out so it drops from
        # the paired test rather than scoring a misleading 0.
        scored = [r for r in rs if r.get("identity_scored")]
        if scored:
            row["identity"] = float(np.mean([1.0 if r["identity_match"] else 0.0
                                             for r in scored]))
        out[font] = row
    return out


def paired_wilcoxon(a_vals, b_vals) -> WilcoxonResult:
    """Paired Wilcoxon signed-rank test on per-font metric values.

    median_delta is median(b - a), a robust magnitude. Read direction off
    `direction`, not off median_delta's sign -- on a near-ceiling metric most
    pairs tie exactly and the median delta is 0.0 even when the test is
    highly significant. The caller decides whether the underlying metric is
    larger-better or smaller-better.
    Effect size r = |z| / sqrt(N) using Cohen 1988 thresholds. For
    n_nonzero < USE_APPROX_AT we use the exact null distribution for the
    p-value but still report r from the normal-approximation z.
    """
    a = np.asarray(a_vals, dtype=np.float64)
    b = np.asarray(b_vals, dtype=np.float64)
    diffs = b - a
    median_a = float(np.median(a)) if len(a) else float("nan")
    median_b = float(np.median(b)) if len(b) else float("nan")
    median_delta = float(np.median(diffs)) if len(diffs) else float("nan")
    n_nonzero = int(np.sum(diffs != 0))
    nz = diffs[diffs != 0]
    mean_nz = float(np.mean(nz)) if len(nz) else 0.0
    direction = int(np.sign(mean_nz))
    if n_nonzero < MIN_NONZERO_PAIRS:
        return WilcoxonResult(median_a, median_b, median_delta,
                              float("nan"), float("nan"), float("nan"), n_nonzero,
                              direction, mean_nz)

    # Pass (b, a) so scipy's internal diff = b - a matches median_delta.
    # Only |zstatistic| is used downstream; this just keeps the raw scipy
    # result readable to anyone who inspects it.
    p_method = "exact" if n_nonzero < USE_APPROX_AT else "approx"
    res = stats.wilcoxon(b, a, zero_method="wilcox", alternative="two-sided", method=p_method)
    if p_method == "approx":
        z = float(res.zstatistic)
    else:
        z_res = stats.wilcoxon(b, a, zero_method="wilcox", alternative="two-sided", method="approx")
        z = float(z_res.zstatistic)
    r = abs(z) / np.sqrt(n_nonzero)
    return WilcoxonResult(median_a, median_b, median_delta,
                          float(res.statistic), float(res.pvalue), float(r), n_nonzero,
                          direction, mean_nz)


# Regression-to-the-mean floor for the redistribution statistic, measured on
# same-model seed pairs where the true effect is ZERO by construction (the four
# 4B seeds in bestofn_4b/scores.json, 12 ordered pairs). See the docstring.
BITCOUNT_SHARED_REFERENCE = ("BitcountGridDoubleInk", "BitcountPropDoubleInk")

REDIST_NULL_RHO = -0.253      # conditioning on the baseline
REDIST_NULL_GAP = 0.038       # spurious |harder-half - easier-half|


def redistribution(a_vals, b_vals, larger_better=True):
    """Is B moving quality from easy fonts to hard ones, rather than adding it?

    Correlates each font's delta against the MIDPOINT (a+b)/2, not against the
    baseline a. That choice is the whole correctness of this function.

    Conditioning on the baseline is what this project did originally, and it is
    biased by construction:

        Cov(a, b - a) = Cov(a, b) - Var(a)

    so ordinary seed noise drives rho negative even when the true effect is
    completely unrelated to difficulty. Splitting "hard vs easy" on the same
    noisy baseline compounds it -- fonts land in the hard half partly because
    their baseline drew a negative error, and then regress upward.

    Measured, not argued: on 12 pairs of DIFFERENT SEEDS OF THE SAME MODEL,
    where the true effect is exactly zero, baseline conditioning yields mean
    rho=-0.253 and a spurious hard-vs-easy gap of 0.038 (one pair reaching
    p=0.037). Midpoint conditioning yields rho=-0.000 on the same data.

    Consequence for anything reported before 2026-08-07: the five-lever
    "every lever redistributes" pattern was substantially this artefact, and
    apparent hard-half gaps below ~0.038 are not distinguishable from noise.
    Compare against REDIST_NULL_GAP before believing one.
    """
    a = np.asarray(a_vals, dtype=np.float64)
    b = np.asarray(b_vals, dtype=np.float64)
    d = b - a
    if len(a) < 4 or np.all(d == 0) or np.all(a == a[0]):
        return None
    # Work in "quality" space so rho and the halves mean the same thing on
    # every metric: for lpips lower is better, so the HIGH-lpips fonts are the
    # hard ones and both the baseline and the delta must be negated.
    q, dq = (a, d) if larger_better else (-a, -d)
    mid = q + dq / 2.0          # (quality_a + quality_b) / 2
    rho, p = stats.spearmanr(mid, dq)
    med = float(np.median(mid))
    hard, easy = dq[mid <= med], dq[mid > med]
    gap = (float(np.mean(hard)) - float(np.mean(easy))) if len(hard) and len(easy) else float("nan")
    return {"rho": float(rho), "p": float(p),
            "mean_delta": float(np.mean(dq)),
            "harder_half": float(np.mean(hard)) if len(hard) else float("nan"),
            "easier_half": float(np.mean(easy)) if len(easy) else float("nan"),
            "gap": gap,
            "gap_vs_null": gap / REDIST_NULL_GAP if gap == gap else float("nan"),
            "n_harder": int(len(hard)), "n_easier": int(len(easy)),
            "conditioned_on": "midpoint (a+b)/2"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("run_a", help="Path to run A per_cell.json")
    p.add_argument("run_b", help="Path to run B per_cell.json")
    p.add_argument("--label-a", default=None)
    p.add_argument("--label-b", default=None)
    p.add_argument("--no-integrity-guard", action="store_true",
                   help="do NOT drop the byte-identical font groups and the "
                        "shared-reference Bitcount pair. The holdout is 46 "
                        "unique atlases, not 50; keeping them enters four exact "
                        "copies into the rank test.")
    p.add_argument("--no-stratify", action="store_true",
                   help="Skip the redistribution / hard-vs-easy-half block.")
    args = p.parse_args()

    label_a = args.label_a or Path(args.run_a).parent.name
    label_b = args.label_b or Path(args.run_b).parent.name

    with open(args.run_a, encoding="utf-8") as f:
        rec_a = json.load(f)
    with open(args.run_b, encoding="utf-8") as f:
        rec_b = json.load(f)

    per_font_a = per_font_metrics(rec_a)
    per_font_b = per_font_metrics(rec_b)

    shared = sorted(set(per_font_a) & set(per_font_b))

    # HOLDOUT INTEGRITY, applied here as well as in analysis/multiseed_compare.
    # The 50-font holdout is 46 unique GT atlases: IBMPlexSansArabic/Thai/
    # ThaiLooped are byte-identical, as are TiroGurmukhi/Tamil/Telugu. Their
    # generated output is identical too, so four rows were exact copies
    # entering a rank test three times -- inflating n and the effect size.
    # And BitcountGridDoubleInk / BitcountPropDoubleInk share a reference image
    # but have DIFFERENT ground truth, so any per-font number there measures
    # the target, not the model.
    dropped_dupe, dropped_bitcount = [], []
    if not args.no_integrity_guard:
        seen = {}
        for name in list(shared):
            if name.startswith(BITCOUNT_SHARED_REFERENCE):
                dropped_bitcount.append(name)
                continue
            key = (round(per_font_a[name].get("dinov2", 0.0), 6),
                   round(per_font_b[name].get("dinov2", 0.0), 6),
                   round(per_font_a[name].get("lpips", 0.0), 6))
            if key in seen:
                dropped_dupe.append(f"{name} == {seen[key]}")
            else:
                seen[key] = name
        drop = set(dropped_bitcount) | {d.split(" == ")[0] for d in dropped_dupe}
        shared = [n for n in shared if n not in drop]
        if dropped_bitcount or dropped_dupe:
            print(f"  integrity guard: n {len(shared) + len(drop)} -> {len(shared)}")
            for d in dropped_bitcount:
                print(f"    dropped (shared reference, different GT): {d[:52]}")
            for d in dropped_dupe:
                print(f"    dropped (duplicate of another font): {d[:64]}")

    only_a = set(per_font_a) - set(per_font_b)
    only_b = set(per_font_b) - set(per_font_a)
    if only_a:
        print(f"WARN: {len(only_a)} fonts only in A: {sorted(only_a)[:5]}...")
    if only_b:
        print(f"WARN: {len(only_b)} fonts only in B: {sorted(only_b)[:5]}...")
    n = len(shared)

    print()
    print("=" * 76)
    print(f"PAIRED WILCOXON  A={label_a}  vs  B={label_b}")
    print(f"  n={n} shared fonts  (effective sample size, NOT 4,700 cells)")
    print("=" * 76)

    metrics = [
        ("composite", True),
        ("char_acc", True),
        ("racc", True),
        ("dinov2", True),
        ("lpips", False),  # lower is better
    ]
    # identity only exists if BOTH runs were scored with --identity, and only
    # for fonts that had GT-gated cells. Require it on every shared font so the
    # paired test never compares a present value against a missing one.
    if all("identity" in per_font_a[f] and "identity" in per_font_b[f] for f in shared):
        metrics.append(("identity", True))
    elif any("identity" in per_font_a[f] or "identity" in per_font_b[f] for f in shared):
        print("NOTE: identity present in only some fonts/runs -- omitted from the table.")

    print(f"{'Metric':>10} {'med_A':>9} {'med_B':>9} {'d_med':>10} {'d_mean_nz':>10} "
          f"{'W':>10} {'p':>10} {'eff_r':>7} {'n_nz':>5}  verdict")
    print("-" * 104)
    # Build the paired vectors once; the redistribution pass below reuses them.
    vals = {m: ([per_font_a[f][m] for f in shared], [per_font_b[f][m] for f in shared])
            for m, _ in metrics}
    rows = []
    for metric, larger_better in metrics:
        res = paired_wilcoxon(*vals[metric])

        # Direction comes from res.direction (sign of the mean nonzero delta),
        # not from comparing median_a to median_b -- those can disagree when
        # the delta distribution is skewed -- and not from median_delta, which
        # is 0 whenever most pairs tie.
        sig = res.p < 0.05 if not np.isnan(res.p) else False
        meaningful = (not np.isnan(res.effect_r)) and res.effect_r >= EFFECT_R_MEDIUM
        delta_sign_b_better = (res.direction > 0) if larger_better else (res.direction < 0)
        if sig and meaningful:
            direction = "B better" if delta_sign_b_better else "A better"
            verdict = f"SIG  ({direction})"
        elif sig:
            verdict = "sig but small effect"
        else:
            verdict = "no diff"

        print(f"{metric:>10} {res.median_a:>9.4f} {res.median_b:>9.4f} "
              f"{res.median_delta:>+10.4f} {res.mean_delta_nonzero:>+10.4f} "
              f"{res.W:>10.1f} {res.p:>10.4f} "
              f"{res.effect_r:>7.3f} {res.n_nonzero:>5}  {verdict}")
        rows.append({"metric": metric, "larger_better": larger_better, **asdict(res)})

    print()
    print("Effect size r: <0.1 trivial, 0.1-0.3 small, 0.3-0.5 medium, >0.5 large")
    print("Significance: p<0.05 AND r>=0.3 to call a real improvement")
    print("")
    print("!! SCOPE: this gate pairs by FONT and answers 'is B better on more")
    print("!! fonts than A'. It does NOT account for TRAINING-run variance, and")
    print("!! it PASSES on two runs that differ only in --seed: measured")
    print("!! char_acc p=0.0000 r=0.731, dinov2 p=0.0000 r=0.742. Only trust a")
    print("!! SIG verdict between two training runs with replicate runs behind")
    print("!! it -- see research/2026-08-13-training-run-variance-measured-at-last.md")

    strat = {}
    if not args.no_stratify:
        print()
        print("REDISTRIBUTION  (delta vs MIDPOINT; negative rho = easy -> hard)")
        print(f"{'Metric':>10} {'mean_d':>10} {'rho':>8} {'p':>9} "
              f"{'harder/2':>10} {'easier/2':>10} {'gap':>9} {'xnull':>7}")
        print("-" * 80)
        for metric, larger_better in metrics:
            st = redistribution(*vals[metric], larger_better)
            if st is None:
                continue
            strat[metric] = st
            print(f"{metric:>10} {st['mean_delta']:>+10.4f} {st['rho']:>8.3f} "
                  f"{st['p']:>9.4f} {st['harder_half']:>+10.4f} "
                  f"{st['easier_half']:>+10.4f} {st['gap']:>+9.4f} "
                  f"{st['gap_vs_null']:>6.1f}x")
        print("\nQUALITY space (higher = better) for every metric, lpips included.")
        print("Split and rho condition on the MIDPOINT (a+b)/2, not the baseline: "
              "conditioning\non the baseline is biased by Cov(a,b-a)=Cov(a,b)-Var(a) "
              f"and reads rho={REDIST_NULL_RHO}\non same-model seed pairs where the true "
              "effect is zero.")
        print(f"'xnull' compares the gap to the {REDIST_NULL_GAP} noise floor measured "
              "there. Under ~1x is\nnot distinguishable from seed noise.")

    today = datetime.date.today().isoformat()
    out_path = Path(f"research/{today}-wilcoxon_{label_a}_vs_{label_b}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({
            "run_a": args.run_a, "run_b": args.run_b,
            "label_a": label_a, "label_b": label_b,
            "n_shared_fonts": n,
            "results": rows,
            "redistribution": strat,
            "redistribution_sign_convention":
                "quality space (higher = better) for every metric, lpips included",
        }, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
