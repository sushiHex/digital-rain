"""Pin the two defects the label census already had, and the bar it reports.

Both defects were mine, both were found by writing the ad-hoc measurement up as
a tool, and both inflated the answer in the direction I wanted:

  * READING PANOSE WITHOUT bFamilyType. `bSerifStyle` only indexes serif shapes
    when `bFamilyType == 2` (Latin Text). Under Hand Written / Decorative /
    Symbol the same byte means something else. Unguarded the census reported
    6,040 serif/sans labels; guarded it reports 1,703 -- a 3.5x overstatement,
    with every decorative face mislabelled.
  * COUNTING FILES INSTEAD OF FAMILIES. Width looked like 4,556 examples and is
    59 FAMILIES, because width variants cluster in a few large superfamilies. A
    holdout splits by family -- 32 of this project's 50 holdout fonts share a
    superfamily with a training font -- so families are the n that governs.

The third test pins that `attribute_separation` groups by family rather than
splitting at random, which is the same leak in the evaluation rather than the
count.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.attribute_label_supply import (MIN_FAMILIES, PANOSE_LATIN_TEXT,
                                             PANOSE_SANS, PANOSE_SERIF,
                                             family_of, measure)

REPO = Path(__file__).resolve().parent.parent
SUPPLY = REPO / "research" / "attribute_label_supply.json"


# --- the PANOSE guard -----------------------------------------------------

def test_panose_serif_is_ignored_outside_latin_text():
    """A DECORATIVE face with bSerifStyle=2 must not count as a serif.

    Without the bFamilyType guard this record labels as serif, which is how the
    unguarded census reached 6,040.
    """
    decorative = {"stem": "Fake-Regular", "family": "Fake",
                  "panose_family": 4, "panose_serif": 2}
    table = measure([decorative])
    assert table["serif vs sans"]["files"] == 0
    assert table["serif vs sans"]["negative_files"] == 0


def test_panose_serif_counts_inside_latin_text():
    latin = {"stem": "Fake-Regular", "family": "Fake",
             "panose_family": PANOSE_LATIN_TEXT, "panose_serif": 2}
    assert measure([latin])["serif vs sans"]["files"] == 1


def test_the_serif_and_sans_sets_do_not_overlap():
    """An overlap would let one font count on both sides of the same question."""
    assert not (PANOSE_SERIF & PANOSE_SANS)


@pytest.mark.parametrize("value", [0, 1])
def test_panose_any_and_no_fit_are_neither_serif_nor_sans(value):
    """0 is 'Any' and 1 is 'No Fit'. Over 5,000 files carry 0; treating it as a
    class would be inventing a label out of an unset field."""
    assert value not in PANOSE_SERIF and value not in PANOSE_SANS


# --- families, not files --------------------------------------------------

def test_one_family_with_many_files_is_one_family():
    """18 weights of one superfamily is 18 files and ONE family. The census must
    report both, because the family count is what a holdout can split."""
    recs = [{"stem": f"Big-{w}", "family": "Big", "weight": w}
            for w in (100, 200, 300, 700, 800, 900)]
    table = measure(recs)
    assert table["weight"]["files"] == 6
    assert table["weight"]["families"] == 1


def test_trainable_is_decided_on_families_not_files():
    """Many files in few families must NOT read as trainable."""
    recs = [{"stem": f"Big-{i}", "family": "Big", "weight": 700}
            for i in range(500)]
    entry = measure(recs)["weight"]
    assert entry["files"] == 500
    assert entry["families"] == 1
    assert entry["trainable"] is False


@pytest.mark.parametrize("stem,expected", [
    ("Roboto-Regular", "Roboto"),
    ("Doto[ROND,wght]", "Doto"),
    ("JetBrainsMono-Italic[wght]", "JetBrainsMono"),
])
def test_family_key_matches_the_exclusions_convention(stem, expected):
    assert family_of(stem) == expected


# --- the recorded census, WITHOUT skipping when absent --------------------

def test_the_recorded_census_is_present():
    """NOT a skip. An absent artifact previously turned every check below into a
    pass, which is how a missing result reads as a confirmed one."""
    assert SUPPLY.is_file(), f"missing: {SUPPLY}"


def test_the_rare_attributes_are_recorded_as_not_trainable():
    """The finding this census exists to carry: stencil and inline -- the two
    attributes the eye caught the generator failing -- have too few families.
    If this ever flips, the corpus changed and the synthesis plan needs
    revisiting rather than silently keeping its justification."""
    d = json.loads(SUPPLY.read_text(encoding="utf-8"))["attributes"]
    for name in ("stencil", "inline"):
        assert d[name]["families"] < MIN_FAMILIES, (
            f"{name} now has {d[name]['families']} families")
        assert d[name]["trainable"] is False


def test_the_census_counted_families_below_files_everywhere():
    """A family count above its file count would mean the grouping is broken."""
    d = json.loads(SUPPLY.read_text(encoding="utf-8"))["attributes"]
    for name, e in d.items():
        assert e["families"] <= e["files"], name


# --- the evaluation must group by family ----------------------------------

def test_separation_holds_out_by_family_not_at_random():
    """A random split puts siblings of one superfamily on both sides, which is
    the leak already recorded against this project's own benchmark."""
    src = (REPO / "analysis" / "attribute_separation.py").read_text(encoding="utf-8")
    assert "GroupKFold" in src
    assert "train_test_split" not in src, "a random split would leak families"


def test_separation_bar_was_registered_before_the_run():
    """The bar lives in the docstring, and the docstring was committed before the
    tool was ever executed. Changing these constants after a run is the
    goalpost-move the CLIP retraction was about."""
    from analysis.attribute_separation import BAR_CARRIED, BAR_WEAK
    assert (BAR_CARRIED, BAR_WEAK) == (0.75, 0.60)
    doc = __import__("analysis.attribute_separation",
                     fromlist=["x"]).__doc__
    assert "PRE-REGISTERED" in doc and "IF IT FAILS" in doc
