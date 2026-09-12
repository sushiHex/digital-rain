#!/usr/bin/env bash
# Train the LoRA ON the distilled FLUX.2-klein-4B, rather than transferring a
# base-trained adapter onto it.
#
# WHY: research/2026-07-30-distilled-4step-path.md decomposed the distilled
# path's quality loss. The model swap alone (base@20 -> distilled@20) costs
# 0.089 identity, MORE than the 20->4 step reduction costs. So the adapter, not
# the step count, is the bigger problem -- and the fix for a non-transferring
# adapter is to train it where it will be used.
#
# Single variable against training_glyph_4b_r32_5000: same rank 32, same 5000
# steps, same lr/warmup/batch/accum/seed/wd, same neutral template.pt. Only
# --model changes, base-4B -> distilled-4B.
#
# UNKNOWN: few-step distilled models sometimes need a different training recipe
# than plain flow-matching (LCM-style objectives etc.). If the loss does not
# descend in the first few hundred steps, this recipe is wrong for a distilled
# base and the run should be killed rather than left for 11h. Reference: the
# base-4B run's first 500 steps had median loss 0.0598.
#
# Evaluated at BOTH 4 and 20 steps so the result is comparable to
# eval_runs/distill_4b_s4 and distill_4b_s20 (the transferred adapter).
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f DISTILL_TRAIN_DONE DISTILL_TRAIN_FAIL

MODEL="black-forest-labs/FLUX.2-klein-4B"
OUT=training_glyph_4bdistill_r32_5000
CKPT_EVERY=500
MAX_ATTEMPTS=60
NEED_MB=${NEED_MB:-12000}

fail() { echo "=== DISTILL TRAIN FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ==="; \
         echo "$1 exit=$2" > DISTILL_TRAIN_FAIL; exit 1; }

latest_ckpt() {
  ls -d "$OUT"/checkpoint-*/ 2>/dev/null | sed 's#/$##' \
    | awk -F- '{print $NF, $0}' | sort -n | tail -1 | cut -d' ' -f2-
}

gate() {
  free=0
  for i in $(seq 1 480); do
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1)
    free=${free:-0}
    [ "$free" -ge "$NEED_MB" ] && break
    [ $((i % 20)) -eq 0 ] && echo "  waiting: ${free}MB free @ $(date '+%H:%M:%S')"
    sleep 30
  done
  [ "$free" -ge "$NEED_MB" ] || return 1
  echo "=== gate passed: ${free}MB free @ $(date '+%H:%M:%S') ==="
}

{
  gate || fail vram_gate 1

  for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
    [ -d "$OUT/final" ] && { echo "=== training complete ==="; break; }
    ckpt="$(latest_ckpt)"
    if [ -z "$ckpt" ]; then
      echo "=== [train] attempt $attempt: fresh start @ $(date '+%H:%M:%S') ==="; resume_args=""
    else
      echo "=== [train] attempt $attempt: resuming from $ckpt @ $(date '+%H:%M:%S') ==="
      resume_args="--resume $ckpt"
    fi
    start=$(date +%s)
    # shellcheck disable=SC2086
    python train_lora_kg.py \
      --model "$MODEL" --dataset-dir dataset_v2 --output-dir "$OUT" \
      --steps 5000 --rank 32 --lr 1e-4 --grad-accum 2 --seed 42 \
      --use-template --checkpoint-every "$CKPT_EVERY" $resume_args
    code=$?; dur=$(( $(date +%s) - start ))
    echo "=== [train] exited code=$code after ${dur}s @ $(date '+%H:%M:%S') ==="
    [ -d "$OUT/final" ] && { echo "=== training complete ==="; break; }
    [ "$dur" -lt 60 ] && fail train_startup_crash "$code"
    echo "=== [train] incomplete (at ~$(latest_ckpt)); retrying in 20s ==="
    sleep 20
    gate || fail vram_gate_retry 1
  done
  [ -d "$OUT/final" ] || fail train_exhausted_attempts 4

  for steps in 4 20; do
    echo "=== [eval] 50 fonts @ ${steps} steps @ $(date '+%H:%M:%S') ==="
    gate || fail "vram_gate_eval_$steps" 1
    python eval_checkpoint.py \
      --model "$MODEL" --checkpoint "$OUT/final" \
      --holdout eval_holdout --out "eval_runs/distill_trained_s${steps}" \
      --use-template --template-pt dataset_v2/cache/template_disambig_mild.pt \
      --in-process --identity --strict-conditioning --skip-existing \
      --steps "$steps" || fail "eval_s${steps}" $?
  done

  echo "=== DISTILL TRAIN DONE @ $(date '+%H:%M:%S') ==="
  echo "ok" > DISTILL_TRAIN_DONE
} >> distill_train.log 2>&1
