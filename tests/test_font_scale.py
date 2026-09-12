"""The produced font must set at a normal size, and not blow up line height.

`build_font` used `scale = upm / cell_h`, which assumes the em equals the 160px
atlas cell. It does not: `build_dataset` binary-searches a per-font pixel size
that FITS the cell (measured 55-93px, width-bound on 48 of 50 holdout fonts).

Measured end-to-end on GROUND-TRUTH atlases, where model error is exactly zero,
that produced a median cap height of **0.422 em against a source median of
0.703** -- every generated font set ~41% too small at any point size. No metric
in the repo could see it: everything is scored on atlas cells, and the defect is
introduced after scoring, when cells become an OTF.

MEASURED AFTER THE FIX, on ground-truth atlases:

    cap height vs source   0.588 -> 0.989
    advance width vs source  ~0.67 -> 1.024
    line height              would have hit ~1.7 em -> exactly 1.00 em

The advance widths were corrected as a side effect: advance is
`content_w * scale + 2 * side_bearing`, so fixing the scale fixed them too.

WHAT REMAINS UNFIXABLE HERE. Real fonts have per-glyph sidebearings spanning
roughly -0.29..+0.18 em; this pipeline gives every glyph the same one. That
information does not exist in the atlas: `build_dataset` CENTRES each glyph in
its cell, so the left and right gaps are equal by construction (measured
difference 0.98-1.31px). Deriving sidebearings from the cell gap degenerates to
monospace and scores worse than a constant. Recovering them needs a different
atlas rendering and a retrain -- it is a data-pipeline limit, not a bug here.

The second half matters as much as the first. Vertical metrics used to be
derived from the same `scale`, so raising the scale to fix the cap height would
have dragged ascent/descent with it and produced a ~1.7 em line height. They are
now set from a fixed em budget.
"""
import numpy as np
import pytest

pytest.importorskip("fontTools")

from atlas_to_font import (ASCENT_EM, TARGET_CAP_EM, _uppercase_metrics,
                           build_font)

CELL_W, CELL_H = 106, 160


def _rect(x0, y0, x1, y1):
    """One closed subpath, in the (cmd, points) shape trace_atlas_cells emits."""
    return [[('M', [(x0, y0)]), ('L', [(x1, y0)]), ('L', [(x1, y1)]),
             ('L', [(x0, y1)]), ('Z', [])]]


def _cells(cap_px, charset="AB"):
    """Uppercase cells whose glyphs are `cap_px` tall, sitting on y=120."""
    return [_rect(10, 120 - cap_px, 90, 120) for _ in charset]


def test_uppercase_metrics_reads_baseline_and_cap():
    baseline, cap = _uppercase_metrics(_cells(60), CELL_H, "AB")
    assert baseline == pytest.approx(120)
    assert cap == pytest.approx(60)


def test_no_uppercase_gives_no_cap_and_a_safe_baseline():
    """Lowercase-only input must not crash, and must fall back."""
    baseline, cap = _uppercase_metrics([_rect(10, 60, 90, 120)], CELL_H, "a")
    assert cap is None
    assert baseline == pytest.approx(CELL_H * 0.75)


@pytest.mark.parametrize("cap_px", [40, 60, 90])
def test_cap_height_lands_on_target_whatever_the_atlas_size(cap_px):
    """The whole point: the produced cap must not depend on the render size."""
    from fontTools.pens.boundsPen import BoundsPen

    f = build_font(_cells(cap_px), "AB", CELL_W, CELL_H, upm=1000)
    gs, cmap = f.getGlyphSet(), f.getBestCmap()
    bp = BoundsPen(gs)
    gs[cmap[ord("A")]].draw(bp)
    assert bp.bounds[3] / 1000 == pytest.approx(TARGET_CAP_EM, abs=0.02)


def test_line_height_is_exactly_one_em_regardless_of_scale():
    """Vertical metrics must be decoupled from the (now much larger) scale."""
    for cap_px in (30, 60, 100):
        f = build_font(_cells(cap_px), "AB", CELL_W, CELL_H, upm=1000)
        h = f["hhea"]
        assert h.ascent - h.descent == 1000, f"line height wrong at cap {cap_px}"
        assert h.ascent == round(ASCENT_EM * 1000)
        assert h.descent < 0


def test_the_old_behaviour_really_was_too_small():
    """Pin the defect, so the reason for the fix stays legible.

    The old rule was scale = upm/cell_h, i.e. cap_em = cap_px/cell_h. A typical
    traced cap of ~67px in a 160px cell gives 0.42 em against a ~0.70 source.
    """
    old_cap_em = 67 / CELL_H
    assert old_cap_em == pytest.approx(0.419, abs=0.01)
    assert old_cap_em / 0.703 == pytest.approx(0.596, abs=0.02)


def test_a_pathological_cap_measurement_is_clamped():
    """A near-zero cap must not produce a font many times too large."""
    from fontTools.pens.boundsPen import BoundsPen

    f = build_font(_cells(2), "AB", CELL_W, CELL_H, upm=1000)
    gs, cmap = f.getGlyphSet(), f.getBestCmap()
    bp = BoundsPen(gs)
    gs[cmap[ord("A")]].draw(bp)
    assert bp.bounds[3] / 1000 < 4.0 * CELL_H / CELL_H


def test_sidebearing_defaults_scale_with_upm():
    """A raw 50 units means something different at upm 1000 vs 2048."""
    a = build_font(_cells(60), "AB", CELL_W, CELL_H, upm=1000)
    b = build_font(_cells(60), "AB", CELL_W, CELL_H, upm=2000)
    wa = a["hmtx"][a.getBestCmap()[ord("A")]][0] / 1000
    wb = b["hmtx"][b.getBestCmap()[ord("A")]][0] / 2000
    assert wa == pytest.approx(wb, abs=0.02)
