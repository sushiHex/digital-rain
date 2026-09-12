"""A generated font must carry its licence in its own name table.

The demo hands the user a bare .otf and .woff2. Those files travel without
the repository, so a licence stated only in README.md does not reach anyone
who downloads one. Until 2026-08-08 `build_font` set only familyName and
styleName, so every generated font shipped with name IDs 0/13/14 empty --
while the project's own documentation said generated fonts are OFL
derivatives that must carry OFL terms.
"""
import pytest

pytest.importorskip("fontTools")

from atlas_to_font import (DEFAULT_COPYRIGHT, DEFAULT_LICENSE_DESCRIPTION,
                           DEFAULT_LICENSE_URL, build_font)

COPYRIGHT, LICENSE_DESC, LICENSE_URL = 0, 13, 14


def _tiny_font(**kw):
    """Two drawn cells is enough to exercise the name table.

    A cell is a list of subpaths; a subpath is a list of (command, points)
    pairs, matching what trace_atlas_cells emits.
    """
    square = [[('M', [(10, 10)]),
               ('L', [(90, 10)]),
               ('L', [(90, 140)]),
               ('L', [(10, 140)]),
               ('Z', [])]]
    return build_font([square, square], "AB", 106, 160, **kw)


def _name(font, name_id):
    rec = font["name"].getDebugName(name_id)
    return rec or ""


def test_licence_fields_are_populated_by_default():
    f = _tiny_font()
    assert _name(f, LICENSE_DESC), "name ID 13 (licence description) is empty"
    assert _name(f, LICENSE_URL), "name ID 14 (licence URL) is empty"
    assert _name(f, COPYRIGHT), "name ID 0 (copyright) is empty"


def test_the_default_licence_is_the_OFL():
    f = _tiny_font()
    desc = _name(f, LICENSE_DESC)
    assert "Open Font License" in desc, desc
    assert "1.1" in desc, desc
    assert "openfontlicense.org" in _name(f, LICENSE_URL)


def test_defaults_match_the_exported_constants():
    """The constants are the documented override point; keep them wired."""
    f = _tiny_font()
    assert _name(f, LICENSE_DESC) == DEFAULT_LICENSE_DESCRIPTION
    assert _name(f, LICENSE_URL) == DEFAULT_LICENSE_URL
    assert _name(f, COPYRIGHT) == DEFAULT_COPYRIGHT


def test_a_caller_can_override_the_licence():
    f = _tiny_font(license_description="Bespoke terms.",
                   license_url="https://example.invalid/licence",
                   copyright_notice="Copyright (c) somebody.")
    assert _name(f, LICENSE_DESC) == "Bespoke terms."
    assert _name(f, LICENSE_URL) == "https://example.invalid/licence"
    assert _name(f, COPYRIGHT) == "Copyright (c) somebody."


def test_passing_none_restores_a_bare_name_table():
    """The escape hatch, for anyone who has taken their own legal advice."""
    f = _tiny_font(license_description=None, license_url=None,
                   copyright_notice=None)
    assert not _name(f, LICENSE_DESC)
    assert not _name(f, LICENSE_URL)


def test_family_and_style_still_work():
    f = _tiny_font(font_name="Demo", style_name="Italic")
    assert _name(f, 1) == "Demo"
    assert _name(f, 2) == "Italic"


def test_the_licence_survives_a_woff2_roundtrip(tmp_path):
    """The demo also serves WOFF2; the name table must survive the flavour."""
    pytest.importorskip("brotli")
    from fontTools.ttLib import TTFont

    f = _tiny_font()
    f.flavor = "woff2"
    p = tmp_path / "demo.woff2"
    f.save(str(p))
    assert "Open Font License" in TTFont(str(p))["name"].getDebugName(LICENSE_DESC)
