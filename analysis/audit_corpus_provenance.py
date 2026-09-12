"""Emit a TRACKED, auditable licence manifest for the training corpus.

WHY THIS EXISTS. The repo asserted "the training corpus is 97.5% OFL" for
months. That number counted a raw Google Fonts *checkout* (3760/3858), not the
925 fonts actually trained on -- `build_dataset` then filters for charset
support and near-duplicates, and writes its manifest into a GITIGNORED tree, so
a clean clone contained no source-to-training-item mapping at all. Nobody could
check the claim, including the people repeating it.

The real composition is 87.0% OFL, with 49 fonts whose OWN licence field states
vendor-supplied terms that permit rendering content but not redistribution or
conversion -- a right-to-train question that no output licence fixes. See
research/2026-08-08-the-corpus-is-not-97-percent-ofl.md.

Licence comes from the font's embedded name ID 13 wherever the fetch manifest
is silent. Do NOT infer it from where the file lives: Inter and Lato are OFL
and are also installed in C:\\Windows\\Fonts.

So: this script reads the gitignored inputs and writes a COMMITTED artifact,
`research/corpus_provenance.json`. The point is that the output is tracked. Any
future licence claim about the corpus must be derivable from that file in a
clean clone, and `tests/test_corpus_provenance.py` fails if the headline
numbers drift from it.

  python analysis/audit_corpus_provenance.py            # rewrite the manifest
  python analysis/audit_corpus_provenance.py --check    # verify, exit 1 on drift
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
import os
from collections import Counter

CORPUS = "research/font_distinctiveness.json"
POOL = "font_pool/source_manifest.json"
OUT = "research/corpus_provenance.json"
WINDOWS_FONTS = r"C:\Windows\Fonts"

# Licences that permit training and derivative distribution for this project's
# purposes. Anything outside this set is called out individually, not bucketed.
PERMISSIVE = {"OFL-1.1", "OFL", "Apache-2.0", "UFL"}


def load_corpus(path=CORPUS):
    d = json.load(open(path, encoding="utf-8"))
    return sorted(d.get("scores", d))


def load_pool(path=POOL):
    """{stem: entry} from the (gitignored) fetch manifest, case-tolerant."""
    if not os.path.isfile(path):
        return {}
    by_stem = {}
    for e in json.load(open(path, encoding="utf-8")):
        stem = os.path.splitext(e["filename"])[0]
        by_stem.setdefault(stem, e)
        by_stem.setdefault(stem.lower(), e)
    return by_stem


def windows_font_stems(d=WINDOWS_FONTS):
    if not os.path.isdir(d):
        return set()
    return {os.path.splitext(f)[0].lower() for f in os.listdir(d)}


# ---------------------------------------------------------------------------
# Reading the licence OUT OF THE FONT, which is the only authoritative source.
#
# An earlier version of this script inferred "proprietary" from presence in
# C:\Windows\Fonts. That is not evidence: Inter and Lato are OFL and are also
# installed there, and a first pass with loose substring markers additionally
# scored Arial as open, because the phrase "...as permitted by the license
# terms..." contains "mit licen". Classify on the LEADING CLAUSE of name ID 13,
# which is what actually states the terms.
# ---------------------------------------------------------------------------
FONT_SEARCH_DIRS = [WINDOWS_FONTS, "extra-fonts", "font_pool", "google-fonts"]
MS_BOILERPLATE = "microsoft supplied font"
LIBRE_PHRASES = {
    "OFL-1.1": "licensed under the sil open font license",
    "Apache-2.0": "licensed under the apache license",
    "UFL": "ubuntu font licence",
}


def find_font_file(stem, dirs=None):
    import glob

    for root in (dirs or FONT_SEARCH_DIRS):
        if not os.path.isdir(root):
            continue
        for ext in (".ttf", ".otf", ".ttc"):
            p = os.path.join(root, stem + ext)
            if os.path.isfile(p):
                return p
        hits = [h for h in glob.glob(os.path.join(root, "**", stem + ".*"),
                                     recursive=True)
                if h.lower().endswith((".ttf", ".otf", ".ttc"))]
        if hits:
            return sorted(hits)[0]
    return None


def embedded_licence(path):
    """(licence_label, copyright, note) read from the font's own name table."""
    try:
        from fontTools.ttLib import TTFont
        t = TTFont(path, lazy=True, fontNumber=0)["name"]
        desc = (t.getDebugName(13) or "").strip()
        cp = (t.getDebugName(0) or "").strip()
    except Exception as e:
        return None, "", f"unreadable: {e}"
    low = desc.lower()
    if low.startswith(MS_BOILERPLATE):
        note = ("restricted: vendor-supplied terms permit rendering content, "
                "not redistribution or conversion")
        if "open font license" in low:
            note += "; the UPSTREAM release of this face is OFL -- re-source it"
        return "PROPRIETARY", cp, note
    for label, phrase in LIBRE_PHRASES.items():
        if phrase in low:
            return label, cp, "libre licence stated in the font"
    if not desc:
        return None, cp, "no licence field in the font"
    return None, cp, f"unrecognized licence text: {desc[:80]}"


def build(corpus=None, pool=None, winstems=None):
    corpus = load_corpus() if corpus is None else corpus
    pool = load_pool() if pool is None else pool
    winstems = windows_font_stems() if winstems is None else winstems

    entries, lic = [], Counter()
    for name in corpus:
        e = pool.get(name) or pool.get(name.lower())
        licence = (e or {}).get("license")
        rec = {
            "stem": name,
            "license": licence,
            "source": (e or {}).get("source"),
            "resolved": e is not None,
        }
        if e is None:
            # Fall back to the font's OWN embedded licence before giving up.
            # This is authoritative where the fetch manifest is merely absent.
            rec["in_windows_fonts"] = name.lower() in winstems
            path = find_font_file(name)
            if path:
                emb, cp, note = embedded_licence(path)
                rec["embedded_license"] = emb
                rec["embedded_note"] = note
                rec["copyright"] = cp[:120]
                rec["source_file"] = path
                if emb:
                    rec["license"] = emb
                    licence = emb
        entries.append(rec)
        lic[licence or "UNRESOLVED"] += 1

    n = len(entries)
    unresolved = [e for e in entries if not e["resolved"]]
    proprietary = [e for e in entries if e.get("license") == "PROPRIETARY"]
    still_unknown = [e for e in unresolved if not e.get("license")]
    ofl = lic.get("OFL-1.1", 0) + lic.get("OFL", 0)
    permissive = sum(v for k, v in lic.items() if k in PERMISSIVE)

    return {
        "_comment": "Generated by analysis/audit_corpus_provenance.py. TRACKED "
                    "on purpose: its inputs are gitignored, so this file is the "
                    "only clean-clone evidence for any corpus licence claim.",
        "corpus_size": n,
        "license_counts": dict(lic.most_common()),
        "ofl_count": ofl,
        "ofl_fraction": round(ofl / n, 4) if n else 0.0,
        "permissive_fraction": round(permissive / n, 4) if n else 0.0,
        "unresolved_in_pool_count": len(unresolved),
        "proprietary_count": len(proprietary),
        "proprietary_stems": sorted(e["stem"] for e in proprietary),
        "proprietary_upstream_is_libre": sorted(
            e["stem"] for e in proprietary
            if "UPSTREAM" in (e.get("embedded_note") or "")),
        "still_unknown_count": len(still_unknown),
        "still_unknown_stems": sorted(e["stem"] for e in still_unknown),
        "max_ofl_fraction_if_all_unknown_were_ofl":
            round((ofl + len(still_unknown)) / n, 4) if n else 0.0,
        "fonts": entries,
    }


def summarize(m):
    n = m["corpus_size"]
    out = [f"corpus: {n} fonts"]
    for k, v in m["license_counts"].items():
        out.append(f"  {k:<14} {v:4d}  {v/n:7.2%}")
    out.append(f"\nOFL fraction            : {m['ofl_fraction']:.2%}")
    out.append(f"ceiling if every still-unknown font were OFL: "
               f"{m['max_ofl_fraction_if_all_unknown_were_ofl']:.2%}")
    out.append(f"absent from the fetch manifest : {m['unresolved_in_pool_count']}")
    out.append(f"PROPRIETARY (per the font's own licence field): "
               f"{m['proprietary_count']}  <-- right-to-train question")
    if m["proprietary_stems"]:
        out.append("  " + ", ".join(m["proprietary_stems"][:12]) + " ...")
    if m["proprietary_upstream_is_libre"]:
        out.append(f"  of those, libre UPSTREAM (re-source to fix): "
                   f"{', '.join(m['proprietary_upstream_is_libre'])}")
    out.append(f"still unknown           : {m['still_unknown_count']}")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="compare against the committed manifest; exit 1 on drift")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)

    if not os.path.isfile(POOL):
        raise SystemExit(
            f"{POOL} is missing. It is gitignored -- this script must be run in a "
            "working checkout that has fetched the font pool. The COMMITTED "
            f"{OUT} is the artifact for everyone else.")

    fresh = build()
    print(summarize(fresh))

    if args.check:
        if not os.path.isfile(args.out):
            raise SystemExit(f"\nFAIL: {args.out} does not exist; run without --check")
        old = json.load(open(args.out, encoding="utf-8"))
        drift = [k for k in ("corpus_size", "license_counts", "ofl_count",
                             "proprietary_count", "still_unknown_count")
                 if old.get(k) != fresh.get(k)]
        if drift:
            print(f"\nFAIL: committed manifest is stale on {drift}")
            return 1
        print(f"\nOK: {args.out} matches the current pool")
        return 0

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(fresh, f, indent=1, sort_keys=False)
        f.write("\n")
    print(f"\nwrote {args.out}  ({len(fresh['fonts'])} entries) -- COMMIT THIS")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
