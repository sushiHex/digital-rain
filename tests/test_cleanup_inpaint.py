import numpy as np
from cleanup.inpaint import NeutralPasteRepairer
from atlas_constants import CELL_W, CELL_H

def test_neutral_paste_returns_cell_sized_glyph():
    rep = NeutralPasteRepairer()
    bad = np.zeros((CELL_H, CELL_W, 3), dtype=np.uint8)
    out = rep.repair(bad, "A", context_atlas=None)
    assert out.shape == (CELL_H, CELL_W, 3)
    assert out.max() > 200  # drew the glyph
