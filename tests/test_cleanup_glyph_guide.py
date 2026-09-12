import numpy as np
from cleanup.glyph_guide import render_neutral_glyph
from atlas_constants import CELL_W, CELL_H

def test_renders_white_on_black_correct_size():
    cell = render_neutral_glyph("A")
    assert cell.shape == (CELL_H, CELL_W, 3)
    assert cell.max() > 200          # has bright glyph pixels
    assert cell.mean() < 128         # mostly black background

def test_blank_for_space():
    cell = render_neutral_glyph(" ")
    assert cell.max() == 0           # nothing drawn for space
