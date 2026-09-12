"""Homogenization audit for glyph-latent conditioning: does feeding the neutral
(Arial) template collapse generated fonts toward the template skeleton, or do
they keep the target font's structural variety?

Two modes:
  --visual : CPU-only contact sheet. For structurally-distinctive fonts + telling
             chars (a g e R Q 4 &), stack [GT | template | generated] crops so you
             can EYEBALL whether the gen glyph follows the target's structure or
             drifts to Arial. (char-acc/DINOv2 reward readability, not fidelity —
             so the eyeball check is essential.)
  (metric) : GPU DINOv2. Per cell, drift = sim(gen,template) - sim(gen,GT). >0 means
             leaning toward Arial. Plus inter-font diversity ratio (gen spread vs
             GT spread); <1 = collapsed. Run at the post-training eval.

  python audit_diversity.py --gen-dir eval_runs/glyph_cc_2000_full/generated --visual
  python audit_diversity.py --gen-dir eval_runs/<run>/generated            # metric (GPU)
"""
import argparse
import glob
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from atlas_constants import CHARSET
from eval_checkpoint import crop_cell
from build_dataset import render_atlas
from render_glyph_template import render_glyph_template

# structurally telling characters + distinctive holdout fonts
PROBE_CHARS = ["a", "g", "e", "R", "Q", "4", "&"]
DISTINCTIVE = ["BitcountGridDoubleInk", "PlaywriteMXGuides", "RubikDistressed",
               "AveriaSerifLibre", "Dangrek", "AlikeAngular", "FascinateInline"]


def _font_file(name):
    hits = glob.glob(f"eval_holdout/fonts/{name}*.ttf")
    return hits[0] if hits else None


def _cells_for(atlas_np, chars):
    idxs = [CHARSET.index(c) for c in chars if c in CHARSET]
    return [crop_cell(atlas_np, i) for i in idxs]


def visual(gen_dir, fonts):
    tmpl_np = np.asarray(render_glyph_template().convert("RGB"))
    out = Path("audit_diversity"); out.mkdir(exist_ok=True)
    for name in fonts:
        gpath = sorted(glob.glob(f"{gen_dir}/{name}*.png"))
        ff = _font_file(name)
        if not gpath or not ff:
            print(f"skip {name} (gen={bool(gpath)} ttf={bool(ff)})"); continue
        gen_np = np.asarray(Image.open(gpath[0]).convert("RGB"))
        gt_np = np.asarray(render_atlas(ff).convert("RGB"))
        rows = {"GT": _cells_for(gt_np, PROBE_CHARS),
                "template": _cells_for(tmpl_np, PROBE_CHARS),
                "generated": _cells_for(gen_np, PROBE_CHARS)}
        ch = rows["GT"][0].shape[0]; cw = rows["GT"][0].shape[1]
        pad, lblw = 6, 90
        sheet = Image.new("RGB", (lblw + len(PROBE_CHARS) * (cw + pad), 3 * (ch + pad) + 20), (30, 30, 30))
        d = ImageDraw.Draw(sheet)
        for r, (label, cells) in enumerate(rows.items()):
            y = r * (ch + pad) + 10
            d.text((4, y + ch // 2), label, fill=(255, 255, 0))
            for c, cell in enumerate(cells):
                sheet.paste(Image.fromarray(cell), (lblw + c * (cw + pad), y))
        sheet.save(out / f"{name}.png")
        print(f"  saved audit_diversity/{name}.png  (rows: GT | template | generated; cols: {' '.join(PROBE_CHARS)})")


def metric(gen_dir, fonts, embed_fn):
    from atlas_constants import DRAWN_INDICES
    tmpl_cells = [crop_cell(np.asarray(render_glyph_template().convert("RGB")), i) for i in DRAWN_INDICES]
    tmpl_e = _norm(embed_fn(tmpl_cells))
    gen_embeds = {}
    print(f"{'font':24s} target_sim template_sim  drift")
    for name in fonts:
        gpath = sorted(glob.glob(f"{gen_dir}/{name}*.png")); ff = _font_file(name)
        if not gpath or not ff:
            continue
        gen_cells = [crop_cell(np.asarray(Image.open(gpath[0]).convert("RGB")), i) for i in DRAWN_INDICES]
        gt_cells = [crop_cell(np.asarray(render_atlas(ff).convert("RGB")), i) for i in DRAWN_INDICES]
        ge, te = _norm(embed_fn(gen_cells)), _norm(embed_fn(gt_cells))
        gen_embeds[name] = ge.mean(0)
        tgt = float((ge * te).sum(1).mean())
        tpl = float((ge * tmpl_e).sum(1).mean())
        print(f"{name:24s}   {tgt:.3f}      {tpl:.3f}    {tpl-tgt:+.3f}")
    # inter-font diversity: gen spread vs GT spread
    if len(gen_embeds) >= 2:
        names = list(gen_embeds)
        gt_means = {n: _norm(embed_fn([crop_cell(np.asarray(render_atlas(_font_file(n)).convert("RGB")), i)
                                       for i in DRAWN_INDICES])).mean(0) for n in names}
        def spread(m):
            v = _norm(np.stack([m[n] for n in names]))
            return float(np.mean([1 - (v[i] @ v[j]) for i in range(len(v)) for j in range(i + 1, len(v))]))
        print(f"\ninter-font diversity  gen={spread(gen_embeds):.3f}  GT={spread(gt_means):.3f}  "
              f"ratio={spread(gen_embeds)/(spread(gt_means)+1e-9):.2f} (1.0=preserved, <1=collapsed)")


def guard(gen_dir, fonts):
    """Independent-space diversity guard: LPIPS-to-GT + connected-component
    topology penalty, per font, over the distinctive holdout subset.

    Deliberately lives in a DIFFERENT metric space than the DINOv2 objective
    the DPO run optimizes (metric() above) — LPIPS is an AlexNet perceptual
    distance and topology_penalty is ink-density/connected-component based —
    so a diversity collapse that DINOv2-embedding space misses would still
    be caught here, and vice versa. GPU-only (compute_lpips loads an AlexNet
    backbone onto cuda); not exercised by CPU-only tests.

    Returns {font_name: {"lpips_to_gt": float, "mean_topology_penalty": float}}.
    """
    from eval_checkpoint import compute_lpips
    from score_candidates import topology_penalty
    from atlas_constants import DRAWN_INDICES

    rows = {}
    for name in fonts:
        gp = glob.glob(f"{gen_dir}/{name}*.png")
        if not gp:
            continue
        gen = np.array(Image.open(gp[0]).convert("RGB"))
        gt = np.array(render_atlas(_font_file(name)).convert("RGB"))
        gt_cells = [crop_cell(gt, i) for i in DRAWN_INDICES]
        gen_cells = [crop_cell(gen, i) for i in DRAWN_INDICES]
        lp, _ = compute_lpips(gt_cells, gen_cells, "cuda")
        tp = float(np.mean([topology_penalty(g, c) for g, c in zip(gt_cells, gen_cells)]))
        rows[name] = {"lpips_to_gt": float(lp), "mean_topology_penalty": tp}

    for n, r in rows.items():
        print(f"  {n[:22]:22}  lpips={r['lpips_to_gt']:.3f}  topo={r['mean_topology_penalty']:.3f}")

    return rows


def _norm(x):
    x = np.asarray(x, dtype=np.float64)
    return x / (np.linalg.norm(x, axis=-1, keepdims=True) + 1e-9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen-dir", required=True)
    ap.add_argument("--visual", action="store_true", help="CPU contact sheet (no GPU)")
    ap.add_argument("--guard", action="store_true",
                     help="independent-space diversity guard: LPIPS-to-GT + topology penalty (GPU)")
    ap.add_argument("--fonts", default=None, help="comma-sep font names (default: distinctive set)")
    args = ap.parse_args()
    fonts = args.fonts.split(",") if args.fonts else DISTINCTIVE
    if args.visual:
        visual(args.gen_dir, fonts)
    elif args.guard:
        guard(args.gen_dir, fonts)
    else:
        from cleanup.models import build_dino_embed_fn
        metric(args.gen_dir, fonts, build_dino_embed_fn())


if __name__ == "__main__":
    main()
