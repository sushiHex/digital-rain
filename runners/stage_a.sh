#!/usr/bin/env bash
# Stage A: SFT self-distillation on cross-model WINNER atlases (the cheap
# kill-gate: does the GT-guided signal transfer to the 50-font holdout?).
#
# Resume is WEIGHTS-ONLY (training_glyph_r32_5000/adapter_only has no
# training_state.pt) so global_step starts at 0 and the LR schedule restarts —
# resuming checkpoint-5000 directly would restore the cosine-decayed LR (~0)
# and guarantee a false-negative.
#
# VRAM-gated: this box is shared with other agents' Ollama models.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f STAGE_A_DONE STAGE_A_FAIL
fail() { echo "=== STAGE A FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ==="; echo "$1 exit=$2" > STAGE_A_FAIL; exit 1; }
gate() { # gate <need_mb> <label>
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
  echo "=== [1/3] build_sft_cache (VAE-encode 80 winner atlases) @ $(date '+%H:%M:%S') ==="
  python build_sft_cache.py --sft-targets dpo_pilot/sft_targets.json \
    --candidate-dir dpo_pilot/candidates --out-cache dpo_pilot/sft_cache || fail build_sft_cache $?

  gate 18000 train
  echo "=== [2/3] Stage A train (400 steps, lr 5e-5, weights-only resume) @ $(date '+%H:%M:%S') ==="
  python train_lora_kg.py --model black-forest-labs/FLUX.2-klein-base-9B --dataset-dir dpo_pilot --cache-dir dpo_pilot/sft_cache \
    --output-dir training_stageA_pilot --resume training_glyph_r32_5000/adapter_only \
    --rank 32 --steps 400 --lr 5e-5 --warmup-steps 50 --checkpoint-every 100 --use-template || fail train $?

  gate 20000 eval
  echo "=== [3/3] eval on 50-font holdout (dual scorecard) @ $(date '+%H:%M:%S') ==="
  python eval_checkpoint.py --model black-forest-labs/FLUX.2-klein-base-9B --checkpoint training_stageA_pilot/final --identity --use-template --in-process \
    --template-pt dataset_v2/cache/template_disambig_mild.pt \
    --holdout eval_holdout --out eval_runs/stageA_pilot --skip-existing || fail eval $?

  echo "=== STAGE A DONE @ $(date '+%H:%M:%S') ==="
  echo "ok" > STAGE_A_DONE
} >> stage_a.log 2>&1
