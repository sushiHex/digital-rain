"""Decide, per training font, whether its licence permits this project's use.

Emits `research/corpus_exclusions.json` -- TRACKED, because it is what
`train_lora_kg.py` filters on and what any future licence claim rests on.

THE TEST APPLIED. This project trains a generative model on the corpus and
DISTRIBUTES the fonts it produces. A licence therefore has to permit two things
a plain use-the-font licence does not: creating derivative works, and
redistributing them. "Free for personal and commercial use" is a statement
about setting type; it is not a grant for either.

DECISIONS (see research/2026-08-08-identifying-the-undocumented-13-percent.md):

  KEEP  OFL-1.1 / Apache-2.0 / UFL -- explicit grants covering both.
  KEEP  Families confirmed OFL upstream whose local copy merely lacks a
        name-table licence field. A missing name ID 13 is a packaging omission,
        not a different licence. The files are re-sourced from the canonical
        OFL copy so future builds use it.
  DROP  Vendor-supplied Windows fonts. Their terms permit rendering content,
        not conversion or redistribution.
  DROP  Fontshare closed-source (ITF-FFL): "cannot be modified or
        redistributed", and derivative works are "the exclusive property of the
        Licensor". Directly contrary to the two rights this project needs.
  DROP  Anything with no locatable licence grant at all. Aggregator claims of
        "free for commercial use" are not a licence from the rights holder.

  python analysis/corpus_licence_exclusions.py
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
from collections import Counter

PROVENANCE = "research/corpus_provenance.json"
UNLICENSED = "research/unlicensed_corpus_fonts.json"
OUT = "research/corpus_exclusions.json"

PERMISSIVE = {"OFL-1.1", "OFL", "Apache-2.0", "UFL"}

# Families confirmed OFL/public-domain upstream, whose local file lacks a
# name-table licence field. Evidence recorded per entry; all verified 2026-08-08.
RECOVERED = {
    "Fira_Sans": "google-fonts/ofl/firasans ships an OFL file",
    "knewave": "google-fonts/ofl/knewave ships an OFL file",
    "prociono": "google-fonts/ofl/prociono ships an OFL file; the font's own "
                "copyright dedicates it to the public domain",
    "sniglet": "google-fonts/ofl/sniglet ships an OFL file",
    # First-party evidence: fetched from upstream and the licence read out of
    # the repository's own licence file, not a third-party listing.
    "chunk": "ChunkFive, The League of Moveable Type -- OFL-1.1 per the repo's "
             "own 'Open Font License.markdown' (github.com/theleagueof/chunk), "
             "re-fetched into font_pool",
    "junction": "Junction, The League of Moveable Type -- OFL-1.1 per the "
                "repo's own licence file (github.com/theleagueof/junction), "
                "re-fetched into font_pool",
    "CascadiaCode": "OFL-1.1 per the repo's own licence file "
                    "(github.com/microsoft/cascadia-code), re-fetched into "
                    "font_pool; the Windows-bundled copy carries Microsoft's "
                    "terms instead",
}

# Explicitly dropped despite an identifiable source, with the reason.
DROP_NAMED = {
    "20db": "Jovanny Lemonad ships no explicit licence; aggregator claims of "
            "'free for commercial use' are not a grant from the rights holder",
    "Striper": "Fontstore Pte Ltd, distributed via Fontshare -- same "
               "closed-source ITF-FFL question as the other Fontshare faces",
    "unispace_bd": "file is not present on disk; provenance unrecoverable",
}


def decide(entry, unlicensed_by_stem):
    stem, lic = entry["stem"], entry.get("license")
    if stem in RECOVERED:
        return "keep", f"recovered: {RECOVERED[stem]}"
    if stem in DROP_NAMED:
        return "drop", DROP_NAMED[stem]
    if lic in PERMISSIVE:
        return "keep", f"{lic} recorded in " + (
            "the fetch manifest" if entry.get("resolved") else "the font itself")
    if lic == "PROPRIETARY":
        return "drop", (entry.get("embedded_note")
                        or "vendor-supplied terms: rendering only")
    u = unlicensed_by_stem.get(stem)
    if u and u["verdict"] == "ITF_FFL_PRESUMED":
        return "drop", ("Fontshare closed-source (ITF-FFL presumed): forbids "
                        "modification and redistribution, claims derivatives")
    return "drop", f"no licence grant located (license={lic!r})"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)

    prov = json.load(open(PROVENANCE, encoding="utf-8"))
    unl = {r["stem"]: r for r in
           json.load(open(UNLICENSED, encoding="utf-8"))["fonts"]}

    keep, drop = [], []
    for e in prov["fonts"]:
        verdict, why = decide(e, unl)
        rec = {"stem": e["stem"], "license": e.get("license"), "reason": why}
        (keep if verdict == "keep" else drop).append(rec)

    n = len(prov["fonts"])
    print(f"corpus {n}  ->  keep {len(keep)}   drop {len(drop)}  "
          f"({len(drop)/n:.1%})")
    print("\ndrop reasons:")
    for r, c in Counter(d["reason"][:58] for d in drop).most_common():
        print(f"  {c:4d}  {r}")
    print(f"\nrecovered by re-sourcing: {len([k for k in keep if 'recovered' in k['reason']])}")

    payload = {
        "_comment": "TRACKED. train_lora_kg.py filters the corpus on "
                    "`exclude_stems`. Generated by "
                    "analysis/corpus_licence_exclusions.py; the test applied is "
                    "'does this licence permit creating AND redistributing "
                    "derivative works', because that is what this project does.",
        "corpus_size": n,
        "keep_count": len(keep),
        "exclude_count": len(drop),
        "exclude_stems": sorted(d["stem"] for d in drop),
        "excluded": sorted(drop, key=lambda d: d["stem"].lower()),
        "recovered": sorted((k for k in keep if "recovered" in k["reason"]),
                            key=lambda d: d["stem"].lower()),
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
        f.write("\n")
    print(f"\nwrote {args.out} -- COMMIT THIS")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
