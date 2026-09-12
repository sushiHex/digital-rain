from src.svg_parser import extract_paths_from_svg, svg_path_to_glyph


def test_triangle_glyph():
    svg_d = "M 100 0 L 500 0 L 300 700 Z"
    glyph = svg_path_to_glyph(svg_d, upm=1000)
    assert glyph is not None
    assert glyph.numberOfContours == 1


def test_empty_path_returns_none():
    assert svg_path_to_glyph("", upm=1000) is None
    assert svg_path_to_glyph("Z", upm=1000) is None


def test_extract_paths_from_combined_svg():
    svg = '<svg><path d="M 0 0 L 100 100 Z"/><path d="M 200 200 L 300 300 Z"/></svg>'
    paths = extract_paths_from_svg(svg)
    assert len(paths) == 2
    assert "M 0 0" in paths[0]
    assert "M 200 200" in paths[1]


def test_extract_paths_empty_svg():
    assert extract_paths_from_svg("") == []
    assert extract_paths_from_svg("<svg></svg>") == []
