============================================================
## Chain A — Anderson Report
============================================================

# ANDERSON SYNTHESIS PACKAGE — Chain A (10 Smiths)
**Prepared:** 2026-07-27 | **Destination:** Opus final synthesis
**Triage rule key:** [AGREE] = multi-Smith convergence | [DEDUP] = merged | [DISPUTE] = flagged | [CORRECT] = fixed | [GAP] = uncovered

---

## THEME A: NUNCHAKU & SVDQUANT INFRASTRUCTURE

### A1. Nunchaku Repository — FLUX.2 Implementation State
**Source:** Smith #1 (HIGH confidence, direct GitHub API)

**PR #926 Status:**
- State: OPEN, NOT MERGED
- Created: 2026-03-31T14:58:57Z
- Last updated: 2026-06-24T23:49:27Z
- `merged_at: null`, `state: "open"` — HIGH confidence
- Repository owner: `nunchaku-ai` org (NOT `mit-han-lab` — see CORRECTIONS)

**Main Branch FLUX.2 Status — Already Present:**
- Class: `NunchakuFluxTransformer2DModelV2`
- File: `nunchaku/models/transformers/transformer_flux_v2.py`
- Last commit: 2025-08-15, author lmxyy (Muyang Li), message: "feat: pythonized model and QwenImage Support (#593)"
- Exported in top-level `nunchaku/__init__.py`
- Dev version: `1.3.0dev` (from `nunchaku/__version__.py`)
- Latest stable release: v1.2.1 (2026-01-25)

**PR #926 vs. Main Branch Naming Discrepancy — UNRESOLVED:**
- PR #926 proposes: `NunchakuFlux2Transformer2DModel` (naming: "Flux2")
- Main branch has: `NunchakuFluxTransformer2DModelV2` (naming: "FluxV2")
- These are **different naming conventions, possibly different implementations**
- PR references specific "FLUX.2-klein-9B-Nunchaku" model variant
- Interpretation candidates: (1) duplicate/competing implementations, (2) PR superseded by earlier merge, (3) intentional API refactoring
- **Smith #1 flags this as KEY CONTRADICTION — unresolved**

**Runtime LoRA Loading API:**
- `transformer_flux_v2.py` does NOT document runtime LoRA loading methods — HIGH confidence (code inspection)
- File DOES contain state dict key conversions: `.lora_down` → `.proj_down`, `.lora_up` → `.proj_up` — HIGH confidence
- tonera/FLUX.2-klein-9B-Nunchaku HuggingFace model card documents:
  ```python
  transformer.update_lora_params(lora_path)
  transformer.set_lora_strength(0.8)
  ```
  — MEDIUM confidence (third-party card, not official Nunchaku repo)
- `skip_refiners = True` flag documented for Z-Image transformer (keeps refiner blocks FP16, main layers 4-bit) — HIGH confidence (Smith #5 corroborates via Nunchaku docs)

**Release Changelog:**
- No releases mention "FLUX.2" or "Flux2Klein" — HIGH confidence
- Latest changelog entries focus on FLUX.1 variants + general optimizations
- FLUX.2 support not in official README as of 2026-07-27 — HIGH confidence

---

### A2. SVDQuant / DeepCompressor — FLUX.2 Recipe Status
**Source:** Smith #2 (HIGH confidence, direct GitHub search)

**Finding: NO FLUX.2 or FLUX.2-klein recipe exists in `nunchaku-ai/deepcompressor`**
- Search for "FLUX.2" returns 0 results — HIGH confidence
- Repository last git push: 2025-08-14T00:43:00Z (repo page shows 2026-07-27T04:01:25Z but no commits after August 2025)

**Quantization Configs That Exist (in `/examples/diffusion/configs/model/`):**
1. `flux.1-dev.yaml` — W4A4, low-rank SVDQuant correction, 50-step
2. `flux.1-schnell.yaml` — W4A4, 4-step
3. `sana-1.6b.yaml` — SANA-1.6b
4. `pixart-sigma.yaml` — PixArt-Sigma

**README-validated models:** FLUX.1-dev, FLUX.1-schnell, SANA-1.6b, PixArt-Sigma. No FLUX.2 or FLUX.2-klein anywhere in docs or configs.

**Implication for project (cross-ref project memory):** Memory states "offline merge-V3+SVDQuant" is needed for sub-minute with V3 — Smith #2 confirms no out-of-box deepcompressor recipe exists; must be custom-built.

---

### A3. SVDQuant Architecture (Context for A1/A2)
**Source:** Smith #5 (HIGH confidence, cited papers)

- SVDQuant uses 4-bit main branch + 16-bit low-rank branch for outlier-sensitive operations
- Low-rank FP16 branch absorbs activation outliers moved from weights — native design handles some embedding sensitivity
- Dual-precision architecture (W4A4 + low-rank correction) is production architecture in Nunchaku runtime
- Refiner blocks stay in BF16 in production SVDQuant — HIGH confidence (MIT-HanLab Nunchaku docs)

---

## THEME B: FLUX.2 KLEIN LoRA TRAINING — TOOLS & CONFIGURATION

### B1. Official Documentation & Licensing
**Source:** Smith #3, #4, #8, #9 — [AGREE on all licensing facts]

**[DEDUP — cited by #3, #8, #9, and project memory]:**
- FLUX.2-klein-4B: **Apache 2.0** — commercially usable — HIGH confidence
  - Source: docs.bfl.ml/flux_2/flux2_klein_training; github.com/black-forest-labs/flux2
- FLUX.2-klein-base-9B: **Non-Commercial License** — HIGH confidence
  - This applies to the BASE 9B; the 9B distilled may differ (see GAPS)
- Release date of Klein models: November 25, 2025 — HIGH confidence (Smith #3)

**Official training guides (Smith #3):**
- BFL: https://docs.bfl.ml/flux_2/flux2_klein_training
- HF Blog: https://huggingface.co/blog/black-forest-labs/flux-2-klein-lora
- AWS Deadline Cloud: https://docs.aws.amazon.com/deadline-cloud/latest/developerguide/flux2-klein-lora.html
- Diffusers script: `train_dreambooth_lora_flux2_klein.py`

---

### B2. Training Toolchain Support
**Source:** Smith #3 (HIGH confidence throughout)

#### ai-toolkit (Ostris)
- Full FLUX Klein support documented
- GitHub: https://github.com/ostris/ai-toolkit
- Baseline config:
  - images: 20–40
  - resolution: 1024
  - batch_size: 1
  - lora_rank: 8
  - steps: 2000–3000
  - sample_every: 250 / save_every: 500
  - learning_rate: 2e-4 (or conservative 1e-4 for product/character)
  - LoRA strength: 0.6–1.0 typical, ~0.73 sweet spot (MEDIUM); up to 1.5+ for Klein base (MEDIUM)

#### Kohya SS (sd-scripts)
- Full FLUX Klein support
- **Minimum version: v0.9.0+ (January 2025)** — HIGH confidence (for fused backward pass)
- PyTorch 2.1+ required
- VRAM with fused backward (v0.9.0+): 4–8 GB — HIGH confidence
- Block swapping: each block swapped reduces VRAM ~0.3 GB, increases RAM ~0.4 GB — MEDIUM
- Standard (no optimization): 24 GB minimum — HIGH confidence
- Guide: https://github.com/kohya-ss/musubi-tuner/issues/405

#### SimpleTuner
- Full FLUX Klein support
- Docs: https://github.com/bghira/SimpleTuner/blob/main/documentation/quickstart/FLUX2.md
- **Critical Klein specifics:**
  - No guidance embeddings on Klein models; guidance training options ignored — HIGH
  - Text encoder: Qwen3 bundled in model repo — HIGH
  - Leave `pretrained_text_encoder_model_name_or_path` unset unless replacing Qwen3 — HIGH
  - Set `model_flavour` to select Klein variant — HIGH
  - LyCORIS config examples for klein-9b not fully documented as of Jan 17, 2026 (Issue #2435) — HIGH
- Embedding dimensions:
  - klein-9b: 12,288 (3×4,096) — HIGH
  - klein-4b: 7,680 (3×2,560) — HIGH
- Batch size by GPU: 12GB→1, 16GB→2, 24GB+→4 — HIGH
- Hardware recommendation: klein-4b on 16GB (RTX 4080/A4000); klein-9b on 24GB (3090/4090/A5000)
- Prodigy optimizer recommended for automatic LR management — MEDIUM
- Weight decay flagged as "most revealing parameter" — HIGH (apatero.com)

#### Diffusers (HuggingFace)
- Full FLUX Klein support
- Script: `train_dreambooth_lora_flux2_klein.py`
- Multi-image LoRA training: Feature request (Issue #13008), NOT yet implemented — HIGH
- Current pipelines designed for single-image conditioning — HIGH
- AWS Deadline Cloud provides full training + inference scripts — HIGH

---

### B3. Winning Hyperparameter Configuration (Research-Backed)
**Source:** Smith #3 + Smith #8 — [AGREE, both cite Herbst 50+ run research]

**[DEDUP — Smiths #3 and #8 both reference Calvin Herbst's research (Feb–Mar 2026, 50+ runs)]:**

| Parameter | Value | Confidence | Source |
|---|---|---|---|
| LoRA rank (winning) | 128/64/64/32 (linear 128/64, conv 64/32) | HIGH | Herbst #3+#8 |
| Weight decay | 0.00001 (1/10th default 0.0001) | HIGH | Herbst #3+#8 |
| Training steps (optimal) | 2000–3000 | HIGH | Herbst + multiple guides |
| Visual quality peak | 750–1500 steps (NOT final) | HIGH | Herbst #3+#8 |
| Learning rate | 2e-4 baseline; 1e-4 conservative | HIGH | #3 |
| Dataset size | 15–40 images (style LoRA) | HIGH | BFL/HF blog |
| Training time (4090, ~1800 steps) | <1 hour | HIGH | HF Blog #3+#4 |
| Rental cost (cloud GPU) | ~$0.50 | HIGH | #3 |
| Best sampler (cinematic) | DPM++ 2M Ancestral + SGM Uniform | MEDIUM | Herbst |
| Steps to anatomical degradation (FLUX.2-dev) | Past 7,000 | HIGH | Herbst #8 |

**Note (Smith #3):** Herbst research is specifically labeled as FLUX.2-dev + Klein; some parameters (especially step counts) may differ between models. Pick best-looking checkpoint visually, not necessarily final.

---

### B4. Community Implementations & Repositories (2026)
**Source:** Smith #3 (HIGH confidence, direct GitHub dates)

| Repo | Description | Date | URL |
|---|---|---|---|
| flux-2-klein-lora-comfy | ComfyUI setup & fine-tuning guide | Jan 27, 2026 | github.com/grumpykai/flux-2-klein-lora-comfy |
| next-frame-lora | Temporal consistency video editing w/ FLUX 2 Klein 4B | Feb 27–Mar 4, 2026 | github.com/basakozsoy/next-frame-lora |
| nt02-h2r-lora | H→R LoRA fine-tuning Klein 9B, custom dataset | May 14, 2026 | github.com/ryan-seungyong-lee/nt02-h2r-lora |
| Fizgig | Klein 9B LoRA lifecycle: train, profile, repair, extract | — | github.com/shootthesound/Fizgig |
| comfyUI-Realtime-Lora | Real-time LoRA training inside ComfyUI (supports Klein) | — | github.com/shootthesound/comfyUI-Realtime-Lora |

---

## THEME C: BASE→DISTILLED LoRA TRANSFER & FEW-STEP QUALITY

### C1. Official Base→Distilled Workflow
**Source:** Smith #4 (HIGH confidence, BFL official docs)

**Recommended workflow (BFL official):**
- **Train on BASE** (klein-base-9B or klein-base-4B) — preserves full training signal
- **Run inference on DISTILLED** — "typically gives better results than base, runs faster"
- "Distilled models are step-compressed for fast inference; you train against the base checkpoint and the adapter still loads on the distilled model afterward"
- Sources: docs.bfl.ml (HIGH), HF Blog (HIGH)

**Step-count parameters by mode:**

| Mode | Steps | CFG/Guidance | Notes |
|---|---|---|---|
| Distilled | Exactly 4 | 1.0–1.5 | Guidance-distilled; don't exceed 4 steps |
| Base | 20–50 | 3.5–5.0 | Not guidance-distilled; flexible |

**Critical caveat — #1 cause of "my LoRA is bad" reports:**
- Sampling BASE at 4–8 steps → looks undercooked/noisy (Step-count mismatch)
- Running distilled at >4 steps → "overcooked, waxy, or deep-fried images"
- Source: RunComfy — MEDIUM confidence

**LoRA Scale:**
- Recommended range: 0.8–1.0 — MEDIUM confidence (community/vendor)
- Diffusers `lora_scale` parameter has known FLUX issues (Issue #9525)
  - Workaround 1: `pipe.set_adapters([adapter_name], adapter_weights=[scale])`
  - Workaround 2: `pipeline.fuse_lora(lora_scale=0.7)`
- Community report: Some LoRAs show very weak or "mushy/degraded" output at 1.0 vs. disabled (Issue #11975) — MEDIUM

---

### C2. Few-Step Distilled Model Quality Issues
**Source:** Smith #8 (HIGH confidence for empirical findings)

**Documented Problems:**

1. **Amplified noise in Klein vs. dev:**
   - Klein produces heavier grain structure than FLUX.2-dev under identical settings — HIGH (Herbst empirical)
   - Light leaks "more textural and more degraded in Klein" — smaller base model's noisy output gets amplified by LoRA — HIGH

2. **Oversaturation with high CFG in distilled models:**
   - Parallel CFG component causes oversaturation; orthogonal component enhances quality — HIGH (arXiv 2410.02416)
   - LoRA subtraction method: train delta between clean originals vs. degraded versions — MEDIUM (community)

3. **Step count sensitivity:**
   - FLUX.1-Schnell at 4-step: noticeable quality degradation at 1.2× acceleration — HIGH (ToCa paper)
   - FLUX.1-dev at 50 steps: nearly lossless at 1.5× acceleration — HIGH
   - FLUX.2-Turbo optimal: 6–10 steps, best at 8 steps — HIGH (official FLUX.2-dev-Turbo spec)

4. **Distillation compression bottleneck:**
   - Student models don't match teacher capacity → blurry results with MSE loss — HIGH (distillation literature)

5. **LoRA rank & overfitting:**
   - Lower rank LoRAs show clear overfitting at same step counts as higher rank — HIGH (comparative training studies)
   - Higher rank → slower learning → better scene diversity — HIGH

**Mitigations:**

| Issue | Mitigation | Confidence |
|---|---|---|
| Oversaturation | Adaptive Projected Guidance (APG): down-weight parallel CFG component | HIGH |
| Oversaturation | Step size clipping + empirical schedulers | HIGH |
| Step count | FLUX Turbo: stay 6–10 steps; 8 optimal | HIGH |
| LoRA scale (Turbo) | Must be exactly 1.0 per official FLUX.2-dev-Turbo README | HIGH |
| LoRA scale (general) | Character: 0.8–1.0; Style: 0.3–0.6; Concept: 0.6–0.8; Distilled initial: 0.4–1.0 | MEDIUM |
| LoRA scale floor | Below 0.4 → drastic quality degradation | HIGH |
| CFG for distilled | CFG for generator = real model value − 2.0 (video distillation research) | HIGH |
| CFG for Turbo | 3.5 with LoRA scale 1.0 | HIGH |

---

## THEME D: QUANTIZATION WITH MODIFIED INPUT LAYERS

**Source:** Smith #5 (HIGH confidence, cited peer-reviewed papers)

### D1. Core Problem Statement

When x_embedder/patch embedding is replaced with a wider layer accepting concatenated conditioning channels (e.g., `[image_tokens, time_embed, context_tokens]`), quantization faces:
- Non-uniform activation distributions across concatenation boundary
- Parameter mismatch between concatenated input segments
- Silent quality degradation in condition embeddings (worst case: mode collapse)

**Failure mode confidence:**
- Best case (SVDQuant): Low-rank FP16 branch absorbs outliers; accuracy drops 2–5% — MEDIUM
- Typical case (naive INT4/INT8): Accuracy drops 10–20% — MEDIUM
- Worst case: Mode collapse or inconsistent samples — HIGH (this is a real failure mode)
- With proper exclusion: ~0.5–1% accuracy drop — HIGH

---

### D2. Framework-Specific Layer Exclusion

**SVDQuant:**
- Parameter: `--quantization-ignored-layers` (string patterns)
- Critical layers to exclude:
  - `patch_embed`, `x_embedder` — HIGH (quantizers disabled here → impact negligible)
  - `time_embed`, `t_embed` — HIGH (most important non-attention weights; highest importance score)
  - `out_proj`, output projection — HIGH (high median variance)
  - Attention gates, MixFFN depth-wise convolution — HIGH (remain BF16 in production)
- Pattern example: `--quantization-ignored-layers "patch_embed,time_embed,out_proj,attention.*gates,head"`

**Bitsandbytes INT4/INT8:**
- Parameter: `llm_int8_skip_modules` in `BitsAndBytesConfig`
- LLM.int8() mixed-precision decomposition: outliers stay FP16, non-outliers INT8 — intrinsically handles some variance
- Vector-wise quantization per activation dimension
- Known compatibility issue (`llm_int8_skip_modules`, Issue #24037): possibly fixed in recent 2025+ versions — LOW confidence on current state

**Optimum-Quanto:**
- No built-in skip parameter exposed directly
- Recommended: sensitivity analysis → skip top 10 most-sensitive layers
- Skipping top 10 → 0.65% relative accuracy drop vs. naive — HIGH (NVIDIA Tao Toolkit)

**Nunchaku:**
- `transformer.skip_refiners = True` — keeps refiner blocks FP16, main layers 4-bit — HIGH

---

### D3. Best-Practice Layer Exclusion Table

| Layer Pattern | Strategy | Confidence | Justification |
|---|---|---|---|
| `patch_embed`, `x_embedder`, `patchify` | Skip entirely (FP16/FP32) | HIGH | Bimodal statistics; impact negligible only if fully skipped |
| `time_embed`, `t_embed`, `timestep_embed` | Skip entirely (FP16/FP32) | HIGH | Highest importance score; calibration instability across time steps |
| `out_proj`, `head` | Skip entirely (FP16/FP32) | HIGH | Critical for output fidelity; high output channel variance |
| `attention.*` (gates, QKV) | Consider skipping or per-head quantization | MEDIUM | Dimension-critical |
| `norm` (LayerNorm, RMSNorm) | INT8 or FP16 | MEDIUM | Robust if downstream projections careful |
| `mlp.*` (FFN inner layers) | Can safely quantize (INT4/INT8) | HIGH | Wide, smooth distributions |
| Concatenation inputs (conditioning) | Skip if magnitude-diverse; per-segment if uniform | MEDIUM | Prefer FP16 for heterogeneous tokens |

---

### D4. Handling Wider / Modified Input Projections

**Recommended approach (Smith #5):**
1. Keep modified layer in FP16 entirely — HIGH confidence
2. If must quantize: use per-input-segment quantization (SegQuant approach, arXiv 2507.14811)
   - Decompose concatenation before layer
   - Apply separate quantization per component's projection
   - Reconstruct concatenation after individual projections
3. Alternative: Add FP16 residual path (SVDQuant-style low-rank branch)

**SegQuant (arXiv 2507.14811, 2025):** High confidence for theory; MEDIUM for production code

---

### D5. Recent Supporting Research

| Paper | arXiv | Finding | Confidence |
|---|---|---|---|
| Qua²SeDiMo | 2412.14628 | Time/embedding layers consistently high-sensitivity across all diffusion models | HIGH |
| SegQuant | 2507.14811 | Handles semantically-distinct concatenated inputs; per-segment quantization framework | HIGH (theory) |
| QuEST | 2402.03666 | Selective finetuning of time embeddings + attention layers under FP supervision reduces post-quant errors | HIGH |
| Analysis on Quantizing DiTs | 2406.11100 | Empirically confirms patch_embed and t_embed MUST be skipped for sub-1% accuracy loss | HIGH |

---

## THEME E: KLEIN-4B HARDWARE PERFORMANCE

**Source:** Smith #6

### E1. Klein-4B Distilled Inference Benchmarks (4-step)

| GPU | Resolution | Time/Image | VRAM | Source | Confidence | Date |
|---|---|---|---|---|---|---|
| RTX 3090 (24GB) | 1024×1024 | ~3–5s (CPU-offload) | ~13GB | smeltcore.com | MEDIUM | 2026-01 |
| RTX 4090 (24GB) | 512×512 | 0.19s | 16GB | InferenceBench | HIGH | 2026-04 |
| RTX 4090 (24GB) | 1024×1024 | ~0.5–1.0s | 17.8GB | Multiple sources | MEDIUM | 2026-01 to 2026-04 |
| RTX 5090 (32GB) | 1024×1024 | ~0.25–1.2s | ~8.4GB | InferenceBench; GLM-Image; Apatero | MEDIUM-HIGH | 2026-01 to 2026-04 |
| H100 (80GB) | 512×512 | 0.19s | <8GB | InferenceBench | HIGH | 2026-04 |
| H100 (80GB) | 1024×1024 | 0.57s | <8GB | InferenceBench | HIGH | 2026-04 |

**Most rigorous source: InferenceBench (April 2026)**

### E2. Klein-9B Distilled Inference Benchmarks (4-step)

| GPU | Resolution | Time/Image | VRAM | Source | Confidence | Date |
|---|---|---|---|---|---|---|
| RTX 3090 (24GB) | 1024×1024 | 24–35s | ~19GB | HuggingFace discussion #11 | HIGH | 2026-01 |
| RTX 4090 (24GB) | — | ~0.5–2.0s | ~20GB+ | Black Forest Labs | MEDIUM | 2026-01 |
| RTX 5090 (32GB) | 1024×1024 | ~2s | — | GLM-Image; Apatero | MEDIUM | 2026-01 to 2026-04 |
| RTX 5090 (32GB) | 1024×1024 | ~35s | — | RunDiffusion (base model, 50-step) | MEDIUM | 2026-01 |

### E3. Klein-4B Base (Undistilled, 50-step)

| GPU | Resolution | Time/Image | VRAM | Source | Confidence |
|---|---|---|---|---|---|
| RTX 5090 (32GB) | 1024×1024 | ~17s | 9.2GB | DeepWiki Performance Benchmarks | MEDIUM |

### E4. Key Derived Facts

**[DEDUP — confirmed by Smiths #3, #4, #6]:**
- Distilled (4B + 9B): 4 steps — HIGH (universal)
- Base models: 50 steps — HIGH (BFL docs)
- Klein-4B vs Klein-9B speed: "5–10× faster" — MEDIUM (reported, not independently verified under identical conditions)
- Klein-4B inference VRAM minimum: ~13GB (CPU-offload path, BFL-recommended) — HIGH
- RTX 3090: no published direct benchmark for Klein-4B distilled (9B data is HIGH; 4B extrapolated)

**Quantization VRAM reduction:**
- FP8 and NVFP4 variants: claimed 1.6–2.7× speedup, 40–55% VRAM reduction
- No specific consumer GPU benchmarks for quantized variants available in these reports

---

### E5. Training VRAM Summary
**[DEDUP — Smiths #3, #6 agree]:**

| Use Case | VRAM | GPU Examples | Confidence |
|---|---|---|---|
| Klein 4B Inference | ~13 GB | RTX 3060 12GB (offload), RTX 4060 Ti 16GB | HIGH |
| Klein 4B LoRA Training (recommended) | 24 GB | RTX 4090, L4 | HIGH |
| Klein 4B LoRA Training (minimum) | 12–16 GB | With optimization | HIGH |
| Klein 9B LoRA Training | 24 GB | RTX 3090, A5000 | HIGH |
| Kohya fused backward (v0.9.0+) | 4–8 GB | 4-step/distilled only + block swap | MEDIUM |

---

## THEME F: SPATIAL CONDITIONING ARCHITECTURES

**Source:** Smith #7 (as of July 2026)

### F1. Technique Comparison Table

| Technique | Input Layer Retraining | LoRA Compatible | Parameters | Training Data | FLUX Status |
|---|---|---|---|---|---|
| Channel Concatenation | NO (frozen) | YES | 0.1–0.5M | <10K | Native |
| ControlNet | YES (copy encoder) | Indirect/conditional | 10M–1B | 50K–1M | Community |
| IP-Adapter | NO (frozen) | YES | ~22M | <100K | Emerging |
| In-Context / Reference Tokens | NO (frozen) | YES | 1–5M | Variable | Best for DiT |

### F2. Channel Concatenation (Detail)
- Spatial condition encoded via same VAE as generation target
- Condition latent patches concatenated to noise latent patches along sequence dimension
- Processed jointly through transformer self-attention
- LoRA applied to downstream attention layers; patch projection can be trained separately
- Parameter overhead: ~0.1–0.5M per new condition type — MEDIUM
- VideoCanvas (2025) uses patch-based spatial conditioning with in-context reference tokens — HIGH
- Key limitation: Assumes pixel-level spatial alignment; degrades with misaligned references

### F3. ControlNet (Detail)
- Duplicated locked copy of base model encoders + trainable copy
- Zero-convolution gates connect to main model
- Full ControlNet: ~1B params — HIGH; ControlNet-XS: 10–50M params — HIGH (ECCV 2024)
- FLUX implementations available (as of 2025–2026):
  - TheMistoAI/MistoControlNet-Flux-dev (scalable dual-stream) — MEDIUM
  - Shakker Labs FLUX.1-dev-ControlNet-Union-Pro (3.98GB, Apr 2025)
  - XLabs-AI collections (edge, depth, surface normals)
- ControlNet + LoRA: works but requires careful weight management; inference bottleneck

### F4. IP-Adapter (Detail)
- Lightweight projection layers map reference image features (CLIP/custom encoder)
- Decoupled cross-attention layers inject into main model's attention
- ~22M params base; 10–15M for FaceID variants
- FLUX native IP-Adapter: NOT officially shipped as of Jul 2026 — LOW confidence on current status
- Can stack: IP-Adapter + LoRA + ControlNet (inference bottleneck, not training issue)

### F5. In-Context / Reference Token Conditioning (Detail)
- Reference image tokens embedded directly into token sequence (self-attention path)
- No separate encoder duplication
- Key innovations:
  - Context Diffusion (ECCV 2024): MLLM embeddings via cross/self-attention
  - Keep The Essentials (2025, arXiv 2606.23682): Token dropping for multi-reference → 4× speedup
  - VT-DUDA (2025, arXiv 2606.21700): Visual token domain adaptation
- Best fit for DiT/transformer backbone (not U-Net compatible)
- Reference positioning in token sequence matters — sparse research — LOW confidence
- Requires DiT backbone (FLUX qualifies)

### F6. LoRA Merging Utilities (HF Diffusers)
- Weighted merging: `add_weighted_adapter()` (task-arithmetic; requires same rank)
- Fusing: `fuse_lora()` — integrates LoRA weights into base model for inference speed
- For dynamic scaling: `pipe.set_adapters([adapter_name], adapter_weights=[scale])` — HIGH (also cross-referenced in Smith #4 for `lora_scale` workaround)

### F7. Recommended Hierarchy (no input-layer retraining)
1. Best — no training: Channel concatenation + frozen projection (lowest overhead)
2. Good — lightweight: IP-Adapter (22M) or In-context tokens (1–5M)
3. Heavy — full encoder copy: ControlNet-XS (10–50M) or standard ControlNet (1B)

---

## THEME G: GLYPH CONDITIONING SOTA

**Source:** Smith #10

### G1. Summary Table (All Methods)

| Method | arXiv/Venue | Date | Conditioning | Key Metric | Confidence |
|---|---|---|---|---|---|
| TextPixs | 2507.06033 | Jul 2025 | Dual-stream (semantic+glyph) | CER: 0.08 (62% ↓ from 0.21) | HIGH |
| UniGlyph | 2507.00992 / ICCV 2025 | Jul 2025 | Segmentation masks (pixel-level) | EN: 0.9018 Acc, 0.9582 NED | HIGH |
| FontFusion | 2606.06066 | Jun 2026 | Position-aware token embeddings | 74.97% OCR; 76.52% font consistency | HIGH |
| FLUX-Text | 2505.03329 | May 2025 | Visual+Text Embedding Modules | SOTA text editing (numbers absent) | MEDIUM |
| TextFlux | 2505.17778 | May 2025 | Spatial glyph concat (OCR-free) | 1% training data vs. competitors | HIGH |
| HDGlyph | 2505.06543 | May 2025 | Hierarchical disentanglement | Long-tail text (metrics absent) | LOW |
| EasyText | 2505.24417 / AAAI 2026 | May 2025 | Char positioning + DiT backbone | Metrics not quantified | LOW |
| GlyphDraw2 | 2407.02252 | Jul 2024 | Triple-cross attention | Chinese: 0.8266 Acc, 0.8543 NED (AnyText) | HIGH |
| Glyph-ByT5 v1+v2 | 2403.09622 / ECCV 2024 | Mar–Jun 2024 | Character-aware ByT5 encoder | ~90% text accuracy (from <20% baseline) | HIGH |
| GlyphControl | NeurIPS 2023 | Nov 2023 | ControlNet glyph branch | Outperforms DeepFloyd IF on OCR/CLIP/FID | MEDIUM |

### G2. Recent Breakthroughs (2025–2026 Detail)

**TextPixs (arXiv 2507.06033, July 2025):**
- Dual-stream text encoder: semantic + explicit glyph representation
- Character-level glyph embeddings + OCR-guided supervision
- CER: 0.08 vs. 0.21 prior SOTA — 62% reduction — HIGH
- Spelling accuracy: ~90% across 10 languages — HIGH

**UniGlyph (arXiv 2507.00992, ICCV 2025):**
- Pixel-level visual text segmentation masks as unified conditional inputs
- Fine-tuned bilingual segmentation model + adaptive glyph condition + glyph region loss
- AnyText-benchmark results:
  - Chinese: Sen.Acc = 0.8267, NED = 0.8976 — HIGH
  - English: Sen.Acc = 0.9018, NED = 0.9582 — HIGH

**FontFusion (arXiv 2606.06066, June 2026 — most current):**
- Plug-and-play DiT conditioning; **no retraining required** of base model
- Dual encoder: DeepFont + DINOv2 for font embeddings
- Hierarchical token representation at multiple granularities
- Position-aware embeddings (spatial binding typography↔image)
- Multi-level token dropping (efficiency + generalization to unseen fonts)
- Results on FLUX.1 [dev] benchmark:
  - OCR Accuracy: 74.97% (vs. 72.31% unconditioned, 53.57% FonTS) — HIGH
  - Font Consistency: 76.52% (vs. 0.91% unconditioned) — 84× improvement — HIGH
  - CLIP image score: 31.84% (vs. 32.09% unconditioned) — negligible drop — HIGH
  - Decorative fonts: 76% relative improvement over single-encoder baselines — MEDIUM

**TextFlux (arXiv 2505.17778, May 2025):**
- Direct visual glyph conditioning via spatial concatenation — OCR-free
- Built on DiT with Flux backbone
- Trained on 1% of competitor data — HIGH
- Strong multilingual performance with <1,000 samples per new language — HIGH
- Repo: https://github.com/yyyyyxie/textflux

**FLUX-Text (arXiv 2505.03329, May 2025):**
- Built on FLUX-Fill; dual modality: visual + textual conditioning
- Trained on 100K examples vs. 2.9M for competitors (40× data reduction) — HIGH
- Regional Text Perceptual Loss (tailored for text regions)
- Repo: https://huggingface.co/GD-ML/FLUX-Text

### G3. Paradigm Shift Observation (Smith #10)
- **2025–2026 dominant approach:** Spatial/visual conditioning (pixel-level rendered glyphs, segmentation masks, learned glyph embeddings)
- **Superseded:** Text-encoder-only approaches (CLIP text embeddings) — insufficient character-level precision
- **No-retraining options:** FontFusion (token-level), TextFlux (spatial concat) — relevant to project's constraint

---

## THEME H: OPEN-WEIGHT COMMERCIAL MODEL LANDSCAPE

**Source:** Smith #9

### H1. Apache 2.0 Licensed Models

| Model | Parameters | Category | HuggingFace Repo | Confidence | Date Verified |
|---|---|---|---|---|---|
| FLUX.1-schnell | 12B | T2I | black-forest-labs/FLUX.1-schnell | HIGH | Jul 2026 |
| FLUX.2-klein-4B | 4B | T2I + Multi-Ref Editing | black-forest-labs/FLUX.2-klein-4B | HIGH | Jan 2026 |
| CogView4-6B | 6B | T2I | THUDM/CogView4-6B or zai-org/CogView4-6B | HIGH | 2026 |
| Z-Image-Turbo | 6B | T2I | Tongyi-MAI/Z-Image-Turbo | HIGH | Nov 2025 |
| Qwen-Image | 20.43B denoising / 28.85B full pipeline | T2I | Qwen/Qwen-Image | HIGH | ~2025 |
| Qwen-Image-2512 | ~20B (native 2K res) | T2I | Qwen/Qwen-Image-2512 | HIGH | Dec 2025 |
| Kolors | ChatGLM3-6B text encoder + U-Net | T2I (Bilingual) | Kwai-Kolors/Kolors | HIGH (commercial use needs form submission) | 2025 |
| Boogu-Image-0.1 | 10B unified | T2I + Edit | Boogu/Boogu-Image-0.1-Base/-Turbo/-Edit/-Edit-Turbo | HIGH (10B not independently verified) | Jun 2026 |

### H2. MIT Licensed Models

| Model | Parameters | Category | HuggingFace Repo | Confidence | Date Verified |
|---|---|---|---|---|---|
| HiDream-O1-Image | 8B | T2I (Pixel-Native) | HiDream-ai/HiDream-O1-Image | HIGH | May 8, 2026 |
| GLM-Image | 9B autoregressive + 7B diffusion decoder | T2I | zai-org/GLM-Image | HIGH | Jan 10, 2026 |

### H3. Critical Exclusions (Non-Permissive)
- FLUX.2-klein-9B: Non-commercial (despite 4B being Apache 2.0) — [AGREE: Smiths #3, #8, #9, project memory]
- FLUX.1-dev: Non-commercial + non-production
- Stable Diffusion 3: OpenRAIL-M (restrictions)
- SDXL: Stability AI Research License (proprietary)
- InstaFlow: CC-BY-NC-4.0
- Grok-2: Grok 2 Community License (not permissive)

### H4. Notable Fine-Tuning Notes
- All Apache 2.0/MIT models above permit fine-tuning and derivative works (attribution required)
- Kolors commercial use: Requires form submission to kwai-kolors@kuaishou.com (still permissive, with registration step)

---

## CORRECTIONS

**CORRECT #1 — Repository Owner (Smith #1):**
Nunchaku repository is owned by **`nunchaku-ai`** org, NOT `mit-han-lab`. Smith #1 flags this explicitly. Any tooling referencing `mit-han-lab/nunchaku` may be pointing to wrong or legacy URL.

**CORRECT #2 — Smith #3 Internal Dataset Size Inconsistency:**
Smith #3 states "15–40 images" in key findings table (citing BFL/HF Blog) but also links to "Make FLUX.2 Yours: Train a 4B LoRA on 50–100 Images" (HackerNoon). These reflect different guides / different use cases (style vs. subject). Both are valid ranges; they are not contradictory but should be presented as a range (15–100 images) with note that style LoRAs skew lower (15–40) and subject LoRAs may go higher (50–100).

**CORRECT #3 — Klein-9B Distilled License Ambiguity:**
Smiths #3 and #9 state "klein-base-9B: Non-Commercial." Smith #9 lists only `FLUX.2-klein-4B` as Apache 2.0 and does not include `FLUX.2-klein-9B` (distilled) in the approved commercial list. The non-commercial restriction appears to apply to the 9B in all variants. Opus should flag for clarification: does FLUX.2-klein-9B (distilled, non-base) also carry non-commercial restrictions? Smith #9 implicitly says yes by omission.

**CORRECT #4 — Smith #6 "Base Models 16–24 Steps" Entry:**
Smith #6 mentions "16–24 steps for 'base models'" as LOW confidence conflicting source, "may refer to different model variant." Smith #4 firmly establishes base models require 20–50 steps (HIGH confidence, BFL official). The 16–24 step figure should be deprioritized; the BFL-documented 20–50 step figure is authoritative.

**CORRECT #5 — Kohya v0.9.0 Date Framing:**
Smith #3 notes "Kohya v0.9.0 from January 2025 is now 18 months old — recommend verifying latest version." This is accurate as of 2026-07-27. The MINIMUM version requirement (v0.9.0+) is still valid, but current Kohya versions are likely higher. Downstream users should treat v0.9.0 as the floor, not the target.

---

## DISPUTES

**DISPUTE #1 — Nunchaku PR #926 vs. Main Branch (Smith #1, unresolved):**
- Main branch already has FLUX.2 support (`NunchakuFluxTransformer2DModelV2`) since 2025-08-15
- PR #926 (updated 2026-06-24) proposes different naming: `NunchakuFlux2Transformer2DModel`
- These have different naming conventions and may be different implementations
- Smith #1 provides three interpretations but does NOT resolve which is correct
- **Opus action needed:** Determine whether the two are functionally equivalent or represent parallel development tracks with different APIs

**DISPUTE #2 — Minimum VRAM for Klein-4B Training (Smiths #3 vs. #6):**
- Smith #3: "4–8 GB minimum with Kohya fused backward (v0.9.0+)" — HIGH
- Smith #6: "~13 GB minimum for inference (CPU-offload, BFL-recommended)" — HIGH
- **Resolution:** These cover different operations. 4–8 GB is aggressive training-time figure with block swapping + fused backward (extreme optimization path). 13 GB is inference with standard CPU offload. NOT a true dispute — different operations. **Anderson resolution: present both with their respective contexts; not contradictory.**

**DISPUTE #3 — LoRA Runtime in Nunchaku (Smiths #1 vs. #5):**
- Smith #1: `update_lora_params()` / `set_lora_strength()` documented in third-party model card — MEDIUM
- Smith #5: `skip_refiners = True` for Z-Image transformer (official) — HIGH
- These cover different model types (Klein-9B-Nunchaku vs. Z-Image), so not directly contradictory
- **Genuine uncertainty:** Whether the `update_lora_params` / `set_lora_strength` API is functional and supported in current Nunchaku for Klein variants remains unconfirmed from official sources
- **Opus action needed:** Treat runtime LoRA loading on Nunchaku as MEDIUM confidence pending official confirmation

**DISPUTE #4 — Glyph Conditioning "No Retraining" Claim (Smiths #7 vs. #10):**
- Smith #7 lists "Channel Concatenation" as "NO retraining" with ~0.1–0.5M parameter overhead (new projection weights only)
- Smith #10 describes TextFlux's spatial glyph concat as built on DiT backbone — but does not specify retraining status
- FontFusion (Smith #10) explicitly claims "no retraining required" of base model
- **Not a true dispute** — different systems. But Smith #7's claim that channel concatenation requires "only new projection weights" should be verified against specific FLUX backbone implementations. The parameter overhead is for the projection, not the full model.

---

## GAPS

**GAP #1 — Nunchaku INT4 + Klein-4B Runtime LoRA Merge Path:**
Project memory states "Nunchaku INT4 = 2x on 3090 but no runtime LoRA → sub-minute-with-V3 needs offline merge-V3+SVDQuant." No Smith covers the mechanics of this offline merge process. How to merge a trained LoRA into the SVDQuant quantized checkpoint is undocumented across all 10 reports.

**GAP #2 — SVDQuant Quantization of FLUX.2-Klein Specifically:**
Smith #2 confirms NO deepcompressor recipe for FLUX.2 exists. No Smith covers what adaptations are required to quantize FLUX.2-Klein with SVDQuant (e.g., what layers differ from FLUX.1, whether the Qwen3 text encoder introduces new challenges, whether in_channels=128 affects quantization).

**GAP #3 — Qwen3 Text Encoder Specifics:**
Smith #3 (SimpleTuner section) mentions Klein uses "Qwen3 bundled in model repo" as text encoder. No Smith provides detail on Qwen3's architecture, whether it's frozen during LoRA training, its VRAM footprint separately, or how it interacts with quantization.

**GAP #4 — FLUX.2-Klein-9B Distilled Commercial License Status:**
Multiple Smiths confirm base-9B is non-commercial, and 4B is Apache 2.0. Whether the FLUX.2-klein-9B DISTILLED variant also carries non-commercial restrictions is not directly addressed. Smith #9's omission of 9B from the Apache 2.0 list implies non-commercial, but this is inferred, not stated.

**GAP #5 — quanto INT8 Results:**
Project memory states "quanto int8 gave nothing." No Smith covers what was tested with Optimum-Quanto on this specific model family or why it underperformed.

**GAP #6 — FLUX.2 Inference Pipeline Code (diffusers):**
Smiths #3 and #4 cover training pipelines extensively. No Smith covers the complete inference pipeline code for FLUX.2-Klein with LoRA applied (especially the distilled 4-step path via diffusers).

**GAP #7 — Ref2Font Integration:**
Project memory lists "FLUX.2 + Ref2Font is the primary approach, beats VecGlypher on all fronts." No Smith covers Ref2Font — its architecture, how it integrates with FLUX.2, training requirements, or current status. This is a significant gap given it's the project's primary approach.

**GAP #8 — Klein-4B-Base vs. Klein-4B-Distilled Code-Level Differences:**
Smith #4 explains the conceptual difference. No Smith covers what actually differs at the code/weights level between base and distilled (e.g., distillation layers, guidance conditioning modules) or how this affects LoRA weight initialization.

**GAP #9 — Potrace / Vectorization Pipeline:**
Project memory mentions "Potrace CLI + 4x preprocess is production vectorizer." No Smith covers this.

**GAP #10 — Self-Supervised Glyph Completion:**
Project memory mentions "After v1 retrain, use model to fill missing glyphs in partial-coverage fonts." No Smith covers this approach, its feasibility, or related prior work.

**GAP #11 — FontFusion / Glyph Conditioning + LoRA Compatibility:**
Smith #10 describes FontFusion as "no retraining required." Smith #7 shows spatial conditioning is LoRA-compatible. No Smith covers whether glyph conditioning methods (TextFlux, FontFusion, UniGlyph) can be composed with LoRA fine-tuned models simultaneously, or whether training the LoRA jointly with glyph conditioning is feasible.

**GAP #12 — Klein-4B Direct RTX 3090 Benchmark:**
Smith #6 explicitly flags: no published direct benchmark for Klein-4B distilled on RTX 3090. Only Klein-9B on RTX 3090 is HIGH confidence (24–35s). Project's target hardware includes 3090; this remains unverified.

---

## CROSS-REFERENCE MAP (for Opus)

| Topic | Primary Smith | Secondary Smiths | Agreement Level |
|---|---|---|---|
| Klein-4B Apache 2.0 | #9 | #3, #8, memory | FULL AGREE |
| Klein-9B non-commercial | #9 | #3, #8, memory | FULL AGREE |
| 4-step distilled | #4 | #3, #6, #8 | FULL AGREE |
| 20–50 step base | #4 | #6 (conflicting LOW) | AGREE (prefer #4) |
| <1hr training on 4090 | #3 | #4 | FULL AGREE |
| Herbst 50-run findings | #3 | #8 | FULL AGREE |
| `update_lora_params` API | #1 | — | MEDIUM only; unverified |
| SVDQuant skip layers | #5 | #1 (partial corroboration) | AGREE |
| No FLUX.2 deepcompressor recipe | #2 | — | HIGH, single source |
| PR #926 naming discrepancy | #1 | — | HIGH, single source, unresolved |
| FontFusion no-retrain claim | #10 | #7 (general principle) | AGREE |
| LoRA scale issues in diffusers | #4 | #8 (scale thresholds) | COMPATIBLE |

---

*Anderson — Chain A complete. 10 Smiths processed. All unique signal preserved. Opus: editorial judgment is yours.*

============================================================
## Chain B — Anderson Report
============================================================

# CHAIN B — STRUCTURED FINDINGS FOR OPUS SYNTHESIS
**Smiths #11–#20 | Organized: 2026-07-27 | Triage by Anderson**

---

## PREFLIGHT: MEMORY CROSS-CHECKS

Before findings, three memory-note tensions flagged upfront — Opus must resolve:

| Memory Note | Chain B Signal | Status |
|---|---|---|
| "Potrace CLI + 4x preprocess is the production vectorizer" | Smith #11 ranks VTracer > Potrace; calls Potrace "outdated for font work" | ⚑ DISPUTE (see §Disputes) |
| "FLUX.2 + Ref2Font is the primary approach, beats VecGlypher on all fronts" | Smiths #11/#12/#16 treat VecGlypher as top-tier; no Ref2Font data in Chain B | ⚑ COVERAGE GAP — no Smith covers Ref2Font |
| "char_acc ceiling is a style-lottery artifact; GT-guided DPO track CLOSED 2026-07-21" | Smith #16 cites R-ACC/OCR metrics as standard; Smith #11 reports VecGlypher 2× R-ACC win | CONSISTENT — R-ACC is an eval metric; closing DPO track ≠ abandoning OCR eval |

---

---

# SECTION 1: BITMAP-TO-VECTOR TRACING TOOLS

**Primary source:** Smith #11 | **Supporting:** Smith #12 (neural context), Smith #20 (pipeline context)

---

## 1A. Potrace

**Curve type:** Cubic Bézier (primary output curves) and straight line segments. Smith #11 describes "Quadratic Bézier (straight segments), cubic Bézier (corners)" — **see §Corrections #1.** | Sources: Smith #11 [HIGH]

**Output quality for fonts:**
- Sharp edge definition but monochromatic-only | Smith #11 [MEDIUM]
- Produces patchy/broken outlines with low noise resistance | Smith #11 [MEDIUM, derived from aisvg.app + saashub review]
- O(n²) complexity | Smith #11 [MEDIUM]
- Unsuitable for practical font work without pre-processing | Smith #11 [MEDIUM]

**Licensing:** GPLv2 or later (copyleft); GPL library available since v1.6 | Smith #11 [HIGH]

**CLI:** Full command-line tool. Homebrew, PyPI (potrace-cli, potracer). First release 2001; current v1.16+ | Smith #11 [HIGH]

**Pipeline use:** Smith #11 notes the memory "Potrace + 4× preprocessing" approach as acceptable if optimized, but "not recommended for new projects." | Smith #11 [MEDIUM]

---

## 1B. AutoTrace

**Curve type:** Cubic Bézier | Smith #11 [MEDIUM]

**Output quality for fonts:**
- Supports both **outline tracing AND centerline tracing** (`-centerline` mode) | Smith #11 [MEDIUM]
- Precision controllable via tolerance settings | Smith #11 [MEDIUM]
- Fewer artifacts than Potrace for complex shapes | Smith #11 [MEDIUM]
- Only traditional tool offering centerline mode — enables stroke-based fonts | Smith #11 [HIGH — distinctive feature]

**Licensing:** GPLv2+ OR LGPL 2.1+ (I/O functions more permissive) | Smith #11 [HIGH]

**CLI:** Full CLI with centerline mode; integrated into Inkscape 1.0+ | Smith #11 [HIGH]

---

## 1C. VTracer

**Curve type:** Spline curves (high-quality mode, recommended); polygon approximation (fast mode) | Smith #11 [MEDIUM — brightcoding.dev March 2026]

**Output quality for fonts:**
- Most consistent and usable outlines of traditional tools (Smith #11 ranking) | Smith #11 [HIGH overall assessment]
- O(n) complexity — 64× faster than Potrace on scale-invariant tasks | Smith #11 [HIGH — GitHub visioncortex/vtracer]
- Handles colored, high-resolution input | Smith #11 [HIGH]
- Smoother curves, fewer redundant nodes than Potrace/Image Trace | Smith #11 [MEDIUM]
- Used as baseline in 2024–2026 research papers | Smith #11 [MEDIUM]

**Licensing:** Open-source, non-GPL (license type not fully specified in sources) | Smith #11 [MEDIUM — GitHub repo, license file present but type unclear]

**CLI:** Rust-based. `cargo install vtracer-cli`. Also PyPI (vtracer 0.6.15+) and web UI | Smith #11 [HIGH — crates.io]

**Smith #11 production ranking (traditional tools):** VTracer > AutoTrace > Potrace

---

## 1D. Comparative Table (Traditional Tools) — As Reported by Smith #11

| Tool | Noise Resistance | Detail Quality | Speed | Monochrome Only |
|---|---|---|---|---|
| Potrace | POOR | SHARP but broken | O(n²) slow | Yes |
| AutoTrace | MEDIUM | GOOD w/ precision tuning | Medium | Yes |
| VTracer | GOOD | GOOD, fewer artifacts | O(n) fast | No (color-aware) |

Source: Smith #11 [MEDIUM overall — derived from comparative reviews]

---

---

# SECTION 2: NEURAL / LEARNED VECTORIZATION FOR FONT GLYPHS

**Primary sources:** Smith #11, Smith #12 | **Supporting:** Smith #16 (metrics), Smith #17 (embedding context), Smith #18 (few-shot context)

**Convergence across Smith #11 + #12:** No 2024–2026 paper provides quantitative benchmarks comparing neural vectorization directly to traditional tracing (potrace/vtracer/AutoTrace). Comparisons are exclusively against older neural baselines. [HIGH — both Smiths flag independently]

---

## 2A. VecGlypher (CVPR 2026)

**arXiv:** 2602.21461 | **Submitted:** February 25, 2026 | **Accepted:** CVPR 2026

**Architecture:** Multimodal LLM operating directly on SVG path token sequences. No raster intermediate. Supports text-prompt AND image-reference conditioning. | Smith #12 [HIGH]

**Training data:**
- Stage 1: 39K Envato fonts (continuation pre-training) | Smith #12 [HIGH]
- Stage 2: 2.5K expert-annotated Google Fonts (post-training) | Smith #12 [HIGH]

**Quality metrics (Smith #11, cited as HIGH from arXiv:2602.21461):**
- 2× R-ACC vs baselines
- 92% lower Chamfer Distance vs DeepVecFont-v2/DualVector
- 97.8% lower FID

**Smith #12 on quality:** "Substantially outperforms both general-purpose LLMs and specialized vector-font baselines" — qualitative framing, no additional numerics in #12 abstract | [MEDIUM]

**Composite proxy rewards used:** R-ACC, CD, CLIP, DINO, FID — mixes vector/raster geometry, topology, typographic regularity, recognizability | Smith #16 [HIGH]

**Charset:** Full charset (English and Chinese demonstrated); direct SVG emission without post-processing | Smith #12 [HIGH]

**Key advantage:** One-pass generation, editable SVG output, watertight outlines | Smith #12 [HIGH]

**Code status:** ⚑ DISPUTE — Smith #12 states "✓ Released — https://github.com/xk-huang/VecGlypher"; Smith #18 states "Not yet public; project page: xk-huang.github.io/VecGlypher" — see §Disputes #2

**HuggingFace:** VecGlypher/VecGlypher-27b-it | Smith #17 [MEDIUM]

**Authors:** Huang et al. (Peking University) | Smith #12 [HIGH]

---

## 2B. VecFusion (CVPR 2024)

**arXiv:** 2312.10540 | **Submitted:** December 16, 2023 | **Revised:** May 21, 2024

**Architecture:** Cascaded dual-stage diffusion. Raster diffusion → vector diffusion (transformer backbone, mixed discrete-continuous representation). Predicts control point count, path topology. | Smith #12 [HIGH]

**Quality metrics (Smith #11, HIGH from CVPR paper):**
- L1 error: 0.014 (geometric distance)
- Chamfer Distance: 0.16 (control point accuracy) — confirmed independently by Smith #16 [HIGH]
- Control point count difference: ±3.05 from ground truth
- Path count variance: ±0.03
- Outperforms PolyVec, LIVE, Potrace/VTracer on glyphs | Smith #11 [MEDIUM]

**Smith #12 on quality:** "Higher quality vector fonts with complex structures and diverse styles" — visual claims, no additional numerical confirmation in #12 | [MEDIUM]

**Charset:** Full font generation + partial-font completion capability | Smith #12 [HIGH]

**Code:** ✓ Released — https://vikastmz.github.io/VecFusion/ | Smith #12 [HIGH]

**Authors:** Thamizharasan, Liu, Agarwal, Fisher, Gharbi, Wang, Jacobson, Kalogerakis (UMass/Adobe) | Smith #12 [HIGH]

---

## 2C. DeepVecFont-v2 (CVPR 2023)

**arXiv:** 2303.14585 | **Submitted:** March 25, 2023

**Architecture:** Transformer-based sequence model (replaces RNN); relaxation representation; auxiliary point sampling; context-based self-refinement | Smith #12 [HIGH]

**Quality metrics [HIGH — from paper table]:**
- Error-EN: 0.052
- Error-CN: 0.080
- DeepSVG baseline: Error-EN 0.125 / Error-CN 0.167
- Original DeepVecFont: Error-EN 0.056 / Error-CN 0.086

**Code:** ✓ Released — https://github.com/yizhiwang96/deepvecfont-v2 | Smith #12 [HIGH]

**Authors:** Wang, Yu, Zhu, Lian (Peking University) | Smith #12 [HIGH]

---

## 2D. NIV: Neural Axis Variations for Variable Font Generation (2026)

**arXiv:** 2606.05261 | **Submitted:** June 3, 2026

**Architecture:** Per-point displacement prediction + Property Embedding for multi-axis interactions; converts static fonts → variable fonts | Smith #12 [HIGH]

**Training data:** 1M+ variation tuples from variable Google Fonts dataset (novel construction) | Smith #12 [HIGH]

**Charset generalization:** Unseen code points, unseen font styles, high-complexity CJK glyphs, out-of-distribution handwriting | Smith #12 [HIGH]

**Code:** ✗ No code release found | Smith #12 [HIGH]

**Authors:** Benedek (Reichman), Shamir, Fried (Stanford) | Smith #12 [HIGH]

---

## 2E. DiffVecFont (CVM 2025)

**Published:** April 26, 2025

**Architecture:** Dual-modal vector denoising diffusion model integrating vector and raster images; quadratic Bézier reconstruction | Smith #12 [HIGH]

**Quality:** Claims to overcome "fine contour reconstruction" and "concise representation" limitations; no baseline comparison quantified in sources | Smith #11/12 [MEDIUM]

**Code:** ✗ No code release | Smith #12 [HIGH]

---

## 2F. LIVE (CVPR 2022 Oral)

**arXiv:** 2206.04655

**Architecture:** Iterative Bézier path optimization with layer-wise structure learning; component-wise path initialization + novel loss functions | Smith #12 [HIGH]

**Quality:** "PolyVec and LIVE often failed to produce coherent curve topology" per VecFusion (Smith #11 cites LIVE as outperformed baseline); Smith #12 says LIVE "produces more plausible vectorized forms than prior works" | [MEDIUM — conflicting context between VecFusion-era and LIVE's own claims]

**Code:** ✓ Released — https://github.com/ma-xu/LIVE | Smith #12 [HIGH]

**Authors:** Ma, Xu, et al. (Picsart/MIT) | Smith #12 [HIGH]

---

## 2G. Im2Vec (CVPR 2021 Oral)

**arXiv:** 2102.02798

**Architecture:** VAE mapping raster → latent space → Bézier curves. Dual-part representation (positive/negative paths for glyph contours via boolean ops). Differentiable rasterization. | Smith #12 [HIGH]

**Quality:** Outperforms SVG-VAE and DeepSVG (L2 pixel-space loss) | Smith #12 [MEDIUM]

**Code:** ✓ Released — https://github.com/preddy5/Im2Vec | Smith #12 [HIGH]

**Authors:** Reddy, Gharbi, Mitra, Funkhouser, Johnson (UCL/Princeton/Google) | Smith #12 [HIGH]

---

## 2H. NIVeL (CVPR 2024)

**arXiv:** 2405.15217

**Architecture:** Neural implicit field representation; decomposable, editable layers. Solves topology/genus constraints unaddressed by Bézier-based methods | Smith #12 [HIGH]

**Input:** Text-to-vector; Illustrator-compatible output | Smith #12 [HIGH]

**Code:** ✗ No code release found | Smith #12 [HIGH]

**Authors:** Thamizharasan, Liu, Fisher, Zhao, Kalogerakis, Lukáč (UMass/Adobe) | Smith #12 [HIGH]

---

## 2I. VectorArk (CVPR 2026)

**arXiv:** 2605.24398 | **Submitted:** May 23, 2026

**Architecture:** VLM with novel rounded polygon primitives (non-Bézier); degradation model for noisy/imperfect inputs | Smith #12 [HIGH]

**Scope:** General image vectorization, not font-specific | Smith #12 [HIGH]

**Code:** ✗ No code release | Smith #12 [HIGH]

**Authors:** Gehlaut, Liu, Bansal et al. (Adobe/others) | Smith #12 [HIGH]

---

## 2J. VFIG (arXiv:2603.24575, March 2026)

**Architecture:** VLM-based raster-to-SVG for technical figures; dataset: 66K figure-SVG pairs (VFIG-DATA) | Smith #12 [HIGH]

**Scope:** Technical diagrams, not font-specific | Smith #12 [HIGH]

**Code:** ✓ Released — https://github.com/RAIVNLab/VFig | Smith #12 [HIGH]

---

## 2K. SVGDreamer (CVPR 2024)

**arXiv:** 2312.16476

**Architecture:** Text-to-SVG diffusion + Semantic-driven Image Vectorization (SIVE) + Vectorized Particle-based Score Distillation (VPSD) | Smith #12 [HIGH]

**Scope:** Text-guided graphics, not font-specific charset generation | Smith #12 [HIGH]

**Code:** ✓ Released — https://github.com/ximinng/SVGDreamer | Smith #12 [HIGH]

---

## 2L. DualVector (CVPR 2023)

**Architecture:** Unsupervised learning of vector font representations; dual-part paths (positive/negative) | Smith #12 [HIGH]

**Code:** ✓ Released — https://github.com/thuliu-yt16/dualvector | Smith #12 [HIGH]

---

## 2M. Code Availability Master Table (Neural Methods)

| Method | Year | Code? | Repository |
|---|---|---|---|
| VecGlypher | 2026 | ⚑ DISPUTED | github.com/xk-huang/VecGlypher (if released) |
| VectorArk | 2026 | ✗ | — |
| VFIG | 2026 | ✓ | github.com/RAIVNLab/VFig |
| NIV | 2026 | ✗ | — |
| VecFusion | 2024 | ✓ | vikastmz.github.io/VecFusion |
| SVGDreamer | 2024 | ✓ | github.com/ximinng/SVGDreamer |
| NIVeL | 2024 | ✗ | — |
| DiffVecFont | 2025 | ✗ | — |
| DeepVecFont-v2 | 2023 | ✓ | github.com/yizhiwang96/deepvecfont-v2 |
| DualVector | 2023 | ✓ | github.com/thuliu-yt16/dualvector |
| LIVE | 2022 | ✓ | github.com/ma-xu/LIVE |
| Im2Vec | 2021 | ✓ | github.com/preddy5/Im2Vec |

Sources: Smith #12 [HIGH throughout]

---

## 2N. Literature Gap (Convergence: Smith #11 + Smith #12)

**No 2024–2026 neural vectorization paper benchmarks against traditional CLI tracers (potrace, vtracer, AutoTrace).** All neural comparisons target older neural baselines (SVG-VAE, DeepSVG, original DeepVecFont, PolyVec). This gap is independently flagged by both Smiths. [HIGH confidence on gap existence]

---

---

# SECTION 3: FONT HINTING TOOLS & PRACTICES

**Primary source:** Smith #13

---

## 3A. Tool Inventory

**ttfautohint:**
- Version: 1.8.4 (released August 14, 2021; no 2025–2026 releases found) | Smith #13 [HIGH/2021]
- Status: Stable but dormant — last significant update was v1.8.3.2
- Architecture: CLI tool based on FreeType's auto-hinting engine; removes existing bytecode, inserts new TrueType instructions
- Does NOT hint TrueType variable fonts (only default instance) | Smith #13 [HIGH]
- Python wrapper: ttfautohint-py — last commit July 15, 2026 (actively maintained) | Smith #13 [HIGH/2026]
- De facto standard for automated hinting as of 2026 | Smith #13 [HIGH]

**FreeType:**
- Current version: 2.14.3 (March 2026) | Smith #13 [HIGH/2026]
- Active development

**fontTools:**
- Version: 4.34.4+ (latest on PyPI, 2026) | Smith #13 [HIGH/2026]
- Does NOT include a built-in general-purpose autohinter — requires AFDKO for CFF/PostScript hints | Smith #13 [HIGH]
- For TrueType: manual bytecode manipulation only; no automatic instruction generation | Smith #13 [HIGH]
- Variable font hinting: handles hint interpolation via `cvar` table during compilation | Smith #13 [HIGH]
- Limitation: autohinter only sees default instance; does not auto-generate hints for variable font deltas | Smith #13 [HIGH]

**Visual TrueType (VTT, Microsoft):**
- Version: 6.35 (July 2021) | Smith #13 [MEDIUM/2021]
- Status: Professional manual + automated hinting tool; supports variable fonts; Windows GUI + Python interface
- No 2026 update found | Smith #13 [HIGH]

**Specialized:**
- vttLib (Dalton Maag): Dump/merge/compile VTT data in UFO3 | Smith #13 [HIGH]
- fonttools-opentype-hinting-freezer (Adam Twardoch): Last updated July 5, 2026 | Smith #13 [HIGH/2026]
- gftools fix-nonhinting: Google Fonts batch hinting utility | Smith #13 [HIGH]

---

## 3B. Hinting Effectiveness by Size

- Below ~24px: Hinting determines crispness by aligning outline points to pixel grid | Smith #13 [HIGH]
- 10–12px: Critical for UI text (Verdana, Tahoma, Inter, Roboto, Open Sans, IBM Plex Sans recommend 12px minimum) | Smith #13 [HIGH/modern design standards]
- 12–24px: Significant improvement | Smith #13 [MEDIUM]
- 24–36px: Hinting less critical | Smith #13 [MEDIUM]
- >36px: Largely irrelevant | Smith #13 [HIGH/documented practice]

---

## 3C. Platform Rendering (2026)

| Platform | Approach | Hinting Use |
|---|---|---|
| Windows | ClearType + DirectWrite + subpixel RGB | Important <24px |
| macOS | Antialiasing (grayscale) | Ignored |
| Linux (FreeType) | LCD/grayscale antialiasing | Optional |
| Web (Browsers) | CSS font-smoothing varies | Inconsistent; variable fonts preferred |
| iOS/Android | Antialiasing | Ignored |

Source: Smith #13 [HIGH on platform behaviors]

---

## 3D. 2026 Consensus: Hinting Declining but Not Dead

- **Declining necessity on modern platforms** (high-DPI, macOS, Android, web) — 2026 consensus | Smith #13 [HIGH]
- **Still matters** for Windows GDI/DirectWrite <24px, legacy/budget displays, e-readers, print <8pt | Smith #13 [HIGH]
- **Estimated ~30% of user base still benefits** | Smith #13 [LOW — estimated, varies by application audience]
- **Practical recommendation for synthesized fonts:**
  - Windows + <24px target: Apply ttfautohint
  - Variable font: Hint default instance only; skip if high-DPI target
  - Modern web-only: Skip hinting; focus on WOFF2
  - Validate with fontBakery | Smith #13 [HIGH]

---

## 3E. Variable Font Hinting Limitations

- ttfautohint does NOT hint TrueType variable fonts | Smith #13 [HIGH]
- CFF2 supports variable fonts but overlapping contours + hinting remain problematic | Smith #13 [HIGH]
- Recommendation: Use variable TTF if hinting required | Smith #13 [HIGH]
- fontTools.varLib compiles hint differences into `cvar` table; requires pre-hinted masters | Smith #13 [HIGH]

---

## 3F. No AI Hinting Breakthroughs (2025–2026)

No breakthrough autohinting tools released in 2025–2026. Neural research (DiffuFont, GAR-Font 2026) targets glyph outline synthesis, not hinting. No evidence of neural-network–trained autohinter replacing FreeType engine. | Smith #13 [MEDIUM/HIGH — 2025–2026 scan]

---

---

# SECTION 4: AUTOMATED KERNING & SPACING

**Primary source:** Smith #14

---

## 4A. Spacing / Sidebearing Tools

**HTLetterspacer:**
- Last update: 2026-06-24 | Smith #14 [HIGH]
- Type: Optical spacing via white-area polygon measurement
- Automation: Fully automated with manual tuning options
- Approach: Analyzes glyph outline at configurable frequency (paramFreq=5 default, in font units); computes left/right sidebearings for target optical spacing
- Version 2.0 (Glyphs 3 plugin, 2026 rewrite): Rules now stored inside font (not sidecar files) | Smith #14 [HIGH]
- Keeps manually-positioned components in place when respacing bases | Smith #14 [HIGH]
- Status: Gold standard for automated sidebearing

**kernagic:**
- Last update: 2019-03-27 | Smith #14 [MEDIUM — last push 2019]
- Type: Semi-automatic optical spacing via rhythm-point detection
- Input: UFO fonts
- Status: Mature but stale; suggested in 2026 surveys but not updated post-2019 | Smith #14 [LOW on 2026 usage]

---

## 4B. Kerning Pair Generation Tools

**Kern On:**
- Latest: v1.38, released 2026-07-26 | Smith #14 [HIGH — most recent tool update in any Smith]
- Type: Automated class-based kerning pair generation
- Recent changes: v1.38 adds Glyphs 4 support; drops Glyphs 2; v1.36 (2025-03-23) made generated class kerning "closer to what humans would typically do" | Smith #14 [MEDIUM on changelogs]
- Manual work required: Proof-reading and refinement of generated pairs
- Status: Active 2026

**Kerning Pairs Generator (kerning-pairs-generator.vercel.app):**
- 44 language presets (Latin, Cyrillic, Armenian, Hindi, Thai, CJK, Arabic, Georgian) | Smith #14 [HIGH]
- Generates test strings (ABA, AB, BA patterns); designer must kern manually after
- Browser-based; fonts never leave browser; exports to FontLab, Glyphs, RoboFont, FontForge
- Automation level: SEMI-AUTOMATED (strings only; no pair values) | Smith #14 [HIGH]

**iKern:**
- Creator: Igino Marini (Fell Types)
- Type: Custom proprietary service; algorithm NOT published | Smith #14 [LOW — algorithm details]
- Requires multiple rounds of designer interaction
- Status: Historical; among first services to claim reliable kern-pair generation (~2010s) | Smith #14 [MEDIUM]

---

## 4C. Built-in Editor Autokerning

**FontLab K2 algorithm:**
- Adjusts kerning so smallest horizontal distance between glyph contours = target distance | Smith #14 [MEDIUM]
- Adds/changes pairs only if calculated value differs significantly from current | Smith #14 [MEDIUM]
- FontLab notes "for best results, manually kern instead" | Smith #14 [MEDIUM]

**FontCreator Optical Metrics Wizard:**
- Automated sidebearing generation via glyph shape analysis | Smith #14 [HIGH]
- "Finds it harder to calculate good values for glyphs with bowls (be, pe, po)" — direct quote | Smith #14 [HIGH]
- Provides strong first draft; requires hand-correction of problematic glyphs | Smith #14 [MEDIUM]
- Updated 2026 | Smith #14 [HIGH]

**FontForge:**
- No automatic kerning/spacing algorithms documented in public help | Smith #14 [HIGH]
- Manual kerning pair dialog only | Smith #14 [HIGH]
- Documentation updated 2025-10-09 | Smith #14 [HIGH]

---

## 4D. Machine Learning Approaches

**"Learning to Kern: Set-wise Estimation of Optimal Letter Space" (ICDAR 2024, arXiv:2402.14313):**
- Architecture: Set-wise Transformer (1 layer, 2 heads, 2-layer FFN); input 512D ResNet18 features per letter → 32D pair vectors
- Self-attention enables consistent spacing across entire character set | Smith #14 [HIGH]
- Results on ~2500 Google Fonts:
  - MAE: ~5.3 pixels (average letter space ~115 pixels) | Smith #14 [HIGH]
  - Sans-serif MAE: ~4.0 pixels | Smith #14 [HIGH]
  - Outperformed heuristics on 217/256 test fonts | Smith #14 [MEDIUM]
  - <7px error on 203 fonts | Smith #14 [MEDIUM]
- **No public tool announced as of 2026** | Smith #14 [LOW on deployment]
- Authors: Kei Nakatsuru & Seiichi Uchida (Kyushu University)

---

## 4E. Critical Finding: Neural Font Generators Do NOT Handle Metrics

**VecGlypher does NOT generate kerning or spacing metrics** — must be handled separately via HTLetterspacer or Kern On | Smith #14 [HIGH — explicitly tested/stated]

**VecFontSDF (CVPR 2023, arXiv:2303.12675):** Glyph metrics mentioned as metadata (width, ascender, descender) but NOT synthesized by model | Smith #14 [MEDIUM]

This is a **pipeline gap** relevant to the entire synthesis workflow: glyph generation → spacing → kerning are decoupled steps.

---

## 4F. Helper Scripts / Utilities

- **StringSmash** (github.com/FrankFonts/StringSmash): RoboFont/Glyphs spacing+kerning test string generator; last update 2023-02-28 | Smith #14 [MEDIUM]
- **KernBot.io** (github.com/joeygrable94/KernBot.io): Glyphs App rapid prototyping utility; created 2020 | Smith #14 [MEDIUM]
- **Glyph-Sandwich** (github.com/archieheaslip/Glyph-Sandwich): Glyphs script for spacing preview; created 2024-02-26 | Smith #14 [HIGH/recent]

---

---

# SECTION 5: FONT VALIDATION / QA TOOLS

**Primary source:** Smith #15

---

## 5A. FontBakery

- Version: 1.1.0 (current) | Smith #15 [HIGH]
- GitHub: github.com/fonttools/fontbakery
- Install: `pip install fontbakery`
- Status: Maintained but not updated with new features (per GitHub changelog and TypeDrawers discussion) | Smith #15 [HIGH]
- Speed: SLOW (minutes per font) | Smith #15 [HIGH]
- Profiles: universal, googlefonts, adobefonts, ufo, ufonts
- Check categories: OpenType spec compliance, name table, outline quality (self-intersecting paths, extrema), metric consistency (OS/2, hhea), kerning, hinting, cmap, GSUB/GPOS, embedding permissions | Smith #15 [HIGH]
- Output formats: HTML, JSON, Markdown, Text | Smith #15 [HIGH]
- Severity levels: FAIL, WARN, INFO, PASS | Smith #15 [HIGH]

**Key CLI:**
```bash
fontbakery check-universal myfont.ttf
fontbakery check-googlefonts fonts/*.ttf --html report.html
fontbakery check-googlefonts fonts/*.ttf --json report.json
```
Source: Smith #15 [HIGH]

---

## 5B. Fontspector (2026 — Active Successor to FontBakery)

- GitHub: github.com/fonttools/fontspector | Smith #15 [HIGH/2026]
- Language: Rust (Read-Fonts implementation)
- Status: Active development 2026; positioned as FontBakery successor | Smith #15 [HIGH]
- Speed claim: "1000× faster than FontBakery; can evaluate entire Google Fonts library in seconds" | Smith #15 [MEDIUM — not independently benchmarked]
- Web version (WASM): https://fonttools.github.io/fontspector/ | Smith #15 [HIGH]
- Optional Python support via `--use-python` flag | Smith #15 [HIGH]
- Profiles: googlefonts, opentype, universal, microsoft, adobe | Smith #15 [HIGH]
- Install: Binary downloads or `cargo install fontspector` | Smith #15 [HIGH]
- CLI syntax: MEDIUM confidence (documentation sparse; rely on --help) | Smith #15 [MEDIUM]

---

## 5C. Font Validator (Microsoft / HinTak Fork)

- Original Microsoft project: NOT actively maintained | Smith #15 [HIGH]
- Active fork: github.com/HinTak/Font-Validator (active 2026 releases) | Smith #15 [HIGH]
- Language: C# | Smith #15 [HIGH]
- Check categories: OS/2, head, hmtx, cmap, name, glyf, loca, post, gasp, DSIG, CFF tables; broken contours, hairpins, tight loops, invalid point sequences; vertical metrics (usWinAscent, usWinDescent); TrueType and CFF hinting instruction validity; GSUB, GPOS, MATH, BASE table structure; embedding bits | Smith #15 [HIGH]
- Supports batch processing for CI/CD pipelines | Smith #15 [HIGH]
- CLI exact flags require checking HinTak fork README | Smith #15 [MEDIUM]

---

## 5D. OTS (OpenType Sanitizer)

- Source: chromium.googlesource.com (Google/Chromium) | Smith #15 [HIGH]
- Language: C++; security-oriented; used in Chrome and Firefox | Smith #15 [HIGH]
- Focus: Binary structure validation, security (prevents font-based attacks)
- Output: Pass/fail + sanitized font; strips unknown tables | Smith #15 [HIGH]
- Install: `brew install ots` / `apt-get install opentype-sanitizer` | Smith #15 [HIGH]
- CLI: `ots-sanitize myfont.ttf` / `ots-sanitize myfont.woff2` | Smith #15 [HIGH]

---

## 5E. FontForge (GUI-Based + Limited CLI)

- Version: FontForge 20251009 (October 2025) | Smith #15 [HIGH]
- Validation via Find Problems tool: Paths (open paths, self-intersecting, clockwise direction, missing extrema), Metrics, Outlines, Coordinates, Names, Hinting, Kern, Comments | Smith #15 [HIGH]
- CLI validation: LIMITED; primarily GUI-based; Python scripting preferred | Smith #15 [LOW on CLI]

---

## 5F. fontTools (Inspection/Infrastructure)

- Primary use: Programmatic access; NOT primarily a CLI validator | Smith #15 [HIGH]
- Key validation: `ttFont.checkChecksums()` (3 modes); `ttx` for XML conversion and manual inspection | Smith #15 [HIGH]
- Python checksum: `TTFont('myfont.ttf', checkChecksums=2)` raises exception on wrong checksums | Smith #15 [HIGH]

---

## 5G. Additional Tools

- **font-line** (source-foundry/font-line): Vertical metrics reporting and CLI adjustment; `font-line myfont.ttf --report` | Smith #15 [HIGH]
- **Fontist/Fontisan:** Active alternative to Font Validator; migration guide available | Smith #15 [MEDIUM — minimal details]

---

## 5H. Recommended Production Workflow (Smith #15)

1. Frontline: Fontspector (fastest, modern, web option)
2. Secondary: FontBakery (mature, comprehensive, integrates Font Validator)
3. Specialist: Font Validator (table-level detail, especially metrics)
4. Browser safety: OTS (security validation before web deployment)
5. Manual: FontForge (GUI debugging when checks fail)

Source: Smith #15 [HIGH on tool strengths; LOW on "best" workflow — context-dependent]

---

---

# SECTION 6: FONT GENERATION EVALUATION METRICS

**Primary source:** Smith #16 | **Supporting:** Smith #11 (VecGlypher metrics), Smith #12 (method benchmarks), Smith #17 (SWER), Smith #18 (method benchmarks)

---

## 6A. Pixel-Level Metrics (Universal — HIGH confidence, 3+ papers)

| Metric | Description | Papers |
|---|---|---|
| SSIM | Structural similarity (luminance, contrast, structure) | Universal in 2025–2026 |
| LPIPS | Learned perceptual patch similarity (VGG features, human-judgment-trained) | Universal |
| FID | Fréchet Inception Distance (distribution distance, InceptionNet features) | Universal |
| L1 / MAE | Per-pixel mean absolute difference | Universal |
| RMSE | Root mean square error | Universal |
| PSNR | Peak signal-to-noise ratio | Universal |

Source: Smith #16 [HIGH — appears in 3+ independent recent papers with consistent definitions]

---

## 6B. OCR / Legibility Metrics

| Metric | Description | Source Paper | Date | Confidence |
|---|---|---|---|---|
| R-ACC | OCR accuracy normalized by GT accuracy; variant R-ACC(U) treats upper/lowercase sharing as correct; can exceed 100% | VecGlypher (2602.21461) | 2026 | HIGH |
| CER | Character Error Rate from OCR models | TextMastero (2408.10623) | 2025 | HIGH |
| NED / NLD | Normalized Edit Distance / Levenshtein Distance | Multiple 2025–2026 | HIGH | HIGH |
| CNN recognition accuracy | Multi-font CNN assessment; tolerant of missing/broken strokes in stroke-rich characters | Survey 2025–2026 | HIGH | HIGH |

Source: Smith #16 [HIGH throughout]

**Note from memory:** "char_acc ceiling is a style-lottery artifact at every level" — OCR metrics valid for *evaluation* but not as optimization targets for DPO-style training.

---

## 6C. Style Consistency Metrics

| Metric | Description | Source | Confidence |
|---|---|---|---|
| CLIP-I | Style-adapted CLIP encoder (cosine similarity, style-trained) | arXiv:2510.09475, 2025 | HIGH |
| Long-CLIP (font fine-tuned) | Reliable for typographic style preservation | FontUse 2603.06038, 2026 | HIGH |
| Style Score | Classification accuracy trained to distinguish font styles | arXiv:2410.02309, 2025 | HIGH |
| Content Score | Classification accuracy for character structure preservation | arXiv:2410.02309, 2025 | HIGH |
| Stylistic Coherence (5-pt Likert) | Human rating: stroke weights and serifs consistent across charset | Standard 2025–2026 | HIGH |
| DINO Similarity | Vision Transformer feature-based similarity | VecGlypher 2026 | HIGH |

Source: Smith #16 [HIGH on all above]

---

## 6D. Geometry / Vectorization Metrics

| Metric | Description | Specific Result | Confidence |
|---|---|---|---|
| Chamfer Distance (CD) | Sum of minimum distances from edge points; lower = better | VecFusion: CD=0.16 | HIGH (confirmed: Smith #11, #16) |
| Geodesic CD (GeoCD) | Topology-aware variant via multi-hop kNN-graph; insensitive to Euclidean shortcuts across concavities | arXiv:2506.23478, 2025 | MEDIUM (specialized, recent) |
| Hausdorff / Partial Hausdorff (PHD) | Sensitive to worst-case outliers; PHD useful for stroke-weight similarity | Smith #16 | MEDIUM |
| Max-IoU | Intersection-over-Union after glyph alignment | Multiple 2025–2026 | HIGH |

Source: Smith #16 [HIGH/MEDIUM as noted]

---

## 6E. Stroke & Topology Metrics

| Metric | Description | Confidence |
|---|---|---|
| Stroke-normalized L1 / RMSE | Accounts for rendering scheme impact on metric values | HIGH |
| Stroke Weight Similarity | Visual difference between adjacent weights (pixel units; differences as small as a few pixels) | HIGH |
| HOG difference + Stroke Width Similarity | Novel metrics for skeleton-based font generation | MEDIUM |
| Corner Consistency Loss / Elastic Mesh Feature Loss | Auxiliary losses optimizing discrete junction points and topological coherence | HIGH |
| HOG-Similarity, MS-SSIM | Shape similarity after glyph segmentation and alignment | MEDIUM |

Source: Smith #16 [as noted]

---

## 6F. Human Evaluation Protocol (2025–2026 Standard)

- 5-point Likert scale on 3 dimensions: Visual Fidelity, Stylistic Coherence, Usability | Smith #16 [HIGH]
- Blind evaluation with ≥5 years professional design experience + general users; identities anonymized | Smith #16 [HIGH]
- Sample size: 20 volunteers (standard per MX-Font++, DA-Font, others) | Smith #16 [HIGH]
- Bradley-Terry model for pairwise comparison aggregation | Smith #16 [MEDIUM]

---

## 6G. Concrete Benchmark Numbers from Specific Papers

| Paper | FID | SSIM | LPIPS | CD | Other |
|---|---|---|---|---|---|
| FontDiffuser (AAAI 2024) | 7.70 | 0.4682 | Best at hard level | — | — |
| VQ-Font (AAAI 2024, SFUC) | — | — | 0.096 | — | Better than CF-Font (0.111), FS-Font (0.126) |
| MX-Font++ (UFSC seen chars) | 103.94 | 0.689 | 0.201 | — | — |
| VecFusion (CVPR 2024) | — | — | — | 0.16 | L1=0.014, CP diff ±3.05 |
| DeepVecFont-v2 (CVPR 2023) | — | — | — | — | Error-EN 0.052, Error-CN 0.080 |

Sources: Smith #16 [HIGH], Smith #18 (FontDiffuser, VQ-Font), Smith #11 (VecFusion), Smith #12 (DeepVecFont-v2)

---

## 6H. Known Metric Limitations (Literature Consensus)

1. **No single metric captures both style fidelity AND character diversity** — quantitative scores plateau at high quality; human eval essential | Smith #16 [HIGH/2025]
2. **OCR and CLIP measure orthogonal aspects** — high OCR / low CLIP or vice versa are both possible failure modes | Smith #16 [HIGH/2026]
3. **Rendering scheme confounds L1/RMSE** — stroke-normalized variants needed | Smith #16 [HIGH/2025]
4. **No 2024–2026 paper benchmarks neural vectorization against traditional tracers** | Smith #11, #12 [HIGH — independent convergence]
5. **Subtle enhancements not well captured by standard metrics** — fine-grained details missed | Smith #16 [MEDIUM/2026]
6. **SWER (Subtle Weight Error Rate)** — typographically-weighted error metric; novel in GoogleFontsBench 2026 — not yet in broader use | Smith #17 [HIGH]

---

---

# SECTION 7: FONT STYLE EMBEDDINGS & SIMILARITY MODELS

**Primary source:** Smith #17

---

## 7A. Tier 1 — Best Available (July 2026)

**DINOv2 + LoRA (GoogleFontsBench, arXiv:2602.13889):**
- Date: April 3, 2026
- Accuracy: **99.0% top-1** on GoogleFontsBench | Smith #17 [HIGH — official paper v2]
- Architecture: DINOv2 ViT backbone (87.2M params); LoRA training only 1% of parameters
- Benchmark: 394 font variants, 32 Google Fonts families, 226K synthetic images (512×512px)
- Metric: SWER (typographically-weighted error rate); errors 140× less severe than random guessing
- Weights: PUBLIC — HuggingFace: dchen0/font-classifier-v3 | Smith #17 [HIGH]

**FontFusion (Dual DeepFont + DINOv2, arXiv:2606.06066):**
- Date: June 6, 2026
- Font Similarity Score: **0.885** (dual encoder) vs. 0.818 (DeepFont alone) | Smith #17 [HIGH]
- 76% relative improvement on decorative fonts; 68–76% font consistency gains over unconditioned baselines | Smith #17 [HIGH]
- Plug-and-play for Diffusion Transformer architectures without retraining | Smith #17 [HIGH]
- Code: Available | Smith #17 [HIGH]

---

## 7B. Tier 2 — Vision-Language Models

**FontCLIP (arXiv:2403.06453, EUROGRAPHICS 2024):**
- Architecture: CLIP backbone with compound descriptive prompts; typography-specific knowledge
- Capabilities: Multilingual (Roman, CJK); cross-lingual font retrieval
- Performance: Better pairwise similarity than base CLIP on cross-lingual task | Smith #17 [MEDIUM — qualitative, no numeric benchmark]
- Weights: PUBLIC | Smith #17 [HIGH]
- Date: March 2024

---

## 7C. Tier 3 — CNN / Specialized

**DeepFont (Legacy baseline, ~2015 ACM SIGGRAPH):**
- Accuracy: >80% top-5 on collected dataset | Smith #17 [MEDIUM — older data]
- Silhouette score: **0.76** | Smith #17 [HIGH]
- NN accuracy: **0.82** | Smith #17 [HIGH]
- Retrieval precision: **0.79** | Smith #17 [HIGH]
- Weights: Not widely publicly available | Smith #17 [HIGH]
- Note: DINOv2 silhouette 0.58 (FonTS paper) vs DeepFont 0.76 — DeepFont retains edge on fine-grained typographic clustering | Smith #17 [MEDIUM — derived from FonTS arXiv:2412.00136]

**Font-Identifier (ResNet18, gaborcselle/HF):**
- Accuracy: 96.33% on 48-font classification | Smith #17 [HIGH — model card]
- Architecture: Fine-tuned microsoft/resnet-18
- Dataset: gaborcselle/font-examples (1,500 fonts), 80/20 split
- Weights: PUBLIC — HuggingFace: gaborcselle/font-identifier | Smith #17 [HIGH]

---

## 7D. Contrastive / Metric Learning

**Paired-Glyph Matching (arXiv:2211.10967, BMVC 2022):**
- Metric learning: same-font glyphs together, different-fonts apart
- Mean Accuracy:
  - O'Donovan dataset: **89.91%** | Smith #17 [HIGH]
  - OFL dataset: **66.46%** | Smith #17 [HIGH]
- Code: PUBLIC (github.com/junhocho/paired-glyph-matching) | Smith #17 [HIGH]

**DS-Font (arXiv:2301.10008, January 2023):**
- First to explicitly model positive (same-style) and negative (different-style) relationships for few-shot font generation | Smith #17 [HIGH]
- Code: Available | Smith #17 [HIGH]

**FontDiffuser (arXiv:2312.12142, AAAI 2024):**
- Style Contrastive Refinement (SCR) module + Multi-scale Content Aggregation
- State-of-the-art on complex characters and large style changes | Smith #17 [MEDIUM — qualitative]
- Code: PUBLIC (github.com/yeungchenwa/FontDiffuser) | Smith #17 [HIGH]

---

## 7E. Transformer-Based (Vector Outline Encoding)

**TrueType Transformer (arXiv:2203.05338, DAS 2022):**
- Input: TrueType outline control points (resolution-independent)
- Advantage: Direct vector outline handling; fine stroke structures
- Numeric accuracy: Not reported | Smith #17 [LOW]
- Code: PUBLIC (github.com/uchidalab/TrueTypeTransformer) | Smith #17 [HIGH]

**Quantifying Character Similarity with ViT (arXiv:2305.14672, EMNLP 2023):**
- Application: Homoglyph detection (confusable characters: "0" vs "O"); multilingual (CJK + Roman)
- NOT a direct font-style similarity metric | Smith #17 [LOW on style clustering task]
- Weights: PUBLIC (github.com/dell-research-harvard/quantifying-character-similarity) | Smith #17 [HIGH]

---

## 7F. Benchmarks

**GoogleFontsBench (First Public Benchmark, April 2026):**
- Scale: 394 font variants, 32 families, ~226K synthetic images (512×512px)
- Metric: SWER (Subtle Weight Error Rate — typographically informed)
- PUBLIC release (benchmark + models + pipeline) | Smith #17 [HIGH]

**Font Recognition Benchmark (FRB) for VLMs (arXiv:2603.08497, 2025):**
- Coverage: 15 Latin fonts
- VLM performance: ~30% accuracy (easy); ~15% accuracy (hard/"Stroop" variant) | Smith #17 [HIGH]
- GPT-4O: ~15% on hard | Smith #17 [HIGH]
- Reveals significant typography gap in current VLMs | Smith #17 [HIGH]

---

## 7G. Summary Table

| Rank | Model | Primary Use | Public Weights | Key Metric | Date |
|---|---|---|---|---|---|
| 1 | DINOv2 + LoRA | Font classification | ✅ HF | 99.0% top-1 | Apr 2026 |
| 2 | FontFusion | Typography conditioning in diffusion | ✅ | 0.885 sim | Jun 2026 |
| 3 | FontCLIP | Multilingual font retrieval | ✅ | Qualitative | Mar 2024 |
| 4 | Paired-Glyph Matching | Font style transfer | ✅ | 89.91% MACC | Nov 2022 |
| 5 | DeepFont | Legacy clustering baseline | ⚠️ Limited | 0.76 silhouette | ~2015 |

Source: Smith #17 [HIGH on rankings/metrics]

---

---

# SECTION 8: FEW-SHOT FONT GENERATION / GLYPH COMPLETION

**Primary source:** Smith #18 | **Supporting:** Smith #12 (neural methods overlap), Smith #16 (shared metrics), Smith #17 (FontDiffuser, DS-Font overlap)

---

## 8A. Methods with Quantitative Metrics [HIGH confidence]

| Method | Venue | FID | SSIM | LPIPS | Notes |
|---|---|---|---|---|---|
| FontDiffuser | AAAI 2024 | **7.70** | **0.4682** | Best at hard level | Confirmed: Smith #16, #17, #18 |
| VQ-Font (SFUC) | AAAI 2024 | — | — | **0.096** | Better than CF-Font (0.111), FS-Font (0.126), DG-Font (0.127) |
| MX-Font++ (UFSC, seen) | 2025 | 103.94 | 0.689 | 0.201 | Cross-lingual; confirmed Smith #16 |

Source: Smith #18 [HIGH], cross-confirmed Smith #16

---

## 8B. All Documented Methods (2022–2026)

| Method | arXiv | Venue | Code | Latin Support | Primary Charset |
|---|---|---|---|---|---|
| VQ-Font | 2308.14018 | AAAI 2024 | ✓ Yaomingshuai/VQ-Font | Not specified | Chinese |
| CF-Font | 2303.14017 | CVPR 2023 | ✓ wangchi95/CF-Font | Not documented | Chinese |
| FontDiffuser | 2312.12142 | AAAI 2024 | ✓ yeungchenwa/FontDiffuser | Via -CL variant | Chinese (base) |
| FontDiffuser-CL | — | Feb 2026 | ✓ ra1nei/FontDiffuser-CL | YES (cross-lingual) | Multi |
| VecGlypher | 2602.21461 | CVPR 2026 | ⚑ DISPUTED | YES (multilingual) | Multi |
| DA-Font | 2509.16632 | ACM MM 2025 | ✓ wrchen2001/DA-Font | Chinese + English | Multi |
| Beyond Patches (GAR-Font) | 2601.01593 | 2026 | ✗ | YES (CJK + alphabetic) | Multi |
| SmartFont | 2606.13382 | — | ✗ | Unknown | Unknown |
| MX-Font++ | 2503.02799 | 2025 | ✗ | YES (Cyrillic, Latin) | Multi |
| One-Shot ViT | 2412.11342 | Dec 2024 | ✗ | LIKELY (multilingual design) | CJK + alphabetic |
| HFH-Font | 2410.06488 | TOG 2024 | ✗ | ✗ (Chinese specialized) | Chinese |
| Diff-Font | 2212.05895 | IJCV 2024 | — | ✗ | Chinese (410 fonts, 6625 chars) |
| QT-Font | — | SIGGRAPH 2024 | ✓ lsflyt-pku/QT-Font | Unknown | Unknown |
| DRG-Font | 2604.13797 | Apr 2026 | ✗ | YES (52 English) | Multi |
| Few-Part-Shot | 2509.10006 | ICDAR 2025 | — | Unknown | Unknown |
| InkDiffuser | 2605.05865 | May 2026 | — | ✗ | Chinese calligraphy |
| VecFusion | 2312.10540 | CVPR 2024 | ✓ | — | Multi (vector output) |
| GAS-NeXt | 2212.02886 | Dec 2022 | — | YES (Chinese↔Latin) | Multi |
| DK-Font | 2504.21325 | Apr 2025 | — | NO (Korean) | Hangul |
| FontFusion | 2606.06066 | Jun 2026 | ✓ | — | Multi (DiT conditioning) |
| SLD-Font | 2602.18874 | Feb 2026 | — | ✗ | Chinese |
| MA-Font | — | IEEE 2024 | — | YES (52 Latin + 1000 Chinese) | Multi |
| DP-Font | — | IJCAI 2024 | — | ✗ | Chinese calligraphy |
| CD-Font | — | ICIC 2024 | — | Unknown | Unknown |

Source: Smith #18 [HIGH for code availability and charset; LOW for quality claims without numerics]

---

## 8C. Latin Charset Support (Confirmed Instances)

| Method | Latin Detail | Source |
|---|---|---|
| MA-Font | 52 Latin letters + 1000 Chinese per font | IEEE 2024 |
| DRG-Font | 52 English + 993 Chinese | arXiv:2604.13797 |
| MX-Font++ | Cross-lingual Cyrillic + Latin | arXiv:2503.02799 |
| VecGlypher | Multilingual (39K Envato fonts) | arXiv:2602.21461 |
| GAS-NeXt | Chinese ↔ Latin translation | arXiv:2212.02886 |
| FontDiffuser-CL | Cross-lingual extension (Feb 2026) | github.com/ra1nei/FontDiffuser-CL |
| Beyond Patches | CJK + alphabetic scripts | arXiv:2601.01593 |

Source: Smith #18 [HIGH on documented instances]

**CJK-only (no Latin support confirmed):** FontDiffuser (base), Diff-Font, HFH-Font, DP-Font, InkDiffuser, SLD-Font | Smith #18 [HIGH]

---

## 8D. Key Trend Findings (Smith #18)

1. **Diffusion dominates 2024–2026:** FontDiffuser variants, Diff-Font, DRG-Font, DP-Font, InkDiffuser, QT-Font, CD-Font all use diffusion | Smith #18 [HIGH]
2. **Vector output emerging 2024+:** VecGlypher (LLM→SVG), VecFusion (cascaded diffusion→SVG) | Smith #18 [HIGH]
3. **CJK specialization still dominant:** ~60% of documented methods target Chinese | Smith #18 [HIGH]
4. **Multimodal trend 2025–2026:** Beyond Patches + SmartFont + VecGlypher integrate text conditioning | Smith #18 [HIGH]
5. **Publication velocity accelerating:** 23+ distinct methods 2024–2026 (vs ~5–10 annually pre-2024) | Smith #18 [HIGH]
6. **Few-Part-Shot (arXiv:2509.10006, ICDAR 2025):** Generates entire font from **partial shapes** — unique capability among reviewed methods | Smith #18 [HIGH]

---

---

# SECTION 9: AI FONT GENERATION PRODUCTS (COMMERCIAL)

**Primary source:** Smith #19

---

## 9A. Full TTF/OTF Font Generators

**Mixfont (mixfont.com):**
- Launch: May 20, 2026
- Output: TTF, 320+ glyphs (26+ languages, punctuation, symbols); vector-based, editable
- Input: Text prompts or reference images
- Pricing: FREE (3 generations); PRO $20/month (1,000 credits); MAX $200/month (5,000 credits); ENTERPRISE custom | Smith #19 [HIGH/July 2026]
- Commercial license: Included in PRO+ (resale/redistribution); NOT in free tier
- Quality notes: Production-ready for decorative/display fonts; known issues with kerning/spacing; curve quality visible at 84px+; "good enough for vast majority of use cases" | Smith #19 [HIGH — TypeDrawers discussion]

**Lipi.ai (lipi.ai):**
- Output: TTF, OTF, WOFF, WOFF2 (full working typeface: uppercase/lowercase/numerals/punctuation)
- Input: Text prompts, handwriting images, existing fonts
- Pricing: FREE (10 preview credits); commercial license $4.99/font; own outright $9.99/font | Smith #19 [HIGH/July 2026]
- Commercial license: Included with purchase
- Status: Production-ready, professional formats

**FontStruct (fontstruct.com):**
- Output: TTF (grid/brick-based construction)
- Pricing: FREE forever
- Input: Grid-based brick assembly
- Quality: Accessible for beginners; geometric/pixel-perfect | Smith #19 [HIGH/July 2026]

**Creative Fabrica (creativefabrica.com/tools/ai-font-generator/):**
- Output: TTF (trained on 100,000s of typefaces; diffusion-based with inter-elemental style consistency)
- Input: Prompts and/or image reference
- Pricing: $47/year (~$3.99/month) | Smith #19 [MEDIUM — bundle pricing varies]
- Commercial: Most assets include commercial POD licenses

---

## 9B. Image-Only Text Effects (NOT Installable Fonts)

**FontVibe (fontvibe.ai):**
- Output: JPG/PNG text effects ONLY; 100+ AI text styles (neon, 3D, cyberpunk, fire, etc.)
- Up to 4K resolution
- Pricing: FREE 200/month; STARTER $3.99 one-time (400 credits); GROWTH $9.99/month; EXPERT $24.99/month | Smith #19 [HIGH/July 2026]
- Commercial: Free on all tiers

**Refont AI (refont.ai):**
- Output: PNG/JPG images ONLY — "you'll be disappointed" if wanting installable fonts (explicit limitation) | Smith #19 [MEDIUM]
- Pricing: FREE limited credits + pay-per-credit

**Ideogram (ideogram.ai):**
- Output: Images with text (90–95% text accuracy); SVG export for designs (NOT fonts)
- 3× higher text accuracy than Midjourney/Stable Diffusion | Smith #19 [MEDIUM]
- Pricing: FREE 10/day; PLUS $15/month (annual); PRO $42/month

---

## 9C. Specialized Tools

**Fontself Maker (fontself.com) — Illustrator/Photoshop plugin:**
- Output: OTF/TTF/WOFF; auto-kerning/spacing; color fonts (SVG); ligatures
- Input: Vector artwork in Illustrator/Photoshop
- Pricing: $39 (Illustrator); $59 (bundle) | Smith #19 [HIGH/July 2026]
- Commercial: YES

**Calligraphr (calligraphr.com):**
- Output: SVG vector fonts (handwriting-specific)
- Input: Handwriting samples + text
- Pricing: CONFLICTING — free per some sources; ~$10/month per others | Smith #19 [MEDIUM]
- Trained on IAM Handwriting Database

**Skywork AI (skywork.ai):**
- Output: PNG/JPG high-resolution character sheets ONLY; users must trace/vectorize separately
- ~95% time savings claimed; requires post-processing to get a usable font | Smith #19 [MEDIUM]
- Pricing: FREE limited; ~$16–19.90/month; ~$149.99/year | Smith #19 [MEDIUM — ranges across sources]

**Prototypo (prototypo.io):**
- Output: Variable/parametric fonts (weight, width, x-height sliders)
- Pricing: NOT FOUND in 2026 public sources | Smith #19 [LOW]

---

## 9D. Quality Assessment Across Products (July 2026)

- **All AI generators require manual kerning/spacing refinement** for high-visibility use | Smith #19 [HIGH]
- **Curve quality visible at 84px+**; minimal at body text sizes | Smith #19 [HIGH]
- **Redundant anchor points common**; professional cleanup recommended in FontLab/Glyphs | Smith #19 [HIGH]
- VecGlypher (CVPR 2026) cited as evidence that vector-based generation outperforms raster/bitmap approaches for editability and quality | Smith #19 [MEDIUM]

---

---

# SECTION 10: PYTHON FONT ASSEMBLY TOOLCHAIN

**Primary source:** Smith #20 | **Supporting:** Smith #13 (hinting context), Smith #15 (validation tools)

---

## 10A. Core Library Stack

| Library | Role | Install |
|---|---|---|
| **fontTools** | Core: TTFont class, ttx, varLib, cu2qu, feaLib | PyPI: fonttools |
| **ufo2ft** | UFO → TTF/OTF bridge; compileTTF(), compileOTF(), compileVariableTTFs() | PyPI: ufo2ft |
| **ufoLib2** | Lightweight UFO v3 processor; JSON/MessagePack serialization; replaces defcon for batch ops | PyPI: ufoLib2 |
| **fontmake** | High-level CLI build tool; wraps ufo2ft | PyPI: fontmake |
| **cu2qu** | Cubic-to-quadratic conversion; embedded in ufo2ft workflow | PyPI: cu2qu |

Source: Smith #20 [HIGH throughout]

**fontmake CLI:**
```bash
fontmake -g file.glyphs -o variable ttf otf
fontmake -m design.designspace -o variable ttf otf
```
Source: Smith #20 [HIGH]

---

## 10B. cu2qu Conversion Details

- Default tolerance: **0.001 em** (perceptually imperceptible) | Smith #20 [HIGH]
- Conversion typically requires 2–4 quadratic segments per cubic | Smith #20 [HIGH]
- Point count increase: **20–35%** (TTF vs OTF for same outlines) | Smith #20 [HIGH]
- Mitigation for critical glyphs: Use tolerance ≤ 0.0005 em; inspect converted outlines visually | Smith #20 [MEDIUM]

---

## 10C. Required OpenType Tables

| Table | Purpose | Required |
|---|---|---|
| cmap | Character→glyph mapping | ✓ YES |
| glyf + loca | TrueType glyph outlines + index | ✓ TTF only |
| CFF / CFF2 | PostScript glyph outlines | ✓ OTF only |
| head | Font header (units/em, bbox, flags) | ✓ YES |
| hhea | Horizontal header (ascender, descender, line gap) | ✓ YES |
| hmtx | Horizontal metrics (glyph widths/LSB) | ✓ YES |
| maxp | Max profile (glyph/component limits) | ✓ YES |
| OS/2 | Metrics, weight, license type, Unicode ranges | ✓ YES |
| post | PostScript name, glyph format version | ✓ YES |
| name | Family, style, copyright, version strings | ✓ YES |
| GSUB | Glyph substitution (ligatures, alternates) | Optional (auto-gen via feature file) |
| GPOS | Glyph positioning (kerning, mark attachment) | Optional (auto-gen via feature writers) |
| GDEF | Glyph definitions (mark/base classification) | Optional (auto-gen) |

Source: Smith #20 [HIGH — ufo2ft + fontTools documentation]

---

## 10D. ufo2ft Feature Writers

Auto-generates:
- Kern feature (from UFO kerning data)
- Mark-to-base, mark-to-mark features (from UFO anchors)
- GDEF table (glyph categorization)

Manual option: `.fea` feature file compiled via `feaLib.builder` | Smith #20 [HIGH]

---

## 10E. WOFF2 Production

**Python:**
```python
from fontTools.ttLib import TTFont
font = TTFont('MyFont.ttf')
font.flavor = 'woff2'
font.save('MyFont.woff2')
# Requires: pip install fonttools[woff] brotli
```

**CLI:**
```bash
pyftsubset MyFont.ttf --flavor=woff2 --output-file=MyFont.woff2
# Subset:
pyftsubset MyFont.woff2 --unicodes=U+0020-007E,U+0100-0120 --output-file=subset.woff2
```

Source: Smith #20 [HIGH]

**Compression ratios (2025 data):**
| Format | Size vs TTF |
|---|---|
| TTF | 100% (baseline) |
| WOFF | ~70% |
| WOFF2 | **~32%** (~68% smaller than TTF) |

Source: Smith #20 [MEDIUM — font-converters.com 2025; actual ratios vary ±5–10% by font complexity]

---

## 10F. Composite Glyph Handling

- **TTF:** Composite glyphs preserved by default; saves file size, maintains dependencies | Smith #20 [HIGH]
- **OTF (CFF):** Composite glyphs **decomposed to paths on export** — CFF lacks composite format | Smith #20 [HIGH]
- **Pitfall:** Missing base component → composition fails silently or errors | Smith #20 [HIGH]

---

## 10G. Seven Pitfalls for Synthesized (Non-Hand-Drawn) Outlines

1. **Curve approximation loss:** cu2qu discretization error; undersample sharp peaks or oversample flat curves → use tolerance ≤ 0.0005 em for critical glyphs | Smith #20 [MEDIUM]

2. **Component dependency gaps:** Synthesized accented glyphs (é = e + acute) fail silently if base components missing → pre-validate glyph set | Smith #20 [HIGH]

3. **Composite decomposition in CFF:** All composites decomposed on OTF export; use TTF for synthesized fonts or design composites at UFO level before export | Smith #20 [HIGH]

4. **Hinting loss:** TrueType fonts edited post-generation have hinting discarded by fontTools; small-size rendering (≤12px) affected → generate final outlines in one pass; skip hinting for web delivery | Smith #20 [HIGH]

5. **Overlapping contours & self-intersections:** Common in ML-generated and raster-traced glyphs → run remove-overlaps (potrace, FontForge CLI, or skia-pathops) | Smith #20 [HIGH]

6. **Fractional coordinates:** Generated pipelines produce fractional coordinates (e.g., 123.456); TrueType glyf requires integers → round before assembly | Smith #20 [MEDIUM]

7. **Missing/incorrect metrics:** Synthesized glyphs may have zero width, incorrect bearings (LSB/RSB), or missing advance width → validate via `ttx -t hmtx font.ttf`; set UFO glyph width before compilation | Smith #20 [HIGH]

Source: Smith #20 [HIGH/MEDIUM as noted]

---

---

# CORRECTIONS

**#1 — Potrace curve type (Smith #11):**
Smith #11 states "Quadratic Bézier (straight segments), cubic Bézier (corners)" as Potrace's curve type. This description is confused. Potrace's algorithm uses **cubic Bézier curves** as its primary output curve type, with straight line segments for short runs — straight segments are not a type of Bézier curve. The "quadratic" description appears to be an error in Smith #11's reporting. This does not affect the tool's quality assessment or production ranking. [Basis: Standard potrace algorithm documentation; cross-check against Smith #12 which correctly uses Potrace as a cubic Bézier baseline]

**#2 — Potrace licensing specificity (Smith #11):**
Smith #11 states "GPLv2 or later" — this is correct per the README. No correction needed; confirming [HIGH].

**#3 — Smith #11 FID claim for VecGlypher:**
Smith #11 states "97.8% lower FID" for VecGlypher vs. baselines. This is an unusually large improvement (nearly eliminating FID gap). The claim is sourced [HIGH from arXiv:2602.21461] and not contradicted elsewhere, but Opus should treat this single-paper figure with appropriate caution — percent-reduction claims on FID are sensitive to baseline choice.

**#4 — Calligraphr pricing (Smith #19):**
Smith #19 reports conflicting pricing for Calligraphr: "FREE or ~$10/month (conflicting sources; most recent: free Feb 2026)." This is an unresolved inconsistency within Smith #19 itself. Confidence: MEDIUM. Opus should treat pricing as uncertain and recommend direct verification.

---

---

# DISPUTES

**⚑ DISPUTE #1 — Potrace vs. VTracer as Production Vectorizer**

| Source | Position |
|---|---|
| Memory (predates Chain B) | "Potrace CLI + 4x preprocess is the production vectorizer, smoother than scikit-image" |
| Smith #11 (2026) | VTracer is strongest production choice; Potrace "outdated for font work"; hybrid Potrace+4x "not recommended for new projects" |

**Nature of dispute:** Memory note documents a *prior project decision* (Potrace + preprocessing as the chosen approach). Smith #11 represents *current research consensus* that VTracer outperforms Potrace for font work overall. These may not contradict — the memory note compares Potrace to scikit-image (not to VTracer), and Smith #11's hybrid Potrace approach is acknowledged as "acceptable if optimized." However, Smith #11 explicitly deprioritizes it vs. VTracer. **Recency rule favors Smith #11.** Recommend Opus reconcile against the feedback note [Potrace Quality] in MEMORY.md.

---

**⚑ DISPUTE #2 — VecGlypher Code Availability**

| Source | Position |
|---|---|
| Smith #12 (dedicated neural vectorization report) | "Code Status: ✓ Released — https://github.com/xk-huang/VecGlypher" |
| Smith #18 (few-shot font generation report) | "Code: Not yet public; project page: xk-huang.github.io/VecGlypher" |

**Nature of dispute:** Both Smiths are contemporaneous (Chain B search, July 2026). Smith #12 explicitly lists the GitHub URL with ✓; Smith #18 marks it as pending. Could reflect a time-of-search difference (code released between the two searches) or one Smith miscategorized. The GitHub URL is specific and cited by Smith #12. **Tentative resolution: Code released as of Chain B.** Opus should verify before treating as public release.

---

**⚑ DISPUTE #3 — VecGlypher vs. Ref2Font (Memory vs. Smith #11)**

| Source | Position |
|---|---|
| Memory (Ref2Font Wins) | "FLUX.2 + Ref2Font is the primary approach, beats VecGlypher on all fronts" |
| Smith #11 | VecGlypher has "highest quality for glyph-specific tasks"; direct generation, 2× R-ACC, 92% lower CD |
| Smith #12 | VecGlypher "substantially outperforms" specialized baselines |

**Nature of dispute:** GENUINE DISPUTE. Memory is a prior project-level judgment (based on project-specific evaluation); Smiths report published benchmark results. Critically, **Ref2Font appears nowhere in Chain B** — no Smith covers it. The comparison cannot be resolved from Chain B alone. Recommend Opus treat this as a Chain A/Chain B gap requiring dedicated Ref2Font coverage or reconciliation against memory note [Ref2Font Wins].

---

**⚑ DISPUTE #4 — DINOv2 for Typographic Classification**

| Source | Context | Result |
|---|---|---|
| Smith #17 (DINOv2 + LoRA on GoogleFontsBench) | Font family classification | **99.0% top-1** |
| Smith #17 (FonTS paper, arXiv:2412.00136) | Font conditioning quality in text-to-image | DINOv2 silhouette **0.58** vs DeepFont **0.76** |

**Nature of dispute:** NOT a genuine contradiction — these measure different tasks. 99.0% is font *family identification* (classification task, binary correct/wrong). 0.58 silhouette is *fine-grained typographic clustering quality* (continuous space). DeepFont (0.76) retains edge on clustering coherence despite DINOv2's superior classification accuracy. **Not flagged as unresolved** — document both for Opus as task-dependent performance.

---

---

# GAPS

### G1 — Ref2Font Coverage (Critical)
No Smith in Chain B covers Ref2Font or the FLUX.2 + Ref2Font pipeline. Memory note calls it "the primary approach, beats VecGlypher on all fronts." This is the largest gap relative to the project's declared primary method. **Action: Dedicated Ref2Font Smith required.**

### G2 — No Neural-vs-Traditional Vectorizer Benchmark
Confirmed independently by Smith #11 and Smith #12: no 2024–2026 paper quantitatively benchmarks neural vectorization methods (VecFusion, VecGlypher, etc.) against traditional CLI tracers (potrace, VTracer, AutoTrace). Gap is in the literature itself, not just in Chain B. **Action: If pipeline benchmarks are needed, team must run original comparison.**

### G3 — Full-Charset Coverage Standards
Most few-shot methods address representative subsets (English ~52–250 glyphs, CJK subsets). GB18030-2000's 27,533 characters and similar large charsets are not addressed in Chain B. Unicode coverage requirements (minimum sets for web/OS fonts) not covered. **Action: May need dedicated Unicode/charset coverage Smith.**

### G4 — OpenType Layout Features (GSUB/GPOS)
Smith #20 documents table structure and ufo2ft feature writers but does not cover the *design* of OpenType features: ligatures, stylistic sets, contextual alternates, mark positioning. No Smith covers `.fea` feature code design or testing for synthesized fonts.

### G5 — Variable Font Generation Pipeline (End-to-End)
NIV (Smith #12) and varLib (Smith #20) are mentioned, but no Smith covers an end-to-end variable font *generation* pipeline: axis design, designspace construction, interpolation compatibility checking, instance naming, STAT table. Smith #13 covers variable font *hinting* limitations only.

### G6 — Font Licensing / Legal Framework
Smith #19 touches on commercial licenses for products (Mixfont, Lipi.ai), but no Smith covers SIL OFL, Apache font licenses, or licensing considerations for synthesized fonts derived from training data. Memory note [Base Model Licensing] flags the klein-9B non-commercial issue but Chain B doesn't expand on this.

### G7 — CJK Stroke Order Databases
Smith #18 covers CJK font generation broadly, but no Smith addresses stroke order databases (KangXi, Unihan, cnchar, etc.), stroke decomposition standards, or how CJK glyph synthesis differs architecturally from Latin synthesis.

### G8 — Subsetting Strategy for Production Deployment
Smith #20 mentions `pyftsubset` in passing. No Smith covers subsetting strategy: Unicode range selection, text-based subsetting, Google Fonts subsetting protocol, or how to maintain proper cmap entries post-subset.

### G9 — Intermediate Format: Glyph → UFO
Smith #20 assumes glyphs are already in UFO format. No Smith covers the step *before* — how synthesized raster or vector glyph outputs are converted into well-formed UFO `.glif` files with correct anchors, components, and contour winding direction, ready for fontmake ingestion.

### G10 — Fontspector CLI Documentation
Smith #15 explicitly notes: "MEDIUM confidence — precise syntax not yet verified from official docs; README is authoritative source." Fontspector is the recommended frontline validator but its CLI is incompletely documented within Chain B.

---

---

# CROSS-THEME CONNECTIONS (For Opus Synthesis)

1. **VecGlypher threads:** Referenced in Smith #11 (vectorization quality), #12 (neural methods), #14 (does NOT handle kerning), #16 (R-ACC/CD/FID metrics), #17 (embedding: not benchmarked), #18 (few-shot: code disputed), #19 (quality context) — highest cross-Smith presence of any single model.

2. **FontDiffuser threads:** Smith #17 (architecture/SCR module), #18 (FID 7.70, SSIM 0.4682 — highest specific benchmark), #16 (metrics table) — metrics confirmed across 3 Smiths [HIGH compound confidence].

3. **fontTools as common substrate:** Smith #13 (hinting), #15 (validation/ttx), #20 (assembly) all depend on fontTools. Version 4.34.4+ is consistent across all three Smiths [HIGH].

4. **"No metrics gap" between neural generation and traditional tracers:** Independent convergence of Smith #11 + Smith #12 on this gap. Also consistent with Smith #16 (metrics exist for neural-vs-neural but not neural-vs-traditional).

5. **Synthesis pipeline dependency chain:** Glyph generation (Section 2/8) → vectorization if needed (Section 1) → spacing/kerning (Section 4) → hinting (Section 3) → assembly (Section 10) → validation (Section 5). Chain B covers each stage, with largest gap at the glyph→UFO handoff (Gap G9).

---

*Chain B Structured Findings complete. 10 Smiths processed. All unique signal preserved. Opus synthesis ready.*

---
**Oracle SDK Execution Metrics**
- Architecture: 20 Smiths -> 2 Andersons -> Opus (you)
- Total time: 811s
- Total tokens: 214,833 (in: 47,146 | out: 167,687)
- Quota: 0.41% weekly (3.1% session)
- Smiths: 20 (0 errors)
- Andersons: 2 (0 errors)
- Phase timing: scout: 260s | compress: 551s
- Phase costs: decompose: 0.00% | scout: 0.16% | compress: 0.25%

