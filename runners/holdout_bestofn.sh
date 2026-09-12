#!/usr/bin/env bash
# Foundational sanity check: is the 0.6883 char_acc "ceiling" on the 50-font
# holdout (glyph-cond@5000+disambig) architectural, or partly variance-bound
# and recoverable by sampling? EVERY char_acc number in this investigation
# (0.688, 0.668, all Stage A variants) comes from a SINGLE FIXED SEED
# (--seed 42, "fixed for reproducibility" per eval_checkpoint.py:976) --
# nobody has measured the model's own best-of-N ceiling on the real holdout.
#
# On the 80-font PILOT, going 2->4 glyph seeds recovered +0.093 char_acc from
# sampling ALONE (0.649->0.742), and the apparent cross-model headroom that
# motivated the whole DPO track shrank correspondingly (0.0605->0.0240 gap).
# This generates 4 INDEPENDENT glyph-only seeds on the ACTUAL holdout (no
# baseline model -- isolates same-model variance from the cross-model
# question) to see whether that effect replicates on the real distribution.
#
# Pure inference, no training. VRAM-gated (shared box).
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f HOLDOUT_BESTOFN_DONE HOLDOUT_BESTOFN_FAIL
fail() { echo "=== HOLDOUT BESTOFN FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ==="; echo "$1 exit=$2" > HOLDOUT_BESTOFN_FAIL; exit 1; }

{
  echo "=== [0/3] waiting for >=4000MB free VRAM @ $(date '+%H:%M:%S') ==="
  for i in $(seq 1 480); do
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1); free=${free:-0}
    [ "$free" -ge 4000 ] && break
    [ $((i % 20)) -eq 0 ] && echo "  waiting: ${free}MB free @ $(date '+%H:%M:%S')"
    sleep 30
  done
  echo "=== gate passed: ${free}MB free @ $(date '+%H:%M:%S') ==="

  echo "=== [1/3] candidate_gen: 4 glyph seeds on the 50-font HOLDOUT (200 renders) @ $(date '+%H:%M:%S') ==="
  python candidate_gen.py --fonts-manifest eval_holdout/manifest.json --out-dir dpo_holdout_bestofn \
    --models glyph --glyph-seeds 4 --steps 20 || fail candidate_gen $?
  echo "=== [2/3] score_candidates against holdout GT @ $(date '+%H:%M:%S') ==="
  python score_candidates.py --candidates-dir dpo_holdout_bestofn/candidates \
    --gt-atlas-dir eval_holdout/atlases --out dpo_holdout_bestofn/scores.json || fail score_candidates $?
  echo "=== [3/3] best-of-N ceiling (glyph-only, no cross-model) @ $(date '+%H:%M:%S') ==="
  python analysis/analyze_holdout_bestofn.py dpo_holdout_bestofn/scores.json || fail analysis $?
  echo "=== HOLDOUT BESTOFN DONE @ $(date '+%H:%M:%S') ==="
  echo "ok" > HOLDOUT_BESTOFN_DONE
} >> holdout_bestofn.log 2>&1
