# Improving AI-Generated Font Atlas Quality & Raster-to-Vector Pipeline

**Date:** 2026-04-03
**Context:** FLUX.2-klein-base-9B + Ref2Font LoRA generates 1280x1280 atlas (72 chars, 8x9 grid). Ref2Font flux_grid_to_ttf.py traces contours with scikit-image and builds TTF.

---

## 1. Higher Resolution Generation (2048x2048 or 2560x2560)

**Difficulty:** Low-Medium | **Expected Improvement:** 15-25% sharper glyphs

FLUX.2 supports resolutions up to 4 megapixels (2048x2048) with dimensions as multiples of 16.

### VRAM Requirements (FP8)

| Resolution | Baseline VRAM | Peak VRAM (attention) | Notes |
|------------|--------------|----------------------|-------|
| 1280x1280  | ~14-15 GB    | ~16-18 GB            | Current setup, comfortable on 24 GB |
| 2048x2048  | ~14-15 GB    | ~18-20 GB            | Feasible on 24 GB with tiled VAE |
| 2560x2560  | ~14-15 GB    | ~22-26 GB            | Tight on 24 GB, needs aggressive tiling |

**Key technique: Tiled VAE decoding.** Splits the latent into 512x512 tiles decoded sequentially, preventing the VAE decode memory spike. Adds 15-25% generation time but enables resolutions that would otherwise OOM.

- FP8 at 2048x2048 shows no perceptible quality difference versus FP16 while being ~100% faster (28.6s vs 58.2s benchmarked).
- Tile size 512 for max VRAM savings, 768 for faster decode with slightly more VRAM.
- ComfyUI: use VAEDecodeTiled node. For programmatic use, both diffusers and ComfyUI tiled diffusion extension support this.

**Practical recommendation:** Move to 2048x2048 first. Each glyph cell grows from ~160x142 to ~256x227 pixels -- almost double the detail per character. The 2560x2560 push is marginal gain for significant VRAM pressure.

**Caveat:** Ref2Font LoRA was trained on 1280x1280 atlases. Generating at 2048x2048 may produce layout drift unless the LoRA generalizes well to higher resolutions, or you fine-tune it at the new resolution. Test with the same prompt/seed at 2048x2048 to see if grid alignment holds before committing.

Sources:
- https://docs.jarvislabs.ai/tutorials/running-flux2-klein
- https://www.apatero.com/blog/flux-2-memory-optimization-62gb-vram-spike-fix-guide-2025
- https://apatero.com/blog/flux-2-24gb-vram-optimal-settings-guide
- https://www.runcomfy.com/comfyui-nodes/ComfyUI/VAEDecodeTiled

---

## 2. Multi-Pass Generation (img2img Refinement)

**Difficulty:** Low | **Expected Improvement:** 10-20% edge sharpness

### Approach

Generate the atlas at full resolution with text-to-image, then run a second img2img pass at low denoise strength (0.15-0.35) to sharpen edges without destroying the layout.

### Implementation Options

**A. FLUX.2 img2img (native):**
- Use the same model with image-to-image mode, providing the first-pass atlas as input.
- Denoise strength 0.2-0.3 preserves composition while re-rendering details.
- Prompt should emphasize sharp edges, clean contours, high contrast black on white.
- FLUX.2 Redux mechanism re-diffuses only what needs changing while preserving composition, lighting, and colors.

**B. Dedicated upscale + refine:**
- Ref2Font already has an experimental flux_upscale.py script (noted as may not improve quality yet).
- Could be replaced with a targeted img2img pass using ControlNet (canny edge) to lock down the structure.

### Parameters to tune

- denoise_strength: 0.15 (subtle cleanup) to 0.35 (significant resharpening). Above 0.4 risks layout destruction.
- steps: 15-20 is sufficient for refinement (vs 28-50 for generation).
- cfg_scale: Keep moderate (3.5-5.0 for FLUX.2) to avoid over-sharpening artifacts.

**Risk:** At higher denoise, the model may alter glyph shapes. Always validate with OCR or visual diff after refinement.

Sources:
- https://learn.rundiffusion.com/img2img-docs/
- https://github.com/SnJake/Ref2Font
---

## 3. Better Vectorization Than scikit-image Contour Tracing

**Difficulty:** Low-Medium | **Expected Improvement:** 20-40% cleaner curves

This is likely the single highest-impact change. scikit-image find_contours produces polygon approximations that need heavy simplification. Purpose-built tracers produce better Bezier curves natively.

### Option Comparison

| Tool | Curve Quality | Speed | Color Support | Font Suitability | Install |
|------|-------------|-------|---------------|-----------------|---------|
| **Potrace** | Excellent (sharp, clean) | Fast | Monochrome only | Best for B&W glyphs | pip install pypotrace or system binary |
| **VTracer** (Rust) | Very good | Very fast O(n) | Full color | Good with colormode bw | pip install vtracer |
| **AutoTrace** | Moderate (artifacts) | Moderate | Limited | Avoid -- visible artifacts | System package |
| **DiffVG** | Best (optimized Bezier) | Slow (GPU) | N/A (optimization) | Excellent as post-process | Build from source |
| scikit-image | Basic (polygon) | Fast | N/A | Current baseline, weakest | Already installed |

### Recommended: Potrace for Primary Tracing

Potrace is the industry standard for monochrome bitmap-to-vector. It outputs optimized Bezier curves directly, which is exactly what font glyphs need. It was literally designed with font conversion as a use case.

Key parameters:
- turdsize: Suppress speckles of this many pixels (2-5 for clean glyphs)
- alphamax: Corner threshold (1.0 = smooth curves, 0.0 = sharp corners)
- opticurve=True: Optimize curves by fitting longer Bezier segments
- opttolerance: Tolerance for curve optimization (0.2 is good default)

### Alternative: VTracer for Speed and Flexibility

VTracer has Python bindings via PyO3 (pip install vtracer since v0.6). Relevant settings for font work:
- colormode: bw (for font glyphs)
- mode: spline (for smooth curves)
- filter_speckle: 4 (remove small noise patches)
- corner_threshold: 60 degrees (lower = more corners preserved)
- hierarchical: stacked (more compact output)
- Presets available: bw, poster, photo
- Algorithm is O(n) versus Potrace O(n^2), significantly faster on large images.

### Advanced: DiffVG as Post-Optimization

After initial tracing (Potrace or VTracer), use DiffVG to further optimize the Bezier control points by minimizing the difference between the rasterized vector and the original raster glyph. This is a gradient-descent refinement step.

The PyTorch-SVGRender library wraps DiffVG with a clean API. The optimization loop:
1. Initialize SVG paths from Potrace output
2. Rasterize with DiffVG (differentiable)
3. Compute L2 loss against original raster glyph
4. Backpropagate and update control points
5. Repeat for 100-500 iterations

This adds ~1-3 seconds per glyph on GPU but produces mathematically optimal curves.

**Bezier Splatting** (2025) is a newer alternative to DiffVG achieving an order-of-magnitude speedup for differentiable rendering.

Sources:
- https://potrace.sourceforge.net/potrace.pdf
- https://github.com/visioncortex/vtracer
- https://www.aisvg.app/blog/image-to-svg-converter-guide
- https://github.com/ximinng/PyTorch-SVGRender
- https://people.csail.mit.edu/tzumao/diffvg/
- https://arxiv.org/html/2503.16424v3

---

## 4. ControlNet / IP-Adapter for FLUX.2 Style Control

**Difficulty:** Medium | **Expected Improvement:** 15-30% style consistency

### Current State (2025-2026)

XLabs-AI provides both ControlNet and IP-Adapter for FLUX:

**ControlNet for FLUX:**
- Canny edge ControlNet can lock down glyph structure while allowing style variation.
- Keep strength above 0.7 for reliable structural control.
- Use case: provide a template grid layout as canny input to guarantee character positioning.

**IP-Adapter for FLUX:**
- Trained at 512x512 for 50k steps by XLabs.
- Keep weight below 0.5 -- higher values degrade image quality.
- Works for transferring style from a reference font image.

### Known Limitations

- IP-Adapter + ControlNet together cause consistency issues: ControlNet stops working properly when IP-Adapter is active at high weights.
- IP-Adapter is described as not very powerful yet for style transfer in its current FLUX implementation.
- These tools were built for FLUX.1; FLUX.2 compatibility may need verification.

### Practical Application for Font Atlases

The most viable approach: use Canny ControlNet to enforce the grid layout, combined with the Ref2Font LoRA for style. Skip IP-Adapter until the FLUX.2 native version matures.

Workflow:
1. Generate a clean reference grid (black lines on white) showing cell boundaries
2. Extract canny edges
3. Feed as ControlNet input alongside the Ref2Font prompt
4. ControlNet enforces cell alignment; LoRA handles font style

Sources:
- https://huggingface.co/XLabs-AI/flux-ip-adapter-v2/discussions/19
- https://openart.ai/workflows/odam_ai/100-flux-native-controlnet-ipadapter-style-transfer/u55OSJqYClitcKGAqQ8B
- https://www.digitalcreativeai.net/en/post/detailed-usage-flux-1-controlnet-ip-adapter-comfyui
---

## 5. Multi-Seed Ensemble (Generate Multiple, Pick Best Per-Character)

**Difficulty:** Low | **Expected Improvement:** 15-25% consistency

### Approach

Generate N atlases (N=3-8) with different seeds, then extract individual glyph cells and select the best version of each character. This is a brute-force quality improvement that requires no model changes.

### Selection Criteria

**A. OCR confidence scoring:**
- Run each extracted glyph through an OCR model (e.g., TrOCR, PaddleOCR).
- Select the glyph with highest confidence for the correct character.
- Rejects malformed or ambiguous glyphs automatically.

**B. Structural similarity (SSIM):**
- Render the target character in a reference font at matching size.
- Compute SSIM between each candidate and the reference.
- Select highest SSIM per character.

**C. Edge sharpness scoring:**
- Compute Laplacian variance on each glyph cell.
- Higher variance = sharper edges = cleaner tracing.

**D. Hybrid scoring:**
- Weighted combination: 0.5 * OCR_conf + 0.3 * SSIM + 0.2 * edge_sharpness.

### Cost

- 5 atlases at 1280x1280 with FP8: ~5 minutes total on a 4090.
- At 2048x2048: ~8-10 minutes for 5 atlases.
- Selection scoring is negligible (less than 1s total).

### Research Context

Academic work on font generation confirms this general pattern. MX-Font (ICCV 2021) uses multiple localized experts to capture different glyph components. Component-style methods decompose font style into parts extracted from different reference instances.

Sources:
- https://openaccess.thecvf.com/content/ICCV2021/papers/Park_Multiple_Heads_Are_Better_Than_One_Few-Shot_Font_Generation_With_ICCV_2021_paper.pdf
- https://openaccess.thecvf.com/content/CVPR2024/papers/Fu_Generate_Like_Experts_Multi-Stage_Font_Generation_by_Incorporating_Font_Transfer_CVPR_2024_paper.pdf

---

## 6. Raster Post-Processing Before Tracing

**Difficulty:** Low | **Expected Improvement:** 10-30% tracing quality

### Pipeline: Raster Cleanup Before Vectorization

The quality of vectorization is directly limited by the quality of the input raster. A preprocessing pipeline between atlas generation and contour tracing can significantly improve results.

### Step 1: Super-Resolution Upscaling

Upscale extracted glyph cells 2-4x before tracing. More pixels = smoother curves during tracing.

| Model | Quality (1-10) | Speed | VRAM | Best For |
|-------|---------------|-------|------|----------|
| Real-ESRGAN | 9.2 | 6s | ~2 GB | General upscaling, fast |
| SwinIR | 9.7 | 12s | ~4 GB | Maximum quality |
| AESRGAN | 9.0 | 4s | ~1.5 GB | Fastest, slightly lower quality |

**Caveat:** Some SR models struggle with font/text content, particularly italicized text. Test with your specific glyph style before committing.

**Recommendation:** Real-ESRGAN with the realesrgan-x4plus model. 4x upscale turns a 160x142 glyph cell into 640x568 -- much more detail for the tracer.

### Step 2: Binarization (Otsu or Adaptive)

Convert to clean black/white before tracing. Otsu thresholding works well for generated atlases with good contrast. Use adaptive thresholding for atlases with uneven background.

### Step 3: Morphological Cleanup

Key operations:
- **Closing** (dilate then erode): fills small gaps and holes in glyph strokes.
- **Opening** (erode then dilate): removes small noise specks outside glyphs.
- **Morphological gradient** (dilation - erosion): extracts clean edges.
- Use an elliptical kernel (3x3 or 5x5) for smooth results; rectangular for sharper corners.

### Step 4: Edge Enhancement (Optional)

For particularly soft/blurry glyphs, apply unsharp masking before binarization.

### Full Preprocessing Pipeline Order

1. Extract glyph cell from atlas
2. Super-resolution upscale (4x with Real-ESRGAN)
3. Convert to grayscale
4. Unsharp mask (if blurry)
5. Otsu binarization
6. Morphological close (fill gaps) then open (remove specks)
7. Feed to Potrace/VTracer

Sources:
- https://github.com/xinntao/Real-ESRGAN
- https://github.com/JingyunLiang/SwinIR
- https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html
- https://www.apatero.com/blog/ai-image-upscaling-battle-esrgan-vs-beyond-2025
---

## 7. Training a Custom LoRA on Top of Ref2Font

**Difficulty:** Medium-High | **Expected Improvement:** 25-50% for targeted styles

### Approach A: Fine-Tune Ref2Font LoRA Further

Stack a second LoRA on top of Ref2Font, trained on high-quality font atlases in your target style. This is the FLUX-Font approach.

**FLUX-Font architecture (ACPR 2025):**
- Uses two separate LoRA modules: one for glyph structure, one for style.
- Incorporates a character-aware loss via OCR to ensure structural integrity during training.
- Converges in 500-1000 steps (vs 3000-5000 for SDXL LoRAs) due to FLUX flow-matching architecture.

### Training Setup

**Tools:** Kohya_ss (gold standard), SimpleTuner, or ai-toolkit.

**Dataset preparation:**
- Render 20-50 high-quality atlases of your target font style using professional fonts.
- Each atlas should follow the exact same 8x9 grid layout as Ref2Font.
- Include caption files describing the style.
- Augment with slight rotations, contrast variations.

**Recommended parameters for FLUX.2 LoRA training:**
- Learning rate: 1e-4 to 5e-4 (FLUX trains faster than SDXL)
- Rank: 16-32 (higher rank = more capacity for fine style details)
- Steps: 500-1500
- Resolution: 1280x1280 (match Ref2Font training resolution)
- Optimizer: AdamW8bit or Prodigy (adaptive)
- Mixed precision: bf16 or fp16
- VRAM: ~20-24 GB for rank 16-32 on FLUX.2 klein

**Estimated training time:** 2-4 hours on a consumer GPU (4090).

### Approach B: Train From Scratch (Higher Effort)

If Ref2Font base quality is limiting, train a new LoRA from scratch on FLUX.2-klein-9B with a curated dataset of professional font atlases. Requires 100-500 atlas images minimum.

### Approach C: LoRA Merging

Merge Ref2Font with a style-specific LoRA at different weights to blend capabilities:
- Ref2Font at 0.7 (grid layout knowledge) + Style LoRA at 0.3 (aesthetic refinement)
- Tune the merge ratio empirically.

Sources:
- https://link.springer.com/chapter/10.1007/978-981-95-4395-3_23
- https://apatero.com/blog/lora-training-best-practices-flux-stable-diffusion-2025
- https://apatero.com/blog/flux-2-lora-training-complete-guide-2025
- https://civitai.com/articles/7044/font-model-training-with-flux-training-diary
- https://modal.com/blog/fine-tuning-flux-style-lora

---

## Priority Ranking (Impact vs Effort)

| Priority | Improvement | Difficulty | Impact | Standalone? |
|----------|------------|------------|--------|-------------|
| 1 | **Replace scikit-image with Potrace** | Low | 20-40% | Yes |
| 2 | **Raster preprocessing pipeline** | Low | 10-30% | Yes, stacks with 1 |
| 3 | **Multi-seed ensemble selection** | Low | 15-25% | Yes |
| 4 | **2048x2048 resolution** | Low-Med | 15-25% | Yes, test LoRA compat first |
| 5 | **img2img refinement pass** | Low | 10-20% | Yes, stacks with 4 |
| 6 | **ControlNet grid enforcement** | Medium | 15-30% | Yes |
| 7 | **Custom LoRA training** | Med-High | 25-50% | Needs dataset |
| 8 | **DiffVG curve optimization** | Medium | 5-15% on top of Potrace | Needs GPU, stacks with 1 |

**Recommended implementation order:** 1 > 2 > 3 > 4 > 5. These five changes stack multiplicatively and require no model training. Items 6-8 are worthwhile but require more infrastructure.

**Combined expected improvement (items 1-5):** Rough estimate 50-70% quality uplift over current pipeline, primarily from better vectorization and higher input quality to the tracer.