"""Spike 2 (part 1): render K fonts x N seeds with OUR structured-5000 LoRA so we
can measure cross-seed per-cell failure independence.

Loads the model ONCE and loops (unlike render_checkpoint.py which reloads per
call). Produces our 12x8/95 atlas layout, which the existing per-cell OCR
tooling understands. Generator is parametrized: point --model at base-9B
(full quality) or the KV model (sub-minute) depending on Spike 1's result.

Usage:
  python probes/spike2_seeds.py                       # base-9B, 3 hard fonts, 4 seeds, 20 steps
  python probes/spike2_seeds.py --model black-forest-labs/FLUX.2-klein-9b-kv --steps 4
"""

# repo root on sys.path so `python probes/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import os
import time
from pathlib import Path

import torch

from atlas_constants import make_prompt
from probe_utils import HARD_FONTS
from pipeline.render_checkpoint import render_ref, seed_everything

OUT_DIR = Path("experiments/spike2_seeds")
DEFAULT_CKPT = "experiments/20260412-215340_Kg_structured_prompt_5000/checkpoints/checkpoint-5000"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="black-forest-labs/FLUX.2-klein-base-9B")
    parser.add_argument("--checkpoint", default=DEFAULT_CKPT)
    parser.add_argument("--fonts", nargs="+",
                        default=["RubikDistressed", "BitcountGridDoubleInk", "PlaywriteMXGuides"])
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44, 45])
    parser.add_argument("--steps", type=int, default=20)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tag = args.model.split("/")[-1].replace(".", "").replace("-", "").lower()

    # Pre-render Kg references (oracle: each font's own Kg) on CPU first.
    print("Pre-rendering Kg references...")
    refs = {name: render_ref(HARD_FONTS[name], "Kg").convert("RGB") for name in args.fonts}

    from diffusers import Flux2KleinPipeline
    from optimum.quanto import quantize, qfloat8, freeze
    from peft import PeftModel

    print(f"Loading {args.model} + LoRA {args.checkpoint} ...")
    t0 = time.time()
    pipe = Flux2KleinPipeline.from_pretrained(args.model, torch_dtype=torch.bfloat16)
    quantize(pipe.transformer, weights=qfloat8)
    freeze(pipe.transformer)
    pipe.transformer = PeftModel.from_pretrained(pipe.transformer, args.checkpoint, adapter_name="default")
    pipe.enable_model_cpu_offload()
    print(f"  loaded in {time.time()-t0:.0f}s")

    prompt = make_prompt("Kg")
    results = []
    for name in args.fonts:
        for seed in args.seeds:
            out_path = OUT_DIR / f"{name}__{tag}_seed{seed}.png"
            if out_path.exists():
                print(f"SKIP {out_path.name} (exists)")
                continue
            seed_everything(seed)
            print(f"=== {name} / seed {seed} / {args.steps} steps ===", flush=True)
            t1 = time.time()
            try:
                img = pipe(
                    prompt=prompt,
                    image=[refs[name]],
                    height=1280, width=1280,
                    num_inference_steps=args.steps,
                    generator=torch.Generator("cpu").manual_seed(seed),
                ).images[0]
            except Exception as e:
                print(f"  FAILED: {type(e).__name__}: {str(e)[:300]}", flush=True)
                continue
            dt = time.time() - t1
            tmp = out_path.with_suffix(".png.tmp")
            img.save(tmp, format="PNG")
            os.replace(tmp, out_path)
            print(f"  saved {out_path.name}  {dt:.1f}s", flush=True)
            results.append((name, seed, dt))

    print(f"\nRendered {len(results)} atlases to {OUT_DIR}/")
    if results:
        print(f"  mean latency {sum(r[2] for r in results)/len(results):.1f}s")


if __name__ == "__main__":
    main()
