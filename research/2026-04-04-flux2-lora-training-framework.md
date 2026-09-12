Oracle SDK v4.2 -- 50 Smiths -> 5 Andersons -> Opus (you)
  [oracle] Phase 1/2 -- Smiths (50 Haiku, all parallel)
  [oracle]   Smith #28 (C/AdamW8bit optimizer) done [46.7s, 49 left]
  [oracle]   Smith #3 (A/FLUX2 prepare IDs) done [53.0s, 48 left]
  [oracle]   Smith #2 (A/FLUX2 latent unpacking) done [57.7s, 47 left]
  [oracle]   Smith #1 (A/FLUX2 latent packing) done [61.1s, 46 left]
  [oracle]   Smith #4 (A/FLUX2 transformer forward) done [61.1s, 45 left]
  [oracle]   Smith #29 (C/EMA for LoRA) done [61.8s, 44 left]
  [oracle]   Smith #39 (D/LoRA inference loading) done [62.5s, 43 left]
  [oracle]   Smith #38 (D/LoRA weight merging) done [65.5s, 42 left]
  [oracle]   Smith #19 (B/kohya FLUX2 training) done [67.2s, 41 left]
  [oracle]   Smith #7 (A/FLUX2 Klein scheduler) done [68.3s, 40 left]
  [oracle]   Smith #37 (D/training convergence metrics) done [69.2s, 39 left]
  [oracle]   Smith #21 (C/peft FLUX2 LoRA) done [74.3s, 38 left]
  [oracle]   Smith #30 (C/caption dropout) done [75.6s, 37 left]
  [oracle]   Smith #43 (E/Windows training issues) done [78.3s, 36 left]
  [oracle]   Smith #23 (C/flow matching timestep sampling) done [85.0s, 35 left]
  [oracle]   Smith #36 (D/training data augmentation) done [86.0s, 34 left]
  [oracle]   Smith #8 (A/FLUX2 Klein no guidance) done [86.1s, 33 left]
  [oracle]   Smith #50 (E/mixed precision training) done [89.2s, 32 left]
  [oracle]   Smith #34 (D/IP-Adapter training) done [91.0s, 31 left]
  [oracle]   Smith #46 (E/validation during training) done [91.3s, 30 left]
  [oracle]   Smith #22 (C/flow matching theory) done [91.4s, 29 left]
  [oracle]   Smith #5 (A/FLUX2 VAE encode) done [91.6s, 28 left]
  [oracle]   Smith #12 (B/DiffSynth trainer class) done [91.7s, 27 left]
  [oracle]   Smith #40 (D/multi-resolution training) done [93.2s, 26 left]
  [oracle]   Smith #41 (E/batch size vs accum) done [94.8s, 25 left]
  [oracle]   Smith #48 (E/dataset size scaling) done [97.6s, 24 left]
  [oracle]   Smith #18 (B/SimpleTuner latent prep) done [97.8s, 23 left]
  [oracle]   Smith #9 (A/diffusers FLUX1 train script) done [99.3s, 22 left]
  [oracle]   Smith #47 (E/LoRA to safetensors) done [100.3s, 21 left]
  [oracle]   Smith #26 (C/gradient checkpointing FLUX) done [100.3s, 20 left]
  [oracle]   Smith #14 (B/ai-toolkit training loop) done [101.6s, 19 left]
  [oracle]   Smith #17 (B/SimpleTuner flow matching) done [102.1s, 18 left]
  [oracle]   Smith #10 (A/diffusers FLUX1 loss) done [102.4s, 17 left]
  [oracle]   Smith #16 (B/SimpleTuner FLUX2 trainer) done [116.1s, 16 left]
  [oracle]   Smith #33 (D/contextual LoRA training) done [116.2s, 15 left]
  [oracle]   Smith #27 (C/INT8 quantized training) done [117.6s, 14 left]
  [oracle]   Smith #45 (E/save and resume) done [118.6s, 13 left]
  [oracle]   Smith #15 (B/ai-toolkit latent caching) done [119.9s, 12 left]
  [oracle]   Smith #35 (D/Ref2Font architecture) done [120.6s, 11 left]
  [oracle]   Smith #31 (D/FLUX.2 text encoder) done [121.3s, 10 left]
  [oracle]   Smith #32 (D/FLUX.2 text encoding details) done [121.4s, 9 left]
  [oracle]   Smith #49 (E/FLUX.2 pixel shuffle) done [131.5s, 8 left]
  [oracle]   Smith #24 (C/FLUX LoRA rank selection) done [137.3s, 7 left]
  [oracle]   Smith #20 (B/kohya network module) done [147.4s, 6 left]
  [oracle]   Smith #25 (C/FLUX LoRA learning rate) done [149.7s, 5 left]
  [oracle]   Smith #44 (E/training speed benchmarks) done [158.7s, 4 left]
  [oracle]   Smith #6 (A/FLUX2 VAE config) done [162.9s, 3 left]
  [oracle]   Smith #13 (B/ai-toolkit FLUX2 support) done [173.1s, 2 left]
  [oracle]   Smith #11 (B/DiffSynth FLUX2 training) done [191.9s, 1 left]
  [oracle]   Smith #42 (RTX 3090 VRAM budget) TIMEOUT [360s, 0 left]
  [oracle]   50 Smiths returned (360.2s), 1 errors | 283,152 tok (0.26% weekly)
  [oracle] Phase 2/2 -- Anderson (5 parallel Sonnet)
  [oracle]   Truncated 3 Smiths to 5505 chars (total cap 50000)
  [oracle]   Truncated 4 Smiths to 4950 chars (total cap 50000)
  [oracle]   Truncated 7 Smiths to 4950 chars (total cap 50000)
  [oracle]   Truncated 3 Smiths to 4950 chars (total cap 50000)
  [oracle]   Truncated 1 Smiths to 4950 chars (total cap 50000)
  [oracle]   Anderson B done (247.1s) | 14,168 tok (0.08% weekly)
  [oracle]   Anderson C done (261.0s) | 12,949 tok (0.08% weekly)
  [oracle]   Anderson A done (258.1s) | 15,115 tok (0.09% weekly)
  [oracle]   Anderson E done (299.0s) | 15,241 tok (0.09% weekly)
  [oracle]   Anderson D done (324.5s) | 17,451 tok (0.10% weekly)
  [oracle]   5 Andersons returned (329.5s) | 74,924 tok (0.45% weekly)
============================================================
## Chain E — Anderson Report
============================================================

# Chain E — Organized Findings for Opus Synthesis

---

## STATUS SUMMARY

| # | Topic | Status | Confidence Profile | Data Range |
|---|-------|--------|--------------------|------------|
| #41 | Batch size vs grad accum | ✅ | HIGH across | 2024–2026 |
| #42 | RTX 3090 VRAM budget | ❌ ERRORED (360s timeout) | — | — |
| #43 | Windows training issues | ✅ | HIGH / LOW on xFormers % | 2021–2026 |
| #44 | Training speed benchmarks | ✅ | HIGH (1024px), LOW (1280px est.) | 2025 |
| #45 | Save & resume | ✅ | HIGH across | 2026-04-02 |
| #46 | Validation during training | ✅ | HIGH (inference), MEDIUM (freq.) | 2025–2026 |
| #47 | LoRA to safetensors | ✅ | HIGH across | 2024–2025 |
| #48 | Dataset size scaling | ✅ | HIGH (small-set), MEDIUM (formulas) | 2024–2026 |
| #49 | FLUX.2 VAE / pixel shuffle | ✅ | HIGH (source code, 2026-04-04) | 2026-04-04 |
| #50 | Mixed precision | ✅ | HIGH across | 2025–2026 |

**9 usable / 1 errored. All 9 fully preserved below.**

---

## THEME 1: Hardware Configuration & VRAM Management

---

### 1A. Batch Size vs. Gradient Accumulation on 24GB GPUs
**Sources: Smith #41 (primary), Smith #43 (DDP memory bloat)**

**Top-line recommendation (HIGH confidence, Smith #41):**
`batch_size=2, grad_accum=2` is superior to `batch_size=1, grad_accum=4` for 24GB GPU LoRA training in most cases.

**Governing principle (HIGH confidence, Smith #41):**
- Activation memory scales **linearly with batch size**, not with gradient accumulation steps
- Both configs achieve **effective batch size = 4** — the same statistical target
- `batch=2, grad_accum=2` is ~**2× faster** wall-clock: 24 sec effective per iteration vs. 96 sec

**VRAM estimates for FLUX on RTX 4090 / 24GB class (Smith #41):**

| Config | Activation Memory | Approx. VRAM |
|--------|------------------|--------------|
| batch=1, grad_accum=4 | 1× baseline | ~18–26 GB |
| batch=2, grad_accum=2 | 2× baseline | ~20–28 GB |

**SimpleTuner per-tier guidance (HIGH confidence, Smith #41):**
- `batch_size=2`: 16GB+ cards, bf16 precision
- `batch_size=4`: 24GB+ (if headroom permits)
- With `--gradient_checkpointing` + bf16: batch_size=2 fits comfortably on 24GB
- With int8-bnb quantization: batch_size=4 possible at ~18GB

**Gradient accumulation overhead — quoted verbatim (HIGH confidence, Smith #41):**
> SimpleTuner FLUX.md: "gradient_accumulation_steps=2 will make your training run half as quickly, and take twice as long."

**Small-batch accumulation inefficiency (MEDIUM confidence — preprint, Smith #41):**
- arXiv 2507.07101: grad accum for very small batches may be "wasteful" in computation

**DDP-specific memory bloat (HIGH confidence, Smith #43):**
- Memory can **nearly double** after wrapping model with `DistributedDataParallel` vs. non-DDP baseline
- Non-primary GPUs incorrectly allocate memory on GPU 0 even with correct device placement
- Root cause: `find_unused_parameters=True` clones all output tensors
- Fix: `DistributedDataParallel(model, find_unused_parameters=False)`

**Fallback rule (Smith #41):** Only drop to batch_size=1, grad_accum=4 if OOM with batch_size=2.

---

### 1B. RTX 3090 VRAM Budget
**⚠️ CRITICAL GAP — Smith #42 ERRORED (timed out at 360s)**

- VRAM consumption figures specific to RTX 3090 are **entirely missing** from this chain
- Smith #41 provides generic 24GB estimates; Smith #44 provides speed data only
- **Action required:** Re-run Smith #42, or pull from prior-chain data (21 prior rounds in memory)

---

### 1C. Training Speed Benchmarks — RTX 3090
**Source: Smith #44 (all figures)**

**At 1024×1024 — unquantized (HIGH confidence, Smith #44):**
- **4–5 sec/step** — RTX 3090 FLUX LoRA baseline (multiple 2025 training tutorials)
- **720–900 steps/hour** at this rate
- **~3.5 sec/step** — RTX 4090 at 1280×1280 (reference point)

**At 1280×1280 on RTX 3090 — NO direct benchmark published (LOW confidence, Smith #44):**
- Estimate: **~9–10 sec/step** — extrapolated from 4090 data (1280×1280 is ~2.5× slower than 1024×1024 on 4090)
- ⚠️ See **CORRECTION C1** — the intermediate A6000 data point is not a valid proxy for 3090

**With Quanto int8 quantization (MEDIUM confidence, Smith #44 — SimpleTuner docs):**
- **1.0–1.5 steps/sec** (3,600–5,400 steps/hour)

**Projected total time for 5,000 steps (Smith #44):**

| Scenario | sec/step | Estimated Total | Confidence |
|----------|----------|-----------------|------------|
| Unquantized, 1024×1024 | 4–5 | 5.5–6.9 hrs | MEDIUM |
| Unquantized, 1280×1280 (3090 est.) | ~9–10 | ~13.8–13.9 hrs | LOW |
| Quanto int8 | 0.67–1.0 | 1.4–1.7 hrs | MEDIUM |

---

## THEME 2: Training Configuration

---

### 2A. Mixed Precision: BF16 Base + fp32 LoRA
**Source: Smith #50 (primary), Smith #41 (supplementary — references bf16 throughout)**

**LoRA weight precision default (HIGH confidence, Smith #50 — PEFT v0.12.0+):**
- LoRA adapter weights stored in **fp32 by default** even when base model is loaded in bf16/fp16
- Forward pass sequence: input arrives bf16 → PEFT upcasts to fp32 → LoRA A/B compute in fp32 → result downcast to bf16
- Override: `autocast_adapter_dtype=False` in `get_peft_model()` — not recommended

**Stability consequences of forcing bf16 adapters (HIGH confidence, Smith #50):**
- Risk of `grad_norm: nan` and `loss: inf` on first steps
- BF16 adapters require higher learning rate (reduced precision demands more aggressive steps)

**Autocast interaction rules (HIGH confidence, Smith #50):**
- `torch.autocast` should wrap **forward pass + loss computation only** — NOT backward pass
- PEFT's automatic fp32 promotion persists even inside `autocast(dtype=torch.bfloat16)` (PR #2433)
- Documented conflict: autocast regions receive unexpected dtypes; works fine with LoRA/PEFT disabled (issue #971)
- `disable_input_dtype_casting()` context manager available if conflict arises (MEDIUM confidence — inferred from API)

**Gradient accumulation + mixed precision (MEDIUM confidence, Smith #50 — derived):**
- fp32 LoRA master weights accumulate gradients in fp32 → stable gradient flow across accumulation steps

**FLUX-specific recommendations (HIGH confidence, Smith #50):**
- BF16 is standard for FLUX LoRA on RTX 30-series and newer
- BF16 requires **no loss scaling** — fp32-like exponent range prevents overflow (unlike FP16)
- Recommended combination: bf16 mixed precision + AdamW8bit optimizer + fp32 LoRA adapters (MEDIUM confidence — synthesized from guides)

---

### 2B. Dataset Size & Step Scaling for FLUX LoRA
**Source: Smith #48 (primary)**

**Top-line consensus across all FLUX guides (HIGH confidence, Smith #48):**
- Optimal: **10–50 images** — no FLUX-specific guide advocates 1000+ image datasets
- Quality dominates quantity: 16 carefully curated images **outperformed 110 mediocre images** empirically (Civitai post-mortem, 2025)
- Empirical convergence data (GitHub #1492, kohya-ss, HIGH confidence): 140-image dataset → loss ~0.38; 12-image dataset → loss ~0.08

**Step scaling formula (MEDIUM confidence, Smith #48 — Shakker AI / Kohya):**
```
total_steps = (dataset_size × repeats × epochs) / batch_size
```

**Empirical mapping table (MEDIUM confidence, Smith #48):**

| Dataset Size | Repeats | Epochs | Target Steps | Notes |
|---|---|---|---|---|
| 10–20 images | 3–5 | 20–40 | 1,000–2,000 | High exposure per image |
| 20–50 images | 2–3 | 15–30 | 1,500–3,000 | Optimal FLUX range |
| 50–100 images | 1–2 | 10–20 | 2,000–4,000 | Fewer repeats needed |
| 100+ images | 1 | 5–15 | 2,500–5,000 | Minimal repetition |

**Task-specific step targets (Smith #48):**

| Task | Images | Step Range | Confidence | Notes |
|------|--------|-----------|------------|-------|
| Style LoRA | 20–30 | 1,000–1,500 preferred | HIGH (fal.ai 2025) | 2000+ risks prompt adherence |
| Style LoRA | 20–30 | 3,000 | MEDIUM (Civitai) | Often optimal convergence |
| Character LoRA | 25–30 | 3,000–8,000 | MEDIUM (Civitai 2025) | Final 2,500–3,000 typically best |
| General heuristic | any | 50–75 steps/image | MEDIUM | At LR 1e-4 to 5e-4 |

**500-image case — convergence warning (HIGH confidence, Smith #48 — GitHub #1492):**
- Sits in "awkward middle zone": computationally expensive without proportional quality gain
- Scaling to 3,000 images required "substantial resources" with "slow convergence"
- Likely requires multi-GPU or extended training duration

**Overfitting risk factors (Smith #48):**
- Excessive repeats (>5): causes memorization — HIGH confidence, universal across guides
- Multiple epochs on small datasets: performance degradation documented — MEDIUM confidence
- Rank-to-data mismatch: excess capacity → memorization

**Rank guidance by dataset size (MEDIUM confidence, Smith #48 — Brenndoerfer 2026):**

| Dataset | Recommended Rank | Dropout |
|---------|-----------------|---------|
| <500 images | 4–8 | 0.1 |
| 1,000–5,000 images | 8–16 | — |
| 10,000+ images | 32–64 | — |

**Learning rates by task (HIGH confidence, Smith #48 — Civitai 2025):**
- Style LoRA: **1.5e-4**
- Character LoRA: **2.5e-5** (significantly lower)

**Mitigation strategies (Smith #48):**
- Save checkpoints every 250 steps — HIGH confidence
- Optimal convergence often appears before max steps — MEDIUM confidence
- Dual captioning: (1) detailed description + trigger; (2) trigger only → weakens subject-style lock, allows longer training without degradation — MEDIUM confidence (fal.ai 2025)
- LoRA+: `loraplus_unet_lr_ratio=4` may speed convergence on multi-GPU — MEDIUM confidence (kohya-ss 2025, anecdotal but authoritative)

---

## THEME 3: Checkpointing & Training Resume

---

### 3A. What to Save and How to Resume
**Source: Smith #45**

**Four required components for true training resumption (HIGH confidence, Smith #45):**
1. **LoRA weights** — `model.save_pretrained(path)` → `adapter_config.json` + `adapter_model.safetensors` (~6–50MB)
2. **Optimizer state** — `torch.save(optimizer.state_dict(), path)` (momentum buffers, LR schedule metadata)
3. **Scheduler state** — `torch.save(scheduler.state_dict(), path)` (current step counts, warmup progress)
4. **Global step count** — critical; scheduler restarts from zero if not restored

**Key caveat (HIGH confidence, Smith #45):**
> PEFT's `save_pretrained()` saves **only adapter weights** (~0.19% of model params). Optimizer and scheduler must be saved separately for true resumption.

**HuggingFace Trainer auto-saves all four (HIGH confidence, Smith #45):**
- `pytorch_model.bin` or adapter weights
- `optimizer.pt`
- `scheduler.pt`
- `trainer_state.json` (global_step, best_model_checkpoint, etc.)

**Trainer resume patterns (HIGH confidence, Smith #45):**
```python
trainer.train(resume_from_checkpoint=True)          # loads last checkpoint in output_dir
trainer.train(resume_from_checkpoint="./checkpoint/checkpoint-1000")  # specific path
```

**Manual loop resume (HIGH confidence, Smith #45):**
```python
model = get_peft_model(base_model, peft_config)
# Load LoRA weights
checkpoint = torch.load('lora_checkpoint_1000/pytorch_model.bin')
model.load_state_dict(checkpoint)
# Restore optimizer, scheduler, step
training_state = torch.load('lora_checkpoint_1000/training_state.pt')
optimizer.load_state_dict(training_state['optimizer_state_dict'])
scheduler.load_state_dict(training_state['scheduler_state_dict'])
global_step = training_state['global_step']
```

**Critical ordering requirement (HIGH confidence, Smith #45):**
- Must restore `global_step` **before** first `scheduler.step()` call — else scheduler restarts from warmup
- `ignore_data_skip` in TrainingArguments controls whether already-processed batches are skipped on resume

**Distributed training (Smith #45):** Trainer + Accelerate handle distributed checkpointing automatically; no extra handling needed.

---

## THEME 4: Validation & Inference During Training

---

### 4A. Validation Approach & Merge Requirements
**Sources: Smith #46 (primary), Smith #48 (supplementary — step interval)**

**No merge required for validation (HIGH confidence, Smith #46 + HF docs):**
- Validation loads LoRA adapters directly — `pipeline.load_lora_weights(path)` then run inference
- Standard CLI pattern: `--validation_prompt` + `--num_validation_images` + `--validation_epochs N`
- Merge (`fuse_lora()` / `merge_and_unload()`) is optional and only for post-training production deployment

**Validation loop sequence (HIGH confidence, Smith #46):**
1. Pause training at specified interval
2. Load current checkpoint LoRA into base pipeline
3. Run `pipeline(validation_prompt)` × N images
4. Save images to disk for visual inspection
5. Resume training with updated weights

**Validation frequency for FLUX:**
- Smith #46: Every 100–250 steps (MEDIUM confidence — derived from Gabeci 2026)
- Smith #48: Save every 250 steps (HIGH confidence)
- **→ AGREE:** Both sources converge on ~250-step cadence (see Agreement A4)

**Why FLUX needs earlier/more frequent validation (HIGH confidence, Smith #46):**
- FLUX LR range: 0.001–0.004 (vs. SDXL's 0.0001–0.0003) → drift visible sooner
- FLUX total steps: 500–1,500 (vs. SDXL's 2,000–5,000+) → validation samples are a higher fraction of total run

**Inference overhead comparison (HIGH confidence, Smith #46):**

| Mode | Throughput Cost | Tradeoff |
|------|----------------|----------|
| Unmerged LoRA | ~12% overhead/layer pair | Can swap/stack multiple LoRAs |
| Merged/fused | Zero overhead | Loses multi-LoRA flexibility |

**Merge APIs (HIGH confidence, Smith #46):**
- PEFT: `model.merge_and_unload()` → returns base model with LoRA permanently fused
- Diffusers: `pipeline.fuse_lora(lora_scale=1.0)` + `pipeline.unload_lora_weights()` → use with `torch.compile`

---

## THEME 5: Output Formats & Conversion

---

### 5A. LoRA Checkpoint Formats & Conversion Paths
**Source: Smith #47**

**PEFT checkpoint structure (HIGH confidence, Smith #47):**
- `adapter_model.safetensors` — adapter weights only (lora_A, lora_B matrices); NOT base model
- `adapter_config.json` — target modules, rank, alpha, peft_type, etc.
- Size example: ~260KB adapter vs ~420MB full BERT

**Framework key format differences (HIGH confidence, Smith #47):**

| Framework | Key Format | Example |
|-----------|-----------|---------|
| PEFT | `base_model.model.<layer>.lora_A.default.weight` | Transformers wrapper |
| Diffusers | `unet.down_blocks.0.attentions.0...to_q.lora.up.weight` | Model-agnostic paths |
| ComfyUI | `diffusion_model.<layer>` | Framework-specific prefix |

**SimpleTuner output (HIGH confidence, Smith #47 — Apatero blog 2025):**
- Default output: **`pytorch_lora_weights.safetensors`** in Diffusers format
- No conversion needed for Diffusers usage — load directly with `load_lora_weights()`
- Includes `export_comfyui.py` for ComfyUI conversion (MEDIUM confidence)

**Manual conversion paths (Smith #47):**

PEFT → Diffusers:
```python
# Strip "base_model.model." prefix and ".default" adapter name
new_key = key.replace("base_model.model.", "").replace(".default", "")
# Save as pytorch_lora_weights.safetensors
```

PEFT → ComfyUI:
```python
# Replace prefix, strip .default
new_key = key.replace("base_model.model.", "diffusion_model.")
new_key = new_key.replace(".default", "")
# Place in: ComfyUI/models/loras/
```

**Recommended path for SimpleTuner + base-9B setup (Smith #47):**
1. Diffusers: output already compatible, load directly
2. ComfyUI: run `export_comfyui.py` or manually rename keys
3. PEFT two-file format only needed if continuing PEFT-based training; single-file preferred for inference

---

## THEME 6: Platform-Specific Issues (Windows)

---

### 6A. Windows Training Constraints
**Source: Smith #43**

**NCCL — Linux-only (HIGH confidence, Smith #43):**
- NCCL fundamentally unavailable on Windows; PyTorch v1.8+ removed it from Windows builds
- No resolution as of April 2026
- Workaround: Gloo backend
```python
torch.distributed.init_process_group(backend="gloo")
```
- Trade-off: Gloo is **20–40% slower** than NCCL on GPU (MEDIUM confidence — varies by workload)

**DDP FileStore initialization issue (HIGH confidence, Smith #43):**
- FileStore requires a brand-new empty file per initialization
- Symptom: training hangs during process group initialization
- Fix sequence: kill all prior processes → delete FileStore file → use fresh path each run
- Recommend extended timeout:
```python
torch.distributed.init_process_group(
    backend="gloo",
    timeout=timedelta(minutes=30)  # up from default 10min
)
```

**bitsandbytes on Windows (HIGH confidence, Smith #43):**
- No official support as of April 2026
- Windows CI pipeline and preview win_amd64 wheels exist (MEDIUM confidence, 2025–2026)
- Community forks (unofficial, use at own risk): `bitsandbytes-windows` (PyPI), `fa0311/bitsandbytes-windows`, `jllllll/bitsandbytes-windows-webui`

**Windows-compatible VRAM optimizations noted (Smith #43 — confidence varies):**
- xFormers memory-efficient attention: speed improvement + VRAM reduction (LOW confidence on the ~30–40% figure — see CORRECTION C3)
- CPU offloading: VAE/text encoder to system RAM after encoding
- Pre-encoding latents + embeddings offline (eliminates redundant forward passes)
- Half-precision `model.half()`: 50% VRAM reduction (general principle, not Windows-specific)

---

## THEME 7: FLUX.2 Architecture

---

### 7A. FLUX.2 VAE & Latent Space
**Source: Smith #49 (data date: 2026-04-04 — current diffusers source, HIGH confidence throughout)**

**Confirmed parameters (from `autoencoder_kl_flux2.py`):**
- **Latent channels: 32** (line 110: `latent_channels: int = 32`)
- **Patch size: (2, 2)** (line 111: `patch_size: tuple[int, int] = (2, 2)`)
- **BatchNorm2d input channels: 128** = 2×2 patch × 32 channels (lines 125–131)

```python
self.bn = nn.BatchNorm2d(
    math.prod(patch_size) * latent_channels,  # = 4 * 32 = 128
    eps=batch_norm_eps,
    momentum=batch_norm_momentum,
    affine=False,
    track_running_stats=True,
)
```

**Pixel shuffle / pixel unshuffle: CONFIRMED ABSENT (HIGH confidence — negative, Smith #49):**
- Files searched: `transformer_flux2.py` (55.8KB), `autoencoder_kl_flux2.py` (20.8KB), `upsampling.py`, `downsampling.py`, base `vae.py`
- **None contain pixel_shuffle or pixel_unshuffle**
- FLUX.2 uses stride-based downsampling (encoder) and `F.interpolate()`-based upsampling (decoder)

**Latent flow architecture (Smith #49):**
1. Encoder: 3-channel RGB → stride-2 Conv downsampling ×4 layers → **32-channel latent at 1/16 spatial resolution**
2. Decoder: interpolate upsampling ×4 → 3-channel RGB output

---

## CORRECTIONS

**C1 — Smith #44: "RTX A6000 = hardware equivalent to RTX 3090" — INCORRECT**
- RTX A6000 has **48GB VRAM** vs. RTX 3090's **24GB VRAM**. While both use GA102 silicon and share similar compute throughput, they are not equivalent for training: the A6000 can accommodate 2× the batch size and holds larger activation buffers.
- The A6000 benchmark of 3.7 sec/step at 1280×1280 cannot be directly extrapolated to the RTX 3090.
- The Smith #44 LOW-confidence estimate of 9–10 sec/step for 3090 at 1280×1280 is derived from 4090 ratios, not A6000 ratios — that derivation is internally consistent but separately unreliable.
- **Impact:** All 1280×1280 timing and 5,000-step duration estimates for RTX 3090 carry LOW reliability until Smith #42 is re-run.

**C2 — Smith #41: arXiv 2507.07101 citation**
- Paper prefix "2507" = July 2025 submission. As of April 2026 this is a ~9-month-old preprint. Smith #41 correctly flags it as MEDIUM confidence. Opus should verify whether it has been peer-reviewed or updated since submission before citing as settled fact.

**C3 — Smith #43: xFormers VRAM reduction figure (~30–40%)**
- Smith #43 itself labels this LOW confidence with "estimated." This range appears widely in community guides but lacks rigorous benchmarks at controlled resolution/batch settings. Should not be cited as a reliable figure; treat as directional only.

---

## DISPUTES

**D1 — FLUX Training Steps: Apparent Range Inconsistency (Smith #46 vs. Smith #48)**
- Smith #46 (HIGH confidence, segmind 2026): "500–1,500 total steps for FLUX (vs. SDXL 2,000–5,000+)"
- Smith #48 (MEDIUM confidence, Civitai 2025): Style LoRA optimal at 3,000 steps; character LoRA 3,000–8,000 steps
- **Assessment: NOT a genuine dispute.** Difference is task/dataset scope, not contradictory data:
  - 500–1,500 applies to small curated FLUX datasets (10–30 images), rapid-convergence scenarios
  - 3,000–8,000 applies to character LoRAs with 25–30 diverse-angle images requiring broader generalization
  - Smith #48 itself states 1,500 as "preferred baseline" for style LoRA, overlapping with #46
- **Resolution:** Use Smith #48's dataset-size table as primary guide; interpret #46's 500–1,500 as the lower bound for small, clean datasets

**D2 — Rank Selection: No Conflicting Data, But Chain E Is Thin**
- Smith #48 recommends rank 4–8 for <500 images (MEDIUM confidence, Brenndoerfer 2026)
- No other Chain E Smith directly addresses rank selection for FLUX LoRA
- Project memory specifies base-9B + SimpleTuner + Google Fonts dataset, but the dataset image count is not stated in any Chain E Smith
- **Flag for Opus:** Rank choice for the actual project dataset is unresolved in Chain E

---

## GAPS

**G1 — RTX 3090 VRAM Budget (Smith #42 errored — HIGH PRIORITY)**
- Critical missing: exact VRAM consumption by config on RTX 3090 under FLUX LoRA training
- Only approximate 24GB-class figures available (Smith #41); 3090-specific data absent
- Affects: batch size safety margins, OOM threshold validation, whether batch_size=4 is viable

**G2 — LoRA Target Module Selection**
- No Chain E Smith covers which attention modules to target (to_q, to_k, to_v, to_out, ff, etc.) for FLUX.2 LoRA
- Smith #49 confirms architecture (32-channel latent, (2,2) patch) but does not map this to LoRA targeting strategy

**G3 — Learning Rate Scheduler Type**
- Smith #45 requires scheduler state be saved/restored, but no Chain E Smith covers scheduler type selection (cosine, linear, constant with warmup, etc.) for FLUX LoRA training

**G4 — Captioning Pipeline & Trigger Word Strategy**
- Smith #48 briefly mentions dual captioning (MEDIUM confidence) but no detailed captioning pipeline is covered
- No coverage of trigger word placement, caption length guidelines, or automated captioning tooling (BLIP-2, LLaVA, etc.)

**G5 — Google Fonts Domain Specifics**
- Chain E is entirely framework/hardware focused
- Zero coverage of font-domain considerations: glyph diversity requirements, character coverage strategy, rendering pipeline for training image generation, or caption structure for glyph/style learning

**G6 — KV Transfer Integration**
- Project memory notes "KV transfer" as a training goal alongside SimpleTuner and base-9B
- No Chain E Smith addresses KV transfer compatibility with LoRA, or how KV transfer interacts with checkpoint save/resume (Theme 3)

**G7 — Rank/Alpha ↔ FLUX.2 Architecture Mapping**
- Smith #49 establishes FLUX.2's 32-channel latent and (2,2) patch size precisely
- No Smith connects these architectural specifics to optimal LoRA rank or alpha choices

**G8 — Optimizer Selection Beyond AdamW8bit**
- Smith #50 mentions AdamW8bit as part of a recommended combo (MEDIUM confidence, synthesized)
- No Chain E Smith benchmarks or compares alternative optimizers (Prodigy, CAME, AdaFactor) for FLUX LoRA

---

## CROSS-SMITH AGREEMENTS (CONFIDENCE BOOSTS)

**A1 — Validation requires no merge: UNANIMOUS**
- Smith #46 (HIGH, HF docs): load LoRA directly for validation inference
- Smith #47 (by implication): PEFT two-file format used for active training; inference via load_lora_weights
- **→ Elevated confidence: merge is strictly optional, post-training only**

**A2 — SimpleTuner outputs Diffusers-compatible format: UNANIMOUS**
- Smith #47 (HIGH): default output is `pytorch_lora_weights.safetensors`, Diffusers format
- Smith #46 (HIGH): uses `load_lora_weights()` pattern throughout, consistent with Diffusers format

**A3 — BF16 is standard for FLUX on RTX 30-series: UNANIMOUS**
- Smith #50 (HIGH): BF16 standard, RTX 30-series+, no loss scaling needed
- Smith #41 (HIGH): references bf16 throughout all training configurations

**A4 — ~250-step checkpoint/validation cadence: AGREE**
- Smith #46 (MEDIUM): validation every 100–250 steps
- Smith #48 (HIGH): save checkpoints every 250 steps
- **→ 250-step interval is the convergent practical recommendation**

**A5 — Quality >> Quantity for FLUX datasets: UNANIMOUS**
- Smith #48 (HIGH, empirical): 16-image curated set outperforms 110 mediocre; loss data confirms
- Smith #46 (HIGH): "FLUX learns fast" — implies small, quality sets are the mode
- Smith #44 (implicit): FLUX training is measured in hours for small datasets, not days

---

*End of Chain E organized findings. 9/10 Smiths preserved in full. Smith #42 errored — re-run recommended before Opus synthesis to complete the VRAM budget picture.*

============================================================
## Chain D — Anderson Report
============================================================

# CHAIN D — STRUCTURED FINDINGS FOR OPUS SYNTHESIS
**Smiths #31–#40 | Organized by Anderson | 2026-04-04**
*Triage applied: DEDUP, RECENCY, AGREE, DISAGREE, GAPS, CORRECT*

---

## THEME 1: FLUX.2 KLEIN TEXT ENCODER ARCHITECTURE

### 1.1 Encoder Model Identity
| Property | Value | Confidence | Source |
|----------|-------|-----------|--------|
| Full model class | `Qwen3ForCausalLM` | HIGH | Smith #32 (diffusers docs) |
| Embedding variant — Klein 9B | Qwen3-Embedding-8B | HIGH | Smith #31 (QwenLM GitHub) |
| Embedding variant — Klein 4B | Qwen3-Embedding-4B | HIGH | Smith #31 (QwenLM GitHub) |
| Tokenizer class | `Qwen2TokenizerFast` | HIGH | Smith #32 (HF API docs) |

### 1.2 Per-Variant Architecture Specifications
| Variant | Layers | Hidden Dim | Output Vector | Sequence Length |
|---------|--------|-----------|---------------|-----------------|
| Qwen3-Embedding-8B (Klein 9B) | 36 | **4096** | 4096 | 32K native / 512 at inference |
| Qwen3-Embedding-4B (Klein 4B) | 36 | **2560** | 2560 | 32K native / 512 at inference |

**Confidence: HIGH** — Smith #31, official QwenLM/Qwen3-Embedding repository, April 2026
**⚠️ See Correction C1 — Smith #32 conflicts on hidden dim; Smith #31 preferred.**

### 1.3 Layer Extraction — ✅ AGREE (Smiths #31 + #32)
- **Extracted layers**: `[9, 18, 27]` (0-indexed, from 36 total)
- **Method signature**: `text_encoder_out_layers: tuple[int] = (9, 18, 27)` — default in `pipeline_flux2_klein.py`
- **Source files**: `src/flux2/text_encoder.py` (BFL repo) and `pipeline_flux2_klein.py` (diffusers)
- **Confidence: HIGH** — Independently confirmed by two Smiths from separate codebases

### 1.4 Embedding Shape Transformation
| Step | Operation | Output Shape | Source |
|------|-----------|-------------|--------|
| 1 | Stack 3 hidden states | `(batch, 3, seq_len, hidden_dim)` | Smith #31, HIGH |
| 2 | Einops reshape `"b c l d -> b l (c d)"` | `(batch, seq_len, 3×hidden_dim)` | Smith #31, HIGH |
| 3 — Klein 9B | Final output | `(batch, 512, 12288)` = 3 × 4096 | Smith #31, HIGH |
| 3 — Klein 4B | Final output | `(batch, 512, 7680)` = 3 × 2560 | Smith #31, HIGH |
| 4 — Klein 9B | Downstream linear projection | `nn.Linear(12288 → 4096)` into transformer | Smith #31, HIGH |

**Layer fusion method**: Concatenation (not averaging) — confirmed by einops reshape pattern [Smith #31, HIGH]

### 1.5 Processing Pipeline (Full Sequence — Agreed)
1. Apply chat template formatting with `add_generation_prompt=True` [Smith #31, HIGH]
2. Tokenize via `Qwen2TokenizerFast` [Smith #32, HIGH]
3. Forward pass with `output_hidden_states=True, use_cache=False` [Smith #32, HIGH]
4. Extract hidden states at layers 9, 18, 27 [Smith #31 + #32, HIGH — AGREE]
5. Stack & reshape via einops `"b c l d -> b l (c d)"` [Smith #31, HIGH]
6. Project to transformer hidden size via `nn.Linear` [Smith #31, HIGH]
7. Conditioning flows through `double_blocks`, then concatenated for `single_blocks` [Smith #31, HIGH]

**No prompt upsampling or content filtering applied** (unlike Mistral variants in other FLUX.2 models) [Smith #31, HIGH]

### 1.6 `text_ids` Output Tensor
- **Shape**: `(batch_size × num_images_per_prompt, seq_len, 4)` [Smith #32, HIGH]
- **Content**: (T, H, W, L) position coordinates
- **Generated by**: `_prepare_text_ids()` method [Smith #32, HIGH]

### 1.7 Qwen3 Internal Architecture Features
| Feature | Value | Source |
|---------|-------|--------|
| Activation function | SwiGLU | Smith #31, HIGH |
| Position encoding | RoPE (Rotary Position Embeddings) | Smith #31, HIGH |
| Attention type | Grouped-Query Attention (GQA) | Smith #31, HIGH |
| MRL support | Matryoshka Representation Learning — flexible vector dims | Smith #31, HIGH |

### 1.8 `encode_prompt()` Return Signature
- Returns **2-tuple**: `(prompt_embeds, text_ids)` [Smith #32, HIGH]
- `prompt_embeds` batch dim: `batch_size × num_images_per_prompt` [Smith #32, HIGH]
- View operation: `prompt_embeds.view(batch_size * num_images_per_prompt, seq_len, -1)` [Smith #32, HIGH]

---

## THEME 2: REF2FONT ARCHITECTURE & TRAINING

### 2.1 Base Model & Version History
| Item | Value | Confidence | Source |
|------|-------|-----------|--------|
| Base model | FLUX.2-klein-9B | HIGH | Smith #33 + #35 — **AGREE** |
| V2 changes | Fixed dataset gen issues, resolution → 1280px, improved vectorization | HIGH | Smith #35 (README) |
| V3 changes | Cyrillic support, extended glyphs (`"` & `&`), reduced jitter, straighter alignment | HIGH | Smith #35 (README) |

### 2.2 Training Metrics (from CivitAI — accessed 2026-04-05)
| Metric | Value | Confidence |
|--------|-------|-----------|
| Training steps | **5,999** | HIGH — Smith #35 |
| Epochs | **1** | HIGH — Smith #35 |
| Training approach | In-Context LoRA (pixel-level concat) | HIGH — Smith #33 + #35 **AGREE** |

**Note**: IC-LoRA paper (Smith #33) cites 5,000 steps as methodology baseline (MEDIUM) — this is general methodology, not Ref2Font-specific. The 5,999 figure (Smith #35, CivitAI) is the actual Ref2Font training run. Not a conflict.

### 2.3 Reference Image Conditioning — ✅ AGREE (Smiths #33 + #35)
| Property | Value | Confidence |
|----------|-------|-----------|
| Reference input (Latin) | 1280×1280 pure black/white image of "Aa" | HIGH |
| Reference input (Cyrillic) | 1280×1280 pure black/white image of "Аа" | HIGH |
| Output atlas | 1280×1280, strict black & white (no gray/shadows/volume) | HIGH |

**Prompt template (Latin)**:
```
"A technical font atlas grid of the Latin charset: ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!?.,;:-\"&\". The style is strictly derived from the reference image \"Aa\"."
```
[Smith #35, HIGH]

**Prompt template (Cyrillic)**: Equivalent 105-character Cyrillic set prompt [Smith #35, HIGH]

### 2.4 In-Context LoRA Methodology (IC-LoRA paper, not Ref2Font-specific)
- Dataset scale: 20–100 high-quality image sets [Smith #33, HIGH — from IC-LoRA paper, 2024]
- Training scale: single A100, 5,000 steps, batch size 4, LoRA rank 16 [Smith #33, MEDIUM]
- No architectural modification to base model — training data approach only [Smith #33, HIGH]
- Multi-image compositing: images concatenated at pixel level into one large image (e.g., 2×2 grid) [Smith #33, HIGH]
- Composite passed through VAE encoder **once** [Smith #33, HIGH]
- Prompts merged: per-image prompts + task description + bracketed panel-wise annotations [Smith #33, HIGH]

### 2.5 Undisclosed / Confirmed Gaps (from Smith #35)
- Dataset size and composition — **not public**
- Number of training images — **not public**
- Specific training toolkit (SimpleTuner suspected but **unconfirmed**)
- LoRA rank used — **not listed on CivitAI or GitHub**
- No technical blog post, paper, or detailed writeup by SnJake exists

---

## THEME 3: CONDITIONING APPROACHES — TAXONOMY & COMPARISON

### 3.1 Three Primary Methods
| Approach | Reference Handling | Architecture Change | Use Case | Source |
|----------|-------------------|--------------------|----------|--------|
| **In-Context LoRA (Ref2Font)** | Pixel-level concatenation into composite | None (training data only) | Style transfer, font generation | Smith #33, HIGH |
| **IP-Adapter** | Separate CLIP encoding → decoupled cross-attention | Adds K′, V′ cross-attention layers | Face/style consistency | Smith #33 + #34, HIGH |
| **FLUX.1 Kontext** | Latent sequence concatenation | None (unified arch) | Unified editing & generation | Smith #33, HIGH — arXiv 2506.15742, Apr 2025 |

### 3.2 IP-Adapter Architecture
| Component | Value | Confidence | Source |
|-----------|-------|-----------|--------|
| Base image encoder | OpenCLIP-ViT-H-14 | HIGH | Smith #34 |
| Preference note | ViT-H-14 preferred over ViT-bigG-14 — experimental results showed no significant difference despite larger size | HIGH | Smith #34 |
| For SD1.5 | OpenCLIP ViT H 14 (632M params) | HIGH | Smith #33 |
| For SDXL | OpenCLIP ViT BigG 14 (1845M params) | HIGH | Smith #33 |
| Trainable params | ~22M (~3–5% of total model) | HIGH | Smith #33 + #34 — **AGREE** |
| Frozen components | U-Net, CLIP text encoder, CLIP image encoder | HIGH | Smith #34 |
| Projection layer | `Linear(clip_embeddings_dim → clip_extra_context_tokens × cross_attention_dim)` + LayerNorm | HIGH | Smith #34 |
| Projection output sequence length | ~4 tokens | HIGH | Smith #34 |
| Adapter weight size | ~100MB | HIGH | Smith #33 |

**Note on D2**: Smith #33 and #34 appear to conflict on encoder selection but do not genuinely conflict — Smith #33 lists available encoders by base model variant; Smith #34 states experimental preference. Both can be simultaneously true. (See Disputes section.)

### 3.3 IP-Adapter Training Details
| Hyperparameter | Value | Confidence | Source |
|----------------|-------|-----------|--------|
| Dataset | ~10M text-image pairs (LAION-2B + COYO-700M) | HIGH | Smith #34 — arXiv 2308.06721 |
| Training steps | 1 million | HIGH | Smith #34 |
| Loss function | L2 diffusion: `‖ϵ − ϵθ(x_t, c_t, c_i, t)‖²` | HIGH | Smith #34 |
| Optimizer | AdamW, weight decay 0.01 | HIGH | Smith #34 |
| Learning rate | 1e-4 (fixed) | HIGH | Smith #34 |
| Batch size | 8 images/GPU × 8 V100 GPUs | HIGH | Smith #34 |
| CFG dropout — individual | 5% probability | HIGH | Smith #34 |
| CFG dropout — simultaneous text+image | 5% probability | HIGH | Smith #34 |
| Paper date | August 2023 (arXiv 2308.06721) | HIGH | Smith #34 |

### 3.4 FontAdapter (IP-Adapter Extension for Fonts)
- **Paper**: arXiv 2506.05843 (2024) [Smith #34, HIGH]
- **Two-stage curriculum**:
  - Stage 1: Train on isolated glyphs (black text on white) — extracts pure font attributes without scene interference [Smith #34, HIGH]
  - Stage 2: Freeze Resampler (image projection module), fine-tune on realistic scenes — preserves learned font representations [Smith #34, HIGH]
- **Key dataset design**: Reference and target images have *different text content* — enables glyph-agnostic font attribute extraction that generalizes to unseen characters and languages without retraining [Smith #34, HIGH]
- **Speed**: ~11 seconds vs ~40 minutes for full fine-tuning [Smith #34, HIGH]
- **Evaluation metrics**: Max-IoU, HOG-similarity, MS-SSIM (font similarity); OCR-based (text accuracy); CLIP/SigLIP (prompt alignment) [Smith #34, HIGH]

### 3.5 Why IP-Adapter Outperforms LoRA for Fonts
- LoRA learns per-font style space but requires detailed text descriptions ("serif, thin, elegant")
- IP-Adapter extracts pixel-level/structural features directly from glyphs — no description needed
- Glyph-agnostic conditioning generalizes to unseen characters/languages without retraining
[Smith #34, HIGH]

### 3.6 IP-Adapter vs LoRA Comparison Table
| Dimension | IP-Adapter | LoRA |
|-----------|-----------|------|
| Mechanism | Decoupled cross-attention — parallel K′, V′ branches | Low-rank weight decomposition ΔW = BA |
| Conditioning input | Direct CLIP image embeddings | Text-based; no image encoder |
| Architectural change | Adds new cross-attention layers | Modifies existing weight matrices |
| Trainable params | ~22M (3–5%) | 1–10M depending on rank/targets |
| Flexibility | Works on any base model; text + image both | Per-model fine-tuning; text only |
| Inference cost | Low (parallel attention, no UNet mod) | Very low (weights merged or loaded) |
[Smith #34, HIGH — multiple sources consistent]

---

## THEME 4: LORA TRAINING — DATA AUGMENTATION

### 4.1 Recommended Augmentations
| Augmentation | Recommendation | Confidence | Notes |
|-------------|----------------|-----------|-------|
| Horizontal flip | ✅ SAFE for most fonts | HIGH | Exception: script/calligraphic styles. Enable with cached latents for efficiency. [Smith #36] |
| Random crop + resize | ✅ RECOMMENDED | MEDIUM | FontDiffuser (AAAI 2024) uses for robustness; enhances style imitation [Smith #36] |
| Small rotation ±5–10° | ⚠️ CONDITIONAL | HIGH | Risky for orientation-dependent chars (e.g., 6/9 in digit fonts) [Smith #36] |
| Mask augmentation | ✅ BEST PRACTICE (multi-stage training) | MEDIUM-HIGH | Gaussian noise on mask boundaries (σ-based expansion/contraction); preserves structure while varying style. CVPR 2024 [Smith #36] |

### 4.2 Not Recommended Augmentations
| Augmentation | Recommendation | Confidence | Reason |
|-------------|----------------|-----------|--------|
| Color jitter (brightness/saturation/hue) | ❌ DISABLE | MEDIUM | Corrupts intentional color palette and typography [Smith #36] |
| Gaussian noise | ⚠️ SPARINGLY (σ ≤ 0.03 max) | MEDIUM | Higher values corrupt glyph recognition; threshold derived from character recognition research [Smith #36] |
| Random blur | ⚠️ CONTEXT-DEPENDENT | LOW | σ ∈ [0,1] may help thin-line chars but breaks crisp type rendering [Smith #36] |

### 4.3 Efficiency Principle
- **Enable cached latents + flip augmentation** = best quality-to-speed ratio [Smith #36, HIGH]
- Avoids repeated VAE encoding; flipping is "free" variation
- Disabling augmentation entirely causes overfitting on small font datasets [Smith #36, HIGH]

### 4.4 Confirmed Gap
❌ **No empirical studies specifically on "font atlas LoRA + augmentation" strategies exist** [Smith #36]
— Diffusion-based font generation research exists (2024+) but SimpleTuner-specific font atlas guidance absent from public sources

---

## THEME 5: LORA TRAINING — CONVERGENCE & METRICS

### 5.1 Primary Monitoring Signal
- **Loss curves alone are insufficient** — visual quality assessment is primary signal [Smith #37, MEDIUM]
- **Preview generation every 50–100 steps** gives better feedback than staring at loss [Smith #37, MEDIUM]
- **Critical finding**: Quality peaks before loss bottoms — best checkpoint often at steps 800–1,200, not final convergence [Smith #37, MEDIUM — reported across multiple 2025–2026 guides]

### 5.2 FID / CLIP Scores — Practical Assessment
| Metric | Recommendation | Confidence | Notes |
|--------|----------------|-----------|-------|
| FID | Research/benchmarking only | HIGH | Expensive (full generation + inception features) [Smith #37] |
| CLIP Score | Research/benchmarking only | HIGH | Correlates with human judgment [Smith #37] |
| Validation loss | ✅ Sufficient for practical LoRA | HIGH | Correlates highly with FID and CLIP per MLCommons FLUX.1 benchmark (single forward pass) [Smith #37] |

**MLPerf FLUX.1 validation loss target**: **0.586** (64 B200 GPUs, bf16, ~95 min) [Smith #37, HIGH — MLCommons, Oct 2025]

### 5.3 Healthy Loss Curve — 5,000 Steps
| Phase | Steps | Pattern | Confidence |
|-------|-------|---------|-----------|
| Sharp drop | 1–500 | ~0.5 → ~0.34 | MEDIUM (kohya-ss issue reports, 2025) |
| Gradual decrease → stabilization | 500–1,500 | Continued slow drop | MEDIUM (SimpleTuner guides, 2025–2026) |
| Plateau | 1,500+ | Minor fluctuations or very slow decrease | MEDIUM |

**Dataset size effect on settled loss range**:
- 20–30 images: 0.08–0.34 [MEDIUM — user reports, kohya-ss]
- 100+ images: 0.34–0.38 [MEDIUM — user reports, kohya-ss]

### 5.4 Red Flags
| Signal | Diagnosis | Confidence |
|--------|-----------|-----------|
| Erratic oscillation | Learning rate too high | MEDIUM |
| Flat loss after 500+ steps | LR too low OR dataset quality issues | MEDIUM |
| Loss increases | Severe misconfiguration | HIGH |

### 5.5 FLUX-Specific Convergence Notes
| Finding | Value | Confidence | Source |
|---------|-------|-----------|--------|
| Training paradigm | Flow matching (not standard diffusion) | MEDIUM | Smith #37 |
| Recommended max LR | ≤ 2e-4 (not standard 5e-4) | MEDIUM | Smith #37 — Kevin Gabeci, Mar 2026 |
| Usable results | 500–1,000 steps vs SDXL's 3,000–5,000 | MEDIUM | Smith #37 |
| Validation loss in kohya-ss | Added via PR #1898 (2026) for automated early stopping | HIGH | Smith #37 — GitHub PR |

### 5.6 SimpleTuner-Specific Monitoring
- Logs loss, LR, training speed to console + optional TensorBoard [Smith #37, HIGH]
- Monitor VRAM during first 100–300 steps (peak at optimizer init) [Smith #37, MEDIUM]
- Generate validation images every 500–1,000 steps from saved checkpoints [Smith #37, MEDIUM]

---

## THEME 6: LORA WEIGHT MERGING & FORMAT

### 6.1 Merging LoRA into Base Model
```python
merged_model = model.merge_and_unload()
```
| Step | Effect | Confidence |
|------|--------|-----------|
| Iterates layers, identifies LoRA adapters | — | HIGH — Smith #38 |
| Computes merged weights: base + adapter params | — | HIGH |
| Replaces LoRA layers with standard layers | — | HIGH |
| Returns base model class (no longer PeftModel) | — | HIGH |
| **Irreversible** unless original weights kept separately | — | HIGH |

**Trade-offs**: Reduced inference latency (single matmul vs. base + adapter), simplified deployment (one checkpoint) — [Smith #38, HIGH]

### 6.2 Saving to Safetensors
```python
model.save_pretrained('output_dir', safe_serialization=True)
```
- `safe_serialization=True` is **default** in current PEFT [Smith #38, HIGH — GitHub issues #2098, #754]
- Output: `adapter_model.safetensors` + `adapter_config.json` [Smith #38, HIGH]
- Already in diffusers-compatible format — no additional conversion [Smith #38, HIGH]

### 6.3 Manual Format Conversion (from other formats, e.g., MLX, GGUF)
```python
# Key rename: 'lora_a' → 'lora_A.weight', 'lora_b' → 'lora_B.weight'
from safetensors.torch import save_file
save_file(new_state_dict, "adapter_model.safetensors")
# Create/update adapter_config.json with HF PEFT format
```
[Smith #38, MEDIUM]

### 6.4 Known Issues
- DeepSpeed Zero3 training can produce empty (40-byte) `adapter_model.safetensors` files [Smith #38, MEDIUM — GitHub #2892, #4416]
- Shared tensor errors on some configs → try `safe_serialization=False` [Smith #38, MEDIUM]

---

## THEME 7: LORA INFERENCE LOADING

### 7.1 Basic Load
```python
pipe = Flux2KleinPipeline.from_pretrained(
    "black-forest-labs/FLUX.2-klein-base-9B",
    torch_dtype=torch.bfloat16
)
pipe.load_lora_weights("path/to/your_lora.safetensors")
pipe.to("cuda")
```
[Smith #39, HIGH — Black Forest Labs official docs, 2026]

### 7.2 Named Adapter Load
```python
pipe.load_lora_weights(
    "path/to/lora/directory",
    weight_name="pytorch_lora_weights.safetensors",
    adapter_name="my_custom_lora"
)
```
[Smith #39, HIGH — HF Diffusers API docs, 2026]

**Note on filename discrepancy**: Smith #38 uses `adapter_model.safetensors` (PEFT standard output); Smith #39 uses `pytorch_lora_weights.safetensors` (diffusers training script output). Not a conflict — different origins of LoRA file. Both are valid; both load via `pipe.load_lora_weights()`.

### 7.3 File Formats & Directory Structure
| Format | Status |
|--------|--------|
| `.safetensors` | Primary (required/recommended) |
| `.bin` (PyTorch pickle) | Alternative, accepted |
| Single file: `path/to/lora.safetensors` | Supported |
| Directory: `lora_dir/pytorch_lora_weights.safetensors` + optional `.json` | Supported |
[Smith #39, HIGH]

### 7.4 LoRA Strength at Inference
```python
# Uniform scaling
image = pipe("prompt", cross_attention_kwargs={"scale": 0.7}).images[0]
```
- Scale 0.0 = base model only (LoRA disabled)
- Scale 1.0 = full LoRA application
- Values between adjust blending
[Smith #39, HIGH]

**Fine-grained component scaling** via `pipe.set_adapters("adapter_name", scales_dict)` — supports per-block, per-layer granularity [Smith #39, HIGH]

### 7.5 Dynamic Scale Scheduling (Per-Step)
```python
# Modify LoRA strength step-by-step via callback_on_step_end
lora_scales = torch.linspace(1.5, 0.7, lora_steps).tolist()

def callback(pipeline, step, timestep, callback_kwargs):
    pipeline.set_adapters("lora", lora_scales[step])
    return callback_kwargs
```
[Smith #39, HIGH — HF Diffusers docs]
**⚠️ See Gap G7**: Example uses `FluxPipeline` (FLUX.1), not `Flux2KleinPipeline` — applicability unconfirmed but likely compatible.

### 7.6 Metadata Handling
If trained with Diffusers training scripts, metadata is automatically saved in `.safetensors` and automatically parsed on load — no manual config needed [Smith #39, HIGH]

---

## THEME 8: MULTI-RESOLUTION TRAINING & ASPECT RATIO BUCKETING

### 8.1 Multi-Resolution Recommendation
| Finding | Value | Confidence | Source |
|---------|-------|-----------|--------|
| Recommended approach for fonts | Single resolution (1280×1280) | HIGH | Smith #40 |
| Quality diff 512 vs 1024 training | Negligible for style LoRAs | MEDIUM | Smith #40 (Civitai community testing, ~2025) |
| Multi-resolution benefit | Marginal improvement in prompt adherence / composition | MEDIUM | Smith #40 |
| FLUX.2 native capability | Fine-tuned on multi-aspect buckets; handles varied resolutions natively | HIGH | Smith #40 (Segmind guide + Civitai, 2025–2026) |
| Ref2Font precedent | Single 1280×1280 — no multi-resolution documented | HIGH | Smith #40 (GitHub repo) |

### 8.2 Aspect Ratio Bucketing (ARB) — Core Mechanism
1. Images grouped by aspect ratio into buckets
2. Scale factor computed to cover image; bucket selected with fewest removed pixels [HIGH — NovelAI implementation, still current]
3. All images in a batch must have identical tensor dimensions
4. Each batch filled from single bucket only; different batches can have different resolutions
[Smith #40, HIGH]

**Available FLUX buckets (1024px base)**: Aspect ratios 0.14, 0.33, 0.60, 1.00, 1.67, 3.00, 7.00 [Smith #40, HIGH — Segmind Flux guide, 2026]
**Common bucket sizes**: 1024×1024, 768×1024, 1024×768, 1280×768 [Smith #40, MEDIUM — community consensus]

### 8.3 ARB Benefits for Font Atlas
| Benefit | Confidence |
|---------|-----------|
| No forced square cropping — content preserved | HIGH |
| Accepts images of varied shapes | MEDIUM |
| Glyph format flexibility: padded vs. tight glyphs mixed | MEDIUM |
| Random selection during training enhances textural detail perception while preserving aspect ratio | MEDIUM — font-specific glyph training practices, 2025–2026 |
[Smith #40]

### 8.4 ARB Drawbacks for Fonts
| Drawback | Confidence |
|---------|-----------|
| Increased training time | MEDIUM |
| Buckets with single image are suboptimal (need ≥ 2 per bucket) | MEDIUM |
| Center cropping risk if resolution mismatch is severe | MEDIUM |
[Smith #40]

### 8.5 Recommended Configuration for Font Atlas
- Train at 1280×1280 base with 3–4 buckets: `[1024×1024, 1280×1024, 1024×1280, optionally 1280×1280]`
- Enable ARB to preserve glyph detail without forced squaring
- **Avoid** full multi-resolution (512/768/1024/1280) — adds training time for negligible font quality gain
[Smith #40]

---

## ⚠️ CORRECTIONS

### C1 — CRITICAL: Hidden Dimension Conflict (Smiths #31 vs #32)

**Smith #32 states**: `hidden_dim = 768`, therefore `3 layers × 768 = 2,304`
**Smith #31 states**: Qwen3-Embedding-8B has `hidden_dim = 4096`, therefore `3 layers × 4096 = 12,288`

**Assessment**: Smith #32's figure of 768 is almost certainly wrong. **768 is the hidden dimension of CLIP ViT-B/32** — an entirely different model. For an 8-billion-parameter Qwen3 model, 4096 is architecturally consistent and expected. Smith #31 cites the official QwenLM/Qwen3-Embedding repository directly; Smith #32 cites diffusers docs and appears to have incorrectly assumed a CLIP-like hidden size.

**Preferred value**: `hidden_dim = 4096` (Klein 9B), `hidden_dim = 2560` (Klein 4B) per Smith #31

**Cascading correction to Smith #32**:
- `prompt_embeds hidden_dim` → **12,288** (not 2,304) for Klein 9B
- `downstream projection` → `nn.Linear(12288 → 4096)` (not `nn.Linear(2304 → ...)`)

**Action for Opus**: Verify against `pipeline_flux2_klein.py` in diffusers main branch — specifically check whether the diffusers implementation uses a reduced/different Qwen3 variant that could legitimately have 768-dim hidden states, or whether Smith #32's source was misread.

### C2 — Clarification: Ref2Font Step Count Disambiguation

Smith #33 cites **5,000 steps** from IC-LoRA paper (MEDIUM confidence — general methodology)
Smith #35 cites **5,999 steps** from CivitAI model page (HIGH confidence — actual Ref2Font run)

**Not an error in either Smith.** These are distinct sources describing different things. The 5,999 is the authoritative figure for Ref2Font specifically. No numeric correction needed — only disambiguation for Opus.

---

## ⚡ DISPUTES

### D1 — prompt_embeds hidden_dim: 12,288 vs 2,304 (Smiths #31 vs #32)
**This is the primary unresolved dispute in Chain D.**

| Smith | Claim | Source | Confidence |
|-------|-------|--------|-----------|
| #31 | hidden_dim = **4096**, concat = **12,288** | BFL flux2 repo + QwenLM GitHub | HIGH |
| #32 | hidden_dim = **768**, concat = **2,304** | diffusers pipeline_flux2_klein.py | HIGH (but value appears erroneous) |

**Assessment**: This is most likely an *error* in Smith #32, not a genuine architectural dispute. The 768 figure has no plausible architectural basis for Qwen3-Embedding-8B. However, it is possible (though unlikely) that the diffusers implementation wraps a quantized or truncated version with a different projection. Flagged for Opus to resolve via direct code inspection.

**Recommended resolution source**: `diffusers/src/diffusers/pipelines/flux2/pipeline_flux2_klein.py`, specifically `_get_qwen3_prompt_embeds()` — look for the actual hidden state dimensionality used.

### D2 — IP-Adapter encoder selection (Smiths #33 vs #34) — LOW PRIORITY
- Smith #33: Lists ViT-H-14 (SD1.5) and ViT-BigG-14 (SDXL) as the standard encoder by variant
- Smith #34: States ViT-H-14 is preferred over ViT-BigG-14 based on experimental results showing no significant difference

**Assessment**: Not a genuine dispute — Smith #33 describes standard deployment by model variant; Smith #34 describes experimental comparison preference. Both can simultaneously be true. No Opus action needed unless encoder choice specifically matters for downstream implementation.

---

## 🔍 GAPS

| ID | Gap Description | Relevant Smiths |
|----|----------------|-----------------|
| G1 | FLUX.2 Klein `double_blocks` vs `single_blocks` internal architecture — depth, dimensions, attention mechanism details not covered | #31 |
| G2 | Ref2Font dataset composition entirely undisclosed — size, source, composition unknown; training toolkit (SimpleTuner vs ai-toolkit vs kohya-ss) unconfirmed | #33, #35 |
| G3 | Ref2Font LoRA rank — not listed on CivitAI, GitHub, or any public source | #35 |
| G4 | No SimpleTuner-specific font atlas LoRA augmentation guidance — confirmed absent from public sources | #36 |
| G5 | FLUX.2-klein-9B inference parameters specific to Ref2Font — guidance scale, num_inference_steps, scheduler choice | #35, #39 |
| G6 | Smith #34 truncated mid-sentence on Character-Adapter comparison — full results and methodology missing | #34 |
| G7 | Dynamic LoRA scale scheduling (Smith #39) demonstrated with `FluxPipeline` (FLUX.1) — applicability to `Flux2KleinPipeline` unconfirmed | #39 |
| G8 | VAE specifications for FLUX.2 Klein not covered — encoder/decoder architecture, latent channel count, scale factor | — |
| G9 | Matryoshka Representation Learning (MRL) in Qwen3 — mentioned in Smith #31 but implications for FLUX.2 Klein text encoding not explored | #31 |
| G10 | SimpleTuner config file specifics for FLUX.2-klein-9B LoRA training — recommended LR, scheduler, warmup steps, optimizer choice | #37 |
| G11 | FLUX.2 Klein 4B variant — mentioned in Smith #31 but not referenced in any Ref2Font or training context; unclear if it's a supported training target | #31 |

---

## SIGNAL INTEGRITY SUMMARY

| Theme | Coverage | Confidence Level | Primary Risk |
|-------|----------|-----------------|-------------|
| Text encoder architecture | High — two Smiths, two codebases | HIGH overall | C1 hidden_dim dispute must be resolved |
| Ref2Font training metrics | Moderate — CivitAI + GitHub only | HIGH on what's known; large undisclosed gap | Dataset/toolkit opacity |
| Conditioning approaches taxonomy | High — three methods well-documented | HIGH | None |
| IP-Adapter specifics | High — from original paper | HIGH | — |
| FontAdapter | Moderate — paper-level only | HIGH | Truncated Smith #34 |
| Augmentation strategy | Moderate — no font-atlas-specific empirical data | MEDIUM overall | Lack of domain-specific studies |
| Convergence metrics | High — multiple guides + MLCommons | MEDIUM-HIGH | Community guides vs. formal benchmarks |
| Weight merging/format | High | HIGH | DeepSpeed Zero3 edge case noted |
| Inference loading | High | HIGH | G7 (FLUX.1 vs FLUX.2 callback) |
| Multi-resolution/bucketing | High | HIGH-MEDIUM | — |

**Most critical unresolved item for Opus**: **C1/D1** — `prompt_embeds hidden_dim` (12,288 vs 2,304). This affects all downstream dimension calculations for FLUX.2 Klein 9B text conditioning.

============================================================
## Chain C — Anderson Report
============================================================

# CHAIN C — STRUCTURED FINDINGS FOR OPUS SYNTHESIS
**Smiths #21–#30 | Organized by Anderson | 2026-04-04**
*All unique signal preserved. Do not edit for brevity — Opus handles synthesis.*

---

## ⚠️ CORRECTIONS (Read First)

### CORRECTION C-1 — Smith #29: EMA Decay Value Mislabeled (HIGH CONFIDENCE ERROR)

**The problem:** Smith #29 attributes the value `0.00001` to *EMA decay* for FLUX.2-dev photorealistic LoRA, citing Calvin Herbst's 50+ training runs. It calls this "drastically lower than standard defaults" and implies FLUX models respond differently to EMA tuning.

**Cross-check with Smith #25:** The same Calvin Herbst experiments explicitly identify `0.00001` as the **weight decay** value ("1/10th default = 0.00001 instead of 0.0001") and flag weight decay as the **single most impactful parameter** in Herbst's runs. EMA was separately listed in #25 as "tested but NOT flagged as primary drivers of output quality."

**Verdict:** Smith #29's table entry `FLUX.2-dev photorealistic LoRA → 0.00001` is the *weight decay*, not EMA decay. EMA decay standard range (0.968–0.9999) is stated correctly elsewhere in #29. The conflation is a labeling error, not a data error. Opus should treat this value as weight decay exclusively.

**Corrected EMA picture:** No empirically-tested optimal EMA decay for FLUX.2 LoRA is documented in Chain C. The standard range (0.999–0.9999) from general diffusion literature remains the best available guidance.

---

### CORRECTION C-2 — Smith #23: Logit-Normal FID Figures Are From Different Comparisons

**Not an error, but requires disambiguation:** Smith #23 uses "16%" twice with opposite signs:
- "Logit-Normal suffers **16% FID penalty** vs. uniform" (static logit-normal alone)
- "Curriculum sampling yields **16% relative FID improvement**" (two-phase logit-normal → uniform vs. static uniform)

These are consistent figures from the same source (arxiv 2603.12517, 2026-03). No contradiction. Opus should treat them as complementary data points about the same spectrum.

---

## SECTION 1 — FLUX.2 ARCHITECTURE

### 1.1 Block Structure
**[Smith #21, #22 — CONFIDENCE: HIGH — AGREE]**

FLUX.2 consists of two distinct transformer block types:
- **19 double-stream blocks** (cross-attention; some sources say 8 — see dispute D-1 below)
- **38–48 single-stream blocks** (parallel attention + MLP fused; see dispute D-1)

Double-stream blocks handle text-image cross-attention. Single-stream blocks handle parallel self-attention and MLP computation in a fused design.

**Fused QKV+MLP Projection (single-stream blocks):**
- Single-stream blocks use `to_qkv_mlp_proj`: one linear layer that outputs both QKV tensors (3×3072) and MLP hidden states (4×3072)
- Native FLUX architecture stores QKV as a single fused matrix
- Diffusers-format LoRAs unfold these into separate `to_q, to_k, to_v` modules
- This architectural difference between native FLUX and diffusers-wrapped versions must be accounted for in LoRA target module selection
- **Source:** Smith #21 [Architecture documentation, DiffSynth-Studio]

### 1.2 Training Objective: Flow Matching (not DDPM)
**[Smith #22 — CONFIDENCE: HIGH]**

FLUX uses pure velocity prediction (v-prediction), not epsilon prediction:
- **Velocity target:** `v = ε − x₀`
- **Interpolation path:** `x_t = (1−t)x₀ + tε`
- **Velocity is time-independent:** `v_t = d/dt[(1−t)x₀ + tε] = ε − x₀` — constant across all t
- **Training loss:** `L = E_{t,x₀,ε}[‖v_θ(x_t, t) − (ε − x₀)‖²]`
- Simulation-free during training (no ODE integration)
- No noise/beta schedule required
- FLUX.1 Kontext (arxiv 2506.15742, 2026-04) confirmed: velocity-only training in latent space on concatenated context + instruction token sequences
- **Source:** Smith #22 [arxiv 2506.02070, 2026-04; arxiv 2506.15742]

### 1.3 FLUX.2 vs. FLUX.1 Architectural Differences
**[Smith #25 — CONFIDENCE: HIGH]**

| Parameter | FLUX.1 | FLUX.2 |
|-----------|--------|--------|
| Parameters | 12B | 32B |
| Text encoder | CLIP | Mistral-3 |
| Convergence speed | Baseline | 40–50% faster |
| LoRA compatibility | — | NOT compatible with FLUX.1 LoRAs |
| VRAM (training) | ~20GB | 24GB+ |
| Optimal LR range | 1e-4 to 4e-4 | 8e-4 to 1.5e-3 |

**Source:** Smith #25 [fal.ai, multiple sources, Feb 2026]

---

## SECTION 2 — FLOW MATCHING THEORY

### 2.1 Velocity Prediction vs. DDPM Epsilon Prediction
**[Smith #22 — CONFIDENCE: HIGH — Comprehensive]**

| Aspect | DDPM (Epsilon) | Flow Matching (Velocity) |
|--------|----------------|--------------------------|
| Prediction target | Noise ε added to data | Velocity field v |
| Loss formula | `E[‖ε − ε_θ(√(ᾱ_t)x₀ + √(1−ᾱ_t)ε, t)‖²]` | `E[‖v_θ(x_t, t) − (ε − x₀)‖²]` |
| Path geometry | Curved, stochastic SDE trajectories | Straight, deterministic ODE paths |
| Time-dependence of target | Changes with t (different SNR at each t) | **Constant** across all t |
| Inference steps | ~1000 (HIGH confidence) | ~10 (MEDIUM estimate) |
| Variance schedule | Requires β schedule (linear, cosine, etc.) | No schedule needed |

**Source:** Smith #22 [arxiv 2506.02070; SOTAAZ Blog; Physics-based DL textbook]

### 2.2 Mathematical Intuition
**[Smith #22 — CONFIDENCE: HIGH]**

The key property enabling FLUX efficiency: the network learns `v_θ(x_t, t)` must output the same direction regardless of t. This makes the learning problem more constrained and stable than DDPM's t-dependent noise prediction. Straight-line interpolation with minimal curvature enables fewer inference steps.

**Source:** Smith #22 [physicsbaseddeeplearning.org]

---

## SECTION 3 — TIMESTEP SAMPLING STRATEGIES

### 3.1 Strategy Comparison
**[Smith #23 — CONFIDENCE: HIGH (uniform, logit-normal); MEDIUM (shifted cosine)]**

| Strategy | Mechanism | Key Trade-off |
|----------|-----------|---------------|
| **Uniform** | Equal probability across [0,1] | Wastes updates on trivial boundary cases; better asymptotic quality (ceiling) |
| **Logit-Normal** | Concentrates mass toward t ≈ 0.5 | Accelerates early convergence; 16% FID penalty vs. uniform due to boundary under-sampling |
| **Shifted Cosine** | `f(t) = cos²((t/T + s)/(1+s) · π/2)`, s ≈ 0.008–0.2 | Geometrically optimal (Fisher–Rao-geodesic); balances mid-timestep emphasis |
| **Curriculum (two-phase)** | Phase 1: Logit-Normal → Phase 2: Uniform | 16% FID improvement + 33% convergence speed-up vs. static uniform |

**Sources:** Smith #23 [WACV 2024 noise schedule paper; ICCV 2025 improved schedule; arxiv 2603.12517 (2026-03)]

### 3.2 FLUX's Actual Approach: Generalized Time SNR Shift Transformation
**[Smith #23 — CONFIDENCE: HIGH]**

FLUX does not use pure uniform, logit-normal, or cosine. It uses:
- Sigmoid-like transformation controlled by **μ (mu)** and **σ (sigma, fixed at 1.0)**
- Reparameterizes standard uniform timestep distribution
- Concentrates timesteps at regions where velocity field changes most rapidly
- Non-uniform, with **emphasis on middle regions** of flow trajectory

**Scheduler:** `FlowMatchEulerDiscreteScheduler` (based on SD3's flow matching)
- Timestep schedule stretched and shifted to terminate at `shift_terminal` value
- Implements Euler integration along learned velocity field

**Source:** Smith #23 [Hugging Face Diffusers docs]

### 3.3 Shift Parameter Behavior (FLUX-Specific)
**[Smith #23 — CONFIDENCE: HIGH]**

| Parameter | Default | Effect When Increased |
|-----------|---------|----------------------|
| `base_shift` | 0.5 | Reduces variation; images more consistent with prompt |
| `max_shift` | 1.15 | Encourages stylization & exaggeration |
| `use_dynamic_shifting` | False | When True: shift auto-calculated per-image based on resolution |

**Dynamic Shift Formula (FLUX.2 high-resolution):**
```
μ = 0.00016927 × image_seq_len + 0.45666666
```
For variable steps ≤4300: interpolates between 10-step and 200-step schedules.
**Source:** Smith #23 [black-forest-labs FLUX.2 implementation via deepwiki.com — HIGH confidence]

**`flux_shift` Method (FLUX.1-specific):**
- Automatically computes shift based on resolution — no manual `--discrete_flow_shift` needed
- Resolution-aware adaptation produces more realistic samples vs. static shift
- Barely documented; source: kohya-ss issue #1958
- **Source:** Smith #23 [MEDIUM confidence]

### 3.4 Practical Recommendations for FLUX Training
**[Smith #23 — CONFIDENCE: HIGH (default), MEDIUM (curriculum)]**

1. **Default:** Use built-in `flux_shift` (resolution-aware, auto-optimized)
2. **Training:** Implement two-phase curriculum (Logit-Normal → Uniform) for 16% quality gain + 33% speed gain
3. **Fine-tuning:** Start with `base_shift=0.5`; increase only if consistency needed over diversity
4. **High-res images:** Rely on dynamic shift calculation; do not hardcode — resolution matters

---

## SECTION 4 — LORA TARGET MODULES

### 4.1 Comprehensive Target Module List (FLUX.2)
**[Smith #21 — CONFIDENCE: HIGH — DiffSynth-Studio, 2025]**

Full block coverage across both `single_transformer_blocks` and `transformer_blocks`:

```
to_q, to_k, to_v, to_out.0,
add_q_proj, add_k_proj, add_v_proj,
to_add_out,
linear_in, linear_out,
to_qkv_mlp_proj
```

**Layer-by-layer breakdown:**

| Layer | Module Names | Block Type | Confidence |
|-------|-------------|------------|------------|
| Query/Key/Value projections | `to_q`, `to_k`, `to_v` | Both | HIGH |
| Output projection | `to_out.0` | Both | HIGH |
| Cross-attention projections | `add_q_proj`, `add_k_proj`, `add_v_proj` | Double-stream only | HIGH |
| Additional output | `to_add_out` | Double-stream only | HIGH |
| MLP layers | `linear_in`, `linear_out` | Both | HIGH |
| Fused QKV+MLP projection | `to_qkv_mlp_proj` | Single-stream only | MEDIUM |

**Source:** Smith #21 [DiffSynth-Studio examples, HuggingFace PEFT docs]

### 4.2 Minimal Attention-Only Configuration
**[Smith #21 — CONFIDENCE: MEDIUM]**

`attn.to_k, attn.to_q, attn.to_v, attn.to_out.0`
— Achieves good results with smaller LoRA size.
**Source:** Smith #21 [Documentation references]

---

## SECTION 5 — KNOWN PEFT/FLUX ISSUES

### 5.1 Issue Catalog
**[Smith #21 — CONFIDENCE: HIGH for all unless noted]**

| Issue | Date | Description | Status |
|-------|------|-------------|--------|
| State dict mismatch during inference | Aug 2024 (#9178) | `--flux_lora_target=all+ffs` causes state_dict errors at inference; trained layers not found in base model | UNRESOLVED |
| Hotswapping multiple LoRAs | Apr 2025 (#11298) | Unexpected keys error on hotswap: `"transformer_blocks.13.norm1.linear.lora_B.weight"` | DOCUMENTED, partially mitigated |
| Torch compile module naming conflict | Dec 2025 (#2957) | `torch.compile()` (inductor) adds `_orig_mod.` prefix; PEFT cannot match target modules | DOCUMENTED |
| Slow LoRA loading | Early 2025 (#2055) | `pipe.load_lora_weights()` takes >290 seconds for FLUX | KNOWN, no fix |
| State dict export (adapter names) | Jan 2025 | `peft.get_peft_model_state_dict()` doesn't preserve adapter names | DOCUMENTED, MEDIUM confidence |
| FP8 + CPU offload incompatibility | Undated | Cannot use FP8 quantization with CPU offloading and compilation simultaneously | DOCUMENTED, MEDIUM confidence |

**Workaround for hotswapping:** Load the LoRA targeting the most layers first to avoid recompilation.
**Source:** Smith #21 [GitHub issues: diffusers #9178, #11298; peft #2957, #2055]

---

## SECTION 6 — LORA RANK SELECTION

### 6.1 Rank Quality Comparison
**[Smith #24 — Primary. CONFIDENCE: HIGH for ranks 16, 32, 64, 128+; MEDIUM for rank 4–8]**

| Rank | Quality Assessment | Source | Confidence | Date |
|------|-------------------|--------|------------|------|
| 4 | Minimal effect; very small files (42MB reduction from 451MB) | Segmind, SeaArt | MEDIUM | 2025–2026 |
| 8–16 | Clean, well-structured for simpler styles; sometimes unexpectedly noisy at very low ranks | Modal (FLUX.1), SimpleTuner | HIGH | 2024–2026 |
| 16 | **Optimal for most styles** (per Modal testing: 4000 steps, LR 2e-4) | modal.com | HIGH | 2024 |
| 32 | Natural grain patterns, fine details, texture capture without overcooking | Calvin Herbst Feb 2026 | HIGH | 2026 |
| 64 | Better complex faces/details | Calvin Herbst, SimpleTuner | HIGH | 2026 |
| **128/64/64/32** | **Winning config for FLUX.2** (4:2:2:1 ratio): natural grain, resolved details, optimal texture | Calvin Herbst 50+ runs | HIGH | Feb 2026 |
| 256 | Image destruction — ripped apart, unrecognizable output | Calvin Herbst | HIGH | Feb 2026 |

**Key finding:** Calvin Herbst tested ~64 separate rank combinations across ratios (1:2:4). The **4:2:2:1 ratio (128/64/64/32)** outperformed all others. Past this point: diminishing returns with increased file size.

### 6.2 File Size Impact
**[Smith #24 — CONFIDENCE: HIGH for SD baseline; MEDIUM for FLUX-specific estimates]**

**Stable Diffusion baseline (SeaArt):**
- Rank 32 = 40MB+ | Rank 64 = 70MB+ | Rank 128 = 140MB+

**FLUX-specific scaling:**
- Linear: doubling rank ≈ doubles file size
- Larger base models (12B–24B) amplify rank's file impact vs. SD (1.5B–3.5B)

**Storage formula:** Total bytes ≈ `rank × model_dimension × 2 × ~4 bytes` (FP32)

### 6.3 Ref2Font V3 Rank Inference
**[Smith #24 — CONFIDENCE: HIGH for file size; LOW for rank estimate]**

- **Confirmed file size:** Ref2Font V3 = 316.04 MB (FLUX.2-klein-9B specialized LoRA)
- **Sources:** Civitai, HuggingFace, GitHub [HIGH confidence]
- **Rank inference (NOT documented):** 316MB for FLUX.2-klein-9B suggests rank ~64–96 range
  - Klein: ~19 double blocks + 39 single blocks (58 blocks total)
  - At ~128KB per layer per rank unit → 316MB ≈ rank 64–80
  - **Confidence: LOW** — estimate only; Ref2Font GitHub README & Civitai do not state rank parameters

**FLAGGED GAP:** Ref2Font rank remains undocumented publicly. `Ref2FontV3.safetensors` model card lacks this metadata.

### 6.4 Practical Recommendations
**[Smith #24 — CONFIDENCE: HIGH]**

| Use Case | Rank | File Size | Notes |
|----------|------|-----------|-------|
| Simple concepts | 8–16 | 50–80MB | Fast, minimal VRAM |
| Style training (standard) | 32–48 | 100–150MB | Recommended balance |
| Complex faces/detail | 64 | 170–200MB | High quality, more memory |
| Multi-layer optimization | 128/64/64/32 (ratio) | 250–316MB | Empirically optimal (Herbst) |

---

## SECTION 7 — LEARNING RATE OPTIMIZATION

### 7.1 Optimal Ranges by Model
**[Smith #25 — CONFIDENCE: HIGH — Feb 2026]**

**FLUX.1:**
- Optimal range: `1e-4` to `4e-4` (0.0001–0.0004)
- Standard starting point: `1e-4` — HIGH confidence
- For characters/faces: `4e-4` works better than generic `1e-4` — MEDIUM confidence
- `1e-3` (0.001): Causes heavy overfitting at 500–1000 steps, image "burning" — HIGH confidence
- `1e-5` (0.00001): Produces no observable changes after 1000 steps — MEDIUM confidence

**FLUX.2 (dev & Klein):**
- Optimal range: `8e-4` to `1.5e-3` (0.0008–0.0015) — HIGH confidence
- FLUX.2 Klein defaults: `5e-5` (0.00005) or `9.5e-5` (0.000095) — HIGH confidence
- Minimum for Klein: `1e-4` (0.0001) — MEDIUM confidence

**Why different:** FLUX.2 learns 40–50% faster than FLUX.1 despite being larger (32B vs 12B), requiring higher learning rates for comparable convergence. **FLUX.2 is not just a scaled FLUX.1 — its learning dynamics are qualitatively different.**
**Source:** Smith #25 [fal.ai, Feb 2026]

### 7.2 LR Sensitivity
**[Smith #25 — CONFIDENCE: HIGH — Calvin Herbst, Feb 2026]**

> "Changing the learning rate by five thousandths of a percent on the Flux architecture ripped the image apart."

FLUX is extraordinarily sensitive to precise LR values — far more than SDXL or SD families. Unlike those models, **FLUX.2 demands you leave the learning rate alone once set.**

### 7.3 LR Is NOT the High-Leverage Variable
**[Smith #25 — CONFIDENCE: HIGH — Herbst 50+ runs, Feb 2026]**

Across 50+ controlled runs on FLUX.2-dev, Herbst did NOT flag LR as a primary quality driver. LR was held constant at a safe default and proved robust. The high-leverage parameters are **weight decay** and **network dimensions** (rank configuration).

**Note:** This is not a contradiction with 7.1 above — LR matters for being in the right range (not burning/stalling), but once there, tuning it further yields less return than optimizing weight decay and rank.

---

## SECTION 8 — WEIGHT DECAY

### 8.1 Herbst's Most Impactful Finding
**[Smith #25 — CONFIDENCE: HIGH — Calvin Herbst, Feb 2026]**

**Winning configuration:** Weight decay = `0.00001` (1/10th of the default `0.0001`)

**Effect:** Lowered weight decay dramatically improved:
- Grain pickup
- Shadow texture
- Film-like quality

**Herbst's analogy:** "Decay controls color channel separation the way different film stocks control dye coupling."

**Relative importance:** Weight decay was flagged as **more impactful than LR, optimizer choice, EMA, FP32 vs BF16, timestep type, caption dropout, and gradient accumulation** in Herbst's controlled experiments.

**Source:** Smith #25 [Calvin Herbst Medium, Feb 2026]

### 8.2 Winning Full Configuration (FLUX.2-dev → HerbstPhoto V4)
**[Smith #24, #25 — CONFIDENCE: HIGH — AGREE across both Smiths]**

- **Network dimensions:** 128/64/64/32 (4:2:2:1 ratio)
- **Weight decay:** 0.00001
- **Steps:** 7,000
- **Training hardware:** H200 GPU cluster, Ostris AI Toolkit, Runpod
- **Dataset:** 41 image/caption pairs

---

## SECTION 9 — GRADIENT CHECKPOINTING & VRAM

### 9.1 Core Mechanism
**[Smith #26 — CONFIDENCE: HIGH — foundational CS result]**

Gradient checkpointing (activation checkpointing) trades compute for memory by omitting intermediate activations from the computational graph during the forward pass. During backpropagation, omitted activations are **recomputed on demand**.

- **Memory complexity:** Reduces from O(n) to O(√n) where n = number of layers
- **Optimal checkpoint placement:** Every √(n)-th node
- **Implementation:** `torch.utils.checkpoint.checkpoint()` wrapping transformer blocks; `reentrant=False` recommended

**Source:** Smith #26 [PyTorch Training Performance Guide; PyTorch checkpoint docs]

### 9.2 VRAM Savings — General PyTorch
**[Smith #26 — CONFIDENCE: HIGH for speed cost; MEDIUM for memory savings ranges]**

- Selective checkpointing: 50–60% memory savings, only 10–15% slowdown
- Full checkpointing: 60–70% memory savings
- Speed cost: 20–30% increased computation time (recomputing forward passes during backprop)

### 9.3 FLUX-Specific Benchmarks
**[Smith #26 — CONFIDENCE: HIGH (Apatero 2025); MEDIUM (derived)]**

- **Activation memory reduction:** 60–70% with 20–30% speed penalty
- **Without** optimizations: 35GB+ required for FLUX LoRA training
- **With** gradient checkpointing + quantization: 16–18GB (comfortable on 24GB GPU)
- **Rank-16 LoRA (all components):** ~40GB without → ~20–24GB with checkpointing + other optimizations
- **Minimum:** 12GB (heavy optimization)
- **Comfortable:** 16–24GB

**Training time example:** RTX 4090, batch size 6, 1024×1024:
- VRAM: ~21–22GB
- Time: ~2.5 hours for typical face LoRA
- **Source:** Smith #26 [Apatero 2025 — MEDIUM confidence, case-specific]

**Inference activation memory** (no checkpointing): 15–25GB for single 1024×1024 image, varies with model variant and precision.

### 9.4 `FluxTransformer2DModel.enable_gradient_checkpointing()`
**[Smith #26 — CONFIDENCE: HIGH for existence; MEDIUM for version availability]**

- Method exists and is callable on the transformer to activate memory-efficient training
- `Transformer2DModel` has `_supports_gradient_checkpointing = True` flag
- Earlier issue (#5862, Nov 2023) reported lack of support; current codebase indicates support added (PR #10611)
- Used in Hugging Face Diffusers LoRA training scripts via `unet.enable_gradient_checkpointing()`

**Source:** Smith #26 [diffusers transformer_flux.py; DreamBooth FLUX README]

---

## SECTION 10 — QUANTIZATION & INT8 TRAINING

### 10.1 QLoRA Pattern: How It Works
**[Smith #27 — CONFIDENCE: HIGH — 2023–2024 standard]**

**Standard architecture:**
- **Base model weights:** Loaded in INT4/INT8 and **frozen** (no gradients)
- **LoRA adapters:** Kept in BF16 (unfrozen, gradients computed)
- **Forward pass:** INT8 weights dequantized to BF16 on-the-fly, then combined with LoRA outputs

**Memory savings:** INT8 quantization reduces base model footprint by ~75% (32-bit → 8-bit). LoRA overhead is ~0.01–1% of base model parameters depending on rank.

**Source:** Smith #27 [HuggingFace 4-bit blog; QLoRA principles guide]

### 10.2 optimum-quanto: Dynamic Dequantization in Forward Pass
**[Smith #27 — CONFIDENCE: HIGH — code-level analysis]**

**Execution flow:**
1. `QLinear.forward()` invokes `torch.nn.functional.linear(input, self.qweight, bias=self.bias)`
2. `qweight` property dynamically quantizes weights **every forward pass** using `quantize_weight()` with per-axis scales
3. `quantize_weight` returns a QTensor, immediately **dequantized to BF16** for the matmul
4. Backward pass: gradients flow through dequantized values to update float32 base weights (if unfrozen) and adapter weights

**Key insight:** Weights exist as float32 in memory during training but are quantized on-the-fly for each forward pass. Dynamic conversion allows gradient propagation to underlying float weights while keeping storage footprint small.

**Source:** Smith #27 [optimum-quanto source: qlinear.py, qmodule.py lines 180–210]

### 10.3 optimum-quanto: Current Status
**[Smith #27 — CONFIDENCE: HIGH — 2026-04-02]**

**Status:** Maintenance mode as of 2026-04-02. Only minor bug fixes and documentation improvements accepted. Major new features unlikely to be merged.

**Capabilities:**
- ✅ Supports dynamic/unfrozen training via `optimum.quanto.quantize()` (not QuantizedModel API)
- ✅ QAT example provided (tune quantized model for a few epochs to recover accuracy)
- ❌ LoRA integration unclear: feature request exists (PEFT issue #1997) but not confirmed as fully supported as of 2025 — MEDIUM confidence

**Source:** Smith #27 [optimum-quanto GitHub README, 2026-04-02; PEFT issue #1997]

### 10.4 Practical Recommendation: Prefer bitsandbytes or torchAO for INT8+LoRA
**[Smith #27 — CONFIDENCE: HIGH]**

- **bitsandbytes:** Mature QLoRA support, proven with LLMs up to 70B parameters
- **torchAO:** PyTorch official, newer FP8 support, Unsloth integration
- **optimum-quanto:** Not recommended for new training pipelines given maintenance mode and unclear LoRA support

---

## SECTION 11 — ADAMW8BIT OPTIMIZER

### 11.1 How It Works
**[Smith #28 — CONFIDENCE: HIGH]**

**Blockwise dynamic quantization:**
- Groups 128 parameters
- Computes scale from max absolute value
- Quantizes to 8-bit; dequantization approximates <1% error
- Decoupled weight decay (separate from adaptive steps) ensures stability post-quantization

**Source:** Smith #28 [HuggingFace bitsandbytes docs]

### 11.2 Memory Savings
**[Smith #28 — CONFIDENCE: HIGH for core claims; MEDIUM for specific benchmarks]**

| Metric | Reduction | Confidence | Source |
|--------|-----------|------------|--------|
| Optimizer state (8-bit vs 32-bit) | **75%** | HIGH | HuggingFace optimizer docs |
| AMD GPU reduction | **41%** | HIGH | ROCm blog |
| MLPerf 2025 benchmark | **78%** | MEDIUM | Johal 2026 (not directly verified) |
| Llama-70B FP16→8-bit | **73%** (320GB vs 1.2TB) | MEDIUM | Kaitchup Substack |
| 3B model | **75%** (24GB→6GB) | HIGH | Kaitchup Substack |
| Batch size gain (24GB VRAM) | 1→32+, 4x throughput | HIGH | HuggingFace optimizer docs |

**Tradeoff:** CPU-GPU transfer overhead can reduce training throughput vs. full-precision when the standard optimizer fits in VRAM.

### 11.3 Windows Compatibility
**[Smith #28 — CONFIDENCE: HIGH]**

- **Official status:** bitsandbytes **not supported on Windows** — CUDA custom functions compiled for Linux only
- **Community workaround:** `bitsandbytes-windows` fork (fa0311/bitsandbytes-windows) — fragile, sensitive to dependency state, unreliable
- **RTX 5090:** Reported compatibility issues (Issue #1517)
- **AdamW8bit constraints:** `AMSGrad` parameter not supported (must be False); `optim_bits` ignored (always uses 8-bit)

**Source:** Smith #28 [HuggingFace installation guide; Mindfire Technology]

---

## SECTION 12 — EMA FOR LORA TRAINING

### 12.1 Core Mechanism
**[Smith #29 — CONFIDENCE: HIGH — Nov 2024 paper]**

**Formula:** `s_new = s_old × decay + p × (1 − decay)`

Where:
- `s` = shadow parameter (EMA copy)
- `p` = current training parameter
- `decay` = exponential decay constant

EMA accumulates weighted historical average; reduces noise from individual training steps. Shadow copy kept separate from training but used at inference time.

**Source:** Smith #29 [Lei Mao's Log Book; arxiv 2411.18704 "Exponential Moving Average of Weights in Deep Learning", Nov 2024]

### 12.2 Should EMA Be Used in LoRA Training?
**[Smith #29 — CONFIDENCE: MEDIUM — Contradictory sources]**

**Yes (evidence for):**
- EMA maintains smoothed copy, produces higher quality generations than raw training model
- Implicit regularization effect (requires less LR decay than SGD)
- SimpleTuner includes EMA support and generates EMA checkpoints by default

**Disputed:**
- SimpleTuner documentation states "This does not apply to LoRA" in some places, yet implements it
- Unclear if this note distinguishes full-model training vs. LoRA specifically

**Herbst finding:** EMA was tested across 50+ FLUX.2 runs and was **NOT flagged as a primary quality driver** (MEDIUM confidence — secondary finding in Herbst's experiments).

### 12.3 Recommended Decay Values
**[Smith #29 — CONFIDENCE: HIGH for standard range; see Correction C-1 for FLUX-specific value]**

| Context | Value | Confidence |
|---------|-------|------------|
| Typical diffusion training | 0.999–0.9999 | HIGH |
| Tested range (arxiv 2411.18704) | [0.968, 0.984, 0.992, 0.996, 0.998] | MEDIUM |
| Large datasets | Higher (~0.999) | MEDIUM |
| Smaller/noisier datasets | Lower | MEDIUM |
| Approx. half-life | 1000 batches | MEDIUM |
| **FLUX.2-dev "EMA decay" = 0.00001** | **⚠️ SEE CORRECTION C-1 — this is weight decay, not EMA decay** | ERROR |

### 12.4 Stability Benefits (Indirect Evidence Only)
**[Smith #29 — CONFIDENCE: MEDIUM — inferred, not FLUX-specific]**

1. EMA's noise-reduction mechanism would theoretically help given FLUX's extreme LR sensitivity
2. No direct comparative study of EMA vs. non-EMA for FLUX published in Chain C

---

## SECTION 13 — CAPTION DROPOUT

### 13.1 Definition and Mechanism
**[Smith #30 — CONFIDENCE: HIGH — primary sources]**

Caption dropout = randomly dropping text captions during training with probability `p_uncond`. The model trains to predict denoising for both conditioned and unconditioned scenarios from a single network by periodically replacing captions with null tokens.

**Mechanism (from classifier-free guidance):**
- During training: conditioning dropped with probability `p_uncond`
- At sampling: `x_guided = x_uncond + w(x_cond − x_uncond)` where w = guidance scale
- Enables CFG at inference time — caption dropout is the training-time prerequisite for CFG

**Source:** Smith #30 [Ho & Salimans 2022, arxiv 2207.12598]

### 13.2 Empirical Foundation for 5–10% Range
**[Smith #30 — CONFIDENCE: HIGH for DALL-E/Imagen; MEDIUM for LoRA practice]**

| Model | Rate | Source |
|-------|------|--------|
| DALL-E v1 | 10% | AssemblyAI, 2022–2023 |
| DALL-E 2 | 10% caption + 50% CLIP embedding | AssemblyAI |
| Imagen | 10% | Cited in CFG context |
| Ho & Salimans (CFG) | 10–20% recommended | arxiv 2207.12598, 2022 |
| SD LoRA practice | 5% caption dropout | kohya_ss wiki, viewcomfy guide |

**Observed range:** 10–20% for pre-training; LoRA practitioners prefer 5%.

### 13.3 Why It Works — Generalization Mechanism
**[Smith #30 — CONFIDENCE: HIGH for CFG; MEDIUM for inferred mechanisms]**

1. **Prevents caption-centric encoding:** Forces model to "learn the image anyway" — prevents too many image features from being associated with specific words
2. **Enables CFG:** Caption dropout is the training-time implementation that makes CFG sampling work — cannot be retrofitted post-hoc
3. **Improves unconditioned generation:** Models with dropout maintain consistent performance when no caption is provided

### 13.4 Caption Dropout for Single-Caption / Concept Datasets — NOT RECOMMENDED
**[Smith #30 — CONFIDENCE: MEDIUM — inferred from character training guidance]**

**Critical finding for font/glyph training contexts:**

| Scenario | Recommended Rate | Rationale |
|----------|-----------------|-----------|
| Character/concept training | 0–0.02 (minimal) | "Useless when training concepts or characters" — model needs strong token-to-image binding |
| Style training | 0.1–0.25 | Higher values appropriate; styles are generalizable features |
| **Font atlases (glyph-specific)** | **0 (not applicable)** | Each glyph needs strong token binding; dropout weakens "character A" → visual variant associations |

**Practical guidance for glyph/character datasets:**
- `caption_dropout_rate = 0`
- `caption_tag_dropout = 0` (or minimal 0.01–0.02)
- Ensure consistent token naming (e.g., "sks_CharacterName")

**Source:** Smith #30 [kohya guides; Civitai; character training practice documentation]

---

## 🔴 DISPUTES

### DISPUTE D-1 — FLUX.2 Block Count: 8+48 vs. 19+38 vs. 19+39

| Smith | Double-stream blocks | Single-stream blocks | Source cited |
|-------|---------------------|---------------------|--------------|
| #21 | 8 | 48 | Architecture documentation |
| #21 (also) | 19 | 39 | DiffSynth-Studio / "Klein applies LoRA to ~19 double blocks + 39 single blocks" (from rank inference section) |
| #24 | 19 | 39 | Ref2Font rank estimate |

**Nature of dispute:** Smith #21 contains internally inconsistent numbers (8+48 in the architecture section vs. 19+39 implied in the same report). The 8+48 figure may be for FLUX.2-dev while 19+39 may be for FLUX.2-klein (a smaller variant). The 8 double-stream blocks figure may also refer to a subset (e.g., double-stream "cross-attention" blocks only vs. total double-stream blocks).

**Flag for Opus:** Verify exact block counts for FLUX.2-dev vs. FLUX.2-klein separately. The 19+39 figure appears in context of Klein-specific analysis (LoRA target count for Ref2Font). This is likely a model-variant distinction, not an error in either Smith — but confirmation is needed.

---

### DISPUTE D-2 — EMA Applicability to LoRA (SimpleTuner)

| Source | Position |
|--------|---------|
| SimpleTuner (one location) | "EMA does not apply to LoRA" |
| SimpleTuner (implementation) | Generates EMA checkpoints by default; LoRA training supported |
| HuggingFace diffusers discussion | EMA recommended for LoRA |
| Herbst 50+ runs | EMA tested but not flagged as primary driver |

**Nature:** Genuine ambiguity within SimpleTuner documentation. Could be a documentation lag (note written for full-model context, not updated for LoRA), or a functional distinction (EMA checkpointing behavior differs between full-model and LoRA modes). Not stale-vs-fresh — both positions coexist in current SimpleTuner.

**Flag for Opus:** Unresolved. Recommend treating EMA for LoRA as "available but unproven" for FLUX specifically until further evidence.

---

### DISPUTE D-3 — FLUX.1 Optimal Learning Rate: 1e-4 vs. 2e-4

| Source | Value | Context |
|--------|-------|---------|
| Smith #25 (multiple industry guides) | `1e-4` as standard starting point | General guidance |
| Smith #24 (Modal testing) | `2e-4` as optimal (4000 steps, rank 16) | Specific experimental configuration |

**Nature:** Likely not a genuine dispute — 2e-4 is within the stated range (1e-4 to 4e-4) and may reflect a valid higher-end choice for specific configurations. However, the two sources present different values as "optimal" without explicit reconciliation. Noting for completeness.

---

## 🕳️ GAPS

### Technical Gaps (Not Covered in Chain C)

| Gap | Relevance |
|-----|-----------|
| **Ref2Font V3 rank parameters** | Undocumented publicly; Smith #24 estimated 64–80 at LOW confidence |
| **VAE settings for FLUX LoRA training** | No coverage in any of Smiths #21–#30 |
| **Text encoder fine-tuning vs. frozen** | FLUX.2 uses Mistral-3; whether T5/CLIP should be frozen during LoRA training is not addressed |
| **Batch size effects on FLUX LoRA quality** | Mentioned only incidentally (batch size 6 in Apatero example); no systematic treatment |
| **Dataset preprocessing for font/glyph LoRAs** | Caption dropout guidance in #30 addresses captioning but not image preprocessing, augmentation, or atlas slicing |
| **DDP / multi-GPU training for FLUX** | Not covered; only single-GPU benchmarks present |
| **Checkpoint saving frequency** | Not discussed; relevant for long (7000-step) runs |
| **Text encoder learning rate (separate LR for TE vs. UNet)** | Not addressed; common configuration parameter in SimpleTuner/kohya |
| **SimpleTuner configuration file specifics** | Referenced multiple times but no Smith covers the actual config schema |
| **EMA optimal decay for FLUX LoRA (empirical)** | Correction C-1 shows the only FLUX-specific value was mislabeled; genuine gap remains |
| **Inference pipeline optimization** (FLUX.2 → production) | Not covered; Chain C focuses on training |
| **FP8 training** (as opposed to FP8 inference) | Smith #27 mentions torchAO FP8 support; no depth on FP8 training for FLUX |
| **LoRA merging strategies** (multiple LoRAs → single model) | Smith #21 covers hotswapping issues; merging not addressed |
| **FLUX.2-klein vs. FLUX.2-dev differences** (beyond parameter counts and LR) | Mentioned but not systematically compared |

### Coverage Gaps (Would Expect From Chain C Scope)

- No Smith covers **Ref2Font inference parameters** (guidance scale, steps, seed behavior for font generation)
- No Smith covers **SimpleTuner multi-resolution training** / aspect ratio bucketing
- No Smith covers **caption quality strategies** for font datasets beyond dropout rate

---

## 📊 CROSS-SMITH CONFIDENCE SUMMARY

| Finding | Converging Smiths | Confidence |
|---------|------------------|------------|
| FLUX.2 uses flow matching, v-prediction | #22 (explicit), #21 (implicit) | HIGH — AGREE |
| 128/64/64/32 rank configuration best for FLUX.2 | #24, #25 (both cite Herbst) | HIGH — AGREE |
| Weight decay 0.00001 as primary quality lever | #25 (explicit); #29 (mislabeled as EMA — Correction C-1) | HIGH after correction |
| Caption dropout contraindicated for glyph/concept training | #30 (sole) | MEDIUM — no corroboration |
| FLUX.2 learns 40–50% faster than FLUX.1 | #25 (sole — fal.ai) | HIGH — single primary source |
| Curriculum timestep sampling: 16% FID + 33% speed | #23 (sole — arxiv 2603.12517) | MEDIUM — single recent source |
| Rank 256 causes image destruction | #24 (sole — Herbst) | HIGH — empirical, specific |
| bitsandbytes not supported on Windows | #28 (official docs) | HIGH |
| optimum-quanto in maintenance mode | #27 (2026-04-02) | HIGH — recent |
| Gradient checkpointing: O(n) → O(√n) | #26 (foundational) | HIGH |
| EMA "does not apply to LoRA" (SimpleTuner) | #29 vs. #29 implementation | DISPUTED |

---

*End of Chain C structured findings. Total Smiths processed: 10 (#21–#30). All unique signal preserved. Ready for Opus synthesis.*

============================================================
## Chain B — Anderson Report
============================================================

# Chain B — Smith #11–#20: Organized Findings for Opus Synthesis

**Organization date:** 2026-04-04 | **Source window:** Smiths #11–#20 | **Frameworks covered:** DiffSynth-Studio, ostris/ai-toolkit, bghira/SimpleTuner, kohya-ss/musubi-tuner, kohya-ss/sd-scripts

---

## SECTION 1 — FLUX.2 Klein Model Architecture Parameters

### 1A. Klein Variant Dimensions
**Source: Smith #19 (kohya/musubi-tuner, HIGH confidence, commit SHA `23d3a5f6`)**

| Parameter | Klein-9B | Klein-4B |
|---|---|---|
| Context dim | 12,288 | 7,680 |
| Hidden size | 4,096 | 3,072 |
| Num heads | 32 | 24 |
| Double blocks | 8 | 5 |
| Single blocks | 24 | 20 |
| Guidance embed | **Disabled** | **Disabled** |

**Source:** `flux2_models.py` — `Klein9BParams` and `Klein4BParams` dataclasses (Smith #19, HIGH).

### 1B. FLUX.2 Base Reference Dimensions
**Source: Smith #20 (kohya/sd-scripts, MEDIUM confidence — GitHub API rate limited)**

| Parameter | FLUX.2 Base |
|---|---|
| DoubleStreamBlocks | 19 |
| SingleStreamBlocks | 38 |
| Split dims (DSB attention, Q/K/V) | [3072, 3072, 3072] |
| Split dims (SSB linear1, Q/K/V/MLP) | [3072, 3072, 3072, 12288] |

⚠️ **See DISPUTE C** — these block counts (19/38) match FLUX.1 architecture, not Klein; Smith #19 says Klein support is exclusive to musubi-tuner.

### 1C. Guidance Embedding Handling
- **Klein-9B/4B:** `use_guidance_embed=False`; guidance_vec fixed at **1.0** during training (Smith #19, HIGH)
- **ai-toolkit:** requires `bypass_guidance_embedding: true` in config YAML for Klein (Smith #13, HIGH)
- **FLUX.2-dev:** has guidance embedding (contrast point established by both Smiths #13 and #19)

---

## SECTION 2 — LoRA Network Architecture & Injection Targets

### 2A. Target Block Types
**Agreement across frameworks:**

| Framework | Target Blocks | Source |
|---|---|---|
| DiffSynth | DiT attention layers (24 modules) | Smith #11, HIGH |
| musubi-tuner | `DoubleStreamBlock` + `SingleStreamBlock` | Smith #19, HIGH |
| sd-scripts | `DoubleStreamBlock` + `SingleStreamBlock` (img_attn, txt_attn, img_mlp, txt_mlp, img_mod, txt_mod, single linear1, single modulation) | Smith #20, HIGH |
| ai-toolkit | Same FLUX block routing via `is_flux = True` path | Smith #13, HIGH |

### 2B. Explicit Exclusion Patterns
**Source: Smith #19 (musubi-tuner, HIGH):**
```python
exclude_patterns = [
    r".*(img_mod\.lin|txt_mod\.lin|modulation\.lin).*",  # modulation layers
    r".*(norm).*"  # all normalization layers
]
```
Prevents LoRA injection into: image modulation linear, text modulation linear, guidance modulation linear, all LayerNorm/RMSNorm/QKNorm.

**Contrast: Smith #20 (sd-scripts)** explicitly INCLUDES `img_mod`, `txt_mod`, and `modulation` as targeted layers — this contradicts musubi-tuner's exclusion pattern. See **DISPUTE D**.

### 2C. LoRA Weight Structure
**Source: Smith #20 (sd-scripts, HIGH):**
- Standard: `lora_down` (in_dim → rank) + `lora_up` (rank → out_dim), Kaiming uniform / zero init
- Split QKV variant: separate Linear per split dimension
- Default rank: **4** (overridable per module via regex)
- Scale: `alpha / lora_dim` (alpha defaults to `lora_dim`)
- Forward: `output = org_forward(x) + lora_up(lora_down(x)) * multiplier * scale`

**Source: Smith #11 (DiffSynth, HIGH):**
- Rank: **32** (hardcoded in example script)
- Applied to: `dit` transformer only (not text encoder)
- `inject_adapter_in_model(pipe, lora_rank=32, model_names=["dit"])`

### 2D. Regularization (sd-scripts)
**Source: Smith #20 (HIGH):**
| Mechanism | Method |
|---|---|
| Module dropout | Skip entire LoRA branch → return `org_forward` |
| Rank dropout | Mask random dims + scale compensation `1/(1-p)` |
| Neuron dropout | `F.dropout()` between down/up |
| GGPO | Learned perturbation scaled by weight+gradient norms |
| LoRA+ | Differentiated LR: up-weights get `lora_plus_lr_ratio` multiplier |

### 2E. Module Naming Convention (sd-scripts)
**Source: Smith #20 (HIGH):**
- `lora_unet` → FLUX blocks
- `lora_te1` → CLIP text encoder
- `lora_te3` → T5XXL text encoder
- Example: `lora_unet_double_blocks_0_img_attn_to_q`

### 2F. Block-Level Control
**Source: Smith #20 (HIGH):** `train_double_block_indices` / `train_single_block_indices` accept range strings like `"0-5,10,15-18"` for selective LoRA block activation.

---

## SECTION 3 — VAE Latent Encoding

### 3A. VAE Channel Count
⚠️ **GENUINE DISPUTE A — see Section 8**

| Framework | VAE Channels | Spatial Reduction | Source |
|---|---|---|---|
| DiffSynth (Klein-9B) | **16** | 1/8 (H/8, W/8) | Smith #11, HIGH |
| SimpleTuner (FLUX.2) | **32** | unclear | Smith #18, HIGH |

### 3B. DiffSynth Latent Pipeline (16-ch, 1/8 spatial)
**Source: Smith #11 (HIGH, direct code):**

**Phase 1 — Noise Init:**
```
Input: (1, 128, H/16, W/16)
After reshape: (1, 128, H*W/256)
After permute: (1, H*W/256, 128)  ← sequence format
```
For 1024×1024: **4,096 tokens** (HIGH)

**Phase 2 — VAE Encoding:**
```
VAE output: (B, 16, H/8, W/8)
After rearrange B C H W → B (H W) C: (B, H*W/64, 16)
```
For 1024×1024: **16,384 tokens** (HIGH)

⚠️ **CORRECTION 1:** Smith #12 states "Latent reduction: 16× (H/16, W/16)" for the VAE — this is WRONG for the latent sequence fed to the transformer. The `height//16 * width//16` appears in `dynamic_shift_len` (for scheduler shift calculation only), not the actual latent shape. The VAE produces 1/8 spatial, giving seq_len = H*W/64 = 16,384 for 1024². Smith #11 is correct; Smith #12's "16×" is misattributed.

**Phase 3 — Edit Image Handling (inpainting):**
Source truncated in Smith #11 — details not captured.

### 3C. SimpleTuner Latent Pipeline (32-ch)
**Source: Smith #18 (HIGH, direct code):**

```
VAE output: (B, 32, H, W)
  ↓ _patchify_latents (2×2 spatial patch → channel)
Patchified: (B, 128, H/2, W/2)
  ↓ _pack_latents (flatten spatial)
Packed: (B, H*W/4, 128)  ← sequence for transformer
```

- `_patchify_latents`: `view → permute → reshape` grouping 2×2 spatial blocks into channel dim (32×4=128 channels)
- `_pack_latents`: `reshape → permute(0,2,1)`
- VAE extraction uses **argmax mode** (deterministic, not sampled): `retrieve_latents(..., sample_mode='argmax')`
- VAE scale factor: `2^(len(block_out_channels)-1)` = **8** for 4-block VAE (MEDIUM, computed)
- No patchification in `collate.py` — all deferred to pipeline (Smith #18, HIGH)

---

## SECTION 4 — Text Embedding Preparation

### 4A. Text Encoder Selection by Model Variant
**Agreement: Smiths #12 and #16**

| Model | Text Encoder | Notes |
|---|---|---|
| FLUX.2-dev | Mistral-Small-3.1-24B-Instruct-2503 | Loaded separately |
| Klein-4B | **Qwen3** | Bundled in checkpoint |
| Klein-9B | **Qwen3** | Bundled in checkpoint |

**Critical config detail (Smith #16, HIGH, PR #2664 merged 2026-04-01):** For Klein variants, `pretrained_text_encoder_model_name_or_path` must **NOT be set**; setting it causes download of wrong (Mistral) encoder. Issue #2643 (open as of 2026-04-01) confirms this still fails in SimpleTuner.

### 4B. DiffSynth Text Embedding Pathways
**Source: Smith #12 (HIGH):**

**Mistral-3 Small pathway (`Flux2Unit_PromptEmbedder`):**
- Hidden layers extracted: **(10, 20, 30)**
- Output: `(B, seq_len, 3×hidden_dim)` via stack + permute + reshape
- Max sequence length: **512 tokens**

**Qwen3 pathway (`Flux2Unit_Qwen3PromptEmbedder`):**
- Hidden layers extracted: **(9, 18, 27)**
- Output: same `(B, seq_len, 3×hidden_dim)` format
- Chat template applied with `enable_thinking=False`

### 4C. Text Position IDs (4D format)
**Strong agreement: Smiths #12 and #14**

```python
# DiffSynth (Smith #12):
t = torch.arange(1); h = torch.arange(1); w = torch.arange(1); l = torch.arange(seq_len)
text_ids = torch.cartesian_prod(t, h, w, l)  # → (seq_len, 4)

# ai-toolkit (Smith #14):
Position IDs: [time_coord, height_id, width_id, length_id] → (seq_len, 4)
```

Both frameworks independently produce 4D position IDs (t, h, w, l) for text sequences. **HIGH confidence, cross-validated.**

---

## SECTION 5 — Flow Matching Noise & Forward Pass

### 5A. Noise Interpolation Formula
⚠️ **GENUINE DISPUTE B — see Section 8**

| Framework | Formula | t=0 state | t=1 state | Source |
|---|---|---|---|---|
| DiffSynth | `(1-σ)*data + σ*noise` | pure data | pure noise | Smith #12, HIGH |
| ai-toolkit | `(1-t_01)*data + t_01*noise` | pure data | pure noise | Smith #14, HIGH |
| SimpleTuner (primary) | `t*data + (1-t)*noise` | pure noise | pure data | Smith #17, HIGH |
| SimpleTuner (TwinFlow/UCGM) | `(1-sigma)*data + sigma*noise` | pure data | pure noise | Smith #17, HIGH |

DiffSynth and ai-toolkit share identical convention (noise increases with t). SimpleTuner's primary flow matching formula has **reversed sign convention** relative to the other two.

### 5B. Training Target (Velocity Prediction)
**Agreement: Smiths #12 and #19**
```python
training_target = noise - input_latents  # DiffSynth (Smith #12)
target = noise - latents                 # musubi-tuner (Smith #19)
```
Both compute velocity as `noise - data`. **HIGH confidence, cross-validated.**

### 5C. Timestep Normalization
**Agreement: Smiths #12 and #14**
- Timestep range: **0–1000** (integer)
- Normalized to [0,1] for model input: `timestep / 1000` (explicit in both)
- Smith #14: "dit expects timestep normalized to [0,1] via timestep/1000" (HIGH)

### 5D. Model Forward Pass (ai-toolkit)
**Source: Smith #14 (HIGH, truncated):**
```python
txt, txt_ids = batched_prc_txt(text_embeddings.text_embeds)   # (B, seq_len, D), (B, seq_len, 4)
packed_latents, img_ids = batched_prc_img(latent_model_input) # (B, H*W, C), (B, H*W, 4)
```
Report truncated before loss computation.

### 5E. musubi-tuner Forward Pass
**Source: Smith #19 (HIGH):**
```python
noisy_model_input, img_ids = flux2_utils.prc_img(noisy_model_input)  # (B, HW, C), (B, HW, 4)
ctx, ctx_ids = flux2_utils.prc_txt(ctx_vec)                          # (B, 512, D)
guidance_vec = torch.full((bsize,), 1.0, ...)  # Fixed for Klein
timesteps = timesteps / 1000.0
model_pred = model(x=img_input, x_ids=img_input_ids, timesteps=timesteps, ctx=ctx, ctx_ids=ctx_ids, guidance=guidance_vec)
model_pred = rearrange(model_pred, "b (h w) c -> b c h w", h=packed_latent_height)
```

---

## SECTION 6 — Loss Computation

### 6A. DiffSynth Loss
**Source: Smith #12 (HIGH):**
```python
loss = F.mse_loss(noise_pred.float(), training_target.float())
loss = loss * pipe.scheduler.training_weight(timestep)
```
- Loss type: **MSE** between model prediction and velocity target
- Weighted by per-timestep Gaussian weight

### 6B. Gaussian Timestep Weighting (Bell-Shaped Mean-Normalized)
**Agreement: Smiths #12 and #14** — independently describe identical formula:
```python
# DiffSynth (Smith #12, flow_match.py):
steps = 1000
x = timesteps
y = torch.exp(-2 * ((x - steps/2) / steps)**2)
bsmntw_weighing = (y - y.min()) * (steps / y.sum())

# ai-toolkit (Smith #14, custom_flowmatch_sampler.py):
x = torch.arange(num_timesteps, dtype=torch.float32)
y = torch.exp(-2 * ((x - num_timesteps/2) / num_timesteps)**2)
y_shifted = y - y.min()
bsmntw_weighing = y_shifted * (num_timesteps / y_shifted.sum())
```
**Gaussian-shaped weighting centered at timestep 500, mean-normalized to 1.** HIGH confidence, cross-validated by two independent Smiths.

---

## SECTION 7 — Timestep Sampling Strategies

### 7A. DiffSynth Dynamic Shift (FLUX.2-Specific)
**Source: Smith #12 (HIGH):**
```python
sigma_min = 1 / num_inference_steps
sigmas = torch.linspace(sigma_start, sigma_min, num_inference_steps)
mu = 0.8  # or compute_empirical_mu(dynamic_shift_len)
sigmas = exp(μ) / (exp(μ) + (1/σ - 1))
timesteps = sigmas * 1000
```
μ=0.8 empirically chosen ("yields better training" — comment in source).

### 7B. ai-toolkit Timestep Modes (5 strategies)
**Source: Smith #14 (HIGH):**

| Mode | Method |
|---|---|
| `linear` | `torch.linspace(1000, 1, n)` |
| `flux_shift` | Dynamic μ based on image sequence length |
| `sigmoid` | Normal distribution → sigmoid for center bias |
| `lognorm_blend` | 75% log-normal + 25% linear (MEDIUM) |
| `weighted` | Default weighting scheme (MEDIUM) |

**Dynamic shift formula (flux_shift):**
```
mu = m * image_seq_len + b
where m = (max_shift - base_shift) / (max_seq_len - base_seq_len)
Config: base_seq_len=256, max_seq_len=4096, base_shift=0.5, max_shift=1.15, shift=3.0
```

**ai-toolkit scheduler config:**
```python
{
    "base_image_seq_len": 256,
    "base_shift": 0.5,
    "max_image_seq_len": 4096,
    "max_shift": 1.15,
    "num_train_timesteps": 1000,
    "shift": 3.0,
    "use_dynamic_shifting": True,
}
```

### 7C. SimpleTuner Timestep Strategies
**Source: Smith #17 (HIGH, updated 2026-04-04):**
```python
# From plan.py
if strategy == "uniform":
    offsets = torch.randint(0, max_step_offset + 1, (batch_size,), ...)
elif strategy == "biased_early":
    offsets = torch.round(torch.rand(...) ** 2 * max_step_offset).to(torch.long)
elif strategy == "biased_late":
    offsets = torch.round((1.0 - torch.rand(...) ** 2) * max_step_offset).to(torch.long)
```
- Strategies: **uniform** (default), **biased_early**, **biased_late**
- **NOT logit-normal** (explicitly confirmed absent from codebase, Smith #17)
- Sigma mapping: scheduler's native sigmas → linear fallback: `timestep / (num_train_timesteps - 1)`

**SimpleTuner Scheduled Sampling (advanced):**
ODE rollout for curriculum learning via Skrample samplers (UniPC, DPM++, Euler). Mini rollouts from source timestep → target timestep using model predictions.

---

## SECTION 8 — Framework Status & Readiness

### 8A. DiffSynth-Studio
**Source: Smiths #11, #12 (HIGH, repo date 2026-04-04, 12.2k stars)**
- Actively maintained, recent commits
- Supports Klein-9B via dedicated shell script + `Flux2ImageTrainingModule`
- Task modes: `sft`, `sft:data_process`, `direct_distill`
- Pipeline splitting: separates trainable vs. frozen models for gradient computation
- Dtype: **bfloat16** (full 16-bit, not 8-bit)

### 8B. ostris/ai-toolkit
**Source: Smiths #13, #14, #15 (HIGH, date 2026-04-04/05)**
- **No `is_flux2` detection** — Klein treated as generic FLUX via `arch == 'flux'`
- **No Klein-specific code paths** — shared pipeline with other FLUX variants
- **Known open issues as of 2026-04-04:**
  - #647: FLUX.2-klein support tracking
  - #653: Layer offloading broken for Klein-9B
  - #654: Training collapse
  - #691: GPU loading problems
- Support added via model plugin system (not core architecture), MEDIUM confidence

### 8C. SimpleTuner
**Source: Smiths #16, #17, #18 (HIGH, date 2026-03-31 to 2026-04-04)**
- Klein variants declared: `model_flavour='klein-4b'` and `'klein-9b'`
- **Partially functional**: checkpoints generated (checkpoint-1000 through -2250 seen in Issue #2660) but text encoder init incomplete
- Issue #2643 (open 2026-03-17): Still downloads Mistral instead of bundled Qwen3 for Klein
- PR #2664 (merged 2026-04-01): Documentation workaround, not code fix
- Klein-specific logic not found in `/helpers/models/flux2/__init__.py` or `common.py` by Smith

### 8D. kohya-ss/musubi-tuner
**Source: Smith #19 (HIGH, commit `23d3a5f6`, date not confirmed)**
- **Production-ready Klein support** with explicit `Klein9BParams` / `Klein4BParams` dataclasses
- Training entry: `flux_2_train_network.py`
- Network config: `networks/lora_flux_2.py`

### 8E. kohya-ss/sd-scripts
**Source: Smith #20 (MEDIUM — GitHub API rate limited, no commit date)**
- Smith #19 says Klein is exclusive to musubi-tuner; sd-scripts has only FLUX.1 Kontext
- Smith #20 labels `lora_flux.py` as "FLUX.2 LoRA" with 19/38 blocks — see **DISPUTE C**

---

## SECTION 9 — Latent Caching

### 9A. ai-toolkit Caching
**Source: Smith #15 (HIGH, code date 2026-04-05)**
- Format: **safetensors** (`safetensors.torch.load_file / save_file`)
- Location: `_latent_cache/` subdirectory alongside source images
- Naming: `{filename}_{BASE64_MD5_of_config}.safetensors` (padding stripped)
- Keys: `'latent'`, `'first_frame_latent'` (video), `'audio_latent'` (audio), `'num_frames'`
- Cache invalidation: config dict → sorted JSON → MD5 → base64 hash
- Load device: **CPU-first** (`device='cpu'`), GPU movement deferred to training loop
- `cleanup_latent()` unloads after use when `not is_caching_to_memory`
- Latents **never re-encoded** during training epochs (Smith #15, HIGH)

### 9B. SimpleTuner Caching
**Source: Smith #18 (HIGH)**
- Pre-cached VAE latents retrieved in collate
- Config: `cache_latents_to_disk: true` ("leave true unless you know what you're doing" — FLUX config note)
- No channel manipulation in collate — all patchification deferred to pipeline
- Backend: not specified (vs. safetensors in ai-toolkit)

---

## SECTION 10 — DISPUTES

### DISPUTE A — VAE Channel Count: 16 vs 32
| Claim | Smith | Confidence | Framework |
|---|---|---|---|
| VAE produces **16-channel** latents | #11 | HIGH | DiffSynth (Klein-9B shell script + code) |
| VAE produces **32-channel** latents | #18 | HIGH | SimpleTuner (direct `latent_channels = 32` in autoencoder.py) |

**Not necessarily a framework conflict** — these may be different VAE variants used for different FLUX.2 submodels. Smith #11 uses `black-forest-labs/FLUX.2-klein-base-9B:vae/` specifically. Smith #18 does not specify which FLUX.2 variant its VAE config applies to. **Opus should resolve: is Klein-base VAE 16-ch while FLUX.2-dev VAE is 32-ch?**

### DISPUTE B — Flow Matching Formula Sign Convention
| Claim | Smith | Convention |
|---|---|---|
| `(1-t)*data + t*noise` | #12 (DiffSynth), #14 (ai-toolkit) | t=0 → data; t=1 → noise |
| `t*data + (1-t)*noise` (primary FM) | #17 (SimpleTuner) | t=0 → noise; t=1 → data |

Both call it "flow matching." SimpleTuner also has `(1-sigma)*data + sigma*noise` in its TwinFlow/UCGM variant, which matches the other two. **Possible explanation:** SimpleTuner's primary formula may use a reversed time parameterization (σ_SimpleTuner = 1 − σ_others), or it's an implementation bug. **Opus should determine if these produce equivalent gradients under their respective timestep sampling.**

### DISPUTE C — sd-scripts FLUX.1 vs FLUX.2 Attribution
| Claim | Smith | Source |
|---|---|---|
| sd-scripts `lora_flux.py` covers **FLUX.2** (19 double, 38 single blocks) | #20 | MEDIUM confidence |
| Klein support **exclusive to musubi-tuner**; sd-scripts has FLUX.1 only | #19 | HIGH confidence |

Block counts of 19 double / 38 single match the **FLUX.1** architecture (not Klein-9B which has 8/24). Smith #20 may be describing FLUX.1 support mislabeled as FLUX.2, or sd-scripts has FLUX.2-dev (non-Klein) support. **Opus should verify.**

### DISPUTE D — Modulation Layer LoRA Targeting
| Claim | Smith | Framework |
|---|---|---|
| Modulation layers (`img_mod`, `txt_mod`, `modulation`) **EXCLUDED** from LoRA | #19 | musubi-tuner |
| Modulation layers (`img_mod`, `txt_mod`, `modulation`) **INCLUDED** in LoRA targets | #20 | sd-scripts |

Both are kohya family tools but have opposite policies on modulation layers. Could reflect genuine design choice difference between frameworks, or FLUX.1 vs FLUX.2 convention difference.

---

## SECTION 11 — CORRECTIONS

**CORRECTION 1 — Smith #12 misattributes 16× latent reduction to VAE:**
Smith #12 states "Latent reduction: 16× (H/16, W/16) — HIGH." However, this figure is extracted from `dynamic_shift_len = height//16 * width//16` which is passed to the scheduler for timestep μ calculation only. The actual VAE spatial reduction (per Smith #11, same framework/code) is **8×** (H/8, W/8), yielding sequence length H×W/64. The 16× figure applies to noise initialization shape (distinct from image latents). Smith #12 conflates these two distinct resolution points.

**CORRECTION 2 — Smith #20 FLUX.2 labeling is suspect:**
Smith #20 labels its findings as "FLUX.2 LoRA Network Module" with block counts 19/38 — these match FLUX.1 architecture. Given Smith #19's explicit statement that Klein is exclusive to musubi-tuner and sd-scripts only contains FLUX.1 Kontext in `lora_flux.py`, Smith #20 is likely describing FLUX.1 support incorrectly attributed to FLUX.2. All numerical findings from Smith #20 should be treated as **FLUX.1 reference data, not FLUX.2 Klein.**

**CORRECTION 3 — Smith #12 μ description is incomplete:**
Smith #12 states μ=0.8 with truncated explanation ("I can only say that it yields better training..."). The full formula from Smith #14 shows μ is dynamically computed from image sequence length via `calculate_shift()`. μ=0.8 is a default/fallback, not a fixed value. Dynamic μ is the production behavior.

---

## SECTION 12 — GAPS (Topics Not Covered by Chain B)

| Gap | Relevance | Notes |
|---|---|---|
| **Inference/generation pipeline** | High | All Smiths cover training only; no generation workflow |
| **VRAM requirements by framework** | High | No quantitative VRAM numbers for Klein LoRA training |
| **KV transfer mechanism** | High | Listed in MEMORY.md as project goal; zero coverage in Chain B |
| **Google Fonts dataset preprocessing** | High | MEMORY.md goal; not mentioned in any Smith |
| **Validation/eval during training** | Medium | No coverage of how LoRA quality is measured |
| **Quantization (GGUF/NF4/INT8)** | Medium | Smith #13 notes no Klein-specific quantization; no detail on what's available |
| **Edit image handling (inpainting)** | Medium | Smith #11 Phase 3 was truncated before completion |
| **SimpleTuner Qwen3 init mechanism** | Medium | Issue #2643 open; bundling mechanism not found in code search |
| **FLUX.2-dev vs Klein-base complete diff** | Medium | Partial info (architecture params); no systematic comparison |
| **musubi-tuner commit date** | Low | SHA `23d3a5f6` cited but no date |
| **Training throughput benchmarks** | Low | No tokens/sec, steps/sec, or time-to-convergence data |
| **Dataset format specifications** | Low | Only DiffSynth covers (metadata.csv); ai-toolkit/SimpleTuner/musubi-tuner dataset formats not detailed |
| **ai-toolkit forward pass completion** | Low | Smith #14 was truncated mid-function; loss computation not captured |

---

## SECTION 13 — HIGH-CONFIDENCE CROSS-VALIDATED FACTS

The following findings are confirmed by ≥2 independent Smiths from different frameworks:

| Fact | Smiths | Confidence |
|---|---|---|
| Velocity target = `noise − latents` | #12, #19 | ✅ HIGH, 2 frameworks |
| Gaussian-weighted loss centered at timestep 500 (bell-shaped, mean-normalized) | #12, #14 | ✅ HIGH, 2 frameworks |
| Timestep range 0–1000, normalized /1000 for model | #12, #14 | ✅ HIGH, 2 frameworks |
| Text/image position IDs are 4D: (t, h, w, l) shape (seq, 4) | #12, #14 | ✅ HIGH, 2 frameworks |
| Qwen3 text encoder bundled in Klein checkpoints | #12, #16 | ✅ HIGH, 2 frameworks |
| Mistral-Small-3.1-24B used for FLUX.2-dev (not Klein) | #12, #16 | ✅ HIGH, 2 frameworks |
| Klein variants have no guidance embedding (fixed 1.0) | #13, #19 | ✅ HIGH, 2 frameworks |
| Flow matching uses MSE on velocity prediction | #12, #19 | ✅ HIGH, 2 frameworks |
| Latent caching to disk pre-training is standard practice | #15, #18 | ✅ HIGH, 2 frameworks |
| Dynamic shift μ varies with image sequence length | #12, #14 | ✅ HIGH, 2 frameworks |

---

*End of Chain B organized findings. 10 Smiths processed (#11–#20). All unique signal preserved. 4 disputes flagged. 3 corrections issued. 13 gaps catalogued. Ready for Opus synthesis.*

============================================================
## Chain A — Anderson Report
============================================================

# CHAIN A — ORGANIZED FINDINGS FOR OPUS SYNTHESIS
**Triage date:** 2026-04-04 | **Smiths processed:** 10 | **Source repo:** huggingface/diffusers + black-forest-labs/flux2

---

## THEME 1: Latent Packing & Unpacking Operations

**Primary sources:** Smith #1 (SHA `1f3b5c3c`, 2026-04-05), Smith #2 (SHA `1f3b5c3c`, 2026-04-04)
**DEDUP NOTE:** Both Smiths accessed the same commit. All `_pack`/`_unpack`/`_patchify`/`_unpatchify` code is duplicated across both reports. Merged here; all confidence levels HIGH unless noted.

---

### 1.1 `_pack_latents` — Spatial → Sequence

**File:** `pipeline_flux2_klein.py` (copied from base `Flux2Pipeline`)

```python
@staticmethod
def _pack_latents(latents):
    batch_size, num_channels, height, width = latents.shape
    latents = latents.reshape(batch_size, num_channels, height * width).permute(0, 2, 1)
    return latents
```

| Step | Operation | Shape |
|------|-----------|-------|
| Input | — | `(B, C, H, W)` |
| Reshape | Flatten spatial | `(B, C, H×W)` |
| Permute `(0,2,1)` | Move channels last | `(B, H×W, C)` |
| Output | Sequence for transformer | `(B, H×W, C)` |

**Purpose:** Converts spatial feature map to token sequence for transformer attention. Token count = H×W per batch item.
**Usage site:** ~line 622, `latents = self._pack_latents(latents)  # [B,C,H,W] → [B,H*W,C]`
**Sources:** Smith #1, Smith #2 — AGREE, HIGH

---

### 1.2 `_patchify_latents` — Space-to-Channel (2×2 patches)

**File:** `pipeline_flux2_klein.py` (copied from base `Flux2Pipeline`)

```python
@staticmethod
def _patchify_latents(latents):
    batch_size, num_channels_latents, height, width = latents.shape
    latents = latents.view(batch_size, num_channels_latents, height // 2, 2, width // 2, 2)
    latents = latents.permute(0, 1, 3, 5, 2, 4)
    latents = latents.reshape(batch_size, num_channels_latents * 4, height // 2, width // 2)
    return latents
```

| Step | Operation | Shape |
|------|-----------|-------|
| Input | — | `(B, C, H, W)` |
| View | Split spatial into 2×2 blocks | `(B, C, H/2, 2, W/2, 2)` |
| Permute `(0,1,3,5,2,4)` | Gather patch elements to channel dim | `(B, C, 2, 2, H/2, W/2)` |
| Reshape | Merge patch dims into channels | `(B, C×4, H/2, W/2)` |
| Output | 4× channel expansion | `(B, C×4, H/2, W/2)` |

**Purpose:** Inverse pixel-shuffle — folds 2×2 spatial patches into channel dimension. Halves H and W, quadruples C.
**Usage site:** ~line 595, applied after VAE encoding of reference images: `image_latents = self._patchify_latents(image_latents)`
**BatchNorm applied after patchify:** Yes — normalizes with VAE's `bn.running_mean` and `bn.running_var` (Smith #1).
**Sources:** Smith #1, Smith #2 — AGREE, HIGH

---

### 1.3 `_unpatchify_latents` — Channel-to-Space (inverse of 1.2)

**File:** `pipeline_flux2_klein.py`, lines 360–366 (Smith #2)

```python
@staticmethod
def _unpatchify_latents(latents):
    batch_size, num_channels_latents, height, width = latents.shape
    latents = latents.reshape(batch_size, num_channels_latents // (2 * 2), 2, 2, height, width)
    latents = latents.permute(0, 1, 4, 2, 5, 3)
    latents = latents.reshape(batch_size, num_channels_latents // (2 * 2), height * 2, width * 2)
    return latents
```

| Step | Operation | Shape |
|------|-----------|-------|
| Input | — | `(B, C×4, H, W)` |
| Reshape | Separate patch structure | `(B, C, 2, 2, H, W)` |
| Permute `(0,1,4,2,5,3)` | Reorder spatial dims | `(B, C, H, 2, W, 2)` |
| Reshape | Reconstruct full resolution | `(B, C, H×2, W×2)` |
| Output | Full spatial resolution | `(B, C, H×2, W×2)` |

**Purpose:** Inverse of `_patchify_latents`. Called before VAE decode.
**Sources:** Smith #1 (code listed), Smith #2 (line numbers + transformation flow detail) — AGREE, HIGH

---

### 1.4 `_unpack_latents_with_ids` — Position-Indexed Scatter (inverse of 1.1)

**File:** `pipeline_flux2_klein.py`, lines 419–448 (Smith #2)

```python
@staticmethod
def _unpack_latents_with_ids(
    x: torch.Tensor, x_ids: torch.Tensor, height: int | None = None, width: int | None = None
) -> list[torch.Tensor]:
    x_list = []
    for data, pos in zip(x, x_ids):
        _, ch = data.shape
        h_ids = pos[:, 1].to(torch.int64)
        w_ids = pos[:, 2].to(torch.int64)
        h = height if height is not None else torch.max(h_ids) + 1
        w = width if width is not None else torch.max(w_ids) + 1
        flat_ids = h_ids * w + w_ids
        out = torch.zeros((h * w, ch), device=data.device, dtype=data.dtype)
        out.scatter_(0, flat_ids.unsqueeze(1).expand(-1, ch), data)
        out = out.view(h, w, ch).permute(2, 0, 1)
        x_list.append(out)
    return torch.stack(x_list, dim=0)
```

**Input:**
- `x`: `(B, L, C)` — packed sequence (L tokens)
- `x_ids`: `(B, L, 4)` — per-token position coords `[T, H, W, L]`
- `height`, `width`: explicit spatial dims (optional; avoids GPU→CPU sync from `torch.max().item()`)

**Operation sequence:**
1. Extract H-coord from `x_ids[:, 1]`, W-coord from `x_ids[:, 2]`
2. Flat index: `flat_id = h_id × w + w_id` (row-major)
3. Scatter tokens into `(H×W, C)` buffer
4. Reshape → `(H, W, C)` → permute → `(C, H, W)`

**Output:** `(B, C, H, W)` spatial latent tensor
**Sources:** Smith #2 — HIGH (only reporter)

---

### 1.5 Pipeline Integration: Full Inverse Sequence

**File:** `pipeline_flux2_klein.py`, lines 1114–1119 (Smith #2)

```python
latent_height = 2 * (int(height) // (self.vae_scale_factor * 2))
latent_width  = 2 * (int(width)  // (self.vae_scale_factor * 2))
latents = self._unpack_latents_with_ids(latents, latent_ids, latent_height // 2, latent_width // 2)
# → (B, C×4, H/2, W/2)
latents = latents * latents_bn_std + latents_bn_mean   # BatchNorm denormalization
latents = self._unpatchify_latents(latents)
# → (B, C, H, W) final latents → VAE decode
```

**Canonical operation table (Smith #2, confirmed by Smith #1):**

| Operation | Direction | Input | Output | Mechanism |
|-----------|-----------|-------|--------|-----------|
| `_pack_latents` | Forward | `(B, C, H, W)` | `(B, H×W, C)` | Reshape + permute |
| `_patchify_latents` | Forward | `(B, C, H, W)` | `(B, C×4, H/2, W/2)` | 2×2 patch → channel |
| `_unpack_latents_with_ids` | Inverse | `(B, H×W, C)` + IDs | `(B, C×4, H/2, W/2)` | Scatter by position IDs |
| `_unpatchify_latents` | Inverse | `(B, C×4, H/2, W/2)` | `(B, C, H, W)` | Channel → 2×2 spatial |

**Sources:** Smith #1, Smith #2 — AGREE, HIGH

---

### 1.6 FLUX.1 vs FLUX.2 Klein: Different `_pack_latents` Signatures

**⚠ IMPORTANT DISTINCTION** (flagged by cross-reading Smith #1 and Smith #9):

| Pipeline class | Signature | Source |
|----------------|-----------|--------|
| `Flux2KleinPipeline._pack_latents` | `_pack_latents(latents)` — single tensor arg | Smith #1 |
| `FluxPipeline._pack_latents` | `_pack_latents(noisy_input, batch_size=..., num_channels_latents=..., height=..., width=...)` — explicit dims | Smith #9 |

**Not a conflict** — these are different classes for different models. Smith #9 covers the FLUX.1 DreamBooth script; Smith #1 covers FLUX.2 Klein. Both HIGH confidence within their respective scope.

---

## THEME 2: Position ID Tensors

**Primary source:** Smith #3 (commit `fbe8a75a`, 2026-04-04) — sole reporter on this theme, HIGH confidence throughout.

---

### 2.1 `_prepare_text_ids`

**Lines:** 302–315, `pipeline_flux2_klein.py`
**Input:** `x` — text embeddings, shape `(B, L, D)`
**Output:** `(B, L, 4)` — position coordinates per text token

**Construction logic (pseudo):**
```python
for i in range(B):
    t = torch.arange(1)   # → [0], fixed
    h = torch.arange(1)   # → [0], fixed
    w = torch.arange(1)   # → [0], fixed
    l = torch.arange(L)   # → [0..L-1], sequence position
    coords = torch.cartesian_prod(t, h, w, l)  # (L, 4)
    out_ids.append(coords)
return torch.stack(out_ids)  # (B, L, 4)
```

**4D coordinate layout:** `[T=0, H=0, W=0, L=token_index]`
**Interpretation:** Text tokens are undifferentiated in spatial space; only L-coordinate varies.

---

### 2.2 `_prepare_latent_ids`

**Lines:** 317–347, `pipeline_flux2_klein.py`
**Input:** `latents` — shape `(B, C, H, W)`
**Output:** `(B, H×W, 4)` — position coordinates per spatial patch

**Construction:**
```python
t = torch.arange(1)      # [0], fixed
h = torch.arange(height) # [0..H-1]
w = torch.arange(width)  # [0..W-1]
l = torch.arange(1)      # [0], fixed
latent_ids = torch.cartesian_prod(t, h, w, l)  # (H*W, 4)
latent_ids = latent_ids.unsqueeze(0).expand(batch_size, -1, -1)  # (B, H*W, 4)
```

**4D coordinate layout:** `[T=0, H=row, W=col, L=0]`
**Interpretation:** Each spatial patch gets unique H, W coords. T and L frozen at 0. All batches share identical spatial structure.

---

### 2.3 `_prepare_image_ids`

**Lines:** 349–398, `pipeline_flux2_klein.py`
**Input:** `image_latents` — list of `(1, C, H_i, W_i)` tensors (variable spatial dims); `scale` — default `10`
**Output:** `(1, N_total, 4)` where `N_total = Σ(H_i × W_i)`

**Construction:**
```python
t_coords = [scale + scale * t for t in torch.arange(0, len(image_latents))]
# With scale=10: t values = [10, 20, 30, ...]

for x, t in zip(image_latents, t_coords):
    x = x.squeeze(0)  # (C, H, W)
    _, height, width = x.shape
    x_ids = torch.cartesian_prod(t, torch.arange(height), torch.arange(width), torch.arange(1))
    # (H*W, 4)
    image_latent_ids.append(x_ids)

image_latent_ids = torch.cat(image_latent_ids, dim=0)   # (N_total, 4)
image_latent_ids = image_latent_ids.unsqueeze(0)         # (1, N_total, 4)
```

**4D coordinate layout:** `[T=scale*(i+1), H=row, W=col, L=0]` per reference image `i`
**Time separation mechanism:** Each reference image gets a unique T-offset (`10, 20, 30, ...`), making different conditioning images distinguishable in the model's temporal dimension. Same H/W structure per-image.

---

### 2.4 Summary Table (from Smith #3)

| Function | Input Shape | Output Shape | T | H | W | L |
|----------|------------|-------------|---|---|---|---|
| `_prepare_text_ids` | `(B, L, D)` | `(B, L, 4)` | 0 | 0 | 0 | `[0..L-1]` |
| `_prepare_latent_ids` | `(B, C, H, W)` | `(B, H×W, 4)` | 0 | `[0..H-1]` | `[0..W-1]` | 0 |
| `_prepare_image_ids` | `List[(1,C,H,W)]` | `(1, N_total, 4)` | `[10,20,30…]` | `[0..H_i-1]` | `[0..W_i-1]` | 0 |

**Coordinate index alignment with `_unpack_latents_with_ids`:** Confirmed consistent — that function reads `pos[:, 1]` as H and `pos[:, 2]` as W, matching the `[T, H, W, L]` layout above (Smith #2 × Smith #3 cross-check).

---

## THEME 3: Transformer Architecture & Forward Pass

**Primary sources:** Smith #4 (SHA `5c90f3a4`, 2026-04-04), Smith #8 (accessed 2026-04-05)

---

### 3.1 `Flux2Transformer2DModel.forward()` — Complete Signature

**File:** `src/diffusers/models/transformers/transformer_flux2.py`
**Source:** Smith #4 — HIGH confidence

```python
@apply_lora_scale("joint_attention_kwargs")
def forward(
    self,
    hidden_states: torch.Tensor,
    encoder_hidden_states: torch.Tensor = None,
    timestep: torch.LongTensor = None,
    img_ids: torch.Tensor = None,
    txt_ids: torch.Tensor = None,
    guidance: torch.Tensor = None,
    joint_attention_kwargs: dict[str, Any] | None = None,
    return_dict: bool = True,
    kv_cache: "Flux2KVCache | None" = None,
    kv_cache_mode: str | None = None,
    num_ref_tokens: int = 0,
    ref_fixed_timestep: float = 0.0,
) -> torch.Tensor | Flux2Transformer2DModelOutput:
```

**Parameter inventory:**

| # | Parameter | Type | Default | Role |
|---|-----------|------|---------|------|
| 1 | `hidden_states` | `torch.Tensor` | **REQUIRED** | Input latent; shape `(batch, image_seq_len, in_channels)` |
| 2 | `encoder_hidden_states` | `torch.Tensor` | `None` | Text/context conditional embeddings |
| 3 | `timestep` | `torch.LongTensor` | `None` | Denoising step indicator |
| 4 | `img_ids` | `torch.Tensor` | `None` | Image patch position IDs (RoPE) |
| 5 | `txt_ids` | `torch.Tensor` | `None` | Text token position IDs (RoPE) |
| 6 | `guidance` | `torch.Tensor` | `None` | Guidance tensor for distilled variants (e.g., FLUX.2-Krea) |
| 7 | `joint_attention_kwargs` | `dict \| None` | `None` | Kwargs passed to attention processors |
| 8 | `return_dict` | `bool` | `True` | `True` → `Flux2Transformer2DModelOutput`; `False` → tuple |
| 9 | `kv_cache` | `Flux2KVCache \| None` | `None` | Cached KV tensors from prior denoising steps |
| 10 | `kv_cache_mode` | `str \| None` | `None` | `"extract"` (first step) or `"cached"` (reuse) |
| 11 | `num_ref_tokens` | `int` | `0` | Count of reference image tokens |
| 12 | `ref_fixed_timestep` | `float` | `0.0` | Fixed timestep for reference token modulation |

**Decorator:** `@apply_lora_scale("joint_attention_kwargs")` — auto-applies LoRA scaling to attention kwargs.
**Source:** Smith #4, HIGH

---

### 3.2 Klein9B: `use_guidance_embed = False`

**File:** `black-forest-labs/flux2`, `src/flux2/model.py` (accessed 2026-04-05)
**Source:** Smith #8 — HIGH confidence

```python
@dataclass
class Klein9BParams:
    use_guidance_embed: bool = False
```

**Architectural comparison:**

| Parameter | Klein9B | FLUX.2-dev (32B) | FLUX.1-dev |
|-----------|---------|-----------------|-----------|
| `use_guidance_embed` | **False** | True | True |
| `context_in_dim` | 12,288 | 15,360 | 3,072 |
| `hidden_size` | 4,096 | 6,144 | 3,072 |
| `num_heads` | 32 | 48 | 24 |

**Forward-pass consequence:**
- **Klein9B:** `vec = self.time_in(timestep_emb)` — timestep only, no guidance fusion
- **FLUX.2-dev:** `vec = vec + self.guidance_in(guidance_emb)` — guidance fused into modulation path

**Consequences of `use_guidance_embed=False`:**
1. `guidance_in` MLP embedder is never instantiated
2. Modulation vectors (`double_stream_modulation_img`, `double_stream_modulation_txt`, `single_stream_modulation`) are computed from timestep-only embeddings
3. `guidance` parameter in the forward signature (Theme 3.1) is **silently ignored** at inference
4. No classifier-free guidance scaling available — this is a training-time decision, not bypassable at inference
5. Klein was trained without guidance distillation; FLUX.2-dev was trained with it

**Sources:** Smith #4 (forward sig), Smith #8 (architectural detail) — AGREE, HIGH

---

### 3.3 Timestep Normalization to Transformer

**Finding (cross-Smith):** The transformer receives timesteps in `[0, 1]` range via explicit `/1000` division in the pipeline/training script — NOT inside the scheduler.

- Smith #9 (FLUX.1 training): `timestep=timesteps / 1000` in transformer call (HIGH)
- Smith #7 (scheduler): Scheduler does NOT divide by 1000; raw `[0, 1000]` values stored in `self.timesteps` (HIGH)
- **Cross-check:** CONSISTENT — pipeline is responsible for the `/1000` normalization, scheduler is agnostic to it

**Sources:** Smith #7, Smith #9 — AGREE

---

## THEME 4: VAE Architecture & Normalization

**Primary sources:** Smith #5 (2025 copyright, current main), Smith #6 (April 2026), Smith #2 (BatchNorm denorm in pipeline)

---

### 4.1 `AutoencoderKLFlux2` — Architecture

**File:** `src/diffusers/models/autoencoders/autoencoder_kl_flux2.py`
**Source:** Smith #5 — HIGH confidence

**Latent channels:**
- Config parameter: `latent_channels: int = 32` (line 106)
- Encoder output: `64` channels (2×32, because `double_z=True`) — splits into mean + logvar
- Post-sampling (from `DiagonalGaussianDistribution`): **32 channels** — this is what the pipeline works with

**Spatial downscale:**
- 4 down-block types defined; only 3 actually downsample (`add_downsample=not is_final_block`)
- Total: **8× spatial downscale** (2³)
- Confirmed: `tile_latent_min_size = sample_size / 2^(4-1) = sample_size / 8`

**`encode()` method — 3 stages:**
```python
# Stage 1: Optional slicing
h = self._encode(x)          # Encoder → quant_conv (1×1 conv)
# Stage 2: Parameterize
posterior = DiagonalGaussianDistribution(h)   # Splits 64ch → mean(32) + logvar(32)
# Stage 3: Return
return AutoencoderKLOutput(latent_dist=posterior)
```

**BatchNorm2d layer (defined in VAE class):**
```python
self.bn = nn.BatchNorm2d(
    math.prod(patch_size) * latent_channels,  # (2×2)×32 = 128 channels
    affine=False,
    track_running_stats=True,
)
```
`patch_size=(2, 2)` — aligns with `_patchify_latents` which produces C×4 channels.
Smith #5 notes this BN "defined but never called" in `forward/encode/decode` methods — see **Dispute D1** below.

---

### 4.2 VAE Normalization Parameters

**Source:** Smith #6 — HIGH confidence for parameter values; MEDIUM for confirmed equivalence to Klein variants

**Documented values for FLUX.2:**
- `scaling_factor`: **0.3611**
- `shift_factor`: **0.1159**

**Normalization formula (encode → transformer):**
```python
latents = (latents - vae.config.shift_factor) * vae.config.scaling_factor
```

**Denormalization formula (transformer → decode):**
```python
latents = (latents / vae.config.scaling_factor) + vae.config.shift_factor
```

**Note on Klein VAE parity:** Smith #6 (MEDIUM) states FLUX.2-klein-base-9B shares the same VAE (`flux2-vae.safetensors`) as FLUX.2-dev, implying these values apply to Klein. Not directly verified from `vae/config.json` due to auth walls.

**⚠ LABELING ERROR IN Smith #6 — see Correction C1 below.**

---

### 4.3 FLUX.2 Klein BatchNorm Denormalization (Pipeline-Level)

**Source:** Smith #2 (HIGH), corroborated by Smith #1 and Smith #5

After `_unpack_latents_with_ids`, before `_unpatchify_latents`, the Klein pipeline applies:
```python
latents = latents * latents_bn_std + latents_bn_mean   # denorm using VAE BatchNorm stats
```
where `latents_bn_std` and `latents_bn_mean` come from `vae.bn.running_var` and `vae.bn.running_mean`.

**This is DISTINCT from the shift_factor/scaling_factor normalization in 4.2.** See **Dispute D2** for implications.

---

### 4.4 FLUX.1 vs FLUX.2 Latent Channels — Important Distinction

**⚠ Do not conflate these:**

| Model | VAE Latent Channels | Source |
|-------|---------------------|--------|
| FLUX.1 (dev/schnell) | **4 channels** | Smith #9 (FLUX.1 DreamBooth script) |
| FLUX.2 Klein | **32 channels** | Smith #5 (autoencoder_kl_flux2.py, HIGH) |

Smith #9's mention of "4×64×64, 4 channels" is FLUX.1-specific. It does not conflict with Smith #5's 32-channel finding; they refer to different models.

---

## THEME 5: `FlowMatchEulerDiscreteScheduler`

**Primary source:** Smith #7 (SHA `1021abf0`, April 2026) — sole reporter, HIGH confidence on code-derived values

---

### 5.1 Initial Schedule Creation

```python
timesteps = np.linspace(1, num_train_timesteps, num_train_timesteps)[::-1].copy()
# num_train_timesteps default: 1000 (HIGH)
sigmas = timesteps / num_train_timesteps
sigmas = shift * sigmas / (1 + (shift - 1) * sigmas)  # when use_dynamic_shifting=False
# shift default: 1.0 (HIGH) → simplifies to identity: sigmas = sigmas (MEDIUM, calculated)
self.timesteps = sigmas * num_train_timesteps
```

With default `shift=1.0`: linear sigma schedule over `[0, 1]`.

**Sigma bounds:**
```python
self.sigma_min = self.sigmas[-1].item()
self.sigma_max = self.sigmas[0].item()
```

---

### 5.2 Alternative Sigma Schedules

| Schedule | Formula | Key Params |
|----------|---------|------------|
| Karras | Standard Karras | `rho=7.0` (HIGH) |
| Exponential | `exp(linspace(log(σ_max), log(σ_min), steps))` | — |
| Beta | Beta distribution | `alpha=0.6, beta=0.6` (HIGH) |

---

### 5.3 Runtime Step Resolution

`step()` uses `index_for_timestep()` — direct value matching against `self.timesteps`. No internal `/1000` scaling. Scheduler stores timesteps as `sigmas * num_train_timesteps` (raw `[0, 1000]` range).

**Critical:** Timestep scaling to `[0, 1]` for the transformer is the pipeline's responsibility (confirmed in Smith #9 for FLUX.1; see Theme 3.3).

**Source:** Smith #7 — HIGH

---

### 5.4 Noisy Input Construction

```python
noisy_model_input = (1.0 - sigmas) * model_input + sigmas * noise
```
Flow-matching interpolation between clean latent and Gaussian noise. (Also in Smith #9, same formula — AGREE, HIGH.)

---

## THEME 6: Training Loop & Loss (FLUX.1 DreamBooth LoRA)

**⚠ Scope note:** Smith #9 and Smith #10 both cover `train_dreambooth_lora_flux.py` — the **FLUX.1** DreamBooth LoRA training script. Architecture-specific values (4-channel latents, scale factor 8) are FLUX.1 values. Do not assume parity with FLUX.2 Klein training without separate confirmation.

**Primary sources:** Smith #9 (SHA `e0e7d2e4`, 2026-04-04), Smith #10 (2026-04-05) — DEDUP below

---

### 6.1 Training Loop Sequence (DEDUPED from Smith #9 + #10)

Both Smiths report the same sequence with consistent detail. Smith #10 adds deeper loss mechanics.

**Step 1 — VAE Encode:**
```python
model_input = vae.encode(pixel_values).latent_dist.sample()
model_input = (model_input - vae_config_shift_factor) * vae_config_scaling_factor
```
- Input: 512×512 RGB → `(B, 4, 64, 64)` latent (FLUX.1 specific)
- Normalize with `(x - shift) * scale`

**Step 2 — Noise Addition (Flow Matching):**
```python
noise = torch.randn_like(model_input)
sigmas = get_sigmas(timesteps, n_dim=model_input.ndim, dtype=model_input.dtype)
noisy_model_input = (1.0 - sigmas) * model_input + sigmas * noise
```

**Step 3 — Pack Latents:**
```python
packed_noisy_model_input = FluxPipeline._pack_latents(
    noisy_model_input,
    batch_size=..., num_channels_latents=..., height=..., width=...
)
```
FLUX.1 version takes explicit dims (cf. Theme 1.6).

**Step 4 — Transformer Forward:**
```python
model_pred = transformer(
    hidden_states=packed_noisy_model_input,
    timestep=timesteps / 1000,              # normalized to [0,1]
    guidance=guidance,
    pooled_projections=pooled_prompt_embeds,
    encoder_hidden_states=prompt_embeds,
    txt_ids=text_ids,
    img_ids=latent_image_ids,
    return_dict=False,
)[0]
```

**Step 5 — Unpack Latents:**
```python
model_pred = FluxPipeline._unpack_latents(
    model_pred,
    height=model_input.shape[2] * vae_scale_factor,   # 64 × 8 = 512
    width=model_input.shape[3] * vae_scale_factor,    # 64 × 8 = 512
    vae_scale_factor=vae_scale_factor,                 # = 8
)
```

**Step 6 — Compute Loss:** (see 6.2 below)

**Key numbers (FLUX.1 script, both Smiths agree):**

| Value | Number | Confidence |
|-------|--------|------------|
| VAE latent shape | `(B, 4, 64, 64)` | HIGH |
| VAE scale factor | 8 | HIGH |
| Timestep input range | `[0, 1000]` → normalized to `[0, 1]` | HIGH |
| Code lines (actual) | ~1365–1445 (Smith #9 corrects user's "1740–1820") | HIGH |

---

### 6.2 Loss Computation (DEDUPED from Smith #9 + #10)

Smith #10 is the authoritative source; Smith #9 is consistent but less detailed.

**Target definition:**
```python
target = noise - model_input   # flow vector: clean → noise
```

**Loss formula:**
```python
weighting = compute_loss_weighting_for_sd3(weighting_scheme=args.weighting_scheme, sigmas=sigmas)
loss = torch.mean(
    (weighting.float() * (model_pred.float() - target.float()) ** 2)
    .reshape(target.shape[0], -1),
    1,
)
loss = loss.mean()
```
- **Reduction:** Per-sample mean over flattened spatial dims → batch mean
- **Type:** Weighted MSE (flow-matching residual)

---

### 6.3 Weighting Schemes (Smith #10, HIGH)

**Critical distinction from Smith #10:** `--weighting_scheme` controls TWO separate things depending on scheme:

**Schemes that affect loss weight (applied to MSE directly):**

| Scheme | Loss weight formula | Notes |
|--------|---------------------|-------|
| `sigma_sqrt` | `σ^(-2.0)` | Upweights low-noise steps |
| `cosmap` | `2 / (π × (1 - 2σ + 2σ²))` | Cosine-mapped weighting |
| `none` | `ones_like(σ)` | Uniform (default) |

**Schemes that affect only timestep sampling density (loss weight = uniform):**

| Scheme | Sampling formula | Params |
|--------|-----------------|--------|
| `logit_normal` | `u = sigmoid(N(logit_mean, logit_std))` | `logit_mean=0.0`, `logit_std=1.0` |
| `mode` | Rejection sampling with cosine bias | `mode_scale=1.29` |
| `sigma_sqrt`, `cosmap`, `none` | `u = uniform(0, 1)` | — |

---

### 6.4 Sigma Lookup (`get_sigmas`)

```python
def get_sigmas(timesteps, n_dim=4, dtype=torch.float32):
    sigmas = noise_scheduler_copy.sigmas.to(device=accelerator.device, dtype=dtype)
    schedule_timesteps = noise_scheduler_copy.timesteps.to(accelerator.device)
    step_indices = [(schedule_timesteps == t).nonzero().item() for t in timesteps]
    sigma = sigmas[step_indices].flatten()
    while len(sigma.shape) < n_dim:
        sigma = sigma.unsqueeze(-1)
    return sigma
```
Lookup by exact value match; unsqueezes to broadcast against latent shape.
**Source:** Smith #10 — HIGH

---

### 6.5 Prior Preservation Loss (Smith #9 + #10, AGREE)

```python
if args.with_prior_preservation:
    model_pred, model_pred_prior = torch.chunk(model_pred, 2, dim=0)
    target, target_prior = torch.chunk(target, 2, dim=0)
    prior_loss = torch.mean(
        (weighting * (model_pred_prior - target_prior) ** 2).reshape(target_prior.shape[0], -1), 1
    ).mean()
    loss = loss + args.prior_loss_weight * prior_loss
```
Batch split: first half = instance images, second half = class prior. Losses computed separately, combined with `prior_loss_weight`.
**Sources:** Smith #9, Smith #10 — AGREE, HIGH

---

### 6.6 Key Default Hyperparameters (Smith #10, HIGH)

| Parameter | Default |
|-----------|---------|
| `logit_mean` | 0.0 |
| `logit_std` | 1.0 |
| `mode_scale` | 1.29 |
| `sigma_sqrt` exponent | -2.0 |
| cosmap numerator | `2/π ≈ 0.6366` |

---

## CORRECTIONS

### C1 — Labeling Error in Smith #6 (Normalization direction)

**Smith #6** labels `(latents / scaling_factor) + shift_factor` as "Latent Normalization Before Transformer." This is **incorrect labeling.** That formula is the **denormalization** direction (transforms from model latent space back to VAE space, used before VAE decode). The normalization before transformer is:
```python
(latents - shift_factor) * scaling_factor
```
which Smith #6 itself calls "Inverse operation during encoding." The labels are inverted in Smith #6.

**Correct mapping:**
- **After VAE encode / before transformer:** `(x - shift) * scale` ← NORMALIZATION
- **After denoising / before VAE decode:** `(x / scale) + shift` ← DENORMALIZATION

**Evidence:** Smith #9 (`(model_input - shift) * scale` in training loop, clearly post-encode, HIGH) contradicts Smith #6's labeling. The underlying values (0.3611, 0.1159) are unaffected.

---

### C2 — Smith #9 Line Number Correction (Self-corrected)

Smith #9 itself flags this: the user-specified range `1740–1820` does not contain the training loop. Actual location: **lines ~1365–1445**. Smith #9 reports this as a self-correction; confirmed by code search.

---

### C3 — Smith #5 BatchNorm "Never Called" Claim Needs Qualification

Smith #5 (MEDIUM confidence) states the `BatchNorm2d` in the VAE is "defined but never called" in the provided forward/encode/decode methods. However:
- Smith #1 (HIGH) states "Batch norm applied after patchify: Normalizes with VAE's `bn.running_mean` and `bn.running_var`"
- Smith #2 (HIGH) shows `latents * latents_bn_std + latents_bn_mean` called in the pipeline with BN stats

**Resolution:** The BN is not called from within `autoencoder_kl_flux2.py`'s own `forward()` — but its `running_mean`/`running_var` stats are **read externally by the pipeline** (`pipeline_flux2_klein.py`) for the patchified latent normalization step. Smith #5's claim is technically accurate in scope (internal VAE methods) but creates a misleading impression. The BN stats are live and actively used; they're just consumed pipeline-side, not VAE-side.

---

## DISPUTES

### D1 — FLUX.2 Klein Normalization Mechanism: BatchNorm vs shift_factor/scaling_factor

**Smith #2 (HIGH):** Klein pipeline denormalizes with `latents * bn_std + bn_mean` (BatchNorm running stats from VAE).

**Smith #6 (HIGH for values, MEDIUM for Klein parity):** Documents `shift_factor=0.1159`, `scaling_factor=0.3611` as the normalization mechanism; asserts Klein shares the same VAE and these apply.

**Nature of dispute:** These may describe **different normalization operations in the same pipeline**, not competing mechanisms:
- `(x - shift) * scale` / `(x / scale) + shift` — applied to the VAE latent for model-space normalization (FLUX.1 style, also present in FLUX.2?)
- `x * bn_std + bn_mean` — applied to the patchified latent specifically, using BN running stats

**Or** FLUX.2 Klein may have replaced the shift/scale normalization with BN-based normalization as an architectural change. This cannot be resolved from the current Smiths alone.

**Signal to preserve:** Both mechanisms are real. Their precise interaction in the FLUX.2 Klein pipeline (whether they coexist or one replaces the other) requires direct pipeline code inspection at lines covering the full latent preprocessing sequence.

---

### D2 — Klein9B `context_in_dim` Value Scope

Smith #8 (HIGH) reports `context_in_dim=12,288` for Klein9B from `black-forest-labs/flux2`. Smith #4 (HIGH) documents the diffusers transformer forward signature but does not specify `encoder_hidden_states` shape. **Not a direct conflict**, but there is an unresolved question: does the diffusers implementation of `Flux2Transformer2DModel` enforce `12,288` for Klein or is this an upstream-only value? No Smith directly addresses the diffusers-side shape constraint.

---

## GAPS

The following topics are **not covered** by any Smith in Chain A:

| Gap # | Topic | Why it matters |
|-------|-------|----------------|
| G1 | **KV cache mechanism** (`kv_cache`, `kv_cache_mode` in forward sig) | Forward sig documented (Smith #4) but operational semantics of `"extract"` vs `"cached"` modes unresearched |
| G2 | **Text encoder architecture** for FLUX.2 Klein (CLIP vs T5, tokenizer, pooled vs non-pooled) | `encoder_hidden_states` shape (`context_in_dim=12,288`) implies very large context dim; source not explained |
| G3 | **Double-stream vs single-stream attention blocks** in Klein9B transformer | Modulation vectors named in Smith #8 but block architecture not described |
| G4 | **Reference image conditioning mechanics** beyond ID tensors | Smith #3 covers IDs; how they interact with attention (cross-attn, concat, etc.) unresearched |
| G5 | **FLUX.2 Klein-specific training script** | Smith #9/#10 cover FLUX.1 DreamBooth; Klein training with 32-ch latents and BN normalization may differ significantly |
| G6 | **BN running stats update during training** | BatchNorm in VAE with `track_running_stats=True` and `affine=False` — when/how stats accumulate, frozen vs live during fine-tuning |
| G7 | **Full inference denoising loop** for Klein pipeline | Packing/unpacking ops covered; the surrounding denoising loop (CFG, step scheduling, etc.) not directly mapped |
| G8 | **LoRA target modules for FLUX.2 Klein** | LoRA training mentioned in memory context (`project_lora_training.md`) but not covered by any Chain A Smith |
| G9 | **VAE decode path** | Encode path covered (Smith #5); decode path (including `_unpatchify_latents` → `vae.decode()` integration) not fully traced |
| G10 | **Exact `vae/config.json` for Klein9B** | Smith #6 acknowledges auth-wall blockage; shift/scaling values cited from documentation, not raw config file |
| G11 | **Guidance distillation training details** | Smith #8 mentions FLUX.2-dev was trained with guidance distillation; Klein was not — details of what that means for inference behavior not explored |

---

## CONFIDENCE INVENTORY

| Finding | Confidence | Agreement across Smiths |
|---------|------------|------------------------|
| `_pack_latents` signature + transforms | HIGH | Smith #1 + #2 |
| `_patchify_latents` signature + transforms | HIGH | Smith #1 + #2 |
| `_unpatchify_latents` signature + transforms | HIGH | Smith #1 + #2 |
| `_unpack_latents_with_ids` signature + logic | HIGH | Smith #2 (sole) |
| Full pipeline inverse sequence (lines 1114–1119) | HIGH | Smith #2 (sole) |
| ID tensor 4D layout `[T, H, W, L]` | HIGH | Smith #3 (sole) |
| `_prepare_image_ids` time separation (scale=10) | HIGH | Smith #3 (sole) |
| `Flux2Transformer2DModel.forward()` signature | HIGH | Smith #4 (sole) |
| Klein9B `use_guidance_embed=False` | HIGH | Smith #8 (sole) |
| Klein9B architectural dims | HIGH | Smith #8 (sole) |
| FLUX.2 VAE latent_channels=32 | HIGH | Smith #5 (sole) |
| VAE spatial downscale = 8× | HIGH | Smith #5, Smith #9 (FLUX.1 confirms 8×) |
| shift_factor=0.1159, scaling_factor=0.3611 | HIGH | Smith #6 |
| BN normalization in Klein pipeline | HIGH | Smith #1, #2 |
| Klein shares VAE with FLUX.2-dev | MEDIUM | Smith #6 (sole, auth-blocked) |
| Scheduler raw [0,1000] timesteps (no internal /1000) | HIGH | Smith #7 (sole) |
| Scheduler default shift=1.0 → linear sigmas | MEDIUM | Smith #7 (calculated) |
| Training loop sequence (FLUX.1) | HIGH | Smith #9 + #10 |
| Loss formula and target definition | HIGH | Smith #9 + #10 |
| Weighting scheme semantics (loss vs sampling) | HIGH | Smith #10 (sole, detailed) |
| FLUX.1 latent = 4ch (distinct from FLUX.2 32ch) | HIGH | Smith #9 (scope-bound) |
| VAE pixel shuffling NOT in VAE internals | MEDIUM | Smith #5 (sole) — qualified by C3 |

---

*END CHAIN A — 10 Smiths organized. All unique signal preserved. Ready for Opus synthesis.*

---
**Oracle SDK Execution Metrics**
- Architecture: 50 Smiths -> 5 Andersons -> Opus (you)
- Total time: 690s
- Total tokens: 358,076 (in: 86,288 | out: 271,788)
- Quota: 0.71% weekly (5.4% session)
- Smiths: 50 (1 errors)
- Andersons: 5 (0 errors)
- Phase timing: scout: 360s | compress: 330s
- Phase costs: decompose: 0.00% | scout: 0.26% | compress: 0.45%

