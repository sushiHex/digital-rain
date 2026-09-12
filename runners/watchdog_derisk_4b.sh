#!/usr/bin/env bash
# Watchdog for run_derisk_4b.sh. Relaunches the runner if its outer loop dies
# before a terminal marker appears (harness task-kills, transient OOM).
#
# NEED_MB must match the runner's VRAM gate: a mismatch previously made a
# legitimately-parked runner read as stalled. Export the same value to both.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
touch WATCHDOG_DERISK_4B_RUNNING
LOG=watchdog_derisk_4b.log
while true; do
  if [ -f DERISK_4B_DONE ] || [ -f DERISK_4B_FAIL ] || [ -f DERISK_4B_STOP ]; then
    echo "watchdog: terminal state reached, exiting @ $(date '+%H:%M:%S')" >> "$LOG"
    break
  fi
  outer=$(python misc/count_running.py "run_derisk_4b.sh" || echo -1)   # no output at all would read as 0, hence relaunch
  if [ "${outer:-0}" -eq 0 ]; then
    steps=$(tail -200 derisk_4b.log 2>/dev/null | grep -oE 'step [0-9]+' | tail -1)
    echo "watchdog: run_derisk_4b.sh outer loop gone (${steps:-no step yet}), relaunching @ $(date '+%H:%M:%S')" >> "$LOG"
    "C:\Program Files\Git\bin\bash.exe" ./runners/run_derisk_4b.sh &
    sleep 120
  fi
  sleep 180
done
rm -f WATCHDOG_DERISK_4B_RUNNING
