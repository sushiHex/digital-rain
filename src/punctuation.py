"""Parametric punctuation glyph generator.

Rules (derived from stem metrics):
  period_size  = stem_width * 1.2
  comma_height = period_size * 0.8
  bracket_weight = stem_weight * 0.85

TrueType winding (y-up): outer contours CLOCKWISE, inner counters COUNTER-CLOCKWISE.
Period is the root glyph; all others derive from it.
"""
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._g_l_y_f import Glyph


def _draw_square(pen: TTGlyphPen, x: int, y: int, size: int) -> None:
    """Draw a clockwise square with bottom-left at (x, y) with given size."""
    pen.moveTo((x, y))
    pen.lineTo((x + size, y))
    pen.lineTo((x + size, y + size))
    pen.lineTo((x, y + size))
    pen.closePath()


def generate_period_glyph(stem_width: int, upm: int) -> Glyph:
    """Generate a square sans-serif period glyph.

    Size = stem_width * 1.2, centered at x=250, baseline-sitting.

    Args:
        stem_width: Stem width in font units.
        upm: Units per em (e.g. 1000).

    Returns:
        A Glyph object with one clockwise contour.
    """
    size = round(stem_width * 1.2)
    # Center horizontally at x=250
    x = 250 - size // 2
    y = 0  # sits on baseline

    pen = TTGlyphPen(glyphSet=None)
    _draw_square(pen, x, y, size)
    return pen.glyph()


def generate_comma_glyph(stem_width: int, upm: int) -> Glyph:
    """Generate a comma glyph: period head + descending rectangular tail below baseline.

    Head size = period_size = stem_width * 1.2.
    Tail: width = period_size * 0.4, height = period_size * 0.8 (comma_height),
    centered under the head, descends below baseline.

    Args:
        stem_width: Stem width in font units.
        upm: Units per em.

    Returns:
        A Glyph object with two clockwise contours (head + tail).
    """
    period_size = round(stem_width * 1.2)
    comma_height = round(period_size * 0.8)

    # Head: same square as period, sits on baseline
    head_x = 250 - period_size // 2
    head_y = 0

    # Tail: narrower rectangle descending below baseline
    tail_width = round(period_size * 0.4)
    tail_x = 250 - tail_width // 2
    tail_y = -comma_height  # below baseline

    pen = TTGlyphPen(glyphSet=None)
    # Head (clockwise)
    _draw_square(pen, head_x, head_y, period_size)
    # Tail (clockwise): from tail_y up to baseline (y=0)
    pen.moveTo((tail_x, tail_y))
    pen.lineTo((tail_x + tail_width, tail_y))
    pen.lineTo((tail_x + tail_width, 0))
    pen.lineTo((tail_x, 0))
    pen.closePath()
    return pen.glyph()


def generate_colon_glyph(stem_width: int, upm: int, x_height: int = 500) -> Glyph:
    """Generate a colon glyph: two stacked period squares.

    Lower dot sits at baseline; upper dot sits at x_height - period_size.

    Args:
        stem_width: Stem width in font units.
        upm: Units per em.
        x_height: x-height in font units (default 500).

    Returns:
        A Glyph object with two clockwise contours.
    """
    size = round(stem_width * 1.2)
    x = 250 - size // 2

    pen = TTGlyphPen(glyphSet=None)
    # Lower dot at baseline
    _draw_square(pen, x, 0, size)
    # Upper dot near x-height
    upper_y = x_height - size
    _draw_square(pen, x, upper_y, size)
    return pen.glyph()


def get_punctuation_glyphs(stem_width: int, upm: int) -> dict[str, Glyph]:
    """Return a dict of glyph_name -> Glyph for all parametric punctuation.

    Args:
        stem_width: Stem width in font units.
        upm: Units per em.

    Returns:
        Mapping of PostScript glyph name to Glyph object.
    """
    return {
        "period": generate_period_glyph(stem_width, upm),
        "comma": generate_comma_glyph(stem_width, upm),
        "colon": generate_colon_glyph(stem_width, upm),
    }
