"""Every headline claim, on EVERY metric, against that metric's training noise.

WHY THIS EXISTS. `research/2026-08-13-training-run-variance-measured-at-last.md`
tabulated each claim against only the ONE metric it had originally been reported
on, and concluded "Nothing reaches 2 SE". That was wrong twice over: the licence
filter is 2.16 SE on composite, and the dinov2 row divided a dinov2 effect by
char_acc's standard deviation. A ledger that shows every claim on every metric
makes both mistakes impossible to repeat.

HOW TO READ IT. Divide an effect by ITS OWN metric's training-run SD
(`research/training_variance_<metric>.json`). Composite is ~20x more stable than
char_acc, so the same underlying change can be resolvable on one and invisible
on the other. That is a fact about the instruments, not about the change.

WHAT xSE DOES AND DOES NOT MEAN. sigma is estimated from 3 runs (2 df) and its
own 95% CI is ~12x wide. xSE therefore RANKS effects and establishes none.
Treating 2.0 as a significance threshold here would be false precision.

Nearly every row is a comparison of two SINGLE TRAINING RUNS, so its true
uncertainty is the training-run SD -- not the eval's bootstrap CI, and not the
inference-seed SE.

  python analysis/claim_ledger.py
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
import math
import os

import numpy as np

METRICS = ("composite", "char_acc", "dinov2", "racc", "lpips")
LOWER_BETTER = {"lpips"}
EXCLUDE = ("BitcountGridDoubleInk", "BitcountPropDoubleInk")

# (label, arm_A, arm_B, note). Effect is B - A, in QUALITY space.
# "3v1" marks the licence filter, whose clean arm has three replicate runs.
CLAIMS = [
    ("glyph vs baseline LoRA",  "structured_prompt_5000", "prompt_trained_short", "1v1"),
    ("4B -> 9B",                "glyph_4b_r32_5000",      "glyph_r32_5000",       "1v1"),
    ("rank 64",                 "glyph_4b_r32_5000",      "glyph_4b_r64_5000",    "1v1"),
    ("oversampling",            "glyph_4b_r32_5000",      "glyph_4b_distinct_5000", "1v1"),
    ("rank64 + oversampling",   "glyph_4b_r32_5000",      "glyph_4b_r64_distinct_5000", "1v1"),
    ("corpus expansion v3",     "glyph_4b_r32_5000",      "glyph_4b_v3_5000",     "1v1"),
    ("LR-horizon fix",          "glyph_4b_r32_5000",      "glyph_4b_r32_5000_lrfix", "1v1"),
    ("licence filter (838)",    "lrfix_ckpt4500",         "CLEAN3",               "3v1"),
    ("non-oracle ref (photo)",  "glyph_4b_r32_5000_lrfix", "nonoracle_photo",     "same-ckpt"),
]
CLEAN3 = ["glyph_4b_r32_clean", "glyph_4b_r32_clean_s43", "glyph_4b_r32_clean_s44"]


def per_font(run, metric):
    p = os.path.join("eval_runs", run, "scores.json")
    d = json.load(open(p, encoding="utf-8"))
    return {f["name"]: f[metric] for f in d["per_font"] if metric in f}


def training_sd(metric):
    p = f"research/training_variance_{metric}.json"
    if not os.path.isfile(p):
        return None
    return json.load(open(p, encoding="utf-8"))["run_mean_sd"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="research/claim_ledger.json")
    args = ap.parse_args(argv)

    SD = {m: training_sd(m) for m in METRICS}
    print("training-run SD (3 runs, 2 df, ~12x-wide CI on each):")
    print("  " + "  ".join(f"{m} {SD[m]:.4f}" for m in METRICS if SD[m]))
    print()

    rows = []
    for label, a, b, kind in CLAIMS:
        row = {"claim": label, "arm_a": a, "arm_b": b, "kind": kind, "metrics": {}}
        for m in METRICS:
            try:
                A = per_font(a, m)
                B = ([per_font(r, m) for r in CLEAN3] if b == "CLEAN3"
                     else [per_font(b, m)])
            except (FileNotFoundError, KeyError):
                continue
            common = sorted(set(A) & set.intersection(*(set(x) for x in B)))
            common = [f for f in common if not f.startswith(EXCLUDE)]
            if len(common) < 10:
                continue
            va = np.array([A[f] for f in common])
            vb = np.mean([[x[f] for f in common] for x in B], axis=0)
            delta = float(vb.mean() - va.mean())
            if m in LOWER_BETTER:
                delta = -delta                       # quality space
            sd = SD.get(m)
            if not sd:
                continue
            # 1v1: two single runs. 3v1: mean of three vs one.
            # same-ckpt: ONE checkpoint re-evaluated, so training noise cancels
            # entirely and this SE does not apply -- flagged, not divided.
            if kind == "3v1":
                se = sd * math.sqrt(1 + 1 / 3)
            else:
                se = sd * math.sqrt(2)
            row["metrics"][m] = {"delta": round(delta, 4),
                                 "se": round(se, 4),
                                 "x_se": round(delta / se, 2),
                                 "n": len(common)}
        rows.append(row)

    hdr = f"{'claim':<26}" + "".join(f"{m[:9]:>19}" for m in METRICS)
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        line = f"{r['claim']:<26}"
        for m in METRICS:
            v = r["metrics"].get(m)
            line += f"{v['delta']:>+9.4f}/{v['x_se']:>+5.1f}" if v else f"{'--':>19}"
        print(line)
    print("\n  each cell: delta / xSE, in QUALITY space (lpips sign flipped)")
    print("  xSE uses THAT metric's training-run SD. Never another metric's.")
    print("  'non-oracle ref' re-evaluates ONE checkpoint, so training noise")
    print("  cancels and its xSE is not meaningful -- shown for completeness.")

    big = [(r["claim"], m, v["x_se"]) for r in rows for m, v in r["metrics"].items()
           if abs(v["x_se"]) >= 2 and r["kind"] != "same-ckpt"]
    print(f"\nEffects reaching 2 xSE on any metric: {len(big)}")
    for c, m, x in sorted(big, key=lambda t: -abs(t[2])):
        print(f"  {x:+6.2f}  {c}  ({m})")
    if not big:
        print("  (none)")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"_comment": "Every claim on every metric, each against its OWN "
                               "metric's training-run SD. sigma is 2 df with a "
                               "~12x CI: xSE ranks, it does not establish.",
                   "training_sd": SD, "claims": rows}, f, indent=1)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
