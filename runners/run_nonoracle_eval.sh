#!/usr/bin/env bash
# Measure the ORACLE-REFERENCE GAP: how much quality survives a realistic input.
#
# Every number this project has published uses a reference rendered from the
# target font's own TTF by the same pipeline that made the ground truth --
# pixel-exact, noiseless, perfectly framed. Users upload screenshots and photos.
# docs/quality-roadmap-v3.md said in May that quality "WILL drop sharply" on
# non-oracle references; it has never been measured, and it is the largest gap
# between these results and a usable product.
#
# Three tiers give a dose-response curve rather than one arbitrary point.
# Ground truth is IDENTICAL across all of them (analysis/build_degraded_holdout.py
# copies the atlases untouched), so only the model's INPUT varies.
#
# Baseline for comparison: the same checkpoint on the undegraded holdout,
# already measured at char_acc 0.6183 (eval_runs/glyph_4b_r32_5000_lrfix).
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root

MARKER=${MARKER:-NONORACLE}
rm -f "${MARKER}_DONE" "${MARKER}_FAIL"

MODEL=${MODEL:-black-forest-labs/FLUX.2-klein-base-4B}
CKPT=${CKPT:-training_glyph_4b_r32_5000_lrfix/final}
NEED_MB=${NEED_MB:-12000}
TIERS=${TIERS:-"screenshot upload photo"}

# Leave the desktop usable; this is a foreground-hours job.
export GPU_DUTY_CYCLE=${GPU_DUTY_CYCLE:-0.9}

fail() { echo "=== NONORACLE FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ==="; \
         echo "$2" > "${MARKER}_FAIL"; exit "$2"; }

echo "=== waiting for >=${NEED_MB}MB free VRAM @ $(date '+%H:%M:%S') ==="
while true; do
  free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)
  [ "$free" -ge "$NEED_MB" ] && break
  sleep 60
done
echo "=== gate passed: ${free}MB free @ $(date '+%H:%M:%S') ==="

for tier in $TIERS; do
  echo "=== [$tier] eval @ $(date '+%H:%M:%S') ==="
  python eval_checkpoint.py \
    --model "$MODEL" --checkpoint "$CKPT" \
    --holdout "eval_holdout_${tier}" --out "eval_runs/nonoracle_${tier}" \
    --use-template --template-pt dataset_v2/cache/template_disambig_mild.pt \
    --in-process --identity --strict-conditioning --skip-existing \
    || fail "eval_$tier" $?
done

echo "=== NONORACLE DONE @ $(date '+%H:%M:%S') ==="
echo "ok" > "${MARKER}_DONE"
