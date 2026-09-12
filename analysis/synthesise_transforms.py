"""Applying a treatment to a REFERENCE-sized glyph, rather than an atlas cell.

Extracted so the probe that measured this and the product code that uses it
share one definition. Moved verbatim; the reference images this produces are
byte-identical to the ones `synthesised_reference_probe.py` scored.

WHY THESE ARE NOT `synthesize_rare_attributes`'s TRANSFORMS. That module's
operators are written for a 106x160 atlas cell, where a glyph is ~100px tall and
roughly uniform in stroke width. Two things break at reference scale:

  * BAND SPACING is a fraction of the array height, so handing a transform a
    whole 1024px canvas spaces the bands by the CANVAS rather than by the
    letter. Hence the ink bounding box, per glyph.
  * `_inline` thresholds against a GLOBAL `dist.max()`. On a 1024px reference
    the thickest junction of a `K` sets that peak, the stems fall below the
    threshold, and it erases 7% of the ink where it should remove roughly the
    inner half of every stroke -- a treatment that silently does almost nothing.

`synthesize_rare_attributes` is deliberately LEFT ALONE: the 10/11 classifier
result was trained on its output, so changing it would invalidate that. These
are the same IDEAS at a different scale, not the same operators, and anything
citing them should say so.
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import numpy as np
from PIL import Image
from scipy import ndimage

from analysis.synthesize_rare_attributes import TRANSFORMS, draw_params

__all__ = ["TRANSFORMS", "draw_params", "inline_at_reference_scale",
           "transform_reference"]

REF_CHARS = "Kg"


def inline_at_reference_scale(ink, spine):
    """Remove each stroke's spine, thresholding against a LOCAL ridge.

    The local maximum is taken over a window a few stroke widths wide, so every
    stroke is measured against its own thickness rather than against the
    thickest junction in the glyph.
    """
    if not ink.any():
        return ink
    dist = ndimage.distance_transform_edt(ink)
    typical = float(np.median(dist[ink]))
    size = max(3, int(typical * 4) | 1)          # a few stroke widths, odd
    local = ndimage.maximum_filter(dist, size=size)
    return ink & ~(dist >= spine * np.maximum(local, 1e-6))


def transform_reference(img, arm, params, n_cols=len(REF_CHARS)):
    """Apply a treatment to a reference image, PER GLYPH and scaled to the ink.

    Per glyph because the transforms measure against the array they are handed:
    across both letters at once, one thick junction governs the whole image.
    """
    if arm == "plain":
        return img
    arr = np.asarray(img.convert("L")).copy()
    col_w = arr.shape[1] // n_cols
    for i in range(n_cols):
        col = arr[:, i * col_w:(i + 1) * col_w]
        rows, cols = np.where(col > 128)
        if not len(rows):
            continue
        y0, y1 = rows.min(), rows.max() + 1
        x0, x1 = cols.min(), cols.max() + 1
        region = col[y0:y1, x0:x1]
        if arm == "inline":
            kept = inline_at_reference_scale(region > 128, params["spine"])
        else:
            kept = TRANSFORMS[arm](region > 128, params)
        col[y0:y1, x0:x1] = np.where(kept, region, 0)
    return Image.fromarray(arr).convert("RGB")
