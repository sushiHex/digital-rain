"""QUALITY-mode cleanup eval: measure best-of-N's lift THROUGH the pipeline.

Spike 2 measured best-of-N at the cell level (+0.13-0.15). This runs the actual
`select_best_cells` over the N seed atlases we already rendered
(experiments/spike2_seeds/{font}__*_seed*.png), then verify + repair, and reports
char-acc at three stages so we can see where the lift comes from:

  single-seed (baseline)  ->  best-of-N  ->  best-of-N + repair

Both metrics: DINOv2 template (style-sensitive, the trusted quality metric) and
OCR readability (style-invariant). No new generation — reuses existing seeds.

Usage:
  python studies/eval_cleanup_quality.py --seeds-dir experiments/spike2_seeds \
      --fonts RubikDistressed BitcountGridDoubleInk PlaywriteMXGuides
"""

# repo root on sys.path so `python studies/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import json
from pathlib import Path

import numpy as np
from PIL import Image

from atlas_constants import DRAWN_INDICES
from cleanup.cells import crop_cell, paste_cell
from cleanup.ensemble import select_best_cells
from cleanup.verify import verify_atlas
from cleanup.inpaint import NeutralPasteRepairer
from cleanup.types import expected_chars
from cleanup.models import build_trocr_ocr_fn, build_dino_embed_fn
from probe_utils import render_gt_atlas, HARD_FONTS
from studies.eval_cleanup import char_acc_template, ocr_char_acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds-dir", default="experiments/spike2_seeds")
    ap.add_argument("--fonts", nargs="+",
                    default=["RubikDistressed", "BitcountGridDoubleInk", "PlaywriteMXGuides"])
    args = ap.parse_args()

    ocr_fn = build_trocr_ocr_fn()
    embed_fn = build_dino_embed_fn()
    exp = expected_chars()
    rep = NeutralPasteRepairer()

    rows = []
    hdr = (f"{'font':>26} | {'tpl: 1seed':>10} {'bestN':>8} {'+repair':>8} | "
           f"{'ocr: 1seed':>10} {'bestN':>8} {'+repair':>8}")
    print(hdr)
    print("-" * len(hdr))
    for font in args.fonts:
        paths = sorted(glob.glob(f"{args.seeds_dir}/{font}__*_seed*.png"))
        if len(paths) < 2:
            print(f"skip {font} (<2 seeds in {args.seeds_dir})")
            continue
        atlases = [np.array(Image.open(p).convert("RGB")) for p in paths]
        gt = np.array(render_gt_atlas(HARD_FONTS[font]))

        # stage 1: single seed
        tpl_1 = char_acc_template(atlases[0], gt, embed_fn)
        ocr_1 = ocr_char_acc(atlases[0], ocr_fn, exp)

        # stage 2: best-of-N composite
        best = select_best_cells(atlases, expected=exp, ocr_fn=ocr_fn)
        tpl_n = char_acc_template(best, gt, embed_fn)
        ocr_n = ocr_char_acc(best, ocr_fn, exp)

        # stage 3: + verify/repair the residual
        verdicts = verify_atlas(best, expected=exp, ocr_fn=ocr_fn, embed_fn=embed_fn)
        for v in verdicts:
            if v.flagged:
                paste_cell(best, v.index, rep.repair(crop_cell(best, v.index), exp[v.index], best))
        tpl_r = char_acc_template(best, gt, embed_fn)
        ocr_r = ocr_char_acc(best, ocr_fn, exp)

        rows.append({"font": font, "n_seeds": len(atlases),
                     "tpl": [tpl_1, tpl_n, tpl_r], "ocr": [ocr_1, ocr_n, ocr_r]})
        print(f"{font:>26} | {tpl_1:>10.4f} {tpl_n:>8.4f} {tpl_r:>8.4f} | "
              f"{ocr_1:>10.4f} {ocr_n:>8.4f} {ocr_r:>8.4f}")

    if rows:
        def col(metric, k): return float(np.mean([r[metric][k] for r in rows]))
        print("-" * len(hdr))
        print(f"{'MEAN':>26} | {col('tpl',0):>10.4f} {col('tpl',1):>8.4f} {col('tpl',2):>8.4f} | "
              f"{col('ocr',0):>10.4f} {col('ocr',1):>8.4f} {col('ocr',2):>8.4f}")
        print(f"\nbest-of-N lift (template): {col('tpl',1)-col('tpl',0):+.4f}   "
              f"(ocr): {col('ocr',1)-col('ocr',0):+.4f}")
        print(f"repair delta on top      (template): {col('tpl',2)-col('tpl',1):+.4f}   "
              f"(ocr): {col('ocr',2)-col('ocr',1):+.4f}")
        Path("research").mkdir(exist_ok=True)
        Path("research/2026-06-01-cleanup_quality_eval.json").write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
