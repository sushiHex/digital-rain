"""Per-cell medoid selection in DINOv2 space -- the untried best-of-N selector.

WHY THIS AND NOT THE CLOSED TRACK. Two selectors were tried and both failed, in
ORTHOGONAL ways:

  seed/atlas-level DINOv2 medoid -- right space, WRONG GRANULARITY. CLAUDE.md:
    "the style lottery is per-cell, not per-atlas, which rules out every
     seed-level and atlas-level selector. Only a per-cell signal can work."

  per-cell OCR (TrOCR 4.3%, GOT-OCR2 4.7%) -- right granularity, WRONG SPACE.
    "The oracle headroom is defined in DINOv2 space; OCR-based selectors
     optimize a different space they agree with only ~65% of the time."

Per-cell selection IN DINOv2 SPACE fixes both at once and was never built. The
mechanism is self-consistency: if a cell's errors are idiosyncratic across
seeds, the medoid cell is the consensus cell, and consensus should track
correctness. It uses no ground truth, so it is deployable.

The reserve it targets is the largest known in the project: +0.164 char_acc of
best-of-N headroom, 2.2x the whole 4B->9B gap.

FOUR STRATEGIES, so the result is interpretable rather than a lone number:

  seed0        a single seed -- the shipped behaviour, the thing to beat
  atlas_medoid pick ONE seed per font by whole-atlas medoid -- the KNOWN
               FAILURE, included as a control. If this does not reproduce its
               recorded failure, the harness is wrong, not the idea.
  cell_medoid  THE CANDIDATE: pick each cell independently by medoid
  oracle_cell  per-cell argmax similarity to ground truth -- the CEILING,
               not deployable, included to say what fraction was captured

Scoring mirrors eval_checkpoint.compute_char_acc exactly: within one font, a
94x94 cosine matrix against that font's own GT cells, cell i counted when
argmax_j sim(gen[i], gt[j]) == i.

  python analysis/per_cell_medoid.py --candidates bestofn_4b/candidates
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import json
import os

import numpy as np
from PIL import Image

from atlas_constants import BLANK_INDICES, CHARSET
from eval_checkpoint import crop_cell

DRAWN = [i for i in range(len(CHARSET)) if i not in BLANK_INDICES]


def cell_embeds(atlas_path, embed_fn):
    """(n_drawn, D) unit embeddings for one atlas's drawn cells."""
    with Image.open(atlas_path) as im:
        a = np.asarray(im.convert("RGB"))
    cells = [crop_cell(a, i) for i in DRAWN]
    v = embed_fn(cells)
    return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-8)


def medoid_index(V):
    """Index minimising summed cosine distance to the others. V: (n, D) unit."""
    S = V @ V.T                       # cosine similarity
    return int(np.argmax(S.sum(axis=1)))


def char_acc(sel, gt):
    """eval_checkpoint.compute_char_acc, restricted to one font."""
    S = sel @ gt.T
    return float((S.argmax(axis=1) == np.arange(len(sel))).mean())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidates", default="bestofn_4b/candidates")
    ap.add_argument("--gt-dir", default="eval_holdout/atlases")
    ap.add_argument("--out", default="research/per_cell_medoid.json")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)

    from cleanup.models import build_dino_embed_fn
    embed_fn = build_dino_embed_fn()

    fonts = sorted(d for d in os.listdir(args.candidates)
                   if os.path.isdir(os.path.join(args.candidates, d)))
    if args.limit:
        fonts = fonts[:args.limit]

    # The Bitcount pair shares a reference but has different ground truth, so
    # any per-font number there measures the target, not the model.
    fonts = [f for f in fonts if not f.startswith(("BitcountGridDoubleInk",
                                                   "BitcountPropDoubleInk"))]

    results = {k: [] for k in ("seed0", "atlas_medoid", "cell_medoid", "oracle_cell")}
    per_font = []
    for n, font in enumerate(fonts, 1):
        gt_path = os.path.join(args.gt_dir, f"{font}.png")
        # NOT glob: variable-font stems contain brackets -- InterTight[wght],
        # MirandaSans[wght] -- and glob reads "[wght]" as a character class, so
        # those directories silently match nothing. That dropped 12 of 48 fonts
        # on the first run, including every variable font in the holdout.
        cdir = os.path.join(args.candidates, font)
        seeds = sorted(os.path.join(cdir, f) for f in os.listdir(cdir)
                       if "seed" in f and f.lower().endswith(".png"))
        if not os.path.isfile(gt_path) or len(seeds) < 2:
            continue
        gt = cell_embeds(gt_path, embed_fn)
        V = np.stack([cell_embeds(p, embed_fn) for p in seeds])   # (S, C, D)

        picks = {}
        picks["seed0"] = V[0]
        # whole-atlas medoid: one seed for the entire font
        flat = V.reshape(len(seeds), -1)
        flat = flat / (np.linalg.norm(flat, axis=1, keepdims=True) + 1e-8)
        picks["atlas_medoid"] = V[medoid_index(flat)]
        # per-cell medoid: choose independently for every cell
        picks["cell_medoid"] = np.stack(
            [V[medoid_index(V[:, c, :]), c, :] for c in range(V.shape[1])])
        # per-cell oracle: the ceiling
        picks["oracle_cell"] = np.stack(
            [V[int(np.argmax(V[:, c, :] @ gt[c])), c, :] for c in range(V.shape[1])])

        row = {"font": font, "n_seeds": len(seeds)}
        for k, sel in picks.items():
            acc = char_acc(sel, gt)
            results[k].append(acc)
            row[k] = round(acc, 4)
        per_font.append(row)
        if n % 10 == 0:
            print(f"  {n}/{len(fonts)} fonts")

    print(f"\n{len(per_font)} fonts, {results['seed0'] and len(results['seed0'])} scored\n")
    base = float(np.mean(results["seed0"]))
    ceiling = float(np.mean(results["oracle_cell"]))
    print(f"{'strategy':<14}{'char_acc':>10}{'vs seed0':>11}{'% of headroom':>15}")
    for k in ("seed0", "atlas_medoid", "cell_medoid", "oracle_cell"):
        m = float(np.mean(results[k]))
        d = m - base
        pct = 100 * d / (ceiling - base) if ceiling > base else float("nan")
        print(f"{k:<14}{m:>10.4f}{d:>+11.4f}{pct:>14.1f}%")

    print("\natlas_medoid is the CONTROL: it is recorded as failing on the 4B.")
    print("If it does not fail here, distrust the harness before the result.")

    payload = {"_comment": "Per-cell medoid selection in DINOv2 space. "
                           "oracle_cell is a non-deployable ceiling.",
               "n_fonts": len(per_font),
               "aggregate": {k: round(float(np.mean(v)), 4)
                             for k, v in results.items()},
               "per_font": per_font}
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
