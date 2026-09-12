"""Compare repair strategies on saved 8-seed atlases (consensus base):
  consensus  |  + NeutralPaste repair  |  + SDEdit style-preserving repair.
Reports OCR + TEMPL for each, and #cells repaired.

  ./.venv-nunchaku/Scripts/python.exe test_sdedit_repair.py --s 0.75
"""

# repo root on sys.path so `python misc/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import os

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--s", type=float, default=0.75)
    args = ap.parse_args()

    pipe = get_int4_v3_pipe()
    embeds = _cached_prompt_embeds(pipe)
    ocr_fn = build_trocr_ocr_fn()
    embed_fn = build_dino_embed_fn()

    adir = "experiments/select_atlases"
    fonts = sorted({os.path.basename(p).rsplit("_s", 1)[0] for p in glob.glob(f"{adir}/*_s*.png")})
    rows = []
    for fname in fonts:
        paths = sorted(glob.glob(f"{adir}/{fname}_s*.png"))
        if len(paths) < 4 or fname not in TTF:
            continue
        atlases = [np.asarray(Image.open(p).convert("RGB")) for p in paths]
        gt = [render_gt_cell(TTF[fname], EXPECTED[i]) for i in DRAWN]
        ref = render_aa_reference(TTF[fname]).convert("RGB")

        cons = consensus_best_of_n(atlases, ocr_fn, embed_fn)
        neu, broken = verify_and_repair_v3(cons, ocr_fn, embed_fn)
        sde = repair_atlas_sdedit(pipe, embeds, ref, cons, broken, s=args.s)

        def sc(a):
            return ocr_acc(a, ocr_fn), template_acc(a, gt, embed_fn)
        co, ct = sc(cons); no, nt = sc(neu); so, st = sc(sde)
        rows.append((co, ct, no, nt, so, st, len(broken)))
        print(f"  {fname:20s} cons {co:.3f}/{ct:.3f} | neutral {no:.3f}/{nt:.3f} | "
              f"sdedit {so:.3f}/{st:.3f}  ({len(broken)} cells)", flush=True)

    a = np.array([r[:6] for r in rows])
    m = a.mean(axis=0)
    print(f"\n=== MEAN ({len(rows)} fonts, s={args.s}) — OCR / TEMPL ===")
    print(f"  consensus        {m[0]:.3f} / {m[1]:.3f}")
    print(f"  + NeutralPaste   {m[2]:.3f} / {m[3]:.3f}")
    print(f"  + SDEdit repair  {m[4]:.3f} / {m[5]:.3f}")
    print(f"  SDEdit vs consensus  OCR {m[4]-m[0]:+.3f}  TEMPL {m[5]-m[1]:+.3f}")
    print(f"  SDEdit vs neutral    OCR {m[4]-m[2]:+.3f}  TEMPL {m[5]-m[3]:+.3f}")


if __name__ == "__main__":
    main()
