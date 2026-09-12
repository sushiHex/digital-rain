"""Pin the reference gate: reject disagreeing glyphs before generating.

The model transfers whatever style it is given, so two reference glyphs that
disagree produce an atlas split along the K-like / g-like seam. Identity scored
that ABOVE a coherent control, so nothing downstream catches it. The gate
catches it at the input, for milliseconds instead of a generation.

This is a DIFFERENT statistic from analysis/style_coherence.py, and the tests
below pin that distinction: dispersion over 94 cells versus a distance between
two style vectors. Calling them one measure was loose.

The statistical claim (separates at r=0.678, predicts the atlas at rho=+0.666)
lives in research/reference_gate_validation.json, because its inputs are
gitignored GPU artifacts. These tests pin the mechanism.
"""
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.reference_gate import (REF_TARGET_H, glyph_cells,
                                     reference_consistency)
from analysis.style_coherence import load_stats
from atlas_constants import CELL_H, CELL_W

CANVAS = 1280


def reference(left_thickness, right_thickness, slant=0.0, size=CANVAS):
    """A two-column reference with independently controllable glyph weights."""
    arr = np.zeros((size, size), dtype=np.uint8)
    col = size // 2
    for i, thick in enumerate((left_thickness, right_thickness)):
        x0 = i * col + col // 2 - thick // 2
        for y in range(int(size * 0.25), int(size * 0.68)):
            x = int(x0 + slant * (y - size * 0.25)) if i == 1 else x0
            arr[y, x:x + thick] = 255
    p = Path(__file__).parent / f"_ref_{left_thickness}_{right_thickness}_{slant}.png"
    Image.fromarray(arr).save(p)
    return str(p)


@pytest.fixture
def stats():
    return load_stats()


def test_glyph_cells_are_returned_at_atlas_resolution():
    """The domain fix. Stats are fitted on 106x160 atlas cells; a reference
    column is 640x1280, and comparing across that gap is comparing nothing."""
    path = reference(40, 40)
    try:
        cells = glyph_cells(path)
        assert len(cells) == 2
        for c in cells:
            assert c is not None and c.shape == (CELL_H, CELL_W)
    finally:
        Path(path).unlink(missing_ok=True)


def test_glyphs_are_rescaled_not_merely_cropped():
    """A cropped 1280px glyph would not fit a 160px cell at all."""
    path = reference(40, 40)
    try:
        ink_rows = np.where(glyph_cells(path)[0] > 128)[0]
        height = ink_rows.max() - ink_rows.min() + 1
        assert abs(height - REF_TARGET_H) <= 6, (
            f"glyph height {height}px is not near the {REF_TARGET_H}px target")
    finally:
        Path(path).unlink(missing_ok=True)


def test_matching_glyphs_score_lower_than_disagreeing_ones(stats):
    """The gate's whole job."""
    same, differ = reference(40, 40), reference(16, 90)
    try:
        a = reference_consistency(same, stats, chars="Kg")
        b = reference_consistency(differ, stats, chars="Kg")
        assert a and b
        assert b["distance"] > a["distance"], (
            f"a 16px/90px pair scored {b['distance']:.3f}, no worse than a "
            f"matched 40px/40px pair at {a['distance']:.3f}")
    finally:
        for p in (same, differ):
            Path(p).unlink(missing_ok=True)


def test_the_worst_feature_is_reported(stats):
    """The score has to say WHY, or a user cannot act on a rejection."""
    path = reference(16, 90)
    try:
        rc = reference_consistency(path, stats, chars="Kg")
        assert set(rc["per_feature"]) >= {"stroke", "slant", "fill", "parts"}
        assert max(rc["per_feature"], key=rc["per_feature"].get) == "stroke", (
            "a pure weight mismatch should be attributed to stroke")
    finally:
        Path(path).unlink(missing_ok=True)


def test_per_character_normalisation_uses_the_named_characters(stats):
    """Each glyph is z-scored against ITS OWN character, so the same pixels
    scored as `Kg` and as `Rg` must not give the same answer. The shipped
    references render Kg while the conditioning records Rg."""
    path = reference(30, 60)
    try:
        kg = reference_consistency(path, stats, chars="Kg")
        rg = reference_consistency(path, stats, chars="Rg")
        assert kg and rg
        assert kg["distance"] != rg["distance"]
    finally:
        Path(path).unlink(missing_ok=True)


def test_a_blank_column_yields_no_score(stats):
    """An empty half must not silently score as perfectly consistent."""
    arr = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    arr[300:800, 200:260] = 255                 # left column only
    p = Path(__file__).parent / "_ref_blank.png"
    Image.fromarray(arr).save(p)
    try:
        assert reference_consistency(str(p), stats, chars="Kg") is None
    finally:
        p.unlink(missing_ok=True)
