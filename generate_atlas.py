"""Generate a font atlas using FLUX.2-klein-base-9B (FP8) + Ref2Font LoRA.

Uses FP8 quantization to fit the 9B model on RTX 3090.
Supports caching (FirstBlockCache), reduced steps, VAE tiling,
multi-seed ensemble, and 2048x2048 resolution.

Usage:
  python generate_atlas.py --input reference_Aa.png --output atlas.png
  python generate_atlas.py --input ref.png --output atlas.png --fast
  python generate_atlas.py --input ref.png --output atlas.png --ensemble 5
  python generate_atlas.py --input ref.png --output atlas.png --resolution 2048
"""
import argparse
import time
import torch
from pathlib import Path


def load_pipeline():
    from diffusers import Flux2KleinPipeline
    from optimum.quanto import quantize, qfloat8, freeze
    from huggingface_hub import hf_hub_download

    print("Downloading Ref2Font LoRA...")
    lora_path = hf_hub_download("SnJake/Ref2Font", "Ref2FontV3.safetensors")

    print("Loading FLUX.2-klein-base-9B...")
    t0 = time.time()

    pipe = Flux2KleinPipeline.from_pretrained(
        "black-forest-labs/FLUX.2-klein-base-9B",
        torch_dtype=torch.bfloat16,
    )

    print("Quantizing transformer to FP8...")
    quantize(pipe.transformer, weights=qfloat8)
    freeze(pipe.transformer)

    print("Loading Ref2Font LoRA...")
    pipe.load_lora_weights(lora_path)

    # Enable VAE tiling if supported (helps with high resolutions)
    if hasattr(pipe, 'enable_vae_tiling'):
        pipe.enable_vae_tiling()
        print("VAE tiling enabled")
    elif hasattr(pipe.vae, 'enable_tiling'):
        pipe.vae.enable_tiling()
        print("VAE tiling enabled (via vae)")

    pipe.enable_model_cpu_offload()

    print(f"Pipeline loaded in {time.time() - t0:.0f}s")
    return pipe


def enable_cache(pipe, cache_type="firstblock"):
    """Enable transformer caching to skip redundant forward passes."""
    try:
        from diffusers import FirstBlockCacheConfig
        if cache_type == "firstblock":
            config = FirstBlockCacheConfig(threshold=0.05)
            pipe.transformer.enable_cache(config)
            print("FirstBlockCache enabled (threshold=0.05)")
    except (ValueError, Exception) as e:
        print(f"Cache not available for this model: {e}")


def generate_single(pipe, ref_image, steps, cfg, seed, resolution, prompt):
    """Generate a single atlas."""
    generator = torch.Generator().manual_seed(seed) if seed is not None else None

    try:
        result = pipe(
            prompt=prompt,
            image=ref_image,
            height=resolution,
            width=resolution,
            num_inference_steps=steps,
            guidance_scale=cfg,
            generator=generator,
        ).images[0]
    except TypeError as e:
        if "image" in str(e):
            result = pipe(
                prompt=prompt,
                height=resolution,
                width=resolution,
                num_inference_steps=steps,
                guidance_scale=cfg,
                generator=generator,
            ).images[0]
        else:
            raise
    return result


def score_glyph_cell(cell_img):
    """Score a glyph cell by edge sharpness (Laplacian variance)."""
    import numpy as np
    arr = np.array(cell_img.convert("L"), dtype=np.float32)
    # Laplacian edge response — sharper = higher variance
    laplacian = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    from scipy.signal import convolve2d
    edges = convolve2d(arr, laplacian, mode="valid")
    return float(np.var(edges))


def extract_grid_cells(atlas_img, rows=9, cols=8):
    """Extract individual glyph cells from an atlas grid."""
    w, h = atlas_img.size
    cell_w, cell_h = w // cols, h // rows
    cells = []
    for r in range(rows):
        for c in range(cols):
            box = (c * cell_w, r * cell_h, (c + 1) * cell_w, (r + 1) * cell_h)
            cells.append(atlas_img.crop(box))
    return cells, cell_w, cell_h


def ensemble_best(atlases, rows=9, cols=8):
    """Pick the best glyph from each cell across multiple atlases."""
    from PIL import Image

    all_grids = []
    for atlas in atlases:
        cells, cell_w, cell_h = extract_grid_cells(atlas, rows, cols)
        all_grids.append(cells)

    total_cells = rows * cols
    best_cells = []
    for i in range(total_cells):
        candidates = [grid[i] for grid in all_grids]
        scores = [score_glyph_cell(c) for c in candidates]
        best_idx = scores.index(max(scores))
        best_cells.append(candidates[best_idx])

    # Reconstruct atlas
    w, h = atlases[0].size
    result = Image.new("RGB", (w, h))
    idx = 0
    for r in range(rows):
        for c in range(cols):
            result.paste(best_cells[idx], (c * cell_w, r * cell_h))
            idx += 1

    return result


def main():
    parser = argparse.ArgumentParser(description="Generate font atlas with Ref2Font")
    parser.add_argument("--input", type=str, required=True, help="Path to Aa reference image")
    parser.add_argument("--output", type=str, default="test_atlas.png", help="Output atlas path")
    parser.add_argument("--steps", type=int, default=None, help="Inference steps (default: 20 fast, 35 normal)")
    parser.add_argument("--cfg", type=float, default=5.0, help="CFG guidance scale")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--fast", action="store_true", help="Enable all speed optimizations")
    parser.add_argument("--no-cache", action="store_true", help="Disable transformer caching")
    parser.add_argument("--ensemble", type=int, default=None, help="Generate N atlases, pick best per glyph")
    parser.add_argument("--resolution", type=int, default=1280, choices=[1280, 2048], help="Atlas resolution")
    args = parser.parse_args()

    from PIL import Image

    if args.steps is None:
        args.steps = 20 if args.fast else 35

    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM free: {(torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()) / 1024**3:.1f} GB")

    pipe = load_pipeline()

    if not args.no_cache:
        enable_cache(pipe)

    # Load reference image
    print(f"Loading reference: {args.input}")
    ref_image = Image.open(args.input).convert("RGB")
    target_size = args.resolution
    if max(ref_image.size) != target_size:
        ref_image = ref_image.resize((target_size, target_size), Image.LANCZOS)

    prompt = 'A technical font atlas grid of the Latin charset: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!?.,;:-"&". The style is strictly derived from the reference image "Aa".'

    if args.ensemble:
        import random
        base_seed = args.seed if args.seed is not None else random.randint(0, 2**32 - 1)
        seeds = [base_seed + i for i in range(args.ensemble)]
        print(f"Ensemble mode: generating {args.ensemble} atlases (seeds: {seeds})")

        atlases = []
        total_time = 0
        for i, seed in enumerate(seeds):
            print(f"\n--- Atlas {i+1}/{args.ensemble} (seed={seed}) ---")
            t1 = time.time()
            result = generate_single(pipe, ref_image, args.steps, args.cfg, seed, args.resolution, prompt)
            gen_time = time.time() - t1
            total_time += gen_time
            print(f"Generated in {gen_time:.1f}s")
            atlases.append(result)
            # Save individual atlas too
            individual_path = args.output.replace(".png", f"_seed{seed}.png")
            result.save(individual_path)

        print(f"\nTotal generation time: {total_time:.1f}s")
        print("Selecting best glyphs per cell...")
        best = ensemble_best(atlases)
        best.save(args.output)
        print(f"Saved ensemble result: {args.output}")
    else:
        print(f"Generating atlas (steps={args.steps}, cfg={args.cfg}, res={args.resolution})...")
        t1 = time.time()
        result = generate_single(pipe, ref_image, args.steps, args.cfg, args.seed, args.resolution, prompt)
        gen_time = time.time() - t1
        print(f"Generated in {gen_time:.1f}s")
        result.save(args.output)
        print(f"Saved: {args.output} ({result.size[0]}x{result.size[1]})")


if __name__ == "__main__":
    main()
