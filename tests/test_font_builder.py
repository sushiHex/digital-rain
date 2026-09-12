from io import BytesIO

from fontTools.ttLib import TTFont

from src.font_builder import build_font


def test_build_minimal_font():
    """Build a font with 3 characters and verify it's valid."""
    glyphs = {
        "A": "M 50 0 L 300 700 L 550 0 Z",
        "B": "M 50 0 L 50 700 L 400 700 L 400 350 L 50 350 Z",
        "C": "M 450 0 L 50 0 L 50 700 L 450 700 Z",
    }
    ttf_bytes = build_font(glyphs, font_name="TestFont")
    assert ttf_bytes is not None
    assert len(ttf_bytes) > 0

    # Verify it's a valid TTF
    font = TTFont(BytesIO(ttf_bytes))
    glyph_order = font.getGlyphOrder()
    assert ".notdef" in glyph_order
    assert "space" in glyph_order
    assert "A" in glyph_order
    assert "B" in glyph_order
    assert "C" in glyph_order


def test_build_font_has_required_tables():
    """Font must have all required OpenType tables."""
    glyphs = {"A": "M 50 0 L 300 700 L 550 0 Z"}
    ttf_bytes = build_font(glyphs, font_name="TestFont")
    font = TTFont(BytesIO(ttf_bytes))
    required = ["head", "hhea", "maxp", "OS/2", "name", "cmap", "glyf", "post"]
    for table in required:
        assert table in font, f"Missing required table: {table}"
