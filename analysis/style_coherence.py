"""A ground-truth-free measure of whether an atlas is ONE typeface.

WHY THIS IS THE MISSING INSTRUMENT. The product concept has the user describe a
style, a generative model draw the two reference characters, and the user select
and iterate. There is then no target font -- so char_acc, DINOv2, LPIPS, R-ACC
and composite, all of which compare against a ground-truth atlas, cannot score
it at all. Only identity survives, and identity is blind to the failure that
actually happens.

THE FAILURE IT HAS TO CATCH. Given a reference whose two glyphs disagree on
style, the model transfers both: it emits a light `H` then bold `amburg`, or
keeps inline striping on the `H` and loses it elsewhere. Every letter is the
right letter, so identity scored that 0.9034 against a coherent control's 0.8910
-- ABOVE it. See research/2026-08-21-two-styles-in-two-styles-out.md.

WHY THE OBVIOUS MEASURE FAILED, AND WHAT THAT DICTATES. The first attempt was
the spread of ink fraction across cells. It returned p=0.970 on the labelled
set. Two reasons, and the design here follows from both:

  1. LETTER IDENTITY DOMINATES. `.` and `M` differ enormously for reasons that
     have nothing to do with style. So every feature is z-scored against that
     CHARACTER's distribution over a population of real fonts, and only the
     residual is style. THIS IS THE FIX. It is the whole difference between
     p=0.970 and p=0.0021.
  2. A SECOND HYPOTHESIS, WHICH WAS WRONG AND IS KEPT AS THE RECORD. The defect
     looked bimodal -- the atlas splits into a K-like group and a g-like group --
     so a two-means separation should have beaten plain dispersion. It does not:
     `split` scores p=0.313 and `split_max` p=0.072, while `dispersion` clears
     both gates. The shape of the statistic did not matter; removing the
     character effect did. Both are still reported, so the claim stays checkable.

VALIDATED TWICE, INDEPENDENTLY, on 50 fonts (`--validate`):

  paired      oracle 0.3368 vs mixed 0.4064   p=0.0021  r=0.435
  severity    Spearman rho = +0.407           p=0.0034

The second is the stronger evidence: the labels are GRADED, running from
serif-meets-dot-grid to sans-meets-sans, and the measure tracks that severity
rather than merely separating two groups.

AT n=12 NEITHER REACHED SIGNIFICANCE (p=0.176 and p=0.170) while the effect
sizes were already r=0.408 and rho=0.424. The effects barely moved on the way to
n=50; only the power did. That is the shape of an underpowered comparison, and
recognising it rather than concluding from it is why this section exists.

FEATURES, chosen to be interpretable and to target what was observed -- a weight
split, a slant, and a solid-versus-dot-grid texture change:

  stroke   mean stroke half-width from the distance transform, x2
  slant    shear angle from second-order image moments
  fill     ink area over bounding-box area
  parts    log connected-component count (dot-grid vs solid strokes)

  python analysis/style_coherence.py --fit
  python analysis/style_coherence.py --validate
  python analysis/style_coherence.py --score eval_runs/<run>/generated
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import json
import os
import random

import numpy as np
from PIL import Image
from scipy import ndimage

from atlas_constants import BLANK_INDICES, CHARSET

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(REPO, "dataset_v2", "atlases")
STATS = os.path.join(REPO, "research", "style_feature_stats.json")
PROBE = os.path.join(REPO, "eval_runs", "_synthetic_probe")
GT_ATLASES = os.path.join(REPO, "eval_holdout", "atlases")
REF_MANIFEST = os.path.join(REPO, "eval_runs", "_synthetic_refs", "manifest.json")

DRAWN = [i for i in range(len(CHARSET)) if i not in BLANK_INDICES]
FEATURES = ("stroke", "slant", "fill", "parts")
MIN_INK = 12          # a cell with less ink than this carries no style signal


def cell_features(cell):
    """Style features for one glyph cell. None when there is too little ink.

    Ink is the BRIGHT fraction: these atlases are light glyphs on a dark ground,
    and measuring dark pixels returns ~0.93 and looks plausible
    (analysis/measure_ink.py documents that trap).
    """
    ink = cell > 128
    n = int(ink.sum())
    if n < MIN_INK:
        return None

    rows, cols = np.where(ink)
    h = rows.max() - rows.min() + 1
    w = cols.max() - cols.min() + 1

    # Stroke thickness: the distance transform peaks at a stroke's spine, so
    # twice its mean over ink is an average stroke width. Normalised by glyph
    # height so it is a proportion of the letter, not of the cell.
    dist = ndimage.distance_transform_edt(ink)
    stroke = float(2.0 * dist[ink].mean() / h)

    # Slant from second-order central moments: mu11/mu02 is the shear that maps
    # an upright glyph onto this one.
    ys, xs = rows.astype(float), cols.astype(float)
    yc, xc = ys.mean(), xs.mean()
    mu02 = float(((ys - yc) ** 2).mean())
    mu11 = float(((ys - yc) * (xs - xc)).mean())
    slant = float(mu11 / mu02) if mu02 > 1e-6 else 0.0

    fill = float(n / (h * w))
    parts = float(np.log1p(ndimage.label(ink)[1]))
    return {"stroke": stroke, "slant": slant, "fill": fill, "parts": parts}


def atlas_features(path):
    """char -> features, for every drawn cell of one atlas."""
    from eval_checkpoint import crop_cell
    with Image.open(path) as im:
        arr = np.asarray(im.convert("RGB"))
    out = {}
    for idx in DRAWN:
        f = cell_features(crop_cell(arr, idx)[:, :, 0])
        if f is not None:
            out[CHARSET[idx]] = f
    return out


def fit(sample, seed):
    """Per-character feature mean/SD over real corpus fonts."""
    paths = sorted(glob.glob(os.path.join(CORPUS, "*.png")))
    if not paths:
        print(f"no corpus atlases at {CORPUS}", file=_sys.stderr)
        return None
    random.Random(seed).shuffle(paths)
    paths = paths[:sample] if sample else paths

    acc = {c: {f: [] for f in FEATURES} for c in CHARSET}
    for i, p in enumerate(paths, 1):
        for ch, feats in atlas_features(p).items():
            for f in FEATURES:
                acc[ch][f].append(feats[f])
        if i % 50 == 0:
            print(f"  fitted {i}/{len(paths)} fonts", flush=True)

    stats = {}
    for ch, per_f in acc.items():
        if len(per_f["stroke"]) < 20:
            continue
        stats[ch] = {f: {"mean": float(np.mean(per_f[f])),
                         "sd": float(np.std(per_f[f]) or 1e-6)}
                     for f in FEATURES}
    payload = {
        "_comment": ("TRACKED. Per-character style-feature statistics over real "
                     "corpus fonts. analysis/style_coherence.py z-scores each "
                     "cell against ITS OWN character here, so the residual is "
                     "style rather than letter identity -- the confound that "
                     "made the first coherence attempt return p=0.970."),
        "n_fonts": len(paths), "features": list(FEATURES), "chars": stats,
    }
    with open(STATS, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {STATS}  ({len(stats)} characters, {len(paths)} fonts)")
    return payload


def load_stats():
    if not os.path.isfile(STATS):
        raise SystemExit(f"missing {STATS} -- run --fit first")
    return json.load(open(STATS, encoding="utf-8"))["chars"]


def score_atlas(path, stats):
    """Incoherence scores for one atlas. Higher means less like one typeface."""
    feats = atlas_features(path)
    rows = []
    for ch, f in feats.items():
        s = stats.get(ch)
        if not s:
            continue
        rows.append([(f[k] - s[k]["mean"]) / s[k]["sd"] for k in FEATURES])
    if len(rows) < 20:
        return None
    z = np.asarray(rows, dtype=float)
    z = np.clip(z, -8, 8)          # a single wild cell must not set the score

    # dispersion: a coherent font has ONE weight and ONE slant, so its residuals
    # sit still. Averaged over features.
    dispersion = float(np.mean(z.std(axis=0)))

    # split: two-means separation per feature, in SD units. This is the shape
    # the observed defect actually has -- the atlas divides into a K-like and a
    # g-like group rather than simply becoming noisier.
    splits = []
    for j in range(z.shape[1]):
        v = np.sort(z[:, j])
        best = 0.0
        for cut in range(3, len(v) - 3):
            lo, hi = v[:cut], v[cut:]
            pooled = np.sqrt((lo.var() + hi.var()) / 2) or 1e-6
            best = max(best, abs(hi.mean() - lo.mean()) / pooled)
        splits.append(best)
    return {"dispersion": dispersion, "split": float(np.mean(splits)),
            "split_max": float(np.max(splits)), "n_cells": int(z.shape[0])}


def style_vector(font, stats):
    """A real font's mean z-scored style vector, from its GT atlas."""
    path = os.path.join(GT_ATLASES, font + ".png")
    if not os.path.isfile(path):
        return None
    rows = []
    for ch, f in atlas_features(path).items():
        s = stats.get(ch)
        if s:
            rows.append([(f[k] - s[k]["mean"]) / s[k]["sd"] for k in FEATURES])
    if len(rows) < 20:
        return None
    return np.clip(np.asarray(rows), -8, 8).mean(axis=0)


def severity_check(stats, per_arm):
    """Second, independent validation: does incoherence track HOW mismatched
    each pair was?

    The labels are graded, not binary -- the pairings run from
    serif-meets-dot-grid to sans-meets-sans. Severity is the distance between
    the two SOURCE fonts' style vectors. A measure that separates the arms but
    ignores severity would be suspect; one that does both is hard to explain
    by anything other than working.
    """
    if not os.path.isfile(REF_MANIFEST):
        return None
    partners = json.load(open(REF_MANIFEST, encoding="utf-8")).get("mixed_partners")
    if not partners:
        return None
    from scipy import stats as sstats

    sev, delta = [], []
    for font, partner in partners.items():
        if font not in per_arm.get("oracle", {}) or font not in per_arm.get("mixed", {}):
            continue
        a, b = style_vector(font, stats), style_vector(partner, stats)
        if a is None or b is None:
            continue
        sev.append(float(np.linalg.norm(a - b)))
        delta.append(per_arm["mixed"][font]["dispersion"]
                     - per_arm["oracle"][font]["dispersion"])
    if len(sev) < 10:
        return None
    rho, p = sstats.spearmanr(sev, delta)
    print("\nseverity check: does incoherence track HOW mismatched the pair was?")
    print(f"  Spearman rho = {rho:+.3f}   p = {p:.4f}   n = {len(sev)}")
    print("  (independent of the paired test above -- graded, not binary)")
    return {"spearman_rho": float(rho), "p": float(p), "n": len(sev)}


def validate(stats):
    """Does it separate the labelled set? oracle = coherent, mixed = not."""
    out = {}
    for arm in ("oracle", "mixed", "perturbed"):
        d = os.path.join(PROBE, arm)
        if not os.path.isdir(d):
            continue
        out[arm] = {}
        for p in sorted(glob.glob(os.path.join(d, "*.png"))):
            s = score_atlas(p, stats)
            if s:
                out[arm][os.path.splitext(os.path.basename(p))[0]] = s
    if "oracle" not in out or "mixed" not in out:
        print("need the oracle and mixed arms; run the probe first", file=_sys.stderr)
        return None

    from analysis.compare_runs import paired_wilcoxon
    print("\nlabelled set: oracle = one real font, mixed = two superfamilies\n")
    print(f"  {'metric':<12} {'oracle':>9} {'mixed':>9} {'perturbed':>10} "
          f"{'p':>8} {'r':>7}  verdict")
    results = []
    for metric in ("dispersion", "split", "split_max"):
        shared = sorted(set(out["oracle"]) & set(out["mixed"]))
        a = [out["oracle"][f][metric] for f in shared]
        b = [out["mixed"][f][metric] for f in shared]
        res = paired_wilcoxon(a, b)
        sig = res.p < 0.05 and res.effect_r >= 0.3
        detects = sig and float(np.mean(b)) > float(np.mean(a))
        pert = (float(np.mean([v[metric] for v in out["perturbed"].values()]))
                if out.get("perturbed") else float("nan"))
        print(f"  {metric:<12} {np.mean(a):>9.4f} {np.mean(b):>9.4f} "
              f"{pert:>10.4f} {res.p:>8.4f} {res.effect_r:>7.3f}  "
              f"{'DETECTS incoherence' if detects else 'no'}")
        results.append({"metric": metric, "oracle": float(np.mean(a)),
                        "mixed": float(np.mean(b)), "p": res.p,
                        "effect_r": res.effect_r, "detects": bool(detects),
                        "n": len(shared)})

    print("\n  for scale, the measure this replaces -- ink CV -- scored p=0.970")
    severity = severity_check(stats, out)
    return {"per_arm": out, "results": results, "severity": severity}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fit", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--score", help="directory of atlases to score")
    ap.add_argument("--sample", type=int, default=250, help="fonts for --fit")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--json")
    args = ap.parse_args()

    if args.fit and fit(args.sample, args.seed) is None:
        return 2
    if not (args.validate or args.score):
        return 0

    stats = load_stats()
    payload = None
    if args.validate:
        payload = validate(stats)
        if payload is None:
            return 3
    if args.score:
        rows = {}
        for p in sorted(glob.glob(os.path.join(args.score, "*.png"))):
            s = score_atlas(p, stats)
            if s:
                rows[os.path.splitext(os.path.basename(p))[0]] = s
        print(f"\nscored {len(rows)} atlases in {args.score}")
        for k in ("dispersion", "split"):
            print(f"  mean {k:<12} {np.mean([v[k] for v in rows.values()]):.4f}")
        payload = {"scored": rows}

    if args.json and payload:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=1)
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
