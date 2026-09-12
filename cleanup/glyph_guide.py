import platform
import numpy as np
from PIL import Image, ImageDraw
from atlas_constants import CELL_W, CELL_H, load_truetype_pinned

_NEUTRAL_FONT = {
    "Windows": "C:/Windows/Fonts/arial.ttf",
    "Darwin": "/Library/Fonts/Arial.ttf",
    "Linux": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
}.get(platform.system(), "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

def render_neutral_glyph(char: str, size=(CELL_W, CELL_H)) -> np.ndarray:
    """White `char` on black, centered, in a neutral sans -- a structural guide
    for reference-guided repair (correct letterform, no target style)."""
    w, h = size
    img = Image.new("RGB", (w, h), (0, 0, 0))
    if char == " ":
        return np.array(img)
    draw = ImageDraw.Draw(img)
    lo, hi = 8, h
    while lo < hi:                       # largest font size that fits the cell
        mid = (lo + hi + 1) // 2
        font = load_truetype_pinned(_NEUTRAL_FONT, mid)
        box = font.getbbox(char)
        if (box[2] - box[0]) <= w * 0.8 and (box[3] - box[1]) <= h * 0.7:
            lo = mid
        else:
            hi = mid - 1
    font = load_truetype_pinned(_NEUTRAL_FONT, lo)
    box = font.getbbox(char)
    cw, ch = box[2] - box[0], box[3] - box[1]
    draw.text(((w - cw) // 2 - box[0], (h - ch) // 2 - box[1]), char, fill=(255, 255, 255), font=font)
    return np.array(img)
