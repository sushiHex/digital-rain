"""Resolve the font pool's `license: unknown` entries from embedded licences.

1,596 of the 6,153 pool entries carry no licence. Most came through the github
adapter, whose detector searched only the font's own directory and its parent
and so missed repositories that keep LICENSE at the root while fonts live in
`fonts/ttf/`. That detector is fixed (2026-08-08), but re-running it is not
possible for entries already in the pool: `fetch_fonts` COPIES fonts out of a
temporary clone, so the repository context is gone.

What survives is the font's own name ID 13, which is authoritative where
present. This resolves what it can and leaves the rest explicitly unknown.

Writes back to font_pool/source_manifest.json, recording `license_source` so a
licence read from the binary is never confused with one recorded at fetch time.

  python analysis/resolve_pool_unknowns.py --dry-run
  python analysis/resolve_pool_unknowns.py
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
import os
from collections import Counter

MANIFEST = "font_pool/source_manifest.json"
POOL_DIR = "font_pool"

# Leading-clause phrases, matched against name ID 13. Substring matching on
# short tokens is how an earlier pass scored Arial as open ("...as permitted by
# the license terms..." contains "mit licen"), so these are full phrases.
LIBRE_PHRASES = {
    "OFL-1.1": ("licensed under the sil open font license",
                "licensed under the open font license",
                "this font software is licensed under the sil open font license"),
    "Apache-2.0": ("licensed under the apache license",),
    "UFL": ("ubuntu font licence", "ubuntu font license"),
    "MIT": ("permission is hereby granted, free of charge",),
}
RESTRICTED_PREFIXES = ("microsoft supplied font",)


def classify(desc):
    low = (desc or "").strip().lower()
    if not low:
        return None
    if low.startswith(RESTRICTED_PREFIXES):
        return "PROPRIETARY"
    for spdx, phrases in LIBRE_PHRASES.items():
        if any(p in low for p in phrases):
            return spdx
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--manifest", default=MANIFEST)
    args = ap.parse_args(argv)

    from fontTools.ttLib import TTFont

    manifest = json.load(open(args.manifest, encoding="utf-8"))
    targets = [e for e in manifest if e.get("license") in (None, "unknown")]
    print(f"pool {len(manifest)}; unknown licence: {len(targets)}")

    resolved, missing, unreadable = Counter(), 0, 0
    for e in targets:
        path = os.path.join(POOL_DIR, e["filename"])
        if not os.path.isfile(path):
            missing += 1
            continue
        try:
            desc = TTFont(path, lazy=True, fontNumber=0)["name"].getDebugName(13)
        except Exception:
            unreadable += 1
            continue
        lic = classify(desc)
        if lic:
            resolved[lic] += 1
            if not args.dry_run:
                e["license"] = lic
                e["license_source"] = "font name ID 13 (embedded)"

    print(f"\nresolved {sum(resolved.values())} of {len(targets)}:")
    for k, v in resolved.most_common():
        print(f"  {k:<14} {v}")
    print(f"  still unknown  {len(targets) - sum(resolved.values())}")
    if missing:
        print(f"  (file absent from the pool: {missing})")
    if unreadable:
        print(f"  (unparsable: {unreadable})")

    if not args.dry_run and sum(resolved.values()):
        with open(args.manifest, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=1)
            f.write("\n")
        print(f"\nwrote {args.manifest}")
        after = Counter(e.get("license") or "unknown" for e in manifest)
        print("pool licence composition now:")
        for k, v in after.most_common():
            print(f"  {k:<14} {v}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
