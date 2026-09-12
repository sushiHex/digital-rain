#!/usr/bin/env bash
# Score structural distinctiveness of every OFL family not already in the
# corpus, to pick a corpus-expansion set on measured spread rather than family
# names.
#
# Why this and not another training lever: rank 64, distinctiveness
# oversampling, and the V5 source swap all produced the same signature --
# gains on hard fonts, matching losses on easy ones, flat aggregate. That is
# redistribution at fixed information. Only 93 of 925 corpus fonts sit above
# p90 distinctiveness, and the corpus keeps ~37% of what it saw where
# comparable work keeps 73%. Adding information has never been tested.
#
# Scores are anchored to the CORPUS centroid so they are directly comparable
# to research/font_distinctiveness.json. Holdout fonts are excluded -- they are
# absent from dataset_v2 and would otherwise read as fresh candidates.
#
# Mostly CPU (font gates + rendering); DINOv2 is the only GPU part.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f SCORE_POOL_DONE SCORE_POOL_FAIL

FONT_DIR="${POOL_FONT_DIR:-google-fonts/ofl}"
OUT="${POOL_OUT:-research/pool_distinctiveness.json}"
GATE_MB="${POOL_GATE_MB:-3000}"
LOG="${POOL_LOG:-score_pool.log}"

fail() { echo "=== SCORE POOL FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ==="; echo "$1 exit=$2" > SCORE_POOL_FAIL; exit 1; }

{
  echo "=== [0/1] waiting for >=${GATE_MB}MB free VRAM @ $(date '+%H:%M:%S') ==="
  for i in $(seq 1 480); do
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1); free=${free:-0}
    [ "$free" -ge "$GATE_MB" ] && break
    [ $((i % 20)) -eq 0 ] && echo "  waiting: ${free}MB free @ $(date '+%H:%M:%S')"
    sleep 30
  done
  echo "=== gate passed: ${free}MB free @ $(date '+%H:%M:%S') ==="

  echo "=== scoring $FONT_DIR -> $OUT @ $(date '+%H:%M:%S') ==="
  python analysis/score_pool_distinctiveness.py \
    --font-dir "$FONT_DIR" --out "$OUT" || fail score_pool $?

  echo "=== SCORE POOL DONE @ $(date '+%H:%M:%S') ==="
  echo "ok" > SCORE_POOL_DONE
} >> "$LOG" 2>&1
