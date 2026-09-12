import numpy as np
from cleanup.cells import crop_cell, paste_cell
from atlas_constants import CANVAS, DRAWN_INDICES

def test_paste_then_crop_roundtrip():
    atlas = np.zeros((CANVAS, CANVAS, 3), dtype=np.uint8)
    idx = DRAWN_INDICES[10]
    cell = crop_cell(atlas, idx)
    patch = np.full_like(cell, 200)
    paste_cell(atlas, idx, patch)
    assert np.array_equal(crop_cell(atlas, idx), patch)

def test_paste_resizes_mismatched_patch():
    atlas = np.zeros((CANVAS, CANVAS, 3), dtype=np.uint8)
    idx = DRAWN_INDICES[0]
    target = crop_cell(atlas, idx)
    small = np.full((target.shape[0] // 2, target.shape[1] // 2, 3), 255, dtype=np.uint8)
    paste_cell(atlas, idx, small)  # must not raise; resizes to cell
    assert crop_cell(atlas, idx).shape == target.shape
