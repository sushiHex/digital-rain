"""Side-by-side: shipped 9B glyph model vs the Apache-2.0 4B, against GT.

The 4B loses char_acc -0.046 and DINOv2 -0.030 against the 9B, both large
effects (p=0.0001, research/2026-07-30-klein-4b-derisk-gate.md). Those are
*style fidelity* axes, and whether that difference is visible is not something
a number answers. This renders one row of glyphs per font: ground truth, 9B,
4B -- so the style gap can be judged directly.

Run from the repo root:
  python viz/compare_9b_4b.py
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atlas_constants import CELL_H, CELL_W, CHARSET, GRID_COLS
from viz._common import FONTS, GT, ensure_out, label_font, load_atlas

NINE = os.path.join("eval_runs", "prompt_trained_short", "generated")
FOUR = os.path.join("eval_runs", "glyph_4b_r32_5000", "generated")
DIST4 = os.path.join("eval_runs", "distill_trained_s4", "generated")
WORD = "Hamburg"
SCALE = 1.0
COLS = 2                      # font blocks per row
# Bottom row is the product configuration: distilled 4B trained on itself,
# 4 inference steps, ~7 s/atlas against the 4B base row's 62.7 s.
ROWS = [("GT", GT), ("9B", NINE), ("4B", FOUR), ("4B/4step", DIST4)]

# The fonts that actually discriminate, worst regression first, plus a control
# where the two models are indistinguishable. Labels carry the measured delta
# so the figure states its own evidence.
PICK = [
    ("FascinateInline-Regular", "Fascinate Inline", "char_acc -0.298"),
    ("BitcountPropDoubleInk", "Bitcount Prop (dot-grid)", "dinov2 -0.162"),
    ("Dangrek-Regular", "Dangrek", "char_acc -0.181"),
    ("AveriaSerifLibre-Regular", "Averia Serif Libre", "char_acc -0.085"),
    ("RubikDistressed-Regular", "Rubik Distressed", "char_acc -0.032"),
    ("Wonky", "Wonky (control)", "no change"),
]


def cell(atlas, ch):
    """Crop one character cell from a 1280x1280 atlas."""
    i = CHARSET.index(ch)
    r, c = divmod(i, GRID_COLS)
    return atlas[r * CELL_H:(r + 1) * CELL_H, c * CELL_W:(c + 1) * CELL_W]


def strip(atlas):
    """The word rendered from individual generated cells (naive spacing)."""
    return np.hstack([cell(atlas, ch) for ch in WORD])


def main():
    out_dir = ensure_out()
    cw, ch = int(CELL_W * len(WORD) * SCALE), int(CELL_H * SCALE)
    lab_w, pad, head, gap = 46, 8, 34, 30

    fonts = [f for f in PICK if all(load_atlas(d, f[0]) is not None for _, d in ROWS)]
    if not fonts:
        print("no font has all three atlases; nothing to draw")
        return

    block_w = lab_w + cw + pad
    block_h = head + len(ROWS) * (ch + pad)
    nrows = (len(fonts) + COLS - 1) // COLS
    canvas = Image.new("L", (COLS * block_w + gap * (COLS - 1) + 2 * pad,
                             nrows * block_h + gap * (nrows - 1) + 2 * pad), 255)
    d = ImageDraw.Draw(canvas)

    for i, (stem, label, delta) in enumerate(fonts):
        bx = pad + (i % COLS) * (block_w + gap)
        by = pad + (i // COLS) * (block_h + gap)
        d.text((bx, by + 4), label, font=label_font(19, bold=True), fill=0)
        d.text((bx + len(label) * 11 + 14, by + 7), delta, font=label_font(15), fill=110)
        for ri, (row_label, directory) in enumerate(ROWS):
            y = by + head + ri * (ch + pad)
            d.text((bx, y + ch // 2 - 9), row_label, font=label_font(16, bold=True), fill=0)
            img = Image.fromarray(strip(load_atlas(directory, stem)))
            canvas.paste(img.resize((cw, ch), Image.LANCZOS), (bx + lab_w, y))

    path = os.path.join(out_dir, "compare_9b_4b.png")
    canvas.save(path)
    print(f"wrote {path}  ({len(fonts)} fonts, {canvas.size[0]}x{canvas.size[1]})")


if __name__ == "__main__":
    main()
