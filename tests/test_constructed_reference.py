"""Pin the constructed arm: what it detects, what it refuses, and that it fails open.

The finding behind it: no text-to-image model invents a stencil -- sixteen
images across three mechanisms produced no break -- but the LoRA propagates one
it is handed. So for those treatments the product builds the reference instead
of generating it.

Three properties this file exists to keep:

  * DETECTION IS NARROW. A false construction is worse than a missing one: it
    puts an option in front of the user that they did not ask for. "no stencil
    breaks" must not produce a stencil.
  * THE TREATMENT GOES ONTO A DRAWN CANDIDATE, not a neutral font, so the
    description's style survives. Applying it to a neutral face would answer
    "a heavy blackletter stencil" with a stencilled plain sans.
  * IT FAILS OPEN. A construction that cannot be built must never be the reason
    the drawn candidates are withheld.
"""
import os
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app  # noqa: E402
from analysis.constructed_reference import (TREATMENTS, best_candidate, build,
                                            construct, detect)


def a_reference(tmp_path, name="ref.png", weight=110):
    """A plausible Kg: light glyphs on a dark ground, ink in both halves."""
    img = Image.new("L", (1024, 1024), 0)
    draw = ImageDraw.Draw(img)
    for i in range(2):
        x0 = i * 512 + 120
        draw.rectangle([x0, 300, x0 + weight, 760], fill=255)
        draw.rectangle([x0, 300, x0 + weight + 130, 300 + weight], fill=255)
        draw.rectangle([x0, 560, x0 + weight + 90, 560 + weight], fill=255)
    dst = tmp_path / name
    img.convert("RGB").save(dst)
    return str(dst)


# --- detection ------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("a stencil sans with deliberate breaks in the strokes", ["stencil"]),
    ("an inline face with a white stripe inset within each stroke", ["inline"]),
    ("an outlined blackletter", ["outline"]),
    ("a heavy geometric sans serif, closed apertures", []),
    ("a wide low-contrast monospace with prominent spurs", []),
])
def test_detection_matches_only_what_is_asked_for(text, expected):
    assert detect(text) == expected


@pytest.mark.parametrize("text", [
    "a solid face with no stencil breaks",
    "a sans without inline striping",
    "solid strokes, not outlined",
])
def test_a_negated_treatment_is_not_constructed(text):
    """A false construction is worse than a missing one."""
    assert detect(text) == []


def test_detection_survives_an_empty_description():
    assert detect("") == [] and detect(None) == []


def test_every_named_treatment_has_a_transform():
    from analysis.synthesise_transforms import TRANSFORMS as T
    for name in TREATMENTS:
        assert name in T, f"{name} is detectable but cannot be built"


# --- construction ---------------------------------------------------------

def test_a_construction_changes_the_ink_substantially(tmp_path):
    """A treatment that alters almost nothing is a silent no-op -- the exact
    failure that nearly voided the probe's positive control."""
    src = a_reference(tmp_path)
    base = np.asarray(Image.open(src).convert("L"), dtype=float)
    ink = int((base > 128).sum())
    for name in ("stencil", "inline", "outline"):
        out = construct(src, name, seed=0)
        assert out is not None, name
        arr = np.asarray(out.convert("L"), dtype=float)
        changed = int((np.abs(arr - base) > 40).sum())
        assert changed / ink > 0.05, f"{name} changed only {changed/ink:.1%}"


def test_build_applies_to_the_most_coherent_candidate(tmp_path, monkeypatch):
    paths = [a_reference(tmp_path, "a.png"), a_reference(tmp_path, "b.png", 60)]
    monkeypatch.setattr("analysis.constructed_reference.best_candidate",
                        lambda p, chars=None: p[1])
    built = build("a stencil sans", paths, seed=0)
    assert [n for n, _ in built] == ["stencil"]
    chosen = np.asarray(Image.open(paths[1]).convert("L"), dtype=float)
    made = np.asarray(built[0][1].convert("L"), dtype=float)
    # the construction must derive from the CHOSEN candidate, not the other
    other = np.asarray(Image.open(paths[0]).convert("L"), dtype=float)
    assert np.abs(made - chosen).mean() < np.abs(made - other).mean()


def test_build_returns_nothing_when_no_treatment_is_named(tmp_path):
    assert build("a heavy geometric sans serif", [a_reference(tmp_path)]) == []


def test_best_candidate_falls_back_rather_than_refusing():
    assert best_candidate(["/nonexistent/a.png"]) == "/nonexistent/a.png"
    assert best_candidate([]) is None


# --- failing open ---------------------------------------------------------

def test_construct_returns_none_on_an_unreadable_source():
    assert construct("/nonexistent.png", "stencil") is None


def test_the_app_helper_fails_open(tmp_path):
    """An unbuildable construction must not take the picker down with it."""
    assert app.construct_references("a stencil sans", ["/nonexistent.png"],
                                    str(tmp_path)) == []
    assert app.construct_references("a plain sans", [], str(tmp_path)) == []


def test_the_app_helper_writes_files_that_exist(tmp_path):
    src = a_reference(tmp_path)
    built = app.construct_references("a stencil sans", [src], str(tmp_path))
    assert built and all(os.path.isfile(p) for _, p in built)
