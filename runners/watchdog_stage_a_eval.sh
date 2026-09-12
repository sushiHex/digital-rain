#!/usr/bin/env bash
# Relaunches stage_a_eval.sh if its OWN process (the outer loop, not just the
# eval_checkpoint.py child it spawns per attempt) dies before completion.
# The prior run died silently ~7h45m before detection (log mtime stale, both
# eval_checkpoint.py AND the outer loop bash gone) — a full process-tree
# kill, not a wedge. Untracked/detached, matching the training-run pattern.
#
# NOTE: stage_a_eval.sh has its OWN internal retry loop + VRAM wait (up to 4h
# between attempts), so eval_checkpoint.py being briefly absent is normal —
# only relaunch if the OUTER script itself is gone.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
touch WATCHDOG_STAGE_A_EVAL_RUNNING
while true; do
  if [ -f STAGE_A_EVAL_DONE ] || [ -f STAGE_A_EVAL_FAIL ] || [ -f STAGE_A_EVAL_STOP ]; then
    echo "watchdog: terminal state reached, exiting @ $(date '+%H:%M:%S')" >> watchdog_stage_a_eval.log
    break
  fi
  outer=$(python misc/count_running.py "stage_a_eval.sh" || echo -1)   # no output at all would read as 0, hence relaunch
  if [ "${outer:-0}" -eq 0 ]; then
    n=$(ls eval_runs/stageA_pilot/generated/*.png 2>/dev/null | wc -l)
    echo "watchdog: stage_a_eval.sh outer loop gone, $n/50 atlases, relaunching @ $(date '+%H:%M:%S')" >> watchdog_stage_a_eval.log
    "C:\Program Files\Git\bin\bash.exe" ./runners/stage_a_eval.sh &
    sleep 120   # let it fully start before the next liveness check
  fi
  sleep 180
done
rm -f WATCHDOG_STAGE_A_EVAL_RUNNING
