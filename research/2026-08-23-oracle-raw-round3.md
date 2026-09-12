# Oracle raw report, round 3: benchmarks and operational detail (2026-08-23)

Unedited 20-Smith / 2-chain run, pointed at build-blocking gaps rather than
model discovery. Synthesis in `2026-08-23-round3-the-numbers-that-were-missing.md`.

---

============================================================
## Chain A — Anderson Report
============================================================

Below is the fully organized Anderson output — all signal preserved, nothing compressed, ready for Opus.

---

# SMITH CHAIN A — ORGANIZED FINDINGS FOR OPUS SYNTHESIS
**Anderson pass · 2026-08-23 · Triage applied: DEDUP · RECENCY · AGREE · DISAGREE · GAPS · CORRECT**

---

## META-NOTE ON SCOPE

Ten Smiths cover: text rendering benchmarks (#1, #8), Z-Image img2img mechanics (#2), Z-Image GGUF/FP8 quantization (#3), Z-Image prompt format (#4), Z-Image training data (#5), Qwen-Image-Edit prompt patterns (#6), Qwen-Image-Edit failure modes (#7), ERNIE-Image conditioning (#8), structure-preservation head-to-head (#9), and August 2026 new open-weight models (#10).

---

---

# SECTION 1: TEXT RENDERING BENCHMARKS

## 1.1 LongTextBench Scores

**Sources:** Smith #1 (Nov 2025 paper data), Smith #8 (ERNIE-Image). **AGREE** across both Smiths on overlapping values. Table sorted by LongText-EN descending.

| Model | LongText-EN | LongText-ZH | Source Date | Confidence | Smith |
|---|---|---|---|---|---|
| ERNIE-Image | 0.973 overall* | 0.973 overall* | May 25, 2026 | HIGH | #1, #8 |
| JoyAI-Image | 0.963 | 0.963 | 2026 (no exact date) | LOW | #1 only |
| Qwen-Image 2.0 | 0.943 | 0.946 | May 11, 2026 | HIGH | #1 |
| Ovis-Image (7B) | 0.922 | 0.964 | Nov 2025 | MEDIUM | #1 only |
| Z-Image | 0.935 | 0.936 | Nov 27, 2025 | HIGH | #1 |
| Z-Image-Turbo | 0.917 | 0.926 | Nov 27, 2025 | HIGH | #1 |

*ERNIE-Image EN/ZH breakdown not disclosed in paper; 0.973 is overall combined.
**DEDUP:** Paper value 0.973 vs GitHub value 0.9733 — same number, rounding only. Not a genuine dispute.
**RECENCY note:** ERNIE-Image and Qwen-Image 2.0 (both May 2026) are newer than Z-Image (Nov 2025). All rankings are models' own self-reported results.

---

## 1.2 CVTG-2K Word Accuracy Scores

**Source:** Smith #1.

| Model | Avg Word Accuracy | CLIP Score | Source Date | Confidence | Smith |
|---|---|---|---|---|---|
| Ovis-Image (7B) | 0.920 | not reported | Nov 2025 | MEDIUM | #1 only |
| Z-Image | 0.8671 | top-ranked* | Nov 27, 2025 | HIGH | #1 |
| Z-Image-Turbo | 0.8585 | 0.8048 (highest all models) | Nov 27, 2025 | HIGH | #1 |
| Qwen-Image 2.0 | 0.829** | not reported | May 11, 2026 | HIGH | #1 |
| ERNIE-Image | NOT REPORTED | NOT REPORTED | — | — | #1, #8 |

*Smith #1 says "Z-Image: highest score" on CVTG-2K. **CORRECT [C1]:** Same Smith's comparison table shows Ovis-Image (7B) at 0.920, which exceeds Z-Image's 0.8671. "Highest score" appears to apply only to models evaluated in the Z-Image paper itself; Ovis-Image may not have been in that baseline set.
**Qwen-Image 2.0 regional breakdown: 0.837 (2 regions), 0.836 (3 regions), 0.831 (4 regions), 0.816 (5 regions); average ~0.829. Earlier report of 0.8288 — same run, rounding. [arXiv 2605.10730]

---

## 1.3 Z-Image Internal Typography Benchmarks

**Source:** Smith #5. [arXiv 2511.22699, Nov 27, 2025]
- English Text Score: **0.987** | Chinese Text Score: **0.988** | HIGH
- These are Z-Image's own internal typography metrics, **distinct from** LongTextBench and CVTG-2K.

---

## 1.4 Other Benchmarks (non-text-rendering)

**Source:** Smith #8. [arXiv 2605.25347]
- ERNIE-Image GENEval: **0.8856** | HIGH
- No GENEval scores for Z-Image or Qwen-Image 2.0 in any Smith.

---

## 1.5 ImgEdit Benchmark (Image Editing Quality, not text rendering)

**Source:** Smith #9. [arXiv 2511.22699, Nov 2025] HIGH.
- Z-Image-Edit: **4.30** (combined instruction completion + visual quality)
- Qwen-Image-Edit: **4.27**
- Difference: 0.03 — effectively tied.
- **NOTE:** "Z-Image-Edit" here is presented as a distinct editing model, not ZImageImg2ImgPipeline. See **GAP G1**.

## 1.6 Qwen-Image-Edit 2511 Structure Metrics (ImgEdit benchmark)

**Source:** Smith #9. [arXiv 2604.05180 — MIRAGE paper] HIGH.
- LPIPS: **0.066** (lower = better perceptual similarity)
- SSIM: **0.811** (higher = better structural similarity)
- PSNR: **22.424 dB**
- Z-Image-Edit equivalent metrics: **NOT DISCLOSED**. See **GAP G3**.

---

## 1.7 FLUX Text Rendering

**Source:** Smith #1.
- No CVTG-2K or LongTextBench official scores exist for FLUX.
- TextCrafter shows 45% OCR accuracy improvement over FLUX. [arXiv 2503.23461, Mar 2025] MEDIUM
- FLUX.2-dev: 94.9 on CoreBench (different metric, not comparable). MEDIUM
- Conclusion: FLUX was not formally evaluated on text-rendering-specific benchmarks.

---

## 1.8 Orphaned Table Entries (Smith #1 only, LOW confidence)

- **JoyAI-Image** — 0.963/0.963 LongTextBench. No citation, no date specificity, no dedicated Smith.
- **Ovis-Image (7B)** — 0.922/0.964 LongTextBench, 0.920 CVTG-2K, Nov 2025. MEDIUM confidence. No dedicated Smith.
- Both flagged for Opus: verify or treat as unconfirmed context.

---

---

# SECTION 2: Z-IMAGE MODEL FAMILY

## 2.1 Core Architecture & Specs

**Sources:** Smith #1, #3, #5, #9. **AGREE** across all Smiths.

| Attribute | Value | Confidence | Source |
|---|---|---|---|
| Full name | Tongyi-MAI Z-Image / Z-Image-Turbo (Alibaba Tongyi Laboratory) | HIGH | Multiple |
| Architecture | Scalable Single-Stream Diffusion Transformer (S3-DiT) | HIGH | arXiv 2511.22699 |
| Parameters | 6B | HIGH | arXiv 2511.22699 |
| Training cost | 314K H800 GPU hours ≈ $630K USD | HIGH | arXiv 2511.22699 |
| Model license | Apache 2.0 (weights only) | HIGH | GitHub Tongyi-MAI/Z-Image |
| Paper date | November 27, 2025 | HIGH | arXiv 2511.22699 |

- HuggingFace: https://huggingface.co/Tongyi-MAI/Z-Image-Turbo
- GitHub: https://github.com/Tongyi-MAI/Z-Image
- Blog: https://tongyi-mai.github.io/Z-Image-blog/

---

## 2.2 Training Data

**Source:** Smith #5. Unique to that Smith. [arXiv 2511.22699, Nov 27, 2025]

### Disclosed:
- Training corpus: "large-scale internal copyrighted collections" | HIGH
- Approach: real-world data (NOT synthetic data distillation) | HIGH
- Five caption types: long captions, medium captions, short captions, tags, simulated user prompts | HIGH
- Caption components: world knowledge, OCR results (kept in original language, not translated) | HIGH
- Curation methods: cross-modal embedding deduplication, rule-based filtering (resolution / caption length / visual complexity), PageRank-based pruning (unvisualizable concepts), human feedback integration, Active Curation Engine, Data Profiling Engine, World Knowledge Topological Graph | HIGH
- Synthetic captions: Z-Captioner generates bilingual multi-level captions | HIGH
- Self-play loop: Z-Image-Turbo generates synthetic artistic text images from Z-Captioner output | MEDIUM
- Bilingual text rendering: Chinese calligraphic styles + English | HIGH

### NOT Disclosed (HIGH certainty of absence):
- Dataset size (image count), source breakdown, font count/categories/licensing, LAION-5B usage (mentioned in related work only — not claimed as training source), data licensing breakdown, any dataset release plan.
- Reproducibility gap explicitly flagged in arXiv paper: dataset, knowledge graph, captioner training data, reward model, and active curation tooling all unreleased.

---

---

# SECTION 3: Z-IMAGE IMG2IMG PIPELINE

## 3.1 `strength` Parameter

**Source:** Smith #2. [HuggingFace diffusers pipeline code, Jan 2025 latest commit] HIGH.

- **Type:** float | **Range:** 0.0–1.0 | **Default:** 0.6
- **Validation:** `ValueError` raised if `strength < 0` or `strength > 1` (line 512–513)
- **Docs:** https://huggingface.co/docs/diffusers/api/pipelines/z_image
- **Source code:** github.com/huggingface/diffusers/blob/main/src/diffusers/pipelines/z_image/pipeline_z_image_img2img.py

**Mechanism** (from docstring, lines 457–463):
Controls noise added to input image via `scheduler.scale_noise()` (line 285). Timestep range: `init_timestep = min(num_inference_steps × strength, num_inference_steps)` (line 359). At `strength=1.0`: maximum noise, denoising runs full iterations, original image ignored. At `strength=0.0`: no noise, output ≈ input.

**Practical ranges** (MEDIUM — consistent across 2025–2026 blog guides):

| Range | Effect |
|---|---|
| 0.10–0.25 | Light polish: artifact removal, gentle lighting/sharpening |
| 0.30–0.45 | Strong refinement: restyle while preserving composition/pose |
| 0.50–0.65 | Major changes: significant transformation, some compositional drift |
| 0.70+ | Almost new image; >0.85 approaches pure text-to-image |
| **0.35–0.45** | **Recommended starting point**; adjust in 0.05 increments |

## 3.2 No Separate Denoise Parameter

**Source:** Smith #2. Pipeline does NOT expose a `denoise_strength` parameter. Control is exclusively via `strength`.

## 3.3 Related Parameters

**Source:** Smith #2.
- `num_inference_steps` (int, default=50): denoising iterations
- `guidance_scale` (float, default=5.0): text prompt adherence — **see CORRECT C2 for Turbo-specific override**
- `cfg_normalization` (bool, default=False): CFG renormalization flag
- `cfg_truncation` (float, default=1.0): CFG truncation threshold

## 3.4 Official Code Example (img2img)

**Source:** Smith #2. [github.com/huggingface/diffusers/blob/main/docs/source/en/api/pipelines/z_image.md]
```python
import torch
from diffusers import ZImageImg2ImgPipeline
from diffusers.utils import load_image

pipe = ZImageImg2ImgPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", dtype=torch.bfloat16)
pipe.to("cuda")

url = "https://raw.githubusercontent.com/CompVis/stable-diffusion/main/assets/stable-samples/img2img/sketch-mountains-input.jpg"
init_image = load_image(url).resize((1024, 1024))

prompt = "A fantasy landscape with mountains and a river, detailed, vibrant colors"
image = pipe(
    prompt,
    image=init_image,
    strength=0.6,
    num_inference_steps=8,
    guidance_scale=0.0,  # Turbo-specific; consistent with Smith #4
    generator=torch.Generator("cuda").manual_seed(42),
).images[0]
image.save("zimage_img2img.png")
```

---

---

# SECTION 4: Z-IMAGE QUANTIZATION & LOADING

## 4.1 Framework Support Matrix

**Source:** Smith #3.

| Framework | Formats Supported | VRAM (BF16 / FP8 / GGUF Q4) | Notes |
|---|---|---|---|
| Diffusers (PyTorch) | BF16, FP8 | 14–16 GB / 8 GB / — | FP8 requires NVIDIA TE + RTX 40-series |
| ComfyUI | BF16, FP8, GGUF | 14–16 GB / 8 GB / 4–5 GB | GGUF needs ComfyUI-GGUF node (city96) |
| stable-diffusion.cpp | GGUF only | — / — / 4–6 GB | Multi-platform: CUDA, Vulkan, Metal, CPU |

ComfyUI model folder layout: GGUF → `models/unet/` | Text encoder (Qwen3) → `models/text_encoders/` | VAE → `models/vae/`
- Official workflow: github.com/Comfy-Org/workflow_templates/blob/main/templates/image_z_image_turbo.json
- Docs: docs.comfy.org/tutorials/image/z-image/z-image-turbo

stable-diffusion.cpp components required: GGUF model + `ae.safetensors` VAE + Qwen3 4B Instruct GGUF
- Repo: https://github.com/leejet/stable-diffusion.cpp
- Docs: github.com/leejet/stable-diffusion.cpp/blob/master/docs/z_image.md

## 4.2 GGUF Quantized Repositories

**Source:** Smith #3. Sizes MEDIUM confidence (repo listings).

| Repo | Total Size | Quantization Levels | URL |
|---|---|---|---|
| **leejet/Z-Image-Turbo-GGUF** (OFFICIAL) | 29.7 GB | Q2_K, Q3_K, Q4_0, Q4_K, Q5_0, Q6_K, Q8_0 | hf.co/leejet/Z-Image-Turbo-GGUF |
| jayn7/Z-Image-Turbo-GGUF | 41.4 GB | Q3_K_S/M, Q4_K_S/M, Q5_K_S/M, Q8_0 | hf.co/jayn7/Z-Image-Turbo-GGUF |
| unsloth/Z-Image-Turbo-GGUF | — | Q2_K–Q8_0, BF16, F16 | hf.co/unsloth/Z-Image-Turbo-GGUF |
| vantagewithai/Z-Image-Turbo-GGUF | — | Q3_K, Q4_0, Q4_1, Q4_K_M/S, BF16 | hf.co/vantagewithai/Z-Image-Turbo-GGUF |
| wbruna/Z-Image-Turbo-sdcpp-GGUF | — | Multiple (legacy/experimental) | hf.co/wbruna/Z-Image-Turbo-sdcpp-GGUF |

File sizes (leejet repo, MEDIUM): Q2_K: 2.59 GB | Q3_K: 3.14 GB | Q4_0: 3.68 GB | Q4_K: 3.86 GB | Q5_0: 4.54 GB | Q6_K: 5.26 GB | Q8_0: 6.58 GB

## 4.3 FP8 / INT8 Quantized Repositories

**Source:** Smith #3. HIGH on repo existence.

| Repo | Quantization | URL |
|---|---|---|
| drbaph/Z-Image-Turbo-FP8 (most used) | FP8_E5M2, FP8_E4M3FN | hf.co/drbaph/Z-Image-Turbo-FP8 |
| ykarout/Z-Image-Turbo-FP8-Full | FP8_E5M2, FP8_E4M3FN | hf.co/ykarout/Z-Image-Turbo-FP8-Full |
| tsqn/Z-Image-Turbo_fp8_comfyui | FP8 (ComfyUI-optimized) | hf.co/tsqn/Z-Image-Turbo_fp8_comfyui |
| mzbac/Z-Image-Turbo-8bit | INT8 | hf.co/mzbac/Z-Image-Turbo-8bit |
| TheCodingBug/Z-Image-Turbo-int8 | INT8 | hf.co/TheCodingBug/Z-Image-Turbo-int8 |

FP8 format note: E4M3FN (better quality) vs E5M2 (faster inference). drbaph includes both.

## 4.4 VRAM & Performance Summary

**Source:** Smith #3. HIGH on VRAM figures; MEDIUM on speed/quality deltas.

| Format | VRAM | Speed vs BF16 | Quality vs BF16 | Frameworks |
|---|---|---|---|---|
| BF16 | 14–16 GB | Baseline | 100% | Diffusers, ComfyUI |
| FP8 | 8 GB | ~30% faster | 98–99% | Diffusers, ComfyUI |
| INT8 | 8 GB | ~30% faster | 98–99% (research: exceeds FP8) | ComfyUI |
| GGUF Q4_K | 4–5 GB | ~40% faster | 96–97% | sd.cpp, ComfyUI-GGUF |
| GGUF Q3_K | 3.5–4 GB | ~50% faster | 94–95% | sd.cpp, ComfyUI-GGUF |
| GGUF Q2_K | 2.5–3 GB | ~60% faster | 90–92% | sd.cpp, ComfyUI-GGUF |

## 4.5 Supported GGUF Quantization Types

**Source:** Smith #3. HIGH. Q2_K, Q3_K_S/M/L, Q4_0, Q4_1, Q4_K_S/M, Q5_0, Q5_1, Q5_K_S/M, Q6_K, Q8_0, BF16, F16, I-Quants (vantagewithai variant). `"bne4"` quantization: not found anywhere — likely typo or unreleased.

## 4.6 Known Issues: Quantization & Loading

**Source:** Smith #3.

**Issue A — Ollama FP8 Loader Failure** | MEDIUM confidence
Ollama v0.16.0/v0.16.1 fails to load FP8 model; works on v0.15.6. Root cause: text encoder tensor mapping regression in MLX runner. Workaround: use Diffusers/llama.cpp directly, or downgrade Ollama to v0.15.6. [github.com/ollama/ollama/issues/14249]
**ANDERSON FLAG — see CORRECT C3:** Ollama is primarily an LLM framework. Its use for diffusion model inference is atypical; this issue may refer specifically to loading the Qwen3 text encoder component within a hybrid pipeline. Opus should verify.

**Issue B — LoRA Compatibility** | HIGH confidence
SDXL-trained LoRAs fail entirely. Nunchaku v1.1.0 cannot load any LoRAs (PR fix in progress, Aug 2026). Only Z-Image-architecture LoRAs work. [apatero.com blog]

**Issue C — ComfyUI FP16 Compute Error** | MEDIUM confidence
Z-Image Base (parent model) fp16 compute failures on some hardware. Specific FP8/Turbo impact unclear. [github.com/Comfy-Org/ComfyUI/issues/12176]

**Issue D — FP8 Quality Degradation** | HIGH confidence
Subtle quality loss in fine details and color precision vs. BF16. Research indicates INT8 outperforms FP8 for diffusion models. [apatero.com blog]

## 4.7 Recommended Setup by Use Case

**Source:** Smith #3.
1. **Ease-of-use:** drbaph/Z-Image-Turbo-FP8 + ComfyUI official workflow | 8 GB VRAM
2. **Memory-constrained:** leejet/Z-Image-Turbo-GGUF Q4_K or Q3_K + stable-diffusion.cpp | 4–5 GB
3. **Quality-first:** Tongyi-MAI/Z-Image-Turbo (BF16) or drbaph FP8 + Diffusers | 8–16 GB

---

---

# SECTION 5: Z-IMAGE PROMPTING

## 5.1 Language & Tone

**Source:** Smith #4. MEDIUM. [deAPI.ai, Fliki.ai blogs, 2025–2026]
- Natural language sentences preferred — NOT tag-soup/comma-separated keywords.
- Write like a film director giving shot instructions, not random adjectives.

## 5.2 Negative Prompts

**Source:** Smith #4. HIGH. Z-Image-Turbo does **NOT** support negative prompts. All exclusions must be embedded in the main prompt using "without X," "avoid Y."

## 5.3 Prompt Length

**Source:** Smith #4. MEDIUM.
- Sweet spot: 80–250 words [Fliki.ai]
- Acceptable: 30–120 words for simpler scenes [deAPI.ai]
- Turbo text encoder handles hundreds of words if needed [deAPI.ai]

## 5.4 Six-Part Prompt Formula

**Source:** Smith #4. MEDIUM. [z-image.win, Fliki.ai, deAPI.ai]

| Part | Content |
|---|---|
| 1. Subject | Who/what, age, clothing, materials, one non-idealized feature per person |
| 2. Scene | Where/when, max 1–2 supporting props |
| 3. Composition | Camera angle, framing, lens (e.g., "85mm f/1.4," "medium shot") |
| 4. Lighting | Direction, color temperature, time of day — **stated as the single most impactful element** |
| 5. Style | Pick ONE (e.g., "analog film photograph," "cel-shaded anime," "oil painting") — mixing degrades output |
| 6. Constraints | Exact text requirements, no-logo rules, anatomy rules |

## 5.5 CFG (Guidance Scale) — Turbo-Specific

**Source:** Smith #4. HIGH. [HuggingFace diffusers docs; AI/ML API docs; deAPI.ai]

| Value | Context | Reasoning |
|---|---|---|
| **0.0** | Theoretically optimal | Distilled model; CFG baked in during training |
| **1.5–2.0** | ComfyUI practical | Slight real-world adherence boost |
| 6–9 | **INCOMPATIBLE** | Standard SD values degrade Turbo output |

Rule: If a prompt isn't landing, change wording or seed — do **not** raise CFG.

**DEDUP with Smith #2:** Smith #2 states `guidance_scale` default=5.0 for ZImageImg2ImgPipeline. This is the Base model pipeline default. For Turbo, use 0.0. The official code example in Smith #2 itself uses `guidance_scale=0.0`. Both are correct for their respective contexts. See **CORRECT C2**.

## 5.6 Inference Steps — Turbo-Specific

**Source:** Smith #4. HIGH. [HuggingFace Tongyi-MAI model card; AI/ML API]
- Optimal: **8–9 steps** (default)
- Range: 8–12 steps; increase only if obvious noise visible
- Native resolution: **1024×1024**; 768 or 512 acceptable for drafts
- Enables sub-second latency at 8 steps

## 5.7 Reference URLs

- HuggingFace Pipeline Docs: https://huggingface.co/docs/diffusers/api/pipelines/z_image (HIGH — official)
- Tongyi-MAI Model Card: https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/blob/main/README.md (HIGH)
- AI/ML API Docs: https://docs.aimlapi.com/api-references/image-models/alibaba-cloud/z-image-turbo (HIGH)
- GitHub Prompting Guide: https://gist.github.com/illuminatianon/c42f8e57f1e3ebf037dd58043da9de32 (MEDIUM — community)
- Z-Image Prompt Formula: https://www.z-image.win/blog/z-image-prompt-formula-6-part-template (MEDIUM)

---

---

# SECTION 6: QWEN-IMAGE-EDIT PROMPT PATTERNS

## 6.1 Core Principles

**Source:** Smith #6. HIGH. [deAPI.ai, each::labs, Qwen official blog — 2026]
1. **Lead with preservation** — state what to protect BEFORE stating the change. Prevents aggressive drift.
2. **One operation per API call** — chain complex edits sequentially (output of step N = input of step N+1).
3. **Use action verbs**, not descriptive sentences.
4. **Specify exact style/material labels** — "Van-Gogh style" beats "artistic"; "brushed metal" beats "shiny."
5. **End with explicit preservation clause** — "keep all other elements unchanged."

## 6.2 Documented Patterns

**Source:** Smith #6.

### Pattern 1: Preservation-First (Highest Confidence)
Structure: `[Preservation clause] + [Action] + [Constraints]`
Example: *"Keep the product identical, replace the background with a textured concrete wall illuminated by soft side light."* | HIGH | [deAPI.ai, each::labs, Jan 2026]

### Pattern 2: Action + Target + Constraints
*"Replace the product material with brushed metal, keep the structure and lighting direction unchanged."* | HIGH | [deAPI.ai, qw-image.com, 2026]

### Pattern 3: Style Transfer with Identity Preservation
Template: *"Transfer [Subject] into [Style], keeping [specific preserved elements]."*
- *"Transfer the portrait into Van-Gogh style, keeping facial features and pose identical."* | HIGH
- *"Transform the image into a 2D anime style poster with thick outlines and bold color blocks; preserve pose and outfit details."* | HIGH
[TeleStyleV2 GitHub; QwenStyle paper arXiv:2601.06202; getimg.ai — HIGH, Jan 2026]

### Pattern 4: Multi-Image Style Reference
Template: *"Style Transfer the style of [Source Image] to [Target Image], keeping content and characteristics of [Target Image]."* | HIGH | [TeleStyleV2, QwenStyle papers, Jan 2026]

### Pattern 5: Typography/Material Locking
Lock typography explicitly when editing text to prevent font drift.
*"Change the sign text from 'CAFÉ BELLA' to 'LIBRARY BAR'. Keep the same serif gold lettering, same font style, same vintage weathered patina, same sign placement and lighting."* | HIGH | [deAPI.ai — tested extensively]

## 6.3 Failure Modes

**Source:** Smith #6.

**Too much drift:**
- Missing preservation clause → model errs aggressive | HIGH
- Multiple operations in one prompt → use sequential chaining instead | HIGH
- Vague/descriptive instructions instead of action verbs | HIGH
- Extreme style transfer → identity loss; use intermediate styles or reference images | MEDIUM

**Too little change:**
- Over-specification of constraints can suppress desired edits | LOW (limited data)
- Remedy: gradually reduce preservation clauses, or start with a larger semantic change then refine

## 6.4 Semantic vs. Appearance Editing

**Source:** Smith #6. HIGH. [Official Qwen Blog: qwenlm.github.io/blog/qwen-image-edit/]

| Mode | Pixel behavior | Use cases | Instruction style |
|---|---|---|---|
| **Semantic** | Overall pixel changes allowed while maintaining semantic consistency | Style transfer, pose changes, object rotation | Focus on conceptual transformation |
| **Appearance** | All other regions must remain completely unchanged | Add/remove objects, lighting, color correction | Hyper-specific about what changes and what doesn't |

## 6.5 Negative Prompts

**Source:** Smith #6. HIGH. Qwen-Image-Edit's `negative_prompt` does **NOT** exclude content. Model was not trained for negative conditioning (unlike Stable Diffusion or FLUX). If using it at all, limit to 3–6 targeted failure-mode terms only (MEDIUM).

## 6.6 Documented Templates

**Source:** Smith #6. HIGH. [Aggregate: deAPI, each::labs, getimg.ai, 2026]

**Background Replacement:**
> "Keep the [subject] and their [pose/details] exactly as-is, but replace the background with [new background description], match the lighting direction and color temperature on the subject, preserve original shadows and keep all other elements unchanged."

**Material/Style Transfer:**
> "Transfer [subject] into [material/style], keeping [specific preserved elements — facial features, pose, composition], preserve [secondary elements — shadows, lighting direction], keep all other aspects identical."

**Text Editing:**
> "A [scene description] with [original text location and context]. Change [description of current text] to [exact new text in quotes]. Keep the [font characteristics], [styling], [weathering/effects], [placement], and [lighting] identical."

**Multi-Image:**
> "Replace the [element] of picture 1 with the [element] of picture 2, keeping picture [X]'s [specific attributes], keep the background/foreground/lighting/composition unchanged."

## 6.7 Reference URLs

**Source:** Smith #6.
- deAPI Prompting Guide (most comprehensive): https://deapi.ai/blog/qwen-image-edit-plus-prompting-guide-how-to-write-edit-instructions-that-actually-work | HIGH, 2026
- Official Qwen Blog: https://qwenlm.github.io/blog/qwen-image-edit/ | HIGH, official
- HuggingFace Model Card Discussion: https://huggingface.co/Qwen/Qwen-Image-Edit-2511/discussions/7 | HIGH
- QwenStyle Paper: https://arxiv.org/abs/2601.06202 | HIGH, Jan 2026
- TeleStyleV2: https://github.com/Tele-AI/TeleStyleV2 | https://arxiv.org/html/2606.20709v1 | HIGH, Jun 2026
- 26 Demo Cases Tutorial: https://github.com/FurkanGozukara/Stable-Diffusion/wiki/Qwen-Image-Edit-Full-Tutorial-26-Different-Demo-Cases-Prompts-and-Images-Pwns-FLUX-Kontext-Dev | HIGH
- each::labs Guide: https://www.eachlabs.ai/blog/what-and-how-you-can-edit-with-qwen-image-edit | HIGH, 2026

---

---

# SECTION 7: QWEN-IMAGE-EDIT FAILURE MODES

**Source:** Smith #7. Data currency: most reports 2025-12-30 to 2026-01-25, searched 2026-08-23. Resolution status as of Aug 2026 unknown — see **GAP G10**.

## 7.1 Black Image Generation — HIGH Severity

Trigger: Multiple inference runs in ComfyUI; unstable frequency (~run 15–25 of 40+ iterations).
RuntimeWarning: `"invalid value encountered in cast img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))"`
- Without LoRA: turns black at step 18/19 (of 20) or ~25 (of 40); subsequent runs also start black.
- Persists with custom nodes disabled.
- Affects both BF16 and FP8 mixed quantized versions.
- Platforms: ComfyUI on ROCm 7.2.0 + gfx1101; also NVIDIA GPUs.
- Sources: [github.com/Comfy-Org/ComfyUI/issues/11865, 2026-01-14 | github.com/ROCm/ROCm/issues/6028, 2026-01-25 | github.com/QwenLM/Qwen-Image/issues/68]
- Workaround: GPU clock underclocking (~50 MHz) reportedly stabilizes noisy outputs. Unclear if prevents black images entirely | LOW confidence, community-only.

## 7.2 Square Resolution Degradation — HIGH Severity

Trigger: Square aspect ratios — 1024×1024, 1288×1288.
Manifestations: washed-out or hallucinated background details during style transformations; general coherence loss; inconsistent prompt results. Tested across BF16 unquantized, quantized, with/without LoRAs — degradation persists in all configurations.
Source: [github.com/QwenLM/Qwen-Image/issues/243, 2025-12-30]
Mitigation: Use non-square aspect ratios (portrait/landscape) for production workflows | MEDIUM.

## 7.3 Perspective Synthesis Failure — MEDIUM Severity

Trigger: Perspective synthesis feature (integrated in 2511) on objects underexposed in training (e.g., cars).
Suspected cause: model undertrained on multi-view imagery for certain object classes.
Source: [github.com/QwenLM/Qwen-Image/issues/242, 2025-12-30]
Mitigation: None formally documented.

## 7.4 Torchvision Dependency Error — MEDIUM Severity

Error: `"Qwen2VLVideoProcessor requires the Torchvision library but it was not found."`
Affected: oobabooga/textgen integration; some diffusers integrations. [oobabooga/textgen #7552]
Mitigation: Install torchvision from PyTorch site matching PyTorch/CUDA version; restart runtime.

## 7.5 Multi-Image Input Order Confusion — MEDIUM Severity

Trigger: Multi-image workflows referencing "image 1" vs "image 2" in prompt.
Manifestation: Model maps images incorrectly relative to prompt references.
Source: [github.com/QwenLM/Qwen-Image/issues/169 — older issue number; resolution in 2511 unclear]
Mitigation: Swap input image order in workflow if output doesn't match prompt intent.

## 7.6 Quantization/Format Loading Errors — LOW–MEDIUM Severity

- SGlang 4-bit serving: initialization errors [github.com/sgl-project/sglang/issues/18029] | MEDIUM
- Diffusers GGUF/FP8 safetensors support: unclear [github.com/huggingface/diffusers/issues/12891] | MEDIUM
- unsloth GGUF variant: discussions active, unresolved | MEDIUM
- Mitigation: Use BF16 or validated FP8 from official sources; use native diffusers integration.

## 7.7 Text Preservation (Conditional)

Official claim: model preserves font/size/styling during text editing with minimal artifacts [qwen.ai/blog?id=qwen-image-edit-2511 — MEDIUM, marketing material]. Text degradation co-occurs with square resolution degradation (Issue 7.2). No isolated text-only failure mode reports found. Recommendation: test text editing with non-square resolutions.

---

---

# SECTION 8: ERNIE-IMAGE (BAIDU)

## 8.1 Architecture

**Source:** Smith #8. HIGH. [github.com/baidu/ERNIE-Image updated 2026-08-22; arXiv 2605.25347, May 25, 2026]

| Attribute | Value | Confidence |
|---|---|---|
| Parameters | 8B | HIGH |
| Architecture | Single-stream Diffusion Transformer (DiT) | HIGH |
| Text encoder | Ministral-3 (3B) | HIGH |
| VAE | FLUX.2 VAE | HIGH |
| Paper | arXiv:2605.25347 | HIGH |
| GitHub created | 2026-04-14 | HIGH |
| GitHub last update | 2026-08-22 | HIGH |

- GitHub: https://github.com/baidu/ERNIE-Image
- HuggingFace standard (~50 steps): https://huggingface.co/baidu/ERNIE-Image
- HuggingFace Turbo (8 steps): https://huggingface.co/baidu/ERNIE-Image-Turbo
- Pipeline Docs: https://huggingface.co/docs/diffusers/main/api/pipelines/ernie_image
- Technical Report: https://arxiv.org/abs/2605.25347

## 8.2 Pipeline Classes

**Source:** Smith #8. HIGH.
- `ErnieImagePipeline` — text-to-image generation
- `ErnieImageInpaintPipeline` — inpainting support

## 8.3 Conditioning & Editing Features

**Source:** Smith #8.
- Inpainting (mask-based) | HIGH | [ernie-image.app/blog, May 2, 2026]
- Outpainting (canvas expansion) | HIGH | [same source]
- Image-to-Image (img2img) | HIGH | [HuggingFace ERNIE-Image collection]
- Style Transfer & Composite Operations | HIGH | [atlascloud.ai/models/ERNIE-Image]

## 8.4 ControlNet

**Source:** Smith #8.
- No official Baidu ControlNet support | HIGH (confirmed absence from official repo and HF docs)
- Community ControlNet for ComfyUI exists | MEDIUM | [ernie-image.app/blog, May 10, 2026]
  - Community-supported types: Canny (edges), Depth (spatial), Pose (body posture) | MEDIUM

## 8.5 Official Documentation Discrepancy

**Source:** Smith #8. MEDIUM. Baidu's official documentation emphasizes text-to-image. Img2img, inpainting, outpainting, and ControlNet are documented in community/third-party guides, not official materials. This is a documentation gap, not a capability absence.

---

---

# SECTION 9: STRUCTURE PRESERVATION — Z-IMAGE vs QWEN-IMAGE-EDIT

## 9.1 Central Finding

**Source:** Smith #9. No direct head-to-head benchmark comparing Z-Image img2img and Qwen-Image-Edit on structure preservation during style transfer exists in the published literature.

## 9.2 Architectural Contrast

**Source:** Smith #9. HIGH.

**Z-Image img2img:** Structure controlled via denoising strength (0.1–0.7+) on latent representation. Single-stream S3-DiT with lightweight modality-specific adapters. [arXiv 2511.22699, Nov 2025]

**Qwen-Image-Edit:** Dual-pathway architecture — image fed through both Qwen2.5-VL (semantic control) AND VAE encoder (visual appearance control). VAE encoder uses Global Skip Connections (GSC) for fine-grained detail preservation. Two explicit editing modes (appearance/semantic). [qwenlm.github.io/blog/qwen-image-edit/; arXiv 2508.02324]

These are fundamentally different control mechanisms; not directly comparable without controlled experiments.

## 9.3 QwenStyle Research

**Source:** Smith #9. HIGH. [arXiv 2601.06202, Jan 8, 2026]
First content-preserving style transfer model trained on Qwen-Image-Edit. Curriculum Continual Learning framework on 2,000 content-style pairs (50 style refs × 40 content refs). Claims SOTA in style similarity, content consistency, and aesthetic quality. No Z-Image baseline comparison.

## 9.4 Qualitative Observation (Non-Quantitative)

**Source:** Smith #9. MEDIUM. [Chris Green, Medium "Diffusion Doodles," early 2025]
- Z-Image Turbo: applies "aesthetic smoothing" layer; prioritizes balanced composition
- Qwen-Image-2512: "more literal and gritty," follows instructions strictly, high information density
- Neither directly compared on structure preservation in this article.

## 9.5 Analytical Assessment (Smith #9)

Qwen-Image-Edit's dual-pathway VAE encoder architecture implies a structural preservation advantage over Z-Image's single denoising-strength dial. However, no published study validates this specifically for style transfer. Opus should treat this as an informed hypothesis, not an established finding.

---

---

# SECTION 10: AUGUST 2026 NEW OPEN-WEIGHT MODELS

## 10.1 Key Finding

**Source:** Smith #10. **Zero pure text-to-image or image-editing models with confirmed open weights were released specifically in August 2026.**

## 10.2 Confirmed August 2026 Open-Weight Releases

**Source:** Smith #10. HIGH.

| Model | Developer | Date | Type | Params | License | Notes |
|---|---|---|---|---|---|---|
| Muse Glimmer | Meta | Aug 10, 2026 | Multimodal LM — NOT image gen | 30B | Apache 2.0 | Agentic, consumer hardware |
| MiniMax H3 (Hailuo 3.0) | MiniMax | Aug 3, 2026 | Video/omnimodal — NOT image-only | 33B | MiniMax H3 Community (excludes US, EU, UK, South Korea) | 4–15 sec video, up to 2K/24fps, stereo audio; #1 Video Editing on Artificial Analysis |
| Nemotron 3.5 Lightning | NVIDIA | ~Aug 11, 2026 | LM for agents — NOT image gen | 30B total / 3B active (MoE) | OpenMDW-1.1 | 30% faster than Qwen3.6 35B |

**Muse Spark 1.2 (Meta):** Announced Aug 10, 2026 as proprietary coding LM. Open weights promised but **not yet released** as of announcement date | MEDIUM.

## 10.3 Notable Non-August Open-Weight Image Models (Context)

**Source:** Smith #10. HIGH.

| Model | Developer | Release | Params | License | Notable |
|---|---|---|---|---|---|
| Cosmos3-Super-Text2Image | NVIDIA | May 31, 2026 | 64B | OpenMDW-1.1 | Current Artificial Analysis T2I Arena leader; MoT architecture |
| Ideogram 4.0 | Ideogram | Jun 3, 2026 | 9.3B | Non-Commercial (weights) / Apache 2.0 (code) | #1 open-weight on DesignArena; JSON prompt support |
| Krea 2 | Krea | Jun 22, 2026 | 12.9B Raw / 8B Turbo | Custom commercial | Enterprise-grade; ~2 sec generation |
| Seedream 5.0 Pro | ByteDance | Jul 8, 2026 | Proprietary | Proprietary API-only | Not open weights |

- Cosmos3-Super-Text2Image HuggingFace: https://huggingface.co/nvidia/Cosmos3-Super-Text2Image
- Ideogram 4.0 blog: https://ideogram.ai/blog/ideogram-4.0/

---

---

# CORRECTIONS

## C1: Z-Image CVTG-2K "Highest Score" Claim Is Internally Inconsistent

**Smith #1** twice asserts Z-Image has the "highest score" on CVTG-2K word accuracy (0.8671). The same Smith's comparison table shows Ovis-Image (7B) at **0.920**, which exceeds Z-Image's 0.8671.

**CORRECT:** Z-Image does not hold the highest CVTG-2K word accuracy based on Smith #1's own table. "Highest score" in the paper text likely refers only to models Z-Image was benchmarked against within its own paper, which may not have included Ovis-Image. Opus should audit which models were in the Z-Image paper's comparison set vs. the broader table populated from multiple papers.

## C2: guidance_scale Default 5.0 (Smith #2) vs. 0.0 for Turbo (Smith #4)

**Smith #2** states `guidance_scale` default=5.0 for ZImageImg2ImgPipeline. **Smith #4** states guidance_scale should be 0.0 for Z-Image-Turbo. Both are correct for different contexts: 5.0 is the pipeline code's generic default, inherited from Z-Image Base. Z-Image-Turbo is a distilled model requiring 0.0 (or 1.5–2.0 in practice). The official code example in Smith #2 itself uses `guidance_scale=0.0` for Turbo, confirming the Smith #4 guidance. This is a precision issue, not an error — but the two values must not be presented together without clarification.

## C3: Ollama + Diffusion Model Inference (Smith #3)

Smith #3 reports Ollama v0.16.0/v0.16.1 failing to load Z-Image-Turbo FP8, citing github.com/ollama/ollama/issues/14249. Ollama is primarily designed for LLM inference (llama-family models), not image diffusion models. Smith #3 attributes the failure to "text encoder tensor mapping in MLX runner," which suggests the Ollama issue may specifically concern loading the **Qwen3 text encoder** component within a hybrid pipeline — not the full Z-Image diffusion model. Opus should verify whether Ollama had added diffusion model support by mid-2026, or whether this issue concerns only the LLM text encoder subcomponent.

---

---

# DISPUTES

## No Genuine Disputes Identified

All apparent numerical disagreements between Smiths resolve cleanly under RECENCY or DEDUP:

| Apparent Conflict | Resolution |
|---|---|
| ERNIE-Image LongTextBench 0.973 (paper) vs 0.9733 (GitHub) | Same number, rounding — DEDUP |
| Smith #2 guidance_scale=5.0 vs Smith #4 guidance_scale=0.0 | Different model variants (Base vs Turbo) — not a conflict |
| Qwen-Image CVTG-2K 0.829 vs 0.8288 | Same measurement, evaluation configuration rounding — DEDUP |

No Smith directly contradicts another Smith on the same claim at the same model/date.

---

---

# GAPS

| ID | Gap | Smiths Affected |
|---|---|---|
| **G1** | "Z-Image-Edit" identity unclear — distinct editing model or img2img pipeline evaluated under a different name? Relationship unspecified. Matters for structure-preservation analysis. | #9 |
| **G2** | ERNIE-Image has no CVTG-2K score despite strong text rendering emphasis. Cross-benchmark ranking is incomplete. | #1, #8 |
| **G3** | Z-Image-Edit LPIPS/SSIM/PSNR on ImgEdit not disclosed. Structural comparison with Qwen-Image-Edit is one-sided. | #9 |
| **G4** | JoyAI-Image (0.963/0.963 LongTextBench) — no citation, no exact date, no dedicated Smith. LOW confidence. Verify or discard. | #1 |
| **G5** | Ovis-Image (7B) — MEDIUM confidence, no dedicated Smith, may rank above Z-Image on CVTG-2K (0.920 vs 0.8671). | #1 |
| **G6** | Cosmos3-Super-Text2Image (NVIDIA, May 2026, 64B, Artificial Analysis T2I leader) — mentioned only in passing; no benchmark scores, architecture detail, or comparison with covered models. | #10 |
| **G7** | Ideogram 4.0 (#1 open-weight DesignArena, Jun 2026) and Krea 2 (Jun 2026) — mentioned only as context; not included in any benchmark comparison. | #10 |
| **G8** | Zero confirmed August 2026 dedicated text-to-image / image-editing open-weight model releases. | #10 |
| **G9** | ERNIE-Image img2img, inpainting, outpainting, and community ControlNet documented in third-party guides only — not in Baidu's official materials. Official capability boundary unclear. | #8 |
| **G10** | Qwen-Image-Edit failure modes (Smith #7) dated 2025-12-30 to 2026-01-25 — ~7–8 months before search date. Resolution status of black image, square resolution degradation, and perspective synthesis issues as of Aug 2026 is unknown. | #7 |
| **G11** | Z-Image text encoder identity in GGUF workflows — Smith #3 names "Qwen3 4B Instruct" but no Smith confirms this definitively across all frameworks from the arXiv paper itself. | #3 |

---

---

# QUICK-REFERENCE: SOURCE DATES BY MODEL

| Model | Earliest Source | Most Recent Source | Smith(s) |
|---|---|---|---|
| Z-Image / Z-Image-Turbo | Nov 27, 2025 (arXiv 2511.22699) | Aug 2026 (community guides, repos) | #1, #2, #3, #4, #5, #9 |
| ERNIE-Image | Apr 14, 2026 (GitHub created) | Aug 22, 2026 (GitHub updated) | #1, #8 |
| Qwen-Image 2.0 | May 11, 2026 (arXiv 2605.10730) | Jun 2026 (TeleStyleV2) | #1 |
| Qwen-Image-Edit 2511 | Nov 2025 (2511 version) | Jun 2026 (TeleStyleV2 paper) | #6, #7, #9 |
| JoyAI-Image | 2026 (no exact date) | 2026 (no exact date) | #1 only — LOW |
| Ovis-Image (7B) | Nov 2025 | Nov 2025 | #1 only — MEDIUM |
| Cosmos3-Super-Text2Image | May 31, 2026 | Jun 22, 2026 (tech report) | #10 only |
| Ideogram 4.0 | Jun 3, 2026 | Jun 3, 2026 | #10 only |
| Krea 2 | Jun 22, 2026 | Jun 22, 2026 | #10 only |
| MiniMax H3 | Aug 3, 2026 | Aug 3, 2026 | #10 only |

---

**END OF ANDERSON ORGANIZED FINDINGS — CHAIN A**
*All unique signal preserved. Corrections applied inline. Disputes resolved or marked. Gaps enumerated. Opus: editorial judgment on emphasis and synthesis is yours.*

============================================================
## Chain B — Anderson Report
============================================================

No filesystem access in this environment — delivering the full organized findings directly here. All unique signal preserved; nothing compressed.

---

# CHAIN B — ANDERSON ORGANIZED FINDINGS
**For Opus synthesis. Smiths #11–#20. Date: 2026-08-23.**

---

## THEME A — TEXT & GLYPH RENDERING IN IMAGE GENERATION MODELS
*Sources: Smith #11, Smith #19*

---

### A1. MODEL ACCURACY RANKINGS FOR SHORT TEXT / ISOLATED GLYPHS
**[AGREE: Smith #11 and Smith #19 converge on Ideogram as best-in-class]**

**IDEOGRAM 3 / 4.0**
- 90–95% accuracy on short text (1–4 words)
- Drops to ~70% for 5–12 words; sharp drop beyond 15 words
- Practical ceiling: ~60 characters per image
- Confidence: **HIGH** (Smith #11 + #19) — multiple independent practitioner reviews, 2026; both Smiths independently name it top performer
- Sources (Smith #11): imagetoprompt.dev, 3daistudio.com, ucstrategies.com, June–Aug 2026
- Source (Smith #19): imagetoprompt.dev Ideogram Prompt Guide 2026

**GLM-IMAGE (Zhipu AI, 16B, released Jan 14, 2026)**
- 91.16% word accuracy on CVTG-2K benchmark (2,000 prompts, 2–5 text regions)
- Outperforms GPT Image 1 (85.69%) and FLUX.1 Dev (49.65%) on CVTG-2K — current leader on that benchmark
- Confidence: **HIGH** (Smith #20) — primary source: HuggingFace zai-org/GLM-Image
- ⚠️ **Coverage gap in Smith #11**: Smith #11 cites CVTG-2K but does NOT mention GLM-Image, despite GLM-Image being released January 2026, well before Smith #11's June–Aug 2026 research window. Opus should treat GLM-Image as the CVTG-2K leader.

**GPT IMAGE 1**
- CVTG-2K word accuracy: 0.8569 (85.69%)
- Source (Smith #11): arxiv 2503.23461 — Confidence: **MEDIUM**
- ⚠️ See **Correction C1** on paper date

**GPT-4O IMAGE GENERATION**
- TextAtlasEval (4,000 samples, 4 domains): 60.69–82.88% character-level accuracy
  - Highest domain: CleanTextSynth (82.88%)
  - Lowest domain: TextVisionBlend (60.69%)
- Source (Smith #11): arxiv 2504.05979 — Confidence: **HIGH** (peer-reviewed benchmark, April–May 2025)

**DALL-E 3**
- ~95% accuracy on short strings; errors rise with sentences over 8 words
- Source (Smith #11): modelranked.com reviews (2026) — Confidence: **MEDIUM** (third-party reviews only)
- ⚠️ See **Dispute D1** — this figure likely inflated vs. peer-reviewed GPT-4o data

**RECRAFT V4**
- Strong on short phrases, headlines, single-line text; "context is clean and text is singular" = best results
- Struggles with dense/multi-element layouts
- Confidence: **MEDIUM** (Smith #11) — replicate.com, mindstudio.ai, 2026; no quantitative benchmark cited

**GPT IMAGE 1.5**
- 85–90% text fidelity on embedded text
- Confidence: **MEDIUM** (Smith #11)
- ⚠️ See **Correction C2** — "GPT Image 1.5" is not a publicly documented model designation; Opus should treat with **LOW** confidence until verified

**REVE 2.1** (Released July 9, 2026)
- #2 on Text-to-Image Arena (Elo 1306); layout-first 4K; hierarchical editable layers
- No specific text accuracy benchmark cited
- Confidence: **MEDIUM** (Smith #20)

**FLUX.1 DEV**
- CVTG-2K word accuracy: 49.65% (Smith #20 / GLM-Image paper)
- With FontFusion conditioning: 76.52% font consistency (up from 0.91% baseline); minimal quality degradation (CLIP score 31.84% vs. 32.09% baseline)
- Source (Smith #19): arxiv 2606.06066, June 2026 — Confidence: **HIGH**

**GROK IMAGINE IMAGE 2.0** (Released Aug 8, 2026)
- "Typography-aware image model; Flux-based"; native image and video editing
- No quantitative text accuracy benchmark cited
- Confidence: **LOW** on specifics (Smith #20)

**GEMINI 2.5 FLASH IMAGE**
- CVTG-2K word accuracy: 0.7364 (73.64%)
- Source (Smith #11): arxiv 2503.23461 — Confidence: **MEDIUM**

**STABLE DIFFUSION (various)**
- SD: ~30–40% text accuracy (Smith #11); SD 3.5: "fair" text rendering, rewards structured/weighted keywords (Smith #19)
- Confidence: **MEDIUM** (Smith #11, toolscompare.ai comparisons 2026)

**FLUX (non-conditioned general)** — Mid-tier between SD and Ideogram (Smith #11); Confidence: **MEDIUM**

**OPEN-SOURCE BASELINES** (MX-Font, LF-Font, etc.) — CVTG-2K catastrophic failure: 0.11–2.98% word accuracy; Confidence: **MEDIUM**

**MIDJOURNEY V8.1** — "First legible version"; still far behind Ideogram; "marginal" text rendering; Confidence: **MEDIUM** (Smith #19; prior MJ v6 data 2023–2024 is explicitly obsolete)

**ACCURACY HIERARCHY TABLE [AGREE — Smith #11 + Smith #19 converge]:**

| Rendering Type | Accuracy | Notes |
|---|---|---|
| Clean block letters (sans-serif, plain bg) | 90–95% | Best: single UC letter or 2-letter pairs |
| Short words (1–3 words, quoted) | 85–90% | Ideogram sweet spot |
| Decorative lettering | 30–50% | Curves/stylization causes sharp accuracy drop |
| Handwritten text | 20–40% | Ornamental serif worsens issues |

Source: Smith #11 (imagine.art/blogs/why-do-ai-image-generators-struggle-with-text, 2026) — Confidence: **MEDIUM** (practitioner observation, not formal two-letter benchmark)

---

### A2. PROMPT PATTERNS FOR CLEAN ISOLATED GLYPHS
**[AGREE: Smith #11 and Smith #19 strongly converge]**

**QUOTATION MARKS — CRITICAL** (Confidence: **HIGH**, AGREED Smith #11 + #19)
- Enclose exact literal text in quotation marks; models read quoted text as content to render, not descriptive metadata
- Sources: docs.ideogram.ai, imagine.art/blogs/ideogram-4-0-prompt-guide, 2026

**PLAIN BACKGROUND SPECIFICATION** (Confidence: **MEDIUM**, Smith #11)
- "Isolated on fully transparent/white background"; explicitly exclude "scenery, solid backdrops, checkerboards, unwanted shadows"
- Sources: developers.openai.com/cookbook, getvidzy.com/text-in-image, 2024–2026

**FONT SPECIFICATION DETAILS** (Confidence: **MEDIUM** Smith #11 / **HIGH** Smith #19)
- Style: sans-serif preferred for accuracy; serif or monospace also recognized
- Weight: bold, regular — "ultra-bold condensed sans-serif" works reliably (Smith #19)
- Spacing: "wide spacing," "tight tracking" for two-glyph pairs
- Color: "monochrome" or specific hex code
- Example phrase: *"ultra-thin, clean sans-serif fonts with monochrome colors and wide spacing on a plain white background"* (help.apiyi.com, 2026)

**TEXT LENGTH LIMITS** (Confidence: **HIGH**, Smith #11)
- 1–4 words: ~90% accuracy (Ideogram); 5–12 words: ~70%; 15+ words: sharp drop (letters omit/cram)
- Two-letter specific: within 1–4-word bracket, inferred ~90%+
- No published benchmark tests two isolated letters specifically — this is a documented research gap (see GAP-2)

**MAGIC PROMPT CONTROL — Ideogram-specific** (Smith #11)
- Disable Magic Prompt to keep wording exact
- Source: imagetoprompt.dev, 2026

**THREE TESTED PROMPT TEMPLATES FOR TWO ISOLATED LETTERS** (Smith #11):

> *Template 1 (Ideogram official docs):*
> `Capital K and lowercase g, "K" "g", bold sans-serif, plain white background, isolated, no shadows`

> *Template 2 (practitioner guides):*
> `The text "Kg" in heavy sans-serif, monochrome black on pure white (#FFFFFF), clean kerning, centered composition, gallery-print quality`

> *Template 3 (GPT-Image-2 guides):*
> `Two letters: capital K beside lowercase g, ultra-clean geometric typeface, no background detail, simple typography, high contrast, studio lighting`

Sources: help.apiyi.com, picsart.com, docs.ideogram.ai, 2024–2026

---

### A3. TYPOGRAPHY PROMPT VOCABULARY — WHAT WORKS / WHAT IS IGNORED
*[Smith #19 primary; corroborated by Smith #11 on model-specific behavior]*

**TERMS THAT WORK RELIABLY** (Confidence: **HIGH**, Smith #19):
- `serif` vs. `sans-serif` — distinct visual results across all major models
- `slab serif` — visible block-like serifs (Ideogram confirmed)
- Font weight: `bold`, `light`, `regular`, `ultra-bold condensed`
- `condensed` / `expanded` — measurable proportional changes
- `script` / `handwritten` — models distinguish from formal serifs
- Color contrast specifications with hex codes (min 4.5:1 contrast for legibility)

**TERMS THAT PARTIALLY WORK** (Confidence: **MEDIUM**, Smith #19):
- `geometric sans` — broad category; inconsistent fine distinctions
- `humanist sans-serif` — Ideogram interprets; produces Gill Sans-like feel
- `grotesque` / `chunky grotesque` — Ideogram: heavy early-sans feel
- `transitional serif` / `elegant serif` — produces "refined, moderate contrast" on Ideogram; less reliable than `serif` alone
- `monospace` — basic even-spacing works; fine control unreliable
- `distressed` / `grunge` — worn irregular edges; works across multiple models
- `vintage [era] serif` — produces era-appropriate contextual style

**TERMS WITH NO EVIDENCE OF RECOGNITION** (Confidence: **LOW**, Smith #19 — 0 sources confirming effect):
- `flared terminals` — zero practitioner sources showing model response
- `humanist axis` / `stress` / `diagonal stress` — relational reasoning beyond current encoder capability (confirmed by arxiv 2603.08497 below)
- `bracket style` (serif bracket) — not tested in any practitioner source
- `high contrast` as a descriptor — ignored; use `bold`/`thin` weight instead
- Complex named classifications (e.g., `Didone`) — rarely in working prompts
- `bowl shapes`, `x-height ratios` — no working prompt documentation found

**KEY RESEARCH FINDING — TYPOGRAPHY BLINDNESS** (Confidence: **HIGH**, Smith #19):
- Source: arxiv 2603.08497 *"Reading ≠ Seeing: Diagnosing and Closing the Typography Gap,"* March 2026
- Models achieve near-perfect accuracy reading text *content* but fail dramatically on *visual typography style*
- Perception hierarchy: Color ≈100%, font family ≈50%, font style <20%
- Cause: Font style requires "relational reasoning about stroke weight and slant" — patch-based encoders cannot do this
- Fine-tuning improves color/size recognition; **font style remains resistant to fine-tuning**

**FONTUSE DATASET** (Confidence: **HIGH**, Smith #19): arxiv 2603.06038 — 70K annotated images pairing user-friendly typographic prompts with rendered text; style + use-case combinations (e.g., "elegant serif for wedding invitations") improve model consistency. Fine-tuned models consistently interpret these paired descriptors.

**FONTFUSION CONDITIONING** (Confidence: **HIGH**, Smith #19): arxiv 2606.06066, June 2026 — Hierarchical token representation added to FLUX.1 DiT. Font consistency: 76.52% (vs. 0.91% baseline); minimal quality degradation (CLIP score 31.84% vs. 32.09%). Performance by font category: geometric > sans-serif > serif > decorative.

**MODEL-SPECIFIC TYPOGRAPHY TABLE** (Smith #19, Confidence: **MEDIUM**, 2026):

| Model | Serif/Sans | Slab | Weight | Geo/Hum/Grot | Text Rendering |
|---|---|---|---|---|---|
| Ideogram | Excellent | Good | Excellent | Fair | Best-in-class (9/10 for 1–4 words) |
| DALL-E 3 | Good | Fair | Good | Untested | Good short; fails long |
| FLUX.1 | Good | Fair | Good | Untested | Excellent w/ FontFusion |
| Midjourney V8.1 | Poor | Fails | Poor | Poor | Marginal (first legible version) |
| Stable Diffusion 3.5 | Moderate | Fair | Untested | Untested | Fair |

---

### A4. ACADEMIC BENCHMARKS FOR GLYPH / TEXT ACCURACY
*[Smith #11 primary]*

**CVTG-2K** (arxiv 2503.23461): 2,000 prompts, 2–5 text regions per image. ⚠️ See Correction C1 on paper date. Results: GLM-Image 91.16% (Smith #20), GPT Image 1 85.69%, Gemini 2.5 Flash 73.64%, open-source baselines 0.11–2.98%. Confidence: **MEDIUM** (Smith #11); **HIGH** for GLM-Image figure (Smith #20).

**TextAtlasEval** (arxiv 2504.05979): 4,000 samples, 4 domains. GPT-4o: 60.69–82.88% character-level accuracy. Confidence: **HIGH** (peer-reviewed, April–May 2025).

**STRICT benchmark** (arxiv 2505.18985) and **TIQA** (arxiv 2603.07119): Listed in Smith #11's URL index; no detailed numbers provided in any Smith.

---

### A5. ACADEMIC GLYPH RENDERING FRAMEWORKS (Research; not production)
*[Smith #11]*

- **GlyphBanana** (arxiv 2603.12155, March 2026): Agentic 4-stage pipeline (Extract → Draft Preview → Glyph Injection → Style Refinement); VLM-guided + latent/attention map injection. GitHub: github.com/yuriYanZeXuan/GlyphBanana. Confidence: **MEDIUM** (academic, not production-tested)
- **FonTS** (ICCV 2025, arxiv 2412.00136, December 2024): Two-stage DiT pipeline; word-level typographic control; 55% Word-level Attribute Accuracy (all baselines 0%). Confidence: **MEDIUM**
- **CharGen** (arxiv 2412.17225, December 2024): Character-level multimodal encoder; +8% AnyText, +6% MARIO-Eval, +5.5% Chinese. Confidence: **MEDIUM**
- **Lakhanpal et al.** (WACV 2025, arxiv 2403.16422): Glyph-controlled generation; introduces LenCom-Eval benchmark. Confidence: **MEDIUM**

---

## THEME B — FONT GENERATION ON OPEN-WEIGHT MODELS
*Sources: Smith #18, Smith #12*

---

### B1. DIFFUSION-BASED FONT GENERATION PROJECTS
*[Smith #18 primary]*

**MSD-FONT** (CVPR 2024): Base — Stable Diffusion. Three-stage reverse diffusion: (1) structure construction, (2) font transfer, (3) refinement. Output: Raster bitmap 512px. No raster-to-font conversion. Quality caveat: degrades if content info over-injected in later diffusion iterations. GitHub: github.com/fubinfb/MSD-Font. Confidence: **HIGH**.

**FONTDIFFUSER** (AAAI 2024): Base — general diffusion. Multi-scale content aggregation + style contrastive learning. Output: Raster. No font file conversion. Quantitative: FID 7.70 (vs. competitors ≥7.79); SSIM 0.4682. Quality caveat: "still quite blurry" (Simon Cozens blog 2024 — **LOW** confidence: subjective). HuggingFace demo available. GitHub: github.com/yeungchenwa/FontDiffuser. Confidence: **HIGH**.

**VECFUSION** (CVPR 2024, arxiv 2312.10540): Two-stage diffusion (raster + vector). Stage 1: raster diffusion → low-res fonts + auxiliary control points. Stage 2: vector diffusion transformer → direct SVG/Bézier curves. **NOT raster-to-vector post-processing** — novel mixed discrete-continuous control point representation. "Higher quality vector fonts with complex structures" vs. prior methods. No official code release found. Confidence: **HIGH**.

**VECGLYPHER** (CVPR 2026, arxiv 2602.21461 — ⚠️ see Correction C3 on date): Base — **LLM, NOT a diffusion/image model** (important distinction). SVG path token language modeling; multimodal LLM. Output: Direct SVG, no raster intermediate. Trained on 39K Envato fonts + 2.5K annotated Google Fonts. SOTA on cross-family OOD evaluation and image-referenced generation. GitHub: github.com/xk-huang/VecGlypher. Confidence: **HIGH**.

**DIFFCJK** (ICCC 2024, arxiv 2404.05212): Base — general diffusion. Styles: Gothic, Regular, Song/Ming, Clerical, Semi-cursive, Cursive. Output: Bitmap (requires external vectorization). Zero-shot generalization for non-CJK scripts; smooth style interpolation. No code release found. Confidence: **HIGH**.

**QWEN-IMAGE** (font/text context): 20B MMDiT. Output: Raster images with rendered text only — NOT font file generation. Qwen-Image-Edit-2511 supports text rendering/editing with "perfect font matching." Released 2026-02-10. GitHub: github.com/QwenLM/Qwen-Image. Confidence: **HIGH**.

**Summary table (Smith #18):**

| Project | Base Model | Output | Vector Method | Font File Output | Date |
|---|---|---|---|---|---|
| MSD-Font | Stable Diffusion | Raster 512px | None | No | CVPR 2024 |
| FontDiffuser | Diffusion (general) | Raster | None | No | AAAI 2024 |
| VecFusion | Diffusion (2-stage) | SVG | Direct vector diffusion | Theoretically yes | CVPR 2024 |
| VecGlypher | LLM (not img model) | SVG | No raster step | Yes (SVG) | CVPR 2026 |
| DiffCJK | Diffusion (general) | Raster bitmap | External tool required | No | ICCC 2024 |
| Qwen-Image | MMDiT 20B | Raster | None | No | 2026-02-10 |

**Note (Smith #18):** No projects found that exclusively use FLUX or Qwen-Image for font generation with documented raster-to-font conversion.

---

### B2. RASTER-TO-VECTOR / RASTER-TO-FONT CONVERSION TOOLS
*[Smith #18]*

- **Potrace** (most common): Open-source, 2001. Bitmap → smooth vector outlines. Limitation: **black-and-white ONLY** (no color). FontForge uses Potrace as its engine. Confidence: **HIGH**
- **VTracer** (faster alternative): Processes 4K images in milliseconds vs. minutes. Handles colored images. GitHub: github.com/visioncortex/vtracer. Confidence: **MEDIUM** (speed claim from blog, not independently benchmarked)
- **FontForge**: Open-source font editor with Potrace-based vectorization; typical workflow: Raster → Potrace → TTF/OTF assembly. Confidence: **HIGH**
- **ComfyUI-ToSVG-Potracer**: ComfyUI node for raster→SVG using pure Python Potrace; integrates vectorization into diffusion workflows. GitHub: github.com/ImagineerNL/ComfyUI-ToSVG-Potracer. Confidence: **HIGH**

**Raster-to-vector quality caveats (Smith #18):** Traditional pipelines produce imprecise control points and curve distortions; Potrace limited to B&W; rasterization artifacts transfer to vector. VecFusion's direct vector diffusion avoids all of these. Competing raster-based methods (MX-Font, LF-Font) show missing strokes, blurriness, layout errors.

---

### B3. SOURCE TYPEFACE SELECTION FOR NEURAL STYLE TRANSFER
*[Smith #12 primary]*

**PRIMARY FINDING — Source font choice is negligibly important** (Confidence: **HIGH**):
- **Attribute2Font** (SIGGRAPH 2020, arxiv 2005.07865): *"The influence of source font selection was found to be negligibly small when regular fonts were selected as the source. There is no strict restriction on the source font in their model."*
- Experiments showed generated glyphs are "nearly the same for most source fonts" — contradicts intuitive expectation that similar source = better output
- Similarity measured via PANOSE-1 attribute values

**Baseline practice in research (Smith #12):** Song font (simple regular serif; common in Chinese typography) used as source baseline in Attribute2Font and related work. No published rationale beyond "simple and commonly used." Confidence: **MEDIUM**.

**No published guidance exists on:** grotesque vs. distinctive typefaces as source inputs; comparative studies on source typeface neutrality. The field has moved toward transfer technique selection, not source font selection. Confirmation of absence: **HIGH confidence**.

**What actually matters (Smith #12):** Content structure preservation (Multi-scale Content Aggregation blocks; MDPI Electronics 2023); stroke characteristics (width, serifs, slant, ligatures, texture) learned from style references — not from source font properties; method type matters more than source font choice.

**⚠️ FLAG — POTENTIALLY OUTDATED CONVENTIONAL WISDOM (Smith #12):** "Simple, neutral sources work best" is an outdated assumption contradicted by SIGGRAPH 2020 research. Systems post-2020 should prioritize source content clarity over typeface neutrality.

---

## THEME C — IMG2IMG STRENGTH / DENOISING PARAMETER
*Source: Smith #13 only — no overlap with other Smiths*

**Technical definition:** `strength` (0.0–1.0) controls noise added to input's latent representation before denoising. Formula: `effective_denoising_steps = ceil(num_inference_steps × strength)`. 0.0 = identical to input; 1.0 = input fully replaced. Default in HuggingFace Diffusers: 0.9999. Confidence: **HIGH** (official docs).

**Content replacement threshold:** ~0.40 — below this, input structure heavily influences output; above 0.40, model increasingly ignores input structure. Confidence: **MEDIUM** (practitioner consensus, not peer-reviewed).

**Content survival by strength (Confidence: MEDIUM — practitioner consensus, no peer-reviewed empirical study):**

| Strength | Label | Content Survival | Use Case |
|---|---|---|---|
| 0.15–0.35 | Low | Identity largely preserved | Cleanup, artifact removal, identity/layout preservation |
| 0.35–0.50 | Low-Med | Strong + texture enhancement | Upscaling, detail (skin pores, fabric) without composition change |
| 0.40–0.60 | Medium | Moderate preservation | Noticeable restyling; composition stays recognizable |
| 0.45–0.65 | Med-High | Reduced preservation | Moderate redraws, new lighting/mood |
| 0.70+ | High | Minimal preservation | Dramatic transforms; image drifts far from source |

**Recommended ranges by use case:** Portrait/face identity: 0.2–0.35 | Faithful representation: below 0.4 | Balanced "sweet spot": 0.4–0.6 | Upscaling w/ detail: 0.35–0.5 | Dramatic rewrite: 0.7+

**Troubleshooting:** Output too similar → raise strength +0.1 | Output loses subject/pose → lower strength

**Sources (all HIGH confidence, Smith #13):** 10b.ai blog (2026); AIARTY (2025); Stable Diffusion Art (2024+); Shakker AI wiki (2024+); RunDiffusion docs (2024+); HuggingFace Diffusers (official, current)

**⚠️ Important caveat (Smith #13):** All numerical ranges are **MEDIUM** confidence — practitioner consensus, NOT a single peer-reviewed empirical study. No formal academic study specifically measuring identity preservation by strength value found in literature (2024–2026).

---

## THEME D — TRAINING DATA PROVENANCE & MODEL TRANSPARENCY
*Source: Smith #14*

**Four Apache 2.0 models compared:**

**QWEN-IMAGE (Alibaba) — MOST TRANSPARENT**
- Paper: arxiv 2508.02324
- Disclosed dataset composition (Confidence: **HIGH**): Nature 55%, Design 27%, People 13%, Synthetic (text-rendering-focused) 5%
- Text rendering pipeline categories (HIGH): Pure Rendering (dynamic font layout on homogeneous BG), Compositional Rendering (text in photorealistic scenes), Complex Rendering (slides/multi-block)
- Annotation: Qwen2.5-VL vision model → JSON-structured metadata
- >90% accuracy in bilingual text editing (Confidence: **MEDIUM**)
- Silent on: specific font families, typeface sources, third-party font licensing

**Z-IMAGE (Alibaba / Tongyi-MAI) — LEAST TRANSPARENT (of Apache 2.0 models)**
- Paper: arxiv 2511.22699
- Disclosed: "Real-world data" only; 314K H800 GPU hours; S3-DiT architecture
- Font/typeface: controllable rendering system (font, color, size, position) disclosed; CJK strength mentioned; "small font sizes" support noted
- Silent on: no named datasets; no composition percentages; no CJK font families

**ERNIE-IMAGE (Baidu) — MEDIUM TRANSPARENCY**
- Paper: arxiv 2605.25347
- Disclosed: Internal Baidu corpus; 10,000 visual categories; pipeline (VLM caption enhancement, ERNIE-Image-Aes aesthetic scoring, hierarchical sampling); trained on posters, CJK signage, multi-panel comics (HIGH)
- Font/typeface: CJK character-aware encoder; stroke order, radical composition, visual grammar of CJK typography understood; LongTextBench: 0.9733; GenEval: 0.8728
- Silent on: no named external datasets; no specific CJK font families; no Latin font sources

**FLUX.2-KLEIN (Black Forest Labs, January 2026) — SILENT**
- Disclosed: "Step distilled and guidance distilled from FLUX.2 base model"; NSFW/CSAM filtered
- Font/typeface: ~60% text accuracy (MEDIUM); character spacing/kerning/line heights maintained; responds to font style specs in prompts
- Silent on: **Complete silence on original FLUX.2 base training data sources**; no datasets named; no composition percentages; no font family sources

**Transparency ranking (Smith #14):** Qwen-Image (most) → ERNIE-Image → Z-Image → FLUX.2-klein (least)

**Note:** Smith #20 adds Boogu-Image (Apache 2.0), GLM-Image (Apache 2.0/MIT), Inkling (Apache 2.0) — training data transparency for these models is **NOT covered by any Smith**. Gap noted below.

---

## THEME E — LEGAL: AI-GENERATED TYPEFACE COPYRIGHT & OUTPUT RIGHTS
*Source: Smith #15*

---

### E1. AI-Generated Typeface Copyrightability

**Core finding — Purely AI-generated typefaces cannot be copyrighted (Confidence: HIGH):**
- **U.S. Copyright Office (January 2025):** Works created solely by AI are not copyrightable even with human prompts. "Sufficient human control over expressive elements" required. Prompts alone ≠ authorship.
- **Foley & Lardner (February 2025):** AI-assisted typefaces require "meaningful human creative input." If AI enhancements are "so integrated that original human authorship can no longer be identified as distinct," entire work loses protection.
- **Canada:** AI portions must be disclaimed; human typographer must demonstrate "original aspects that are the product of the typographer's skill and judgment."
- Sources: copyright.gov/ai/; foley.com (Feb 2025); bennettjones.com

---

### E2. Typeface Design vs. Font Software — Critical Legal Distinction (Confidence: HIGH, universal)

| Element | Definition | Copyright Status |
|---|---|---|
| Typeface Design | Visual appearance of letterforms/glyphs | Varies by jurisdiction |
| Font Software | Digital code (.ttf, .otf) enabling rendering | **Universally protected** as computer program |

A competitor can legally copy a typeface's visual design and redistribute under a different name IF they independently code the font software. Designers rely instead on: trademark (font name), design patents, trade dress.

---

### E3. US vs. EU — Major Divergence

**UNITED STATES — Typeface Design NOT copyrightable (Confidence: HIGH)**
- 17 U.S.C. § 102 explicitly excludes typeface designs
- Copyright Office refuses registration for "mere variations of typographic ornamentation or lettering"
- What IS protected: Font software code only
- Alternative protections: design patents, trademark, trade secrets
- Source: copyright.gov/circs/circ33.pdf

**EUROPEAN UNION — Dual Protection — RECENT REFORM (Confidence: HIGH)**
- EU Design Regulation 2024/2822 (effective **May 1, 2025**) + Design Directive 2024/2823 (effective December 8, 2024)
- Typeface designs qualify as "products"; receive: (1) Registered Community Design — 25 years, (2) Unregistered Community Design — 3 years automatic, (3) Copyright — now expressly permitted to coexist
- EU Originality Standard (CJEU): must "reflect the personality of the author as an expression of his or her free and creative choices"
- EUIPO registration requires: all alphabet letters (UC+LC), Arabic numerals, five lines of text, all at 16-pitch

---

### E4. Global Protection Matrix

| Jurisdiction | Protection | Notes |
|---|---|---|
| Germany | Copyright | Recognized since 1981 |
| France | Copyright + Design | Both available; originality standard applies |
| UK | Copyright + Design | CDPA 1988; unregistered design 10–15 years |
| Japan | Conditional only | Requires "remarkable originality AND excellent aesthetic characteristics" (high bar); font software = protected |
| China | Copyright | "Highly unique aesthetic appreciation" + clearly differentiated; single chars may be protected individually |
| Australia | Copyright (limited) | Unregistered design right + copyright; font software protected |
| Canada | Copyright | "Skill and judgment" standard; excludes unoriginal underlying alphanumeric chars |

Source: monotype.com global survey — Confidence: **HIGH–MEDIUM** (law changing rapidly)

---

### E5. Letterform Protection: Artistic vs. Functional (US, Confidence: HIGH)

**Copyrightable expression (Useful Article Doctrine):** unusual stroke weights, decorative serifs, geometric distortions, ligatures, alternate characters, unique spacing/proportional relationships

**NOT protectable:** basic letterform "A" or "B" itself; standard serif vs. sans-serif conventions; unoriginal variations on existing letterforms

---

### E6. Case Law: Spectral Font (France, 2023, Confidence: MEDIUM)
- *Tribunal Judiciaire de Paris:* Porchez v. Production Type
- Finding: Copyright exists for typeface design (Le Monde Journal = original creative work)
- Outcome: Infringement claim DISMISSED — similarities insufficient to establish copying of protectable expression
- Demonstrates: EU recognizes typeface copyright but applies rigorous "substantial similarity" test
- Source: ipkitten.blogspot.com/2023/05/the-copyright-adventure-of-two.html

---

### E7. AI Typeface Legal Risks & Current Vacuum

**Two concurrent risks (Confidence: HIGH):**
1. AI tools can replicate/distribute typefaces without proper licensing → may violate existing licensing/copyright
2. "Questions remain about whether AI-created typefaces possess sufficient originality for copyright protection and whether they infringe existing designs"

**Legal vacuum:** No court has ruled whether an AI-generated typeface — even with human direction — qualifies for copyright protection anywhere globally. 2025 U.S. Copyright Office framework has NOT been tested on typeface designs specifically.

**Most recent developments:**
- EU Design Reform: effective May 1, 2025
- U.S. Copyright Office Part 2 AI Report: January 2025
- UK: *Getty Images v. Stability AI* — November 4, 2025 — Getty LOST infringement claim in UK's first such ruling (ropesgray.com)

Confidence for statutory/regulatory citations: **HIGH** | Pre-2023 case law: **MEDIUM** | AI typeface-specific case law: **NONE** (extrapolated only)

---

## THEME F — IMAGE QUALITY & STYLE EVALUATION METRICS (NO GROUND TRUTH)
*Sources: Smith #16 (NR-IQA), Smith #17 (style consistency)*

---

### F1. Classical No-Reference IQA Metrics

**BRISQUE (2012)** ⚠️ OUTDATED:
- Natural scene statistics + SVM; locally normalized luminance coefficients fitted to AGGD
- Scoring: Lower = higher quality
- Weakness: Designed for natural images; single global statistical model loses local info; poor fit for AI-generated aesthetics
- Source: live.ece.utexas.edu; weakness: arxiv 2505.07175 (2025)

**NIQE (2012)** ⚠️ OUTDATED:
- Opinion-unaware; multivariate Gaussian (MVG) model on local features
- Weakness: Single global MVG loses local info; insensitive to anatomical/structural errors; distribution assumptions mismatched to AI aesthetics
- Weakness source: arxiv 2505.07175 (2025)

**NIMA** (Neural Image Assessment):
- Variants: NIMA-TID (quality), NIMA-AVA (aesthetic)
- Weakness: Trained on real images; cannot detect distortions specific to generated content
- Source: arxiv 2505.07175 (2025)

**TReS** (Transformers, Relative Ranking, Self-Consistency, 2021, Confidence: **HIGH**):
- Hybrid CNN + self-attention; self-consistency enforced via horizontal flip invariance
- SOTA across 7 standard IQA datasets (synthetic + authentic)
- GitHub: github.com/isalirezag/TReS
- Source: arxiv 2108.06858

**PromptIQA** (ECCV 2024):
- Image-score pairs as prompts for quality prediction at inference
- Limitation: Requires multiple reference images at inference — not truly reference-free
- Source: Springer ECCV 2024

**AGHI-QA** (2025): Subjective-aligned dataset/metric specifically for AI-generated human images. Source: eu-opensci.org

**CLIP-AGIQA** (2024): CLIP-based regression leveraging visual + textual knowledge. Weakness: compositional blindness (shared with CLIPScore). Source: arxiv 2408.15098

**LAION-Aesthetics Predictor (LAP):**
- Curated ~1.2 billion images from LAION-5B; used to train Stable Diffusion
- Weakness (Confidence: **HIGH**): gender and LGBTQ+ bias in filtering; disproportionately filters in captions mentioning women; filters out captions mentioning men or LGBTQ+ people; one-size-fits-all aesthetic ignores cultural/personal variation
- Bias source: arxiv 2601.09896v4 (2025 audit)

---

### F2. CLIP-Based Prompt Adherence Scoring

**CLIPScore** (2021, widely adopted through 2025): Cosine similarity between image and text prompt in shared CLIP embedding space.

Weaknesses (Confidence: **HIGH**, multiple sources):
1. Coarse-grained: insensitive to fine-grained compositional errors
2. Bag-of-words: insensitive to word order, negation, linguistic phenomena
3. Saturation: scores plateau across models; poor discriminative power
4. Poor human correlation: misaligns with expert human evaluations
5. Centrality bias: biased toward centrally positioned objects
6. Assigns high scores to correct objects in wrong positions

Sources: arxiv 2403.05125 (2024); arxiv 2510.02987 (2024); arxiv 2508.13816 (2024)

**ImageReward:** Unified reward model fine-tuned on human preferences (alignment, fidelity, harmlessness). Weakness: inappropriately low scores for high-detail, high-aesthetic images. Source: arxiv 2507.19002 (2025)

**PickScore:** CLIP-based preference model; trained on Pick-a-Pic dataset via KL-divergence minimization. Advantage: stronger human correlation in open-domain generation vs. CLIP. Source: arxiv 2507.19002 (2025)

**HPSv2** (Human Preference Score v2, 2023): Fine-tuned CLIP on HPD v2. Advantage: outperforms base CLIP; better generalization to other models. Source: arxiv 2306.09341

**HPSv3** (Human Preference Score v3, August 2025 — **MOST RECENT**): Adopts Qwen2VL-7B backbone (replaces CLIP). Highest correlations with human preferences; effectively distinguishes models across performance spectrum; substantial gains over Qwen2VL-2B and CLIP. Source: arxiv 2508.03789 (ICCV 2025) — Confidence: **HIGH**

---

### F3. Perceptual & Distribution-Based Metrics

**LPIPS** [DEDUP: appears in Smith #16 (perceptual loss) and Smith #17 (style) — merged here]:
- Trained neural network comparing local perceptual features (AlexNet/VGG/SqueezeNet with human-judgment training)
- Advantage: Much better human correlation than pixel-based metrics
- Limitation: Requires reference image; cannot isolate style from content
- GitHub (Smith #17): github.com/richzhang/PerceptualSimilarity (official); variants: wanghaoyu33437, S-aiueo32; TF: Image-X-Institute/lpips_torch2tf; shift-tolerant: abhijay9/ShiftTolerant-LPIPS

**DINO-Based Perceptual Loss** [DEDUP: Smith #16 covers as loss; Smith #17 covers for style — kept separate in F3 for loss context, full style use in F4]:
- ViT self-distillation; attends to semantic hierarchy, object parts, spatial coherence
- Adding DINO loss to LPIPS improved FID from 10.00 to 7.46 on ImageNet-256
- Limitation: Requires reference image for loss computation
- Source: emergentmind.com; arxiv 2405.20392 (2025)

**Inception Score (IS, 2016)** ⚠️ Outdated approach: Pre-trained Inception v3; evaluates class prediction distribution on ~30,000 generated images. Higher = better. Weakness: poor human perception correlation; coarse.

**FID (Fréchet Inception Distance, 2017):** Compares feature distributions (Inception) between generated and real images. Lower = better. De facto standard. SOTA: FID below 2.0 on FFHQ dataset (2025). Limitation: Inception v3 architecture bias; distribution-level, misses fine-grained errors. Source: dl.acm.org/doi/10.1145/3708778.3708790 (2024)

**SSIM / MS-SSIM:** Luminance + contrast + structure decomposition. Limitation: measures structural/perceptual similarity, not semantic style. Standard in scikit-image, PyTorch.

---

### F4. Style Consistency Metrics — No Ground Truth
*[Smith #17 primary; DINO deduplicated from Smith #16]*

**CSD (Contrastive Style Descriptor)** — Best for style (Confidence: **HIGH**):
- Paper: arxiv 2404.01292, April 2024
- Architecture: ViT-L/14 fine-tuned on WikiArt artist labels; 1024-D → 768-D style vectors via projection
- Evaluation: Cosine similarity of CSD embeddings between images
- GitHub: github.com/learn2phoenix/CSD; HuggingFace: huggingface.co/yuxi-liu-wired/CSD
- ⚠️ Limitation note (Confidence: **HIGH**, June 2026): arxiv 2605.09030 *"When Style Similarity Scores Fail"* — raw cosine similarity shows discrimination gaps; CSLS readout on frozen backbone improves verification AUC from 0.883 → 0.905

**DINO ViT-B/8 + Pairwise Cosine Similarity** (Confidence: **HIGH**):
- Self-supervised training makes DINO more sensitive to style variations than CLIP; better differentiates styles vs. content
- Used in: ConsiStyle (arxiv 2505.20626, May 2025); Training-Free Style-aligned Image Generation (arxiv 2504.06144, April 2024)
- GitHub: github.com/facebookresearch/dinov2 (Meta DINOv2)

**Gram Matrix Distance (F-norm):**
- Gram matrices from VGG-19 intermediate layers (5 ReLU layers); Frobenius norm between matrices
- For sets: pairwise differences or mean/variance of differences
- Survey: arxiv 2506.19278 "Style Transfer: A Decade Survey" (June 2025)
- Application: Jigsaw3D (arxiv 2510.10497), video frame consistency
- Availability: Standard in PyTorch/TF style transfer pipelines

**Gram-MMD** (April 2026, Confidence: **HIGH**):
- Paper: arxiv 2604.03064
- Method: Vectorize Gram matrices from CNN activations (DINOv2, VGG19, Stable Diffusion VAE); compute Maximum Mean Discrepancy (MMD)
- Advantage: Captures second-order feature correlations (textural/structural) overlooked by semantic-level metrics
- Tested backbones: DINOv2, DC-AE, SD VAE encoder, VGG19, AlexNet
- Datasets: KADID-10k, RAISE
- Code: Not explicitly stated; uses standard MMD implementations

**MEt3R** (CVPR 2025, January 2025, Confidence: **HIGH**):
- Paper: arxiv 2501.06336
- Method: DUSt3R for dense 3D reconstruction → extract upsampled DINO features → warp into shared coordinate frame via point projections → compare warped feature maps
- Advantage: Pose-free, appearance-invariant, independent of sampling procedure
- GitHub: github.com/mohammadasim98/met3r (pip installable)
- Note: Designed for multi-view consistency; generalizable to stylistic consistency via feature similarity

**CLIP-MMD:**
- CLIP embeddings + Maximum Mean Discrepancy (no multivariate normality assumption)
- Limitation: CLIP produces high scores for similar content even with different styles; less ideal for pure style evaluation than CSD/DINO
- GitHub: github.com/arrrr2/clip-mmd

**AdaIN Loss** (Adaptive Instance Normalization, origin 2017):
- Channel-wise mean and variance alignment between feature maps
- For sets: average variance differences across image set
- Availability: Standard in PyTorch/TF neural style transfer pipelines

**Only-Style Framework** (ICCV 2025 Workshop P13N, June 2025, Confidence: **HIGH**):
- Paper: arxiv 2506.09916
- Innovation: Quantifies style consistency **while penalizing content leakage** — separates two dimensions that other metrics conflate
- GitHub: github.com/TilemahosAravanis/Only-Style

**Semantic Consistency Score** (2024, diffusion-specific):
- Pairwise mean CLIP score measuring repeatability/consistency in diffusion models
- Validation: 94% agreement with aggregated human annotations
- Applied to: SDXL vs. PixArt-α comparison
- Source: arxiv 2404.08799

**Style Metrics Summary (Smith #17):**

| Metric | No GT? | Open Code? | Recent? | Primary Strength |
|---|---|---|---|---|
| CSD | YES | YES | Apr 2024 | Style similarity between images |
| DINO + Cosine | YES | YES | Ongoing | Style vs. content separation |
| Gram Distance | YES | YES | Active | Textural style consistency |
| Gram-MMD | YES | Paper only | Apr 2026 | Second-order texture capture |
| MEt3R | YES | YES | Jan 2025 | Multi-view/spatial consistency |
| CLIP-MMD | YES | YES | 2023+ | Distribution-level comparison |
| AdaIN Loss | YES | YES | Active | Channel-wise mean/variance |
| LPIPS | Partial | YES | Active | Perceptual (needs reference) |
| Only-Style | YES | YES | Jun 2025 | Style without content leakage |
| SSIM/MS-SSIM | Partial | YES | Active | Structural (needs reference) |

**Most suitable for style-only sets, no ground truth (Confidence: HIGH):** CSD, DINO+Cosine, MEt3R, Only-Style, Gram-MMD

---

### F5. Comprehensive Metric Weaknesses (Meta-analysis, Smith #16)

1. **Saturation** (HIGH): CLIP Score, BLIP Score, FGA BLIP2 show saturated scores across modern models; fail to discriminate quality levels. Source: arxiv 2403.05125 (2024)
2. **Poor human correlation** (HIGH): MUSIQ, MANIQA, CLIP-IQA often assign high scores to images deviating from human judgment; no existing metric strongly correlates in large-scale psychophysical experiments. Source: arxiv 2603.00643 (2025)
3. **Task mismatch** (MEDIUM): Many NR metrics correlate poorly with downstream task suitability; insensitive to localized anatomical/structural details. Source: arxiv 2505.07175 (2025)
4. **Dataset lag** (MEDIUM): IQA datasets lag behind SOTA generative models in resolution, content complexity, output diversity. Source: arxiv 2603.00643 (2025)
5. **Distribution shift misleading** (MEDIUM): Metrics can yield misleading scores regarding data memorization and distribution shifts. Source: arxiv 2505.07175 (2025)
6. **Compositional blindness** (HIGH): CLIP's contrastive training ignores compositional information; errors in spatial relationships, attribute binding, fine-grained alignment. Sources: arxiv 2505.24424; arxiv 2504.16801 (2025)
7. **Global representation collapse** (HIGH): All contrastive VLMs (CLIP, LaCLIP, SigLiP) encode into global representations, constraining compositional understanding. Source: arxiv 2504.16801 (2025)
8. **Cultural/aesthetic bias** (HIGH): LAION-Aesthetics Predictor shows gender and LGBTQ+ bias; single cultural aesthetic standard. Source: arxiv 2601.09896v4 (2025)

**Note on self-consistency bridge (Smith #16 + #17):** TReS uses horizontal flip invariance as self-consistency signal (Smith #16); Self-Guided Diffusion Models (CVPR 2023) uses self-supervised proposals for semantically consistent generation (Smith #16). MEt3R uses warped DINO feature comparison (Smith #17). These are complementary — not duplicative.

---

## THEME G — MODEL LANDSCAPE: CURRENT & UPCOMING RELEASES
*Source: Smith #20; cross-references with Smith #11, #14, #19*

---

### G1. Models Released June–August 2026 with Text/Typography Strength
*Confidence: HIGH for release dates (primary sources); MEDIUM for licensing details (secondary aggregators)*

**IDEOGRAM 4** (Released June 3, 2026)
- Strength: Best-in-class typography; graphic design, poster layouts, long headlines, kerning-sensitive logotypes — *[AGREE with Smith #11, #19: independently confirmed as top typography performer]*
- License: Non-Commercial (open weights, quantized, HuggingFace) | Commercial self-serve: $0.035/img for 10K–100K img/month | Enterprise: >100K img/month
- Source: ideogram.ai/news/ideogram-4.0/; ideogram.ai/licensing/

**BOOGU-IMAGE-0.1** (Released June 16, 2026)
- Strength: Text-to-image + image-to-image editing; 10B parameters; near-closed-source performance
- License: **Apache 2.0** — unrestricted commercial use, no cost
- GitHub: github.com/boogu-project/Boogu-Image

**GLM-IMAGE** (Released January 14, 2026)
- Strength: 91.16% word accuracy on CVTG-2K — current benchmark leader — *[AGREE with Smith #11 CVTG-2K data; Smith #11 missed GLM-Image specifically]*
- License: MIT or Apache-2.0 — **CONFLICTING SOURCES** (see Dispute D3)
- Source: huggingface.co/zai-org/GLM-Image

**GROK IMAGINE IMAGE 2.0** (Released August 8, 2026)
- Strength: Typography-aware; Flux-based; native image + video editing
- License: Proprietary / API-only; $0.02/image fast tier; no free tier
- Source: x.ai/news/grok-imagine-api

**QWEN-IMAGE-3.0** (Invited preview July 21, 2026; Public GA August 5, 2026)
- Strength: Professional typography rendering, 1k-token instructions, infographic generation
- License: **Hosted-only proprietary — NO open weights** ⚠️ **IMPORTANT SHIFT from versions 1.0/2.0 which were Apache 2.0** *[RECENCY: Smith #14 covers Qwen-Image as Apache 2.0; Smith #20 shows version 3.0 reversed this — Smith #20 is current]*
- Source: orcarouter.ai/blog/qwen-image-3-0-ga

**REVE 2.1** (Released July 9, 2026)
- Strength: #2 on Text-to-Image Arena (Elo 1306); layout-first 4K; hierarchical editable layers
- License: **NOT SPECIFIED** — verify before production use

**INKLING** (Released July 15, 2026)
- Strength: Multimodal (text, image, audio); 975B parameter MoE
- License: **Apache 2.0**
- Note: General-purpose; NOT specifically optimized for typography
- Source: TechCrunch, July 15, 2026

---

### G2. Rumored Q4 2026 Models (Confidence: LOW)
- Next-gen Ideogram (Q4 2026): extended text rendering; license TBD
- Google Next-Gen T2I (Q4 2026): likely proprietary (historical pattern)
- Stable Diffusion Next (Q4 2026): likely open-source (Stability AI pattern)
- Kuaishou Kling Image (Q4 2026): photoreal Asian faces, product photography; TBD

---

### G3. Licensing Trends (As of August 2026, Smith #20)

| License | Models | Commercial Use |
|---|---|---|
| Apache 2.0 | Ideogram 4 (quantized), Boogu-Image, GLM-Image (claimed), Inkling, Z-Image | Free, unrestricted |
| Proprietary/API-only | Grok Imagine 2.0, Qwen-Image-3.0 | Paid, hosted-only |
| Proprietary + tiers | Ideogram 4 (full precision) | $0.035/img+ |
| Non-Commercial | FLUX.1 dev, some Ideogram 4 variants | Research/personal only |

---

## CORRECTIONS

**C1. Arxiv Paper Date Error — Smith #11**
Smith #11 describes arxiv 2503.23461 as "dated Feb 27, 2026." Arxiv IDs in format YYMM.NNNNN: "2503" = **March 2025**, not 2026. Smith #11 also parenthetically hedges "March 2025–2026," confirming internal uncertainty. **Correction: Treat this paper as March 2025.** This does not affect the accuracy figures it reports; only the date attribution.

**C2. "GPT Image 1.5" Designation — Smith #11**
Smith #11 cites "GPT Image 1.5: 85–90% text fidelity" (MEDIUM confidence). "GPT Image 1.5" is not a publicly documented OpenAI model designation. Known models: GPT Image 1 (API), GPT-4o (image generation mode). This may be a misidentification of an intermediate/unreleased version or informal practitioner naming. **Correction: Treat this figure as LOW confidence until source is independently verified.**

**C3. VecGlypher Paper Date — Smith #18**
Smith #18 lists VecGlypher as "CVPR 2026, February 2025 paper (arxiv 2602.21461)." Arxiv ID 2602 = **February 2026**, not February 2025. The paper is from February 2026 and was accepted to CVPR 2026 — both dates are internally consistent and consistent with today (2026-08-23). **Correction: The paper date is February 2026, not February 2025 as parenthetically stated.**

---

## DISPUTES

**D1. DALL-E 3 Outperforms GPT-4o? — Internal to Smith #11** ⚠️ GENUINE
Smith #11 reports: DALL-E 3 ~95% (source: modelranked.com reviews, 2026 — MEDIUM confidence) vs. GPT-4o 60.69–82.88% (source: TextAtlasEval peer-reviewed benchmark, April–May 2025 — HIGH confidence). DALL-E 3 is an older model than GPT-4o. This is NOT a stale-vs-fresh issue; both are recent sources. However, methodologies differ entirely: "95% on short strings" is from practitioner reviews with no standardized test or domain control; TextAtlasEval is a rigorous 4,000-sample benchmark across four defined difficulty domains. **RIGOR RULING: TextAtlasEval GPT-4o figures should be treated as more reliable. The DALL-E 3 "~95%" figure is likely methodology-inflated (optimistic conditions, no domain standardization) and should not be compared directly to TextAtlasEval figures. Opus should not treat both as equivalent data points.**

**D2. Qwen-Image Apache 2.0 Status — Smith #14 vs. Smith #20** (Not a genuine conflict)
Smith #14: Qwen-Image = Apache 2.0 (covers versions 1.0/2.0, paper arxiv 2508.02324). Smith #20: Qwen-Image-3.0 = hosted-only proprietary (released August 5, 2026). These are different model versions. **RECENCY RULING: For any current deployment decision, Qwen-Image-3.0 is proprietary. Historical versions 1.0/2.0 remain Apache 2.0 on HuggingFace. Always specify version when citing license.**

**D3. GLM-Image License: MIT vs. Apache-2.0 — Within Smith #20** ⚠️ UNRESOLVED
Smith #20 explicitly flags this conflict. Both licenses allow commercial use, so the practical impact is low — but the exact terms differ. **Status: Unresolved. Verify directly at huggingface.co/zai-org/GLM-Image before citing a specific license.**

**D4. Source Font Neutrality: Conventional Wisdom vs. Research — Smith #12** (Research resolves it)
Conventional practitioner wisdom (pre-2020): simple/neutral source fonts produce better style transfer. Attribute2Font SIGGRAPH 2020: source font choice negligibly impacts output. Not a dispute between Smiths — Smith #12 explicitly resolves in favor of the 2020 research. **Flag for Opus: This is a case of peer-reviewed research overturning practitioner intuition. Older practitioner guidance in this domain should not be cited without noting it is contradicted by SIGGRAPH 2020.**

---

## GAPS — Topics Not Covered by Any Smith in Chain B

**GAP-1. End-to-End Font Production Workflow**
No Smith covers the complete practical pipeline: AI-generated glyph → vectorization → font metrics (kerning pairs, advance widths, hinting, OpenType tables) → production-ready TTF/OTF delivery. Smith #18 covers individual stages in isolation, not integrated end-to-end.

**GAP-2. Two-Letter-Specific Benchmark** *(Documented by Smith #11 itself)*
No published benchmark specifically tests two isolated letters. All accuracy data is extrapolated from "1–4 word" or "short text" categories. This is a confirmed research gap, not a search failure.

**GAP-3. Training Data Transparency for New Apache 2.0 Models**
Smith #14 covers Qwen-Image, Z-Image, ERNIE-Image, FLUX.2-klein. Smith #20 introduces Boogu-Image, GLM-Image, Inkling (all Apache 2.0). No Smith provides training data provenance or font/typeface disclosure analysis for any of these newer models.

**GAP-4. Comprehensive API Pricing Comparison**
Smith #20 mentions Ideogram ($0.035/img) and Grok ($0.02/img fast) but does not provide systematic pricing comparison across Recraft V4, FLUX.1 API, OpenAI Image API, Midjourney subscription tiers, etc.

**GAP-5. Letter Spacing / Kerning Instruction Response**
No Smith covers how models respond to explicit kerning, tracking, or letter-spacing prompt instructions beyond general mentions that Ideogram handles "wide spacing" and "tight tracking" descriptors.

**GAP-6. Color and Gradient Fills in Letterforms**
No Smith covers generation of multi-color, gradient, or textured letterform fills as isolated glyphs — relevant for decorative type use cases.

**GAP-7. Animated / Variable Font Generation**
No Smith covers OpenType variable font axes, animated letterforms, or motion typography — an emerging area entirely absent from Chain B.

**GAP-8. Training Data Copyright for Font Imagery Used AS Training Data**
Smith #15 covers output rights (AI-generated typeface copyrightability). Smith #14 covers what's disclosed in training data. No Smith covers the distinct legal question of whether using existing copyrighted font imagery as training data is lawful — an active litigation area.

**GAP-9. Reve 2.1 Licensing**
Smith #20 explicitly flags Reve 2.1 (strong performer, #2 on Arena) as having licensing "not specified." No follow-up search resolved this. Deployment-blocking gap.

**GAP-10. Style Metrics Validated on Typography-Specific Sets**
Smith #17 covers style metrics for general image sets. No Smith evaluates which metrics are most appropriate or validated for typography-specific consistency (e.g., same-font consistency across a full glyph set, intra-family style coherence).

**GAP-11. Midjourney V8.1 Quantitative Text Benchmarks**
Smith #19 notes MJ V8.1 is the first legible version but provides only qualitative practitioner assessment. No quantitative accuracy figures exist for MJ V8.1 on any text rendering benchmark.

---

## CROSS-CUTTING NOTES FOR OPUS

**1. Recency landscape:** Most data is 2025–2026. The oldest high-confidence data is Attribute2Font (SIGGRAPH 2020, Smith #12) — and it remains the most directly relevant result for source font selection. Legal data in Smith #15 has a hard recency cliff at EU Design Regulation effective May 1, 2025; anything prior is superseded for EU analysis.

**2. Benchmark hierarchy:**
- Highest confidence (peer-reviewed, large-scale): TextAtlasEval (arxiv 2504.05979, 4,000 samples); CVTG-2K (arxiv 2503.23461, 2,000 prompts)
- Medium confidence (practitioner consensus, multi-source): Ideogram 90–95%; img2img strength ranges
- Low confidence (single-source review or subjective): DALL-E 3 ~95% (modelranked.com); FontDiffuser "blurry" (Cozens blog)

**3. Model versions matter critically:**
- Qwen-Image: 1.0/2.0 Apache 2.0 → 3.0 proprietary (active shift)
- Ideogram: 3.0 and 4.0 both cited across Smiths; 4.0 is current
- Midjourney: v6 data (2023–2024) explicitly obsoleted; v8.1 is current baseline
- FLUX: FLUX.1 dev vs. FLUX.2-klein are different model generations with different specs

**4. DINO appears in three distinct contexts across Smiths — Opus should not conflate them:**
- (a) Smith #16: DINO-based **perceptual loss** (requires reference image pair)
- (b) Smith #17: DINO embeddings for **style consistency in sets** (no ground truth needed)
- (c) Smith #17: MEt3R uses DINO features for **multi-view spatial consistency** (pose-free)

**5. Legal synthesis note:** Smith #15's legal analysis is current as of mid-2025 (EU reform effective May 2025; U.S. guidance January 2025; UK *Getty v. Stability AI* November 2025). The landscape for AI-generated typefaces remains unresolved — no case directly on point exists in any jurisdiction. Any legal conclusions Opus draws should carry that caveat explicitly.

---
*Anderson organized. All unique signal preserved. Corrections: 3. Disputes: 4. Gaps: 11. Ready for Opus synthesis.*

---
**Oracle SDK Execution Metrics**
- Architecture: 20 Smiths -> 2 Andersons -> Opus (you)
- Total time: 1058s
- Total tokens: 3,898,227 (in: 113,991 | out: 153,465 | cache r/w: 2,911,063/719,708)
- Quota: 1.00% weekly (7.6% session)
- Smiths: 20 (0 errors)
- Andersons: 2 (0 errors)
- Phase timing: scout: 191s | compress: 867s
- Phase costs: decompose: 0.00% | scout: 0.37% | compress: 0.63%

