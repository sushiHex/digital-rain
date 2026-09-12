"""Pin the picker's WIRING, without a GPU.

WHY THIS EXISTS. `describe_candidates` and `pick_candidate` shipped on
2026-08-25 with only their pure helpers under test. The path that actually
runs -- generate, normalise, save, thread the paths through Gradio state, then
turn a click into a reference image -- had never been executed at all. A live
GPU smoke run proved it works once; this keeps it working.

Everything except the model call is exercised here by substituting the backend,
so the wiring is pinned in a suite that needs no checkpoint and no card. The
model call itself is not testable this way and is not pretended to be.
"""
import os
import sys
import types
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app  # noqa: E402
from analysis.generate_candidate_references import BACKENDS  # noqa: E402

CANVAS = 1024


def fake_reference(weight=1.0, seed=0):
    """A plausible Kg: light glyphs on a dark ground, ink in BOTH halves.

    `normalise` checks polarity, ink fraction and per-half balance, so a blank
    or one-sided image would be rejected and the test would pass for the wrong
    reason.
    """
    img = Image.new("L", (CANVAS, CANVAS), 0)
    draw = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed)
    for i in range(2):
        x0 = i * CANVAS // 2 + 90
        w = int(150 * weight)
        # A stem and a bar per half -- enough ink, in the right places.
        draw.rectangle([x0, 300, x0 + w, 740], fill=255)
        draw.rectangle([x0, 300, x0 + w + int(120 * weight), 300 + w], fill=255)
        if rng.random() > 0.5:
            draw.rectangle([x0, 640, x0 + w + 80, 640 + w // 2], fill=255)
    return img.convert("RGB")


def install_fake_backend(monkeypatch, weights):
    """Replace the generator with one yielding prepared images.

    The dict is MUTATED rather than replaced: `describe_candidates` does
    `from ... import BACKENDS` at call time, which binds the same object, so
    rebinding the name in the module would not be seen.
    """
    def fake(items, steps):
        for i, (label, _prompt, seed) in enumerate(items):
            yield label, fake_reference(weights[i % len(weights)], seed), 0.1

    monkeypatch.setitem(BACKENDS, "flux2-klein-base", fake)


@pytest.fixture
def tmp_out(monkeypatch, tmp_path):
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    return tmp_path


def test_a_blank_description_is_refused_without_generating(monkeypatch, tmp_out):
    def explode(*a, **k):
        raise AssertionError("generation must not start on an empty description")

    monkeypatch.setitem(BACKENDS, "flux2-klein-base", explode)
    gallery, status, paths = app.describe_candidates("   ", 4, 42,
                                                     progress=lambda *a, **k: None)
    assert gallery == [] and paths == []
    assert "describe" in status.lower()


def test_the_gallery_and_the_state_hold_the_same_paths(monkeypatch, tmp_out):
    install_fake_backend(monkeypatch, [1.0, 0.5, 1.4])
    gallery, status, paths = app.describe_candidates("a slab serif", 3, 42,
                                                     progress=lambda *a, **k: None)
    assert gallery == paths, "a mismatch here silently picks the wrong candidate"
    assert len(paths) == 3
    assert all(os.path.isfile(p) for p in paths)
    assert "3 candidate" in status


def test_identical_candidates_produce_the_narrow_advisory(monkeypatch, tmp_out):
    """Four copies of one image cannot differ, so the user must be told."""
    install_fake_backend(monkeypatch, [1.0])
    _gallery, status, paths = app.describe_candidates("a slab serif", 4, 42,
                                                      progress=lambda *a, **k: None)
    assert len(paths) == 4
    assert "reword" in status.lower(), status


def test_a_click_becomes_a_reference_image(monkeypatch, tmp_out):
    install_fake_backend(monkeypatch, [1.0, 0.6])
    _gallery, _status, paths = app.describe_candidates("a slab serif", 2, 42,
                                                       progress=lambda *a, **k: None)
    picked = app.pick_candidate(paths, types.SimpleNamespace(index=1))
    assert isinstance(picked, np.ndarray)
    assert picked.ndim == 3 and picked.shape[2] == 3, "generate_font wants RGB"
    with Image.open(paths[1]) as im:
        assert picked.shape[:2] == np.asarray(im.convert("RGB")).shape[:2]


@pytest.mark.parametrize("paths,index", [([], 0), (["a.png"], 5), (["a.png"], None)])
def test_an_impossible_pick_returns_none_rather_than_raising(paths, index):
    assert app.pick_candidate(paths, types.SimpleNamespace(index=index)) is None


def test_a_backend_that_raises_is_reported_not_propagated(monkeypatch, tmp_out):
    """A generation failure must reach the user as text, not a stack trace."""
    def broken(items, steps):
        raise RuntimeError("CUDA out of memory")
        yield  # pragma: no cover - generator marker

    monkeypatch.setitem(BACKENDS, "flux2-klein-base", broken)
    gallery, status, paths = app.describe_candidates("a slab serif", 2, 42,
                                                     progress=lambda *a, **k: None)
    assert gallery == [] and paths == []
    assert "CUDA out of memory" in status
