# Oracle raw report, round 2: newest reference-generation options (2026-08-23)

Unedited output of a 20-Smith / 2-chain run. Synthesis in
`2026-08-23-the-permissive-local-field-opened-up.md`.

---

============================================================
## Chain A — Anderson Report
============================================================

# Anderson Synthesis Package — Chain A (10 Smiths)
**Compiled:** 2026-08-23 | **Destination:** Opus final synthesis
**Triage applied:** DEDUP · RECENCY · AGREE · DISAGREE · GAPS · CORRECT

---

## MASTER FINDINGS

---

### THEME A — HiDream-O1-Image
*Primary source: Smith #1 | Cross-reference: Smith #5*

#### A1 — Parameters
- **8B base model** | HIGH | Smith #1 (HuggingFace official, GitHub official, May 2026)
- **200B+ Pro variant** exists | HIGH | Smith #1 (arXiv 2605.11061)
- One arXiv reference cites "9B"; primary sources confirm 8B. Smith #1 flags this inconsistency internally. Dominant authoritative reading: **8B**. | Smith #1

#### A2 — License & Commercial Use
- **MIT License** | HIGH | Smith #1 (GitHub LICENSE file, HuggingFace model card)
- **Commercial use: YES** — MIT permits unrestricted commercial use, SaaS, fine-tuning, self-hosted deployment | HIGH | Smith #1
- **⚠ Caveat:** Optional Gemma-4-31B-it prompt agent uses Google Gemini Terms of Service; may create licensing conflict in production | MEDIUM | Smith #1 (third-party analysis, May 2026)

#### A3 — VRAM (Smallest Usable Quantization)
- **FP8 quantization: ~10 GB VRAM** | HIGH | Smith #1 (drbaph/HiDream-O1-Image-FP8)
- **Verified on 12 GB GPUs** (RTX 3080/4070/4080) at 2048×2048 | MEDIUM | Smith #1
- **BF16 (full precision): ~20+ GB** (derived, not directly measured) | MEDIUM | Smith #1
- Hopper/Ada Lovelace GPUs (RTX 40xx, H100) support native FP8 compute; older GPUs dequantize on-the-fly | HIGH | Smith #1

#### A4 — Text-Rendering Benchmarks
- **LongText-Bench-EN: 0.979** | HIGH | Smith #1 (arXiv 2605.11061)
- **LongText-Bench-ZH: 0.978** | HIGH | Smith #1 (arXiv 2605.11061)
- **CVTG-2K:** Achieves highest scores (Table 5) | HIGH | Smith #1 (arXiv 2605.11061)
- Outperforms Qwen-Image (27B) on LongText-Bench | HIGH | Smith #1
- Benchmark source date: arXiv v1 deposited June 2026

#### A5 — Commercial Self-Hosting
- **Self-hosted commercially: YES** (MIT) | HIGH | Smith #1
- Compatible frameworks: **ComfyUI, DiffSynth-Studio** | HIGH | Smith #1 (official GitHub)
- Per-image cost (self-hosted estimate): **$0.008–$0.017** vs $0.04–$0.12 on APIs | MEDIUM | Smith #1 (commercial analysis, May 2026)

#### A6 — Release Dates & URLs
- Released: **May 8, 2026** (GitHub created_at) | HIGH | Smith #1
- arXiv paper: **June 2026** | HIGH | Smith #1
- GitHub: https://github.com/HiDream-ai/HiDream-O1-Image
- HuggingFace (base): https://huggingface.co/HiDream-ai/HiDream-O1-Image
- HuggingFace (Dev): https://huggingface.co/HiDream-ai/HiDream-O1-Image-Dev
- Community FP8: https://huggingface.co/drbaph/HiDream-O1-Image-FP8
- arXiv: https://arxiv.org/abs/2605.11061

---

### THEME B — ERNIE-Image (Baidu)
*Primary source: Smith #2 | Cross-reference: Smith #5*

#### B1 — Parameters & Architecture
- **DiT: 8B parameters** | HIGH | Smith #2 (official GitHub, multiple confirmations)
- **Prompt Enhancer: 3B parameters** (lightweight, built-in) | HIGH | Smith #2
- Architecture: Single-stream Diffusion Transformer (DiT) + integrated Prompt Enhancer | HIGH | Smith #2

#### B2 — License & Commercial Use
- **Apache License 2.0** | HIGH | Smith #2 (official LICENSE file), corroborated Smith #5
- **Commercial use: FULLY PERMITTED** | HIGH | Smith #2
  - Commercial sale of weights, commercial deployment, ads, product imagery, print, resale, modification, distribution, sublicensing of outputs — all allowed
  - No additional commercial agreement required (royalty-free)
  - No China-specific clauses detected in license | HIGH | Smith #2
- **⚠ Inference-layer caveat:** Politically sensitive terms may be blocked in Baidu's cloud API inference; local deployments inherit Baidu content safety filters. Not a license restriction — an operational concern | MEDIUM | Smith #2

#### B3 — VRAM Requirements
| Precision | VRAM | GPU Example | Confidence | Source |
|---|---|---|---|---|
| BF16 (Recommended) | ~24 GB | RTX 4090, H100 | HIGH | Smith #2 |
| FP16 | ~16 GB | RTX 4090, A100 | HIGH | Smith #2 |
| FP8 | ~12–16 GB | RTX 40-series | MEDIUM | Smith #2 |
| INT8 | ~8–10 GB | RTX 3090, consumer | MEDIUM | Smith #2 |
| NVFP4 | <8 GB | Mobile/edge | LOW | Smith #2 |

FP8 recommended for cost/quality balance; RTX 30-series requires software emulation | Smith #2

#### B4 — Text-Rendering Benchmarks
- **LongTextBench (w/ Prompt Enhancer):** 0.9733 average | HIGH | Smith #2 (official April 2026 release docs)
  - English subset: **0.9804** | HIGH | Smith #2
  - Chinese subset: **0.9661** | HIGH | Smith #2
  - Rank: 2nd overall (Seedream 4.5 at 0.9882); **leader among open-weight 8B models** | HIGH | Smith #2
- **GenEval (w/o Prompt Enhancer):** 0.8856 overall | HIGH | Smith #2
  - Single Object: 1.0000 (perfect)
  - Two Objects: 0.9596
  - Attribute Binding: 0.7925
- **OneIG-EN:** Overall 0.5750 (3rd rank); Text subscore 0.9788 | HIGH | Smith #2
- **OneIG-ZH:** Overall 0.5543; Text subscore 0.9539 | HIGH | Smith #2
- Benchmark date: April 2026 (official release) | HIGH | Smith #2
- Smith #5 cites same 0.9733 LongTextBench score | MEDIUM | Smith #5 (secondary citation without primary source access — lower confidence; **Smith #2 is primary and authoritative**)

#### B5 — Inference & Deployment
- Standard: 50 steps (CFG 4.0) — quality-optimized | HIGH | Smith #2
- Turbo: 8 steps (CFG 1.0) — speed-optimized (DMD + RL distillation) | HIGH | Smith #2
- Compatible frameworks: Diffusers (PyTorch), SGLang, ComfyUI, vLLM (Prompt Enhancer only) | HIGH | Smith #2

#### B6 — Release Date & URLs
- **Released: April 15, 2026** | HIGH | Smith #2, corroborated Smith #5
- HuggingFace (Standard): https://huggingface.co/baidu/ERNIE-Image
- HuggingFace (Turbo): https://huggingface.co/baidu/ERNIE-Image-Turbo
- GGUF (Unsloth): https://huggingface.co/unsloth/ERNIE-Image-GGUF | MEDIUM | Smith #2
- GGUF (Vantage): https://huggingface.co/vantagewithai/ERNIE-Image-GGUF-Base-Turbo | MEDIUM | Smith #2
- GitHub: https://github.com/baidu/ERNIE-Image
- Official site: https://ernie-image.net/ (Smith #5)

---

### THEME C — Z-Image & Z-Image-Turbo (Tongyi-MAI / Alibaba)
*Primary source: Smith #3 | Cross-reference: Smith #5*

#### C1 — Parameters (Both Models)
- **Z-Image: 6B** | HIGH | Smith #3 (HuggingFace: Tongyi-MAI/Z-Image)
- **Z-Image-Turbo: 6B** | HIGH | Smith #3 (HuggingFace: Tongyi-MAI/Z-Image-Turbo)

#### C2 — License (Both Models)
- **Apache 2.0** (both models) | HIGH | Smith #3

#### C3 — Architecture
- **Scalable Single-Stream DiT (S3-DiT)** — unified sequence of text, visual semantic tokens, and VAE tokens | HIGH | Smith #3

#### C4 — VRAM Requirements

**Z-Image-Turbo:**
| Precision | VRAM | Confidence |
|---|---|---|
| BF16 (full precision) | 14–16 GB | MEDIUM |
| FP8 | 8 GB | MEDIUM |
| GGUF (quantized) | 6 GB | MEDIUM |
Sub-second latency threshold: 16 GB consumer GPUs (RTX 3090/4090) | HIGH | Smith #3

**Z-Image (Standard):**
- **24 GB** (standard/baseline) | HIGH | Smith #3

#### C5 — Generation Speed (Z-Image-Turbo)
- **Enterprise H800:** <1 second (sub-second) | MEDIUM | Smith #3
- **RTX 4090 (24GB), 1024×1024, 8 steps:** 3.4 seconds | MEDIUM | Smith #3 (WaveSpeed AI blog)
- **Managed cluster / mid-range GPUs:** 2–4 seconds (<10 seconds) | MEDIUM | Smith #3 (fal.ai)
- **June 2026 update:** Median dropped from ~6s to ~4s for 1024×1024 | MEDIUM | Smith #3

**Z-Image (Standard):**
- **RTX 4090 (24GB), 20 steps:** 4.2 seconds | MEDIUM | Smith #3
- **Default 50 steps:** ~10+ seconds (estimated) | LOW | Smith #3

#### C6 — Image-to-Image & Conditioning
- **Both models NOW support img2img** as of August 2026 (previously text-to-image only) | HIGH | Smith #3
- **Z-Image-Turbo:**
  - Native img2img: ZImageImg2ImgPipeline | HIGH | Smith #3 (fal.ai)
  - ControlNet (Fun ControlNet Union 2.1): Canny, depth, pose, MLSD, HED, scribble, gray, inpaint | HIGH | Smith #3
    - Latest version: 2601 (January 2026), adds Scribble Control | HIGH | Smith #3
    - Lite models: 1.9 GB (5 layers); Full: 15 layers + 2 refiner layers | MEDIUM | Smith #3
    - Multi-resolution: 512–1536px; Training: 1M images at 1328px, bfloat16 | HIGH | Smith #3
- **Z-Image (Standard):**
  - Structural ControlNet conditioning, semantic conditioning, img2img via ZImageImg2ImgPipeline | HIGH | Smith #3 (GitHub issue #20)
- **Output Resolution:** 512×512 to 2048×2048 (any aspect ratio, total pixel area) | HIGH | Smith #3

#### C7 — Release Dates & URLs
- Z-Image-Turbo: December 2025 | MEDIUM | Smith #3
- Z-Image (standard): January 28, 2026 | MEDIUM | Smith #3
- ControlNet Union 2.1: January 2026 | HIGH | Smith #3
- June 2026 performance update | HIGH | Smith #3
- HuggingFace (Z-Image): https://huggingface.co/Tongyi-MAI/Z-Image
- HuggingFace (Z-Image-Turbo): https://huggingface.co/Tongyi-MAI/Z-Image-Turbo
- HuggingFace (ControlNet): https://huggingface.co/alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union-2.1

---

### THEME D — FLUX.2 Family (Black Forest Labs)
*Primary source: Smith #4 | Cross-reference: Smith #5*

#### D1 — License Matrix
| Variant | License | Self-Hosted Commercial Use (No Paid Agreement) | Confidence |
|---|---|---|---|
| FLUX.2 [klein] 4B | Apache 2.0 | **YES** ✅ | HIGH |
| FLUX.2 [klein] 4B Base | Apache 2.0 | **YES** ✅ | HIGH |
| FLUX.2 [klein] 9B | FLUX Non-Commercial License v2.1 | **NO** ❌ | HIGH |
| FLUX.2 [klein] 9B Base | FLUX Non-Commercial License v2.1 | **NO** ❌ | HIGH |
| FLUX.2 [klein] 9B KV | FLUX Non-Commercial License v2.1 | **NO** ❌ | HIGH |
| FLUX.2 [dev] | FLUX [dev] Non-Commercial License v2.0 | **NO** ❌ | HIGH |

Source: Black Forest Labs official flux2 repo, README + /model_licenses/ | HIGH | Smith #4

#### D2 — Commercial Licensing Details
- **Outputs** from non-commercial models (Klein 9B, Dev) *may* be used commercially without restriction (Section 2.d of non-commercial license) | HIGH | Smith #4
- Commercial self-hosting licenses for Klein 9B/9B-KV/Dev available via tiered plans (Builder, Platform, Professional, Enterprise) at https://bfl.ai/legal/self-hosted-commercial-license-terms | HIGH | Smith #4
- **Klein 4B / 4B Base:** No restrictions whatsoever under Apache 2.0 — full commercial use, modification, redistribution without paid agreement | HIGH | Smith #4

#### D3 — Parameters & Model Scope
- Klein 4B: **4B parameters** | HIGH | Smith #4, Smith #5
- Klein 9B variants: **9B parameters** | HIGH | Smith #4
- No other FLUX.2 variants released as open-weight models as of August 2026 (FLUX.2 Pro, FLUX.2 Ultra exist as API-only, no downloadable weights) | HIGH | Smith #4
- **⚠ NOTE — Dispute flagged in §DISPUTES below:** Smith #5 describes Klein 4B as "4B (Klein variant, full model 12B)" — see DISPUTES.

#### D4 — Text Rendering
- Klein 4B/9B specialized for typography and text rendering; excels at readable text in images | MEDIUM | Smith #5 (no specific benchmark score cited)

#### D5 — Release Date & URLs
- First FLUX.2 release: **January 15, 2026** | HIGH | Smith #5 (Black Forest Labs blog)
- GitHub: https://github.com/black-forest-labs/flux2
- HuggingFace (Klein 4B): https://huggingface.co/black-forest-labs/FLUX.2-klein-4B
- Docs: https://docs.bfl.ml/flux_2/flux2_overview
- Commercial license: https://bfl.ai/legal/self-hosted-commercial-license-terms

---

### THEME E — Boogu-Image 0.1
*Primary source: Smith #5*

#### E1 — Core Specifications
- **Parameters: 10B** (Base), **10B distilled** (Turbo variant) | HIGH | Smith #5
- **License: Apache 2.0** | HIGH | Smith #5 (GitHub, HuggingFace)
- **Release dates:** Base June 16, 2026 | Turbo June 25, 2026 | HIGH | Smith #5

#### E2 — Text Rendering
- Renders **100+ characters** accurately at 2K resolution | HIGH | Smith #5
- **Bilingual:** Chinese/English | HIGH | Smith #5
- **Qwen-Image-Bench score: 53.58** (#1 among open-source at release) | HIGH | Smith #5
- arXiv technical report: arXiv:2607.13125 (July 16, 2026) | HIGH | Smith #5

#### E3 — URLs
- HuggingFace (Base): https://huggingface.co/Boogu/Boogu-Image-0.1-Base
- HuggingFace (Turbo): https://huggingface.co/Boogu/Boogu-Image-0.1-Turbo-hotfix
- GitHub: https://github.com/boogu-project/Boogu-Image

*Note: VRAM requirements for Boogu-Image 0.1 not reported by any Smith — see GAPS.*

---

### THEME F — Permissive T2I Landscape: Models Outside Criteria (Smith #5)
*Context for Opus: scope-boundary findings from Smith #5*

Models **excluded** from permissive-license category (June–Aug 2026 window):

| Model | Release | Size | Reason Excluded |
|---|---|---|---|
| Ideogram 4.0 | June 3, 2026 | 9.3B | Code Apache-2.0; **weights under non-commercial Ideogram NCMA** — commercial use requires paid license |
| Krea 2 | June 22, 2026 | 12.9B Raw / distilled Turbo | **Custom Krea 2 Community License** (not Apache/MIT/CC-BY); revenue cap ($1M); content moderation required |
| Cosmos3-Super-Text2Image | May/June 2026 | 64B | **OpenMDW1.1 license** (not Apache/MIT/CC-BY) |

Key URLs (Smith #5):
- Krea 2 licensing: https://www.krea.ai/krea-2-licensing
- Ideogram licensing: https://ideogram.ai/licensing/

---

### THEME G — Qwen-Image-Edit-2511: Quantizations
*Primary source: Smith #6 | Cross-reference: Smith #9*

#### G1 — GGUF (Unsloth)
- Repo: https://huggingface.co/unsloth/Qwen-Image-Edit-2511-GGUF
- Method: GGUF with Unsloth Dynamic 2.0 (important layers upcasted)
- CPU-compatible

| Variant | File Size | VRAM | 24 GB OK? | Confidence |
|---|---|---|---|---|
| Q4_K_M | 13.2 GB | ~14 GB | ✅ | HIGH |
| Q4_0 | 11.9 GB | ~12 GB | ✅ | HIGH |
| Q5_K_S | 14.3 GB | ~15 GB | ✅ | HIGH |
| Q8_0 | 21.8 GB | ~22 GB | ✅ (tight) | HIGH |

Quality loss: Minimal for Q4; important layers preserved via upcast. No quantitative degradation documented. | MEDIUM | Smith #6

**⚠ INTERNAL INCONSISTENCY (Smith #6):** Body text attributes Q8_0 (21.8 GB) to **unsloth** repo, but summary table cites **"calcuis/qwen-image-edit-gguf"** for Q8_0 — these are different HuggingFace repos. See DISPUTES.

Files: https://huggingface.co/unsloth/Qwen-Image-Edit-2511-GGUF/tree/main

#### G2 — FP8
**drbaph repo:**
- https://huggingface.co/drbaph/Qwen-Image-Edit-2511-FP8
- File: `qwen_image_edit_2511_fp8_e4m3fn.safetensors` | 20.4 GB | ~20.5 GB VRAM | ✅ 24 GB | HIGH (size) / MEDIUM (VRAM) | Smith #6

**1038lab repo:**
- https://huggingface.co/1038lab/Qwen-Image-Edit-2511-FP8
- File: `Qwen-Image-Edit-2511-FP8_e4m3fn.safetensors` | 20.4 GB | ~20.5 GB VRAM | ✅ 24 GB | HIGH (size) / MEDIUM (VRAM) | Smith #6

Quality: "Maintains editing fidelity" | HIGH | Smith #6
⚠ Known artifact: FP8 2511 base + BF16 2511 Lightning 4-step LoRA combo produces visible artifacts; FP8 mixed variant (with BF16 LoRA) superior to FP8 scaled variant | MEDIUM | Smith #6 (community-reported)

#### G3 — NF4 Quantization (4-bit bitsandbytes)
- **ovedrive:** https://huggingface.co/ovedrive/Qwen-Image-Edit-2511-4bit | ~17 GB | 16–20 GB VRAM | ✅ 24 GB | MEDIUM (size estimated) | Smith #6
- **toandev:** https://huggingface.co/toandev/Qwen-Image-Edit-2511-4bit | Size not stated | 16–24 GB VRAM | ✅ | "Minimal quality loss" (vendor claim) | LOW | Smith #6
- **mash2005 Multi-Angles:** https://huggingface.co/mash2005/Qwen-Image-Edit-2511-MultiAngles-Q4 | NF4 with double quantization | <20 GB (claimed) | ✅ | Multi-angle generation support | LOW | Smith #6

#### G4 — INT4 SVDQuant (Nunchaku) — Community Build
Repo: https://huggingface.co/QuantFunc/Nunchaku-Qwen-Image-EDIT-2511
Framework: Nunchaku 1.3.0+
**Status: Community build (QuantFunc), NOT official Nunchaku** | HIGH | Smith #6, Smith #9

| Variant | File Size | VRAM (w/ per-layer offload) | 24 GB OK? | Confidence |
|---|---|---|---|---|
| Best Quality INT4 | 14.2 GB | 3–4 GB | ✅ | HIGH |
| Balance INT4 | ~13–14 GB | 3–4 GB | ✅ | MEDIUM |
| Ultimate Speed INT4 | 11.5 GB | 3–4 GB | ✅ | HIGH |
| Best Quality FP4 | Not stated | 3–4 GB | ✅ | MEDIUM |

- Per-layer offloading enables RTX 2060 Super (8 GB) to run model | HIGH | Smith #6
- 2×–11× speedup over BF16/FP16 | MEDIUM | Smith #6, Smith #9
- FP4 variants also available | HIGH | Smith #6
- Files: https://huggingface.co/QuantFunc/Nunchaku-Qwen-Image-EDIT-2511/tree/main

#### G5 — INT4 SVDQuant (nunchaku-tech official — for 2509 base, not 2511)
Repo: https://huggingface.co/nunchaku-tech/nunchaku-qwen-image-edit

| Variant | File Size | VRAM | 24 GB OK? | Confidence |
|---|---|---|---|---|
| svdq-int4_r128 | 12.7 GB | ~13 GB | ✅ | HIGH |
| svdq-int4_r32 | 11.5 GB | ~12 GB | ✅ | HIGH |

r128 = better quality; r32 = faster. Pre-Blackwell GPU support (RTX 20/30/40 series) | HIGH | Smith #6
**Note on org name:** Smith #6 calls this "nunchaku-tech"; Smith #9 says official org is "nunchaku-ai" — see DISPUTES.

#### G6 — Missing Quantization Formats
- **AWQ:** No public quantization found | HIGH | Smith #6 (comprehensive search)
- **GPTQ:** No public quantization found | HIGH | Smith #6

#### G7 — Quality Loss Ranking (Best → Worst, per Smith #6)
1. FP8 — Near-BF16 quality (−50% VRAM)
2. GGUF Q8_0 — Minimal loss
3. INT4 SVDQuant (Best Quality) — Documented quality-speed tradeoff
4. GGUF Q4_K_M — Acceptable; important layers preserved
5. NF4 Q4 — Claimed minimal; poorly documented
6. INT4 SVDQuant (Ultimate Speed) — Noticeable but acceptable

#### G8 — Optimal 24 GB Picks (per Smith #6)
1. FP8 (20.4 GB) — Best quality-to-size ratio; no CPU offload
2. GGUF Q5_K_S (14.3 GB) — CPU-compatible, headroom for overhead
3. Nunchaku Best Quality INT4 (14.2 GB) — Fastest with offload support
4. GGUF Q8_0 (21.8 GB) — Highest precision GGUF (tight)

---

### THEME H — Qwen-Image-Edit-2511: Inference Speed
*Primary source: Smith #7*

**⚠ Overarching caveat (Smith #7):** No official independent benchmarks for RTX 3090/4090-class 24 GB cards at 1024×1024 exist. Consumer GPU figures are aggregated from user/community reports. Times vary by quantization (most reports unspecified). A100 figures NOT directly extrapolatable to RTX 4090.

#### H1 — Consumer GPU Benchmarks (Community-Reported)
| GPU | Steps | Resolution | Time | VRAM Used | Confidence | Source |
|---|---|---|---|---|---|---|
| RTX 4090 (24 GB) | 4-step Lightning LoRA | 1024×1024 | ~14 sec | — | MEDIUM | HuggingFace Discussion #18, 2025 |
| RTX 3090 (24 GB) | 8-step LoRA | 1024×1024 | ~36 sec | 17 GB+ | MEDIUM | HuggingFace Discussion #18, 2025 |

#### H2 — Cloud / Server Benchmarks
| Hardware | Steps | Resolution | Latency | Confidence | Source |
|---|---|---|---|---|---|
| A100 80 GB | 4 steps | 1024×1024 | 5.10 sec | HIGH | Replicate, 2025 |
| A100 80 GB | 2 steps | 1024×1024 | 2.70 sec | HIGH | Replicate, 2025 |
| H100 80 GB | 40 steps (full) | — | ~45 sec | MEDIUM | Multiple reports, 2025 |
| H100 80 GB | 100 steps | — | ~60 sec | MEDIUM | Multiple reports, 2025 |
| SGLang serving | Single request | — | 35.3 sec latency; 47.96 GB peak VRAM | HIGH | SGLang docs, 2025 |

#### H3 — Default Parameters & Step Ratios
- **Default steps:** 28 | HIGH | Smith #7 (fal.ai API docs)
- **Lightning LoRA standard:** 4 steps | HIGH | Smith #7
- **Full model (unoptimized):** 40 steps | HIGH | Smith #7
- Lightning ~10× faster than 40-step unoptimized | HIGH | Smith #7 (LightX2V GitHub)
- **LightX2V distillation:** 42.55× overall speedup; 25× fewer DiT operations | MEDIUM | Smith #7 (HuggingFace Discussions)

---

### THEME I — Qwen-Image-Edit-2511: Diffusers API
*Primary source: Smith #8*

#### I1 — Pipeline Class Name
**`QwenImageEditPlusPipeline`** | HIGH | Smith #8 (official HuggingFace docs, multiple source implementations)

#### I2 — Minimal Working Code
```python
import torch
from PIL import Image
from diffusers import QwenImageEditPlusPipeline

pipeline = QwenImageEditPlusPipeline.from_pretrained(
    "Qwen/Qwen-Image-Edit-2511", torch_dtype=torch.bfloat16
)
pipeline.to('cuda')

image1 = Image.open("input1.png")
image2 = Image.open("input2.png")

prompt = "The magician bear is on the left, the alchemist bear is on the right, facing each other in the central park square."

output = pipeline(
    image=[image1, image2],
    prompt=prompt,
    generator=torch.manual_seed(0),
    true_cfg_scale=4.0,
    negative_prompt=" ",
    num_inference_steps=40,
    guidance_scale=1.0,
    num_images_per_prompt=1,
)
output.images[0].save("output_image_edit_2511.png")
```
Source: Official HuggingFace Model Card | HIGH | Smith #8

#### I3 — Required Diffusers Version
- **Latest dev from GitHub** (no specific version number documented) | MEDIUM | Smith #8
- `pip install git+https://github.com/huggingface/diffusers`
- Historical compatibility: diffusers v0.31.0+; exact minimum unspecified | Smith #8

#### I4 — Pipeline Call Inputs
**Required:**
- `image`: Single PIL Image or list of PIL Images (up to 3 reference images) | HIGH | Smith #8
- `prompt`: String — edit instruction | HIGH | Smith #8

**Key Optional Parameters:**
| Parameter | Notes | Confidence |
|---|---|---|
| `num_inference_steps` | Default 28; typical 40–50 | HIGH |
| `true_cfg_scale` | **Primary CFG control** (standard `guidance_scale` is ineffective alone) | HIGH |
| `negative_prompt` | Even empty string `" "` enables CFG computation | HIGH |
| `guidance_scale` | Often set to 1.0 when using `true_cfg_scale` | MEDIUM |
| `generator` | torch Generator for reproducibility | HIGH |
| `num_images_per_prompt` | Integer | MEDIUM |

⚠ Key implementation note: Use `true_cfg_scale` + `negative_prompt` for effective CFG — NOT standard `guidance_scale` alone | HIGH | Smith #8

#### I5 — Supported Resolutions
- **Native:** 1024×1024 | HIGH | Smith #8
- **Supported range:** 256–2560 px | MEDIUM | Smith #8
- **Optimal for quality:** 1920×1920; 2560×2560 (best) | MEDIUM | Smith #8
- **Multi-image:** Up to 3 input reference images | HIGH | Smith #8

#### I6 — Implementation Notes
- Use `torch.bfloat16` dtype | HIGH | Smith #8
- Pipeline concatenates multiple input images automatically | HIGH | Smith #8

#### I7 — Documentation URLs
- Diffusers Pipeline Docs (latest): https://huggingface.co/docs/diffusers/main/en/api/pipelines/qwenimage
- Diffusers Docs (Stable v0.35.1): https://huggingface.co/docs/diffusers/v0.35.1/api/pipelines/qwenimage
- Official Model Card: https://huggingface.co/Qwen/Qwen-Image-Edit-2511
- Diffusers Source: https://github.com/huggingface/diffusers/blob/main/src/diffusers/pipelines/qwenimage/pipeline_qwenimage_edit.py
- vLLM Usage Guide: https://docs.vllm.ai/projects/recipes/en/stable/Qwen/Qwen-Image.html

---

### THEME J — Qwen-Image-Edit-2511: Nunchaku / SVDQuant
*Primary source: Smith #9 | Cross-reference: Smith #6*

#### J1 — Official Nunchaku Status for 2511
- **No official Nunchaku build for Qwen-Image-Edit-2511 exists** as of August 2026 | HIGH | Smith #9
- GitHub Issue #871 ("Any plans to support qwen image edit 2511?") opened January 7, 2026 — **remains open, unresolved** | HIGH | Smith #9
- Official Nunchaku only has builds for **Qwen-Image-Edit-2509** at: https://huggingface.co/nunchaku-ai/nunchaku-qwen-image-edit-2509 | HIGH | Smith #9

#### J2 — Community Build (QuantFunc)
- Repo: https://huggingface.co/QuantFunc/Nunchaku-Qwen-Image-EDIT-2511
- Third-party, not official Nunchaku project | HIGH | Smith #9
- Speedup: **2×–11×** over standard BF16/FP16 | MEDIUM | Smith #9
- Concrete example: Forge-Neo + Nunchaku = **19 sec** vs standard 34 sec and ComfyUI standard 32 sec | MEDIUM | Smith #9 (DCAI blog ~2026)
- RTX 4090: **8.7× speedup**, **3× faster** than NF4 W4A16 baseline | LOW | Smith #9 (single benchmark, unclear context)
- VRAM: **3–4 GB minimum** with per-layer CPU offloading | MEDIUM | Smith #9
- Async CPU offloading (`set_offload()`): reduces Transformer VRAM to ~3 GB with "no performance loss" (vendor claim) | MEDIUM | Smith #9

#### J3 — LoRA Loading (QuantFunc Community Build)
- **Runtime LoRA loading: Supported** in community build (4-step LoRA workflow for ComfyUI; best-quality/balanced/ultimate-speed variants with integrated LoRA) | MEDIUM | Smith #9
- ⚠ Note: Described as "4-step LoRA workflow" — may be pre-quantized LoRA variants rather than fully dynamic loading | Smith #9
- **Known bug (official Nunchaku ComfyUI plugin):** Issue #557 — "qwen image edit does not support Lora loading" | HIGH | Smith #9 (GitHub, 2026)
- Third-party workaround: https://github.com/ussoewwin/ComfyUI-QwenImageLoraLoader | HIGH | Smith #9

#### J4 — Official Nunchaku URLs
- GitHub: https://github.com/nunchaku-ai/nunchaku
- HuggingFace org: https://huggingface.co/nunchaku-ai
- Official 2509 build: https://huggingface.co/nunchaku-ai/nunchaku-qwen-image-edit-2509
- Community 2511 build: https://huggingface.co/QuantFunc/Nunchaku-Qwen-Image-EDIT-2511

---

### THEME K — Qwen-Image Ecosystem & Model Timeline
*Primary source: Smith #10*

#### K1 — Full Model Timeline
| Model | Release Date | Type | License | Parameters | Status | Confidence |
|---|---|---|---|---|---|---|
| Qwen-Image | Aug 4, 2025 | Generation + Editing | Apache 2.0 | 20B | Superseded | HIGH |
| Qwen-Image-Edit-2509 | Sept 22, 2025 | Edit-only | Apache 2.0 | 20B | Superseded | HIGH |
| Qwen-Image-Edit-2511 | Dec 23, 2025 | Edit-only | Apache 2.0 | **20B (MMDiT, dense — all 20B active per step, not MoE)** | Latest edit-only | HIGH |
| Qwen-Image-2.0 | Feb 10, 2026 | Generation + Editing (unified) | Apache 2.0 | **7B** *(see §CORRECTIONS — internal conflict)* | Latest open unified | HIGH |
| Qwen-Image-3.0 | July 21, 2026 | Generation + Editing | **Closed / No weights** | Unknown | Latest overall, closed | HIGH |

All dates: HIGH | Smith #10 (official Qwen blogs, multiple sources)

#### K2 — Qwen-Image-Edit-2511 Architecture Detail (Smith #10)
- **20B MMDiT, dense** — all 20B parameters active per inference step, NOT a mixture-of-experts model | HIGH | Smith #10
- Improvements vs 2509:
  - Character consistency: significantly improved multi-person consistency
  - Image drift: reduced during editing
  - Industrial design: enhanced product design / material replacement
  - Geometric reasoning: stronger spatial/geometric accuracy
  - Multi-image editing: person-person, person-product, person-scene combos
  - ControlNet: depth maps, edge maps, keypoint maps
  - Integrated popular LoRAs directly into base model

#### K3 — Qwen-Image-2.0 (Latest Open Unified)
- Released: **February 10, 2026** | HIGH | Smith #10
- Apache 2.0 | HIGH | Smith #10
- Architecture: 8B Qwen3-VL encoder + 7B diffusion decoder (unified generation + editing in one model)
- ⚠ **Conflicting size claim within Smith #10:** See §CORRECTIONS
- Native 2K (2048×2048) resolution | HIGH | Smith #10
- Prompt capacity: ~1K tokens | HIGH | Smith #10
- Ranked #1 on AI Arena for both T2I generation and editing (at release) | HIGH | Smith #10
- GitHub: https://github.com/QwenLM/Qwen-Image (last pushed Feb 10, 2026)
- HuggingFace: https://huggingface.co/Qwen/Qwen-Image-2.0

#### K4 — Qwen-Image-3.0 (Closed Source)
- Released: **July 21, 2026** | HIGH | Smith #10
- **No weights available** — access only via Qwen Chat interface | HIGH | Smith #10
- **No benchmarks published** | HIGH | Smith #10
- **No parameter count disclosed** | HIGH | Smith #10
- Key capability upgrades vs 2.0:
  - 4.5K-token instruction limit (vs ~1K in 2.0)
  - Fine text: 10-pixel text capability
  - Native multilingual rendering: 12 languages; 20+ fonts; 100+ visual styles
  - Complex layout handling
  - Reference-preserving image editing
- Focus: Practical, text-heavy, layout-driven content (infographics, documents) over artistic images
- Official blog: https://qwenimages.com/blog/qwen-image-3-release

#### K5 — Confirmed: 2511 Remains Latest Edit-Specific Model
- As of August 23, 2026: **Qwen-Image-Edit-2511 (Dec 23, 2025) is the latest edit-only model** | HIGH | Smith #10
- No newer Edit-specific model released post-2511
- Qwen-Image-3.0 is closed-source unified, not an edit-only model

---

## CORRECTIONS

### CORRECTION 1 — Qwen-Image-2.0 Parameter Count (Smith #10, internal conflict)
- Smith #10 states **"7B parameters (unified encoder-decoder)"** in the headline summary
- Smith #10 then describes the architecture as **"8B Qwen3-VL encoder + 7B diffusion decoder"**
- 8B + 7B = **15B total**, not 7B
- These figures conflict within a single Smith report
- **Most likely interpretation:** "7B" refers to the diffusion decoder component alone; total model is ~15B (or the 8B encoder is shared/frozen from Qwen3-VL)
- **⚠ Opus should verify:** Actual total parameter count of Qwen-Image-2.0 is **ambiguous in source material** — treat as disputed until confirmed

### CORRECTION 2 — Smith #6 GGUF Q8_0 Repo Attribution (Smith #6, internal inconsistency)
- Body text attributes Q8_0 (21.8 GB) to **unsloth** repo
- Summary table cites **"calcuis/qwen-image-edit-gguf"** for Q8_0
- These are **different HuggingFace repositories** — one or both attributions may be wrong
- **Retained both** in findings under G1 (body = unsloth); summary table entry noted
- **⚠ Opus / downstream:** Verify which repo actually hosts the 21.8 GB Q8_0 file

### CORRECTION 3 — HiDream-O1-Image "9B" Reference (Smith #1, flagged internally)
- Smith #1 self-flags: one arXiv reference mentions "9B"; primary sources (official GitHub, HuggingFace) cite **8B**
- Dominant authoritative reading: **8B** is correct
- Filed as a known source inconsistency, not a genuine dispute

---

## DISPUTES

### DISPUTE 1 — FLUX.2 Klein 4B: Standalone vs. "Full Model 12B" (Smith #4 vs. Smith #5)
- **Smith #4** (primary, official BFL repo): Klein 4B = a discrete **4B parameter model**; no "12B full model" mentioned
- **Smith #5:** "4B (Klein variant, full model 12B)" — implies Klein 4B is a 4B distillation of a 12B backbone
- These are not reconcilable from the available data
- **Smith #4 is higher confidence** (primary source: official GitHub + HuggingFace), but Smith #5's "12B" claim may reflect an underlying architecture detail
- **⚠ Opus:** Treat FLUX.2 Klein 4B total parameter count as **uncertain**; 4B is the deployable weight count (high confidence); 12B backbone claim is unverified

### DISPUTE 2 — Nunchaku HuggingFace Org Name (Smith #6 vs. Smith #9)
- **Smith #6** identifies the official Nunchaku org as **"nunchaku-tech"** (https://huggingface.co/nunchaku-tech/nunchaku-qwen-image-edit)
- **Smith #9** identifies it as **"nunchaku-ai"** (https://huggingface.co/nunchaku-ai/nunchaku-qwen-image-edit-2509; GitHub: https://github.com/nunchaku-ai/nunchaku)
- These may be two separate HuggingFace orgs (one official, one community mirror) OR a naming inconsistency in Smith reports
- **Smith #9 is higher confidence** for official org ("nunchaku-ai") as it cites the GitHub repo directly; "nunchaku-tech" (Smith #6) may be a community mirror
- **⚠ Opus:** Treat "nunchaku-ai" as the likely official org; verify "nunchaku-tech" status

### DISPUTE 3 — Qwen-Image-2.0 Total Parameter Count (Smith #10, internal — escalated to Opus)
- (See CORRECTION 1 above) — escalated as a dispute because the 7B vs. 15B gap is material for VRAM planning

---

## GAPS (Topics Uncovered or Underspecified)

| # | Gap | Relevant Theme | Notes |
|---|---|---|---|
| G-01 | **Boogu-Image 0.1 VRAM requirements** — not reported by any Smith | Theme E | Critical for self-hosting decisions; 10B model |
| G-02 | **FLUX.2 Klein 4B text-rendering benchmark scores** — qualitative only, no numeric benchmarks | Theme D | Smith #5 explicitly notes absence |
| G-03 | **HiDream-O1-Image BF16 VRAM** — only derived (~20+ GB), not directly measured | Theme A | Derived from FP8 being ~half |
| G-04 | **Z-Image / Z-Image-Turbo text-rendering benchmark scores** — no LongTextBench or equivalent cited | Theme C | Only qualitative capability statements |
| G-05 | **Qwen-Image-3.0 parameters, benchmarks, VRAM** — all unknown (closed model) | Theme K | Alibaba released no specs |
| G-06 | **Qwen-Image-2.0 VRAM requirements** — not covered by any Smith | Theme K | 7B or 15B ambiguity makes this more critical |
| G-07 | **Independent RTX 3090/4090 benchmarks for Qwen-Image-Edit-2511** — only community-reported estimates | Theme H | Smith #7 explicitly flags; A100 data is reliable, consumer not |
| G-08 | **AWQ / GPTQ quantizations for Qwen-Image-Edit-2511** — confirmed absent (not a gap in knowledge, but a gap in available tooling) | Theme G | HIGH confidence: neither exists publicly |
| G-09 | **Boogu-Image text-rendering benchmark methodology** — Qwen-Image-Bench (53.58) cited but metric definition/full leaderboard not elaborated | Theme E | Limits cross-model comparability |
| G-10 | **HiDream-O1-Image 200B+ Pro variant** — exists (arXiv 2605.11061) but no VRAM, license, or availability details provided | Theme A | May be API-only or unreleased weights |
| G-11 | **Minimum diffusers version for Qwen-Image-Edit-2511** — no specific version number documented; only "install from GitHub main" | Theme I | Blocking for reproducible env setups |
| G-12 | **ERNIE-Image: Seedream 4.5 details** — cited as #1 on LongTextBench (0.9882) but no coverage of Seedream 4.5 as a standalone model | Cross-theme | If Opus needs full leaderboard context |

---

## AGREEMENT SIGNALS (Multi-Smith Convergence = Highest Confidence)

| Finding | Agreement | Smiths |
|---|---|---|
| ERNIE-Image: Apache 2.0 license | ✅ Agree | Smith #2, Smith #5 |
| ERNIE-Image: 8B DiT parameters | ✅ Agree | Smith #2, Smith #5 |
| ERNIE-Image: LongTextBench 0.9733 | ✅ Agree (Smith #2 is primary) | Smith #2, Smith #5 |
| ERNIE-Image: Released April 15, 2026 | ✅ Agree | Smith #2, Smith #5 |
| FLUX.2 Klein 4B: Apache 2.0, commercial OK | ✅ Agree | Smith #4, Smith #5 |
| FLUX.2 Klein 9B+: Non-commercial license | ✅ Agree | Smith #4, Smith #5 |
| Z-Image & Z-Image-Turbo: Apache 2.0, 6B | ✅ Agree | Smith #3, Smith #5 |
| QuantFunc INT4 community build exists for 2511 | ✅ Agree | Smith #6, Smith #9 |
| No official Nunchaku 2511 build (as of Aug 2026) | ✅ Agree | Smith #6 (by implication), Smith #9 |
| Qwen-Image-Edit-2511: Apache 2.0 | ✅ Agree | Smith #6, Smith #7, Smith #8, Smith #9, Smith #10 |
| Qwen-Image-Edit-2511: Released Dec 23, 2025 | ✅ Agree | Smith #6–#10 |
| Qwen-Image-3.0: Closed, no weights, no benchmarks | ✅ Agree (sole Smith, high confidence) | Smith #10 |
| Boogu-Image 0.1: Apache 2.0, 10B, June 2026 | ✅ Agree (sole Smith) | Smith #5 |

---

*All findings preserved for Opus. No compression applied. Recency applied where noted (ERNIE benchmarks: Smith #2 primary over Smith #5 secondary citation). Disputes and corrections explicitly flagged. All URLs retained as reported.*

============================================================
## Chain B — Anderson Report
============================================================

# ANDERSON SYNTHESIS PACKAGE — CHAIN B (Smiths #11–#20)
### Prepared for Opus | Date: 2026-08-23 | Do not editorially compress

---

## ⚠️ CRITICAL FLAGS (Read Before All Else)

### FLAG 1 — Smith #12 "Nano Banana Pro": PROBABLE HALLUCINATION — HIGH CONCERN

Smith #12 reports on a model called **"Nano Banana Pro" (official designation: "Gemini 3 Pro Image")** from Google. **No such Google model exists by this name in any verified corpus.** Indicators of fabrication:

- The model name "Nano Banana Pro" does not appear in any Google AI, DeepMind, or Google Cloud official naming convention.
- All cited "official" URLs (e.g., `https://ai.google.dev/gemini-api/docs/models/gemini-3-pro-image`, `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-pro-image`) cannot be verified against known Google product lines as of Aug 2026.
- Third-party sources cited (glbgpt.com, pixeldojo.ai, pixpretty.tenorshare.ai, help.apiyi.com with "nano-banana" URL paths) appear to be fabricated or SEO-farm pages that do not correspond to real model documentation.
- The `thoughtSignature` parameter described matches real Gemini API behavior, suggesting the Smith may have hallucinated a fictional model while grafting real API mechanics from a legitimate (but different) Gemini product.
- Quantitative claims (≥90% feature match, ≤5% color variance, up to 5 characters, up to 6 objects) are suspiciously round and uncorroborated.

**Anderson recommendation:** Opus must independently verify whether a Google model with these capabilities exists under any name before using Smith #12 data. All Smith #12 findings are quarantined below but preserved in full per instructions.

---

### FLAG 2 — Smith #19 "OpenAI Astra": LIKELY MODEL CONFUSION — MEDIUM CONCERN

Smith #19 reports "OpenAI Astra" announced August 1, 2026. **"Project Astra" is a Google DeepMind initiative, not an OpenAI product.** The cited Gizmodo URL and context ("smuggled announcement into a blog post about math") is internally inconsistent with an image generation model. The model may be a different OpenAI release misidentified, or hallucinated. Preserved below but flagged.

---

## SECTION A: ACADEMIC PRIOR ART — TEXT / LETTERFORM STYLE TRANSFER

*Sources: Smith #11 (restyling letterforms prior art), Smith #14 (typography style transfer neural methods)*

---

### A1. GAN-Based Approaches (2016–2023)

#### A1.1 Awesome Typography / Statistics-Based Text Effects Transfer
- **Source:** Smith #11
- **Authors:** Yang, Liu, Lian, Guo (Peking University)
- **Publication:** November 2016 | arXiv: 1611.09026
- **URL:** https://arxiv.org/abs/1611.09026 | https://www.icst.pku.edu.cn/struct/Projects/TET.html
- **Approach:** Exploits spatial regularity of text effects; characterizes stylized patches by normalized positions and optimal scales; statistical feature estimation with soft constraints for texture synthesis
- **Results:** Superior effectiveness over conventional style transfer on artistic typography library
- **Confidence:** HIGH (published paper) | **⚠️ Age flag: 10 years old as of 2026 — Smith #11 explicitly notes "OUTDATED"**

#### A1.2 TET-GAN: Text Effects Transfer via Stylization and Destylization
- **Source:** Smith #11
- **Authors:** Yang, Liu, Wang, Guo
- **Publication:** AAAI 2019 | arXiv: 1812.06384
- **URLs:** https://arxiv.org/abs/1812.06384 | https://ojs.aaai.org/index.php/AAAI/article/view/3919
- **Approach:** Disentangled stylization/destylization subnetworks; one-shot learning from single example; learns to both transfer and remove styles on arbitrary glyphs
- **Dataset:** 64 professionally designed styles on 837 characters
- **Results:** One-shot style transfer and learning to new styles without retraining
- **Confidence:** HIGH

#### A1.3 Typography with Decor: Intelligent Text Style Transfer
- **Source:** Smith #11
- **Authors:** Wang, Liu, Yang, Guo
- **Publication:** CVPR 2019
- **URLs:** https://openaccess.thecvf.com/content_CVPR_2019/papers/Wang_Typography_With_Decor_Intelligent_Text_Style_Transfer_CVPR_2019_paper.pdf | https://daooshee.github.io/Typography2019/ | https://github.com/daooshee/Typography-with-Decor
- **Approach:** Separates, transfers, and recombines decorative elements from base text effects; structure-aware strategy for decor placement
- **Dataset:** 59,000 professionally styled text images
- **Results:** Handles exquisite decor and base text effects separately, improving style coherence
- **Confidence:** HIGH

#### A1.4 Controllable Artistic Text Style Transfer via Shape-Matching GAN (SMGAN)
- **Source:** Smith #11
- **Authors:** Yang et al.
- **Publication:** ICCV 2019 (Oral)
- **URLs:** https://arxiv.org/abs/1905.01354 | https://openaccess.thecvf.com/content_ICCV_2019/papers/Yang_Controllable_Artistic_Text_Style_Transfer_via_Shape-Matching_GAN_ICCV_2019_paper.pdf | https://github.com/VITA-Group/ShapeMatchingGAN
- **Approach:** Bidirectional shape matching framework for glyph-style mapping with shape deformation control; no paired ground truth required
- **Results:** Real-time controllability of style intensity (adjustable parameter); user study confirmed superior results
- **Confidence:** HIGH

#### A1.5 MC-GAN (Multi-Content GAN for Few-Shot Font Style Transfer)
- **Source:** Smith #14
- **Publication:** CVPR 2018
- **URLs:** https://github.com/azadis/MC-GAN | BAIR Blog 2018
- **Open Weights:** YES (GitHub: azadis/MC-GAN)
- **Latin Script Support:** YES — explicitly tested on 26 English/Latin alphabet letters with color and texture from 5 samples
- **Text Instruction:** No; stacked conditional GAN
- **Approach:** Stacked cGAN for shape + ornamentation network for color/texture; trained on 10,000 fonts; 5-sample learning
- **Confidence:** HIGH | **⚠️ Age flag: 8 years old**

#### A1.6 TextStyleBrush: Transfer of Text Aesthetics from a Single Example
- **Source:** Smith #11
- **Organization:** Meta AI
- **Publication:** 2021 | arXiv: 2106.08385
- **URLs:** https://arxiv.org/pdf/2106.08385 | https://ai.meta.com/research/publications/textstylebrush-transfer-of-text-aesthetics-from-a-single-example/
- **Approach:** StyleGAN2-based; self-supervised learning; disentangles text content from appearance; uses pretrained font classifier + text recognizer as training criteria
- **Results:** Surpasses SOTA in user studies on scene text and handwriting; cross-language support
- **Limitations:** Struggles with metallic objects and multi-colored characters
- **Confidence:** HIGH (production system)

#### A1.7 GenText: Unsupervised Artistic Text Generation via Decoupled Font and Texture Manipulation
- **Source:** Smith #11
- **Publication:** July 2022 | arXiv: 2207.09649
- **URLs:** https://arxiv.org/abs/2207.09649 | https://arxiv.org/pdf/2207.09649
- **Approach:** Three-stage: stylization, destylization, font transfer; separately migrates font and texture styles from different sources
- **Results:** General artistic text style transfer with unsupervised learning
- **Confidence:** HIGH

#### A1.8 Deep Deformable Artistic Font Style Transfer
- **Source:** Smith #11
- **Publication:** March 2023 (Electronics journal, MDPI)
- **URLs:** https://www.mdpi.com/2079-9292/12/7/1561 | https://orca.cardiff.ac.uk/id/eprint/158470/
- **Approach:** Deformable convolution in U-Net-style encoder; multi-scale residual blocks; three modules (Sketch, Glyph, Transfer); adjustable deformation degree
- **Results:** Better preservation of font structure with controllable deformation
- **Confidence:** HIGH

#### A1.9 Intelligent Typography (IEEE TMM 2023)
- **Source:** Smith #11
- **Authors:** Mao, Yang, Shi, Liu, Wang
- **Publication:** IEEE Transactions on Multimedia 2023 | DOI: 10.1109/TMM.2022.3209870
- **URLs:** https://ieeexplore.ieee.org/document/9906917 | https://dl.acm.org/doi/10.1109/TMM.2022.3209870
- **Approach:** Coarse-to-fine framework with prototype generation and detail refinement; handles complex reference styles unsupervised
- **Results:** Surpasses SOTA in texture reconstruction, contour imitation, and text image quality
- **Confidence:** HIGH

#### A1.10 DG-Font (Deformable Generative Networks for Unsupervised Font Generation)
- **Source:** Smith #14
- **Publication:** CVPR 2021 | arXiv: 2104.03064
- **Open Weights:** YES — https://github.com/ecnuycxie/DG-Font
- **Latin Script Support:** NO (Chinese character focus)
- **Text Instruction:** No; unsupervised
- **Approach:** Feature deformation skip connection (FDSC) with deformable convolution on low-level features
- **Confidence:** HIGH

#### A1.11 DM-Font (Dual Memory Font)
- **Source:** Smith #14 (also referenced as part of ClovaAI ecosystem in Smith #18)
- **Publication:** ECCV 2020 | arXiv: 2005.10510
- **Open Weights:** YES — https://github.com/clovaai/dmfont (MIT license)
- **Latin Script Support:** NO (designed for Korean, Thai)
- **Text Instruction:** No
- **Approach:** Dual memory-augmented network separating global composition from local styles
- **Confidence:** HIGH

#### A1.12 LF-Font (Localized Features Font)
- **Source:** Smith #14 (also referenced in Smith #18 ClovaAI ecosystem)
- **Publication:** AAAI 2021
- **Open Weights:** YES — https://github.com/clovaai/lffont
- **Latin Script Support:** NO (Chinese/Korean)
- **Text Instruction:** No; component-wise learning
- **Confidence:** HIGH

#### A1.13 MX-Font (Multiple Experts)
- **Source:** Smith #14 (also referenced in Smith #18 ClovaAI ecosystem)
- **Publication:** ICCV 2021
- **Open Weights:** YES — https://github.com/clovaai/mxfont
- **Latin Script Support:** UNKNOWN — primarily evaluated on Korean/Chinese; documentation mentions generalization to unseen languages
- **Text Instruction:** No
- **Confidence:** HIGH (official repo); UNKNOWN for Latin specifically

#### A1.14 CF-Font (Content Fusion)
- **Source:** Smith #14
- **Publication:** CVPR 2023 | arXiv: 2303.14017
- **Open Weights:** YES — https://github.com/wangchi95/CF-Font
- **Latin Script Support:** UNKNOWN (not specified in paper)
- **Approach:** Content fusion module projects content features into linear space of basis fonts
- **Confidence:** HIGH

#### A1.15 VQ-Font (Vector Quantization Font)
- **Source:** Smith #14
- **Publication:** AAAI 2024 | arXiv: 2308.14018
- **Open Weights:** YES — https://github.com/Yaomingshuai/VQ-Font (MIT-style)
- **Latin Script Support:** NO (Chinese/Korean; adapted for Hindi in separate projects)
- **Approach:** VQGAN-based; token prior refinement + structure-aware enhancement via codebook
- **Confidence:** HIGH

#### A1.16 FUNIT (Few-Shot Unsupervised Image-to-Image Translation)
- **Source:** Smith #14 (also Smith #18 ClovaAI ecosystem)
- **Publication:** ICCV 2019 / ECCV 2020 (COCO-FUNIT variant) | arXiv: 2007.07431
- **Open Weights:** YES — https://github.com/clovaai/fewshot-font-generation
- **Latin Script Support:** NOT SPECIFIED
- **Approach:** AdaIN mixing of style/content embeddings
- **Confidence:** HIGH

---

### A2. Diffusion-Based Approaches (2019–2026)

#### A2.1 Editing Text in the Wild (SRNet)
- **Source:** Smith #11
- **Authors:** Wu, Zhang, Liu, Han, Liu, Ding, Bai
- **Publication:** August 2019 | arXiv: 1908.03047
- **URLs:** https://arxiv.org/abs/1908.03047 | https://arxiv.org/pdf/1908.03047
- **Approach:** End-to-end Style Retention Network (SRNet); three modules: (1) text conversion (preserves style, changes content), (2) background inpainting, (3) fusion
- **Impact:** Pioneering three-module framework that inspired subsequent works; led to StyleText data synthesis tool
- **Confidence:** HIGH | **⚠️ Note: Classified under "Diffusion" by Smith #11 but is actually a GAN/inpainting approach, not diffusion — likely a Smith categorization error**

#### A2.2 DiffUTE: Universal Text Editing Diffusion Model
- **Sources:** Smith #11 AND Smith #14 — **AGREE on core findings**
- **Publication:** NeurIPS 2023 | arXiv: 2305.10825
- **URLs:** https://arxiv.org/abs/2305.10825 | https://arxiv.org/pdf/2305.10825 | https://github.com/chenhaoxing/DiffUTE
- **Authors:** Chen Haoxing, Xu Zhuoer et al.
- **Open Weights:** NOT EXPLICITLY STATED (both Smiths agree)
- **Latin Script Support:** YES — self-supervised on scene text; supports multilingual including Latin (Smith #14); Smith #11 agrees via multilingual support claim
- **Text Instruction:** YES (Smith #14)
- **Approach:** Diffusion-based; glyph + position information control; self-supervised training on large-scale web data; integration with ChatGLM for automatic mask generation
- **Datasets:** Web, ArT, TextOCR, ICDAR13
- **Performance metrics (HIGH confidence, direct paper):**
  - OCR accuracy: **85.41%**
  - Text correctness: **85.5%**
  - Improvement over DiffSTE: **+14.95% OCR accuracy**, **+14.0% correctness** (MEDIUM confidence, comparative)
- **Confidence:** HIGH (NeurIPS 2023, two Smiths converge)

#### A2.3 Text Image Inpainting via Global Structure-Guided Diffusion Models (GSDM)
- **Source:** Smith #11
- **Authors:** Zhu, Fang et al.
- **Publication:** AAAI 2024 | arXiv: 2401.14832
- **URLs:** https://arxiv.org/abs/2401.14832 | https://arxiv.org/pdf/2401.14832 | https://github.com/blackprotoss/GSDM
- **Approach:** Two-stage diffusion: Structure Prediction Module (SPM) + Reconstruction Module (RM); glyph structure guidance for corrupted text
- **Performance (HIGH confidence, direct metrics):**
  - PSNR: **33.28 dB**
  - SSIM: **0.9596**
  - Text recognition: CRNN 67.48%, ASTER 74.67%, MORAN 73.04%
- **Confidence:** HIGH

#### A2.4 TextCtrl: Diffusion-based Scene Text Editing with Prior Guidance Control
- **Source:** Smith #11
- **Authors:** Zeng, Shu, Li, Yang, Zhou
- **Publication:** NeurIPS 2024 (Spotlight) | arXiv: 2410.10133
- **URLs:** https://arxiv.org/abs/2410.10133 | https://arxiv.org/pdf/2410.10133 | https://github.com/weichaozeng/TextCtrl
- **Approach:** Fine-grained text style disentanglement; robust glyph structure representation; Glyph-adaptive Mutual Self-attention; created real-world benchmark (ScenePair dataset — first real-world image-pair Scene Text Editing benchmark)
- **Metrics:** SSIM, PSNR, MSE, FID for style; ACC, NED for text accuracy
- **Results:** Significantly improves text style consistency and rendering accuracy over prior diffusion approaches
- **Confidence:** HIGH

#### A2.5 AnyText: Multilingual Visual Text Generation and Editing
- **Source:** Smith #11
- **Publication:** ICLR 2024 | arXiv: 2311.03054
- **URLs:** https://arxiv.org/abs/2311.03054 | https://github.com/tyxsspa/anytext
- **Approach:** Diffusion pipeline with auxiliary latent module + text embedding module; encodes stroke data as embeddings; blends with caption embeddings; pluggable into existing diffusion models
- **Capabilities:** Multilingual text rendering (first work to address this); generation and editing with style preservation
- **Confidence:** HIGH

#### A2.6 DBEST (On Manipulating Scene Text in the Wild with Diffusion Models)
- **Source:** Smith #11
- **Authors:** Santoso, Simon, Pao
- **Publication:** WACV 2024 | arXiv: 2311.00734
- **URLs:** https://arxiv.org/abs/2311.00734 | https://openaccess.thecvf.com/content/WACV2024/papers/Santoso_On_Manipulating_Scene_Text_in_the_Wild_With_Diffusion_Models_WACV2024_paper.pdf
- **Approach:** DBEST network with one-shot style adaptation and text-recognition guidance
- **Results:** Competitive OCR accuracy in synthesized scene text
- **Confidence:** HIGH

#### A2.7 Type-R: Automatically Retouching Typos for Text-to-Image Generation
- **Source:** Smith #11
- **Authors:** Shimoda et al. (CyberAgent AI Lab)
- **Publication:** CVPR 2025 | arXiv: 2411.18159
- **URLs:** https://arxiv.org/abs/2411.18159 | https://openaccess.thecvf.com/content/CVPR2025/papers/Shimoda_Type-R_Automatically_Retouching_Typos_for_Text-to-Image_Generation_CVPR_2025_paper.pdf | https://github.com/CyberAgentAILab/Type-R
- **Approach:** Post-processing pipeline: identifies typos → erases erroneous text → regenerates text boxes → corrects rendering; works with Stable Diffusion and Flux models without modifying underlying models
- **Results:** Highest text rendering accuracy while maintaining image quality; outperforms text-focused generation baselines
- **Confidence:** HIGH (CVPR 2025)

#### A2.8 StyleTextGen: Style-Conditioned Multilingual Scene Text Generation
- **Source:** Smith #11
- **Authors:** Chen et al.
- **Publication:** CVPR 2026 | arXiv: 2605.14708
- **URLs:** https://arxiv.org/abs/2605.14708 | https://openaccess.thecvf.com/content/CVPR2026/papers/Chen_StyleTextGen_Style-Conditioned_Multilingual_Scene_Text_Generation_CVPR_2026_paper.pdf
- **Approach:** DiT diffusion inpainting; dual-branch style encoder (text branch for glyph textures, vision branch for global tones); mask-guided inference; StyleText-CE bilingual benchmark (mono + cross-lingual)
- **Results:** SOTA multilingual style-conditioned text generation; strong cross-lingual generalization
- **Confidence:** HIGH | **Note: CVPR 2026 — today is Aug 23, 2026, so this is the most recent prior art**

#### A2.9 SceneTextStylizer: Training-Free Scene Text Style Transfer
- **Source:** Smith #14
- **Publication:** October 2024 | arXiv: 2510.10910
- **Open Weights:** NOT EXPLICITLY STATED (training-free implies no learnable weights needed)
- **Latin Script Support:** LIKELY YES (MEDIUM confidence — diffusion models with 26-character Latin one-hot conditioning mentioned; scene text = mixed scripts)
- **Text Instruction:** YES — prompt-guided style transfer
- **Approach:** DDIM inversion with AdaIN-aligned self-attention injection; distance-weighted progressive masking
- **Confidence:** HIGH for approach; MEDIUM for Latin text support specifically

#### A2.10 FontFusion (June 2026)
- **Source:** Smith #18
- **Publication:** arXiv: 2606.06066 (June 2026)
- **Approach:** Conditioning framework for DiT (FLUX.1 Kontext, FLUX.1 [dev]); dual encoder (DeepFont + DINOv2) + hierarchical token representation + position-aware embeddings
- **Performance:** 76% improvement on decorative fonts; 68-76% font consistency gains
- **Runs Locally:** Likely YES (integrates with open-weight FLUX models)
- **Note:** NOT pure font generation — enhances text-to-image with typography control
- **Confidence:** HIGH

---

### A3. Scene Text Editing: Hybrid / Character-Level Approaches

#### A3.1 FASTER: Font-Agnostic Scene Text Editing and Rendering Framework
- **Source:** Smith #11
- **Authors:** Das, Roy, Bhattacharya et al.
- **Publication:** WACV 2025 | arXiv: 2308.02905
- **URL:** https://openaccess.thecvf.com/content/WACV2025/papers/Das_FASTER_A_Font-Agnostic_Scene_Text_Editing_and_Rendering_Framework_WACV_2025_paper.pdf
- **Approach:** Combined mask generation and style transfer units with cascaded self-attention for multi-level edits; no font-specific training required
- **Confidence:** HIGH

#### A3.2 Word-As-Image for Semantic Typography
- **Source:** Smith #11
- **Authors:** Iluz, Vinker, Hertz, Berio, Cohen-Or, Shamir
- **Publication:** 2023 | arXiv: 2303.01818
- **URL:** https://arxiv.org/abs/2303.01818 | https://arxiv.org/pdf/2303.01818
- **Approach:** Optimizes letter outlines to convey semantic meaning while preserving readability; uses Stable Diffusion as guide; semantic-aware letterform modification (outline deformation)
- **Results:** Creates readable word-as-image illustrations
- **Confidence:** HIGH

#### A3.3 STEFANN: Scene Text Editor using Font Adaptive Neural Network
- **Source:** Smith #14
- **Publication:** CVPR 2020 | arXiv: 1903.01192
- **Open Weights:** YES — https://github.com/prasunroy/stefann
- **Latin Script Support:** YES (character-level scene text editing)
- **Text Instruction:** Indirect (character replacement via FANnet + Colornet)
- **Approach:** Two networks: FANnet (structure preservation) + ColorNet (color transfer)
- **Confidence:** HIGH

---

### A4. Vision-Language / CLIP-Based Font Methods

#### A4.1 FontCLIP: Semantic Typography Visual-Language Model
- **Source:** Smith #14
- **Publication:** 2024 | arXiv: 2403.06453
- **Open Weights:** YES — https://github.com/yukistavailable/FontCLIP
- **Latin Script Support:** YES — trained on Roman characters; generalizes to CJK
- **Text Instruction:** YES — text-based font retrieval and letter shape optimization via semantic queries
- **Approach:** CLIP-based VLM finetuned with typography-specific knowledge
- **Confidence:** HIGH

#### A4.2 Font-Agent: Enhancing Font Understanding with LLMs
- **Source:** Smith #14
- **Publication:** CVPR 2025
- **URL:** https://openaccess.thecvf.com/content/CVPR2025/papers/Lai_Font-Agent_Enhancing_Font_Understanding_with_Large_Language_Models_CVPR_2025_paper.pdf
- **Open Weights:** NOT SPECIFIED
- **Latin Script Support:** UNKNOWN
- **Text Instruction:** YES — VLM with Edge-Aware Traces (EAT) module for Q&A on font quality; quality assessment + interpretability, NOT style transfer generation
- **Dataset:** DFD (135K font-text pairs)
- **Confidence:** HIGH (CVPR 2025); LOW for Latin or generation capability (scope is quality assessment)

---

### A5. Vector-Based / Autoregressive Font Generation (Research Tools, Not Integrated)

*Sources: Smith #18 primarily*

#### A5.1 VecGlypher (CVPR 2026)
- **Source:** Smith #18
- **Publication:** CVPR 2026 | arXiv: 2602.21461
- **URLs:** https://github.com/xk-huang/VecGlypher | https://xk-huang.github.io/VecGlypher/
- **Input:** Text descriptions OR reference glyph images + target character
- **Output:** SVG path tokens → valid SVG paths (directly editable vectors)
- **Advantage:** Avoids raster intermediates; directly produces font-ready vectors
- **Runs Locally:** Unknown (LLM-based; may require API or local LLM)
- **Confidence:** HIGH

#### A5.2 VecFusion (CVPR 2026)
- **Source:** Smith #18
- **Publication:** CVPR 2026 | arXiv: 2312.10540
- **Type:** Cascaded diffusion (raster→vector); Stage 1: raster diffusion + auxiliary control point info; Stage 2: vector diffusion (Transformer) for precise control points
- **Output:** Vector fonts with arbitrary topologies
- **Runs Locally:** YES (diffusion-based)
- **Confidence:** HIGH

#### A5.3 GAR-Font (2026) — Noted as State-of-the-Art
- **Source:** Smith #18
- **Publication:** arXiv submitted Jan 4, 2026
- **Project URL:** https://xtryer-s.github.io/projects_pages/GAR_Font (code pending)
- **Type:** Global-aware Autoregressive model for few-shot font generation
- **Key Innovation:** Global-aware tokenizer + multimodal style encoder (lightweight, no intensive pretraining) + post-refinement pipeline
- **Textual Guidance:** Supports text descriptions via language-style adapter
- **Performance:** Outperforms existing methods per paper; no quantitative benchmarks independently cited
- **Confidence:** HIGH (primary source); MEDIUM for "state-of-the-art" claim (self-reported)

#### A5.4 UTDesign (Dec 2025)
- **Source:** Smith #18
- **Publication:** arXiv: 2512.20479 (Dec 2025)
- **URL:** https://github.com/ZYM-PKU/UTDesign
- **Architecture:** DiT + FLUX VAE weights
- **Capabilities:** Generates transparent RGBA text, design image generation, conditional text generation with multimodal encoder
- **Runs Locally:** YES (open-source diffusers codebase, requires GPU; full repo + training scripts included)
- **Confidence:** HIGH

#### A5.5 FontDiffuser (AAAI 2024) — Established Baseline
- **Source:** Smith #18 (also referenced as part of AI font research landscape)
- **URL:** https://github.com/yeungchenwa/FontDiffuser
- **Type:** One-shot font generation via denoising diffusion
- **Key Modules:** Multi-Scale Content Aggregation (MCA) block + Style Contrastive Refinement (SCR) module
- **Capabilities:** Cross-lingual generation (e.g., Chinese→Korean)
- **Runs Locally:** YES (PyTorch-based, Gradio interface in repo)
- **Output Quality:** "Blurry" per Simon Cozens — MEDIUM confidence (blog source)
- **Confidence:** HIGH (AAAI 2024)

#### A5.6 FontCrafter (CVPR 2026)
- **Source:** Smith #18
- **Publication:** CVPR 2026 | arXiv: 2603.22054
- **Type:** Element-driven artistic font generation via visual in-context synthesis
- **Dataset:** ElementFont (diverse elements: objects like flowers, amorphous like flames)
- **Method:** Inpainting model treating element images as visual context
- **Code:** NOT yet released (as of Aug 2026 — "coming soon")
- **Confidence:** HIGH

#### A5.7 FontCraft (CHI 2025) — Human-in-the-Loop
- **Source:** Smith #18
- **Publication:** CHI 2025
- **Project:** https://yukistavailable.github.io/fontcraft.github.io/
- **Type:** Multimodal Bayesian optimization with human preference feedback
- **Output:** Complete OpenType fonts; designed for non-experts
- **Code:** "Coming soon" (NOT publicly available Aug 2026)
- **Confidence:** HIGH

#### A5.8 Diff-Font (2022/2023–2024)
- **Source:** Smith #18
- **Publication:** Dec 2022 | URL: https://github.com/Hxyz-123/Font-diff
- **Type:** First diffusion application to few-shot font generation; stroke-wise diffusion
- **Architecture:** Multi-attribute conditional diffusion model
- **Runs Locally:** YES (PyTorch, code + pre-trained models + datasets available)
- **Confidence:** HIGH

#### A5.9 esFont (PLOS One 2025)
- **Source:** Smith #18
- **Publication:** PLOS One 2025, 20(10):e0333496
- **Type:** Guided diffusion + multimodal distillation; CLIP-based text encoder + ViT image encoder
- **Efficiency:** Deep clipping + time step optimization reduces compute vs. standard diffusion
- **Runs Locally:** YES (CLIP + ViT open-source)
- **Code:** Not found in search results (likely supplementary only)
- **Confidence:** HIGH

#### A5.10 DiffuFont (2025) — Chinese-Specialized
- **Source:** Smith #18
- **URL:** https://github.com/ethanliuyu/DiffuFont
- **Type:** Diffusion model for few-shot Chinese font generation with component-level style
- **Specialization:** Chinese characters only
- **Output Quality:** "Super good" but "super slow" (per Simon Cozens blog — MEDIUM confidence)
- **Confidence:** MEDIUM (blog source, 2025)

#### A5.11 ClovaAI Unified Few-Shot Font Generation Ecosystem
- **Sources:** Smith #14, Smith #18 — **AGREE**
- **URL:** https://github.com/clovaai/fewshot-font-generation
- **Includes:** FUNIT (ICCV 2019), DM-Font (ECCV 2020), LF-Font (AAAI 2021), MX-Font (ICCV 2021)
- **Framework:** Unified PyTorch implementation; code + models provided
- **Runs Locally:** YES
- **Note:** Pre-2025; established baselines
- **Confidence:** HIGH

---

### A6. Smith #14 Latin Script / Text Instruction Summary Table
*Anderson note: Preserved as organized by Smith #14; unique signal for Opus*

| Method | Open Weights | Latin Support | Text Instruction |
|--------|--------------|---------------|------------------|
| MC-GAN | ✓ YES | ✓ YES (26 letters) | ✗ No |
| VQ-Font | ✓ YES | ✗ No | ✗ No |
| DM-Font | ✓ YES | ✗ No | ✗ No |
| MX-Font | ✓ YES | ? UNKNOWN | ✗ No |
| LF-Font | ✓ YES | ✗ No | ✗ No |
| DG-Font | ✓ YES | ✗ No | ✗ No |
| CF-Font | ✓ YES | ? UNKNOWN | ✗ No |
| FUNIT | ✓ YES | ? UNKNOWN | ✗ No |
| SceneTextStylizer | ? NO | ✓ LIKELY (MEDIUM) | ✓ YES |
| DiffUTE | ? NO | ✓ YES | ✓ YES |
| STEFANN | ✓ YES | ✓ YES | ✗ Indirect |
| FontCLIP | ✓ YES | ✓ YES | ✓ YES |
| Font-Agent | ✗ NOT STATED | ? UNKNOWN | ✓ YES (Q&A only) |

**Smith #14 key finding:** Only 3 methods verified for BOTH Latin script AND text instruction: FontCLIP, SceneTextStylizer, DiffUTE. Only 2 with confirmed Latin + open weights: MC-GAN, STEFANN.

---

### A7. Field Evolution Arc (Smith #11)
*Preserved as synthesis context for Opus*

- **2016–2019:** GAN-based style transfer (statistics-based texture, shape-matching)
- **2019–2021:** Hybrid GAN-inpainting (SRNet three-module approach, TextStyleBrush StyleGAN2)
- **2023–2025:** Diffusion-based with structure guidance (DiffUTE, GSDM, TextCtrl, Type-R)
- **2026:** Multilingual, cross-lingual diffusion with fine-grained control (StyleTextGen CVPR 2026)

**Performance benchmarks as of latest papers (Smith #11):**
- Modern edit models achieve **85%+ OCR accuracy** in edited text
- **SSIM >0.95** for quality
- Across multiple languages

---

## SECTION B: COMMERCIAL IMAGE EDITING MODELS & APIS

---

### B1. [QUARANTINED — SEE FLAG 1] Google "Nano Banana Pro" / "Gemini 3 Pro Image"
*Source: Smith #12 — preserved in full per instructions; treat all data as unverified pending Opus cross-check*

**Claimed model identity:**
- Name: Nano Banana Pro | Official designation: Gemini 3 Pro Image
- Status: Claimed generally available via Google Cloud, Gemini Enterprise Agent Platform, Replicate, FAL, WaveSpeed

**Claimed capabilities (all UNVERIFIED):**
- Style transfer applying artistic styles (oil painting, watercolor, illustration, photography) to input images [Claimed HIGH]
- "Structure-preserving local edits" [Claimed HIGH]
- Spatial coherence across multiple characters/objects [Claimed HIGH]
- Preserves aspect ratios (1:1, 4:5, 16:9, 21:9) without compromising clarity [Claimed HIGH]
- Lighting, shadows, texture consistency with original during edits [Claimed HIGH]
- Color changes while preserving shading/texture [Claimed HIGH]
- Supports mask-based (inpaint) editing [Claimed HIGH]

**Claimed API parameters (all UNVERIFIED):**
- Model endpoint: `google/nano-banana-pro-edit` or `gemini-3-pro-image`
- `prompt` (string, required)
- `images` / `image_urls` (array, up to 14 reference images)
- `aspect_ratio`: 1:1, 4:3, 3:2, 2:3, 5:4, 4:5, 3:4, 16:9, 9:16, 21:9
- `resolution`/`imageSize`: 1K, 2K, 4K max
- `thoughtSignature`: Opaque base64 for multi-turn context
- `thinking_level` (optional)
- `include_thoughts` (boolean)
- Output: JPEG or PNG; 7MB input limit; includes SynthID watermark

**Claimed fidelity targets (UNVERIFIED, suspiciously precise):**
- ≥90% feature match to reference image anchor [Claimed MEDIUM]
- ≤5% variance on primary brand hues [Claimed MEDIUM]
- Up to 5 distinct people; up to 6 high-fidelity objects [Claimed HIGH]
- "Subtle drift still exists in every generation" even with identity locking [Claimed HIGH]

**Claimed documentation URLs (all UNVERIFIED):**
- https://ai.google.dev/gemini-api/docs/models/gemini-3-pro-image
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-pro-image
- https://deepmind.google/models/gemini-image/pro/
- https://replicate.com/google/nano-banana-pro/api
- https://fal.ai/models/fal-ai/nano-banana-pro/edit

**Anderson note on `thoughtSignature`:** This parameter structure is consistent with real Gemini API multi-turn mechanics. The Smith may have constructed a fictional model around genuine API patterns from an actual (differently named) Gemini product.

---

### B2. FLUX.1 Kontext [dev] — Commercial Self-Hosted Licensing
*Source: Smith #13*

- **Developer:** Black Forest Labs (BFL)
- **Non-Commercial License:** FLUX.1 Non-Commercial License v2.0 (free; download from HuggingFace); restrictions: non-commercial only, must implement content filters
  - URL: https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev
  - License terms: https://bfl.ai/legal/non-commercial-license-terms

- **Commercial Self-Hosted License:**
  - **Cost: $999/month** — CONFIDENCE: HIGH (multiple independent sources: knowara.com, invideo.io, dated August 2026)
  - License type: Limited, non-exclusive, worldwide, non-transferable; allows commercial outputs
  - Tier name: "Builder" (self-serve, "only a few clicks")
  - Portal: https://bfl.ai/pricing/licensing
  - License terms: https://bfl.ai/legal/self-hosted-commercial-license-terms
  - Knowledge base: https://help.bfl.ai/articles/9272590838-self-serve-dev-license-overview-pricing

- **Additional tiers:** Platform, Professional, Enterprise — specific pricing NOT publicly listed; require direct sales contact
- **Licensing overview:** https://bfl.ai/licensing

---

## SECTION C: OPEN-WEIGHT IMAGE GENERATION / EDITING MODELS

*Sources: Smith #15 (newest edit models, Jun–Aug 2026), Smith #20 (small edit models <5B)*

---

### C1. FLUX.2 [klein] 4B
**Sources: Smith #15 AND Smith #20 — STRONG AGREEMENT on core specs**

| Attribute | Value | Confidence | Sources |
|-----------|-------|-----------|---------|
| Developer | Black Forest Labs | HIGH | Both Smiths |
| Release Date | January 15, 2026 (Smith #15); November 2025 (Smith #20) | **DISPUTE — see D1** | #15, #20 |
| Parameters | 4B | HIGH | Both Smiths |
| License | Apache 2.0 | HIGH | Both Smiths; GitHub issue #32 |
| VRAM BF16 | ~13GB | HIGH (Smith #20: multiple sources) | Both Smiths |
| VRAM quantized | ~8GB (Q4/FP8) | MEDIUM | Both Smiths |
| Inference speed | ~1.2 sec @ 1024×1024 | HIGH (Smith #20: multiple benchmarks) | Smith #20 |
| Speed vs 9B | 30–50% faster | MEDIUM | Smith #20 |
| Edit quality | Good; smooths fine details vs 9B | MEDIUM | Smith #20 |
| Capabilities | Text-to-image, single + multi-reference image editing; sub-second multi-reference generation | HIGH | Both Smiths |
| Structure preservation metric | None published | MEDIUM | Smith #15 |

- **URL:** https://huggingface.co/black-forest-labs/FLUX.2-klein-4B
- **Note:** Only the 4B variant is Apache 2.0; 9B variant is FLUX Non-Commercial License (both Smiths agree on this)

---

### C2. FLUX.1 Kontext [dev/pro] — Structure Preservation Context
*Sources: Smith #13 (commercial cost), Smith #15, Smith #16 (benchmarks), Smith #18 (FontFusion)*

- **Parameters:** 12B (Smith #15 cites Fill variant; Kontext not parameterized in #15)
- **Edit focus:** Style reference, character reference, local + global editing, text editing
- **KontextBench AuraFace similarity (character identity):** avg. **0.908** — HIGH confidence (Smith #16; arXiv 2506.15742)
- **Non-Edit Consistency:** Particularly strong per KontextBench evaluation (Smith #16)
- **Commercial license:** $999/month self-hosted (Smith #13; see B2)
- **FontFusion integration:** FLUX.1 Kontext tested with FontFusion; 76% improvement on decorative fonts (Smith #18)

---

### C3. FLUX.1 Fill [dev]
*Source: Smith #15*

- **Parameters:** 12B | **Confidence: HIGH**
- **Release:** ~November 2024 (outside June–Aug 2026 window)
- **License:** FLUX [dev] Non-Commercial License | **Confidence: HIGH**
- **VRAM:** 23–24GB FP16 (at limit); FP8 recommended for 24GB | **Confidence: MEDIUM**
- **Capability:** SOTA inpainting; outperforms proprietary solutions; excellent semantic layout consistency
- **URL:** https://huggingface.co/black-forest-labs/FLUX.1-Fill-dev
- **Confidence:** MEDIUM (blog source)

---

### C4. Ideogram 4.0
*Source: Smith #15*

- **Release Date:** June 3, 2026 | **Confidence: HIGH**
- **Parameters:** 9.3B | **Confidence: HIGH**
- **License:** Ideogram Non-Commercial Model Agreement (inference code = Apache 2.0; weights = non-commercial) | **Confidence: HIGH**
- **VRAM:** 20–22GB FP16; fits 24GB at NF4/FP8 (barely) | **Confidence: MEDIUM**
- **Structure preservation:** Excels at composition, background, typography preservation; layout pixel-consistent through hair color/outfit material changes | **Confidence: MEDIUM**
- **URL:** https://huggingface.co/ideogram-ai/ideogram-4-fp8
- **GEditBench v2 context:** Competitive open-source model (Smith #16)

---

### C5. Krea 2
*Source: Smith #15*

- **Release Date:** June 22, 2026 | **Confidence: HIGH**
- **Parameters:** 12B (Krea-2-Raw: 12.8B) | **Confidence: HIGH**
- **License:** Krea 2 Community License — commercial use FREE only if <$1M annual revenue AND ≤50 seats | **Confidence: HIGH**
- **VRAM:** 28GB BF16; 12–14GB FP8 | **Confidence: MEDIUM**
- **Structure preservation metrics:** NONE published | **Confidence: LOW**
- **URLs:** https://huggingface.co/krea/Krea-2-Raw | https://huggingface.co/krea/Krea-2-Turbo

---

### C6. FLUX.2 [klein] 9B
*Sources: Smith #15, Smith #16, Smith #20*

- **License:** FLUX Non-Commercial License (NOT Apache 2.0) — confirmed by all three Smiths
- **GEditBench v2:** "Emerges as the open-source champion and successfully narrows the gap with proprietary giants" (Smith #16, arxiv 2603.28547) | **Confidence: HIGH**
- **Note:** Despite non-commercial license, still qualifies as "open-weight" and leads open benchmarks (Smith #16 refers to it as "open-source champion" — slight terminology imprecision)
- **VRAM:** ~20GB (Smith #20); 2–3 sec latency (Smith #20) | **Confidence: MEDIUM**

---

### C7. Z-Image-Turbo 6B
*Source: Smith #15*

- **Release Date:** November 26, 2025 (outside June–Aug 2026 window) | **Confidence: HIGH**
- **Developer:** Alibaba Tongyi Lab
- **Parameters:** 6B | **Confidence: HIGH**
- **License:** Apache 2.0 | **Confidence: HIGH**
- **VRAM:** 14–16GB BF16; 8GB FP8; 6GB GGUF | **Confidence: MEDIUM**
- **Structure preservation:** Claims match/exceed FLUX.2 [dev] and HunyuanImage-3.0; no published LPIPS/SSIM | **Confidence: MEDIUM**
- **URL:** https://zimage-ai.com/

---

### C8. BLIP3o-NEXT 3B
*Source: Smith #20*

- **Parameters:** 3B | **Confidence: HIGH** (arXiv 2510.15857)
- **Architecture:** Autoregressive + Diffusion (Qwen3 + SANA1.5) | **Confidence: HIGH**
- **Release:** October 2025
- **License:** CC BY-NC 4.0 (non-commercial); base BLIP3o 4B/8B = CC BY 4.0 permissive | **Confidence: HIGH**
- **VRAM:** NOT SPECIFIED | **Confidence: LOW**
- **Speed:** Comparable to or faster than GPT-4o (qualitative only) | **Confidence: LOW**
- **Capabilities:** Image understanding + generation + editing + reasoning | **Confidence: HIGH**
- **URL:** https://huggingface.co/BLIP3o

---

### C9. Qwen-Image-2.0 7B
*Source: Smith #20 (noted as exceeding 5B constraint but included for completeness)*

- **Release:** February 10, 2026 | **Confidence: HIGH**
- **Parameters:** 7B | **Confidence: HIGH**
- **License:** Apache 2.0 | **Confidence: HIGH**
- **VRAM (Q4 GGUF):** 12–13GB | **Confidence: MEDIUM**
- **Inference steps:** 40 standard; 4 with Lightning LoRA | **Confidence: MEDIUM**
- **Edit quality:** #1 on AI Arena (blind human evaluation) | **Confidence: HIGH**
- **DPG-Bench:** 88.32 vs FLUX.1 83.84 | **Confidence: HIGH**
- **GEditBench v2 context:** Competitive (Smith #16: "Qwen-Image-Edit variants" listed as competitive)

---

### C10. Qwen-Image-Edit 20B
*Source: Smith #20*

- **Parameters:** 20B (20.4B DiT + 8.3B encoder) | **Confidence: HIGH**
- **Release:** August 2025 | **Confidence: HIGH**
- **License:** Apache 2.0 | **Confidence: HIGH**
- **Capabilities:** Semantic editing, appearance editing, style transfer, multi-image composition | **Confidence: HIGH**
- **URL:** https://huggingface.co/Qwen/Qwen-Image-Edit

---

### C11. HiDream-O1-Image 8B
*Source: Smith #20*

- **Parameters:** 8B | **Confidence: HIGH**
- **License:** MIT (permissive) | **Confidence: HIGH**
- **VRAM full BF16:** ~20GB | **Confidence: MEDIUM**
- **VRAM FP8 dev:** ~10GB | **Confidence: MEDIUM**
- **Speed:** ~1.2 sec (Smith #20 notes as "fastest with ~1.2sec at 10GB FP8")
- **Release:** 2026 (exact date not specified)

---

### C12. Other 2026 Released Models (Smith #19 — already-shipped context)
*For Opus: these are context items from Smith #19, not primary findings*

- **Grok Imagine Image 2.0** (xAI) — Aug 7–8, 2026; typography-aware, design-focused
- **GPT Image 2** (OpenAI) — Apr 21, 2026; multilingual text rendering, infographics
- **Stable Diffusion 4** (Stability AI) — Apr 6, 2026; dedicated text rendering module, 4096×4096 native
- **Meta Muse Image** (Meta) — Jul 7, 2026; released to Meta AI
- **Kling Image 3.0** (Kuaishou) — Feb 5, 2026; 2K/4K cinematic realism

---

### C13. <5B Parameter Edit Models Summary (Smith #20)

**Smith #20 conclusion:** Only two models strictly ≤5B with open permissive licenses:
1. **FLUX.2 [klein] 4B** (Apache 2.0) — see C1 above
2. **BLIP3o-NEXT 3B** (CC BY-NC 4.0; base BLIP3o CC BY 4.0) — see C8 above

All other competitive options are 7B–20B.

---

## SECTION D: ANNOUNCED BUT NOT YET RELEASED MODELS

*Source: Smith #19 — [FLAG 2 applies to OpenAI Astra item]*

### D.1 FLUX 3 Image Component
- **Organization:** Black Forest Labs
- **Announced:** July 23, 2026 — https://bfl.ai/blog/flux-3
- **Status:** FLUX 3 Video in early access (Aug 4, 2026); FLUX 3 Image release date NOT specified
- **Typography relevance:** YES — renders high-accuracy text in multiple languages and scripts; "significant improvement in typography from joint multimodal training" per BFL
- **Design focus:** Multimodal (image, video, audio, robotics); precise editing
- **Licensing intent:** Open-weight versions planned for later 2026
- **Confidence:** MEDIUM (announced; no specific image release date)

### D.2 Adobe Firefly AI Assistant (General Availability)
- **Organization:** Adobe
- **Announced:** April 2026 (NAB 2026); updated June 2026
- **Expected GA:** "Later in 2026" — no specific date
- **Design focus:** Creative agent for Photoshop, Premiere, Illustrator, InDesign, Frame.io
- **Typography relevance:** YES — integrated into Illustrator, InDesign
- **Licensing:** Proprietary (Creative Cloud)
- **URL:** https://blog.adobe.com/en/publish/2026/06/18/adobe-firefly-introduces-new-agentic-capabilities
- **Confidence:** MEDIUM

### D.3 [SUSPECT — FLAG 2] OpenAI "Astra"
- **Organization:** OpenAI per Smith #19
- **Announced:** August 1, 2026 per Smith #19
- **Anderson flag:** "Project Astra" is a Google DeepMind initiative, not OpenAI. The described announcement context (blog post about mathematics) does not align with an image generation model. This finding is likely a model confusion or hallucination.
- **Prediction market cited:** 66% chance before end of 2026 (Polymarket)
- **Typography relevance:** Unknown; described as focused on math/reasoning
- **Confidence:** LOW (suspect sourcing)

### D.4 Meta Muse Spark 1.2 (Open-Weight Release)
- **Organization:** Meta Superintelligence Labs
- **Announced:** August 6, 2026
- **Status:** Open-weight release pending (announced but not yet released)
- **Typography/image relevance:** NO — text-only output currently; image/audio generation "coming in the future"
- **Licensing intent:** Apache License 2.0
- **Confidence:** MEDIUM

---

## SECTION E: STRUCTURE PRESERVATION BENCHMARKS

*Source: Smith #16*

### E1. KontextBench
- **Source:** arXiv 2506.15742 | https://bfl.ai/blog/flux-1-kontext
- **Size:** 1,026 image-prompt pairs | **Confidence: HIGH**
- **Coverage:** Local editing, global editing, character reference, style reference, text editing
- **Key metrics:**
  - **Non-Edit Consistency:** Evaluates preservation of irrelevant regions | **Confidence: HIGH**
  - **AuraFace Similarity:** Character identity preservation; FLUX.1 Kontext avg **0.908** | **Confidence: HIGH**
  - **CLIP-based scores:** Semantic accuracy in edited regions
- **Leaders:** FLUX.1 Kontext [pro] highest in text editing and character preservation; "particularly strong performance on Non-edit Consistency" | **Confidence: HIGH**

### E2. GEditBench v2
- **Source:** arXiv 2603.28547 (March 2026) | Leaderboard: https://zhangqijiang07.github.io/gedit2_web/
- **Size:** 1,200 real-world user queries | **Confidence: HIGH**
- **Coverage:** 23 predefined tasks + open-set category
- **Evaluation dimensions:** Instruction Following (IF), Visual Quality (VQ), Visual Consistency (VC)
- **Key metric: PVC-Judge** — open-source pairwise assessment model trained via region-decoupled preference data synthesis; achieves **Spearman's rank correlation ρ = 0.929** (p < 2×10⁻⁷) with Arena human rankings | **Confidence: HIGH**
- **Model ranking method:** Bradley-Terry model with ELO score transformation
- **Open-weight leader (as of March 2026):** **FLUX.2 [klein] 9B** — "emerges as the open-source champion" | **Confidence: HIGH**
- **Other competitive open-source:** Qwen-Image-Edit variants, BAGEL, OmniGen2

### E3. VIEScore
- **Source:** arXiv 2312.14867 | GitHub: https://github.com/TIGER-AI-Lab/VIEScore | Project: https://tiger-ai-lab.github.io/VIEScore/
- **Publication:** ACL 2024
- **⚠️ Age flag:** December 2023 source — potentially outdated as of Aug 2026 (Smith #16 explicitly flags this)
- **Metrics:** SC (Semantic Consistency), PQ (Perceptual Quality), O (Overall)
- **Key limitation:** VIEScore (GPT-4o) achieves Spearman correlation **0.4** with human evaluations; human-to-human baseline = 0.45; **"struggles in editing tasks"** specifically | **Confidence: HIGH**
- **Backbone:** GPT-4o or Gemini as MLLM judge

### E4. ImgEdit-Bench (NeurIPS 2025 Datasets & Benchmarks)
- **Source:** arXiv 2505.20275 | GitHub: https://github.com/PKU-YuanGroup/ImgEdit
- **Dataset:** 1.2 million curated edit pairs | **Confidence: HIGH**
- **Evaluation suites:**
  - Basic-Edit Suite: 9 common tasks
  - Understanding-Grounding-Editing (UGE) Suite: complex images + challenging instructions
  - Multi-Turn Suite: content memory and version backtracking
- **Metrics:** GPT-4o 1–5 ratings for Instruction Adherence, Image Editing Quality, **Detail Preservation** ("fidelity of regions that should remain unchanged") | **Confidence: HIGH**
- **Leaders:** ImgEdit-E1 "surpasses all existing open-source models in instruction adherence, detail preservation, and visual quality"; "achieves results comparable to GPT-4o-Image" | **Confidence: HIGH**
- **Leaderboard updated:** July 27, 2025; competitive: Step1X-Edit, BAGEL, OmniGen2, Flux-Kontext-dev, Ovis-U1

### E5. GIE-Bench (Grounded Evaluation for Image Editing)
- **Source:** arXiv 2505.11493 (posted May 26, 2025)
- **Size:** 1,000+ high-quality editing examples; 20 diverse content categories
- **Annotation:** Editing instructions, evaluation questions, spatial object masks
- **Key feature:** Object-aware masking — computes similarity only over regions intended to remain untouched
- **Preservation metrics (example scores):**
  - Masked CLIP (semantic): **0.94** | **Confidence: HIGH**
  - Masked PSNR (pixel): **11.81** | **Confidence: HIGH**
  - Masked MSE (error in preserved regions)
  - Masked SSIM (structural similarity in preserved regions)
- **Models evaluated:** MGIE, OmniGen, GPT-Image-1, StableDiffusion, HQ-Edit, OneDiffusion, InsPix2Pix variants, MagicBrush
- **Key finding:** GPT-Image-1 shows strong functional correctness but "tendency to over-edit irrelevant regions" | **Confidence: HIGH**

### E6. Edit-Compass & EditReward-Compass
- **Source:** arXiv 2605.13062 (June 2025)
- **Dimensions:** IF (Instruction Following), **NC (Non-Edit Consistency)**, VQ (Visual Quality), RA (Reasoning Accuracy)
- **Key advantage:** NC metric "correctly identifies unintended removals that VIEScore overlooks" | **Confidence: HIGH**
- **Coverage:** 36 fine-grained tasks across 6 categories

### E7. UnicEdit-10M (CVPR 2026)
- **Source:** arXiv 2512.02790
- **Dimensions:** Same four as Edit-Compass: IF, NC, VQ, RA
- **NC metric:** Specifically addresses preservation failures
- **Confidence:** HIGH

### E8. Patrick Star Bench (2025)
- **Source:** ScienceDirect 2025
- **Focus:** Consistent mask regions and evaluation metrics across editing modalities; discriminates simple (quantity, color, position) from complex (material transformation, texture) tasks
- **Confidence:** HIGH

### E9. VDE Bench (Visual Document Editing)
- **Source:** arXiv 2602.00122
- **Specialization:** Text-document editing preservation
- **Metrics:** BLEU-4, CDM, TEDS-like for text; IoU for layout consistency; OCR text-level + image visual-level
- **Confidence:** HIGH

### E10. I2EBench (Instruction-based Image Editing)
- **Source:** arXiv 2408.14180 | NeurIPS 2024
- **Metrics:** PSNR, LPIPS, MSE for background preservation
- **Confidence:** HIGH

### E11. Smith #16 Confidence Summary Table (Anderson-preserved)

| Metric | Source | Confidence |
|--------|--------|-----------|
| GEditBench v2 PVC-Judge ρ = 0.929 | arXiv 2603.28547 | HIGH |
| FLUX.1 Kontext AuraFace = 0.908 | arXiv 2506.15742 | HIGH |
| VIEScore GPT-4o r = 0.4 | arXiv 2312.14867 | HIGH |
| GIE-Bench example CLIP = 0.94 | arXiv 2505.11493 | HIGH |
| KontextBench size = 1,026 pairs | arXiv 2506.15742 | HIGH |
| ImgEdit dataset = 1.2M pairs | arXiv 2505.20275 | HIGH |
| FLUX.2 [klein] 9B as open-weight leader | arXiv 2603.28547 | HIGH |

---

## SECTION F: ALPHABET / FONT GENERATION WEB TOOLS

*Source: Smith #17*

### F1. Lipi.ai
- **URL:** https://www.lipi.ai/
- **Input:** Natural language text descriptions
- **Output formats:** TTF, OTF, WOFF, WOFF2 | **Confidence: HIGH**
- **Character coverage:** Uppercase, lowercase, numerals, punctuation, common symbols; 81 languages with full diacritic coverage | **Confidence: MEDIUM** (product claim)
- **License:** "Buy for Use" ($4.99) = non-exclusive commercial; "Full Ownership" ($9.99) = exclusive, copyright transfer | **Confidence: HIGH**
- **Free tier:** Yes (10 free previews)
- **Availability:** 2025

### F2. Mixfont
- **URL:** https://www.mixfont.com/ | Generator: https://www.mixfont.com/font-generator
- **Input:** Text description OR reference image
- **Output:** TTF; >320 glyphs; full alphabet, numerals, punctuation, accents across 26 languages | **Confidence: HIGH**
- **License:** Fully permissive — any use including commercial, resale, redistribution, embedding, sublicensing; no attribution required | **Confidence: HIGH** (https://www.mixfont.com/license)
- **Free tier:** Yes (starter web credits); multiple paid tiers | **Confidence: MEDIUM**
- **Availability:** 2025

### F3. Google GenType
- **URL:** https://labs.google/gentype
- **Launch:** June 2024 | **Confidence: HIGH**
- **Input:** Natural language prompts (e.g., "alphabet made of cake")
- **Output:** Complete A–Z alphabet as PNG images — NOT TTF/OTF font files | **Confidence: HIGH**
- **License:** Free packs (no specified attribution); Premium packs $19–$45 one-time perpetual | **Confidence: MEDIUM** (2024 source)
- **Key distinction:** Image-based output only; not installable fonts

### F4. Font2Art
- **URL:** https://font2.art/en/
- **Specialization:** Chinese/CJK characters (NOT natural language input — requires ~100 handwriting samples or existing font)
- **Output:** 100,000+ CJK characters (Traditional, Simplified, Japanese); TTF, WOFF, WOFF2 | **Confidence: HIGH**
- **Generation time:** 1–2 hours | **Confidence: MEDIUM**
- **License:** Free download | **Confidence: MEDIUM**
- **Availability:** 2025

### F5. ReFontAI
- **URL:** https://refont.ai/
- **Input:** Natural language descriptions OR handwriting/images
- **Output:** Complete alphabet in consistent style; major Latin-based alphabets; CJK gradually being added | **Confidence: MEDIUM**
- **License:** Commercial use under fair-use terms | **Confidence: MEDIUM**

### F6. Canvus
- **URL:** https://canvus.ai/tools/font-generator
- **Input:** Natural language text descriptions
- **Output:** Full character set (serif, sans-serif, decorative, script options)
- **Confidence:** LOW (limited technical details publicly available)

### F7. Figma Plugins
- AI Font Generator plugin (Mixfont): https://www.figma.com/community/plugin/1647427123130432067/ — TTF export; complete alphabet | **Confidence: HIGH**
- Fontma: https://www.figma.com/community/plugin/1665823879003503599/ — Draw in Figma → installable font | **Confidence: HIGH**
- Font-o-matic: https://www.figma.com/community/plugin/1393383433101745773/ — Requires minimum 94 characters | **Confidence: HIGH**
- All free within Figma | **Confidence: HIGH** (plugin registry 2025)

### F8. Open-Source GitHub Projects
- Fancy Fonts Generator (waterrmalann): Unicode pseudofont converter; complete character mappings | HIGH
- FontGenerator using GAN (myconejo): Alphabet font generation via GANs | MEDIUM
- Deep Fonts (erikbern): Deep learning font generation | MEDIUM
- AI_Font_Generator (Johannes-Schall): EfficientNet + custom Encoder/Decoder for filling missing glyphs (e.g., German umlauts); PyTorch + Jupyter | MEDIUM
- Glyph-Generator (MarkMakies): Last commit Jul 6, 2026; random glyph creation, Unicode extraction, ML classification ("good"/"bad"), artistic transformations; NOT production font design | HIGH

### F9. Smith #17 Feature Comparison Table (Anderson-preserved)

| Feature | Lipi.ai | Mixfont | GenType | Font2Art | ReFontAI |
|---------|---------|---------|---------|----------|----------|
| Complete Alphabet | ✓ | ✓ | ✓ | ✓ (100k CJK) | ✓ |
| Natural Language Input | ✓ | ✓ | ✓ | ✗ (handwriting) | ✓ |
| Output Format | TTF/OTF/WOFF/WOFF2 | TTF | PNG | TTF/WOFF/WOFF2 | Unspecified |
| Commercial License | ✓ ($4.99+) | ✓ (Free) | ✓ ($19–45) | ✓ (Free) | ✓ (Fair-use) |
| Free Tier | ✓ | ✓ | ✓ | ✓ | Unspecified |

---

## SECTION G: AI FONT DESIGN TOOL INTEGRATION LANDSCAPE

*Source: Smith #18*

### G1. Core Finding
**No major open-source font design tools (FontForge, Birdfont, fontTools) have integrated native AI generation features into official releases as of August 2026.** All major AI advances remain in academic/standalone form.

### G2. Traditional Tools — AI Integration Status

| Tool | Type | Latest Version | AI Generation | Notes |
|------|------|---------------|---------------|-------|
| FontForge | Open-source | v20251009 (Oct 9, 2025) | NO | Python-scriptable; used as post-processor for AI-generated glyphs; fontforge-mcp exists on Glama.ai |
| Birdfont | Open-source | v6.15.5 (Feb 23, 2026) | NO | Vector graphics editor only; 2026 features: OpenType, SVG import, Linux improvements |
| fontTools | Open-source | v4.60.2+ (2025) | NO | Post-processing library; used downstream of AI pipelines |
| Glyphs.app | Commercial ($300–500) | v3.4–3.5 (Feb 2026) | Stroke harmonization only (NOT generative) | Included for context; NOT open-source |

**Confidence:** HIGH for all (primary sources verified)

### G3. GlyphsGPT Plugin (Third-Party Integration for Glyphs.app)
- **URL:** https://github.com/ShoExperiment/GlyphsGPT
- **Launch:** 2025 | **Confidence: HIGH**
- **Function:** Integrates OpenAI GPT + Anthropic Claude for Python scripting assistance within Glyphs
- **Runs Locally:** NO — requires API keys (cloud APIs)
- **NOT generative:** Assists with scripting, not glyph generation itself
- **Confidence:** HIGH

### G4. Industry Signal
- **Glyphs "Fonts & AI 2025" event:** Oct 23–24, 2025 (online, recorded) — https://glyphsapp.com/events/fonts-ai-2025 — indicates industry awareness of gap between research and tooling | **Confidence: HIGH**

### G5. Dominant Architecture Patterns (2025–2026) per Smith #18
1. Autoregressive models (GAR-Font 2026): Tokenize glyphs → transformer autoregressively
2. Diffusion models (UTDesign, FontDiffuser, DiffuFont): Raster generation via denoising
3. Cascaded diffusion (VecFusion): Raster→vector pipeline
4. LLM-based (VecGlypher): Direct SVG token prediction from text/images
5. Guided diffusion (esFont, FontFusion): Text/image conditioning on diffusion

### G6. Code Availability Status (Smith #18)
- Code available: ~60% of 2025–2026 research projects
- Publicly available: UTDesign, FontDiffuser, Diff-Font, VecGlypher (pending), VecFusion (pending), ClovaAI ecosystem
- NOT available (coming soon / unreleased): GAR-Font, FontCrafter, FontCraft
- Code unconfirmed: DiffuFont, esFont, HFH-Font

---

## SECTION H: CORRECTIONS

### CORRECTION 1 — Smith #11 Categorization Error
Smith #11 categorizes **SRNet (Editing Text in the Wild, 2019)** under "Diffusion Model-Based Approaches." SRNet is a **GAN/CNN-based Style Retention Network** — it predates diffusion models and uses no diffusion process. The three-module architecture is purely convolutional. This is a Smith categorization error. Smith #11's description of the approach is otherwise accurate.

### CORRECTION 2 — Smith #15: FLUX.2 [klein] Release Date
Smith #15 gives release date as **January 15, 2026**. Smith #20 gives **November 2025**. These conflict — see Dispute D1 below.

### CORRECTION 3 — Smith #16: "Open-source" vs. "Open-weight" Terminology
Smith #16 refers to FLUX.2 [klein] 9B as the "open-source champion." The 9B variant has a FLUX Non-Commercial License — it is **open-weight but not open-source** (source code may be available but commercial use of weights is restricted). Smith #15 and #20 both correctly distinguish 4B (Apache 2.0) from 9B (non-commercial). Smith #16's terminology is imprecise but its factual benchmark claim is unaffected.

### CORRECTION 4 — Smith #18: DiffuFont Confidence Elevation
Smith #18 assigns DiffuFont MEDIUM confidence citing a blog source (Simon Cozens). Simon Cozens is a well-known font engineer whose technical evaluations carry domain authority. Anderson note: MEDIUM is appropriate per Anderson triage rules since it is still a single blog source, but Opus should weight it as a credible technical opinion.

### CORRECTION 5 — Smith #19: "Seedream 5.0 Pro" Classification
Smith #19 correctly excludes Seedream 5.0 Pro as "API-only, not open weights." Preserved as-is.

---

## SECTION I: DISPUTES

### DISPUTE D1 — FLUX.2 [klein] 4B Release Date
- **Smith #15:** January 15, 2026 (citing GitHub release notes: https://docs.bfl.ml/release-notes)
- **Smith #20:** November 2025 (citing HuggingFace, GitHub)
- **Anderson recency rule:** Smith #15 gives specific date with specific source. Smith #20 says "Nov 2025" without day-level specificity.
- **Status:** Could be reconciled as November 2025 initial release with January 2026 stable/documented release. Alternatively, one Smith is wrong. **Cannot resolve without primary source verification. Flagged for Opus.**

### DISPUTE D2 — FLUX.2 [klein] 9B: "Open-Source Champion" vs. License Restriction
- **Smith #16:** Names FLUX.2 [klein] 9B as "open-source champion" on GEditBench v2 (citing arxiv 2603.28547)
- **Smith #15 and #20:** Both state only the 4B variant is Apache 2.0; 9B is FLUX Non-Commercial License
- **Anderson assessment:** This is NOT a genuine factual dispute — it is a terminology conflict. FLUX.2 [klein] 9B can be simultaneously the GEditBench v2 leader AND non-commercially licensed. The "open-source champion" label from Smith #16 reflects benchmark performance, not license status. Facts are compatible; terminology is imprecise in Smith #16.

### DISPUTE D3 — Smith #19 "OpenAI Astra" vs. Known AI Landscape
- **Smith #19:** Claims OpenAI announced "Astra" on August 1, 2026 as a model focused on math/reasoning
- **Known context:** "Project Astra" is a Google DeepMind initiative (multimodal AI assistant)
- **Anderson assessment:** This is a probable model confusion or hallucination. The cited Gizmodo URL ("smuggled announcement of Astra into a blog post about math") could plausibly refer to an OpenAI model announcement that is NOT called Astra, or may be entirely fabricated. **Flagged for Opus verification.**

### DISPUTE D4 — DiffUTE Open Weights Availability
- **Smith #11:** "Open Weights: NOT EXPLICITLY STATED"
- **Smith #14:** "Open Weights: NOT EXPLICITLY STATED" (same wording, different Smith)
- **Both Smiths agree this is unknown.** GitHub repository exists (https://github.com/chenhaoxing/DiffUTE) — weights availability not confirmed by either Smith. Not a dispute; agreement on uncertainty.

---

## SECTION J: GAPS

The following topics were **not covered** by any of the 10 Smith reports:

1. **Pricing for FLUX.1 Kontext via API** (as distinct from self-hosted): Smith #13 covers self-hosted at $999/month but does not address per-API-call pricing via BFL's hosted inference.

2. **FLUX.1 Kontext [pro] vs. [dev] capability differences**: Multiple Smiths reference both but none systematically compares the two variants.

3. **Proprietary closed-model APIs for text/letterform style transfer** (e.g., GPT-Image-2, Midjourney style reference, Adobe Firefly current capabilities): Smith #12 attempts this but is quarantined. No reliable data for this category exists in the Chain B corpus.

4. **LoRA / fine-tuning ecosystem for letterform style transfer on open models**: No Smith addresses fine-tuning FLUX or SD variants on custom font datasets.

5. **SVG/vector output from diffusion models** beyond VecGlypher and VecFusion (which are research-stage): No production tool identified.

6. **Benchmark comparison of letterform restyling specifically** (as distinct from general scene text editing or general image editing): Smith #16 covers general editing benchmarks; none specifically benchmarks letterform identity preservation under stylistic transformation.

7. **Mobile / edge deployment** of any of the models or font tools discussed: No coverage.

8. **Watermarking and provenance** of AI-generated fonts or styled text: Only briefly mentioned in Smith #12 (SynthID, quarantined).

9. **Legal status of AI-generated fonts and copyright** for commercial output: Smith #13 addresses licensing terms but not IP ownership of model outputs.

10. **Integration of font AI research into browser-based / no-GPU workflows**: Web tools (Smith #17) are noted but their underlying models are unspecified and not benchmarked.

11. **ComfyUI / diffusers pipelines for letterform tasks**: Smith #18 mentions Gradio for FontDiffuser; no systematic coverage of workflow tooling.

---

## APPENDIX: PERFORMANCE SUMMARY TABLE

*Compiled from Smith #11, #16, #20; all HIGH confidence values unless noted*

| Method | Type | Key Metric | Value | Date | Source Smith |
|--------|------|-----------|-------|------|-------------|
| DiffUTE | Diffusion | OCR Accuracy | 85.41% | 2023 | #11, #14 |
| DiffUTE | Diffusion | Text Correctness | 85.5% | 2023 | #11, #14 |
| DiffUTE | Diffusion | Improvement vs DiffSTE | +14.95% OCR | 2023 | #11, #14 |
| GSDM | Diffusion | PSNR | 33.28 dB | 2024 | #11 |
| GSDM | Diffusion | SSIM | 0.9596 | 2024 | #11 |
| GSDM | Diffusion | CRNN recognition | 67.48% | 2024 | #11 |
| GSDM | Diffusion | ASTER recognition | 74.67% | 2024 | #11 |
| GSDM | Diffusion | MORAN recognition | 73.04% | 2024 | #11 |
| FLUX.1 Kontext | Edit model | AuraFace identity | 0.908 | 2025–26 | #16 |
| GIE-Bench (GPT-Image-1) | Benchmark | Masked CLIP | 0.94 | 2025 | #16 |
| GIE-Bench (GPT-Image-1) | Benchmark | Masked PSNR | 11.81 | 2025 | #16 |
| GEditBench v2 PVC-Judge | Benchmark | Spearman ρ | 0.929 | 2026 | #16 |
| VIEScore (GPT-4o) | Benchmark | Spearman corr. | 0.4 | 2023 | #16 |
| FLUX.2 [klein] 4B | Gen/Edit | Inference speed | ~1.2 sec | 2025–26 | #20 |
| FontFusion | Font control | Decorative font improvement | 76% | 2026 | #18 |
| Qwen-Image-2.0 7B | Gen/Edit | DPG-Bench | 88.32 | 2026 | #20 |

---

*Anderson package complete. All unique signal preserved. Opus to apply editorial judgment.*

---
**Oracle SDK Execution Metrics**
- Architecture: 20 Smiths -> 2 Andersons -> Opus (you)
- Total time: 608s
- Total tokens: 3,532,979 (in: 95,588 | out: 119,083 | cache r/w: 2,622,891/695,417)
- Quota: 0.67% weekly (5.1% session)
- Smiths: 20 (0 errors)
- Andersons: 2 (0 errors)
- Phase timing: scout: 192s | compress: 416s
- Phase costs: decompose: 0.00% | scout: 0.38% | compress: 0.29%

