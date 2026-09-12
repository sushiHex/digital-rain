"""The hero figure — ten stylized holdout typefaces, ground truth beside generated.

THE FIRST THING ANYONE SEES. It opens `README.md` and Act 1 of
`docs/what-happened.md`, so it has one job: show that a model trained without
these ten font files can draw a word in each of them, and let the reader judge
the result with their own eyes.

WHERE THE PIXELS COME FROM. Ground truth is `eval_holdout/atlases/`; the
generated column is `eval_runs/glyph_r32_disambig50_mild/generated/` (both paths
live in `viz/_common.py`). That run is not a guess. The figure this one replaces
had no recorded provenance, so it was re-derived two ways: its ten `char_acc`
labels match that run's `scores.json` to three decimals and no other run's, and
re-running `viz/showcase_words.py` -- which turned out to be its generator, and
was removed once this script replaced it; it is in the history -- reproduced
the committed PNG with 0 of 3,136,616 pixels different.

NO METRIC APPEARS ON THIS FIGURE, DELIBERATELY. The earlier version printed
`char_acc` under every font name. `CLAUDE.md` opens by explaining at length that
char_acc is neither letter-correctness nor style fidelity, and the README spends
a section discrediting it -- so putting it under the hero asked the reader to
judge the work by a number the next paragraph takes away. Do not re-add a score.

SAY "FILES", NOT "FONTS". These ten were held out as FILES. 32 of the 50 holdout
fonts share a superfamily with a training font, Playwrite and Bitcount among
them, so "the model never saw these typefaces" is an overclaim that `CLAUDE.md`
explicitly warns against. The caveat line under the subtitle is load-bearing.

THE WORD IS BUILT FROM CELLS, NOT SET IN A FONT. Each glyph is cropped to its
ink and butted against the next at a fixed gap; nothing is kerned and no
sidebearing is honoured, so the spacing is this figure's, not the typeface's.
Glyphs are scaled by their CELL height rather than their ink height, which is
what keeps relative sizes within a row comparable -- subject to the ink
threshold below, which crops away anything fainter than it.

DO NOT SUPERSAMPLE THIS FIGURE. An earlier draft rendered at 2x and downsampled
with LANCZOS. It bought nothing -- FreeType already anti-aliases text at the
final size, and GLYPH_H == CELL_H means the glyph bitmaps are already native --
while the downsample rang, putting pure-white halo pixels around ink on a warm
ground and landing the hairlines at roughly 45% of their intended contrast.
Everything here is drawn once, at output scale.

  python viz/stylized_showcase.py
  python viz/stylized_showcase.py --word Amber
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atlas_constants import CELL_H, CHARSET                      # noqa: E402
from eval_checkpoint import crop_cell                            # noqa: E402
from viz._common import FONTS, GEN, GT, OUT, REPO, label_font, load_atlas  # noqa: E402

WORD = "Hamburg"

# Output pixels. GLYPH_H == CELL_H so an atlas cell lands at native scale and is
# never resampled; INK_MIN is the threshold that defines a cell's ink bbox, and
# anything fainter is cropped away before anything else happens.
GLYPH_H = CELL_H
GLYPH_GAP = 11
BLANK_GAPS = 2      # advance for a cell with no ink, e.g. the space
SLACK = 40          # headroom around the shared baseline for ascenders
INK_MIN = 40

MARGIN = 56
NAME_W = 268
GUTTER = 44
ROW_PAD = 22
HEAD_H = 168

PAPER = (252, 251, 249)
INK = (24, 24, 27)
NAME = (46, 48, 56)
TITLE_C = (17, 19, 25)
SUB = (122, 125, 134)
CAVEAT_C = (136, 139, 149)   # a caveat nobody can read is not a caveat
HEAD = (152, 154, 161)
RULE = (231, 228, 223)
HEAD_RULE = (206, 202, 196)

TITLE = "Stylized holdout fonts — ground truth vs generated"
CAVEAT = ("The holdout excluded font files, not families: some of these ten have "
          "superfamily siblings in the training corpus.")
COUNTS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six",
          7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten", 11: "Eleven", 12: "Twelve"}


def subtitle_for(n):
    """Spelled out, and derived from the rows actually drawn -- a missing atlas
    used to drop a row while the caption went on claiming ten."""
    return (f"{COUNTS.get(n, n)} held-out font files. Each word is composed from "
            "that font's own atlas cells, at naive spacing — nothing is kerned.")


def clean_name(label):
    """`Playwrite AU SA (cursive)` -> `Playwrite AU SA`. The parenthetical said
    what the picture already shows; on a figure about letterforms, it is noise."""
    return label.split(" (")[0].strip()


def ink_crop(cell):
    """Crop one atlas cell to its ink and scale it by the CELL height.

    Returns (image, top_fraction) so the caller can restore where the ink sat
    inside the cell -- that is what puts the glyphs back on a shared baseline.
    Scaling by the cell rather than by the ink preserves the relative size of a
    cap, an x-height and a descender within the row. Returns (None, 0.0) for a
    cell with no ink above INK_MIN, which is how the space is handled.
    """
    if cell.ndim == 3:
        cell = cell[..., 0]
    ys, xs = np.where(cell > INK_MIN)
    if len(ys) == 0:
        return None, 0.0
    ink = cell[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    top = ys.min() / cell.shape[0]
    if cell.shape[0] == GLYPH_H:                  # native: do not resample at all
        return Image.fromarray(ink), top
    scale = GLYPH_H / cell.shape[0]
    size = (max(1, int(ink.shape[1] * scale)), max(1, int(ink.shape[0] * scale)))
    return Image.fromarray(ink).resize(size, Image.LANCZOS), top


def render_word(atlas, word):
    """An L-mode mask of `word` -- bright ink on black -- glyphs on one baseline.

    The advance of each glyph is computed ONCE and used for both the mask width
    and the placement. Deriving them separately silently clipped the tail of any
    word containing a space, whose cell has no ink and so no width.
    """
    glyphs = [ink_crop(crop_cell(atlas, CHARSET.index(ch))) for ch in word]
    advances = [g.width if g else GLYPH_GAP * BLANK_GAPS for g, _ in glyphs]
    width = sum(a + GLYPH_GAP for a in advances) + GLYPH_GAP
    mask = Image.new("L", (max(width, 10), GLYPH_H + SLACK), 0)
    x = GLYPH_GAP
    for (glyph, top), advance in zip(glyphs, advances):
        if glyph is not None:
            mask.paste(glyph, (x, int(top * GLYPH_H) + SLACK // 5))
        x += advance + GLYPH_GAP
    return mask


def tracked(draw, xy, text, font, fill, tracking):
    """Letter-spaced capitals. PIL has no tracking and no small caps. Advancing
    per character drops pair kerning, which for spaced capitals is the point."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking


def build(word):
    rows = []
    for stem, label, _char_acc in FONTS:          # the metric is read and dropped
        gt, gen = load_atlas(GT, stem), load_atlas(GEN, stem)
        if gt is None or gen is None:
            print(f"  skip {stem}: gt={gt is not None} gen={gen is not None}")
            continue
        rows.append((clean_name(label), render_word(gt, word), render_word(gen, word)))
    if not rows:
        return None, 0

    subtitle = subtitle_for(len(rows))
    title_font = label_font(34, True)
    sub_font, caveat_font = label_font(17), label_font(14)
    head_font, name_font = label_font(13), label_font(20)   # name: regular, on purpose

    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    col_w = max(max(a.width, b.width) for _, a, b in rows)
    row_h = GLYPH_H + SLACK + 2 * ROW_PAD
    width = MARGIN + NAME_W + col_w + GUTTER + col_w + MARGIN
    # A short --word must not crop the headings off the right edge.
    width = max(width, MARGIN * 2 + int(max(probe.textlength(TITLE, font=title_font),
                                            probe.textlength(subtitle, font=sub_font),
                                            probe.textlength(CAVEAT, font=caveat_font))) + 4)
    height = HEAD_H + len(rows) * row_h + MARGIN

    canvas = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(canvas)

    draw.text((MARGIN, 34), TITLE, font=title_font, fill=TITLE_C)
    draw.text((MARGIN, 79), subtitle, font=sub_font, fill=SUB)
    draw.text((MARGIN, 103), CAVEAT, font=caveat_font, fill=CAVEAT_C)

    col1 = MARGIN + NAME_W
    col2 = col1 + col_w + GUTTER
    tracked(draw, (col1, HEAD_H - 30), "GROUND TRUTH", head_font, HEAD, 2.2)
    tracked(draw, (col2, HEAD_H - 30), "GENERATED", head_font, HEAD, 2.2)

    left, right = MARGIN, width - MARGIN
    draw.line([(left, HEAD_H - 8), (right, HEAD_H - 8)], fill=HEAD_RULE)

    y = HEAD_H
    for i, (name, gt_mask, gen_mask) in enumerate(rows):
        if i:
            draw.line([(left, y), (right, y)], fill=RULE)
        _, top, _, bottom = draw.textbbox((0, 0), name, font=name_font)
        draw.text((MARGIN, y + (row_h - (bottom - top)) // 2 - top),
                  name, font=name_font, fill=NAME)
        for x, mask in ((col1, gt_mask), (col2, gen_mask)):
            # Composite the ink THROUGH the mask rather than pasting the word as
            # an opaque tile: the old figure showed a white box behind every word
            # where the tile met the page.
            canvas.paste(Image.new("RGB", mask.size, INK), (x, y + ROW_PAD), mask)
        y += row_h

    return canvas, len(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--word", default=WORD)
    args = ap.parse_args()

    missing = sorted({ch for ch in args.word if ch not in CHARSET})
    if missing:
        print(f"--word has characters the atlas does not carry: {missing}",
              file=sys.stderr)
        return 2

    canvas, n = build(args.word)
    if canvas is None:
        print(f"no atlases found under {GT} and {GEN}", file=sys.stderr)
        return 2

    # The hero is committed at viz/ rather than viz/out/, because README.md and
    # docs/what-happened.md link it there. FIGURE_OUT redirects it for a test
    # render without dirtying the tracked PNG.
    if "FIGURE_OUT" in os.environ:
        os.makedirs(OUT, exist_ok=True)
        dest = os.path.join(OUT, "stylized_showcase.png")
    else:
        dest = os.path.join(REPO, "viz", "stylized_showcase.png")
    canvas.save(dest)
    print(f"wrote {dest}  ({n} fonts, {canvas.width}x{canvas.height})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
