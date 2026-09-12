#!/usr/bin/env bash
# Re-score the ORIGINAL 9B 400-step de-risk checkpoint with the prompt it was
# actually trained on, so the 4B de-risk has a same-protocol baseline.
#
# WHY: eval_runs/glyph_cc_400{,_zero} were scored 2026-06-04. `--prompt-style`
# did not exist until 2026-07-28, so those runs used make_prompt()'s structured
# prompt while train_lora_kg.py trains on TRAINED_SHORT_PROMPT -- the mismatch
# documented in research/2026-07-28-reference-char-mismatch.md. Comparing the
# 4B's prompt-matched 0.3050 against the 9B's mismatched 0.4894 is not
# apples-to-apples, and the mismatch depresses the 9B number, so the real gap
# is wider than it looks.
#
# Writes to NEW dirs; the 2026-06 runs stay untouched as the historical record.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f RESCORE_9B_DONE RESCORE_9B_FAIL

MODEL="black-forest-labs/FLUX.2-klein-base-9B"
CKPT="training_glyph_cc_400/final"
NEED_MB=${NEED_MB:-12000}

fail() { echo "=== RESCORE 9B FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ==="; \
         echo "$1 exit=$2" > RESCORE_9B_FAIL; exit 1; }

{
  echo "=== [1/3] waiting for >=${NEED_MB}MB free VRAM @ $(date '+%H:%M:%S') ==="
  free=0
  for i in $(seq 1 480); do
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1)
    free=${free:-0}
    [ "$free" -ge "$NEED_MB" ] && break
    [ $((i % 20)) -eq 0 ] && echo "  waiting: ${free}MB free @ $(date '+%H:%M:%S')"
    sleep 30
  done
  [ "$free" -ge "$NEED_MB" ] || fail vram_gate 1
  echo "=== gate passed: ${free}MB free @ $(date '+%H:%M:%S') ==="

  # prompt_style is DERIVED from the checkpoint (guard infers trained-short from
  # train_config.json lineage) -- same path the 4B eval took. Not hardcoded.
  echo "=== [2/3] 9B WITH template, matched prompt (3 fonts) @ $(date '+%H:%M:%S') ==="
  python eval_checkpoint.py \
    --model "$MODEL" --checkpoint "$CKPT" \
    --holdout eval_holdout --out eval_runs/glyph_cc_400_matched \
    --use-template --in-process --identity --strict-conditioning \
    --count 3 || fail eval_matched $?

  echo "=== [3/3] 9B template ZEROED, matched prompt (3 fonts) @ $(date '+%H:%M:%S') ==="
  python eval_checkpoint.py \
    --model "$MODEL" --checkpoint "$CKPT" \
    --holdout eval_holdout --out eval_runs/glyph_cc_400_matched_zero \
    --use-template --template-zero --in-process --identity --strict-conditioning \
    --count 3 || fail eval_matched_zero $?

  echo "=== RESCORE 9B DONE @ $(date '+%H:%M:%S') ==="
  echo "ok" > RESCORE_9B_DONE
} >> rescore_9b.log 2>&1
