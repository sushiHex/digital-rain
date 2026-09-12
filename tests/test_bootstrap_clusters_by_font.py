"""Bootstrap CIs must resample FONTS, not cells.

CLAUDE.md states the rule plainly -- "Effective n is the 50 fonts, not the
4,700 cells. Never cell-bootstrap" -- and analysis/compare_runs.py obeys it.
The eval harness that produces the headline numbers did not: it resampled the
per-cell lists directly, treating n as ~4,700.

The 94 cells of one font share a typeface, a reference image, a seed and a
sampling trajectory. Resampling them independently understates the variance by
roughly sqrt(cells per font) when the within-font correlation is high, so every
published interval was far too narrow.
"""
import numpy as np
import pytest

from eval_checkpoint import bootstrap_ci


def _ranges(n_fonts, per_font):
    return [(f"font{i}", i * per_font, (i + 1) * per_font) for i in range(n_fonts)]


def _width(vals, ranges=None, n=2000, seed=0):
    _, lo, hi = bootstrap_ci(vals, n, 0.95, np.random.default_rng(seed), ranges)
    return hi - lo


def test_cell_bootstrap_understates_uncertainty_when_fonts_differ():
    """The defect: strong between-font structure, invisible to a cell resample."""
    per_font = 94
    rng = np.random.default_rng(0)
    # Each font has its own level; cells within a font barely vary.
    vals = np.concatenate([np.full(per_font, lvl) + rng.normal(0, 0.001, per_font)
                           for lvl in rng.normal(0.7, 0.15, 50)])
    ranges = _ranges(50, per_font)
    assert _width(vals, ranges) > 5 * _width(vals), (
        "clustered CI should be far wider than the per-cell CI when the "
        "variance lives between fonts")


def test_clustered_ci_is_near_the_analytic_font_level_ci():
    """Sanity: the clustered width should track the 50-font standard error."""
    per_font, n_fonts = 94, 50
    rng = np.random.default_rng(1)
    levels = rng.normal(0.7, 0.15, n_fonts)
    vals = np.concatenate([np.full(per_font, lvl) for lvl in levels])
    expected = 2 * 1.96 * levels.std(ddof=1) / np.sqrt(n_fonts)
    assert _width(vals, _ranges(n_fonts, per_font)) == pytest.approx(expected, rel=0.25)


def test_identical_fonts_give_a_near_zero_interval():
    """No between-font variance means no uncertainty about the font mean."""
    vals = np.tile(np.linspace(0.0, 1.0, 94), 30)
    assert _width(vals, _ranges(30, 94)) < 1e-9


def test_the_mean_is_unchanged_by_clustering():
    """Only the interval moves; the point estimate must not."""
    vals = np.random.default_rng(3).normal(0.6, 0.2, 94 * 20)
    m_cell, _, _ = bootstrap_ci(vals, 500, 0.95, np.random.default_rng(0))
    m_clus, _, _ = bootstrap_ci(vals, 500, 0.95, np.random.default_rng(0),
                                _ranges(20, 94))
    assert m_cell == pytest.approx(m_clus) == pytest.approx(float(np.mean(vals)))


def test_unequal_font_sizes_are_weighted_by_cell_count():
    """Fonts contribute their own cell counts, not an unweighted font mean."""
    vals = np.array([0.0] * 10 + [1.0] * 90)
    ranges = [("a", 0, 10), ("b", 10, 100)]
    mean, lo, hi = bootstrap_ci(vals, 2000, 0.95, np.random.default_rng(0), ranges)
    assert mean == pytest.approx(0.9)
    assert lo >= 0.0 and hi <= 1.0


def test_empty_and_degenerate_inputs_are_safe():
    assert bootstrap_ci([], 100, 0.95, np.random.default_rng(0)) == (0.0, 0.0, 0.0)
    # ranges that select nothing must fall back rather than divide by zero
    m, lo, hi = bootstrap_ci([0.5] * 10, 200, 0.95, np.random.default_rng(0),
                             [("a", 0, 0)])
    assert m == pytest.approx(0.5) and lo == pytest.approx(0.5)


def test_falls_back_to_cell_resampling_without_font_structure():
    """Callers with genuinely exchangeable values keep the old behaviour."""
    vals = np.random.default_rng(5).normal(0, 1, 500)
    a = bootstrap_ci(vals, 1000, 0.95, np.random.default_rng(7))
    b = bootstrap_ci(vals, 1000, 0.95, np.random.default_rng(7), None)
    assert a == b


def test_the_harness_passes_font_ranges_to_every_ci():
    """Guard the call sites, not just the helper."""
    import inspect

    import eval_checkpoint
    src = inspect.getsource(eval_checkpoint.score_phase)
    for metric in ("lpips_per_cell", "racc_match_per_cell", "dino_per_cell",
                   "char_acc_per_cell_f"):
        idx = src.find(f"bootstrap_ci({metric}")
        assert idx != -1, f"no bootstrap_ci call for {metric}"
        assert "font_cell_ranges" in src[idx:idx + 260], \
            f"bootstrap_ci({metric}, ...) does not pass font_cell_ranges"
