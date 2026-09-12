"""Cheap selector tuning on SAVED 8-seed atlases (no generation). Compares
consensus-selector variants to squeeze more quality from the same samples:

  V0 medoid      : among OCR-correct, max cosine-sim to mean(OCR-correct embeds)  [current]
  V1 all-centroid: centroid = mean of ALL candidates; pick OCR-correct max-sim
  V2 trimmed     : centroid = mean of OCR-correct minus the farthest; max-sim
  V3 hybrid      : among OCR-correct, max( sim_to_centroid + 0.5*z(sharpness) )

  ./.venv-nunchaku/Scripts/python.exe spike_selector_variants.py
"""

# repo root on sys.path so `python probes/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import glob
import os
import numpy as np
from PIL import Image

from eval_v3_bestofn import DRAWN, EXPECTED, v3_crop, _COLS, _CELL, _OX, _OY, render_gt_cell, ocr_acc, template_acc
from cleanup.models import build_trocr_ocr_fn, build_dino_embed_fn
from generate_atlas import score_glyph_cell

TTF = {os.path.basename(p).split("[")[0].split("-")[0]: p for p in glob.glob("eval_holdout/fonts/*.ttf")}
ocr_fn = build_trocr_ocr_fn()
embed_fn = build_dino_embed_fn()


def _paste(atlas, idx, patch):
    r, c = idx // _COLS, idx % _COLS
    atlas[_OY + r * _CELL:_OY + r * _CELL + _CELL, _OX + c * _CELL:_OX + c * _CELL + _CELL] = patch


def select(atlases, variant):
    base = atlases[0].copy()
    cands = {i: [v3_crop(a, i) for a in atlases] for i in DRAWN}
    oks = {i: [ocr_fn(c) == EXPECTED[i] for c in cands[i]] for i in DRAWN}
    flat, spans = [], {}
    for i in DRAWN:
        spans[i] = (len(flat), len(flat) + len(cands[i])); flat.extend(cands[i])
    E = embed_fn(flat); E = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-9)
    for i in DRAWN:
        s, e = spans[i]; emb = E[s:e]
        pool = [j for j, ok in enumerate(oks[i]) if ok] or list(range(len(cands[i])))
        if len(pool) == 1:
            pick = pool[0]
        else:
            pe = emb[pool]
            if variant == "all-centroid":
                ctr = emb.mean(0, keepdims=True)
            elif variant == "trimmed":
                c0 = pe.mean(0, keepdims=True)
                d = (pe @ (c0 / (np.linalg.norm(c0) + 1e-9)).T).ravel()
                keep = np.argsort(-d)[:max(1, len(pool) - 1)]
                ctr = pe[keep].mean(0, keepdims=True)
            else:
                ctr = pe.mean(0, keepdims=True)
            ctr = ctr / (np.linalg.norm(ctr) + 1e-9)
            sims = (pe @ ctr.T).ravel()
            if variant == "hybrid":
                sh = np.array([score_glyph_cell(Image.fromarray(cands[i][j])) for j in pool], dtype=np.float64)
                sh = (sh - sh.mean()) / (sh.std() + 1e-9)
                score = sims + 0.5 * sh
            else:
                score = sims
            pick = pool[int(score.argmax())]
        _paste(base, i, cands[i][pick])
    return base


adir = "experiments/select_atlases"
fonts = sorted({os.path.basename(p).rsplit("_s", 1)[0] for p in glob.glob(f"{adir}/*_s*.png")})
variants = ["medoid", "all-centroid", "trimmed", "hybrid"]
agg = {v: [] for v in variants}
for fname in fonts:
    paths = sorted(glob.glob(f"{adir}/{fname}_s*.png"))
    if len(paths) < 4 or fname not in TTF:
        continue
    atlases = [np.asarray(Image.open(p).convert("RGB")) for p in paths]
    gt = [render_gt_cell(TTF[fname], EXPECTED[i]) for i in DRAWN]
    line = f"  {fname:20s}"
    for v in variants:
        a = select(atlases, v)
        o, t = ocr_acc(a, ocr_fn), template_acc(a, gt, embed_fn)
        agg[v].append((o, t)); line += f"  {v}:{o:.3f}/{t:.3f}"
    print(line, flush=True)

print(f"\n=== MEAN ({len(agg['medoid'])} fonts) — OCR / TEMPL ===")
for v in variants:
    m = np.array(agg[v]).mean(0)
    print(f"  {v:14s} OCR={m[0]:.3f}  TEMPL={m[1]:.3f}")
