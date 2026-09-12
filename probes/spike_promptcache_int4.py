"""Spike: prompt-embed caching on the INT4+V3 (Route B) path.

Our prompt is FIXED, so encode it ONCE and pass prompt_embeds= to every render.
With cpu-offload the text-encoder hook only fires on text_encoder.forward, which
never runs when prompt_embeds is supplied -> the 24B encoder loads exactly once,
and per-render cost drops to diffusion + vae only.

Measures, in one process: (a) one UNCACHED render (prompt=V3_PROMPT, encodes
every call) = today's path, vs (b) CACHED renders (prompt_embeds=cached). Reports
total, s/step, peak VRAM. Also sanity-scores OCR so caching didn't break output.

  ./.venv-nunchaku/Scripts/python.exe spike_promptcache_int4.py --steps 8
"""

# repo root on sys.path so `python probes/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import os
import time

os.environ.setdefault("NUNCHAKU_FORCE_UNFUSED_QKV", "1")

import numpy as np
import torch

from eval_v3_bestofn import DRAWN, EXPECTED, render_gt_cell, ocr_acc
from cleanup.models import build_trocr_ocr_fn
from run_ref2font_v3_benchmark import render_aa_reference
from nunchaku_v3_lora import get_int4_v3_pipe, V3_PROMPT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--runs", type=int, default=2)
    args = ap.parse_args()

    pipe = get_int4_v3_pipe()
    ocr_fn = build_trocr_ocr_fn()
    fpath = sorted(glob.glob("eval_holdout/fonts/*.ttf"))[0]
    ref = render_aa_reference(fpath).convert("RGB")
    gt = [render_gt_cell(fpath, EXPECTED[i]) for i in DRAWN]
    print(f"font={os.path.basename(fpath)} steps={args.steps}\n", flush=True)

    def score(img):
        return ocr_acc(np.asarray(img.convert("RGB")), ocr_fn)

    # (a) UNCACHED — encodes the prompt every call (today's path)
    torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    img = pipe(prompt=V3_PROMPT, image=ref, height=1280, width=1280,
               num_inference_steps=args.steps,
               generator=torch.Generator("cpu").manual_seed(42)).images[0]
    dt_uncached = time.time() - t0
    print(f"  UNCACHED   {dt_uncached:6.1f}s  (~{dt_uncached/args.steps:.1f}s/step)  "
          f"peak={torch.cuda.max_memory_allocated()/1e9:.1f}GB  OCR={score(img):.3f}", flush=True)

    # Encode the fixed prompt ONCE
    t1 = time.time()
    enc = pipe.encode_prompt(V3_PROMPT, device="cuda")
    prompt_embeds = (enc[0] if isinstance(enc, (tuple, list)) else enc).to("cuda")
    print(f"  encode-once {time.time()-t1:5.1f}s  embeds={tuple(prompt_embeds.shape)}", flush=True)

    # (b) CACHED — pass prompt_embeds, encoder never runs
    times = []
    for r in range(args.runs):
        torch.cuda.reset_peak_memory_stats()
        t2 = time.time()
        img = pipe(prompt_embeds=prompt_embeds, image=ref, height=1280, width=1280,
                   num_inference_steps=args.steps,
                   generator=torch.Generator("cpu").manual_seed(42 + r)).images[0]
        dt = time.time() - t2
        times.append(dt)
        print(f"  CACHED #{r+1}  {dt:6.1f}s  (~{dt/args.steps:.1f}s/step)  "
              f"peak={torch.cuda.max_memory_allocated()/1e9:.1f}GB  OCR={score(img):.3f}", flush=True)

    best = min(times)
    print(f"\n=== RESULT ===")
    print(f"  uncached:      {dt_uncached:.1f}s")
    print(f"  cached (best): {best:.1f}s   speedup {dt_uncached/best:.2f}x")
    print(f"  per-extra-seed cost (best-of-N marginal): ~{best:.0f}s")


if __name__ == "__main__":
    main()
