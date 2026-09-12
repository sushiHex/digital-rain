#!/usr/bin/env bash
# Relaunches stage_a_lite_eval.sh if its OWN process dies (full process-tree
# kill, distinct from eval_checkpoint.py being briefly absent between the
# script's own retry attempts) — see watchdog_stage_a_eval.sh for the incident
# that motivated this pattern.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
touch WATCHDOG_STAGE_A_LITE_EVAL_RUNNING
while true; do
  if [ -f STAGE_A_LITE_EVAL_DONE ] || [ -f STAGE_A_LITE_EVAL_FAIL ] || [ -f STAGE_A_LITE_EVAL_STOP ]; then
    echo "watchdog: terminal state reached, exiting @ $(date '+%H:%M:%S')" >> watchdog_stage_a_lite_eval.log
    break
  fi
  outer=$(python misc/count_running.py "stage_a_lite_eval.sh" || echo -1)   # no output at all would read as 0, hence relaunch
  if [ "${outer:-0}" -eq 0 ]; then
    n=$(ls eval_runs/stageA_lite/generated/*.png 2>/dev/null | wc -l)
    echo "watchdog: stage_a_lite_eval.sh outer loop gone, $n/50 atlases, relaunching @ $(date '+%H:%M:%S')" >> watchdog_stage_a_lite_eval.log
    "C:\Program Files\Git\bin\bash.exe" ./runners/stage_a_lite_eval.sh &
    sleep 120
  fi
  sleep 180
done
rm -f WATCHDOG_STAGE_A_LITE_EVAL_RUNNING
