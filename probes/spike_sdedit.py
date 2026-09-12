"""De-risk spike for latent-inpaint repair: SDEdit ROUND-TRIP on the INT4+V3 pipe.

Encode a known atlas -> z0 (denoise latent space) -> noise to strength s ->
denoise via the pipeline (custom latents + sigmas, image=ref) -> decode. If the
output reconstructs the atlas (structure preserved, low MAE) at s<1, the core
mechanism (latent-space match + custom-latents + partial-schedule) works and the
full masked/glyph-guided repair is buildable. Also prints scheduler diagnostics
(does it honor custom sigmas, or null them for flow?).

  ./.venv-nunchaku/Scripts/python.exe spike_sdedit.py
"""

# repo root on sys.path so `python probes/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import glob
import os

os.environ.setdefault("NUNCHAKU_FORCE_UNFUSED_QKV", "1")

import numpy as np
import torch
from PIL import Image

from run_ref2font_v3_benchmark import render_aa_reference
from nunchaku_v3_lora import get_int4_v3_pipe, _cached_prompt_embeds


def main():
    pipe = get_int4_v3_pipe()
    embeds = _cached_prompt_embeds(pipe)
    dev = pipe.transformer.proj_out.weight.device if hasattr(pipe.transformer, "proj_out") else "cuda"
    dev = "cuda"
    print("scheduler:", pipe.scheduler.__class__.__name__,
          "use_flow_sigmas=", getattr(pipe.scheduler.config, "use_flow_sigmas", None), flush=True)

    fpath = sorted(glob.glob("eval_holdout/fonts/*.ttf"))[0]
    ref = render_aa_reference(fpath).convert("RGB")
    src_png = sorted(glob.glob("experiments/select_atlases/AkayaTelivigala_s*.png"))[0]
    atlas = Image.open(src_png).convert("RGB").resize((1280, 1280))
    a0 = np.asarray(atlas, dtype=np.float32)

    # encode to denoise latent space
    img_t = pipe.image_processor.preprocess(atlas, height=1280, width=1280).to(dev, torch.bfloat16)
    gen = torch.Generator("cpu").manual_seed(0)
    z0 = pipe._encode_vae_image(image=img_t, generator=gen)  # (1,128,h,w) unpacked normalized
    print("z0 shape:", tuple(z0.shape), z0.dtype, flush=True)

    N = 8
    for s in (1.0, 0.7, 0.5):
        noise = torch.randn(z0.shape, generator=torch.Generator("cpu").manual_seed(1), dtype=z0.dtype).to(dev)
        init = (1.0 - s) * z0 + s * noise            # flow-match init at sigma=s
        sigmas = list(np.linspace(s, 1.0 / N, N))
        try:
            out = pipe(image=ref, prompt_embeds=embeds, height=1280, width=1280,
                       num_inference_steps=N, sigmas=sigmas, latents=init,
                       generator=torch.Generator("cpu").manual_seed(2)).images[0]
            b = np.asarray(out.convert("RGB").resize((1280, 1280)), dtype=np.float32)
            mae = float(np.abs(a0 - b).mean())
            out.save(f"sdedit_s{s}.png")
            print(f"  s={s}: MAE(out, src)={mae:.1f}/255  saved sdedit_s{s}.png  "
                  f"{'reconstructs' if mae < 40 else 'diverged'}", flush=True)
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  s={s}: FAILED {type(e).__name__}: {str(e)[:200]}", flush=True)


if __name__ == "__main__":
    main()
