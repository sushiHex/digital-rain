"""Route B speed gate: full-generation latency, fused vs unfused QKV path.

Run twice (fresh process each), GPU otherwise idle:
  ./.venv-nunchaku/Scripts/python.exe benchmark_route_b.py
  NUNCHAKU_FORCE_UNFUSED_QKV=1 ./.venv-nunchaku/Scripts/python.exe benchmark_route_b.py

GATE: unfused s/step must stay well below quanto's ~30s/step (target <=~20).
"""
import os
import time

import torch


def main():
    forced = os.getenv("NUNCHAKU_FORCE_UNFUSED_QKV", "0") == "1"
    print(f"=== Route B benchmark  forced_unfused={forced} ===", flush=True)
    print("torch", torch.__version__, torch.cuda.get_device_name(0), flush=True)

    from nunchaku.models.transformers.transformer_flux2 import (
        NunchakuFlux2Transformer2DModel,
        _FORCE_UNFUSED_QKV,
    )
    from nunchaku.utils import get_precision
    from diffusers import Flux2KleinPipeline
    from huggingface_hub import hf_hub_download

    assert _FORCE_UNFUSED_QKV == forced, (_FORCE_UNFUSED_QKV, forced)
    prec = get_precision()
    repo, name = "tonera/FLUX.2-klein-9B-Nunchaku", "FLUX.2-klein-9B-Nunchaku"
    tpath = hf_hub_download(repo, f"svdq-{prec}_r32-{name}.safetensors")

    t0 = time.time()
    tf = NunchakuFlux2Transformer2DModel.from_pretrained(tpath, torch_dtype=torch.bfloat16)
    pipe = Flux2KleinPipeline.from_pretrained(repo, torch_dtype=torch.bfloat16, transformer=tf)
    pipe.enable_model_cpu_offload()
    print(f"loaded in {time.time()-t0:.0f}s", flush=True)

    prompt = ("a technical font atlas grid of latin letters A to Z, "
              "clean black glyphs on a white background")
    steps = 8

    def render(seed):
        return pipe(
            prompt=prompt, height=1280, width=1280,
            num_inference_steps=steps,
            generator=torch.Generator("cpu").manual_seed(seed),
        ).images[0]

    print("warm-up...", flush=True)
    render(1000)

    times = []
    torch.cuda.reset_peak_memory_stats()
    for r in range(2):
        t1 = time.time()
        render(42 + r)
        dt = time.time() - t1
        times.append(dt)
        print(f"  timed run {r+1}/2: {dt:.1f}s  (~{dt/steps:.1f}s/step)", flush=True)

    best = min(times)
    peak = torch.cuda.max_memory_allocated() / 1e9
    print("\n=== RESULT ===")
    print(f"  forced_unfused: {forced}")
    print(f"  best total:     {best:.1f}s  (~{best/steps:.1f}s/step)")
    print(f"  peak VRAM:      {peak:.1f}GB")


if __name__ == "__main__":
    main()
