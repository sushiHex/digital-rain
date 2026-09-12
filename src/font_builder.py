"""Build a complete TrueType font from SVG path data using fontTools FontBuilder.

Call order is mandatory per FontBuilder docstring:
1. FontBuilder(upm)  2. setupGlyphOrder  3. setupCharacterMap  4. setupGlyf
5. setupHorizontalMetrics  6. setupHorizontalHeader  7. setupNameTable
8. setupOS2  9. setupPost  10. save
"""
from io import BytesIO

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._g_l_y_f import Glyph

from src.svg_parser import svg_path_to_glyph

# Fixed advance widths for prototype (skip kerning)
UPPERCASE_WIDTH = 600
LOWERCASE_WIDTH = 500
NUMERAL_WIDTH = 550
SPACE_WIDTH = 250
NOTDEF_WIDTH = 500


def _make_notdef_glyph() -> Glyph:
    """Create a .notdef glyph (rectangle 0,0 to 500,700 with inner cutout).

    TrueType winding (y-up): outer = clockwise, inner = counter-clockwise.
    """
    pen = TTGlyphPen(glyphSet=None)
    # Outer rectangle — clockwise (y-up)
    pen.moveTo((0, 0))
    pen.lineTo((0, 700))
    pen.lineTo((500, 700))
    pen.lineTo((500, 0))
    pen.closePath()
    # Inner rectangle — counter-clockwise (hole)
    pen.moveTo((50, 50))
    pen.lineTo((450, 50))
    pen.lineTo((450, 650))
    pen.lineTo((50, 650))
    pen.closePath()
    return pen.glyph()


def _make_empty_glyph() -> Glyph:
    """Create an empty glyph (for space and .null — no contours)."""
    glyph = Glyph()
    glyph.numberOfContours = 0
    return glyph


def _get_advance_width(char: str) -> int:
    """Determine advance width for a character."""
    if char.isupper():
        return UPPERCASE_WIDTH
    elif char.islower():
        return LOWERCASE_WIDTH
    elif char.isdigit():
        return NUMERAL_WIDTH
    return UPPERCASE_WIDTH  # default for punctuation etc.


def _char_to_glyph_name(char: str) -> str:
    """Convert a character to a standard PostScript glyph name."""
    names = {
        "!": "exclam", "@": "at", "#": "numbersign", "$": "dollar",
        "%": "percent", "&": "ampersand", "*": "asterisk", "(": "parenleft",
        ")": "parenright", "-": "hyphen", "+": "plus", "=": "equal",
        "[": "bracketleft", "]": "bracketright", "{": "braceleft",
        "}": "braceright", "/": "slash", "\\": "backslash", "|": "bar",
        ";": "semicolon", ":": "colon", "'": "quotesingle", '"': "quotedbl",
        ",": "comma", ".": "period", "<": "less", ">": "greater",
        "?": "question", "`": "grave", "~": "asciitilde", "^": "asciicircum",
        "_": "underscore",
    }
    if char in names:
        return names[char]
    return char  # A-Z, a-z, 0-9 use the character itself


def _glyph_name_to_char(glyph_name: str) -> str | None:
    """Reverse lookup: glyph name to character."""
    if len(glyph_name) == 1:
        return glyph_name
    # Reverse the known names
    reverse_map = {
        "exclam": "!", "at": "@", "numbersign": "#", "dollar": "$",
        "percent": "%", "ampersand": "&", "asterisk": "*", "parenleft": "(",
        "parenright": ")", "hyphen": "-", "plus": "+", "equal": "=",
        "bracketleft": "[", "bracketright": "]", "braceleft": "{",
        "braceright": "}", "slash": "/", "backslash": "\\", "bar": "|",
        "semicolon": ";", "colon": ":", "quotesingle": "'", "quotedbl": '"',
        "comma": ",", "period": ".", "less": "<", "greater": ">",
        "question": "?", "grave": "`", "asciitilde": "~", "asciicircum": "^",
        "underscore": "_",
    }
    return reverse_map.get(glyph_name)


def build_font(
    glyphs: dict[str, str],
    font_name: str = "GeneratedFont",
    style_name: str = "Regular",
    upm: int = 1000,
) -> bytes:
    """Build a complete TTF from a dict of character to SVG path d-attribute.

    Args:
        glyphs: Mapping of single character to SVG path d-attribute string.
        font_name: Font family name.
        style_name: Font style name (e.g., "Regular").
        upm: Units per em (default 1000).

    Returns:
        TTF file bytes.
    """
    # Build glyph objects from SVG paths
    glyph_objects = {}
    glyph_objects[".notdef"] = _make_notdef_glyph()
    glyph_objects[".null"] = _make_empty_glyph()
    glyph_objects["space"] = _make_empty_glyph()

    for char, svg_d in glyphs.items():
        glyph_name = _char_to_glyph_name(char)
        glyph_obj = svg_path_to_glyph(svg_d, upm=upm)
        if glyph_obj is not None:
            glyph_objects[glyph_name] = glyph_obj
        else:
            # Fallback: use .notdef for failed glyphs
            glyph_objects[glyph_name] = _make_notdef_glyph()

    # Glyph order: .notdef must be first
    glyph_order = [".notdef", ".null", "space"] + [
        _char_to_glyph_name(c) for c in glyphs
    ]

    # Character map: Unicode codepoint to glyph name
    char_map = {32: "space"}  # space always present
    for char in glyphs:
        char_map[ord(char)] = _char_to_glyph_name(char)

    # FontBuilder — exact call order per fontTools docstring
    fb = FontBuilder(upm, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(char_map)
    fb.setupGlyf(glyph_objects)

    # Horizontal metrics — MUST follow setupGlyf (needs xMin from glyph bounds)
    metrics = {}
    glyf_table = fb.font["glyf"]
    for glyph_name in glyph_order:
        if glyph_name == ".notdef":
            width = NOTDEF_WIDTH
        elif glyph_name == ".null":
            width = 0
        elif glyph_name == "space":
            width = SPACE_WIDTH
        else:
            char = _glyph_name_to_char(glyph_name)
            width = _get_advance_width(char) if char else UPPERCASE_WIDTH
        glyph_entry = glyf_table[glyph_name]
        if hasattr(glyph_entry, "xMin") and glyph_entry.xMin is not None:
            lsb = glyph_entry.xMin
        else:
            lsb = 0
        metrics[glyph_name] = (width, lsb)
    fb.setupHorizontalMetrics(metrics)

    fb.setupHorizontalHeader(ascent=800, descent=-200)

    fb.setupNameTable({
        "familyName": font_name,
        "styleName": style_name,
        "uniqueFontIdentifier": f"{font_name}-{style_name}",
        "fullName": f"{font_name} {style_name}",
        "psName": f"{font_name}-{style_name}".replace(" ", ""),
        "version": "Version 1.0",
    })

    fb.setupOS2(
        sTypoAscender=800,
        sTypoDescender=-200,
        sTypoLineGap=0,
        usWinAscent=1000,
        usWinDescent=200,
        sxHeight=500,
        sCapHeight=700,
        usWeightClass=400,
        fsType=0,  # Installable embedding
    )

    fb.setupPost()

    # Save to bytes via BytesIO
    buf = BytesIO()
    fb.font.save(buf)
    buf.seek(0)
    return buf.read()
