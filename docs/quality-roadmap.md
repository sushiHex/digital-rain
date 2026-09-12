# Font LoRA Quality Improvement Roadmap

> **Superseded.** This is v1, written before any quantitative eval existed.
> Current: [`quality-roadmap-v3.md`](quality-roadmap-v3.md) (read its
> SUPERSEDED section too) and [`../README.md`](../README.md).
> Kept as the record of what was believed at the time — several of its
> premises, char_acc chief among them, were later shown to be measuring
> something other than what the plan assumed.

Captured 2026-04-07 after synthesis of 10-agent-smith research round + prior 21 oracle rounds.

## Starting state

- Working Kg LoRA on FLUX.2-klein-base-9B produces clean 12×8 atlases
- 925 training fonts, rank 16, LR 1e-4, 3500 steps, best loss 0.0219
- Phase-A fix landed (ref resolution 1280→512 in render_checkpoint.py) — resolved the grid drift root cause
- No quantitative eval — all quality judgments are visual eyeballing

## Research-validated findings

| Finding | Source | Action |
|---|---|---|
| Our setup IS the FLUX.1-Kontext pattern; fixed caption is correct | Smith 8 (Scenario Kontext guide, Pelayo caption rule, Civitai study) | Keep fixed prompt. **Do NOT add per-font style descriptors** — T5 would hijack the style signal from the reference image |
| Klein LR defaults are 5e-5 to 9.5e-5, not 1e-4 | Smith 5 (fal.ai docs, Herbst benchmarks) | Drop LR to 9.5e-5 on next retrain |
| Rank 16 is "safe but conservative" for FLUX.2; rank 32 is community floor | Smith 5 | Bump to rank 32 |
| 925 fonts is too aggressively filtered (VecGlypher keeps 73%, we're at ~37%) | Smith 6 | Switch to perceptual dedup + re-include weight/italic variants → ~1,800-2,200 fonts |
| FLUX best checkpoint typically at steps 800-1200 | Smith 5 | Matches our own observation (converged by step 1500). Cap retrain at 2500 steps |
| Composite eval: LPIPS + R-ACC (OCR) + DINOv2 | Smith 2 | Build eval harness FIRST |
| No public competitor on FLUX.2 reference-to-atlas | Smith 10 | We're in uncharted territory — measurement matters more than copying best practices |
| Horizontal flip breaks b/d p/q 6/9 ; rotation breaks baselines | Smith 9 | Skip all pixel augmentation; do morphological stroke dilate/erode only if needed |
| Reference train/inference resolution mismatch is a known silent killer | Smith 4 (AI Toolkit troubleshooting) | Already fixed in Phase A; guard against future drift |

## Priority-ordered execution plan

### Priority 1 — Eval harness (blocker, ~2h, no GPU)

Without measurement, every experiment is a hunch. Prior research at `research/2026-04-03-atlas-quality-improvements.md:182-200` already sketches this.

**Deliverables**:
- `eval_build_holdout.py` — picks 50 Google Fonts NOT in `dataset_Kg`, deterministic seed, runs them through `build_dataset.find_fonts` quality filter, renders GT atlases + references via existing `render_atlas` / `render_reference`, copies TTF files for later inference
- `eval_checkpoint.py` — loads a LoRA checkpoint ONCE, loops through holdout fonts generating outputs, computes per-font + aggregate scores, writes `scores.json`
- Metrics (ranked by importance for our failure modes):
  1. **R-ACC** (TrOCR round-trip): catches glyph duplicates/drops/swaps that LPIPS misses. Headline metric.
  2. **LPIPS** (AlexNet backbone): perceptual style fidelity, field-standard in font papers
  3. **DINOv2 cosine**: robust to small jitter, complements LPIPS
- Composite: `0.5 * (1 - LPIPS) + 0.35 * R-ACC + 0.15 * DINOv2_cos`

**Validation**: run against existing `experiments/20260406-204250_Kg_300_ab/checkpoints/checkpoint-3500`. This becomes the baseline number every future experiment must beat.

### Priority 2 — Dataset rebuild (~2h code + 30min rebuild, no GPU)

Per Smith 6's published-VecGlypher-pipeline comparison:

**Changes to `build_dataset.py`**:
- Switch from `one_per_family=True` family dedup → **perceptual dedup** (pHash on a 64px pangram render, threshold ~0.95)
- Re-include bold/italic/weight variants — they represent real geometric variation, not duplicates
- Loosen caps-only filter: current "G vs g similarity < 0.9" → **< 0.7** (too many legit display fonts are dropping)
- Add cmap/render sanity wrapper: `try: font.getBestCmap()['A']; ImageFont.truetype(...).getbbox('Ag')` — drops the ~1-3% silently-broken fonts
- Parameterize `REF_CHARS` via CLI arg (currently hardcoded constant)

**Outcome**: `dataset_Kg_v2` with ~1,800-2,200 fonts. Cache latents at 1280/512 (unchanged resolutions).

### Priority 3 — Retrain with fixes (~11h GPU + ~1h orchestrator overhead)

Single decisive retrain incorporating all the above:

| Knob | Current | New | Rationale |
|---|---|---|---|
| Dataset | dataset_Kg (925) | dataset_Kg_v2 (~2000) | Priority 2 |
| LR | 1e-4 | **9.5e-5** | fal.ai Klein default |
| Rank | 16 | **32** | FLUX.2 community floor |
| Steps | 3500 | **2500** | Converged by 1500 anyway |
| Weight decay | 1e-5 | 1e-5 (no change) | Already at Smith 5's winning value |
| Warmup | 100 | 100 (no change) | Fine |
| Reference | "Kg" (Phase-A 512px) | "Kg" (unchanged) | Don't stack reference change here |

Use `experiment_runner.py` + `continuous_train.py` with eval harness running against each checkpoint from the orchestrator. Measure full progression against Priority-1 baseline.

### Priority 4 — A/B richer reference (~14h, CONDITIONAL on Priority 3 results)

Only run if Priority 3 shows good results and time permits. This is the novel-contribution experiment — no published head-to-head exists.

- **Control**: `"Kg"` (current, 2 glyphs) — Ref2Font precedent
- **Treatment**: `"HOadgenos&8"` (11 glyphs) — per Smith 1, maximum style coverage including hardest-to-extrapolate forms (g descender, & complexity, 8 numeral, H/O control characters, full `adhesion` lowercase set)

Same hyperparameters as Priority 3. Measure with eval harness. Decision: whichever has better composite score becomes the production reference.

### Priority 5 — Potrace tuning (~30min, whenever vectorization becomes the bottleneck)

From Smith 7 — current defaults under-perform for type:

```bash
potrace --turdsize 2 --alphamax 0.8 --unit 10 --opttolerance 0.2 ...
```

Optional post-pass: **Bezier Splatting** (arXiv 2503.16424, NeurIPS 2025) — ~100× faster than DiffVG for the same quality improvement. Only worth integrating if vectorization fidelity becomes the quality bottleneck.

## Out of scope / explicitly not doing

- **Per-font style captions** — Smith 8 showed this hijacks the reference image signal via FLUX T5 dominance
- **Horizontal flip / rotation augmentation** — Smith 9 showed these corrupt character identity or baseline alignment
- **LoRA rank >32** — overfitting risk without much larger dataset; diminishing returns per original Hu et al. paper
- **Canvas rebuild to 1152×1152** — Bug #2 (latent alignment) turned out to be a non-issue; Phase A fix was sufficient
- **Per-font evaluation via caption** — not meaningful when captions are fixed
- **ControlNet / IP-Adapter switch** — in-context LoRA already works; switching architectures is high-risk for marginal gain

## Key research references

- `research/2026-04-04-flux2-lora-training-framework.md` — comprehensive prior research on LoRA hyperparameters for FLUX.2
- `research/2026-04-03-atlas-quality-improvements.md:182-200` — prior eval harness sketch (OCR + SSIM composite)
- `research/2026-03-26-oracle-round11-report.md:2780-2845` — VecGlypher Google Fonts filter pipeline
- `research/2026-04-03-cutting-edge-font-tools.md` — FontDiffuser, VecFusion, DeepVecFont details
- FLUX.1-Kontext training guide (Scenario): caption-consistency rationale
- fal.ai FLUX.2 Klein LoRA defaults: `lr=9.5e-5`
- Smith 1 / Leonidas 2001 (adhesion): typographic reference glyph selection
