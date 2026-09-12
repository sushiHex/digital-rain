"""Replace recovered fonts with their canonical OFL copies, and record it.

Seven corpus fonts are confirmed OFL (or public domain) upstream but the local
file lacks a name-table licence field, or -- for Cascadia Code -- is the
Windows-bundled copy carrying Microsoft's terms instead of the OFL release.

For four of them a canonical OFL copy is already in the local Google Fonts tree,
so the swap is a file copy. The rest need fetching from upstream, which this
script reports rather than pretends to do.

It also BACKFILLS the provenance manifest for whatever it places, so the fonts
stop being invisible to `build_dataset.find_fonts`'s new provenance guard.

  python analysis/resource_recovered_fonts.py --dry-run
  python analysis/resource_recovered_fonts.py
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import json
import os
import shutil
from datetime import datetime, timezone

EXCLUSIONS = "research/corpus_exclusions.json"
MANIFEST = "font_pool/source_manifest.json"
GF_OFL = "google-fonts/ofl"
DEST = "font_pool"

# stem -> google-fonts family directory holding the canonical OFL release
LOCAL_OFL = {
    "Fira_Sans": "firasans",
    "knewave": "knewave",
    "prociono": "prociono",
    "sniglet": "sniglet",
}

# Confirmed OFL upstream, but no local canonical copy to swap in.
NEEDS_FETCH = {
    "chunk": "https://github.com/theleagueof/chunk (OFL-1.1)",
    "junction": "https://github.com/theleagueof/junction (OFL-1.1)",
    "CascadiaCode": "https://github.com/microsoft/cascadia-code (OFL-1.1)",
}


def pick_regular(family_dir):
    """The upright Regular static, or the variable font, whichever exists."""
    files = sorted(glob.glob(os.path.join(family_dir, "*.ttf"))
                   + glob.glob(os.path.join(family_dir, "*.otf")))
    if not files:
        return None
    for f in files:
        if "italic" not in os.path.basename(f).lower() and \
                "regular" in os.path.basename(f).lower():
            return f
    upright = [f for f in files if "italic" not in os.path.basename(f).lower()]
    return (upright or files)[0]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dest", default=DEST)
    args = ap.parse_args(argv)

    recovered = {r["stem"] for r in
                 json.load(open(EXCLUSIONS, encoding="utf-8"))["recovered"]}
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    known = {os.path.splitext(e["filename"])[0].lower() for e in manifest}
    now = datetime.now(timezone.utc).isoformat()

    placed, added, missing = [], 0, []
    for stem in sorted(recovered):
        if stem in NEEDS_FETCH:
            missing.append((stem, NEEDS_FETCH[stem]))
            continue
        fam = LOCAL_OFL.get(stem)
        src = pick_regular(os.path.join(GF_OFL, fam)) if fam else None
        if not src:
            missing.append((stem, f"no canonical copy found in {GF_OFL}/{fam}"))
            continue
        dst = os.path.join(args.dest, os.path.basename(src))
        placed.append((stem, src, dst))
        if args.dry_run:
            continue
        os.makedirs(args.dest, exist_ok=True)
        shutil.copy2(src, dst)
        if os.path.splitext(os.path.basename(src))[0].lower() not in known:
            manifest.append({
                "filename": os.path.basename(src),
                "source": "google-fonts",
                "license": "OFL-1.1",
                "origin_path": os.path.abspath(src),
                "fetched_at": now,
                "note": f"re-sourced canonical OFL copy replacing the "
                        f"unlicensed local file for corpus stem {stem!r}",
            })
            added += 1

    for stem, src, dst in placed:
        print(f"  {'would place' if args.dry_run else 'placed'}  {stem:<14} "
              f"<- {src}")
    if missing:
        print("\n  NOT placed -- needs fetching from upstream:")
        for stem, why in missing:
            print(f"    {stem:<14} {why}")

    if not args.dry_run and added:
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=1)
            f.write("\n")
        print(f"\n  manifest: +{added} entries -> {MANIFEST}")
    print(f"\n{len(placed)} placed, {len(missing)} still to fetch")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
