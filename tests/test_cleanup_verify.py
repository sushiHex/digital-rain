import numpy as np
from cleanup.verify import verify_atlas
from atlas_constants import CANVAS, DRAWN_INDICES, CHARSET

def _fake_atlas():
    return np.zeros((CANVAS, CANVAS, 3), dtype=np.uint8)

def test_flags_only_ocr_fail_and_style_outlier():
    atlas = _fake_atlas()
    drawn = DRAWN_INDICES[:5]
    bad_idx = drawn[2]
    from cleanup.cells import paste_cell
    paste_cell(atlas, bad_idx, np.full((4, 4, 3), 99, dtype=np.uint8))
    def ocr_fn(cell): return "?" if cell[0, 0, 0] == 99 else "OK_SENTINEL"
    expected = {i: ("X" if i == bad_idx else "OK_SENTINEL") for i in drawn}
    def embed_fn(cells):
        embs = np.tile(np.array([1.0, 0.0]), (len(cells), 1))
        embs[2] = np.array([50.0, 0.0])  # bad_idx is index 2 within the drawn slice
        return embs
    verdicts = verify_atlas(atlas, expected=expected, ocr_fn=ocr_fn,
                            embed_fn=embed_fn, drawn_indices=drawn)
    assert [v.index for v in verdicts if v.flagged] == [bad_idx]

def test_ocr_fail_but_in_style_is_not_flagged():
    atlas = _fake_atlas()
    drawn = DRAWN_INDICES[:4]
    expected = {i: "Z" for i in drawn}
    def ocr_fn(cell): return "wrong"   # everything fails OCR
    def embed_fn(cells): return np.tile(np.array([1.0, 1.0]), (len(cells), 1))  # all in-cluster
    verdicts = verify_atlas(atlas, expected=expected, ocr_fn=ocr_fn,
                            embed_fn=embed_fn, drawn_indices=drawn)
    assert [v.index for v in verdicts if v.flagged] == []
