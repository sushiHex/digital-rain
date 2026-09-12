"""The floor nobody measured: return a REAL font instead of generating one.

THE QUESTION. Every score in this repo compares a generated atlas against the
holdout's ground truth. Nothing has ever asked what a trivial non-generative
baseline scores on the same instrument. If "find the nearest training font by
its reference image and hand back that font's atlas" scores comparably, then
the metric suite cannot distinguish GENERATING a typeface from RETURNING a
different, clean, vaguely similar real one -- and every model comparison built
on it has been measuring something other than what it claimed.

This is not a proposal to ship retrieval. Retrieval cannot produce a typeface
that does not already exist, and shipping it would mean redistributing someone
else's font. It is a measuring stick.

THE LEAK GUARD, and why it is mandatory. 8 of the 50 holdout GT atlases are
BYTE-IDENTICAL to a training atlas (AkayaTelivigala==AkayaKanadaka,
JainiPurva==Jaini, Tirra==Akatab, ...). Unguarded retrieval finds those exactly
and scores ~1.0 on them, which flatters the baseline and is also a finding in
its own right about the holdout. `--allow-leak` reports both numbers.

  python analysis/retrieval_baseline.py
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import hashlib
import json
import os

import numpy as np
from PIL import Image

from atlas_constants import BLANK_INDICES, CHARSET
from eval_checkpoint import crop_cell

DRAWN = [i for i in range(len(CHARSET)) if i not in BLANK_INDICES]


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def unit(v):
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-8)


def embed_image(path, embed_fn):
    """One vector for a whole image (the reference), for nearest-neighbour."""
    with Image.open(path) as im:
        a = np.asarray(im.convert("RGB"))
    return unit(embed_fn([a])[0])


def embed_cells(path, embed_fn):
    with Image.open(path) as im:
        a = np.asarray(im.convert("RGB"))
    return unit(embed_fn([crop_cell(a, i) for i in DRAWN]))


def char_acc(gen, gt):
    """eval_checkpoint.compute_char_acc, one font."""
    return float(((gen @ gt.T).argmax(axis=1) == np.arange(len(gen))).mean())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--holdout", default="eval_holdout")
    ap.add_argument("--corpus", default="dataset_v2")
    ap.add_argument("--out", default="research/retrieval_baseline.json")
    ap.add_argument("--allow-leak", action="store_true",
                    help="do NOT skip corpus fonts whose atlas is byte-identical "
                         "to the holdout target (reports the flattered number)")
    args = ap.parse_args(argv)

    from cleanup.models import build_dino_embed_fn
    embed_fn = build_dino_embed_fn()

    h_refs = os.path.join(args.holdout, "references")
    h_atl = os.path.join(args.holdout, "atlases")
    c_refs = os.path.join(args.corpus, "references")
    c_atl = os.path.join(args.corpus, "atlases")

    holdout = sorted(os.path.splitext(f)[0] for f in os.listdir(h_atl)
                     if f.endswith(".png"))
    corpus = sorted(os.path.splitext(f)[0] for f in os.listdir(c_atl)
                    if f.endswith(".png")
                    and os.path.isfile(os.path.join(c_refs, f)))
    print(f"holdout {len(holdout)} fonts   corpus {len(corpus)} fonts")

    print("hashing atlases for the leak guard...")
    c_hash = {n: sha(os.path.join(c_atl, n + ".png")) for n in corpus}
    h_hash = {n: sha(os.path.join(h_atl, n + ".png")) for n in holdout}
    leaked = {n for n in holdout if h_hash[n] in set(c_hash.values())}
    print(f"  {len(leaked)} holdout fonts have a byte-identical corpus twin")

    print("embedding corpus references...")
    C = np.stack([embed_image(os.path.join(c_refs, n + ".png"), embed_fn)
                  for n in corpus])

    rows = []
    for i, name in enumerate(holdout, 1):
        q = embed_image(os.path.join(h_refs, name + ".png"), embed_fn)
        sims = C @ q
        order = np.argsort(-sims)
        pick = None
        for j in order:
            if not args.allow_leak and c_hash[corpus[j]] == h_hash[name]:
                continue                      # the answer itself; skip
            pick = corpus[j]
            break
        gt = embed_cells(os.path.join(h_atl, name + ".png"), embed_fn)
        gen = embed_cells(os.path.join(c_atl, pick + ".png"), embed_fn)
        rows.append({"font": name, "retrieved": pick,
                     "leaked_twin": name in leaked,
                     "char_acc": round(char_acc(gen, gt), 4),
                     "dinov2": round(float((gen * gt).sum(axis=1).mean()), 4)})
        if i % 10 == 0:
            print(f"  {i}/{len(holdout)}")

    ca = float(np.mean([r["char_acc"] for r in rows]))
    dv = float(np.mean([r["dinov2"] for r in rows]))
    print(f"\nRETRIEVAL BASELINE ({'WITH leak' if args.allow_leak else 'leak-guarded'})")
    print(f"  char_acc {ca:.4f}   dinov2 {dv:.4f}   n={len(rows)}")
    print("\nfor comparison, the trained models on the same holdout:")
    print("  4B r32 lrfix   char_acc 0.6183   dinov2 0.8388")
    print("  4B r32 clean   char_acc 0.4914-0.6070 (3 seeds)")
    print("\nA baseline that returns a DIFFERENT REAL FONT is not a model of")
    print("quality -- it is a test of whether the metric can tell the")
    print("difference. If it scores comparably, the metric cannot.")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"_comment": "Nearest-training-font retrieval, scored as if it "
                               "were a generation. A measuring stick, NOT a "
                               "shippable approach.",
                   "leak_guarded": not args.allow_leak,
                   "n_leaked_holdout_fonts": len(leaked),
                   "leaked_fonts": sorted(leaked),
                   "char_acc": round(ca, 4), "dinov2": round(dv, 4),
                   "per_font": rows}, f, indent=1)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
