"""Per-cell best-of-N selection by GLYPH-CLASSIFIER CONFIDENCE.

WHY THIS AFTER MEDOID FAILED. `analysis/per_cell_medoid.py` established the
granularity point decisively -- per-cell beats per-atlas at p=0.0004 -- but
captured only 4.2% of the +0.12 reserve, because medoid is an AGREEMENT
statistic and seeds agree on plausible cells as readily as on correct ones.

A discriminative signal should do better. `glyph_classifier.py` is a 94-class
CNN at val_acc 0.9385 trained on THIS domain (font atlas cells), which is the
specific reason to expect it to beat the two general text recognisers that
already failed here: TrOCR captured 4.3% and GOT-OCR2 4.7%, both optimising a
space that agrees with DINOv2 only ~65% of the time.

For each cell we know which character it is SUPPOSED to be -- position in the
atlas determines it -- so the classifier's probability for that expected
character is a per-cell, no-ground-truth quality signal. Pick the seed whose
cell the classifier is most confident about.

STRATEGIES, matching per_cell_medoid.py so the two are directly comparable:

  seed0        single seed, the shipped behaviour
  cell_medoid  the DINOv2 consensus selector, for reference (4.2% recorded)
  cell_conf    THE CANDIDATE: argmax classifier confidence in the expected char
  cell_combo   confidence, tie-broken toward the DINOv2 medoid -- tests whether
               the two signals are complementary rather than redundant
  oracle_cell  per-cell argmax similarity to ground truth: the ceiling

Scoring mirrors eval_checkpoint.compute_char_acc: within one font, a 94x94
cosine matrix against that font's own GT cells, cell i counted when
argmax_j sim(gen[i], gt[j]) == i.

  python analysis/per_cell_classifier_select.py
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
import os

import numpy as np
from PIL import Image

from atlas_constants import BLANK_INDICES, CHARSET
from eval_checkpoint import crop_cell

DRAWN = [i for i in range(len(CHARSET)) if i not in BLANK_INDICES]
EXPECTED = [CHARSET[i] for i in DRAWN]


def _seed_paths(cdir):
    # NOT glob: variable-font stems contain brackets (InterTight[wght]) which
    # glob reads as a character class, silently skipping every variable font.
    return sorted(os.path.join(cdir, f) for f in os.listdir(cdir)
                  if "seed" in f and f.lower().endswith(".png"))


def _cells(atlas_path):
    with Image.open(atlas_path) as im:
        a = np.asarray(im.convert("RGB"))
    return [crop_cell(a, i) for i in DRAWN]


def _unit(v):
    return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-8)


def medoid_index(V):
    return int(np.argmax((V @ V.T).sum(axis=1)))


def char_acc(sel, gt):
    return float(((sel @ gt.T).argmax(axis=1) == np.arange(len(sel))).mean())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidates", default="bestofn_4b/candidates")
    ap.add_argument("--gt-dir", default="eval_holdout/atlases")
    ap.add_argument("--out", default="research/per_cell_classifier.json")
    args = ap.parse_args(argv)

    import torch

    from cleanup.models import build_dino_embed_fn
    from glyph_classifier import _batched_logits, load_classifier

    embed_fn = build_dino_embed_fn()
    model, idx_to_char = load_classifier()
    # classify_conf() returns (char, MAX prob) -- the confidence of whatever the
    # model guessed. The signal wanted here is the probability of the character
    # the cell is SUPPOSED to be, which needs the full softmax. Build the
    # inverse map from the model's own idx_to_char rather than assuming CHARS
    # ordering matches it.
    char_to_idx = {c: i for i, c in idx_to_char.items()} \
        if isinstance(idx_to_char, dict) else \
        {c: i for i, c in enumerate(idx_to_char)}
    exp_idx = np.array([char_to_idx.get(c, -1) for c in EXPECTED])
    missing = int((exp_idx < 0).sum())
    if missing:
        print(f"  note: {missing} expected chars absent from the classifier's "
              f"label set; those cells fall back to seed order")

    def expected_probs(cells):
        """(n_cells, 94) softmax over the classifier's label set."""
        out = []
        for logits in _batched_logits(model, cells, 256):
            out.append(torch.softmax(logits, dim=1).cpu().numpy())
        return np.concatenate(out, axis=0)

    fonts = sorted(d for d in os.listdir(args.candidates)
                   if os.path.isdir(os.path.join(args.candidates, d))
                   and not d.startswith(("BitcountGridDoubleInk",
                                         "BitcountPropDoubleInk")))

    keys = ("seed0", "cell_medoid", "cell_conf", "cell_combo", "oracle_cell")
    results = {k: [] for k in keys}
    per_font = []
    for n, font in enumerate(fonts, 1):
        gt_path = os.path.join(args.gt_dir, f"{font}.png")
        cdir = os.path.join(args.candidates, font)
        seeds = _seed_paths(cdir)
        if not os.path.isfile(gt_path) or len(seeds) < 2:
            continue

        gt = _unit(embed_fn(_cells(gt_path)))
        V, C = [], []
        for p in seeds:
            cells = _cells(p)
            V.append(_unit(embed_fn(cells)))
            C.append(expected_probs(cells))                     # (n_cells, 94)
        V = np.stack(V)                                        # (S, cells, D)
        C = np.stack(C)                                        # (S, cells, 94)

        ncell = V.shape[1]
        conf = np.stack([C[:, c, exp_idx[c]] if exp_idx[c] >= 0
                         else np.zeros(len(seeds)) for c in range(ncell)], axis=1)

        picks = {"seed0": V[0]}
        picks["cell_medoid"] = np.stack(
            [V[medoid_index(V[:, c, :]), c, :] for c in range(ncell)])
        picks["cell_conf"] = np.stack(
            [V[int(np.argmax(conf[:, c])), c, :] for c in range(ncell)])
        # Complementarity: confidence picks the set within 2% of the best, then
        # the DINOv2 medoid breaks the tie inside that set.
        combo = []
        for c in range(ncell):
            best = conf[:, c].max()
            cand = np.flatnonzero(conf[:, c] >= best - 0.02)
            sub = V[cand, c, :]
            combo.append(sub[medoid_index(sub)] if len(cand) > 1 else V[cand[0], c, :])
        picks["cell_combo"] = np.stack(combo)
        picks["oracle_cell"] = np.stack(
            [V[int(np.argmax(V[:, c, :] @ gt[c])), c, :] for c in range(ncell)])

        row = {"font": font, "n_seeds": len(seeds)}
        for k in keys:
            acc = char_acc(picks[k], gt)
            results[k].append(acc)
            row[k] = round(acc, 4)
        per_font.append(row)
        if n % 10 == 0:
            print(f"  {n}/{len(fonts)} fonts")

    base = float(np.mean(results["seed0"]))
    ceil = float(np.mean(results["oracle_cell"]))
    print(f"\n{len(per_font)} fonts\n")
    print(f"{'strategy':<14}{'char_acc':>10}{'vs seed0':>11}{'% headroom':>13}")
    for k in keys:
        m = float(np.mean(results[k]))
        print(f"{k:<14}{m:>10.4f}{m-base:>+11.4f}"
              f"{(100*(m-base)/(ceil-base) if ceil > base else float('nan')):>12.1f}%")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"n_fonts": len(per_font),
                   "aggregate": {k: round(float(np.mean(v)), 4)
                                 for k, v in results.items()},
                   "per_font": per_font}, f, indent=1)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
