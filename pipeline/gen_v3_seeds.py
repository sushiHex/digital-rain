"""Generate V3 best-of-N seed atlases on distilled klein-9B for the hard fonts.

V3 is the better generator (beats our structured-5000 LoRA). Distilled klein-9B
at 4 steps (~120s/render) is the practical choice — base-9B is ~57s/step (clean
benchmark), and V3 survives 4-step distillation with grids intact (Spike 1).
Saves experiments/v3_seeds/{font}__v3_seed{seed}.png for the V3-layout eval.
"""

# repo root on sys.path so `python pipeline/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import os
import time
from pathlib import Path

import torch

from probe_utils import HARD_FONTS
from run_ref2font_v3_benchmark import render_aa_reference
from probes.spike1_distilled import load_pipeline, V3_PROMPT

OUT = Path("experiments/v3_seeds")
FONTS = ["RubikDistressed", "BitcountGridDoubleInk", "PlaywriteMXGuides"]
SEEDS = [42, 43, 44, 45]
MODEL = "black-forest-labs/FLUX.2-klein-9B"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    refs = {f: render_aa_reference(HARD_FONTS[f]).convert("RGB") for f in FONTS}
    pipe = load_pipeline(MODEL)
    total = len(FONTS) * len(SEEDS)
    done = 0
    for font in FONTS:
        for seed in SEEDS:
            done += 1
            out = OUT / f"{font}__v3_seed{seed}.png"
            if out.exists():
                print(f"[{done}/{total}] SKIP {out.name}", flush=True)
                continue
            print(f"[{done}/{total}] {font} seed {seed}", flush=True)
            t0 = time.time()
            try:
                img = pipe(prompt=V3_PROMPT, image=refs[font],
                           height=1280, width=1280, num_inference_steps=4,
                           generator=torch.Generator().manual_seed(seed)).images[0]
            except Exception as e:
                print(f"  FAILED: {type(e).__name__}: {str(e)[:200]}", flush=True)
                continue
            tmp = out.with_suffix(".png.tmp")
            img.save(tmp, format="PNG"); os.replace(tmp, out)
            print(f"  saved {out.name}  {time.time()-t0:.0f}s", flush=True)
    print(f"\nDone. V3 seed atlases in {OUT}/")


if __name__ == "__main__":
    main()
