# Beat-V3 + Sub-Minute Feasibility Research

Date: 2026-05-31. Six-agent fan-out triggered by the product decision: **beat Ref2Font V3 on quality** AND **hit sub-minute generation** (hard requirement), with **multiple models acceptable** for full 95-char coverage.

## TL;DR

**UPDATE 2026-06-01 — definitive benchmark overturns the sub-minute premise.** A clean fresh-process benchmark (`benchmark_latency.py`, one model per process) shows **sub-minute is NOT achievable on the 3090 with any 9B variant**: per-step floor is ~30s (distilled/kv; base is 57s), so 4 steps = ~119s, 2× over budget. Peak VRAM 18.2 GB (fits — not an offload problem); ~30s/step is the real compute cost of a quantized 9B DiT at 1280² on Ampere. The earlier "8s/step" never reproduced and was an anomaly. **Sub-minute requires 4B (smaller, ungated, needs a new LoRA), FP8-capable hardware, or relaxing the requirement.** See the "DEFINITIVE latency benchmark" section.

Original framing (quality side still holds): decouple quality from the generator — run the generator and recover char-accuracy in a post-process cleanup step. Cleanup CPU core is built; its value with the placeholder repairer is unproven (needs style-preserving repair + the better V3 generator).

## Findings by pillar

### Latency — sub-minute is reachable
| Lever | Latency | LoRA survives? |
|---|---|---|
| Distilled `FLUX.2-klein-9B` (4-step) + NF4 + torch.compile | ~10–25s | loads mechanically; **grid integrity unproven** |
| `FLUX.2-klein-9b-kv` (the owner's "KV model", ~37s) | ~37s | needs ~29GB → **overflows 24GB 3090** |
| NF4 vs FP8 | ~1.3–3.8x/step | yes (orthogonal to LoRA) |
| torch.compile + FP8 | ~2–3.3x | yes |
| Step reduction on base | dead (proven) | n/a |

Most promising: distilled 4-step klein. Biggest risk = "distillation collapse / grid issues" (matches the owner's prior KV-grid memory). ComfyUI #11975 shows base-trained klein LoRAs misbehaving on distilled siblings. **Only resolvable empirically.**

### Caching — dead end for sub-minute
`Flux2TransformerBlock` is **not registered** for FBCache in diffusers v0.38 (that's why `generate_atlas.py`'s `enable_cache` logs a failure). FBCache/TeaCache give ~1.5–2.25x at most (198s→~90–130s, still over 60s), **blur high-frequency detail** (thin strokes/small glyphs — directly threatens char-acc), and **don't compose** with few-step (nothing to skip at 4 steps). Don't bet on it.

### Quality method 1 — DPO with OCR reward
- **Correction:** our roadmap's "D-DPO (Font-Agent CVPR 2025)" attribution is **wrong**. Font-Agent is a font-*understanding* VLM, not a generator; its D-DPO aligns the VLM, not an image model.
- The real method: **Diffusion-DPO** generalizes to flow-matching (Linear-DPO 2026, validated on SD3-Medium). Works as a **LoRA**, ~hundreds–thousands of OCR-ranked self-generated preference pairs, **fits 24GB**, ~1–2 days.
- **Crux:** naive DPO on a few-step distilled model **fails** (reward hacking → "oil-painted" artifacts; Flash-DMD 2026). Must align-then-distill or joint distill+align — not DPO-the-distilled-student.

### Quality method 2 — glyph conditioning (Glyph-ByT5 → FLUX-native)
- Glyph-ByT5's region cross-attention (SDXL) has **not** been ported to FLUX, but FLUX-native equivalents exist that need **no transformer surgery**: they **spatially concatenate a rendered-glyph latent** with the noised latent.
  - **TextFlux** (FLUX.1-Fill): ships **LoRA weights** matching full-finetune, +~11pp.
  - **FLUX-Text** (2505.03329): frozen-VAE glyph/mask concat, no new cross-attn, 16×H20 ~2.5d, 100K samples, 84.2% EN sentence-acc.
  - **FreeText** (2601.00535, training-free, FLUX.1-dev, +15.4% NED) — but assumes 50 steps.
- Expressible as **LoRA-only** (rank-16 compatible). Plausibly lifts 0.67 → 0.80–0.90.
- **Same crux:** glyph guidance lives in high-noise early steps that a 4-step schedule barely samples → likely collapses unless baked in **before/during** distillation.

### Hardware reality
- DPO-LoRA on base 9B: **fits 24GB** (tight).
- True 9B distillation: **cloud-only** (80GB-class; teacher+student+fake-score resident). Re-distill ≈ **$300–1500+**; joint distill+align = multi-thousand, multi-A100.
- **Multi-model charset split: NOT viable** for a single-atlas product. An atlas is one image in one denoising pass; two models = two passes (latency doubles) + seam/style risk. **Extend one model's charset coverage instead.**
- **Shortcut: Z-Image-Turbo** (Alibaba, 6B, Apache-2.0) is **already distilled AND text-aligned** (8 NFE, fits 16GB, sub-second). Fine-tune the **Z-Image base** (turbo is non-finetunable) and inherit its turbo distillation — sidesteps the whole 9B distill problem. Open Q: glyph-grid char-acc after turbo distillation is unbenchmarked.

### Cleanup step — the decoupling lever (mostly already built)
- **Per-cell verification is cheap and exists**: `eval_checkpoint.py` already has TrOCR (`_ocr_decode_cell`) + DINOv2 template matching. Expected char is known (fixed grid) → flag bad cells in ~1–2s/atlas batched.
- **Repair options:**
  | Option | Added latency | Char-acc lift | Retrain? |
  |---|---|---|---|
  | Best-of-N, OCR-scored per-cell (swap `ensemble_best` Laplacian→OCR) | N× pass | moderate, plateaus ~N=4 | no |
  | Cropped-cell inpaint (crop→inpaint small→paste; full-canvas inpaint is NOT cheaper) | seconds for a few cells | high | no |
  | Glyph-restoration model (TIGER/GLYPH-SR) | 0.6s+/cell | high | **yes** (skip v1) |
  | Classical morphology | <1s | low (won't fix S→8) | no |
- **Verdict:** verification + best-of-N + cropped-inpaint can plausibly take char-acc **0.67 → 0.85 with no generator retraining**, sub-minute on a 3090. **Key unknown:** whether per-cell failures are independent across seeds (best-of-N wins) or systematic (need cropped-inpaint + reference hint).

## The two decisive spikes (cheap, no training, existing tooling)

1. **Distilled grid-integrity spike** — load Ref2Font V3 (and our structured-5000 LoRA) onto distilled `FLUX.2-klein-9B` at 4 steps; render the 5 hard fonts; check grid integrity, char-acc, latency. *Gates whether sub-minute generation is viable at all with our existing LoRAs.*
2. **Cross-seed failure-correlation spike** — ensemble N=4, per-cell OCR flags, measure independence. *Gates whether best-of-N cleanup recovers char-acc.*

Together they decide whether the cheap route is viable before any cloud/training spend.

## Routes (selected after spikes)

- **Route A (recommended, cheapest, consumer-HW):** fast generator (distilled klein, or Z-Image base+turbo) + cleanup pipeline (verify → best-of-N → cropped-inpaint). **Pipeline-level** beats V3. No cloud, minimal training.
- **Route B (if model-level beat-V3 is required):** fine-tune Z-Image base for glyph atlas, inherit turbo distillation (sub-second, consumer-HW). Open Q: glyph-acc after turbo distill.
- **Route C (last resort):** glyph-latent-concat + DPO-OCR LoRA on klein base, then **cloud** re-distill ($300–1500+). Only if A and B fail.

## Roadmap v3 corrections
- Drop "D-DPO (Font-Agent CVPR 2025)" as a generation method — Font-Agent is a VLM. Real method = Diffusion-DPO/Linear-DPO + OCR reward.
- "Glyph-ByT5 pattern" → FLUX-native = glyph-latent concatenation (TextFlux/FLUX-Text), LoRA-expressible, no surgery.
- Multi-model charset split = not viable for single-atlas; extend one model's coverage.
- Caching (FirstBlockCache/TaylorSeer) = dead for sub-minute on Flux2.
- New principle: you cannot bolt quality onto an already-distilled model — align/condition before/during distillation, or inherit a pre-distilled-aligned base (Z-Image).

## Spike Results (2026-05-31)

### Spike 1 — distilled grid integrity (KV variant tested first; already cached)
Ran Ref2Font V3 on the cached `FLUX.2-klein-9b-kv` (step-wise distilled — pipeline confirms "guidance ignored for step-wise distilled models") at 4 and 8 steps, on RubikDistressed + BitcountGridDoubleInk.

- **Grid integrity: PRESERVED.** All cells present, all glyphs legible at 4 steps. **The "KV grid issues" memory is outdated/wrong** — V3 survives 4-step distillation structurally.
- **High-frequency texture degrades at 4 steps, recovers by ~8.** BitcountGrid's double-ink dot texture goes blobby at 4 steps, returns at 8. RubikDistressed's rough texture is clean at 4. The cleanup step fixes char-acc, NOT style texture — so very-low-step texture loss on high-freq fonts is unrecovered. Implication: use ~6 steps, or accept texture loss on the minority of dot-matrix/novelty fonts.
- **Latency on KV: DISQUALIFYING on a 24GB 3090.** 124–234s (4–8 steps), ~24s/step vs base's ~8s/step, because the KV variant is ~29GB and offload-bound. This is a *KV-variant* problem (its KV-cache bloats residency), not a distillation problem. The KV model is the wrong sub-minute vehicle for this GPU.
- **Real sub-minute candidate: distilled `FLUX.2-klein-9B`** (same footprint as base → ~8s/step → 4 steps ≈ 32s, 6 steps ≈ 48s). Latency confirmation on the actual distilled model in progress (separate ~34GB download).

Files: `spike1_distilled.py`, `experiments/spike1_distilled/`, `experiments/spike1_log.txt`.
**Distilled `FLUX.2-klein-9B` is GATED** — account not yet authorized (403). Latency confirm on the real distilled model is pending an HF access request.

### Spike 2 — cross-seed failure independence (cleanup viability)
Rendered 3 hardest holdout fonts (RubikDistressed, BitcountGridDoubleInk, PlaywriteMXGuides) x 4 seeds with our structured-5000 LoRA on base-9B; scored per-cell two ways.

| Metric | mean single-seed | best-of-4 | lift | systematic-fail % |
|---|---|---|---|---|
| TrOCR (R-ACC) | 0.42 | 0.55 | +0.13 | 60.3% |
| DINOv2 template | 0.30 | 0.45 | +0.15 | 61.6% |

Both metrics agree (the TrOCR-overstates-systematic worry didn't materialize):
- **Best-of-N is a real lever: +0.13–0.15 char-acc** even on the hardest fonts.
- **But ~60% of failures are systematic** (fail in all 4 seeds) — the model genuinely can't draw that glyph in that style in any seed. Best-of-N alone stalls there.
- Measured on the WORST 3 fonts, so 60% is a **worst-case upper bound**; typical fonts are far more best-of-N-recoverable. The cleanup burden is concentrated on the hard tail.
- **Conclusion: cleanup is viable but is a two-part effort** — best-of-N (cheap, fixes the seed-independent ~40%) + reference-guided cropped-inpaint (fixes the systematic ~60%). Best-of-N alone is insufficient on hard fonts.

Files: `spike2_seeds.py`, `spike2_analyze.py`, `spike2_analyze_template.py`, `experiments/spike2_seeds/`, `research/2026-05-31-crossseed_correlation*.json`.

### FLUX.2 lineup survey (2026-05-31)
Full BFL FLUX.2 line (via HfApi). 9B variants take our existing 9B LoRAs; 4B variants would need a new LoRA.

| Variant | Size | Access | Fits 24GB? | Notes |
|---|---|---|---|---|
| klein-base-9B | 52.9GB bf16 | cached | offload | our train/eval model, 50-step |
| klein-9B (distilled) | 52.9GB bf16 | GATED (403) | offload | 4-step |
| klein-9b-fp8 (distilled) | 9.4GB | gated | likely fits | 4-step + fp8 = ideal sub-minute |
| klein-9b-kv | 52.9GB bf16 | cached | offload | KV; tested 24s/step |
| klein-9b-kv-fp8 | 9.8GB | UNGATED | likely fits | KV + fp8 |
| klein-9b-nvfp4 | 5.8GB | gated | fits | NVFP4 not usable on Ampere |
| klein-4B (distilled) | 23.7GB | UNGATED, cached | fits | needs NEW 4B LoRA |
| klein-4b-fp8 / -nvfp4 | 4.1 / 2.5GB | UNGATED | fits easily | needs NEW 4B LoRA |
| FLUX.2-small-decoder | 0.6GB | UNGATED | - | faster VAE decode lever |

Key facts:
- fp8 repos are a **single transformer .safetensors** (not a full pipeline) → load via `Flux2Transformer2DModel.from_single_file` + scaffold the rest from a cached repo.
- torchao 0.17.0 + quanto 0.2.7 both available (the "Unable to import torchao" line is a harmless diffusers-version notice).
- The 3090 (Ampere) has **no native FP8/FP4 tensor cores** → fp8/nvfp4 help by *fitting in VRAM* (avoiding offload), not by faster matmul. FP8 is the right target; NVFP4 is Blackwell-only.
- The **distilled klein-9B is gated** for this account (403); its fp8 sibling is also gated. The **KV-fp8 is ungated**. Whether KV is viable hinges on Spike 3 (offload vs intrinsic per-step).

### Spike 3 — KV offload-vs-intrinsic (2026-05-31)
Ran cached klein-9b-kv, quanto-fp8, with `pipe.to("cuda")` and **no offload** (fit in 24GB without OOM).
- Result: **~360s/step** — ~15× SLOWER than the offload path's 24s/step.
- The "offload caused the KV slowness" hypothesis is **refuted**. quanto-fp8 weights resident on a 3090 (Ampere, **no native FP8 tensor cores**) hit a slow dequant-per-matmul path; `enable_model_cpu_offload` was actually the *faster* route. **Rule: on this GPU, don't run quanto-fp8 via `.to("cuda")`; use offload.**
- Combined with KV being ~3× slower per step than base on the offload path (24s vs 8s), the **KV variants — including the ungated `klein-9b-kv-fp8` — are not the sub-minute answer.** Don't download it.

### Revised sub-minute conclusion
- **No ungated 9B sub-minute path exists.** base-9B (ungated, cached) is 8s/step but undistilled (needs ~28+ steps → ~224s). KV is 3× slow. The distilled klein-9B is gated.
- **Prime path: plain distilled `klein-9B` (gated)** — same architecture as base → expected ~8s/step on the proven quanto+offload path → **4 steps ≈ 32s, sub-minute.** Only the HF access gate blocks confirming it. The `klein-9b-fp8` single-file (also gated) is an alternative once access lands, but on a 3090 the bf16+quanto+offload path is the safe one (fp8-resident is slow here).
- **Ungated fallback: the 4B line** (`klein-base-4B` to train, `klein-4B` distilled to infer) — needs a NEW 4B LoRA (~10–15h) and has lower base quality (offset by cleanup), but is comfortably sub-minute and needs no gate.
- **So the HF access request for distilled `klein-9B` is the critical path for the 9B sub-minute route.** The cleanup-pipeline sub-project is generator-agnostic and proceeds regardless.

### Distilled-9B confirm (access granted, 2026-05-31) — SUB-MINUTE NOT ACHIEVED
Ran V3 on the real distilled `klein-9B` (quanto+offload, same loader as the 8s/step base benchmark):
- 4 steps = **152s**, 6 steps = **173s** — all OVER 60s. Quality is good (clean grid, distressed texture intact at 4 steps).
- Denoise loop runs at **~27s/step** — same as KV, **3.4× the base-9B 8s/step** under the *identical* loader (verified base = 7.99–8.10s/it across 43 measurements in `experiments/ref2font_v3_log.txt`).
- **The extrapolation "distilled = base = 8s/step → 32s" was WRONG.** Distillation reduces step *count* but per-step cost on distilled/KV is 3.4× base here.
- **Leading hypothesis (unconfirmed): quanto quantization isn't taking effect on the distilled/KV checkpoints** (different weight format) → transformer stays bf16 → memory pressure → `enable_model_cpu_offload` thrashes the transformer per step (~27s) instead of keeping it resident (~8s). Base quantizes cleanly → fits → resident → 8s/step.
- **Candidate fixes (untested):** (1) prompt-embed caching — our prompt is FIXED, so encode once, drop the big text encoder from GPU, freeing memory so the transformer stays resident (could fix both the fixed text-encode overhead AND the per-step thrash); (2) confirm/repair quantization on the distilled checkpoint; (3) the ungated **4B line** (smaller → faster per step), needs a new LoRA.
- **Status: sub-minute on a 24GB 3090 for 9B is unproven and at risk.** It hinges on the 8-vs-27 anomaly being a fixable config issue. The cleanup pipeline (generator-agnostic) is unaffected.

Files: `experiments/spike1_distilled/*flux2klein9b*`, `experiments/spike1c_distilled_log.txt`.

### Spike 5 — quantization is NOT the cause (2026-06-01)
Quantized both base-9B and distilled-9B and counted converted Linear layers:
- **Both: 153/153 Linear → QLinear (WeightQBytesTensor), 100% quantized.** quanto works identically on both. The Spike-4 "quanto no-op / 23.2GB" read was wrong (the footprint metric using `element_size()` is unreliable for quanto tensors — showed 18.2GB unchanged for both, so it measures nothing useful).
- **So the 27s/step (distilled/KV) vs 8s/step (base) gap is NOT quantization.** Same loader, same module structure, same quantization — yet 3.4× per-step difference. Cause is an intrinsic difference in the distilled/KV transformer forward pass, unidentified after spikes 1/3/4/5.
- **Status: sub-minute via 9B is stuck with a murky root cause.** Realistic paths: (a) deep per-step profiling of the distilled forward (uncertain payoff), (b) the ungated 4B line (smaller → likely faster, needs a new LoRA), (c) relax the sub-minute requirement for v1. Decision pending.

Files: `spike5_quantcheck.py`, `experiments/spike5_log.txt`.

Files: `spike3_nooffload.py`, `list_flux2_models.py`, `spike3_inspect.py`.

### Latency/quality tension to resolve in design
Best-of-N needs N sub-minute passes; at distilled 4-step (~32s/pass), N=4 ≈ 128s — over budget. So sub-minute and best-of-N are different *modes*: a FAST single-pass (N=1) mode, vs a QUALITY best-of-N mode. The sub-minute-compatible cleanup lever is **reference-guided cropped-inpaint of flagged cells** (targeted, seconds), which can fix both random and systematic failures; best-of-N is an optional quality-mode booster.

### DEFINITIVE latency benchmark (2026-06-01) — sub-minute ruled out on 9B/3090
`benchmark_latency.py`, each model in its OWN fresh process (clean allocator), V3 LoRA, quanto-fp8 + offload, 4 steps, best of 2 timed runs:

| model | per-step | 4-step total | peak VRAM | verdict |
|---|---|---|---|---|
| FLUX.2-klein-base-9B | 56.9s | 227.8s | 18.2 GB | OVER |
| FLUX.2-klein-9B (distilled) | 29.8s | 119.2s | 18.2 GB | OVER |
| FLUX.2-klein-9b-kv | 29.8s | 119.2s | 18.2 GB | OVER |

- Distilled and KV are identical (~30s/step), ~2× faster per-step than base (57s) — distillation/KV halves per-step but the floor is still ~30s.
- Peak VRAM 18.2/25.8 GB → it FITS; this is NOT offload thrash. ~30s/step is the genuine compute cost of a quantized 9B DiT at 1280² on an Ampere card with no FP8 tensor cores.
- The session's earlier "8s/step" (generate_atlas benchmark) did NOT reproduce in a clean process — treat it as an anomaly.
- **Conclusion: sub-minute is impossible on this 3090 with 9B at usable step counts (4 steps = ~119s; only ≤2 steps fit, too few for quality).** Paths to sub-minute: the ungated **4B line** (≈half the per-step → ~15s/step → 4 steps ≈ 60s borderline; needs a new 4B LoRA), **FP8/FP4-capable hardware** (Ada/Hopper/Blackwell), or **relax the requirement** and ship V3-on-9B (~2 min) + cleanup. File: `experiments/benchmark_latency.txt`.

### Cleanup eval finding (2026-06-01) — value UNPROVEN with placeholder repairer
Built the cleanup pipeline CPU core (branch `feat/cleanup-pipeline`) and ran `eval_cleanup.py` (FAST mode = verify → NeutralPaste repair) on the 3 hardest fonts:

| font | template Δ | OCR Δ | cells repaired |
|---|---|---|---|
| RubikDistressed | −0.011 | +0.000 | 2 |
| BitcountGridDoubleInk | −0.053 | +0.000 | 10 |
| PlaywriteMXGuides | −0.011 | +0.000 | 1 |

- **Template char-acc regresses** (style-loss: a clean Arial glyph mismatches the textured GT embedding — DINOv2 template matching is style-sensitive).
- **OCR char-acc is exactly flat** despite repairs — diagnostic: the flagged cells are predominantly **symbols/punctuation that TrOCR-small misreads even when rendered cleanly** (a clean letter OCRs fine, per Task 8). So the OCR-based verify over-flags symbols AND can't credit their repair. TrOCR is unreliable for ~25% of the charset (symbols/brackets/punct).

**Caveats (this is a worst-case, not a fair test):** only the 3 HARDEST fonts; FAST mode only (the best-of-N QUALITY path — where Spike 2 measured +0.13–0.15 — was NOT exercised here); placeholder NeutralPaste repairer (not the style-preserving diffusion repairer, Task 9, deferred).

**Implication:** the cleanup machinery is built and measuring, but its value is **unproven**. A fair assessment of Route A still needs: (1) **QUALITY-mode eval** (best-of-N) on the 4 seeds/font we already have in `experiments/spike2_seeds/` — the direct test of Spike 2's lift through the pipeline; (2) full 50-font holdout (not just the 3 hardest); (3) the style-preserving diffusion repairer; (4) a per-cell correctness metric that doesn't rely on TrOCR for symbols (e.g., DINOv2 template against a neutral-font template bank, or a glyph classifier).

### Best-of-N QUALITY eval (2026-06-01) — the validated "better results" lever
Ran best-of-N (select-best-cell-per-position by OCR) through the pipeline on N=4 seeds for the 3 hard fonts, dual metric:

| generator | OCR 1seed → best-N | template 1seed → best-N |
|---|---|---|
| structured-5000 (20-step, 95 chars, 106×160 cells) | 0.401 → 0.543 (**+0.142**) | 0.337 → 0.330 |
| Ref2Font V3 (4-step distilled, 71 chars, 142² cells, geometry via `atlas_to_font.compute_grid`) | 0.268 → 0.423 (**+0.155**) | 0.169 → 0.197 |

- **Best-of-N reliably lifts OCR readability +0.14–0.16 across BOTH generators** — the robust, comparable, validated win. (Matches Spike 2's cell-level estimate.)
- **The DINOv2-template metric stays flat** under best-of-N (it's style-dominated; best-of-N optimizes readability, not template-nearness).
- **The absolute V3-vs-ours numbers are NOT comparable** — different charset (71 vs 95, V3 omits the harder brackets/symbols), cell geometry (square 142² vs 106×160), and step count (V3 forced to 4 distilled steps because base-9B is 57s/step; ours at 20). V3's lower absolute is mostly the 4-step distillation penalty + layout differences, not a real deficiency (V3 visually beats our LoRA). A fair generator comparison needs full-step V3, which is infeasible on the 3090 (~27 min/render) — reinforcing the hardware bottleneck.
- **Eval-geometry gotcha (fixed):** V3 atlases use square cells with centering offsets (cols=8, rows=9, cell=142, offset=(72,1)) per the production vectorizer `atlas_to_font.compute_grid`, NOT an even 1280/8×1280/9 grid. The first V3 eval used the wrong geometry and undercounted; corrected here.

**Net for "better results":** best-of-N (+0.14–0.16 OCR) is the demonstrated, generator-agnostic lever. Pushing beyond it needs a full-quality generator (hardware-blocked on the 3090), a style-preserving repairer (hard; Flux2Klein has no img2img), or better hardware. Files: `eval_cleanup_quality.py`, `eval_v3_bestofn.py`, `gen_v3_seeds.py`, `research/2026-06-01-*_eval.json`.

### Nunchaku / SVDQuant (2026-06-01) — REOPENS sub-minute on the 3090
Research into "use the 3090 effectively" found the key lever the quanto-fp8 path missed: the 3090 (Ampere sm_86) has **INT8 AND INT4 tensor cores but no FP8** — so our `qfloat8` had no hardware matmul (dequant to bf16, ~zero compute gain). **Nunchaku (SVDQuant, W4A4/INT4)** uses those INT4 tensor cores.

- **Pre-quantized FLUX.2-klein-9B weights already exist:** `tonera/FLUX.2-klein-9B-Nunchaku` (+ a `-kv` variant), format SVDQuant INT4/FP4 (INT4 on Ampere). Loads via `NunchakuFlux2Transformer2DModel` into `Flux2KleinPipeline`. **LoRA supported** (`transformer.update_lora_params(path)` + `set_lora_strength()`, off-the-shelf LoRAs without requantization) — so V3 should load.
- **Speed (per the model card / hardware class):** 1024² text-to-image **<1–3 s**, image-edit **~2–6 s at 8 steps**, **3–4× over base**. VRAM 14 GB (no offload) / 7.5 GB (offload) at 1024². Community: FLUX.1-dev on a Win11 RTX 3080 went **40s → 11–12s** with Nunchaku.
- **Quality:** near-lossless on the card's metrics (cosine ~1.0; PSNR 17.6/20.6, SSIM 0.74/0.84, LPIPS 0.21/0.30) — moderate PSNR, so **glyph/fine-detail quality must be visually verified** for our use.
- **Implication:** our atlas is 1280² (more tokens than 1024²), but even scaled up this is very likely **well under 60s → sub-minute is achievable on the 3090 after all.** The earlier "~30s/step floor" was a quanto-fp8 artifact, not a hardware ceiling.
- **Bonus:** with generation in seconds, full-quality multi-step generation, best-of-N (N seeds cheap), and a *fair* V3-vs-ours comparison all become affordable on the 3090 — the "better results" levers unblock too.
- **Caveats:** FLUX.2 support in Nunchaku is bleeding-edge (PR #926/#883 under review → manual copy of `transformer_flux2.py` + `torch_transfer_utils.py`); Windows needs a build env (Visual Studio) or a prebuilt/ComfyUI wheel; verify V3 LoRA conversion + glyph quality.

Secondary 3090 levers (smaller, stackable): **torch.compile** ~1.5× with quant (5–300% on Ampere; FLUX.2 on a 3090 ~18.7s with compile+offload per DataCamp), and **optimum-quanto `qint8`** (engages Ampere INT8 tensor cores, unlike `qfloat8`) — both dominated by Nunchaku W4A4.

**Next step: install Nunchaku, load `tonera/FLUX.2-klein-9B-Nunchaku` + V3 LoRA, benchmark per-step at 1280² on the 3090, and visually check glyph quality.** If sub-minute + quality hold, the whole project unblocks on existing hardware.

Sources: [Nunchaku GitHub](https://github.com/nunchaku-ai/nunchaku), [tonera/FLUX.2-klein-9B-Nunchaku](https://huggingface.co/tonera/FLUX.2-klein-9B-Nunchaku), [Nunchaku FLUX.2 issue #883](https://github.com/nunchaku-ai/nunchaku/issues/883), [Nunchaku LoRA docs](https://nunchaku.tech/docs/nunchaku/usage/lora.html), [SVDQuant/Nunchaku v0.1.4](https://digialps.com/nunchaku-v0-1-4-unleashed-svdquant-to-3x-speed-up-12b-flux-on-rtx-4090/), [DataCamp: FLUX.2 on RTX 3090](https://www.datacamp.com/tutorial/how-to-run-flux2-locally), [bestgpusforai: 3090 INT8 no-FP8](https://www.bestgpusforai.com/blog/best-gpus-for-ai).

### Nunchaku trial — actually run on the 3090 (2026-06-02)
Bootstrapped an isolated env (Python 3.14 has no nunchaku wheel; used `uv` to make a **Python 3.13 venv** with torch 2.11/cu128 + the matching `nunchaku 1.2.1 cp313` wheel). FLUX.2 support is unmerged **PR #926** (pure Python, no kernels) → hot-patched `transformer_flux2.py` + `torch_transfer_utils.py` from the `tonera` fork into the venv; the wheel's compiled INT4 kernels cover it. Loaded `tonera/FLUX.2-klein-9B-Nunchaku` (precision auto = **int4** on the 3090) into `Flux2KleinPipeline` and generated at 1280².

Results:
- **Speed: INT4 ~14–16s/step — roughly 2× faster than quanto-fp8's ~30s/step.** Confirms the lever (Ampere INT4 tensor cores vs fp8-dequant). 4 steps = 66s (just over 60s, *with* a VRAM spill); a clean fit should dip under.
- **VRAM:** at 1280² no-offload, peak **26.2 GB > 24 GB** → spilled into Windows shared memory (slow). The INT4 transformer is small (~5GB); the **FLUX.2 text encoder** is what overflows.
- **diffusers `enable_model_cpu_offload` CRASHES the Nunchaku kernels** (CUDA invalid-argument in the W4A4 forward) — must use Nunchaku's native `transformer.set_offload(True)` instead.
- **BLOCKER — V3 LoRA does not load.** `pipe.load_lora_weights` (PEFT) can't inject into `SVDQW4A4Linear`; PR #926 adds **no LoRA support** (its diff is only the base transformer). So Nunchaku currently yields *base* klein-9B, not our V3 atlas generator. **Path to V3-on-Nunchaku = offline: merge V3 into klein-9B (bf16) → SVDQuant-quantize the merged model with nunchaku's deepcompressor tool → load the custom int4 weights.** Involved (calibration), but it's the way to get V3 quality at Nunchaku speed. Or wait for upstream FLUX.2-LoRA support.

**Verdict:** Nunchaku proves the 3090 can run FLUX.2-klein-9B ~2× faster, but it's **not drop-in for V3** today (no LoRA on the quantized model). Files: `.venv-nunchaku/`, `test_nunchaku.py`, `experiments/nunchaku_trial*.log`.

### quanto qint8 — NO speedup (refutes the int8-cores hope, 2026-06-02)
Benchmarked distilled klein-9B + V3 with quanto `qint8` vs `qfloat8`: **29.7s/step vs 29.8s/step — identical.** quanto int8 is **weight-only quantization (storage); the matmul still runs in bf16**, so it never touches the Ampere INT8 tensor cores. The 2× speedup needs a **true low-bit *fused-kernel* engine (Nunchaku W4A4)**, not quanto. So there's no free V3-preserving speedup from switching quanto dtypes. File: `experiments/bench_qint8.log`.

### CONCLUSION — using the 3090 effectively
| Path | per-step (1280²) | keeps V3? | sub-minute @4steps? |
|---|---|---|---|
| quanto fp8 (current) | ~30s | yes | no (~119s) |
| quanto int8 | ~30s (same) | yes | no |
| quanto + torch.compile (untested) | ~est 15–20s | yes | borderline/no (~60–80s) |
| **Nunchaku W4A4 INT4, base** | **~14–16s** | **NO (LoRA unsupported)** | close (~66s spilled; native-offload likely <60s) |
| **Nunchaku W4A4 with V3 merged-then-SVDQuant** | ~14–16s | **yes (baked in)** | **likely YES (<60s)** |

**The only path to sub-minute WITH V3 on the 3090 is offline: merge V3 into klein-9B (bf16, `load_lora_weights`+`fuse_lora`+save) → SVDQuant-quantize the merged model with nunchaku's `deepcompressor` → load the custom INT4 weights via `NunchakuFlux2Transformer2DModel`.** That bakes V3 into the W4A4 weights, sidestepping the unsupported runtime-LoRA path, and inherits Nunchaku's ~2× speed.

### Offline path attempted (2026-06-02) — step 1 DONE, step 2 BLOCKED on tooling
- **Step 1 (merge) DONE:** `merge_v3.py` loaded distilled klein-9B's transformer (bf16, transformer-only to avoid the ~24B text encoder), converted V3 kohya→diffusers (288 keys) via `Flux2KleinPipeline.lora_state_dict` + `load_lora_into_transformer`, `fuse_lora`, and saved the merged bf16 transformer to `experiments/klein9b_v3_merged/transformer/` (~18 GB). This artifact is ready to quantize whenever the tooling exists.
- **Step 2 (SVDQuant) BLOCKED:** upstream `deepcompressor` ships diffusion configs only for **flux.1-dev/schnell, pixart, sana — NO FLUX.2/klein.** tonera (who produced `tonera/FLUX.2-klein-9B-Nunchaku`) has no public deepcompressor fork (only their `nunchaku` PR branch + `fluxsd`). So running SVDQuant on FLUX.2 requires either tonera's unpublished recipe/config or porting FLUX.2 into deepcompressor's diffusion app (significant bleeding-edge dev) — not completable in-session.
- **Route B (runtime LoRA) also dev-gated:** the FLUX.1 nunchaku class has `update_lora_params`/`set_lora_strength` + a `lora/flux/` converter, but it's FLUX.1-architecture-specific; wiring it for FLUX.2 needs a FLUX.2 LoRA converter (why PR #926 skipped it).

### Bottom line for the 3090
- **Today:** ship **V3-on-9B (quanto, ~2 min) + best-of-N + cleanup** — full V3 quality, works now.
- **~2× speedup with V3 is real but tooling-gated** (deepcompressor FLUX.2 config OR nunchaku FLUX.2-LoRA support — both active upstream, likely landing soon). The merged model is staged; when either lands, sub-minute-with-V3 on the 3090 is a short hop.
- **If urgent:** a one-time cloud SVDQuant (after porting FLUX.2 to deepcompressor) → INT4 weights then run on the 3090.
- torch.compile (~1.5×, keeps V3): **BLOCKED on this env** — `torch._inductor.exc.TritonMissing` (no Triton for Windows + Python 3.14; inductor can't generate GPU kernels). Would need Linux or a py3.13+Triton env, and wouldn't reach sub-minute alone anyway.

### EXHAUSTIVE 3090-lever verdict (2026-06-02)
On the current setup (Windows 11, Python 3.14, no Triton, RTX 3090), with V3 LoRA REQUIRED, **every speedup lever is blocked**:
- quanto fp8/int8: ~30s/step, no acceleration (weight-only).
- torch.compile: TritonMissing (no Windows/py3.14 Triton).
- Nunchaku INT4: ~2× proven, but no V3 LoRA on FLUX.2 (upstream-gated) and no public deepcompressor FLUX.2 config to bake V3 in.
So **V3-on-9B stays ~2 min on this box today.** Faster-with-V3 requires: (1) upstream nunchaku FLUX.2-LoRA landing (merged model + tonera INT4 weights staged → ~2×), (2) a one-time cloud SVDQuant of the merged model, or (3) a different env (Linux / py3.13+Triton for torch.compile's ~1.5×, marginal). Ship V3-on-9B + best-of-N + cleanup for v1; treat 2× as a fast-follow when upstream support lands.

## Sources
FLUX.2-klein-9B / -9b-kv / -base-9B (HF, BFL); ComfyUI #11975; HF lora-fast blog; optimum-quanto #277; diffusers hooks/_helpers.py + _common.py (v0.38); TeaCache4FLUX; Diffusion-DPO (2311.12908); Linear-DPO (2605.21123); Flash-DMD (2511.20549); PSO (timestep-distilled tuning); Glyph-ByT5 (2403.09622); FLUX-Text (2505.03329); TextFlux; FreeText (2601.00535); Z-Image-Turbo (Tongyi-MAI); TIGER (2510.21590); GLYPH-SR (2510.26339); inference-time scaling plateaus (2506.12633).
