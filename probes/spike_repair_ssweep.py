"""Is the SDEdit-repair negative result an s-tuning artifact? Sweep s on one font."""

# repo root on sys.path so `python probes/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import glob, os
os.environ.setdefault("NUNCHAKU_FORCE_UNFUSED_QKV", "1")
import numpy as np
from PIL import Image
from eval_v3_bestofn import DRAWN, EXPECTED, render_gt_cell, ocr_acc, template_acc
from cleanup.models import build_trocr_ocr_fn, build_dino_embed_fn
from run_ref2font_v3_benchmark import render_aa_reference
from nunchaku_v3_lora import get_int4_v3_pipe, _cached_prompt_embeds
from v3_select import consensus_best_of_n, verify_and_repair_v3
from studies.repair_sdedit import repair_atlas_sdedit

TTF = {os.path.basename(p).split("[")[0].split("-")[0]: p for p in glob.glob("eval_holdout/fonts/*.ttf")}
pipe = get_int4_v3_pipe(); embeds = _cached_prompt_embeds(pipe)
ocr_fn = build_trocr_ocr_fn(); embed_fn = build_dino_embed_fn()

fname = "AkayaTelivigala"
atlases = [np.asarray(Image.open(p).convert("RGB")) for p in sorted(glob.glob(f"experiments/select_atlases/{fname}_s*.png"))]
gt = [render_gt_cell(TTF[fname], EXPECTED[i]) for i in DRAWN]
ref = render_aa_reference(TTF[fname]).convert("RGB")
cons = consensus_best_of_n(atlases, ocr_fn, embed_fn)
_, broken = verify_and_repair_v3(cons, ocr_fn, embed_fn)
co, ct = ocr_acc(cons, ocr_fn), template_acc(cons, gt, embed_fn)
print(f"{fname}: consensus OCR={co:.3f} TPL={ct:.3f}  ({len(broken)} broken)", flush=True)
for s in (0.5, 0.6, 0.9):
    a = repair_atlas_sdedit(pipe, embeds, ref, cons, broken, s=s)
    print(f"  s={s}: OCR={ocr_acc(a, ocr_fn):.3f} TPL={template_acc(a, gt, embed_fn):.3f}", flush=True)
