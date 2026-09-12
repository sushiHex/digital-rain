"""Pin per-character letterfitting, and pin that it is NOT the default.

`atlas_to_font` gave every glyph the same sidebearing -- one constant, 0.05 em,
both sides. Real fitting is not like that: over 600 fonts `H` wants LSB 0.054 em
and `A` wants 0.007 em, because a vertical stem needs air beside it and a
diagonal does not.

That mattered because letterfitting is 74% of the finished font's error
(research/2026-08-18-scoring-the-finished-font.md), and `A`, `T` and `V` were
among its worst glyphs -- exactly the characters a constant is most wrong about.

Two traps this pins:

  * The prior is OFF by default, and that is a measured decision. Applied to
    this pipeline it gains nothing (gt_traced advance MAE 0.1168 -> 0.1165) and
    makes text width materially worse (-0.0030 -> -0.0622), because the tracer
    under-measures ink by ~3.5% on letters and the flat sidebearing was
    absorbing that bias. Two wrong terms were cancelling.
  * A missing or corrupt prior file must degrade to the constant, never raise.
    The font builder runs inside the demo request path.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import atlas_to_font
from atlas_constants import BLANK_INDICES, CELL_H, CELL_W, CHARSET
from atlas_to_font import SIDEBEARING_PRIOR_PATH, build_font, load_sidebearing_prior

UPM = 1000
BASELINE_Y, CAP_TOP_Y, XHEIGHT_TOP_Y = 130, 60, 85


def box(x0, y0, x1, y1):
    return [[("M", [(x0, y0)]), ("L", [(x1, y0)]), ("L", [(x1, y1)]),
             ("L", [(x0, y1)]), ("Z", [])]]


def uniform_cells(width=50):
    """Every drawn glyph gets IDENTICAL ink, so advances differ only by fitting."""
    cells = []
    for i, ch in enumerate(CHARSET):
        if i in BLANK_INDICES or not ch.isalpha():
            cells.append([])
        elif ch.isupper():
            cells.append(box(20, CAP_TOP_Y, 20 + width, BASELINE_Y))
        else:
            cells.append(box(20, XHEIGHT_TOP_Y, 20 + width, BASELINE_Y))
    return cells


def advances(font):
    upm = font["head"].unitsPerEm
    cmap, hmtx = font.getBestCmap(), font["hmtx"].metrics
    return {c: hmtx[cmap[ord(c)]][0] / upm
            for c in CHARSET if cmap.get(ord(c)) in hmtx}


def test_the_prior_file_is_tracked_and_covers_the_charset():
    prior = load_sidebearing_prior()
    missing = [c for c in CHARSET if c != " " and c not in prior]
    assert not missing, f"prior is missing {len(missing)} characters: {missing[:10]}"


def test_a_is_fitted_tighter_than_h():
    """The headline character effect, and the one a constant cannot express."""
    adv = advances(build_font(uniform_cells(), CHARSET, CELL_W, CELL_H, upm=UPM,
                              use_sidebearing_prior=True))
    assert adv["A"] < adv["H"], (
        f"identical ink, yet A={adv['A']:.4f} em is not tighter than "
        f"H={adv['H']:.4f} em -- the prior is not being applied")


def test_asymmetric_characters_are_fitted_asymmetrically():
    """`V` sits at LSB 0.018 / RSB 0.002; a constant makes those equal."""
    prior = load_sidebearing_prior()
    lsb, rsb = prior["V"]
    assert abs(lsb - rsb) > 0.005, f"V fitted symmetrically: {lsb} / {rsb}"


def test_the_prior_is_off_by_default():
    """Pins the measured decision: shipping it regressed text width."""
    default = advances(build_font(uniform_cells(), CHARSET, CELL_W, CELL_H, upm=UPM))
    assert default["A"] == default["H"] == default["V"], (
        "the default build applied per-character fitting; it measures worse in "
        "this pipeline -- see the build_font docstring")


def test_the_prior_changes_fitting_when_asked_for():
    """The opt-in path must actually reach the builder."""
    adv = advances(build_font(uniform_cells(), CHARSET, CELL_W, CELL_H, upm=UPM,
                              use_sidebearing_prior=True))
    assert adv["A"] != adv["H"], "use_sidebearing_prior=True had no effect"


def test_a_missing_prior_degrades_to_the_constant(tmp_path, monkeypatch):
    """This runs in the demo request path; it must never raise."""
    monkeypatch.setattr(atlas_to_font, "_SIDEBEARING_PRIOR", None)
    assert load_sidebearing_prior(str(tmp_path / "absent.json")) == {}


def test_a_corrupt_prior_degrades_to_the_constant(tmp_path, monkeypatch):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(atlas_to_font, "_SIDEBEARING_PRIOR", None)
    assert load_sidebearing_prior(str(bad)) == {}


def test_prior_values_are_plausible_sidebearings():
    """Guard against a regenerated prior in the wrong units."""
    data = json.loads(Path(SIDEBEARING_PRIOR_PATH).read_text(encoding="utf-8"))
    for ch, rec in data["chars"].items():
        assert -0.15 <= rec["lsb"] <= 0.30, f"{ch!r} lsb {rec['lsb']} not in em"
        assert -0.15 <= rec["rsb"] <= 0.30, f"{ch!r} rsb {rec['rsb']} not in em"
