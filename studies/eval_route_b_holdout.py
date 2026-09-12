"""Broader Route B quality eval: INT4 + V3 on N holdout fonts, single-seed vs
best-of-N (dual metric). Nails INT4+V3's absolute quality + the best-of-N lift
on a representative set (not just the hardest fonts).

  ./.venv-nunchaku/Scripts/python.exe eval_route_b_holdout.py --n 10 --seeds 4 --steps 8
"""

# repo root on sys.path so `python studies/x.py` works as well as `-m`
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
from nunchaku_v3_lora import get_int4_v3_pipe, build_nunchaku_generate_fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--seeds", type=int, default=4)
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--fonts-dir", default="eval_holdout/fonts")
    args = ap.parse_args()

    get_int4_v3_pipe()  # loads the INT4 pipe + applies V3 (once)
    ocr_fn = build_trocr_ocr_fn()
    embed_fn = build_dino_embed_fn()
    fonts = sorted(glob.glob(f"{args.fonts_dir}/*.ttf"))[: args.n]

    rows = []
    for fpath in fonts:
        fname = os.path.basename(fpath).split("[")[0].split("-")[0]
        ref = render_aa_reference(fpath).convert("RGB")          # rendered once per font
        gen = build_nunchaku_generate_fn(ref, steps=args.steps)
        atlases = [gen(42 + s) for s in range(args.seeds)]
        gt = [render_gt_cell(fpath, EXPECTED[i]) for i in DRAWN]
        o1, t1 = ocr_acc(atlases[0], ocr_fn), template_acc(atlases[0], gt, embed_fn)
        bo = best_of_n(atlases, ocr_fn)
        oN, tN = ocr_acc(bo, ocr_fn), template_acc(bo, gt, embed_fn)
        rows.append((fname, o1, t1, oN, tN))
        print(f"  {fname:24s} single OCR={o1:.3f} TPL={t1:.3f} | best{args.seeds} OCR={oN:.3f} TPL={tN:.3f}", flush=True)

    arr = np.array([[r[1], r[2], r[3], r[4]] for r in rows])
    m = arr.mean(axis=0)
    print(f"\n=== SUMMARY ({len(rows)} fonts, {args.seeds} seeds, {args.steps} steps) ===")
    print(f"  single-seed  OCR={m[0]:.3f} TEMPL={m[1]:.3f}")
    print(f"  best-of-{args.seeds}   OCR={m[2]:.3f} TEMPL={m[3]:.3f}")
    print(f"  best-of-N lift  OCR={m[2]-m[0]:+.3f} TEMPL={m[3]-m[1]:+.3f}")


if __name__ == "__main__":
    main()
