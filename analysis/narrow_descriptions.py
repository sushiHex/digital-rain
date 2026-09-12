"""Which descriptions give the user no real choice, and what should be said?

THE PROBLEM THIS TURNS INTO A SIGNAL. Within-description spread runs 0.454 to
3.960 across the twelve descriptions -- an 8.7x range -- and it is NARROWEST
exactly where the generator is known to fail. Four seeds of "a stencil sans with
deliberate breaks" produce four solid faces. Offering a user four options there
is a false promise: re-rolling cannot rescue a prompt the model systematically
misses. (`research/2026-08-25-the-picker-works-except-where-it-is-needed.md`)

NO NEW INSTRUMENT, AND NO INVENTED CONSTANT. The cut is taken from a threshold
that already exists and was derived elsewhere: `reference_gate` rejects a
reference whose OWN TWO GLYPHS sit more than 1.875 apart, because at that
distance they no longer read as one typeface. So for a pair of CANDIDATES,
1.875 is the distance at which the gate would call them different styles.

A description offers a real choice when at least one of its candidate pairs
reaches that distance. A description where NO pair does is offering variations
the project's own validated instrument would call the same style.

That cut is 0 out of N pairs -- not a percentile, not a number fitted to these
twelve, and not a judgement about where "enough" begins.

WHAT THIS IS NOT. It is not calibrated against human judgement, because no
person has yet labelled a candidate set as offering a real choice or not. The
gate's own 1.875 carries the same caveat and says so. Both are provisional in
the same way and for the same reason.

  python analysis/narrow_descriptions.py
  python analysis/narrow_descriptions.py --json research/narrow_descriptions.json
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

from analysis.within_prompt_diversity import (GATE_THRESHOLD, description_of,
                                              style_vector)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DIR = os.path.join(REPO, "eval_runs", "_candidate_refs", "klein-base-n4")

# What the interface should do, by band. Written here rather than in the UI so
# the rule and the evidence for it live in one place.
ADVICE = {
    "choice": "show all candidates",
    "narrow": ("show them, and say the model draws this style much the same way "
               "every time -- offer to reword rather than re-roll"),
}


def analyse(directory, stats, threshold=GATE_THRESHOLD):
    """Per description: pairwise distances, and whether any pair clears the gate."""
    by_desc = {}
    unscoreable = []
    for path in sorted(glob.glob(os.path.join(directory, "*.png"))):
        stem = os.path.splitext(os.path.basename(path))[0]
        v = style_vector(path, stats)
        if v is None:
            unscoreable.append(stem)
            continue
        by_desc.setdefault(description_of(stem), []).append(v)

    rows = []
    for desc, vecs in sorted(by_desc.items()):
        if len(vecs) < 2:
            rows.append({"description": desc, "n": len(vecs),
                         "skipped": "fewer than 2 usable candidates"})
            continue
        d = [float(np.linalg.norm(a - b))
             for a, b in itertools.combinations(vecs, 2)]
        above = int(sum(x > threshold for x in d))
        rows.append({"description": desc, "n": len(vecs), "pairs": len(d),
                     "mean": float(np.mean(d)), "max": float(np.max(d)),
                     "pairs_above_gate": above,
                     "verdict": "choice" if above else "narrow"})
    return rows, unscoreable


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--json", default=os.path.join(REPO, "research",
                                                   "narrow_descriptions.json"))
    args = ap.parse_args()

    from analysis.style_coherence import load_stats

    rows, unscoreable = analyse(args.dir, load_stats())
    scored = [r for r in rows if "verdict" in r]
    if not scored:
        print(f"nothing scoreable in {args.dir}", file=_sys.stderr)
        return 2

    print(f"\n  cut: a description offers a CHOICE when at least one candidate "
          f"pair exceeds {GATE_THRESHOLD},")
    print("  the distance at which `reference_gate` calls two glyphs different "
          "styles.\n")
    print(f"  {'description':<34} {'n':>3} {'mean':>7} {'max':>7} "
          f"{'>gate':>6}  verdict")
    for r in sorted(scored, key=lambda r: r["max"]):
        print(f"  {r['description'][:33]:<34} {r['n']:>3} {r['mean']:>7.3f} "
              f"{r['max']:>7.3f} {r['pairs_above_gate']:>3}/{r['pairs']:<2} "
              f"{r['verdict']}")

    narrow = [r for r in scored if r["verdict"] == "narrow"]
    print(f"\n  NARROW: {len(narrow)} of {len(scored)} descriptions")
    for r in narrow:
        print(f"    {r['description']}")
    print(f"\n  interface, choice : {ADVICE['choice']}")
    print(f"  interface, narrow : {ADVICE['narrow']}")
    print("\n  PROVISIONAL. Not calibrated against human judgement -- nobody has")
    print("  yet labelled a candidate set as offering a real choice or not. The")
    print("  gate's own 1.875 carries the same caveat, for the same reason.")

    # Repo-relative, never absolute -- a tracked record must not carry a home
    # directory (see sanitize_for_publish).
    payload = {"threshold": GATE_THRESHOLD,
               "dir": os.path.relpath(args.dir, REPO).replace("\\", "/"),
               "calibrated_against_humans": False, "advice": ADVICE,
               "narrow": [r["description"] for r in narrow],
               "unscoreable": unscoreable, "rows": rows}
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
