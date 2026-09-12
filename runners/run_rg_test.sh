#!/usr/bin/env bash
# Rg reference test: identical to the banked best-generator eval EXCEPT the
# reference images are rendered with Rg (what training actually used) instead
# of Kg. Prompt text stays "Kg" -- that is what the hardcoded training prompt
# says (train_lora_kg.py:270-273), so leaving it matches training on BOTH axes
# and keeps the reference IMAGE as the single changed variable.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f RG_TEST_DONE RG_TEST_FAIL
fail() { echo "=== RG TEST FAIL (exit $1) @ $(date '+%H:%M:%S') ==="; echo "exit=$1" > RG_TEST_FAIL; exit 1; }

{
  echo "=== waiting for >=20000MB free VRAM @ $(date '+%H:%M:%S') ==="
  for i in $(seq 1 480); do
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1); free=${free:-0}
    [ "$free" -ge 20000 ] && break
    [ $((i % 20)) -eq 0 ] && echo "  waiting: ${free}MB free @ $(date '+%H:%M:%S')"
    sleep 30
  done
  echo "=== gate passed: ${free}MB free @ $(date '+%H:%M:%S') ==="

  echo "=== generating 10 fonts with Rg references @ $(date '+%H:%M:%S') ==="
  python eval_checkpoint.py --model black-forest-labs/FLUX.2-klein-base-9B \
    --checkpoint training_glyph_r32_5000/checkpoint-5000 \
    --identity --use-template --in-process \
    --template-pt dataset_v2/cache/template_disambig_mild.pt \
    --holdout eval_holdout_rg --out eval_runs/rg_ref_test \
    --count 10 --skip-existing || fail $?

  echo "=== RG TEST DONE @ $(date '+%H:%M:%S') ==="
  echo "ok" > RG_TEST_DONE
} >> rg_test.log 2>&1
