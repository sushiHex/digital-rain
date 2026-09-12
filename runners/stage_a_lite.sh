#!/usr/bin/env bash
# Cheap re-test of Stage A: SAME cached winner-atlas data (dpo_pilot/sft_cache,
# already built), SAME weights-only resume (fresh LR schedule), but dialed
# back — fewer steps + lower LR — to test whether the -0.044 char_acc
# regression from the 400-step/5e-5 run was overfitting to the narrow/biased
# 80-font pilot (leading hypothesis: best-improved fonts there were exactly
# the pilot's over-sampled distinctive set) rather than a flaw in the
# cross-model preference-distillation idea itself. No new candidate
# generation — this only costs a short train + eval.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f STAGE_A_LITE_DONE STAGE_A_LITE_FAIL
fail() { echo "=== STAGE A LITE FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ==="; echo "$1 exit=$2" > STAGE_A_LITE_FAIL; exit 1; }
gate() {
  local need=$1 label=$2 free=0
  echo "=== gate($label): waiting for >=${need}MB free VRAM @ $(date '+%H:%M:%S') ==="
  for i in $(seq 1 480); do
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1); free=${free:-0}
    [ "$free" -ge "$need" ] && break
    [ $((i % 20)) -eq 0 ] && echo "  waiting: ${free}MB free @ $(date '+%H:%M:%S')"
    sleep 30
  done
  echo "=== gate($label) passed: ${free}MB free @ $(date '+%H:%M:%S') ==="
}

{
  gate 18000 train
  echo "=== Stage A LITE train (150 steps, lr 2e-5, weights-only resume) @ $(date '+%H:%M:%S') ==="
  python train_lora_kg.py --model black-forest-labs/FLUX.2-klein-base-9B --dataset-dir dpo_pilot --cache-dir dpo_pilot/sft_cache \
    --output-dir training_stageA_lite --resume training_glyph_r32_5000/adapter_only \
    --rank 32 --steps 150 --lr 2e-5 --warmup-steps 20 --checkpoint-every 50 --use-template || fail train $?
  echo "=== STAGE A LITE TRAIN DONE @ $(date '+%H:%M:%S') ==="
  echo "ok" > STAGE_A_LITE_DONE
} >> stage_a_lite.log 2>&1
