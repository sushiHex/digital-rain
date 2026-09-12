#!/usr/bin/env bash
# Re-score the six-seed 4B and 9B candidate sets with eval_checkpoint -- no
# generation -- so R-ACC, IDENTITY and the README composite get the same
# six-seed treatment char_acc, DINOv2 and LPIPS already have (issue #12).
#
# INPUT   bestofn_{4b,9b}/candidates/<font>/glyph__seed<k>.png, the atlases
#         run_multiseed_4b_vs_9b.sh generated (six seeds x 50 fonts x two arms).
# OUTPUT  eval_runs/multiseed_<arm>_s<k>/{generated,per_cell.json,scores.json}
#         per seed, then research/multiseed_rescore.json from
#         analysis/multiseed_rescore.py, which applies multiseed_compare's
#         registered statistic to the new metrics.
#
# Scoring only needs the small models (TrOCR, DINOv2, LPIPS, the glyph
# classifier), so the gate is lower than a training runner's; it still
# waits rather than evicts.
# pipefail, because the analysis below is piped through tee: without it the
# pipeline's status is tee's, a failed analysis reads as success, and the
# DONE marker lies (review finding, 2026-09-12).
set -u -o pipefail
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root

MARKER=${MARKER:-RESCORE_MULTISEED}
rm -f "${MARKER}_DONE" "${MARKER}_FAIL"
LOG=${LOG:-rescore_multiseed.log}
SEEDS=${SEEDS:-"0 1 2 3 4 5"}
GATE_MB=${GATE_MB:-6000}
CKPT_4B=${CKPT_4B:-training_glyph_4b_r32_5000/final}
CKPT_9B=${CKPT_9B:-training_glyph_r32_5000/final}
BASE_4B=${BASE_4B:-black-forest-labs/FLUX.2-klein-base-4B}
BASE_9B=${BASE_9B:-black-forest-labs/FLUX.2-klein-base-9B}

fail() { echo "=== RESCORE FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ===" | tee -a "$LOG"; \
         echo "$1 exit=$2" > "${MARKER}_FAIL"; exit 1; }
gate() {
  echo "=== waiting for >=${GATE_MB}MB free VRAM @ $(date '+%H:%M:%S') ===" | tee -a "$LOG"
  free=0
  for i in $(seq 1 960); do
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1)
    free=${free:-0}
    [ "$free" -ge "$GATE_MB" ] && break
    [ $((i % 20)) -eq 0 ] && echo "  waiting: ${free}MB free @ $(date '+%H:%M:%S')" | tee -a "$LOG"
    sleep 30
  done
  [ "$free" -ge "$GATE_MB" ] || return 1
  echo "=== gate passed: ${free}MB free @ $(date '+%H:%M:%S') ===" | tee -a "$LOG"
}

# stage <arm> <seed>: lay one seed's atlases out the way eval_checkpoint reads
# a run (generated/<font>.png), copied so the candidate set stays untouched.
stage() {
  local src="bestofn_$1/candidates" dst="eval_runs/multiseed_$1_s$2/generated" n=0
  mkdir -p "$dst"
  for d in "$src"/*/; do
    local font; font=$(basename "$d")
    [ -f "$d/glyph__seed$2.png" ] || fail "stage_$1_s$2_missing_$font" 1
    cp -p "$d/glyph__seed$2.png" "$dst/$font.png" && n=$((n + 1))
  done
  [ "$n" -eq 50 ] || fail "stage_$1_s$2_count_$n" 1
}

score() {   # score <arm> <seed> <checkpoint> <base model>
  local out="eval_runs/multiseed_$1_s$2"
  if [ -f "$out/per_cell.json" ] && [ -f "$out/scores.json" ]; then
    echo "=== [$1 s$2] already scored ===" | tee -a "$LOG"; return 0
  fi
  echo "=== [$1 s$2] staging + scoring @ $(date '+%H:%M:%S') ===" | tee -a "$LOG"
  stage "$1" "$2"
  gate || fail "vram_gate_$1_s$2" 1
  python eval_checkpoint.py --checkpoint "$3" --model "$4" --holdout eval_holdout \
    --out "$out" --skip-generate --identity >> "$LOG" 2>&1 || fail "eval_$1_s$2" $?
}

echo "=== RESCORE MULTISEED: seeds [$SEEDS] @ $(date '+%H:%M:%S') ===" | tee -a "$LOG"
for s in $SEEDS; do
  score 4b "$s" "$CKPT_4B" "$BASE_4B"
  score 9b "$s" "$CKPT_9B" "$BASE_9B"
done

echo "=== analysis @ $(date '+%H:%M:%S') ===" | tee -a "$LOG"
# shellcheck disable=SC2086  # SEEDS is a space-separated list on purpose
python analysis/multiseed_rescore.py --seeds $SEEDS 2>&1 | tee -a "$LOG" || fail "analysis" $?

echo "=== RESCORE MULTISEED DONE @ $(date '+%H:%M:%S') ===" | tee -a "$LOG"
echo "ok" > "${MARKER}_DONE"
