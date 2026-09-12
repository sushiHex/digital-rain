import os

import numpy as np, pytest
from atlas_constants import CELL_W, CELL_H

def _have_models():
    try:
        import torch, transformers  # noqa
        return True
    except Exception:
        return False

# These two tests DOWNLOAD TrOCR and DINOv2 from the Hub on first run. CI sets
# FONTGEN_NO_MODEL_DOWNLOADS=1 so a pull request does not pull a gigabyte of
# weights per run; locally they run and use the cache.
_NO_DOWNLOADS = os.environ.get("FONTGEN_NO_MODEL_DOWNLOADS") == "1"

@pytest.mark.skipif(not _have_models(), reason="transformers/torch not available")
@pytest.mark.skipif(_NO_DOWNLOADS, reason="FONTGEN_NO_MODEL_DOWNLOADS=1")
def test_ocr_fn_decodes_a_rendered_A():
    from cleanup.glyph_guide import render_neutral_glyph
    from cleanup.models import build_trocr_ocr_fn
    ocr_fn = build_trocr_ocr_fn(device="cpu")
    assert ocr_fn(render_neutral_glyph("A")).upper().startswith("A")

@pytest.mark.skipif(not _have_models(), reason="transformers/torch not available")
@pytest.mark.skipif(_NO_DOWNLOADS, reason="FONTGEN_NO_MODEL_DOWNLOADS=1")
def test_embed_fn_shape():
    from cleanup.models import build_dino_embed_fn
    embed_fn = build_dino_embed_fn(device="cpu")
    cells = [np.zeros((CELL_H, CELL_W, 3), dtype=np.uint8) for _ in range(3)]
    embs = embed_fn(cells)
    assert embs.shape[0] == 3 and embs.ndim == 2
