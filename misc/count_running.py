"""Count the live processes whose command line contains every given substring.

WHY THIS EXISTS. Every `runners/watchdog_*.sh` decided whether its runner was
still alive with `wmic process where "name='bash.exe'" get commandline |
grep -c "<runner>.sh"`. This Windows build no longer ships `wmic` (checked
2026-09-11: `where wmic` finds nothing), so the pipeline produced no output,
the count read 0, and the watchdog concluded the runner was gone -- every poll,
for a runner that was running fine. A 24-hour training run under that watchdog
would have been relaunched onto the GPU on top of itself, every 180 seconds.
psutil is already a dependency and is not Windows-specific, so this replaces
the `wmic` line on every platform rather than trading one for another.

WHY IT PRINTS -1 AND NEVER FAILS. The caller is `outer=$(python
misc/count_running.py "run_x.sh")` followed by `[ "${outer:-0}" -eq 0 ]`, so
whatever this prints IS the decision. Printing 0 when the count cannot be taken
would reproduce the bug being fixed: an unreadable process table would read as
"the runner is gone" and relaunch a live run. A watchdog that cannot count must
not relaunch, so an error prints -1 -- not 0, and not a failure exit, because a
non-zero exit leaves the substitution empty and `${outer:-0}` turns that back
into 0. -1 is non-zero, so every existing `-eq 0` test already treats it as
"alive", which is the safe direction: the cost of a false "alive" is a watchdog
that does nothing, and the cost of a false "gone" is two trainings on one card.

MATCHING. All substrings must appear in the process's joined command line, so
`count_running.py train_lora_kg.py training_glyph_r32_5000` replaces the
`grep "train_lora_kg.py.*$OUT"` the two regex callers used, without ordering.
Comparison is case-insensitive: Windows hands back paths in whatever case the
launcher used, and a missed match is the failure mode this module exists to
prevent.

EXCLUSION IS BY PID, AND IT IS THE WHOLE ANCESTOR CHAIN. This module's own argv
contains the pattern, so it must not count itself. Neither may the shell that
asked: five of the eight watchdogs are named after the runner they watch, so
`watchdog_stage_a_eval.sh` contains `stage_a_eval.sh` and matched its own
`wmic` line -- a second defect in the same line, pointing the other way, which
would have left a genuinely dead runner unrestarted. The parent alone is not
enough either; measured from such a shell, excluding only self and parent
still counted 3, because the launcher above it carries the same command line
and `$(...)` can fork a copy of the shell in between. Every ancestor is
excluded instead, and the same probe then reported 0. That cannot hide a real
match: a watched runner is a detached sibling or a child, never an ancestor of
the watchdog asking about it.

SIBLINGS ARE NOT EXCLUDABLE BY PID, and that is the honest limit. For those
same five, two copies of one watchdog would each read the other's command line
as the runner and neither would relaunch a dead one; measured, running the
probe under a harness that keeps its own shell alive beside it returns 2 for
the same reason. One watchdog per runner is a standing rule, not something a
process count can decide -- and this is still an improvement on the `wmic`
line, where a single watchdog was enough to match itself.

A PROCESS WHOSE COMMAND LINE CANNOT BE READ IS UNDECIDABLE, NOT ABSENT.
`process_iter(attrs=...)` hands back `cmdline=None` for AccessDenied rather
than raising, so skipping those quietly would put the original bug back: a
live runner whose command line happened to be unreadable would count as gone
and be relaunched. Escalating every one of them is not usable either -- 147 of
570 processes on this machine have an unreadable command line, nearly all of
them `svchost.exe` -- so -1 would become the normal answer and the watchdog
permanently inert. The line is drawn by NAME, which stays readable when the
command line does not: an unreadable process named like a shell or a Python
(`bash`, `sh`, `pwsh`, `python*`, ...) could be the runner, so a count of zero
alongside one of those returns -1 instead. Measured on the same 570: two
unreadable processes match on name substrings and neither matches on the stem
this uses, so in practice zero means zero.

  python misc/count_running.py "run_glyph_4b_r32.sh"
  python misc/count_running.py "train_lora_kg.py" "training_glyph_r32_5000"
"""

# repo root on sys.path so `python misc/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import os
import sys

try:
    import psutil
except Exception:                 # a missing psutil must print -1, not traceback
    psutil = None

ERROR = -1
# Executable stems a watched runner could have. An unreadable process with one
# of these names makes a zero count undecidable; anything else cannot be a
# runner of ours. Stems are compared after stripping `.exe`, so `python3.12`
# and `pythonw` are covered by the prefix.
SHELL_STEMS = ("bash", "sh", "dash", "zsh", "ksh", "pwsh", "powershell", "cmd")
SHELL_PREFIXES = ("python",)


def _own_pids(limit=64):
    """This process and every ancestor of it. See MATCHING in the docstring.

    The whole chain, not just the parent: the asking shell's own launcher
    carries the same command line, and a `$(...)` substitution may add a
    forked copy of the shell in between.
    """
    me = os.getpid()
    pids = {me}
    try:
        proc = psutil.Process(me)
    except (psutil.Error, OSError):
        return pids
    for _ in range(limit):
        try:
            proc = proc.parent()
        except (psutil.Error, OSError):
            break
        if proc is None or proc.pid in pids:
            break
        pids.add(proc.pid)
    return pids


def could_be_a_runner(name):
    """Is this executable name one a watched runner could have?"""
    stem = (name or "").lower()
    if stem.endswith(".exe"):
        stem = stem[:-4]
    return stem in SHELL_STEMS or stem.startswith(SHELL_PREFIXES)


def count(patterns, exclude_pids=None):
    """Live processes whose command line contains every pattern, case-folded.

    Returns ERROR (-1) when the count is zero but at least one process that
    could have been the runner had an unreadable command line -- undecidable,
    and the safe answer to an undecidable question here is "still alive".

    Raises whatever psutil raises at the process-table level; `main` turns
    that into -1 as well.
    """
    if psutil is None:
        raise RuntimeError("psutil is not importable (it is in requirements.txt)")
    wanted = [p.lower() for p in patterns]
    skip = _own_pids() if exclude_pids is None else set(exclude_pids)
    n = 0
    undecidable = 0
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            info = proc.info
            if info["pid"] in skip:
                continue
            cmdline = " ".join(info["cmdline"] or "").lower()
            name = info["name"]
        except (psutil.Error, OSError, TypeError, KeyError):
            # Raised rather than filled in, which `process_iter(attrs=...)`
            # does only for a process that went away mid-scan -- AccessDenied
            # and ZombieProcess come back as None instead. A process that no
            # longer exists is absent, not undecidable, so it is skipped.
            continue
        if not cmdline:
            undecidable += could_be_a_runner(name)
        elif all(w in cmdline for w in wanted):
            n += 1
    return n if n or not undecidable else ERROR


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Count live processes whose command line contains every "
                    "PATTERN. Prints the count, or -1 if it cannot be taken; "
                    "always exits 0, because a watchdog reads the number.")
    ap.add_argument("pattern", nargs="+", help="substring the command line must contain")
    args = ap.parse_args(argv)

    try:
        print(count(args.pattern))
    except Exception as exc:
        # -1, never 0, and never a non-zero exit: see the module docstring.
        print(ERROR)
        print(f"count_running: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
