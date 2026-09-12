# Adversarial Analysis Round 2: Challenging the Proposed Fixes

5 adversarial agents challenged the team's proposed action plan from roadmap v2. Key finding: most of the proposed fixes are wrong or suboptimal. Several cheap experiments have been overlooked.

## Smith 1: The Proposed Eval Fixes Are Mostly Wrong

### char-acc in composite adds no new information
char-acc and DINOv2-cos both use DINOv2 ViT embeddings (same backbone, same feature manifold). Estimated Pearson correlation r~0.7. The effective independent information from char-acc at weight 0.20 is only ~0.10 after accounting for correlation.

Published font generation papers (FontDiffuser, CF-Font, IF-Font, Patch-Font) use genuinely orthogonal metrics with DIFFERENT backbones: LPIPS (VGG), SSIM (pixel-level), FID (InceptionV3), L1 (raw pixels). No paper uses two metrics from the same model in a composite.

**Correct approach:** Report metrics separately. No composite needed.

### SSIM on 106x160 cells is useless
Typical Latin glyph occupies ~25% of cell area. 75% is uniform black background. SSIM windows falling in background return ~1.0 regardless of glyph quality. Expected discriminative range compressed to 0.88-0.96. Published papers using SSIM evaluate 128x128 CJK characters that fill 60%+ of canvas — fundamentally different signal-to-background ratio.

**If SSIM must be used:** Crop to glyph bounding box + padding before computing.

### Font-level bootstrap at n=50 is underpowered
Power analysis: detecting a 0.01 composite difference at 80% power requires ~400 fonts per group. At n=50, power to detect 0.01 difference is ~12-15%.

**Correct approach:** Paired Wilcoxon signed-rank test on per-font means. Well-powered at n=50 for meaningful differences (Cohen's d >= 0.5).

### Non-Google holdout biases in the OTHER direction
Adding SIL/Monaspace holdout fonts where the baseline never trained on that distribution creates a reverse bias. This measures distribution coverage, not quality.

**Correct approach from SOTA:** Train/test split from the SAME distribution. Report OOD generalization separately.

### Removing "garbage" holdout fonts reduces discriminative power
PlaywriteGuides, Bitcount, RubikDistressed ARE the fonts where models differ most. Removing them reduces sensitivity to generalization quality. No published paper removes test fonts for being "weird."

Sources: FontDiffuser (AAAI 2024), CF-Font (CVPR 2023), IF-Font (NeurIPS 2024), Patch-Font (2025), LPIPS (CVPR 2018)

---

## Smith 2: Sub-Grid Splitting Is Worse Than Status Quo

### Style consistency across separate passes is unsolved
FontDiffuser uses a purpose-built Style Contrastive Refinement module. MSD-Font uses a dual-network 3-stage architecture. FontStudio uses Shape-Adaptive Effect Transfer. None of these are applicable to FLUX.2 Klein LoRA.

With sub-grids, uppercase "A" and lowercase "a" are denoised from DIFFERENT random noise in SEPARATE passes. No mechanism guarantees style consistency.

### Current resolution is already comparable to published systems
Current 106x160 cells = ~66 latent tokens per glyph (at 16x VAE downscaling). FontDiffuser operates at 64x64 per character = 64 latent tokens (at 8x downscaling). Comparable information density.

### Training cost triples with no proven benefit
3 layouts to train, potential style divergence across sub-LoRAs, SimpleTuner warns multi-aspect bucketing is "unreliable for FLUX."

### Better path: 2048x2048 single grid
Same 12x8 grid but each cell gets 170x256 pixels. Preserves single denoising trajectory (style consistency), single LoRA, single prompt. Fits on 24GB for inference, training needs latent caching + gradient accumulation.

cache_latents.py already supports `--atlas-resolution 2048`.

---

## Smith 3: "HOadgenos&8" Has a Critical Resolution Problem

### Per-character detail drops 5.5x at fixed 512x512
- Current "Kg" (2 chars): each character ~256px wide, ~512 latent tokens of detail
- Proposed "HOadgenos&8" (11 chars): each character ~46px wide, ~93 latent tokens

To maintain 256px per character with 11 chars requires 2816px reference resolution → 30,976 ref tokens. Beyond FLUX's attention window.

### Typographic research supports FEWER, better-chosen characters
- Famira proofing method: only 4 control characters (n, o, H, O) establish fundamental parameters
- "adhesion" set (8 chars): designed for proofing text legibility, not style identification
- VQ-Font (ICCV 2023): greedy component-coverage strategy — select characters that maximize stroke component coverage

### Better path: 4-character component-coverage set
"Rog8" — vertical+diagonal (R), round (o), descender+loop (g), compound curves (8). Half the token budget of "HOadgenos&8" with ~80% component coverage.

Or: multi-scale "Kg" — render at 3 optical sizes within the same 512x512 reference. Zero retraining required.

Sources: Wikipedia (Hamburgevons), adhesiontext.com, VQ-Font (ICCV 2023), Famira proofing method

---

## Smith 4: Cosine LR Is Actually Correct — Don't Switch

### Best loss at step 3130 is evidence FOR cosine, not against it
The low LR at step 3130 is what ENABLED the best loss. Cosine annealing's purpose is fine-grained convergence in the final phase. Constant LR would cause permanent oscillation because step size is too large for the loss landscape near convergence.

### SimpleTuner's recommendation is domain-mismatched
Constant LR recommendation is for general image LoRAs (portraits, styles), not structured grid generation. Font atlas is a PRECISION task — 95 characters in exact positions.

### V4 data contradicts constant LR theory
V4 at 9.5e-5 (lower constant-equivalent) was a "disaster." If constant LR were correct, lower constant should converge slower but stably. Instead it underfit completely.

### Better path: Extend cosine to 5000 steps
This gives more time at high LR (first 3000 steps remain at higher LR) while preserving the critical refinement tail. At step 3500/5000, LR would be at ~34% of peak instead of ~3%.

Or: Cosine with warm restarts (CosineAnnealingWarmRestarts). PyTorch-native. T_0=1250, 4 equal cycles. Multiple refinement phases + escape from local minima.

### grad_accum=4 dilutes per-font signal
Each training sample is a different font style. Averaging gradients across 4 random fonts dilutes what makes each font unique. Research supports small batch sizes for fine-tuning: "batch size 1 trains stably, is consistently more robust to hyperparameter choices" (arxiv 2507.07101).

Sources: SGDR paper (Loshchilov & Hutter 2016), SimpleTuner discussions, Calvin Herbst 50-run study

---

## Smith 5: Three Cheap Experiments Nobody Has Tried

### 1. Structured positional prompt (zero cost)
Current prompt says "95 printable ASCII characters in a 12x8 grid" but doesn't specify WHERE each character goes. The model must learn layout from training data alone.

Proposed:
```
Row 1: A B C D E F G H I J K L
Row 2: M N O P Q R S T U V W X
...
```

FLUX.2 supports structured compositional prompts with 32K token encoder. This is a zero-cost code change that could improve char-acc by 5-10%.

### 2. Inference step scaling test (1 hour)
Current: 20 steps. fal.ai docs: "50 step generation maximizes detail and typography accuracy." With 95 characters competing for attention budget, each gets less refinement per step.

Test 20/35/50/75 steps on the same checkpoint. If char-acc jumps at 50 steps, the model CAN render correct characters — it just runs out of denoising budget. This is the cheapest possible diagnostic.

### 3. img2img on template atlas (eliminates grid ordering problem)
Create a template atlas in a neutral font (Roboto). Use FLUX.2's img2img at denoise 0.5-0.7 to restyle. Character identity comes from the template (guaranteed correct), style comes from the reference + denoise. Eliminates the 26% OCR failure because the model doesn't need to solve grid ordering.

### Bonus: Reward fine-tuning with OCR loss
After LoRA converges on flow-matching loss (~2500 steps), run a second-stage reward pass using OCR correctness per cell as the reward signal. Papers: Centered Reward Distillation (arxiv 2603.14128) uses OCR as rule-based reward for text rendering in diffusion post-training. Directly applicable.

Sources: fal.ai FLUX.2 docs, ReinFlow (NeurIPS 2025), Centered Reward Distillation, FLUX.2 img2img guide

---

## Revised Priority Order

| # | Action | Cost | Why |
|---|--------|------|-----|
| 1 | Structured positional prompt | 0 (code change) | Might immediately fix char-acc by giving the model grid layout information it currently lacks |
| 2 | Inference step scaling (20/35/50/75) | 1 hour | Cheap diagnostic — reveals whether the model knows the answer but runs out of budget |
| 3 | Extend cosine to 5000 steps | 1 train run | Evidence-based: model was still improving at 3% LR. Give it more time at meaningful rates |
| 4 | 4-character reference "Rog8" or multi-scale "Kg" | 1 train run | Better component coverage than "HOadgenos&8" at manageable reference size |
| 5 | img2img template restyling | 1 day implementation | Architecture-level fix for the grid ordering problem |
| 6 | Fix eval: separate metrics, paired Wilcoxon, crop SSIM to bbox | 2 hours | Better measurement before more experiments |
| 7 | 2048x2048 single grid | 1 train run (longer) | Resolution increase without style consistency risk |
| 8 | Reward RL fine-tuning with OCR loss | 1-2 weeks | Nuclear option for char-acc if nothing else works |

Items 1-2 should be done BEFORE any training run. They cost almost nothing and could reveal that the problem is simpler than we think.
