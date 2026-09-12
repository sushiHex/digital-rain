"""Can a NO-GT heuristic capture the +0.1483 same-model best-of-4 headroom
found on the holdout? Tests self-consistency selection: for each cell, embed
all 4 candidate crops with DINOv2, pick the "medoid" (highest mean similarity
to the other 3 -- the most-typical, least-outlier candidate) as the no-GT
pick, with NO reference to ground truth in the selection itself. GT is used
only to SCORE how well this did (via char_acc_match already in scores.json),
which is standard offline evaluation, not a leak into the selection.
"""

# repo root on sys.path so `python studies/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from PIL import Image

CANDIDATES_DIR = "dpo_holdout_bestofn/candidates"
SCORES_PATH = "dpo_holdout_bestofn/scores.json"


def load_scores():
    from candidate_gen import parse_candidate_key
    s = json.load(open(SCORES_PATH))
    # (font, char) -> {seed_int: char_acc_match}
    by_cell = defaultdict(dict)
    for key, cells in s.items():
        font, model, seed_i = parse_candidate_key(key)
        for c in cells:
            by_cell[(font, c["char"])][seed_i] = bool(c["char_acc_match"])
    return by_cell


def embed_all_candidates(fonts, n_seeds, device):
    """Returns {(font, char): {seed_i: embedding tensor}}"""
    from eval_checkpoint import crop_cell, _DINOV2_CACHE, DINOV2_MODEL_ID
    from atlas_constants import CHARSET, DRAWN_INDICES
    from transformers import AutoImageProcessor, AutoModel

    _k = str(device)
    if _k not in _DINOV2_CACHE:
        _DINOV2_CACHE[_k] = (
            AutoImageProcessor.from_pretrained(DINOV2_MODEL_ID),
            AutoModel.from_pretrained(DINOV2_MODEL_ID).to(device).eval(),
        )
    processor, model = _DINOV2_CACHE[_k]

    out = defaultdict(dict)
    BATCH = 32
    with torch.no_grad():
        for font in fonts:
            atlases = {}
            for seed_i in range(n_seeds):
                p = Path(CANDIDATES_DIR) / font / f"glyph__seed{seed_i}.png"
                if not p.exists():
                    continue
                atlases[seed_i] = np.array(Image.open(p).convert("RGB"))
            if len(atlases) < 2:
                continue

            # gather all (char, seed_i, crop) triples for this font, batch-embed
            items = []
            for idx in DRAWN_INDICES:
                ch = CHARSET[idx]
                for seed_i, atlas in atlases.items():
                    items.append((ch, seed_i, crop_cell(atlas, idx)))

            for i in range(0, len(items), BATCH):
                batch = items[i:i + BATCH]
                imgs = [Image.fromarray(c) for _, _, c in batch]
                inputs = processor(images=imgs, return_tensors="pt").to(device)
                feats = model(**inputs).last_hidden_state[:, 0]
                feats = torch.nn.functional.normalize(feats, dim=-1).cpu()
                for (ch, seed_i, _), feat in zip(batch, feats):
                    out[(font, ch)][seed_i] = feat
    return out


def medoid_pick(embeds_by_seed):
    """Highest mean cosine similarity to the other candidates."""
    seeds = list(embeds_by_seed.keys())
    if len(seeds) == 1:
        return seeds[0]
    mat = torch.stack([embeds_by_seed[s] for s in seeds])  # (N, D)
    sim = mat @ mat.T  # (N, N) cosine (already normalized)
    mean_sim_to_others = (sim.sum(dim=1) - 1.0) / (len(seeds) - 1)
    return seeds[int(mean_sim_to_others.argmax())]


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    by_cell = load_scores()
    fonts = sorted({f for f, _ in by_cell})
    print(f"embedding candidates for {len(fonts)} fonts...")
    embeds = embed_all_candidates(fonts, n_seeds=4, device=device)

    n_total = n_any_ok = n_medoid_ok = n_seed0_ok = 0
    for (font, ch), per_seed in by_cell.items():
        if (font, ch) not in embeds or len(embeds[(font, ch)]) < 2:
            continue
        n_total += 1
        any_ok = any(per_seed.values())
        n_any_ok += any_ok
        pick = medoid_pick(embeds[(font, ch)])
        n_medoid_ok += bool(per_seed.get(pick, False))
        n_seed0_ok += bool(per_seed.get(0, False))

    print(f"\ncells analyzed: {n_total}")
    print(f"  always-seed0 (naive, no selection):        {n_seed0_ok/n_total:.4f}")
    print(f"  self-consistency medoid pick (no-GT):       {n_medoid_ok/n_total:.4f}")
    print(f"  best-of-4 oracle ceiling (uses GT to pick):  {n_any_ok/n_total:.4f}")
    capture = (n_medoid_ok - n_seed0_ok) / max(n_any_ok - n_seed0_ok, 1e-9)
    print(f"\ncapture rate of the no-selection->oracle gap: {capture:.1%}")


if __name__ == "__main__":
    main()
