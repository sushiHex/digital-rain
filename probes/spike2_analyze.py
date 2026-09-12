"""Spike 2 (part 2): measure cross-seed per-cell failure independence.

For each font, OCR every drawn cell across all rendered seeds and build a
[seed x cell] pass/fail matrix. Then answer the question that decides the
cleanup strategy:

  - best-of-N char-acc (a cell counts as correct if ANY seed gets it right)
    vs mean single-seed char-acc -> the ceiling best-of-N selection can reach.
  - systematic-failure fraction: of cells that fail in >=1 seed, what fraction
    fail in ALL seeds? High -> failures are systematic, best-of-N stalls, need
    cropped-inpaint + reference hint. Low -> failures are seed-independent,
    best-of-N recovers most of them cheaply.
"""

# repo root on sys.path so `python probes/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

from atlas_constants import CHARSET, DRAWN_INDICES
from eval_checkpoint import TROCR_MODEL_ID, crop_cell, _ocr_decode_cell

SEEDS_DIR = Path("experiments/spike2_seeds")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default=None,
                        help="Model tag in filenames (e.g. flux2kleinbase9b). Auto-detected if omitted.")
    args = parser.parse_args()

    pngs = sorted(SEEDS_DIR.glob("*__*_seed*.png"))
    if not pngs:
        print(f"No atlases in {SEEDS_DIR}/ -- run spike2_seeds.py first.")
        return

    # Parse {font}__{tag}_seed{seed}.png
    by_font = defaultdict(dict)  # font -> {seed: path}
    tags = set()
    for p in pngs:
        stem = p.stem
        font, rest = stem.split("__", 1)
        tag, seedpart = rest.rsplit("_seed", 1)
        tags.add(tag)
        if args.tag and tag != args.tag:
            continue
        by_font[font][int(seedpart)] = p

    if args.tag is None and len(tags) > 1:
        print(f"Multiple model tags present {sorted(tags)}; pass --tag to pick one.")
        return

    import torch
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading TrOCR ({TROCR_MODEL_ID}) on {device}...")
    processor = TrOCRProcessor.from_pretrained(TROCR_MODEL_ID)
    model = VisionEncoderDecoderModel.from_pretrained(TROCR_MODEL_ID).to(device).eval()

    expected = {idx: CHARSET[idx] for idx in DRAWN_INDICES}

    report = {}
    for font, seed_paths in sorted(by_font.items()):
        seeds = sorted(seed_paths)
        # pass_matrix[seed_i][cell_idx] = 1 if OCR(cell) == expected char
        pass_matrix = {}
        for seed in seeds:
            atlas = np.array(Image.open(seed_paths[seed]).convert("L"))
            passes = {}
            for idx in DRAWN_INDICES:
                cell = crop_cell(atlas, idx)
                decoded = _ocr_decode_cell(cell, processor, model, device)
                passes[idx] = int(decoded == expected[idx])
            pass_matrix[seed] = passes
            acc = np.mean(list(passes.values()))
            print(f"  {font:>26} seed {seed}: char-acc {acc:.4f}")

        n = len(seeds)
        per_seed_acc = [np.mean(list(pass_matrix[s].values())) for s in seeds]
        # best-of-N: cell correct if any seed got it
        best_of_n = np.mean([
            int(any(pass_matrix[s][idx] for s in seeds)) for idx in DRAWN_INDICES
        ])
        # systematic fraction among ever-failing cells
        ever_fail = [idx for idx in DRAWN_INDICES if any(pass_matrix[s][idx] == 0 for s in seeds)]
        always_fail = [idx for idx in ever_fail if all(pass_matrix[s][idx] == 0 for s in seeds)]
        systematic_frac = (len(always_fail) / len(ever_fail)) if ever_fail else 0.0

        report[font] = {
            "n_seeds": n,
            "per_seed_char_acc": [float(a) for a in per_seed_acc],
            "mean_single_seed": float(np.mean(per_seed_acc)),
            "best_of_n_char_acc": float(best_of_n),
            "best_of_n_lift": float(best_of_n - np.mean(per_seed_acc)),
            "n_ever_fail": len(ever_fail),
            "n_always_fail": len(always_fail),
            "systematic_fraction": float(systematic_frac),
        }

    print()
    print("=" * 92)
    print("CROSS-SEED FAILURE ANALYSIS")
    print("=" * 92)
    print(f"{'font':>26} {'mean_1seed':>11} {'best_of_N':>10} {'lift':>8} "
          f"{'ever_fail':>10} {'always_fail':>12} {'systematic%':>12}")
    print("-" * 92)
    for font, r in report.items():
        print(f"{font:>26} {r['mean_single_seed']:>11.4f} {r['best_of_n_char_acc']:>10.4f} "
              f"{r['best_of_n_lift']:>+8.4f} {r['n_ever_fail']:>10} {r['n_always_fail']:>12} "
              f"{r['systematic_fraction']*100:>11.1f}%")

    agg_sys = np.mean([r["systematic_fraction"] for r in report.values()])
    agg_lift = np.mean([r["best_of_n_lift"] for r in report.values()])
    print()
    print("=" * 92)
    print("VERDICT")
    print("=" * 92)
    print(f"Mean best-of-N lift over single seed: {agg_lift:+.4f} char-acc")
    print(f"Mean systematic-failure fraction:     {agg_sys*100:.1f}%")
    print()
    if agg_sys < 0.4:
        print("-> FAILURES ARE LARGELY SEED-INDEPENDENT. Best-of-N cleanup recovers")
        print("   most errors cheaply. Route A (cleanup-decoupled) is viable.")
    elif agg_sys < 0.7:
        print("-> MIXED. Best-of-N helps but leaves a systematic residue that needs")
        print("   cropped-inpaint + reference-glyph hint to mop up.")
    else:
        print("-> FAILURES ARE SYSTEMATIC across seeds. Best-of-N stalls; the model")
        print("   simply can't draw these glyphs in any seed. Cleanup must use")
        print("   reference-guided cropped-inpaint, or the generator itself needs work.")

    out = Path("research/2026-05-31-crossseed_correlation.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"per_font": report,
                                "mean_systematic_fraction": float(agg_sys),
                                "mean_best_of_n_lift": float(agg_lift)}, indent=2))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
