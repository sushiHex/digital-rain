from io import BytesIO

from fontTools.ttLib import TTFont


def ttf_to_woff2(ttf_bytes: bytes) -> bytes:
    font = TTFont(BytesIO(ttf_bytes))
    font.flavor = "woff2"
    buf = BytesIO()
    font.save(buf)
    buf.seek(0)
    return buf.read()
