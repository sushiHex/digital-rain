#!/usr/bin/env bash
# Levers 2+3: how much training throughput is left on the table on the 4B?
#
# The rank-32 run peaked at 7.8 GB of 24 WITH grad checkpointing on, and rank 32
# cost the same as rank 16 -- activations dominate, not adapter parameters. So
# grad-checkpointing-off and larger batches are affordable here in a way they
# never were on the 9B (15.6 GB peak).
#
# Each arm trains 120 steps into a throwaway dir and is read for s/step and peak
# VRAM from its metrics.csv. 120 steps is enough for a stable rate and costs
# ~15 min per arm; nothing here is a quality measurement.
#
# Arms:
#   A  rank 32, grad-ckpt ON,  batch 1   -- the shipped-run config (control)
#   B  rank 32, grad-ckpt OFF, batch 1   -- does removing recompute pay?
#   C  rank 32, grad-ckpt ON,  batch 2   -- more work per optimizer step
#   D  rank 64, grad-ckpt ON,  batch 1   -- does the quality lever cost speed?
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f PROBE_DONE PROBE_FAIL

MODEL="black-forest-labs/FLUX.2-klein-base-4B"
STEPS=120
NEED_MB=${NEED_MB:-14000}

fail() { echo "=== PROBE FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ==="; \
         echo "$1 exit=$2" > PROBE_FAIL; exit 1; }

gate() {
  free=0
  for i in $(seq 1 480); do
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1)
    free=${free:-0}
    [ "$free" -ge "$NEED_MB" ] && break
    [ $((i % 20)) -eq 0 ] && echo "  waiting: ${free}MB free @ $(date '+%H:%M:%S')"
    sleep 30
  done
  [ "$free" -ge "$NEED_MB" ] || return 1
}

# arm <name> <extra-args...>
arm() {
  name="$1"; shift
  out="probe_$name"
  rm -rf "$out"
  gate || fail "vram_gate_$name" 1
  echo "=== [$name] $* @ $(date '+%H:%M:%S') ==="
  # An OOM here is a RESULT (that config does not fit), not a run failure --
  # record it and continue to the next arm.
  if python train_lora_kg.py --model "$MODEL" --dataset-dir dataset_v2 \
       --output-dir "$out" --steps "$STEPS" --lr 1e-4 --seed 42 --use-template "$@"; then
    echo "=== [$name] ok @ $(date '+%H:%M:%S') ==="
  else
    echo "=== [$name] FAILED (likely OOM) -- recorded, continuing @ $(date '+%H:%M:%S') ==="
  fi
}

{
  arm A_ckpt_on_b1   --rank 32 --grad-accum 2 --grad-checkpointing
  arm B_ckpt_off_b1  --rank 32 --grad-accum 2 --no-grad-checkpointing
  arm C_ckpt_on_b2   --rank 32 --grad-accum 2 --batch-size 2 --grad-checkpointing
  arm D_rank64       --rank 64 --grad-accum 2 --grad-checkpointing

  echo "=== PROBE DONE @ $(date '+%H:%M:%S') ==="
  echo "ok" > PROBE_DONE
} >> throughput_probe.log 2>&1
