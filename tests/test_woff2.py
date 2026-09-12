from src.font_builder import build_font
from src.woff2_convert import ttf_to_woff2


def test_woff2_conversion():
    glyphs = {"A": "M 50 0 L 300 700 L 550 0 Z"}
    ttf_bytes = build_font(glyphs, font_name="TestFont")
    woff2_bytes = ttf_to_woff2(ttf_bytes)
    assert woff2_bytes is not None
    assert len(woff2_bytes) > 0
    assert len(woff2_bytes) < len(ttf_bytes)
    assert woff2_bytes[:4] == b"wOF2"
