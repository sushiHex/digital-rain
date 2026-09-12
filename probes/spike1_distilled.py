"""Spike 1: does the Ref2Font V3 LoRA survive a FAST klein variant with grid
integrity, at sub-minute latency?

Defaults to the already-cached FLUX.2-klein-9b-kv (the owner's "~37s KV model",
flagged in memory as having "grid issues"). Renders a subset of the hard fonts
at a few step counts and times each generation (excluding model load). Compare
visually + via OCR against the base-9B V3 atlases already in
experiments/ref2font_v3_benchmark/.

Usage:
  python probes/spike1_distilled.py                         # KV model, 2 fonts, steps 4+8
  python probes/spike1_distilled.py --model black-forest-labs/FLUX.2-klein-9B --steps 4
  python probes/spike1_distilled.py --fonts RubikDistressed --steps 4 8 28
"""

# repo root on sys.path so `python probes/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import time
from pathlib import Path

import torch

from probe_utils import HARD_FONTS
from run_ref2font_v3_benchmark import render_aa_reference

OUT_DIR = Path("experiments/spike1_distilled")

V3_PROMPT = ('A technical font atlas grid of the Latin charset: '
             '"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
             '0123456789!?.,;:-\"&". The style is strictly derived from '
             'the reference image "Aa".')


def model_tag(model_repo: str) -> str:
    return model_repo.split("/")[-1].replace(".", "").replace("-", "").lower()


def load_pipeline(model_repo: str):
    from diffusers import Flux2KleinPipeline
    from optimum.quanto import quantize, qfloat8, freeze
    from huggingface_hub import hf_hub_download

    print(f"Downloading Ref2Font V3 LoRA...")
    lora_path = hf_hub_download("SnJake/Ref2Font", "Ref2FontV3.safetensors")

    print(f"Loading {model_repo} ...")
    t0 = time.time()
    pipe = Flux2KleinPipeline.from_pretrained(model_repo, torch_dtype=torch.bfloat16)
    quantize(pipe.transformer, weights=qfloat8)
    freeze(pipe.transformer)
    pipe.load_lora_weights(lora_path)
    if hasattr(pipe, "enable_vae_tiling"):
        pipe.enable_vae_tiling()
    elif hasattr(pipe.vae, "enable_tiling"):
        pipe.vae.enable_tiling()
    pipe.enable_model_cpu_offload()
    print(f"  loaded in {time.time()-t0:.0f}s")
    return pipe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="black-forest-labs/FLUX.2-klein-9b-kv")
    parser.add_argument("--steps", type=int, nargs="+", default=[4, 8])
    parser.add_argument("--fonts", nargs="+",
                        default=["RubikDistressed", "BitcountGridDoubleInk"])
    parser.add_argument("--cfg", type=float, default=5.0)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tag = model_tag(args.model)

    # Pre-render Aa references (CPU) so any bug surfaces before the slow load.
    print("Pre-rendering Aa references...")
    refs = {}
    for name in args.fonts:
        refs[name] = render_aa_reference(HARD_FONTS[name]).convert("RGB")

    pipe = load_pipeline(args.model)

    results = []
    for name in args.fonts:
        for steps in args.steps:
            out_path = OUT_DIR / f"{name}__{tag}_{steps}step.png"
            if out_path.exists():
                print(f"SKIP {out_path.name} (exists)")
                continue
            print(f"=== {name} / {tag} / {steps} steps ===", flush=True)
            gen = torch.Generator().manual_seed(args.seed)
            t0 = time.time()
            try:
                img = pipe(
                    prompt=V3_PROMPT,
                    image=refs[name],
                    height=1280, width=1280,
                    num_inference_steps=steps,
                    guidance_scale=args.cfg,
                    generator=gen,
                ).images[0]
            except Exception as e:
                print(f"  GENERATION FAILED: {type(e).__name__}: {str(e)[:300]}", flush=True)
                continue
            dt = time.time() - t0
            tmp = out_path.with_suffix(".png.tmp")
            img.save(tmp, format="PNG")
            import os
            os.replace(tmp, out_path)
            sub_minute = "OK (<60s)" if dt < 60 else "OVER 60s"
            print(f"  saved {out_path.name}  latency={dt:.1f}s  [{sub_minute}]", flush=True)
            results.append((name, steps, dt))

    print("\n=== LATENCY SUMMARY ===")
    for name, steps, dt in results:
        print(f"  {name:>26}  {steps:>3} steps  {dt:>6.1f}s  {'<60s OK' if dt<60 else 'OVER'}")
    print(f"\nOutputs in {OUT_DIR}/  -- compare visually to experiments/ref2font_v3_benchmark/{{font}}__v3_atlas.png")


if __name__ == "__main__":
    main()
