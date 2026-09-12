"""Score multi-reference outputs and decide whether passing 2+ refs helps."""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from probe_utils import (
    HARD_FONTS,
    LPIPS_MEANINGFUL_DELTA,
    LPIPS_NOISE_FLOOR,
    MULTIREF_VARIANTS,
    REF1_KG,
    REF2_KG_MN,
    REF2_MN_KG,
    load_scoring_models,
    print_per_font_table,
    render_gt_atlas,
    score_atlas_pair,
)


PROBE_DIR = Path("experiments/multiref")


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    models = load_scoring_models(device)

    print("Loading GT atlases...")
    gt = {name: render_gt_atlas(path) for name, path in HARD_FONTS.items()}

    rows = []
    for name in HARD_FONTS:
        for variant in MULTIREF_VARIANTS:
            p = PROBE_DIR / f"{name}__{variant}.png"
            if not p.exists():
                print(f"MISSING {p}")
                continue
            gen = Image.open(p).convert("RGB")
            lp, di = score_atlas_pair(gen, gt[name], models)
            rows.append({"font": name, "variant": variant, "lpips": lp, "dinov2": di})
            print(f"  {name:>26} / {variant:<10}  lpips={lp:.4f}  dino={di:.4f}")

    if not rows:
        print("No probe outputs found -- nothing to score.")
        return

    by_font = {}
    for r in rows:
        by_font.setdefault(r["font"], {})[r["variant"]] = r

    print_per_font_table(by_font, MULTIREF_VARIANTS, font_col_width=26, val_col_width=10)

    print()
    print("=" * 90)
    print(f"DELTAS vs single-ref ({REF1_KG})")
    print("=" * 90)
    print("Negative lpips delta = multi-ref CLOSER to GT than single-ref (better)")
    print("Positive dino  delta = multi-ref CLOSER to GT than single-ref (better)")
    print()
    print(f"{'font':>26}  {'2kgmn-1':>10}  {'2mnkg-1':>10}  {'2kgmn-1':>10}  {'2mnkg-1':>10}  {'order_eff':>10}")
    print(f"{'':>26}  {'lpips':>10}  {'lpips':>10}  {'dino':>10}  {'dino':>10}  {'lpips':>10}")
    print("-" * 102)
    deltas = []
    for font, by_variant in by_font.items():
        if REF1_KG not in by_variant:
            continue
        base = by_variant[REF1_KG]
        d = {"font": font}
        if REF2_KG_MN in by_variant:
            d["d_lp_kgmn"] = by_variant[REF2_KG_MN]["lpips"] - base["lpips"]
            d["d_di_kgmn"] = by_variant[REF2_KG_MN]["dinov2"] - base["dinov2"]
        if REF2_MN_KG in by_variant:
            d["d_lp_mnkg"] = by_variant[REF2_MN_KG]["lpips"] - base["lpips"]
            d["d_di_mnkg"] = by_variant[REF2_MN_KG]["dinov2"] - base["dinov2"]
        if REF2_KG_MN in by_variant and REF2_MN_KG in by_variant:
            d["order_eff_lpips"] = by_variant[REF2_MN_KG]["lpips"] - by_variant[REF2_KG_MN]["lpips"]
        deltas.append(d)
        print(f"{font:>26}  "
              f"{d.get('d_lp_kgmn', float('nan')):>+10.4f}  "
              f"{d.get('d_lp_mnkg', float('nan')):>+10.4f}  "
              f"{d.get('d_di_kgmn', float('nan')):>+10.4f}  "
              f"{d.get('d_di_mnkg', float('nan')):>+10.4f}  "
              f"{d.get('order_eff_lpips', float('nan')):>+10.4f}")

    if not deltas:
        print(f"\nNo {REF1_KG} baseline found -- skipping verdict.")
        return

    print()
    print("=" * 90)
    print("VERDICT")
    print("=" * 90)
    mean_dlp = float(np.mean([d.get("d_lp_kgmn", 0) for d in deltas]))
    mean_ddi = float(np.mean([d.get("d_di_kgmn", 0) for d in deltas]))
    order_effects = [abs(d.get("order_eff_lpips", 0)) for d in deltas if "order_eff_lpips" in d]
    mean_order = float(np.mean(order_effects)) if order_effects else 0.0
    print(f"Mean ({REF2_KG_MN}) - ({REF1_KG}):  lpips={mean_dlp:+.4f}  dino={mean_ddi:+.4f}")
    print(f"Mean |order effect|:       lpips={mean_order:.4f}  (kg-then-mn vs mn-then-kg)")
    print()

    if mean_dlp < -LPIPS_MEANINGFUL_DELTA and mean_ddi > +LPIPS_MEANINGFUL_DELTA:
        print("-> 2-REF HELPS.  Multi-reference at inference unlocks gains at zero training cost.")
        print("   Next: optimal-pair selection, or extend training to support more refs.")
    elif abs(mean_dlp) < LPIPS_NOISE_FLOOR and abs(mean_ddi) < LPIPS_NOISE_FLOOR:
        print("-> 2-REF IGNORED.  Adding refs has no effect -- model uses only the first.")
        print("   T=10 training means refs 2+ get OOD position IDs and the model drops them.")
    elif mean_dlp > LPIPS_MEANINGFUL_DELTA:
        print("-> 2-REF HURTS.  OOD position embeddings confuse the model on extra refs.")
        print("   Don't pass multiple refs at inference. Would need training-time changes")
        print("   (T-grid expansion, or explicit position embeddings) to use multi-ref.")
    else:
        print("-> Mixed/marginal -- manual inspection needed.")
    if mean_order > LPIPS_NOISE_FLOOR:
        print(f"-> Note: ref ORDER matters (mean |delta| = {mean_order:.4f}).")
        print("   The model is not symmetric across reference positions.")

    out = Path("research/2026-05-02-multiref_analysis.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "rows": rows, "deltas": deltas,
        "summary": {"mean_d_lpips_kgmn": mean_dlp,
                    "mean_d_dino_kgmn": mean_ddi,
                    "mean_abs_order_effect_lpips": mean_order},
    }, indent=2))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
