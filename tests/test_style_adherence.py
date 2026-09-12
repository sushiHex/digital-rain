"""Pin the style-adherence estimator, and pin what it is NOT.

REWRITTEN after an adversarial review (Codex gpt-5.6-sol) found the first
version worthless as a test: it imported only constants, never executed the
statistic, skipped whenever its recorded JSON was absent -- so a missing result
gave a green suite, the exact failure mode the file claimed to guard -- and its
"clustered" test asserted only that a list had length 12.

Three claims this file exists to keep honest:

  * The statistic is a RANKING statistic. `win_rate == (n - rank) / (n - 1)`
    exactly when there are no ties. An earlier note claimed the paired test was
    "a different question, not a relaxed bar". It is not, and the identity below
    is the proof.
  * Ties score HALF. Strict `>` charged every tie as a loss.
  * Significance is an ASSOCIATION on a fixed set, never a usable gate. There is
    no held-out threshold and no error rates.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.style_adherence import (DEFAULT_MODEL, TEXT_TEMPLATE,
                                      permutation_p, win_rates)

REPO = Path(__file__).resolve().parent.parent


# --- the estimator, executed on controlled matrices -----------------------

def test_a_perfect_diagonal_gives_a_perfect_win_rate():
    sim = np.eye(5) * 0.5 + 0.1
    assert np.allclose(win_rates(sim), 1.0)


def test_an_all_ties_matrix_scores_exactly_half():
    """Ties are half, not losses. Strict `>` would return 0.0 here."""
    assert np.allclose(win_rates(np.full((5, 5), 0.3)), 0.5)


def test_a_worst_case_diagonal_scores_zero():
    sim = np.full((4, 4), 0.9)
    np.fill_diagonal(sim, 0.1)
    assert np.allclose(win_rates(sim), 0.0)


def test_win_rate_is_exactly_a_ranking_statistic():
    """(n - rank) / (n - 1). This is the identity that refuted the claim that
    the paired test asked a different question from the ranking test."""
    rng = np.random.default_rng(0)
    sim = rng.random((7, 7))
    n = len(sim)
    ranks = [int(np.where(np.argsort(-sim[i]) == i)[0][0]) + 1 for i in range(n)]
    assert np.allclose(win_rates(sim), [(n - r) / (n - 1) for r in ranks])


def test_permutation_p_finds_no_signal_in_a_flat_matrix():
    obs, p = permutation_p(np.full((6, 6), 0.3), iters=500)
    assert obs == pytest.approx(0.5)
    assert p > 0.05


def test_permutation_p_finds_signal_in_a_diagonal_matrix():
    obs, p = permutation_p(np.eye(6) * 0.5 + 0.1, iters=2000)
    assert obs == pytest.approx(1.0)
    assert p < 0.05


def test_permutation_p_can_never_report_zero():
    """The +1 correction. A reported p of 0 from 20k samples would be a lie."""
    _, p = permutation_p(np.eye(8) * 0.9 + 0.01, iters=200)
    assert p > 0.0


# --- the embedded text ----------------------------------------------------

def test_only_the_style_clause_is_embedded():
    rendered = TEXT_TEMPLATE.format(style="a chunky slab serif")
    for boilerplate in ("black background", "no shadow", "flat lighting",
                        "pure white", "no perspective"):
        assert boilerplate not in rendered.lower()


def test_the_template_names_the_domain():
    rendered = TEXT_TEMPLATE.format(style="x").lower()
    assert "typeface" in rendered or "letterform" in rendered


# --- the recorded results, WITHOUT skipping when absent -------------------

RESULTS = ["research/style_adherence.json", "research/style_adherence_vitl.json"]


def test_the_recorded_runs_are_present():
    """NOT a skip. A missing artifact previously turned every check below into
    a pass, which is how an absent result reads as a confirmed one."""
    missing = [r for r in RESULTS if not (REPO / r).is_file()]
    assert not missing, f"recorded runs are missing: {missing}"


@pytest.mark.parametrize("path", RESULTS)
def test_the_ranking_verdict_is_still_reported_as_a_failure(path):
    d = json.loads((REPO / path).read_text(encoding="utf-8"))
    assert d["usable"] is False, (
        f"{path} now claims the ranking test passed; its top-1 was "
        f"{d['top1']:.0%} against {d['chance_top1']:.0%} chance")
    assert d["top1"] < 0.5, "the 50% ranking bar is the one that was set"


def test_the_recorded_win_rates_reproduce_from_the_recorded_matrix():
    """Recompute rather than trust. A stale or hand-edited JSON fails here."""
    d = json.loads((REPO / RESULTS[1]).read_text(encoding="utf-8"))
    assert np.allclose(win_rates(np.array(d["similarity"])),
                       d["per_image_win_rate"], atol=1e-6)


PERMUTATION_ITERS = 20000
PERMUTATION_FLOOR = 1.0 / (PERMUTATION_ITERS + 1)


def test_the_recorded_p_is_a_permutation_not_an_unclustered_binomial():
    """A binomial over the 132 dependent pairs reports ~6e-07 and is wrong.

    The bar is the permutation's RESOLUTION FLOOR, not a round number. A
    20k-sample permutation cannot report below 1/(iters+1); anything smaller
    came from a different test. My first attempt at this test used a hand-picked
    1e-4 and failed on a legitimate p of 9.9995e-05 -- which is the floor plus
    one, i.e. the smallest honest value this estimator can produce.
    """
    d = json.loads((REPO / RESULTS[1]).read_text(encoding="utf-8"))
    assert d["paired_p"] >= PERMUTATION_FLOOR, (
        f"paired_p={d['paired_p']:.2e} is below the {PERMUTATION_FLOOR:.2e} "
        "floor of a 20k permutation -- it came from another test, most likely "
        "an unclustered binomial over dependent pairs")
    assert len(d["per_image_win_rate"]) == d["n"], "one rate per IMAGE, not per pair"


def test_the_two_verdicts_stay_separate():
    """The ranking bar failed. The permutation result is a different question,
    recorded beside it -- not a relaxed version of the same one."""
    d = json.loads((REPO / RESULTS[1]).read_text(encoding="utf-8"))
    assert d["usable"] is False and "paired_usable" in d
