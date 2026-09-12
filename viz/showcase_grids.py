"""Full 94-glyph character grid (the raw atlas) for each stylized holdout font,
ground truth beside generated. One PNG per font, black-on-white with cell
gridlines so individual glyphs are inspectable.
"""

# repo root on sys.path so `python viz/x.py` works as well as `-m viz.x`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import glob
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from viz._common import FONTS, GEN, GT, ensure_out, label_font, load_atlas
from atlas_constants import CANVAS, GRID_COLS, GRID_ROWS, CELL_W, CELL_H



PANEL_W = 660                      # rendered width of each atlas panel
PAD, TOP = 18, 100
GRID_RGB = (222, 226, 234)


def panel(atlas):
    """White-glyph-on-black atlas -> black-on-white PIL RGB, scaled, gridlines."""
    a = atlas[:GRID_ROWS * CELL_H, :GRID_COLS * CELL_W]
    im = Image.fromarray(a)
    im = Image.eval(im, lambda p: 255 - p).convert("RGB")
    scale = PANEL_W / im.width
    im = im.resize((PANEL_W, int(im.height * scale)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    cw, ch = PANEL_W / GRID_COLS, im.height / GRID_ROWS
    for c in range(1, GRID_COLS):
        d.line([(c * cw, 0), (c * cw, im.height)], fill=GRID_RGB)
    for r in range(1, GRID_ROWS):
        d.line([(0, r * ch), (PANEL_W, r * ch)], fill=GRID_RGB)
    d.rectangle([0, 0, im.width - 1, im.height - 1], outline=(200, 204, 214))
    return im


TITLE, LAB, SUB = label_font(26, True), label_font(17, True), label_font(14)
written = []
for stem, label, acc in FONTS:
    gt_a, gen_a = load_atlas(GT, stem), load_atlas(GEN, stem)
    if gt_a is None or gen_a is None:
        print(f"  skip {stem}")
        continue
    p_gt, p_gen = panel(gt_a), panel(gen_a)
    W = PAD * 3 + PANEL_W * 2
    H = TOP + p_gt.height + PAD + 24
    c = Image.new("RGB", (W, H), (250, 250, 252))
    d = ImageDraw.Draw(c)
    d.text((PAD, 16), f"{label}  —  full 94-glyph grid", font=TITLE, fill=(18, 20, 28))
    d.text((PAD, 48), f"char_acc {acc:.3f}   ·   holdout font, never seen in training",
           font=SUB, fill=(110, 115, 130))
    d.text((PAD, TOP - 24), "GROUND TRUTH", font=LAB, fill=(120, 125, 140))
    d.text((PAD * 2 + PANEL_W, TOP - 24), "GENERATED", font=LAB, fill=(120, 125, 140))
    c.paste(p_gt, (PAD, TOP))
    c.paste(p_gen, (PAD * 2 + PANEL_W, TOP))
    safe = stem.split("[")[0]
    path = f"{ensure_out()}/grid_{safe}.png"
    c.save(path)
    written.append(path)
    print(f"  wrote grid_{safe}.png  ({c.width}x{c.height})")

print(f"\n{len(written)} grids written")
