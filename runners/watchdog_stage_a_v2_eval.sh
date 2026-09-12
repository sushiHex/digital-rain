#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
touch WATCHDOG_STAGE_A_V2_EVAL_RUNNING
while true; do
  if [ -f STAGE_A_V2_EVAL_DONE ] || [ -f STAGE_A_V2_EVAL_FAIL ] || [ -f STAGE_A_V2_EVAL_STOP ]; then
    echo "watchdog: terminal state reached, exiting @ $(date '+%H:%M:%S')" >> watchdog_stage_a_v2_eval.log
    break
  fi
  outer=$(wmic process where "name='bash.exe'" get commandline 2>/dev/null | grep -c "stage_a_v2_eval\.sh")
  if [ "${outer:-0}" -eq 0 ]; then
    n=$(ls eval_runs/stageA_v2/generated/*.png 2>/dev/null | wc -l)
    echo "watchdog: stage_a_v2_eval.sh outer loop gone, $n/50 atlases, relaunching @ $(date '+%H:%M:%S')" >> watchdog_stage_a_v2_eval.log
    "C:\Program Files\Git\bin\bash.exe" ./runners/stage_a_v2_eval.sh &
    sleep 120
  fi
  sleep 180
done
rm -f WATCHDOG_STAGE_A_V2_EVAL_RUNNING
