"""Pin the publication gate to the leak it missed.

`sanitize_for_publish.py --check` reported the tree clean on 2026-09-11 while
three tracked JSON result files carried `C:\\Users\\<name>\\repos\\fonts\\...`.
JSON doubles every backslash, and the home-path pattern allowed exactly one
separator, so a path that a human reads as a home path was invisible to the
gate. A gate that passes on the thing it exists to catch is worse than no
gate: it converts "unchecked" into "verified clean".

Two properties this file keeps:

  * EVERY spelling of a home path is caught -- plain, JSON-escaped, MSYS.
  * `--check` fails on a tracked file carrying one. The unit test on the
    regex is not enough by itself; the CLI is what the release runbook calls.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.sanitize_for_publish import clean_text, scan_text  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
TOOL = REPO / "analysis" / "sanitize_for_publish.py"

# The fixtures are ASSEMBLED at runtime rather than written out, because this
# file is itself tracked and the gate scans it: a literal home path here would
# fail the very check it tests. (It did, the first time.)
NAME = "someone"


def home(sep):
    return f"C:{sep}Users{sep}{NAME}{sep}repos{sep}fonts"


@pytest.mark.parametrize("text", [
    home("\\"),                              # plain Windows
    home("\\\\"),                            # as it sits inside JSON
    home("/"),                               # forward slashes
    "/c/Users/" + NAME + "/repos/fonts",     # MSYS / Git Bash
    json.dumps({"dir": home("\\")}),         # a real JSON payload
])
def test_every_spelling_of_a_home_path_is_found(text):
    n_home, _, _, _ = scan_text(text)
    assert n_home >= 1, f"missed: {text!r}"
    assert NAME not in clean_text(text)


def test_a_repo_relative_path_is_not_a_finding():
    n_home, _, _, _ = scan_text('{"dir": "eval_runs/_candidate_refs/klein-base-n4"}')
    assert n_home == 0


def test_check_fails_on_a_tracked_json_with_an_escaped_home_path(tmp_path):
    """The CLI must fail, not just the regex -- the runbook calls the CLI."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"],
                   cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    leak = tmp_path / "record.json"
    leak.write_text(json.dumps({"dir": home("\\")}), encoding="utf-8")
    subprocess.run(["git", "add", "record.json"], cwd=tmp_path, check=True)
    proc = subprocess.run([sys.executable, str(TOOL), "--check"],
                          cwd=tmp_path, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "home path" in proc.stdout


def test_the_tracked_tree_is_clean():
    """The gate itself, as the release runbook runs it."""
    proc = subprocess.run([sys.executable, str(TOOL), "--check"],
                          cwd=REPO, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
