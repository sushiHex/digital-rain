"""Pick replacements for the 87 fonts the licence filter removed.

WHY ORDINARY, NOT DISTINCTIVE. The previous expansion selected the most
structurally DISTINCTIVE fonts, justified by "the 4B's gap is in the distinctive
tail". The matched six-seed run inverted that: against a frozen,
model-independent moderator the 9B's advantage over the 4B *shrinks* as fonts
get more distinctive (char_acc rho = -0.536, p=1.8e-4), so the 4B loses hardest
on ORDINARY typefaces
(research/2026-08-08-multiseed-the-4b-9b-gap-is-real-and-bigger.md).

So the DEFAULT selects toward the LOW end of the distinctiveness distribution.

BUT BE CLEAR ABOUT WHAT THAT COSTS. The fonts removed were corpus-typical, not
ordinary: dropped median distinctiveness 0.0460 against a corpus median of
0.0467. The 87 most ordinary available sit at 0.0250. So the default set does
NOT replace like with like -- it restores corpus SIZE while shifting corpus
COMPOSITION, and a run using it cannot separate the two effects. Net shift on
the whole corpus is small (median -0.0038) because 87 of 925 is 9.4%, but it is
a real second change.

`--match-dropped` is the control: it draws candidates nearest each dropped
font's distinctiveness, holding the distribution fixed so the run isolates size
alone. Use the default to pursue the moderator finding; use the control to
measure the licence filter's cost cleanly. Do not use one and claim the other.

WHAT THIS DOES NOT DO. `analysis/select_expansion_set.py` additionally explores
variable-font axis instances and runs a DINOv2 global duplicate guard. Both need
the GPU, which is busy. This is CPU-only: it selects STATIC fonts and uses an
exact atlas hash for duplicates. Run the DINOv2 guard before adopting the set.

  python analysis/select_replacement_set.py --n 87
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import hashlib
import json
import os

import numpy as np

from analysis.select_expansion_set import (corpus_default_loader, ink_fraction,
                                           shares_family)

POOL = "research/pool_distinctiveness.json"
CORPUS = "research/font_distinctiveness.json"
EXCLUSIONS = "research/corpus_exclusions.json"
HOLDOUT = "eval_holdout/manifest.json"
CORPUS_ATLASES = "dataset_v2/atlases"
OUT = "research/replacement_set.json"


def corpus_ink_median(atlas_dir=CORPUS_ATLASES, limit=300):
    """Median ink fraction of the existing corpus, for the ink floor."""
    import glob

    from PIL import Image
    vals = []
    for p in sorted(glob.glob(os.path.join(atlas_dir, "*.png")))[:limit]:
        with Image.open(p) as im:
            vals.append(ink_fraction(np.asarray(im.convert("L"))))
    return float(np.median(vals)) if vals else 0.0


def render(path, size=640):
    """Atlas for a candidate, through the loader the corpus actually used."""
    from build_dataset import render_atlas
    return np.asarray(render_atlas(path, size=size,
                                   loader=corpus_default_loader).convert("L"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=None,
                    help="how many to select (default: as many as were dropped)")
    ap.add_argument("--licence", default="ofl")
    ap.add_argument("--min-ink-ratio", type=float, default=0.5)
    ap.add_argument("--max-ink-ratio", type=float, default=3.0)
    ap.add_argument("--match-dropped", action="store_true",
                    help="draw replacements matching the DROPPED fonts' "
                         "distinctiveness distribution, so the run isolates "
                         "corpus size from corpus composition. The default "
                         "instead skews ordinary, which is the direction the "
                         "multi-seed moderator points but changes two things "
                         "at once.")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)

    pool = json.load(open(POOL, encoding="utf-8"))["scores"]
    corpus = json.load(open(CORPUS, encoding="utf-8"))["scores"]
    exc = json.load(open(EXCLUSIONS, encoding="utf-8"))
    holdout = [e["name"] for e in
               json.load(open(HOLDOUT, encoding="utf-8"))["fonts"]]
    want = args.n or exc["exclude_count"]
    print(f"replacing {exc['exclude_count']} dropped fonts; target {want}\n")

    rej = {"licence": 0, "holdout_family": 0, "in_corpus": 0,
           "unrenderable": 0, "ink": 0, "duplicate": 0}
    cands = []
    for stem, v in sorted(pool.items()):
        if v.get("licence") != args.licence:
            rej["licence"] += 1
        elif stem in corpus:
            rej["in_corpus"] += 1
        elif any(shares_family(stem, h) for h in holdout):
            rej["holdout_family"] += 1
        else:
            cands.append({"stem": stem, "path": v["path"], "score": v["score"]})
    print(f"{len(cands)} eligible after licence/holdout/corpus guards")
    print(f"  rejected: {rej['licence']} licence, {rej['holdout_family']} "
          f"holdout superfamily, {rej['in_corpus']} already in corpus")

    if args.match_dropped:
        # CONTROL MODE. Replacing 87 corpus-typical fonts (dropped median
        # 0.0460) with the 87 most ordinary available (0.0250) changes the
        # corpus's COMPOSITION as well as its size, so a run using it cannot
        # separate "restored the fonts" from "made the corpus more ordinary".
        # This mode instead draws candidates nearest each dropped font's
        # distinctiveness, holding the distribution fixed.
        dropped_scores = sorted(corpus[s] for s in exc["exclude_stems"]
                                if s in corpus)
        pool_by_score = sorted(cands, key=lambda c: c["score"])
        picked, used = [], set()
        for target in dropped_scores:
            best = min((c for i, c in enumerate(pool_by_score) if i not in used),
                       key=lambda c: abs(c["score"] - target), default=None)
            if best is None:
                break
            used.add(pool_by_score.index(best))
            picked.append(best)
        cands = picked
        print(f"\n--match-dropped: drawing to match the dropped distribution "
              f"(median {np.median(dropped_scores):.4f})")
    else:
        # ORDINARY FIRST: ascending distinctiveness.
        cands.sort(key=lambda c: c["score"])

    med = corpus_ink_median()
    lo, hi = med * args.min_ink_ratio, med * args.max_ink_ratio
    print(f"\ncorpus median ink {med:.4f}; accepting [{lo:.4f}, {hi:.4f}]")

    # Exact-atlas duplicate guard. Cheap stand-in for the DINOv2 global guard,
    # which needs the GPU. Catches identical renders (the holdout's own
    # byte-identical IBMPlex/Tiro groups are exactly this failure).
    seen_hashes, chosen = set(), []
    for c in cands:
        if len(chosen) >= want:
            break
        try:
            atlas = render(c["path"])
        except Exception:
            rej["unrenderable"] += 1
            continue
        ink = ink_fraction(atlas)
        if not (lo <= ink <= hi):
            rej["ink"] += 1
            continue
        h = hashlib.sha256(atlas.tobytes()).hexdigest()
        if h in seen_hashes:
            rej["duplicate"] += 1
            continue
        seen_hashes.add(h)
        c["ink_fraction"] = round(ink, 5)
        chosen.append(c)

    print(f"\nselected {len(chosen)} of {want}")
    print(f"  rejected during render: {rej['ink']} ink floor, "
          f"{rej['duplicate']} duplicate atlas, {rej['unrenderable']} unrenderable")

    if chosen:
        sc = np.array([c["score"] for c in chosen])
        cs = np.array(list(corpus.values()))
        print(f"\n  selected distinctiveness : median {np.median(sc):.4f}  "
              f"p10 {np.percentile(sc, 10):.4f}  p90 {np.percentile(sc, 90):.4f}")
        print(f"  existing corpus          : median {np.median(cs):.4f}  "
              f"p10 {np.percentile(cs, 10):.4f}  p90 {np.percentile(cs, 90):.4f}")
        dropped = np.array([corpus[s] for s in exc["exclude_stems"] if s in corpus])
        print(f"  fonts actually DROPPED   : median {np.median(dropped):.4f}  "
              f"p10 {np.percentile(dropped, 10):.4f}  "
              f"p90 {np.percentile(dropped, 90):.4f}")
        if args.match_dropped:
            print("  (control mode: selected should TRACK the dropped row above)")
        else:
            print("  (default mode: selected sits BELOW both -- an intentional "
                  "composition shift, not a like-for-like replacement)")

    payload = {
        "_comment": "Replacements for the licence-excluded fonts, selected "
                    "toward the ORDINARY end of the distinctiveness "
                    "distribution. CPU-only: no DINOv2 duplicate guard and no "
                    "variable-axis instancing. Run those before adopting.",
        "target": want, "selected_count": len(chosen),
        "rejected": rej, "corpus_ink_median": med,
        "fonts": chosen,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
        f.write("\n")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
