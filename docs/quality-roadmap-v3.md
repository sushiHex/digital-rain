# Font LoRA Quality Improvement Roadmap v3

Updated 2026-04-30 after 4 training runs and 3 rounds of adversarial analysis (15 unique findings, 9 of which corrected our prior plans).

## Current State

| Run | Composite | char-acc | Best loss | Variables changed from baseline |
|---|---|---|---|---|
| Baseline | 0.8074 | 0.6398 | 0.0219 | (reference) |
| V4 | 0.7728 | 0.6309 | 0.0260 | LR 9.5e-5, 2500 steps, sibling variants |
| V5 | 0.7921 | 0.6609 | 0.0250 | 8-source dataset, one-per-family |
| **Structured Prompt 5000** | **0.8110** | **0.6677** | 0.0238 | Structured prompt + 5000 steps + dataset hash drift |

The "best run" has THREE confounded changes (prompt + step count + silently-mutated dataset). The +0.0036 composite gain may be noise (within ±0.005-0.015 typical training variance).

**UPDATE 2026-05-01 (paired Wilcoxon, n=50 fonts):**
- structured **beats** baseline: composite p=0.027, r=0.313 (medium); char_acc p=0.010, r=0.367 (medium); lpips p=0.0009, r=0.472 (medium-large). The +0.0036 composite is **not bootstrap noise** — paired sign-rank with effective n=50 confirms a real per-font shift.
- baseline **beats** v5: composite p=0.0002, r=0.519 (large). v5 retrain regressed.
- structured **beats** v5: composite p<0.0001, r=0.630 (large).
- Multi-seed variance probe (1c) is still required to rule out *training-process* variance — Wilcoxon only rules out *cell-resampling* variance.

## Critical Finding: Stop Running 14-20h Training Experiments

10 adversarial agents converged on this independently. The data we already have, plus a few cheap inference-time probes, will tell us more than another retrain. Process bugs (silent dataset hash drift) and metric biases (LPIPS dominance, cell-bootstrap overconfidence) mean each new training run produces ambiguous evidence.

## Phase 1: Cheap Diagnostics (~6 GPU-hours + 2 hours code, total)

Do ALL of these BEFORE any new training run.

### 1a. Per-cell failure heatmap (30 min, 0 GPU)

The eval already produces per-cell match data but only stores per-font aggregates. Patch `eval_checkpoint.py` to dump `per_cell.json`. Re-score existing 3 generated atlas sets. Pivot 14,250 rows (95 chars × 50 fonts × 3 runs) to find:

- Concentrated character failures → oversample those characters in next training
- Concentrated font failures → reference image overhaul
- Diffuse failures → architectural ceiling, pivot

### 1b. Caption A/B with null control (30 min on existing checkpoint) — DONE 2026-05-02

Tested 4 prompt variants × 3 reference fonts (Times/Arial/Consolas) on checkpoint-5000:
- A_control (no prefix)  -> baseline
- B_match ("A regular serif typeface.")  -> mean LPIPS Δ = +0.0094 (farther from GT)
- C_clash ("A thin script handwriting font.")  -> mean LPIPS Δ = +0.0066
- D_null ("abc xyz qrs.")  -> mean LPIPS Δ = +0.0024

**Verdict: caption engineering at inference is DEAD.** The matching caption (B) does NOT pull closer to GT than the clashing (C) or null (D) caption — in fact B perturbs *most*. Style-direction signal (C−B) = −0.0028 (wrong sign).

The model is mildly sensitive to ANY token perturbation but learned no caption→style mapping (training captions were structured layout descriptions, not style descriptors). Don't pursue inference-time style captions. Cross-references: `research/2026-05-02-caption_probe_analysis.json`, `analyze_caption_probe.py`.

### 1c. Multi-seed variance floor (~2 GPU-hours)

5 seeds × 3 worst fonts on best checkpoint. If composite std-dev > 0.005, the +0.0036 win is noise. Could invalidate "structured prompt won" before another retrain.

### 1d. Multi-reference inference test (~75 min) — DONE 2026-05-02

5 worst fonts × 3 ref configs (1 ref [Kg], 2 refs [Kg,Mn], 2 refs [Mn,Kg] reversed).

**Result: multi-ref is a wash.** Mean Δ vs single-ref: lpips −0.003 (marginal gain), dino −0.017 (marginal regression). One font (PlaywriteMXGuides) dropped 0.10 on DINO with multi-ref. Order effect tiny (mean |Δ| = 0.004 lpips).

Training was T=10 single-ref, so ref 2+ position IDs are OOD. The model neither uses them productively nor breaks catastrophically — refs 2+ are mild noise. Don't pass multi-ref at inference. To use multi-ref would require training-time changes (T-grid expansion or explicit reference-position embeddings). Cross-references: `research/2026-05-02-multiref_analysis.json`, `analyze_multiref.py`, outputs in `experiments/multiref/`.

### 1e. Reference image ablation (~3 GPU-hours) — DONE 2026-05-02

5 worst fonts × 3 ref variants (skipped Famira "Hno": 3-char would confound position-ID effects since training was 2-char "Kg" only).

**Result: ORACLE DOMINATES (5/5 fonts).** Mean delta vs Times: lpips −0.045, dino +0.123. Two fonts saw dramatic gains: RubikDistressed lpips 0.39→0.20 (halved), BitcountGridDoubleInk dino 0.55→0.88 (+59%). Roboto reference was intermediate.

Implication: model IS reference-attentive. Reference engineering is the lever. Cross-references: `research/2026-05-02-ref_ablation_analysis.json`, `analyze_ref_ablation.py`, outputs in `experiments/ref_ablation/`.

**Critical correction (verified 2026-05-02)**: `eval_checkpoint.py:181` passes the target font's own TTF as `--reference-font`. **Eval has been using oracle refs the whole time.** `build_dataset.py:130-181` similarly renders each training reference using that font's own TTF. So the 0.811 composite IS the oracle-reference ceiling with the current model.

What this actually means:
1. The "use better references" lever is already pulled. There is no free training-data upgrade from re-rendering references.
2. The remaining gap (composite 0.81 → 0.95+) is NOT a reference problem. It's an architectural / training-objective ceiling.
3. **For production**: if users supply non-oracle refs (lower fidelity to target style), quality WILL drop sharply. The product surface needs to encourage high-quality 2-char samples (or render them server-side from a target font the user uploads).
4. **Phase 1d (multi-reference) is now more interesting**: if one oracle ref gives ~0.81 ceiling, would multiple oracle refs (Kg + Mn) push higher? Worth the 1-hour test.
5. **For breaking the ceiling**: the diagnostic chain (per-cell diffuse + caption ignored + reference already oracle) all point to architectural change. Phase 3 should be Glyph-ByT5 / D-DPO / Ref2Font V3 warm-start, not more reference engineering.

## Phase 2: Process Fixes (Free)

### 2a. Version dataset directories — PARTIAL DONE 2026-05-01

- **Hash-validation guard**: `experiment_runner.py` now registers `(dir, hash, exp_name)` in `experiments/_dataset_registry.json` on first use and aborts on hash drift. Backfilled from manifests; the silent `dataset_Kg/` mutation between Apr 6 (`7bfea4c5...`) and Apr 12 (`fcd50f56...`) was caught immediately when running the guard. Registry writes are atomic (tmp + os.replace) so a crash mid-write can't corrupt the file. `backfill_dataset_registry.py` refuses to clobber an existing registry without `--force`.
- **Still pending (user action)**: rename current `dataset_Kg/` to `dataset_Kg_20260412/` and recreate the Apr 6 contents as `dataset_Kg_20260406/`. The guard catches the drift; explicit versioning is the durable fix.

### 2b. Replace cell-bootstrap with paired Wilcoxon — DONE 2026-05-01

Standalone tool `analysis/compare_runs.py` loads two `per_cell.json` files, aggregates per-font means, and runs paired Wilcoxon signed-rank on composite/char_acc/racc/dinov2/lpips — and, since 2026-07-29, IDENTITY when both runs carry it — with the right effective `n` (50 fonts, not 4,700 cells). Results returned as a `WilcoxonResult` dataclass; per-metric verdict prints SIG/no-diff based on `p<0.05 AND r>=0.3`. For `n_nonzero < 20` it switches to scipy's exact method so the test stays valid on small samples; `MIN_NONZERO_PAIRS=10` blocks reports below that.

Confirmed structured-prompt 5000 is a real win over baseline (composite p=0.027, r=0.313 medium), v5 a real regression (composite p=0.0002, r=0.519 large). Cross-references: `compare_runs.py`, `research/2026-05-01-wilcoxon_*.json`.

## Phase 3: ONE Decisive Training Experiment (Choose based on Phase 1 results)

**If failures are character-concentrated:**
- Try Ref2Font V3 (SnJake/Ref2Font on GitHub) as warm-start — public LoRA on FLUX.2-klein-9B, may compress training to a few hundred steps
- Or implement D-DPO with OCR reward (Font-Agent CVPR 2025) — specifically targets char-acc

**If failures are font-concentrated:**
- "Hno" (3 chars at 170px each) reference A/B — Famira-canonical Latin proofing set, 11/14 component coverage, +77% per-char latent tokens vs Rog8

**If failures are diffuse (architectural ceiling):**
- Pivot to Glyph-ByT5 pattern (separate glyph-image conditioning channel) — reported char-acc <20% → ~90%
- Or accept current quality, ship downstream pipeline (vectorization, TTF generation)

## Phase 4: Strategic Decision Point

After Phase 1 + Phase 2 + ONE Phase 3 experiment, decide:
- **Ship gate met (char-acc >= 0.85)**: Move to downstream pipeline
- **Significant progress (char-acc 0.75-0.85)**: One more training experiment
- **No meaningful progress**: Architectural pivot or accept ceiling

## Strategic Question: What Is This Product?

Smith 3 raised this and it deserves an answer:
- **Style sketch + deterministic downstream renderer** → char-acc 0.67 may already be shippable
- **End-to-end LoRA generation** → published-paper landscape suggests ceiling is below 0.90 char-acc; need architectural change

We've been optimizing as if it's the second, but haven't confirmed.

## Ecosystem Wins Available (Smith 9)

Free improvements waiting to be tried:
1. **Ref2Font V3 warm-start** — public LoRA, exact same task as ours
2. **NF4 quantization** (BitsAndBytes) — drops VRAM ~4GB, may finally enable rank 32
3. **TaylorSeer cache** (diffusers 0.36+) — claimed 3x inference speedup
4. **DoRA** (`use_dora=True`) — single-flag flip, quality approaching full fine-tune
5. **FLUX.2-klein 4-step distilled** — could drop inference 50→4 steps

## Updated "Don't Do" List

**Reaffirmed from round 2:**
- Constant LR, grad_accum=4, sub-grid splitting, "HOadgenos&8" reference, char-acc in composite, removing "garbage" holdout fonts, rank 32 (until NF4 enables it), more fonts from pool, perceptual dedup, LR 9.5e-5

**New in round 3:**
- "Rog8" reference (R overloaded, 8 generic — use "Hno" instead)
- More inference step scaling (already proved dead)
- Resolution sweeps at inference (LoRA position embeddings break)
- Guidance scale sweeps (Klein is guidance-distilled)
- Naive 5000-step extension stacked on more variables (deepens confound)
- More 14h training runs without isolating variables
- IP-Adapter for FLUX.2 (doesn't exist; native multi-ref is the replacement)
- img2img with strength parameter (doesn't exist for Klein)

## Phase 3 OUTCOME (2026-07-17): glyph-latent conditioning — PARITY + structural edge, not a decisive win

The diffuse→architectural pivot (glyph-latent conditioning, rank-32/5000) was executed and evaluated. Result: char-acc/composite **parity** with the structured-5000 baseline (char-acc 0.684 vs 0.668, p=0.065 — NOT significant), a **significant DINOv2 structural-fidelity win** (r=0.671), and **no diversity loss** (ratio 0.87; the Bitcount dot-grid collapse feared at @2000 did NOT recur at @5000). The @5000 model significantly beat the @2000 model (char-acc r=0.692), confirming @2000 was undertrained. Bottom line: the architectural lever *works and is diversity-safe* but ties (not beats) the baseline on readability at 5000 steps. Decision (train-further / productionize / shelve) pending user. Full analysis: `research/2026-06-03-generator-track-decision.md` (final section).

## SUPERSEDED (2026-07-29): the "parity" verdict above was a measurement artifact

The Phase 3 outcome section immediately above concluded char-acc **parity**
(p=0.065, not significant). Two later findings overturned it. Both are worth
reading as method lessons, not just results.

**1. The comparison was unfair.** Both models were evaluated with the
*structured* prompt, but the glyph model was trained on a different, shorter
prompt. Fixing that — each model evaluated on the prompt it actually trained
with — moved the glyph model's IDENTITY from 0.9780 to 0.9936 (all 50 fonts
better, r=0.870) and flipped char_acc from failing the gate to passing it.
The mismatch was invisible to char_acc (p=0.948) and only showed up on
IDENTITY. Guard: `conditioning_config.py` + `eval_checkpoint --strict-conditioning`.

**2. char_acc was never measuring what the roadmap assumed.** It is a DINOv2
template match — *style fidelity*, not letter correctness. A font-invariant
glyph classifier (`glyph_classifier.py`, val_acc 0.9385) shows the model
produces the correct letter **99.4%** of the time. The apparent "31% of
characters wrong" was mostly a style lottery: the genuine wrong-letter rate is
~3.2% of cells (~1% excluding dot-grid and heavy-distress fonts), and
same-model best-of-4 recovers +0.148 char_acc by resampling alone, with 88.6%
of recovered cells already identity-correct at seed 0.

### Corrected head-to-head (each model on its own trained prompt, n=50, gate p<0.05 ∧ r≥0.3)

| metric | baseline | glyph | p | r | |
|---|---|---|---|---|---|
| char_acc (style fidelity) | 0.6677 | **0.6917** | 0.0156 | 0.353 | glyph ✅ |
| DINOv2 | 0.8487 | **0.8788** | <1e-5 | 0.768 | glyph ✅ |
| LPIPS | 0.1514 | 0.1457 | 0.372 | 0.126 | ns |
| R-ACC | **0.7411** | 0.7279 | 0.0066 | 0.424 | baseline ✅ |
| IDENTITY | **0.9968** | 0.9936 | 0.0020 | 0.886 | baseline ✅ |

A clean split: glyph conditioning wins both *style* axes, the baseline wins
both *letter-reading* axes. The identity edge is statistically real but
practically negligible (18 cells of 4,400; both above 99.3%).

### Consequences for this roadmap

- **Phase 4's ship gate ("char-acc ≥ 0.85") is not a meaningful target.**
  It gates on style-nuance agreement with one ground-truth rendering, which
  a correct-but-differently-styled glyph fails. Identity is already 0.994.
- **The "Strategic Question" above is answered**: this is the *style sketch +
  deterministic downstream renderer*, not end-to-end letter generation. The
  letters are already right; the remaining gap is style nuance, spacing,
  kerning and hinting — none of which char_acc measures.
- **GT-guided preference optimization (DPO) is CLOSED.** The full 8-task
  pipeline was built, reviewed and GPU-validated; Stage A regressed char_acc
  three times running, and the seed-variance analysis showed the gap it
  targeted was mostly lottery. See `research/2026-06-03-generator-track-decision.md`.
- **Ecosystem wins**, re-checked 2026-07-27: Nunchaku has **no** runtime-LoRA
  API for the FLUX.2-klein transformer (`update_lora_params`/`set_lora_strength`
  are absent; the `load_lora_adapter`/`fuse_lora` methods that appear present
  are inherited from diffusers' `PeftAdapterMixin` and do not work here).
  Sub-minute inference would need an offline merge + SVDQuant. The
  Apache-2.0 **klein-4B** port remains the live lead — it is both the
  licensing fix and the 4-step speed win.

Current state of record: [`../README.md`](../README.md).

---

---

## CORRECTED (2026-08-07): several numbers in this document are superseded

Per the convention, this is appended rather than rewritten -- but do not read
the sections above without it. Four claims here are now known wrong:

1. **"char_acc ... is a DINOv2 template match -- *style fidelity*"** (Phase-3
   outcome, item 2). It is a WITHIN-FONT nearest-neighbour discrimination
   against that font's own GT cells; its docstring says style is dominated by
   glyph identity in that comparison, i.e. style is controlled FOR. It is not
   validated as a style measure.

2. **"the model produces the correct letter 99.4% of the time"** and **"the
   letters are already right"**. 0.9936 is case-folded, equivalence-merged and
   GT-gated. Exact 94-class identity is **0.9355** gated and **0.9243**
   ungated. Reproduce with `analysis/verify_identity_definitions.py`.

3. **"the genuine wrong-letter rate is ~3.2% of cells (~1% excluding
   dot-grid...)"**. The 151 wrong cells are ~6.9% of the cells actually SCORED;
   dividing by all 4,700 counts ~2,500 abstentions as correct. The ~1% figure
   is not reproducible.

4. **"DPO is CLOSED"**. The three negative runs were Stage A **SFT
   self-distillation**. Stage B (diffusion-DPO) was built and never executed --
   this document itself says "do not pursue Stage B". DPO is untested.

Also: the five-lever "one ceiling" table below rests on a redistribution
statistic since shown to be regression to the mean, and every arm is
single-seed at ~1.2 SE. See `research/2026-08-07-headline-claim-sweep.md`.

## CLOSED (2026-08-05): the 4B lever programme is exhausted

The klein-4B port above landed, and five generator-side levers were then tested
against it. **All five hit the same ceiling.** This section closes that track;
it does not supersede the sections above, which remain accurate.

**First, the target was mis-stated.** The 4B trails the 9B by 0.0457 char_acc
in aggregate, and that framing drove most of the work. Split by half, the 9B's
dinov2 advantage on the *easier* 25 holdout fonts is **+0.0007** — the models
are indistinguishable on ordinary typefaces. The real target is **hard-half
+0.0702 char_acc / +0.0599 dinov2**, and four of six metrics show no
significant difference at all.

| lever | hard char_acc | hard dinov2 | easy char_acc | composite | verdict |
|---|---|---|---|---|---|
| **rank 64** | +0.0298 | **+0.0301** | −0.0289 | **+0.0029** | **adopt** |
| distinctiveness oversampling | +0.0221 | +0.0077 | −0.0357 | −0.0027 | no |
| corpus expansion (925→1,113) | +0.0077 | +0.0028 | −0.0834 | −0.0334 | no |
| corpus @ matched per-font budget | — | — | — | — | invalid |
| rank 64 + oversampling | +0.0400 | +0.0004 | −0.1230 | −0.0353 | no |

Every one redistributes (Spearman ρ = −0.40 to −0.85) and none creates.
**Stacking two redistributors compounds their costs, not their benefits.**

Three things worth carrying forward:

1. **Rank 64 should be adopted** — ~30% of the hard-half gap for +1% training
   time, composite slightly up. It was originally rejected on the aggregate
   gate, which was the wrong instrument.
2. **Report the stratified split by default.** `analysis/compare_runs.py` now
   emits it. The aggregate gate mis-scored this project repeatedly.
3. **Check generated ink coverage.** Two runs failed with healthy training loss
   and a passing conditioning guard, detectable only as a global stroke-weight
   shift (−32.5% and +19.7% against GT's 0.0652, re-measured 2026-08-18; this
   line previously read −27% and +15% against 0.0712, which does not reproduce).

Also closed against the 4B: **best-of-N with any no-GT selector** (headroom is
real at +0.1638 but unharvestable; medoid scores −4.9%), and
**reference-anchored selection** (the style lottery is per-cell, not
per-atlas, which rules out every seed-level and atlas-level selector).

Writeups: `research/2026-08-05-stacking-levers-overshoots-rank64-is-the-lever.md`,
`research/2026-08-04-matched-budget-run-and-the-hairline-defect.md`,
`research/2026-08-03-corpus-expansion-v3-result.md`,
`research/2026-08-02-4b-bestofn-headroom-is-real-but-unharvestable.md`,
`research/2026-08-02-reference-anchored-selection-fails.md`.

## Round 3 Source Documents

- `research/2026-04-30-adversarial-analysis-round3.md` — full Smith findings
- `research/2026-04-12-adversarial-analysis-round2.md` — round 2 corrections
- `research/2026-04-12-adversarial-analysis.md` — round 1 findings
- `research/2026-04-12-step-scaling-test.md` — proved step scaling dead
