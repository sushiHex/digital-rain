"""hybrid_replay.py -- realizable (no-GT) OCR-swap hybrid replay + accounting.

Task 2 (free forensics). Two generators -- baseline (structured_prompt_5000)
and glyph-cond (glyph_r32_5000) -- were each evaluated on the same 50-font
holdout, giving one per_cell.json record per (font, char) cell for each model.
An *oracle* hybrid (picks whichever model's cell has char_acc_match==1, using
DINOv2 template-match GT knowledge) reaches char_acc = 0.7711. That oracle is
unrealizable at inference time because char_acc_match is computed from GT
atlas embeddings.

This script builds the REALIZABLE version: a swap rule that only looks at
what TrOCR reads off the GENERATED cell (racc_gen_decoded) -- something you
have without any ground-truth image -- and asks whether it reads back as the
expected character.

===========================================================================
METRIC DISCIPLINE (binding, see task-2 brief):
  - `char_acc` / `char_acc_match` = DINOv2 template-match. This is the
    RESEARCH metric. It requires GT atlas embeddings, so it is used ONLY for
    accounting (measuring how well the no-GT rule tracks the oracle split),
    NEVER inside the selector itself.
  - `racc_gen_decoded` = TrOCR's decode of the GENERATED cell. This is the
    ONLY per-cell field the swap rule may consult, compared against the
    already-known "expected char" (the layout tells us what character was
    supposed to be drawn at that grid position -- that's metadata, not a
    ground-truth pixel comparison).
  - `racc_gt_decoded` = TrOCR's decode of the GROUND-TRUTH cell. This field
    is GT-derived. It appears ONLY in Step-1 capture-rate accounting (to
    show how the no-GT rule's picture compares to the racc_match field,
    which itself is gt_decoded == gen_decoded). It MUST NEVER be read inside
    swap_rule() or racc_correct() below.
  - TrOCR is case-insensitive on this holdout font set -- all char
    comparisons below are done case-insensitively (.strip().lower()).
===========================================================================

Usage:
  python studies/hybrid_replay.py --step accounting
  python studies/hybrid_replay.py --step composite
  python studies/hybrid_replay.py --step all          # default
"""

# repo root on sys.path so `python studies/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from atlas_constants import CHARSET, DRAWN_INDICES, GRID_COLS, CELL_W, CELL_H
# Canonical cell cropper -- imported, not reimplemented. Its geometry (row =
# idx // GRID_COLS, col = idx % GRID_COLS, fixed CELL_W/CELL_H) is mirrored
# below ONLY for the inverse operation (pasting a crop back), using the same
# imported constants -- no competing geometry is defined.
from eval_checkpoint import crop_cell

BASELINE_RUN = Path("eval_runs/structured_prompt_5000")
GLYPH_RUN = Path("eval_runs/glyph_r32_5000")
OUT_RUN = Path("eval_runs/hybrid_replay")
HOLDOUT_DIR = Path("eval_holdout")

BASELINE_LABEL = "baseline (structured_prompt_5000)"
GLYPH_LABEL = "glyph-cond (glyph_r32_5000)"

# Known facts (from the oracle hybrid, computed with GT char_acc_match) that
# this script's accounting should reproduce exactly as a self-check.
EXPECTED_ORACLE = {"both_ok": 2730, "only_base": 408, "only_glyph": 486, "both_fail": 1076}
EXPECTED_ORACLE_CHAR_ACC = 0.7711

# Symbols TrOCR is documented-blind on: backslash, quote marks, and the O/0
# confusable pair. Used only for honest accounting, never for the rule.
TROCR_BLIND_CHARS = {"\\", "'", '"', "O", "0"}


# ===========================================================================
# I/O + join
# ===========================================================================

def load_per_cell(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def join_records(base_records: list[dict], glyph_records: list[dict]) -> dict:
    """Join two per_cell.json lists on (font, char). Returns
    {(font, char): (base_rec, glyph_rec)} for keys present in BOTH."""
    base_by_key = {(r["font"], r["char"]): r for r in base_records}
    glyph_by_key = {(r["font"], r["char"]): r for r in glyph_records}
    shared = set(base_by_key) & set(glyph_by_key)
    missing_in_glyph = set(base_by_key) - set(glyph_by_key)
    missing_in_base = set(glyph_by_key) - set(base_by_key)
    if missing_in_glyph or missing_in_base:
        print(f"WARN: {len(missing_in_base)} keys only in glyph run, "
              f"{len(missing_in_glyph)} keys only in baseline run (excluded from join)")
    return {k: (base_by_key[k], glyph_by_key[k]) for k in shared}


# ===========================================================================
# The no-GT swap rule
# ===========================================================================

def racc_correct(rec: dict, char: str) -> bool:
    """No-GT correctness check: does TrOCR's decode of the cell THIS MODEL
    GENERATED match the expected character? Case-insensitive.

    Uses ONLY rec["racc_gen_decoded"] -- never rec["racc_gt_decoded"]. The
    "expected" char comes from the atlas layout (metadata: what character we
    asked to be drawn at this grid position), not from a GT pixel render.
    """
    return rec["racc_gen_decoded"].strip().lower() == char.strip().lower()


def swap_rule(base_rec: dict, glyph_rec: dict, char: str) -> bool:
    """The binding no-GT OCR-swap rule (task-2 brief):

    Take the glyph model's cell iff the baseline's OWN generated cell fails
    to read back as the expected character, AND the glyph model's OWN
    generated cell succeeds. Both checks route through racc_correct(), i.e.
    only racc_gen_decoded is consulted -- no ground-truth field.
    """
    return (not racc_correct(base_rec, char)) and racc_correct(glyph_rec, char)


# ===========================================================================
# Step 1: CPU accounting
# ===========================================================================

def step1_accounting(joined: dict) -> dict:
    """Emit (a) racc_match-vs-char_acc_match agreement matrices, (b) the no-GT
    rule's capture rate against both the char_acc-space oracle split and a
    racc-native complementarity split, (c) a TrOCR-blind symbol table, and
    (d) the both-fail ceiling statement. Returns a dict summary for the
    research note / JSON dump.
    """
    print("=" * 78)
    print("STEP 1: CPU ACCOUNTING")
    print("=" * 78)

    n = len(joined)
    print(f"\nJoined {n} (font, char) cells.\n")

    # ---- (a) racc_match vs char_acc_match agreement matrix, per model -----
    print("-" * 78)
    print("(a) racc_match vs char_acc_match agreement (per model)")
    print("    racc_match = TrOCR(gt_decoded) == TrOCR(gen_decoded)  [GT-consistency]")
    print("    char_acc_match = DINOv2 template-match against own-font GT embeddings")
    print("-" * 78)

    agreement = {}
    for label, idx in ((BASELINE_LABEL, 0), (GLYPH_LABEL, 1)):
        tt = tf = ft = ff = 0
        for base_rec, glyph_rec in joined.values():
            rec = base_rec if idx == 0 else glyph_rec
            r = bool(rec["racc_match"])
            c = bool(rec["char_acc_match"])
            if r and c:
                tt += 1
            elif r and not c:
                tf += 1
            elif not r and c:
                ft += 1
            else:
                ff += 1
        agree_pct = (tt + ff) / n * 100
        print(f"\n  {label}:")
        print(f"    racc_match=T, char_acc=T (both agree correct):   {tt:5d}")
        print(f"    racc_match=T, char_acc=F (racc false-positive):  {tf:5d}")
        print(f"    racc_match=F, char_acc=T (racc false-negative):  {ft:5d}")
        print(f"    racc_match=F, char_acc=F (both agree wrong):     {ff:5d}")
        print(f"    agreement rate: {agree_pct:.1f}%")
        agreement[label] = {"TT": tt, "TF": tf, "FT": ft, "FF": ff, "agree_pct": agree_pct}

    # ---- oracle split (char_acc_match space) — self-check vs known facts --
    both_ok = only_base = only_glyph = both_fail = 0
    only_glyph_keys = []
    only_base_keys = []
    for key, (base_rec, glyph_rec) in joined.items():
        b = bool(base_rec["char_acc_match"])
        g = bool(glyph_rec["char_acc_match"])
        if b and g:
            both_ok += 1
        elif b and not g:
            only_base += 1
            only_base_keys.append(key)
        elif g and not b:
            only_glyph += 1
            only_glyph_keys.append(key)
        else:
            both_fail += 1

    print("\n" + "-" * 78)
    print("Oracle split (char_acc_match space) -- self-check vs known facts")
    print("-" * 78)
    print(f"  both_ok={both_ok}  only_base={only_base}  only_glyph={only_glyph}  both_fail={both_fail}")
    oracle_char_acc = (both_ok + only_base + only_glyph) / n
    print(f"  oracle char_acc = {oracle_char_acc:.4f}  (expected {EXPECTED_ORACLE_CHAR_ACC})")
    matches_known_facts = (
        both_ok == EXPECTED_ORACLE["both_ok"]
        and only_base == EXPECTED_ORACLE["only_base"]
        and only_glyph == EXPECTED_ORACLE["only_glyph"]
        and both_fail == EXPECTED_ORACLE["both_fail"]
    )
    print(f"  matches known facts (2730/408/486/1076): {matches_known_facts}")
    if not matches_known_facts:
        print("  *** MISMATCH -- investigate before trusting downstream numbers ***")

    # ---- (b-i) capture rate against the char_acc-space oracle split -------
    print("\n" + "-" * 78)
    print("(b-i) No-GT rule's capture rate, measured in CHAR_ACC (DINOv2) space")
    print("-" * 78)
    captured = sum(1 for (font, char) in only_glyph_keys
                   if swap_rule(joined[(font, char)][0], joined[(font, char)][1], char))
    wrongly_swapped = sum(1 for (font, char) in only_base_keys
                          if swap_rule(joined[(font, char)][0], joined[(font, char)][1], char))
    capture_rate = captured / len(only_glyph_keys) if only_glyph_keys else 0.0
    false_swap_rate = wrongly_swapped / len(only_base_keys) if only_base_keys else 0.0
    print(f"  of {len(only_glyph_keys)} only-glyph cells (glyph right, baseline wrong per DINOv2):")
    print(f"    rule captures (correctly swaps): {captured}  ({capture_rate*100:.1f}%)")
    print(f"  of {len(only_base_keys)} only-baseline cells (baseline right, glyph wrong per DINOv2):")
    print(f"    rule wrongly swaps away the good baseline cell: {wrongly_swapped}  ({false_swap_rate*100:.1f}%)")

    # ---- (b-ii) racc-native complementarity split + capture rate ----------
    print("\n" + "-" * 78)
    print("(b-ii) Racc-native complementarity split (racc_correct(gen) vs expected char)")
    print("       -- the space the rule actually operates in; capture should be ~100%/0% by construction")
    print("-" * 78)
    both_ok_r = only_base_r = only_glyph_r = both_fail_r = 0
    only_glyph_r_keys = []
    only_base_r_keys = []
    for key, (base_rec, glyph_rec) in joined.items():
        font, char = key
        b = racc_correct(base_rec, char)
        g = racc_correct(glyph_rec, char)
        if b and g:
            both_ok_r += 1
        elif b and not g:
            only_base_r += 1
            only_base_r_keys.append(key)
        elif g and not b:
            only_glyph_r += 1
            only_glyph_r_keys.append(key)
        else:
            both_fail_r += 1
    print(f"  both_ok={both_ok_r}  only_base={only_base_r}  only_glyph={only_glyph_r}  both_fail={both_fail_r}")
    captured_r = sum(1 for k in only_glyph_r_keys if swap_rule(joined[k][0], joined[k][1], k[1]))
    false_r = sum(1 for k in only_base_r_keys if swap_rule(joined[k][0], joined[k][1], k[1]))
    print(f"  rule captures {captured_r}/{len(only_glyph_r_keys)} racc-only-glyph cells "
          f"({captured_r/len(only_glyph_r_keys)*100 if only_glyph_r_keys else 0:.1f}%, tautological check)")
    print(f"  rule wrongly swaps {false_r}/{len(only_base_r_keys)} racc-only-baseline cells "
          f"({false_r/len(only_base_r_keys)*100 if only_base_r_keys else 0:.1f}%, tautological check)")

    # cross-tab: how much does the racc-native split overlap the char_acc split?
    print("\n  Cross-tab: racc-space only-glyph cells that are ALSO char_acc-space only-glyph:")
    overlap_glyph = len(set(only_glyph_r_keys) & set(only_glyph_keys))
    print(f"    {overlap_glyph} / {len(only_glyph_r_keys)} racc-only-glyph cells "
          f"({overlap_glyph/len(only_glyph_r_keys)*100 if only_glyph_r_keys else 0:.1f}%) "
          f"also verified good by DINOv2 char_acc")
    overlap_base = len(set(only_base_r_keys) & set(only_base_keys))
    print(f"    {overlap_base} / {len(only_base_r_keys)} racc-only-baseline cells "
          f"({overlap_base/len(only_base_r_keys)*100 if only_base_r_keys else 0:.1f}%) "
          f"also verified good-baseline by DINOv2 char_acc")

    # ---- predicted char_acc delta: classify EVERY rule-fired swap by its
    # char_acc-space effect (helpful / harmful / neutral). This is the
    # cheapest possible forecast of Step 3's scored outcome.
    all_swapped_keys = [k for k in joined if swap_rule(joined[k][0], joined[k][1], k[1])]
    helpful = harmful = neutral = 0
    for k in all_swapped_keys:
        base_rec, glyph_rec = joined[k]
        b, g = bool(base_rec["char_acc_match"]), bool(glyph_rec["char_acc_match"])
        if not b and g:
            helpful += 1
        elif b and not g:
            harmful += 1
        else:
            neutral += 1
    print(f"\n  Forecast: of {len(all_swapped_keys)} total rule-fired swaps -- "
          f"{helpful} helpful (+char_acc), {harmful} harmful (-char_acc), {neutral} neutral")
    predicted_delta = (helpful - harmful) / n
    print(f"  Predicted char_acc delta vs baseline: {predicted_delta:+.4f} "
          f"(baseline char_acc + this ~= hybrid char_acc; verify against Step 3's real score)")

    # ---- (c) TrOCR-blind symbol table --------------------------------------
    print("\n" + "-" * 78)
    print("(c) TrOCR-blind symbol accounting: \\, ', \", O, 0")
    print("    (honest accounting -- these chars make racc_correct unreliable "
          "regardless of true glyph quality)")
    print("-" * 78)
    print(f"  {'char':<6} {'n':>4}  {'base racc_ok':>13}  {'glyph racc_ok':>14}  "
          f"{'base char_acc':>14}  {'glyph char_acc':>15}")
    blind_table = {}
    for ch in sorted(TROCR_BLIND_CHARS):
        keys = [k for k in joined if k[1] == ch]
        if not keys:
            continue
        base_racc_ok = sum(racc_correct(joined[k][0], ch) for k in keys) / len(keys)
        glyph_racc_ok = sum(racc_correct(joined[k][1], ch) for k in keys) / len(keys)
        base_char_acc = sum(bool(joined[k][0]["char_acc_match"]) for k in keys) / len(keys)
        glyph_char_acc = sum(bool(joined[k][1]["char_acc_match"]) for k in keys) / len(keys)
        print(f"  {ch!r:<6} {len(keys):>4}  {base_racc_ok:>13.2f}  {glyph_racc_ok:>14.2f}  "
              f"{base_char_acc:>14.2f}  {glyph_char_acc:>15.2f}")
        blind_table[ch] = {
            "n": len(keys), "base_racc_ok": base_racc_ok, "glyph_racc_ok": glyph_racc_ok,
            "base_char_acc": base_char_acc, "glyph_char_acc": glyph_char_acc,
        }
    print("\n  Low racc_ok despite non-trivial char_acc on these rows = TrOCR misreads the "
          "SYMBOL itself (not a generation defect) -- the no-GT rule can neither confirm nor "
          "rescue these cells reliably; treat swap decisions on these chars with caution.")

    # ---- (d) both-fail ceiling ----------------------------------------------
    print("\n" + "-" * 78)
    print("(d) Both-fail ceiling")
    print("-" * 78)
    print(f"  both_fail = {both_fail} cells ({both_fail/n*100:.1f}% of {n}) -- neither model "
          f"produced a DINOv2-correct glyph. No 2-candidate selector (oracle or realized) can "
          f"rescue these; they set the hard ceiling on ANY hybrid built from just these two runs.")

    return {
        "n_joined": n,
        "agreement": agreement,
        "oracle_split_char_acc": {"both_ok": both_ok, "only_base": only_base,
                                   "only_glyph": only_glyph, "both_fail": both_fail,
                                   "matches_known_facts": matches_known_facts,
                                   "oracle_char_acc": oracle_char_acc},
        "capture_char_acc_space": {"captured": captured, "of": len(only_glyph_keys),
                                    "capture_rate": capture_rate,
                                    "wrongly_swapped": wrongly_swapped, "of_base": len(only_base_keys),
                                    "false_swap_rate": false_swap_rate},
        "racc_native_split": {"both_ok": both_ok_r, "only_base": only_base_r,
                               "only_glyph": only_glyph_r, "both_fail": both_fail_r},
        "trocr_blind_table": blind_table,
        "both_fail_ceiling_pct": both_fail / n * 100,
        "swap_forecast": {"total_swaps": len(all_swapped_keys), "helpful": helpful,
                          "harmful": harmful, "neutral": neutral,
                          "predicted_char_acc_delta": predicted_delta},
    }


# ===========================================================================
# Step 2: composite real hybrid atlases
# ===========================================================================

def composite_font(font_name: str, joined: dict, base_gen_dir: Path,
                    glyph_gen_dir: Path, out_gen_dir: Path) -> int:
    """Build one hybrid atlas: start from a copy of the baseline atlas, paste
    in glyph-model cells wherever swap_rule() fires. Returns the swap count.
    """
    base_path = base_gen_dir / f"{font_name}.png"
    glyph_path = glyph_gen_dir / f"{font_name}.png"

    base_img = Image.open(base_path).convert("RGB")
    base_np = np.array(base_img)
    out_np = base_np.copy()

    swap_count = 0
    if glyph_path.exists():
        glyph_np = np.array(Image.open(glyph_path).convert("RGB"))
        for idx in DRAWN_INDICES:
            char = CHARSET[idx]
            key = (font_name, char)
            if key not in joined:
                continue  # cell missing from one of the per_cell.json files
            base_rec, glyph_rec = joined[key]
            if swap_rule(base_rec, glyph_rec, char):
                cell = crop_cell(glyph_np, idx)
                row, col = idx // GRID_COLS, idx % GRID_COLS
                y0, x0 = row * CELL_H, col * CELL_W
                out_np[y0:y0 + CELL_H, x0:x0 + CELL_W] = cell
                swap_count += 1
    else:
        print(f"  WARN: {glyph_path} missing -- {font_name} written as a straight baseline copy")

    out_gen_dir.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out_np).save(out_gen_dir / f"{font_name}.png")
    return swap_count


def step2_composite(joined: dict, holdout_dir: Path = HOLDOUT_DIR,
                     base_run: Path = BASELINE_RUN, glyph_run: Path = GLYPH_RUN,
                     out_run: Path = OUT_RUN) -> dict:
    """Composite hybrid atlases for ALL 50 holdout fonts. Fonts with zero
    swaps are still written (identical to the baseline copy) so downstream
    scoring covers the full holdout.

    NOTE: pool is n=1/model here -- this tests the OCR-swap RULE only. The
    consensus-medoid mechanism (majority vote / centroid pick across >=3
    candidates) is vacuous at n=2 and is explicitly NOT being tested.
    """
    print("=" * 78)
    print("STEP 2: COMPOSITE HYBRID ATLASES")
    print("=" * 78)
    print("(pool is n=1/model -- tests the OCR-swap rule only; consensus-medoid "
          "is vacuous at n=2 and not exercised here)\n")

    with open(holdout_dir / "manifest.json", encoding="utf-8") as f:
        manifest = json.load(f)
    font_names = [entry["name"] for entry in manifest["fonts"]]

    base_gen_dir = base_run / "generated"
    glyph_gen_dir = glyph_run / "generated"
    out_gen_dir = out_run / "generated"

    swap_counts = {}
    for name in font_names:
        swap_counts[name] = composite_font(name, joined, base_gen_dir, glyph_gen_dir, out_gen_dir)
        print(f"  {name:<40s} swaps={swap_counts[name]:>3d}")

    total_swaps = sum(swap_counts.values())
    fonts_with_swaps = sum(1 for v in swap_counts.values() if v > 0)
    max_font, max_swaps = max(swap_counts.items(), key=lambda kv: kv[1])
    print(f"\n  Total swaps: {total_swaps} across {fonts_with_swaps}/{len(font_names)} fonts")
    print(f"  Max swaps in one font: {max_font} = {max_swaps}")
    high_mixing = {k: v for k, v in swap_counts.items() if v >= 40}
    if high_mixing:
        print(f"  HIGH MIXING RISK (>=40 swapped cells, ransom-note candidates): {high_mixing}")
    else:
        print("  No font has >=40 swapped cells (no high-mixing-risk fonts by this proxy).")
    print(f"\n  Wrote {len(font_names)} atlases to {out_gen_dir}/")

    return {"swap_counts": swap_counts, "total_swaps": total_swaps,
            "fonts_with_swaps": fonts_with_swaps, "max_font": max_font, "max_swaps": max_swaps}


# ===========================================================================
# main
# ===========================================================================

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", choices=["accounting", "composite", "all"], default="all")
    ap.add_argument("--base-run", default=str(BASELINE_RUN))
    ap.add_argument("--glyph-run", default=str(GLYPH_RUN))
    ap.add_argument("--out-run", default=str(OUT_RUN))
    ap.add_argument("--holdout", default=str(HOLDOUT_DIR))
    ap.add_argument("--dump-json", default=None,
                    help="optional path to dump the accounting + swap summary as JSON")
    args = ap.parse_args()

    base_run = Path(args.base_run)
    glyph_run = Path(args.glyph_run)
    out_run = Path(args.out_run)
    holdout_dir = Path(args.holdout)

    base_records = load_per_cell(base_run / "per_cell.json")
    glyph_records = load_per_cell(glyph_run / "per_cell.json")
    joined = join_records(base_records, glyph_records)

    summary = {}
    if args.step in ("accounting", "all"):
        summary["accounting"] = step1_accounting(joined)
    if args.step in ("composite", "all"):
        summary["composite"] = step2_composite(joined, holdout_dir, base_run, glyph_run, out_run)

    if args.dump_json:
        dump_path = Path(args.dump_json)
        dump_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dump_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"\nSummary dumped to {dump_path}")


if __name__ == "__main__":
    main()
