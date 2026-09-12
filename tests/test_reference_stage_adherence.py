"""Pin the coupling that would rot silently, and the label compatibility.

Three things this file exists to keep honest:

  * `normalise_like_reference` MIRRORS `reference_gate.glyph_cells`. Training
    cells and reference cells must live in one space. If `glyph_cells` changes
    its normalisation and this copy does not, nothing fails loudly -- the model
    just trains on a different geometry than it is asked about. This project has
    already shipped that exact bug once, when `render_atlas` and
    `render_reference` had different variable-font defaults and mismatched ~110
    of 177 additions to dataset_v3.
  * `build_prompts` LEAVES n=1 LABELS UNCHANGED. `_synthetic_probe/external/`,
    `attribute_transfer.py` and the twelve atlases index by the `NN-` prefix, so
    an unconditional seed suffix would break every cross-reference to the
    2026-08-23 run without raising anything.
  * `--limit` cuts STYLES, not the flat candidate list. Cutting the list would
    give the first style all n candidates and the rest none.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.reference_stage_adherence import normalise_like_reference
from analysis.synthesize_rare_attributes import vector_from_cells


def build_prompts(*args, **kwargs):
    """The reference generator is part of the product recipe and is held in
    the private archive; in the public tree the four label tests skip."""
    gcr = pytest.importorskip("analysis.generate_candidate_references",
                              reason="reference generator held in the private archive")
    return gcr.build_prompts(*args, **kwargs)

REPO = Path(__file__).resolve().parent.parent


# --- the mirrored normalisation -------------------------------------------

def _synthetic_glyph(h=40, w=24, thickness=6):
    """A bar-and-stem shape with ink well inside a cell, at an arbitrary size."""
    from atlas_constants import CELL_H, CELL_W
    cell = np.zeros((CELL_H, CELL_W), dtype=np.uint8)
    y0, x0 = 20, 15
    cell[y0:y0 + h, x0:x0 + thickness] = 255
    cell[y0:y0 + thickness, x0:x0 + w] = 255
    return cell


def test_normalisation_rescales_ink_to_the_reference_height():
    """The whole point: an atlas cell is NOT rescaled and a reference glyph is."""
    from analysis.reference_gate import REF_TARGET_H

    out = normalise_like_reference(_synthetic_glyph(h=40))
    rows = np.where((out > 128).any(axis=1))[0]
    assert abs((rows[-1] - rows[0] + 1) - REF_TARGET_H) <= 2


def test_two_glyphs_of_different_sizes_normalise_to_the_same_height():
    """Without this, `K` at cap height and `g` at x-height would disagree about
    what a glyph's height means, which silently changes width_cv."""
    heights = []
    for h in (30, 45, 60):
        out = normalise_like_reference(_synthetic_glyph(h=h))
        rows = np.where((out > 128).any(axis=1))[0]
        heights.append(rows[-1] - rows[0] + 1)
    assert max(heights) - min(heights) <= 2, heights


def test_normalisation_output_matches_the_glyph_cells_canvas():
    from atlas_constants import CELL_H, CELL_W
    out = normalise_like_reference(_synthetic_glyph())
    assert out.shape == (CELL_H, CELL_W)
    assert out.dtype == np.uint8


def test_normalisation_refuses_a_cell_with_no_ink():
    from atlas_constants import CELL_H, CELL_W
    assert normalise_like_reference(np.zeros((CELL_H, CELL_W), np.uint8)) is None


def test_the_mirror_is_declared_in_the_docstring():
    """A copy nobody knows is a copy is the failure mode. If this assertion is
    ever deleted, delete the copy too."""
    import analysis.reference_stage_adherence as mod
    doc = mod.normalise_like_reference.__doc__ or ""
    assert "glyph_cells" in doc


# --- a two-cell vector is possible at all ---------------------------------

def test_vector_from_cells_accepts_two_cells_but_not_by_default():
    cells = [_synthetic_glyph(h=40), _synthetic_glyph(h=50, w=30)]
    assert vector_from_cells(cells) is None, "the 40-cell floor still guards atlases"
    v = vector_from_cells(cells, min_cells=2)
    assert v is not None and len(v) == 8


def test_width_cv_is_not_nan_for_a_single_cell():
    """std/mean over one value is 0/0. A NaN here would poison the whole vector."""
    v = vector_from_cells([_synthetic_glyph()], min_cells=1)
    assert v is not None and np.isfinite(v).all()


# --- label compatibility with the 2026-08-23 run --------------------------

def test_n1_labels_are_unchanged():
    items = build_prompts()
    assert len(items) == 12
    assert items[0][0] == "00-a_heavy_geometric_sans_serif"
    assert all("__s" not in label for label, _, _ in items)


def test_n1_labels_still_match_the_committed_atlases():
    """The cross-reference that would break silently."""
    external = REPO / "eval_runs" / "_synthetic_probe" / "external"
    if not external.is_dir():
        pytest.skip("generated atlases are a gitignored output")
    on_disk = sorted(p.stem for p in external.glob("*.png"))
    assert [lab for lab, _, _ in build_prompts()] == on_disk


def test_n_greater_than_one_gives_distinct_seeds_per_style():
    items = build_prompts(n=4, seed=42)
    assert len(items) == 48
    first = [i for i in items if i[0].startswith("00-")]
    assert sorted(s for _, _, s in first) == [42, 43, 44, 45]
    assert len({lab for lab, _, _ in items}) == 48


def test_every_style_gets_the_same_number_of_candidates():
    import collections
    items = build_prompts(n=3)
    counts = collections.Counter(lab.split("__")[0] for lab, _, _ in items)
    assert set(counts.values()) == {3}
