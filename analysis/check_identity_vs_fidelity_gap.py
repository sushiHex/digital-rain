"""Is the +0.1483 same-model best-of-4 char_acc gap mostly about IDENTITY
(reads as the right letter -- a no-GT-needed axis) or STYLE-FIDELITY (matches
this particular font's exact rendering -- inherently GT-relative)? This
project already proved char_acc/DINOv2 conflates the two (research/2026-07-18
-wrong-letters-are-a-metric-artifact.md): IDENTITY was 0.978 vs FIDELITY 0.688
on the single-seed baseline. If the best-of-4 gap is mostly fidelity (style-
matching luck), it's less practically important than the raw char_acc number
implies, and reframes whether chasing it further is worthwhile.
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from PIL import Image

CANDIDATES_DIR = "dpo_holdout_bestofn/candidates"
SCORES_PATH = "dpo_holdout_bestofn/scores.json"


def main():
    from eval_checkpoint import crop_cell
    from atlas_constants import CHARSET, DRAWN_INDICES
    from glyph_classifier import load_classifier, classify
    from candidate_gen import parse_candidate_key
    from identity_score import reads_as

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, idx_to_char = load_classifier("glyph_classifier.pt", device=device)

    s = json.load(open(SCORES_PATH))
    by_cell_fidelity = defaultdict(dict)  # (font,char) -> {seed: char_acc_match}
    for key, cells in s.items():
        font, model_name, seed_i = parse_candidate_key(key)
        for c in cells:
            by_cell_fidelity[(font, c["char"])][seed_i] = bool(c["char_acc_match"])

    fonts = sorted({f for f, _ in by_cell_fidelity})
    n_total = n_fid_any = n_fid_seed0 = 0
    n_id_any = n_id_seed0 = 0
    # among cells where fidelity FAILS at seed0 but SUCCEEDS at some other seed,
    # how many of those seed0-failures were already IDENTITY-correct (i.e. the
    # "failure" seed0 already had the right letter, just not the exact style)?
    n_recoverable = n_recoverable_seed0_already_identity_ok = 0

    for font in fonts:
        atlases = {}
        for seed_i in range(4):
            p = Path(CANDIDATES_DIR) / font / f"glyph__seed{seed_i}.png"
            if p.exists():
                atlases[seed_i] = np.array(Image.open(p).convert("RGB"))
        if len(atlases) < 2:
            continue

        cells_by_seed = {}
        chars = []
        for idx in DRAWN_INDICES:
            ch = CHARSET[idx]
            chars.append(ch)
        for seed_i, atlas in atlases.items():
            cells_by_seed[seed_i] = [crop_cell(atlas, idx) for idx in DRAWN_INDICES]

        preds_by_seed = {}
        for seed_i, cells in cells_by_seed.items():
            preds_by_seed[seed_i] = classify(model, idx_to_char, cells)

        for i, ch in enumerate(chars):
            fid = by_cell_fidelity.get((font, ch), {})
            if not fid:
                continue
            n_total += 1
            fid_any = any(fid.values())
            n_fid_any += fid_any
            n_fid_seed0 += bool(fid.get(0, False))

            id_ok = {seed_i: reads_as(preds_by_seed[seed_i][i], ch, lenient=True)
                     for seed_i in preds_by_seed}
            id_any = any(id_ok.values())
            n_id_any += id_any
            n_id_seed0 += bool(id_ok.get(0, False))

            fid_recoverable = (not fid.get(0, False)) and fid_any
            if fid_recoverable:
                n_recoverable += 1
                n_recoverable_seed0_already_identity_ok += bool(id_ok.get(0, False))

    print(f"cells analyzed: {n_total}\n")
    print("FIDELITY (char_acc, DINOv2 template-match):")
    print(f"  seed0 only:  {n_fid_seed0/n_total:.4f}")
    print(f"  best-of-4:   {n_fid_any/n_total:.4f}   (gap +{n_fid_any/n_total - n_fid_seed0/n_total:.4f})")
    print("\nIDENTITY (glyph classifier, GT-gated equivalence classes):")
    print(f"  seed0 only:  {n_id_seed0/n_total:.4f}")
    print(f"  best-of-4:   {n_id_any/n_total:.4f}   (gap +{n_id_any/n_total - n_id_seed0/n_total:.4f})")
    print(f"\nOf the {n_recoverable} cells where seed0 FAILED fidelity but SOME seed recovers it:")
    print(f"  seed0 was ALREADY identity-correct (right letter, just wrong style): "
          f"{n_recoverable_seed0_already_identity_ok} "
          f"({n_recoverable_seed0_already_identity_ok/max(n_recoverable,1):.1%})")


if __name__ == "__main__":
    main()
