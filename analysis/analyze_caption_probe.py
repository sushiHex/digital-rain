"""Score caption A/B probe outputs and decide whether captions move the
model's output in a style-aware way.
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
    CAPTION_CLASH,
    CAPTION_CONTROL,
    CAPTION_MATCH,
    CAPTION_NULL,
    CAPTION_VARIANTS,
    LPIPS_NOISE_FLOOR,
    load_scoring_models,
    print_per_font_table,
    render_gt_atlas,
    score_atlas_pair,
)


PROBE_DIR = Path("experiments/caption_probe")
FONTS = {
    "times": "C:/Windows/Fonts/times.ttf",
    "arial": "C:/Windows/Fonts/arial.ttf",
    "consol": "C:/Windows/Fonts/consola.ttf",
}


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    models = load_scoring_models(device)

    print("Loading GT atlases...")
    gt = {f: render_gt_atlas(path) for f, path in FONTS.items()}

    rows = []
    for font in FONTS:
        for variant in CAPTION_VARIANTS:
            p = PROBE_DIR / f"{font}_{variant}.png"
            if not p.exists():
                print(f"MISSING {p}")
                continue
            gen = Image.open(p).convert("RGB")
            lp, dino = score_atlas_pair(gen, gt[font], models)
            rows.append({"font": font, "variant": variant, "lpips": lp, "dinov2": dino})
            print(f"  {font:>6} / {variant:<10}  lpips={lp:.4f}  dino={dino:.4f}")

    if not rows:
        print("No probe outputs found -- nothing to score.")
        return

    by_font = {}
    for r in rows:
        by_font.setdefault(r["font"], {})[r["variant"]] = r

    print_per_font_table(by_font, CAPTION_VARIANTS, font_col_width=8, val_col_width=8)

    print()
    print("=" * 76)
    print(f"DIRECTION ANALYSIS  vs {CAPTION_CONTROL}")
    print("=" * 76)
    print(f"Negative lpips delta = closer to GT than {CAPTION_CONTROL} (better)")
    print(f"Positive dino  delta = closer to GT than {CAPTION_CONTROL} (better)")
    print()
    print(f"{'font':>8} {'B-A_lpips':>11} {'C-A_lpips':>11} {'D-A_lpips':>11} "
          f"{'B-A_dino':>10} {'C-A_dino':>10} {'D-A_dino':>10}")
    print("-" * 86)
    deltas = []
    for font, by_variant in by_font.items():
        if CAPTION_CONTROL not in by_variant:
            continue
        a = by_variant[CAPTION_CONTROL]
        d = {"font": font}
        for v in [CAPTION_MATCH, CAPTION_CLASH, CAPTION_NULL]:
            if v in by_variant:
                d[f"lp_{v}"] = by_variant[v]["lpips"] - a["lpips"]
                d[f"dn_{v}"] = by_variant[v]["dinov2"] - a["dinov2"]
        deltas.append(d)
        print(f"{font:>8} "
              f"{d.get(f'lp_{CAPTION_MATCH}', float('nan')):>+11.4f} "
              f"{d.get(f'lp_{CAPTION_CLASH}', float('nan')):>+11.4f} "
              f"{d.get(f'lp_{CAPTION_NULL}',  float('nan')):>+11.4f} "
              f"{d.get(f'dn_{CAPTION_MATCH}', float('nan')):>+10.4f} "
              f"{d.get(f'dn_{CAPTION_CLASH}', float('nan')):>+10.4f} "
              f"{d.get(f'dn_{CAPTION_NULL}',  float('nan')):>+10.4f}")

    if not deltas:
        print(f"\nNo {CAPTION_CONTROL} baseline found -- skipping verdict.")
        return

    print()
    print("=" * 76)
    print("VERDICT")
    print("=" * 76)
    abs_lp_d = float(np.mean([abs(d.get(f"lp_{CAPTION_NULL}", 0)) for d in deltas]))
    abs_lp_b = float(np.mean([abs(d.get(f"lp_{CAPTION_MATCH}", 0)) for d in deltas]))
    abs_lp_c = float(np.mean([abs(d.get(f"lp_{CAPTION_CLASH}", 0)) for d in deltas]))

    signed_b = float(np.mean([d.get(f"lp_{CAPTION_MATCH}", 0) for d in deltas]))
    signed_c = float(np.mean([d.get(f"lp_{CAPTION_CLASH}", 0) for d in deltas]))
    signed_d = float(np.mean([d.get(f"lp_{CAPTION_NULL}", 0) for d in deltas]))
    style_signal = signed_c - signed_b  # >0 means matching closer than clashing

    print(f"Mean |lpips delta|:  {CAPTION_MATCH}={abs_lp_b:.4f}  {CAPTION_CLASH}={abs_lp_c:.4f}  {CAPTION_NULL}={abs_lp_d:.4f}")
    print(f"Mean signed lpips delta vs {CAPTION_CONTROL}:")
    print(f"  {CAPTION_MATCH} (matching style):  {signed_b:+.4f}  ({'closer to GT' if signed_b<0 else 'farther from GT'})")
    print(f"  {CAPTION_CLASH} (wrong style):     {signed_c:+.4f}")
    print(f"  {CAPTION_NULL} (random words):     {signed_d:+.4f}")
    print(f"Style-direction signal (C - B): {style_signal:+.4f}")
    print(f"  Positive means matching caption pulls closer to GT than clashing -- what we'd want.")
    print()

    any_caption_moves = max(abs_lp_b, abs_lp_c, abs_lp_d) > LPIPS_NOISE_FLOOR
    null_perturbs_too = abs_lp_d > LPIPS_NOISE_FLOOR
    style_helps = style_signal > LPIPS_NOISE_FLOOR

    if not any_caption_moves:
        print("-> VERDICT: Captions ignored entirely.  Don't bother with caption engineering.")
    elif style_helps:
        print("-> VERDICT: Style captions help.  Worth exploring guided captions at inference.")
    else:
        print("-> VERDICT: Captions perturb output but NOT in a useful style direction.")
        print("   The matching caption (B) does not pull closer to GT than the clashing (C)")
        print("   or null (D) caption.  Training captions were structured layout descriptions,")
        print("   not style descriptors -- the model never learned a caption->style mapping.")
        print("   Caption engineering at inference is DEAD.  Don't include style prefixes.")
    if null_perturbs_too:
        print(f"   (Note: random words also perturb (|D| = {abs_lp_d:.4f}), which means the")
        print("   model is sensitive to ANY token perturbation, not specifically to style.)")

    out = Path("research/2026-05-02-caption_probe_analysis.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "rows": rows, "deltas": deltas,
        "abs_lpips_deltas": {CAPTION_MATCH: abs_lp_b, CAPTION_CLASH: abs_lp_c, CAPTION_NULL: abs_lp_d},
    }, indent=2))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
