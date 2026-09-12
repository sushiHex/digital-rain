#!/usr/bin/env bash
# Prompt-mismatch test: generate the glyph model with the prompt it was ACTUALLY
# trained on (train_lora_kg.py's 208-char string) instead of make_prompt()'s
# 534-char structured prompt that eval has always used.
# Same holdout (eval_holdout), same checkpoint, same template -> the PROMPT is
# the only variable. See research/2026-07-28-reference-char-mismatch.md.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f PROMPT_TEST_DONE PROMPT_TEST_FAIL
fail() { echo "=== PROMPT TEST FAIL (exit $1) @ $(date '+%H:%M:%S') ==="; echo "exit=$1" > PROMPT_TEST_FAIL; exit 1; }
{
  echo "=== waiting for >=12000MB free VRAM @ $(date '+%H:%M:%S') ==="
  for i in $(seq 1 480); do
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1); free=${free:-0}
    [ "$free" -ge 12000 ] && break
    [ $((i % 20)) -eq 0 ] && echo "  waiting: ${free}MB free @ $(date '+%H:%M:%S')"
    sleep 30
  done
  echo "=== gate passed: ${free}MB free @ $(date '+%H:%M:%S') ==="
  python eval_checkpoint.py \
    --checkpoint training_glyph_r32_5000/checkpoint-5000 \
    --identity --use-template --in-process \
    --template-pt dataset_v2/cache/template_disambig_mild.pt \
    --holdout eval_holdout --out eval_runs/prompt_trained_short \
    --prompt-style trained-short --skip-existing || fail $?
  echo "=== PROMPT TEST DONE @ $(date '+%H:%M:%S') ==="
  echo "ok" > PROMPT_TEST_DONE
} >> prompt_test.log 2>&1
