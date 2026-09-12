"""Trial: Nunchaku (SVDQuant W4A4/INT4) FLUX.2-klein-9B + Ref2Font V3 LoRA on the 3090.

Self-contained (no repo heavy imports — runs in the .venv-nunchaku 3.13 env which
only has torch/diffusers/nunchaku/PIL/hf_hub). Measures per-step latency at 1280²
and saves the atlas for a glyph-quality eyeball.

Run:  .venv-nunchaku/Scripts/python.exe test_nunchaku.py
"""
import os
import time

import torch
from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import hf_hub_download

CANVAS = 1280
FONT = "google-fonts/ofl/rubikdistressed/RubikDistressed-Regular.ttf"
V3_PROMPT = ('A technical font atlas grid of the Latin charset: '
             '"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
             '0123456789!?.,;:-\"&". The style is strictly derived from '
             'the reference image "Aa".')
OUT = "experiments/nunchaku_trial"


def render_aa(font_path, size=CANVAS):
    img = Image.new("RGB", (size, size), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    target_w, target_h = int(size * 0.75), int(size * 0.45)
    lo, hi = 50, 1500
    while lo < hi:
        mid = (lo + hi + 1) // 2
        f = ImageFont.truetype(str(font_path), mid)
        ba, bl = f.getbbox("A"), f.getbbox("a")
        tot_w = (ba[2] - ba[0]) + (bl[2] - bl[0]) + size // 12
        tot_h = max(ba[3] - ba[1], bl[3] - bl[1])
        if tot_w <= target_w and tot_h <= target_h:
            lo = mid
        else:
            hi = mid - 1
    f = ImageFont.truetype(str(font_path), lo)
    ba, bl = f.getbbox("A"), f.getbbox("a")
    aw, lw = ba[2] - ba[0], bl[2] - bl[0]
    gap = size // 12
    x0 = (size - (aw + lw + gap)) // 2
    asc, _ = f.getmetrics()
    by = int(size * 0.62)
    draw.text((x0 - ba[0], by - asc), "A", fill=(255, 255, 255), font=f)
    draw.text((x0 + aw + gap - bl[0], by - asc), "a", fill=(255, 255, 255), font=f)
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    print("torch", torch.__version__, "cuda", torch.cuda.is_available(),
          torch.cuda.get_device_name(0))

    from nunchaku.models.transformers.transformer_flux2 import NunchakuFlux2Transformer2DModel
    from nunchaku.utils import get_precision
    from diffusers import Flux2KleinPipeline

    prec = get_precision()
    print("nunchaku precision:", prec)
    repo, name = "tonera/FLUX.2-klein-9B-Nunchaku", "FLUX.2-klein-9B-Nunchaku"
    weight = f"svdq-{prec}_r32-{name}.safetensors"
    print("downloading transformer:", weight)
    tpath = hf_hub_download(repo, weight)

    t0 = time.time()
    transformer = NunchakuFlux2Transformer2DModel.from_pretrained(tpath, torch_dtype=torch.bfloat16)
    pipe = Flux2KleinPipeline.from_pretrained(repo, torch_dtype=torch.bfloat16, transformer=transformer)
    # Offload the (large) text encoder; the INT4 transformer is small (~5GB) and
    # stays resident during denoising -> no VRAM spill into Windows shared memory.
    pipe.enable_model_cpu_offload()
    print(f"loaded in {time.time()-t0:.0f}s (model_cpu_offload)")

    # Ref2Font V3 LoRA via the standard diffusers PEFT path (the class has the
    # PeftAdapterMixin; the model card's update_lora_params does not exist here).
    lora = hf_hub_download("SnJake/Ref2Font", "Ref2FontV3.safetensors")
    lora_ok = False
    try:
        pipe.load_lora_weights(lora)
        lora_ok = True
        print("V3 LoRA loaded OK (pipe.load_lora_weights)")
    except Exception as e:
        print(f"V3 LoRA load FAILED ({type(e).__name__}: {str(e)[:240]}); continuing without LoRA")

    ref = render_aa(FONT).convert("RGB")

    def gen(steps, seed):
        return pipe(prompt=V3_PROMPT, image=ref, height=CANVAS, width=CANVAS,
                    num_inference_steps=steps, guidance_scale=1.0,
                    generator=torch.Generator("cpu").manual_seed(seed)).images[0]

    print("warmup...", flush=True)
    gen(4, 1000)
    torch.cuda.reset_peak_memory_stats()
    for steps in (4, 8):
        t = time.time()
        img = gen(steps, 42)
        dt = time.time() - t
        peak = torch.cuda.max_memory_allocated() / 1e9
        tag = f"lora{'1' if lora_ok else '0'}_{steps}step"
        img.save(f"{OUT}/RubikDistressed_nunchaku_{tag}.png")
        print(f"  {steps} steps: {dt:.1f}s  (~{dt/steps:.2f}s/step)  peak {peak:.1f}GB  "
              f"[{'SUB-MINUTE' if dt < 60 else 'OVER 60s'}]", flush=True)


if __name__ == "__main__":
    main()
