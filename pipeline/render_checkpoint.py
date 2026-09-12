"""Render a sample atlas from a LoRA checkpoint.

Standalone — loads base model, applies LoRA, generates one atlas, exits.

Usage:
  python pipeline/render_checkpoint.py <checkpoint_dir> --out <output.png> --reference-chars Kg
"""

# repo root on sys.path so `python pipeline/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import gc
import os
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont


def seed_everything(seed: int) -> None:
    """Seed every RNG path FLUX or its dependencies might pull from.

    bf16 reduction order on CUDA is still non-deterministic across cuBLAS
    workspace sizes, so two seeded runs may differ at the 4th-5th decimal of
    DINOv2 cosine -- well under the Wilcoxon medium-effect threshold (r=0.3).
    """
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def render_ref(font_path, chars, size=512):
    if not chars:
        raise ValueError("render_ref requires at least one character")
    from atlas_constants import load_truetype_pinned
    img = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(img)
    n = len(chars)
    cell_w = size // n
    lo, hi = 10, 800
    while lo < hi:
        mid = (lo + hi + 1) // 2
        font = load_truetype_pinned(font_path, mid)
        fits = all(
            (font.getbbox(ch)[2] - font.getbbox(ch)[0]) <= cell_w * 0.80
            and (font.getbbox(ch)[3] - font.getbbox(ch)[1]) <= size * 0.45
            for ch in chars
        )
        if fits:
            lo = mid
        else:
            hi = mid - 1
    font = load_truetype_pinned(font_path, lo)
    ascent, _ = font.getmetrics()
    baseline_y = int(size * 0.6)
    for i, ch in enumerate(chars):
        cx = i * cell_w
        bbox = font.getbbox(ch)
        ch_w = bbox[2] - bbox[0]
        draw.text((cx + (cell_w - ch_w) // 2 - bbox[0], baseline_y - ascent),
                  ch, fill=255, font=font)
    return img


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint_dir")
    parser.add_argument("--out", required=True)
    parser.add_argument("--reference-chars", action="append", default=None,
                        help="Reference characters. Pass once for single ref (default 'Rg'); "
                             "pass multiple times for multi-reference inference (Phase 1d).")
    parser.add_argument("--reference-font", action="append", default=None,
                        help="Reference font path. Must be passed the same number of times as "
                             "--reference-chars when using multi-reference.")
    parser.add_argument("--model", default="black-forest-labs/FLUX.2-klein-base-9B")
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--prompt-prefix", default="",
                        help="Optional prefix prepended to the structured prompt (for caption A/B testing)")
    args = parser.parse_args()

    # Both flags default together (single Rg-on-Times reference) if NEITHER
    # was provided. If only one was given, the user almost certainly meant
    # to pair it -- bail with a clearer message rather than silently mixing
    # their value with a default.
    if (args.reference_chars is None) != (args.reference_font is None):
        parser.error(
            "--reference-chars and --reference-font must be passed together "
            "(once each for single ref, or N times each for multi-ref). "
            "Pass both flags or neither (neither = defaults to 'Rg' + platform Times)."
        )
    from probe_utils import default_reference_font
    ref_chars_list = args.reference_chars or ["Rg"]
    ref_font_list = args.reference_font or [default_reference_font()]
    if len(ref_chars_list) != len(ref_font_list):
        parser.error(
            f"--reference-chars passed {len(ref_chars_list)} times but --reference-font "
            f"passed {len(ref_font_list)} times -- counts must match."
        )

    seed_everything(args.seed)

    from diffusers import Flux2KleinPipeline
    from optimum.quanto import quantize, qfloat8, freeze
    from peft import PeftModel

    print(f"Loading base pipeline...")
    pipe = Flux2KleinPipeline.from_pretrained(args.model, torch_dtype=torch.bfloat16)
    quantize(pipe.transformer, weights=qfloat8)
    freeze(pipe.transformer)

    print(f"Loading LoRA from {args.checkpoint_dir}...")
    pipe.transformer = PeftModel.from_pretrained(
        pipe.transformer, args.checkpoint_dir, adapter_name="default"
    )
    pipe.enable_model_cpu_offload()

    ref_imgs = [
        render_ref(font, chars).convert("RGB")
        for chars, font in zip(ref_chars_list, ref_font_list)
    ]
    print(f"  {len(ref_imgs)} reference image(s): "
          + ", ".join(f"'{c}' from {Path(f).name}"
                      for c, f in zip(ref_chars_list, ref_font_list)))

    from atlas_constants import make_prompt
    # Use the FIRST ref's chars for prompt structure (training was single-ref)
    base_prompt = make_prompt(ref_chars_list[0])
    prompt = f"{args.prompt_prefix} {base_prompt}".strip() if args.prompt_prefix else base_prompt

    from atlas_constants import CANVAS
    print(f"Generating ({args.steps} inference steps, seed={args.seed})...")
    result = pipe(
        prompt=prompt,
        image=ref_imgs,
        height=CANVAS, width=CANVAS,
        num_inference_steps=args.steps,
        generator=torch.Generator("cpu").manual_seed(args.seed),
    ).images[0]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write: tmp file, then os.replace, so a kill mid-write doesn't
    # leave a partial PNG that the run_*.py drivers would later "skip" as
    # already-existing.
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    result.save(str(tmp_path), format="PNG")
    os.replace(tmp_path, out_path)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
