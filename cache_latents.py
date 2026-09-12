"""Pre-cache VAE latents for all dataset images.

Encodes all reference and atlas images through the VAE, patchifies, applies
BatchNorm, and saves packed latent tensors to disk. This eliminates VAE
encoding during training and allows the VAE to be freed from GPU.

Usage:
  python cache_latents.py --dataset-dir dataset_v2 --cache-dir dataset_v2/cache
  python cache_latents.py --dataset-dir dataset_v2 --cache-dir dataset_v2/cache --ref-resolution 512
"""
import argparse
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm


def patchify_latents(latents):
    B, C, H, W = latents.shape
    latents = latents.view(B, C, H // 2, 2, W // 2, 2)
    latents = latents.permute(0, 1, 3, 5, 2, 4)
    return latents.reshape(B, C * 4, H // 2, W // 2)


def pack_latents(latents):
    B, C, H, W = latents.shape
    return latents.reshape(B, C, H * W).permute(0, 2, 1)


def encode_and_cache(vae, bn_mean, bn_std, image_path, resolution, device):
    """Encode a single image -> packed latent tensor."""
    image = Image.open(image_path).convert("RGB")
    if image.size != (resolution, resolution):
        image = image.resize((resolution, resolution), Image.LANCZOS)

    arr = np.array(image, dtype=np.float32) / 255.0
    pixel_values = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0) * 2.0 - 1.0
    pixel_values = pixel_values.to(device, dtype=torch.bfloat16)

    with torch.no_grad():
        latents = vae.encode(pixel_values).latent_dist.mode()
        latents = patchify_latents(latents)
        latents = (latents - bn_mean[None, :, None, None]) / bn_std[None, :, None, None]
        h, w = latents.shape[2], latents.shape[3]
        packed = pack_latents(latents)

    # Return on CPU as float16 to save disk space
    return packed.squeeze(0).cpu().half(), h, w


def main():
    parser = argparse.ArgumentParser(description="Pre-cache VAE latents for training")
    parser.add_argument("--dataset-dir", default="dataset_v2")
    parser.add_argument("--cache-dir", default=None, help="Cache directory (default: dataset_dir/cache)")
    parser.add_argument("--model", default="black-forest-labs/FLUX.2-klein-base-9B")
    parser.add_argument("--atlas-resolution", type=int, default=1280)
    parser.add_argument("--ref-resolution", type=int, default=512, help="Reference image resolution (smaller = faster training)")
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    cache_dir = Path(args.cache_dir) if args.cache_dir else dataset_dir / "cache"
    atlas_cache = cache_dir / "atlases"
    ref_cache = cache_dir / "references"
    atlas_cache.mkdir(parents=True, exist_ok=True)
    ref_cache.mkdir(parents=True, exist_ok=True)

    # Find all pairs
    ref_dir = dataset_dir / "references"
    atlas_dir = dataset_dir / "atlases"
    pairs = []
    for atlas_path in sorted(atlas_dir.glob("*.png")):
        ref_path = ref_dir / atlas_path.name
        if ref_path.exists():
            pairs.append((ref_path, atlas_path, atlas_path.stem))

    print(f"Found {len(pairs)} image pairs to cache")
    print(f"Atlas resolution: {args.atlas_resolution}px -> {args.atlas_resolution // 16}×{args.atlas_resolution // 16} latent")
    print(f"Reference resolution: {args.ref_resolution}px -> {args.ref_resolution // 16}×{args.ref_resolution // 16} latent")

    # Load VAE
    print("Loading VAE...")
    from diffusers import Flux2KleinPipeline
    pipe = Flux2KleinPipeline.from_pretrained(args.model, torch_dtype=torch.bfloat16)
    vae = pipe.vae.to("cuda", dtype=torch.bfloat16)
    vae.eval()

    bn_eps = getattr(vae.config, 'batch_norm_eps', 1e-4)
    bn_mean = vae.bn.running_mean.to("cuda", dtype=torch.bfloat16)
    bn_std = (vae.bn.running_var + bn_eps).sqrt().to("cuda", dtype=torch.bfloat16)

    # Free everything except VAE
    del pipe.transformer, pipe.text_encoder, pipe.tokenizer
    del pipe
    import gc
    gc.collect()
    torch.cuda.empty_cache()

    print(f"VAE VRAM: {torch.cuda.memory_allocated() / 1024**3:.1f} GB")

    # Cache all latents
    t0 = time.time()
    atlas_shape = None
    ref_shape = None

    for ref_path, atlas_path, stem in tqdm(pairs, desc="Caching"):
        atlas_out = atlas_cache / f"{stem}.pt"
        ref_out = ref_cache / f"{stem}.pt"

        if atlas_out.exists() and ref_out.exists():
            continue

        # Encode atlas
        if not atlas_out.exists():
            atlas_packed, ah, aw = encode_and_cache(
                vae, bn_mean, bn_std, atlas_path, args.atlas_resolution, "cuda"
            )
            torch.save({"latents": atlas_packed, "h": ah, "w": aw}, atlas_out)
            if atlas_shape is None:
                atlas_shape = atlas_packed.shape
                print(f"  Atlas latent: {atlas_packed.shape} ({ah}×{aw})")

        # Encode reference
        if not ref_out.exists():
            ref_packed, rh, rw = encode_and_cache(
                vae, bn_mean, bn_std, ref_path, args.ref_resolution, "cuda"
            )
            torch.save({"latents": ref_packed, "h": rh, "w": rw}, ref_out)
            if ref_shape is None:
                ref_shape = ref_packed.shape
                print(f"  Ref latent: {ref_packed.shape} ({rh}×{rw})")

    elapsed = time.time() - t0
    cache_size = sum(f.stat().st_size for f in cache_dir.rglob("*.pt")) / 1024**3
    print(f"\nCached {len(pairs)} pairs in {elapsed:.0f}s")
    print(f"Cache size: {cache_size:.2f} GB")
    print(f"Atlas tokens: {atlas_shape[0] if atlas_shape else '?'}, Ref tokens: {ref_shape[0] if ref_shape else '?'}")
    print(f"Total tokens per step: {(atlas_shape[0] if atlas_shape else 0) + (ref_shape[0] if ref_shape else 0)}")

    # Save metadata
    import json
    meta = {
        "atlas_resolution": args.atlas_resolution,
        "ref_resolution": args.ref_resolution,
        "num_pairs": len(pairs),
        "atlas_seq_len": int(atlas_shape[0]) if atlas_shape else None,
        "ref_seq_len": int(ref_shape[0]) if ref_shape else None,
        "atlas_spatial": [int(args.atlas_resolution // 16), int(args.atlas_resolution // 16)],
        "ref_spatial": [int(args.ref_resolution // 16), int(args.ref_resolution // 16)],
    }
    with open(cache_dir / "cache_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Metadata saved: {cache_dir / 'cache_meta.json'}")


if __name__ == "__main__":
    main()
