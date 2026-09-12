"""Pin what the public export withholds, and that it withholds it.

The public repository is a fresh history built from the private tree by
`misc/export_public.py`. The properties this file keeps:

  * EVERY EXCLUSION RULE STILL MATCHES SOMETHING. A rule that matches nothing
    is a guard that has silently died (a directory renamed under it) -- the
    same shape as the glob mismatches that dropped a description from the
    transfer test without erroring. The script refuses to run; this test
    refuses first.
  * THE THINGS KNOWN TO BE PRIVATE ARE IN THE EXCLUDED HALF, by name, so a
    rewrite of the rules cannot quietly let one through.
  * THE END-TO-END PATH STAGES EXACTLY THE KEPT SET, blob and mode identical
    to HEAD, including files the shared .gitignore would otherwise skip and
    the executable bit Windows cannot represent on disk.
  * THE DESTINATION CANNOT BE THE PRIVATE REPOSITORY, inside it, or a tree
    that has been worked in since the last export. Each of those would have
    turned an export into a deletion.

THESE TESTS RUN IN BOTH TREES. In the public repository every rule is dead by
construction -- that is what an export IS -- so the rule-level tests skip
there rather than fail CI, and `misc/export_public.py` itself refuses to run.
The fixture-repo tests and the public-face test run everywhere.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from misc import export_public as ex  # noqa: E402


def _partition():
    kept, excluded = ex.partition(ex.tracked_at_head(ex.REPO))
    if ex.is_export(excluded):
        pytest.skip("this tree is a public export; nothing is left to exclude")
    return kept, excluded


def test_no_exclusion_rule_is_dead():
    _, excluded = _partition()
    assert ex.dead_rules(excluded) == []


def test_every_tracked_file_lands_in_exactly_one_half():
    tracked = ex.tracked_at_head(ex.REPO)
    kept, excluded = _partition()
    gone = [p for paths in excluded.values() for p in paths]
    assert sorted(kept + gone) == tracked
    assert not set(kept) & set(gone)


def test_the_known_private_material_is_withheld():
    kept, _ = _partition()
    kept = set(kept)
    for p in ("research/RESEARCH.md", "research/BRAINSTORM.md",
              "docs/PUSH-PREP.md",
              "research/2026-03-26-oracle-full-report.md",
              "research/2026-03-29-oracle-round21-report.md",
              "research/2026-04-09-legal-font-sources.md",
              "research/2026-08-01-bfl-commercial-licensing.md"):
        assert p not in kept, p
    for prefix in ("research/sessions/", "docs/archive/", "docs/superpowers/"):
        assert not any(p.startswith(prefix) for p in kept), prefix
    # the product recipe -- results public, code and how-to private
    for p in ("app.py", "analysis/generate_candidate_references.py",
              "analysis/constructed_reference.py", "tests/test_picker_path.py",
              "research/2026-08-25-the-picker-works-except-where-it-is-needed.md"):
        assert p not in kept, p


def test_nothing_kept_imports_a_withheld_module():
    """A kept module importing withheld code would fail on the public tree."""
    kept, _ = _partition()
    withheld_mods = {p[:-3].replace("/", ".") for p in ex.RECIPE if p.endswith(".py")}
    withheld_mods |= {m.rsplit(".", 1)[-1] for m in withheld_mods}   # bare names
    offenders = []
    for p in kept:
        if not p.endswith(".py"):
            continue
        text = open(os.path.join(ex.REPO, p), encoding="utf-8", errors="replace").read()
        for m in withheld_mods:
            if f"from {m} import" in text or f"import {m}\n" in text or f"import {m} " in text:
                offenders.append((p, m))
    assert offenders == [], offenders


def test_the_public_face_is_kept():
    """Runs in both trees: in the export these files simply exist."""
    kept, _ = ex.partition(ex.tracked_at_head(ex.REPO))
    for p in ("README.md", "CLAUDE.md", "AGENTS.md", "LICENSE", "NOTICE",
              "LICENSES/CC-BY-4.0.txt", "LICENSES/CC0-1.0.txt",
              "docs/licensing.md", ".github/CLA.md", ".github/CLA-signatures.md",
              "docs/public-release.md", "docs/what-happened.md",
              "research/README.md", "misc/export_public.py",
              ".github/PULL_REQUEST_TEMPLATE.md", ".github/workflows/ci.yml",
              "eval_runs/prompt_trained_short/per_cell.json",
              # the results of the product track stay public
              "research/2026-08-23-the-loop-closes.md",
              "research/2026-08-28-hand-it-a-stencil-and-it-propagates-one.md",
              "viz/out/description_to_font.png", "viz/out/synthesised_reference.png",
              "analysis/reference_gate.py", "analysis/style_coherence.py",
              "analysis/synthesize_rare_attributes.py"):
        assert p in kept, p


def test_the_listing_prints_the_kept_half_too(capsys):
    """A newly tracked file no rule names lands in the kept half with no other
    signal; the listing must show it."""
    ex.print_listing(["a.py", "b.md"], {"x/": ["x/y"]}, (("x/", "why"),))
    out = capsys.readouterr().out
    assert "a.py" in out and "b.md" in out and "x/y" in out and "why" in out


def test_a_public_export_refuses_to_export_itself():
    """`main()` must stop on a tree where no rule matches -- the public repo."""
    excluded = {pat: [] for pat, _ in ex.EXCLUDE}
    assert ex.is_export(excluded)
    excluded[ex.EXCLUDE[0][0]] = ["something"]
    assert not ex.is_export(excluded)


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout


def _fixture_repo(root):
    src = root / "private"
    src.mkdir()
    _git(["init", "-q", "-b", "main"], src)
    _git(["config", "user.email", "t@users.noreply.github.com"], src)
    _git(["config", "user.name", "t"], src)
    (src / "keep.py").write_text("print('kept')\n", encoding="utf-8")
    (src / "run.sh").write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    (src / ".gitignore").write_text("*.json\n", encoding="utf-8")
    (src / "secret").mkdir()
    (src / "secret" / "notes.md").write_text("private\n", encoding="utf-8")
    (src / "forced.json").write_text("{}\n", encoding="utf-8")
    _git(["add", "keep.py", "run.sh", ".gitignore", "secret/notes.md"], src)
    _git(["add", "-f", "forced.json"], src)
    _git(["update-index", "--chmod=+x", "run.sh"], src)
    _git(["commit", "-q", "-m", "fixture"], src)
    return src


def _with_fixture_rules(monkeypatch):
    rules = (("secret/", "fixture"),)
    monkeypatch.setattr(ex, "EXCLUDE", rules)
    monkeypatch.setattr(ex, "MAY_BE_EMPTY", set())
    return rules


def _export(src, dest, rules):
    keep, excluded = ex.partition(ex.tracked_at_head(str(src)), rules)
    ex.prepare_dest(str(dest))
    ex.extract_head(str(src), str(dest), keep)
    ex.stage(str(dest), keep, repo=str(src))
    return keep, excluded


def test_end_to_end_on_a_fixture_repo(tmp_path, monkeypatch):
    """Excluded file absent, ignored-but-tracked file present, blobs AND modes
    identical to HEAD -- including the executable bit."""
    src = _fixture_repo(tmp_path)
    rules = _with_fixture_rules(monkeypatch)
    dest = tmp_path / "public"
    keep, excluded = _export(src, dest, rules)
    assert keep == [".gitignore", "forced.json", "keep.py", "run.sh"]
    assert excluded == {"secret/": ["secret/notes.md"]}
    assert not (dest / "secret").exists()
    assert (dest / "keep.py").read_bytes() == (src / "keep.py").read_bytes()
    assert ex.staged_modes(str(dest)) == {
        p: ex.modes_at_head(str(src))[p] for p in keep}
    assert ex.staged_modes(str(dest))["run.sh"][0] == "100755"


def test_a_re_export_is_allowed_only_over_export_commits(tmp_path, monkeypatch):
    src = _fixture_repo(tmp_path)
    rules = _with_fixture_rules(monkeypatch)
    dest = tmp_path / "public"
    _export(src, dest, rules)
    _git(["config", "user.email", "t@users.noreply.github.com"], dest)
    _git(["config", "user.name", "t"], dest)
    ex.commit(str(dest), str(src))
    # a second export over an export-only history is fine
    _export(src, dest, rules)
    # someone works in the public tree...
    (dest / "keep.py").write_text("print('changed by a contributor')\n",
                                  encoding="utf-8")
    _git(["commit", "-q", "-am", "feat: a contributor's change"], dest)
    with pytest.raises(SystemExit, match="did not make"):
        ex.prepare_dest(str(dest))
    assert "contributor" in (dest / "keep.py").read_text(encoding="utf-8"), \
        "refusal must not touch the tree"


def test_commit_refuses_a_personal_email(tmp_path, monkeypatch):
    src = _fixture_repo(tmp_path)
    rules = _with_fixture_rules(monkeypatch)
    dest = tmp_path / "public"
    _export(src, dest, rules)
    _git(["config", "user.email", "someone@example.com"], dest)
    _git(["config", "user.name", "t"], dest)
    with pytest.raises(SystemExit, match="noreply"):
        ex.commit(str(dest), str(src))


def test_the_destination_cannot_be_the_private_repository(tmp_path):
    src = tmp_path / "private"
    src.mkdir()
    with pytest.raises(SystemExit, match="IS the private"):
        ex.check_dest_is_safe(str(src), repo=str(src))
    with pytest.raises(SystemExit, match="inside"):
        ex.check_dest_is_safe(str(src / "public"), repo=str(src))
    with pytest.raises(SystemExit, match="parent"):
        ex.check_dest_is_safe(str(tmp_path), repo=str(src))
    ex.check_dest_is_safe(str(tmp_path / "public"), repo=str(src))  # fine


def test_prepare_dest_refuses_a_dirty_public_tree(tmp_path):
    dest = tmp_path / "public"
    dest.mkdir()
    _git(["init", "-q", "-b", "main"], dest)
    (dest / "edited.txt").write_text("x", encoding="utf-8")
    with pytest.raises(SystemExit, match="uncommitted"):
        ex.prepare_dest(str(dest))
    assert (dest / "edited.txt").exists(), "refusal must not delete anything"
