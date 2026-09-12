"""Pin the pre-registered calibration analysis to its registration.

The analysis was committed while the label file was an empty template, and
its docstring fixes the statistic, the bar and the exclusion rules. These
tests keep the code honest to that text: the AUC is the Mann-Whitney one with
ties at one half, the permutation test is one-sided, blank rows are excluded
and counted, a bad label value refuses, and the bar constants are the ones
the docstring states.
"""
import csv
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis import calibrate_instruments as ci  # noqa: E402


def test_auc_is_mann_whitney_with_half_ties():
    assert ci.auc([3, 2, 1, 0], [1, 1, 0, 0]) == 1.0
    assert ci.auc([0, 1, 2, 3], [1, 1, 0, 0]) == 0.0
    assert ci.auc([1, 1, 1, 1], [1, 1, 0, 0]) == 0.5
    assert np.isnan(ci.auc([1, 2], [1, 1]))


def test_permutation_p_is_small_for_a_perfect_separation_and_large_for_noise():
    scores = list(range(40))
    labels = [0] * 20 + [1] * 20
    p = ci.permutation_p(scores, labels, ci.auc(scores, labels), n=2000)
    assert p < 0.01
    rng = np.random.default_rng(1)
    noise = rng.permutation(labels)
    p2 = ci.permutation_p(scores, noise, ci.auc(scores, noise), n=2000)
    assert p2 > 0.05


def test_cut_report_counts_the_confusion_matrix():
    d = [1.0, 1.5, 2.0, 2.5]      # <= 1.875 predicts usable
    y = [1, 0, 1, 0]
    r = ci.cut_report(d, y)
    assert (r["tp"], r["fp"], r["fn"], r["tn"]) == (1, 1, 1, 1)
    assert r["precision"] == 0.5 and r["recall"] == 0.5 and r["specificity"] == 0.5


def _csv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "description_index", "seed",
                                           "description", "usable", "note"])
        w.writeheader()
        w.writerows(rows)


def test_blank_rows_are_excluded_and_counted(tmp_path):
    p = tmp_path / "labels.csv"
    _csv(p, [{"id": "00-s0", "description_index": 0, "seed": 0,
              "description": "x", "usable": "1", "note": ""},
             {"id": "00-s1", "description_index": 0, "seed": 1,
              "description": "x", "usable": "", "note": ""},
             {"id": "09-s3", "description_index": 9, "seed": 3,
              "description": "y", "usable": "0", "note": "solid"}])
    rows, blank = ci.read_labels(p)
    assert blank == 1
    assert [(r["index"], r["seed"], r["usable"]) for r in rows] == [(0, 0, 1), (9, 3, 0)]


def test_a_bad_label_value_refuses(tmp_path):
    p = tmp_path / "labels.csv"
    _csv(p, [{"id": "00-s0", "description_index": 0, "seed": 0,
              "description": "x", "usable": "yes", "note": ""}])
    with pytest.raises(SystemExit, match="usable must be"):
        ci.read_labels(p)


def test_the_bar_matches_the_registration_text():
    doc = ci.__doc__
    assert ci.BAR_AUC == 0.70 and ci.BAR_P == 0.05 and ci.MIN_LABELLED == 30
    assert "AUC >= 0.70" in doc and "p < 0.05" in doc and "Fewer than 30" in doc
    assert ci.GATE_THRESHOLD == 1.875 and "No new threshold is fitted" in doc
    assert ci.TREATMENT_OF == {9: "stencil", 10: "inline"}


def test_an_empty_template_scores_nothing_and_exits_clean(tmp_path, capsys):
    p = tmp_path / "labels.csv"
    _csv(p, [{"id": f"{i:02d}-s{s}", "description_index": i, "seed": s,
              "description": "d", "usable": "", "note": ""}
             for i in range(12) for s in range(4)])
    assert ci.main(["--labels", str(p), "--json", str(tmp_path / "out.json")]) == 0
    out = capsys.readouterr().out
    assert "48 blank" in out and "nothing to score yet" in out
