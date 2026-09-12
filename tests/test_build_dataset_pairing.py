"""An (atlas, reference) pair must be rendered through ONE loader.

This is the test whose absence let a real defect ship. `render_atlas` defaults
to `load_truetype_pinned` (the "Regular" named instance) while
`render_reference` opens the face raw at its axis defaults. For a VARIABLE font
those differ, so calling both bare gives the atlas one instance and the
reference another -- and the reference is the style-conditioning input the model
is trained to copy, so the pair teaches "this reference -> a different style".

That is exactly what happened: ~110 of 177 additions to dataset_v3 were built
that way (every instance, plus 101 of 168 variable statics), and nothing failed.

Existing coverage rendered atlases only and never compared a pair.
"""
import numpy as np
import pytest

pytest.importorskip("PIL")


def _variable_font():
    """Any variable font, or skip."""
    import glob

    from fontTools.ttLib import TTFont

    for pat in ("google-fonts/ofl/doto/*.ttf", "google-fonts/ofl/workbench/*.ttf",
                "google-fonts/ofl/**/*.ttf"):
        for p in glob.glob(pat, recursive=True):
            try:
                if TTFont(p, lazy=True).get("fvar"):
                    return p
            except Exception:
                continue
    pytest.skip("no variable font available in this checkout")


def _divergent_variable_font():
    """A variable font whose 'Regular' instance is NOT its axis defaults.

    Not every variable font diverges -- Workbench's "Regular" IS its defaults,
    so both loaders agree there and it cannot demonstrate the trap. Doto is the
    known divergent case (axis default wght 900, "Regular" wght 400). Search
    rather than hardcode, so the test keeps working if the corpus changes.
    """
    import glob

    import numpy as np
    from fontTools.ttLib import TTFont

    import build_dataset

    candidates = (glob.glob("google-fonts/ofl/doto/*.ttf")
                  + glob.glob("google-fonts/ofl/*/*.ttf")[:40])
    for p in candidates:
        try:
            if not TTFont(p, lazy=True).get("fvar"):
                continue
            a = np.asarray(build_dataset.render_atlas(p, 320).convert("L"), dtype=int)
            b = np.asarray(build_dataset.render_atlas(
                p, 320, loader=build_dataset._raw_truetype_loader).convert("L"),
                dtype=int)
        except Exception:
            continue
        if not np.array_equal(a, b):
            return p
    pytest.skip("no variable font whose named Regular differs from axis defaults")


def test_the_two_renderers_have_DIFFERENT_defaults():
    """Pin the trap itself, so the asymmetry cannot be forgotten again."""
    import build_dataset
    from atlas_constants import load_truetype_pinned

    path = _divergent_variable_font()
    pinned = np.asarray(build_dataset.render_atlas(path, 1280).convert("L"), dtype=int)
    raw = np.asarray(
        build_dataset.render_atlas(
            path, 1280, loader=build_dataset._raw_truetype_loader).convert("L"),
        dtype=int)
    assert load_truetype_pinned is not build_dataset._raw_truetype_loader
    assert not np.array_equal(pinned, raw), (
        f"{path} was selected because the loaders diverge on it; they no longer do")
    assert np.abs(pinned - raw).mean() > 0.1


def test_build_dataset_main_passes_one_loader_to_both_halves():
    """main() must not call the two renderers with their bare defaults."""
    import inspect

    import build_dataset
    src = inspect.getsource(build_dataset.main)
    assert "pair_loader" in src, "main() must build one loader for the pair"
    assert "render_reference(font_path, size=args.canvas, loader=pair_loader)" in src
    assert "render_atlas(font_path, size=args.canvas, loader=pair_loader)" in src


def test_a_shared_loader_makes_the_pair_agree():
    """Same loader in -> both halves reflect the same face instance."""
    from PIL import ImageFont

    import build_dataset

    path = _variable_font()
    calls = []

    def recording_loader(font_path, size):
        calls.append(("load", str(font_path), size))
        return ImageFont.truetype(str(font_path), size)

    build_dataset.render_atlas(path, 640, loader=recording_loader)
    n_atlas = len(calls)
    build_dataset.render_reference(path, 640, loader=recording_loader)
    assert n_atlas > 0 and len(calls) > n_atlas, \
        "render_reference did not go through the supplied loader"
    assert {c[1] for c in calls} == {str(path)}


def test_expansion_builder_uses_one_loader_per_entry():
    """pipeline/build_expansion.py must do the same for added fonts."""
    import inspect

    from pipeline import build_expansion
    src = inspect.getsource(build_expansion.main)
    assert "loader = loader_for(path, coords)" in src
    assert src.count("loader=loader") >= 2, \
        "both render_atlas and render_reference must receive the loader"
