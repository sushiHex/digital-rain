from atlas_constants import DRAWN_INDICES
from cleanup.cells import crop_cell, paste_cell
from generate_atlas import score_glyph_cell as _score_glyph_cell  # Laplacian sharpness (existing)
from PIL import Image
import numpy as np


def _sharpness_default(cell: np.ndarray) -> float:
    """Wrap score_glyph_cell (PIL-based) to accept a numpy array."""
    return _score_glyph_cell(Image.fromarray(cell))


def select_best_cells(atlases, *, expected, ocr_fn, drawn_indices=DRAWN_INDICES,
                      sharpness_fn=None):
    """Composite one atlas by choosing, per cell position, the variant whose OCR
    reads as the expected char (tie-break on sharpness); if none is correct,
    take the sharpest."""
    if sharpness_fn is None:
        sharpness_fn = _sharpness_default
    base = atlases[0].copy()
    for idx in drawn_indices:
        cands = [crop_cell(a, idx) for a in atlases]
        correct = [c for c in cands if ocr_fn(c) == expected[idx]]
        pool = correct if correct else cands
        best = max(pool, key=sharpness_fn)
        paste_cell(base, idx, best)
    return base
