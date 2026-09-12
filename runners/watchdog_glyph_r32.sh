#!/usr/bin/env bash
# Detached watchdog for the glyph-cond rank-32 run.
#
# WHY DETACHED: harness-tracked background tasks on this box are being killed
# (bash task terminated, python grandchild orphaned/survived). Launched via
# PowerShell Start-Process, this watchdog is NOT a tracked task, so it should
# outlive that. It coexists safely with an already-running training process:
# it only (re)launches training when NONE is running and final/ is absent, so
# it never double-launches onto the GPU.
#
# Logs to watchdog_glyph_r32.log. To stop: kill this bash + any train_lora_kg
# python (see `tasklist | grep python`), or `touch training_glyph_r32_5000/STOP`.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
OUT=training_glyph_r32_5000
CKPT_EVERY=100
MAX_LAUNCHES=40
launches=0

log() { echo "$(date '+%H:%M:%S') WATCHDOG: $*"; }

training_running() {
  wmic process where "name='python.exe'" get commandline 2>/dev/null \
    | grep -q "train_lora_kg.py.*$OUT"
}

latest_ckpt() {
  ls -d "$OUT"/checkpoint-*/ 2>/dev/null | sed 's#/$##' \
    | awk -F- '{print $NF, $0}' | sort -n | tail -1 | cut -d' ' -f2-
}

log "watchdog started (pid $$)"
while true; do
  if [ -f "$OUT/STOP" ]; then log "STOP file present — exiting."; exit 0; fi
  if [ -d "$OUT/final" ]; then log "$OUT/final exists — run complete."; exit 0; fi

  if training_running; then
    sleep 60
    continue
  fi

  # No training process and not complete → (re)launch from the latest checkpoint.
  if [ "$launches" -ge "$MAX_LAUNCHES" ]; then
    log "hit MAX_LAUNCHES=$MAX_LAUNCHES without final — exiting for human review."
    exit 4
  fi
  ckpt="$(latest_ckpt)"
  if [ -z "$ckpt" ]; then log "no checkpoint under $OUT — aborting."; exit 2; fi
  launches=$((launches + 1))
  log "launch #$launches — resuming from $ckpt"
  start=$(date +%s)
  python train_lora_kg.py --dataset-dir dataset_v2 --output-dir "$OUT" \
      --steps 5000 --rank 32 --lr 1e-4 --checkpoint-every "$CKPT_EVERY" \
      --resume "$ckpt" >> watchdog_train_stdio.log 2>&1
  dur=$(( $(date +%s) - start ))
  log "training exited code=$? after ${dur}s"
  if [ -d "$OUT/final" ]; then log "final reached — complete."; exit 0; fi
  if [ "$dur" -lt 60 ]; then
    log "launch died in ${dur}s (<60s) — startup failure, not eviction. STOPPING."
    exit 3
  fi
  sleep 20
done
