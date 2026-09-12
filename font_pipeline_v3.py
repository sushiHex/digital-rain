"""Product entry point: V3-on-INT4 (Route B) font-atlas generation with the
validated quality lever (best-of-N), in V3's native 71-char geometry.

FAST:    one render.
QUALITY: best-of-N cell selection over N seeds (the validated +0.20 OCR lever).

The cleanup package's verify/inpaint layer is currently locked to the Kg/95-char
geometry (cleanup/cells.py -> atlas_constants); V3 uses the 71-char compute_grid
layout, so this uses the V3-geometry best-of-N from eval_v3_bestofn directly.
Making run_cleanup geometry-configurable (so V3 can also use NeutralPaste/Flux
repair) is the remaining cleanup-package refactor — see route_b/README.md.

  ./.venv-nunchaku/Scripts/python.exe font_pipeline_v3.py   # smoke test
"""
import os

os.environ.setdefault("NUNCHAKU_FORCE_UNFUSED_QKV", "1")  # before nunchaku import

import numpy as np

from nunchaku_v3_lora import build_nunchaku_generate_fn


def generate_font_v3(reference, mode: str = "QUALITY", seeds: int = 8, steps: int | None = None,
                     strength: float = 1.0, seed: int = 42, ocr_fn=None, embed_fn=None,
                     repair: bool = False) -> np.ndarray:
    """reference: PIL image (the per-font 'Aa' reference). Returns a V3-layout
    RGB atlas (np.uint8, HxWx3). Step defaults are mode-tuned (validated): FAST=3
    (sub-minute, single-seed quality intact), QUALITY=8 (best-of-N is ~0.04 OCR
    better at 8 steps than 4 — quality mode isn't time-bound).

    repair=True (QUALITY only) runs a final NeutralPaste pass on systematic-failure
    cells (fail OCR AND style-outlier): a near-wash on the dual metric (+0.009 OCR
    / -0.014 TEMPL) but guarantees a readable correct glyph for vectorization
    completeness — opt-in, off by default (it trades style for readability)."""
    if steps is None:
        steps = 3 if mode == "FAST" else 8
    gen = build_nunchaku_generate_fn(reference, strength=strength, steps=steps)
    if mode == "FAST":
        return gen(seed)
    if mode == "QUALITY":
        # consensus-aware best-of-N: holds OCR, recovers style vs plain best_of_n
        from v3_select import consensus_best_of_n, verify_and_repair_v3
        if ocr_fn is None:
            from cleanup.models import build_trocr_ocr_fn
            ocr_fn = build_trocr_ocr_fn()
        if embed_fn is None:
            from cleanup.models import build_dino_embed_fn
            embed_fn = build_dino_embed_fn()
        atlases = [gen(seed + i) for i in range(seeds)]
        atlas = consensus_best_of_n(atlases, ocr_fn, embed_fn)
        if repair:
            atlas, _ = verify_and_repair_v3(atlas, ocr_fn, embed_fn)
        return atlas
    raise ValueError(f"unknown mode {mode!r} (expected 'FAST' or 'QUALITY')")


def _smoke():
    import glob
    import time
    from run_ref2font_v3_benchmark import render_aa_reference
    from nunchaku_v3_lora import build_nunchaku_generate_fn
    fpath = sorted(glob.glob("eval_holdout/fonts/*.ttf"))[0]
    ref = render_aa_reference(fpath).convert("RGB")
    gen = build_nunchaku_generate_fn(ref, steps=3)  # loads pipe + caches prompt embeds
    gen(999)                                         # warm (excludes load/encode from timing)
    t0 = time.time()
    atlas = gen(42)                                  # steady-state sub-minute render
    dt = time.time() - t0
    assert atlas.shape == (1280, 1280, 3), atlas.shape
    assert atlas.dtype == np.uint8, atlas.dtype
    print(f"SMOKE OK: FAST 3-step cached render {atlas.shape} in {dt:.1f}s "
          f"({'SUB-MINUTE' if dt < 60 else 'OVER 60s'}) from {os.path.basename(fpath)}")


if __name__ == "__main__":
    _smoke()
