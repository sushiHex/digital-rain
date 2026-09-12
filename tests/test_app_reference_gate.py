"""Pin the gate's WIRING into the product path.

tests/test_reference_gate.py pins the measure. This pins that `app.generate_font`
actually consults it, refuses before spending a generation, and -- the part that
matters most -- FAILS OPEN.

Failing open is deliberate. The threshold is provisional, calibrated on the
spread of coherent references rather than on references a person judged
unacceptable. A guard on a provisional threshold must never become the reason a
working reference is refused, so anything it cannot score is generated normally.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app


@pytest.fixture(autouse=True)
def never_load_the_real_pipeline(monkeypatch):
    """Any test that reaches generation has already failed; make that loud."""
    def boom():
        raise AssertionError("generation was reached; the gate did not block")
    monkeypatch.setattr(app, "get_pipeline", boom)


def blank_reference():
    return np.zeros((256, 256, 3), dtype=np.uint8)


def test_a_reference_over_the_threshold_is_refused_before_generating(monkeypatch):
    monkeypatch.setattr(app, "check_reference",
                        lambda _p: (app.REFERENCE_GATE_THRESHOLD + 1.0,
                                    "the two glyphs differ in weight"))
    msg, atlas, otf, woff2 = app.generate_font(blank_reference(), "T", 20, 42)
    assert (atlas, otf, woff2) == (None, None, None)
    assert "rejected" in msg.lower()
    assert "differ in weight" in msg, "the message must say WHAT disagrees"


def test_the_check_can_be_turned_off(monkeypatch):
    """Unticking the box must reach generation -- the autouse fixture proves it."""
    monkeypatch.setattr(app, "check_reference",
                        lambda _p: (app.REFERENCE_GATE_THRESHOLD + 1.0, "x"))
    msg, *_ = app.generate_font(blank_reference(), "T", 20, 42,
                                gate_reference=False)
    assert "did not block" in msg or "Error" in msg


def test_an_unscoreable_reference_fails_open(monkeypatch):
    """The whole point: a guard on a provisional threshold must not refuse
    something merely because it could not read it."""
    monkeypatch.setattr(app, "check_reference", lambda _p: (None, None))
    msg, *_ = app.generate_font(blank_reference(), "T", 20, 42)
    assert "rejected" not in msg.lower()


def test_a_score_under_the_threshold_passes(monkeypatch):
    monkeypatch.setattr(app, "check_reference",
                        lambda _p: (app.REFERENCE_GATE_THRESHOLD - 0.5, "x"))
    msg, *_ = app.generate_font(blank_reference(), "T", 20, 42)
    assert "rejected" not in msg.lower()


def test_check_reference_never_raises(tmp_path):
    """It runs inside the request path. A malformed file must return None."""
    junk = tmp_path / "not-an-image.png"
    junk.write_text("definitely not a PNG", encoding="utf-8")
    assert app.check_reference(str(junk)) == (None, None)
    assert app.check_reference(str(tmp_path / "missing.png")) == (None, None)


def test_the_blocking_threshold_is_the_conservative_operating_point():
    """99th percentile: 2% of coherent references rejected, against 6% at the
    95th for four more points of recall. A false positive here refuses a real
    user, so the blocking gate takes the conservative end."""
    assert app.REFERENCE_GATE_THRESHOLD == pytest.approx(1.875)
