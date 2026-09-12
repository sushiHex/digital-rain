"""Consensus-aware best-of-N cell selection (V3 geometry).

`best_of_n` (eval_v3_bestofn) picks, per cell, the OCR-correct candidate with the
highest generic sharpness score (score_glyph_cell) — which ignores STYLE, so at
high N it can favour readable-but-style-drifted cells (TEMPL drops).

`consensus_best_of_n` instead picks, among the OCR-correct candidates, the one
closest to that cell's cross-seed CENTROID (the "typical" rendering). The correct
on-style glyph recurs across seeds; garbled / style-drifted versions are outliers
far from the centroid, so the medoid is the consensus on-style rendering. Keeps
the OCR gain while preserving style. Inference-time, no GT needed.
"""
import numpy as np

from eval_v3_bestofn import DRAWN, EXPECTED, v3_crop, _COLS, _CELL, _OX, _OY
from cleanup.glyph_guide import render_neutral_glyph


def consensus_best_of_n(atlases, ocr_fn, embed_fn):
    base = atlases[0].copy()
    cands = {idx: [v3_crop(a, idx) for a in atlases] for idx in DRAWN}
    oks = {idx: [ocr_fn(c) == EXPECTED[idx] for c in cands[idx]] for idx in DRAWN}

    # Embed every candidate of every cell in ONE batched call, then slice.
    flat, spans = [], {}
    for idx in DRAWN:
        spans[idx] = (len(flat), len(flat) + len(cands[idx]))
        flat.extend(cands[idx])
    embs = embed_fn(flat)
    embs = embs / (np.linalg.norm(embs, axis=1, keepdims=True) + 1e-9)

    for idx in DRAWN:
        s, e = spans[idx]
        emb = embs[s:e]
        pool = [i for i, ok in enumerate(oks[idx]) if ok] or list(range(len(cands[idx])))
        if len(pool) == 1:
            pick = pool[0]
        else:
            pe = emb[pool]
            centroid = pe.mean(axis=0, keepdims=True)
            centroid = centroid / (np.linalg.norm(centroid) + 1e-9)
            sims = (pe @ centroid.T).ravel()  # cosine sim to consensus centroid
            pick = pool[int(sims.argmax())]   # medoid = most typical on-style
        best = cands[idx][pick]
        r, c = idx // _COLS, idx % _COLS
        y0, x0 = _OY + r * _CELL, _OX + c * _CELL
        base[y0:y0 + _CELL, x0:x0 + _CELL] = best
    return base


def _paste(atlas, idx, patch):
    r, c = idx // _COLS, idx % _COLS
    y0, x0 = _OY + r * _CELL, _OX + c * _CELL
    atlas[y0:y0 + _CELL, x0:x0 + _CELL] = patch


def verify_and_repair_v3(atlas, ocr_fn, embed_fn, z_thresh: float = 3.0):
    """Final cleanup stage (V3 geometry): for cells that BOTH fail OCR and are
    MAD-z style/shape outliers (z>=thresh) — the systematic-failure cells that
    best-of-N/consensus can't fix — paste the correct char in a neutral font.
    Recovers readability (and usually the GT char-shape) on broken cells; the
    AND-guard keeps it off correct-but-stylized cells. Returns (atlas, flagged)."""
    cells = [v3_crop(atlas, i) for i in DRAWN]
    embs = np.asarray(embed_fn(cells), dtype=np.float64)
    centroid = np.median(embs, axis=0)
    dists = np.linalg.norm(embs - centroid, axis=1)
    med = np.median(dists)
    mad = np.median(np.abs(dists - med)) + 1e-9
    z = (dists - med) / mad
    out = atlas.copy()
    flagged = []
    for k, idx in enumerate(DRAWN):
        if ocr_fn(cells[k]) != EXPECTED[idx] and z[k] >= z_thresh:
            _paste(out, idx, render_neutral_glyph(EXPECTED[idx], size=(_CELL, _CELL)))
            flagged.append(idx)
    return out, flagged
