"""Select the corpus-expansion set: new OFL fonts + variable-font instances.

Produces research/expansion_set.json, the single source of truth for what
pipeline/build_expansion.py renders.

Four correctness rules, each of which caught a real problem:

1. **Holdout SUPERFAMILY exclusion, not just exact names.** The holdout holds
   `BitcountGridDoubleInk[CRSV,ELSH,ELXP,...]` while the corpus holds
   `Bitcount[CRSV,ELSH,ELXP,...]` -- same superfamily, same structural axes.
   Instancing those axes would generate styles approaching the holdout font,
   and Bitcount Grid is the headline result where the weighted 4B beat the 9B.
   32 of 50 holdout fonts already share a superfamily with training fonts
   (the holdout excluded font FILES, not families), so expansion must not
   make that worse.
2. **Licence filter.** The corpus is 87.0% OFL (not the 97.5% long asserted
   here -- see research/2026-08-08-the-corpus-is-not-97-percent-ofl.md)
   and that underpins the
   output-licensing position. Only `licence == "ofl"` is eligible.
3. **Structural axes, not weight axes.** Registered axes (wght/wdth/slnt/
   ital/opsz) move weight and slant; custom axes (ELSH, ELXP, BLED, SCAN,
   ROND, EDPT, EHLT) move letterform structure. Measured: Workbench's
   BLED/SCAN instances reach 62.7% of the diversity between entirely
   different distinctive typefaces, while Doto's ROND+wght reaches 23%.
4. **Axis-grid sampling, not just named instances.** Nabla carries two
   structural axes (EDPT, EHLT) but ships ONE named instance. Sampling the
   axis grid recovers the diversity its named instances do not expose.

Selection is diversity-greedy (farthest-point) with a per-family cap, so one
many-instance family cannot dominate the tail, and every kept instance must
sit at least MIN_SEP from everything already selected -- including the
default instance already in the corpus.

  python analysis/select_expansion_set.py --out research/expansion_set.json
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import itertools
import json
import os
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image

import build_dataset
from analysis.score_font_distinctiveness import telling_cells
from atlas_constants import CANVAS

# Registered axes move weight/slant/optical size. Everything else is a custom
# axis and is where structural variation lives.
COSMETIC_AXES = {"wght", "wdth", "slnt", "ital", "opsz"}


def family_root(name):
    """Leading alphabetic run, axes and style suffix stripped."""
    name = re.sub(r"\[.*?\]", "", name)
    return re.split(r"[-_]", name)[0].lower()


def shares_family(a, b, n=6):
    a, b = family_root(a), family_root(b)
    return a.startswith(b[:n]) or b.startswith(a[:n])


def index_fonts(dirs):
    idx = {}
    for d in dirs:
        for root, _dirs, files in os.walk(d):
            for fn in files:
                if fn.lower().endswith((".ttf", ".otf")):
                    idx.setdefault(Path(fn).stem, os.path.join(root, fn))
    return idx


def axis_candidates(path, max_grid=3):
    """Instances to try for one font.

    Returns (candidates, structural_tags, all_tags) where candidates are
    (label, {axisTag: value}) pairs: every named instance plus a grid over the
    STRUCTURAL axes. all_tags is the full fvar order, which the caller needs to
    pin coordinates positionally.
    """
    try:
        f = TTFont(path, lazy=True)
        fvar = f.get("fvar")
    except Exception:
        return [], [], []
    if not fvar:
        return [], [], []

    structural = [a for a in fvar.axes if a.axisTag not in COSMETIC_AXES]
    out = []
    for inst in fvar.instances:
        nm = f["name"].getDebugName(inst.subfamilyNameID)
        if nm:
            out.append((f"named:{nm}", dict(inst.coordinates)))

    # Axis grid over STRUCTURAL axes only; cosmetic axes stay at default.
    if structural:
        defaults = {a.axisTag: a.defaultValue for a in fvar.axes}
        grids = []
        for a in structural[:3]:  # 3 axes -> at most 27 points
            pts = sorted({a.minValue, a.defaultValue, a.maxValue})
            if len(pts) > max_grid:
                pts = [a.minValue, a.defaultValue, a.maxValue]
            grids.append([(a.axisTag, v) for v in pts])
        for combo in itertools.product(*grids):
            coords = dict(defaults)
            coords.update(dict(combo))
            label = "grid:" + ",".join(f"{t}={v:g}" for t, v in combo)
            out.append((label, coords))
    # Return the FULL axis order too: the caller needs it for pinning and
    # would otherwise re-open the same font via axis_order().
    return out, [a.axisTag for a in structural], [a.axisTag for a in fvar.axes]


@lru_cache(maxsize=None)
def axis_order(path):
    """Axis tags in fvar order -- the order PIL's set_variation_by_axes expects.

    PIL's get_variation_axes() reports human axis NAMES ("Weight"), not the
    4-letter tags fontTools uses ("wght"), so coordinates must be applied
    positionally rather than by name.

    Cached: build_expansion calls this once per selected instance, so a parent
    contributing several instances would otherwise be re-parsed once each.
    """
    fvar = TTFont(path, lazy=True).get("fvar")
    return [a.axisTag for a in fvar.axes] if fvar else []


def pinned_loader(coords, order):
    """A build_dataset `loader` that pins variable axes to explicit coordinates.

    The single home for axis pinning. Pass it to BOTH render_atlas and
    render_reference -- pinning only the atlas leaves the reference at the
    default instance, which silently produced instanced pairs sharing one
    byte-identical reference (see render_reference's docstring).

    coords is {axisTag: value}; order is the fvar tag order, because PIL's
    get_variation_axes() reports human names ("Weight") rather than tags
    ("wght"), so values must be applied positionally.
    """
    from PIL import ImageFont

    def loader(font_path, size):
        fnt = ImageFont.truetype(str(font_path), size)
        if coords and order:
            axes = fnt.get_variation_axes()
            fnt.set_variation_by_axes(
                [coords.get(t, ax["default"]) for t, ax in zip(order, axes)])
        return fnt

    return loader


def corpus_default_loader(font_path, size):
    """Open a face the way dataset_v2's atlases were actually rendered.

    NOT load_truetype_pinned. That pins to the "Regular" named instance, and for
    variable fonts it does not reproduce the corpus: rendering
    Doto[ROND,wght] through it differs from dataset_v2/atlases/Doto[ROND,wght].png
    by a mean of 17.6/255, while a plain ImageFont.truetype is byte-identical.
    dataset_v2 predates the pin.

    This matters because the seed render is the "what the corpus already has"
    baseline that every instance is measured against for min_sep. Using a seed
    the corpus does not contain silently changes which instances survive --
    measured, it dropped Doto's from the selection.
    """
    from PIL import ImageFont
    return ImageFont.truetype(str(font_path), size)


def render_coords(path, coords, order):
    """render_atlas pinned to explicit axis coordinates, or the corpus default."""
    loader = pinned_loader(coords, order) if coords else corpus_default_loader
    return np.asarray(
        build_dataset.render_atlas(path, CANVAS, loader=loader).convert("RGB"))


def embed_atlas(atlas, embed_fn):
    """Unit-normalized mean DINOv2 embedding of an atlas's telling cells."""
    v = embed_fn(telling_cells(atlas)).mean(axis=0)
    return v / (np.linalg.norm(v) + 1e-8)


def ink_fraction(atlas):
    """Fraction of the atlas that is ink. Atlases are white-on-black."""
    a = atlas.max(axis=2) if atlas.ndim == 3 else atlas
    return float((a > 128).mean())


def greedy_diverse(vectors, seed_vec, cap, min_sep):
    """Farthest-point selection: repeatedly take the candidate furthest from
    everything already chosen, stopping at cap or when nothing clears min_sep."""
    chosen, chosen_vecs = [], [seed_vec]
    remaining = list(range(len(vectors)))
    while remaining and len(chosen) < cap:
        C = np.stack(chosen_vecs)
        best, best_d = None, -1.0
        for i in remaining:
            d = float(1.0 - (C @ vectors[i]).max())  # distance to nearest chosen
            if d > best_d:
                best, best_d = i, d
        if best is None or best_d < min_sep:
            break
        chosen.append((best, best_d))
        chosen_vecs.append(vectors[best])
        remaining.remove(best)
    return chosen


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pool", default="research/pool_distinctiveness.json")
    ap.add_argument("--corpus", default="research/font_distinctiveness.json")
    ap.add_argument("--corpus-atlas-dir", default="dataset_v2/atlases",
                    help="Origin for instance scoring and the ink floor.")
    ap.add_argument("--holdout-manifest", default="eval_holdout/manifest.json")
    ap.add_argument("--out", default="research/expansion_set.json")
    ap.add_argument("--percentile", type=float, default=90.0,
                    help="Distinctiveness percentile defining 'the tail'. An "
                         "INSTANCE is kept on its own score against this, not "
                         "its parent's -- ClimateCrisis[YEAR], TiltWarp[XROT,"
                         "YROT] and AguDisplay[MORF] all have ordinary defaults "
                         "and dramatic axes, and a parent-score rule misses them.")
    ap.add_argument("--cap", type=int, default=6, help="Max NEW instances per font.")
    ap.add_argument("--min-sep", type=float, default=0.08,
                    help="Minimum cosine distance from every already-selected "
                         "render, including the default instance the corpus has.")
    ap.add_argument("--licence", default="ofl")
    ap.add_argument("--min-ink-ratio", type=float, default=0.5,
                    help="Reject an instance whose ink coverage is below this "
                         "fraction of the corpus median.")
    ap.add_argument("--max-ink-ratio", type=float, default=3.0,
                    help="Reject an instance whose ink coverage exceeds this "
                         "multiple of the corpus median.")
    args = ap.parse_args()

    corpus = json.load(open(args.corpus, encoding="utf-8"))["scores"]
    pool = json.load(open(args.pool, encoding="utf-8"))["scores"]
    holdout = [e["name"] for e in
               json.load(open(args.holdout_manifest, encoding="utf-8"))["fonts"]]
    thresh = float(np.percentile(np.array(list(corpus.values())), args.percentile))
    print(f"corpus p{args.percentile:g} distinctiveness threshold = {thresh:.4f}")

    def holdout_family(name):
        return any(shares_family(name, h) for h in holdout)

    # ---- static expansion fonts -------------------------------------------
    statics, rej = [], {"licence": 0, "holdout_family": 0}
    for stem, v in sorted(pool.items()):
        if v.get("licence") != args.licence:
            rej["licence"] += 1
            continue
        if holdout_family(stem):
            rej["holdout_family"] += 1
            continue
        statics.append({"stem": stem, "path": v["path"], "score": v["score"],
                        "instance": None, "source": "expansion"})
    n_dist = sum(1 for s in statics if s["score"] >= thresh)
    print(f"static expansion: {len(statics)} fonts ({n_dist} above p{args.percentile:g})"
          f"   rejected licence={rej['licence']} holdout_family={rej['holdout_family']}")

    # ---- instancing candidates --------------------------------------------
    idx = index_fonts(("google-fonts", "font_pool", "font_pool_selected", "extra-fonts"))
    # EVERY font with a structural axis is a candidate, whatever its default
    # scores -- selection happens per instance, below.
    cands_all = [(k, corpus[k], idx.get(k), "corpus") for k in corpus]
    cands_all += [(k, v["score"], v["path"], "expansion") for k, v in pool.items()
                  if v.get("licence") == args.licence]

    import glob as _glob

    from cleanup.models import build_dino_embed_fn
    embed_fn = build_dino_embed_fn()

    # Keep the corpus EMBEDDINGS, not just their centroid. An instance that
    # merely reproduces a font the corpus already has adds no information, and
    # two different fonts can contribute near-identical instances (Sixtyfour
    # and SixtyfourConvergence do). Both are caught by requiring global
    # separation, which a per-font greedy pass cannot see.
    #
    # One pass, one decode per atlas: the embedding and the ink floor both need
    # the same array, and opening all 925 PNGs twice cost ~7s and ~4.5GB of
    # transient allocation for nothing.
    print("embedding corpus (origin for scoring + global duplicate guard)")
    corpus_vecs, corpus_ink = [], []
    for i, p in enumerate(sorted(_glob.glob(os.path.join(args.corpus_atlas_dir,
                                                         "*.png")))):
        try:
            arr = np.asarray(Image.open(p).convert("RGB"))
            v = embed_fn(telling_cells(arr)).mean(axis=0)
        except Exception:
            continue
        corpus_vecs.append(v / (np.linalg.norm(v) + 1e-8))
        corpus_ink.append(ink_fraction(arr))
        if (i + 1) % 300 == 0:
            print(f"  corpus embedded {i + 1}", flush=True)
    C = np.stack(corpus_vecs)
    centroid = C.mean(axis=0)
    centroid /= np.linalg.norm(centroid) + 1e-8
    print(f"  centroid over {len(C)} corpus fonts")

    ink_med = float(np.median(corpus_ink))
    lo_ink, hi_ink = ink_med * args.min_ink_ratio, ink_med * args.max_ink_ratio
    print(f"  corpus ink median {ink_med:.4f}; instances must fall in "
          f"[{lo_ink:.4f}, {hi_ink:.4f}]")
    kept_vecs = []   # every instance selected so far, across ALL fonts

    instances = []
    skipped = Counter({k: 0 for k in ("holdout_family", "not_variable",
                                      "no_structural_axis", "below_threshold",
                                      "missing", "ink_out_of_range", "duplicate")})
    for stem, score, path, source in sorted(cands_all, key=lambda t: -t[1]):
        if path is None:
            skipped["missing"] += 1
            continue
        if holdout_family(stem):
            skipped["holdout_family"] += 1
            continue
        cands, structural, order = axis_candidates(path)
        if not cands:
            skipped["not_variable"] += 1
            continue
        if not structural:
            skipped["no_structural_axis"] += 1
            continue
        try:
            seed = embed_atlas(render_coords(path, None, order), embed_fn)
        except Exception:
            skipped["missing"] += 1
            continue

        cand_recs = []
        for label, coords in cands:
            try:
                atlas = render_coords(path, coords, order)
                v = embed_atlas(atlas, embed_fn)
            except Exception:
                continue
            # INK FLOOR. Centroid distance cannot distinguish "distinctive"
            # from "degenerate": the cheapest way to be far from a centroid is
            # to be nearly blank, and axes like Amstelvar's XOPQ (x-opaque =
            # stem thickness) go to hairline at their minimum. Four such
            # instances (ink 0.006-0.013 against a corpus median of 0.057)
            # reached dataset_v3, and at 6016 steps the model converged onto
            # them -- generated ink fell 27% below GT and char_acc, racc, lpips
            # and identity all regressed significantly. Static fonts never hit
            # this because font_supports_charset gates them on
            # check_render_visibility; the instance path bypassed that gate.
            ink = ink_fraction(atlas)
            if not (lo_ink <= ink <= hi_ink):
                skipped["ink_out_of_range"] += 1
                continue
            own = float(1.0 - v @ centroid)
            if own < thresh:          # the instance itself must be distinctive
                continue
            cand_recs.append({"vec": v, "label": label, "coords": coords,
                              "score": own})
        if not cand_recs:
            skipped["below_threshold"] += 1
            continue
        # Global guard: an instance must clear min_sep from every corpus font
        # AND every instance already kept, not merely from its own siblings.
        prior = np.concatenate([C, np.stack(kept_vecs)]) if kept_vecs else C
        keep = [r for r in cand_recs
                if float(1.0 - (prior @ r["vec"]).max()) >= args.min_sep]
        skipped["duplicate"] += len(cand_recs) - len(keep)
        if not keep:
            skipped["below_threshold"] += 1
            continue
        cand_recs = keep

        picks = greedy_diverse([r["vec"] for r in cand_recs], seed,
                               args.cap, args.min_sep)
        if not picks:
            skipped["below_threshold"] += 1
            continue
        picked_scores = []
        for i, d in picks:
            r = cand_recs[i]
            kept_vecs.append(r["vec"])
            picked_scores.append(r["score"])
            instances.append({
                "stem": f"{stem}__{re.sub(r'[^A-Za-z0-9=,.-]', '_', r['label'])}",
                "parent": stem, "path": path, "instance": r["coords"],
                "label": r["label"], "sep": round(d, 4),
                "score": round(r["score"], 4), "parent_score": round(score, 4),
                "source": f"instance/{source}"})
        print(f"  {stem[:42]:44} parent={score:.3f} {','.join(structural)[:16]:16}"
              f" -> {len(picks)} inst, score "
              f"{min(picked_scores):.3f}..{max(picked_scores):.3f}")

    print(f"\ninstancing skipped: {skipped}")

    out = {"threshold": thresh, "percentile": args.percentile, "cap": args.cap,
           "min_sep": args.min_sep, "licence": args.licence,
           "n_static": len(statics), "n_instances": len(instances),
           "corpus_ink_median": ink_med, "ink_range": [lo_ink, hi_ink],
           "entries": statics + instances}
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(out, open(args.out, "w", encoding="utf-8"), indent=1)

    tail_now = sum(1 for v in corpus.values() if v >= thresh)
    print(f"\ncorpus distinctive tail now:      {tail_now}")
    print(f"  + new static distinctive fonts: {n_dist}")
    print(f"  + instances:                    {len(instances)}")
    print(f"  = distinctive training examples: {tail_now + n_dist + len(instances)}"
          f"  ({(tail_now + n_dist + len(instances)) / tail_now:.2f}x)")
    print(f"total new atlases to render: {len(statics) + len(instances)}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
