#!/usr/bin/env bash
# Complete the Stage A LITE holdout eval (mirrors stage_a_eval.sh: eval_checkpoint
# aborts generation on its RAM guard and exits 0 after scoring whatever it made,
# so loop with --skip-existing until all 50 atlases exist / scores.json num_fonts=50).
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f STAGE_A_LITE_EVAL_DONE STAGE_A_LITE_EVAL_FAIL
OUT=eval_runs/stageA_lite

{
  prev_n=-1
  for attempt in $(seq 1 30); do
    n=$(ls $OUT/generated/*.png 2>/dev/null | wc -l)
    echo "=== attempt $attempt: $n/50 atlases @ $(date '+%H:%M:%S') ==="

    for i in $(seq 1 480); do
      free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1); free=${free:-0}
      [ "$free" -ge 20000 ] && break
      sleep 30
    done

    python eval_checkpoint.py --model black-forest-labs/FLUX.2-klein-base-9B --checkpoint training_stageA_lite/final --identity --use-template --in-process \
      --template-pt dataset_v2/cache/template_disambig_mild.pt \
      --holdout eval_holdout --out $OUT --skip-existing
    rc=$?
    nf=$(python -c "import json;print(json.load(open('$OUT/scores.json')).get('num_fonts',0))" 2>/dev/null || echo 0)
    n=$(ls $OUT/generated/*.png 2>/dev/null | wc -l)
    echo "=== after attempt $attempt: rc=$rc atlases=$n scored_fonts=$nf @ $(date '+%H:%M:%S') ==="
    if [ "$nf" -ge 50 ]; then echo "ok" > STAGE_A_LITE_EVAL_DONE; echo "=== EVAL COMPLETE (50 fonts) @ $(date '+%H:%M:%S') ==="; exit 0; fi
    if [ "$n" -eq "$prev_n" ] && [ "$attempt" -gt 2 ]; then
      echo "=== NO PROGRESS across attempts — aborting @ $(date '+%H:%M:%S') ==="; echo "no-progress" > STAGE_A_LITE_EVAL_FAIL; exit 1
    fi
    prev_n=$n
  done
  echo "attempts-exhausted" > STAGE_A_LITE_EVAL_FAIL
} >> stage_a_lite_eval.log 2>&1
