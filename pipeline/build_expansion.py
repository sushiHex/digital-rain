"""Build dataset_v3 = dataset_v2 + the expansion set, without re-rendering.

research/expansion_set.json (from analysis/select_expansion_set.py) lists new
OFL fonts and variable-font instances to add. This renders their atlas and
reference PNGs and links everything else through from dataset_v2.

Existing files are HARDLINKED, not copied: the latent cache alone is 1.7 GB,
and re-rendering the 925 existing atlases would risk changing bytes that every
prior run's provenance depends on. dataset_v3 is a separate directory rather
than a mutation of dataset_v2 so earlier runs stay reproducible
(analysis/compare_experiments.py checks dataset provenance).

After this, cache the new latents -- cache_latents.py skips entries that
already exist, so only the new fonts are encoded:

  python pipeline/build_expansion.py
  python cache_latents.py --dataset-dir dataset_v3 --ref-resolution 512
"""

# repo root on sys.path so `python pipeline/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
import os
import shutil
from pathlib import Path

import build_dataset
from atlas_constants import CANVAS


def link_or_copy(src, dst):
    if dst.exists():
        return "skip"
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)
        return "link"
    except OSError:
        shutil.copy2(src, dst)
        return "copy"


def mirror(src_dir, dst_dir, pattern="*"):
    n = {"link": 0, "copy": 0, "skip": 0}
    src_dir, dst_dir = Path(src_dir), Path(dst_dir)
    if not src_dir.exists():
        return n
    for p in src_dir.glob(pattern):
        if p.is_file():
            n[link_or_copy(p, dst_dir / p.name)] += 1
    return n


def loader_for(path, coords):
    """One loader for BOTH halves of an entry's (atlas, reference) pair.

    Instances pin their axis coordinates. Everything else uses
    corpus_default_loader -- NOT each renderer's own default, which is the trap:
    render_atlas defaults to load_truetype_pinned ("Regular") while
    render_reference defaults to a plain ImageFont.truetype. For a VARIABLE font
    those disagree, so letting each pick its own gave the atlas one instance and
    the reference another. 101 of the 168 static expansion fonts are variable,
    so that mismatched most of the additions.

    corpus_default_loader is also how dataset_v2's 925 atlases were actually
    rendered, so added fonts now match the corpus convention rather than
    introducing a second one.
    """
    from analysis.select_expansion_set import (axis_order, corpus_default_loader,
                                               pinned_loader)
    if not coords:
        return corpus_default_loader
    return pinned_loader(coords, axis_order(path))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expansion", default="research/expansion_set.json")
    ap.add_argument("--src", default="dataset_v2")
    ap.add_argument("--dst", default="dataset_v3")
    ap.add_argument("--canvas", type=int, default=CANVAS)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    spec = json.load(open(args.expansion, encoding="utf-8"))
    entries = spec["entries"][:args.limit] if args.limit else spec["entries"]
    src, dst = Path(args.src), Path(args.dst)

    print(f"mirroring {src} -> {dst}")
    for sub, pat in [("atlases", "*.png"), ("references", "*.png"),
                     ("cache/atlases", "*.pt"), ("cache/references", "*.pt")]:
        n = mirror(src / sub, dst / sub, pat)
        print(f"  {sub:20} link={n['link']} copy={n['copy']} skip={n['skip']}")
    # templates and the rendered template PNGs travel unchanged (same VAE,
    # same geometry -- CLAUDE.md: in_channels=128 on both bases)
    for pat in ("template*.pt", "glyph_template*.png"):
        n = mirror(src / "cache", dst / "cache", pat)
        print(f"  cache/{pat:15} link={n['link']} copy={n['copy']} skip={n['skip']}")

    made, failed, existing = 0, [], 0
    for i, e in enumerate(entries):
        stem, path, coords = e["stem"], e["path"], e.get("instance")
        atlas_out = dst / "atlases" / f"{stem}.png"
        ref_out = dst / "references" / f"{stem}.png"
        if atlas_out.exists() and ref_out.exists():
            existing += 1
            continue
        loader = loader_for(path, coords)
        try:
            # The SAME loader for both halves of the pair. Pinning only the
            # atlas leaves the reference at the default instance.
            build_dataset.render_atlas(path, args.canvas, loader=loader).save(atlas_out)
            build_dataset.render_reference(path, args.canvas, loader=loader).save(ref_out)
            made += 1
        except Exception as ex:
            failed.append((stem, f"{type(ex).__name__}: {ex}"))
            for p in (atlas_out, ref_out):      # never leave a half-written pair
                if p.exists():
                    p.unlink()
        if (i + 1) % 25 == 0:
            print(f"  rendered {i + 1}/{len(entries)} (ok={made} failed={len(failed)})",
                  flush=True)

    n_atlas = len(list((dst / "atlases").glob("*.png")))
    n_ref = len(list((dst / "references").glob("*.png")))
    print(f"\nrendered {made} new, {existing} already present, {len(failed)} failed")
    for stem, err in failed[:10]:
        print(f"  FAIL {stem[:50]}: {err}")
    print(f"{dst}: {n_atlas} atlases, {n_ref} references")
    if n_atlas != n_ref:
        raise SystemExit(f"MISMATCH: {n_atlas} atlases vs {n_ref} references")
    print(f"\nnext: python cache_latents.py --dataset-dir {dst} --ref-resolution 512")


if __name__ == "__main__":
    main()
