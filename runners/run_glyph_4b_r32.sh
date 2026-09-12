#!/usr/bin/env bash
# Full klein-base-4B glyph-conditioned run: rank 32, 5000 steps, then a 50-font
# scored eval. The Apache-2.0 counterpart to training_glyph_r32_5000.
#
# Hyperparameters copied from training_glyph_r32_5000/train_config.json so the
# result is comparable to the shipped 9B model: rank 32, 5000 steps, lr 1e-4,
# warmup 100, batch 1, grad_accum 2, seed 42, wd 1e-5, grad-checkpointing on.
# Only --model differs.
#
# Conditioning mirrors the shipped protocol exactly: training always uses the
# neutral dataset_v2/cache/template.pt (hardcoded in train_lora_kg.py), and the
# eval swaps in template_disambig_mild.pt -- the deliberate zero-shot win the
# 9B model banked. prompt_style is derived from the checkpoint by the guard.
#
# CONTEXT: the 400-step de-risk gate PASSED (template-zeroing collapses
# char_acc 0.3050 -> 0.0284 and identity 0.5609 -> 0.0406), so the mechanism
# transfers. But at that matched checkpoint the 4B trails the 9B badly
# (identity 0.5609 vs 0.9004). This run tests whether the gap closes by 5000
# steps; identity saturates on the 9B (0.9004@400 -> 0.9936@5000), which is why
# 400 steps is weak evidence either way. Expect ~12h.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
# Marker prefix is overridable so parallel/sequential variants do not
# overwrite each other's terminal state.
MARKER=${MARKER:-GLYPH_4B}
rm -f "${MARKER}_DONE" "${MARKER}_FAIL"

# RANK/OUT/EVAL_OUT are overridable so the same runner serves the rank sweep.
# Defaults reproduce the original rank-32 run exactly.
MODEL="black-forest-labs/FLUX.2-klein-base-4B"
RANK=${RANK:-32}
OUT=${OUT:-training_glyph_4b_r32_5000}
EVAL_OUT=${EVAL_OUT:-eval_runs/glyph_4b_r32_5000}
LOG=${LOG:-glyph_4b.log}
# DATASET is overridable so the same runner serves the corpus-expansion run.
# train_lora_kg.py derives its cache and template.pt from this, so a v3
# dataset must carry cache/template.pt (build_expansion.py links it through).
DATASET=${DATASET:-dataset_v2}
# STEPS scales with corpus size to hold the PER-FONT gradient budget fixed.
# dataset_v2 is 5000/925 = 5.41 steps/font; a 1,113-font corpus needs 6016 to
# match. Holding STEPS constant while the corpus grew 20% cut the budget 17%
# and significantly regressed char_acc and dinov2 -- the same mechanism that
# sank V4 (quality-roadmap-v2 finding 1).
STEPS=${STEPS:-5000}
# Extra train_lora_kg.py flags, e.g. distinctiveness-weighted sampling.
# Empty by default, so a bare invocation is unchanged.
EXTRA_TRAIN_ARGS=${EXTRA_TRAIN_ARGS:-}
# SEED was hardcoded to 42 until 2026-08-12, which would have made a
# training-run VARIANCE experiment silently measure nothing: two runs launched
# with "different seeds" would have been the same run twice.
SEED=${SEED:-42}
# Desktop headroom. train_lora_kg.py reads GPU_DUTY_CYCLE from the environment;
# exporting it here means it survives into the python child. 1.0 = unthrottled.
# 0.9 leaves ~10% of wall-clock idle for the Windows compositor, costing ~11%
# longer training -- worth it when you need to use the machine while it runs.
export GPU_DUTY_CYCLE=${GPU_DUTY_CYCLE:-1.0}
CKPT_EVERY=500
MAX_ATTEMPTS=60
NEED_MB=${NEED_MB:-12000}

fail() { echo "=== GLYPH 4B FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ==="; \
         echo "$1 exit=$2" > "${MARKER}_FAIL"; exit 1; }

latest_ckpt() {
  ls -d "$OUT"/checkpoint-*/ 2>/dev/null \
    | sed 's#/$##' \
    | awk -F- '{print $NF, $0}' | sort -n | tail -1 | cut -d' ' -f2-
}

gate() {
  echo "=== waiting for >=${NEED_MB}MB free VRAM @ $(date '+%H:%M:%S') ==="
  free=0
  for i in $(seq 1 480); do   # up to 4h
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

  # ---- training, with resume-on-eviction (each loss costs <=CKPT_EVERY steps)
  for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
    [ -d "$OUT/final" ] && { echo "=== training complete ($OUT/final) ==="; break; }

    ckpt="$(latest_ckpt)"
    if [ -z "$ckpt" ]; then
      echo "=== [train] attempt $attempt: fresh start @ $(date '+%H:%M:%S') ==="
      resume_args=""
    else
      echo "=== [train] attempt $attempt: resuming from $ckpt @ $(date '+%H:%M:%S') ==="
      resume_args="--resume $ckpt"
    fi

    start=$(date +%s)
    # shellcheck disable=SC2086
    python train_lora_kg.py \
      --model "$MODEL" \
      --dataset-dir "$DATASET" --output-dir "$OUT" \
      --steps "$STEPS" --rank "$RANK" --lr 1e-4 --grad-accum 2 --seed "$SEED" \
      --use-template --checkpoint-every "$CKPT_EVERY" $EXTRA_TRAIN_ARGS $resume_args
    code=$?
    dur=$(( $(date +%s) - start ))
    echo "=== [train] exited code=$code after ${dur}s @ $(date '+%H:%M:%S') ==="

    [ -d "$OUT/final" ] && { echo "=== training complete ($OUT/final) ==="; break; }

    # A launch that dies in under 60s is a startup failure, not a VRAM
    # eviction. Retrying would crash-loop; stop for a human.
    if [ "$dur" -lt 60 ]; then
      fail train_startup_crash "$code"
    fi
    echo "=== [train] incomplete (at ~$(latest_ckpt)); retrying in 20s ==="
    sleep 20
    gate || fail vram_gate_retry 1
  done

  [ -d "$OUT/final" ] || fail train_exhausted_attempts 4

  # ---- 50-font scored eval, shipped protocol (disambig template, identity)
  echo "=== [eval] 50 fonts, disambig-mild template @ $(date '+%H:%M:%S') ==="
  gate || fail vram_gate_eval 1
  python eval_checkpoint.py \
    --model "$MODEL" --checkpoint "$OUT/final" \
    --holdout eval_holdout --out "$EVAL_OUT" \
    --use-template --template-pt dataset_v2/cache/template_disambig_mild.pt \
    --in-process --identity --strict-conditioning --skip-existing \
    || fail eval $?

  echo "=== GLYPH 4B DONE @ $(date '+%H:%M:%S') ==="
  echo "ok" > "${MARKER}_DONE"
} >> "$LOG" 2>&1
