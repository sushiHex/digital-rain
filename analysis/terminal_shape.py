"""Can a terminal-shape feature make serif-vs-sans readable?

PRE-REGISTERED. Written and committed before any number was computed.

THE GAP. `attribute_separation.py` returned serif-vs-sans at **AUC 0.733** over
100 families -- real, and weak. The cause is not mysterious: the six features
are stroke thickness, slant, fill, component count, ink-width spread and aspect
ratio. NONE OF THEM MEASURES TERMINAL SHAPE. A human reads a serif instantly.

This is the largest labelled gap in the vocabulary. 121 families carry a PANOSE
serif label, so unlike stencil and inline this needs no synthesis -- only a
feature that can see the thing.

WHY THIS IS NOT THE MOVE THAT WAS REFUSED. `attribute_separation.py`'s
registration forbids rescuing a failed attribute "with a different feature set
ON THE SAME DATA". That run used the alphabetically-FIRST 50 families of each
class. This one uses families **51 onward** -- 71 serif and 277 sans remain, so
a disjoint 50+50 sample exists. The failed families are never scored here.
Both the 6-feature baseline and the 7-feature version are measured on that same
fresh sample, so the comparison is fair and the old result is not reused.

THE FEATURE, AND WHY IT IS TWO NUMBERS. The obvious guess -- "a serif is extra
ink at the stroke end, so the distance transform is larger there" -- is WRONG,
and reasoning it through is what produced the actual feature. A serif is a
crossbar: the skeleton of a serifed stem is a T, not a line. So a serif

  * MULTIPLIES skeleton endpoints (two at each terminal instead of one), and
  * makes those endpoints THINNER, because they sit at the tips of a fine bar.

`term_count` and `term_ratio` capture exactly those, and they move in OPPOSITE
directions, which is why one number will not do.

=== PRE-REGISTRATION, fixed before running ===

SAMPLE        50 serif + 50 sans FAMILIES, taken from index OFFSET onward in
              sorted order, so the families scored by the run that failed are
              excluded. One file per (family, class).
LABELS        PANOSE `bSerifStyle`, valid ONLY where `bFamilyType == 2`, the
              same guard `attribute_label_supply.py` uses.
STATISTIC     ROC AUC of a logistic regression under `GroupKFold` by FAMILY.
BASELINE      The same six features, on the SAME fresh sample. Reported beside
              the new number so the feature's contribution is visible rather
              than inferred from a run on other families.
BAR           Held-out AUC >= 0.75 with the terminal features -- the same
              "carried" bar the other four attributes cleared.
              Below 0.75 the feature is reported as NOT WORKING.
SIGNIFICANCE  Label permutation against the out-of-fold scores, 2000 draws,
              +1 corrected.
IF IT FAILS   Reported as a failure. The feature is NOT iterated against this
              sample -- no second definition scored on the same families. A
              further attempt needs the remaining untouched families and its
              own registration.

  python analysis/terminal_shape.py
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage

from analysis.attribute_label_supply import (EXCLUSIONS, PANOSE_LATIN_TEXT,
                                             PANOSE_SANS, PANOSE_SERIF, scan)
from analysis.attribute_separation import atlas_path
from analysis.style_coherence import FEATURES, cell_features

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP = 50
OFFSET = 50            # skip the families the failed run scored
PERM_ITERS = 2000
BAR = 0.75
MIN_SKELETON = 12
TERMINAL = ("term_count", "term_ratio")


def terminal_features(cell):
    """(endpoints per skeleton pixel, endpoint thickness / mean thickness).

    A serif is a CROSSBAR, so the skeleton of a serifed stem is a T rather than
    a line: more endpoints, and thinner ones. The two move in opposite
    directions, which is why this returns a pair.
    """
    from skimage.morphology import skeletonize

    ink = cell > 128
    if ink.sum() < MIN_SKELETON:
        return None
    skel = skeletonize(ink)
    n_skel = int(skel.sum())
    if n_skel < MIN_SKELETON:
        return None

    # A skeleton pixel with exactly one skeleton neighbour is a free end.
    kernel = np.ones((3, 3), dtype=np.uint8)
    neighbours = ndimage.convolve(skel.astype(np.uint8), kernel,
                                  mode="constant") - skel.astype(np.uint8)
    ends = skel & (neighbours == 1)
    n_ends = int(ends.sum())
    if n_ends == 0:
        return {"term_count": 0.0, "term_ratio": 1.0}

    dist = ndimage.distance_transform_edt(ink)
    spine = float(dist[skel].mean())
    ratio = float(dist[ends].mean() / spine) if spine > 1e-6 else 1.0
    return {"term_count": float(np.log1p(n_ends / n_skel * 100.0)),
            "term_ratio": ratio}


def vector(path, with_terminal):
    """Per-cell means over an atlas: the six features, optionally plus two."""
    from atlas_constants import BLANK_INDICES, CELL_H, CELL_W, CHARSET, GRID_COLS

    arr = np.asarray(Image.open(path).convert("L"))
    base, term, widths, aspects = [], [], [], []
    for idx in range(len(CHARSET)):
        if idx in BLANK_INDICES:
            continue
        r, c = idx // GRID_COLS, idx % GRID_COLS
        cell = arr[r * CELL_H:(r + 1) * CELL_H, c * CELL_W:(c + 1) * CELL_W]
        f = cell_features(cell)
        if f is None:
            continue
        base.append([f[k] for k in FEATURES])
        ink = cell > 128
        rows, cols = np.where(ink)
        cw = cols.max() - cols.min() + 1
        ch = rows.max() - rows.min() + 1
        widths.append(float(cw))
        aspects.append(float(cw) / float(ch))
        if with_terminal:
            t = terminal_features(cell)
            if t is not None:
                term.append([t[k] for k in TERMINAL])
    if len(base) < 40:
        return None
    base = np.asarray(base, dtype=float)
    widths = np.asarray(widths, dtype=float)
    out = np.concatenate([base.mean(axis=0),
                          [float(widths.std() / widths.mean()),
                           float(np.mean(aspects))]])
    if with_terminal:
        if len(term) < 40:
            return None
        out = np.concatenate([out, np.asarray(term, dtype=float).mean(axis=0)])
    return out


def evaluate(X, y, groups, seed=0):
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import GroupKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    n_splits = min(5, len(set(groups)))
    pred = np.zeros(len(y), dtype=float)
    for tr, te in GroupKFold(n_splits=n_splits).split(X, y, groups):
        if len(set(y[tr])) < 2:
            return None
        m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
        m.fit(X[tr], y[tr])
        pred[te] = m.predict_proba(X[te])[:, 1]
    observed = float(roc_auc_score(y, pred))
    rng = np.random.default_rng(seed)
    null = np.array([roc_auc_score(rng.permutation(y), pred)
                     for _ in range(PERM_ITERS)])
    p = float(((null >= observed).sum() + 1) / (PERM_ITERS + 1))
    return {"auc": observed, "p": p, "n": int(len(y)),
            "families": int(len(set(groups)))}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pool", default=os.path.join(REPO, "font_pool"))
    ap.add_argument("--cap", type=int, default=CAP)
    ap.add_argument("--offset", type=int, default=OFFSET)
    ap.add_argument("--json", default=os.path.join(REPO, "research",
                                                   "terminal_shape.json"))
    args = ap.parse_args()

    exclude = set(json.load(open(EXCLUSIONS, encoding="utf-8"))["exclude_stems"])
    print("reading the pool ...")
    records, _ = scan(args.pool, exclude)

    def latin(r):
        return r.get("panose_family") == PANOSE_LATIN_TEXT

    rep = {}
    for rec in records:
        if not latin(rec):
            continue
        side = (1 if rec.get("panose_serif") in PANOSE_SERIF else
                0 if rec.get("panose_serif") in PANOSE_SANS else None)
        if side is None:
            continue
        key = (rec["family"], side)
        if key not in rep or rec["stem"] < rep[key]:
            rep[key] = rec["stem"]

    pos = sorted(stem for (_, s), stem in rep.items() if s == 1)
    neg = sorted(stem for (_, s), stem in rep.items() if s == 0)
    print(f"  serif families {len(pos)}   sans families {len(neg)}")
    pos, neg = pos[args.offset:], neg[args.offset:]
    take = min(args.cap, len(pos), len(neg))
    if take < 10:
        print(f"too few families past offset {args.offset}", file=_sys.stderr)
        return 2
    chosen = [(s, 1) for s in pos[:take]] + [(s, 0) for s in neg[:take]]
    print(f"  FRESH sample past offset {args.offset}: {take} + {take} families\n")

    results = {}
    for name, with_terminal in (("six features (baseline)", False),
                                ("+ terminal shape", True)):
        X, y, groups = [], [], []
        for stem, label in chosen:
            path = atlas_path(args.pool, stem)
            if path is None:
                continue
            v = vector(path, with_terminal)
            if v is None:
                continue
            X.append(v)
            y.append(label)
            groups.append(stem.split("[")[0].split("-")[0])
        if len(set(y)) < 2:
            continue
        res = evaluate(np.asarray(X), np.asarray(y), groups)
        if res is None:
            continue
        results[name] = res
        print(f"  {name:<26} AUC {res['auc']:.3f}  p={res['p']:.4f}  "
              f"n={res['n']:<4} families={res['families']}")

    new = results.get("+ terminal shape")
    base = results.get("six features (baseline)")
    passed = bool(new and new["auc"] >= BAR)
    if new and base:
        print(f"\n  terminal shape moves AUC {base['auc']:.3f} -> "
              f"{new['auc']:.3f}  ({new['auc'] - base['auc']:+.3f})")
    print(f"  PRE-REGISTERED BAR AUC >= {BAR}: "
          f"{'PASSED' if passed else 'FAILED'}")
    if not passed:
        print("\n  The terminal feature does not make serif-vs-sans carried.")
        print("  Reported as a failure; NOT iterated against this sample.")

    payload = {"preregistered": True, "bar": BAR, "offset": args.offset,
               "cap": take, "terminal_features": list(TERMINAL),
               "results": results, "passed": passed,
               "note": "families before the offset were scored by the run that "
                       "failed at 0.733 and are excluded here"}
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
