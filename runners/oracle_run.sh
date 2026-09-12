#!/usr/bin/env bash
# Detached Oracle run (survives harness task-kills). Marker: oracle_DONE. Log: oracle_relaunch.log
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
PROMPTS="${ORACLE_PROMPTS:?set ORACLE_PROMPTS to the Smith-prompts JSON array}"
ORACLE_SDK="${ORACLE_SDK:-$HOME/.claude/skills/oracle/oracle_sdk.py}"
OUT="${ORACLE_OUT:-research/oracle-run.md}"
rm -f oracle_DONE
python "$ORACLE_SDK" --verbose < "$PROMPTS" > "$OUT" 2> oracle_relaunch.log
echo "exit=$?" > oracle_DONE
