"""The six-seed 4B-vs-9B comparison on the metrics the multiseed run never scored.

WHY. `analysis/multiseed_compare.py` settled the 4B-9B gap on char_acc,
DINOv2 and LPIPS with six inference seeds per checkpoint, but the run's
`scores.json` came from `score_candidates`, which records neither R-ACC nor
IDENTITY, and whose `score` is a different composite from
`eval_checkpoint.compute_composite`. So the README's claims on those three
metrics still rest on ONE seed (CLAUDE.md, "R-ACC, IDENTITY and the README
composite were NOT scored in this run"; issue #12). `runners/run_rescore_multiseed.sh`
re-scores the twelve existing candidate sets with `eval_checkpoint`, no
generation, and this script applies the REGISTERED statistic to the result.

WHAT IS REUSED, UNCHANGED. The estimand and every step of the analysis are
`multiseed_compare`'s: average each model over its seeds within font, take
per-font differences 9B - 4B, drop the two fonts that share a reference image,
collapse byte-identical ground-truth atlases into one observation, paired
Wilcoxon, and the seed-blocked bootstrap that resamples fonts AND seeds
(`multiseed_compare.seed_blocked_bootstrap`). Only the reader differs: it
takes `eval_checkpoint`'s `per_cell.json` per seed instead of one
`scores.json` keyed by candidate. The metrics were named in issue #12 before
anything was scored.

PER-FONT VALUES, AS THE EVALUATOR DEFINES THEM.
  racc       rate of `racc_match` over a font's cells
  identity   rate of `identity_match` over the cells the GT gate kept
             (`identity_scored`), i.e. the 0.9936-style number
  lpips, dinov2   cell means
  composite  eval_checkpoint.compute_composite(lpips, racc, dinov2) of the
             font's means -- the README composite, not score_candidates'

  python analysis/multiseed_rescore.py
  python analysis/multiseed_rescore.py --runs "eval_runs/multiseed_{arm}_s{seed}" --seeds 0 1 2 3 4 5
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
import os
from collections import defaultdict

import numpy as np
from scipy import stats

from analysis.multiseed_compare import (EXCLUDE_SHARED_REFERENCE, collapse,
                                        duplicate_groups, seed_blocked_bootstrap)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS = ("racc", "identity", "composite", "lpips", "dinov2")
RUN_PATTERN = "eval_runs/multiseed_{arm}_s{seed}"
ARMS = {"4b": "4B", "9b": "9B"}
DEFAULT_SEEDS = (0, 1, 2, 3, 4, 5)
OUT_JSON = os.path.join(REPO, "research", "multiseed_rescore.json")


def _composite(lpips, racc, dinov2):
    from eval_checkpoint import compute_composite
    return compute_composite(lpips, racc, dinov2)


def font_values(cells):
    """{font: {metric: value}} from one per_cell.json's cell records.

    A font with no scored cell for a metric has no entry for it, so it drops
    out of that metric's comparison instead of counting as zero.
    """
    by_font = defaultdict(list)
    for c in cells:
        by_font[c["font"]].append(c)
    out = {}
    for font, cs in by_font.items():
        v = {}
        racc = [bool(c["racc_match"]) for c in cs if c.get("racc_match") is not None]
        lp = [float(c["lpips"]) for c in cs if c.get("lpips") is not None]
        dn = [float(c["dinov2"]) for c in cs if c.get("dinov2") is not None]
        ident = [bool(c["identity_match"]) for c in cs
                 if c.get("identity_scored") and c.get("identity_match") is not None]
        if racc:
            v["racc"] = float(np.mean(racc))
        if lp:
            v["lpips"] = float(np.mean(lp))
        if dn:
            v["dinov2"] = float(np.mean(dn))
        if ident:
            v["identity"] = float(np.mean(ident))
        if racc and lp and dn:
            v["composite"] = float(_composite(v["lpips"], v["racc"], v["dinov2"]))
        out[font] = v
    return out


def per_font_per_seed(paths_by_seed, metric):
    """{font: {seed: value}} over several per_cell.json files, one per seed."""
    out = defaultdict(dict)
    for seed, path in paths_by_seed.items():
        with open(path, encoding="utf-8") as fh:
            cells = json.load(fh)
        for font, v in font_values(cells).items():
            if metric in v:
                out[font][seed] = v[metric]
    return dict(out)


def compare(A, B, groups, keep_shared_reference=False, n_boot=None):
    """The registered comparison for one metric. Returns a plain dict."""
    fonts = sorted(set(A) & set(B))
    dropped = []
    if not keep_shared_reference:
        for f in list(fonts):
            if any(f.startswith(p) for p in EXCLUDE_SHARED_REFERENCE):
                fonts.remove(f)
                dropped.append(f)
    if not fonts:
        raise SystemExit("no shared fonts")
    seeds_a = sorted({s for f in fonts for s in A[f]})
    seeds_b = sorted({s for f in fonts for s in B[f]})
    mA = {f: float(np.mean(list(A[f].values()))) for f in fonts}
    mB = {f: float(np.mean(list(B[f].values()))) for f in fonts}
    d = {f: mB[f] - mA[f] for f in fonts}
    d_c = collapse(d, groups)
    # The arm means are reported over the SAME collapsed observations as the
    # difference, so mean_b - mean_a equals mean_diff exactly; averaging the
    # arms over the uncollapsed fonts gave columns that did not subtract
    # (review finding, 2026-09-12).
    mA_c, mB_c = collapse(mA, groups), collapse(mB, groups)
    vals = np.array(list(d_c.values()))
    p = float(stats.wilcoxon(vals, alternative="two-sided").pvalue) if len(vals) >= 10 else None
    kw = {} if n_boot is None else {"n_boot": n_boot}
    lo, hi = seed_blocked_bootstrap(A, B, d_c, seeds_a, seeds_b, **kw)
    return {"n_fonts": len(fonts), "n_unique": len(d_c), "dropped": dropped,
            "seeds_a": seeds_a, "seeds_b": seeds_b,
            "mean_a": float(np.mean(list(mA_c.values()))),
            "mean_b": float(np.mean(list(mB_c.values()))),
            "mean_diff": float(vals.mean()), "median_diff": float(np.median(vals)),
            "wilcoxon_p": p, "ci95": [float(lo), float(hi)],
            "excludes_zero": bool(lo > 0 or hi < 0)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", default=RUN_PATTERN,
                    help="per-seed eval directory pattern with {arm} and {seed}")
    ap.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    ap.add_argument("--atlas-dir", default="eval_holdout/atlases")
    ap.add_argument("--out", default=OUT_JSON)
    ap.add_argument("--keep-shared-reference", action="store_true")
    args = ap.parse_args(argv)

    paths = {}
    for arm in ARMS:
        paths[arm] = {}
        for s in args.seeds:
            p = os.path.join(args.runs.format(arm=arm, seed=s), "per_cell.json")
            if not os.path.isfile(p):
                raise SystemExit(f"missing {p}; run runners/run_rescore_multiseed.sh first")
            paths[arm][s] = p
    groups = duplicate_groups(args.atlas_dir)

    results = {}
    print(f"{'metric':<10} {'4B':>8} {'9B':>8} {'9B-4B':>9} {'95% CI (fonts+seeds)':>24} "
          f"{'Wilcoxon p':>11}  n")
    for metric in METRICS:
        A = per_font_per_seed(paths["4b"], metric)
        B = per_font_per_seed(paths["9b"], metric)
        r = compare(A, B, groups, args.keep_shared_reference)
        results[metric] = r
        lo, hi = r["ci95"]
        pv = "n/a" if r["wilcoxon_p"] is None else f"{r['wilcoxon_p']:.4g}"
        print(f"{metric:<10} {r['mean_a']:>8.4f} {r['mean_b']:>8.4f} {r['mean_diff']:>+9.4f} "
              f"[{lo:+.4f}, {hi:+.4f}] {'excl' if r['excludes_zero'] else 'incl':>5} "
              f"{pv:>11}  {r['n_unique']}")
    print("\nESTIMAND REMINDER: two checkpoints, one training seed each -- inference seeds"
          "\ncannot separate architecture from training luck (CLAUDE.md).")

    payload = {"_comment": "Generated by analysis/multiseed_rescore.py from eval_checkpoint "
                           "re-scores of the six-seed candidate sets (issue #12). Same estimand "
                           "and statistic as analysis/multiseed_compare.py.",
               "runs": args.runs, "seeds": args.seeds, "metrics": results}
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
