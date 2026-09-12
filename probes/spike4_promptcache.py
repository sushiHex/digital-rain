"""Spike 4: prompt-embed caching to break the ~27s/step wall on distilled-9B.

Our prompt is FIXED (same atlas layout every render; only the reference image
changes). So encode it ONCE with the text encoder on GPU, move the text encoder
to CPU, keep the transformer RESIDENT on GPU (no offload), and render with the
cached embeds. Hypothesis: the ~27s/step seen with enable_model_cpu_offload was
the big FLUX.2 text encoder competing for VRAM and forcing per-step transformer
thrash; freeing it should restore base-like ~8s/step -> 4 steps ~= sub-minute.

Reports per-step latency, total, and peak VRAM. Distilled klein-9B (gated, now
accessible).
"""

# repo root on sys.path so `python probes/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import time

import torch

from probe_utils import HARD_FONTS
from run_ref2font_v3_benchmark import render_aa_reference

MODEL = "black-forest-labs/FLUX.2-klein-9B"
V3_PROMPT = ('A technical font atlas grid of the Latin charset: '
             '"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
             '0123456789!?.,;:-\"&". The style is strictly derived from '
             'the reference image "Aa".')


def main():
    total_vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"GPU: {torch.cuda.get_device_name(0)} ({total_vram:.1f}GB)")

    from diffusers import Flux2KleinPipeline
    from optimum.quanto import quantize, qfloat8, freeze
    from huggingface_hub import hf_hub_download

    lora = hf_hub_download("SnJake/Ref2Font", "Ref2FontV3.safetensors")

    print("Loading distilled klein-9B + quanto + LoRA...")
    t0 = time.time()
    pipe = Flux2KleinPipeline.from_pretrained(MODEL, torch_dtype=torch.bfloat16)
    quantize(pipe.transformer, weights=qfloat8)
    freeze(pipe.transformer)
    pipe.load_lora_weights(lora)
    print(f"  loaded in {time.time()-t0:.0f}s")

    # 1) Encode the fixed prompt ONCE with the text encoder briefly on GPU.
    print("Encoding fixed prompt once (text encoder -> GPU)...")
    pipe.text_encoder.to("cuda")
    t1 = time.time()
    enc = pipe.encode_prompt(V3_PROMPT, device="cuda")
    prompt_embeds = enc[0] if isinstance(enc, (tuple, list)) else enc
    prompt_embeds = prompt_embeds.to("cuda")
    print(f"  encoded in {time.time()-t1:.0f}s  embeds shape={tuple(prompt_embeds.shape)}")

    # 2) Evict the text encoder from GPU; keep transformer + VAE resident.
    pipe.text_encoder.to("cpu")
    torch.cuda.empty_cache()
    pipe.transformer.to("cuda")
    pipe.vae.to("cuda")
    if hasattr(pipe.vae, "enable_tiling"):
        pipe.vae.enable_tiling()
    torch.cuda.empty_cache()
    after_load_vram = torch.cuda.memory_allocated() / 1e9
    print(f"  transformer+VAE resident, text encoder on CPU. VRAM in use: {after_load_vram:.1f}GB")

    results = []
    for font in ["RubikDistressed", "BitcountGridDoubleInk"]:
        ref = render_aa_reference(HARD_FONTS[font]).convert("RGB")
        torch.cuda.reset_peak_memory_stats()
        print(f"=== {font} @ 4 steps (cached embeds, transformer resident) ===", flush=True)
        t2 = time.time()
        try:
            img = pipe(
                image=ref,
                prompt_embeds=prompt_embeds,
                height=1280, width=1280,
                num_inference_steps=4,
                generator=torch.Generator("cpu").manual_seed(42),
            ).images[0]
        except Exception as e:
            print(f"  FAILED: {type(e).__name__}: {str(e)[:400]}", flush=True)
            return
        dt = time.time() - t2
        peak = torch.cuda.max_memory_allocated() / 1e9
        from pathlib import Path
        out = Path("experiments/spike4_promptcache")
        out.mkdir(parents=True, exist_ok=True)
        img.save(str(out / f"{font}_distilled9b_4step_cached.png"), format="PNG")
        verdict = "<60s SUB-MINUTE" if dt < 60 else "OVER 60s"
        print(f"  total {dt:.1f}s  (~{dt/4:.1f}s/step)  peak VRAM {peak:.1f}GB  [{verdict}]", flush=True)
        results.append((font, dt))

    print("\n=== RESULT ===")
    for font, dt in results:
        print(f"  {font:>26}  {dt:6.1f}s  ~{dt/4:.1f}s/step  {'SUB-MINUTE' if dt<60 else 'OVER'}")
    print("  baseline (offload, no cache): ~27s/step, ~152s total")


if __name__ == "__main__":
    main()
