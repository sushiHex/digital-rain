"""Test the NeutralPaste repair stage on the SAVED 8-seed atlases (no generation):
consensus vs consensus + verify_and_repair_v3. Reports OCR/TEMPL + #cells repaired."""

# repo root on sys.path so `python misc/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import glob
import os
import numpy as np
from PIL import Image

from eval_v3_bestofn import DRAWN, EXPECTED, render_gt_cell, ocr_acc, template_acc
from cleanup.models import build_trocr_ocr_fn, build_dino_embed_fn
from v3_select import consensus_best_of_n, verify_and_repair_v3

# font name -> ttf path (from the holdout)
TTF = {os.path.basename(p).split("[")[0].split("-")[0]: p
       for p in glob.glob("eval_holdout/fonts/*.ttf")}

ocr_fn = build_trocr_ocr_fn()
embed_fn = build_dino_embed_fn()

adir = "experiments/select_atlases"
fonts = sorted({os.path.basename(p).rsplit("_s", 1)[0] for p in glob.glob(f"{adir}/*_s*.png")})
rows = []
for fname in fonts:
    paths = sorted(glob.glob(f"{adir}/{fname}_s*.png"))
    if len(paths) < 4 or fname not in TTF:
        print(f"skip {fname} ({len(paths)} atlases)"); continue
    atlases = [np.asarray(Image.open(p).convert("RGB")) for p in paths]
    gt = [render_gt_cell(TTF[fname], EXPECTED[i]) for i in DRAWN]
    cons = consensus_best_of_n(atlases, ocr_fn, embed_fn)
    rep, flagged = verify_and_repair_v3(cons, ocr_fn, embed_fn)
    co, ct = ocr_acc(cons, ocr_fn), template_acc(cons, gt, embed_fn)
    ro, rt = ocr_acc(rep, ocr_fn), template_acc(rep, gt, embed_fn)
    rows.append((co, ct, ro, rt, len(flagged)))
    print(f"  {fname:22s} consensus OCR={co:.3f} TPL={ct:.3f} | +repair OCR={ro:.3f} TPL={rt:.3f}  (repaired {len(flagged)})", flush=True)

a = np.array([r[:4] for r in rows])
m = a.mean(axis=0)
print(f"\n=== MEAN ({len(rows)} fonts) ===")
print(f"  consensus      OCR={m[0]:.3f}  TEMPL={m[1]:.3f}")
print(f"  consensus+rep  OCR={m[2]:.3f}  TEMPL={m[3]:.3f}")
print(f"  delta          OCR={m[2]-m[0]:+.3f}  TEMPL={m[3]-m[1]:+.3f}   (avg {np.mean([r[4] for r in rows]):.1f} cells/font repaired)")
