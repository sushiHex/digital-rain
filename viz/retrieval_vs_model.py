"""Show the finding that closed the project: a wrong font scores higher.

For each holdout typeface, three rows of the same word:

  GROUND TRUTH   what the target font actually looks like
  MODEL          what the generator produced from one reference image
  RETRIEVAL      a DIFFERENT, REAL font -- the nearest training font by DINOv2
                 on the reference image, handed back unchanged

Retrieval scores HIGHER than the model on both style metrics
(char_acc 0.7768 vs 0.6917; DINOv2 0.9389 vs 0.8788).

READ THE FIGURE HONESTLY. Row 3 is not obvious nonsense -- nearest-neighbour
retrieval returns a genuinely SIMILAR real typeface, which is exactly why it
scores well. On Dangrek and IBMPlexSansArabic the three rows are hard to tell
apart; on AlikeAngular and AveriaSerifLibre the retrieved face is visibly a
different design.

That is the finding, and it is subtler than "the metric is broken". The metric
cannot distinguish A SIMILAR REAL FONT from AN ATTEMPT AT THE RIGHT ONE. Those
are different tasks, and only one of them is what this project set out to do.

Retrieval is not a proposal. It cannot produce a typeface that does not already
exist, and shipping it would redistribute someone else's font. It is a ruler.

  python viz/retrieval_vs_model.py
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from atlas_constants import CHARSET  # noqa: E402
from eval_checkpoint import crop_cell  # noqa: E402
from viz._common import ensure_out, label_font  # noqa: E402

GT_DIR = os.path.join(REPO, "eval_holdout", "atlases")
MODEL_DIR = os.path.join(REPO, "eval_runs", "glyph_4b_r32_5000_lrfix", "generated")
CORPUS_DIR = os.path.join(REPO, "dataset_v2", "atlases")
RETRIEVAL = os.path.join(REPO, "research", "retrieval_baseline.json")

WORD = "Hamburg"
ROWS = [("GROUND TRUTH", (150, 255, 150)),
        ("MODEL", (255, 255, 255)),
        ("RETRIEVAL", (255, 170, 170))]
CELL_SCALE = 0.55


def word_strip(atlas_path, word=WORD):
    """Compose `word` from an atlas's own cells, trimmed and butted together."""
    with Image.open(atlas_path) as im:
        a = np.asarray(im.convert("L"))
    tiles = []
    for ch in word:
        idx = CHARSET.index(ch)
        cell = crop_cell(np.stack([a] * 3, -1), idx)[:, :, 0]
        cols = np.flatnonzero((cell > 40).any(axis=0))
        if len(cols):                       # trim horizontal whitespace
            cell = cell[:, max(0, cols[0] - 2):cols[-1] + 3]
        tiles.append(cell)
    if not tiles:
        return None
    h = tiles[0].shape[0]
    gap = np.zeros((h, 6), dtype=tiles[0].dtype)
    joined = np.concatenate([t for pair in zip(tiles, [gap] * len(tiles))
                             for t in pair][:-1], axis=1)
    img = Image.fromarray(joined, mode="L").convert("RGB")
    return img.resize((int(img.width * CELL_SCALE), int(img.height * CELL_SCALE)),
                      Image.LANCZOS)


def main():
    data = json.load(open(RETRIEVAL, encoding="utf-8"))
    # Fonts where retrieval returned a visibly different family, and where all
    # three atlases exist. Skip the byte-identical leak cases: they would show
    # three identical rows and prove nothing.
    picks = [r for r in data["per_font"]
             if not r["leaked_twin"]
             and os.path.isfile(os.path.join(MODEL_DIR, r["font"] + ".png"))
             and os.path.isfile(os.path.join(CORPUS_DIR, r["retrieved"] + ".png"))
             and r["font"].split("-")[0][:5].lower() != r["retrieved"].split("-")[0][:5].lower()]
    picks = picks[:4]
    if not picks:
        raise SystemExit("no usable fonts found -- run analysis/retrieval_baseline.py first")

    blocks = []
    for r in picks:
        strips = [word_strip(os.path.join(GT_DIR, r["font"] + ".png")),
                  word_strip(os.path.join(MODEL_DIR, r["font"] + ".png")),
                  word_strip(os.path.join(CORPUS_DIR, r["retrieved"] + ".png"))]
        blocks.append((r, strips))

    pad, label_w, row_gap, block_gap = 28, 150, 8, 40
    strip_w = max(s.width for _, ss in blocks for s in ss if s)
    # MIN_W so the title is never clipped -- the first version sized the canvas
    # from the images alone and cut both title and captions.
    MIN_W = 660
    width = max(MIN_W, pad + label_w + strip_w + pad)
    height = pad
    for _, ss in blocks:
        height += 30 + sum(s.height + row_gap for s in ss if s) + block_gap

    canvas = Image.new("RGB", (width, height + 70), (18, 18, 20))
    d = ImageDraw.Draw(canvas)
    title = label_font(21, bold=True)
    small = label_font(14)
    tiny = label_font(12)

    d.text((pad, pad - 6), "A different real font scores higher than the model",
           font=title, fill=(240, 240, 240))
    d.text((pad, pad + 22),
           "retrieval  char_acc 0.7768 / DINOv2 0.9389        "
           "model  0.6183 / 0.8388",
           font=small, fill=(165, 165, 175))

    d.text((pad, pad + 40),
           "Row 3 is a similar REAL typeface, not nonsense -- that is why it wins.",
           font=tiny, fill=(200, 170, 120))
    d.text((pad, pad + 56),
           "The metric cannot tell it from an attempt at the right one.",
           font=tiny, fill=(200, 170, 120))

    y = pad + 84
    for r, strips in blocks:
        d.text((pad, y), f"{r['font'][:44]}", font=small, fill=(225, 225, 235))
        d.text((pad + 330, y + 1), f"retrieval gave you  {r['retrieved'][:30]}",
               font=tiny, fill=(255, 150, 150))
        y += 26
        for (name, colour), strip in zip(ROWS, strips):
            if strip is None:
                continue
            d.text((pad, y + strip.height // 2 - 8), name, font=tiny, fill=colour)
            canvas.paste(strip, (pad + label_w, y))
            y += strip.height + row_gap
        y += block_gap - row_gap

    ensure_out()
    out = os.path.join(REPO, "viz", "out", "retrieval_vs_model.png")
    canvas.save(out)
    print(f"wrote {out}  ({canvas.width}x{canvas.height})")
    for r, _ in blocks:
        print(f"  {r['font'][:40]:<42} <- {r['retrieved'][:40]}")


if __name__ == "__main__":
    main()
