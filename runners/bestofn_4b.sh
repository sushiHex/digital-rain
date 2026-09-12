#!/usr/bin/env bash
# Does the 4B have the same sampling headroom the 9B has, and can a no-GT
# selector capture enough of it to close the 4B->9B gap?
#
# Framing (research/2026-08-02-...; README results table):
#   9B  char_acc 0.6917   4B char_acc 0.6460   gap 0.0457
#   9B best-of-4 on the holdout: 0.6738 seed0 -> 0.8366 oracle  (+0.1628)
#   9B DINOv2-medoid no-GT selector:           -> 0.6968        (+0.0230)
# So the 4B's entire deficit is ~28% of the 9B's own seed variance, and the
# already-built medoid selector recovered 50% of that gap on the 9B. This
# measures both quantities on the 4B itself.
#
# NOTE: candidate_gen.py used to hardcode load_generation_pipe's defaults
# (prompt_style="structured", reference_chars="Kg", 9B base) while BOTH glyph
# checkpoints are train_lora_kg.py lineage -> "trained-short"/"Rg". It now
# derives them from the checkpoint. The pre-existing dpo_holdout_bestofn/
# candidates were generated mis-conditioned; this run is not.
#
# Pure inference, no training. VRAM-gated (shared box).
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f BESTOFN_4B_DONE BESTOFN_4B_FAIL

OUT="${BESTOFN_OUT:-bestofn_4b}"
CKPT="${BESTOFN_CKPT:-training_glyph_4b_r32_5000/final}"
BASE="${BESTOFN_BASE:-black-forest-labs/FLUX.2-klein-base-4B}"
SEEDS="${BESTOFN_SEEDS:-4}"
GATE_MB="${BESTOFN_GATE_MB:-4000}"
LOG="${BESTOFN_LOG:-bestofn_4b.log}"

fail() { echo "=== BESTOFN 4B FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ==="; echo "$1 exit=$2" > BESTOFN_4B_FAIL; exit 1; }

{
  echo "=== [0/3] waiting for >=${GATE_MB}MB free VRAM @ $(date '+%H:%M:%S') ==="
  for i in $(seq 1 480); do
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1); free=${free:-0}
    [ "$free" -ge "$GATE_MB" ] && break
    [ $((i % 20)) -eq 0 ] && echo "  waiting: ${free}MB free @ $(date '+%H:%M:%S')"
    sleep 30
  done
  echo "=== gate passed: ${free}MB free @ $(date '+%H:%M:%S') ==="

  echo "=== [1/3] candidate_gen: ${SEEDS} glyph seeds, 4B, 50-font HOLDOUT @ $(date '+%H:%M:%S') ==="
  python candidate_gen.py --fonts-manifest eval_holdout/manifest.json --out-dir "$OUT" \
    --models glyph --glyph-seeds "$SEEDS" --steps 20 \
    --glyph-checkpoint "$CKPT" --base-model "$BASE" || fail candidate_gen $?

  echo "=== [2/3] score_candidates against holdout GT @ $(date '+%H:%M:%S') ==="
  python score_candidates.py --candidates-dir "$OUT/candidates" \
    --gt-atlas-dir eval_holdout/atlases --out "$OUT/scores.json" || fail score_candidates $?

  echo "=== [3/3] best-of-N ceiling on the 4B @ $(date '+%H:%M:%S') ==="
  python analysis/analyze_holdout_bestofn.py "$OUT/scores.json" || fail analysis $?

  echo "=== BESTOFN 4B DONE @ $(date '+%H:%M:%S') ==="
  echo "ok" > BESTOFN_4B_DONE
} >> "$LOG" 2>&1
