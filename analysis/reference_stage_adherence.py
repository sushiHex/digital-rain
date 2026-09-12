"""Can TWO glyphs carry the adherence signal, or must the picker wait for an atlas?

PRE-REGISTERED. Written and committed before any number was computed.

WHY THIS IS THE BLOCKING ARCHITECTURE QUESTION. The product shows several
candidates and lets the user pick. Selection at the REFERENCE stage costs ~25 s
per candidate; at the ATLAS stage it costs ~62 s and throws away three atlases
out of four. So the picker wants to rank references.

But `synthesize_rare_attributes.py` aggregates over 94 cells and refuses fewer
than 40. A reference has TWO. Nothing established that two glyphs carry enough,
and assuming it would put the whole interface on an unmeasured premise.

THE SPACE MISMATCH THIS AVOIDS, WHICH IS THE REAL TRAP. `reference_gate.
glyph_cells` crops each glyph to its ink and RESCALES IT to a fixed height
before centring it. An atlas cell is not rescaled -- it is drawn at the atlas's
own size, baseline-aligned, so `K` is cap-height and `g` is x-height plus a
descender. Train on raw atlas cells and test on reference images and the two
sides disagree about what a glyph's height means, which silently changes
`width_cv` and any feature that compares the two glyphs.

So BOTH sides here go through the same normalisation: `normalise_like_reference`
mirrors what `glyph_cells` does to a reference, and it is applied to the
training cells too. This project has been bitten by exactly this shape before --
`build_dataset.render_atlas` and `render_reference` had different defaults and
mismatched ~110 of 177 additions to `dataset_v3`.

=== PRE-REGISTRATION, fixed before running ===

TRAINING      The same synthetic solid / stencil / inline / outline variants
              `synthesize_rare_attributes.py` builds from the same source
              faces, but aggregated over the TWO reference characters only,
              each normalised exactly as a reference image would be.
PRIMARY       The same 11 real superfamilies -- 5 stencil, 6 inline -- scored
              from their K and g cells alone, under the same normalisation.
BAR           >= 9 of 11, exact binomial p < 0.05. THE SAME BAR the 94-cell
              measure cleared (10/11, p=0.0059), because the question is
              whether two glyphs still carry it, not whether a weaker number
              can be found.
IF IT FAILS   Reported as "two glyphs do not carry this measure". The
              consequence is architectural and is stated, not worked around:
              selection moves to the atlas stage, or the reference stage
              selects on COHERENCE alone -- which `reference_gate` already
              does validly at n=2, since a distance between two vectors needs
              no aggregation.
SECOND USE    **This is the SECOND use of those 11 faces.** The first was
              `synthesize_rare_attributes.py`. Reusing a held-out set across
              models erodes its independence, and a THIRD use would make it a
              validation set rather than a test set. Recorded here so the next
              reader does not have to notice it.
DESCRIPTIVE   The n=4 reference candidates, once generated. No claim.

  python analysis/reference_stage_adherence.py
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import collections
import glob
import json
import os
import re

import numpy as np
from PIL import Image

from analysis.attribute_label_supply import EXCLUSIONS, NAME_ATTRS, scan
from analysis.attribute_separation import atlas_path
from analysis.reference_gate import REF_TARGET_H, glyph_cells
from analysis.synthesize_rare_attributes import (CLASSES, RARE_RX, SEED,
                                                 SOURCES, apply_transform,
                                                 atlas_cells, draw_params, load,
                                                 superfamily, vector_from_cells)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_CHARS = "Kg"
DEFAULT_REFS = os.path.join(REPO, "eval_runs", "_candidate_refs", "klein-base-n4")


def char_indices(chars=REF_CHARS):
    from atlas_constants import CHARSET
    return [CHARSET.index(c) for c in chars]


def normalise_like_reference(cell):
    """Crop to ink and rescale to REF_TARGET_H, exactly as `glyph_cells` does.

    Mirrors `reference_gate.glyph_cells` so training cells and reference cells
    live in one space. If that function's normalisation changes, this must too.
    """
    from atlas_constants import CELL_H, CELL_W
    from analysis.style_coherence import MIN_INK

    ink = cell > 128
    if ink.sum() < MIN_INK:
        return None
    rows, cols = np.where(ink)
    glyph = cell[rows.min():rows.max() + 1, cols.min():cols.max() + 1]
    gh, gw = glyph.shape
    scale = REF_TARGET_H / gh
    small = np.asarray(Image.fromarray(glyph).resize(
        (max(1, round(gw * scale)), max(1, round(gh * scale))), Image.LANCZOS))
    sh, sw = small.shape
    if sh > CELL_H or sw > CELL_W:
        f = min(CELL_H / sh, CELL_W / sw)
        small = np.asarray(Image.fromarray(small).resize(
            (max(1, int(sw * f)), max(1, int(sh * f))), Image.LANCZOS))
        sh, sw = small.shape
    canvas = np.zeros((CELL_H, CELL_W), dtype=np.uint8)
    y0, x0 = (CELL_H - sh) // 2, (CELL_W - sw) // 2
    canvas[y0:y0 + sh, x0:x0 + sw] = small
    return canvas


def two_cell_vector(arr, indices):
    """Feature vector from an atlas array, using only the reference characters."""
    cells = [normalise_like_reference(c) for c in atlas_cells(arr, indices)]
    return vector_from_cells([c for c in cells if c is not None], min_cells=2)


def fit_reference_stage_model(pool, n_sources=SOURCES, seed=SEED, verbose=True):
    """Fit the two-glyph treatment model exactly as the registered run did.

    Extracted from `main` on 2026-09-11, unchanged in behaviour, so that
    `analysis/calibrate_instruments.py` can score the same model against
    human labels. Returns (model, real, records): the fitted pipeline, the
    {(superfamily, label): stem} map of real held-out faces, and the scanned
    pool records.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    idx = char_indices()
    exclude = set(json.load(open(EXCLUSIONS, encoding="utf-8"))["exclude_stems"])
    if verbose:
        print("reading the pool ...")
    records, _ = scan(pool, exclude)

    real = {}
    for rec in records:
        for label in ("stencil", "inline"):
            if re.search(NAME_ATTRS[label], rec["stem"], re.I):
                key = (superfamily(rec["stem"]), label)
                if key not in real or rec["stem"] < real[key]:
                    real[key] = rec["stem"]
    held_out = {superfamily(s) for s in real.values()}

    seen, sources = set(), []
    for rec in sorted(records, key=lambda r: r["stem"]):
        if rec["family"] in seen or RARE_RX.search(rec["stem"]):
            continue
        if superfamily(rec["stem"]) in held_out:
            continue
        seen.add(rec["family"])
        sources.append(rec["stem"])
        if len(sources) >= n_sources:
            break
    if verbose:
        print(f"  {len(sources)} synthesis sources, {len(real)} real held-out faces\n")

    rng = np.random.default_rng(seed)
    X, y = [], []
    for stem in sources:
        path = atlas_path(pool, stem)
        if path is None:
            continue
        arr = load(path)
        params = draw_params(rng)
        for label in CLASSES:
            v = two_cell_vector(apply_transform(arr, label, params), idx)
            if v is None:
                continue
            X.append(v)
            y.append(CLASSES.index(label))
    X, y = np.asarray(X), np.asarray(y)
    if verbose:
        print(f"  training set: {len(y)} two-glyph samples, "
              f"{len(collections.Counter(y))} classes")

    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000))
    model.fit(X, y)
    return model, real, records


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pool", default=os.path.join(REPO, "font_pool"))
    ap.add_argument("--sources", type=int, default=SOURCES)
    ap.add_argument("--refs", default=DEFAULT_REFS)
    ap.add_argument("--json", default=os.path.join(REPO, "research",
                                                   "reference_stage_adherence.json"))
    args = ap.parse_args()

    from scipy import stats

    model, real, _records = fit_reference_stage_model(args.pool, args.sources)

    i_s, i_i = CLASSES.index("stencil"), CLASSES.index("inline")
    rows, correct = [], 0
    for (face, label), stem in sorted(real.items()):
        path = atlas_path(args.pool, stem)
        if path is None:
            continue
        v = two_cell_vector(load(path), idx)
        if v is None:
            rows.append({"face": face, "true": label, "skipped": "unscoreable"})
            continue
        prob = model.predict_proba(v.reshape(1, -1))[0]
        pred = "stencil" if prob[i_s] >= prob[i_i] else "inline"
        ok = pred == label
        correct += ok
        rows.append({"face": face, "stem": stem, "true": label, "pred": pred,
                     "ok": bool(ok), "p_stencil": float(prob[i_s]),
                     "p_inline": float(prob[i_i]),
                     "argmax4": CLASSES[int(np.argmax(prob))]})

    scored = [r for r in rows if "pred" in r]
    n = len(scored)
    p = float(stats.binomtest(correct, n, 0.5, alternative="greater").pvalue)
    print(f"\n  {'superfamily':<34} {'true':<8} {'pred':<8} {'P(sten)':>8}"
          f" {'P(inl)':>7}  4-way")
    for r in scored:
        print(f"{' ' if r['ok'] else 'X'} {r['face']:<34} {r['true']:<8} "
              f"{r['pred']:<8} {r['p_stencil']:>8.3f} {r['p_inline']:>7.3f}  "
              f"{r['argmax4']}")

    passed = correct >= 9 and p < 0.05
    print(f"\n  PRIMARY  {correct}/{n} correct   exact binomial p = {p:.4f}")
    print(f"  PRE-REGISTERED BAR >=9/11 and p<0.05: "
          f"{'PASSED' if passed else 'FAILED'}")
    print("  For scale, the 94-cell measure scored 10/11 on these same faces.")
    if not passed:
        print("\n  TWO GLYPHS DO NOT CARRY THIS MEASURE. The consequence is")
        print("  architectural: selection moves to the atlas stage, or the")
        print("  reference stage selects on COHERENCE alone, which")
        print("  `reference_gate` already does validly at n=2.")

    # --- DESCRIPTIVE: the generated reference candidates -------------------
    gen = []
    for path in sorted(glob.glob(os.path.join(args.refs, "*.png"))):
        cells = glyph_cells(path, len(REF_CHARS))
        v = vector_from_cells([c for c in cells if c is not None], min_cells=2)
        if v is None:
            continue
        prob = model.predict_proba(v.reshape(1, -1))[0]
        gen.append({"stem": os.path.splitext(os.path.basename(path))[0],
                    "argmax": CLASSES[int(np.argmax(prob))],
                    "p_stencil": float(prob[i_s]),
                    "p_inline": float(prob[i_i])})
    if gen:
        print(f"\n  DESCRIPTIVE ONLY -- {len(gen)} generated reference candidates")
        by_class = collections.Counter(r["argmax"] for r in gen)
        print(f"  4-way spread: {dict(by_class)}")

    payload = {"preregistered": True, "bar": "9/11 and p<0.05",
               "ref_chars": REF_CHARS, "sources": len(sources),
               "train_n": int(len(y)), "correct": correct, "n": n, "p": p,
               "passed": bool(passed), "real": rows, "generated": gen,
               "note_94cell": "10/11 on the same faces, p=0.0059"}
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
