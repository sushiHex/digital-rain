"""Tests for the paired-Wilcoxon comparison that produces every headline
statistic in this project.

The direction tests exist because of a real reporting bug: identity is a
near-ceiling metric where 40 of 50 fonts tie exactly, so median(b - a) is
0.0 while the test reports p=0.002. Reading direction off the median's sign
gave "A better" only by the accident that `0.0 > 0` is False.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.compare_runs import paired_wilcoxon, per_font_metrics


def _cell(font, char, **kw):
    base = {"font": font, "char": char, "lpips": 0.1, "racc_match": True,
            "dinov2": 0.8, "char_acc_match": True}
    base.update(kw)
    return base


def test_direction_survives_a_tied_median():
    # 20 pairs: 14 tie exactly, 6 favour A. median(b-a) == 0.0, but the
    # signed-rank test only ranks the 6 nonzero pairs, all of which are
    # negative -- direction must be -1 (A better), not read off the median.
    a = [1.0] * 20
    b = [1.0] * 14 + [0.9] * 6
    res = paired_wilcoxon(a, b)
    assert res.median_delta == 0.0
    assert res.n_nonzero == 6
    assert res.direction == -1
    assert res.mean_delta_nonzero < 0


def test_direction_matches_median_when_nothing_ties():
    a = [0.1 * i for i in range(1, 21)]
    b = [x + 0.05 for x in a]
    res = paired_wilcoxon(a, b)
    assert res.direction == 1
    assert res.median_delta > 0
    assert res.p < 0.05


def test_below_min_nonzero_pairs_returns_nan_but_keeps_direction():
    # 9 nonzero pairs is under MIN_NONZERO_PAIRS: no p-value is reported,
    # but the caller can still see which way the differences point.
    a = [1.0] * 30
    b = [1.0] * 21 + [1.1] * 9
    res = paired_wilcoxon(a, b)
    assert res.n_nonzero == 9
    assert res.p != res.p          # NaN
    assert res.direction == 1


def test_identity_averages_only_gt_gated_cells():
    # Two gated cells (one match, one miss) and one ungated cell that would
    # drag the mean to 1/3 if it were counted. Correct answer is 0.5.
    records = [
        _cell("F", "A", identity_scored=True, identity_match=True),
        _cell("F", "B", identity_scored=True, identity_match=False),
        _cell("F", "C", identity_scored=False, identity_match=False),
    ]
    row = per_font_metrics(records)["F"]
    assert abs(row["identity"] - 0.5) < 1e-9


def test_font_with_no_gated_cells_has_no_identity_key():
    # Must be absent, not 0.0 -- a 0.0 would silently score as a total
    # identity failure in the paired test.
    records = [_cell("F", "A", identity_scored=False)]
    assert "identity" not in per_font_metrics(records)["F"]
