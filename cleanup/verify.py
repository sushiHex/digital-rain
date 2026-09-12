import numpy as np
from atlas_constants import DRAWN_INDICES
from cleanup.cells import crop_cell
from cleanup.types import CellVerdict, STYLE_Z_THRESH

def verify_atlas(atlas, *, expected, ocr_fn, embed_fn,
                 drawn_indices=DRAWN_INDICES, style_z_thresh=STYLE_Z_THRESH):
    """Flag a cell only when it BOTH fails OCR AND is a style/shape outlier
    (over-correction guard). Returns a CellVerdict per drawn cell."""
    cells = [crop_cell(atlas, i) for i in drawn_indices]
    embs = np.asarray(embed_fn(cells), dtype=np.float64)
    centroid = np.median(embs, axis=0)
    dists = np.linalg.norm(embs - centroid, axis=1)
    med = np.median(dists)
    mad = np.median(np.abs(dists - med)) + 1e-9
    z = (dists - med) / mad
    verdicts = []
    for k, idx in enumerate(drawn_indices):
        ocr = ocr_fn(cells[k])
        ocr_pass = (ocr == expected[idx])
        flagged = (not ocr_pass) and (z[k] >= style_z_thresh)
        verdicts.append(CellVerdict(idx, expected[idx], ocr, ocr_pass, float(z[k]), flagged))
    return verdicts
