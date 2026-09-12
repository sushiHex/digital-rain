"""Identify the corpus fonts whose licence could not be read from the font.

45 of the 925 training fonts carry NO licence field (name ID 13) and are absent
from the fetch manifest: 38 from `extra-fonts/fontshare`, 5 from
`extra-fonts/league`, 1 from `extra-fonts/fontsquirrel`, 1 not on disk at all.
`extra-fonts/` has no manifest and no licence files -- those fonts were copied
in outside `pipeline/fetch_fonts.py`, which is the only thing that records
provenance (and which has a `directory` adapter that would have done it).

This script gathers EVIDENCE rather than guessing. For each font it reads the
full name table (family, manufacturer, designer, vendor/designer URLs,
trademark, copyright) and checks whether the same family exists in the local
Google Fonts OFL tree -- which is authoritative, because a family shipped in
`google-fonts/ofl/` is available under OFL regardless of which copy was used
here.

VERDICTS, deliberately conservative:
  OFL_UPSTREAM   same family present in google-fonts/ofl -> re-source and the
                 provenance question closes without dropping the face
  VENDOR_REVIEW  identifiable foundry, no OFL copy found -> needs a human
                 licence decision against that foundry's terms
  UNKNOWN        no usable evidence

A verdict here is a research aid, not a legal conclusion. Nothing in this file
should be quoted as establishing a licence.

  python analysis/identify_unlicensed_corpus_fonts.py
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
import os
import re
from collections import Counter

MANIFEST = "research/corpus_provenance.json"
GF_OFL = "google-fonts/ofl"
OUT = "research/unlicensed_corpus_fonts.json"

NAME_IDS = {0: "copyright", 1: "family", 7: "trademark", 8: "manufacturer",
            9: "designer", 11: "vendor_url", 12: "designer_url"}


def slug(s):
    """Google Fonts directory convention: lowercase, alphanumerics only."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def read_names(path):
    try:
        from fontTools.ttLib import TTFont
        t = TTFont(path, lazy=True, fontNumber=0)["name"]
    except Exception as e:
        return {"error": str(e)}
    out = {}
    for nid, key in NAME_IDS.items():
        v = t.getDebugName(nid)
        if v:
            out[key] = v.strip()[:160]
    return out


def gf_families(root=GF_OFL):
    """{slug: dirname} for every family in the local Google Fonts OFL tree."""
    if not os.path.isdir(root):
        return {}
    return {slug(d): d for d in os.listdir(root)
            if os.path.isdir(os.path.join(root, d))}


def gf_has_ofl(dirname, root=GF_OFL):
    """Confirm the Google Fonts family directory actually ships an OFL file."""
    d = os.path.join(root, dirname)
    return any(f.upper().startswith("OFL") for f in os.listdir(d))


# Style words that may be appended to a family name in name ID 1 without
# changing which family it is. Stripping ONLY a trailing style word keeps
# "Knewave Outline" -> "Knewave" (a real Google Fonts family) while refusing to
# turn "Fira Sans" into "Fira", which is a different family.
STYLE_WORDS = {"outline", "italic", "regular", "bold", "book", "light",
               "medium", "black", "condensed", "expanded", "display", "text"}


def _family_candidates(fam):
    yield fam
    yield fam.replace(" ", "")
    parts = fam.split()
    if len(parts) > 1 and parts[-1].lower() in STYLE_WORDS:
        yield " ".join(parts[:-1])


def classify(names, gf):
    fam = names.get("family", "")
    for candidate in _family_candidates(fam):
        hit = gf.get(slug(candidate))
        if hit and gf_has_ofl(hit):
            note = "" if slug(candidate) == slug(fam) else \
                f" (matched on '{candidate}', trailing style word dropped)"
            return "OFL_UPSTREAM", f"google-fonts/ofl/{hit} ships an OFL file{note}"

    # Public-domain dedications state their terms in the copyright field.
    cp = (names.get("copyright") or "").lower()
    if "public domain" in cp:
        return "PUBLIC_DOMAIN", f"copyright field dedicates it: {names['copyright'][:100]}"
    vendor = " ".join(filter(None, (names.get("manufacturer"),
                                    names.get("designer"),
                                    names.get("vendor_url"),
                                    names.get("copyright")))).strip()

    # Fontshare (Indian Type Foundry) publishes under TWO licences: SIL OFL for
    # its open-source faces, and the proprietary "ITF Free Font License" for its
    # closed-source ones. Our fontshare files split exactly that way -- some
    # carry OFL text in name ID 13, these carry no licence field at all. Per
    # fontshare.com/licenses/itf-ffl, FFL fonts are "proprietary freeware ...
    # cannot be modified or redistributed", derivative works "are the exclusive
    # property of the Licensor" and "may not be ... given away without the
    # express written permission of the Licensor".
    #
    # That is squarely incompatible with training a generative model whose
    # OUTPUT fonts are distributed. Flagged as presumed, not proven: the
    # per-font open/closed split is published on the website, not in the file.
    if any(k in vendor.lower() for k in ("indian type foundry", "indiantypefoundry")):
        return "ITF_FFL_PRESUMED", (
            "Indian Type Foundry / Fontshare with NO licence field -- presumed "
            "closed-source ITF-FFL, which forbids modification and "
            "redistribution and claims derivative works. VERIFY per font.")
    if vendor:
        return "VENDOR_REVIEW", f"identifiable source: {vendor[:110]}"
    return "UNKNOWN", "no manufacturer, designer, URL or copyright in the font"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)

    man = json.load(open(MANIFEST, encoding="utf-8"))
    targets = [e for e in man["fonts"] if not e["resolved"] and not e.get("license")]
    gf = gf_families()
    print(f"{len(targets)} fonts with no readable licence; "
          f"{len(gf)} families in {GF_OFL}\n")

    rows = []
    for e in targets:
        path = e.get("source_file")
        names = read_names(path) if path and os.path.isfile(path) else {}
        if not path or not os.path.isfile(path):
            verdict, why = "UNKNOWN", "file not present on disk"
        else:
            verdict, why = classify(names, gf)
        rows.append({"stem": e["stem"], "source_file": path, "verdict": verdict,
                     "evidence": why, "names": names})

    order = {"OFL_UPSTREAM": 0, "PUBLIC_DOMAIN": 1, "VENDOR_REVIEW": 2,
             "ITF_FFL_PRESUMED": 3, "UNKNOWN": 4}
    rows.sort(key=lambda r: (order[r["verdict"]], r["stem"].lower()))
    # Designer names carry non-cp1252 characters and this console is cp1252,
    # so sanitize for display only. The JSON keeps the real text.
    def safe(s):
        return s.encode("ascii", "replace").decode("ascii")

    for r in rows:
        print(f"  {r['verdict']:<14} {safe(r['stem']):<18} {safe(r['evidence'])[:88]}")

    counts = Counter(r["verdict"] for r in rows)
    print("\n" + "=" * 60)
    for k, v in counts.most_common():
        print(f"  {k:<14} {v}")
    print("\nOFL_UPSTREAM fonts can be re-sourced from Google Fonts and the "
          "question closes.\nVENDOR_REVIEW needs a human decision against that "
          "foundry's terms.")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"_comment": "Evidence for the corpus fonts with no embedded "
                               "licence. A verdict here is a research aid, NOT a "
                               "legal conclusion.",
                   "counts": dict(counts), "fonts": rows}, f, indent=1)
        f.write("\n")
    print(f"\nwrote {args.out} -- COMMIT THIS")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
