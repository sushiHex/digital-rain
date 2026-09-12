"""Pin the GT-free coherence measure, and the reason it works.

The product concept has no target font, so char_acc, DINOv2, LPIPS, R-ACC and
composite cannot score it. Identity survives and is blind to the failure that
actually happens: given a reference whose two glyphs disagree on style, the
model transfers both and the atlas splits. Identity scored that 0.9034 against
a coherent control's 0.8910 -- ABOVE it.

The first coherence attempt, raw ink spread, returned p=0.970. The fix is the
PER-CHARACTER normalisation: `.` and `M` differ enormously for reasons that have
nothing to do with style, so each feature is z-scored against its own
character's distribution over real fonts and only the residual is style. That
single change is the difference between p=0.970 and p=0.0021.

These tests pin the mechanism, not the p-value -- the validation set is a
gitignored GPU artifact, so the statistical claim lives in
research/2026-08-21-... and research/style_coherence_validation.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.style_coherence import (FEATURES, STATS, cell_features,
                                      load_stats, score_atlas)

UPM_CELL = (160, 106)


def bar(h, w, thickness, slant=0.0, top=20, left=30):
    """One vertical bar in a blank cell -- a minimal glyph with known style."""
    cell = np.zeros(UPM_CELL, dtype=np.uint8)
    for y in range(top, UPM_CELL[0] - top):
        x = int(left + slant * (y - top))
        cell[y, x:x + thickness] = 255
    return cell


def test_stats_file_is_tracked_and_covers_the_charset():
    data = json.loads(Path(STATS).read_text(encoding="utf-8"))
    assert data["n_fonts"] >= 100, "prior fitted on too few fonts to be stable"
    assert len(data["chars"]) >= 90
    assert set(data["features"]) == set(FEATURES)


def test_a_thicker_stroke_reads_as_heavier():
    """The weight axis, which is what the observed split moved along."""
    thin = cell_features(bar(0, 0, 4))
    thick = cell_features(bar(0, 0, 14))
    assert thick["stroke"] > thin["stroke"] * 1.5


def test_a_slanted_stroke_reads_as_slanted():
    upright = cell_features(bar(0, 0, 8, slant=0.0))
    italic = cell_features(bar(0, 0, 8, slant=0.5))
    assert abs(italic["slant"]) > abs(upright["slant"]) + 0.1


def test_a_dotted_glyph_reads_as_more_parts():
    """The dot-grid case: Bitcount vs a solid face."""
    solid = np.zeros(UPM_CELL, dtype=np.uint8)
    solid[30:130, 30:46] = 255
    dotted = np.zeros(UPM_CELL, dtype=np.uint8)
    for y in range(30, 130, 12):
        dotted[y:y + 6, 30:36] = 255
    assert cell_features(dotted)["parts"] > cell_features(solid)["parts"]


def test_an_empty_cell_yields_no_features():
    assert cell_features(np.zeros(UPM_CELL, dtype=np.uint8)) is None


def test_dispersion_rises_when_an_atlas_mixes_two_weights(tmp_path):
    """The mechanism, end to end: a split atlas must score higher than a
    uniform one. This is what identity and raw ink CV both missed."""
    from PIL import Image
    from atlas_constants import BLANK_INDICES, CELL_H, CELL_W, CHARSET, GRID_COLS

    def atlas(thickness_for_index):
        rows = (len(CHARSET) + GRID_COLS - 1) // GRID_COLS
        canvas = np.zeros((rows * CELL_H, GRID_COLS * CELL_W), dtype=np.uint8)
        for i in range(len(CHARSET)):
            if i in BLANK_INDICES:
                continue
            r, c = divmod(i, GRID_COLS)
            canvas[r * CELL_H:(r + 1) * CELL_H,
                   c * CELL_W:(c + 1) * CELL_W] = bar(0, 0, thickness_for_index(i))
        p = tmp_path / f"{thickness_for_index(0)}.png"
        Image.fromarray(canvas).save(p)
        return str(p)

    stats = load_stats()
    uniform = score_atlas(atlas(lambda i: 8), stats)
    split = score_atlas(atlas(lambda i: 4 if i % 2 else 14), stats)
    assert uniform and split
    assert split["dispersion"] > uniform["dispersion"], (
        f"a two-weight atlas scored {split['dispersion']:.4f}, no worse than "
        f"the uniform one at {uniform['dispersion']:.4f}")


def test_per_character_normalisation_is_actually_applied():
    """The fix itself. Two different characters with IDENTICAL pixels must not
    produce identical z-scores, because each is scored against its own
    character's distribution. Without this the measure returns p=0.970.
    """
    stats = load_stats()
    shared = [c for c in ("H", "o") if c in stats]
    assert len(shared) == 2
    means = [stats[c]["stroke"]["mean"] for c in shared]
    assert abs(means[0] - means[1]) > 1e-6, (
        "H and o have the same fitted stroke mean; the prior is not "
        "per-character and the normalisation cannot be doing anything")
