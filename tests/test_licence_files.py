"""Pin the licensing files to the decision they record.

Three ways this can rot without anything else noticing: someone appends a
paragraph of history to `LICENSE`, which stops GitHub and every licence
detector recognising it (the history belongs in docs/licensing.md); a
licence text under LICENSES/ is dropped or edited; the package metadata
says something different from the tree. Each is cheap to pin.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_license_is_the_verbatim_agpl_text():
    text = (REPO / "LICENSE").read_text(encoding="utf-8")
    assert text.lstrip().startswith("GNU AFFERO GENERAL PUBLIC LICENSE")
    assert "Version 3, 19 November 2007" in text
    assert "13. Remote Network Interaction" in text
    # nothing appended: the file ends with the FSF's closing paragraph
    assert text.rstrip().endswith("<https://www.gnu.org/licenses/>.")
    assert "sushiHex" not in text, "project text belongs in NOTICE, not LICENSE"


def test_the_creative_commons_texts_are_present_and_intact():
    by = (REPO / "LICENSES" / "CC-BY-4.0.txt").read_text(encoding="utf-8")
    zero = (REPO / "LICENSES" / "CC0-1.0.txt").read_text(encoding="utf-8")
    assert "Attribution 4.0 International" in by[:200]
    assert "Section 3 -- License Conditions" in by
    assert "CC0 1.0 Universal" in zero[:200]
    assert "Waiver" in zero


def test_notice_names_all_three_parts_and_the_cla():
    notice = (REPO / "NOTICE").read_text(encoding="utf-8")
    for needle in ("AGPL-3.0-only", "CC-BY-4.0", "CC0-1.0", "route_b/NOTICE",
                   ".github/CLA.md", "docs/licensing.md"):
        assert needle in notice, needle


def test_the_cla_grants_what_dual_licensing_needs():
    cla = (REPO / ".github" / "CLA.md").read_text(encoding="utf-8")
    for needle in ("sublicensable", "including proprietary terms",
                   "patent licence", "moral rights", "employer"):
        assert needle in cla, needle
    sig = (REPO / ".github" / "CLA-signatures.md").read_text(encoding="utf-8")
    assert "| date | GitHub handle |" in sig


def test_pyproject_declares_the_code_licence():
    toml = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r'license\s*=\s*(\{\s*text\s*=\s*)?"AGPL-3\.0-only"', toml)


def test_no_live_doc_still_says_there_is_no_licence():
    for rel in ("README.md", "CLAUDE.md", "AGENTS.md", ".github/CONTRIBUTING.md",
                ".github/PULL_REQUEST_TEMPLATE.md", "docs/public-release.md"):
        text = (REPO / rel).read_text(encoding="utf-8").lower()
        for phrase in ("without a licence", "no licence is granted",
                       "carries no licence", "carries **no licence**"):
            assert phrase not in text, (rel, phrase)
