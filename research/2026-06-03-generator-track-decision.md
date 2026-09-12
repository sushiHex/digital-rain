# Generator track — grounded decision (2026-06-03)

After exhausting the inference-side quality levers (Route B + consensus selector + the negative SDEdit-repair result), the only path to more quality is a better *generator*. This note grounds that pivot against the prior training research.

## What's already settled (don't re-litigate)
- **Failures are DIFFUSE** (`research/2026-04-30-per-cell-analysis.json`): 33 chars = 50% of failures, 61 = 80% of ~95; per-char failure 0.2–0.6 broadly. Not character- or font-concentrated → roadmap-v3's tree says **architectural ceiling**, not data/oversampling.
- **References already oracle** (eval + training render each ref from the font's own TTF) → 0.81 composite IS the oracle-reference ceiling; no free data upgrade there.
- **Caption engineering dead; multi-ref a wash; inference-step scaling dead** (roadmap-v2/v3 probes).
- **rank-16 was a 3090 VRAM ceiling** (rank-32 OOM'd); "more fonts within rank-16 makes things worse" → capacity-bound at 16.
- **V3 (rank-64, reference-conditioned) is the warm-start ecosystem win the roadmap recommended — already adopted.** It beats our rank-16 model but STILL has diffuse systematic failures (confirmed: the SDEdit latent-inpaint repair couldn't fix them — re-running V3 can't render what V3 fails). So rank + warm-start do NOT break the ceiling.

## Conclusion
The cheap generator levers (rank, data, warm-start, references) are effectively **exhausted** — V3 embodies them and still hits the diffuse ceiling. Two real options remain:

1. **NF4/DoRA rank-32 retrain (cheaper, lower-EV).** NF4 (BitsAndBytes) drops ~4GB → finally enables rank-32 on the 3090 (the documented ecosystem win); DoRA is a single-flag quality bump. But failures are *diffuse/architectural*, so capacity alone is predicted to give only modest gains — and the project explicitly warned against more 14–20h runs without isolating variables.
2. **Glyph-latent conditioning (the real lever, bigger build).** Add a conditioning channel that renders the *correct target glyph shapes* (the full neutral charset) as input the model attends to — TextFlux / FLUX-Text / Glyph-ByT5 pattern, reported char-acc <20% → ~90%. Directly attacks the diffuse "model doesn't know the letterform" failure. **LoRA-expressible** (glyph-latent concat as extra conditioning tokens, like the reference tokens but for every char) — feasible within FLUX.2+LoRA, not a from-scratch retrain. This is roadmap-v3's "Phase 3 diffuse → architectural pivot."

## FEASIBILITY BLOCKER (2026-06-03): atlas-res template too slow on the 3090
Built the full pipeline (template render/cache, `train_lora_kg --use-template` at T=20, eval wiring with verified id-match). Wiring + memory are fine (5-step smoke OK, no OOM, 8.5GB). BUT the atlas-resolution template (80×80 = **6400 tokens**) ~doubles the forward sequence (7424→**13824 tokens**); the grad-checkpointed backward recomputes it → **~2.7 min/step** on the 3090 (27 min, 0 steps logged at the 10-step interval; matches the smoke's 2.9 min/step). Projection: **400-step gate ≈ 18h, full 5000-step ≈ 9 days.** Infeasible on this box at atlas resolution.

**Resolution/fidelity/time tradeoff** (attention is O(seq²); baseline 7424 tok ≈ 0.3 min/step):
| template res | latent | tokens | total seq | ~min/step | 5000-step | letterform fidelity |
|---|---|---|---|---|---|---|
| 512 | 32×32 | 1024 | 8448 | ~0.4 | ~33h | coarse (~2.7×4 units/cell — likely too low) |
| 768 | 48×48 | 2304 | 9728 | ~0.5 | ~42h | moderate (~4×6 units/cell) |
| 1280 | 80×80 | 6400 | 13824 | ~2.7 | ~9 days | best (infeasible on 3090) |

Options: (a) feasible-but-risky smaller template on the 3090 (768px ~42h full / ~3.5h gate is the best fidelity/time balance); (b) cloud A100/H100 for the atlas-res version (fast, $); (c) accept the ceiling (inference-side quality already strong). The gate is cheap at smaller res, so one 768px try answers "does the model use the template" before the full run.

## RE-STRATEGY for the 3090: channel-concat (not token-concat)
The token-concat blowup was a *mechanism* error. The grid-aligned template doesn't need its own tokens — **channel-concatenate** it into the atlas input channels (the FLUX control/inpaint-LoRA pattern):
- atlas latent `(6400,128)` ⊕ template `(6400,128)` → `(6400,256)`; ref tokens zero-pad the template channels. **Sequence stays 7424 (unchanged) → training speed ~original.**
- Expand `x_embedder` `Linear(128→inner)` → `Linear(256→inner)`, new channels init 0 (warm-neutral), bf16/trainable, persisted via `LoraConfig(modules_to_save=["x_embedder"])`.
- Eval: expand x_embedder pre-`PeftModel.from_pretrained` (so `modules_to_save` loads) + a forward-pre-hook on x_embedder that channel-concats the template (pipeline feeds 128-ch).
- **Smoke confirmed: channel-concat 5 steps = 6.2 min vs token-concat 14.5 min (~2.3× faster, seq restored); no OOM; x_embedder (4096×256) saved in the adapter.** The already-cached template (6400,128 packed) is reused as-is.

Code: `train_lora_kg.py --use-template` (now channel-concat), `eval_checkpoint.py --use-template` (expand + hook), `cache_template.py`, `render_glyph_template.py`. De-risk gate (400-step template vs no-template control) running.

## DE-RISK GATE RESULT (2026-06-04): channel-concat works, model uses the template
400-step channel-concat gate (7.9h on the 3090, 72s/step, loss 0.07→0.03):
- **x_embedder new template-channels grew from init-0 to norm 0.84** — direct mechanistic proof the model incorporates the glyph conditioning (gradient flows into channels that started at zero).
- **Eval (3 holdout fonts, 400 steps): char-acc 0.489 / DINOv2 0.78 / composite 0.767.** The structured baseline needed **5000** steps to reach char-acc 0.667 — so 0.489 at 400 steps suggests the template *accelerates* char learning (it's handed the letterforms). Channel-concat eval wiring validated (x_embedder expand + pre-hook).
- **Ablation DEFINITIVE: zeroing the template content collapses char-acc 0.489→0.174 (−0.315).** The model reads letterforms from the template — exactly the mechanism to break the diffuse ceiling. (DINOv2 0.78→0.70, composite 0.767→0.447.)

**DE-RISK PASSED (GO).** Three signals: x_embedder channels learned (norm 0.84), char-acc 0.489 at 400 steps (vs baseline 0.667 at 5000), ablation +0.315 from template content. Glyph-latent conditioning works on the 3090 via channel-concat. Next = full 5000-step run (3090 ~4.2 days at rank-16, or 5090/cloud ~1.3-1.5 days at rank-32 + better quality).

Timeline reality: 72s/step on the 3090 → full 5000-step run ≈ 4.2 days (gate was 8h). A 5090 (~2-3×, 32GB → rank-32 + grad-ckpt-off) would cut the full run to ~1.3-1.5 days at higher quality (benchmark-grounded estimate).

## PARTIAL RUN (2000 steps, 2026-06-05): glyph-cond BEATS baseline composite
2000-step channel-concat run (31.6h on 3090, resumed from 400, best loss 0.0277; x_embedder template-channel norm grew 0.84→1.31 = model leans harder on the template with training).
- Eval (5 holdout fonts, 2000 steps): **char-acc 0.596 / DINOv2 0.851 / composite 0.851**.
- vs structured-5000 baseline (no template, 5000 steps, 50 fonts): char-acc 0.667 / composite 0.811.
- **composite 0.851 > 0.811 baseline at 2000 steps** (vs 5000); char-acc climbing 0.489(@400)→0.596(@2000), on track to pass 0.667 before 5000. Caveat: 5 fonts here vs 50 for baseline — needs a 50-font paired-Wilcoxon for an apples-to-apples char-acc claim.

**Verdict: glyph-latent conditioning works and is beating the diffuse ceiling.** Next: (a) 50-font eval of checkpoint-2000 vs structured-5000 (~10h, GPU free, rigorous confirm) then decide on finishing to 5000; (b) continue training 2000→5000 (~3 days) for the converged model; (c) a 5090/cloud for a faster rank-32 converged run.

## 50-FONT CONFIRM (2026-06-06) — corrects the 5-font optimism
Apples-to-apples paired Wilcoxon (n=50), glyph-cond @2000 vs structured-5000 baseline:
- char-acc 0.627 vs 0.667 — **baseline SIG better (p=0.0009, r=0.48 medium)**.
- composite 0.808 vs 0.811 — **no diff** (p=0.47). dinov2 baseline sig-but-small; racc/lpips no diff.
- **The 5-font "composite 0.851>0.811" was a small-sample artifact.** Across 50 fonts glyph-cond@2000 is tied-on-composite / slightly-behind-on-char-acc — NOT a win.

**Honest read:** confounded by steps (glyph-cond 2000 vs baseline 5000). char-acc trajectory still rising (0.489@400→0.627@2000, 50-font) and the ablation proves the model uses the template (+0.315) — so it's *undertrained, not failed*. The decisive fair test is **glyph-cond@5000 vs baseline@5000** (~3 more days on 3090, or faster on 5090/cloud at rank-32). Until that, glyph-latent conditioning is *promising but unproven* — it has not yet beaten the baseline at equal-ish footing.

## 3090 MEMORY VERIFIED (2026-06-06): rank-32 FITS (the "OOM'd" was stale)
Challenged the roadmap's "rank-32 OOM'd on 3090" against the CURRENT config (qint8 base + grad-ckpt):
- rank-16 glyph-cond peaked **15.6 GB / 24** (~8 GB headroom). rank-32 smoke (88M trainable) ran with **no OOM** (~16 GB peak). **rank-32 fits on the 3090 with grad-checkpointing.**
- grad-ckpt-OFF does NOT help: peak 51 GB (spills to system RAM via WDDM) → **494s/step (7× slower)**. The 9B un-checkpointed activations (~50 GB) far exceed 24 GB. grad-checkpointing is mandatory; no free speedup from the headroom. Speed is compute-bound at ~72s/step.
- Cloud cost (for reference): full rank-32 run ~$30–80 / ~1 day on a rented H100 (80 GB fits ckpt-off). **Decision: stay on the 3090** — rank-32 run ~4.2 days, grad-ckpt on.

**DECISION: launch rank-32 glyph-cond run to 5000 steps on the 3090** (`training_glyph_r32_5000`, --use-template, grad-ckpt on) — stacks both ceiling-breakers (glyph letterforms + rank-32 capacity), the strongest local shot at beating (not tying) the baseline. ~4.2 days. It's a multi-step build (glyph-template conditioning + train LoRA+adapter on augmented input + eval), and the project deliberately paused training here — so the scope decision is the user's.

## DIVERSITY / HOMOGENIZATION — EARLY READ (2026-06-07, glyph-cond @2000 rank-16)
The user's concern ("will the Arial template make all generated styles cookie-cutter? there is a vast variety of form across fonts"). Built `audit_diversity.py` (CPU contact sheet GT|template|generated for distinctive holdout fonts, + a GPU DINOv2 drift/diversity-ratio mode for the post-run eval). Ran the **CPU visual mode** on the already-generated @2000 atlases (no GPU contention with the rank-32 training run). Probe chars: a g e R Q 4 &.

| font | GT character | result |
|---|---|---|
| PlaywriteMXGuides | thin cursive + guide-lines | **preserved** (cursive forms + guide-lines reproduced) |
| RubikDistressed | cracked/distressed texture | **preserved** (distress texture intact) |
| AveriaSerifLibre | bracketed serifs | **preserved** (serifs intact, not sans) |
| FascinateInline | heavy inline-decorative | style preserved; fine inline stripe softened (fidelity, not homogenization) |
| BitcountGridDoubleInk | discontinuous **dot-grid** | **COLLAPSED → smooth Arial skeleton** (only faint dot-vestiges) |

**Answer: NOT broadly cookie-cutter.** Surface style (weight/serif/cursive/texture/decorative) transfers faithfully because the *reference image* carries it — the template supplies letterform identity, not style. The single realized collapse is the **dot-grid pixel font**, whose discontinuous topology conflicts with the continuous template hint → the model follows the continuous skeleton over the reference's dots. That is the specific failure mode (radically-discontinuous topology: pixel/dot-grid/stencil), not a general flattening. Caveat: this is the *undertrained rank-16 @2000* model and the x_embedder template-channel norm grew 0.84→1.31 (leans harder on the template with training) — so the rank-32 @5000 model could homogenize *more*. Baked into the post-run eval (plan Task 3 Step 2b): re-run the visual audit + the DINOv2 diversity-ratio metric (accept ≥~0.8), re-check Bitcount specifically. **Mitigation if it worsens: randomize the template font during training (or template-dropout)** so the model treats the template as a hint, not the answer.

## FINAL RESULT — rank-32 @5000 (2026-07-17): PARITY + STRUCTURAL EDGE, NOT A DECISIVE WIN
The rank-32 glyph-cond run finished 5000 steps (`training_glyph_r32_5000/checkpoint-5000`, best loss 0.0222; the run was interrupted at step ~4280 and resumed from checkpoint-4000 — see the session notes). Full 50-font in-process eval (`eval_runs/glyph_r32_5000`; **note: the eval MUST use `--in-process` — the default subprocess path shells to `render_checkpoint.py` which has no `--use-template` support and silently crashes on the 256-ch x_embedder checkpoint with stderr=DEVNULL**). Aggregate: char-acc **0.6843** (CI 0.671–0.697), composite **0.8144**, dinov2 0.8738, racc 0.7428.

**Decisive paired Wilcoxon (n=50), glyph-cond r32@5000 vs structured-5000 baseline (0.6677 / 0.8110):**
- char-acc: d_med +0.0106 (mean +0.017), W=408.5, **p=0.0654, r=0.266 → NOT a significant win** (misses the p<0.05 ∧ r≥0.3 bar; directionally ahead, near-miss).
- dinov2: d_med +0.0191, **p<0.0001, r=0.671 → SIG win, LARGE effect** (structural/style fidelity decisively better).
- composite: p=0.91 → **tie**. racc: tie. lpips: marginally worse (p=0.04, r=0.29, small).

**Trajectory paired Wilcoxon (n=50), glyph r16@2000 vs glyph r32@5000:**
- char-acc: d_med +0.0532, **p<0.0001, r=0.692 → SIG, LARGE** — @5000 decisively beats @2000. Confirms @2000 was *undertrained, not failed*: 0.489@400 → 0.627@2000 → 0.684@5000. The approach works and improved substantially.
- dinov2: SIG (r=0.773). composite: tie.

**Per-char (baseline vs glyph): 51/94 chars improved, 33 worsened, net failure-rate 0.332→0.316.** Failures stay DIFFUSE (31 chars=50%). Broad small gains (%, I, o, ), N, z, v, 1, P, c, d) partially offset by sharp regressions — notably `\` 0.22→0.94, `'` +0.26, `O` +0.26. This is why char-acc net-improves but only marginally.

**Diversity audit @5000 (Task 3 Step 2b) — PASS, and the @2000 homogenization worry is DISPROVEN:**
- Inter-font diversity ratio **0.87** (gen 0.236 / GT 0.273; ≥0.8 accept). Every probed font's drift is NEGATIVE (closer to own GT than to template) — no homogenization.
- **BitcountGridDoubleInk PRESERVED** at @5000 (template_sim 0.463 far from Arial, target_sim 0.871 close to GT, drift −0.408; visually confirmed dot-grid, not Arial skeleton). The rank-32@5000 model preserves discontinuous topology *better* than rank-16@2000, which had collapsed it. "More training homogenizes more" is false — the opposite held. Contact sheets in `audit_diversity/`.

**VERDICT (outcome matrix: quality = near-win/parity, diversity = OK, trajectory = rising).** glyph-latent conditioning at rank-32/5000 **erased the @2000 significant deficit and reached char-acc/composite PARITY with the baseline, with a significant DINOv2 structural-fidelity edge and no diversity loss.** It did NOT achieve the decisive char-acc win (p=0.065, just misses). This is a validated, de-risked, diversity-safe generator that ties the baseline on readability and beats it on structure — but does not clearly justify either (a) the productionization complexity (INT4 template-wiring probe, unproven) or (b) an immediate further multi-hour run, since LR is decayed to ~0 at 5000 and naive continuation won't help (would need an LR-reheat + more steps, speculative for clearing p<0.05). **DECISION IS THE USER'S** (per the standing no-multi-day-runs-without-agreement rule). Options: (A) train further with LR-reheat toward a decisive win (~10–20h, speculative); (B) accept parity and productionize for the DINOv2/letterform benefit (Task 7, INT4 probe first); (C) shelve — keep the simpler baseline as production generator, glyph-cond proven-but-not-worth-the-complexity.

## POST-EVAL FORENSICS (2026-07-17): two discoveries that reframe A/B/C
1. **ORACLE HYBRID = 0.7711 char_acc (+0.0868 over best single).** Per-cell complementarity between baseline and glyph@5000: both-ok 2730 / only-baseline 408 / only-glyph 486 / both-fail 1076 (of 4700). A per-cell selector between the two generators has ~5× the headroom the entire 5000-step run bought (+0.017). The Route B consensus selector (`v3_select.consensus_best_of_n`) is the existing machinery to realize it without GT.
2. **TEMPLATE AMBIGUITY causes the sharp regressions.** `\` and `/` render byte-identically in the neutral template (ink=959 px, bbox=(34,32,70,127) — mirror diagonals); `'`/`"` and `O`/`0` near-identical. The @5000 model over-trusts the template on confusable pairs → `\` fail 0.22→0.94, `'` +0.26, `O` +0.26. Targeted fix = disambiguated template glyphs (zero-shot first, retrain only if needed).

**Superseding plan: `docs/superpowers/plans/2026-07-17-hybrid-selection-template-disambig.md`** — cost-ordered kill-gates: free hybrid replay + style audit → <2 GPU-h zero-shot disambig probe → production-pair bridge (sign-off) → isolated two-arm retrain (sign-off, only if zero-shot fails). Metric discipline binding (char_acc=DINOv2-template-match ≠ racc/OCR=TrOCR; never gate across the boundary; production claims need same-fonts paired controls).

## HYBRID + DISAMBIG RESULTS (2026-07-17, plan 2026-07-17 executed via SDD)
- **HD-Task 2 — hybrid via TrOCR: KILLED (verified).** No-GT OCR-swap hybrid char_acc 0.6696 < 0.70 gate and < glyph-alone 0.6843. TrOCR captured only 21/486 (4.3%) of oracle-advantage cells; TrOCR↔DINOv2(char_acc) agreement 63-66%. Oracle headroom (0.7711, +0.087) is REAL but not realizable via TrOCR. Accounting machinery validated (reproduced 2730/408/486/1076 exactly) → standing diagnostic. **NOT dead as an idea** — see Oracle finding below.
- **HD-Task 3 — zero-shot template disambiguation: GATE PASSED (free win).** Root cause reframed: `\`/`/` are distinct mirror glyphs in Arial; ink+bbox tie BY SYMMETRY (weakly-discriminative template cells, not a byte-identical bug). Mild cues (slashed-0, serifed-I, thickness/length asymmetry) cached to `dataset_v2/cache/template_disambig_mild.pt`, applied ZERO-SHOT to checkpoint-5000. 50-font same-font paired result vs original template: **confusable char_acc +0.0288 (Wilcoxon p=0.0025, 22↑/7↓), non-confusable −0.0007 (within tolerance)**; `\` recovered 0.06→0.34 (+0.28). Bonus: disambig-mild vs structured baseline char_acc now **p=0.048** (was 0.065 for plain glyph) — crossed marginal significance; dinov2 SIG r=0.761; lpips now SIG better. Mild > strong (strong overcorrects `\`+0.40 but /flat + collateral −0.10 on 0,{,|). **ADOPT template_disambig_mild.pt for the glyph-cond QUALITY path.**
- **Oracle sweep (`research/2026-07-17-oracle-cutting-edge.md`, 30 Smiths): hybrid is revivable with a better no-GT signal.** TrOCR was the wrong tool. Replacements: PP-OCRv6 (Apache, NO symbol hallucination, +200 punctuation chars), TIQA (no-ref glyph-topology/stroke QA, arXiv 2603.07119), DINOv2+LoRA GoogleFontsBench (99% font-style, open, arXiv 2602.13889). Caveat: VLMs poor at font STYLE (Reading≠Seeing) → use font encoders not VLMs. Sub-minute: Nunchaku FLUX.2 still unmerged (PR #926) → bf16 stays; but FLUX.2-klein-4B (4-step, Apache-2.0!) + pi-Flow FLUX.2 LoRA + fal Turbo-8step now exist.
- **REVISED PLAN DELTA:** HD-Task 5 (retrain) SHRINKS — confusable win obtained free zero-shot. Highest-value next step is a NEW cheap task: hybrid-v2 with PP-OCRv6 swap oracle + TIQA/font-DINOv2 tiebreak, on the disambig-improved glyph candidates, before the sign-off-gated HD-Task 4/5.

## HD-Task 6 — hybrid-v2 (GOT-OCR2 swap): NO-GO. The no-GT selection MECHANISM is the limiter, not the OCR.
De-risk GO: GOT-OCR2 (Apache, transformers) reads symbols +0.222 over TrOCR (0.329→0.551), fixes TrOCR-blind brackets/quotes/O. Built `hybrid_v2_replay.py` (combined OCR: GOT on symbol/confusable cells, TrOCR-stored on letters/digits; guards on 0→O and the OCR-blind thin strokes \\'|l). **Full 50-font result: char_acc 0.6702 — BELOW glyph-alone 0.6843, barely above baseline 0.6677 and the TrOCR-hybrid 0.6696.** Paired vs glyph-alone: char_acc −0.011 (worse, ns), dinov2 SIG worse (r=0.68). **Capture rate 23/486 (4.7%) vs TrOCR 21/486 (4.3%)** — a +0.222 symbol-OCR gain moved capture only +0.4pp.
**ROOT CAUSE (the design panel predicted it): metric boundary.** The +0.087 oracle headroom is in DINOv2-char_acc space; a no-GT OCR swap optimizes OCR-correctness; the two agree only ~63-66%. So better OCR can't realize DINOv2-defined advantage cells. The per-cell no-GT swap MECHANISM is fundamentally limited — TrOCR AND GOT-OCR2 both fail (~4-5% capture). **Hybrid-selection track CLOSED.** The oracle headroom is real but not realizable via no-GT per-cell OCR selection. (TIQA/font-DINOv2 wouldn't fix it — they score quality/style, not char IDENTITY, which is what the swap needs.) Artifacts: hybrid_v2_ocr.py, hybrid_v2_replay.py, eval_runs/hybrid_v2/.

## NET SESSION STANDING (2026-07-17)
Best generator = **glyph-cond checkpoint-5000 + template_disambig_mild.pt** (char_acc 0.6883, vs baseline p=0.048; dinov2 SIG r=0.76; lpips SIG better; diversity-safe). That zero-shot disambig win is the banked, free improvement. Both hybrid attempts (TrOCR, GOT-OCR2) failed — no-GT per-cell selection can't beat the single best model. Remaining levers all sign-off-gated: HD-Task 4 (productionize glyph+disambig as QUALITY vs V3), HD-Task 5 (isolated retrain, now low-EV since disambig already fixed confusables free). Faster-base option surfaced by Oracle: FLUX.2-klein-4B (4-step, Apache-2.0).

## GT-GUIDED CROSS-MODEL PREFERENCE OPTIMIZATION (DPO) TRACK — CLOSED (2026-07-21)

Full plan: `docs/superpowers/plans/2026-07-19-fidelity-push-gt-guided-preference.md`, spec: `docs/superpowers/specs/2026-07-19-fidelity-push-gt-guided-preference-design.md`. Motivated by the +0.087 cross-model oracle headroom above (glyph@5000, pre-disambig) — the idea: distill the cross-model advantage into weights via GT-guided preference at *training* time (GT exists on training fonts, sidestepping the no-GT wall that closed the OCR hybrid track).

**Built and reviewed:** 8-task pipeline (cross-model candidate-gen, texture-aware scoring, winner/loser selection with a correctness filter, Stage A SFT distillation, Stage B diffusion-DPO with a frozen PEFT reference adapter, an independent-space diversity guard) via subagent-driven-development — every task spec+quality reviewed, one Critical integration bug (`scores.json` schema mismatch) caught by the whole-branch review and fixed with a regression test. End-to-end GPU-smoked clean.

**Gate −1 (free, holdout, pre-disambig-consistent): GO.** Realizable cross-model ceiling 0.7719 vs glyph-alone 0.6883 (+0.0836 headroom) — confirmed the adversarial-review correction that the headroom is genuinely cross-model, not accessible via single-model self-distillation.

**Stage A (SFT self-distillation) — negative on the 80-font pilot, three times, with diminishing returns:**
| variant | char_acc Δ vs baseline | fonts worse (of 50) |
|---|---|---|
| 400 steps, lr 5e-5, 3-seed pool | −0.0443 | 31 |
| 150 steps, lr 2e-5, 3-seed pool ("lite") | −0.0287 | 31 |
| 150 steps, lr 2e-5, 5-seed pool ("v2", widened) | −0.0215 | 30 |

Magnitude shrank with both gentler training and a wider candidate pool, but **breadth stayed essentially flat (~30/50 fonts)** — regardless of intensity or pool size — and worst-hit fonts were consistently the pilot's own over-sampled families (Playwrite variants), pointing at training-set composition bias, not a training-hyperparameter or pool-size problem per se.

**The decisive discovery came from stepping back, not from tuning Stage A further.** Every char_acc number in this entire investigation — 0.688, the +0.087/+0.084 oracle headroom, all three Stage A results — was a **single-fixed-seed measurement** (`--seed 42`). Re-measuring on the actual 50-font holdout:
- **Same-model best-of-4 (glyph-cond alone, 4 independent seeds) reaches char_acc 0.8366** — +0.1483 over the single-seed 0.6883, *exceeding* the cross-model oracle ceiling (0.7719) that motivated the whole track. Most of the "cross-model headroom" turns out to be recoverable from the glyph model's own sampling variance, not a genuine baseline-model advantage (confirmed on the pilot too: widening 2→4 glyph seeds shrank the cross-model gap from 0.0605→0.0240).
- **A cheap no-GT self-consistency selector (DINOv2-medoid across 4 candidates) captured only 14.1%** of that gap — echoing the ~4-5% capture that already killed the cross-model OCR hybrid track (HD-Task 6, above). No-GT selection is hard here at both cross-model and same-model granularity.
- **IDENTITY (glyph classifier) is already near-ceiling: 0.9619 single-seed → 0.9970 best-of-4 (+0.035 only).** Of the 765 cells where char_acc recovered via a different seed, **88.6% were already identity-correct at seed0** — same letter, just not the exact stroke/style nuance this particular font's GT happens to have.

**This reconfirms and deepens `research/2026-07-18-wrong-letters-are-a-metric-artifact.md` at the seed-variance level.** char_acc's "ceiling" is substantially style-lottery (which correct-letter render happens to land closest to a given font's idiosyncratic style), not a genuine identity/correctness gap — and none of the three mechanisms tried (SFT distillation, cross-model no-GT selection, same-model no-GT selection) can close a gap that isn't primarily real in the sense that matters.

**VERDICT: track CLOSED. Do not pursue Stage B (the multi-day diffusion-DPO run) or further Stage A tuning.** IDENTITY is the metric that reflects real generator quality and is already excellent on the production generator (glyph-cond@5000+disambig, unchanged). Report FIDELITY and IDENTITY as the dual scorecard (already established practice); stop treating FIDELITY's residual gap as a target. The built pipeline (candidate-gen, scoring, selection, Stage A/B trainers, diversity guard) remains as validated, reusable infrastructure if a genuinely different research question ever needs GT-guided preference machinery again — but not for closing this gap.

## LICENSING CONSTRAINT ON HD-TASK 4 (2026-07-27)
Before productionizing glyph-cond+disambig, verified the base model's license directly against the HF model cards: **`FLUX.2-klein-base-9B` — the base all 19 of our scripts load — is `flux-non-commercial-license` and prohibits commercial use.** The `klein-4B` line (both `base-4B` for training and distilled `4B` for inference) is **Apache 2.0**.

The 4B port would be a retrain (inner_dim 4096→3072, layers 8+24→5+20) but the expensive artifacts port free — **`in_channels` is 128 on both models**, so the channel-concat mechanism and the cached `template_disambig_mild.pt` (the banked zero-shot win) are reusable as-is, along with the dataset, eval harness, identity classifier, and diversity audit. It is also *faster*: 4 distilled steps vs 20, which attacks the standing sub-minute goal without depending on the unmerged Nunchaku FLUX.2 PR #926.

**So HD-Task 4's target base is now an open question, not a given.** Full analysis: `research/2026-07-27-klein-licensing-and-4b-port.md`. Caveat: a retrain means every quality claim (char_acc 0.688, IDENTITY 0.978, disambig significance, 0.87 diversity) must be re-established on the new base — none of them transfer.
