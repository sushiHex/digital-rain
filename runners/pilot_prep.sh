#!/usr/bin/env bash
# Pilot data-prep: cross-model candidate gen + scoring + selection on 80 training
# fonts. Resumable (candidate_gen skips existing PNGs; score_candidates now
# checkpoints scores.json every 10 candidates) -> crash-safe.
#
# VRAM GATE: this box is shared. Another agent's Ollama model (e.g. qwen3:32b,
# ~22GB) can land on the GPU mid-run and starve us -- that is what wedged the
# earlier generation and scoring passes. Rather than force-evicting someone's
# live work, wait for headroom before starting.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f PILOT_PREP_DONE PILOT_PREP_FAIL
MAN="${PILOT_MANIFEST:?set PILOT_MANIFEST to the 80-font manifest JSON (same shape as the --fonts-manifest arg of candidate_gen.py)}"
NEED_MB=${NEED_MB:-4000}   # scoring needs ~2GB; ask for margin
fail() { echo "=== PILOT PREP FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ==="; echo "$1 exit=$2" > PILOT_PREP_FAIL; exit 1; }

{
  echo "=== [0/4] waiting for >=${NEED_MB}MB free VRAM @ $(date '+%H:%M:%S') ==="
  free=0
  for i in $(seq 1 480); do   # up to 4h
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1)
    free=${free:-0}
    if [ "$free" -ge "$NEED_MB" ]; then break; fi
    if [ $((i % 20)) -eq 0 ]; then echo "  still waiting: ${free}MB free @ $(date '+%H:%M:%S')"; fi
    sleep 30
  done
  echo "=== VRAM gate passed: ${free}MB free @ $(date '+%H:%M:%S') ==="

  echo "=== [1/4] candidate_gen (already 240/240 -> fast no-op) @ $(date '+%H:%M:%S') ==="
  python candidate_gen.py --fonts-manifest "$MAN" --out-dir dpo_pilot --models baseline,glyph --glyph-seeds 2 --steps 20 || fail candidate_gen $?
  echo "=== [2/4] score_candidates (models cached; ckpt every 10) @ $(date '+%H:%M:%S') ==="
  python score_candidates.py --candidates-dir dpo_pilot/candidates --gt-atlas-dir dataset_v2/atlases --out dpo_pilot/scores.json || fail score_candidates $?
  echo "=== [3/4] select_preferences (eps 0.05) @ $(date '+%H:%M:%S') ==="
  python select_preferences.py --scores dpo_pilot/scores.json --out dpo_pilot --eps 0.05 || fail select_preferences $?
  echo "=== [4/4] pilot realizable ceiling (mini Gate -1 on pilot fonts) @ $(date '+%H:%M:%S') ==="
  python measure_oracle_ceiling.py --scores dpo_pilot/scores.json || fail measure_ceiling $?
  echo "=== PILOT PREP OK @ $(date '+%H:%M:%S') ==="
  echo "ok" > PILOT_PREP_DONE
} >> pilot_prep.log 2>&1
