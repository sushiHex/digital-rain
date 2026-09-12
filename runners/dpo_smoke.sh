#!/usr/bin/env bash
# End-to-end GPU smoke for the DPO pipeline (3 fonts). Validates every
# correct-by-construction GPU path before the pilot/multi-day run.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f DPO_SMOKE_DONE DPO_SMOKE_FAIL
SM="${SMOKE_MANIFEST:?set SMOKE_MANIFEST to a 3-font manifest JSON (same shape as the --fonts-manifest arg of candidate_gen.py)}"
rm -rf dpo_smoke
fail() { echo "=== SMOKE FAIL at $1 (exit $2) ==="; echo "$1 exit=$2" > DPO_SMOKE_FAIL; exit 1; }

{
  echo "=== [1/5] candidate_gen (baseline + glyph x2 seeds, 3 fonts) @ $(date '+%H:%M:%S') ==="
  python candidate_gen.py --fonts-manifest "$SM" --out-dir dpo_smoke --models baseline,glyph --glyph-seeds 2 --steps 20 || fail candidate_gen $?
  echo "=== [2/5] score_candidates @ $(date '+%H:%M:%S') ==="
  python score_candidates.py --candidates-dir dpo_smoke/candidates --gt-atlas-dir dataset_v2/atlases --out dpo_smoke/scores.json || fail score_candidates $?
  echo "=== [3/5] select_preferences (eps 0.0 so a tiny set keeps pairs) @ $(date '+%H:%M:%S') ==="
  python select_preferences.py --scores dpo_smoke/scores.json --out dpo_smoke --eps 0.0 || fail select_preferences $?
  echo "=== [4/5] build_sft_cache (VAE encode winners) @ $(date '+%H:%M:%S') ==="
  python build_sft_cache.py --sft-targets dpo_smoke/sft_targets.json --candidate-dir dpo_smoke/candidates --out-cache dpo_smoke/sft_cache --max-fonts 3 || fail build_sft_cache $?
  echo "=== [5/5] dpo_train 5 steps (auto-builds pair cache, PEFT multi-adapter, shared noise/t) @ $(date '+%H:%M:%S') ==="
  python dpo_train.py --pairs dpo_smoke/pref_pairs.json --candidate-dir dpo_smoke/candidates --pair-cache dpo_smoke/pair_cache --max-fonts 3 --output-dir dpo_smoke/stageB --steps 5 --checkpoint-every 5 || fail dpo_train $?
  echo "=== SMOKE OK @ $(date '+%H:%M:%S') ==="
  echo "ok" > DPO_SMOKE_DONE
} > dpo_smoke.log 2>&1
