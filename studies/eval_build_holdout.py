"""Build a held-out evaluation set for font LoRA quality measurement.

Picks N fonts from Google Fonts that are NOT in a training dataset,
renders ground-truth atlases + references via build_dataset.py's pipeline,
and copies the TTF files into the holdout dir so downstream eval is
self-contained.

Deterministic: fixed seed + sorted candidate list means the same holdout
is produced on every run given the same inputs. Do not modify the seed
once a holdout has been used for a published baseline — you'd be changing
the test set under yourself.

Usage:
  python studies/eval_build_holdout.py \
      --font-dir google-fonts \
      --exclude-dataset dataset_Kg \
      --out eval_holdout \
      --count 50 \
      --reference-chars Kg
"""

# repo root on sys.path so `python studies/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
import random
import shutil
from pathlib import Path

# Reuse the training pipeline so GT renders match what the LoRA was trained on.
import build_dataset
from build_dataset import (
    CANVAS,
    find_fonts,
    render_atlas,
    render_reference,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--font-dir", default="google-fonts")
    parser.add_argument("--exclude-dataset", default="dataset_Kg",
                        help="Dataset dir whose atlases/ stems mark fonts to exclude")
    parser.add_argument("--out", default="eval_holdout")
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    # NOTE: this controls the reference IMAGE only (it patches
    # build_dataset.REF_CHARS below). It is NOT the same knob as
    # eval_checkpoint.py's --reference-chars, which only sets the prompt
    # label. Default is "Rg" to match build_dataset.REF_CHARS, i.e. what the
    # training corpus actually used -- the old "Kg" default silently built
    # holdouts whose references disagreed with training.
    # See research/2026-07-28-reference-char-mismatch.md (measured impact:
    # none, p=0.625 -- this is consistency hygiene, not a quality fix).
    parser.add_argument("--reference-chars", default="Rg")
    parser.add_argument("--canvas", type=int, default=CANVAS)
    args = parser.parse_args()

    # Patch the module-level REF_CHARS constant so render_reference uses
    # the requested reference glyphs (build_dataset.py has this hardcoded).
    build_dataset.REF_CHARS = args.reference_chars
    build_dataset.REF_COLS = len(args.reference_chars)

    # Build exclusion set from the training dataset's atlas stems.
    train_atlas_dir = Path(args.exclude_dataset) / "atlases"
    if not train_atlas_dir.exists():
        print(f"ERROR: training atlas dir not found: {train_atlas_dir}")
        return
    excluded_stems = {p.stem for p in train_atlas_dir.glob("*.png")}
    print(f"Excluding {len(excluded_stems)} training fonts from holdout candidate pool")

    # Scan candidate fonts with the same quality filter used for training.
    # find_fonts already filters caps-only, symbol-only, blank renders, etc.
    print(f"Scanning {args.font_dir} (this runs the training quality filter)...")
    all_valid = find_fonts(args.font_dir, limit=None, one_per_family=True)
    print(f"  {len(all_valid)} fonts passed quality filter")

    # Remove training-set fonts. Both sides use the same stem normalization
    # (spaces → underscores, matching build_dataset.py line 382).
    holdout_pool = [
        fp for fp in all_valid
        if fp.stem.replace(" ", "_") not in excluded_stems
    ]
    print(f"  {len(holdout_pool)} remain after excluding training set")

    if len(holdout_pool) < args.count:
        print(f"WARNING: only {len(holdout_pool)} holdout candidates, wanted {args.count}")
        target = len(holdout_pool)
    else:
        target = args.count

    # Deterministic sample (sort first so random.sample is reproducible
    # regardless of filesystem scan order).
    holdout_pool.sort(key=lambda p: str(p))
    random.seed(args.seed)
    holdout_fonts = random.sample(holdout_pool, target)
    holdout_fonts.sort(key=lambda p: p.stem)

    # Create output structure.
    out_dir = Path(args.out)
    atlas_dir = out_dir / "atlases"
    ref_dir = out_dir / "references"
    font_dir = out_dir / "fonts"
    for d in (atlas_dir, ref_dir, font_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Render GT atlases + references, copy TTFs.
    print(f"\nRendering {target} holdout fonts at {args.canvas}x{args.canvas}...")
    manifest = []
    failed = []
    for i, fp in enumerate(holdout_fonts):
        name = fp.stem.replace(" ", "_")
        try:
            atlas = render_atlas(fp, size=args.canvas)
            ref = render_reference(fp, size=args.canvas)
            atlas.save(str(atlas_dir / f"{name}.png"))
            ref.save(str(ref_dir / f"{name}.png"))
            shutil.copy2(str(fp), str(font_dir / fp.name))
            manifest.append({
                "name": name,
                "font_file": fp.name,
                "atlas": f"atlases/{name}.png",
                "reference": f"references/{name}.png",
            })
            if (i + 1) % 10 == 0 or i == 0:
                print(f"  [{i+1}/{target}] {name}")
        except Exception as e:
            print(f"  SKIP {name}: {e}")
            failed.append({"name": name, "error": str(e)})

    # Manifest records holdout composition for reproducibility.
    with open(out_dir / "manifest.json", "w") as f:
        json.dump({
            "source_font_dir": args.font_dir,
            "excluded_dataset": args.exclude_dataset,
            "count": len(manifest),
            "count_requested": args.count,
            "reference_chars": args.reference_chars,
            "canvas": args.canvas,
            "seed": args.seed,
            "fonts": manifest,
            "failed": failed,
        }, f, indent=2)

    print(f"\nHoldout built: {len(manifest)} fonts at {out_dir}")
    if failed:
        print(f"  {len(failed)} fonts failed to render (see manifest.json 'failed')")


if __name__ == "__main__":
    main()
