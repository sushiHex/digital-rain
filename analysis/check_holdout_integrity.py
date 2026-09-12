"""Is the 50-font holdout actually 50 independent observations? No.

Every comparison in this project treats the holdout as n=50 independent fonts
and pairs by font. Two construction flaws break that, both found by hashing the
committed artifacts:

1. **Duplicate ground truth.** Six fonts collapse into two groups with
   BYTE-IDENTICAL atlases -- IBMPlexSansArabic/Thai/ThaiLooped and
   TiroGurmukhi/Tamil/Telugu. They are non-Latin script families whose LATIN
   glyphs are shared, so a 95-char ASCII atlas is the same file. Effective n is
   46, not 50, and those typefaces carry triple weight in every aggregate.

2. **Duplicate INPUT with different targets.** BitcountGridDoubleInk and
   BitcountPropDoubleInk have byte-identical REFERENCE images but different GT
   atlases (mean |diff| 36.6/255). The reference is the model's only input, so
   it emits byte-identical output for both -- and is then scored against two
   different answers. It is structurally impossible to do well on both; their
   char_acc split (0.1383 vs 0.2660) is an artifact of which target the one
   output lands nearer.

That second case matters beyond the arithmetic: those two fonts were repeatedly
cited as per-font evidence for the oversampling and corpus-expansion work.

  python analysis/check_holdout_integrity.py
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import hashlib
import os
from collections import defaultdict


def hash_groups(pattern):
    """{sha256: [basenames]} for files matching pattern, duplicates only."""
    by_hash = defaultdict(list)
    for p in sorted(glob.glob(pattern)):
        with open(p, "rb") as f:
            by_hash[hashlib.sha256(f.read()).hexdigest()].append(
                os.path.splitext(os.path.basename(p))[0])
    return {h: names for h, names in by_hash.items() if len(names) > 1}, len(by_hash)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--holdout", default="eval_holdout")
    ap.add_argument("--generated", default=None,
                    help="Optional eval_runs/<run>/generated dir to check too.")
    ap.add_argument("--strict", action="store_true",
                    help="Exit non-zero if any duplicate is found.")
    args = ap.parse_args(argv)

    problems = 0
    for label, pat in (("ground-truth atlases", f"{args.holdout}/atlases/*.png"),
                       ("reference images", f"{args.holdout}/references/*.png")):
        dups, n_unique = hash_groups(pat)
        total = len(glob.glob(pat))
        print(f"{label}: {total} files, {n_unique} unique")
        for names in dups.values():
            problems += 1
            print(f"  IDENTICAL: {', '.join(n[:44] for n in names)}")
        if not dups:
            print("  (no duplicates)")

    if args.generated:
        dups, n_unique = hash_groups(f"{args.generated}/*.png")
        total = len(glob.glob(f"{args.generated}/*.png"))
        print(f"generated atlases: {total} files, {n_unique} unique")
        for names in dups.values():
            print(f"  IDENTICAL: {', '.join(n[:44] for n in names)}")

    print("\nConsequences for any paired test over this holdout:")
    print("  * effective n is the number of UNIQUE ground-truth atlases, not 50;")
    print("  * fonts sharing a REFERENCE receive identical model input, so a")
    print("    per-font difference between them measures the target, not the model.")

    if args.strict and problems:
        raise SystemExit(f"{problems} duplicate group(s) found")


if __name__ == "__main__":
    main()
