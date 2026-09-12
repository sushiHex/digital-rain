#!/usr/bin/env bash
# Detached runner: HD-Task 3 Step 3 — 10-font zero-shot probes of checkpoint-5000
# with the mild and strong disambiguated templates. Sequential (one GPU).
# Completion marker: eval_runs/DISAMBIG_PROBES_DONE. Log: run_disambig_probes.log
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
log() { echo "$(date '+%H:%M:%S') PROBES: $*"; }

for variant in mild strong; do
  out="eval_runs/glyph_r32_disambig10_${variant}"
  if [ -f "$out/scores.json" ]; then log "$variant already scored — skip"; continue; fi
  log "starting $variant probe (10 fonts, in-process)"
  python eval_checkpoint.py --model black-forest-labs/FLUX.2-klein-base-9B --checkpoint training_glyph_r32_5000/checkpoint-5000 \
      --use-template --template-pt "dataset_v2/cache/template_disambig_${variant}.pt" \
      --in-process --holdout eval_holdout --out "$out" --count 10 --skip-existing \
      >> "run_disambig_probes_${variant}.log" 2>&1
  code=$?
  log "$variant probe exited code=$code; scores.json: $( [ -f "$out/scores.json" ] && echo yes || echo NO )"
  if [ ! -f "$out/scores.json" ]; then log "$variant FAILED — stopping."; echo "FAILED $variant" > eval_runs/DISAMBIG_PROBES_DONE; exit 1; fi
done
echo "OK" > eval_runs/DISAMBIG_PROBES_DONE
log "both probes complete."
