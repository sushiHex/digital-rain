"""Confirm consensus_best_of_n vs best_of_n on the REAL config: INT4+V3, 8 seeds,
8 steps. Saves the generated atlases (experiments/select_atlases/) so future
selector experiments re-score without regenerating.

  ./.venv-nunchaku/Scripts/python.exe spike_select_confirm.py --n 3 --seeds 8 --steps 8
"""

# repo root on sys.path so `python probes/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import os
from pathlib import Path

os.environ.setdefault("NUNCHAKU_FORCE_UNFUSED_QKV", "1")

import numpy as np
from PIL import Image

from eval_v3_bestofn import DRAWN, EXPECTED, render_gt_cell, ocr_acc, template_acc, best_of_n
from cleanup.models import build_trocr_ocr_fn, build_dino_embed_fn
from run_ref2font_v3_benchmark import render_aa_reference
from nunchaku_v3_lora import build_nunchaku_generate_fn
from v3_select import consensus_best_of_n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--fonts-dir", default="eval_holdout/fonts")
    args = ap.parse_args()

    ocr_fn = build_trocr_ocr_fn()
    embed_fn = build_dino_embed_fn()
    out = Path("experiments/select_atlases"); out.mkdir(parents=True, exist_ok=True)
    fonts = sorted(glob.glob(f"{args.fonts_dir}/*.ttf"))[: args.n]

    import torch
    rows = []
    for fpath in fonts:
        fname = os.path.basename(fpath).split("[")[0].split("-")[0]
        paths = [out / f"{fname}_s{s}.png" for s in range(args.seeds)]
        if all(p.exists() for p in paths):  # resume: reuse saved atlases
            atlases = [np.asarray(Image.open(p).convert("RGB")) for p in paths]
        else:
            gen = build_nunchaku_generate_fn(render_aa_reference(fpath).convert("RGB"), steps=args.steps)
            atlases = []
            for s in range(args.seeds):
                a = gen(42 + s)
                Image.fromarray(a).save(paths[s])
                atlases.append(a)
            torch.cuda.empty_cache()
        gt = [render_gt_cell(fpath, EXPECTED[i]) for i in DRAWN]
        b = best_of_n(atlases, ocr_fn)
        c = consensus_best_of_n(atlases, ocr_fn, embed_fn)
        bo, bt = ocr_acc(b, ocr_fn), template_acc(b, gt, embed_fn)
        co, ct = ocr_acc(c, ocr_fn), template_acc(c, gt, embed_fn)
        rows.append((bo, bt, co, ct))
        print(f"  {fname:22s} best_of_n OCR={bo:.3f} TPL={bt:.3f} | consensus OCR={co:.3f} TPL={ct:.3f}", flush=True)

    m = np.array(rows).mean(axis=0)
    print(f"\n=== MEAN ({len(rows)} fonts, {args.seeds} seeds, {args.steps} steps) ===")
    print(f"  best_of_n   OCR={m[0]:.3f}  TEMPL={m[1]:.3f}")
    print(f"  consensus   OCR={m[2]:.3f}  TEMPL={m[3]:.3f}")
    print(f"  delta       OCR={m[2]-m[0]:+.3f}  TEMPL={m[3]-m[1]:+.3f}")


if __name__ == "__main__":
    main()
