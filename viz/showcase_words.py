"""Compose a real word from the GENERATED glyph cells, side-by-side with the
same word from ground truth, for the most stylized holdout fonts.

Far more legible than showing raw 12x8 atlas grids: crops each glyph to its
ink bbox and sets them on a shared baseline with a fixed gap (note: this is
naive spacing, NOT kerned -- which is exactly the metrics gap the research
flagged).
"""

# repo root on sys.path so `python viz/x.py` works as well as `-m viz.x`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import glob
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from viz._common import FONTS, GEN, GT, ensure_out, label_font, load_atlas
from atlas_constants import CHARSET
from eval_checkpoint import crop_cell


WORD = "Hamburg"

# (font stem, friendly label, char_acc) — ordered best -> hardest

H = 150          # target glyph height
GAP = 10
PAD = 16
LABEL_W = 300


def ink_crop(cell):
    """cell: 2D uint8, white glyph on black. Crop to ink, scale to height H."""
    if cell.ndim == 3:
        cell = cell[..., 0]
    ys, xs = np.where(cell > 40)
    if len(ys) == 0:
        return None, 0
    c = cell[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    # keep vertical position info: where the ink sits within the cell
    top_frac = ys.min() / cell.shape[0]
    im = Image.fromarray(c)
    scale = H / cell.shape[0]           # scale by CELL height so relative sizes hold
    nw, nh = max(1, int(c.shape[1] * scale)), max(1, int(c.shape[0] * scale))
    return im.resize((nw, nh), Image.LANCZOS), top_frac


def render_word(atlas, word):
    """Returns a PIL L-mode image of the word, glyphs on a shared baseline."""
    glyphs = []
    for ch in word:
        idx = CHARSET.index(ch)
        g, top_frac = ink_crop(crop_cell(atlas, idx))
        glyphs.append((g, top_frac))
    total_w = sum(g.width + GAP for g, _ in glyphs if g) + GAP
    canvas = Image.new("L", (max(total_w, 10), H + 40), 0)
    x = GAP
    for g, top_frac in glyphs:
        if g is None:
            x += 30
            continue
        y = int(top_frac * H) + 8
        canvas.paste(g, (x, y))
        x += g.width + GAP
    return canvas


rows = []
for stem, label, acc in FONTS:
    gt_a, gen_a = load_atlas(GT, stem), load_atlas(GEN, stem)
    if gt_a is None or gen_a is None:
        print(f"  skip {stem}: gt={gt_a is not None} gen={gen_a is not None}")
        continue
    rows.append((label, acc, render_word(gt_a, WORD), render_word(gen_a, WORD)))

row_h = H + 60
W = LABEL_W + 2 * (max(max(g.width for _, _, g, _ in rows), max(g.width for _, _, _, g in rows)) + 30) + PAD
canvas = Image.new("RGB", (W, 96 + len(rows) * row_h + PAD), (250, 250, 252))
d = ImageDraw.Draw(canvas)
TITLE, LAB, SUB = label_font(30, True), label_font(19, True), label_font(15)

d.text((PAD, 20), "Stylized holdout fonts — ground truth vs generated", font=TITLE, fill=(18, 20, 28))
d.text((PAD, 58), "The model never saw these fonts. Word composed from individual generated glyph cells "
                  "(naive spacing, not kerned).", font=SUB, fill=(95, 100, 115))

col1 = LABEL_W
col2 = LABEL_W + max(g.width for _, _, g, _ in rows) + 30
d.text((col1, 78), "GROUND TRUTH", font=SUB, fill=(120, 125, 140))
d.text((col2, 78), "GENERATED", font=SUB, fill=(120, 125, 140))

y = 96
for label, acc, gt_img, gen_img in rows:
    d.text((PAD, y + 30), label, font=LAB, fill=(28, 32, 44))
    d.text((PAD, y + 56), f"char_acc {acc:.3f}", font=SUB, fill=(130, 135, 150))
    for col, img in ((col1, gt_img), (col2, gen_img)):
        rgb = Image.eval(img, lambda p: 255 - p).convert("RGB")   # black ink on white
        canvas.paste(rgb, (col, y + 10))
    d.line([(PAD, y + row_h - 6), (W - PAD, y + row_h - 6)], fill=(225, 228, 235))
    y += row_h

out = ensure_out()
canvas.save(f"{out}/stylized_showcase.png")
print(f"wrote stylized_showcase.png  ({len(rows)} fonts, {canvas.width}x{canvas.height})")
