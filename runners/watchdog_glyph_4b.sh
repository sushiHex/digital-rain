#!/usr/bin/env bash
# Watchdog for run_glyph_4b_r32.sh (~12h run on a contended GPU).
# The runner already resumes internally on eviction; this catches the case
# where the runner's own outer loop is killed (harness task-kill, shell death).
#
# NEED_MB must match the runner's gate -- a mismatch once made a legitimately
# parked runner read as stalled.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
touch WATCHDOG_GLYPH_4B_RUNNING
LOG=watchdog_glyph_4b.log
while true; do
  if [ -f GLYPH_4B_DONE ] || [ -f GLYPH_4B_FAIL ] || [ -f GLYPH_4B_STOP ]; then
    echo "watchdog: terminal state reached, exiting @ $(date '+%H:%M:%S')" >> "$LOG"
    break
  fi
  outer=$(wmic process where "name='bash.exe'" get commandline 2>/dev/null | grep -c "run_glyph_4b_r32\.sh")
  if [ "${outer:-0}" -eq 0 ]; then
    step=$(tr '\r' '\n' < glyph_4b.log 2>/dev/null | grep -aoE "step +[0-9]+/5000" | tail -1)
    echo "watchdog: runner gone (${step:-no step yet}), relaunching @ $(date '+%H:%M:%S')" >> "$LOG"
    "C:\Program Files\Git\bin\bash.exe" ./runners/run_glyph_4b_r32.sh &
    sleep 300
  fi
  sleep 180
done
rm -f WATCHDOG_GLYPH_4B_RUNNING
