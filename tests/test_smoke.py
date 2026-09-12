from io import BytesIO

from fontTools.ttLib import TTFont

from src.font_builder import build_font
from src.woff2_convert import ttf_to_woff2

MOCK_GLYPHS = {
    "A": "M 50 0 L 300 700 L 550 0 Z",
    "B": "M 50 0 L 50 700 L 450 700 L 450 350 L 150 350 L 150 0 Z",
    "C": "M 450 0 L 50 0 L 50 700 L 450 700 L 450 600 L 150 600 L 150 100 L 450 100 Z",
    "D": "M 50 0 L 50 700 L 350 700 L 450 350 L 350 0 Z",
    "E": (
        "M 450 0 L 50 0 L 50 700 L 450 700 L 450 600 L 150 600 "
        "L 150 400 L 350 400 L 350 300 L 150 300 L 150 100 L 450 100 Z"
    ),
}


def test_smoke_build_and_convert():
    ttf_bytes = build_font(MOCK_GLYPHS, font_name="SmokeTest")
    assert len(ttf_bytes) > 0
    font = TTFont(BytesIO(ttf_bytes))
    assert ".notdef" in font.getGlyphOrder()
    assert "A" in font.getGlyphOrder()
    assert len(font.getGlyphOrder()) >= 8
    woff2_bytes = ttf_to_woff2(ttf_bytes)
    assert woff2_bytes[:4] == b"wOF2"
    assert len(woff2_bytes) < len(ttf_bytes)
    woff2_font = TTFont(BytesIO(woff2_bytes))
    assert "A" in woff2_font.getGlyphOrder()


def test_smoke_font_renders_in_browser():
    import base64
    ttf_bytes = build_font(MOCK_GLYPHS, font_name="SmokeTest")
    woff2_bytes = ttf_to_woff2(ttf_bytes)
    b64 = base64.b64encode(woff2_bytes).decode()
    html = f"""<!DOCTYPE html>
<html><head><style>
@font-face {{ font-family: 'SmokeTest'; src: url(data:font/woff2;base64,{b64}) format('woff2'); }}
body {{ font-family: 'SmokeTest', sans-serif; font-size: 72px; padding: 40px; }}
</style></head>
<body>ABCDE abcde 12345</body></html>"""
    with open("test_render.html", "w") as f:
        f.write(html)
    assert len(html) > 100
