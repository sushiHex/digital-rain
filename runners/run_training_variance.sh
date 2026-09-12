#!/usr/bin/env bash
# Measure TRAINING-RUN VARIANCE -- the highest-value unspent measurement here.
#
# Every variance figure in this repo measures INFERENCE seeds: one checkpoint
# sampled several times. The spread between two TRAINING runs of one config has
# never been measured, so NO checkpoint-vs-checkpoint comparison in this project
# has a known error bar -- not the levers, not 4B vs 9B, not the LR fix, not the
# -0.133 licence-filter cost.
#
# DESIGN. Two runs is NOT enough: two runs give one difference, and an SD from
# n=2 has a 95% CI of roughly [0.45*sigma, 31*sigma]. So this reuses the clean
# run already on disk (seed 42) as arm 1 and adds seeds 43 and 44, giving n=3 on
# an identical config -- a real variance estimate, and simultaneously a 3-run
# mean for the licence-filter comparison that currently rests on one run.
#
# CONFIG MUST MATCH training_glyph_4b_r32_clean EXACTLY or these are not
# replicates: 4530 steps, rank 32, dataset_v2 + the licence filter (838 fonts).
# 4530 rather than 5000 is deliberate -- it matches the existing arm. The step
# mismatch against lrfix is already handled by the checkpoint-4500 comparison.
#
# `--seed` was hardcoded to 42 in run_glyph_4b_r32.sh until 2026-08-12. Two runs
# launched with "different seeds" would have been the same run twice, and the
# experiment would have measured zero and looked like a finding.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root

MARKER=${MARKER:-TRAINVAR}
rm -f "${MARKER}_DONE" "${MARKER}_FAIL"

SEEDS=${SEEDS:-"43 44"}
STEPS=${STEPS:-4530}
RANK=${RANK:-32}
DATASET=${DATASET:-dataset_v2}
export GPU_DUTY_CYCLE=${GPU_DUTY_CYCLE:-0.9}

echo "=== TRAINING VARIANCE: seeds [$SEEDS] @ $(date '+%H:%M:%S') ==="
echo "=== arm 1 already on disk: training_glyph_4b_r32_clean (seed 42) ==="

for s in $SEEDS; do
  out="training_glyph_4b_r32_clean_s${s}"
  echo "=== seed $s -> $out @ $(date '+%H:%M:%S') ==="
  SEED="$s" \
  OUT="$out" \
  EVAL_OUT="eval_runs/glyph_4b_r32_clean_s${s}" \
  LOG="glyph_4b_clean_s${s}.log" \
  MARKER="GLYPH_4B_CLEAN_S${s}" \
  DATASET="$DATASET" STEPS="$STEPS" RANK="$RANK" \
  ./runners/run_glyph_4b_r32.sh || { echo "seed_${s}_failed" > "${MARKER}_FAIL"; exit 1; }

  # Verify the seed actually landed. A silent fallback to 42 would make this
  # experiment measure nothing while looking like it worked.
  got=$(python -c "import json;print(json.load(open('${out}/train_config.json'))['seed'])" 2>/dev/null)
  if [ "$got" != "$s" ]; then
    echo "=== SEED DID NOT PROPAGATE: wanted $s, config says '$got' ==="
    echo "seed_not_propagated" > "${MARKER}_FAIL"; exit 1
  fi
  echo "=== seed $s confirmed in $out/train_config.json @ $(date '+%H:%M:%S') ==="
done

echo "=== TRAINING VARIANCE DONE @ $(date '+%H:%M:%S') ==="
echo "ok" > "${MARKER}_DONE"
