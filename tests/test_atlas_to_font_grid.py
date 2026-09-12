"""Tests for building a font from a *trained-model* atlas.

app.py used to run the superseded Ref2Font V3 geometry (71 chars, inferred
near-square grid) against atlases the trained model emits on the fixed 12x8
grid of atlas_constants -- wrong charset and wrong pixels. It also would have
produced an unloadable font: 33 of the 95 characters, digits included, mapped
to glyph names OpenType does not allow.
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from atlas_constants import BLANK_INDICES, CELL_H, CELL_W, CHARSET
from atlas_to_font import _char_to_glyph_name, build_font, trace_atlas_cells

# An OpenType glyph name: starts with a letter or underscore, then letters,
# digits, periods and underscores.
GLYPH_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9._]*")


def test_every_charset_char_has_a_valid_glyph_name():
    bad = [c for c in CHARSET if not GLYPH_NAME.fullmatch(_char_to_glyph_name(c))]
    assert bad == [], f"invalid OpenType glyph names for: {bad}"


def test_glyph_names_are_unique_across_the_charset():
    seen = {}
    for c in CHARSET:
        name = _char_to_glyph_name(c)
        assert name not in seen, f"{c!r} and {seen[name]!r} both map to {name!r}"
        seen[name] = c


def test_build_font_survives_the_space_cell():
    # CHARSET contains ' ', and build_font pre-defines a "space" glyph. Emitting
    # it twice makes FontBuilder raise on a duplicate glyph name.
    cells = [[] for _ in CHARSET]
    font = build_font(cells, CHARSET, CELL_W, CELL_H, font_name="T")
    order = font.getGlyphOrder()
    assert len(order) == len(set(order)), "duplicate glyph names in glyph order"
    assert order.count("space") == 1


def _potrace_or_skip():
    from atlas_to_font import setup_potrace
    try:
        return setup_potrace()
    except FileNotFoundError:
        pytest.skip("potrace binary not available")


def test_trace_atlas_cells_is_index_aligned_with_charset():
    from render_glyph_template import render_glyph_template

    potrace = _potrace_or_skip()
    cells = trace_atlas_cells(render_glyph_template(), potrace_bin=potrace)

    assert len(cells) == len(CHARSET)
    for idx in BLANK_INDICES:
        if idx < len(CHARSET):
            assert cells[idx] == [], f"blank cell {idx} should trace to nothing"
    # The template is a clean render of every drawn glyph, so tracing it should
    # find ink nearly everywhere. A wrong grid slices between cells and leaves
    # most of them empty -- that is the failure this guards.
    drawn = sum(1 for i, c in enumerate(cells) if c and i not in BLANK_INDICES)
    assert drawn >= len(CHARSET) - len(BLANK_INDICES) - 5, (
        f"only {drawn} of {len(CHARSET)} cells traced -- grid geometry is wrong"
    )


def test_template_atlas_builds_a_loadable_font(tmp_path):
    from fontTools.ttLib import TTFont
    from render_glyph_template import render_glyph_template

    potrace = _potrace_or_skip()
    cells = trace_atlas_cells(render_glyph_template(), potrace_bin=potrace)
    font = build_font(cells, CHARSET, CELL_W, CELL_H, font_name="GridTest")

    out = tmp_path / "gridtest.otf"
    font.save(out)
    reloaded = TTFont(out)

    cmap = reloaded.getBestCmap()
    # Digits and punctuation are the characters the old name map got wrong.
    for ch in "0123456789@#$%&()[]{}<>|\\~^`":
        assert ord(ch) in cmap, f"{ch!r} missing from cmap"
    assert cmap[ord("0")] == "zero"
    assert cmap[ord("\\")] == "backslash"


def test_cli_defaults_to_the_trained_model_grid_and_charset():
    """The CLI must not slice a trained-model atlas with compute_grid().

    Regression: main() called compute_grid() unconditionally, cropped SQUARE
    cells, and passed cell_size for both dimensions -- the superseded Ref2Font
    V3 geometry that CLAUDE.md explicitly forbids for these atlases. It
    produced a technically-valid OTF built from mis-sliced pixels, silently.

    A second half to the same bug: --charset still defaulted to the 71-char V3
    set while the grid yields 95 cells aligned to the atlas charset. The two
    agree on A-Z/a-z/0-9 and then diverge, so punctuation was mislabeled.
    """
    import atlas_to_font
    from atlas_constants import CHARSET as ATLAS_CHARSET

    # main() resolves the default at parse time; assert the rule in its source.
    import inspect
    src = inspect.getsource(atlas_to_font.main)
    assert "--legacy-square-grid" in src, "legacy escape hatch missing"
    assert "trace_atlas_cells(" in src, "CLI no longer uses the fixed-grid tracer"
    assert "CELL_W, CELL_H" in src or "cell_w, cell_h" in src, \
        "CLI must pass rectangular cell dims, not one square size"
    # the charset default must follow the grid mode
    assert "ATLAS_CHARSET" in src and "args.legacy_square_grid" in src, \
        "charset default must depend on the grid mode"
    assert len(ATLAS_CHARSET) == 95
