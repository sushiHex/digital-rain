"""Spike: best-of-N quality curve at 8 steps (QUALITY config) — does N>4 climb?

Generates N seeds per font, reports best-of-{1,2,4,8} (prefixes) OCR + TEMPL.
Shows where best-of-N plateaus, which bounds how much the systematic-failure
cells (the repair lever) still need to cover.

  ./.venv-nunchaku/Scripts/python.exe spike_bestofn.py --n 4 --seeds 8 --steps 8
"""

# repo root on sys.path so `python probes/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import os

os.environ.setdefault("NUNCHAKU_FORCE_UNFUSED_QKV", "1")

import numpy as np

from eval_v3_bestofn import DRAWN, EXPECTED, render_gt_cell, ocr_acc, template_acc, best_of_n
from cleanup.models import build_trocr_ocr_fn, build_dino_embed_fn
from run_ref2font_v3_benchmark import render_aa_reference
from nunchaku_v3_lora import build_nunchaku_generate_fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--fonts-dir", default="eval_holdout/fonts")
    args = ap.parse_args()
    Ns = [k for k in (1, 2, 4, 8, 16) if k <= args.seeds]

    ocr_fn = build_trocr_ocr_fn()
    embed_fn = build_dino_embed_fn()
    fonts = sorted(glob.glob(f"{args.fonts_dir}/*.ttf"))[: args.n]

    rows = []  # (font, {N: (ocr, tpl)})
    for fpath in fonts:
        fname = os.path.basename(fpath).split("[")[0].split("-")[0]
        gen = build_nunchaku_generate_fn(render_aa_reference(fpath).convert("RGB"), steps=args.steps)
        atlases = [gen(42 + s) for s in range(args.seeds)]
        gt = [render_gt_cell(fpath, EXPECTED[i]) for i in DRAWN]
        per_n = {}
        for k in Ns:
            bo = best_of_n(atlases[:k], ocr_fn)
            per_n[k] = (ocr_acc(bo, ocr_fn), template_acc(bo, gt, embed_fn))
        rows.append((fname, per_n))
        print(f"  {fname:22s} " + "  ".join(f"N{k}:{per_n[k][0]:.3f}/{per_n[k][1]:.3f}" for k in Ns), flush=True)

    print(f"\n=== MEAN over {len(rows)} fonts (steps={args.steps}) — OCR / TEMPL ===")
    for k in Ns:
        mo = np.mean([r[1][k][0] for r in rows])
        mt = np.mean([r[1][k][1] for r in rows])
        print(f"  best-of-{k:<2}  OCR={mo:.3f}  TEMPL={mt:.3f}")


if __name__ == "__main__":
    main()
