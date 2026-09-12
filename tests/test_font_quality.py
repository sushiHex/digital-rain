from font_quality import CheckResult, QualityResult


def test_check_result_fields():
    r = CheckResult(passed=True, name="test_check", detail={"info": "ok"})
    assert r.passed is True
    assert r.name == "test_check"
    assert r.detail == {"info": "ok"}


def test_quality_result_fields():
    c1 = CheckResult(passed=True, name="a", detail={})
    c2 = CheckResult(passed=False, name="b", detail={"reason": "bad"})
    qr = QualityResult(
        passed=False,
        font_name="TestFont",
        checks=[c1, c2],
        failed=[c2],
    )
    assert qr.passed is False
    assert qr.font_name == "TestFont"
    assert len(qr.checks) == 2
    assert len(qr.failed) == 1
    assert qr.failed[0].name == "b"


from pathlib import Path
from font_quality import (
    check_blocklist, check_small_caps, check_cmap_coverage,
    check_render_visibility,
)

# Paths to real fonts in the repo's google-fonts directory.
GOOD_FONT = Path("google-fonts/ofl/abeezee/ABeeZee-Regular.ttf")
SC_FONT = Path("google-fonts/ofl/bowlbyonesc/BowlbyOneSC-Regular.ttf")
GUIDES_FONT = Path("google-fonts/ofl/playwritemxguides/PlaywriteMXGuides-Regular.ttf")


def _skip_if_missing(path):
    import pytest
    if not path.exists():
        pytest.skip(f"Font not found: {path}")


# -- check_blocklist --

def test_blocklist_passes_normal_font():
    _skip_if_missing(GOOD_FONT)
    r = check_blocklist(GOOD_FONT)
    assert r.passed is True
    assert r.name == "blocklist"


def test_blocklist_rejects_guides_font():
    _skip_if_missing(GUIDES_FONT)
    r = check_blocklist(GUIDES_FONT)
    assert r.passed is False
    assert "Playwrite.*Guides" in r.detail.get("matched_pattern", "")


def test_blocklist_rejects_sc_font():
    _skip_if_missing(SC_FONT)
    r = check_blocklist(SC_FONT)
    assert r.passed is False


# -- check_small_caps --

def test_small_caps_passes_normal_font():
    _skip_if_missing(GOOD_FONT)
    r = check_small_caps(GOOD_FONT)
    assert r.passed is True
    assert r.name == "small_caps"


def test_small_caps_rejects_sc_font():
    _skip_if_missing(SC_FONT)
    r = check_small_caps(SC_FONT)
    assert r.passed is False
    assert r.detail.get("flagged_pairs", 0) >= 3


# -- check_cmap_coverage --

def test_cmap_coverage_passes_normal_font():
    _skip_if_missing(GOOD_FONT)
    r = check_cmap_coverage(GOOD_FONT)
    assert r.passed is True
    assert r.name == "cmap_coverage"


# -- check_render_visibility --

def test_render_visibility_passes_normal_font():
    _skip_if_missing(GOOD_FONT)
    r = check_render_visibility(GOOD_FONT)
    assert r.passed is True
    assert r.name == "render_visibility"


from atlas_constants import CANVAS, DRAWN_INDICES, GRID_COLS, CELL_W, CELL_H
from font_quality import (
    check_cell_occupancy, check_baseline_consistency,
    check_duplicate_cells, check_stroke_weight,
)
from build_dataset import render_atlas
import numpy as np


def _load_atlas(font_path):
    """Render an atlas and return as (H, W) uint8 numpy array."""
    img = render_atlas(font_path, size=CANVAS)
    return np.array(img, dtype=np.uint8)


# -- check_cell_occupancy --

def test_cell_occupancy_passes_good_atlas():
    _skip_if_missing(GOOD_FONT)
    atlas = _load_atlas(GOOD_FONT)
    r = check_cell_occupancy(atlas)
    assert r.passed is True
    assert r.name == "cell_occupancy"


# -- check_baseline_consistency --

def test_baseline_passes_good_atlas():
    _skip_if_missing(GOOD_FONT)
    atlas = _load_atlas(GOOD_FONT)
    r = check_baseline_consistency(atlas)
    assert r.passed is True
    assert r.name == "baseline_consistency"


# -- check_duplicate_cells --

def test_duplicate_cells_passes_good_atlas():
    _skip_if_missing(GOOD_FONT)
    atlas = _load_atlas(GOOD_FONT)
    r = check_duplicate_cells(atlas)
    assert r.passed is True
    assert r.name == "duplicate_cells"


# -- check_stroke_weight --

def test_stroke_weight_passes_good_atlas():
    _skip_if_missing(GOOD_FONT)
    atlas = _load_atlas(GOOD_FONT)
    r = check_stroke_weight(atlas)
    assert r.passed is True
    assert r.name == "stroke_weight"


# -- synthetic failure tests --

def test_cell_occupancy_rejects_blank_atlas():
    """A fully black atlas should fail cell_occupancy."""
    blank = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    r = check_cell_occupancy(blank)
    assert r.passed is False


def test_stroke_weight_rejects_white_atlas():
    from atlas_constants import CANVAS
    white = np.full((CANVAS, CANVAS), 255, dtype=np.uint8)
    r = check_stroke_weight(white)
    assert r.passed is False


def test_duplicate_cells_rejects_uniform_atlas():
    from atlas_constants import CANVAS, DRAWN_INDICES, GRID_COLS, CELL_W, CELL_H
    atlas = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    for idx in DRAWN_INDICES:
        row, col = idx // GRID_COLS, idx % GRID_COLS
        y0, x0 = row * CELL_H + 10, col * CELL_W + 10
        atlas[y0:y0+10, x0:x0+10] = 255
    r = check_duplicate_cells(atlas)
    assert r.passed is False


from font_quality import score_font


def test_score_font_passes_good_font():
    _skip_if_missing(GOOD_FONT)
    atlas = _load_atlas(GOOD_FONT)
    qr = score_font(GOOD_FONT, atlas_np=atlas)
    assert qr.passed is True
    assert qr.font_name == GOOD_FONT.stem
    assert len(qr.failed) == 0
    assert len(qr.checks) == 8  # 4 font-level + 4 atlas-level


def test_score_font_rejects_guides():
    _skip_if_missing(GUIDES_FONT)
    qr = score_font(GUIDES_FONT, atlas_np=None, early_exit=True)
    assert qr.passed is False
    assert any(c.name == "blocklist" for c in qr.failed)
    # early_exit=True: should NOT have atlas checks since font-level failed
    assert all(c.name in ("blocklist", "small_caps", "cmap_coverage", "render_visibility")
               for c in qr.checks)


def test_score_font_no_early_exit_runs_all():
    _skip_if_missing(GUIDES_FONT)
    atlas = _load_atlas(GUIDES_FONT)
    qr = score_font(GUIDES_FONT, atlas_np=atlas, early_exit=False)
    assert qr.passed is False
    # Should have run all 8 checks even though font-level failed
    assert len(qr.checks) == 8


import subprocess
import sys


def test_audit_dataset_help():
    result = subprocess.run(
        [sys.executable, "analysis/audit_dataset.py", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--dataset-dir" in result.stdout
    assert "--dry-run" in result.stdout


def test_build_dataset_rejects_sc_font():
    """font_supports_charset should reject known SC font via font_quality."""
    _skip_if_missing(SC_FONT)
    import build_dataset
    assert build_dataset.font_supports_charset(SC_FONT) is False


def test_build_dataset_passes_good_font():
    """font_supports_charset should pass a normal font."""
    _skip_if_missing(GOOD_FONT)
    import build_dataset
    assert build_dataset.font_supports_charset(GOOD_FONT) is True


def test_build_dataset_dedup_threshold():
    """Verify build_dataset uses 0.995 cosine threshold, not 0.985."""
    import build_dataset
    import inspect
    source = inspect.getsource(build_dataset.main)
    assert "0.995" in source, "Dedup threshold should be 0.995"
    assert "0.985" not in source, "Old threshold 0.985 should be removed"


def test_baseline_consistency_rejects_jagged_atlas():
    """Atlas with vertically jittered glyphs should fail baseline check."""
    from font_quality import check_baseline_consistency
    from atlas_constants import CANVAS, DRAWN_INDICES, GRID_COLS, CELL_W, CELL_H
    atlas = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    # Alternate glyphs between top and bottom of each cell (stdev ~= CELL_H/4 >> 32px threshold)
    for idx in DRAWN_INDICES:
        row, col = idx // GRID_COLS, idx % GRID_COLS
        y0_base = row * CELL_H
        # Odd columns: near top; even columns: near bottom — guaranteed large stdev per row
        if col % 2 == 0:
            y_start = y0_base + 5
        else:
            y_start = y0_base + CELL_H - 15
        x0 = col * CELL_W + 10
        atlas[y_start:y_start + 10, x0:x0 + 20] = 255
    r = check_baseline_consistency(atlas)
    assert r.passed is False


def test_score_font_rejects_float_atlas():
    """score_font should reject float32 atlas arrays (must be uint8)."""
    import pytest
    _skip_if_missing(GOOD_FONT)
    float_atlas = np.zeros((CANVAS, CANVAS), dtype=np.float32)
    with pytest.raises(ValueError, match="uint8"):
        score_font(GOOD_FONT, atlas_np=float_atlas)


def test_score_font_rejects_wrong_size_atlas():
    """score_font should reject atlases that aren't CANVAS x CANVAS."""
    import pytest
    _skip_if_missing(GOOD_FONT)
    small_atlas = np.zeros((512, 512), dtype=np.uint8)
    with pytest.raises(ValueError, match="shape"):
        score_font(GOOD_FONT, atlas_np=small_atlas)
