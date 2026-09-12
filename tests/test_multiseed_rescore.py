"""The rescore reader must define each per-font value the way the evaluator
does, keep seeds apart, and hand the REGISTERED statistic exactly what
`multiseed_compare` hands it.

The point of `analysis/multiseed_rescore.py` is that nothing about the
analysis is new -- only the reader. So the tests pin the reader against the
evaluator's own definitions (identity over gated cells only, composite from
the font's means through `eval_checkpoint.compute_composite`) and pin the
extracted bootstrap against a hand-checkable case, plus, where the multiseed
scores are on disk, against the interval the README quotes.
"""
import json
import os

import numpy as np
import pytest

from analysis import multiseed_compare as mc
from analysis import multiseed_rescore as mr

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cell(font, racc=True, lpips=0.1, dinov2=0.8, scored=True, ident=True):
    return {"font": font, "char": "A", "racc_match": racc, "lpips": lpips,
            "dinov2": dinov2, "identity_scored": scored, "identity_match": ident}


def test_identity_counts_only_the_cells_the_gate_kept():
    cells = [_cell("F", scored=True, ident=True), _cell("F", scored=True, ident=False),
             _cell("F", scored=False, ident=False), _cell("F", scored=False, ident=False)]
    v = mr.font_values(cells)["F"]
    assert v["identity"] == pytest.approx(0.5), "ungated cells must not count"


def test_racc_is_a_rate_and_composite_comes_from_the_font_means():
    from eval_checkpoint import compute_composite
    cells = [_cell("F", racc=True, lpips=0.2, dinov2=0.6),
             _cell("F", racc=False, lpips=0.4, dinov2=1.0)]
    v = mr.font_values(cells)["F"]
    assert v["racc"] == pytest.approx(0.5)
    assert v["lpips"] == pytest.approx(0.3)
    assert v["dinov2"] == pytest.approx(0.8)
    assert v["composite"] == pytest.approx(compute_composite(0.3, 0.5, 0.8))


def test_a_font_without_a_metric_has_no_entry_for_it():
    cells = [{"font": "F", "char": "A", "racc_match": None, "lpips": 0.1,
              "dinov2": 0.5, "identity_scored": False, "identity_match": None}]
    v = mr.font_values(cells)["F"]
    assert "racc" not in v and "identity" not in v and "composite" not in v
    assert v["lpips"] == pytest.approx(0.1)


def test_seeds_stay_separate_across_files(tmp_path):
    paths = {}
    for seed, dn in ((0, 0.2), (1, 0.8)):
        p = tmp_path / f"s{seed}.json"
        p.write_text(json.dumps([_cell("F", dinov2=dn)]), encoding="utf-8")
        paths[seed] = str(p)
    out = mr.per_font_per_seed(paths, "dinov2")
    assert out["F"] == {0: pytest.approx(0.2), 1: pytest.approx(0.8)}


def test_bootstrap_of_a_constant_difference_is_that_constant():
    """With every seed of every font differing by exactly 0.1, resampling
    fonts and seeds can only ever average 0.1: the interval collapses on it."""
    A = {f: {s: 0.5 for s in range(3)} for f in "abcdefghij"}
    B = {f: {s: 0.6 for s in range(3)} for f in "abcdefghij"}
    d_c = {f: 0.1 for f in A}
    lo, hi = mc.seed_blocked_bootstrap(A, B, d_c, [0, 1, 2], [0, 1, 2], n_boot=300)
    assert lo == pytest.approx(0.1) and hi == pytest.approx(0.1)


def test_compare_reports_the_mean_difference_and_drops_the_shared_reference_pair():
    A = {f: {0: 0.5, 1: 0.5} for f in "abcdefghijkl"}
    B = {f: {0: 0.7, 1: 0.7} for f in "abcdefghijkl"}
    A["BitcountGridDoubleInk[x]"] = {0: 0.0, 1: 0.0}
    B["BitcountGridDoubleInk[x]"] = {0: 1.0, 1: 1.0}
    r = mr.compare(A, B, groups=[], n_boot=200)
    assert r["dropped"] == ["BitcountGridDoubleInk[x]"]
    assert r["n_fonts"] == 12 and r["mean_diff"] == pytest.approx(0.2)
    assert r["ci95"] == pytest.approx([0.2, 0.2])
    assert r["excludes_zero"]


def test_arm_means_are_over_the_same_collapsed_observations_as_the_difference():
    """mean_b - mean_a must equal mean_diff exactly, so the table subtracts."""
    A = {f: {0: 0.5} for f in "abcdefghijkl"}
    B = {f: {0: 0.7} for f in "abcdefghijkl"}
    A["a"], B["a"] = {0: 0.1}, {0: 0.9}          # one font far from the rest
    groups = [["a", "b", "c"]]                     # collapse it with two others
    r = mr.compare(A, B, groups, n_boot=50)
    assert r["n_unique"] == 10
    assert r["mean_b"] - r["mean_a"] == pytest.approx(r["mean_diff"])


@pytest.mark.skipif(not (os.path.isfile(os.path.join(REPO, "bestofn_4b", "scores.json"))
                         and os.path.isfile(os.path.join(REPO, "bestofn_9b", "scores.json"))),
                    reason="the multiseed scores are local artifacts")
def test_the_extracted_bootstrap_reproduces_the_published_char_acc_interval():
    """README / CLAUDE.md: char_acc 9B - 4B = +0.0731, CI [+0.0473, +0.0993]."""
    A = mc.per_font_per_seed(os.path.join(REPO, "bestofn_4b", "scores.json"))
    B = mc.per_font_per_seed(os.path.join(REPO, "bestofn_9b", "scores.json"))
    # The byte-identical ground-truth groups, as analysis/check_holdout_integrity.py
    # finds them (CLAUDE.md, "The 50-font holdout is not 50 independent
    # observations"). Named here rather than hashed, because the holdout
    # atlases are gitignored and absent in CI: without the collapse the
    # bootstrap runs on 46 observations, not 44, and the interval moves.
    groups = [["IBMPlexSansArabic-Regular", "IBMPlexSansThai-Regular",
               "IBMPlexSansThaiLooped-Regular"],
              ["TiroGurmukhi-Regular", "TiroTamil-Regular", "TiroTelugu-Regular"]]
    r = mr.compare(A, B, groups)
    assert r["n_unique"] == 44
    assert r["mean_diff"] == pytest.approx(0.0731, abs=5e-4)
    assert r["ci95"][0] == pytest.approx(0.0473, abs=1e-3)
    assert r["ci95"][1] == pytest.approx(0.0993, abs=1e-3)
