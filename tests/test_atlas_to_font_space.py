"""Pin the space advance to a typographic quantity, not half a grid cell.

The space is the one glyph nothing is ever traced for -- it is a BLANK cell by
construction -- so its advance is assigned rather than measured, and no
atlas-space metric can see it being wrong. It was `cell_w * scale * 0.5`, which
produced 0.49-0.54 em against a 0.2635 em mean across the 50 holdout source
fonts. Every font this project generated set running text at roughly DOUBLE word
spacing, for its whole life, invisibly.

Found by `analysis/score_finished_font.py`, which scores the traced OTF instead
of the atlas: the space was the single worst glyph in 42 of 50 fonts.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from atlas_constants import BLANK_INDICES, CELL_H, CELL_W, CHARSET
from atlas_to_font import SPACE_FALLBACK_EM, SPACE_TO_LOWERCASE, build_font

UPM = 1000


def box(x0, y0, x1, y1):
    """One rectangular subpath in the (cmd, points) form the tracer emits."""
    return [[("M", [(x0, y0)]), ("L", [(x1, y0)]), ("L", [(x1, y1)]),
             ("L", [(x0, y1)]), ("Z", [])]]


# build_dataset binary-searches a per-font pixel size that FITS the 160px cell,
# so real cap heights land at 55-93px. The geometry below has to sit in that
# range or the test proves nothing: at a 100px cap the OLD half-cell rule yields
# 0.371 em, which would slip under any sane "not double spacing" threshold. At a
# realistic 70px cap it yields 0.530 em, which is the bug as it actually shipped.
BASELINE_Y, CAP_TOP_Y, XHEIGHT_TOP_Y = 130, 60, 85


def old_space_em(upm=UPM):
    """What `cell_w * scale * 0.5` produced for this synthetic geometry."""
    scale = 0.70 * upm / (BASELINE_Y - CAP_TOP_Y)
    return CELL_W * scale * 0.5 / upm


def synthetic_cells(lower_width=40, upper_width=60):
    """Index-aligned cells: uppercase set the cap metrics, lowercase the space."""
    cells = []
    for i, ch in enumerate(CHARSET):
        if i in BLANK_INDICES or not ch.isalpha():
            cells.append([])
        elif ch.isupper():
            cells.append(box(20, CAP_TOP_Y, 20 + upper_width, BASELINE_Y))
        else:
            cells.append(box(20, XHEIGHT_TOP_Y, 20 + lower_width, BASELINE_Y))
    return cells


def space_em(font):
    upm = font["head"].unitsPerEm
    return font["hmtx"].metrics["space"][0] / upm


def build(cells):
    return build_font(cells, CHARSET, CELL_W, CELL_H, upm=UPM)


def test_the_synthetic_geometry_reproduces_the_old_bug():
    """Guard the guard: if this drifts, every test below stops proving anything."""
    assert 0.45 < old_space_em() < 0.60, (
        f"synthetic cap height no longer reproduces the shipped bug "
        f"({old_space_em():.3f} em); real fonts trace at 55-93px cap")


def test_space_is_not_half_a_grid_cell():
    """Pinned against the actual old formula, not an absolute threshold."""
    got = space_em(build(synthetic_cells()))
    assert got < 0.6 * old_space_em(), (
        f"space is {got:.3f} em against the half-cell rule's "
        f"{old_space_em():.3f} em -- the ~2x word spacing is back")


def test_space_is_in_a_typographic_range():
    """Real fonts sit at 0.13-0.60 em, mean 0.2635, across the 50 holdout faces."""
    assert 0.12 <= space_em(build(synthetic_cells())) <= 0.45


def test_space_scales_with_the_font_s_own_lowercase():
    """Font-adaptive, not a constant: a wider lowercase gets a wider space."""
    narrow = space_em(build(synthetic_cells(lower_width=25)))
    wide = space_em(build(synthetic_cells(lower_width=70)))
    assert wide > narrow * 1.3, (
        f"space did not track lowercase width: {narrow:.3f} -> {wide:.3f} em")


def test_space_ignores_uppercase_width():
    """Derived from lowercase specifically; caps must not move it."""
    a = space_em(build(synthetic_cells(upper_width=40)))
    b = space_em(build(synthetic_cells(upper_width=95)))
    assert abs(a - b) < 0.02, f"uppercase width moved the space: {a:.3f} vs {b:.3f}"


def test_space_falls_back_when_no_lowercase_is_readable():
    """A font whose lowercase all failed to trace still needs a sane space."""
    cells = [[] if (i in BLANK_INDICES or not CHARSET[i].isupper())
             else box(20, 30, 80, 130)
             for i in range(len(CHARSET))]
    assert abs(space_em(build(cells)) - SPACE_FALLBACK_EM) < 0.01


def test_fit_constants_are_the_ones_that_were_measured():
    """Pin the fitted values so a later edit has to restate the measurement."""
    assert SPACE_TO_LOWERCASE == 0.50
    assert SPACE_FALLBACK_EM == 0.26
