#!/usr/bin/env bash
# Detached, auto-gated, restartable runner for Task 3: 50-font eval of checkpoint-5000.
#
# GATE: waits until training has fully EXITED (checkpoint-5000 exists AND no
# train_lora_kg python running) so the eval never contends with training on the GPU.
# RESILIENCE: --skip-existing makes each relaunch resume; completes when scores.json
# exists. Detached via PowerShell Start-Process so it survives harness task-kills
# (same rationale as watchdog_glyph_r32.sh). Log: run_eval_glyph_r32.log
# To abort: touch eval_runs/glyph_r32_5000/STOP (or kill this bash + eval python).
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
OUT=eval_runs/glyph_r32_5000
CKPT=training_glyph_r32_5000/checkpoint-5000
MAX_LAUNCHES=20
launches=0

log() { echo "$(date '+%H:%M:%S') EVAL-RUNNER: $*"; }
training_running() { wmic process where "name='python.exe'" get commandline 2>/dev/null | grep -q "train_lora_kg.py.*training_glyph_r32_5000"; }
eval_running()     { wmic process where "name='python.exe'" get commandline 2>/dev/null | grep -q "eval_checkpoint.py.*glyph_r32_5000"; }

log "eval-runner started (pid $$)"

# Gate: training must be finished (checkpoint-5000 saved) AND its python gone.
gated=0
for w in $(seq 1 360); do   # up to ~3h
  [ -f "$OUT/STOP" ] && { log "STOP before start — exiting."; exit 0; }
  if [ -d "$CKPT" ] && ! training_running; then gated=1; break; fi
  sleep 30
done
[ "$gated" -eq 1 ] || { log "gate not satisfied (no checkpoint-5000 / training still running) after ~3h — aborting."; exit 2; }
log "gate open: $CKPT present, training exited. Starting eval."

while true; do
  [ -f "$OUT/STOP" ] && { log "STOP file present — exiting."; exit 0; }
  if [ -f "$OUT/scores.json" ]; then log "$OUT/scores.json exists — eval COMPLETE."; exit 0; fi
  if eval_running; then sleep 60; continue; fi
  if [ "$launches" -ge "$MAX_LAUNCHES" ]; then log "hit MAX_LAUNCHES=$MAX_LAUNCHES — stopping for review."; exit 4; fi
  launches=$((launches + 1))
  log "eval launch #$launches"
  start=$(date +%s)
  # --in-process is REQUIRED for template checkpoints: the subprocess path shells
  # out to render_checkpoint.py which has NO --use-template support (x_embedder stays
  # 128ch -> shape-mismatch crash, hidden by stderr=DEVNULL). In-process expands
  # x_embedder 128->256, loads the adapter, and installs the glyph channel-concat hook.
  python eval_checkpoint.py --checkpoint "$CKPT" \
      --use-template --template-pt dataset_v2/cache/template.pt --in-process \
      --holdout eval_holdout --out "$OUT" --skip-existing >> eval_glyph_r32_stdio.log 2>&1
  dur=$(( $(date +%s) - start ))
  log "eval exited code=$? after ${dur}s"
  if [ -f "$OUT/scores.json" ]; then log "scores.json present — COMPLETE."; exit 0; fi
  if [ "$dur" -lt 30 ]; then log "eval died in ${dur}s (<30s) — startup failure, not GPU eviction. STOPPING for review."; exit 3; fi
  sleep 20
done
