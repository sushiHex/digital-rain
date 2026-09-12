import numpy as np

from render_glyph_template import render_glyph_template
from atlas_constants import CANVAS, CHARSET, GRID_COLS
from eval_checkpoint import crop_cell  # canonical Kg crop


def test_template_has_glyphs_in_drawn_cells():
    a = np.asarray(render_glyph_template().convert("RGB"))
    assert a.shape == (CANVAS, CANVAS, 3)
    drawn = [i for i, ch in enumerate(CHARSET) if ch != " "]
    inked = sum(crop_cell(a, i).mean() > 1.0 for i in drawn)
    assert inked >= 0.9 * len(drawn)   # almost every non-space cell has ink
