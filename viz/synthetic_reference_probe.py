"""Give the model two styles and it faithfully transfers both.

The product concept is that a user describes a style, a generative model draws
the two reference characters, and the user selects and iterates. That removes
the ground truth -- and with it the reason the retrieval baseline was fatal,
since "hand back the nearest TRAINING font" answers a question nobody asked.

This figure answers the one thing that had to hold first: what happens when the
two reference glyphs do NOT agree on a style?

Each block is one holdout typeface. The left column is the REFERENCE the model
was given; the right is "Hamburg" composed from the atlas it produced.

  ORACLE     the shipped reference, one real font. Control.
  MIXED      K and g from different superfamilies.
  PERTURBED  same face, right glyph slanted and weight-shifted.

READ THE MIXED ROWS. The model neither picks one style nor fails. It does one
of two things, and both produce an unusable typeface:

  BLENDS   Dangrek's heavy K meets a light serif g, and the whole word comes
           out lighter than the oracle's.
  SPLITS   AlikeAngular emits a LIGHT H followed by BOLD "amburg".
           FascinateInline keeps its inline striping on the H and loses it on
           every other letter.

Note which letter keeps the reference style in both split cases: `H`, the
letter nearest the supplied `K`. The model applies the K-style to K-like
letterforms and the g-style to the rest, so an inconsistent reference produces
an atlas that is internally inconsistent along the same seam.

THE POINT ABOUT MEASUREMENT. Identity scored the MIXED arm 0.9034, slightly
ABOVE the oracle's 0.8910, and the ink-coherence statistic returned no
difference (p=0.97). Every letter is the right letter, so a letter-identity
metric is satisfied. Both instruments are blind to the defect the eye catches
instantly.

  python viz/synthetic_reference_probe.py
"""
import json
import os
import sys

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from atlas_constants import CHARSET  # noqa: E402
from eval_checkpoint import crop_cell  # noqa: E402
from viz._common import ensure_out, label_font  # noqa: E402

REFS = os.path.join(REPO, "eval_runs", "_synthetic_refs")
GEN = os.path.join(REPO, "eval_runs", "_synthetic_probe")
SCORES = os.path.join(REPO, "research", "synthetic_reference_probe.json")

WORD = "Hamburg"
SCALE = 0.40
REF_PX = 96
SURFACE = (18, 18, 20)

# categorical slots 1-3, validated all-pairs on this surface
ARMS = [("ORACLE", "oracle", (57, 135, 229)),
        ("MIXED", "mixed", (217, 89, 38)),
        ("PERTURBED", "perturbed", (25, 158, 112))]

PAD, LABEL_W, ROW_GAP, BLOCK_GAP = 26, 108, 10, 30


def word_strip(atlas_path, word=WORD):
    a = np.asarray(Image.open(atlas_path).convert("L"))
    tiles = []
    for ch in word:
        cell = crop_cell(np.stack([a] * 3, -1), CHARSET.index(ch))[:, :, 0]
        cols = np.flatnonzero((cell > 40).any(axis=0))
        if len(cols):
            cell = cell[:, max(0, cols[0] - 2):cols[-1] + 3]
        tiles.append(cell)
    h = tiles[0].shape[0]
    gap = np.zeros((h, 6), dtype=tiles[0].dtype)
    joined = np.concatenate(
        [t for pair in zip(tiles, [gap] * len(tiles)) for t in pair][:-1], axis=1)
    im = Image.fromarray(joined, "L").convert("RGB")
    return im.resize((int(im.width * SCALE), int(im.height * SCALE)), Image.LANCZOS)


def ref_thumb(path):
    with Image.open(path) as im:
        return im.convert("RGB").resize((REF_PX, REF_PX), Image.LANCZOS)


def main():
    if not os.path.isfile(SCORES):
        raise SystemExit("run analysis/synthetic_reference_probe.py first")
    data = json.load(open(SCORES, encoding="utf-8"))
    per_font = data["per_font"]

    names = sorted(set.intersection(*(set(per_font[a]) for _, a, _ in ARMS)))
    # BitcountGridDoubleInk and BitcountPropDoubleInk share a byte-identical
    # REFERENCE image with different ground truth. That does not invalidate this
    # probe -- nothing here is scored against GT -- but the pair has been cited
    # as per-font evidence more than once in this repo, and a figure is exactly
    # where that mistake gets made again. Keep them out.
    names = [n for n in names if not n.lower().startswith("bitcount")]
    # Fonts whose MIXED partner differed most in weight show the blend clearly;
    # rank by how far the mixed arm's ink moved from the oracle's.
    def shift(n):
        return abs(per_font["mixed"][n]["ink_mean"]
                   - per_font["oracle"][n]["ink_mean"])
    names = sorted(names, key=shift, reverse=True)[:3]

    blocks = []
    for name in names:
        rows = []
        for label, arm, colour in ARMS:
            g = os.path.join(GEN, arm, name + ".png")
            r = os.path.join(REFS, arm, name + ".png")
            if os.path.isfile(g) and os.path.isfile(r):
                rows.append((label, colour, ref_thumb(r), word_strip(g)))
        if rows:
            blocks.append((name, rows))

    strip_w = max(s.width for _, rows in blocks for _, _, _, s in rows)
    width = max(PAD + LABEL_W + REF_PX + 18 + strip_w + PAD, 760)
    height = PAD + 92
    for _, rows in blocks:
        height += 24 + sum(max(r.height, s.height) + ROW_GAP
                           for _, _, r, s in rows) + BLOCK_GAP

    canvas = Image.new("RGB", (width, height), SURFACE)
    from PIL import ImageDraw
    d = ImageDraw.Draw(canvas)
    title, small, tiny = label_font(21, bold=True), label_font(14), label_font(12)

    d.text((PAD, PAD - 6), "Two styles in, two styles out",
           font=title, fill=(240, 240, 240))
    s = {a: data["per_font"][a] for _, a, _ in ARMS}
    ident = {a: np.mean([v["identity_exact"] for v in s[a].values()]) for a in s}
    d.text((PAD, PAD + 24),
           "left: the reference the model was given.   right: the font it produced.",
           font=small, fill=(165, 165, 175))
    d.text((PAD, PAD + 46),
           f"identity  oracle {ident['oracle']:.4f}   mixed {ident['mixed']:.4f}   "
           f"perturbed {ident['perturbed']:.4f}  -- every letter is the right letter,",
           font=tiny, fill=(200, 170, 120))
    d.text((PAD, PAD + 62),
           "so no letter-identity metric can see what the MIXED rows are doing.",
           font=tiny, fill=(200, 170, 120))

    y = PAD + 90
    for name, rows in blocks:
        d.text((PAD, y), name[:44], font=small, fill=(225, 225, 235))
        y += 22
        for label, colour, ref, strip in rows:
            row_h = max(ref.height, strip.height)
            d.text((PAD, y + row_h // 2 - 7), label, font=tiny, fill=colour)
            canvas.paste(ref, (PAD + LABEL_W, y + (row_h - ref.height) // 2))
            canvas.paste(strip, (PAD + LABEL_W + REF_PX + 18,
                                 y + (row_h - strip.height) // 2))
            y += row_h + ROW_GAP
        y += BLOCK_GAP - ROW_GAP

    ensure_out()
    out = os.path.join(REPO, "viz", "out", "synthetic_reference_probe.png")
    canvas.save(out)
    print(f"wrote {out}  ({canvas.width}x{canvas.height})")
    for name, _ in blocks:
        print(f"  {name[:38]:<40} ink shift {shift(name):.4f}")


if __name__ == "__main__":
    main()
