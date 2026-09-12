"""Controlled per-step latency benchmark for ONE model in a fresh process.

Why: across a long session, the same model measured 8s/step AND 54s/step in the
same harness — latency numbers got confounded by accumulated GPU/allocator
state. Run THIS in a fresh session (clean GPU), once per candidate, to get
trustworthy steady-state numbers and decide whether sub-minute (4-step) is real.

Usage (run each in a fresh session, GPU otherwise idle):
  python benchmarks/benchmark_latency.py --model black-forest-labs/FLUX.2-klein-base-9B --steps 8
  python benchmarks/benchmark_latency.py --model black-forest-labs/FLUX.2-klein-9B       --steps 4
  python benchmarks/benchmark_latency.py --model black-forest-labs/FLUX.2-klein-9b-kv    --steps 4

Method: load (quanto fp8 + LoRA + cpu-offload, the production path), do ONE
warm-up render (discarded), then time `--runs` steady-state renders. Reports
per-step latency, total, peak VRAM, and a sub-minute verdict. Loads ONE model
per process so allocator state can't leak between candidates.
"""

# repo root on sys.path so `python benchmarks/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import time

import torch

from probe_utils import HARD_FONTS
from run_ref2font_v3_benchmark import render_aa_reference

V3_PROMPT = ('A technical font atlas grid of the Latin charset: '
             '"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
             '0123456789!?.,;:-\"&". The style is strictly derived from '
             'the reference image "Aa".')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--steps", type=int, default=4)
    ap.add_argument("--warmup", type=int, default=1)
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--font", default="RubikDistressed")
    ap.add_argument("--quant", choices=["fp8", "int8"], default="fp8",
                    help="quanto weight dtype: fp8 (qfloat8, no Ampere accel) or int8 (qint8, Ampere INT8 cores)")
    ap.add_argument("--compile", action="store_true", help="torch.compile the transformer")
    args = ap.parse_args()

    total_vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"GPU: {torch.cuda.get_device_name(0)} ({total_vram:.1f}GB)")
    print(f"Model: {args.model}  steps={args.steps}  quant={args.quant}")

    from diffusers import Flux2KleinPipeline
    from optimum.quanto import quantize, qfloat8, qint8, freeze
    from huggingface_hub import hf_hub_download
    qweights = qfloat8 if args.quant == "fp8" else qint8

    lora = hf_hub_download("SnJake/Ref2Font", "Ref2FontV3.safetensors")
    t0 = time.time()
    pipe = Flux2KleinPipeline.from_pretrained(args.model, torch_dtype=torch.bfloat16)
    quantize(pipe.transformer, weights=qweights)
    freeze(pipe.transformer)
    pipe.load_lora_weights(lora)
    if hasattr(pipe, "enable_vae_tiling"):
        pipe.enable_vae_tiling()
    elif hasattr(pipe.vae, "enable_tiling"):
        pipe.vae.enable_tiling()
    pipe.enable_model_cpu_offload()
    if args.compile:
        # Inductor (no cudagraphs — cudagraphs conflicts with cpu-offload). The
        # first (warmup) render pays the compile cost; timed runs see the gain.
        pipe.transformer = torch.compile(pipe.transformer, mode="default", fullgraph=False)
        print("  torch.compile enabled (inductor, no cudagraphs)")
    print(f"  load+quantize: {time.time()-t0:.0f}s")

    ref = render_aa_reference(HARD_FONTS[args.font]).convert("RGB")

    def render(seed):
        return pipe(
            prompt=V3_PROMPT, image=ref,
            height=1280, width=1280,
            num_inference_steps=args.steps,
            generator=torch.Generator("cpu").manual_seed(seed),
        ).images[0]

    for w in range(args.warmup):
        print(f"  warm-up {w+1}/{args.warmup}...", flush=True)
        render(1000 + w)

    times = []
    torch.cuda.reset_peak_memory_stats()
    for r in range(args.runs):
        t1 = time.time()
        render(42 + r)
        dt = time.time() - t1
        times.append(dt)
        print(f"  timed run {r+1}/{args.runs}: {dt:.1f}s  (~{dt/args.steps:.1f}s/step)", flush=True)
    peak = torch.cuda.max_memory_allocated() / 1e9

    best = min(times)
    print("\n=== RESULT ===")
    print(f"  model:       {args.model}")
    print(f"  steps:       {args.steps}")
    print(f"  best total:  {best:.1f}s  (~{best/args.steps:.1f}s/step)")
    print(f"  peak VRAM:   {peak:.1f}GB / {total_vram:.1f}GB")
    print(f"  verdict:     {'SUB-MINUTE (<60s)' if best < 60 else 'OVER 60s'}")


if __name__ == "__main__":
    main()
