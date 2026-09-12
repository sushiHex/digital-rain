"""Cheap validation of consensus_best_of_n vs best_of_n on the SAVED v3_seeds
atlases (3 fonts x 4 seeds) — no generation, just re-scoring with both selectors.
If consensus holds OCR and recovers TEMPL, it's the strict-win selector."""

# repo root on sys.path so `python studies/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import glob
import numpy as np
from PIL import Image

from eval_v3_bestofn import DRAWN, EXPECTED, render_gt_cell, ocr_acc, template_acc, best_of_n
from cleanup.models import build_trocr_ocr_fn, build_dino_embed_fn
from probe_utils import HARD_FONTS
from v3_select import consensus_best_of_n

ocr_fn = build_trocr_ocr_fn()
embed_fn = build_dino_embed_fn()

seeds_dir = "experiments/v3_seeds"
fonts = ["BitcountGridDoubleInk", "PlaywriteMXGuides", "RubikDistressed"]
rows = []
for fname in fonts:
    paths = sorted(glob.glob(f"{seeds_dir}/{fname}__*seed*.png"))
    if len(paths) < 2:
        print(f"skip {fname} ({len(paths)} seeds)"); continue
    atlases = [np.asarray(Image.open(p).convert("RGB")) for p in paths]
    gt = [render_gt_cell(HARD_FONTS[fname], EXPECTED[i]) for i in DRAWN]
    b = best_of_n(atlases, ocr_fn)
    c = consensus_best_of_n(atlases, ocr_fn, embed_fn)
    bo, bt = ocr_acc(b, ocr_fn), template_acc(b, gt, embed_fn)
    co, ct = ocr_acc(c, ocr_fn), template_acc(c, gt, embed_fn)
    rows.append((bo, bt, co, ct))
    print(f"  {fname:24s} best_of_n OCR={bo:.3f} TPL={bt:.3f} | consensus OCR={co:.3f} TPL={ct:.3f}", flush=True)

a = np.array(rows)
m = a.mean(axis=0)
print(f"\n=== MEAN ({len(rows)} fonts, {len(atlases)} seeds) ===")
print(f"  best_of_n   OCR={m[0]:.3f}  TEMPL={m[1]:.3f}")
print(f"  consensus   OCR={m[2]:.3f}  TEMPL={m[3]:.3f}")
print(f"  delta       OCR={m[2]-m[0]:+.3f}  TEMPL={m[3]-m[1]:+.3f}")
