"""Build a side-by-side comparison page: our LoRA vs Ref2Font V3 vs GT.

Atlas formats differ (12x8/95 chars vs 9x8/70 chars), so we display whole
atlases at matched display width and let visual inspection drive the
go/no-go on warm-start training.
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from pathlib import Path

from PIL import Image

from atlas_constants import CANVAS, CHARSET, GRID_COLS, GRID_ROWS
from probe_utils import HARD_FONTS, html_escape, img_to_data_uri, render_gt_atlas


OUR_DIR = Path("experiments/ref_ablation")     # {font}__ref_oracle.png  -> our LoRA
V3_DIR = Path("experiments/ref2font_v3_benchmark")  # {font}__v3_atlas.png

OUT_HTML = Path("experiments/v3_vs_ours_comparison.html")

V3_GRID_ROWS = 9
V3_GRID_COLS = 8
V3_CHARS = 70


def main():
    ours_layout = f"{GRID_ROWS}x{GRID_COLS} grid, {len(CHARSET)} chars, \"Kg\" reference, {CANVAS}x{CANVAS}"
    v3_layout = f"{V3_GRID_ROWS}x{V3_GRID_COLS} grid, {V3_CHARS} chars, \"Aa\" reference, {CANVAS}x{CANVAS}"
    parts = [f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'><title>Ref2Font V3 vs Our LoRA</title>
<style>
body {{ font-family: monospace; background: #111; color: #eee; padding: 20px; }}
h1 {{ color: #fff; }}
h2 {{ border-bottom: 1px solid #444; padding-top: 30px; color: #aaf; }}
.row {{ display: flex; gap: 12px; align-items: flex-start; margin-bottom: 30px; }}
.col {{ flex: 1; text-align: center; }}
.col img {{ max-width: 100%; border: 1px solid #333; background: #000; }}
.col-label {{ color: #aaa; font-size: 13px; padding: 4px; }}
.note {{ color: #ff8; font-size: 13px; margin-top: 10px; }}
</style></head><body>
<h1>Ref2Font V3 vs Our LoRA (structured-prompt 5000 ckpt) vs GT</h1>
<p class='note'>Note: atlas formats differ. Ours: {html_escape(ours_layout)}.<br>
V3: {html_escape(v3_layout)}. GT atlas matches OURS layout.<br>
Direct numerical comparison is not apples-to-apples - this is for visual inspection only.</p>
"""]

    for name, font_path in HARD_FONTS.items():
        ours_p = OUR_DIR / f"{name}__ref_oracle.png"
        v3_p = V3_DIR / f"{name}__v3_atlas.png"

        ours_img = Image.open(ours_p).convert("RGB") if ours_p.exists() else None
        v3_img = Image.open(v3_p).convert("RGB") if v3_p.exists() else None
        gt_img = render_gt_atlas(font_path)

        ours_uri = img_to_data_uri(ours_img, max_width=520) if ours_img else ""
        v3_uri = img_to_data_uri(v3_img, max_width=520) if v3_img else ""
        gt_uri = img_to_data_uri(gt_img, max_width=520)

        safe_name = html_escape(name)
        parts.append(f"<h2>{safe_name}</h2>")
        parts.append("<div class='row'>")
        parts.append(f"  <div class='col'><div class='col-label'>GT (target font, our {GRID_ROWS}x{GRID_COLS} layout)</div>"
                     f"<img src='{gt_uri}'></div>")
        parts.append(f"  <div class='col'><div class='col-label'>Our LoRA (structured-prompt 5000, oracle ref)</div>"
                     f"<img src='{ours_uri}' /></div>")
        parts.append(f"  <div class='col'><div class='col-label'>Ref2Font V3 (no fine-tune, {V3_GRID_ROWS}x{V3_GRID_COLS} layout)</div>"
                     f"<img src='{v3_uri}' /></div>")
        parts.append("</div>")

    parts.append("</body></html>")
    OUT_HTML.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {OUT_HTML}  ({OUT_HTML.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
