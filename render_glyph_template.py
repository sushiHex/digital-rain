"""Render the ONE font-independent neutral glyph-template atlas: the Kg charset
in the Kg grid, drawn in a neutral sans (Arial). Reused for every training/infer
sample as the letterform guide for glyph-latent conditioning.

--disambig {mild,strong}: optional geometric disambiguation cues layered on
top of a handful of confusable glyphs (backslash, zero, capital I) so that
ink-count and bbox-extent -- the two summary metrics used to detect
confusability -- no longer tie for pairs the trained glyph-cond checkpoint
over-trusts. Default (disambig=None) renders BYTE-IDENTICAL pixels to the
pre-disambig renderer; the default code path is untouched.

Root-cause note (see docs/superpowers/plans/2026-07-17-hybrid-selection-
template-disambig.md and .superpowers/sdd/task-3-report.md): `\\` and `/` are
NOT actually collapsed by a rendering bug -- Arial draws them as true mirror-
image diagonal strokes (visually distinct, and the raw pixel arrays are NOT
byte-equal). The "byte-identical" description in prior forensics referred to
ink-count and bbox, which ARE exactly equal for any mirror-symmetric pair
(same stroke length/thickness, just reflected) -- a blind spot in the ink/
bbox proxy metric, not a font-fallback or escaping bug in the code. The cues
below give the proxy metric (and the model) a real asymmetry to key on.
"""
import argparse

import numpy as np
from PIL import Image, ImageDraw

from atlas_constants import CHARSET, GRID_COLS, GRID_ROWS, CANVAS, load_truetype_pinned
from cleanup.glyph_guide import _NEUTRAL_FONT

# Confusable pairs the trained glyph-cond checkpoint over-trusts (see
# docs/superpowers/plans/2026-07-17-hybrid-selection-template-disambig.md).
CONFUSABLE_PAIRS = [
    ("\\", "/"),
    ("'", '"'),
    ("O", "0"),
    ("I", "l"),
    ("I", "1"),
    ("|", "l"),
]


def _cell_ink_bbox(img_arr, idx, cw, ch):
    """Ink count + bbox (local to the cell) for CHARSET[idx]'s cell."""
    row, col = idx // GRID_COLS, idx % GRID_COLS
    y0, x0 = row * ch, col * cw
    cell = img_arr[y0:y0 + ch, x0:x0 + cw]
    gray = cell.max(axis=-1) if cell.ndim == 3 else cell
    ink = int((gray > 0).sum())
    ys, xs = np.where(gray > 0)
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())) if len(xs) else None
    return ink, bbox


def assert_confusable_pairs(img, raise_on_fail=False):
    """Print per-pair ink/bbox for every entry in CONFUSABLE_PAIRS and return
    the rows. If raise_on_fail, raise AssertionError when any pair still ties
    on BOTH ink count AND bbox (the pre-fix state for `\\`/`/`)."""
    arr = np.asarray(img.convert("RGB"))
    cw, ch = img.width // GRID_COLS, img.height // GRID_ROWS
    idx_of = {c: i for i, c in enumerate(CHARSET)}
    rows = []
    failures = []
    for a, b in CONFUSABLE_PAIRS:
        ia, ib = idx_of[a], idx_of[b]
        ink_a, bbox_a = _cell_ink_bbox(arr, ia, cw, ch)
        ink_b, bbox_b = _cell_ink_bbox(arr, ib, cw, ch)
        differs = (ink_a != ink_b) or (bbox_a != bbox_b)
        rows.append({"a": a, "b": b, "ink_a": ink_a, "bbox_a": bbox_a,
                      "ink_b": ink_b, "bbox_b": bbox_b, "differs": differs})
        print(f"{a!r:>4} ink={ink_a:>5} bbox={bbox_a}   vs   {b!r:>4} ink={ink_b:>5} "
              f"bbox={bbox_b}   -> {'OK differs' if differs else 'FAIL tie'}")
        if not differs:
            failures.append((a, b))
    if raise_on_fail and failures:
        raise AssertionError(f"confusable pairs still tie on ink AND bbox: {failures}")
    return rows


def _disambig_cue(draw, char, left, top, right, bottom, level):
    """Overlay extra monochrome drawing primitives on a just-rendered glyph
    cell to break the ink/bbox tie for confusable pairs. Only chars that need
    a nudge are touched here -- '/', 'O', 'l', '1', '|', "'", '"' are left
    completely alone (they either already differ, or are the untouched
    reference glyph of a pair).
    """
    strong = level == "strong"
    gw, gh = right - left, bottom - top
    if gw <= 0 or gh <= 0:
        return

    if char == "\\":
        # '\' and '/' are true mirror images in Arial: identical ink count and
        # bbox extent by construction (same stroke, reflected). Extend the
        # stroke, continuing along its own diagonal, past its natural
        # bottom-right end (length asymmetry) and, for strong, add a short
        # horizontal foot at the new tip. '/' gets no cue at all.
        width = max(2, gh // 40)
        ux, uy = gw, gh
        norm = (ux ** 2 + uy ** 2) ** 0.5 or 1.0
        ux, uy = ux / norm, uy / norm
        ext_len = gh * (0.22 if strong else 0.12)
        x0, y0 = right - ux * 2, bottom - uy * 2   # slight overlap with the glyph's tip
        x1, y1 = right + ux * ext_len, bottom + uy * ext_len
        draw.line([(x0, y0), (x1, y1)], fill=(255, 255, 255), width=width)
        if strong:
            foot = gw * 0.45
            draw.line([(x1 - foot, y1), (x1 + foot * 0.3, y1)], fill=(255, 255, 255), width=width + 1)

    elif char == "0":
        # Slashed zero: widens the existing 0-vs-O margin further.
        width = max(2, gh // 22)
        x0, y0 = left + gw * 0.24, top + gh * 0.76
        x1, y1 = left + gw * 0.76, top + gh * 0.24
        draw.line([(x0, y0), (x1, y1)], fill=(255, 255, 255), width=width)
        if strong:
            off = gw * 0.16
            draw.line([(x0 - off, y0), (x1 - off, y1)], fill=(255, 255, 255), width=width)

    elif char == "I":
        # Serifed capital I: top/bottom bars separate it from 'l' / '1' / '|'.
        bar_w = gw * (1.2 if strong else 0.8)
        bar_h = max(2, gh // 28) * (2 if strong else 1)
        cx = (left + right) / 2
        draw.line([(cx - bar_w / 2, top), (cx + bar_w / 2, top)], fill=(255, 255, 255), width=bar_h)
        draw.line([(cx - bar_w / 2, bottom), (cx + bar_w / 2, bottom)], fill=(255, 255, 255), width=bar_h)


def render_glyph_template(size: int = CANVAS, disambig: str | None = None) -> Image.Image:
    if disambig not in (None, "mild", "strong"):
        raise ValueError(f"disambig must be None, 'mild', or 'strong' (got {disambig!r})")
    cw, ch = size // GRID_COLS, size // GRID_ROWS
    img = Image.new("RGB", (size, size), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    for idx, char in enumerate(CHARSET):
        if char == " ":
            continue
        r, c = idx // GRID_COLS, idx % GRID_COLS
        lo, hi = 8, ch
        while lo < hi:                       # largest font size that fits the cell
            mid = (lo + hi + 1) // 2
            f = load_truetype_pinned(_NEUTRAL_FONT, mid)
            b = f.getbbox(char)
            if (b[2] - b[0]) <= cw * 0.8 and (b[3] - b[1]) <= ch * 0.6:
                lo = mid
            else:
                hi = mid - 1
        f = load_truetype_pinned(_NEUTRAL_FONT, lo)
        b = f.getbbox(char)
        gw, gh = b[2] - b[0], b[3] - b[1]
        x = c * cw + (cw - gw) // 2 - b[0]
        y = r * ch + (ch - gh) // 2 - b[1]
        draw.text((x, y), char, fill=(255, 255, 255), font=f)
        if disambig is not None:
            _disambig_cue(draw, char, x + b[0], y + b[1], x + b[2], y + b[3], disambig)
    return img


def _parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--disambig", choices=["mild", "strong"], default=None,
                     help="Render a disambiguated variant (adds confusable-pair "
                          "cues) instead of the default template.")
    return ap.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    img = render_glyph_template(disambig=args.disambig)
    out = f"glyph_template_disambig_{args.disambig}.png" if args.disambig else "glyph_template.png"
    img.save(out)
    print(f"saved {out}")
    assert_confusable_pairs(img, raise_on_fail=bool(args.disambig))
