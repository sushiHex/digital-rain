"""Build eval_holdout_rg: identical to eval_holdout except the reference images
are re-rendered with REF_CHARS='Rg' (matching what TRAINING used) instead of
'Kg'. GT atlases are copied byte-for-byte so the only variable is the reference.

See research/2026-07-28-reference-char-mismatch.md.
"""

# repo root on sys.path so `python pipeline/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import json
import shutil
from pathlib import Path

import build_dataset

SRC = Path("eval_holdout")
DST = Path("eval_holdout_rg")
REF_CHARS = "Rg"


def main():
    manifest = json.load(open(SRC / "manifest.json"))
    fonts = manifest["fonts"]
    print(f"source holdout: {len(fonts)} fonts, reference_chars={manifest.get('reference_chars')!r}")

    # Patch the module constants render_reference() reads.
    build_dataset.REF_CHARS = REF_CHARS
    build_dataset.REF_COLS = len(REF_CHARS)

    (DST / "atlases").mkdir(parents=True, exist_ok=True)
    (DST / "references").mkdir(parents=True, exist_ok=True)

    n_ref, n_atlas, missing = 0, 0, []
    for e in fonts:
        name = e["name"]
        # GT atlas: copy byte-for-byte (must NOT change)
        src_atlas = SRC / e["atlas"]
        dst_atlas = DST / e["atlas"]
        if src_atlas.exists():
            shutil.copy2(src_atlas, dst_atlas)
            n_atlas += 1
        else:
            missing.append(f"atlas:{name}")
            continue

        # Reference: RE-RENDER from the font's own TTF with Rg
        ttf = SRC / "fonts" / e["font_file"]
        if not ttf.exists():
            missing.append(f"ttf:{name}")
            continue
        img = build_dataset.render_reference(ttf, size=manifest.get("canvas", 1280))
        img.save(DST / e["reference"])
        n_ref += 1

    out_manifest = dict(manifest)
    out_manifest["reference_chars"] = REF_CHARS
    out_manifest["derived_from"] = str(SRC)
    out_manifest["note"] = ("references re-rendered with Rg to match training "
                            "(build_dataset.REF_CHARS); atlases copied unchanged")
    json.dump(out_manifest, open(DST / "manifest.json", "w"), indent=1)

    print(f"  atlases copied:      {n_atlas}")
    print(f"  references rendered: {n_ref}  (REF_CHARS={REF_CHARS!r})")
    if missing:
        print(f"  MISSING ({len(missing)}): {missing[:6]}")
    print(f"wrote {DST}/manifest.json")


if __name__ == "__main__":
    main()
