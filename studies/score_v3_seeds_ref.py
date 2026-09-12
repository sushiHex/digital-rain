"""Score the existing bf16+V3 reference atlases (experiments/v3_seeds/*_seed42.png)
with the SAME metric as eval_route_b, to compare against INT4+V3 (Route B)."""

# repo root on sys.path so `python studies/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import glob
import numpy as np
from PIL import Image

from eval_v3_bestofn import DRAWN, EXPECTED, render_gt_cell, ocr_acc, template_acc
from cleanup.models import build_trocr_ocr_fn, build_dino_embed_fn
from probe_utils import HARD_FONTS

ocr_fn = build_trocr_ocr_fn()
embed_fn = build_dino_embed_fn()

seeds = {
    "BitcountGridDoubleInk": "experiments/v3_seeds/BitcountGridDoubleInk__v3_seed42.png",
    "PlaywriteMXGuides": "experiments/v3_seeds/PlaywriteMXGuides__v3_seed42.png",
    "RubikDistressed": "experiments/v3_seeds/RubikDistressed__v3_seed42.png",
}
print("bf16+V3 reference (4 steps, seed42) scored with eval_route_b metric:")
os, ts = [], []
for fname, png in seeds.items():
    fpath = HARD_FONTS[fname]
    atlas = np.asarray(Image.open(png).convert("RGB"))
    gt = [render_gt_cell(fpath, EXPECTED[i]) for i in DRAWN]
    o, t = ocr_acc(atlas, ocr_fn), template_acc(atlas, gt, embed_fn)
    os.append(o); ts.append(t)
    print(f"  {fname:24s} OCR={o:.3f} TEMPL={t:.3f}")
print(f"\n  bf16+V3 MEAN  OCR={np.mean(os):.3f} TEMPL={np.mean(ts):.3f}")
print("  (compare to INT4+V3 Route B: same fonts)")
