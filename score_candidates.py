"""Texture-aware GT scoring for generated glyph candidates.

Scores every candidate cell against its ground-truth cell with a composite
that combines DINOv2 cosine similarity (macro style), LPIPS (perceptual
distance), and a topology penalty that specifically punishes candidates that
smooth away GT texture (e.g. a dot-grid or distressed GT rendered as a solid
blob) -- a failure mode DINOv2/LPIPS alone do not reliably catch.

composite: dino_cos - lam*lpips - mu*topo_pen   (higher is better)

CLI: walks dpo_data/candidates/<font>/<model>__seed<seed>.png (the layout
candidate_gen.py writes), scores each candidate against its font's GT atlas,
and merges the per-cell results into dpo_data/scores.json keyed by
candidate_key -- idempotent append-merge: a candidate whose key is already
present is skipped, not re-scored or overwritten.

Usage:
  # Training-set candidates (dataset_v2/atlases/<font>.png is GT)
  python score_candidates.py --candidates-dir dpo_data/candidates \
      --gt-atlas-dir dataset_v2/atlases --out dpo_data/scores.json

  # Gate -1 holdout candidates (eval_holdout/atlases/<font>.png is GT)
  python score_candidates.py --candidates-dir dpo_data/candidates \
      --gt-atlas-dir eval_holdout/atlases --out dpo_data/scores.json
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

from candidate_gen import candidate_key

# Candidate filenames are "<model>__seed<seed>.png" (candidate_gen.candidate_path).
_CANDIDATE_FILENAME_RE = re.compile(r"^(?P<model>.+)__seed(?P<seed>\d+)\.png$")


def _ink_density(cell):
    """Fraction of pixels above the mid-gray threshold. In [0, 1]."""
    g = cell if cell.ndim == 2 else cell[..., 0]
    return float((g > 127).mean())


def _num_components(cell):
    """Count 4-connected foreground (ink) components via scipy.ndimage.label."""
    from scipy import ndimage
    g = cell if cell.ndim == 2 else cell[..., 0]
    _, n = ndimage.label(g > 127)
    return int(n)


def topology_penalty(gt_cell, cand_cell):
    """0.5*|delta ink_density| + 0.5*|delta connected_components| (normalized).

    Both terms are in [0, 1], so the penalty is in [0, 1].

    Design intent: a smoothed/solid candidate must be penalized MORE than a
    faithful-texture candidate when GT is textured (e.g. a dot-grid or
    distressed glyph). Collapsing many small ink components into one solid
    blob is exactly the failure mode this catches, including cases where ink
    density alone wouldn't flag it.
    """
    dg = abs(_ink_density(gt_cell) - _ink_density(cand_cell))            # in [0,1]
    cc_gt, cc_cd = _num_components(gt_cell), _num_components(cand_cell)
    dc = abs(cc_gt - cc_cd) / max(cc_gt, cc_cd, 1)                        # in [0,1]
    return 0.5 * dg + 0.5 * dc


def cell_score(dino_cos, lpips, topo_pen, lam, mu):
    """Composite per-cell quality score, higher is better."""
    return dino_cos - lam * lpips - mu * topo_pen


def score_font(gt_atlas, cand_atlas, device, lam=0.5, mu=0.5):
    """Score one candidate atlas against its GT atlas, per drawn cell.

    Reuses eval_checkpoint's GPU-backed metrics (DINOv2 cosine similarity,
    LPIPS, and the DINOv2-template char_acc match) so scoring stays
    consistent with the rest of the eval pipeline. The candidate atlas is
    treated as a single "font" spanning all drawn cells for
    compute_char_acc's per-font argmax matching, so char_acc_match becomes a
    per-cell argmax-against-own-GT match rather than an aggregate.

    Not exercised on GPU here (none available in this environment); correct
    by construction against eval_checkpoint's documented return shapes.
    """
    from eval_checkpoint import compute_dinov2, compute_char_acc, compute_lpips, crop_cell
    from atlas_constants import CHARSET, DRAWN_INDICES

    gt_cells = [crop_cell(gt_atlas, i) for i in DRAWN_INDICES]
    cd_cells = [crop_cell(cand_atlas, i) for i in DRAWN_INDICES]

    _, dino_sims, gt_emb, cd_emb = compute_dinov2(gt_cells, cd_cells, device)
    _, char_match = compute_char_acc(gt_emb, cd_emb, [("f", 0, len(gt_cells))])
    _, lpips_scores = compute_lpips(gt_cells, cd_cells, device)

    out = []
    for k, i in enumerate(DRAWN_INDICES):
        tp = topology_penalty(gt_cells[k], cd_cells[k])
        out.append({
            "char": CHARSET[i],
            "char_acc_match": bool(char_match[k]),
            "dino_cos": float(dino_sims[k]),
            "lpips": float(lpips_scores[k]),
            "topo_pen": float(tp),
            "score": cell_score(float(dino_sims[k]), float(lpips_scores[k]), tp, lam, mu),
        })
    return out


# ==============================================================================
# CLI: score every candidate under --candidates-dir against its font's GT
# atlas, merging into --out (idempotent -- keys already present are skipped).
# ==============================================================================

def _load_atlas(path):
    return np.array(Image.open(path).convert("RGB"))


def _iter_candidates(candidates_dir):
    """Yield (font, model, seed, png_path) for every candidate PNG on disk.

    Mirrors candidate_gen.candidate_path's layout:
    <candidates_dir>/<font>/<model>__seed<seed>.png
    """
    root = Path(candidates_dir)
    if not root.exists():
        return
    for font_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for png_path in sorted(font_dir.glob("*.png")):
            m = _CANDIDATE_FILENAME_RE.match(png_path.name)
            if not m:
                continue
            yield font_dir.name, m.group("model"), int(m.group("seed")), png_path


def load_scores(out_path):
    """Load an existing scores.json (empty dict if it doesn't exist yet)."""
    p = Path(out_path)
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


CHECKPOINT_EVERY = 10  # flush scores.json every N newly-scored candidates


def _atomic_write_scores(scores, out_path):
    """Write scores.json atomically (tmp + os.replace) so a crash mid-write
    can't leave a truncated file that the resume path would then load."""
    import os
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2)
    os.replace(tmp, out)


def score_all(candidates_dir, gt_atlas_dir, out_path, device, lam=0.5, mu=0.5):
    """Score every not-yet-scored candidate and merge into out_path.

    Idempotent: a candidate whose candidate_key is already a key in the
    existing scores.json is skipped (not re-scored, not overwritten). Returns
    the number of newly scored candidates.
    """
    scores = load_scores(out_path)
    gt_atlas_cache = {}
    n_scored = 0

    for font, model, seed, cand_path in _iter_candidates(candidates_dir):
        key = candidate_key(font, model, seed)
        if key in scores:
            continue

        gt_path = Path(gt_atlas_dir) / f"{font}.png"
        if not gt_path.exists():
            print(f"  SKIP {key}: no GT atlas at {gt_path}")
            continue

        if font not in gt_atlas_cache:
            gt_atlas_cache[font] = _load_atlas(gt_path)
        gt_atlas = gt_atlas_cache[font]
        cand_atlas = _load_atlas(cand_path)
        if cand_atlas.shape != gt_atlas.shape:
            cand_atlas = np.array(
                Image.fromarray(cand_atlas).resize(
                    (gt_atlas.shape[1], gt_atlas.shape[0]), Image.LANCZOS
                )
            )

        cells = score_font(gt_atlas, cand_atlas, device, lam=lam, mu=mu)
        # NOTE: scores[key] is the bare list of per-cell dicts, NOT a
        # {"font"/"model"/"seed"/"cells"} wrapper -- both consumers
        # (measure_oracle_ceiling.py, select_preferences.py) do `for r in rows`
        # over this value and re-derive font/model/seed from `key` via
        # `key.rsplit("__", 2)`. A wrapper dict here would make `for r in rows`
        # iterate the wrapper's string KEYS instead of cell dicts, raising
        # TypeError at `r["char"]` in every downstream consumer.
        scores[key] = cells
        n_scored += 1
        print(f"  scored {key} ({len(cells)} cells)", flush=True)

        # Incremental checkpoint: writing only at the end means a crash/wedge
        # mid-run loses EVERY scored candidate (the load_scores() resume above
        # can only skip what actually reached disk). Flush periodically so a
        # relaunch resumes near where it stopped.
        if n_scored % CHECKPOINT_EVERY == 0:
            _atomic_write_scores(scores, out_path)

    _atomic_write_scores(scores, out_path)
    return n_scored


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates-dir", default="dpo_data/candidates",
                         help="Root dir of candidate_gen.py output (<font>/<model>__seed<seed>.png)")
    parser.add_argument("--gt-atlas-dir", required=True,
                         help="GT atlas dir: dataset_v2/atlases for training, eval_holdout/atlases for Gate -1")
    parser.add_argument("--out", default="dpo_data/scores.json", help="Output scores.json (merged, idempotent)")
    parser.add_argument("--lam", type=float, default=0.5, help="LPIPS weight in cell_score")
    parser.add_argument("--mu", type=float, default=0.5, help="Topology-penalty weight in cell_score")
    parser.add_argument("--device", default=None, help="Override device (default: cuda if available else cpu)")
    args = parser.parse_args(argv)

    device = args.device
    if device is None:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"

    n_scored = score_all(args.candidates_dir, args.gt_atlas_dir, args.out, device, lam=args.lam, mu=args.mu)
    print(f"\nScored {n_scored} new candidates. Merged results: {args.out}")


if __name__ == "__main__":
    main()
