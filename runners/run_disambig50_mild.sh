#!/usr/bin/env bash
# HD-Task 3 Step 4: 50-font extension of the MILD disambig probe (the better cue strength).
# Reuses the 10 atlases already generated (copy + --skip-existing). Detached, survives kills.
# Marker: eval_runs/DISAMBIG50_DONE. Log: run_disambig50_mild.log
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
log() { echo "$(date '+%H:%M:%S') D50: $*"; }
OUT=eval_runs/glyph_r32_disambig50_mild
rm -f eval_runs/DISAMBIG50_DONE
mkdir -p "$OUT/generated"
# reuse the 10 already-generated mild atlases
cp -n eval_runs/glyph_r32_disambig10_mild/generated/*.png "$OUT/generated/" 2>/dev/null
log "seeded $(ls "$OUT/generated"/*.png 2>/dev/null | wc -l) atlases from the 10-font probe"
python eval_checkpoint.py --checkpoint training_glyph_r32_5000/checkpoint-5000 \
    --use-template --template-pt dataset_v2/cache/template_disambig_mild.pt --in-process \
    --holdout eval_holdout --out "$OUT" --skip-existing >> run_disambig50_mild.log 2>&1
code=$?
log "eval exited code=$code; scores.json: $( [ -f "$OUT/scores.json" ] && echo yes || echo NO )"
echo "exit=$code" > eval_runs/DISAMBIG50_DONE
