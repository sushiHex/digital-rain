"""Route B quality eval: INT4 base vs INT4 + V3 (runtime LoRA via forward-hooks),
on the hard fonts, scored with the V3 geometry (OCR-readability + DINO-template).

Sets NUNCHAKU_FORCE_UNFUSED_QKV=1 BEFORE importing nunchaku so qkv LoRA applies.

Usage (3.13 nunchaku env, 3090):
  ./.venv-nunchaku/Scripts/python.exe eval_route_b.py --n 6 --steps 8
"""

# repo root on sys.path so `python studies/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import os

os.environ.setdefault("NUNCHAKU_FORCE_UNFUSED_QKV", "1")  # MUST precede nunchaku import

import numpy as np
import torch

from eval_v3_bestofn import DRAWN, EXPECTED, v3_crop, render_gt_cell, ocr_acc, template_acc, V3_CHARSET
from cleanup.models import build_trocr_ocr_fn, build_dino_embed_fn
from probe_utils import HARD_FONTS
from run_ref2font_v3_benchmark import render_aa_reference
from nunchaku_v3_lora import V3_PROMPT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--skip-base", action="store_true", help="skip the no-LoRA base pass (it is ~0)")
    args = ap.parse_args()

    import nunchaku.models.transformers.transformer_flux2 as tfmod
    from nunchaku.models.transformers.transformer_flux2 import NunchakuFlux2Transformer2DModel
    from nunchaku.utils import get_precision
    from diffusers import Flux2KleinPipeline
    from huggingface_hub import hf_hub_download
    from nunchaku_v3_lora import load_v3_into_nunchaku

    assert tfmod._FORCE_UNFUSED_QKV, "env flag not honored"
    prec = get_precision()
    repo, name = "tonera/FLUX.2-klein-9B-Nunchaku", "FLUX.2-klein-9B-Nunchaku"
    tpath = hf_hub_download(repo, f"svdq-{prec}_r32-{name}.safetensors")
    tf = NunchakuFlux2Transformer2DModel.from_pretrained(tpath, torch_dtype=torch.bfloat16)
    pipe = Flux2KleinPipeline.from_pretrained(repo, torch_dtype=torch.bfloat16, transformer=tf)
    pipe.enable_model_cpu_offload()

    ocr_fn = build_trocr_ocr_fn()
    embed_fn = build_dino_embed_fn()

    fonts = list(HARD_FONTS.items())[: args.n]

    def gen(font_path, seed):
        ref = render_aa_reference(font_path).convert("RGB")
        img = pipe(prompt=V3_PROMPT, image=ref, height=1280, width=1280,
                   num_inference_steps=args.steps,
                   generator=torch.Generator("cpu").manual_seed(seed)).images[0]
        return np.asarray(img.convert("RGB"))

    # BASE (no LoRA)
    base_scores = []
    if not args.skip_base:
        print("=== generating BASE (no V3) ===", flush=True)
        for fname, fpath in fonts:
            atlas = gen(fpath, 42)
            gt = [render_gt_cell(fpath, EXPECTED[i]) for i in DRAWN]
            o, t = ocr_acc(atlas, ocr_fn), template_acc(atlas, gt, embed_fn)
            base_scores.append((fname, o, t))
            print(f"  {fname:24s} OCR={o:.3f} TEMPL={t:.3f}", flush=True)

    # + V3 via hooks
    print("\n=== applying V3 (Route B) ===", flush=True)
    info = load_v3_into_nunchaku(pipe.transformer, strength=args.strength)
    print(f"  applied {info['applied']} LoRA specs", flush=True)

    v3_scores = []
    for fname, fpath in fonts:
        atlas = gen(fpath, 42)
        gt = [render_gt_cell(fpath, EXPECTED[i]) for i in DRAWN]
        o, t = ocr_acc(atlas, ocr_fn), template_acc(atlas, gt, embed_fn)
        v3_scores.append((fname, o, t))
        print(f"  {fname:24s} OCR={o:.3f} TEMPL={t:.3f}", flush=True)

    vo = np.mean([s[1] for s in v3_scores]); vt = np.mean([s[2] for s in v3_scores])
    print("\n=== SUMMARY (mean over {} fonts, steps={}) ===".format(len(fonts), args.steps))
    if base_scores:
        bo = np.mean([s[1] for s in base_scores]); bt = np.mean([s[2] for s in base_scores])
        print(f"  BASE   OCR={bo:.3f} TEMPL={bt:.3f}")
        print(f"  delta  OCR={vo-bo:+.3f} TEMPL={vt-bt:+.3f}")
    print(f"  +V3    OCR={vo:.3f} TEMPL={vt:.3f}")
    print("  (V3 should clearly lift both; compare TEMPL to the bf16+V3 numbers in eval_runs/)")


if __name__ == "__main__":
    main()
