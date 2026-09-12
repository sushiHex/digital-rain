from dataclasses import dataclass
import numpy as np
from atlas_constants import DRAWN_INDICES
from cleanup.cells import crop_cell, paste_cell
from cleanup.ensemble import select_best_cells
from cleanup.verify import verify_atlas
from cleanup.types import Provenance, DEFAULT_QUALITY_N

@dataclass
class CleanedAtlas:
    atlas: np.ndarray
    provenance: dict          # idx -> Provenance.*
    verdicts: list            # list[CellVerdict]

def run_cleanup(*, generate_fn, mode, expected, ocr_fn, embed_fn, repairer,
                drawn_indices=DRAWN_INDICES, n_quality=DEFAULT_QUALITY_N, seed=42):
    """FAST: 1 pass -> verify -> inpaint flagged. QUALITY: N passes -> best-of-N
    -> verify -> inpaint residual. Returns the cleaned atlas + per-cell provenance."""
    if mode == "QUALITY":
        atlases = [generate_fn(seed + i) for i in range(n_quality)]
        atlas = select_best_cells(atlases, expected=expected, ocr_fn=ocr_fn,
                                  drawn_indices=drawn_indices)
        provenance = {i: Provenance.ENSEMBLE for i in drawn_indices}
    elif mode == "FAST":
        atlas = generate_fn(seed)
        provenance = {i: Provenance.ORIGINAL for i in drawn_indices}
    else:
        raise ValueError(f"unknown mode {mode!r} (expected 'FAST' or 'QUALITY')")

    verdicts = verify_atlas(atlas, expected=expected, ocr_fn=ocr_fn,
                            embed_fn=embed_fn, drawn_indices=drawn_indices)
    for v in verdicts:
        if v.flagged:
            repaired = repairer.repair(crop_cell(atlas, v.index), expected[v.index], atlas)
            paste_cell(atlas, v.index, repaired)
            provenance[v.index] = Provenance.INPAINTED
    return CleanedAtlas(atlas=atlas, provenance=provenance, verdicts=verdicts)
