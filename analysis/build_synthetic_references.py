"""Build reference images that did NOT come from one real font.

WHY. Every reference this project has ever evaluated was rendered from the
target font's own TTF, through the pipeline that made the ground truth. The
product concept is different: the user describes a style, a generative model
draws the two reference characters, the user picks one and iterates. There is
then no target font at all -- which is what makes the retrieval baseline stop
being a near-solution, because "hand back the nearest TRAINING font" answers a
question nobody asked.

Before any of that is worth building, one thing has to hold: the generator must
still produce a coherent, identity-correct 94-glyph set when its reference is
not a clean single-font rendering. This tool makes references that break that
assumption in controlled ways, so the question can be answered without an image
model in the loop.

THE ARMS.

  oracle     the shipped reference, rendered from the target font. Control.
  mixed      R from one font, g from a DIFFERENT font. Simulates the exact
             failure mode a text-to-image model has -- two letterforms that do
             not agree on a style. This is why the product concept has a
             human select-and-iterate loop.
  perturbed  the oracle, with ONE glyph slanted and weight-shifted. A subtler
             mismatch than `mixed`: the two glyphs are the same typeface but no
             longer the same style.
  external   whatever PNGs you drop in a directory, resized to the reference
             canvas. This is where real generated references go.

WHAT IS PRESERVED. `build_dataset.render_reference` documents the proportional
relationship between R and g -- R taller, g carrying a descender, one shared
font size and baseline -- as "critical style information for the model". Every
arm here keeps the two-column layout, the shared baseline and the canvas, and
varies only what a generative model would plausibly vary. An arm that also
broke the layout would confound "inconsistent style" with "wrong format".

  python analysis/build_synthetic_references.py --limit 12
  python analysis/build_synthetic_references.py --external-dir my_generated/
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from atlas_constants import CANVAS

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOLDOUT_REFS = os.path.join(REPO, "eval_holdout", "references")
HOLDOUT_FONTS = os.path.join(REPO, "eval_holdout", "fonts")
OUT_ROOT = os.path.join(REPO, "eval_runs", "_synthetic_refs")

# The SHIPPED holdout references render "Kg", while build_dataset.REF_CHARS and
# the checkpoint's recorded conditioning both say "Rg" -- the train/eval
# mismatch in research/2026-07-28-reference-char-mismatch.md, which was measured
# not to matter (p=0.625). The synthetic arms must match the CONTROL, not the
# training convention: if they rendered Rg they would differ from the oracle in
# two ways at once, and style inconsistency could not be separated from glyph
# identity.
REF_CHARS = "Kg"
REF_COLS = 2


def _render_pair(left_font_path, right_font_path, size=CANVAS):
    """Render `Rg` in two columns, one shared size and baseline.

    Mirrors build_dataset.render_reference's geometry. When the two paths
    differ the columns come from different typefaces, which is the point.
    """
    img = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(img)
    cell_w = size // REF_COLS
    max_w = int(cell_w * 0.80)
    max_h = int(size * 0.55)

    # ONE font size for both columns, chosen so every glyph fits its cell in
    # both faces. Sizing the columns independently would destroy the
    # proportional relationship the model reads as style.
    chosen = 8
    for px in range(8, size, 4):
        ok = True
        for ch, path in zip(REF_CHARS, (left_font_path, right_font_path)):
            try:
                f = ImageFont.truetype(str(path), px)
            except OSError:
                return None
            box = f.getbbox(ch)
            if box[2] - box[0] > max_w or box[3] - box[1] > max_h:
                ok = False
                break
        if not ok:
            break
        chosen = px

    baseline = int(size * 0.68)
    for i, (ch, path) in enumerate(zip(REF_CHARS, (left_font_path, right_font_path))):
        f = ImageFont.truetype(str(path), chosen)
        box = f.getbbox(ch)
        x = i * cell_w + (cell_w - (box[2] - box[0])) // 2 - box[0]
        draw.text((x, baseline - box[3]), ch, font=f, fill=255)
    return img


def _perturb_right_column(img, slant=0.18, weight=1.0):
    """Slant and weight-shift ONLY the right column, keeping the left intact."""
    arr = np.asarray(img)
    h, w = arr.shape
    split = w // REF_COLS
    right = Image.fromarray(arr[:, split:])

    # Shear about the baseline so the glyph stays seated on it.
    baseline = int(h * 0.68)
    right = right.transform(
        right.size, Image.AFFINE,
        (1, slant, -slant * baseline, 0, 1, 0),
        resample=Image.BICUBIC, fillcolor=0)

    if weight != 1.0:
        r = np.asarray(right).astype(np.float32)
        r = np.clip((r / 255.0) ** (1.0 / weight) * 255.0, 0, 255)
        right = Image.fromarray(r.astype(np.uint8))

    out = arr.copy()
    out[:, split:] = np.asarray(right)
    return Image.fromarray(out)


def _superfamily(name):
    return name.split("-")[0].split("[")[0].lower().replace("_", "")


def _pick_partner(usable, i):
    """Half-way around the list, then walk on until the family differs."""
    n = len(usable)
    mine = _superfamily(usable[i][0])
    for step in range(n):
        cand = usable[(i + n // 2 + step) % n]
        if _superfamily(cand[0]) != mine:
            return cand
    return usable[(i + 1) % n]          # single-family list; nothing to do


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--limit", type=int, default=12, help="fonts to build for")
    ap.add_argument("--out", default=OUT_ROOT)
    ap.add_argument("--external-dir",
                    help="directory of real generated reference PNGs to include "
                         "as a fourth arm, resized to the reference canvas")
    ap.add_argument("--slant", type=float, default=0.18)
    ap.add_argument("--weight", type=float, default=1.6)
    args = ap.parse_args()

    fonts = sorted(glob.glob(os.path.join(HOLDOUT_FONTS, "*.ttf")))
    names = [os.path.splitext(os.path.basename(p))[0] for p in fonts]
    usable = [(n, p) for n, p in zip(names, fonts)
              if os.path.isfile(os.path.join(HOLDOUT_REFS, n + ".png"))]
    if len(usable) < 2:
        print("need at least two holdout fonts with references", file=_sys.stderr)
        return 2
    usable = usable[:args.limit] if args.limit else usable

    built = {"oracle": [], "mixed": [], "perturbed": [], "external": []}
    partners = {}
    for arm in built:
        os.makedirs(os.path.join(args.out, arm), exist_ok=True)

    for i, (name, path) in enumerate(usable):
        # oracle: copy the shipped reference verbatim, so the control is the
        # exact bytes every published number was produced from.
        src = os.path.join(HOLDOUT_REFS, name + ".png")
        with Image.open(src) as im:
            im.convert("L").save(os.path.join(args.out, "oracle", name + ".png"))
        built["oracle"].append(name)

        # mixed: the partner must be a DIFFERENT superfamily. Pairing with the
        # alphabetical neighbour looked deterministic and was wrong -- the
        # holdout carries five Playwrite faces and three IBMPlex, so neighbours
        # are frequently the same family and the arm would have been
        # accidentally style-CONSISTENT, testing nothing.
        other_name, other_path = _pick_partner(usable, i)
        partners[name] = other_name
        pair = _render_pair(path, other_path)
        if pair is not None:
            pair.save(os.path.join(args.out, "mixed", name + ".png"))
            built["mixed"].append(name)

        # perturbed: same typeface both columns, then slant/weight the right one.
        same = _render_pair(path, path)
        if same is not None:
            _perturb_right_column(same, args.slant, args.weight).save(
                os.path.join(args.out, "perturbed", name + ".png"))
            built["perturbed"].append(name)

    if args.external_dir and os.path.isdir(args.external_dir):
        for p in sorted(glob.glob(os.path.join(args.external_dir, "*.png"))):
            stem = os.path.splitext(os.path.basename(p))[0]
            with Image.open(p) as im:
                im.convert("L").resize((CANVAS, CANVAS), Image.LANCZOS).save(
                    os.path.join(args.out, "external", stem + ".png"))
            built["external"].append(stem)

    meta = {
        "_comment": ("Reference arms for the synthetic-reference probe. `oracle` "
                     "is the shipped reference verbatim; the others break the "
                     "single-font assumption while keeping the two-column "
                     "layout, shared baseline and canvas."),
        "canvas": CANVAS, "ref_chars": REF_CHARS,
        "slant": args.slant, "weight": args.weight,
        "mixed_pairing": ("g comes from the font half-way around the sorted list, "
                          "walking on until the SUPERFAMILY differs -- the holdout "
                          "carries five Playwrite and three IBMPlex faces, so an "
                          "alphabetical neighbour is frequently the same family and "
                          "the arm would be accidentally style-CONSISTENT"),
        "mixed_partners": partners,
        "counts": {k: len(v) for k, v in built.items()},
        "fonts": {k: v for k, v in built.items()},
    }
    with open(os.path.join(args.out, "manifest.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, indent=1)

    for arm, names_ in built.items():
        print(f"  {arm:<10} {len(names_):>3} references")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
