# Adversarial Analysis Round 3: Strengthening Next Steps

10 adversarial agents challenged the proposed next steps after the structured-prompt run achieved composite 0.8110 (best so far). Synthesized 2026-04-30.

## Convergent Finding Across All 10 Agents

**Stop running 14-20h training experiments.** The data already collected, plus a few cheap inference-time probes, will tell us more than another retrain. Multiple Smiths (2, 3, 4, 7, 10) independently arrived at this conclusion through different reasoning paths.

## What Each Smith Found

### Smith 1: "Rog8" Reference Choice Has Critical Gaps

The proposed 4-character reference set "Rog8" covers only 9/14 typographic component classes. Specific gaps:
- No lowercase vertical stem (Famira's canonical lowercase rhythm anchor "n" is missing)
- No ascender (g gives descender info but upper x-height-to-ascender region weak)
- "R" is overloaded (cap-height + vertical stem + diagonal + bowl + terminal + leg all in one glyph)
- "8" is one of the LEAST distinctive characters — many fonts use generic numerals copied from Roboto-like base, no terminals to read style from

**Better alternatives, ranked:**
1. **"Hno" (3 chars at 170px each)** — Famira canonical Latin proofing set, 11/14 component coverage, +77% per-character latent tokens vs Rog8
2. **"Hnog" (4 chars at 128px)** — Hno + descender for g-shape signal
3. **"Ho&8"** — if symbol/numeral char-acc is the bottleneck. "&" carries highest per-glyph style information per Hoefler/MyFonts.

VQ-Font (ICCV 2023) found 3 references saturate diffusion-style backbones; going to 8 added <1% improvement.

### Smith 2: img2img Template Restyle Is Fundamentally Broken for Klein

Verified from `pipeline_flux2_klein.py` source: the `image=` parameter on `Flux2KleinPipeline` is NOT an img2img init image. It is a clean reference token for in-context conditioning. There is **no `strength` parameter, no `start_timestep`, no partial denoise mechanism**.

The proposal "denoise the Roboto template at strength 0.5-0.7" cannot be implemented because that API doesn't exist for Klein.

**Three actual implementation paths:**
- **Path A (1 hour, free)**: Pass `image=[ref_kg, roboto_template]` as multi-reference. The pipeline natively accepts lists. Test if FLUX.2 treats template as layout map.
- **Path B (~1 day code)**: Custom latent injection — manually noise the template latent at chosen sigma, slice the schedule, pass `latents=` to pipeline.
- **Path C**: Wait for diffusers `Flux2KleinImg2ImgPipeline` (not yet released, see issue #13005).

### Smith 3: Stop Hyperparameter Iteration, Run Architectural Experiment

After 4 training runs, the marginal gain from hyperparameter tuning is tiny (+0.0036 best). FontDiffuser is NOT a quick rescue — it's a Chinese-character single-glyph generator with no published Latin char-acc numbers.

**Strategic clarity question:** what is this product?
- Style sketch + deterministic downstream renderer → char-acc 0.67 is shippable, ship the downstream pipeline
- End-to-end LoRA generation → ceiling probably below 0.90, need architectural change

**Recommended ship/pivot/abandon gates:**
- Ship gate: char-acc >= 0.85 OR composite >= 0.83 with no category below 0.70
- Pivot gate: if neither template-restyle nor reward-RL closes >50% of gap to 0.85 char-acc within 2 attempts each, the LoRA-on-FLUX.2 ceiling is real
- Sunk cost gate: 4 runs done, 2 more architectural experiments queued, then decision

### Smith 4: The +0.0036 Improvement Is Likely Noise

Quantitative variance estimate from literature (Mosbach BERT variance, EVA LoRA, GLUE benchmarks):
- Plausible per-run composite std: ±0.005 to ±0.015
- The +0.0036 delta sits inside that interval — 0.24σ to 0.72σ effect, statistically indistinguishable from zero

**The +0.028 char-acc delta is more credible:**
- 4.4% relative improvement on a Bernoulli-like metric
- Per-cell binary accuracy averaged over 4,700 trials
- Mechanistic plausibility: structured positional prompt should help character identification

**The DINOv2 regression (-0.0028) is a red flag.** If structured prompt cleanly improved everything, all metrics should move together. Instead, char-acc improved while DINOv2-cos dropped — suggesting a **trade-off, not a pure win**. The model gained character identity at the cost of style fidelity.

### Smith 5: 2025-2026 Literature Has Direct Solutions

**Most actionable: Font-Agent (CVPR 2025) D-DPO** — Dynamic Direct Preference Optimization specifically targeting char-acc in font generation. Uses OCR-as-reward to fine-tune. Directly addresses the team's exact bottleneck.

**Glyph-ByT5 / GlyphControl pattern** — adding a glyph-image as spatial layout prior. Reported char-acc <20% → ~90%.

**Other key findings:**
- Only ONE published FLUX font paper exists (FLUX-Font, Springer 2025) — research-novel territory
- **Qwen-Image 20B** (Apache 2.0, August 2025) explicitly targets text rendering, ranks #1 open-source on AI Arena. Could be a stronger base than FLUX.2 Klein.
- STRICT benchmark (EMNLP 2025) provides standardized text rendering eval (CER/NED/RNFI)
- DA-Font (ACM MM 2025): corner-consistency + elastic-mesh feature loss as drop-in auxiliary losses
- Char-acc IS the most-researched bottleneck in 2025 font generation — known solutions exist

### Smith 6: Multi-Reference Is Technically Supported, Practically Hard

Verified from `pipeline_flux2_klein.py` source: pipeline natively accepts `image: list[PIL.Image]`. Up to 10 supported in code; BFL caps at 4 in their API.

**Token math (within attention window):**
- 1 ref: 7,424 tokens (current, fits in 24GB)
- 3 refs: 9,472 tokens (~24GB borderline)
- 5 refs: 11,520 tokens (likely OOMs)

**Critical caveat:** the LoRA was trained on single-ref with T=10 only. Refs 2+ would use T=20-50, which are out-of-distribution position IDs. RoPE may extrapolate gracefully (it's designed to), but expect refs 2+ to be weakly conditioning at best.

**Real multi-ref training is 2-4 days:** dataset rebuild + cache_latents.py rewrite + train_lora.py rewrite + retrain. BFL caps at 4 (their tested envelope).

### Smith 7: The "T5 Hijacks Style" Warning Was Wrong For Our Stack

Verified: FLUX.2 Klein uses **Qwen3** text encoder, not T5. The original "T5 hijacks style" warning came from FLUX.1-Kontext patterns. **It does not apply to Klein.**

**Free 30-min experiment:** test prompt-conditioning sensitivity on existing checkpoint with proper controls:
- Prompt A: current structured prompt
- Prompt B-match: "A bold serif typeface. {structured prompt}"
- Prompt C-clash: "A thin script. {structured prompt}"
- Prompt D-null: "abc xyz qrs. {structured prompt}" (random non-style words — critical control)

If A vs D produces significantly different output, the model is just sensitive to any token perturbation, not specifically style semantics. Without this control, you fool yourself.

### Smith 8: The +0.0036 Has THREE Confounds, Not Two

**Critical caught bug:** the dataset hash silently changed between baseline (`7bfea4c536c06fcf`) and new run (`fcd50f5621e136f5`) despite both using `dataset_Kg/`. Same directory name, different content. **Third hidden variable.**

Also: the LR schedules are not equivalent. Baseline used chained 18-cycle cosine via `continuous_train.py`. New run is monolithic 5000-step cosine. So the comparison is "monolithic cosine vs chained 18-cycle cosine," not "extended cosine vs cosine."

**Trajectory shows structured prompt was actually LOSING on training loss for steps 1000-3000, only crossing back ahead at step 3500.** The "structured prompt was clearly winning early" framing is wrong.

**Process bug to fix:** dataset hash recorded in manifest.json but never enforced. Either version dataset directories (`dataset_Kg_20260412/`) or have the runner abort on hash change.

**Most actionable finding:** training loss and composite eval are **decoupled**. Whatever moved the eval metric isn't visible in the loss curve. Cannot use loss as a proxy for eval performance going forward.

### Smith 9: Several Free Wins Available in FLUX.2 Ecosystem

**Top wins for RTX 3090:**
1. **Ref2Font V3 exists** (SnJake/Ref2Font on GitHub) — explicitly trained on FLUX.2-klein-9B for 1280x1280 font atlases. Could be used as warm-start checkpoint to compress training.
2. **NF4 quantization** (BitsAndBytes) drops VRAM ~4GB. Could finally enable rank 32.
3. **TaylorSeer cache** (diffusers 0.36+) — claimed 3x inference speedup for free.
4. **DoRA** via `LoraConfig(use_dora=True)` — single-flag flip, quality approaching full fine-tune.
5. **FLUX.2-klein 4-step distilled** — could drop inference from 50 to 4 steps.

**Things ruled out for our hardware:** Flash Attention 3 (Hopper-only), NVFP4 (Blackwell-only), FP8 training (compute 8.9+ required).

### Smith 10: The Highest-Leverage Cheap Experiment

**Per-cell failure heatmap** — 30 minutes manual time, zero GPU. The eval already produces per-cell match data (`eval_checkpoint.py:540-556`) but only stores per-font aggregates in scores.json. We're throwing this data away.

**Existing per-category data (already in scores.json) shows:**
- Brackets: char-acc 0.535 (regressed from baseline — structured prompt made brackets WORSE)
- Digits: R-ACC 0.95 but char-acc only 0.65 — model writes correct digits, but DINOv2 says they don't look like the GT template (probably 0/O/Q template confusion)
- Aggregate +0.0036 hides per-category trade-offs

**Three top cheap experiments:**
1. Per-cell failure heatmap (30 min, 0 GPU): tells us if failures concentrate on chars/fonts/random
2. Multi-seed inference variance (~2 GPU-h): could invalidate +0.0036 win as noise
3. Reference image ablation with oracle ref (~3 GPU-h): tests if model is reference-blind on hard fonts

## Updated Action Plan (Round 3)

### Phase 1: Cheap Diagnostics (Total cost: ~6 GPU-hours + 2 hours code/analysis)

Do ALL of these BEFORE any new training run.

**1a. Per-cell failure heatmap** (30 min, 0 GPU)
- Patch `eval_checkpoint.py` to dump per-cell results to `per_cell.json`
- Re-run scoring on existing 3 generated atlas sets
- Pivot: 95 chars × 50 fonts × 3 runs = 14,250 rows
- Decision tree: char-concentrated → oversample fix; font-concentrated → reference fix; random → architectural ceiling

**1b. Caption A/B with null control** (30 min on existing checkpoint)
- 6 prompts × 3 reference fonts = 18 generations
- Critical: include "abc xyz qrs" null control to distinguish style-attention from token-perturbation sensitivity
- If text encoder responds to style → unlock per-font caption training (Qwen3 != T5, original warning was wrong)

**1c. Multi-seed variance floor** (~2 GPU-hours)
- 5 seeds × 3 worst fonts = 15 atlases on best checkpoint
- If std-dev > 0.005, the +0.0036 win is noise

**1d. Multi-reference test** (1 hour)
- Pass `image=[ref_kg, roboto_template]` to existing pipeline
- Likely returns "refs 2+ ignored" but worth knowing definitively

**1e. Reference image ablation** (~3 GPU-hours)
- 5 worst fonts × 4 reference variants (current Times Kg, oracle Kg in target font, neutral sans Kg, "Hno" 3-char)
- Tests if model is reference-blind or if better references unlock big gains

### Phase 2: Process Fixes (Free)

**2a. Version dataset directories**
- Rename current `dataset_Kg/` to `dataset_Kg_20260406/` (the original baseline content)
- Recreate the current content as `dataset_Kg_20260412/`
- Update experiment_runner.py to abort if dataset hash doesn't match the version-named directory

**2b. Replace cell-bootstrap with paired Wilcoxon signed-rank test**
- Already identified in round 2 but not implemented
- ~30 lines in `eval_checkpoint.py`
- Provides honest CIs at n=50

### Phase 3: One Decisive Training Experiment (Choose ONE based on Phase 1 results)

**If Phase 1 reveals failures concentrated on specific characters:**
- Try Ref2Font V3 as warm-start (Smith 9) — public LoRA exists, may compress training
- Or implement D-DPO with OCR reward (Smith 5) — Font-Agent CVPR 2025 method directly targets char-acc

**If Phase 1 reveals failures concentrated on specific fonts:**
- Run "Hno" (3 chars at 170px) reference A/B — Famira-canonical, +77% per-char latent tokens vs Rog8

**If Phase 1 reveals failures are random/diffuse:**
- The LoRA-on-FLUX.2 ceiling is real for this task
- Pivot to img2img template restyle (Path A: multi-reference TI2I, 1 hour) or Glyph-ByT5 pattern
- Or accept current quality and ship the downstream pipeline (vectorization, TTF generation)

### Phase 4: Strategic Decision Point

After Phase 1 + Phase 2 + ONE Phase 3 experiment, decide:
- **Ship gate met (char-acc >= 0.85)**: Move to downstream pipeline
- **Significant progress (char-acc 0.75-0.85)**: One more training experiment (Phase 3 alternative)
- **No meaningful progress**: Architectural pivot (D-DPO, Glyph-ByT5, or different base model like Qwen-Image 20B)

## Updated "Don't Do" List (Reaffirmed and New)

**Reaffirmed from round 2:**
- Constant LR, grad_accum=4, sub-grid splitting, "HOadgenos&8" reference, char-acc in composite, removing "garbage" holdout fonts, rank 32, more fonts from pool, perceptual dedup, LR 9.5e-5

**New in round 3:**
- "Rog8" reference (R overloaded, 8 generic — use "Hno" instead)
- More inference step scaling (already proved dead)
- Resolution sweeps at inference (LoRA position embeddings break)
- Guidance scale sweeps (Klein is guidance-distilled)
- Naive 5000-step extension stacked on more variables (deepens confound)
- More 14h training runs without isolating variables
- IP-Adapter for FLUX.2 (doesn't exist; native multi-ref is the replacement)

## Process Bug Caught

`dataset_Kg/` content silently changed between baseline (Apr 6) and new run (Apr 12) despite identical directory name. Manifest hash recorded but never enforced. **This is why the +0.0036 cannot be cleanly attributed to any single change.**

Fix: version dataset directories by date or hash. Add hash-validation gate to experiment_runner.py.

## Key Sources

- Font-Agent (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/papers/Lai_Font-Agent_Enhancing_Font_Understanding_with_Large_Language_Models_CVPR_2025_paper.pdf
- DA-Font (ACM MM 2025): https://arxiv.org/html/2509.16632v1
- AGDFont (PRCV 2025): https://github.com/HAIV-Lab/AGDFont
- Qwen-Image 20B: https://github.com/QwenLM/Qwen-Image
- STRICT benchmark (EMNLP 2025): https://arxiv.org/html/2505.18985v1
- Ref2Font V3: https://github.com/SnJake/Ref2Font
- Glyph-ByT5: https://glyph-byt5.github.io/
- LoRA Learns Less (TMLR 2024): https://arxiv.org/abs/2405.09673
- Famira proofing method: https://famira.com/article/letterproef
- VQ-Font (ICCV 2023): https://github.com/awei669/VQ-Font
