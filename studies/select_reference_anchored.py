"""Reference-anchored no-GT selection: use the glyphs the USER supplies.

Every no-GT selector tried so far ignored the one piece of genuine
ground truth available at inference time. The pipeline is handed a
reference image containing 2 glyphs (the holdout's `reference_chars`,
"Kg") rendered in the *target* style. Those are real GT for 2 of the 95
cells -- in the actual target style, present at generation time, no leak.

Prior selectors and their capture of the best-of-4 gap:
  TrOCR                       4.3%
  GOT-OCR2                    4.7%
  DINOv2 medoid (studies/score_self_consistency.py)  14.1%

All three are unanchored proxies. Medoid in particular is *mode-seeking*
-- "most typical of N candidates" -- which biases toward canonical
letterforms, the wrong direction for exactly the distinctive faces the
4B is weakest on (Fascinate Inline, Bitcount). Anchoring on the supplied
reference has no such bias.

Two selectors are evaluated:

  ref-anchor (per-cell)  each cell independently picks the candidate whose
                         DINOv2 embedding is closest to the font's reference
                         style anchor. Competes with the per-cell oracle.
  ref-best-seed (font)   score each seed by how well ITS K and g cells match
                         the reference's K and g like-for-like, then use that
                         one seed for the whole atlas. Lower ceiling, but the
                         resulting font is guaranteed style-consistent because
                         every glyph comes from one sampling trajectory.

GT is used ONLY to score how well a selection did (via char_acc_match
already in scores.json), never inside the selection itself.

  python studies/select_reference_anchored.py --candidates-dir bestofn_4b/candidates \
      --scores bestofn_4b/scores.json --references eval_holdout/references
"""

# repo root on sys.path so `python studies/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from PIL import Image

INK = 128  # atlas and reference are both white-on-black; ink is the bright side
LAMBDAS = (0.25, 0.5, 1.0, 2.0)  # weight of the per-seed reference prior in the hybrid


def _z(v):
    """Z-score; returns zeros when every value is identical (no signal)."""
    v = np.asarray(v, dtype=float)
    sd = v.std()
    return (v - v.mean()) / sd if sd > 1e-9 else np.zeros_like(v)


def load_scores(scores_path):
    """(font, char) -> {seed_int: bool char_acc_match}."""
    from candidate_gen import parse_candidate_key

    by_cell = defaultdict(dict)
    for key, cells in json.load(open(scores_path)).items():
        font, _model, seed_i = parse_candidate_key(key)
        for c in cells:
            by_cell[(font, c["char"])][seed_i] = bool(c["char_acc_match"])
    return by_cell


def tight_crop(arr):
    """Crop to the ink bounding box; return unchanged if the tile is blank."""
    ink = arr.max(axis=2) > INK if arr.ndim == 3 else arr > INK
    rows, cols = np.where(ink.any(1))[0], np.where(ink.any(0))[0]
    if not len(rows) or not len(cols):
        return arr
    return arr[rows.min():rows.max() + 1, cols.min():cols.max() + 1]


def split_reference(ref_path, n_chars):
    """Split the reference canvas into n_chars vertical bands, tight-cropped.

    The reference is a single square canvas with the reference characters
    laid out left to right (see eval_holdout/references/*.png), so an even
    vertical split separates them before the per-glyph tight crop.
    """
    arr = np.array(Image.open(ref_path).convert("RGB"))
    w = arr.shape[1] // n_chars
    return [tight_crop(arr[:, i * w:(i + 1) * w]) for i in range(n_chars)]


class Embedder:
    """DINOv2 CLS embeddings, L2-normalized, using eval_checkpoint's model."""

    def __init__(self, device):
        from eval_checkpoint import _DINOV2_CACHE, DINOV2_MODEL_ID
        from transformers import AutoImageProcessor, AutoModel

        key = str(device)
        if key not in _DINOV2_CACHE:
            _DINOV2_CACHE[key] = (
                AutoImageProcessor.from_pretrained(DINOV2_MODEL_ID),
                AutoModel.from_pretrained(DINOV2_MODEL_ID).to(device).eval(),
            )
        self.processor, self.model = _DINOV2_CACHE[key]
        self.device = device

    @torch.no_grad()
    def __call__(self, arrays, batch=32):
        out = []
        for i in range(0, len(arrays), batch):
            imgs = [Image.fromarray(a) for a in arrays[i:i + batch]]
            inputs = self.processor(images=imgs, return_tensors="pt").to(self.device)
            feats = self.model(**inputs).last_hidden_state[:, 0]
            out.append(torch.nn.functional.normalize(feats, dim=-1).cpu())
        return torch.cat(out)


def embed_font(embedder, cand_dir, font, ref_path, ref_chars, n_seeds):
    """Returns (cell_embeds, ref_embeds, cropped_embeds), or (None, None, None).

    cell_embeds  {(char, seed): tensor}  native cell geometry, for typicality
    ref_embeds   {char: tensor}          the supplied reference glyphs
    cropped_embeds {(char, seed): tensor} tight-cropped reference chars only,
                                         the only space comparable to ref_embeds
    """
    from eval_checkpoint import crop_cell
    from atlas_constants import CHARSET, DRAWN_INDICES

    atlases = {}
    for seed_i in range(n_seeds):
        p = Path(cand_dir) / font / f"glyph__seed{seed_i}.png"
        if p.exists():
            atlases[seed_i] = np.array(Image.open(p).convert("RGB"))
    if len(atlases) < 2 or not Path(ref_path).exists():
        return None, None, None

    # Typicality is computed on cells in their NATIVE cell geometry. Do not
    # tight-crop here: it normalizes away size and placement, which are part of
    # the quality signal. Measured -- tight-cropping collapses the medoid
    # selector from 14.1% capture to 1.2% on the same 4,700 cells.
    keys, crops = [], []
    for idx in DRAWN_INDICES:
        for seed_i, atlas in atlases.items():
            keys.append((CHARSET[idx], seed_i))
            crops.append(crop_cell(atlas, idx))
    cell_embeds = dict(zip(keys, embedder(crops)))

    # The reference glyph and an atlas cell have different framing, so the
    # like-for-like reference match gets its OWN tight-cropped embedding space.
    # Only the reference characters need it (2 chars x n_seeds per font).
    ref_keys, ref_cell_crops = [], []
    for ch in ref_chars:
        if ch not in CHARSET:
            continue
        idx = CHARSET.index(ch)
        for seed_i, atlas in atlases.items():
            ref_keys.append((ch, seed_i))
            ref_cell_crops.append(tight_crop(crop_cell(atlas, idx)))
    cropped_embeds = dict(zip(ref_keys, embedder(ref_cell_crops)))

    ref_crops = split_reference(ref_path, len(ref_chars))
    ref_embeds = dict(zip(ref_chars, embedder(ref_crops)))
    return cell_embeds, ref_embeds, cropped_embeds


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates-dir", default="bestofn_4b/candidates")
    ap.add_argument("--scores", default="bestofn_4b/scores.json")
    ap.add_argument("--references", default="eval_holdout/references")
    ap.add_argument("--ref-chars", default=None,
                    help="Defaults to the holdout manifest's reference_chars.")
    ap.add_argument("--manifest", default="eval_holdout/manifest.json")
    ap.add_argument("--seeds", type=int, default=4)
    ap.add_argument("--limit", type=int, default=None, help="Only the first N fonts (smoke test).")
    ap.add_argument("--out", default=None, help="Optional JSON summary path.")
    args = ap.parse_args(argv)

    ref_chars = args.ref_chars or json.load(open(args.manifest))["reference_chars"]
    device = "cuda" if torch.cuda.is_available() else "cpu"

    by_cell = load_scores(args.scores)
    fonts = sorted({f for f, _ in by_cell})
    if args.limit:
        fonts = fonts[:args.limit]
        by_cell = {k: v for k, v in by_cell.items() if k[0] in set(fonts)}
    print(f"reference_chars={ref_chars!r}  fonts={len(fonts)}  device={device}")

    embedder = Embedder(device)
    # name -> per-cell hit list, so every selector is scored on the same cells
    hits = defaultdict(list)
    per_font = {}

    for n, font in enumerate(fonts, 1):
        cells, refs, cropped = embed_font(embedder, args.candidates_dir, font,
                                          Path(args.references) / f"{font}.png",
                                          ref_chars, args.seeds)
        if cells is None:
            print(f"  [{n}/{len(fonts)}] {font}: SKIP (missing candidates or reference)")
            continue

        anchor = torch.nn.functional.normalize(
            torch.stack([refs[c] for c in ref_chars]).mean(0), dim=-1)

        # Per-seed reference fit: like-for-like K vs K, g vs g, both tight-cropped.
        seed_ids = sorted({s for _, s in cells})
        seed_fit = {
            s: float(np.mean([float(cropped[(c, s)] @ refs[c])
                              for c in ref_chars if (c, s) in cropped] or [0.0]))
            for s in seed_ids
        }
        best_seed = max(seed_fit, key=seed_fit.get)
        seed_fit_z = dict(zip(seed_ids, _z([seed_fit[s] for s in seed_ids])))

        font_hits = defaultdict(list)
        scored_cells = []
        for (fnt, ch), per_seed in by_cell.items():
            if fnt != font:
                continue
            avail = [s for s in per_seed if (ch, s) in cells]
            if len(avail) < 2:
                continue
            emb = torch.stack([cells[(ch, s)] for s in avail])

            font_hits["seed0"].append(bool(per_seed.get(0, False)))
            font_hits["oracle_cell"].append(any(per_seed[s] for s in avail))

            sim = emb @ emb.T
            typicality = (sim.sum(1) - 1.0) / (len(avail) - 1)
            medoid = avail[int(typicality.argmax())]
            font_hits["medoid"].append(bool(per_seed[medoid]))

            ref_pick = avail[int((emb @ anchor).argmax())]
            font_hits["ref_anchor_cell"].append(bool(per_seed[ref_pick]))

            # Hybrid: medoid is a per-CELL signal, reference fit is a per-SEED
            # prior. Both are weak alone; z-scoring each puts them on a common
            # scale so lam trades local typicality against global style match.
            tz = _z(typicality.numpy())
            fz = np.array([seed_fit_z[s] for s in avail])
            for lam in LAMBDAS:
                pick = avail[int(np.argmax(tz + lam * fz))]
                font_hits[f"hybrid_lam{lam}"].append(bool(per_seed[pick]))

            font_hits["ref_best_seed"].append(bool(per_seed.get(best_seed, False)))
            scored_cells.append((ch, avail))

        # Font-level oracle: the single seed correct on the most cells. Counted
        # over exactly the cells the selectors were scored on, so the ceiling and
        # the selectors share a denominator.
        seed_totals = defaultdict(int)
        for ch, avail in scored_cells:
            for s in avail:
                seed_totals[s] += bool(by_cell[(font, ch)][s])
        n_cells = len(scored_cells)
        best_n = max(seed_totals.values()) if seed_totals else 0
        font_hits["oracle_seed"] = [True] * best_n + [False] * (n_cells - best_n)
        for k, v in font_hits.items():
            hits[k].extend(v)
        per_font[font] = {k: float(np.mean(v)) for k, v in font_hits.items()}
        per_font[font]["picked_seed"] = best_seed
        print(f"  [{n}/{len(fonts)}] {font}: seed0={per_font[font]['seed0']:.3f} "
              f"ref_cell={per_font[font]['ref_anchor_cell']:.3f} "
              f"ref_seed={per_font[font]['ref_best_seed']:.3f} "
              f"oracle={per_font[font]['oracle_cell']:.3f}", flush=True)

    if not hits:
        print("no fonts scored -- check --candidates-dir / --scores")
        return

    agg = {k: float(np.mean(v)) for k, v in hits.items()}
    base, oracle = agg["seed0"], agg["oracle_cell"]

    def capture(name, ceiling):
        return (agg[name] - base) / max(ceiling - base, 1e-9)

    print(f"\ncells analyzed: {len(hits['seed0'])}   fonts: {len(per_font)}")
    print(f"  seed-0 only (no selection)            {base:.4f}")
    print(f"  DINOv2 medoid       (no-GT)           {agg['medoid']:.4f}"
          f"   capture {capture('medoid', oracle):6.1%}")
    print(f"  ref-anchor per-cell (no-GT, x-space)  {agg['ref_anchor_cell']:.4f}"
          f"   capture {capture('ref_anchor_cell', oracle):6.1%}  [diagnostic:"
          " compares padded cells to a tight-cropped anchor]")
    for lam in LAMBDAS:
        k = f"hybrid_lam{lam}"
        print(f"  hybrid medoid+ref lam={lam:<4}(no-GT)     {agg[k]:.4f}"
              f"   capture {capture(k, oracle):6.1%}")
    print(f"  ref-best-seed       (no-GT, font)     {agg['ref_best_seed']:.4f}"
          f"   capture {capture('ref_best_seed', agg['oracle_seed']):6.1%} of font-level oracle")
    print("  --- ceilings (use GT to pick) ---")
    print(f"  best single seed per font             {agg['oracle_seed']:.4f}")
    print(f"  per-cell best-of-N oracle             {oracle:.4f}")

    if args.out:
        json.dump({"aggregate": agg, "per_font": per_font},
                  open(args.out, "w"), indent=2)
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
