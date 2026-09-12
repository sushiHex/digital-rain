"""What the user actually receives: the same words, set in the finished fonts.

Four rows per typeface, all at the same point size:

  SOURCE      the real .ttf -- the target
  GT ATLAS    ground-truth atlas -> OTF. Model error is exactly zero here, so
              any difference from SOURCE is the PIPELINE's cost.
  MODEL       generated atlas -> OTF. The product.
  RETRIEVAL   nearest TRAINING font's atlas -> OTF. The non-generative floor.

READ THE SPACING, NOT THE SHAPES. The three traced rows are letterfitted
uniformly -- `build_dataset` centres every glyph in its cell, so left and right
sidebearings are equal by construction and no atlas-space metric can see it.
Against the source row the traced text reads loose and evenly-gapped, and `A`,
`T` and `V` are the worst offenders because their real sidebearings are the most
asymmetric.

That defect is charged to the pipeline, not the model, which is exactly why the
GT ATLAS row is on the figure. Without it a reader would blame the generator for
something ground truth suffers identically.

Run `python analysis/score_finished_font.py` first -- this reads the OTFs it
builds and caches.

  python viz/finished_font_specimens.py
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from viz._common import ensure_out, label_font  # noqa: E402

CACHE = os.path.join(REPO, "eval_runs", "_finished_fonts")
SOURCES = os.path.join(REPO, "eval_holdout", "fonts")
SCORES = os.path.join(REPO, "research", "finished_font_scores.json")

WORD = "Hamburgefonstiv"
SIZE = 46
SURFACE = (18, 18, 20)
INK = (245, 245, 245)
MUTED = (137, 135, 129)

# source is the target, not a series, so it wears text ink rather than a hue.
ROWS = [("SOURCE", None, (235, 235, 240)),
        ("GT ATLAS", "gt_traced", (57, 135, 229)),    # categorical slot 1
        ("MODEL", "model", (217, 89, 38)),            # slot 2
        ("RETRIEVAL", "retrieval", (25, 158, 112))]   # slot 3

PAD, LABEL_W, ROW_GAP, BLOCK_GAP = 26, 132, 10, 34


def font_path(arm, name):
    if arm is None:
        for ext in (".ttf", ".otf"):
            p = os.path.join(SOURCES, name + ext)
            if os.path.isfile(p):
                return p
        return None
    p = os.path.join(CACHE, arm, name + ".otf")
    return p if os.path.isfile(p) else None


def strip(path, word=WORD, size=SIZE):
    """Render `word`, cropped to its ink, on the figure's dark ground."""
    try:
        pil = ImageFont.truetype(path, size)
    except OSError:
        return None
    canvas = Image.new("RGB", (size * len(word), size * 3), SURFACE)
    ImageDraw.Draw(canvas).text((20, 20), word, font=pil, fill=INK)
    # NOT canvas.getbbox(): that finds non-ZERO pixels, and SURFACE is
    # (18,18,20) rather than black, so it returns the whole canvas and every
    # strip comes back full height.
    mask = (np.asarray(canvas) != np.array(SURFACE, dtype=np.uint8)).any(axis=2)
    if not mask.any():
        return None
    rows, cols = np.where(mask)
    return canvas.crop((cols.min(), rows.min(), cols.max() + 1, rows.max() + 1))


def main():
    if not os.path.isfile(SCORES):
        raise SystemExit("run analysis/score_finished_font.py --json "
                         "research/finished_font_scores.json first")
    data = json.load(open(SCORES, encoding="utf-8"))

    # Fonts where all four rows exist, worst model advance error first: the
    # figure should show the defect, and the caption states it is not typical.
    usable = []
    for row in data["per_font"]:
        name = row["font"]
        paths = {label: font_path(arm, name) for label, arm, _ in ROWS}
        if all(paths.values()):
            usable.append((row, paths))
    if not usable:
        raise SystemExit("no font has all four arms built")
    # One face per superfamily, then a spread across the error range. Sorting by
    # worst error alone returned three Playwrite faces -- one cursive
    # superfamily, which has 46 siblings in the training corpus and whose
    # connected script the tracer cannot do at all (gt_traced alone is 0.32).
    # Three views of one special case is not a figure.
    usable.sort(key=lambda t: (t[0]["arms"].get("model") or {}).get("advance_mae", 0))
    seen, unique = set(), []
    for item in usable:
        family = item[0]["font"].split("-")[0].split("[")[0][:8].lower()
        if family in seen:
            continue
        seen.add(family)
        unique.append(item)
    if len(unique) < 3:
        unique = usable
    picks = [unique[len(unique) // 10],        # good
             unique[len(unique) // 2],         # typical
             unique[-1]]                       # worst

    blocks = []
    for row, paths in picks:
        strips = [(label, colour, strip(paths[label])) for label, _, colour in ROWS]
        blocks.append((row, [s for s in strips if s[2] is not None]))

    width = max(PAD + LABEL_W + max(s.width for _, ss in blocks for _, _, s in ss)
                + PAD, 720)
    height = PAD + 96
    for _, ss in blocks:
        height += 26 + sum(s.height + ROW_GAP for _, _, s in ss) + BLOCK_GAP

    canvas = Image.new("RGB", (width, height), SURFACE)
    d = ImageDraw.Draw(canvas)
    title, small, tiny = label_font(21, bold=True), label_font(14), label_font(12)

    d.text((PAD, PAD - 6), "The finished font, which nothing had ever scored",
           font=title, fill=INK)
    s = data["summary"]
    d.text((PAD, PAD + 24),
           "mean advance error vs the source font   "
           + "   ".join(f"{a.replace('_', ' ')} {s[a]['advance_mae']:.3f}"
                        for a in ("gt_traced", "model", "retrieval") if a in s),
           font=small, fill=(165, 165, 175))
    d.text((PAD, PAD + 46),
           "GT ATLAS carries ZERO model error, so every gap from SOURCE in that row "
           "is the pipeline's.",
           font=tiny, fill=(200, 170, 120))
    d.text((PAD, PAD + 62),
           "On the cursive it fails the same way MODEL does: that break is not the generator.",
           font=tiny, fill=(200, 170, 120))

    y = PAD + 92
    for row, strips in blocks:
        mae = (row["arms"].get("model") or {}).get("advance_mae")
        d.text((PAD, y), row["font"][:40], font=small, fill=(225, 225, 235))
        if mae is not None:
            d.text((PAD + 340, y + 1), f"model advance error {mae:.3f} em",
                   font=tiny, fill=MUTED)
        y += 24
        for label, colour, img in strips:
            d.text((PAD, y + img.height // 2 - 8), label, font=tiny, fill=colour)
            canvas.paste(img, (PAD + LABEL_W, y))
            y += img.height + ROW_GAP
        y += BLOCK_GAP - ROW_GAP

    ensure_out()
    out = os.path.join(REPO, "viz", "out", "finished_font_specimens.png")
    canvas.save(out)
    print(f"wrote {out}  ({canvas.width}x{canvas.height})")
    for row, _ in picks:
        arms = {a: (row["arms"].get(a) or {}).get("advance_mae") for a in
                ("gt_traced", "model", "retrieval")}
        print(f"  {row['font'][:34]:<36} "
              + "  ".join(f"{a}={v:.3f}" for a, v in arms.items() if v is not None))


if __name__ == "__main__":
    main()
