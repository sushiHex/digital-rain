#!/usr/bin/env bash
# Re-score the EXISTING baseline atlases with --identity so the glyph-vs-baseline
# comparison can include the identity axis. --skip-generate => no generation,
# scoring only (DINOv2 + LPIPS + TrOCR + glyph classifier), ~15 min.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f BASE_ID_DONE BASE_ID_FAIL
{
  for i in $(seq 1 480); do
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1); free=${free:-0}
    [ "$free" -ge 6000 ] && break
    [ $((i % 20)) -eq 0 ] && echo "  waiting: ${free}MB free @ $(date '+%H:%M:%S')"
    sleep 30
  done
  echo "=== rescoring baseline with --identity @ $(date '+%H:%M:%S') (${free}MB free) ==="
  python eval_checkpoint.py --model black-forest-labs/FLUX.2-klein-base-9B --skip-generate --identity \
    --holdout eval_holdout --out eval_runs/structured_prompt_5000 || { echo "exit=$?" > BASE_ID_FAIL; exit 1; }
  echo "=== BASELINE IDENTITY DONE @ $(date '+%H:%M:%S') ==="
  echo ok > BASE_ID_DONE
} >> baseline_identity.log 2>&1
