"""Score the reference-ablation outputs and report whether oracle references
beat Times references on hard fonts.
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from probe_utils import (
    DINO_MEANINGFUL_DELTA,
    HARD_FONTS,
    LPIPS_MARGINAL_DELTA,
    LPIPS_MEANINGFUL_DELTA,
    LPIPS_STRONG_DELTA,
    REF_ORACLE,
    REF_TIMES,
    REF_VARIANTS,
    load_scoring_models,
    print_per_font_table,
    render_gt_atlas,
    score_atlas_pair,
)


PROBE_DIR = Path("experiments/ref_ablation")


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    models = load_scoring_models(device)

    print("Loading GT atlases...")
    gt = {name: render_gt_atlas(path) for name, path in HARD_FONTS.items()}

    rows = []
    for name in HARD_FONTS:
        for variant in REF_VARIANTS:
            p = PROBE_DIR / f"{name}__ref_{variant}.png"
            if not p.exists():
                print(f"MISSING {p}")
                continue
            gen = Image.open(p).convert("RGB")
            lp, di = score_atlas_pair(gen, gt[name], models)
            rows.append({"font": name, "variant": variant, "lpips": lp, "dinov2": di})
            print(f"  {name:>26} / ref={variant:<7}  lpips={lp:.4f}  dino={di:.4f}")

    if not rows:
        print("No probe outputs found -- nothing to score.")
        return

    by_font = {}
    for r in rows:
        by_font.setdefault(r["font"], {})[r["variant"]] = r

    print_per_font_table(by_font, REF_VARIANTS, font_col_width=26, val_col_width=9)

    print()
    print("=" * 90)
    print(f"ORACLE DOMINANCE  ({REF_ORACLE} - {REF_TIMES})")
    print("=" * 90)
    print(f"Negative lpips delta = {REF_ORACLE} ref produced output CLOSER to GT than {REF_TIMES} ref")
    print(f"Positive dino  delta = {REF_ORACLE} ref produced output CLOSER to GT than {REF_TIMES} ref")
    print()
    print(f"{'font':>26}  {'lpips_o-t':>10}  {'dino_o-t':>10}  oracle_wins?")
    print("-" * 70)
    deltas = []
    for font, by_variant in by_font.items():
        if REF_TIMES in by_variant and REF_ORACLE in by_variant:
            d_lp = by_variant[REF_ORACLE]["lpips"] - by_variant[REF_TIMES]["lpips"]
            d_di = by_variant[REF_ORACLE]["dinov2"] - by_variant[REF_TIMES]["dinov2"]
            wins = (d_lp < -LPIPS_MEANINGFUL_DELTA) or (d_di > DINO_MEANINGFUL_DELTA)
            deltas.append({"font": font, "d_lpips_o_t": d_lp, "d_dino_o_t": d_di})
            print(f"{font:>26}  {d_lp:>+10.4f}  {d_di:>+10.4f}  {'YES' if wins else 'no'}")

    if not deltas:
        print(f"\nNo {REF_ORACLE}/{REF_TIMES} pairs found -- skipping verdict.")
        return

    print()
    print("=" * 90)
    print("VERDICT")
    print("=" * 90)
    mean_dlp = float(np.mean([d["d_lpips_o_t"] for d in deltas]))
    mean_ddi = float(np.mean([d["d_dino_o_t"] for d in deltas]))
    n_wins = sum(1 for d in deltas
                 if d["d_lpips_o_t"] < -LPIPS_MEANINGFUL_DELTA
                 or d["d_dino_o_t"] > DINO_MEANINGFUL_DELTA)
    print(f"Mean oracle-minus-times: lpips={mean_dlp:+.4f}  dino={mean_ddi:+.4f}")
    print(f"Oracle wins on {n_wins} / {len(deltas)} fonts "
          f"(threshold: lpips<-{LPIPS_MEANINGFUL_DELTA} OR dino>+{DINO_MEANINGFUL_DELTA})")
    print()
    if mean_dlp < -LPIPS_STRONG_DELTA and n_wins >= 4:
        print("-> ORACLE DOMINATES.  References are the lever.")
        print("   Next step: synthesize 'oracle-like' references for hard fonts (cluster")
        print("   training set in style space, pick nearest existing font as ref).")
    elif mean_dlp < -LPIPS_MARGINAL_DELTA and n_wins >= 3:
        print("-> Oracle helps but not dramatically. References matter on the margin;")
        print("   architectural improvements (D-DPO, Glyph-ByT5) likely a bigger lever.")
    else:
        print("-> Oracle does NOT meaningfully beat Times.  Model is reference-blind on")
        print("   hard fonts.  Reference engineering is dead -- architectural change")
        print("   required (D-DPO with OCR reward, Glyph-ByT5 separate channel, or")
        print("   accept ceiling and ship style-sketch + downstream renderer).")

    out = Path("research/2026-05-02-ref_ablation_analysis.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "rows": rows, "deltas": deltas,
        "mean_oracle_minus_times": {"lpips": mean_dlp, "dino": mean_ddi},
        "n_oracle_wins": n_wins, "n_total": len(deltas),
    }, indent=2))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
