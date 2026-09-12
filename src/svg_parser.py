from xml.etree import ElementTree as ET

from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path


def svg_path_to_glyph(svg_d: str, upm: int = 1000):
    if not svg_d or not svg_d.strip() or svg_d.strip() == "Z":
        return None
    try:
        pen = TTGlyphPen(glyphSet=None)
        transform_pen = TransformPen(pen, (1, 0, 0, -1, 0, upm))
        parse_path(svg_d, transform_pen)
        glyph = pen.glyph()
        if glyph.numberOfContours == 0:
            return None
        return glyph
    except Exception:
        return None


def extract_paths_from_svg(svg_content: str) -> list[str]:
    paths = []
    try:
        root = ET.fromstring(svg_content)
        ns = {"svg": "http://www.w3.org/2000/svg"}
        for path_el in root.findall(".//svg:path", ns):
            d = path_el.get("d", "")
            if d.strip():
                paths.append(d.strip())
        if not paths:
            for path_el in root.findall(".//path"):
                d = path_el.get("d", "")
                if d.strip():
                    paths.append(d.strip())
    except ET.ParseError:
        pass
    return paths
