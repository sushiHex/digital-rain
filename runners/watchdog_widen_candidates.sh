#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
touch WATCHDOG_WIDEN_RUNNING
while true; do
  if [ -f WIDEN_DONE ] || [ -f WIDEN_FAIL ] || [ -f WIDEN_STOP ]; then
    echo "watchdog: terminal state reached, exiting @ $(date '+%H:%M:%S')" >> watchdog_widen.log
    break
  fi
  outer=$(python misc/count_running.py "widen_candidates.sh" || echo -1)   # no output at all would read as 0, hence relaunch
  if [ "${outer:-0}" -eq 0 ]; then
    n=$(ls dpo_pilot/candidates/*/*.png 2>/dev/null | wc -l)
    echo "watchdog: widen_candidates.sh outer loop gone, $n candidate PNGs, relaunching @ $(date '+%H:%M:%S')" >> watchdog_widen.log
    "C:\Program Files\Git\bin\bash.exe" ./runners/widen_candidates.sh &
    sleep 120
  fi
  sleep 180
done
rm -f WATCHDOG_WIDEN_RUNNING
