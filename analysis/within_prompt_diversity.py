"""Do N seeds of ONE description give a user a real choice, or the same font N times?

PRE-REGISTERED. Written and committed before any number was computed.

WHY THIS IS THE BLOCKING QUESTION. The product decision is that the interface
shows several candidates for one description and lets the user pick and iterate.
That changes what the instruments must do -- the adherence measure becomes a
RANKER rather than a gate, and calibration stops being the bottleneck -- but it
creates one requirement nothing here has ever measured: THE OPTIONS MUST DIFFER.
Four near-identical candidates make the choice meaningless and the whole design
pointless, and that is cheap to find out before any interface is built.

`audit_diversity.py` measures the analogous thing for the model track, but it
needs a ground-truth atlas to compare against and the product has none.

THE STATISTIC. Each candidate reference gets the style vector `reference_gate`
already uses -- each glyph's features z-scored against THAT CHARACTER's
distribution over 250 corpus fonts -- averaged over the two glyphs. Then:

  WITHIN   mean pairwise distance between candidates of the SAME description
  BETWEEN  mean pairwise distance between candidates of DIFFERENT descriptions
  RATIO    within / between

Both failure modes are visible in one number, and they are opposite:

  ratio -> 0    the seeds collapse. The picker has nothing to offer. BLOCKING.
  ratio -> 1    the description is not controlling the style at all. Also
                serious, and a different problem from the one this asks about.

=== PRE-REGISTRATION, fixed before running ===

SAMPLE        Every usable candidate in --dir, grouped by the `NN-` style
              prefix. A style with fewer than 2 usable candidates contributes
              no within-distance and is reported as dropped, never imputed.
PRIMARY       ratio = within / between.
BAR           ratio < 0.15  => COLLAPSE. Reported as a blocking failure for the
                               options-and-iterate design.
              ratio > 0.85  => the description is not controlling style.
              otherwise     => the picker has something to offer; the value is
                               reported without a further claim.
SIGNIFICANCE  Permutation, 2000 draws, shuffling style labels across candidates
              and recomputing the ratio. The null ratio is ~1 by construction.
              p = fraction of null ratios <= observed, +1 corrected.
ANCHOR        DESCRIPTIVE. The gate rejects a reference whose two glyphs sit
              more than 1.875 apart in THIS SAME SPACE. The fraction of
              within-description candidate pairs exceeding 1.875 is therefore
              "at least as different as a pair the gate calls inconsistent" --
              a human-scale reference, not a bar.
PER STYLE     DESCRIPTIVE ONLY. Some descriptions may pin the style harder than
              others; no claim is made about which.
IF IT FAILS   A collapse is reported as a blocking failure for the design, not
              worked around by raising n until something differs.

  python analysis/within_prompt_diversity.py --dir eval_runs/_candidate_refs/klein-base-n4
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import collections
import glob
import itertools
import json
import os
import re

import numpy as np

from analysis.reference_gate import glyph_cells
from analysis.style_coherence import FEATURES, cell_features

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DIR = os.path.join(REPO, "eval_runs", "_candidate_refs", "klein-base-n4")
REF_CHARS = "Kg"
GATE_THRESHOLD = 1.875          # analysis/reference_gate.py, same space
PERM_ITERS = 2000
COLLAPSE, SATURATED = 0.15, 0.85


SEED_SUFFIX = re.compile(r"__s\d+$")


def description_of(stem):
    """The description a candidate belongs to.

    NOT `stem.split("__")[0]`. The style prefix is truncated to 28 characters
    and that cut can land ON AN UNDERSCORE, so
    `10-an_inline_face_with_a_white___s0` carries THREE underscores and the
    naive split silently returns `...white` instead of `...white_`. Grouping
    still worked -- every candidate loses the same character -- but the KEY was
    wrong, and a downstream glob built from it matched nothing, dropping the
    widest-spread description from the transfer test without erroring.
    """
    return SEED_SUFFIX.sub("", stem)


def style_vector(path, stats, chars=REF_CHARS):
    """Mean z-scored style vector over the reference's two glyphs.

    `reference_consistency` returns the DISTANCE between the two glyphs. Here
    the two are averaged instead, because the question is where this candidate
    sits in style space, not whether it agrees with itself.
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
    return np.clip(np.asarray(vecs, dtype=float), -8, 8).mean(axis=0)


def pair_distances(vectors, labels):
    """(within, between) lists of pairwise distances, grouped by label."""
    within, between = [], []
    for i, j in itertools.combinations(range(len(vectors)), 2):
        d = float(np.linalg.norm(vectors[i] - vectors[j]))
        (within if labels[i] == labels[j] else between).append(d)
    return within, between


def ratio_of(vectors, labels):
    within, between = pair_distances(vectors, labels)
    if not within or not between:
        return None
    return float(np.mean(within) / np.mean(between))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--json", default=os.path.join(REPO, "research",
                                                   "within_prompt_diversity.json"))
    args = ap.parse_args()

    from analysis.style_coherence import load_stats

    stats = load_stats()
    paths = sorted(glob.glob(os.path.join(args.dir, "*.png")))
    if not paths:
        print(f"no candidates in {args.dir}", file=_sys.stderr)
        return 2

    vectors, labels, unscoreable = [], [], []
    for p in paths:
        v = style_vector(p, stats)
        stem = os.path.splitext(os.path.basename(p))[0]
        if v is None:
            unscoreable.append(stem)
            continue
        vectors.append(v)
        labels.append(description_of(stem))
    vectors = np.asarray(vectors)

    counts = collections.Counter(labels)
    dropped = [k for k, c in counts.items() if c < 2]
    print(f"\n  {len(vectors)} usable candidates over {len(counts)} descriptions"
          f"   unscoreable {len(unscoreable)}")
    if dropped:
        print(f"  dropped from WITHIN (fewer than 2 usable): {len(dropped)}")

    within, between = pair_distances(vectors, labels)
    observed = float(np.mean(within) / np.mean(between))

    rng = np.random.default_rng(0)
    null = []
    for _ in range(PERM_ITERS):
        r = ratio_of(vectors, list(rng.permutation(labels)))
        if r is not None:
            null.append(r)
    null = np.asarray(null)
    p = float(((null <= observed).sum() + 1) / (len(null) + 1))

    print(f"\n  WITHIN  mean {np.mean(within):.3f}   n={len(within)} pairs")
    print(f"  BETWEEN mean {np.mean(between):.3f}   n={len(between)} pairs")
    print(f"  RATIO   {observed:.3f}   permutation p = {p:.4f} "
          f"(null mean {null.mean():.3f})")

    verdict = ("COLLAPSE" if observed < COLLAPSE else
               "DESCRIPTION NOT CONTROLLING STYLE" if observed > SATURATED else
               "the picker has something to offer")
    print(f"  PRE-REGISTERED BANDS  <{COLLAPSE} collapse, >{SATURATED} "
          f"not controlling: {verdict}")
    if observed < COLLAPSE:
        print("\n  BLOCKING for options-and-iterate. Reported as a failure, not")
        print("  worked around by raising n until something differs.")

    above = float(np.mean([d > GATE_THRESHOLD for d in within]))
    print(f"\n  DESCRIPTIVE  {above:.0%} of within-description pairs exceed "
          f"{GATE_THRESHOLD}, the distance at which")
    print("  the gate calls a reference's own two glyphs inconsistent.")

    per_style = {}
    for label in sorted(counts):
        idx = [i for i, l in enumerate(labels) if l == label]
        if len(idx) < 2:
            continue
        d = [float(np.linalg.norm(vectors[i] - vectors[j]))
             for i, j in itertools.combinations(idx, 2)]
        per_style[label] = {"n": len(idx), "mean": float(np.mean(d)),
                            "min": float(np.min(d)), "max": float(np.max(d))}
    print(f"\n  DESCRIPTIVE ONLY -- per description\n"
          f"  {'description':<34} {'n':>3} {'mean':>7} {'min':>7} {'max':>7}")
    for label, e in sorted(per_style.items(), key=lambda kv: kv[1]["mean"]):
        print(f"  {label:<34} {e['n']:>3} {e['mean']:>7.3f} "
              f"{e['min']:>7.3f} {e['max']:>7.3f}")

    # Repo-relative, never absolute -- a tracked record must not carry a home
    # directory (see sanitize_for_publish).
    payload = {"preregistered": True,
               "dir": os.path.relpath(args.dir, REPO).replace("\\", "/"),
               "collapse_below": COLLAPSE, "saturated_above": SATURATED,
               "within_mean": float(np.mean(within)),
               "between_mean": float(np.mean(between)),
               "ratio": observed, "p": p, "verdict": verdict,
               "frac_within_above_gate": above,
               "unscoreable": unscoreable, "per_style": per_style}
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
