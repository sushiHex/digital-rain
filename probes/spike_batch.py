"""Spike: batched best-of-N on the INT4+V3 (Route B) path.

Answers three questions for batching seeds in ONE forward (the cheap best-of-N):
  1. CORRECTNESS — does batch>1 corrupt outputs? randn fills row-major, so the
     first sample of a batch-N draw equals a batch-1 draw at the same seed. So
     batch_n.images[0] should ~match the batch-1 render (same seed) — low MAE =
     no cross-batch contamination. Also score every image's OCR (must stay in the
     normal ~0.4 range, not collapse to ~0).
  2. VRAM CEILING — largest batch that fits in 24 GB (OOM-guarded).
  3. SPEED — wall time + s/image at each batch (is batched-N ~ one forward?).

  ./.venv-nunchaku/Scripts/python.exe spike_batch.py --steps 8 --batches 1,2,4,8,16
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
    ap.add_argument("--batches", default="1,2,4,8,16")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    batches = [int(b) for b in args.batches.split(",")]

    pipe = get_int4_v3_pipe()
    ocr_fn = build_trocr_ocr_fn()
    fpath = sorted(glob.glob("eval_holdout/fonts/*.ttf"))[0]
    ref = render_aa_reference(fpath).convert("RGB")
    gt = [render_gt_cell(fpath, EXPECTED[i]) for i in DRAWN]

    def gen_batch(n):
        return pipe(prompt=[V3_PROMPT] * n, image=[ref] * n,
                    height=1280, width=1280, num_inference_steps=args.steps,
                    generator=torch.Generator("cpu").manual_seed(args.seed)).images

    base0 = None
    print(f"font={os.path.basename(fpath)} steps={args.steps} seed={args.seed}\n")
    for n in batches:
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        try:
            t0 = time.time()
            imgs = gen_batch(n)
            dt = time.time() - t0
            peak = torch.cuda.max_memory_allocated() / 1e9
            arrs = [np.asarray(im.convert("RGB")) for im in imgs]
            ocrs = [ocr_acc(a, ocr_fn) for a in arrs]
            if n == 1:
                base0 = arrs[0].astype(np.float32)
                corr = "(baseline)"
            else:
                mae = float(np.abs(arrs[0].astype(np.float32) - base0).mean()) if base0 is not None else -1
                corr = f"img[0] vs batch1 MAE={mae:.1f}/255 {'OK' if mae < 20 else 'CONTAMINATED?'}"
            print(f"  batch={n:2d}  {dt:5.1f}s  {dt/n:5.1f}s/img  peak={peak:4.1f}GB  "
                  f"meanOCR={np.mean(ocrs):.3f}  {corr}", flush=True)
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            print(f"  batch={n:2d}  OOM -> ceiling is below {n}", flush=True)
            break
        except Exception as e:
            print(f"  batch={n:2d}  ERROR {type(e).__name__}: {str(e)[:160]}", flush=True)
            break


if __name__ == "__main__":
    main()
