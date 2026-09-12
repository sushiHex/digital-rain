"""Hand the model a stencil and it propagates one — to letters it never saw.

No general image model will INVENT a stencil: two text-to-image generators
across eight seeds, then image-to-image on the same weights across four
strengths, all returned solid faces. This figure is the different question:
give the glyph-conditioned LoRA a reference that already carries the treatment,
and see whether it reaches the ninety-two letters nobody supplied.

THE WORD DELIBERATELY AVOIDS K AND g. Those are the two glyphs the model is
conditioned to copy, so a strip containing them would show the conditioning
rather than the transfer. "Amber" contains neither. (An earlier draft used
"Hamburg", which ends in `g` -- a copied glyph presented as evidence of
transfer.)

The middle row is a POSITIVE CONTROL, not decoration: the generator carried an
inline stripe unaided on 2026-08-23, so it should move if anything does. Both
rows moving in their OWN predicted directions -- inline raising holes while
leaving parts flat, stencil doing the reverse -- is what separates a real
transfer from a model that merely reacts to any altered reference.

  python viz/synthesised_reference.py
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

SRC = os.path.join(REPO, "eval_runs", "_synthesised_refs")
RESULT = os.path.join(REPO, "research", "synthesised_reference_probe.json")
WORD = "Amber"                    # no K, no g
ARMS = [("plain", "plain reference", "the baseline"),
        ("inline", "inline", "POSITIVE CONTROL"),
        ("stencil", "stencil", "the case that matters")]

INK = (250, 250, 250)
DIM = (150, 150, 150)
GOOD = (120, 210, 140)


def word_strip(atlas_path, word=WORD, height=118):
    with Image.open(atlas_path) as im:
        a = np.asarray(im.convert("L"))
    tiles = []
    for ch in word:
        idx = CHARSET.index(ch)
        cell = crop_cell(np.stack([a] * 3, -1), idx)[:, :, 0]
        cols = np.flatnonzero((cell > 40).any(axis=0))
        if len(cols):
            cell = cell[:, max(0, cols[0] - 2):cols[-1] + 3]
        tiles.append(cell)
    h = tiles[0].shape[0]
    gap = np.zeros((h, 8), dtype=tiles[0].dtype)
    joined = np.concatenate(
        [t for pair in zip(tiles, [gap] * len(tiles)) for t in pair][:-1], axis=1)
    img = Image.fromarray(joined, mode="L").convert("RGB")
    scale = height / img.height
    return img.resize((int(img.width * scale), height), Image.LANCZOS)


def main():
    rows = []
    for arm, title, note in ARMS:
        ref = os.path.join(SRC, f"ref_{arm}.png")
        atlas = os.path.join(SRC, f"atlas_{arm}.png")
        if os.path.isfile(ref) and os.path.isfile(atlas):
            rows.append((arm, title, note, ref, atlas))
    if not rows:
        print(f"nothing to draw in {SRC}", file=sys.stderr)
        return 2
    stats = {}
    if os.path.isfile(RESULT):
        stats = json.load(open(RESULT, encoding="utf-8")).get("arms", {})

    ref_px, word_h = 150, 118
    pad, gap, row_gap = 26, 30, 26
    label_w = 210
    strips = [word_strip(a) for *_, a in rows]
    row_h = max(ref_px, word_h) + row_gap
    head = 132
    width = pad * 2 + label_w + gap + ref_px + gap + max(s.width for s in strips) + 190
    height = head + len(rows) * row_h + pad

    canvas = Image.new("RGB", (width, height), (16, 16, 16))
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, 22), "Hand it a stencil and it propagates one.",
              fill=INK, font=label_font(29, bold=True))
    draw.text((pad, 62),
              "No text-to-image model would draw a stencil — eight seeds, two "
              "generators, then image-to-image, all solid.",
              fill=DIM, font=label_font(16))
    draw.text((pad, 86),
              f"Here the treatment is put INTO the reference. “{WORD}” has no "
              "K and no g, so every letter shown is invented.",
              fill=DIM, font=label_font(16))

    x_ref = pad + label_w + gap
    x_word = x_ref + ref_px + gap
    draw.text((x_ref, head - 24), "reference given", fill=DIM,
              font=label_font(14, bold=True))
    draw.text((x_word, head - 24), "letters it was NOT given", fill=DIM,
              font=label_font(14, bold=True))

    for (arm, title, note, ref, _atlas), strip in zip(rows, strips):
        y = head + rows.index((arm, title, note, ref, _atlas)) * row_h
        cy = y + (row_h - row_gap) // 2
        draw.text((pad, cy - 22), title, fill=INK, font=label_font(19, bold=True))
        draw.text((pad, cy + 4), note,
                  fill=GOOD if note == "POSITIVE CONTROL" else DIM,
                  font=label_font(14))
        with Image.open(ref) as im:
            canvas.paste(im.convert("RGB").resize((ref_px, ref_px), Image.LANCZOS),
                         (x_ref, y + (row_h - row_gap - ref_px) // 2))
        canvas.paste(strip, (x_word, y + (row_h - row_gap - strip.height) // 2))
        s = stats.get(arm)
        if s:
            draw.text((x_word + strip.width + 22, cy - 20),
                      f"parts {s['parts']:.2f}", fill=INK, font=label_font(15))
            draw.text((x_word + strip.width + 22, cy + 2),
                      f"holes {s['holes']:.2f}", fill=INK, font=label_font(15))

    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, "synthesised_reference.png")
    canvas.save(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
