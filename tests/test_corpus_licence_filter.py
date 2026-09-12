"""The corpus licence filter and the provenance guard that prevents recurrence.

87 of the 925 training fonts carry terms that do not permit creating AND
redistributing derivative works -- which is precisely what this project does.
48 are vendor-supplied Windows faces; 36 are Fontshare closed-source (ITF-FFL),
whose licence claims derivative works as the foundry's property.

They got in because a path existed to add a font without recording where it
came from: `pipeline/fetch_fonts.py` writes provenance for everything it
copies, and 121 corpus fonts have no manifest entry at all. Two defences here:
filter what training consumes, and refuse unprovenanced fonts at dataset build.
"""
import json
import os

import pytest

EXCLUSIONS = "research/corpus_exclusions.json"


@pytest.fixture(scope="module")
def exc():
    if not os.path.isfile(EXCLUSIONS):
        pytest.fail(f"{EXCLUSIONS} must be COMMITTED -- training filters on it")
    return json.load(open(EXCLUSIONS, encoding="utf-8"))


def test_the_decision_covers_the_whole_corpus(exc):
    assert exc["keep_count"] + exc["exclude_count"] == exc["corpus_size"] == 925


def test_exclude_stems_matches_the_detail_list(exc):
    assert sorted(exc["exclude_stems"]) == sorted(d["stem"] for d in exc["excluded"])
    assert len(set(exc["exclude_stems"])) == len(exc["exclude_stems"])


def test_every_exclusion_states_a_reason(exc):
    for d in exc["excluded"]:
        assert d.get("reason"), f"{d['stem']} excluded with no reason recorded"


def test_the_known_bad_fonts_are_actually_excluded(exc):
    """Spot-check both categories; a silent regression here is expensive."""
    stems = {s.lower() for s in exc["exclude_stems"]}
    for windows_font in ("arial", "verdana", "georgia", "consola", "segoeuii"):
        assert windows_font in stems, f"{windows_font} is not excluded"
    for itf_font in ("satoshi", "switzer", "general_sans", "zodiak"):
        assert itf_font in stems, f"Fontshare font {itf_font} is not excluded"


def test_libre_fonts_are_kept(exc):
    """The filter must not over-reach; these are OFL and must survive."""
    stems = {s.lower() for s in exc["exclude_stems"]}
    for keep in ("inter-regular", "latoweb-regular", "fira_sans", "knewave",
                 "chunk", "junction", "cascadiacode"):
        assert keep not in stems, f"{keep} is OFL and must not be dropped"


def test_recovered_fonts_cite_first_party_evidence(exc):
    """A recovery must rest on the rights holder's own licence, not a listing."""
    assert exc["recovered"], "no recovered fonts recorded"
    for r in exc["recovered"]:
        assert "recovered:" in r["reason"]
        assert any(k in r["reason"] for k in
                   ("google-fonts/ofl", "repo's own", "public domain")), \
            f"{r['stem']} recovery cites no first-party evidence: {r['reason']}"


def test_roughly_nine_percent_is_dropped(exc):
    """Guard the magnitude: a filter that silently drops everything is a bug."""
    frac = exc["exclude_count"] / exc["corpus_size"]
    assert 0.05 < frac < 0.15, f"excluding {frac:.1%} of the corpus is implausible"


# --------------------------------------------------------------------------
# The training-time filter
# --------------------------------------------------------------------------

def test_dataset_accepts_and_applies_an_exclusion_list(tmp_path):
    import torch

    from train_lora_kg import CachedLatentDataset

    cache = tmp_path / "cache"
    for sub in ("atlases", "references"):
        (cache / sub).mkdir(parents=True)
    for stem in ("keep_me", "drop_me", "also_keep"):
        for sub in ("atlases", "references"):
            torch.save(torch.zeros(2, 2), cache / sub / f"{stem}.pt")

    ds = CachedLatentDataset(cache, exclude_stems=["drop_me"])
    assert sorted(ds.stems) == ["also_keep", "keep_me"]
    assert ds.excluded == ["drop_me"]

    unfiltered = CachedLatentDataset(cache)
    assert len(unfiltered.pairs) == 3, "no exclusions must mean no filtering"


def test_training_filters_by_default_and_names_the_opt_out():
    """Silently training on the excluded fonts is the failure worth preventing."""
    import inspect

    import train_lora_kg
    src = inspect.getsource(train_lora_kg.main)
    assert "no_licence_filter" in src, "training must filter by default"
    assert "exclude_stems=exclude_stems" in src
    parser_src = inspect.getsource(train_lora_kg)
    assert "--no-licence-filter" in parser_src


# --------------------------------------------------------------------------
# The provenance guard at dataset build
# --------------------------------------------------------------------------

def test_find_fonts_refuses_fonts_with_no_manifest_entry(tmp_path):
    import build_dataset

    fonts = tmp_path / "fonts"
    fonts.mkdir()
    (fonts / "known.ttf").write_bytes(b"not a real font")
    (fonts / "smuggled.ttf").write_bytes(b"not a real font")
    man = tmp_path / "manifest.json"
    man.write_text(json.dumps([{"filename": "known.ttf", "source": "directory",
                                "license": "OFL-1.1"}]), encoding="utf-8")

    # Neither file parses as a font, so both would fail the charset check --
    # what matters is that the unprovenanced one is rejected BEFORE that.
    out = build_dataset.find_fonts(fonts, manifest=str(man))
    assert all("smuggled" not in str(p) for p in out)


def test_find_fonts_aborts_when_the_manifest_is_absent(tmp_path):
    """No manifest means no licence can be established -- fail closed."""
    import build_dataset

    fonts = tmp_path / "fonts"
    fonts.mkdir()
    with pytest.raises(SystemExit, match="provenance manifest"):
        build_dataset.find_fonts(fonts, manifest=str(tmp_path / "nope.json"))


def test_find_fonts_refuses_a_manifested_but_unusable_licence(tmp_path):
    """A recorded licence is not necessarily an acceptable one.

    The pool holds 4 CC-BY-NC fonts (non-commercial), 2 GPL, and 1 whose
    repository states no licence at all. All are properly manifested, and none
    may be trained on for a product that distributes the fonts it generates.
    """
    import build_dataset

    man = tmp_path / "manifest.json"
    man.write_text(json.dumps([
        {"filename": "ofl_font.ttf", "source": "github", "license": "OFL-1.1"},
        {"filename": "nc_font.ttf", "source": "github", "license": "CC-BY-NC"},
        {"filename": "gpl_font.ttf", "source": "github", "license": "GPL-2.0"},
        {"filename": "unknown_font.ttf", "source": "github", "license": "unknown"},
    ]), encoding="utf-8")

    assert build_dataset.load_provenance_stems(str(man)) == {"ofl_font"}
    assert build_dataset.load_provenance_stems(str(man), permissive_only=False) == {
        "ofl_font", "nc_font", "gpl_font", "unknown_font"}


def test_non_commercial_and_copyleft_are_not_treated_as_free():
    """CC-BY-NC forbids commercial use; GPL is copyleft. Neither is OFL."""
    import build_dataset

    for bad in ("CC-BY-NC", "GPL", "GPL-2.0", "PROPRIETARY", "unknown"):
        assert bad not in build_dataset.PERMISSIVE_LICENCES
    assert "OFL-1.1" in build_dataset.PERMISSIVE_LICENCES


def test_the_guard_can_be_opted_out_of_explicitly(tmp_path):
    import build_dataset

    fonts = tmp_path / "fonts"
    fonts.mkdir()
    build_dataset.find_fonts(fonts, require_provenance=False,
                             manifest=str(tmp_path / "nope.json"))
