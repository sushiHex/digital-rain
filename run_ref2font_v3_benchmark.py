"""Benchmark Ref2Font V3 against our LoRA on the 5 worst fonts.

Reuses load_pipeline / generate_single from generate_atlas.py to avoid drift
from the production V3 invocation. Renders each font's "Aa" reference, then
generates the V3 atlas. No scoring here — the V3 atlas format (9x8 grid, 70
chars) differs from ours (12x8 grid, 95 chars), so whole-atlas LPIPS isn't
apples-to-apples. This pass produces images for visual inspection; if V3
clearly looks better on these hard fonts, we'll invest in a per-cell scorer.
"""
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path("experiments/ref2font_v3_benchmark")

from probe_utils import HARD_FONTS


def render_aa_reference(font_path, size=1280):
    """Render an 'Aa' reference for V3. V3 expects a square reference where
    'A' and 'a' are presented at a comfortable size — match generate_atlas.py
    style if it has any conventions, otherwise use a simple centered layout."""
    img = Image.new("RGB", (size, size), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Find max font size that fits both A and a within the canvas
    chars = "Aa"
    target_w = int(size * 0.75)
    target_h = int(size * 0.45)
    lo, hi = 50, 1500
    while lo < hi:
        mid = (lo + hi + 1) // 2
        font = ImageFont.truetype(str(font_path), mid)
        bb_a = font.getbbox("A")
        bb_la = font.getbbox("a")
        total_w = (bb_a[2] - bb_a[0]) + (bb_la[2] - bb_la[0]) + size // 12  # gap
        total_h = max(bb_a[3] - bb_a[1], bb_la[3] - bb_la[1])
        if total_w <= target_w and total_h <= target_h:
            lo = mid
        else:
            hi = mid - 1
    font = ImageFont.truetype(str(font_path), lo)
    bb_a = font.getbbox("A")
    bb_la = font.getbbox("a")
    a_w = bb_a[2] - bb_a[0]
    la_w = bb_la[2] - bb_la[0]
    gap = size // 12
    total_w = a_w + la_w + gap

    ascent, _ = font.getmetrics()
    baseline_y = int(size * 0.62)
    x0 = (size - total_w) // 2
    draw.text((x0 - bb_a[0], baseline_y - ascent), "A", fill=(255, 255, 255), font=font)
    draw.text((x0 + a_w + gap - bb_la[0], baseline_y - ascent), "a", fill=(255, 255, 255), font=font)
    return img


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Pre-render all references first (CPU only) so any bugs surface before model load
    print("Pre-rendering Aa references...")
    refs = {}
    for name, path in HARD_FONTS.items():
        ref_path = OUT_DIR / f"{name}__ref_Aa.png"
        if not ref_path.exists():
            ref = render_aa_reference(path)
            ref.save(ref_path)
            print(f"  saved ref: {ref_path}")
        refs[name] = Image.open(ref_path).convert("RGB")

    # Now load V3 pipeline (slow path)
    from generate_atlas import load_pipeline, enable_cache, generate_single
    pipe = load_pipeline()
    enable_cache(pipe)

    PROMPT = ('A technical font atlas grid of the Latin charset: '
              '"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
              '0123456789!?.,;:-\"&". The style is strictly derived from '
              'the reference image "Aa".')

    for i, (name, ref_img) in enumerate(refs.items(), 1):
        out_path = OUT_DIR / f"{name}__v3_atlas.png"
        if out_path.exists():
            print(f"[{i}/{len(refs)}] SKIP {out_path.name} (exists)")
            continue
        print(f"[{i}/{len(refs)}] === {name} ===")
        t0 = time.time()
        result = generate_single(
            pipe, ref_img,
            steps=35,           # match production default for V3
            cfg=5.0,
            seed=42,
            resolution=1280,
            prompt=PROMPT,
        )
        result.save(out_path)
        print(f"  saved {out_path.name} in {time.time()-t0:.1f}s")

    print(f"\nDone. Outputs in {OUT_DIR}/")


if __name__ == "__main__":
    main()
