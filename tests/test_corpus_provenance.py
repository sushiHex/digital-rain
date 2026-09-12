"""The corpus licence claim must be checkable from a clean clone.

"The training corpus is 97.5% OFL" went unchallenged for months because
nothing in a clean clone could contradict it: build_dataset writes its manifest
into a gitignored tree, so there was no source-to-training-item mapping to
audit. The real figure is 87.0% OFL, with 49 fonts whose own licence field grants
rendering but not redistribution or conversion.

research/corpus_provenance.json is committed precisely so that cannot recur.
These tests read only that tracked artifact -- no gitignored inputs -- so they
run anywhere and fail if a licence claim drifts from the evidence.
"""
import json
import os

import pytest

MANIFEST = "research/corpus_provenance.json"


@pytest.fixture(scope="module")
def man():
    if not os.path.isfile(MANIFEST):
        pytest.fail(f"{MANIFEST} is missing -- it must be COMMITTED, not "
                    "regenerated per-checkout. Run "
                    "analysis/audit_corpus_provenance.py in a full checkout.")
    return json.load(open(MANIFEST, encoding="utf-8"))


def test_manifest_covers_the_whole_corpus(man):
    assert man["corpus_size"] == 925
    assert len(man["fonts"]) == man["corpus_size"]


def test_every_entry_names_a_font(man):
    assert all(e.get("stem") for e in man["fonts"])
    assert len({e["stem"] for e in man["fonts"]}) == len(man["fonts"]), \
        "duplicate stems would inflate any licence fraction"


def test_the_corpus_is_NOT_97_percent_ofl(man):
    """The specific retracted claim. Pin it so it cannot come back."""
    assert man["ofl_fraction"] < 0.90, (
        f"OFL fraction is {man['ofl_fraction']:.2%}; the long-published 97.5% "
        "was derived from a raw Google Fonts checkout, not the trained corpus")
    assert man["max_ofl_fraction_if_all_unknown_were_ofl"] < 0.975, (
        "even granting every unresolved file OFL status the ceiling must stay "
        "below the retracted 97.5% figure")


def test_the_counts_are_internally_consistent(man):
    total = sum(man["license_counts"].values())
    assert total == man["corpus_size"]
    unresolved = sum(1 for e in man["fonts"] if not e.get("resolved"))
    assert unresolved == man["unresolved_in_pool_count"]
    prop = sum(1 for e in man["fonts"] if e.get("license") == "PROPRIETARY")
    assert prop == man["proprietary_count"]


def test_restricted_fonts_are_recorded_not_buried(man):
    """The right-to-train problem must stay visible in the tracked artifact."""
    assert man["proprietary_count"] >= 1, \
        "the restricted-licence fonts must remain explicitly listed"
    stems = {s.lower() for s in man["proprietary_stems"]}
    for expected in ("arial", "verdana", "tahoma", "georgia"):
        assert expected in stems, f"{expected} dropped out of the audit"
    assert man["proprietary_count"] == len(man["proprietary_stems"])


def test_libre_fonts_are_NOT_flagged_by_where_the_file_lives(man):
    """Inter and Lato are OFL and also ship in C:\\Windows\\Fonts.

    The first version of this audit inferred "proprietary" from that directory
    and swept both up; a second pass with loose substring markers scored Arial
    as open, because "...as permitted by the license terms..." contains
    "mit licen". Licence comes from the font's own name ID 13, never from its
    location and never from a fuzzy match.
    """
    stems = {s.lower() for s in man["proprietary_stems"]}
    for libre in ("inter-regular", "latoweb-regular"):
        assert libre not in stems, \
            f"{libre} is OFL; it must not be classified by where the file lives"


def test_upstream_libre_cases_are_called_out_separately(man):
    """Cascadia Code is OFL upstream and restricted only in the Windows copy."""
    for stem in man["proprietary_upstream_is_libre"]:
        assert stem in man["proprietary_stems"]
        rec = next(e for e in man["fonts"] if e["stem"] == stem)
        assert "UPSTREAM" in (rec.get("embedded_note") or "")


def test_restricted_fonts_carry_evidence_for_the_claim(man):
    """Every PROPRIETARY label must cite the file and the note it came from."""
    listed = set(man["proprietary_stems"])
    for e in man["fonts"]:
        if e["stem"] in listed:
            assert e.get("source_file"), f"{e['stem']} has no evidence file"
            assert e.get("embedded_note"), f"{e['stem']} has no licence note"


def test_a_licence_absent_from_the_pool_must_come_from_the_font(man):
    for e in man["fonts"]:
        if not e.get("resolved") and e.get("license"):
            assert e.get("embedded_license") == e["license"], \
                (f"{e['stem']} is absent from the fetch manifest, so its licence "
                 "must come from the font's own name table or not at all")


def test_the_docs_do_not_reassert_97_5_percent():
    """Grep the headline docs; the retraction must not be quietly reverted."""
    for path in ("README.md", "CLAUDE.md", "LICENSE"):
        if not os.path.isfile(path):
            continue
        text = open(path, encoding="utf-8", errors="replace").read()
        for line in text.splitlines():
            if "97.5" not in line:
                continue
            low = line.lower()
            assert any(w in low for w in
                       ("retract", "not ", "wrong", "~~", "84.1",
                        "previously", "supersed", "no longer")), \
                f"{path} asserts 97.5% without marking it retracted:\n  {line.strip()}"
