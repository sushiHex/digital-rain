import numpy as np
from PIL import Image
from atlas_constants import GRID_COLS, CELL_W, CELL_H
from eval_checkpoint import crop_cell  # reuse the canonical crop (same cell math)

__all__ = ["crop_cell", "paste_cell"]

def paste_cell(atlas: np.ndarray, idx: int, patch: np.ndarray) -> None:
    """Write `patch` into atlas cell `idx` in place (inverse of crop_cell).

    Resizes patch to the cell size if it differs (cropped-inpaint returns a
    small canvas)."""
    row, col = idx // GRID_COLS, idx % GRID_COLS
    y0, x0 = row * CELL_H, col * CELL_W
    if patch.shape[:2] != (CELL_H, CELL_W):
        patch = np.array(Image.fromarray(patch).resize((CELL_W, CELL_H), Image.LANCZOS))
    atlas[y0:y0 + CELL_H, x0:x0 + CELL_W] = patch
