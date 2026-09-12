"""Reject a reference whose two glyphs disagree, BEFORE spending a generation.

WHY IT IS A SEPARATE MODULE FROM style_coherence.py. That one measures
DISPERSION over 94 atlas cells. A reference carries TWO glyphs, where dispersion
is meaningless -- what it needs is the DISTANCE between two style vectors. Same
features, different statistic, different input. Calling them "one measure" was
loose; they are two.

WHY IT EXISTS. The model transfers whatever style it is given. Hand it two
glyphs that disagree and it splits the atlas along the K-like / g-like seam,
emitting a light `H` then bold `amburg`
(research/2026-08-21-two-styles-in-two-styles-out.md). Identity scored that
0.9034 against a coherent control's 0.8910 -- ABOVE it -- so nothing downstream
catches it. Catching it at the reference costs milliseconds; catching it after
costs a generation.

DOMAIN NOTE, and it is load-bearing. The per-character statistics are fitted on
106x160 ATLAS cells; a reference column is 640x1280. The features are mostly
scale-normalised -- `stroke` divides by glyph height, `slant` and `fill` are
ratios -- but the distance transform and the connected-component count still
behave differently at six times the resolution. So each reference glyph is
trimmed to its ink and rescaled to atlas-cell proportions before features are
taken. Skipping that compares numbers from two different domains.

  python analysis/reference_gate.py --validate
  python analysis/reference_gate.py --score path/to/reference.png
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

from atlas_constants import CELL_H, CELL_W
from analysis.style_coherence import FEATURES, MIN_INK, cell_features, load_stats

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS_DIR = os.path.join(REPO, "eval_runs", "_synthetic_refs")
VALIDATION = os.path.join(REPO, "research", "style_coherence_validation.json")

REF_TARGET_H = 100          # a typical cap height inside a 160px atlas cell


def glyph_cells(path, n_cols=2):
    """Split a reference image into per-glyph cells AT ATLAS RESOLUTION."""
    with Image.open(path) as im:
        arr = np.asarray(im.convert("L"))
    col_w = arr.shape[1] // n_cols
    out = []
    for i in range(n_cols):
        col = arr[:, i * col_w:(i + 1) * col_w]
        ink = col > 128
        if ink.sum() < MIN_INK:
            out.append(None)
            continue
        rows, cols = np.where(ink)
        glyph = col[rows.min():rows.max() + 1, cols.min():cols.max() + 1]
        gh, gw = glyph.shape
        scale = REF_TARGET_H / gh
        small = np.asarray(Image.fromarray(glyph).resize(
            (max(1, round(gw * scale)), max(1, round(gh * scale))), Image.LANCZOS))
        sh, sw = small.shape
        if sh > CELL_H or sw > CELL_W:          # very wide glyph: fit the cell
            f = min(CELL_H / sh, CELL_W / sw)
            small = np.asarray(Image.fromarray(small).resize(
                (max(1, int(sw * f)), max(1, int(sh * f))), Image.LANCZOS))
            sh, sw = small.shape
        canvas = np.zeros((CELL_H, CELL_W), dtype=np.uint8)
        y0, x0 = (CELL_H - sh) // 2, (CELL_W - sw) // 2
        canvas[y0:y0 + sh, x0:x0 + sw] = small
        out.append(canvas)
    return out


def reference_consistency(path, stats, chars="Kg"):
    """How far apart the reference's glyphs are in style. Higher is worse.

    `chars` must be what the image actually contains: each glyph is z-scored
    against ITS OWN character. The shipped holdout references render "Kg" while
    build_dataset.REF_CHARS and the checkpoints' conditioning both say "Rg" --
    the documented train/eval mismatch, immaterial to generation (p=0.625) and
    decisive here.
    """
    cells = glyph_cells(path, len(chars))
    vecs = []
    for ch, cell in zip(chars, cells):
        if cell is None:
            return None
        f, s = cell_features(cell), stats.get(ch)
        if f is None or s is None:
            return None
        vecs.append([(f[k] - s[k]["mean"]) / s[k]["sd"] for k in FEATURES])
    a, b = np.clip(np.asarray(vecs, dtype=float), -8, 8)
    return {"distance": float(np.linalg.norm(a - b)),
            "per_feature": {k: float(abs(a[i] - b[i]))
                            for i, k in enumerate(FEATURES)}}


def validate(stats, chars):
    """Does the REFERENCE score predict the ATLAS it produces?

    Everything needed is already on disk: 50 oracle and 50 mixed references,
    and the dispersion each produced. Separation alone would only describe;
    prediction is what makes it a gate.
    """
    from scipy import stats as sstats
    from analysis.compare_runs import paired_wilcoxon

    if not os.path.isfile(VALIDATION):
        print(f"missing {VALIDATION} -- run style_coherence.py --validate first",
              file=_sys.stderr)
        return None
    per_arm = json.load(open(VALIDATION, encoding="utf-8"))["per_arm"]

    rows = {}
    for arm in ("oracle", "mixed"):
        rows[arm] = {}
        for name, atlas in per_arm.get(arm, {}).items():
            ref = os.path.join(REFS_DIR, arm, name + ".png")
            if not os.path.isfile(ref):
                continue
            rc = reference_consistency(ref, stats, chars)
            if rc:
                rows[arm][name] = {"reference_distance": rc["distance"],
                                   "atlas_dispersion": atlas["dispersion"]}
    if len(rows.get("mixed", {})) < 10:
        print("not enough scored references", file=_sys.stderr)
        return None

    print(f"\nreference-consistency gate   chars={chars!r}\n")
    for arm in ("oracle", "mixed"):
        d = [v["reference_distance"] for v in rows[arm].values()]
        print(f"  {arm:<8} distance  mean {np.mean(d):.3f}  "
              f"median {np.median(d):.3f}  n={len(d)}")

    shared = sorted(set(rows["oracle"]) & set(rows["mixed"]))
    a = [rows["oracle"][f]["reference_distance"] for f in shared]
    b = [rows["mixed"][f]["reference_distance"] for f in shared]
    res = paired_wilcoxon(a, b)
    separates = bool(res.p < 0.05 and res.effect_r >= 0.3
                     and np.mean(b) > np.mean(a))
    print(f"\n  separates the arms   p={res.p:.4f}  r={res.effect_r:.3f}  "
          f"{'YES' if separates else 'no'}   n={len(shared)}")

    allrows = list(rows["oracle"].values()) + list(rows["mixed"].values())
    x = [v["reference_distance"] for v in allrows]
    y = [v["atlas_dispersion"] for v in allrows]
    rho, p = sstats.spearmanr(x, y)
    print(f"  predicts the atlas   rho={rho:+.3f}  p={p:.4f}   n={len(x)}")
    print("  (prediction is what makes this a gate rather than a description)")

    coherent = [v["reference_distance"] for v in rows["oracle"].values()]
    mixed = [v["reference_distance"] for v in rows["mixed"].values()]
    print("\n  PROVISIONAL operating points, cut from the COHERENT spread:\n")
    print(f"    {'percentile':>10} {'threshold':>10} {'catches':>9} {'rejects ok':>11}")
    points = []
    for q in (99, 95, 90, 80, 75):
        thr = float(np.percentile(coherent, q))
        recall = float(np.mean([d > thr for d in mixed]))
        fpr = float(np.mean([d > thr for d in coherent]))
        print(f"    {q:>10} {thr:>10.3f} {recall:>9.0%} {fpr:>11.0%}")
        points.append({"percentile": q, "threshold": thr,
                       "recall_on_mixed": recall,
                       "false_positive_on_coherent": fpr})

    print("\n    Provisional BY CONSTRUCTION: cut from the coherent spread, not")
    print("    from references a human judged unacceptable. That set does not exist.")
    print("    Recall is also a FLOOR, not a ceiling: `mixed` includes benign")
    print("    pairings -- sans meeting sans -- that produce a usable font and")
    print("    SHOULD pass. A perfect gate would not catch 100% of this label.")

    default = next(p_ for p_ in points if p_["percentile"] == 90)
    return {"chars": chars, "rows": rows, "separates": separates,
            "separation": {"p": res.p, "effect_r": res.effect_r, "n": len(shared)},
            "predicts": {"spearman_rho": float(rho), "p": float(p), "n": len(x)},
            "operating_points": points, "suggested": default}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--score", help="a reference PNG, or a directory of them")
    ap.add_argument("--ref-chars", default="Kg",
                    help="what the reference images actually contain")
    ap.add_argument("--json")
    args = ap.parse_args()
    if not (args.validate or args.score):
        ap.error("nothing to do: pass --validate or --score")

    stats = load_stats()
    payload = None
    if args.validate:
        payload = validate(stats, args.ref_chars)
        if payload is None:
            return 3
    if args.score:
        paths = ([args.score] if os.path.isfile(args.score)
                 else sorted(glob.glob(os.path.join(args.score, "*.png"))))
        scored = {}
        for p in paths:
            rc = reference_consistency(p, stats, args.ref_chars)
            if rc:
                scored[os.path.basename(p)] = rc
                worst = max(rc["per_feature"], key=rc["per_feature"].get)
                print(f"  {os.path.basename(p)[:44]:<46} "
                      f"{rc['distance']:>6.3f}   worst: {worst}")
        payload = {"scored": scored}

    if args.json and payload:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=1)
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
