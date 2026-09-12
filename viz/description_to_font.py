"""Words in, typeface out — the whole product on one page.

THE BEFORE AND AFTER THIS PROJECT IS ACTUALLY ABOUT. A user types a
description; a base model draws two reference glyphs; the glyph-conditioned
LoRA produces the other ninety-two. Roughly 90 seconds per font, on two
Apache-2.0 models. Each row here is one style description, the `Kg` it produced,
and a word set in the finished typeface.

THE WORD IS COMPOSED FROM CELLS THE MODEL INVENTED. `K` and `g` are the only
glyphs it was given, and neither appears in "Hamburg". So every letterform on
the right-hand side is one nobody chose and nobody supplied.

WHAT THIS FIGURE REPLACES. `viz/out/candidate_refs_klein_base.png` and
`viz/out/loop_closes_words.png` are the two halves of this, they are cited in
the README, and NEITHER HAS A GENERATOR -- a gap `viz/README.md` records. This
draws both halves together, from the committed artifacts, so the claim rebuilds
from a clean clone.

READ THE CAVEAT WITH THE TABLE. Two of the twelve descriptions were recorded as
MISSED on 2026-08-23, before any instrument existed to check them: "a stencil
sans with deliberate breaks" came back solid, and "a wide low-contrast
monospace" came back an ordinary heavy sans. Eight seeds across two independent
generators later produced no break either, so the stencil row is a property of
the task rather than of this run. The misses are marked rather than omitted.

  python viz/description_to_font.py
  python viz/description_to_font.py --styles 02 05 10 11
"""
import argparse
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atlas_constants import CHARSET                              # noqa: E402
from eval_checkpoint import crop_cell                            # noqa: E402
from viz._common import OUT, REPO, label_font                    # noqa: E402

REFS = os.path.join(REPO, "eval_runs", "_candidate_refs", "flux2-klein-base")
ATLASES = os.path.join(REPO, "eval_runs", "_synthetic_probe", "external")
SPEC = os.path.join(REPO, "research", "candidate_references.json")

WORD = "Hamburg"
DEFAULT_STYLES = ["00", "01", "02", "05", "08", "09", "10", "11"]

# Recorded by eye on 2026-08-23, BEFORE any adherence instrument existed.
# research/2026-08-23-the-loop-closes.md
RECORDED = {
    "09": "MISS — came back solid",
    "06": "MISS — an ordinary heavy sans",
    "07": "reinterpreted as an outline",
}

INK = (250, 250, 250)
DIM = (155, 155, 155)
BAD = (232, 110, 100)
BG = (16, 16, 16)


def styles():
    import json
    if os.path.isfile(SPEC):
        return json.load(open(SPEC, encoding="utf-8"))["styles"]
    return []


def word_strip(atlas_path, word=WORD, height=104):
    """Compose `word` from an atlas's own cells, trimmed and butted together."""
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
    gap = np.zeros((h, 7), dtype=tiles[0].dtype)
    joined = np.concatenate(
        [t for pair in zip(tiles, [gap] * len(tiles)) for t in pair][:-1], axis=1)
    img = Image.fromarray(joined, mode="L").convert("RGB")
    scale = height / img.height
    return img.resize((int(img.width * scale), height), Image.LANCZOS)


def find(directory, prefix):
    hits = sorted(glob.glob(os.path.join(directory, f"{prefix}-*.png")))
    return hits[0] if hits else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--styles", nargs="*", default=DEFAULT_STYLES)
    ap.add_argument("--word", default=WORD)
    args = ap.parse_args()

    all_styles = styles()
    rows = []
    for prefix in args.styles:
        ref = find(REFS, prefix)
        atlas = find(ATLASES, prefix)
        if not ref or not atlas:
            continue
        idx = int(prefix)
        caption = all_styles[idx] if idx < len(all_styles) else prefix
        rows.append((prefix, caption, ref, atlas))
    if not rows:
        print(f"no matching pairs in {REFS} and {ATLASES}", file=sys.stderr)
        return 2

    ref_px, word_h = 132, 104
    pad, gap, row_gap = 26, 26, 20
    text_w = 430
    row_h = max(ref_px, word_h) + row_gap
    head_h = 128
    strips = [word_strip(a, args.word, word_h) for *_, a in rows]
    width = pad * 2 + text_w + gap + ref_px + gap + max(s.width for s in strips)
    height = head_h + len(rows) * row_h + pad

    canvas = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, 24), "You type words. You get a typeface.",
              fill=INK, font=label_font(30, bold=True))
    draw.text((pad, 66),
              "The model is given K and g only. Neither letter appears in "
              f"“{args.word}” — every glyph on the right is one it invented.",
              fill=DIM, font=label_font(17))
    draw.text((pad + text_w + gap, head_h - 26), "reference",
              fill=DIM, font=label_font(15, bold=True))
    draw.text((pad + text_w + gap + ref_px + gap, head_h - 26),
              "the font it produced", fill=DIM, font=label_font(15, bold=True))

    for i, ((prefix, caption, ref, _atlas), strip) in enumerate(zip(rows, strips)):
        y = head_h + i * row_h
        note = RECORDED.get(prefix)
        colour = BAD if (note and note.startswith("MISS")) else INK

        # Wrap first, then quote the WHOLE caption -- opening mark on the first
        # line and closing mark on the last. Quoting each line independently
        # put the closing quote at the end of line one.
        font = label_font(17)
        line, lines = "", []
        for w in caption.split():
            trial = (line + " " + w).strip()
            if draw.textlength(f"“{trial}”", font=font) > text_w - 12:
                lines.append(line)
                line = w
            else:
                line = trial
        lines.append(line)
        lines[0] = "“" + lines[0]
        lines[-1] = lines[-1] + "”"
        ty = y + (row_h - row_gap - len(lines) * 22 - (18 if note else 0)) // 2
        for j, line in enumerate(lines):
            draw.text((pad, ty + j * 22), line, fill=colour, font=font)
        if note:
            draw.text((pad, ty + len(lines) * 22 + 2), note,
                      fill=BAD if note.startswith("MISS") else DIM,
                      font=label_font(14))

        with Image.open(ref) as im:
            canvas.paste(im.convert("RGB").resize((ref_px, ref_px),
                                                  Image.LANCZOS),
                         (pad + text_w + gap, y + (row_h - row_gap - ref_px) // 2))
        canvas.paste(strip, (pad + text_w + gap + ref_px + gap,
                             y + (row_h - row_gap - strip.height) // 2))

    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, "description_to_font.png")
    canvas.save(dest)
    print(f"wrote {dest}  ({len(rows)} rows, {canvas.width}x{canvas.height})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
