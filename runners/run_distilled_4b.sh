#!/usr/bin/env bash
# Lever 1: the distilled 4-step inference path.
#
# Applies the LoRA trained on klein-base-4B to the distilled FLUX.2-klein-4B --
# the standard workflow (train on base, apply on distilled), architecturally
# sound here: in_channels 128, inner 3072, 5/20 layers, joint 7680 on both, and
# identical scheduler configs.
#
# Two arms so "distilled" and "4 steps" are not confounded:
#   A: distilled @ 4 steps   -- the product configuration
#   B: distilled @ 20 steps  -- isolates the distillation effect alone
# The base-4B @20 arm already exists as eval_runs/glyph_4b_r32_5000.
#
# 3 fonts first: if the distilled path is broken this shows it in minutes
# rather than after a 50-font run.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f DISTILL_4B_DONE DISTILL_4B_FAIL

DISTILLED="black-forest-labs/FLUX.2-klein-4B"
CKPT=training_glyph_4b_r32_5000/final
NEED_MB=${NEED_MB:-12000}

fail() { echo "=== DISTILL 4B FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ==="; \
         echo "$1 exit=$2" > DISTILL_4B_FAIL; exit 1; }

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

  echo "=== [1/2] distilled @ 4 steps, 3 fonts @ $(date '+%H:%M:%S') ==="
  python eval_checkpoint.py \
    --model "$DISTILLED" --checkpoint "$CKPT" \
    --holdout eval_holdout --out eval_runs/distill_4b_s4 \
    --use-template --template-pt dataset_v2/cache/template_disambig_mild.pt \
    --in-process --identity --strict-conditioning \
    --steps 4 --count 3 || fail eval_s4 $?

  echo "=== [2/2] distilled @ 20 steps, 3 fonts @ $(date '+%H:%M:%S') ==="
  python eval_checkpoint.py \
    --model "$DISTILLED" --checkpoint "$CKPT" \
    --holdout eval_holdout --out eval_runs/distill_4b_s20 \
    --use-template --template-pt dataset_v2/cache/template_disambig_mild.pt \
    --in-process --identity --strict-conditioning \
    --steps 20 --count 3 || fail eval_s20 $?

  echo "=== DISTILL 4B DONE @ $(date '+%H:%M:%S') ==="
  echo "ok" > DISTILL_4B_DONE
} >> distill_4b.log 2>&1
