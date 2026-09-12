"""Test Flux.1 Dev for generating font glyph images on RTX 3090.

Generates single black letters on white background at 512x512.
Uses FP8 quantization to fit in 24GB VRAM.
"""
import torch
import time
import os

def main():
    from diffusers import FluxPipeline
    from optimum.quanto import qfloat8

    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    print("Loading Flux.1 Dev with FP8 quantization...")
    t0 = time.time()

    pipe = FluxPipeline.from_pretrained(
        "black-forest-labs/FLUX.1-dev",
        torch_dtype=torch.bfloat16,
    )

    # Quantize transformer to FP8 to fit in 24GB
    print("Quantizing transformer to FP8...")
    pipe.transformer = qfloat8(pipe.transformer)

    pipe.enable_model_cpu_offload()  # Offload unused components to CPU

    load_time = time.time() - t0
    print(f"Model loaded in {load_time:.0f}s")
    print(f"VRAM after load: {torch.cuda.memory_allocated() / 1024**3:.1f} GB")

    # Generate glyph images for A-J
    chars = "ABCDEFGHIJ"
    style = "geometric sans-serif"
    os.makedirs("glyph_images", exist_ok=True)

    for char in chars:
        prompt = (
            f"A single large uppercase letter '{char}' in {style} font style. "
            f"Black letter on pure white background. Clean, sharp edges. "
            f"Centered. No other text or decoration. Professional typography."
        )

        print(f"Generating {char}...")
        t1 = time.time()

        image = pipe(
            prompt=prompt,
            height=512,
            width=512,
            num_inference_steps=20,  # Fewer steps for speed
            guidance_scale=3.5,
        ).images[0]

        gen_time = time.time() - t1
        print(f"  {char}: {gen_time:.1f}s")

        image.save(f"glyph_images/{char}.png")

    print(f"\nSaved {len(chars)} glyph images to glyph_images/")
    print(f"Total generation time: {time.time() - t0 - load_time:.0f}s")


if __name__ == "__main__":
    main()
