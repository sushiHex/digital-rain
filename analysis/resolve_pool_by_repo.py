"""Resolve the last unknown-licence pool fonts from their SOURCE REPOSITORY.

After `analysis/resolve_pool_unknowns.py` read what it could from embedded
licence fields, 781 entries remained unknown. Every one is github-sourced and
every one carries an `origin_url`, so the licence is recoverable from the
repository itself -- the authoritative statement, and only ~16 distinct repos.

Two evidence sources, both recorded:

  repo   GitHub's own licence detection for the origin repository (SPDX).
  font   the font's embedded name ID 13.

They are cross-checked. The FONT wins when they disagree, because a repository
can ship files under more than one licence and the per-font field is the
specific claim -- but the disagreement is always recorded, never silently
resolved.

Two classifications that must not be flattened into "free":

  CC-BY-NC-*  non-commercial. Usable for research, NOT for a commercial product,
              and not compatible with distributing generated fonts commercially.
  GPL*        copyleft. Fonts normally carry a font exception, but that has to
              be read; it is not the same grant as OFL.

  python analysis/resolve_pool_by_repo.py --dry-run
  python analysis/resolve_pool_by_repo.py
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
import os
import re
import subprocess
from collections import Counter, defaultdict

MANIFEST = "font_pool/source_manifest.json"
POOL_DIR = "font_pool"

# Checked in order. The restricted prefix MUST come first: the Windows-bundled
# Cascadia Code carries Microsoft's terms and mentions the OFL further down, so
# an OFL match on the whole string would misread it as libre.
RESTRICTED_PREFIXES = ("microsoft supplied font",)
PHRASES = [
    ("CC-BY-NC", ("creative commons by-nc", "creative commons attribution-noncommercial",
                  "cc by-nc", "noncommercial")),
    ("GPL", ("gnu freefont", "gnu general public license", "gnu gpl")),
    ("OFL-1.1", ("sil open font license", "sil ofl", "open font license")),
    ("Apache-2.0", ("licensed under the apache license", "apache license, version 2.0")),
    ("UFL", ("ubuntu font licence", "ubuntu font license")),
    ("MIT", ("permission is hereby granted, free of charge",)),
]
# Licences that permit training on the font AND redistributing derivatives.
PERMISSIVE = {"OFL-1.1", "Apache-2.0", "UFL", "MIT"}


def classify_text(desc):
    low = (desc or "").strip().lower()
    if not low:
        return None
    if low.startswith(RESTRICTED_PREFIXES):
        return "PROPRIETARY"
    for label, phrases in PHRASES:
        if any(p in low for p in phrases):
            return label
    return None


def repo_slug(url):
    m = re.search(r"github\.com[/:]([^/]+/[^/]+?)(?:\.git)?/?$", url or "")
    return m.group(1) if m else None


def _gh(*args, timeout=60):
    try:
        out = subprocess.run(["gh", *args], capture_output=True, text=True,
                             timeout=timeout)
        return out.stdout if out.returncode == 0 else ""
    except Exception:
        return ""


def repo_licence_file(slug, cache):
    """Classify a licence file in the repo root that GitHub did NOT detect.

    GitHub's detector only recognizes conventionally-named files. Velvetyne
    ships `OFL_BluuNext.txt` and `licence_BilboINC.txt`, so its repos report no
    licence at all while stating one plainly in the root -- and the two say
    DIFFERENT things (OFL vs CC BY-NC-SA), so guessing by foundry would have
    been wrong for one of them.
    """
    key = ("file", slug)
    if key in cache:
        return cache[key]
    names = _gh("api", f"repos/{slug}/contents", "--jq", ".[].name").split()
    result = None
    for name in names:
        low = name.lower()
        if not any(k in low for k in ("licen", "ofl", "copying", "gpl")):
            continue
        if any(x in low for x in ("faq", "readme")):
            continue
        import base64
        b64 = _gh("api", f"repos/{slug}/contents/{name}", "--jq", ".content")
        try:
            text = base64.b64decode(b64).decode("utf-8", "ignore")
        except Exception:
            continue
        result = classify_text(text)
        if result:
            break
    cache[key] = result
    return result


def repo_licence(slug, cache):
    """GitHub's detected SPDX id for a repo, falling back to its licence file."""
    if slug in cache:
        return cache[slug]
    val = _gh("api", f"repos/{slug}/license", "--jq", ".license.spdx_id").strip()
    if val in ("", "NOASSERTION", "null"):
        val = repo_licence_file(slug, cache)
    cache[slug] = val or None
    return cache[slug]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--manifest", default=MANIFEST)
    args = ap.parse_args(argv)

    from fontTools.ttLib import TTFont

    manifest = json.load(open(args.manifest, encoding="utf-8"))
    targets = [e for e in manifest if (e.get("license") or "unknown") == "unknown"]
    print(f"unknown-licence entries: {len(targets)}")

    by_repo = defaultdict(list)
    for e in targets:
        by_repo[repo_slug(e.get("origin_url"))].append(e)
    print(f"distinct source repositories: {len(by_repo)}\n")

    cache = {}
    resolved, disagree, still = Counter(), [], []
    for slug, entries in sorted(by_repo.items(), key=lambda kv: -len(kv[1])):
        rlic = repo_licence(slug, cache) if slug else None
        print(f"  {len(entries):4d}  {slug or '<no url>':<44} repo={rlic or '?'}")
        for e in entries:
            path = os.path.join(POOL_DIR, e["filename"])
            flic = None
            if os.path.isfile(path):
                try:
                    flic = classify_text(
                        TTFont(path, lazy=True, fontNumber=0)["name"].getDebugName(13))
                except Exception:
                    flic = None
            # The font's own field is the more specific claim; the repo is the
            # fallback. Record which was used, and any conflict.
            chosen, src = (flic, "font name ID 13") if flic else (rlic, f"repo {slug}")
            if flic and rlic and flic != rlic:
                disagree.append((e["filename"], flic, rlic))
            if not chosen:
                still.append(e["filename"])
                continue
            resolved[chosen] += 1
            if not args.dry_run:
                e["license"] = chosen
                e["license_source"] = src
                e["license_permissive"] = chosen in PERMISSIVE

    print(f"\nresolved {sum(resolved.values())} of {len(targets)}:")
    for k, v in resolved.most_common():
        flag = "" if k in PERMISSIVE else "   <-- NOT usable for redistribution"
        print(f"  {k:<14} {v}{flag}")
    print(f"  still unknown  {len(still)}")
    if disagree:
        print(f"\n  font/repo licence disagreements ({len(disagree)}), font wins:")
        for fn, f, r in disagree[:10]:
            print(f"    {fn[:52]:<54} font={f} repo={r}")

    if not args.dry_run and sum(resolved.values()):
        with open(args.manifest, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=1)
            f.write("\n")
        after = Counter(e.get("license") or "unknown" for e in manifest)
        print(f"\nwrote {args.manifest}; pool composition now:")
        for k, v in after.most_common():
            print(f"  {k:<14} {v}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
