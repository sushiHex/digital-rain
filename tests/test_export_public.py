"""Pin what the public export withholds, and that it withholds it.

The public repository is a fresh history built from the private tree by
`misc/export_public.py`. Three properties keep that safe:

  * EVERY EXCLUSION RULE STILL MATCHES SOMETHING. A rule that matches nothing
    is a guard that has silently died (a directory renamed under it) -- the
    same shape as the glob mismatches that dropped a description from the
    transfer test without erroring. The script refuses to run; this test
    refuses first.
  * THE THINGS KNOWN TO BE PRIVATE ARE IN THE EXCLUDED HALF, by name, so a
    rewrite of the rules cannot quietly let one through.
  * THE END-TO-END PATH STAGES EXACTLY THE KEPT SET, including files the
    shared .gitignore would otherwise skip (the eval artifacts behind the
    README table are force-added in the private tree and must be in the
    public one too).

THESE TESTS RUN IN BOTH TREES. In the public repository every rule is dead by
construction -- that is what an export IS -- so the rule-level tests skip
there rather than fail CI, and `misc/export_public.py` itself refuses to run.
The fixture-repo test and the public-face test run everywhere.
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
              "research/2026-03-29-oracle-round21-report.md"):
        assert p not in kept, p
    for prefix in ("research/sessions/", "docs/archive/", "docs/superpowers/"):
        assert not any(p.startswith(prefix) for p in kept), prefix


def test_the_public_face_is_kept():
    """Runs in both trees: in the export these files simply exist."""
    kept, _ = ex.partition(ex.tracked_at_head(ex.REPO))
    for p in ("README.md", "CLAUDE.md", "AGENTS.md", "LICENSE",
              "docs/public-release.md", "docs/what-happened.md",
              "research/README.md", "misc/export_public.py",
              ".github/PULL_REQUEST_TEMPLATE.md", ".github/workflows/ci.yml",
              "eval_runs/prompt_trained_short/per_cell.json"):
        assert p in kept, p


def test_a_public_export_refuses_to_export_itself():
    """`main()` must stop on a tree where no rule matches -- the public repo."""
    excluded = {pat: [] for pat, _ in ex.EXCLUDE}
    assert ex.is_export(excluded)
    excluded[ex.EXCLUDE[0][0]] = ["something"]
    assert not ex.is_export(excluded)


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout


def test_end_to_end_on_a_fixture_repo(tmp_path, monkeypatch):
    """Excluded file absent, ignored-but-tracked file present, contents exact."""
    src = tmp_path / "private"
    src.mkdir()
    _git(["init", "-q", "-b", "main"], src)
    _git(["config", "user.email", "t@example.invalid"], src)
    _git(["config", "user.name", "t"], src)
    (src / "keep.py").write_text("print('kept')\n", encoding="utf-8")
    (src / ".gitignore").write_text("*.json\n", encoding="utf-8")
    (src / "secret").mkdir()
    (src / "secret" / "notes.md").write_text("private\n", encoding="utf-8")
    (src / "forced.json").write_text("{}\n", encoding="utf-8")
    _git(["add", "keep.py", ".gitignore", "secret/notes.md"], src)
    _git(["add", "-f", "forced.json"], src)
    _git(["commit", "-q", "-m", "fixture"], src)

    rules = (("secret/", "fixture"),)
    monkeypatch.setattr(ex, "EXCLUDE", rules)
    monkeypatch.setattr(ex, "MAY_BE_EMPTY", set())
    keep, excluded = ex.partition(ex.tracked_at_head(str(src)), rules)
    assert keep == [".gitignore", "forced.json", "keep.py"]
    assert excluded == {"secret/": ["secret/notes.md"]}

    dest = tmp_path / "public"
    ex.prepare_dest(str(dest))
    assert ex.extract_head(str(src), str(dest), keep) == 3
    ex.stage(str(dest), keep)
    staged = sorted(p for p in _git(["ls-files", "-z"], dest).split("\0") if p)
    assert staged == keep
    assert not (dest / "secret").exists()
    assert (dest / "keep.py").read_bytes() == (src / "keep.py").read_bytes()
    assert (dest / "forced.json").exists()


def test_prepare_dest_refuses_a_dirty_public_tree(tmp_path):
    dest = tmp_path / "public"
    dest.mkdir()
    _git(["init", "-q", "-b", "main"], dest)
    (dest / "edited.txt").write_text("x", encoding="utf-8")
    try:
        ex.prepare_dest(str(dest))
    except SystemExit as e:
        assert "uncommitted" in str(e)
    else:
        raise AssertionError("a dirty destination must be refused")
    assert (dest / "edited.txt").exists(), "refusal must not delete anything"
