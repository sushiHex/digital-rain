#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
touch WATCHDOG_HOLDOUT_BESTOFN_RUNNING
while true; do
  if [ -f HOLDOUT_BESTOFN_DONE ] || [ -f HOLDOUT_BESTOFN_FAIL ] || [ -f HOLDOUT_BESTOFN_STOP ]; then
    echo "watchdog: terminal state reached, exiting @ $(date '+%H:%M:%S')" >> watchdog_holdout_bestofn.log
    break
  fi
  outer=$(python misc/count_running.py "holdout_bestofn.sh" || echo -1)   # no output at all would read as 0, hence relaunch
  if [ "${outer:-0}" -eq 0 ]; then
    n=$(ls dpo_holdout_bestofn/candidates/*/*.png 2>/dev/null | wc -l)
    echo "watchdog: holdout_bestofn.sh outer loop gone, $n candidate PNGs, relaunching @ $(date '+%H:%M:%S')" >> watchdog_holdout_bestofn.log
    "C:\Program Files\Git\bin\bash.exe" ./runners/holdout_bestofn.sh &
    sleep 120
  fi
  sleep 180
done
rm -f WATCHDOG_HOLDOUT_BESTOFN_RUNNING
