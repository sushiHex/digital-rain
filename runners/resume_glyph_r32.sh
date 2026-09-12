#!/usr/bin/env bash
# Auto-restart wrapper for the glyph-cond rank-32 run on a contended GPU.
# Resumes from the latest checkpoint until `final/` exists. Each interruption
# costs at most --checkpoint-every steps of progress. Guards against a fast
# crash-loop: if a launch dies in under 60s it is a startup failure, not a
# VRAM eviction — stop and let a human look.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
OUT=training_glyph_r32_5000
CKPT_EVERY=100
MAX_ATTEMPTS=60

latest_ckpt() {
  ls -d "$OUT"/checkpoint-*/ 2>/dev/null \
    | sed 's#/$##' \
    | awk -F- '{print $NF, $0}' | sort -n | tail -1 | cut -d' ' -f2-
}

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  if [ -d "$OUT/final" ]; then
    echo "WRAPPER: $OUT/final exists — run complete."; exit 0
  fi
  ckpt="$(latest_ckpt)"
  if [ -z "$ckpt" ]; then
    echo "WRAPPER: no checkpoint found under $OUT — aborting."; exit 2
  fi
  echo "WRAPPER: attempt $attempt/$MAX_ATTEMPTS — resuming from $ckpt"
  start=$(date +%s)
  python train_lora_kg.py --model black-forest-labs/FLUX.2-klein-base-9B --dataset-dir dataset_v2 --output-dir "$OUT" \
      --steps 5000 --rank 32 --lr 1e-4 --checkpoint-every "$CKPT_EVERY" \
      --resume "$ckpt"
  code=$?
  dur=$(( $(date +%s) - start ))
  echo "WRAPPER: training exited code=$code after ${dur}s"
  if [ -d "$OUT/final" ]; then
    echo "WRAPPER: $OUT/final exists — run complete."; exit 0
  fi
  if [ "$dur" -lt 60 ]; then
    echo "WRAPPER: launch died in ${dur}s (<60s) — startup failure, not a VRAM eviction. STOPPING for human review."
    exit 3
  fi
  echo "WRAPPER: incomplete (killed at ~$(latest_ckpt)); retrying in 20s..."
  sleep 20
done
echo "WRAPPER: exhausted $MAX_ATTEMPTS attempts without reaching final — STOPPING."
exit 4
