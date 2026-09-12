"""Pin the label bug that silently dropped a whole arm.

WHAT HAPPENED. The style prefix in a candidate filename is truncated to 28
characters, and for one of the twelve descriptions that cut lands ON AN
UNDERSCORE:

    10-an_inline_face_with_a_white_ + __s0  ->  10-an_inline_face_with_a_white___s0
                                  ^^^ three underscores

`stem.split("__")[0]` returns `...white` instead of `...white_`. GROUPING still
worked, because every candidate of that description loses the same character --
so `within_prompt_diversity.py` produced correct statistics under a wrong KEY.
Then `reference_to_atlas_transfer.py` built a glob from that key, matched
nothing, and scored 12 atlases against a registration that said 16. Nothing
raised.

That is the third glob/label mismatch this repository has logged (a `[wght]`
font name read as a character class dropped 12 of 48 fonts), and the common
shape is: THE WRONG ANSWER LOOKED LIKE A SMALLER CORRECT ONE.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.generate_candidate_references import build_prompts
from analysis.within_prompt_diversity import description_of

REPO = Path(__file__).resolve().parent.parent
CANDIDATES = REPO / "eval_runs" / "_candidate_refs" / "klein-base-n4"


def test_a_prefix_ending_in_underscore_survives():
    """The exact case that broke. `split('__')[0]` returns '...white' here."""
    stem = "10-an_inline_face_with_a_white___s0"
    assert description_of(stem) == "10-an_inline_face_with_a_white_"
    assert stem.split("__")[0] != description_of(stem), (
        "the naive split now agrees, so this test no longer guards anything")


@pytest.mark.parametrize("stem,expected", [
    ("00-a_heavy_geometric_sans_serif__s0", "00-a_heavy_geometric_sans_serif"),
    ("04-a_condensed_grotesque__s12", "04-a_condensed_grotesque"),
    ("10-an_inline_face_with_a_white___s3", "10-an_inline_face_with_a_white_"),
])
def test_description_of_strips_only_the_seed_suffix(stem, expected):
    assert description_of(stem) == expected


def test_an_n1_label_is_returned_unchanged():
    """No `__sN` suffix at n=1, so nothing may be stripped."""
    for label, _, _ in build_prompts():
        assert description_of(label) == label


def test_every_description_key_addresses_its_own_files():
    """The guard that would have caught it: a key must match files on disk."""
    import glob as _glob
    if not CANDIDATES.is_dir():
        pytest.skip("candidate references are a gitignored output")
    stems = [p.stem for p in CANDIDATES.glob("*.png")]
    if not stems:
        pytest.skip("no candidates generated")
    for key in {description_of(s) for s in stems}:
        hits = _glob.glob(str(CANDIDATES / (_glob.escape(key) + "__s*.png")))
        assert hits, f"description key {key!r} matches no files"


def test_labels_round_trip_from_build_prompts_to_description():
    """Generated label -> description must return the n=1 stem exactly."""
    ones = {label for label, _, _ in build_prompts()}
    for label, _, _ in build_prompts(n=4):
        assert description_of(label) in ones, label


def test_every_description_keeps_all_its_candidates():
    import collections
    counts = collections.Counter(
        description_of(label) for label, _, _ in build_prompts(n=4))
    assert set(counts.values()) == {4}, counts
