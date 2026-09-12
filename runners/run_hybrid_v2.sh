#!/usr/bin/env bash
# HD-Task 6 Step 2: full 50-font hybrid-v2 replay (GOT-OCR2 swap) + score.
# ~45min decode + ~10min score. Marker: eval_runs/HYBRID_V2_DONE. Log: run_hybrid_v2.log
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
log() { echo "$(date '+%H:%M:%S') HV2: $*"; }
rm -f eval_runs/HYBRID_V2_DONE
log "=== stage 1: replay (GOT-OCR2 decode + swap + composite, all 50 fonts) ==="
python studies/hybrid_v2_replay.py >> run_hybrid_v2.log 2>&1
r1=$?
log "replay exit=$r1; atlases: $(ls eval_runs/hybrid_v2/generated/*.png 2>/dev/null | wc -l)"
if [ "$r1" -ne 0 ]; then echo "replay_failed=$r1" > eval_runs/HYBRID_V2_DONE; exit 1; fi
log "=== stage 2: score (DINOv2 + TrOCR, --skip-generate) ==="
python eval_checkpoint.py --skip-generate --holdout eval_holdout --out eval_runs/hybrid_v2 >> run_hybrid_v2.log 2>&1
r2=$?
log "score exit=$r2; scores.json: $( [ -f eval_runs/hybrid_v2/scores.json ] && echo yes || echo NO )"
echo "replay=$r1 score=$r2" > eval_runs/HYBRID_V2_DONE
