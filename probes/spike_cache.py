"""Spike: FBCache step-caching on the INT4+V3 (Route B) path — benefit curve.

Measures speed + OCR vs cache-off at 8 and 4 steps across thresholds. FBCache
skips blocks on steps whose first-block residual is stable; benefit scales with
step count, so we expect more at 8 than at 4.

  ./.venv-nunchaku/Scripts/python.exe spike_cache.py
"""

# repo root on sys.path so `python probes/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import glob
import os
import time

os.environ.setdefault("NUNCHAKU_FORCE_UNFUSED_QKV", "1")

import numpy as np

from eval_v3_bestofn import DRAWN, EXPECTED, render_gt_cell, ocr_acc
from cleanup.models import build_trocr_ocr_fn
from run_ref2font_v3_benchmark import render_aa_reference
from nunchaku_v3_lora import get_int4_v3_pipe, build_nunchaku_generate_fn
from misc.route_b_cache import apply_cache_on_flux2_pipe, disable_cache_on_flux2


def main():
    pipe = get_int4_v3_pipe()
    apply_cache_on_flux2_pipe(pipe, residual_diff_threshold=0.12, use_double_fb_cache=True)
    tf = pipe.transformer
    ocr_fn = build_trocr_ocr_fn()
    fpath = sorted(glob.glob("eval_holdout/fonts/*.ttf"))[0]
    ref = render_aa_reference(fpath).convert("RGB")
    gt = [render_gt_cell(fpath, EXPECTED[i]) for i in DRAWN]
    print(f"font={os.path.basename(fpath)}\n", flush=True)

    def timed(gen, seed=42):
        t = time.time()
        atlas = gen(seed)
        return time.time() - t, ocr_acc(atlas, ocr_fn)

    # warm once (model + cuda graphs), cache off
    disable_cache_on_flux2(tf)
    build_nunchaku_generate_fn(ref, steps=8)(999)

    plan = [(8, None), (8, 0.12), (8, 0.25), (8, 0.4), (4, None), (4, 0.25), (4, 0.4)]
    base = {}
    for steps, thr in plan:
        gen = build_nunchaku_generate_fn(ref, steps=steps)
        if thr is None:
            disable_cache_on_flux2(tf)
            dt, ocr = timed(gen)
            base[steps] = dt
            print(f"  steps={steps} cache=OFF        {dt:6.1f}s  OCR={ocr:.3f}", flush=True)
        else:
            tf.residual_diff_threshold_multi = thr
            tf.residual_diff_threshold_single = thr
            tf.use_double_fb_cache = True
            dt, ocr = timed(gen)
            sp = base.get(steps, dt) / dt
            print(f"  steps={steps} thr={thr:<4}      {dt:6.1f}s  ({sp:.2f}x)  OCR={ocr:.3f}", flush=True)


if __name__ == "__main__":
    main()
