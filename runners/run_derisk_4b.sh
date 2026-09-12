#!/usr/bin/env bash
# klein-base-4B de-risk gate: does glyph-latent channel-concat conditioning
# transfer to the Apache-2.0 4B base at all?
#
# Mirrors the ORIGINAL 9B de-risk exactly (training_glyph_cc_400/train_config.json:
# 400 steps, rank 16, lr 1e-4, grad_accum 2, seed 42, dataset_v2, --use-template)
# with ONE variable changed: --model. So the numbers are directly comparable.
#
# GATE: template-zeroing must collapse char_acc. On 9B it went 0.4894 -> 0.1738
# (eval_runs/glyph_cc_400 vs glyph_cc_400_zero, 3 fonts x 94 cells). A comparable
# collapse means the 4B model reads letterforms from the template channel; no
# collapse means the mechanism did not transfer and the port needs rethinking
# before any multi-day run.
#
# The VAE is byte-identical across base-9B / base-4B / 4B (verified by sha256),
# so dataset_v2/cache and the glyph template port unchanged -- no re-encoding.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f DERISK_4B_DONE DERISK_4B_FAIL

MODEL="black-forest-labs/FLUX.2-klein-base-4B"
OUT="training_derisk_4b"
NEED_MB=${NEED_MB:-12000}

fail() { echo "=== DERISK 4B FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ==="; \
         echo "$1 exit=$2" > DERISK_4B_FAIL; exit 1; }

{
  echo "=== [0/4] fetching $MODEL (no GPU) @ $(date '+%H:%M:%S') ==="
  python pipeline/fetch_base_model.py "$MODEL" || fail fetch $?

  # Gate AFTER the download so we don't hold headroom while pulling 15 GB.
  # This box is shared; wait for room rather than evicting someone's work.
  echo "=== [1/4] waiting for >=${NEED_MB}MB free VRAM @ $(date '+%H:%M:%S') ==="
  free=0
  for i in $(seq 1 480); do   # up to 4h
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1)
    free=${free:-0}
    [ "$free" -ge "$NEED_MB" ] && break
    [ $((i % 20)) -eq 0 ] && echo "  waiting: ${free}MB free @ $(date '+%H:%M:%S')"
    sleep 30
  done
  [ "$free" -ge "$NEED_MB" ] || fail vram_gate 1
  echo "=== gate passed: ${free}MB free @ $(date '+%H:%M:%S') ==="

  echo "=== [2/4] training 400 steps on 4B @ $(date '+%H:%M:%S') ==="
  python train_lora_kg.py \
    --model "$MODEL" \
    --dataset-dir dataset_v2 \
    --output-dir "$OUT" \
    --steps 400 --rank 16 --lr 1e-4 --grad-accum 2 --seed 42 \
    --use-template || fail train $?

  echo "=== [3/4] eval WITH template (3 fonts) @ $(date '+%H:%M:%S') ==="
  python eval_checkpoint.py \
    --model "$MODEL" \
    --checkpoint "$OUT/final" \
    --holdout eval_holdout --out eval_runs/derisk_4b \
    --use-template --in-process --identity --strict-conditioning \
    --count 3 || fail eval_template $?

  echo "=== [4/4] eval with template ZEROED (3 fonts) @ $(date '+%H:%M:%S') ==="
  python eval_checkpoint.py \
    --model "$MODEL" \
    --checkpoint "$OUT/final" \
    --holdout eval_holdout --out eval_runs/derisk_4b_zero \
    --use-template --template-zero --in-process --identity --strict-conditioning \
    --count 3 || fail eval_zero $?

  echo "=== DERISK 4B DONE @ $(date '+%H:%M:%S') ==="
  echo "ok" > DERISK_4B_DONE
} >> derisk_4b.log 2>&1
