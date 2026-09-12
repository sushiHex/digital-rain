"""Zero-shot probe: does GLM-Image capture ABSTRACT typeface style?

The hypothesis this tests (research/2026-07-31-successor-model-survey.md):
GLM-Image's Glyph Encoder is Glyph-ByT5, which encodes *canonical* character
shape derived from text -- which letter, not in whose style. Our identity is
already 0.989-0.994, so that headroom is spent. But its decoder is explicitly
tuned to "restore high-frequency details of images and text strokes", which is
exactly where our 4B fails (inline strokes, dot-grid).

Those pull opposite ways, so this probes the only thing that settles it: give
GLM-Image the same reference image our eval uses and see whether it reproduces
a distinctive typeface's letterforms.

This is NOT a like-for-like benchmark. GLM-Image will not emit our 12x8 95-glyph
atlas, so char_acc/identity from eval_checkpoint do not apply. It is a
capability probe, judged visually against the GT/9B/4B rows already rendered in
viz/out/compare_9b_4b.png.

Run from the repo root, after the GLM-Image fetch completes:
  python studies/probe_glm_image.py                 # default font set
  python studies/probe_glm_image.py --steps 28      # fewer steps, faster
  python studies/probe_glm_image.py --fonts Wonky   # single font
"""

# repo root on sys.path so `python studies/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import os
import time

MODEL = "zai-org/GLM-Image"
OUT_DIR = os.path.join("eval_runs", "glm_probe")

# The fonts that discriminate: three where the 4B loses badly on structure,
# one mid, one control where 9B and 4B are indistinguishable.
DEFAULT_FONTS = [
    "FascinateInline-Regular",     # 4B: char_acc -0.298 -- inline stroke lost
    "BitcountPropDoubleInk",       # 4B: dinov2 -0.162 -- dot-grid
    "RubikDistressed-Regular",     # 4B: -0.032 -- distress texture survives
    "Dangrek-Regular",             # 4B: char_acc -0.181
    "Wonky",                       # control: 9B == 4B
]

PROMPT = ('The word "Hamburg" written in exactly the same typeface as the '
          "reference image: identical letterform style, stroke weight, and "
          "texture. White letters on a plain black background, no decoration.")


def find_reference(stem):
    """The same reference image the eval harness conditions on."""
    hits = glob.glob(os.path.join("eval_holdout", "references",
                                  glob.escape(stem) + "*.png"))
    return hits[0] if hits else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fonts", default=None, help="comma-separated font stems")
    ap.add_argument("--steps", type=int, default=50, help="pipeline default is 50")
    ap.add_argument("--seed", type=int, default=42)
    # GLM-Image requires explicit output dimensions -- it builds an internal
    # target_h/target_w and fails on None. Its documented range is 1K-2K.
    ap.add_argument("--height", type=int, default=1024)
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--guidance", type=float, default=None,
                    help="override guidance_scale (pipeline default 1.5)")
    ap.add_argument("--offload", action="store_true", default=True,
                    help="CPU-offload components; bf16 GLM-Image is 33 GB and "
                         "will not fit resident on a 24 GB card")
    ap.add_argument("--no-offload", dest="offload", action="store_false")
    ap.add_argument("--sequential", action="store_true",
                    help="sequential (per-module) offload; slower but survives pipelines "
                         "whose components the model-level offload hook misses")
    ap.add_argument("--model-id", default=MODEL)
    ap.add_argument("--quanto", action="store_true",
                    help="quantise transformer + vision_language_encoder to int8 with "
                         "optimum-quanto, as generation_lib does for FLUX. 31.7 GB bf16 "
                         "-> ~16 GB, fits resident, and avoids both offload bugs")
    args = ap.parse_args()

    import torch
    from diffusers import GlmImagePipeline
    from PIL import Image

    fonts = args.fonts.split(",") if args.fonts else DEFAULT_FONTS
    os.makedirs(OUT_DIR, exist_ok=True)

    print(f"loading {args.model_id} (bf16, offload={args.offload}, "
          f"sequential={args.sequential}) ...", flush=True)
    t0 = time.time()
    pipe = GlmImagePipeline.from_pretrained(args.model_id, torch_dtype=torch.bfloat16)
    if args.quanto:
        # Same pattern as generation_lib.load_generation_pipe: quantise the big
        # components in place, freeze, then move everything to CUDA. Avoids the
        # offload hooks entirely, which are what break on this pipeline.
        from optimum.quanto import quantize, qint8, freeze
        for name in ("transformer", "vision_language_encoder"):
            comp = getattr(pipe, name, None)
            if comp is None:
                print(f"  (no {name} component)", flush=True)
                continue
            print(f"  quantising {name} to int8 ...", flush=True)
            quantize(comp, weights=qint8)
            freeze(comp)
        pipe.to("cuda")
    elif args.sequential:
        pipe.enable_sequential_cpu_offload()
    elif args.offload:
        pipe.enable_model_cpu_offload()
    else:
        pipe.to("cuda")
    print(f"  loaded in {time.time() - t0:.0f}s", flush=True)

    for stem in fonts:
        ref_path = find_reference(stem)
        if not ref_path:
            print(f"  {stem}: NO REFERENCE FOUND -- skipping", flush=True)
            continue
        ref = Image.open(ref_path).convert("RGB")

        kw = {}
        if args.guidance is not None:
            kw["guidance_scale"] = args.guidance

        t1 = time.time()
        try:
            result = pipe(
                prompt=PROMPT,
                image=[ref],          # pipeline calls len() on this; a bare PIL Image fails
                height=args.height, width=args.width,
                num_inference_steps=args.steps,
                generator=torch.Generator("cpu").manual_seed(args.seed),
                **kw,
            ).images[0]
        except Exception as e:
            import traceback
            print(f"  {stem}: FAILED {type(e).__name__}: {e}", flush=True)
            traceback.print_exc()
            continue

        out = os.path.join(OUT_DIR, f"{stem}.png")
        result.save(out)
        print(f"  {stem}: {time.time() - t1:.0f}s -> {out}  {result.size}", flush=True)

    print(f"\ndone. outputs in {OUT_DIR}/", flush=True)
    print("Judge against the GT/9B/4B rows in viz/out/compare_9b_4b.png -- this "
          "is a capability probe, not a scored benchmark.", flush=True)


if __name__ == "__main__":
    main()
