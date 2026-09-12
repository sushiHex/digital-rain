#!/usr/bin/env bash
# Stage A v2: SFT on the WIDENED candidate pool (5 renders/cell: 1 baseline +
# 4 glyph seeds, vs the original 3). Same gentle settings as the "lite" run
# (150 steps, lr 2e-5) for a clean single-variable comparison — isolates
# candidate-pool-size as the only change from the lite result.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f STAGE_A_V2_DONE STAGE_A_V2_FAIL
fail() { echo "=== STAGE A V2 FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ==="; echo "$1 exit=$2" > STAGE_A_V2_FAIL; exit 1; }
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
  gate 6000 build
  echo "=== [1/2] build_sft_cache on the WIDENED sft_targets.json @ $(date '+%H:%M:%S') ==="
  python build_sft_cache.py --sft-targets dpo_pilot/sft_targets.json \
    --candidate-dir dpo_pilot/candidates --out-cache dpo_pilot/sft_cache_v2 || fail build_sft_cache $?

  gate 18000 train
  echo "=== [2/2] Stage A v2 train (150 steps, lr 2e-5, weights-only resume) @ $(date '+%H:%M:%S') ==="
  python train_lora_kg.py --model black-forest-labs/FLUX.2-klein-base-9B --dataset-dir dpo_pilot --cache-dir dpo_pilot/sft_cache_v2 \
    --output-dir training_stageA_v2 --resume training_glyph_r32_5000/adapter_only \
    --rank 32 --steps 150 --lr 2e-5 --warmup-steps 20 --checkpoint-every 50 --use-template || fail train $?

  echo "=== STAGE A V2 TRAIN DONE @ $(date '+%H:%M:%S') ==="
  echo "ok" > STAGE_A_V2_DONE
} >> stage_a_v2.log 2>&1
