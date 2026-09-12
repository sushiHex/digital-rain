"""Measure cleanup's char-acc lift on the GT-bearing holdout, two ways:

  1. DINOv2 template matching (style-sensitive: is a cell closer to its OWN
     font's GT glyph than to other glyphs of that font).
  2. OCR readability (style-INVARIANT: does the cell read as the expected char).

NeutralPaste repair optimizes (2) but is expected to hurt (1) on stylized fonts
(a clean Arial glyph mismatches the textured GT embedding). Reporting both
disentangles "cleanup fixes readability" from "cleanup preserves style".

Runs FAST-mode cleanup (verify -> NeutralPaste repair of flagged cells) on
already-rendered atlases under --gen-dir ({font}.png), pre vs post.
"""

# repo root on sys.path so `python studies/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image
from atlas_constants import DRAWN_INDICES
from cleanup.cells import crop_cell, paste_cell
from cleanup.verify import verify_atlas
from cleanup.inpaint import NeutralPasteRepairer
from cleanup.types import expected_chars
from cleanup.models import build_trocr_ocr_fn, build_dino_embed_fn
from probe_utils import render_gt_atlas, HARD_FONTS
from analysis.compare_runs import paired_wilcoxon


def char_acc_template(atlas, gt_atlas, embed_fn):
    cells = [crop_cell(atlas, i) for i in DRAWN_INDICES]
    gt_cells = [crop_cell(gt_atlas, i) for i in DRAWN_INDICES]
    e = embed_fn(cells); g = embed_fn(gt_cells)
    e = e / (np.linalg.norm(e, axis=1, keepdims=True) + 1e-9)
    g = g / (np.linalg.norm(g, axis=1, keepdims=True) + 1e-9)
    pred = (e @ g.T).argmax(axis=1)
    return float(np.mean(pred == np.arange(len(DRAWN_INDICES))))


def ocr_char_acc(atlas, ocr_fn, exp):
    hits = sum(1 for i in DRAWN_INDICES if ocr_fn(crop_cell(atlas, i)) == exp[i])
    return hits / len(DRAWN_INDICES)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen-dir", required=True, help="dir of {font}.png generated atlases")
    ap.add_argument("--fonts", nargs="+", default=list(HARD_FONTS))
    args = ap.parse_args()
    ocr_fn = build_trocr_ocr_fn(); embed_fn = build_dino_embed_fn()
    exp = expected_chars(); rep = NeutralPasteRepairer()

    tpl_pre, tpl_post, ocr_pre, ocr_post = [], [], [], []
    print(f"{'font':>26}  {'tpl_pre':>8} {'tpl_post':>8} {'tpl_d':>7}  {'ocr_pre':>8} {'ocr_post':>8} {'ocr_d':>7}  {'fixed':>5}")
    for font in args.fonts:
        p = Path(args.gen_dir) / f"{font}.png"
        if not p.exists():
            print(f"skip {font} (no {p})"); continue
        atlas = np.array(Image.open(p).convert("RGB"))
        gt = np.array(render_gt_atlas(HARD_FONTS[font]))

        tpl_b = char_acc_template(atlas, gt, embed_fn)
        verdicts = verify_atlas(atlas, expected=exp, ocr_fn=ocr_fn, embed_fn=embed_fn)
        ocr_b = float(np.mean([v.ocr_pass for v in verdicts]))  # pre OCR-acc, reuses verify
        n_flagged = sum(1 for v in verdicts if v.flagged)
        for v in verdicts:
            if v.flagged:
                paste_cell(atlas, v.index, rep.repair(crop_cell(atlas, v.index), exp[v.index], atlas))
        tpl_a = char_acc_template(atlas, gt, embed_fn)
        ocr_a = ocr_char_acc(atlas, ocr_fn, exp)

        tpl_pre.append(tpl_b); tpl_post.append(tpl_a)
        ocr_pre.append(ocr_b); ocr_post.append(ocr_a)
        print(f"{font:>26}  {tpl_b:>8.4f} {tpl_a:>8.4f} {tpl_a-tpl_b:>+7.4f}  "
              f"{ocr_b:>8.4f} {ocr_a:>8.4f} {ocr_a-ocr_b:>+7.4f}  {n_flagged:>5}")

    if tpl_pre:
        print(f"\n{'MEAN':>26}  {np.mean(tpl_pre):>8.4f} {np.mean(tpl_post):>8.4f} "
              f"{np.mean(tpl_post)-np.mean(tpl_pre):>+7.4f}  "
              f"{np.mean(ocr_pre):>8.4f} {np.mean(ocr_post):>8.4f} "
              f"{np.mean(ocr_post)-np.mean(ocr_pre):>+7.4f}")
        if len(tpl_pre) >= 10:
            rt = paired_wilcoxon(tpl_pre, tpl_post); ro = paired_wilcoxon(ocr_pre, ocr_post)
            print(f"  template: p={rt.p:.4f} r={rt.effect_r:.3f}   ocr: p={ro.p:.4f} r={ro.effect_r:.3f}")
        else:
            print(f"  (n={len(tpl_pre)} < 10 fonts -> Wilcoxon p not meaningful; per-font deltas above)")
        Path("research").mkdir(exist_ok=True)
        Path("research/2026-05-31-cleanup_eval.json").write_text(json.dumps(
            {"template_pre": tpl_pre, "template_post": tpl_post,
             "ocr_pre": ocr_pre, "ocr_post": ocr_post, "fonts": args.fonts}, indent=2))


if __name__ == "__main__":
    main()
