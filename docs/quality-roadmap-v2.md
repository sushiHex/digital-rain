# Font LoRA Quality Improvement Roadmap v2

> **Superseded on 2026-04-30**, the date of v3's first commit, by
> [`quality-roadmap-v3.md`](quality-roadmap-v3.md) (read its SUPERSEDED section
> too) and [`../README.md`](../README.md). Kept as a dated record of the
> three-run era and the adversarial reviews that ended it.

Updated 2026-04-12 after 3 training runs, 5 adversarial code reviews, and 10 adversarial research analyses (2 rounds).

## What we learned from 3 training runs

### Run results

| Run | Dataset | Fonts | LR | Steps | Rank | Composite | Best Loss |
|-----|---------|-------|----|-------|------|-----------|-----------|
| Baseline | dataset_Kg (Google Fonts, one-per-family) | 870 | 1e-4 | 3500 | 16 | **0.8074** | 0.0219 |
| V4 | dataset_v4 (8 sources, perceptual dedup, sibling variants) | 979 | 9.5e-5 | 2500 | 16 | 0.7728 | 0.0260 |
| V5 | dataset_v5 (8 sources, one-per-family, quality-gated) | 908 | 1e-4 | 3500 | 16 | 0.7921 | 0.0250 |

### Key findings

1. **Lower LR + fewer steps was a disaster (V4).** LR 9.5e-5 at 2500 steps gave only 64% of the per-font learning budget. The fal.ai "Klein default" recommendation was wrong for our use case.

2. **More diverse data didn't help (V5).** 908 fonts from 8 sources scored worse than 870 from Google Fonts alone. V5 improved on unusual fonts (MochiyPopPOne +0.055, RubikDistressed +0.040) but regressed on ALL 12 easiest fonts. The model traded mainstream quality for niche coverage.

3. **Perceptual dedup is actively harmful.** At 64x64 resolution, cosine similarity cannot distinguish serif from sans-serif. The 0.995 threshold removed 123 fonts that were in the successful baseline — distinct designs that happened to share similar overall brightness distributions at thumbnail size.

4. **The cosine LR schedule decays too early.** Best loss at step 3130/3500 means the model was at ~3% of peak LR when it found its optimum. Learning was cut short.

5. **char-acc improved on V5 (+0.021).** The model learned better style-specific glyph identity despite lower composite. This suggests the expanded data DID help with diversity — but the benefit is hidden by the eval's bias toward LPIPS (which accounts for 77% of the composite drop).

## Critical eval methodology problems (found by adversarial review)

### Problem 1: Google-Fonts-only holdout biases toward baseline
The holdout draws exclusively from Google Fonts. The baseline trained on Google Fonts. V5 trained on 8 sources. We're measuring in-distribution performance for the baseline vs. out-of-distribution for V5.

**Round 2 correction:** Adding non-Google holdout fonts biases in the OTHER direction. Correct approach: keep holdout from same distribution as training (standard SOTA protocol). Report OOD generalization separately if needed.

### Problem 2: Cell-level bootstrap overestimates significance
The bootstrap resamples 4,700 individual cells as independent, but 94 cells per font are highly correlated (same generation seed, same LoRA pass). Effective n is ~50, not 4,700. The CIs are overconfident.

**Fix:** Use paired Wilcoxon signed-rank test on per-font means. Well-powered at n=50 for meaningful differences (Cohen's d >= 0.5). Bootstrap at n=50 gives only 78-85% actual CI coverage.

### Problem 3: LPIPS is the wrong dominant metric for binary glyph art
LPIPS uses AlexNet features trained on ImageNet photographs. Font glyphs are binary black-on-white with zero texture or color. LPIPS contributes 52% of the composite and accounts for 77% of the V5 drop.

**Round 2 correction:** Don't add SSIM naively — on 106x160 cells with 75% black background, SSIM has only ~0.08 dynamic range. Must crop to glyph bounding box first. Better: add FID (InceptionV3 backbone, genuinely orthogonal to VGG-based LPIPS and ViT-based DINOv2). SOTA approach: report all metrics separately with no composite.

### Problem 4: char-acc excluded from composite
The most user-relevant metric but it's correlated with DINOv2 (both use same ViT embeddings, estimated r~0.7).

**Round 2 correction:** Adding char-acc to composite doesn't add independent information — it just reweights the DINOv2 axis. No published paper uses two metrics from the same backbone in a composite. Correct approach: report char-acc separately as the primary user-facing quality indicator.

## What we built (infrastructure, ready for use)

- **Quality gate** (`font_quality.py`): 8 checks (4 font-level, 4 atlas-level), quarantine with HTML report
- **Standalone auditor** (`audit_dataset.py`): walk any dataset, score, quarantine rejects
- **Font sourcing pipeline** (`fetch_fonts.py`): 5 adapters (Google Fonts, Font Library, Velvetyne, GitHub, directory), provenance manifest
- **Eval harness** (`eval_checkpoint.py`): LPIPS + R-ACC + DINOv2 + char-acc, bootstrap CIs, per-category breakdown
- **Font pool**: 11,371 fonts from 8 sources, ready for selection
- **3 rounds of code review**: 29 issues found and fixed across all files

## Action plan (revised after adversarial round 2)

See `research/2026-04-12-adversarial-analysis-round2.md` for full reasoning behind each correction.

### Priority 1: Cheap diagnostics FIRST (1 hour, no training)

Two zero/low-cost experiments before any training run:

**1a. Inference step scaling (1 hour, existing checkpoint)**
Test baseline at 20, 35, 50, 75 inference steps. fal.ai: "50 steps maximizes typography accuracy." If char-acc jumps at 50 steps, the model CAN render correct characters — it just needs more denoising budget.

**1b. Structured positional prompt (requires retrain to validate)**
Current prompt doesn't specify WHERE characters go. Add row-by-row layout to both training caption and inference prompt. Zero implementation cost, potentially +5-10% char-acc.

### Priority 2: Extend cosine to 5000 steps (1 train run, ~14h)

Round 2 adversarial analysis proved cosine is CORRECT for precision tasks — don't switch to constant LR. Best loss at step 3130 = evidence FOR late-stage refinement, not against it. Constant LR would cause permanent oscillation.

Fix: extend schedule to 5000 steps. At step 3500/5000, LR at ~34% of peak instead of ~3%.

Alternative: cosine with warm restarts (CosineAnnealingWarmRestarts, T_0=1250, 4 cycles). Multiple refinement phases.

Keep batch_size=1, grad_accum=2 (round 2 showed grad_accum=4 dilutes per-font gradient signal).

### Priority 3: Better reference — "Rog8" or multi-scale "Kg" (1 train run)

Round 2 showed "HOadgenos&8" has critical per-character resolution problem at 512x512 (detail drops 5.5x).

**Option A: "Rog8" (4 chars)** — vertical+diagonal, round, descender+loop, compound curves. ~80% component coverage per VQ-Font's greedy strategy. Each char still gets ~128px at 512x512.

**Option B: Multi-scale "Kg"** — render at 3 sizes in one 512x512 image. Zero retraining needed to test.

### Priority 4: Fix eval methodology (2 hours, no GPU)

- Report metrics separately (no composite — per SOTA convention)
- Use paired Wilcoxon signed-rank test (well-powered at n=50)
- Add FID (InceptionV3, genuinely orthogonal to LPIPS and DINOv2)
- Crop cells to glyph bbox before SSIM
- Keep holdout as-is (don't add non-Google fonts, don't remove "garbage" fonts)

### Priority 5: img2img template restyling (1 day implementation)

Architecture-level fix: restyle a correct-layout template atlas at denoise 0.5-0.7. Character identity from template (guaranteed correct), style from reference. Eliminates the 26% OCR failure entirely.

### Priority 6: 2048x2048 single grid (1 train run, longer)

2.5x more latent tokens per glyph with no style consistency risk. cache_latents.py already supports `--atlas-resolution 2048`. Simpler and safer than sub-grid splitting.

### Priority 7: Reward RL fine-tuning with OCR loss (1-2 weeks)

Second-stage reward pass after LoRA converges. OCR correctness per cell as reward signal. Papers: Centered Reward Distillation (arxiv 2603.14128), ReinFlow (NeurIPS 2025).

## Experiments NOT worth running (updated after round 2)

- **Constant LR**: Cosine is correct for precision tasks. Best loss at low LR = evidence FOR decay.
- **grad_accum=4**: Dilutes per-font gradient signal for style transfer.
- **Sub-grid splitting**: Style consistency across passes unsolved. Training triples. Current latent resolution (~66 tokens/glyph) comparable to FontDiffuser (64 tokens/glyph).
- **"HOadgenos&8" at 512x512**: Per-character detail drops 5.5x. Use 4-char set or multi-scale.
- **char-acc in composite**: Correlated with DINOv2. Report separately.
- **Non-Google holdout fonts mixed in**: Creates reverse bias. Report OOD separately.
- **Removing "garbage" holdout fonts**: They test generalization. Keep them.
- **Rank 32**: OOM'd on 3090. Exhausted cheaper options first.
- **More fonts from pool**: V5 showed more fonts within rank-16 makes things worse.
- **Perceptual dedup**: Removed fonts that helped. Disable for one-per-family.
- **LR 9.5e-5**: Proven to undertrain. Stick with 1e-4.

## Research references

### Round 1 adversarial analysis
- "LoRA Learns Less and Forgets Less" (TMLR 2024) — LoRA as regularizer, not capacity limit
- "Understanding LoRA as Knowledge Memory" (March 2025) — Sublinear capacity scaling with rank
- "How Much is Too Much? LoRA Rank Trade-offs" (Dec 2025) — Rank 8-128 similar on many tasks
- Calvin Herbst 50+ Klein training runs — Weight decay 1e-5 optimal, LR sensitivity
- FontDiffuser (AAAI 2024), VecFusion (CVPR 2024), MSD-Font (CVPR 2024) — Per-character generation

### Round 2 adversarial analysis
- VQ-Font (ICCV 2023) — Greedy component-coverage for reference selection
- Famira proofing method — 4 control characters (n, o, H, O) for style identification
- SGDR (Loshchilov & Hutter 2016) — Cosine with warm restarts
- Centered Reward Distillation (arxiv 2603.14128) — OCR reward for diffusion post-training
- ReinFlow (NeurIPS 2025) — RL fine-tuning of flow-matching models
- Small Batch Size Training (arxiv 2507.07101) — batch_size=1 robust for fine-tuning
- fal.ai FLUX.2 flex docs — 50 steps maximizes typography accuracy
- CF-Font (CVPR 2023), IF-Font (NeurIPS 2024), Patch-Font (2025) — Eval protocol standards
