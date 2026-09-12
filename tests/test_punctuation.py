from src.punctuation import generate_comma_glyph, generate_period_glyph


def test_period_glyph_not_empty():
    glyph = generate_period_glyph(stem_width=80, upm=1000)
    assert glyph is not None
    assert glyph.numberOfContours >= 1


def test_comma_glyph_not_empty():
    glyph = generate_comma_glyph(stem_width=80, upm=1000)
    assert glyph is not None
    assert glyph.numberOfContours >= 1
