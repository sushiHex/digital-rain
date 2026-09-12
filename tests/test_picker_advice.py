"""Pin the picker's narrow-set advisory, and that it fails OPEN.

The measurement behind it: within-description spread runs 0.454-3.960 across
twelve descriptions, and on EIGHT of them no candidate pair reaches 1.875 --
the distance at which `reference_gate` calls two glyphs different styles. On
those descriptions, four options are a false promise, because re-rolling cannot
rescue a prompt the model systematically misses.
(`research/2026-08-25-eight-of-twelve-offer-no-real-choice.md`)

Two properties this file exists to keep:

  * THE CUT IS THE GATE'S OWN THRESHOLD, not an invented constant. If someone
    changes `REFERENCE_GATE_THRESHOLD`, the advisory must move with it.
  * IT FAILS OPEN. An advisory must never be the reason a usable candidate set
    is withheld -- the same rule the reference gate follows, for the same
    reason.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import (NARROW_ADVICE, REFERENCE_GATE_THRESHOLD, candidate_set_advice,
                 candidate_spread)


def test_a_set_with_one_far_pair_offers_a_choice():
    verdict, msg = candidate_set_advice([0.2, 0.4, REFERENCE_GATE_THRESHOLD + 0.1])
    assert verdict == "choice"
    assert msg == ""


def test_a_set_where_no_pair_reaches_the_gate_is_narrow():
    verdict, msg = candidate_set_advice([0.2, 0.4, REFERENCE_GATE_THRESHOLD - 0.01])
    assert verdict == "narrow"
    assert msg == NARROW_ADVICE


def test_the_cut_follows_the_gate_threshold_rather_than_a_constant():
    """Raise the threshold and a previously-choice set must become narrow."""
    scores = [REFERENCE_GATE_THRESHOLD + 0.1]
    assert candidate_set_advice(scores)[0] == "choice"
    assert candidate_set_advice(scores, threshold=REFERENCE_GATE_THRESHOLD + 1)[0] \
        == "narrow"


def test_an_empty_set_is_unknown_and_silent():
    """No pairs means nothing to say -- NOT a narrow warning on no evidence."""
    verdict, msg = candidate_set_advice([])
    assert verdict == "unknown"
    assert msg == ""


def test_the_advice_tells_the_user_to_reword_not_to_re_roll():
    """The measured point: re-rolling cannot rescue a systematic miss."""
    assert "reword" in NARROW_ADVICE.lower()


@pytest.mark.parametrize("paths", [[], ["/nonexistent/a.png"],
                                   ["/nonexistent/a.png", "/nonexistent/b.png"]])
def test_candidate_spread_fails_open(paths):
    """Unscoreable input returns [], which reads as 'unknown' and stays silent.

    `check_reference` fails open for the same reason and says so; an advisory
    that raised would take the whole picker down with it.
    """
    assert candidate_spread(paths) == []


def test_a_failed_spread_produces_no_warning():
    """The two halves compose: unscoreable -> [] -> unknown -> empty message."""
    verdict, msg = candidate_set_advice(candidate_spread(["/nonexistent.png"]))
    assert (verdict, msg) == ("unknown", "")
