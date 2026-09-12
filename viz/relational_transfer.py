"""A local treatment propagates; a relational one did not.

Hand the LoRA a reference with the bands erased and all ninety-two other
letters come back banded. Stencil is a LOCAL treatment: every stroke is
altered, and each glyph carries the whole instruction by itself. **Monospace is
relational** -- it is a statement about the set, that all letters share a
width, and two glyphs can only hint at it by agreeing with each other. Nothing
about the stencil result implied the model would generalise "these two match"
into "make all ninety-four match", which is why it was asked separately.

THE STENCIL ROW IS A POSITIVE CONTROL, not decoration. It reproduces its
signature in full (parts up, holes down), so the pipeline was working and the
three arms are comparable. The monospace arm returned the plain atlas.

THE WORD IS "minimal10" FOR TWO REASONS. It contains no `K` and no `g` -- the
two glyphs the model is conditioned to copy, and the two the score excludes --
so every letterform shown is invented. And its ink widths run 14 px to 70 px:
narrow `i` and `l` against wide `m`, exactly what a monospace treatment would
have to close. All three rows keep the same spread.

The boxed note is not a hedge added afterwards. The reference pair is fixed at
`Kg` by the conditioning, and in ABeeZee those two glyphs are already almost
the same width, so equalising them removes very little disagreement. That was
declared in the pre-registration before the run, which is why the finding reads
"did not transfer under a weak signal" and not "relational treatments cannot
propagate".

  python viz/relational_transfer.py
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atlas_constants import CHARSET                              # noqa: E402
from eval_checkpoint import crop_cell                            # noqa: E402
from viz._common import OUT, REPO, label_font                    # noqa: E402

SRC = os.path.join(REPO, "eval_runs", "_relational_refs")
RESULT = os.path.join(REPO, "research", "relational_transfer_probe.json")

WORD = "minimal10"                # no K, no g; narrow i/l against wide m
ARMS = [("plain", "plain", "the baseline"),
        ("stencil", "stencil", "positive control"),
        ("monospace", "monospace", "widths equalised")]

# The two reference glyphs' ink widths in the source face, from
# research/2026-09-11-a-relational-treatment-does-not-transfer-under-a-weak-signal.md.
REF_WIDTHS = "231 and 214 px"

BG = (16, 16, 16)
INK = (245, 245, 245)
DIM = (152, 152, 152)
FAINT = (116, 116, 116)
RULE = (48, 48, 48)
BOX = (60, 60, 60)
ACCENT = (134, 178, 148)          # the only colour: the control's moved numbers

# Geometry. One left margin at PAD; the number columns are right-aligned so
# their decimal points line up down the figure.
WIDTH = 1060
PAD = 36
LABEL_W = 160
REF_W = 146
WORD_H = 126
LETTER_GAP = 11


def on_ground(gray):
    """Lerp a 0..255 greyscale array from the canvas ground to white.

    The atlases and references are ink on pure black. Pasted raw they sit in
    visible rectangles; lerped, the glyphs float on one continuous ground.
    """
    g = np.asarray(gray, dtype=np.float32) / 255.0
    rgb = np.stack([BG[c] + g * (255 - BG[c]) for c in range(3)], axis=-1)
    return Image.fromarray(rgb.round().astype(np.uint8), mode="RGB")


def word_strip(atlas_path, word=WORD, height=WORD_H, gap=LETTER_GAP):
    """The word composed from that atlas's own cells, each trimmed to its ink.

    Trimming columns but keeping the full cell height preserves the baseline
    and puts every glyph's INK WIDTH on the page -- which is the statistic.
    The gap between letters is constant, so only the ink varies.
    """
    with Image.open(atlas_path) as im:
        a = np.asarray(im.convert("L"))
    tiles = []
    for ch in word:
        cell = crop_cell(np.stack([a] * 3, -1), CHARSET.index(ch))[:, :, 0]
        cols = np.flatnonzero((cell > 40).any(axis=0))
        if len(cols):
            cell = cell[:, cols[0]:cols[-1] + 1]
        tiles.append(cell)
    h = tiles[0].shape[0]
    spacer = np.zeros((h, gap), dtype=tiles[0].dtype)
    joined = np.concatenate(
        [t for pair in zip(tiles, [spacer] * len(tiles)) for t in pair][:-1],
        axis=1)
    img = on_ground(joined)
    scale = height / img.height
    return img.resize((max(1, int(img.width * scale)), height), Image.LANCZOS)


def reference_tile(paths, width=REF_W, margin=22):
    """All references cropped to ONE shared ink box, so the tiles compare.

    Cropping each to its own box would rescale them independently and hide the
    very thing the monospace arm changed.
    """
    boxes = []
    for p in paths:
        with Image.open(p) as im:
            a = np.asarray(im.convert("L"))
        ys = np.flatnonzero((a > 40).any(axis=1))
        xs = np.flatnonzero((a > 40).any(axis=0))
        boxes.append((xs[0], ys[0], xs[-1], ys[-1]))
    x0 = max(0, min(b[0] for b in boxes) - margin)
    y0 = max(0, min(b[1] for b in boxes) - margin)
    x1 = max(b[2] for b in boxes) + margin
    y1 = max(b[3] for b in boxes) + margin
    height = int(round(width * (y1 - y0) / (x1 - x0)))
    tiles = []
    for p in paths:
        with Image.open(p) as im:
            crop = np.asarray(im.convert("L"))[y0:y1, x0:x1]
        tiles.append(on_ground(crop).resize((width, height), Image.LANCZOS))
    return tiles, height


def main():
    rows = []
    for arm, title, note in ARMS:
        ref = os.path.join(SRC, f"ref_{arm}.png")
        atlas = os.path.join(SRC, f"atlas_{arm}.png")
        if os.path.isfile(ref) and os.path.isfile(atlas):
            rows.append((arm, title, note, ref, atlas))
    if len(rows) != len(ARMS) or not os.path.isfile(RESULT):
        print(f"need three arms in {SRC} and {RESULT}", file=sys.stderr)
        return 2
    stats = json.load(open(RESULT, encoding="utf-8"))["arms"]

    strips = [word_strip(a) for *_, a in rows]
    tiles, ref_h = reference_tile([r for *_, r, _ in rows])

    # Every number on the page is read from the record, never retyped.
    cv = {a: f"{stats[a]['ink_width_cv']:.3f}" for a, *_ in rows}
    parts = {a: f"{stats[a]['parts']:.2f}" for a, *_ in rows}
    holes = {a: f"{stats[a]['holes']:.2f}" for a, *_ in rows}
    delta = (f"{stats['monospace']['ink_width_cv'] - stats['plain']['ink_width_cv']:+.3f}")

    x_ref = PAD + LABEL_W + 20
    x_word = x_ref + REF_W + 46
    x_right = WIDTH - PAD
    x_holes, x_parts = x_right, x_right - 67
    x_delta = x_parts - 33 - 28
    x_cv = x_delta - 37 - 13

    y_head, y_rule, y_rows = 112, 132, 152
    pitch = WORD_H + 32
    y_note = y_rows + len(rows) * pitch - 32 + 34
    height = y_note + 50 + 30

    canvas = Image.new("RGB", (WIDTH, height), BG)
    draw = ImageDraw.Draw(canvas)

    draw.text((PAD, 24), "A local treatment propagates; a relational one did not",
              fill=INK, font=label_font(27, bold=True))
    draw.text((PAD, 68),
              f"The stencil control reproduced its signature: parts "
              f"{parts['plain']} → {parts['stencil']}.    "
              f"The monospace arm returned the plain atlas: CV "
              f"{cv['plain']} → {cv['monospace']}.",
              fill=DIM, font=label_font(15))

    head = label_font(12)
    draw.text((x_ref, y_head), "reference given", fill=FAINT, font=head)
    draw.text((x_word, y_head), "letters it drew — no K, no g",
              fill=FAINT, font=head)
    for x, text in ((x_cv, "ink-width CV"), (x_parts, "parts"), (x_holes, "holes")):
        draw.text((x, y_head), text, fill=FAINT, font=head, anchor="ra")
    draw.line([(x_ref, y_rule), (x_right, y_rule)], fill=RULE, width=1)
    # The one boundary the finding is about: what the model was handed, and
    # what it drew without being handed it.
    x_split = (x_ref + REF_W + x_word) // 2
    draw.line([(x_split, y_rule), (x_split, y_rows + len(rows) * pitch - 40)],
              fill=RULE, width=1)

    num = label_font(16)
    for i, ((arm, title, note, _ref, _atlas), strip, tile) in enumerate(
            zip(rows, strips, tiles)):
        y = y_rows + i * pitch
        mid = y + WORD_H // 2
        draw.text((PAD, mid - 21), title, fill=INK, font=label_font(18, bold=True))
        draw.text((PAD, mid + 5), note, fill=FAINT, font=label_font(13))
        canvas.paste(tile, (x_ref, y + (WORD_H - ref_h) // 2))
        canvas.paste(strip, (x_word, y))
        moved = ACCENT if arm == "stencil" else INK
        draw.text((x_cv, mid - 9), cv[arm], fill=INK, font=num, anchor="ra")
        draw.text((x_parts, mid - 9), parts[arm], fill=moved, font=num, anchor="ra")
        draw.text((x_holes, mid - 9), holes[arm], fill=moved, font=num, anchor="ra")
        if arm == "monospace":
            draw.text((x_delta, mid - 5), delta, fill=FAINT,
                      font=label_font(12), anchor="ra")

    draw.rectangle([(PAD, y_note), (x_right, y_note + 50)], outline=BOX, width=1)
    draw.text((PAD + 20, y_note + 17),
              "The reference pair is fixed at Kg, whose widths already nearly "
              f"agree ({REF_WIDTHS}), so the relational cue was weak by "
              "construction — declared before the run.",
              fill=DIM, font=label_font(13))

    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, "relational_transfer.png")
    canvas.save(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
