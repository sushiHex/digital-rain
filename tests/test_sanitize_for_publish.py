"""Pin the publication gate to the leaks it missed.

`sanitize_for_publish.py --check` reported the tree clean on 2026-09-11 while
three tracked JSON result files carried `C:\\Users\\<name>\\repos\\fonts\\...`.
JSON doubles every backslash, and the home-path pattern allowed exactly one
separator, so a path that a human reads as a home path was invisible to the
gate. A gate that passes on the thing it exists to catch is worse than no
gate: it converts "unchecked" into "verified clean".

Properties this file keeps:

  * EVERY spelling of a home path is caught -- plain, JSON-escaped, MSYS, WSL,
    file URL, UNC, Linux, macOS -- and a URL path segment is NOT (a review
    found `example.edu/home/x` would otherwise be a false hit).
  * The broadened token shapes are caught; an `.env.example` placeholder is not.
  * A tracked font, weight or archive fails `--check` by itself.
  * `--check` fails on a tracked file carrying a leak. The unit test on the
    regex is not enough by itself; the CLI is what the release runbook calls.
"""
import json
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
    home("\\"),                                  # plain Windows
    home("\\\\"),                                # as it sits inside JSON
    home("/"),                                   # forward slashes
    "/c/Users/" + NAME + "/repos/fonts",         # MSYS / Git Bash
    "/mnt/c/Users/" + NAME + "/repos",           # WSL
    "file:///C:/Users/" + NAME + "/repos",       # file URL
    "\\\\" + "host01" + "\\Users\\" + NAME,      # UNC
    "cwd: /home/" + NAME + "/repos/fonts",       # Linux
    "path='/Users/" + NAME + "/repos'",          # macOS
    json.dumps({"dir": home("\\")}),             # a real JSON payload
])
def test_every_spelling_of_a_home_path_is_found(text):
    n_home, _, _, _ = scan_text(text)
    assert n_home >= 1, f"missed: {text!r}"
    assert NAME not in clean_text(text)


@pytest.mark.parametrize("text", [
    '{"dir": "eval_runs/_candidate_refs/klein-base-n4"}',
    "http://www.example.edu/home/" + NAME + "/paper.pdf",    # a URL segment
    "see https://example.com/Users/" + NAME + "/profile",
])
def test_a_repo_relative_path_or_url_segment_is_not_a_finding(text):
    n_home, _, _, _ = scan_text(text)
    assert n_home == 0, text


@pytest.mark.parametrize("token,name", [
    ("sk-" + "a" * 24, "openai-style key"),
    ("sk-proj-" + "a" * 24, "openai-style key"),
    ("ghp_" + "b" * 24, "github token"),
    ("gho_" + "b" * 24, "github token"),
    ("github_pat_" + "c" * 30, "github fine-grained token"),
    ("AKIA" + "D" * 16, "aws access key"),
    ("xoxb-" + "1234567890-abcdef", "slack token"),
    ("Authorization: Bearer " + "e" * 32, "bearer credential"),
])
def test_token_shapes_are_found(token, name):
    _, _, secrets, _ = scan_text("some text " + token + " more")
    assert name in secrets, (token, secrets)


def test_the_env_example_placeholders_are_not_secrets():
    text = (REPO / ".env.example").read_text(encoding="utf-8")
    _, _, secrets, _ = scan_text(text)
    assert secrets == []


def _repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"],
                   cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)


def _check(cwd):
    return subprocess.run([sys.executable, str(TOOL), "--check"], cwd=cwd,
                          capture_output=True, text=True)


def test_check_fails_on_a_tracked_json_with_an_escaped_home_path(tmp_path):
    """The CLI must fail, not just the regex -- the runbook calls the CLI."""
    _repo(tmp_path)
    leak = tmp_path / "record.json"
    leak.write_text(json.dumps({"dir": home("\\")}), encoding="utf-8")
    subprocess.run(["git", "add", "record.json"], cwd=tmp_path, check=True)
    proc = _check(tmp_path)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "home path" in proc.stdout


def test_check_fails_on_a_tracked_font_or_weight(tmp_path):
    """Fonts and weights are the two licensing blockers; an archive can carry
    anything. Their presence alone fails the gate, and --fix leaves them."""
    _repo(tmp_path)
    (tmp_path / "clean.md").write_text("nothing to see\n", encoding="utf-8")
    (tmp_path / "Some.ttf").write_bytes(b"\x00\x01\x00\x00")
    subprocess.run(["git", "add", "clean.md", "Some.ttf"], cwd=tmp_path, check=True)
    proc = _check(tmp_path)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "Some.ttf" in proc.stdout
    subprocess.run([sys.executable, str(TOOL), "--fix"], cwd=tmp_path,
                   capture_output=True, text=True)
    assert (tmp_path / "Some.ttf").exists()


def test_the_tracked_tree_is_clean():
    """The gate itself, as the release runbook runs it."""
    proc = _check(REPO)
    assert proc.returncode == 0, proc.stdout + proc.stderr
