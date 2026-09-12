"""Shared pieces for the showcase figure generators.

Both `showcase_words.py` and `showcase_grids.py` render the same set of holdout
fonts from the same eval run, so the font table, path resolution, atlas loading
and font-file lookup live here rather than being duplicated (and drifting)
between them.
"""
import glob
import os

import numpy as np
from PIL import Image, ImageFont

# Repo root, derived from this file's location -- never a machine-specific path.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GEN = os.path.join(REPO, "eval_runs", "glyph_r32_disambig50_mild", "generated")
GT = os.path.join(REPO, "eval_holdout", "atlases")

# Figures are written next to the repo by default; override with FIGURE_OUT.
OUT = os.environ.get("FIGURE_OUT", os.path.join(REPO, "viz", "out"))

# (font stem, display label, char_acc) — ordered best to hardest.
# char_acc is from eval_runs/glyph_r32_disambig50_mild/scores.json.
FONTS = [
    ("Wonky", "Wonky", 0.894),
    ("PlaywriteAUSA", "Playwrite AU SA (cursive)", 0.755),
    ("AveriaSerifLibre-Regular", "Averia Serif Libre", 0.734),
    ("Dangrek-Regular", "Dangrek", 0.713),
    ("ProtestStrike-Regular", "Protest Strike", 0.585),
    ("NovaSquare", "Nova Square", 0.574),
    ("FascinateInline-Regular", "Fascinate Inline", 0.489),
    ("Kavoon-Regular", "Kavoon", 0.309),
    ("BitcountPropDoubleInk", "Bitcount Prop (dot-grid)", 0.319),
    ("RubikDistressed-Regular", "Rubik Distressed", 0.170),
]


def load_atlas(directory, stem):
    """Greyscale atlas for a font stem, or None. glob.escape guards names like
    `Bitcount[CRSV,wght]` whose brackets would otherwise be a character class."""
    hits = glob.glob(os.path.join(directory, glob.escape(stem) + "*.png"))
    return np.array(Image.open(hits[0]).convert("L")) if hits else None


def label_font(size, bold=False):
    """A TrueType label font, falling back to PIL's default if unavailable."""
    for name in (["arialbd.ttf"] if bold else []) + ["arial.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def ensure_out():
    os.makedirs(OUT, exist_ok=True)
    return OUT
