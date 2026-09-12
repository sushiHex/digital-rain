"""Spike 3: disambiguate the KV slowdown -- offload-bound vs intrinsic per-step.

Uses the ALREADY-CACHED klein-9b-kv (bf16), quanto-quantizes the transformer
(as spike1 did), but tries pipe.to("cuda") with NO cpu-offload. If per-step
latency drops from ~24s (offload, spike1) to ~8s (base-like), offload was the
cause and the fitting fp8 KV would be fast. If it stays ~24s, the KV variant is
intrinsically slow per step and the real sub-minute path is the plain distilled
klein-9B (gated). Reports peak VRAM and whether it fit without offload.
No download.
"""

# repo root on sys.path so `python probes/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import time

import torch

from probe_utils import HARD_FONTS
from run_ref2font_v3_benchmark import render_aa_reference

V3_PROMPT = ('A technical font atlas grid of the Latin charset: '
             '"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
             '0123456789!?.,;:-\"&". The style is strictly derived from '
             'the reference image "Aa".')


def main():
    total_vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"GPU: {torch.cuda.get_device_name(0)}  ({total_vram:.1f}GB)")

    from diffusers import Flux2KleinPipeline
    from optimum.quanto import quantize, qfloat8, freeze
    from huggingface_hub import hf_hub_download

    lora_path = hf_hub_download("SnJake/Ref2Font", "Ref2FontV3.safetensors")

    print("Loading cached klein-9b-kv (bf16) + quantizing transformer to fp8...")
    t0 = time.time()
    pipe = Flux2KleinPipeline.from_pretrained(
        "black-forest-labs/FLUX.2-klein-9b-kv", torch_dtype=torch.bfloat16
    )
    quantize(pipe.transformer, weights=qfloat8)
    freeze(pipe.transformer)
    pipe.load_lora_weights(lora_path)
    print(f"  loaded+quantized in {time.time()-t0:.0f}s")

    offload = False
    try:
        print("Attempting pipe.to('cuda') with NO offload...")
        pipe.to("cuda")
        print("  fit on GPU without offload")
    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        print("  OOM without offload -> falling back to enable_model_cpu_offload()")
        pipe.enable_model_cpu_offload()
        offload = True

    ref = render_aa_reference(HARD_FONTS["RubikDistressed"]).convert("RGB")

    torch.cuda.reset_peak_memory_stats()
    print("Rendering RubikDistressed @ 4 steps...")
    t1 = time.time()
    img = pipe(
        prompt=V3_PROMPT, image=ref,
        height=1280, width=1280,
        num_inference_steps=4,
        generator=torch.Generator().manual_seed(42),
    ).images[0]
    dt = time.time() - t1
    peak = torch.cuda.max_memory_allocated() / 1e9

    from pathlib import Path
    out = Path("experiments/spike3_nooffload")
    out.mkdir(parents=True, exist_ok=True)
    img.save(str(out / "RubikDistressed_kv_fp8quant_4step.png"), format="PNG")

    print("\n=== RESULT ===")
    print(f"  offload used:    {offload}")
    print(f"  total latency:   {dt:.1f}s  ({'<60s SUB-MINUTE' if dt < 60 else 'OVER 60s'})")
    print(f"  per-step (~):    {dt/4:.1f}s")
    print(f"  peak VRAM:       {peak:.1f}GB / {total_vram:.1f}GB")
    print(f"  spike1 baseline: ~24s/step (kv + offload). If per-step ~8s now -> offload was the cause.")


if __name__ == "__main__":
    main()
