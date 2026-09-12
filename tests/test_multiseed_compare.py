"""The cross-model multiseed reader must not coerce continuous metrics.

`per_font_per_seed` originally read every cell as `bool(c[metric])`. That is
correct for `char_acc_match`, which IS a per-cell boolean, and silently wrong
for every other recorded metric: bool(0.87) is True, so each font mean became
exactly 1.0, each model difference became exactly +0.0000, and the paired
Wilcoxon returned nan on a zero-variance input.

It read as "no significant difference on dinov2, lpips or composite" -- the
same shape as a real null, which is why it survived a first pass. Unfixed, the
9B's actual +0.0440 dinov2 advantage reads as zero.
"""
import json

import numpy as np
import pytest

from analysis.multiseed_compare import per_font_per_seed


def _write(tmp_path, cells_by_key):
    p = tmp_path / "scores.json"
    p.write_text(json.dumps(cells_by_key), encoding="utf-8")
    return str(p)


def test_continuous_metric_is_averaged_not_truthy(tmp_path):
    """The bug: distinct non-zero values must not all collapse to 1.0."""
    path = _write(tmp_path, {
        "FontA__glyph__seed0": [{"dino_cos": 0.2}, {"dino_cos": 0.4}],
        "FontB__glyph__seed0": [{"dino_cos": 0.8}, {"dino_cos": 1.0}],
    })
    out = per_font_per_seed(path, "dino_cos")
    assert out["FontA"][0] == pytest.approx(0.3)
    assert out["FontB"][0] == pytest.approx(0.9)
    assert out["FontA"][0] != out["FontB"][0], \
        "continuous metrics were coerced through bool() and collapsed to 1.0"


def test_negative_and_zero_values_survive(tmp_path):
    """bool() also maps 0.0 -> False; the composite can legitimately be <= 0."""
    path = _write(tmp_path, {
        "FontA__glyph__seed0": [{"score": -0.5}, {"score": 0.0}, {"score": 0.5}],
    })
    assert per_font_per_seed(path, "score")["FontA"][0] == pytest.approx(0.0)


def test_char_acc_match_still_reads_as_a_rate(tmp_path):
    """The boolean metric must keep its original meaning: a match RATE."""
    path = _write(tmp_path, {
        "FontA__glyph__seed0": [{"char_acc_match": True}, {"char_acc_match": False},
                                {"char_acc_match": True}, {"char_acc_match": True}],
    })
    assert per_font_per_seed(path, "char_acc_match")["FontA"][0] == pytest.approx(0.75)


def test_missing_metric_cells_are_skipped_not_counted_as_zero(tmp_path):
    path = _write(tmp_path, {
        "FontA__glyph__seed0": [{"dino_cos": 0.6}, {"dino_cos": None}, {"dino_cos": 0.8}],
    })
    assert per_font_per_seed(path, "dino_cos")["FontA"][0] == pytest.approx(0.7)


def test_a_font_with_no_usable_cells_is_absent(tmp_path):
    path = _write(tmp_path, {
        "FontA__glyph__seed0": [{"dino_cos": None}],
        "FontB__glyph__seed0": [{"dino_cos": 0.5}],
    })
    out = per_font_per_seed(path, "dino_cos")
    assert "FontA" not in out and "FontB" in out


def test_seeds_are_kept_separate(tmp_path):
    """The seed-blocked bootstrap depends on per-seed values, not a pooled mean."""
    path = _write(tmp_path, {
        "FontA__glyph__seed0": [{"dino_cos": 0.2}],
        "FontA__glyph__seed1": [{"dino_cos": 0.8}],
    })
    out = per_font_per_seed(path, "dino_cos")
    assert out["FontA"] == {0: pytest.approx(0.2), 1: pytest.approx(0.8)}


def test_the_real_run_has_variance_on_every_recorded_metric():
    """Guard against the collapse reappearing on the actual artifacts."""
    import os

    path = "bestofn_9b/scores.json"
    if not os.path.isfile(path):
        pytest.skip("bestofn_9b/scores.json not present in this checkout")
    for metric in ("dino_cos", "lpips", "score"):
        vals = [v for per_seed in per_font_per_seed(path, metric).values()
                for v in per_seed.values()]
        assert np.std(vals) > 1e-6, f"{metric} collapsed to a constant"
