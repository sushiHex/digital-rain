"""V3-layout best-of-N eval (dual metric): does V3 (the better generator) + best-of-N
beat our structured-5000 baseline?

V3 uses a square-cell grid with centering offsets (per atlas_to_font.compute_grid,
the PRODUCTION vectorizer's geometry) over a 71-char charset — NOT our 12x8/95.
This reuses that exact geometry so crops align to V3's glyphs. Reports both
OCR-readability (style-invariant) and DINOv2-template (style-sensitive) char-acc,
single-seed vs best-of-N, to compare against eval_cleanup_quality's structured-5000
numbers (OCR 0.401->0.543 best-of-N on the same 3 hard fonts).

Usage (after gen_v3_seeds.py):
  python eval_v3_bestofn.py --seeds-dir experiments/v3_seeds
"""
import argparse
import glob
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from atlas_to_font import compute_grid, CHARSET as V3_CHARSET
from atlas_constants import CANVAS, load_truetype_pinned
from cleanup.models import build_trocr_ocr_fn, build_dino_embed_fn
from generate_atlas import score_glyph_cell
from probe_utils import HARD_FONTS

# Production V3 atlas geometry: square cells + centering offsets.
_COLS, _ROWS, _CELL, _OX, _OY = compute_grid(len(V3_CHARSET), CANVAS, CANVAS)
DRAWN = list(range(len(V3_CHARSET)))
EXPECTED = {i: V3_CHARSET[i] for i in DRAWN}


def v3_crop(atlas, idx):
    r, c = idx // _COLS, idx % _COLS
    y0, x0 = _OY + r * _CELL, _OX + c * _CELL
    return atlas[y0:y0 + _CELL, x0:x0 + _CELL]


def render_gt_cell(font_path, char):
    """The target font's own glyph for `char`, white on black, centered in a square cell."""
    img = Image.new("RGB", (_CELL, _CELL), (0, 0, 0))
    if char == " ":
        return np.array(img)
    draw = ImageDraw.Draw(img)
    lo, hi = 8, _CELL
    while lo < hi:
        mid = (lo + hi + 1) // 2
        f = load_truetype_pinned(font_path, mid)
        b = f.getbbox(char)
        if (b[2] - b[0]) <= _CELL * 0.8 and (b[3] - b[1]) <= _CELL * 0.7:
            lo = mid
        else:
            hi = mid - 1
    f = load_truetype_pinned(font_path, lo)
    b = f.getbbox(char)
    cw, ch = b[2] - b[0], b[3] - b[1]
    draw.text(((_CELL - cw) // 2 - b[0], (_CELL - ch) // 2 - b[1]),
              char, fill=(255, 255, 255), font=f)
    return np.array(img)


def ocr_acc(atlas, ocr_fn):
    return float(np.mean([ocr_fn(v3_crop(atlas, i)) == EXPECTED[i] for i in DRAWN]))


def template_acc(atlas, gt_cells, embed_fn):
    gen = embed_fn([v3_crop(atlas, i) for i in DRAWN])
    g = embed_fn(gt_cells)
    gen = gen / (np.linalg.norm(gen, axis=1, keepdims=True) + 1e-9)
    g = g / (np.linalg.norm(g, axis=1, keepdims=True) + 1e-9)
    pred = (gen @ g.T).argmax(axis=1)
    return float(np.mean(pred == np.arange(len(DRAWN))))


def best_of_n(atlases, ocr_fn):
    base = atlases[0].copy()
    for idx in DRAWN:
        cands = [v3_crop(a, idx) for a in atlases]
        correct = [c for c in cands if ocr_fn(c) == EXPECTED[idx]]
        pool = correct if correct else cands
        best = max(pool, key=lambda c: score_glyph_cell(Image.fromarray(c)))
        r, c = idx // _COLS, idx % _COLS
        y0, x0 = _OY + r * _CELL, _OX + c * _CELL
        base[y0:y0 + _CELL, x0:x0 + _CELL] = best
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds-dir", default="experiments/v3_seeds")
    ap.add_argument("--fonts", nargs="+",
                    default=["RubikDistressed", "BitcountGridDoubleInk", "PlaywriteMXGuides"])
    args = ap.parse_args()
    print(f"V3 grid: cols={_COLS} rows={_ROWS} cell={_CELL} offset=({_OX},{_OY})")

    ocr_fn = build_trocr_ocr_fn()
    embed_fn = build_dino_embed_fn()

    rows = []
    hdr = f"{'font':>26} | {'ocr:1seed':>10} {'ocr:bestN':>10} | {'tpl:1seed':>10} {'tpl:bestN':>10}"
    print(hdr); print("-" * len(hdr))
    for font in args.fonts:
        paths = sorted(glob.glob(f"{args.seeds_dir}/{font}__*seed*.png"))
        if len(paths) < 2:
            print(f"skip {font} (<2 seeds)"); continue
        atlases = [np.array(Image.open(p).convert("RGB")) for p in paths]
        gt_cells = [render_gt_cell(HARD_FONTS[font], V3_CHARSET[i]) for i in DRAWN]

        ocr1 = ocr_acc(atlases[0], ocr_fn)
        tpl1 = template_acc(atlases[0], gt_cells, embed_fn)
        best = best_of_n(atlases, ocr_fn)
        ocrn = ocr_acc(best, ocr_fn)
        tpln = template_acc(best, gt_cells, embed_fn)
        rows.append({"font": font, "ocr": [ocr1, ocrn], "tpl": [tpl1, tpln]})
        print(f"{font:>26} | {ocr1:>10.4f} {ocrn:>10.4f} | {tpl1:>10.4f} {tpln:>10.4f}")

    if rows:
        def m(metric, k): return float(np.mean([r[metric][k] for r in rows]))
        print("-" * len(hdr))
        print(f"{'MEAN':>26} | {m('ocr',0):>10.4f} {m('ocr',1):>10.4f} | {m('tpl',0):>10.4f} {m('tpl',1):>10.4f}")
        print(f"\nV3 best-of-N lift  ocr: {m('ocr',1)-m('ocr',0):+.4f}   tpl: {m('tpl',1)-m('tpl',0):+.4f}")
        print(f"(structured-5000 baseline: ocr 0.401->0.543 (+0.142), tpl 0.337->0.330)")
        Path("research").mkdir(exist_ok=True)
        Path("research/2026-06-01-v3_bestofn_eval.json").write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
