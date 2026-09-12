"""Can a measure tell a stencil BREAK from an inline STRIPE? Train it to.

PRE-REGISTERED, committed before the tool was executed.

WHY THIS EXISTS. `attribute_transfer.py` passed its primary and its descriptive
column killed the interpretation: **the stencil model's favourite generated
atlas was the INLINE one**, and the outline was second. `style_coherence`'s
`parts` counts connected components of ink, so it reads "in many pieces" -- and
a break, a stripe and a hollow contour are all many pieces. More data cannot fix
a feature that cannot express the difference.

THE DIFFERENCE IS TOPOLOGICAL, AND CHEAP.

  style     components   holes
  solid     few          counters only
  stencil   UP           flat        -- strokes cut crosswise
  inline    flat/up      UP          -- a stripe enclosed inside the stroke
  outline   flat         WAY UP      -- every stroke becomes a ring

Components alone conflate all three. Components VERSUS holes separate them, and
a hole count is one `binary_fill_holes`. Two features are therefore added here:
`holes` and `hole_area`.

THIS IS NOT THE MOVE THAT WAS REFUSED YESTERDAY. `attribute_separation.py`
returned serif-vs-sans at 0.733 and its registration forbade rescuing it with a
different feature set ON THE SAME DATA, so no terminal-shape feature was added.
This is a NEW registration, for a DIFFERENT attribute set, whose primary runs on
data the model never sees. The distinction is the whole of the difference
between adding a feature and moving a goalpost.

AND THE NEGATIVES ARE EACH OTHER. A stencil classifier whose negatives are
Roboto and Lato learns "many pieces". Here every class is synthesised from THE
SAME source faces, so the typeface is controlled for and the only thing left to
learn is the treatment.

=== PRE-REGISTRATION, fixed before running ===

TRAINING      SOURCES source families carrying no rare-attribute keyword, one
              file each, sorted deterministically. Each is rendered once and
              transformed four ways -- solid / stencil / inline / outline -- so
              labels are exact by construction and the face is held constant
              across classes. Transform parameters are drawn per source from a
              fixed seed, never per class.
MODEL         Multinomial logistic regression on eight features: the six from
              `attribute_separation.vector` plus `holes` and `hole_area`.
PRIMARY       The 11 REAL superfamilies the pool actually contains -- 5 stencil,
              6 inline -- none of them ever seen in training, collapsed to
              SUPERFAMILY because `BigShouldersStencil*` and
              `BigShouldersInline*` are one typeface and three Sairas are
              another. For each, take the larger of P(stencil) and P(inline).
BAR           >= 9 of 11 correct. Exact binomial one-sided against p=0.5:
              9/11 = 0.0327, 10/11 = 0.0059, 11/11 = 0.0005. Below 9 is a
              failure.
              **BigShoulders appears on BOTH sides** -- the same face with a
              stencil treatment and an inline treatment. That pair is the
              hardest in the set and is deliberately kept.
THE RISK      A classifier can learn MY TRANSFORM'S ARTIFACTS instead of the
              attribute: a band eraser makes grid-aligned gaps, where a real
              designer breaks strokes at junctions. Accuracy on held-out
              SYNTHETIC data is therefore DESCRIPTIVE ONLY and proves nothing.
              Randomising band angle, period and phase is a mitigation, not a
              proof. The 11 real faces are the only evidence.
OUTLINE       Untestable on real data -- the pool holds 3 outline families. It
              is trained as a class because it is a needed hard negative, and no
              claim is made about it.
IF IT FAILS   Reported as a failure. The transforms are NOT retuned against
              those 11 and re-run; that would make the primary a training set.

  python analysis/synthesize_rare_attributes.py
  python analysis/synthesize_rare_attributes.py --sources 80
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import json
import os
import re

import numpy as np
from PIL import Image
from scipy import ndimage

from analysis.attribute_label_supply import EXCLUSIONS, NAME_ATTRS, scan
from analysis.attribute_separation import atlas_path
from analysis.style_coherence import FEATURES, cell_features

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED = os.path.join(REPO, "eval_runs", "_synthetic_probe", "external")

CLASSES = ("solid", "stencil", "inline", "outline")
SOURCES = 60
SEED = 0
RARE_RX = re.compile("|".join(NAME_ATTRS[k] for k in
                              ("stencil", "inline", "outline", "shadow")), re.I)
EXTRA = ("width_cv", "aspect", "holes", "hole_area")


def superfamily(stem):
    """`BigShouldersStencilDisplaySC` and `BigShouldersInlineText` are ONE face.

    Splitting on '-' as `family_of` does would call those two different
    families and let the same typeface sit on both sides of the primary as if
    it were independent evidence.
    """
    m = RARE_RX.search(stem)
    head = stem[:m.start()] if m else stem
    return re.sub(r"[^a-z0-9]", "", head.lower()) or stem.lower()


# --- the transforms, applied per CELL in cell-local coordinates ------------
# Per cell, not per atlas: a real stencil breaks at consistent positions
# relative to the LETTER, not to the sheet it happens to be printed on.

def draw_params(rng):
    """One draw per SOURCE FACE, reused for every cell of that atlas.

    Drawing per cell would break each letter at a different height, which no
    real stencil font does -- the breaks sit at consistent positions relative to
    the baseline across the whole alphabet. Per-cell noise would also hand the
    classifier an easy giveaway that has nothing to do with the attribute.
    """
    return {"theta": float(rng.uniform(-0.6, 0.6)
                           + rng.choice([0.0, np.pi / 2])),
            "period": float(rng.uniform(0.16, 0.30)),
            "phase": float(rng.uniform(0.0, 1.0)),
            "band": float(rng.uniform(0.16, 0.30)),
            "spine": float(rng.uniform(0.55, 0.78)),
            "erode": int(rng.integers(2, 4))}


def _stencil(ink, p):
    """Erase bands across the strokes, at one angle and period per face."""
    h, w = ink.shape
    period = max(p["period"] * h, 3.0)
    ys, xs = np.mgrid[0:h, 0:w]
    proj = xs * np.cos(p["theta"]) + ys * np.sin(p["theta"])
    return ink & ~(((proj + p["phase"] * period) % period) < p["band"] * period)


def _inline(ink, p):
    """Remove the stroke's SPINE, leaving a light stripe inset within it."""
    if not ink.any():
        return ink
    dist = ndimage.distance_transform_edt(ink)
    peak = float(dist.max())
    if peak < 2.0:                       # a hairline has no interior to inset
        return ink
    return ink & ~(dist >= p["spine"] * peak)


def _outline(ink, p):
    """Keep a contour ring, hollow the interior."""
    return ink & ~ndimage.binary_erosion(ink, iterations=p["erode"])


TRANSFORMS = {"solid": lambda ink, p: ink,
              "stencil": _stencil, "inline": _inline, "outline": _outline}


def apply_transform(arr, name, params):
    """Transform every drawn cell of one atlas, on a copy."""
    from atlas_constants import (BLANK_INDICES, CELL_H, CELL_W, CHARSET,
                                 GRID_COLS)

    out = arr.copy()
    fn = TRANSFORMS[name]
    for idx in range(len(CHARSET)):
        if idx in BLANK_INDICES:
            continue
        r, c = idx // GRID_COLS, idx % GRID_COLS
        y0, x0 = r * CELL_H, c * CELL_W
        cell = out[y0:y0 + CELL_H, x0:x0 + CELL_W]
        kept = fn(cell > 128, params)
        out[y0:y0 + CELL_H, x0:x0 + CELL_W] = np.where(kept, cell, 0)
    return out


# --- features: the six that exist, plus the two topology terms ------------

def atlas_cells(arr, indices=None):
    """The drawn cells of an atlas array, in order."""
    from atlas_constants import BLANK_INDICES, CELL_H, CELL_W, CHARSET, GRID_COLS

    wanted = range(len(CHARSET)) if indices is None else indices
    out = []
    for idx in wanted:
        if idx in BLANK_INDICES:
            continue
        r, c = idx // GRID_COLS, idx % GRID_COLS
        out.append(arr[r * CELL_H:(r + 1) * CELL_H, c * CELL_W:(c + 1) * CELL_W])
    return out


def vector_from_cells(cells, min_cells=40):
    """Eight features from a list of glyph cells.

    Split out from `vector_ext` so the SAME features can be computed from the
    two cells of a reference image, which is what the product actually shows a
    user. `reference_gate.glyph_cells` returns cells in this same 106x160 space,
    so the two paths are comparable.
    """
    per_cell, widths, aspects, holes, hole_area = [], [], [], [], []
    for cell in cells:
        if cell is None:
            continue
        f = cell_features(cell)
        if f is None:
            continue
        per_cell.append([f[k] for k in FEATURES])
        ink = cell > 128
        rows, cols = np.where(ink)
        cw = cols.max() - cols.min() + 1
        ch = rows.max() - rows.min() + 1
        widths.append(float(cw))
        aspects.append(float(cw) / float(ch))
        # A hole is background enclosed by ink. `binary_fill_holes` finds
        # exactly that, and the difference from the ink is the holes.
        filled = ndimage.binary_fill_holes(ink)
        gap = filled & ~ink
        holes.append(float(np.log1p(ndimage.label(gap)[1])))
        hole_area.append(float(gap.sum()) / float(max(filled.sum(), 1)))
    if len(per_cell) < min_cells:
        return None
    per_cell = np.asarray(per_cell, dtype=float)
    widths = np.asarray(widths, dtype=float)
    # width_cv over a single cell is 0/0; a two-cell reference is the case that
    # matters, and there it is a real if noisy quantity.
    cv = float(widths.std() / widths.mean()) if len(widths) > 1 else 0.0
    return np.concatenate([per_cell.mean(axis=0),
                           [cv,
                            float(np.mean(aspects)),
                            float(np.mean(holes)),
                            float(np.mean(hole_area))]])


def vector_ext(arr, indices=None, min_cells=40):
    """Eight features from an atlas ARRAY, so a transform needs no round trip."""
    return vector_from_cells(atlas_cells(arr, indices), min_cells)


def load(path):
    with Image.open(path) as im:
        return np.asarray(im.convert("L"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pool", default=os.path.join(REPO, "font_pool"))
    ap.add_argument("--sources", type=int, default=SOURCES)
    ap.add_argument("--generated", default=GENERATED)
    ap.add_argument("--json", default=os.path.join(REPO, "research",
                                                   "synthesize_rare_attributes.json"))
    args = ap.parse_args()

    from scipy import stats
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    exclude = set(json.load(open(EXCLUSIONS, encoding="utf-8"))["exclude_stems"])
    print("reading the pool ...")
    records, _ = scan(args.pool, exclude)

    # REAL held-out set: every stencil and inline superfamily, one file each.
    real = {}
    for rec in records:
        stem = rec["stem"]
        for label in ("stencil", "inline"):
            if re.search(NAME_ATTRS[label], stem, re.I):
                key = (superfamily(stem), label)
                if key not in real or stem < real[key]:
                    real[key] = stem
    held_out_faces = {superfamily(s) for s in real.values()}
    print(f"  real held-out: {sum(1 for k in real if k[1] == 'stencil')} stencil"
          f" + {sum(1 for k in real if k[1] == 'inline')} inline superfamilies")

    # SOURCES: no rare keyword, and never a held-out face.
    seen, sources = set(), []
    for rec in sorted(records, key=lambda r: r["stem"]):
        fam = rec["family"]
        if fam in seen or RARE_RX.search(rec["stem"]):
            continue
        if superfamily(rec["stem"]) in held_out_faces:
            continue
        seen.add(fam)
        sources.append(rec["stem"])
        if len(sources) >= args.sources:
            break
    print(f"  synthesis sources: {len(sources)} families\n")

    rng = np.random.default_rng(SEED)
    X, y, groups = [], [], []
    for stem in sources:
        path = atlas_path(args.pool, stem)
        if path is None:
            continue
        arr = load(path)
        # One parameter draw per SOURCE, reused across all four classes, so the
        # four variants of one face differ only in the transform applied.
        params = draw_params(rng)
        for label in CLASSES:
            v = vector_ext(apply_transform(arr, label, params))
            if v is None:
                continue
            X.append(v)
            y.append(CLASSES.index(label))
            groups.append(stem)
    X, y = np.asarray(X), np.asarray(y)
    print(f"  training set: {len(y)} atlases, {len(set(y))} classes")

    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000))
    model.fit(X, y)

    # --- PRIMARY: the 11 real superfamilies -------------------------------
    i_sten, i_inl = CLASSES.index("stencil"), CLASSES.index("inline")
    rows, correct = [], 0
    for (face, label), stem in sorted(real.items()):
        path = atlas_path(args.pool, stem)
        if path is None:
            continue
        v = vector_ext(load(path))
        if v is None:
            rows.append({"face": face, "true": label, "skipped": "unscoreable"})
            continue
        prob = model.predict_proba(v.reshape(1, -1))[0]
        pred = "stencil" if prob[i_sten] >= prob[i_inl] else "inline"
        ok = pred == label
        correct += ok
        rows.append({"face": face, "stem": stem, "true": label, "pred": pred,
                     "ok": bool(ok), "p_stencil": float(prob[i_sten]),
                     "p_inline": float(prob[i_inl]),
                     "argmax4": CLASSES[int(np.argmax(prob))]})

    scored = [r for r in rows if "pred" in r]
    n = len(scored)
    p = float(stats.binomtest(correct, n, 0.5, alternative="greater").pvalue)
    print(f"\n  {'superfamily':<34} {'true':<8} {'pred':<8} {'P(sten)':>8}"
          f" {'P(inl)':>7}  4-way")
    for r in scored:
        mark = " " if r["ok"] else "X"
        print(f"{mark} {r['face']:<34} {r['true']:<8} {r['pred']:<8} "
              f"{r['p_stencil']:>8.3f} {r['p_inline']:>7.3f}  {r['argmax4']}")

    passed = correct >= 9 and p < 0.05
    print(f"\n  PRIMARY  {correct}/{n} correct   exact binomial p = {p:.4f}")
    print(f"  PRE-REGISTERED BAR >=9/11 and p<0.05: "
          f"{'PASSED' if passed else 'FAILED'}")
    if not passed:
        print("  Reported as a failure. The transforms are NOT retuned against")
        print("  these 11 and re-run; that would make the primary a training set.")

    # --- DESCRIPTIVE: the twelve generated atlases ------------------------
    gen_rows = []
    for path in sorted(glob.glob(os.path.join(args.generated, "*.png"))):
        v = vector_ext(load(path))
        if v is None:
            continue
        prob = model.predict_proba(v.reshape(1, -1))[0]
        gen_rows.append({"atlas": os.path.basename(path)[:2],
                         "argmax": CLASSES[int(np.argmax(prob))],
                         "p_stencil": float(prob[i_sten]),
                         "p_inline": float(prob[i_inl])})
    if gen_rows:
        print("\n  DESCRIPTIVE ONLY -- the twelve generated atlases")
        print(f"  {'atlas':<6} {'4-way':<9} {'P(sten)':>8} {'P(inl)':>7}")
        for r in gen_rows:
            print(f"  {r['atlas']:<6} {r['argmax']:<9} "
                  f"{r['p_stencil']:>8.3f} {r['p_inline']:>7.3f}")

    payload = {"preregistered": True, "bar": "9/11 and p<0.05",
               "classes": list(CLASSES),
               "features": list(FEATURES) + list(EXTRA),
               "sources": len(sources), "train_n": int(len(y)),
               "correct": correct, "n": n, "p": p, "passed": bool(passed),
               "real": rows, "generated": gen_rows}
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
