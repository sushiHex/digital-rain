"""Spike 2 re-score with DINOv2 template matching (style-invariant), the same
metric as our composite's char-acc -- more trustworthy than TrOCR on stylized
glyphs. Re-scores the already-rendered atlases in experiments/spike2_seeds/;
no new generation.

A gen cell "matches" if its DINOv2 embedding is closer to its OWN font's GT
glyph than to any other glyph in that font (robust to style). Then we compute
best-of-N lift and the systematic-failure fraction.
"""

# repo root on sys.path so `python probes/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from atlas_constants import CHARSET, DRAWN_INDICES
from eval_checkpoint import DINOV2_MODEL_ID, crop_cell
from probe_utils import HARD_FONTS, render_gt_atlas

SEEDS_DIR = Path("experiments/spike2_seeds")
DINO_BATCH = 64


def embed_drawn_cells(atlas_rgb_np, processor, model, device):
    """Return L2-normalized DINOv2 CLS embeddings for every drawn cell."""
    cells = [Image.fromarray(crop_cell(atlas_rgb_np, idx)) for idx in DRAWN_INDICES]
    feats = []
    with torch.no_grad():
        for i in range(0, len(cells), DINO_BATCH):
            batch = cells[i:i + DINO_BATCH]
            inputs = processor(images=batch, return_tensors="pt").to(device)
            out = model(**inputs).last_hidden_state[:, 0]
            feats.append(out.cpu())
    emb = torch.cat(feats, dim=0)
    return torch.nn.functional.normalize(emb, dim=-1)


def main():
    pngs = sorted(SEEDS_DIR.glob("*__*_seed*.png"))
    if not pngs:
        print(f"No atlases in {SEEDS_DIR}/ -- run spike2_seeds.py first.")
        return

    by_font = defaultdict(dict)  # font -> {seed: path}
    for p in pngs:
        font, rest = p.stem.split("__", 1)
        _tag, seedpart = rest.rsplit("_seed", 1)
        by_font[font][int(seedpart)] = p

    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import AutoImageProcessor, AutoModel
    print(f"Loading DINOv2 ({DINOV2_MODEL_ID}) on {device}...")
    processor = AutoImageProcessor.from_pretrained(DINOV2_MODEL_ID)
    model = AutoModel.from_pretrained(DINOV2_MODEL_ID).to(device).eval()

    n_drawn = len(DRAWN_INDICES)
    report = {}
    for font, seed_paths in sorted(by_font.items()):
        if font not in HARD_FONTS:
            print(f"  skip {font}: not in HARD_FONTS")
            continue
        gt_atlas = np.array(render_gt_atlas(HARD_FONTS[font]))  # RGB
        gt_emb = embed_drawn_cells(gt_atlas, processor, model, device)  # (n, D) normalized

        seeds = sorted(seed_paths)
        pass_matrix = {}
        for seed in seeds:
            gen_atlas = np.array(Image.open(seed_paths[seed]).convert("RGB"))
            gen_emb = embed_drawn_cells(gen_atlas, processor, model, device)
            sim = gen_emb @ gt_emb.T            # (n gen, n gt)
            pred = sim.argmax(dim=1).tolist()
            passes = {DRAWN_INDICES[i]: int(pred[i] == i) for i in range(n_drawn)}
            pass_matrix[seed] = passes
            acc = np.mean(list(passes.values()))
            print(f"  {font:>26} seed {seed}: char-acc(template) {acc:.4f}")

        per_seed_acc = [np.mean(list(pass_matrix[s].values())) for s in seeds]
        best_of_n = np.mean([
            int(any(pass_matrix[s][idx] for s in seeds)) for idx in DRAWN_INDICES
        ])
        ever_fail = [idx for idx in DRAWN_INDICES if any(pass_matrix[s][idx] == 0 for s in seeds)]
        always_fail = [idx for idx in ever_fail if all(pass_matrix[s][idx] == 0 for s in seeds)]
        systematic_frac = (len(always_fail) / len(ever_fail)) if ever_fail else 0.0

        report[font] = {
            "n_seeds": len(seeds),
            "mean_single_seed": float(np.mean(per_seed_acc)),
            "best_of_n_char_acc": float(best_of_n),
            "best_of_n_lift": float(best_of_n - np.mean(per_seed_acc)),
            "n_ever_fail": len(ever_fail),
            "n_always_fail": len(always_fail),
            "systematic_fraction": float(systematic_frac),
        }

    print()
    print("=" * 92)
    print("CROSS-SEED FAILURE ANALYSIS (DINOv2 template matching)")
    print("=" * 92)
    print(f"{'font':>26} {'mean_1seed':>11} {'best_of_N':>10} {'lift':>8} "
          f"{'ever_fail':>10} {'always_fail':>12} {'systematic%':>12}")
    print("-" * 92)
    for font, r in report.items():
        print(f"{font:>26} {r['mean_single_seed']:>11.4f} {r['best_of_n_char_acc']:>10.4f} "
              f"{r['best_of_n_lift']:>+8.4f} {r['n_ever_fail']:>10} {r['n_always_fail']:>12} "
              f"{r['systematic_fraction']*100:>11.1f}%")

    agg_sys = float(np.mean([r["systematic_fraction"] for r in report.values()]))
    agg_lift = float(np.mean([r["best_of_n_lift"] for r in report.values()]))
    agg_best = float(np.mean([r["best_of_n_char_acc"] for r in report.values()]))
    print()
    print("=" * 92)
    print("VERDICT (template matching)")
    print("=" * 92)
    print(f"Mean single-seed char-acc:            {np.mean([r['mean_single_seed'] for r in report.values()]):.4f}")
    print(f"Mean best-of-N char-acc:              {agg_best:.4f}")
    print(f"Mean best-of-N lift:                  {agg_lift:+.4f}")
    print(f"Mean systematic-failure fraction:     {agg_sys*100:.1f}%")
    print()
    if agg_sys < 0.4:
        print("-> FAILURES LARGELY SEED-INDEPENDENT. Best-of-N recovers most errors.")
    elif agg_sys < 0.7:
        print("-> MIXED. Best-of-N helps; systematic residue needs reference-guided inpaint.")
    else:
        print("-> SYSTEMATIC. Best-of-N stalls; need reference-guided inpaint / generator work.")
    print("(NOTE: measured on the 3 HARDEST holdout fonts -- systematic fraction is a")
    print(" worst-case upper bound; typical fonts will be far more best-of-N-recoverable.)")

    out = Path("research/2026-05-31-crossseed_correlation_template.json")
    out.write_text(json.dumps({"per_font": report,
                                "mean_systematic_fraction": agg_sys,
                                "mean_best_of_n_lift": agg_lift,
                                "mean_best_of_n_char_acc": agg_best}, indent=2))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
