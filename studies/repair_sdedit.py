"""Style-preserving latent-inpaint repair for systematic-failure cells (Route B).

For cells that best-of-N/consensus can't fix (wrong glyph in every seed), paste
the CORRECT char as a neutral glyph (right letterform), then SDEdit-restyle ONLY
those cells to the target style via the V3-reference-conditioned INT4 pipe, with
RePaint-style masked blending so good cells stay frozen on the clean trajectory.
Finally paste only the restyled broken cells back (good cells stay pixel-exact).

Mechanism validated in spike_sdedit.py (custom latents+sigmas round-trip works).
"""

# repo root on sys.path so `python studies/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import numpy as np
import torch
from PIL import Image

from eval_v3_bestofn import EXPECTED, _COLS, _CELL, _OX, _OY
from cleanup.glyph_guide import render_neutral_glyph

_SCALE = 16  # atlas px per latent unit (1280 -> 80)


def _paste(atlas, idx, patch):
    r, c = idx // _COLS, idx % _COLS
    atlas[_OY + r * _CELL:_OY + r * _CELL + _CELL, _OX + c * _CELL:_OX + c * _CELL + _CELL] = patch


def _cell_box(idx):
    r, c = idx // _COLS, idx % _COLS
    return _OY + r * _CELL, _OX + c * _CELL


def _latent_mask(broken_idxs, h, w, device, dtype):
    m = torch.zeros((1, 1, h, w), device=device, dtype=dtype)
    for idx in broken_idxs:
        y0, x0 = _cell_box(idx)
        ly0, ly1 = y0 // _SCALE, -(-(y0 + _CELL) // _SCALE)   # floor / ceil
        lx0, lx1 = x0 // _SCALE, -(-(x0 + _CELL) // _SCALE)
        m[:, :, ly0:min(ly1, h), lx0:min(lx1, w)] = 1.0
    return m


def _unpack(x, h, w):   # (1, h*w, C) -> (1, C, h, w)  [inverse of _pack_latents]
    return x.permute(0, 2, 1).reshape(x.shape[0], -1, h, w)


def _pack(x):           # (1, C, h, w) -> (1, h*w, C)
    b, c, h, w = x.shape
    return x.reshape(b, c, h * w).permute(0, 2, 1)


def repair_atlas_sdedit(pipe, prompt_embeds, ref, consensus, broken_idxs,
                        s: float = 0.8, steps: int = 8, seed: int = 7):
    """Returns a repaired atlas (np.uint8) with broken_idxs restyled in-style."""
    if not broken_idxs:
        return consensus.copy()
    dev = "cuda"

    guided = consensus.copy()
    for idx in broken_idxs:
        _paste(guided, idx, render_neutral_glyph(EXPECTED[idx], size=(_CELL, _CELL)))

    img_t = pipe.image_processor.preprocess(
        Image.fromarray(guided), height=1280, width=1280).to(dev, torch.bfloat16)
    z0 = pipe._encode_vae_image(image=img_t, generator=torch.Generator("cpu").manual_seed(seed))
    _, C, H, W = z0.shape
    eps = torch.randn(z0.shape, generator=torch.Generator("cpu").manual_seed(seed + 1),
                      dtype=z0.dtype).to(dev)
    M = _latent_mask(broken_idxs, H, W, dev, z0.dtype)      # 1 = broken (evolve), 0 = good (freeze)
    init = (1.0 - s) * z0 + s * eps                          # flow-match init at sigma=s

    def callback(pp, i, t, kw):
        lat = kw["latents"]
        u = _unpack(lat, H, W)
        sig = float(pp.scheduler.sigmas[i + 1])              # sigma after this step
        good = (1.0 - sig) * z0 + sig * eps                  # clean atlas noised to current level
        u = M * u + (1.0 - M) * good
        return {"latents": _pack(u)}

    sigmas = list(np.linspace(s, 1.0 / steps, steps))
    out = pipe(image=ref, prompt_embeds=prompt_embeds, height=1280, width=1280,
               num_inference_steps=steps, sigmas=sigmas, latents=init,
               callback_on_step_end=callback, callback_on_step_end_tensor_inputs=["latents"],
               generator=torch.Generator("cpu").manual_seed(seed + 2)).images[0]
    out = np.asarray(out.convert("RGB").resize((1280, 1280)))

    final = consensus.copy()                                 # good cells stay pixel-exact
    for idx in broken_idxs:
        y0, x0 = _cell_box(idx)
        final[y0:y0 + _CELL, x0:x0 + _CELL] = out[y0:y0 + _CELL, x0:x0 + _CELL]
    return final
