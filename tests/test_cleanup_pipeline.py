import numpy as np
from cleanup.pipeline import run_cleanup, CleanedAtlas
from cleanup.cells import crop_cell, paste_cell
from cleanup.inpaint import NeutralPasteRepairer
from cleanup.types import Provenance
from atlas_constants import CANVAS, DRAWN_INDICES

def _atlas(fill=0):
    return np.full((CANVAS, CANVAS, 3), fill, dtype=np.uint8)

def test_fast_mode_inpaints_only_flagged():
    drawn = DRAWN_INDICES[:4]
    expected = {i: "A" for i in drawn}
    bad = drawn[1]
    def generate_fn(seed):
        a = _atlas()
        for i in drawn:
            paste_cell(a, i, np.full((6, 6, 3), 10, dtype=np.uint8))
        paste_cell(a, bad, np.full((6, 6, 3), 99, dtype=np.uint8))
        return a
    def ocr_fn(cell): return "A" if int(cell[0, 0, 0]) == 10 else "X"
    def embed_fn(cells):
        e = np.tile(np.array([1.0, 0.0]), (len(cells), 1))
        e[1] = np.array([50.0, 0.0])  # bad cell (drawn index 1) is outlier
        return e
    res = run_cleanup(generate_fn=generate_fn, mode="FAST", expected=expected,
                      ocr_fn=ocr_fn, embed_fn=embed_fn, repairer=NeutralPasteRepairer(),
                      drawn_indices=drawn)
    assert isinstance(res, CleanedAtlas)
    assert res.provenance[bad] == Provenance.INPAINTED
    assert res.provenance[drawn[0]] == Provenance.ORIGINAL
    assert crop_cell(res.atlas, bad).max() > 200

def test_quality_mode_runs_n_and_marks_ensemble():
    drawn = DRAWN_INDICES[:2]
    expected = {i: "A" for i in drawn}
    calls = []
    def generate_fn(seed):
        calls.append(seed)
        a = _atlas()
        for i in drawn:
            paste_cell(a, i, np.full((6, 6, 3), 10, dtype=np.uint8))
        return a
    def ocr_fn(cell): return "A"
    def embed_fn(cells): return np.tile(np.array([1.0, 0.0]), (len(cells), 1))
    res = run_cleanup(generate_fn=generate_fn, mode="QUALITY", expected=expected,
                      ocr_fn=ocr_fn, embed_fn=embed_fn, repairer=NeutralPasteRepairer(),
                      drawn_indices=drawn, n_quality=3, seed=42)
    assert len(calls) == 3 and calls == [42, 43, 44]
    assert all(res.provenance[i] in (Provenance.ENSEMBLE, Provenance.INPAINTED) for i in drawn)
