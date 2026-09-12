============================================================
## Chain A — Anderson Report
============================================================

---

## Anderson Chain-A Processing Summary

**10 Smiths → 8 themed sections | 6 corrections | 4 disputes | 13 gaps | 10 agreement signals**

### What was done

| Operation | Count | Notes |
|---|---|---|
| **DEDUP merges** | 11 methods appeared in 2+ Smiths | VecGlypher (4 Smiths), DiffInk (2), GAR-Font (2), Z-Image (2), Qwen-Image 2.0 (2), EasyText (2), DeepVecFont-v2 (2), VecFusion (2), WordCon (2), LIVE (2), FonTS/WordCon (2) — all merged with all sources cited |
| **RECENCY applied** | 2 cases | GAR-Font date (Jan vs. May 2026 → Jan); Seedream 3.0 data explicitly flagged as stale (2024 vintage) |
| **CORRECTIONS issued** | 6 | EasyText venue (both #6/#7 wrong); GAR-Font date (#8 wrong); VecFusion GitHub (#8 likely wrong); FontCLIP venue (#5 uncertain); Ref2Font license flag (#2); DeepVecFont v3 non-existence |
| **DISPUTES flagged** | 4 | Z-Image Base vs. Turbo; GLM-Image 24 GB compatibility; VecFusion code; HiDream MIT license |
| **AGREE signals** | 10 | VecGlypher SOTA (4-Smith agreement = highest confidence signal in chain) |
| **GAPS identified** | 13 | Biggest: no independent FLUX.2 [flex] benchmark; no RTL script coverage; no FLUX.2 [dev] coverage; no price-vs-quality comparison |

============================================================
## Chain B — Anderson Report
============================================================

# ANDERSON — STRUCTURED FINDINGS REPORT
**Chain B · Smiths #11–#20 · Organized for Opus Synthesis**
*Compiled: 2026-07-17 | All findings preserved; confidence levels and source Smiths cited throughout*

---

## ⚠️ CORRECTIONS (Process First — Affects Downstream Confidence)

### C-1 · arXiv Date Errors in Smith #11 (12-Month Misattributions)

arXiv IDs encode `YYMM.NNNNN`. Three dates are wrong in #11:

| Entry | arXiv ID | #11 Claims | Correct Date | Impact |
|---|---|---|---|---|
| **pi-Flow** | 2510.14974 | "Oct **2024**" | **Oct 2025** | Recency ranking: pi-Flow is 12 months newer than stated |
| **1.x-Distill** | 2604.04018 | "April **2025**" | **April 2026** | Recency ranking: 1.x-Distill is current, not stale |
| **SenseFlow** | 2506.00523 | "May 2025" | **June 2025** (minor) | Minor; paper may have been submitted May, posted June |

### C-2 · arXiv Date Error in Smith #19 (Two-Year Misattribution)

| Entry | arXiv ID | #19 Claims | Correct Date |
|---|---|---|---|
| **Hierarchical Co-Embedding (Hyperbolic Geometry)** | 2604.04158 | "April **2024**" | **April 2026** |

This repositions it from "foundational" to "very recent" — affects how Opus should weight this against older font embedding methods.

### C-3 · FLUX.2 Klein Licensing Error in Smith #11

Smith #11 states Apache 2.0 for the FLUX.2 Klein section without distinguishing variants. Smith #12 explicitly and granularly separates:
- **FLUX.2 Klein 4B → Apache 2.0** (commercial use permitted)
- **FLUX.2 Klein 9B → FLUX Non-Commercial License** (restricted)

Smith #12 is more specific and cites the HuggingFace model cards directly. **#11's blanket Apache 2.0 claim for the Klein family is incorrect for the 9B variant.** All downstream licensing conclusions should use #12's split.

---

## ⚡ DISPUTES (Genuine Conflicts After Removing Stale-vs-Fresh)

### D-1 · Qwen2.5-VL-72B vs. Qwen2.5-VL-7B OCRBench Ordering

- Smith #17: Qwen2.5-VL "~85%+" for 72B variant on OCRBench [MEDIUM confidence]
- Smith #18: Qwen2.5-VL-7B = **88.8%** on OCRBench [HIGH confidence, official Qwen benchmarks]

If the 7B model scores 88.8%, the 72B should score *higher*, not ~85%. Possible explanations: (a) #17's 85%+ refers to a different benchmark version (OCRBench_v2 vs. v1); (b) #17's 85%+ figure is a floor/minimum estimate from a relative comparison against Gemini rather than an absolute score; (c) genuine reporting error in #17. **Not resolvable from available evidence.** Flag for Opus: do not combine these figures as if from the same benchmark.

### D-2 · FLUX.2 Klein Inference Speed (Hardware Ambiguity, Not True Conflict)

- Smith #11: 0.57s @ 1024×1024 on **H100** [HIGH confidence, InferenceBench Jan 2026]
- Smith #12: ~1.2s on **RTX 5090** (4B); ~2s on **RTX 5090** (9B) [HIGH confidence, Apatero]

These are different GPUs on different variants (#11 doesn't specify 4B vs 9B). Not a logical conflict, but the numbers should not be merged. Both are HIGH confidence; cite hardware alongside every latency figure.

---

## 📋 THEME A — FLUX.2 Distillation Methods & Production Checkpoints
*Sources: Smith #11, #12*

### A-1 · Official Black Forest Labs Distilled Models

**FLUX.2 Klein 4B** [AGREE across #11, #12 — HIGH confidence]
- 4-step distilled checkpoint; released Jan 2026
- VRAM: ~13GB (RTX 3090/4090+); Speed: ~1.2s/RTX 5090 (#12), 0.57s/H100 (unspecified variant, #11)
- License: **Apache 2.0** (commercial) [#12 — HIGH]
- LoRA: Supported; train on base-4B, apply on distilled; stacking 3+ strong LoRAs risks oversaturation [#12 — MEDIUM]
- HuggingFace: `black-forest-labs/FLUX.2-klein-4B`; GitHub: `black-forest-labs/flux2`

**FLUX.2 Klein 9B** [AGREE across #11, #12 — HIGH confidence]
- 4-step distilled; ~2s/RTX 5090
- VRAM: 20GB+
- License: **FLUX Non-Commercial License** [#12 — HIGH; corrects #11]
- Quality vs. 4B: Sharper faces, better micro-detail (bee hairs, pollen, flower textures) [#12 — MEDIUM]
- Text encoder: Qwen3 [#11 — HIGH]

**fal/FLUX.2-dev-Turbo** [#12 only — HIGH confidence]
- 8-step distilled LoRA; released Dec 29, 2025
- Speed: ~6.6s @ 1024×1024; 6–8× faster than 50-step base
- ELO: 1,166 (Artificial Analysis); cost: $0.008/image
- Supports stacking up to 3 custom LoRAs (scale 0.1–2.0)
- License: FLUX [dev] Non-Commercial License v2.0
- HuggingFace: `fal/FLUX.2-dev-Turbo`

**No confirmed 2- or 3-step FLUX.2 production checkpoints** as of July 2026 [#12 — MEDIUM confidence on absence]

### A-2 · Open Research Distillation Methods (Ranked by FLUX.2 Readiness)

**pi-Flow (Policy-Based Flow Distillation)** — FLUX.2 LoRA EXISTS
- arXiv 2510.14974 = **October 2025** (corrected from #11's "Oct 2024")
- 4 NFEs; "teacher-level quality + better diversity than DMD at 4 NFEs" [#11 — MEDIUM]
- ImageNet 256²: 1-NFE FID = **2.85** [#11 — HIGH]
- **FLUX.2 LoRA available**: `Lakonik/pi-FLUX.2` (HuggingFace, Jan 2026) [#11 — HIGH]
- Also: FLUX.1 LoRA (`Lakonik/pi-FLUX.1`); ComfyUI nodes available
- GitHub: `Lakonik/piFlow`

**Align Your Flow (AYF)** — FLUX.1 LoRA only
- arXiv 2506.14603, June 2025; NeurIPS 2025 Poster
- Steps 1–8+ with consistent quality; flow maps generalize consistency models [#11 — HIGH theoretical, MEDIUM empirical]
- No direct FLUX.2 port; FLUX.1 LoRA framework [#11 — HIGH]
- NVIDIA Toronto AI lab; code available

**SenseFlow (DMD2+)** — FLUX.1-dev only
- arXiv 2506.00523, **June 2025** (corrected from "May 2025"); ICLR 2026 submission
- Key technique: IDA (Implicit Distribution Alignment) + ISG (Intra-Segment Guidance)
- Solves vanilla DMD convergence failures on large flow models [#11 — HIGH, peer-reviewed]
- 4-step superior; 1-step requires 6,000 fine-tuning iterations from 4-step student [#11 — MEDIUM]
- No FID/LPIPS numbers disclosed for FLUX [#11 — LOW]
- No FLUX.2 port announced [#11 — HIGH]
- GitHub: `XingtongGe/SenseFlow`

**1.x-Distill (Fractional-Step)** — SD3.5 only, not FLUX
- arXiv 2604.04018 = **April 2026** (corrected from #11's "April 2025")
- 1.67–1.74 effective NFEs; 33× speedup vs. 28-step baseline; better diversity vs. 2-step DMD [#11 — HIGH]
- **Only tested on SD3.5-Large; no FLUX port** [#11 — HIGH]
- Promising for flow models; candidate future work

**Score Distillation (SiD)** — FLUX.1-dev, limited
- arXiv 2509.25127, Sept 2025 (Apple ML Research)
- Data-free capable; verified on FLUX.1-dev (0.6B–12B) [#11 — HIGH]
- FLUX.2 port: limited/in-progress [#11 — HIGH]
- GitHub: forthcoming

**TDD (Target-Driven Distillation)** — FLUX.1-dev LoRA, aging
- arXiv 2409.01347, Sept 2024 (22 months old as of July 2026)
- LoRA weights: `RED-AIGC/TDD` (FLUX-TDD-ADV released Jan 2025, FLUX-TDD-BETA Sept 2024)
- Lower FID than LCM/PCM baselines [#11 — MEDIUM; unverified vs. FLUX.2]
- No FLUX.2 port; #11 explicitly flags age

**Hyper-SD (ByteDance)** — FLUX.1-dev LoRA only
- 8-step and 16-step FLUX.1-dev LoRAs; HuggingFace `ByteDance/Hyper-SD`
- LoRA scale recommendation: ~0.125
- No FLUX.2 port [#11 — HIGH]

**NanoFLUX** — FLUX.1-Schnell compression for mobile
- arXiv 2602.06879, Feb 2026
- 2.4B params (compressed from 17B FLUX.1-Schnell)
- Evaluated on One-IG, DPG, GenEval, HPDv3 [#11 — MEDIUM]
- No FLUX.2 port [#11 — HIGH]

**Deprecated Methods** [AGREE between #11; #12 does not contradict]
- LCM (Oct 2023, 33 months old): Superseded; no FLUX flow-matching port [HIGH]
- TCD (Feb 2024, 29 months): Still used but not FLUX-optimized [HIGH]
- InstaFlow (Sept 2023, 34 months): Pre-flow-matching era; 183 A100 days training cost [HIGH]
- PCM (May 2024): "Difficult to yield satisfactory results on vector diffusion models" [HIGH]

### A-3 · NVIDIA PiD (Decoder-Only, Not Full Checkpoint) [#12 only — HIGH]
- Distilled VAE decoder replacement (latent→pixel), not a generative model
- 4-step via DMD2; 2K–4K upscaling
- Recommended variant: `2kto4k_v1pt5` (for FLUX, FLUX.2, Qwen-Image)
- Released June 2026; License: NSCLv1 (non-commercial research/evaluation only)
- HuggingFace: `nvidia/PiD`

### A-4 · Recommended Ranking (Synthesized #11 + #12 Corrections Applied)

| Rank | Method | Steps | FLUX.2 Ready | Key Caveat |
|---|---|---|---|---|
| 1 | FLUX.2 Klein 4B | 4 | ✅ Official | Apache 2.0; no custom training |
| 2 | fal/FLUX.2-dev-Turbo | 8 | ✅ LoRA | Non-commercial; managed |
| 3 | FLUX.2 Klein 9B | 4 | ✅ Official | Non-commercial license |
| 4 | pi-Flow (FLUX.2 LoRA) | 4 NFE | ✅ LoRA | Oct 2025 paper; Jan 2026 LoRA |
| 5 | SenseFlow | 4 | ❌ FLUX.1 only | Await FLUX.2 port |
| 6 | Align Your Flow | 1–8+ | ❌ FLUX.1 only | Best flexibility |
| 7 | Score Distillation (SiD) | 4 | 🔄 In progress | Data-free, emerging |
| 8 | 1.x-Distill | ~1.7 NFE | ❌ SD3.5 only | April 2026; no FLUX port |

---

## 📋 THEME B — Quantization Infrastructure for FLUX.2

### B-1 · Nunchaku FLUX.2 Support Status [Smith #13 — HIGH confidence throughout]

**Official status: NOT SHIPPED as of July 2026**

Key evidence timeline:
| Event | Date | Confidence |
|---|---|---|
| Issue #826 opened: "Plans to support FLUX.2?" | Dec 20, 2025 | HIGH |
| Issue #883 opened: "Flux2Klein is out" — no maintainer response | Jan 15, 2026 | HIGH |
| v1.2.0 released | Jan 12, 2026 | HIGH |
| v1.2.1 released (no FLUX.2) | Jan 25, 2026 | HIGH |
| PR #926 (FLUX.2 support) — **unmerged** | Current | MEDIUM |
| v1.3.0 in development (nightly) | As of fetch | HIGH |

Infrastructure exists (`transformer_flux_v2.py` in repo; documented in v1.3.0 docs at `nunchaku.models.transformers.transformer_flux_v2`) but lacks production merge, release announcement, and documented LoRA/caching features for FLUX.2.

**LoRA Runtime Loading for FLUX.2:** Undocumented officially. FLUX.1 confirmed via `transformer.update_lora_params()` + `transformer.set_lora_strength()` (v0.2.0+). Community mentions FLUX.2 Klein LoRA via third-party wheel (`tonera/vitoom-nunchaku` HuggingFace) [MEDIUM].

**Step-Caching for FLUX.2:** None found. FB Cache and Double FB Cache (v0.3.0+) documented for FLUX.1 only [HIGH]. No "step-cache" adapter terminology found for any model [MEDIUM].

### B-2 · SVDQuant / deepcompressor FLUX.2 Status [Smith #14 — HIGH confidence]

**Official status: NO FLUX.2 RECIPE as of July 2026**

- deepcompressor repo last updated 2026-07-14; last meaningful commit **2025-08-14**
- Only `flux.1-dev.yaml` and `flux.1-schnell.yaml` model configs exist [HIGH]
- README explicitly: "FLUX.1 validates the effectiveness of SVDQuant"

**SVDQuant W4A4 Quality Results for FLUX.1** (5,000-sample MJHQ-30K):
- FLUX.1-dev INT W4A4: FID **19.9** (vs. 20.3 BF16 baseline) [MEDIUM]
- FLUX.1-schnell INT W4A4: FID **18.3** (vs. 19.2 BF16) [MEDIUM]

**Currently supported models:** FLUX.1-dev (12B), FLUX.1-schnell (12B), SANA-1.6B, PixArt-Sigma [HIGH]

**Third-party forks:** No FLUX.2-specific forks found. Notable forks all predate or ignore FLUX.2:
- `spooknik/deepcompressor-guide`: Last push Oct 2025; "Coming soon: Qwen, WAN" — no FLUX.2 [HIGH]
- `yxxsjby007/deepcompressor_svdquant_reproduction`: Abandoned Jan 2026 [HIGH]
- `FoundationResearch/DeepCompressor`: Nov 2025, scope unclear [MEDIUM]

**Alternatives for FLUX.2 W4A4 on consumer GPUs:**
- W4A16 (AWQ/GPTQ): Lower memory, no activation quantization sensitivity; slower than W4A4
- Mixed precision W4A8KV4 (QoQ algorithm): LLM-focused; needs diffusion adaptation
- SmoothQuant W8A8: More stable on new architectures

**Note:** SVDQuant's low-rank branch absorption technique depends on specific outlier patterns in FLUX.1 that may differ in FLUX.2 architecture [#14 — MEDIUM]

---

## 📋 THEME C — Memory-Efficient LoRA Training on 24GB Consumer GPUs
*Source: Smith #15*

### C-1 · Benchmark Numbers (RTX 4090 Primary Reference)

| Model | Config | VRAM | Duration | Steps/Min | Confidence |
|---|---|---|---|---|---|
| FLUX.1-dev (12B) | QLoRA NF4, r32, bs1, 512×768 | ~9–10 GB | 41 min/700 steps | ~17 | HIGH [HF Blog] |
| FLUX.1-dev (12B) | BF16 LoRA (non-quantized) | ~26 GB | — | — | HIGH |
| FLUX.1-dev (12B) | Full BF16 fine-tuning | ~120 GB | — | — | HIGH |
| FLUX.2 Klein (9B) | LoRA FP8?, r32, bs4–8, 512×768 | ~20–23 GB | ~30 min/1000 steps | ~33 | MEDIUM [blog.fal.ai] |
| SANA-1.6B | Full fine-tune, 8-bit Adam, grad ckpt | ~43 GB | — | — | MEDIUM |

**Key insight:** FLUX.2 Klein (9B) achieves ~2× faster training throughput than FLUX.1-dev QLoRA, attributed to smaller model size (9B vs. 12B) [#15 — MEDIUM]

### C-2 · Quantization Techniques

**NF4 (4-bit Normal Float)**
- Information-theoretically optimal for normally-distributed weights [HIGH]
- QLoRA NF4 ≈ 16-bit LoRA & 16-bit full fine-tuning quality on academic benchmarks [HIGH, HF bitsandbytes blog]
- Peak memory: ~9–10 GB on RTX 4090 for FLUX.1-dev

**FP8**
- FLUX.2 Klein inference: ~14–16 GB at FP8 on RTX 4090 (vs. ~29 GB at FP16)
- BFL provides FP8 and NVFP4 checkpoints officially
- FP8 reduces VRAM ~40%; NVFP4 ~55% [HIGH, WillItRunAI 2026]
- Speed on RTX 4090: ~5–10 sec/image @ 1024×1024 with FP8 [MEDIUM]

**NVFP4:** ~55% VRAM reduction vs. FP16 [HIGH]

### C-3 · Optimizer Strategies

**AdamW 8-bit (bitsandbytes):**
- ~75% reduction in optimizer state footprint vs. FP32 [HIGH]
- DreamBooth SD: 12.5 GB VRAM, 2× faster vs. standard [MEDIUM, AUTOMATIC1111 discussion]

**Adafactor + Fused Backward Pass (Kohya SS v0.9.0+, Jan 2025):**
- Integrates backward + optimizer step into single pass (requires Adafactor + PyTorch 2.1+)
- SDXL: 24 GB → 17 GB (FP32) or 10 GB (BF16) [HIGH, sanj.dev]
- FLUX.1: 24 GB → 4–8 GB with fused backward + other optimizations [MEDIUM]

**CAME-8bit (SANA):**
- 25% memory reduction (57 GB → 43 GB) vs. standard AdamW, no convergence degradation [MEDIUM, arXiv 2501.18427]

### C-4 · LoRA Rank vs. VRAM on 24GB

| Rank | Memory Overhead | Recommendation |
|---|---|---|
| 32 | Baseline | ✅ Sweet spot; handles simple subjects & styles |
| 48 | +minor | ✅ Complex subjects |
| 64 | +0.3–0.6 GB | ⚠️ Feasible; needed for complex faces/detail |
| 128 | +1 GB+ | ❌ Impractical; overfitting risk without quality gains |

[HIGH confidence, multiple 2025 sources: Civitai, Apatero, Jarvislabs.ai]
**Training speed largely unaffected by rank increases** [MEDIUM]

### C-5 · Advanced Memory Techniques

**Gradient Checkpointing:**
- ~35% reduction in activation VRAM; increases compute time [MEDIUM, Axolotl/Meta PyTorch docs]

**Flash Attention 2:**
- Forward pass: 1.3–1.5× faster than v1; Backward: ~2× faster than v1; ~10× vs. standard PyTorch attention [MEDIUM, arXiv 2307.08691]
- Standard in Kohya, SimpleTuner, AI-Toolkit

**GaLore (Gradient Low-Rank Projection):**
- Standard: 65.5% optimizer state reduction; 8-bit GaLore: 82.5% optimizer + 63.3% total training memory reduction [HIGH, ICLR 2024]
- **No diffusion transformer benchmarks published — theoretical application only** [LOW confidence for diffusion]

**SimpleTuner:**
- <10 GB VRAM for FLUX.2 on 20–24GB by combining: int8/fp8/NF4 quantization + cached VAE latents + 8-bit AdamW [MEDIUM, Apatero 2025]

### C-6 · Recent Papers (2025–2026)

**CDM-QTA** (Apr 2025, arXiv 2504.07998):
- Fully quantized training W8A8; 1.81× speedup, 5.50× energy efficiency [HIGH]
- **Tested on generic diffusion; FLUX-specific numbers not provided** [LOW for FLUX]

**Q-DiT** (CVPR 2025):
- Post-training inference quantization; W8A8 FID improvement +1.26 on DiT-XL/2; W4A8 marginal FID increase [HIGH]
- **No LoRA integration reported** [LOW for LoRA training]

**LoRAM** (ICLR 2025, arXiv 2502.13533):
- Train on pruned model → recover for full-model inference; 70B model in 20GB HBM
- **Diffusion applicability noted as open question; no practical evidence yet** [LOW]

### C-7 · Recommended Configurations

**Conservative (High Quality, 24GB GPU):**
- QLoRA (NF4, 4-bit) base + rank 32 + 8-bit AdamW + gradient checkpointing
- Estimated: 8–15 GB VRAM; 30–45 min/1000 steps on RTX 4090

**Aggressive (Maximum Throughput, 24GB GPU):**
- QLoRA (NF4) + rank 64 + Adafactor + Fused Backward + Cached VAE latents + Flash Attention 2
- Estimated: 18–22 GB VRAM; ~30 min/1000 steps on RTX 4090 (tight fit)

---

## 📋 THEME D — LoRA Variants for Diffusion Models
*Source: Smith #16*

### D-1 · Critical Meta-Finding

**Most LoRA variants lack diffusion-specific peer-reviewed benchmarks.** The only 2024 paper systematically benchmarking multiple variants *specifically on diffusion models* is LyCORIS (ICLR 2024) covering LoKr and LoHa. All other variants (DoRA, PiSSA, rsLoRA, LoRA+) were developed and benchmarked exclusively on LLMs.

### D-2 · Per-Variant Evidence

**LoKr & LoHa (LyCORIS) — Primary Diffusion Evidence** [HIGH]
- Paper: arXiv 2309.14859, ICLR 2024 (peer-reviewed)
- Models tested: SD 1.5 and SDXL
- 234 checkpoints trained (26 hyperparameter configs × 3 seeds × 3 checkpoints)
- **LoHa:** Optimized for simple, multi-concept fine-tuning (character + style combinations)
- **LoKr:** Better for complex, single-concept tasks; harder to transfer across architectures
- LoHa/LoKr: Slower training, higher quality; risk of overtraining quickly
- Standard LoRA: Faster training, may miss fine details [HIGH]
- Support: LyCORIS (native), PEFT ≥ 0.7.1, Diffusers (advanced examples)

**DoRA (Weight-Decomposed Low-Rank Adaptation)** — Experimental for diffusion
- arXiv 2402.09353, ICML 2024 Oral (1.5% acceptance rate)
- LLM results: Llama 7B/13B +3.7/+1.0 commonsense reasoning; Llama 3 8B +4.4 [HIGH]
- **Explicitly "experimental" for diffusion; "likely requires different hyperparameter values"** [HIGH, NVIDIA blog citing authors]
- SDXL DreamBooth: Anecdotal "quite detailed" outputs; no quantitative metrics [LOW]
- Support: PEFT ≥ 0.10 (requires magnitude folding during merge); Diffusers via PEFT backend [HIGH]

**PiSSA** — Zero diffusion experiments
- arXiv 2404.02948, NeurIPS 2024 Spotlight
- GSM8K Mistral-7B: 72.86% vs LoRA 67.7% (+5.16 pp) [HIGH]
- **Zero diffusion experiments in paper** [HIGH]
- Support: PEFT (yes); Diffusers (not mentioned) [MEDIUM]

**rsLoRA (Rank-Stabilized)** — LLM only
- arXiv 2312.03732, Dec 2023
- Enables stable learning at very high ranks (≤2048) via √rank scaling [HIGH]
- **No diffusion experiments** [HIGH]
- Support: PEFT (yes); Diffusers (no explicit mention) [MEDIUM]

**LoRA+** — LLM only, not integrated
- arXiv 2402.12354, ICML 2024
- ~2× faster convergence; +1–2% on LLM tasks [HIGH]; B matrix learns 16× faster than A [HIGH]
- **No diffusion experiments** [HIGH]
- Support: External repo only; not in PEFT or Diffusers [MEDIUM]

### D-3 · Library Support Matrix (July 2026)

| Method | PEFT | Diffusers | LyCORIS | Diffusion Evidence |
|---|---|---|---|---|
| LoRA | ✅ | ✅ | ✅ | Strong (baseline) |
| DoRA | ✅ v0.10+ | ✅ via PEFT | ✅ | Experimental [HIGH] |
| PiSSA | ✅ | ⚠️ via PEFT | ❌ | None [HIGH] |
| rsLoRA | ✅ | ⚠️ via PEFT | ❌ | None [HIGH] |
| LoRA+ | ❌ external | ❌ | ❌ | None [HIGH] |
| LoKr | ✅ | ⚠️ advanced | ✅ | ICLR 2024 [HIGH] |
| LoHa | ✅ | ⚠️ advanced | ✅ | ICLR 2024 [HIGH] |

### D-4 · Community Benchmark (Low Confidence, Included for Signal)

**Tensor.Art HALLOWEEN2024 Campaign** (Oct 2024):
- LoRA vs. LoKr vs. DoRA on SDXL/Flux
- "DoRA requires more compute but better for detailed/consistent styles; LoKr intermediate; LoRA fastest"
- [LOW confidence — community, not peer-reviewed]

**Recommendation from #16:** Use LoKr/LoHa for production diffusion work (ICLR-validated); treat DoRA as promising but unvalidated; avoid PiSSA/rsLoRA/LoRA+ without additional benchmarking.

---

## 📋 THEME E — OCR Models for Character/Glyph Recognition (Mid-2026)
*Sources: Smith #17, #18*

### E-1 · Master Model Table (Merged from #17 + #18)

| Model | Params | OCRBench | Speed | License | Source | Date |
|---|---|---|---|---|---|---|
| **PP-OCRv6** | 1.5M–34.5M | 83.2% rec. acc | 0.25–0.32s/img (A100) | Apache 2.0 | #17 HIGH | June 2026 |
| **DeepSeek-OCR-2** | 3B nom. / 570M active | 97% (vendor) | 0.005s/img (A100) | Apache 2.0 | #17 MEDIUM | Jan 27, 2026 |
| **Surya-OCR-2** | 650M | 83.3% (olmOCR-bench) | 5.35 pages/sec GPU | Apache 2.0 (code); AI Pubs Rail-M (weights) | #17 HIGH | Apr 2026 |
| **Qwen3-VL-8B** | 8B | **89.6%** | ~40–50 t/s (est.) | Apache 2.0 | #18 HIGH | Late 2025 |
| **Qwen3-VL-4B** | 4B | Not published | 60–70 t/s | Apache 2.0 | #18 MEDIUM | Late 2025 |
| **Qwen2.5-VL-7B** | 7B | 88.8% | — | Apache 2.0 | #18 HIGH | Jan 2025 ⚠️ |
| **InternVL3.5-4B** | 4B | Not published | ~60–70 t/s (est.) | — | #18 HIGH | 2025 |
| **InternVL3.5-2B** | 2B | VCR EM 93.2% (proxy) | ~70–90 t/s (est.) | — | #18 HIGH | 2025 |
| **SmolVLM-2.2B** | 2.2B | 72.9% | 3–5× faster than 7B | Apache 2.0 | #18 HIGH | Apr 2025 |
| **SmolVLM-500M** | 500M | 61.0% | Very fast | Apache 2.0 | #18 HIGH | Apr 2025 |
| **SmolVLM-256M** | 256M | 52.6% | Fastest | Apache 2.0 | #18 HIGH | Apr 2025 |
| **GOT-OCR2** | 580M (80M enc + 500M dec) | No specific % | GPU-required | Apache 2.0 | #17 #18 AGREE | Sept 2024 ⚠️ |
| **Florence-2-Large** | 0.77B | TextVQA 81.5% (not OCRBench) | ~1s/img T4; 45ms Jetson Orin | MIT | #17 #18 AGREE | June 2024 ⚠️ |
| **Mistral OCR 4** | Proprietary | 94.9% (vendor) | — | Proprietary API | #17 MEDIUM | June 23, 2026 |
| **Moondream 2** | 1.9B | **Unknown** (no OCRBench published) | <400ms (unspecified op) | — | #18 LOW | Mar 2026 |

⚠️ = More than 12 months old as of July 2026

### E-2 · Agreements Between Smith #17 and #18

- **Florence-2:** Both report TextVQA 81.5%, both flag as outdated (June 2024), both recommend against for OCR specialist use [AGREE — HIGH]
- **GOT-OCR2:** Both cite 580M params; both note it's 9 months old (Sept 2024) with no updated version [AGREE — HIGH]
- **VLMs vs. traditional engines:** Both note VLMs run 5–10× slower than traditional engines like PaddleOCR [AGREE — MEDIUM]
- **No symbol/punctuation-isolated benchmark exists:** Critical finding shared by both — no vendor publishes per-symbol-type accuracy [AGREE — HIGH]

### E-3 · Per-Model Detailed Notes

**PP-OCRv6 (June 2026 — most current traditional engine)** [#17 — HIGH]
- +5.1 pp over v5; 93.2% exact match rate (vendor-reported)
- Symbol/punctuation dictionary expanded ~200 accent/punctuation characters; "dense numbers and special symbols (•, -, +) accurately recognized"
- No hallucination risk (traditional engine, not VLM)
- Intel Xeon OpenVINO: 7.30s (server), 0.78s (mobile); Apple M4: >10s (server), 5.82s (mobile)

**DeepSeek-OCR-2 (Jan 27, 2026)** [#17 — MEDIUM confidence; 97% is vendor-reported, unverified]
- MoE architecture: 3B nominal but only 570M active (6/64 experts + 2 shared)
- 200,000+ pages/day on single A100 = ~0.43ms/page
- Uses only 100 vision tokens/page (vs. 256+ for GOT-OCR2)
- "Best character-level OCR" in ancient Greek benchmark comparison vs. Qwen3-VL [MEDIUM]
- CPU inference: 10–50× slower than GPU [MEDIUM]
- Only ~6 months old; independent validation lacking

**Qwen3-VL-8B (Late 2025)** [#18 — HIGH]
- 89.6% OCRBench (state-of-the-art for <8B open models)
- Vision encoder: SigLIP2-SO (400M params)
- Multilingual: 39 languages; specialized OCR training
- Fits RTX 4090 in FP8
- Vision preprocessing latency (Qwen3-VL-4B): 343.78ms @ 4096×4096

**Qwen3-VL-4B OCRBench: Not published** [#18 — gap explicitly noted]
- Throughput: 60–70 tokens/sec [HIGH, AMD MI300X / applicable to RTX 4090]
- OCR accuracy estimate ~87–88% inferred from scaling [MEDIUM — LOW confidence]

**InternVL3.5-4B** [#18 — HIGH]
- No OCRBench score published in searched sources
- DocVQA: 89.4% [HIGH]; AI2D: 82.6% [HIGH]
- VCR (character restoration): InternVL2.5-2B EM **93.2%** / Jaccard **97.6%** [HIGH, arXiv 2412.05271] — strong proxy for character-level understanding
- InternVL3-2B improvement on related metric: 50.7 (vs. predecessor 32.4) [MEDIUM]

**Moondream 2 (Mar 2026)** [#18 — LOW on OCR]
- 40% faster than previous version [MEDIUM]
- Moondream 3.1 on H100 Photon: 59ms/request; ~150–250ms on RTX 4090 estimated [LOW]
- **Insufficient character/glyph recognition benchmark data to rank vs. others**

**Emerging (June–July 2026)** [#17 — MEDIUM/LOW, very recent]
- **Baidu Unlimited-OCR** (June 22, 2026): Processes full PDFs without chunking; no accuracy metrics yet
- **Qwen3-VL-8B on ancient scripts:** ~5.1% CER [MEDIUM]; >70% accuracy on 32/39 languages [MEDIUM]
- **MinerU2.5 & HunyuanOCR:** No public accuracy numbers yet

### E-4 · Critical Gap (AGREE across #17 and #18)

**No published benchmark isolates single-character or symbol-only accuracy for any model.** All metrics are line-level (OCRBench) or page-level (OmniDocBench). The specific requirement for symbol + punctuation accuracy per character type is not currently benchmarked by any vendor. Recommendation from both Smiths: run own benchmark on candidate dataset.

### E-5 · Recommendations by Use Case (Synthesized)

**Replacing TrOCR (symbol hallucination):**
1. PP-OCRv6-medium: No hallucination; explicit symbol support; best CPU performance
2. DeepSeek-OCR-2: Highest reported accuracy; needs GPU; unverified independently
3. Surya-OCR-2: Good speed+accuracy balance; weights require commercial license for large orgs

**If VLM approach acceptable:**
1. Qwen3-VL-8B: Best documented OCRBench performance (89.6%); Apache 2.0
2. Qwen2.5-VL-7B: 88.8% OCRBench; older (Jan 2025) but well-documented
3. InternVL3.5-4B: Strong character restoration; DocVQA 89.4%; OCRBench not published

---

## 📋 THEME F — Font Style Embeddings & Similarity Models
*Source: Smith #19 (corrected per C-2 above)*

### F-1 · Model Directory

**DINOv2 + LoRA on GoogleFontsBench** [#19 — HIGH]
- arXiv 2602.13889, February 2026
- Architecture: DINOv2 ViT (87.2M) + LoRA adapters (1% trainable parameters)
- Performance: **99.0% top-1 accuracy** on GoogleFontsBench (394 variants × 32 families, ~226K synthetic images)
- 140× lower error severity than random
- Self-supervised pre-training: texture + edge detail captured without text bias
- Code: Open-source (models + training pipeline)

**FontCLIP** [#19 — HIGH]
- arXiv 2403.06453, March 2024
- Architecture: Fine-tuned CLIP encoder bridging font images ↔ semantic/impression text
- Capabilities: Weight, serif attributes via dual-modal embeddings; cross-lingual retrieval (CJK generalization); vector font optimization
- Advantage over generic CLIP/DINOv2: Typography-specific fine-tuning; semantic attribute binding
- Code: Available at official project page

**Impression-CLIP (Contrastive Shape-Impression)** [#19 — HIGH]
- arXiv 2402.16350, February 2024
- Co-embeds font shapes + impression tags in shared space; uses negative pairs (unlike Cross-AE)
- Superior bidirectional retrieval vs. one-to-one baselines
- Code: Not released

**Hierarchical Co-Embedding (Hyperbolic Geometry)** [#19 — HIGH; date corrected]
- arXiv 2604.04158, **April 2026** (corrected from #19's "April 2024")
- Captures style specificity hierarchy: low-specificity impressions near origin, high-specificity farther out
- Interpretable radial structure; entailment constraints
- Dataset: MyFonts
- Code: Not released

**Font Representation via Paired-Glyph Matching (BMVC 2022)** [#19 — HIGH; foundational]
- arXiv 2211.10967, November 2022
- Contrastive metric learning: pulls same-font glyph pairs closer, pushes different-font apart
- Better generalization to new fonts + new characters than prior methods
- Code: Available at `github.com/junhocho/paired-glyph-matching`

**gaborcselle/font-identifier** [#19 — HIGH]
- ~2024; ResNet-18 + custom FC layers
- **96.3% accuracy on 48 standard system fonts** (2.4K test images, 80/20 split)
- **Classification only; does not produce style similarity embeddings**
- Code: Full PyTorch training + inference notebook; HuggingFace: `gaborcselle/font-identifier`
- Extended by `Brand-Review/FontIdentification-PaddleOCR-gaborcselle_font_identifier` (Aug 2025)

**DS-Font (Few-Shot Font Generation)** [#19 — HIGH; ICCV 2023]
- arXiv 2301.10008, January 2023
- Cluster-level Contrastive Style (CCS) loss; disentangles global style from structure
- Primarily for generation; style encoder useful for embeddings
- Code: `github.com/awei669/VQ-Font`

**VQ-Font (Vector Quantization)** [#19 — HIGH; AAAI 2024]
- arXiv 2308.14018, AAAI 2024
- VQGAN with structure-aware enhancement + token prior codebook
- Discrete style space via codebook (potentially useful for discrete embeddings)
- Code: `github.com/Yaomingshuai/VQ-Font`

**EdgeFont (Multi-Scale Edge Self-Supervision)** [#19 — HIGH]
- 2024; vs. FUNIT: +0.95 PSNR, +0.055 SSIM, -51.73 FID
- Code: Not released

**google-font-finder** [#19 — MEDIUM]
- `github.com/yv3nne/google-font-finder`; March 2025 creation, March 2026 last update
- Vector-based font embedding database for similarity search against Google Fonts
- Active development

**FM-Font** [#19 — MEDIUM; very recent]
- GitHub: `github.com/wxyxh/FM-Font`; June 2026
- Very recent; limited documentation

### F-2 · Critical Finding: Font Style Resistant to VLM Fine-Tuning

**"Reading ≠ Seeing" paper** (arXiv 2603.08497, March 2026) [#19 — HIGH]
- 26 fonts × 4 scripts × 3 difficulty levels across 15 SOTA VLMs
- Perception hierarchy: **Color > size > family > style**
- Font style recognition remains universally poor despite model scale
- LoRA fine-tuning on synthetic samples improves open-source models but **font style remains resistant**
- Implication: Patch-based encoders insufficient; architectural innovation needed for relational style reasoning

**"Texture or Semantics?" paper** (arXiv 2503.23768, COLM 2025) [#19 — HIGH]
- VLMs (GPT-4V, Claude, etc.) fail at font recognition despite near-perfect text reading
- Root cause: Models attend to text semantics, not visual typography
- Few-shot & CoT provide "minimal benefits"
- Implication: Generic VLMs inadequate; specialized font encoders needed

**Font recognition benchmark (Claude-3.5-Sonnet):** ~31% on font recognition easy version, zero-shot [#19 — HIGH]

### F-3 · Comparative Performance

| Model | Font Task | Key Advantage | Date | Confidence |
|---|---|---|---|---|
| DINOv2 + LoRA | Classification | 99.0% top-1; 1% params; no text bias | Feb 2026 | HIGH |
| FontCLIP | Style similarity + language | Semantic binding; cross-lingual; attribute text | Mar 2024 | HIGH |
| Paired-Glyph Matching | Similarity metric | Glyph-level contrastive; generalizes to new fonts | Nov 2022 | HIGH |
| Generic CLIP | Style similarity | Poor (text bias subsumes typography) | — | HIGH |
| Generic ViT | Classification | Moderate; requires heavy fine-tuning | — | MEDIUM |

### F-4 · Code Availability

✅ Available: Paired-glyph Matching, gaborcselle/font-identifier, VQ-Font, FontCLIP (project site), google-font-finder, FM-Font (Jun 2026), DS-Font
❌ Not released: Impression-CLIP, EdgeFont, Hierarchical Co-Embedding

---

## 📋 THEME G — No-Reference Glyph & Image Quality Predictors
*Source: Smith #20*

### G-1 · Text/Glyph-Specific Quality Assessment

**TIQA: Human-Aligned Perceptual Text Quality Assessment** [#20 — HIGH]
- arXiv 2603.07119, March 2026
- No-reference scorer for text-in-image regions; predicts scalar quality independent of semantic correctness
- Dataset: 120K text crops, 10K MOS labels, 36K AI-generated images
- Targets: glyph topology, stroke continuity, spacing, baseline stability
- Outperforms CER/Levenshtein by catching perceptual defects humans penalize even when text is machine-readable
- **Most directly relevant tool for glyph quality without ground truth**

**DIQA: Document Image Quality Assessment** [#20 — HIGH]
- Frontiers Signal Processing 2026
- Predicts OCR accuracy without executing OCR engine; 12 distinct metrics (sharpness, focus, edge clarity, distortion)
- Objective vs. subjective methods available

**GlyphPrinter** [#20 — HIGH; CVPR 2026 Highlight]
- arXiv 2603.15616; GitHub: `FudanCVL/GlyphPrinter`
- R-GDPO (Region-Grouped Direct Preference Optimization): regional-level glyph preference annotations
- Handles stroke distortion, incorrect glyphs, complex Chinese/multilingual text
- Dataset: GlyphCorrector with region-level preferences
- Outperforms existing methods on glyph accuracy while maintaining stylization balance
- No explicit external reward model dependency

**GLYPH-SR (VLM-Guided Latent Diffusion)** [#20 — HIGH]
- arXiv 2505.06543; CVPR 2025
- Dual-axis protocol: OCR F1 + perceptual quality
- Result: **+15.18 pp improvement in OCR F1** while maintaining top-tier perceptual quality

**Glyph-ByT5-v2** [#20 — HIGH]
- arXiv 2406.10208; ICLR 2025
- Customized text encoder for visual text rendering; 10 languages; high spelling accuracy

**OCR-Quality Dataset** [#20 — HIGH]
- arXiv 2510.21774, 2025
- 1,000 PDF pages → PNG @ 300 DPI; 10K MOS labels + 110K proxy labels; 4-level scoring

**CER Benchmarks** [#20 — HIGH/MEDIUM]
- 1.4% CER ≈ 7% word error rate on typical 2,500-char page [MEDIUM]
- Average OCR accuracy 2025: 96.5% [MEDIUM]
- 300 DPI minimum, <1% CER for printed text standard [HIGH, 2026]

### G-2 · Aesthetic/Human Preference Predictors

**Human Preference Score v3 (HPSv3)** [#20 — HIGH; ICCV 2025]
- arXiv 2508.03789; GitHub: `MizzenAI/HPSv3`
- Dataset: HPDv3 = 1.08M text-image pairs + 1.17M pairwise comparisons
- Architecture: Qwen2-VL backbone + RankNet loss
- Chain-of-Human-Preference (CoHP): iterative refinement without retraining
- Published August 2025

**PickScore** [#20 — HIGH; stable baseline]
- arXiv 2305.01569; HuggingFace: `yuvalkirstain/PickScore_v1`
- 176K+ Pick-a-Pic user preferences; Win rates: 71.3% vs. CLIP-H, 85.1% vs. aesthetics predictor, 71.4% vs. vanilla
- Per-instance scoring conditioned on prompt; used in best-of-K reranking in production

**LAION Aesthetic Predictor V2** [#20 — HIGH]
- CLIP embeddings + MLP; 176K images rated 1–10
- Used with GRPO at ICML 2025 for VAR model fine-tuning

**SPO (Step-by-step Preference Optimization)** [#20 — HIGH; CVPR 2025]
- GitHub: `RockeyCoss/SPO`
- Separates aesthetic preferences from layout/alignment at different diffusion steps
- Applied to SD v1.5, SDXL; better aesthetics than vanilla DPO, faster convergence
- **Note:** Not tested on FLUX/FLUX.2 specifically

**DRM (Diffusion-based Reward Model)** [#20 — MEDIUM]
- arXiv 2605.25661
- Accuracy: 64.1% (PickScore), 73.4% (HPDv2), 82.2%/74.0% (HPDv3)

**Latent-CLIP Rewards** [#20 — MEDIUM]
- CLIP-based reward in latent space; 21% cost reduction vs. standard CLIP while matching GenEval/T2I-CompBench performance

### G-3 · Inference-Time Scaling & Verifier-Free Methods

**VFScale (Verifier-Free Test-Time Scaling)** [#20 — HIGH]
- arXiv 2502.01989; ICLR 2026
- Uses diffusion model's intrinsic energy function as scoring signal; no external verifier
- Scales by searching over denoising trajectories

**IPR (Iterative Partial Refinement)** [#20 — HIGH; May 2026]
- arXiv 2605.19317; ICLR 2026
- Re-noise subset of regions, regenerate conditioned on rest; training-free; no external verifier
- MNIST Sudoku: **55.8% → 75.0% valid solutions (+19.2 pp)**

**LoTTS (Localized Test-Time Scaling)** [#20 — MEDIUM]
- arXiv 2511.19917, 2025
- Adaptively resamples defective regions; **2–4× GPU cost reduction** vs. standard Best-of-N

**CoDe (Local Best-of-N)** [#20 — MEDIUM]
- Replaces global sampling with local BoN every B steps during reverse diffusion; reduces BoN overhead

**DSPO (Direct Score Preference Optimization)** [#20 — HIGH; ICLR 2025]
- Distills human-preferred score function into pretrained model via score matching; no external verifier at inference

**RFG (Reward-Free Guidance)** [#20 — MEDIUM]
- arXiv 2509.25604, 2025; +9.2% on math reasoning & code generation; generalizable without task-specific RL

### G-4 · Compositional Benchmark

**GenEval 2** [#20 — HIGH]
- arXiv 2512.16853; ICLR 2025
- Original GenEval 1 exceeded by SD3/Gemini 2.5/Qwen-Image; GenEval 2 addresses benchmark drift
- Uses atom-level VQA judge (Soft-TIFA)
- SOTA: Show-o + PARM + DPO = **77%** (vs. Show-o baseline 53%, SD3 62%)

**Twin Dataset (Glyph Verification)** [#20 — HIGH; Dec 2025]
- arXiv 2512.23592; 561,000 image-pair queries for fine-grained visual verification
- Fine-tuning VLMs on Twin improves performance on unseen domains (art, symbols, etc.)
- **No baseline accuracy numbers for specific <8B models published**

### G-5 · Recommended Stack for Glyph Generation Without Ground Truth [#20]

| Purpose | Tool | Type | Confidence |
|---|---|---|---|
| Selection | PickScore + HPSv3 (ensemble) | Preference ranker | HIGH |
| Fine-tuning | GlyphPrinter (R-GDPO) or SPO | Region-DPO | HIGH |
| Perceptual verification | TIQA | No-ref scorer | HIGH |
| OCR-predictable quality | DIQA | OCR predictor (no engine needed) | HIGH |
| Inference scaling (no verifier) | VFScale (energy-based) or IPR | Training-free | HIGH |

---

## 🔍 GAPS — Topics Not Covered by Any Smith in Chain B

### G-A · FLUX.2-Specific Gaps
1. **FLUX.2 ControlNet and IP-Adapter:** No Smith covers conditioning adapters (depth, pose, style) for FLUX.2
2. **FLUX.2 Video/Temporal Generation:** No coverage of any FLUX.2 video capabilities
3. **FLUX.2 Inpainting / Outpainting:** No Smith addresses these use cases
4. **Multi-GPU / Distributed Training for FLUX.2:** Only single-GPU (24GB) training covered (Smith #15)
5. **FLUX.2 CPU-only inference:** No data on CPU-only or <8GB VRAM scenarios
6. **Nunchaku vs. baseline FLUX.1 performance comparison:** #13 covers FLUX.2 *absence* in Nunchaku but no comparative benchmarks for what Nunchaku achieves with FLUX.1 (latency/throughput improvement numbers)
7. **SVDQuant calibration strategy for FLUX.2:** #14 notes that FLUX.1's outlier patterns may differ in FLUX.2; no investigation of what calibration data would be needed

### G-B · Training & Quantization Gaps
8. **QLoRA on FLUX.2 Klein 4B specifically:** #15 covers 9B; no 4B training benchmarks
9. **SSD/NVMe gradient offloading for diffusion:** MemAscend-style methods noted as existing in literature but no diffusion + 24GB benchmarks
10. **INT4 quantization latency for small VLMs:** #18 notes all latency estimates assume FP16 or FP8; INT4 quantization effect not detailed

### G-C · OCR & Glyph Pipeline Gaps
11. **Symbol/punctuation-only accuracy benchmark:** Explicitly missing across all OCR literature (noted by #17 and #18); no benchmark isolates this
12. **TrOCR hallucination baseline quantification:** No 2026 source quantifies the original TrOCR hallucination problem for comparison
13. **End-to-end pipeline: FLUX.2 distilled generation → OCR verification → quality scoring:** No Smith covers the integration of Themes A+E+G into a single pipeline
14. **Moondream 2 OCRBench number:** Explicitly missing; only claimed metrics are latency and relative improvement vs. prior version

### G-D · Font Embedding Gaps
15. **Runtime performance of FontCLIP vs. DINOv2 at scale:** #19 covers accuracy but no throughput/latency at inference-time for embedding retrieval
16. **Font embedding + glyph generation integration:** No Smith covers using font embeddings as conditioning signals for generation models
17. **Font verification ("same or not?" at character level):** Twin dataset (#20) is the only relevant signal, but no specific model tested on this task with quantified results

### G-E · Cross-Theme Gaps
18. **No Smith covers LoRA variant benchmarks on FLUX.2 specifically:** #16 covers FLUX/SDXL but not FLUX.2 Klein architecture
19. **No Smith covers combining distillation (Theme A) with quantization (Theme B/C):** e.g., QLoRA training of distilled checkpoints, or SVDQuant on pi-Flow LoRA adapters

---

## 📊 CONFIDENCE SUMMARY BY THEME

| Theme | Highest-Confidence Findings | Lowest-Confidence Findings |
|---|---|---|
| A · FLUX Distillation | Klein specs, InferenceBench speed, code repos | Training costs (all undisclosed); proprietary distillation method |
| B · Nunchaku | Version dates, issue tracker evidence | PR #926 merge status (rate-limited) |
| B · deepcompressor | No FLUX.2 config existence; FLUX.1 FID numbers | FLUX.2 calibration requirements |
| C · LoRA Training | NF4 memory (9–10GB measured); optimizer memory savings | FLUX.2 training numbers (blog sources); GaLore on diffusion |
| D · LoRA Variants | LyCORIS ICLR 2024 diffusion benchmarks; DoRA "experimental" statement | Community benchmarks (Tensor.Art); Moondream OCR |
| E · OCR | Qwen3-VL-8B OCRBench 89.6%; SmolVLM scaling; PP-OCRv6 June 2026 | DeepSeek-OCR-2 97% (vendor only, 6 months old); Moondream OCR |
| F · Font Embeddings | DINOv2 99% top-1; "Reading ≠ Seeing" findings | FM-Font (June 2026, undocumented) |
| G · Quality Predictors | TIQA, PickScore, HPSv3, GlyphPrinter specifics | CoDe, RFG, TTGen (secondary survey citations) |

---

*End of Anderson Findings Report — Chain B, Smiths #11–#20*
*All unique signal preserved. Corrections applied at source; disputes flagged with evidence. Gaps enumerated. Ready for Opus synthesis.*

============================================================
## Chain C — Anderson Report
============================================================

File-write permissions aren't available in this environment, so here are the full organized findings inline for Opus:

---

# CHAIN C — ANDERSON ORGANIZED FINDINGS
**For Opus Synthesis | Date: 2026-07-17**
**Source Smiths: #21, #22, #23, #24, #25, #26, #28, #29, #30 | Smith #27: ERRORED**

> **Triage applied:** DEDUP merges cross-Smith overlaps (all sources cited). RECENCY noted where dates differ. AGREE/[CONVERGE] flags multi-Smith consensus. [DISPUTE] flags genuine contradictions. [CORRECTION] marks internal errors fixed. GAPS listed at end.

---

---

# THEME A: FLUX.2 ECOSYSTEM

## A.1 — Model Family & Klein Lineup

**Sources: #21, #30** [DEDUP — both cover Klein; merged here]

**Full-size FLUX.2 (API-only, no open weights):**
- FLUX.2 Max — quality score 3.965 | Pro — 3.900 | Dev — 3.504 | Schnell — 3.350 *(2026 benchmark, MEDIUM — comparative models ranking)* [#21]
- All full-size FLUX.2: native multi-reference conditioning (2–4 simultaneous reference images) [#21 HIGH]

**FLUX.2 Klein open-weight line — released Jan 15, 2026:**

| Variant | Params | License | Commercial Use (open weights) | VRAM Req | Confidence |
|---|---|---|---|---|---|
| Klein-4B distilled | 4B | Apache 2.0 | ✅ YES | ~13 GB | HIGH [#30] |
| Klein-4B base | 4B | Apache 2.0 | ✅ YES | ~13 GB | HIGH [#30] |
| Klein-9B distilled | 9B | FLUX Non-Commercial | ❌ NO | ~29 GB* | HIGH [#30] |
| Klein-9B base | 9B | FLUX Non-Commercial | ❌ NO | ~29 GB* | HIGH [#30] |
| Klein-9B KV | 9B | FLUX Non-Commercial | ❌ NO | ~29 GB* | HIGH [#30] |

> **[CORRECTION C-1 — Smith #30]:** The 9B is listed as requiring "~29 GB VRAM (NVIDIA RTX 4090+)" but the RTX 4090 has only **24 GB** VRAM — 29 GB does not fit. Either the VRAM figure is wrong (quantized variants likely fit on 4090 at reduced precision) OR the GPU recommendation is wrong (RTX 5090 at 32 GB would genuinely fit). Opus should verify directly against BFL model cards before citing.

- Quantized variants (FP8, NVFP4): available for all 4B and 9B versions, same licenses. [#30 HIGH]
- **104 official adapters** for Klein-9B on Hugging Face as of July 2026. [#21 HIGH]
- Commercial licensing for 9B via BFL: Builder Tier (10K img/month), Platform Tier (100K img/month). [#30 HIGH]
- **License rename (Jan 2026):** "FLUX [dev] Non-Commercial License" → "FLUX Non-Commercial License." No material changes. [#30 HIGH]

---

## A.2 — ControlNets & Integrated Tools

**Source: #21**

### FLUX.2-dev-Fun-ControlNet-Union (Alibaba PAI)
- Modes: Canny | Depth | HED/Softedge | Pose/OpenPose | MLSD | Scribble | Grayscale | Inpainting
- Compatible: FLUX.2-dev **only** — confirmed NOT compatible with Klein 9B/4B [#21 HIGH]
- Architecture: Added on 4 double blocks; trained via VideoX-Fun framework
- Optimal scale: **0.65–0.80** (direct model docs); Inpainting mode: 0.25–0.40 [#21 HIGH]
- Weights: `alibaba-pai/FLUX.2-dev-Fun-Controlnet-Union`; ComfyUI: `bryanmcguire/comfyui-flux2fun-controlnet`

### FLUX.1-dev-ControlNet-Union-Pro-2.0 (Shakker Labs) — Released April 2025
- Modes: Canny | Softedge (HED) | Depth | Pose | Grayscale
- Compatible: FLUX.1-dev explicitly. FLUX.2 compatibility: **UNCONFIRMED** [#21 MEDIUM]
- Architecture: Single Union checkpoint; simultaneous multi-mode stacking supported
- Training: 300K steps (MEDIUM), 20M images (MEDIUM), 512×512 BF16, batch 128, LR 2e-5, text dropout 0.20 [#21 HIGH for hyperparams from Shakker docs]
- Recommended strength: start 0.6–0.7, end step 0.6–0.7
- Weights: `Shakker-Labs/FLUX.1-dev-ControlNet-Union-Pro-2.0`

### FLUX.1 Depth & Canny Tools (Black Forest Labs)
- **Key distinction: Integrated INTO base FLUX.1 model, NOT a separate ControlNet** — officially "Tools" [#21 HIGH]
- Compatible: FLUX.1-dev (12B rectified flow). FLUX.2 dedicated tools: **not announced as of July 2026** [#21]
- Quality: output fidelity directly tied to input map quality; edge extraction noise degrades results significantly

### flux.2-klein-controlnet (ReyChiaro — Community)
- Modes: Depth, edge (likely Canny), pose
- Compatible: FLUX.2-Klein-9B exclusively (fills gap left by Alibaba union model's Klein exclusion)
- Repo: `ReyChiaro/flux.2-klein-controlnet` — diffusers-based, plug-and-play; inference + training scripts
- Status: Community-maintained; no published quality metrics [#21 MEDIUM]

---

## A.3 — IP-Adapters

**Source: #21**

### XLabs flux-ip-adapter-v2
> **⚠️ DEPRECATION ALERT (March 2026):** XLabs IP Adapter marked deprecated. Status as of July 2026 uncertain — may be retracted. [#21 MEDIUM]

- Image encoder: CLIP ViT-Large (clip-vit-large-patch14), 768-dim; ~22M params; MLP projection (2 linear layers)
- Training: 512×512 × 150K steps → 1024×1024 × 350K steps [#21 HIGH]
- FLUX.2 compatibility: unspecified in public docs
- Weights: `XLabs-AI/flux-ip-adapter-v2`

### InstantX FLUX.1-dev-IP-Adapter — Released Nov 22, 2024
- Image encoder: CLIP ViT-Large (clip-vit-large-patch14), 768-dim
- Adapter layers: inserted into 38 single blocks + 19 double blocks (FLUX.1-dev architecture-specific)
- FLUX.2 compatibility: not documented
- Supports: style transfer, character consistency, "make it look like this" workflows
- ComfyUI: `Shakker-Labs/ComfyUI-IPAdapter-Flux` [#21 HIGH]

---

## A.4 — Reference & In-Context Conditioning

**Source: #21**

### FLUX.2 Built-in Multi-Reference Conditioning
- Compatible: FLUX.2 full models AND Klein 9B/4B [#21 HIGH]
- Reference latents: stored as `[batch, 128, H, W]` tensors, distinct from text conditioning
- FLUX.2 patchifies generated and reference latents independently; appends reference token sequences to generated image sequence
- Klein-9B conditioning width: **12,288** (from three 4,096-wide Qwen hidden-state slices) [#21 HIGH]
- Supports 2–4 simultaneous reference images with automatic composition blending
- Config parameters: `early_layer_scale`, `mid_layer_scale`, `late_layer_scale`; `reference_image_num_tokens` (variable, not fixed); `preserve_original` (blends modified region back)
- Use cases: character consistency at scale, product mockups, ad variants, combined pose + character + background guidance [#21 HIGH]

### Klein-9B-Specific Reference Conditioning
- KV (Key-Value) consistency for fast image editing
- Smaller conditioning projections vs. full FLUX.2
- Example adapter: `dx8152/Flux2-Klein-9B-Consistency`
- ComfyUI: `capitan01R/ComfyUI-Flux2Klein-Enhancer` [#21 MEDIUM]

---

## A.5 — FLUX Inpainting

**Sources: #21, #23** [DEDUP — both mention FLUX.1-Fill; merged here]

### FLUX.1-Fill-Pro / FLUX.1-Fill-Dev (BFL, Nov 2024 onward)
- Formulates editing as conditional rectified flow in latent space; transformer-based reasoning over visual content, spatial structure, semantics
- FLUX.1-Fill [Pro]: "State-of-the-art inpainting model" as of 2025–2026; outperforms Ideogram 2.0, AlimamaCreative FLUX-ControlNet-Inpainting [#23 HIGH]
- FLUX.1-Fill [Dev] (open-source): Second place; superior to SDXL-Inpainting and SD1.5-Inpainting [#23 MEDIUM]
- "Genuinely blends with originals; context awareness reduces iteration count" [#23 MEDIUM]
- **FLUX.2 inpainting status (as of April 2026):** Standard inpainting with explicit mask input NOT yet supported in FLUX.2 — feature request open; only available via `edit_image` pipeline [#23]
- No model retraining required [#23 HIGH]

---

## A.6 — Ecosystem Compatibility Matrix

| Tool | FLUX.2-dev | Klein-9B | Klein-4B | Deprecated? | Confidence |
|---|---|---|---|---|---|
| FLUX.2-dev-Fun-ControlNet-Union (Alibaba) | ✅ | ❌ | ❌ | No | HIGH [#21] |
| FLUX.1-dev-ControlNet-Union-Pro-2.0 (Shakker) | ❓ | ❌ | ❌ | No | MEDIUM [#21] |
| FLUX.1 Depth/Canny Tools (BFL) | ❓ | ❓ | ❓ | No | HIGH on FLUX.1; unclear on FLUX.2 [#21] |
| XLabs flux-ip-adapter-v2 | ❓ | ❓ | ❓ | **YES (Mar 2026)** | MEDIUM [#21] |
| InstantX FLUX.1-dev-IP-Adapter | ❌ (FLUX.1 only) | ❌ | ❌ | No | HIGH [#21] |
| FLUX.2 Multi-Reference (native) | ✅ | ✅ | ✅ | No | HIGH [#21] |
| ReyChiaro Klein ControlNet | ❌ | ✅ | ❓ | No | MEDIUM [#21] |
| FLUX.1-Fill-Dev | ✅ (FLUX.1) | — | — | No | HIGH [#23] |

---

---

# THEME B: GPU HARDWARE & COMPUTE COSTS

## B.1 — H100 80GB Rental Pricing (July 2026)

**Source: #28** *(All confidence ratings MEDIUM — aggregator/provider sites; on-demand rates)*

| Provider | H100 Type | Price/hr |
|---|---|---|
| Vast.ai | SXM (marketplace) | $1.73 |
| Vast.ai | PCIe (marketplace) | $1.87 |
| RunPod | Community Cloud | $1.99 |
| RunPod | Secure Cloud (PCIe) | $2.89 |
| Crusoe Cloud | On-demand | $3.90 *(May 2026)* |
| Lambda Labs | SXM 8-GPU cluster | $3.99/GPU |
| Lambda Labs | SXM single | $4.29 |
| CoreWeave | HGX 8-GPU node | $6.16/GPU |

- Spot/reserved discounts typically 30–70% below on-demand rates [#28]
- Vast.ai marketplace: listed rates don't reflect actual costs; storage + host-downtime risk adds 10–40% overhead [#28 — flagged LOW for Vast headroom]
- **CoreWeave capacity warning:** CFO stated company "largely sold out" of 2026 capacity with prices rising across all GPU generations *(Q1 2026 investor disclosure)* [#28 HIGH]

---

## B.2 — Cheaper Alternatives to H100

**Source: #28**

### A100 80GB On-Demand (Most Cost-Effective per Hour)
| Provider | Price/hr | Notes |
|---|---|---|
| Spheron | $1.07 | July 2026 |
| Thunder Compute | $1.09 | June 2026; 6.5× cheaper than GCP |
| PrimeIntellect | $1.29 | In-stock |
| Jarvislabs | $1.49 | Per-minute billing |

A100 is ~67–87% cheaper per hour vs. H100. Performance-per-job tradeoff favors H100 for training despite higher hourly rate. [#28]

### RTX 5090 Cloud Rental (Lowest Cost, Limited Availability)
| Provider | Price/hr |
|---|---|
| Salad | $0.195–$0.294 |
| Vast.ai | $0.40 |
| GPU.ai | $1.05 |

~11 providers total offer RTX 5090 as of May 2026; inventory constrained, prices volatile. [#28 MEDIUM]

---

## B.3 — RTX 5090 vs RTX 3090: Hardware Specs

**Source: #29** [All specs HIGH confidence — official NVIDIA/verified sources]

| Spec | RTX 5090 (Blackwell) | RTX 3090 (Ampere) | Ratio |
|---|---|---|---|
| CUDA Cores | 21,760 | 10,496 | 2.07× |
| VRAM | 32 GB GDDR7 | 24 GB GDDR6X | 1.33× |
| Memory Bandwidth | 1,792 GB/s | 936 GB/s | **1.91×** |
| BF16 Tensor (dense) | 209.51 TFLOPS | 71 TFLOPS | **2.95×** |
| BF16 Tensor (sparse) | 419.01 TFLOPS | 142 TFLOPS | 2.95× |
| FP8 hardware support | ✅ YES | ❌ NO | — |
| Tensor Core generation | 5th (Blackwell) | 3rd (Ampere) | — |

**Theoretical BF16 training speedup: 2.95×** [#29 HIGH — arithmetic from verified specs]
**Memory bandwidth advantage: 1.91×** [#29 HIGH] — critical for memory-bound diffusion workloads

---

## B.4 — RTX 5090 vs RTX 3090: Measured Performance

**Source: #29**

### Training
- **General training speedup: 2.0–2.5×** [MEDIUM — multiple sources converge] **[CONVERGE]**
- Concurrent-load throughput: up to 2.5× aggregate [MEDIUM, Hacker News Jul 2026]
- LoRA fine-tuning: enables larger batch sizes and 30B-class model tier via QLoRA (unavailable on RTX 3090). Specific LoRA speedup derived from 4090 proxy, not direct measurement. [MEDIUM]
- Full fine-tuning: RTX 5090 uniquely enables full fine-tuning of 3.8B models on single card. [MEDIUM]
- BF16 LLM throughput: 28K tok/sec baseline; 52K tok/sec with NVFP4 mixed precision. [MEDIUM — LLM-specific, not diffusion]

### Inference
- **FLUX.1 Dev: 3.08× faster vs RTX 3090 Ti at 16-bit precision** [#29 HIGH — direct Furkan Gözükara benchmark]

> **[CORRECTION C-2 — Smith #29 internal inconsistency]:** Smith #29 simultaneously states RTX 5090 FLUX inference = "0.64 sec for 20 steps," "3 iter/sec," and "~9.55 sec/image." These are mutually incompatible: at 3 iter/sec × 20 steps = 6.67 sec (≠ 0.64 sec, ≠ 9.55 sec); at 0.64 sec for 20 steps = 31.25 iter/sec (≠ 3 iter/sec). Opus should treat only the top-line **"3.08× faster"** as reliable and verify the sub-figures directly from the original benchmark source.

- SD 3.5-Large inference: ~7.3× speedup [MEDIUM — flagged outlier; conditions not specified; typical range 2–3× is more representative]
- General image generation average: 2.1–2.3× [MEDIUM]
- SDXL 1024×1024 FP16 20 steps: 38 img/min (5090) vs 28 img/min (4090) = 36% over 4090; implied 5090 vs 3090 ≈ 2.5–3× [LOW — extrapolated, not directly measured]

### FLUX/DiT-Specific Training — Data Gap
- No practitioner-measured FLUX training throughput on RTX 5090 found. [#29 — explicitly noted]
- MLPerf Training v5.1: FLUX.1 trains in ~95 min on 64 × NVIDIA B200 GPUs (BF16) [#29 HIGH — official MLPerf, not applicable to single 5090]
- Single-GPU 32 GB training feasibility for FLUX confirmed; throughput data sparse. [#29 MEDIUM on feasibility / LOW on throughput]

### VRAM & FLUX Fit
- FLUX.1 Dev weights: ~24 GB at BF16 → fits with headroom on RTX 5090 (32 GB); barely fits on RTX 3090 (24 GB) [#29 HIGH]
- FLUX.1 Dev full FP16 inference requires ~33 GB → only feasible at native FP16 on 32 GB+ cards [#29 HIGH]
- FLUX.1 Dev FP8 quantized: ~17 GB → fits comfortably on both [#29 HIGH]

---

## B.5 — RTX 5090 Retail Pricing (July 2026)

**Source: #29** [HIGH confidence — multiple current price trackers]

- MSRP (launch): $1,999
- Street price: $2,900–$3,400 average (~50% markup)
- Amazon mid-July 2026: $4,329
- Premium/liquid-cooled variants: >$5,000
- RTX 3090 used market: $300–$600 (was $1,499 MSRP in 2020)
- **Root cause of premium:** Global AI buildout has depleted GDDR7 memory supply; memory = ~80% of GPU bill of materials. New fab capacity not at volume until 2027. [#29 HIGH]

---

---

# THEME C: DIFFUSION TRAINING TECHNIQUES

## C.1 — Conditioning Dropout & CFG

**Source: #22**

### Foundational Baseline (Ho & Salimans 2022, arxiv:2207.12598)
- Tested p_uncond: 0.1, 0.2, 0.5 [HIGH]
- Finding: p_uncond = 0.5 performs *worse* than {0.1, 0.2}, which perform "about equally well" [HIGH]
- **Established baseline: 10–20% condition dropout at training time** [HIGH — widely cited; no superseding recommendation found in 2024–2026 literature]
- Mechanism: dropout during training teaches model conditional and unconditional branches; at inference, CFG = score extrapolation with guidance scale w > 1; **dropout is NOT required at inference** [HIGH]
- Date: July 2022 — >4 years old; foundational and uncontested

### 2023–2025 Implementations

| Method | Year | Dropout Rate | Notes | Confidence |
|---|---|---|---|---|
| LayoutDiffusion | 2024 | 0.2 | Classifier-free per hyperparameter tables | MEDIUM |
| CoLay (Google Research) | May 2024 | Variable per condition type | Individual probabilities per condition; exact rates not in available excerpts | MEDIUM |
| STAY Diffusion | March 2025 | 0 (no explicit dropout) | Adapts CFG without training unconditional model; mechanism unverified | MEDIUM |
| General practice | 2024 | 0.1–0.2 | Unchanged from 2022 baseline | HIGH |

**[CONVERGE]:** 0.1–0.2 dropout rate consistent across 2022 foundational work and 2024 practice. No evidence of drift.

### Training-Free Alternatives (Inference-Time CFG Without Training Dropout)
- **ICG (Independent Condition Guidance, Jul 2024 / ICLR 2025 accepted, arxiv:2407.02687):** Matches CFG performance without training-time dropout [#22 HIGH]
- **TSG (Time-Step Guidance, same paper):** Enables guidance on any diffusion model, even unconditional ones [#22 HIGH]
- **CDG (Condition-Degradation Guidance, March 2025, arxiv:2603.10780):** Replaces null prompt with degraded condition (selective token degradation, not dropout); improves compositional accuracy over standard CFG; validated on SDXL, FLUX, Qwen-Image [#22 HIGH/MEDIUM]

### Dropout Rates: Known Gaps
- ControlNet (2023): exact dropout probability not specified; uses zero-convolutions instead
- FLUX (2024): no published dropout rates
- CoLay, HDGlyph: per-condition rates not quantified in public excerpts

---

---

# THEME D: IMAGE EDITING & INPAINTING

## D.1 — DiT Inpainting Methods vs. SDEdit Masking (2025–2026)

**Source: #23**
*(FLUX.1-Fill cross-listed in Theme A.5)*

### Comparative Summary

| Method | Beats SDEdit? | Evidence Quality | Retraining? | Key Advantage |
|---|---|---|---|---|
| FLUX.1-Fill [Pro] | **YES** | HIGH | NO | Official SOTA; outperforms Ideogram 2.0 |
| ConsistEdit (SIGGRAPH Asia 2025) | Likely | MEDIUM | NO | Multi-round multi-region; structural consistency |
| SpotEdit (Dec 2025) | Likely | MEDIUM | NO | Computational efficiency; stable-region skip |
| LanPaint (TMLR Oct 2025) | Likely | MEDIUM-LOW | NO | Generality across DDPM + rectified-flow models |
| FreeInpaint (AAAI 2026) | Likely | MEDIUM-LOW | NO | Simultaneous prompt faithfulness + coherence |
| HarmonPaint (Jul 2025) | Likely | LOW | NO | Self-attention masking; structural fidelity |
| Differential Diffusion (TD-Paint/VideoPDE) | Unclear | LOW | NO | Smooth temporal transitions; theory-driven |

> **CRITICAL NOTE [#23]:** No peer-reviewed 2025–2026 paper benchmarks all methods against SDEdit with unified LPIPS/PSNR/SSIM. All "beats SDEdit" claims are MEDIUM or lower except FLUX.1-Fill [Pro]'s official positioning. All methods require NO model retraining.

### Method Details

**Attention-Steered (Training-Free on Frozen DiT/UNet):**
- **SpotEdit** (arXiv:2512.22323, Dec 2025): Perceptual similarity identifies stable regions → skips computation via feature reuse → adaptive attention fusion for edited regions only. No numerical quality metrics published; efficiency-focused. [#23 MEDIUM]
- **ConsistEdit** (SIGGRAPH Asia 2025, arXiv:2510.17803): Differentiated Q/K/V token manipulation on vision-only layers with mask-guided pre-attention fusion. Supports multi-round, multi-region editing. "SOTA across diverse image and video editing tasks" (venue claim). Specific metrics not disclosed. [#23 MEDIUM]

**Training-Free Localized Editing:**
- **LanPaint** (arXiv:2502.03491, Feb 2025; TMLR Oct 2025): Langevin dynamics partial conditional sampling; asymptotically exact Monte Carlo; no backprop. Supports DDPM (SDXL) and rectified-flow (SD3.5, FLUX.1, HiDream-L1). [#23 HIGH on soundness; LOW on comparative metrics]
- **FreeInpaint** (arXiv:2512.21104, Dec 2024; AAAI 2026): Prior-guided noise optimization + composite guidance on diffusion latents at each step. [#23 HIGH on categorization; LOW on comparative metrics]
- **HarmonPaint** (arXiv:2507.16732, Jul 2025): Self-attention masking strategies. [#23 MEDIUM]

**Reference Numerical Benchmark:**
- MTADiffusion (2025): PSNR >31.87 dB, LPIPS <19, VQA >68.9 on BrushBench (mask-conditioned). [#23 MEDIUM — not strictly training-free localized editing; provided for scale context]

---

---

# THEME E: TYPOGRAPHY & TEXT GENERATION

## E.1 — Confusable Character Handling in Generative Models

**Source: #24**

### Primary Finding
**NO systematic research explicitly addressing confusable character pairs (slash/backslash, O/0, curly vs. straight quotes) as a unified problem in generative models 2024–2026.** [#24 HIGH confidence — verified gap]

**Why the gap persists:** Generative models process glyph embeddings, not visual pixels; confusion manifests only in final pixel rendering — after the model's decision. Addressing it requires: (1) dataset curation tagging confusable pairs, (2) loss function penalizing pixel-identical outputs for distinct codepoints, (3) evaluation metrics beyond OCR (SSIM or perceptual distance for confusable pairs). None appear in 2024–2026 literature.

### Visual Similarity Measurement (Non-Generative)
- **confusable-vision project (paultendo, 2026):** SSIM analysis of 1,418 Unicode TR39 pairs across 230 macOS fonts. Findings: 96.5% of confusables.txt not high-risk; 82 pairs pixel-identical in ≥1 font; 249,976 unique confusable pairs across 245 fonts (RaySpace raycasting). Cyrillic "а" (U+0430) pixel-identical to Latin "a" in 40+ fonts. [#24 HIGH — primary source, github.com/paultendo/confusable-vision]
- Tool: `namespace-guard` (MIT, TypeScript) — `canonicalise()`, `scan()`, `confusableDistance()`
- **Unicode TR39:** ~6,565 source codepoints mapping to confusable targets. Security-focused, not designed for generative evaluation. [#24 HIGH]

### What Generative Text Models DO Achieve (2024–2025)
*(Not confusable disambiguation — context for Opus)*

| Model | Year | Key Result | Metric | Conf. |
|---|---|---|---|---|
| TextPixs | Jul 2025 | CER = 0.08 (vs 0.21 SOTA) | Character error rate; 90% spelling accuracy | HIGH [#24] |
| AnyText | ICLR 2024 Spotlight | — | OCR word F1 + FID | HIGH [#24] |
| HDGlyph | May 2025 / SIGGRAPH Asia | +5.08% English / +11.7% Chinese | Long-tail rendering accuracy | HIGH [#24] |
| EasyText | AAAI 2026 | Character-level accuracy | Multilingual positional encoding | HIGH [#24] |

None use confusable-pair evaluation metrics.

### Security Research (Homoglyph Context — Distinct from Generative)
- SilverSpeak (Jun 2024, arxiv:2406.11239): Homoglyph substitution disrupts AI detector tokenization; reduces detection to near-random. [#24 HIGH]
- Microsoft Digital Defense Report 2025: Homoglyph domain impersonation = fastest-growing AI-driven threat. [#24 HIGH]
- Core insight: LLMs process Unicode codepoints, not visual glyphs — attacks exploit the gap between codepoint and pixel rendering. [#24 HIGH]

---

## E.2 — Discontinuous Style Preservation in Reference-Based Generation

**Source: #25**
*(VecGlypher, NIV, VecFusion, FontCrafter cross-referenced to E.3 — single canonical entry per item below with both themes noted)*

### Why Smooth Priors Destroy Discontinuous Styles
- Continuous DNNs cannot approximate discontinuous functions → forced interpolation between discrete states [#25 HIGH, arXiv:2605.00435 (2025)]
- Discrete diffusion absorbing-state (masking) creates irreversible commitments → errors propagate [#25 HIGH, arXiv:2607.13431 (2025)]
- Practical failures: halftone dot (binary on/off) → smooth model produces gray blur; stencil gap (letterform breaks) → smooth prior fills the gap; pixel art palette → off-palette colors generated
- Smooth Diffusion (CVPR 2024, SHI-Labs): explicitly improves latent smoothness → **worsens** topology-breaking pattern reproduction. Trade-off documented. [#25]
- Mutual information collapse in β-VAEs is structural, not a training artifact [arXiv:2602.09277 (2025)]

### Techniques That Work

**Discrete Diffusion:**
- **D²Styler (ICPR 2024, arXiv:2408.03558):** VQ-VAE (discrete codebook) + discrete diffusion. Outperforms 12+ continuous-diffusion style transfer methods. Avoids smooth blending; tokens match codebook entries or don't. GitHub: `Onkarsus13/D2Styler` [#25 HIGH]

**Flow Matching for Discrete Spaces:**
- **Discrete Flow Matching (NeurIPS 2024, arXiv:2407.15595):** CTMCs on discrete state spaces; no masking irreversibility; direct discrete interpolation. Outperforms diffusion on discrete sequential data. [#25 HIGH]
- **Discrete MeanFlow (2025, arXiv:2605.12805):** Conditional transition kernels. [#25 HIGH]

**Color Quantization:**
- **SD-πXL (SIGGRAPH Asia 2024, arXiv:2410.06236):** Score distillation with explicit color palette constraint. Forces quantization in latent space. Targets pixel art (discrete colors). [#25 HIGH]

> **[CORRECTION C-3 — Smith #25]:** ACM DOI `10.1145/3680528.3687570` is listed in Smith #25 for SD-πXL AND appears in Smith #26 for **SVGFusion** (arXiv:2412.10437). The same DOI cannot belong to two different papers. Per Smith #26, this DOI most likely belongs to SVGFusion. SD-πXL's venue attribution (SIGGRAPH Asia 2024) needs independent verification. Opus should not cite this DOI for SD-πXL without confirmation.

**Edge-Preserving Diffusion:**
- **Edge-Preserving Noise (Max Planck Institute):** Non-isotropic noise schedule; higher variance at edges. Prevents edge smoothing in early denoising. [#25 HIGH — institution-published]

**Constrained Sampling:**
- Primal-Dual Guided Decoding (2025, arXiv:2605.09749): Hard positional constraints via closed-form logit bias (Lagrangian). No auxiliary models. [#25 HIGH]
- Physics-Constrained Flow Matching (2025, arXiv:2506.04171): Continuously applies corrections to intermediate states. [#25 HIGH]

### Technique Ranking by Topology Preservation
| Method | Year | Support | Best For |
|---|---|---|---|
| VecGlypher (LLM SVG) | 2026 | Excellent | Stencil fonts, serif glyphs *(full entry in E.3)* |
| D²Styler (Discrete Diffusion) | 2024 | Very Good | Dot-matrix, pixel art, arbitrary styles |
| Discrete Flow Matching | 2024–25 | Very Good | Discrete sequential patterns |
| FontCrafter (element-driven) | 2025–26 | Very Good | Artistic fonts *(full entry in E.3)* |
| SD-πXL (Quantized Diffusion) | 2024 | Good | Pixel art, limited palettes |
| VecFusion (2-stage) | 2024 | Good | Vector fonts *(full entry in E.3)* |
| Palette-based transfer | 2025 | Good | Halftone via color constraint |
| ControlNet + Attention | 2025 | Moderate | Content + style fusion (cannot *generate* discontinuities) |
| **Smooth Diffusion (CVPR 2024)** | 2024 | **Poor** | Continuous content — **worsens the problem** |

### Open Questions (Discontinuous Style Gaps)
1. No unified halftone-specific generation pipeline for varying dot size/angle as style reference
2. Inverse halftoning (reconstruction: binary → continuous) ≠ halftone style generation from reference — conflated in some literature
3. No explicit "stencil letterform style transfer" method preserving bridged/broken topology
4. No empirical study isolating how halftone dot placement errors in early diffusion steps corrupt final output vs. continuous-space blur

---

## E.3 — Open Font Datasets (2026)

**Sources: #26, #25** [DEDUP — VecGlypher, NIV, VecFusion, FontCrafter appear in both; canonical entries here]

### Major Open Font Collections (July 2026)

| Collection | Scale | License | Confidence |
|---|---|---|---|
| Google Fonts | 1,942 families; 546 variable fonts | Open source (mixed) | HIGH [#26] |
| Noto Fonts | 180+ families (~2,300 fonts); 1,000+ languages, 162 scripts, ~77K characters (50% of Unicode 15.0) | OFL/Google | HIGH [#26] |
| Open Font Library | 6,000+ fonts, 250+ contributors | Multiple | HIGH [#26] |
| Fontesk | 2,300+ OFL fonts | SIL OFL | MEDIUM [#26] |
| OpenFont | 1,933 fonts | OFL/GPL mix | MEDIUM [#26] |

Google Fonts breakdown (2026): Sans-serif 705 | Serif 343 | Display 464 | Handwriting 348 | Monospace 51 [#26 HIGH]

**SIL Open Font License (OFL):** De facto standard. Allows embedding, redistribution, modification; requires fonts remain under OFL. [#26 HIGH]

### ML Font Datasets: Raster/Glyph Images

| Dataset | Scale | Format | ML Task | Year | Conf. |
|---|---|---|---|---|---|
| TMNIST | 1,812 glyphs × 1,355 Google Fonts = 565,292 images | 28×28 px grayscale PNG | Font classification | Feb 2022 | HIGH [#26] |
| SynthGlyph | 4,194 TrueType fonts × 6,857 chars = ~28.8M instances | PNG + texture augmentation | Text editing/generation | Dec 2024 | HIGH [#26] |
| AGIS-Net (Chinese) | 2,495 fonts; 1.8M+ images | High-res PNG | Artistic style transfer (Chinese) | 2019 *(7 yrs old)* | HIGH [#26] |
| FontAdapter | 1,500 fonts → 15K glyph + 15K scene-text composites | 512×512 PNG | Font adaptation | Jun 2025 | HIGH [#26] |

TMNIST license: **CC0 1.0** (public domain) [#26 HIGH]

### ML Font Datasets: Vector/SVG

| Dataset | Scale | Format | ML Task | Year | Conf. |
|---|---|---|---|---|---|
| VecGlypher training set | 39K Envato fonts + 2.5K expert-tagged Google Fonts | SVG path tokens | Vector glyph generation | Feb 2025 / CVPR 2026 | HIGH [#26, #25] |
| NIV Variable Font Dataset | 1M+ variation tuples from variable Google Fonts | XML (per-glyph outline + variation deltas) | Multi-axis variable font generation | Jun 2026 | HIGH [#26, #25] |

VecGlypher licensing caveat: 39K Envato fonts used for pretraining; exact licensing of proprietary-source dataset in open release is unclear. [#26 MEDIUM]

### ML Font Datasets: Multilingual & Multimodal

| Dataset | Scale | Language | ML Task | Year | Conf. |
|---|---|---|---|---|---|
| AnyArtisticGlyph Chinese100 | 9,900 styles × 100 chars (6,900 train / 3,000 test) | Chinese | Controllable artistic glyph | Apr 2025 | HIGH [#26] |
| AnyArtisticGlyph Korean480 | 10,000 styles × 480 chars (7,000 train / 3,000 test) | Korean | Controllable artistic glyph | Apr 2025 | HIGH [#26] |
| Diversity Font Dataset (DFD) | 135,000 font-text pairs with quality annotations | Multilingual | Font understanding, VLM training | Apr 2025 | HIGH [#26] |

### 2025–2026 Font Generation Model Papers

| Model | Key Innovation | Venue | Topology Role | Sources |
|---|---|---|---|---|
| VecGlypher | LLM → SVG path tokens one-pass; multimodal input | CVPR 2026 accepted | Excellent — native SVG topology constraint | #26, #25 |
| NIV (Neural Axis Variations) | Multi-axis variable font generation | arXiv:2606.05261, Jun 2026 | Variable letterform topology | #26, #25 |
| VecFusion | Cascaded raster→vector diffusion | CVPR 2024 | Good — separates geometry from topology | #26, #25 |
| FontCrafter | Element-driven (serif, terminal, stroke) few-shot synthesis | arXiv:2603.22054 2025–26 | Very Good — element decomposition | #26, #25 |
| Font-Agent | VLM-based font understanding (DFD dataset) | CVPR 2025 | — | #26 |
| FontAdapter | Two-stage synthetic glyph + scene-text dataset | ECCV 2025 track | — | #26 |
| HFH-Font | Few-shot Chinese: higher quality/speed/resolution | arXiv:2410.06488, 2024 | — | #26 |
| Beyond Patches | Global-aware autoregressive few-shot font gen | arXiv:2601.01593, 2026 | — | #26 |
| SVGFusion | VAE-Diffusion Transformer for scalable text-to-SVG | arXiv:2412.10437, ACM 2024 | — | #25, #26 |

**Dataset structural gap:** No standalone "open font corpus" paper for 2025–2026; major ML datasets remain embedded in task-specific papers. Chinese/Asian scripts dominate recent research; Latin datasets inherit primarily from Google Fonts. [#26 HIGH]

---

---

# ERRORED SMITH

## Smith #27 — test-time-scaling-imagen
**STATUS: ERRORED — Timed out after 720s (retry suggested)**
**Content: UNKNOWN**

Inferred topic: test-time compute scaling for image generation (multi-sampling, inference-time search, verifier-guided generation), likely applied to Imagen or similar diffusion models. This is a distinct research area from the training-time techniques covered in Smith #22 and not covered elsewhere in Chain C. **Retry required.**

---

---

# CORRECTIONS REGISTER

| ID | Smith | Error Identified | Correction |
|---|---|---|---|
| C-1 | #30 | Klein-9B "~29 GB VRAM (NVIDIA RTX 4090+)" — RTX 4090 has 24 GB, cannot fit 29 GB | Contradiction. Quantized (FP8/NVFP4) variants may fit on 4090; base-precision 9B likely requires RTX 5090 (32 GB) or A100. Verify against BFL model card directly before citing. |
| C-2 | #29 | FLUX.1 Dev inference: "0.64 sec / 20 steps," "3 iter/sec," "~9.55 sec/image" are mutually incompatible (cannot all be true simultaneously) | Trust only "3.08× faster vs RTX 3090 Ti." Sub-figures mix configurations. Verify from original Furkan Gözükara benchmark source. |
| C-3 | #25 | ACM DOI 10.1145/3680528.3687570 attributed to SD-πXL in #25 but appears to belong to SVGFusion per Smith #26 | Do not cite this DOI for SD-πXL. SD-πXL is arXiv:2410.06236; SVGFusion is arXiv:2412.10437 with the ACM DL citation. Verify SD-πXL SIGGRAPH Asia 2024 DOI independently. |

---

---

# DISPUTES REGISTER

**No genuine cross-Smith factual disputes identified.**

**Potential surface tensions (not true disputes — noted for Opus judgment):**
1. Smith #22 (training-free CFG alternatives exist) is fully consistent with Smith #23 (all DiT inpainting methods are inference-only) — both support inference-time flexibility without retraining.
2. Smith #21 says 104 Klein-9B adapters exist on HF; Smith #30 says only the 4B has Apache 2.0 licensing for commercial use. Not a conflict — adapter count and license type are independent facts.

---

---

# GAPS REGISTER

| ID | Topic | Missing Coverage | Action |
|---|---|---|---|
| G-1 | **Smith #27 ERRORED** | Test-time scaling for image generation (Imagen or similar) | **Retry Smith #27** |
| G-2 | FLUX.2 Pro/Max internals | API-only; architecture undocumented publicly | BFL API docs |
| G-3 | FLUX.1 → FLUX.2 ControlNet compatibility | Most community ControlNets built for FLUX.1-dev; FLUX.2 compatibility broadly unconfirmed | Direct testing or BFL compatibility statement |
| G-4 | RTX 5090 FLUX/DiT training benchmarks | All available 5090 data is inference-only; no measured training throughput for FLUX or DiT | Practitioner benchmark needed |
| G-5 | XLabs IP-Adapter post-deprecation alternative | Deprecated March 2026; no confirmed replacement for FLUX.2 image-prompt conditioning | Search current HF/GitHub |
| G-6 | Unified DiT inpainting benchmark | No paper provides LPIPS/PSNR/SSIM comparison across SpotEdit, ConsistEdit, LanPaint, FreeInpaint, HarmonPaint, FLUX.1-Fill vs SDEdit baseline | Likely doesn't exist yet |
| G-7 | Confusable character generative evaluation | No metric, no dataset, no model for confusable-pair disambiguation in generation | Confirmed open research gap |
| G-8 | Halftone-specific generation pipeline | No method handles varying dot size/angle as style reference | Confirmed open research gap |
| G-9 | Klein-9B ControlNet quality metrics | ReyChiaro community ControlNet has no published quality benchmarks | Community testing |
| G-10 | Conditioning dropout rates for FLUX specifically | No published rates; general 10–20% baseline applies by default | BFL internal (unlikely public) |
| G-11 | FLUX.2 inpainting with explicit mask input | Feature request open as of April 2026; resolution unknown | Monitor BFL changelog |

---

---

# CONFIDENCE DISTRIBUTION SUMMARY

| Theme | HIGH | MEDIUM | LOW |
|---|---|---|---|
| A. FLUX.2 Ecosystem (#21, #30) | 20 | 12 | 3 |
| B. GPU Hardware/Costs (#28, #29) | 14 | 14 | 2 |
| C. Diffusion Training (#22) | 8 | 5 | 2 |
| D. Image Editing/Inpainting (#23) | 5 | 10 | 5 |
| E. Typography/Text (#24, #25, #26) | 28 | 8 | 4 |

**Source date range:** July 2022 (CFG foundational) through July 17, 2026 (current pricing, HF adapter counts).
**Most findings:** 2024–2026. Exceptions noted inline (AGIS-Net 2019, TMNIST 2022, SIL OFL 2007 — standard remains current).
**Strongest signal Smiths:** #21, #22, #25, #26, #29, #30.
**Notable LOW-confidence sections:** #23 (comparative inpainting metrics), #28 (all MEDIUM by design — marketplace rates), #29 (extrapolated training figures).

---

*Anderson organized. 9 of 10 Smiths processed. Smith #27 errored — retry required. Opus: all unique signal preserved above; editorial compression is yours.*

---
**Oracle SDK Execution Metrics**
- Architecture: 30 Smiths -> 3 Andersons -> Opus (you)
- Total time: 2470s
- Total tokens: 466,143 (in: 195,071 | out: 271,072)
- Quota: 0.80% weekly (6.0% session)
- Smiths: 30 (1 errors)
- Andersons: 3 (0 errors)
- Phase timing: scout: 1639s | compress: 831s
- Phase costs: decompose: 0.00% | scout: 0.27% | compress: 0.53%

