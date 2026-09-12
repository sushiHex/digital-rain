#!/usr/bin/env bash
# Retrain the 4B r32 on the LICENCE-CLEAN corpus (838 of 925 fonts).
#
# WHY: 87 corpus fonts carry terms that do not permit creating AND
# redistributing derivative works, which is exactly what this model does --
# 48 vendor-supplied Windows faces, 36 Fontshare closed-source (ITF-FFL, which
# claims derivative works as the foundry's property), and 3 with no locatable
# grant. train_lora_kg.py filters them via research/corpus_exclusions.json,
# which is on by default. See
# research/2026-08-08-identifying-the-undocumented-13-percent.md.
#
# STEPS SCALES WITH CORPUS SIZE. dataset_v2 at 925 fonts and 5000 steps is
# 5.405 steps/font. Holding that per-font budget over 838 fonts gives
# 838 * 5.405 = 4530. Running the smaller corpus at the original 5000 would
# quietly RAISE the per-font budget by 10% and confound the licence change with
# a training-length change -- the same mechanism, inverted, that sank V4 and the
# corpus-expansion run (CLAUDE.md, "Runners are parameterised").
#
# This run also carries the LR-horizon fix (f0ccb7e), so it is NOT comparable
# to the pre-2026-08-08 checkpoints. Its comparison partner is
# training_glyph_4b_r32_5000_lrfix, which differs from it ONLY in the corpus.
#
# QUEUED: waits for the in-flight LR-fix run's marker before touching the GPU,
# because the 3090 is shared and both need ~9 GB.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root

WAIT_FOR=${WAIT_FOR:-GLYPH_4B_LRFIX_DONE}
WAIT_TIMEOUT=${WAIT_TIMEOUT:-64800}      # 18h; the LR-fix run is ~12h
MARKER=${MARKER:-GLYPH_4B_CLEAN}

rm -f "${MARKER}_DONE" "${MARKER}_FAIL"

if [ -n "$WAIT_FOR" ]; then
  echo "=== waiting for $WAIT_FOR (timeout ${WAIT_TIMEOUT}s) @ $(date '+%H:%M:%S') ==="
  waited=0
  while [ ! -f "$WAIT_FOR" ]; do
    # A FAIL marker on the predecessor means the GPU is free but something is
    # wrong. Stop rather than pile a second run on top of an unexplained failure.
    if [ -f "${WAIT_FOR%_DONE}_FAIL" ]; then
      echo "=== predecessor FAILED; not starting @ $(date '+%H:%M:%S') ==="
      echo "predecessor_failed" > "${MARKER}_FAIL"
      exit 1
    fi
    if [ "$waited" -ge "$WAIT_TIMEOUT" ]; then
      echo "=== timed out waiting for $WAIT_FOR @ $(date '+%H:%M:%S') ==="
      echo "wait_timeout" > "${MARKER}_FAIL"
      exit 1
    fi
    sleep 120
    waited=$((waited + 120))
  done
  echo "=== $WAIT_FOR present; proceeding @ $(date '+%H:%M:%S') ==="
fi

export RANK=${RANK:-32}
export OUT=${OUT:-training_glyph_4b_r32_clean}
export EVAL_OUT=${EVAL_OUT:-eval_runs/glyph_4b_r32_clean}
export LOG=${LOG:-glyph_4b_clean.log}
export DATASET=${DATASET:-dataset_v2}
export STEPS=${STEPS:-4530}
export MARKER
exec ./runners/run_glyph_4b_r32.sh
