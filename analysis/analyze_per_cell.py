"""Per-cell failure heatmap analysis.

Loads per_cell.json from baseline, v5, and structured_prompt_5000 runs.
Identifies whether failures are character-concentrated, font-concentrated,
or random — to decide between targeted fixes vs architectural pivot.

Usage:
  python analysis/analyze_per_cell.py [per_cell.json] [--label X]

With no positional argument, defaults to the structured_prompt_5000 run
(legacy behavior) and also runs the baseline/v5/structured comparison
sections below. With a positional path, the primary per-char/per-font
failure analysis runs on that file instead.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


RUNS = {
    "baseline": "eval_runs/baseline_checkpoint-3500/per_cell.json",
    "v5": "eval_runs/v5_checkpoint-3500/per_cell.json",
    "structured": "eval_runs/structured_prompt_5000/per_cell.json",
}

DEFAULT_PRIMARY = RUNS["structured"]


def load(path):
    with open(path) as f:
        return json.load(f)


def per_char_failure_rate(records, metric="char_acc_match"):
    """For each character, what fraction of fonts get it WRONG?"""
    by_char = defaultdict(list)
    for r in records:
        by_char[r["char"]].append(r[metric])
    return {ch: 1.0 - np.mean(v) for ch, v in by_char.items()}


def per_font_failure_rate(records, metric="char_acc_match"):
    """For each font, what fraction of chars are wrong?"""
    by_font = defaultdict(list)
    for r in records:
        by_font[r["font"]].append(r[metric])
    return {f: 1.0 - np.mean(v) for f, v in by_font.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("per_cell", nargs="?", default=DEFAULT_PRIMARY,
                        help="Path to the per_cell.json to run the primary "
                             "per-char/per-font analysis on "
                             "(default: structured_prompt_5000 run)")
    parser.add_argument("--label", default=None,
                        help="Label for the primary run in output "
                             "(default: derived from the path's parent dir)")
    args = parser.parse_args()

    primary_label = args.label or Path(args.per_cell).parent.name
    primary = load(args.per_cell)

    # Baseline/v5/structured comparison data below is intentionally hardcoded
    # to these three fixed runs (see RUNS above) regardless of args.per_cell.
    data = {name: load(path) for name, path in RUNS.items()}

    print("=" * 70)
    print("PER-CELL FAILURE HEATMAP ANALYSIS")
    print("=" * 70)
    print()

    print(f"Primary analysis: {primary_label} ({len(primary)} cells)")
    print()

    # ---- CHARACTER CONCENTRATION ----
    char_failure = per_char_failure_rate(primary)
    char_failure_sorted = sorted(char_failure.items(), key=lambda x: -x[1])

    print(f"CHARACTER FAILURE RATES ({primary_label} run, all 50 fonts)")
    print(f"{'Char':>6} {'Fail%':>8} {'Cat':>14}")
    print("-" * 32)

    # Get categories from one record
    by_char_cat = {r["char"]: r["category"] for r in primary}

    print("Worst 20 characters (most fonts get them wrong):")
    for ch, rate in char_failure_sorted[:20]:
        print(f"{repr(ch):>6} {rate*100:>7.1f}% {by_char_cat.get(ch, '?'):>14}")

    print()
    print("Best 20 characters (most fonts get them right):")
    for ch, rate in char_failure_sorted[-20:]:
        print(f"{repr(ch):>6} {rate*100:>7.1f}% {by_char_cat.get(ch, '?'):>14}")

    # Concentration analysis
    char_fail_arr = np.array([r for _, r in char_failure_sorted])
    total_failures = char_fail_arr.sum()
    cumulative = np.cumsum(char_fail_arr) / total_failures
    pct_chars_for_50 = (cumulative < 0.5).sum() + 1
    pct_chars_for_80 = (cumulative < 0.8).sum() + 1
    print()
    print(f"Concentration: {pct_chars_for_50}/{len(char_fail_arr)} chars cause 50% of failures")
    print(f"               {pct_chars_for_80}/{len(char_fail_arr)} chars cause 80% of failures")

    # ---- FONT CONCENTRATION ----
    font_failure = per_font_failure_rate(primary)
    font_failure_sorted = sorted(font_failure.items(), key=lambda x: -x[1])

    print()
    print("=" * 70)
    print("FONT FAILURE RATES")
    print("-" * 32)
    print("Worst 10 fonts (highest char-acc failure rate):")
    for f, rate in font_failure_sorted[:10]:
        print(f"  {rate*100:>6.1f}%  {f}")
    print("Best 10 fonts (lowest char-acc failure rate):")
    for f, rate in font_failure_sorted[-10:]:
        print(f"  {rate*100:>6.1f}%  {f}")

    font_fail_arr = np.array([r for _, r in font_failure_sorted])
    total_font_fails = font_fail_arr.sum()
    cumulative_f = np.cumsum(font_fail_arr) / total_font_fails
    pct_fonts_for_50 = (cumulative_f < 0.5).sum() + 1
    pct_fonts_for_80 = (cumulative_f < 0.8).sum() + 1
    print()
    print(f"Concentration: {pct_fonts_for_50}/{len(font_fail_arr)} fonts cause 50% of failures")
    print(f"               {pct_fonts_for_80}/{len(font_fail_arr)} fonts cause 80% of failures")

    # ---- INTERACTION: chars × fonts ----
    print()
    print("=" * 70)
    print("CHAR x FONT INTERACTION")
    # Build matrix
    fonts = sorted(set(r["font"] for r in primary))
    chars = sorted(set(r["char"] for r in primary))
    matrix = np.zeros((len(fonts), len(chars)), dtype=int)
    font_idx = {f: i for i, f in enumerate(fonts)}
    char_idx = {c: i for i, c in enumerate(chars)}
    for r in primary:
        if not r["char_acc_match"]:
            matrix[font_idx[r["font"]], char_idx[r["char"]]] = 1

    n_fail = int(matrix.sum())
    expected_random = n_fail / matrix.size  # uniform random rate
    actual_concentration = (matrix.sum(axis=0) > 0).sum() / matrix.shape[1]
    print(f"Total failure cells: {n_fail} of {matrix.size} ({n_fail/matrix.size*100:.1f}%)")
    print(f"Chars with at least one failure: {(matrix.sum(axis=0) > 0).sum()}/{matrix.shape[1]} ({actual_concentration*100:.0f}%)")
    print(f"Fonts with at least one failure: {(matrix.sum(axis=1) > 0).sum()}/{matrix.shape[0]}")

    # Diagnosis
    print()
    print("=" * 70)
    print("DIAGNOSIS")
    print("=" * 70)
    if pct_chars_for_50 <= 15:
        print(f"-> CHAR-CONCENTRATED: {pct_chars_for_50} chars cause 50% of failures")
        print("   Fix: oversample these chars in next training, or add char-specific")
        print("   conditioning. The model has CHARACTER-LEVEL gaps.")
    elif pct_fonts_for_50 <= 8:
        print(f"-> FONT-CONCENTRATED: {pct_fonts_for_50} fonts cause 50% of failures")
        print("   Fix: better reference images, or remove these font types from holdout.")
        print("   The model has FONT-DISTRIBUTION gaps.")
    else:
        print("-> DIFFUSE: failures spread across many chars and fonts")
        print("   The model has a fundamental ceiling. Architectural change needed")
        print("   (D-DPO, Glyph-ByT5, or different base model).")

    # ---- COMPARE STRUCTURED vs BASELINE ----
    print()
    print("=" * 70)
    print("STRUCTURED PROMPT vs BASELINE -- what changed per character?")
    print("=" * 70)
    base = data["baseline"]
    base_char = per_char_failure_rate(base)
    deltas = []
    for ch in chars:
        b_rate = base_char.get(ch, 0)
        s_rate = char_failure.get(ch, 0)
        deltas.append((ch, b_rate, s_rate, s_rate - b_rate))

    # Sort by delta — most improved at top
    deltas_improved = sorted([d for d in deltas if d[3] < 0], key=lambda x: x[3])
    deltas_regressed = sorted([d for d in deltas if d[3] > 0], key=lambda x: -x[3])

    print(f"\nMost IMPROVED chars (structured prompt fixed them):")
    for ch, b, s, d in deltas_improved[:15]:
        print(f"  {repr(ch):>6} {b*100:>6.1f}% -> {s*100:>6.1f}% ({d*100:>+6.1f}%)  [{by_char_cat.get(ch, '?')}]")

    print(f"\nMost REGRESSED chars (structured prompt made them worse):")
    for ch, b, s, d in deltas_regressed[:15]:
        print(f"  {repr(ch):>6} {b*100:>6.1f}% -> {s*100:>6.1f}% ({d*100:>+6.1f}%)  [{by_char_cat.get(ch, '?')}]")

    # ---- ALL THREE RUNS ----
    print()
    print("=" * 70)
    print("CHAR-LEVEL VIEW ACROSS ALL 3 RUNS (failure %)")
    print("=" * 70)
    base_c = per_char_failure_rate(data["baseline"])
    v5_c = per_char_failure_rate(data["v5"])
    str_c = per_char_failure_rate(data["structured"])
    rows = []
    for ch in chars:
        rows.append((ch, base_c.get(ch, 0), v5_c.get(ch, 0), str_c.get(ch, 0)))
    rows.sort(key=lambda x: -x[3])
    print(f"{'Char':>6} {'Cat':>14} {'Base%':>8} {'V5%':>8} {'Struct%':>8}")
    print("-" * 50)
    for ch, b, v, s in rows[:25]:
        print(f"{repr(ch):>6} {by_char_cat.get(ch, '?'):>14} {b*100:>7.1f}% {v*100:>7.1f}% {s*100:>7.1f}%")

    # Save full data for plotting
    out_path = Path("research/2026-04-30-per-cell-analysis.json")
    with open(out_path, "w") as f:
        json.dump({
            "concentration": {
                "chars_for_50pct_failures": int(pct_chars_for_50),
                "chars_for_80pct_failures": int(pct_chars_for_80),
                "fonts_for_50pct_failures": int(pct_fonts_for_50),
                "fonts_for_80pct_failures": int(pct_fonts_for_80),
            },
            "char_failure_rates": {ch: float(rate) for ch, rate in char_failure.items()},
            "font_failure_rates": {f: float(rate) for f, rate in font_failure.items()},
            "char_failure_3run": {ch: {"baseline": b, "v5": v, "structured": s} for ch, b, v, s in rows},
            "char_categories": by_char_cat,
        }, f, indent=2)
    print(f"\nFull analysis saved: {out_path}")


if __name__ == "__main__":
    main()
