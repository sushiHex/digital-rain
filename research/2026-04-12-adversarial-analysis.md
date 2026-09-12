# Adversarial Analysis: Font LoRA Training Approach

5 parallel adversarial agents challenged the project's evaluation, capacity assumptions, dataset construction, hyperparameters, and fundamental architecture. Findings synthesized 2026-04-12.

## Smith 1: Eval Methodology Is Flawed

### Finding: Composite formula over-weights LPIPS on binary images
LPIPS uses AlexNet features trained on ImageNet photographs. Font glyphs are binary black-on-white — no texture, no color, ~1 bit per pixel. LPIPS contributes 52.2% of composite and accounts for 76.8% of the V5 regression.

Published font generation papers (FontDiffuser, CF-Font, VQ-Font) report LPIPS as one of 4-5 metrics with NO weighting. No paper uses LPIPS at 50% weight.

For binary line art, SSIM or IoU would be more structurally appropriate.

### Finding: char-acc exclusion is unjustified
char-acc (template matching via DINOv2 embeddings) measures the most user-facing property: does the generated "B" look like a "B"? It's computed from the same embeddings as DINOv2-cos (zero extra inference cost) but excluded from the composite.

Including char-acc at weight 0.20 halves the baseline-V5 gap from 0.0153 to 0.0075.

### Finding: Holdout is biased toward the baseline
50 holdout fonts drawn exclusively from Google Fonts. Baseline trained on Google Fonts. V5 trained on 8 sources. This measures in-distribution performance for baseline vs. out-of-distribution for V5.

### Finding: Bootstrap resamples cells, not fonts
4,700 cells resampled as independent, but 94 cells per font are highly correlated (same generation seed, same LoRA pass). Effective n is ~50, not 4,700. CIs are overconfident.

Published font generation eval set sizes for comparison:
- FontDiffuser (AAAI 2024): 24 unseen fonts
- CF-Font (CVPR 2023): 60 unseen fonts
- VQ-Font (ICCV 2023): 15-20 fonts per category

Sources: FontDiffuser (arxiv 2312.12142), CF-Font (arxiv 2303.14017), LPIPS paper (CVPR 2018)

---

## Smith 2: Capacity Hypothesis Is Wrong

### Finding: LoRA parameters are shared, not per-concept slots
"Understanding LoRA as Knowledge Memory" (March 2025) found capacity scaling is sublinear with rank, with non-monotonic efficiency curves that peak at specific ranks.

"How Much is Too Much?" (Dec 2025): "no single rank that uniformly outperforms others" — rank 8 through 128 performed similarly across recall tasks.

### Finding: 4.4% more data cannot exhaust capacity
If rank-16 were capacity-saturated at 870 fonts, adding 38 more (4.4%) would produce uniform degradation. Instead, V5 improved on unusual fonts and regressed on easy fonts — this is distribution shift, not capacity exhaustion.

### Finding: The regression is optimization dynamics, not capacity
"LoRA Learns Less and Forgets Less" (TMLR 2024): LoRA acts as a regularizer constraining the model to stay close to the pretrained distribution. The V5 regression pattern (worse on easy, better on unusual) maps to LoRA's documented behavior — the regularization constrains the model to a subspace that trades easy-font fidelity for unusual-font coverage.

### Finding: Same final loss (0.0326) proves capacity is not the bottleneck
Both baseline and V5 reach the same loss floor. V5's higher best loss (0.0250 vs 0.0219) is an optimization trajectory issue, not a hard capacity limit.

### Recommended experiments:
1. Train V5 for 5000-7000 steps to test optimization hypothesis
2. Verify holdout composition against the 123 dropped fonts
3. Run 2-3 seeds to measure stochastic variance

Sources: "LoRA Learns Less and Forgets Less" (TMLR 2024, arxiv 2405.09673), "Understanding LoRA as Knowledge Memory" (arxiv 2603.01097), "How Much is Too Much?" (arxiv 2512.15634), "Scaling Law for LoRA" (arxiv 2501.03152)

---

## Smith 3: Perceptual Dedup Is Actively Harmful

### Finding: 64x64 resolution destroys typographic identity
At 64x64, each grid cell is ~5.3x8 pixels. Serifs, inktraps, ball terminals, stroke contrast, x-height ratios are all destroyed. Two visually distinct fonts can share >0.995 cosine similarity because they have similar overall stroke weight distribution.

### Finding: 0.995 dedup removed 123 baseline fonts
These were distinct families (BreeSerif, Antonio, ArchivoBlack, CascadiaCode) that happened to look similar at thumbnail size to some other font in the pool. The baseline included them and scored 0.8074. V5 excluded them and scored 0.7921.

### Finding: The baseline had NO dedup and scored best
The baseline's approach (one-per-family by string matching, no perceptual comparison) produced the best result. Adding perceptual dedup made things worse, not better.

### Finding: Greedy dedup has alphabetical bias
The first font in a cluster always survives. "AbrilFatface" beats "ZillaSlabHighlight" purely because A < Z. No quality-based or diversity-based selection within clusters.

### Recommended experiment:
Disable dedup entirely for one-per-family sets. One-per-family IS the dedup.

---

## Smith 4: LR Schedule Is Cutting Learning Short

### Finding: Best loss at 90% of training = cosine decays too early
At step 3130/3500, cosine LR is at ~3% of peak. The model was still improving with nearly zero learning rate.

SimpleTuner maintainer recommends "constant with warmup" for FLUX LoRA, explicitly preferring it over cosine.

### Finding: Effective batch 2 is minimum viable, not optimal
With 908 fonts and effective batch 2, each gradient update sees 0.22% of the dataset. "Batch size minimum of 4, ideally 6-8 for stable gradient statistics" — community recommendation for FLUX.

Gradient accumulation 4 (effective batch 4) costs zero extra VRAM.

### Finding: Weight decay 1e-5 is validated
The 50+ Klein training run study found 1e-5 optimal. Higher values (1e-3) produced "oversaturated, cooked" results. Keep as-is.

### Finding: Warmup 100 is slightly low
Standard recommendation: 5-10% of total steps = 175-350 for 3500 steps. Especially important if switching to constant LR.

Sources: SimpleTuner discussions (GitHub bghira/SimpleTuner), 50+ Klein runs study (Calvin Herbst), LoRA weight decay analysis (irhum.github.io)

---

## Smith 5: The Grid Approach May Be the Fundamental Ceiling

### Finding: Every published font generation system generates per-character
- FontDiffuser (AAAI 2024): 96x96 per character
- VecFusion (CVPR 2024): 64x64 per character
- DK-Font (2025): 128x128 per character
- MSD-Font (CVPR 2024): per-character multi-stage

Our 12x8 grid at 1280x1280 gives each cell 106x160 pixels — comparable resolution to per-character systems, but shared across 95 neighbors in a joint latent space. The model must simultaneously learn 95 character shapes, spatial consistency, and style coherence.

### Finding: char-acc of 0.64 = 36% of characters are visually wrong
This is the binding constraint. No vectorization improvement can fix a "B" that looks like a "D".

### Finding: R-ACC failure likely concentrates in characters distant from reference
"K" and "g" provide information about angular uppercase strokes and lowercase descenders. Round forms (O, C, e, o), numerals (3, 5, 8), and punctuation have no reference at all.

### Recommended experiments:
1. Split into sub-grids (uppercase/lowercase/digits+symbols) at same canvas size → 2-4x resolution per glyph
2. Run the 11-character reference immediately ("HOadgenos&8") — already designed, never tested
3. Consider per-character generation with shared style encoder as medium-term pivot

Sources: FontDiffuser (arxiv 2312.12142), VecFusion (arxiv 2312.10540), DK-Font (arxiv 2504.21325), MSD-Font (CVPR 2024), FLUX-Font (Springer 2025), Font Style Interpolation (ICDAR 2024, arxiv 2402.14311)
