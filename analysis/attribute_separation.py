"""Does the ATLAS FORMAT carry each labelled style attribute?

PRE-REGISTERED. Written and committed BEFORE the numbers were seen, for the same
reason `style_adherence_minimal_pairs.py` was: the previous attempt at a style
instrument set a bar, failed it, ran a second statistic on the same data and
reported the pass. See
`research/2026-08-24-clip-does-not-read-the-decisive-clause.md`.

WHY THIS RUNS BEFORE ANY CLASSIFIER. Generic CLIP cannot read the clause that
decides a style, so the registered alternative is a discriminative per-attribute
measure trained on real fonts. `attribute_label_supply.py` established which
attributes the corpus can label at all. This one asks the question that comes
next and is easy to skip: OF THE ATTRIBUTES WE CAN LABEL, WHICH SURVIVE THE
ATLAS?

That is not rhetorical. `build_dataset.render_atlas` centres every glyph on its
INK bounding box, so advance width is discarded outright -- and monospace is
DEFINED by equal advances, not equal ink. Weight, slant and serif style are ink
properties and must survive. Width and monospace are advance-derived and might
not. Training a classifier on an attribute the image does not carry would
produce a confident instrument measuring nothing, which is the failure this
project has now logged five times.

FEATURES ARE REUSED, NOT REINVENTED. `style_coherence.cell_features` already
computes stroke / slant / fill / parts per cell, validated at n=50. `parts` is
a connected-component count, which is exactly what a stencil break or an inline
stripe does to a glyph -- so the rare attributes are already targeted by an
existing, tested feature. Two atlas-level aggregates are added because no
per-cell feature can express them: the SPREAD of ink widths (monospace) and the
mean aspect ratio (condensed / extended).

=== PRE-REGISTRATION, fixed before running ===

QUESTION      For each labelled attribute, does a rendered atlas carry it?
SAMPLE        Balanced positive/negative, at most CAP per class, ONE FILE PER
              (family, class) drawn deterministically by sorted name. A family
              may therefore appear on both sides -- an upright and an italic of
              the same face is the ideal minimal pair, differing in the labelled
              attribute and little else. It creates no leak because the split
              groups by family, so both land in the same fold.
STATISTIC     ROC AUC of a logistic regression on the feature vector, under
              GroupKFold by FAMILY. Never a random split: 32 of 50 holdout fonts
              share a superfamily with a training font, and that leak is a
              recorded defect of this repository's own benchmark.
BAR           Held-out AUC >= 0.75 => the atlas carries this attribute, and a
              classifier for it is worth building.
              0.60-0.75 => carried weakly; report, do not build on it alone.
              < 0.60 => not carried. Do not train on it.
SIGNIFICANCE  Label permutation within the sample, 2000 draws, reported beside
              the AUC. A large AUC on n=40 needs it; the bar above does not
              replace it.
RARE ATTRS    stencil / inline / outline have under 15 families each
              (`research/attribute_label_supply.json`). They are reported as
              DESCRIPTIVE ONLY, carry no bar, and no conclusion is drawn from
              them here. Synthesis is the registered route for those.
IF IT FAILS   An attribute below 0.60 is reported as not carried, and is
              dropped from the classifier rather than rescued with a different
              feature set on the same data.

  python analysis/attribute_separation.py
  python analysis/attribute_separation.py --cap 60 --json out.json
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
import os
import re
import warnings

import numpy as np
from PIL import Image

from analysis.attribute_label_supply import (NAME_ATTRS, PANOSE_LATIN_TEXT,
                                             PANOSE_SANS, PANOSE_SERIF,
                                             family_of)
from analysis.style_coherence import FEATURES, cell_features

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPPLY = os.path.join(REPO, "research", "attribute_label_supply.json")
CACHE = os.path.join(REPO, "eval_runs", "_attribute_atlases")

CAP = 50              # families per class; width and mono have ~50-59 available
PERM_ITERS = 2000
BAR_CARRIED, BAR_WEAK = 0.75, 0.60
RARE = ("stencil", "inline", "outline", "shadow", "slab", "rounded")

# Atlas-level aggregates. No per-cell feature can express either: monospace is a
# property of the SET of widths, and aspect needs a ratio the cell crop hides.
EXTRA = ("width_cv", "aspect")


def label_fns():
    """attribute -> (positive, negative) predicates over a scan record.

    Mirrors `attribute_label_supply.measure` exactly. Kept as one definition so
    the two tools cannot drift into labelling different things.
    """
    def latin_text(r):
        return r.get("panose_family") == PANOSE_LATIN_TEXT

    out = {
        "weight": (lambda r: r.get("weight", 400) >= 700,
                   lambda r: r.get("weight", 400) <= 300),
        "width": (lambda r: r.get("width", 5) <= 3,
                  lambda r: r.get("width", 5) == 5),
        "slant": (lambda r: abs(r.get("italic_angle", 0.0)) > 0.01,
                  lambda r: abs(r.get("italic_angle", 0.0)) <= 0.01),
        "serif vs sans": (lambda r: latin_text(r) and r.get("panose_serif") in PANOSE_SERIF,
                          lambda r: latin_text(r) and r.get("panose_serif") in PANOSE_SANS),
    }
    for name in ("mono",) + RARE:
        rx = re.compile(NAME_ATTRS[name], re.I)
        out[name] = (lambda r, rx=rx: bool(rx.search(r["stem"])),
                     lambda r, rx=rx: not rx.search(r["stem"]))
    return out


def atlas_path(pool, stem):
    """Render once, cache to disk. Rendering dominates the runtime."""
    from build_dataset import render_atlas

    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, f"{stem}.png")
    if os.path.isfile(out):
        return out
    src = None
    for ext in ("ttf", "otf"):
        hit = os.path.join(pool, f"{stem}.{ext}")
        if os.path.isfile(hit):
            src = hit
            break
    if src is None:
        return None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            render_atlas(src).save(out)
    except Exception:                                 # noqa: BLE001
        return None
    return out


def vector(path):
    """One feature vector per atlas: per-cell means, plus the two aggregates."""
    from atlas_constants import BLANK_INDICES, CHARSET
    from eval_checkpoint import crop_cell

    with Image.open(path) as im:
        arr = np.asarray(im.convert("L"))
    per_cell, widths, aspects = [], [], []
    for idx in range(len(CHARSET)):
        if idx in BLANK_INDICES:
            continue
        cell = crop_cell(arr, idx)
        cell = cell[:, :, 0] if cell.ndim == 3 else cell
        f = cell_features(cell)
        if f is None:
            continue
        per_cell.append([f[k] for k in FEATURES])
        ink = cell > 128
        rows, cols = np.where(ink)
        w = cols.max() - cols.min() + 1
        h = rows.max() - rows.min() + 1
        widths.append(float(w))
        aspects.append(float(w) / float(h))
    if len(per_cell) < 40:
        return None
    per_cell = np.asarray(per_cell, dtype=float)
    widths = np.asarray(widths, dtype=float)
    return np.concatenate([per_cell.mean(axis=0),
                           [float(widths.std() / widths.mean()),
                            float(np.mean(aspects))]])


def evaluate(X, y, groups, seed=0):
    """Held-out AUC under GroupKFold by family, plus a label permutation p."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import GroupKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    n_splits = min(5, len(set(groups)))
    if n_splits < 2 or len(set(y)) < 2:
        return None

    # Out-of-fold scores: every atlas is scored by a model that never saw its
    # family. The AUC below is computed once over these, not averaged per fold.
    pred = np.zeros(len(y), dtype=float)
    for tr, te in GroupKFold(n_splits=n_splits).split(X, y, groups):
        if len(set(y[tr])) < 2:
            return None
        model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
        model.fit(X[tr], y[tr])
        pred[te] = model.predict_proba(X[te])[:, 1]
    observed = float(roc_auc_score(y, pred))

    # The null permutes LABELS against the fixed out-of-fold scores. Refitting
    # the model 2000 times would be the stricter null and is prohibitive here;
    # for a rank statistic this one answers "could this ordering arise by
    # chance", which is the question the bar is about. The +1 correction means
    # a p of 0 can never be reported.
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
    ap.add_argument("--json", default=os.path.join(REPO, "research",
                                                   "attribute_separation.json"))
    args = ap.parse_args()

    from analysis.attribute_label_supply import EXCLUSIONS, scan

    exclude = set(json.load(open(EXCLUSIONS, encoding="utf-8"))["exclude_stems"])
    print("reading the pool ...")
    records, _ = scan(args.pool, exclude)
    print(f"  {len(records)} licence-clean files\n")

    results = {}
    for attr, (pos_fn, neg_fn) in label_fns().items():
        # Labels are per FILE; the leak guard is GROUPING by family, not family
        # purity. Requiring a family to be all-positive or all-negative would
        # discard nearly every family for slant, because most ship an upright
        # and an italic. Keeping both is strictly better: the pair differs in
        # the labelled attribute and in nothing else, which is the minimal pair
        # the CLIP test had to construct by hand.
        #
        # One file per (family, side), so a large superfamily cannot dominate.
        rep = {}
        for rec in records:
            side = 1 if pos_fn(rec) else (0 if neg_fn(rec) else None)
            if side is None:
                continue
            key = (rec["family"], side)
            if key not in rep or rec["stem"] < rep[key]:
                rep[key] = rec["stem"]

        pos = sorted((fam, stem) for (fam, s), stem in rep.items() if s == 1)
        neg = sorted((fam, stem) for (fam, s), stem in rep.items() if s == 0)
        take = min(args.cap, len(pos), len(neg))
        if take < 5:
            results[attr] = {"skipped": "too few families",
                             "pos_families": len(pos), "neg_families": len(neg)}
            print(f"{attr:<16} skipped: {len(pos)} pos / {len(neg)} neg families")
            continue
        chosen = ([(stem, 1) for _, stem in pos[:take]] +
                  [(stem, 0) for _, stem in neg[:take]])

        X, y, groups = [], [], []
        for stem, label in chosen:
            path = atlas_path(args.pool, stem)
            if path is None:
                continue
            v = vector(path)
            if v is None:
                continue
            X.append(v)
            y.append(label)
            groups.append(family_of(stem))
        if len(set(y)) < 2:
            results[attr] = {"skipped": "one class after rendering"}
            continue
        res = evaluate(np.asarray(X), np.asarray(y), groups)
        if res is None:
            results[attr] = {"skipped": "cross-validation not possible"}
            continue
        res["rare"] = attr in RARE
        res["verdict"] = ("descriptive only" if attr in RARE else
                          "carried" if res["auc"] >= BAR_CARRIED else
                          "weak" if res["auc"] >= BAR_WEAK else "NOT carried")
        results[attr] = res
        print(f"{attr:<16} AUC {res['auc']:.3f}  p={res['p']:.4f}  "
              f"n={res['n']:<4} families={res['families']:<4} {res['verdict']}")

    payload = {"preregistered": True, "cap": args.cap,
               "bar_carried": BAR_CARRIED, "bar_weak": BAR_WEAK,
               "features": list(FEATURES) + list(EXTRA), "attributes": results}
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
