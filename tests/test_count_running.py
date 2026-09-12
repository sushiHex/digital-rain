"""Prove the watchdogs' replacement process count against a real process.

The `wmic` line it replaces was never tested against anything live, which is
exactly why nobody noticed the command had stopped existing: the pipeline
produced no output, `grep -c` said 0, and 0 is a perfectly ordinary answer.
So the tests here spawn an actual process and count it, rather than mocking
psutil -- a mocked process table would have passed for the `wmic` version too.
"""
import os
import shutil
import subprocess
import sys
import uuid

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from misc import count_running  # noqa: E402

HELPER = os.path.join(REPO, "misc", "count_running.py")


@pytest.fixture
def marked_process():
    """A live process carrying a unique marker in its command line.

    The marker is an extra argv the `sleep` ignores -- the point is the
    command line, not what the process does.
    """
    marker = f"count-running-probe-{uuid.uuid4().hex}"
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", marker])
    try:
        yield marker, proc
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=30)


def _cli(*patterns):
    out = subprocess.run([sys.executable, HELPER, *patterns],
                         capture_output=True, text=True, cwd=REPO)
    assert out.returncode == 0, f"the helper must always exit 0: {out.stderr}"
    return int(out.stdout.strip().splitlines()[-1])


def absent(n):
    """Not counted as present, on a machine other things are running on.

    `<= 0` rather than `== 0` because -1 is a legitimate answer here: if any
    unrelated shell or Python on the box has an unreadable command line at
    that instant -- a process dying mid-scan will do it -- the helper declines
    to call the count zero. Both answers mean "do not treat this as alive".
    The exact 0-versus-(-1) semantics are pinned against a fixed process table
    in the `_FakeProc` tests below, where nothing else can interfere.
    """
    return n <= 0


def test_a_live_process_is_counted(marked_process):
    marker, _ = marked_process
    assert count_running.count([marker]) == 1


def test_a_dead_process_is_not_counted(marked_process):
    marker, proc = marked_process
    proc.terminate()
    proc.wait(timeout=30)
    assert absent(count_running.count([marker]))


def test_the_cli_prints_the_count(marked_process):
    """The watchdogs read stdout, so the number has to arrive there."""
    marker, proc = marked_process
    assert _cli(marker) == 1
    proc.terminate()
    proc.wait(timeout=30)
    assert absent(_cli(marker))


def test_the_helper_does_not_count_itself():
    """Its own argv contains the pattern; a self-match would read as alive
    forever and no watchdog would ever relaunch anything.

    The second pattern is what makes this a test of self-exclusion rather than
    of the ancestry: run as `pytest tests/test_count_running.py`, the pytest
    process AND the shell that typed that line both carry `count_running.py`
    in their own command lines, so the bare pattern legitimately counts 3.
    Only the helper's own argv carries the marker as well.
    """
    marker = f"count-running-selfcheck-{uuid.uuid4().hex}"
    assert absent(_cli("count_running.py", marker))


def test_a_shell_named_after_its_pattern_does_not_count_itself(tmp_path):
    """The shape of five of the eight watchdogs, end to end.

    `watchdog_stage_a_eval.sh` searches for `stage_a_eval.sh`, which is a
    substring of its own name, so its own `wmic` line matched and `outer` was
    never 0 -- a dead runner would never have been relaunched. Excluding the
    asking process's whole ancestor chain is what fixes it: the parent alone
    left 3, because the launcher above it carries the same command line.
    """
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("no bash on PATH")
    marker = f"probe-{uuid.uuid4().hex}.sh"
    script = tmp_path / marker
    script.write_text(
        "#!/usr/bin/env bash\nset -u\n"
        f'outer=$("{sys.executable.replace(os.sep, "/")}" '
        f'"{HELPER.replace(os.sep, "/")}" "{marker}")\n'
        'echo "outer=$outer"\n', encoding="utf-8")
    out = subprocess.run([bash, str(script).replace(os.sep, "/")],
                         capture_output=True, text=True, cwd=REPO)
    assert out.returncode == 0, out.stderr
    reported = out.stdout.strip().splitlines()[-1]
    assert reported.startswith("outer="), out.stdout
    assert absent(int(reported.split("=", 1)[1])), out.stdout


def test_every_pattern_must_match(marked_process):
    """The AND form is what replaces the two `grep "a.*b"` callers."""
    marker, _ = marked_process
    assert count_running.count([marker, "time.sleep"]) == 1
    assert absent(count_running.count([marker, "a-string-no-process-has"]))


class _FakeProc:
    def __init__(self, pid, name, cmdline):
        self.info = {"pid": pid, "name": name, "cmdline": cmdline}


def test_a_zero_beside_an_unreadable_shell_is_undecidable(monkeypatch):
    """psutil returns cmdline=None for AccessDenied rather than raising.

    Counting that as "absent" is the original bug wearing a new coat: a live
    runner whose command line could not be read would be relaunched. A zero
    next to an unreadable bash or python is -1, not 0.
    """
    monkeypatch.setattr(count_running.psutil, "process_iter",
                        lambda attrs=None: [_FakeProc(4242, "bash.exe", None)])
    assert count_running.count(["whatever"]) == -1


def test_an_unreadable_svchost_does_not_make_every_count_undecidable(monkeypatch):
    """147 of 570 processes here have no readable command line, nearly all of
    them svchost. If those escalated, -1 would be the normal answer and the
    watchdog would never relaunch anything."""
    monkeypatch.setattr(count_running.psutil, "process_iter",
                        lambda attrs=None: [_FakeProc(4242, "svchost.exe", None)])
    assert count_running.count(["whatever"]) == 0


def test_an_unreadable_process_beside_a_real_match_still_counts(monkeypatch):
    """Once something matched, the runner is known to be alive."""
    monkeypatch.setattr(count_running.psutil, "process_iter", lambda attrs=None: [
        _FakeProc(4242, "bash.exe", None),
        _FakeProc(4243, "bash.exe", ["bash", "./runners/run_x.sh"]),
    ])
    assert count_running.count(["run_x.sh"], exclude_pids=()) == 1


def test_an_unreadable_process_table_prints_minus_one(monkeypatch, capsys):
    """A watchdog that cannot count must NOT relaunch, so the sentinel has to
    be non-zero: `[ "${outer:-0}" -eq 0 ]` reads -1 as "still alive"."""
    def boom(*a, **k):
        raise RuntimeError("no process table")
    monkeypatch.setattr(count_running.psutil, "process_iter", boom)
    assert count_running.main(["anything"]) == 0
    assert capsys.readouterr().out.strip() == "-1"
