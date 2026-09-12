"""Does a measure trained on REAL fonts read a GENERATED atlas the way the eye did?

PRE-REGISTERED, and committed before the tool was executed.

THE ONE THING THIS TEST HAS THAT NOTHING ELSE HERE DOES: its labels were written
down BEFORE the instrument existed. `research/2026-08-23-the-loop-closes.md` and
`research/2026-08-23-candidate-evaluation-round-1.md` record, on 2026-08-23,
which of the twelve style prompts the generator obeyed and which it missed. The
attribute measures were built on 2026-08-24. The git timestamps prove the
ordering, which is exactly what the style-adherence retraction lacked -- there I
labelled a third prompt "missed" after seeing it score third-lowest.

WHAT IS BEING ASKED. `attribute_separation.py` established that six features
separate weight, mono, slant and width on held-out real FAMILIES. That is a
precondition, not an instrument: "is this real font monospace" is an easier
question than "did this generation obey the word monospace". This tool asks the
second one.

THE DESIGN. For each attribute, rank all twelve generated atlases by the
model's probability. The atlas whose PROMPT REQUESTED that attribute should rank
first if the generation obeyed it, and should not if it did not.

=== PRE-REGISTRATION, fixed before running ===

LABELS        Quoted verbatim below from the two notes dated 2026-08-23. Not
              revisited, not re-eyeballed, not extended. Adding a label now
              would repeat the precise error that voided the last attempt.
TRAINING      Each attribute's model is fit on ALL of its real-font sample from
              `attribute_separation.py` -- same sampling, same features, same
              CAP. The twelve generated atlases are the held-out set, and they
              are out of distribution by construction, which is the point.
PRIMARY       Do the two recorded HITS rank better on their requested attribute
              than the two recorded MISSES?
RESOLUTION    With 2 hits and 2 misses the best attainable p is 1/C(4,2) =
              **0.1667**. THIS TEST CANNOT REACH p<0.05 AND NO SIGNIFICANCE WILL
              BE CLAIMED FOR IT. It is a consistency check that can FALSIFY but
              not validate, and it is registered as such rather than dressed up
              in a statistic that would look decisive on n=4.
FALSIFIED IF  A recorded MISS ranks FIRST on the attribute its prompt asked for.
              Then the instrument and the eye disagree, one of them is wrong,
              and that is reported -- not explained away, and not resolved by
              re-examining the image until the instrument looks right.
SECONDARY     The weight ordering across the four weight-bearing prompts, and
              every per-attribute rank. DESCRIPTIVE ONLY, no claim, no bar.
NOT RUN AGAIN Whatever this returns, the measures are not retuned against these
              twelve and re-scored. A different generator arm is the next data,
              not a second pass over this one.

  python analysis/attribute_transfer.py
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import itertools
import json
import os

import numpy as np

from analysis.attribute_label_supply import EXCLUSIONS, scan
from analysis.attribute_separation import CAP, atlas_path, label_fns, vector

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED = os.path.join(REPO, "eval_runs", "_synthetic_probe", "external")

# The twelve prompts, in the order `research/candidate_references.json` lists
# them, which is the order the atlases are numbered in.
#
# `requests` names the attribute the prompt asks for and the direction the
# model's probability should move. `recorded` is the eye's verdict FROM THE
# 2026-08-23 NOTES, quoted, and is the only label this test uses.
#
#   HIT    the note names the attribute as coming through legibly
#   MISS   the note names the style as missed at both stages
#   REINT  "reinterpreted rather than failed" -- excluded from the primary,
#          because it is neither a hit nor a miss and forcing it to be one is
#          how the previous attempt manufactured a third label
PROMPTS = [
    # idx, attribute, direction, recorded, the note's words
    (0,  "weight", "high", None,   "heavy geometric sans"),
    (2,  "weight", "high", None,   "chunky slab serif"),
    (11, "weight", "high", None,   "heavy angular blackletter-influenced"),
    (7,  "weight", "low",  "REINT", "ultra-light hairline -- 'reinterpreted as an outline'"),
    (4,  "width",  "high", "HIT",  "condensed grotesque -- 'came through legibly'"),
    (6,  "mono",   "high", "MISS", "wide low-contrast monospace -- 'an ordinary heavy sans'"),
    (9,  "stencil", "high", "MISS", "stencil with deliberate breaks -- 'solid, no breaks'"),
    (10, "inline", "high", "HIT",  "inline stripe -- 'came through legibly'"),
]
PRIMARY = ("HIT", "MISS")


def fit_on_real(attr, pool, records, cap):
    """Fit one attribute's model on the whole real-font sample. Returns None if
    the attribute has too few families, exactly as `attribute_separation` does."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    pos_fn, neg_fn = label_fns()[attr]
    rep = {}
    for rec in records:
        side = 1 if pos_fn(rec) else (0 if neg_fn(rec) else None)
        if side is None:
            continue
        key = (rec["family"], side)
        if key not in rep or rec["stem"] < rep[key]:
            rep[key] = rec["stem"]
    pos = sorted(stem for (_, s), stem in rep.items() if s == 1)
    neg = sorted(stem for (_, s), stem in rep.items() if s == 0)
    take = min(cap, len(pos), len(neg))
    if take < 5:
        return None

    X, y = [], []
    for stem, label in [(s, 1) for s in pos[:take]] + [(s, 0) for s in neg[:take]]:
        path = atlas_path(pool, stem)
        if path is None:
            continue
        v = vector(path)
        if v is not None:
            X.append(v)
            y.append(label)
    if len(set(y)) < 2:
        return None
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    model.fit(np.asarray(X), np.asarray(y))
    return model, len(y)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pool", default=os.path.join(REPO, "font_pool"))
    ap.add_argument("--generated", default=GENERATED)
    ap.add_argument("--cap", type=int, default=CAP)
    ap.add_argument("--json", default=os.path.join(REPO, "research",
                                                   "attribute_transfer.json"))
    args = ap.parse_args()

    gen = sorted(glob.glob(os.path.join(args.generated, "*.png")))
    if len(gen) != 12:
        print(f"expected 12 generated atlases, found {len(gen)}", file=_sys.stderr)
        return 2
    gen_vectors, usable = [], []
    for i, path in enumerate(gen):
        v = vector(path)
        if v is None:
            print(f"  atlas {i} unscoreable, dropped", file=_sys.stderr)
            continue
        gen_vectors.append(v)
        usable.append(i)
    gen_vectors = np.asarray(gen_vectors)

    print("reading the pool ...")
    exclude = set(json.load(open(EXCLUSIONS, encoding="utf-8"))["exclude_stems"])
    records, _ = scan(args.pool, exclude)

    rows, cache = [], {}
    for idx, attr, direction, recorded, words in PROMPTS:
        if attr not in cache:
            cache[attr] = fit_on_real(attr, args.pool, records, args.cap)
        fitted = cache[attr]
        if fitted is None:
            rows.append({"idx": idx, "attribute": attr, "skipped": "too few families"})
            continue
        model, n_train = fitted
        if idx not in usable:
            rows.append({"idx": idx, "attribute": attr,
                         "skipped": "this atlas was unscoreable"})
            continue
        prob = model.predict_proba(gen_vectors)[:, 1]
        # rank 1 = most attribute-like; ranks are over the atlases that scored.
        order = np.argsort(-prob)
        rank_of = {usable[pos]: r + 1 for r, pos in enumerate(order)}
        rows.append({"idx": idx, "attribute": attr, "direction": direction,
                     "recorded": recorded, "words": words,
                     "rank": int(rank_of[idx]),
                     "of": len(usable), "prob": float(prob[usable.index(idx)]),
                     "train_n": n_train,
                     # DESCRIPTIVE, registered as such. Which atlas the measure
                     # ranks first matters even when the requesting one does
                     # not: if the stencil model's favourite is the INLINE
                     # atlas, `parts` is counting pieces without distinguishing
                     # a break from a stripe, and that is a limit to know
                     # before building on it.
                     "top3": [[int(usable[p]), float(prob[p])] for p in order[:3]]})

    print(f"\n  {'atlas':>5} {'attribute':<9} {'want':<5} {'recorded':<6} "
          f"{'rank':>6} {'p':>7}  note's words")
    for r in rows:
        if "skipped" in r:
            print(f"  {r['idx']:>5} {r['attribute']:<9} {r['skipped']}")
            continue
        top = " ".join(f"{i}({p:.2f})" for i, p in r["top3"])
        print(f"  {r['idx']:>5} {r['attribute']:<9} {r['direction']:<5} "
              f"{str(r['recorded'] or '-'):<6} {r['rank']:>3}/{r['of']:<2} "
              f"{r['prob']:>7.3f}  top3 {top:<26} {r['words']}")

    # PRIMARY, exactly as registered: hits should rank better than misses.
    hits = [r["rank"] for r in rows if r.get("recorded") == "HIT"]
    misses = [r["rank"] for r in rows if r.get("recorded") == "MISS"]
    primary = None
    if hits and misses:
        separated = max(hits) < min(misses)
        n_h, n_m = len(hits), len(misses)
        best_p = 1.0 / len(list(itertools.combinations(range(n_h + n_m), n_h)))
        falsified = [r for r in rows if r.get("recorded") == "MISS" and r["rank"] == 1]
        primary = {"hit_ranks": hits, "miss_ranks": misses,
                   "hits_rank_better": bool(separated),
                   "best_attainable_p": best_p,
                   "falsified_by": [r["idx"] for r in falsified]}
        print(f"\n  PRIMARY  hits {hits} vs misses {misses}: "
              f"{'consistent' if separated else 'NOT consistent'}")
        print(f"  Best attainable p is {best_p:.4f}. NO significance is claimed;"
              " this check can falsify, not validate.")
        for r in falsified:
            print(f"  FALSIFIED: atlas {r['idx']} ({r['attribute']}) is a recorded"
                  " MISS yet ranks FIRST on the attribute its prompt asked for."
                  " The instrument and the eye disagree; one of them is wrong.")

    # Repo-relative, never absolute: an absolute path in a tracked record leaks
    # a home directory, and it slipped past the sanitizer once via JSON's
    # doubled backslashes.
    payload = {"preregistered": True,
               "generated": os.path.relpath(args.generated, REPO).replace("\\", "/"),
               "rows": rows, "primary": primary}
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
