"""hybrid_v2_replay.py -- COMBINED-OCR (TrOCR + GOT-OCR2) no-GT swap hybrid replay.

HD-Task 6b. Realizes the hybrid selector from hybrid_replay.py (HD-Task 2)
with a symbol-capable second OCR. HD-Task 2's TrOCR-only no-GT swap rule
FAILED the gate (hybrid char_acc 0.6696 < glyph-alone 0.6843) because TrOCR
is blind to brackets/quotes/O-vs-0 (captured only 21/486 = 4.3% of the
oracle-advantage cells -- see .superpowers/sdd/task-2-report.md). HD-Task 6
Step 1 (.superpowers/sdd/task-6-report.md) measured GOT-OCR2 at +0.222 on
exactly that confusable/symbol class. This script builds the COMBINED-OCR
hybrid: GOT-OCR2 for confusable/symbol cells, the already-computed stored
TrOCR decode for everything else (no re-decode, no GPU cost).

===========================================================================
DESIGN (mirrors hybrid_replay.py's structure -- see that file's docstring
for the full metric-discipline discussion; repeated here only where it
differs):

  - Two generators, one per_cell.json each (baseline structured_prompt_5000,
    glyph-cond glyph_r32_5000), joined on (font, char) via
    hybrid_replay.join_records (reused, not reimplemented).
  - "Combined decode" per (run, font, char):
      * char in CONFUSABLE_CHARS -> decode the GENERATED cell fresh with
        GOT-OCR2 (build_got_ocr_fn from hybrid_v2_ocr.py). Cached to
        eval_runs/hybrid_v2/got_decodes.json keyed by run/font/char so
        re-running the script (or extending --fonts) never re-decodes a
        cell it has already seen.
      * else -> reuse per_cell.json's own "racc_gen_decoded" (TrOCR's
        already-computed decode of that generated cell). Zero GPU cost.
  - Swap rule (no GT, case-insensitive, tolerates trailing OCR noise via
    startswith): swap baseline's cell for glyph's cell IFF the baseline's
    own combined decode does NOT read back as the expected char AND the
    glyph's own combined decode DOES. Two guards on top (see swap_rule_v2):
      1. NEVER_SWAP_CHARS ({\\, ', |, l}): both OCRs measured 0% on these
         (task-6-report.md) -- a swap decision here is indistinguishable
         from noise, so these chars always keep the baseline cell.
      2. '0' guard: GOT-OCR2 confuses 0->O (task-6-report.md: "GOT 0.50 vs
         TrOCR 1.00 -- GOT reads 0 as O"). A '0' swap additionally requires
         the STORED TrOCR racc_gen_decoded for the glyph cell to also read
         as '0', so a lone GOT hallucination can't trigger a wrong swap.
  - Compositing reuses eval_checkpoint.crop_cell for both the crop (reading
    a cell out of an atlas) and the paste (writing a cell into the hybrid
    output), exactly as hybrid_replay.composite_font does -- no competing
    geometry is defined here.
  - Accounting (per --fonts subset, using per_cell.json's char_acc_match
    DINOv2 ground truth -- never consulted by the rule itself): capture
    rate over "only-glyph-correct" cells (glyph char_acc_match=1, baseline
    char_acc_match=0) and false-swap rate over "only-baseline-correct"
    cells, printed against the full-50-font reference denominators
    (486 / 408) carried over from hybrid_replay.EXPECTED_ORACLE.
===========================================================================

Usage:
  python studies/hybrid_v2_replay.py                                   # all 50 holdout fonts
  python studies/hybrid_v2_replay.py --fonts NovaSquare,RubikDistressed-Regular   # smoke
"""

# repo root on sys.path so `python studies/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

# GOT-OCR2 emits arbitrary Unicode (box-drawing marks, PUA glyphs). Windows'
# default cp1252 stdout crashes printing those; force UTF-8 with replacement
# so a diagnostic print can never kill the (expensive) full run.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np
from PIL import Image

from atlas_constants import CHARSET, DRAWN_INDICES, GRID_COLS, CELL_W, CELL_H
# Canonical cell cropper -- imported, not reimplemented (same contract as
# hybrid_replay.py: row = idx // GRID_COLS, col = idx % GRID_COLS, fixed
# CELL_W/CELL_H). Used here for both cropping (decode) and, mirrored for the
# inverse paste, in composite_font_v2 below.
from eval_checkpoint import crop_cell
from studies.hybrid_v2_ocr import build_got_ocr_fn
# Reuse HD-Task 2's I/O + join + full-50-font reference constants instead of
# duplicating them.
from studies.hybrid_replay import load_per_cell, join_records, EXPECTED_ORACLE

BASELINE_RUN = Path("eval_runs/structured_prompt_5000")
GLYPH_RUN = Path("eval_runs/glyph_r32_5000")
OUT_RUN = Path("eval_runs/hybrid_v2")
HOLDOUT_DIR = Path("eval_holdout")

# Chars a symbol-capable OCR should decide instead of the stored TrOCR
# decode (task brief's exact list).
CONFUSABLE_CHARS = set("\\/'\"O0()[]{}<>|Il1")

# Both TrOCR AND GOT-OCR2 measured 0% on these (task-6-report.md): thin
# single-stroke glyphs aren't "text" to either OCR. A swap decision here is
# noise regardless of what either model says -- never swap, keep baseline.
NEVER_SWAP_CHARS = {"\\", "'", "|", "l"}

# GOT-OCR2 misreads 0 as O (task-6-report.md 0-regression caveat). A '0'
# swap additionally requires the stored TrOCR decode to agree.
ZERO_GUARD_CHAR = "0"


# ===========================================================================
# GOT decode cache: {run_label: {font: {char: decoded_str}}}
# ===========================================================================

def load_got_cache(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_got_cache(path: Path, cache: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, sort_keys=True)


# ===========================================================================
# Combined decode (GOT for confusable/symbol chars, stored TrOCR otherwise)
# ===========================================================================

def build_font_decodes(font: str, joined: dict, base_atlas, glyph_atlas,
                        get_ocr_fn, got_cache: dict) -> tuple[dict, int]:
    """Combined decode for every drawn cell of `font`, for both runs.

    Returns ({(run_label, font, char): decoded_str}, n_fresh_got_calls).
    `get_ocr_fn` is a zero-arg callable that lazily builds (and memoizes) the
    GOT-OCR2 model on first actual cache-miss, so a fully-cached re-run never
    touches the GPU.
    """
    decodes = {}
    got_calls = 0
    for idx in DRAWN_INDICES:
        char = CHARSET[idx]
        key = (font, char)
        if key not in joined:
            continue
        base_rec, glyph_rec = joined[key]
        for run_label, rec, atlas in (("base", base_rec, base_atlas),
                                       ("glyph", glyph_rec, glyph_atlas)):
            if char not in CONFUSABLE_CHARS:
                # Fast path: reuse TrOCR's already-computed decode of the
                # GENERATED cell. No re-decode, no GPU cost.
                decodes[(run_label, font, char)] = rec["racc_gen_decoded"]
                continue
            cached = got_cache.get(run_label, {}).get(font, {}).get(char)
            if cached is not None:
                decodes[(run_label, font, char)] = cached
                continue
            if atlas is None:
                decodes[(run_label, font, char)] = ""
                continue
            cell = crop_cell(atlas, idx)
            decoded = get_ocr_fn()(cell).strip()
            decodes[(run_label, font, char)] = decoded
            got_cache.setdefault(run_label, {}).setdefault(font, {})[char] = decoded
            got_calls += 1
    return decodes, got_calls


def print_sample_decodes(font: str, joined: dict, decodes: dict, limit: int = 6) -> None:
    """Sanity-check print: expected char / TrOCR-stored / GOT, for a handful
    of confusable/symbol cells of `font`, both runs."""
    print(f"\n  Sample symbol-cell decodes for {font} (expected / TrOCR-stored / GOT-fresh):")
    shown = 0
    for idx in DRAWN_INDICES:
        char = CHARSET[idx]
        if char not in CONFUSABLE_CHARS:
            continue
        key = (font, char)
        if key not in joined:
            continue
        base_rec, glyph_rec = joined[key]
        base_trocr = base_rec["racc_gen_decoded"]
        base_got = decodes.get(("base", font, char), "?")
        glyph_trocr = glyph_rec["racc_gen_decoded"]
        glyph_got = decodes.get(("glyph", font, char), "?")
        print(f"    char={char!r:<5} base: TrOCR={base_trocr!r:<8} GOT={base_got!r:<10} | "
              f"glyph: TrOCR={glyph_trocr!r:<8} GOT={glyph_got!r:<10}")
        shown += 1
        if shown >= limit:
            break


# ===========================================================================
# The COMBINED-OCR no-GT swap rule
# ===========================================================================

def decode_matches(decoded: str | None, char: str) -> bool:
    """Case-insensitive match, tolerating trailing OCR noise."""
    if not decoded:
        return False
    d = decoded.strip().lower()
    exp = char.strip().lower()
    return d == exp or d.startswith(exp)


def swap_rule_v2(base_rec: dict, glyph_rec: dict, char: str,
                  base_decoded: str | None, glyph_decoded: str | None) -> bool:
    """Take the glyph model's cell instead of baseline's IFF baseline's own
    combined decode misses the expected char AND glyph's own combined decode
    hits it. Guards (task brief, binding):
      - NEVER_SWAP_CHARS: always keep baseline, regardless of either decode.
      - '0': also require the STORED TrOCR decode of the glyph cell to agree
        it's correct (GOT alone confuses 0->O).
    """
    if char in NEVER_SWAP_CHARS:
        return False
    base_ok = decode_matches(base_decoded, char)
    glyph_ok = decode_matches(glyph_decoded, char)
    if base_ok or not glyph_ok:
        return False
    if char == ZERO_GUARD_CHAR:
        trocr_glyph_ok = decode_matches(glyph_rec.get("racc_gen_decoded"), char)
        if not trocr_glyph_ok:
            return False
    return True


# ===========================================================================
# Compositing (mirrors hybrid_replay.composite_font's geometry exactly)
# ===========================================================================

def load_atlas(gen_dir: Path, font: str) -> np.ndarray | None:
    path = gen_dir / f"{font}.png"
    if not path.exists():
        return None
    return np.array(Image.open(path).convert("RGB"))


def composite_font_v2(font_name: str, joined: dict, decodes: dict,
                       base_atlas, glyph_atlas, out_gen_dir: Path) -> tuple[int, dict]:
    """Build one hybrid atlas: start from a copy of the baseline atlas, paste
    in glyph-model cells wherever swap_rule_v2() fires. Returns
    (swap_count, {char: n_swaps})."""
    if base_atlas is None:
        print(f"  WARN: baseline atlas missing for {font_name} -- skipped entirely")
        return 0, {}

    out_np = base_atlas.copy()
    swap_count = 0
    swaps_by_char: dict[str, int] = {}

    if glyph_atlas is not None:
        for idx in DRAWN_INDICES:
            char = CHARSET[idx]
            key = (font_name, char)
            if key not in joined:
                continue
            base_rec, glyph_rec = joined[key]
            base_decoded = decodes.get(("base", font_name, char))
            glyph_decoded = decodes.get(("glyph", font_name, char))
            if swap_rule_v2(base_rec, glyph_rec, char, base_decoded, glyph_decoded):
                cell = crop_cell(glyph_atlas, idx)
                row, col = idx // GRID_COLS, idx % GRID_COLS
                y0, x0 = row * CELL_H, col * CELL_W
                out_np[y0:y0 + CELL_H, x0:x0 + CELL_W] = cell
                swap_count += 1
                swaps_by_char[char] = swaps_by_char.get(char, 0) + 1
    else:
        print(f"  WARN: glyph atlas missing for {font_name} -- written as a straight baseline copy")

    out_gen_dir.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out_np).save(out_gen_dir / f"{font_name}.png")
    return swap_count, swaps_by_char


# ===========================================================================
# Accounting (char_acc_match ground truth used ONLY here, never in the rule)
# ===========================================================================

def compute_accounting(joined: dict, font_names: list[str], decodes: dict) -> dict:
    font_set = set(font_names)
    subset = {k: v for k, v in joined.items() if k[0] in font_set}
    n = len(subset)

    both_ok = only_base = only_glyph = both_fail = 0
    only_glyph_keys, only_base_keys = [], []
    for key, (base_rec, glyph_rec) in subset.items():
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

    def fires(key) -> bool:
        font, char = key
        base_rec, glyph_rec = joined[key]
        base_decoded = decodes.get(("base", font, char))
        glyph_decoded = decodes.get(("glyph", font, char))
        return swap_rule_v2(base_rec, glyph_rec, char, base_decoded, glyph_decoded)

    captured = sum(1 for k in only_glyph_keys if fires(k))
    wrongly_swapped = sum(1 for k in only_base_keys if fires(k))

    captured_by_char: dict[str, int] = {}
    for k in only_glyph_keys:
        if fires(k):
            captured_by_char[k[1]] = captured_by_char.get(k[1], 0) + 1
    wrong_by_char: dict[str, int] = {}
    for k in only_base_keys:
        if fires(k):
            wrong_by_char[k[1]] = wrong_by_char.get(k[1], 0) + 1

    print("\n" + "=" * 78)
    print(f"CAPTURE ACCOUNTING  (subset: {len(font_names)} fonts, {n} joined cells)")
    print("=" * 78)
    print(f"  oracle split (char_acc_match, GT-derived -- accounting only): "
          f"both_ok={both_ok} only_base={only_base} only_glyph={only_glyph} both_fail={both_fail}")

    capture_rate = captured / len(only_glyph_keys) if only_glyph_keys else 0.0
    false_rate = wrongly_swapped / len(only_base_keys) if only_base_keys else 0.0
    print(f"\n  CAPTURED (rule correctly swaps an only-glyph-correct cell):")
    print(f"    {captured}/{len(only_glyph_keys)} in this subset ({capture_rate*100:.1f}%)")
    print(f"    full-50-font reference denominator: {EXPECTED_ORACLE['only_glyph']} "
          f"(HD-Task 2 TrOCR-only rule captured 21/486 = 4.3%)")
    if captured_by_char:
        print(f"    captured, by char: {dict(sorted(captured_by_char.items(), key=lambda kv: -kv[1]))}")

    print(f"\n  WRONGLY-SWAPPED (rule swaps away an only-baseline-correct cell):")
    print(f"    {wrongly_swapped}/{len(only_base_keys)} in this subset ({false_rate*100:.1f}%)")
    print(f"    full-50-font reference denominator: {EXPECTED_ORACLE['only_base']}")
    if wrong_by_char:
        print(f"    wrongly-swapped, by char: {dict(sorted(wrong_by_char.items(), key=lambda kv: -kv[1]))}")

    return {
        "n_subset": n, "fonts": font_names,
        "oracle_split": {"both_ok": both_ok, "only_base": only_base,
                          "only_glyph": only_glyph, "both_fail": both_fail},
        "captured": captured, "of_only_glyph": len(only_glyph_keys), "capture_rate": capture_rate,
        "wrongly_swapped": wrongly_swapped, "of_only_base": len(only_base_keys), "false_swap_rate": false_rate,
        "captured_by_char": captured_by_char, "wrongly_swapped_by_char": wrong_by_char,
    }


# ===========================================================================
# misc
# ===========================================================================

def gpu_preflight() -> None:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10, check=True,
        )
        print(f"GPU preflight: {out.stdout.strip()}")
    except Exception as e:
        print(f"GPU preflight: nvidia-smi check failed ({e!r}) -- continuing anyway")


def all_holdout_fonts(holdout_dir: Path) -> list[str]:
    with open(holdout_dir / "manifest.json", encoding="utf-8") as f:
        manifest = json.load(f)
    return [entry["name"] for entry in manifest["fonts"]]


# ===========================================================================
# main
# ===========================================================================

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fonts", default=None,
                     help="comma-separated font names (controller subset); default = all 50 holdout fonts")
    ap.add_argument("--base-run", default=str(BASELINE_RUN))
    ap.add_argument("--glyph-run", default=str(GLYPH_RUN))
    ap.add_argument("--out-run", default=str(OUT_RUN))
    ap.add_argument("--holdout", default=str(HOLDOUT_DIR))
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dump-json", default=None,
                    help="optional path to dump the accounting + swap summary as JSON")
    args = ap.parse_args()

    base_run = Path(args.base_run)
    glyph_run = Path(args.glyph_run)
    out_run = Path(args.out_run)
    holdout_dir = Path(args.holdout)
    got_cache_path = out_run / "got_decodes.json"

    base_records = load_per_cell(base_run / "per_cell.json")
    glyph_records = load_per_cell(glyph_run / "per_cell.json")
    joined = join_records(base_records, glyph_records)

    if args.fonts:
        font_names = [f.strip() for f in args.fonts.split(",") if f.strip()]
    else:
        font_names = all_holdout_fonts(holdout_dir)

    print("=" * 78)
    print("HYBRID V2: COMBINED-OCR (TrOCR + GOT-OCR2) NO-GT SWAP REPLAY")
    print("=" * 78)
    print(f"Fonts selected: {len(font_names)}"
          + (f" -> {font_names}" if len(font_names) <= 10 else f" -> {font_names[:10]}..."))
    print(f"Joined cells available: {len(joined)}")

    gpu_preflight()

    # Lazy GOT-OCR2 load: only builds the model on the first actual cache
    # miss, so a fully-cached re-run (or a run over fonts with zero new
    # confusable cells) never touches the GPU.
    _ocr_holder: dict = {}

    def get_ocr_fn():
        if "fn" not in _ocr_holder:
            print(f"\nLoading GOT-OCR2 on {args.device} (first cache-miss)...")
            t0 = time.time()
            _ocr_holder["fn"] = build_got_ocr_fn(args.device)
            print(f"  loaded in {time.time()-t0:.1f}s")
        return _ocr_holder["fn"]

    got_cache = load_got_cache(got_cache_path)

    base_gen_dir = base_run / "generated"
    glyph_gen_dir = glyph_run / "generated"
    out_gen_dir = out_run / "generated"

    print("\n" + "=" * 78)
    print("COMPOSITING HYBRID ATLASES")
    print("=" * 78)

    swap_counts: dict[str, int] = {}
    all_swaps_by_char: dict[str, int] = {}
    all_decodes: dict = {}
    total_got_calls = 0
    t_start = time.time()

    for font in font_names:
        base_atlas = load_atlas(base_gen_dir, font)
        glyph_atlas = load_atlas(glyph_gen_dir, font)

        decodes, got_calls = build_font_decodes(font, joined, base_atlas, glyph_atlas, get_ocr_fn, got_cache)
        total_got_calls += got_calls
        all_decodes.update(decodes)
        if got_calls:
            save_got_cache(got_cache_path, got_cache)  # persist incrementally -- crash-safe

        swap_count, swaps_by_char = composite_font_v2(font, joined, decodes, base_atlas, glyph_atlas, out_gen_dir)
        swap_counts[font] = swap_count
        for ch, n in swaps_by_char.items():
            all_swaps_by_char[ch] = all_swaps_by_char.get(ch, 0) + n

        elapsed = time.time() - t_start
        print(f"  {font:<40s} swaps={swap_count:>3d}  (fresh GOT calls this font: {got_calls:>3d}, "
              f"{elapsed:.1f}s elapsed)")
        print_sample_decodes(font, joined, decodes)

    save_got_cache(got_cache_path, got_cache)

    total_swaps = sum(swap_counts.values())
    fonts_with_swaps = sum(1 for v in swap_counts.values() if v > 0)
    print(f"\nTotal swaps: {total_swaps} across {fonts_with_swaps}/{len(font_names)} fonts")
    print(f"Total fresh GOT-OCR2 decode calls: {total_got_calls} "
          f"({time.time()-t_start:.1f}s total, {(time.time()-t_start)/max(total_got_calls,1):.2f}s/call)")
    if all_swaps_by_char:
        print("Swaps concentrated by char (all fonts in this run):")
        for ch, n in sorted(all_swaps_by_char.items(), key=lambda kv: -kv[1]):
            print(f"    {ch!r:<6} {n}")
    print(f"\nWrote {len(font_names)} atlases to {out_gen_dir}/")

    accounting = compute_accounting(joined, font_names, all_decodes)

    summary = {
        "fonts": font_names,
        "swap_counts": swap_counts,
        "total_swaps": total_swaps,
        "fonts_with_swaps": fonts_with_swaps,
        "swaps_by_char": all_swaps_by_char,
        "total_got_calls": total_got_calls,
        "accounting": accounting,
    }
    if args.dump_json:
        dump_path = Path(args.dump_json)
        dump_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dump_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"\nSummary dumped to {dump_path}")


if __name__ == "__main__":
    main()
