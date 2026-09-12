"""Pin the runners to their directory, the directory to its index, and the
files to being executable.

The 43 shell runners lived at the repo root for five months, each doing
`cd "$(dirname "$0")"` on the assumption that the root IS where it lives.
Moving them to `runners/` (2026-09-11) changed that line to
`cd "$(dirname "$0")/.."`, so every relative path inside them still resolves
from the repo root. A runner added later without the line would silently run
from `runners/` and write its markers and logs there; a runner dropped back at
the root would re-grow the clutter the move removed. Both are drift that
nothing else would catch.

EXECUTABLE IN THE INDEX. Every runner was tracked as mode 100644 for its whole
life, because Windows has no executable bit and git here never set one. The
README tells a Linux reader to run `./runners/x.sh`, and two runners chain into
siblings the same way; on a Linux checkout that was "Permission denied". The
mode lives in the index, so it is checked there, not on the filesystem.
"""
import glob
import os
import re
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNNERS = os.path.join(REPO, "runners")
SELF_LOCATE = 'cd "$(dirname "$0")/.."'
# Any `./name.sh` that names a sibling must go through runners/.
SIBLING = re.compile(r'(?<![\w/])\./(?!runners/)[\w.-]+\.sh\b')


def runners():
    return sorted(glob.glob(os.path.join(RUNNERS, "*.sh")))


def test_there_are_runners():
    assert len(runners()) >= 40


def test_no_shell_runner_sits_at_the_repo_root():
    assert glob.glob(os.path.join(REPO, "*.sh")) == []


def test_every_runner_self_locates_to_the_repo_root():
    missing = [os.path.basename(p) for p in runners()
               if SELF_LOCATE not in open(p, encoding="utf-8").read()]
    assert missing == [], f"no `{SELF_LOCATE}` in: {missing}"


def test_every_sibling_relaunch_goes_through_runners():
    bad = []
    for p in runners():
        for m in SIBLING.finditer(open(p, encoding="utf-8").read()):
            bad.append((os.path.basename(p), m.group(0)))
    assert bad == [], f"relaunch by root-relative path: {bad}"


def test_every_runner_is_executable_in_the_index():
    out = subprocess.run(["git", "ls-files", "-s", "--", "runners/*.sh"],
                         cwd=REPO, capture_output=True, text=True, check=True).stdout
    modes = {ln.split()[3]: ln.split()[0] for ln in out.splitlines() if ln}
    assert len(modes) >= 40, "git did not list the runners"
    not_exec = sorted(p for p, m in modes.items() if m != "100755")
    assert not_exec == [], ("tracked without the executable bit -- run "
                            "`git update-index --chmod=+x -- runners/*.sh`: "
                            f"{not_exec}")


def test_no_runner_counts_processes_with_wmic():
    """`wmic` is gone from this Windows build, and its absence was silent.

    The pipeline produced no output, `grep -c` returned 0, and 0 is what a
    watchdog reads as "the runner is gone" -- so a 24-hour run would have been
    relaunched on top of itself every 180 s. `misc/count_running.py` replaced
    every use; this stops one coming back by copy-paste from an old runner.
    """
    bad = [os.path.basename(p) for p in runners()
           if "wmic" in open(p, encoding="utf-8").read()]
    assert bad == [], f"counts processes with wmic, which is not installed: {bad}"


def test_every_watchdog_counts_with_the_helper():
    watchdogs = [p for p in runners()
                 if os.path.basename(p).startswith("watchdog_")]
    assert len(watchdogs) >= 8, "git did not list the watchdogs"
    missing = [os.path.basename(p) for p in watchdogs
               if "misc/count_running.py" not in open(p, encoding="utf-8").read()]
    assert missing == [], f"no process count via misc/count_running.py in: {missing}"


def test_the_index_lists_every_runner():
    index = open(os.path.join(RUNNERS, "README.md"), encoding="utf-8").read()
    unlisted = [os.path.basename(p) for p in runners()
                if f"`{os.path.basename(p)}`" not in index]
    assert unlisted == [], f"runners/README.md does not list: {unlisted}"
    listed = set(re.findall(r"^- `([\w.-]+\.sh)`", index, re.M))
    gone = sorted(listed - {os.path.basename(p) for p in runners()})
    assert gone == [], f"runners/README.md lists runners that do not exist: {gone}"
