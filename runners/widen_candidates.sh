#!/usr/bin/env bash
# Widen the pilot candidate pool from 3 renders/cell (1 baseline + 2 glyph
# seeds) to 5 (1 baseline + 4 glyph seeds), to test whether Stage A's
# regression (persistent 31/50-fonts-worse breadth even at gentle training)
# is driven by a too-small candidate pool producing borderline "correct"
# winners, rather than purely training-set bias/intensity.
#
# All three steps are idempotent (candidate_gen skips existing PNGs,
# score_candidates skips already-scored keys) EXCEPT select_preferences,
# which overwrites pref_pairs.json/sft_targets.json wholesale — the 3-seed
# versions were already backed up to *_3seed.json before this ran.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f WIDEN_DONE WIDEN_FAIL
MAN="${PILOT_MANIFEST:?set PILOT_MANIFEST to the same 80-font manifest pilot_prep.sh used}"
fail() { echo "=== WIDEN FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ==="; echo "$1 exit=$2" > WIDEN_FAIL; exit 1; }

{
  echo "=== [0/4] waiting for >=4000MB free VRAM @ $(date '+%H:%M:%S') ==="
  for i in $(seq 1 480); do
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1); free=${free:-0}
    [ "$free" -ge 4000 ] && break
    [ $((i % 20)) -eq 0 ] && echo "  waiting: ${free}MB free @ $(date '+%H:%M:%S')"
    sleep 30
  done
  echo "=== gate passed: ${free}MB free @ $(date '+%H:%M:%S') ==="

  echo "=== [1/4] candidate_gen: widen glyph seeds 2->4 (160 new renders) @ $(date '+%H:%M:%S') ==="
  python candidate_gen.py --fonts-manifest "$MAN" --out-dir dpo_pilot --models baseline,glyph --glyph-seeds 4 --steps 20 || fail candidate_gen $?
  echo "=== [2/4] score_candidates (idempotent — scores only the new candidates) @ $(date '+%H:%M:%S') ==="
  python score_candidates.py --candidates-dir dpo_pilot/candidates --gt-atlas-dir dataset_v2/atlases --out dpo_pilot/scores.json || fail score_candidates $?
  echo "=== [3/4] select_preferences on the widened pool (eps 0.05) @ $(date '+%H:%M:%S') ==="
  python select_preferences.py --scores dpo_pilot/scores.json --out dpo_pilot --eps 0.05 || fail select_preferences $?
  echo "=== [4/4] widened pilot realizable ceiling @ $(date '+%H:%M:%S') ==="
  python measure_oracle_ceiling.py --scores dpo_pilot/scores.json || fail measure_ceiling $?
  echo "=== WIDEN DONE @ $(date '+%H:%M:%S') ==="
  echo "ok" > WIDEN_DONE
} >> widen_candidates.log 2>&1
