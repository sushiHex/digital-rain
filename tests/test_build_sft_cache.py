import numpy as np
from PIL import Image


def test_assemble_winner_atlas_pastes_winner_cells(tmp_path):
    from build_sft_cache import assemble_winner_atlas
    from atlas_constants import CHARSET, DRAWN_INDICES, CANVAS
    from eval_checkpoint import crop_cell
    cdir = tmp_path / "candidates" / "F"; cdir.mkdir(parents=True)
    base = np.zeros((CANVAS, CANVAS, 3), np.uint8)
    glyph = base.copy(); glyph[:] = 10
    baseline = base.copy(); baseline[:] = 240
    Image.fromarray(glyph).save(cdir / "glyph__seed0.png")
    Image.fromarray(baseline).save(cdir / "baseline__seed0.png")
    ch = CHARSET[DRAWN_INDICES[0]]
    sft = [{"font": "F", "char": ch, "winner_key": "F__baseline__seed0"}]
    atlas = assemble_winner_atlas("F", sft, str(tmp_path / "candidates"))
    # the winner cell for ch should equal baseline's cell (240), not glyph (10)
    cell = crop_cell(atlas, DRAWN_INDICES[0])
    assert int(cell.mean()) > 200
