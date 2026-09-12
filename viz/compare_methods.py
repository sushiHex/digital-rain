"""Compact 4-method glyph comparison, sized for embedding in a report page.

Rows: ground truth, the shipped 9B, the 4B with uniform sampling, and the 4B
with distinctiveness-weighted sampling. Fonts chosen to show where the methods
actually diverge, plus a control where they do not.

Deliberately small: this is meant to be base64-inlined into an HTML artifact,
where a full-size atlas strip would add megabytes.

  python viz/compare_methods.py
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atlas_constants import CELL_H, CELL_W, CHARSET, GRID_COLS
from viz._common import GT, ensure_out, label_font, load_atlas

ROWS = [
    ("GT", GT),
    ("9B", os.path.join("eval_runs", "prompt_trained_short", "generated")),
    ("4B", os.path.join("eval_runs", "glyph_4b_r32_5000", "generated")),
    ("4B+w", os.path.join("eval_runs", "glyph_4b_distinct_5000", "generated")),
]

# char_acc uniform -> weighted, with the 9B for reference.
PICK = [
    ("BitcountGridDoubleInk", "Bitcount Grid", "0.074 → 0.191   (9B 0.138)"),
    ("FascinateInline-Regular", "Fascinate Inline", "0.191 → 0.287   (9B 0.489)"),
    ("Dangrek-Regular", "Dangrek", "0.511 → 0.649   (9B 0.691)"),
    ("Wonky", "Wonky — control", "0.872 → 0.830   (9B 0.840)"),
]

WORD = "Hamburg"
SCALE = 0.46


def strip(atlas):
    out = []
    for ch in WORD:
        i = CHARSET.index(ch)
        r, c = divmod(i, GRID_COLS)
        out.append(atlas[r * CELL_H:(r + 1) * CELL_H, c * CELL_W:(c + 1) * CELL_W])
    return np.hstack(out)


def main():
    out_dir = ensure_out()
    cw, ch = int(CELL_W * len(WORD) * SCALE), int(CELL_H * SCALE)
    lab_w, pad, head, gap = 40, 5, 30, 20

    fonts = [f for f in PICK if all(load_atlas(d, f[0]) is not None for _, d in ROWS)]
    if not fonts:
        print("no font has all four atlases")
        return

    block_h = head + len(ROWS) * (ch + pad)
    canvas = Image.new("L", (lab_w + cw + 2 * pad,
                             len(fonts) * block_h + gap * (len(fonts) - 1) + 2 * pad), 255)
    d = ImageDraw.Draw(canvas)

    for i, (stem, label, delta) in enumerate(fonts):
        by = pad + i * (block_h + gap)
        d.text((pad, by + 2), label, font=label_font(15, bold=True), fill=0)
        d.text((pad + len(label) * 8 + 12, by + 4), delta, font=label_font(12), fill=120)
        for ri, (row_label, directory) in enumerate(ROWS):
            y = by + head + ri * (ch + pad)
            d.text((pad, y + ch // 2 - 7), row_label, font=label_font(12, bold=True), fill=0)
            img = Image.fromarray(strip(load_atlas(directory, stem)))
            canvas.paste(img.resize((cw, ch), Image.LANCZOS), (lab_w, y))

    path = os.path.join(out_dir, "compare_methods.png")
    canvas.save(path, optimize=True)
    print(f"wrote {path}  {canvas.size}  {os.path.getsize(path) // 1024} KB")


if __name__ == "__main__":
    main()
