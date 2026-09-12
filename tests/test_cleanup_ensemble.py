import numpy as np
from cleanup.ensemble import select_best_cells
from cleanup.cells import crop_cell, paste_cell
from atlas_constants import CANVAS, DRAWN_INDICES

def test_picks_ocr_correct_cell_per_position():
    drawn = DRAWN_INDICES[:3]
    expected = {i: "A" for i in drawn}
    a0 = np.zeros((CANVAS, CANVAS, 3), dtype=np.uint8)
    a1 = np.zeros((CANVAS, CANVAS, 3), dtype=np.uint8)
    for k, idx in enumerate(drawn):
        paste_cell(a0, idx, np.full((6, 6, 3), 10 if k == 0 else 20, dtype=np.uint8))
        paste_cell(a1, idx, np.full((6, 6, 3), 10 if k != 0 else 20, dtype=np.uint8))
    def ocr_fn(cell): return "A" if int(cell[0, 0, 0]) == 10 else "X"  # 10 == correct
    out = select_best_cells([a0, a1], expected=expected, ocr_fn=ocr_fn, drawn_indices=drawn)
    for idx in drawn:
        assert int(crop_cell(out, idx)[0, 0, 0]) == 10

def test_falls_back_to_sharpest_when_none_correct():
    drawn = DRAWN_INDICES[:1]
    expected = {drawn[0]: "A"}
    a0 = np.zeros((CANVAS, CANVAS, 3), dtype=np.uint8)
    a1 = np.zeros((CANVAS, CANVAS, 3), dtype=np.uint8)
    paste_cell(a0, drawn[0], np.full((8, 8, 3), 30, dtype=np.uint8))
    paste_cell(a1, drawn[0], np.full((8, 8, 3), 40, dtype=np.uint8))
    def ocr_fn(cell): return "none-correct"
    sharp = lambda cell: float(cell[0, 0, 0])  # a1's cell is "sharper"
    out = select_best_cells([a0, a1], expected=expected, ocr_fn=ocr_fn,
                            drawn_indices=drawn, sharpness_fn=sharp)
    assert int(crop_cell(out, drawn[0])[0, 0, 0]) == 40
