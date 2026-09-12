"""What style attributes can this corpus label for FREE, and at what n?

WHY THIS RUNS BEFORE ANY CLASSIFIER. Generic CLIP was ruled out for style
adherence on a pre-registered test (6/12, p=0.6128 --
`research/2026-08-24-clip-does-not-read-the-decisive-clause.md`). The registered
alternative is a DISCRIMINATIVE per-attribute classifier, justified in three
documents with the sentence "the labels are free because the fonts' own metadata
supplies them". That sentence was never checked. This tool checks it.

TWO SUPPLIES, AND THEY ARE NOT EQUALLY TRUSTWORTHY

  TABLES  OS/2.usWeightClass, OS/2.usWidthClass, post.italicAngle, PANOSE.
          Numeric, present on nearly every file, and not editorial.
  NAMES   keywords in the family name -- free, but sparse, unverified, and
          absent whenever a foundry did not think to mention the attribute.

COUNT FAMILIES, NOT FILES. A holdout must split by family: 32 of the 50 holdout
fonts share a superfamily with a training font, and that is a known, recorded
defect of the existing benchmark. So the n that governs a classifier is the
number of distinct FAMILIES carrying a label, not the number of files. One
family with 18 weights is one observation for a stencil/not-stencil question and
eighteen for a weight question. Both counts are reported; the family count is
the one to plan against.

THE PANOSE TRAP, AND WHY bFamilyType IS READ FIRST. `bSerifStyle` only means
"what kind of serif" when `bFamilyType == 2` (Latin Text). Under bFamilyType 3
(Hand Written), 4 (Decorative) or 5 (Symbol) the same byte indexes a completely
different table, so reading it as a serif label silently mislabels every
decorative face. A first draft of this measurement did exactly that.

  python analysis/attribute_label_supply.py
  python analysis/attribute_label_supply.py --pool font_pool --json out.json
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import json
import os
import re
import warnings

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUSIONS = os.path.join(REPO, "research", "corpus_exclusions.json")

# Name keywords. Deliberately narrow: a loose pattern inflates the count with
# false positives, and the whole point here is to find out whether the rare
# attributes are rare.
NAME_ATTRS = {
    "stencil": r"stencil",
    "inline": r"inline",
    "outline": r"outline",
    "shadow": r"shadow",
    "slab": r"slab",
    "rounded": r"round(ed)?\b",
    "script/hand": r"script|handwriting|brush|cursive",
    "display": r"display",
    "mono": r"mono",
}

# PANOSE bSerifStyle, valid ONLY when bFamilyType == 2 (Latin Text).
PANOSE_LATIN_TEXT = 2
PANOSE_SERIF = frozenset(range(2, 11)) | {14, 15}   # cove .. triangle, flared, rounded
PANOSE_SANS = frozenset({11, 12, 13})               # normal / obtuse / perpendicular sans

# A classifier needs enough distinct FAMILIES to hold some out. Below this an
# attribute is reported as unsupplied rather than as a small class.
MIN_FAMILIES = 40


def family_of(stem):
    """The family key, matching the convention `corpus_exclusions.json` uses."""
    return stem.split("[")[0].split("-")[0]


def scan(pool, exclude):
    """Read every font once. Returns per-file records, skipping excluded families."""
    from fontTools.ttLib import TTFont

    paths = []
    for ext in ("*.ttf", "*.otf"):
        paths.extend(sorted(glob.glob(os.path.join(pool, ext))))

    records, unreadable = [], []
    for path in paths:
        stem = os.path.splitext(os.path.basename(path))[0]
        family = family_of(stem)
        if family in exclude:
            continue
        rec = {"stem": stem, "family": family}
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                font = TTFont(path, lazy=True, fontNumber=0)
                os2, post = font.get("OS/2"), font.get("post")
                if os2 is not None:
                    rec["weight"] = int(os2.usWeightClass)
                    rec["width"] = int(os2.usWidthClass)
                    panose = getattr(os2, "panose", None)
                    if panose is not None:
                        rec["panose_family"] = int(getattr(panose, "bFamilyType", 0))
                        rec["panose_serif"] = int(getattr(panose, "bSerifStyle", 0))
                if post is not None:
                    rec["italic_angle"] = float(post.italicAngle)
                font.close()
        except Exception as exc:                      # noqa: BLE001 - report, don't crash
            unreadable.append((stem, type(exc).__name__))
            continue
        records.append(rec)
    return records, unreadable


def _supply(records, predicate):
    """(files, families) carrying a label, given a per-record predicate."""
    hits = [r for r in records if predicate(r)]
    return len(hits), len({r["family"] for r in hits})


def measure(records):
    """Every attribute, as (files, families) both for and against."""
    out = {}

    def add(name, source, positive, negative=None):
        pos_f, pos_fam = _supply(records, positive)
        entry = {"source": source, "files": pos_f, "families": pos_fam}
        if negative is not None:
            neg_f, neg_fam = _supply(records, negative)
            entry["negative_files"] = neg_f
            entry["negative_families"] = neg_fam
        entry["trainable"] = bool(pos_fam >= MIN_FAMILIES and
                                  (negative is None or
                                   entry.get("negative_families", 0) >= MIN_FAMILIES))
        out[name] = entry

    add("weight", "OS/2.usWeightClass",
        lambda r: r.get("weight", 400) != 400,
        lambda r: r.get("weight", 400) == 400)
    add("width", "OS/2.usWidthClass",
        lambda r: r.get("width", 5) != 5,
        lambda r: r.get("width", 5) == 5)
    add("slant", "post.italicAngle",
        lambda r: abs(r.get("italic_angle", 0.0)) > 0.01,
        lambda r: abs(r.get("italic_angle", 0.0)) <= 0.01)

    def latin_text(r):
        return r.get("panose_family") == PANOSE_LATIN_TEXT

    add("serif vs sans", "PANOSE.bSerifStyle (bFamilyType==2 only)",
        lambda r: latin_text(r) and r.get("panose_serif") in PANOSE_SERIF,
        lambda r: latin_text(r) and r.get("panose_serif") in PANOSE_SANS)

    for name, pattern in NAME_ATTRS.items():
        rx = re.compile(pattern, re.I)
        add(name, "family name", lambda r, rx=rx: bool(rx.search(r["stem"])))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pool", default=os.path.join(REPO, "font_pool"))
    ap.add_argument("--json", default=os.path.join(REPO, "research",
                                                   "attribute_label_supply.json"))
    args = ap.parse_args()

    if not os.path.isdir(args.pool):
        print(f"font pool not found: {args.pool}", file=_sys.stderr)
        return 2

    exclude = set(json.load(open(EXCLUSIONS, encoding="utf-8"))["exclude_stems"])
    records, unreadable = scan(args.pool, exclude)
    families = {r["family"] for r in records}
    print(f"\nlicence-clean files {len(records)}   families {len(families)}"
          f"   unreadable {len(unreadable)}   excluded families {len(exclude)}\n")

    table = measure(records)
    print(f"  {'attribute':<16} {'files':>7} {'families':>9}  {'source':<38} ok")
    for name, e in table.items():
        mark = "yes" if e["trainable"] else "NO"
        print(f"  {name:<16} {e['files']:>7} {e['families']:>9}  "
              f"{e['source']:<38} {mark}")

    trainable = [n for n, e in table.items() if e["trainable"]]
    missing = [n for n, e in table.items() if not e["trainable"]]
    print(f"\n  trainable at >={MIN_FAMILIES} families: {', '.join(trainable)}")
    print(f"  NOT supplied by the corpus: {', '.join(missing)}")

    payload = {"min_families": MIN_FAMILIES, "files": len(records),
               "families": len(families), "unreadable": unreadable,
               "attributes": table}
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
