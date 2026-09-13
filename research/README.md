# research/ — the dated record

The dated notes, written as the work happened. Some are held in the private
archive rather than published: the twenty-one survey rounds from March 2026
(see *Literature scouting*) and fifteen late-August notes that spell out how a
description becomes a font — which reference generators were tried, at what
speed and licence, and how the picker behaves. Twelve of those fifteen had
index rows and are marked **held privately — product recipe** below; the
other three were raw Oracle transcripts that were never indexed. Their
results are in the notes that remain, and in the README. The notes are
**not** rewritten when a later
note contradicts an earlier one; a superseded finding keeps its original text and
gains a marked correction, so the sequence of being wrong stays readable. Several
of the most useful notes here are the ones that retract an earlier one.

**A note title can outlive its finding.** Because notes are never rewritten, a
headline asserting something later disproved stays at the top of the file. Where
that happens the note now opens with a marked correction, and this index flags it
with ⚠. Five such titles are known: the three levers below; the OFL note,
whose title carries the original "51 Microsoft fonts" figure that its own body
corrects; and the first style-adherence write-up, partly retracted after an
adversarial review.

The narrative that ties these together is [`docs/what-happened.md`](../docs/what-happened.md).
The current state of every claim is [`../README.md`](../README.md) and
[`../CLAUDE.md`](../CLAUDE.md).

---

## Start here

Twelve notes carry the project's actual conclusion. Read them in this order.

| note | what it establishes |
|---|---|
| [Training-run variance, measured](2026-08-13-training-run-variance-measured-at-last.md) | Three runs identical but for `--seed` land 0.1157 apart on char_acc. The comparison tool calls two of the three pairs a significant improvement. |
| [A retrieval baseline beats every model](2026-08-13-a-retrieval-baseline-beats-every-model.md) | Handing back the nearest *training* font outscores every checkpoint on both style metrics. The metrics measure font-likeness, not generation. |
| [The claim ledger, corrected](2026-08-13-the-claim-ledger-corrected.md) | Scored on every metric rather than one each, six effects clear 2×SE — and all six are regressions. |
| [Five runs, and the noise floor moved](2026-09-13-five-runs-and-the-noise-floor-moved.md) | Two more identical runs take σ to 4 df and its interval from 12× to under 5× wide. The LPIPS σ more than doubles — seed 46 drew every glyph at three-quarters of the stroke weight, so stroke weight is itself a seed lottery — and **four** effects clear 2×SE, not six, still all regressions; the 4B→9B LPIPS row (−1.9) and the LR fix (−0.9) drop out. The median-composite rule ships seed 45. |
| [Scoring the finished font](2026-08-18-scoring-the-finished-font.md) | The first metric on the artefact a user receives. Found every generated font had 2× word spacing; the model still does not beat retrieval; 74% of the letterfitting error is the pipeline, not the model. |
| [The sidebearing prior that did not pay](2026-08-19-the-sidebearing-prior-that-did-not-pay.md) | A correct per-character letterfitting model, worth −14.6% in isolation and nothing in the pipeline: the constant it replaced was compensating for the tracer's ink bias. Shipped off by default. |
| [The atlas format is the common cause](2026-08-20-the-atlas-format-is-the-common-cause.md) | The three finished-font defects are one: every constant the builder invents is a number the atlas discards. Cap height measured and already correct at 0.7000; the per-font spread is unrecoverable. |
| [Two styles in, two styles out](2026-08-21-two-styles-in-two-styles-out.md) | The product concept removes the ground truth, which is what made retrieval fatal. The generator transfers style faithfully — give it two and it splits the atlas along K-like vs g-like letters. Identity scored that ABOVE the control. |
| [A GT-free coherence measure that works](2026-08-21-a-gt-free-coherence-measure-that-works.md) | The instrument the product needs, validated twice at n=50 (paired p=0.0021, severity rho=+0.407). The fix was removing the per-character effect; the bimodality hypothesis was wrong. |
| [The reference gate](2026-08-21-the-reference-gate.md) | The first piece of product, not measurement: score the two reference glyphs before generating. Separates at r=0.678 and predicts the atlas it would have produced at rho=+0.666. |
| [Single-seed comparisons cannot resolve the gap](2026-08-07-single-seed-comparisons-cannot-resolve-the-4b-9b-gap.md) | Decomposes seed variance into a main effect that does *not* average out. Every single-seed A/B here carries SE ≈ 0.037. |
| [The redistribution signature was regression to the mean](2026-08-07-the-redistribution-signature-was-regression-to-the-mean.md) | `Cov(a, b−a) = Cov(a,b) − Var(a)`. A statistic used across the whole project was biased by construction. |

---

## How the measurements broke

| note | |
|---|---|
| [Wrong letters are a metric artifact](2026-07-18-wrong-letters-are-a-metric-artifact.md) | The genuine wrong-letter rate is ~3.2% of cells, against the ~31% `char_acc` implies. |
| [Adversarial audit of the headline claims](2026-08-07-adversarial-audit-findings.md) | What the claims say versus what their evidence supports. |
| [Headline claim sweep](2026-08-07-headline-claim-sweep.md) | Each flagship result re-derived; what survives and what does not. |
| [The 4B→9B gap is real, and larger](2026-08-08-multiseed-the-4b-9b-gap-is-real-and-bigger.md) | Six inference seeds per checkpoint. The gap is ~60% bigger than the single-seed A/B showed — the old comparison used the 4B's lucky seed. |
| [The oracle gap is small; per-cell medoid is weak](2026-08-12-oracle-gap-is-small-per-cell-medoid-is-weak.md) | The best-of-N reserve is real but resists every selector tried. |
| [Realizable cross-model oracle ceiling](2026-07-19-fidelity-oracle-ceiling-gate.md) | An upper bound on what selection could ever recover. |

## The training loop

| note | |
|---|---|
| [Three confirmed silent defects](2026-08-08-training-loop-audit-three-confirmed-silent-defects.md) | The cosine LR horizon was in the wrong units and never annealed; the SNR weighting is inert; resume is not reproducible. None was visible in the loss curve. |
| [Reference-character mismatch](2026-07-28-reference-char-mismatch.md) | The model trains on `Rg` and was evaluated on `Kg`. |
| [Matched budget made it worse](2026-08-04-matched-budget-run-and-the-hairline-defect.md) | The hairline defect — generated stroke weight collapsed 27%, with a healthy loss curve. |

## Levers tried, and what they cost

| note | |
|---|---|
| [Rank 64 reallocates capacity](2026-07-31-rank64-redistributes-capacity.md) | ⚠ **Title retracted.** The reallocation claim rests on the biased statistic. What survives is the note's own first section, headed *"The population answer: no"* — rank 64 shows no difference on any metric. |
| [Distinctiveness oversampling](2026-08-02-distinctiveness-oversampling.md) | ⚠ **Both title claims voided.** The redistribution is the biased statistic, and "beats the 9B on one font" is Bitcount Grid — a font whose reference image is byte-identical to another holdout entry with different ground truth. |
| [Stacking overshoots — rank 64 alone is the lever](2026-08-05-stacking-levers-overshoots-rank64-is-the-lever.md) | ⚠ **Half retracted, half the strongest claim here.** "Rank 64 is the lever" is gone; "do not stack" is confirmed at −13.5×SE and mechanically, at 20% over-inked. |
| [Corpus expansion v3](2026-08-03-corpus-expansion-v3-result.md) | Targets improved, the majority regressed, and the run carries a self-inflicted confound. |
| [Corpus expansion and variable instancing](2026-08-02-corpus-expansion-and-variable-instancing.md) | Where the extra fonts could come from, and the atlas/reference loader trap. |
| [The 4B's spare VRAM is not spendable](2026-07-30-4b-training-levers.md) | Only rank is. |
| [The licence filter costs ordinary fonts](2026-08-09-the-licence-filter-costs-ordinary-fonts.md) | Removing the proprietary fonts cost 0.14 char_acc, concentrated in ordinary faces. |

## Selection and best-of-N

| note | |
|---|---|
| [The headroom is real and unharvestable](2026-08-02-4b-bestofn-headroom-is-real-but-unharvestable.md) | The 4B has the 9B's sampling headroom; no selector tried can reach it. |
| [Reference-anchored selection fails](2026-08-02-reference-anchored-selection-fails.md) | The style lottery is **per-cell, not per-atlas** — which rules out every seed-level and atlas-level selector. |
| [Hybrid replay](2026-07-17-hybrid-replay-analysis.md) | A no-GT OCR-swap realization of the oracle hybrid. |
| [Generator track decision](2026-06-03-generator-track-decision.md) | Why the GT-guided preference-optimization (DPO) track was closed. |

## The corpus: provenance and licensing

| note | |
|---|---|
| [The corpus is not 97.5% OFL](2026-08-08-the-corpus-is-not-97-percent-ofl.md) | ⚠ **The title is the original claim; the body corrects it.** 87.0% OFL, and the "51 Microsoft fonts" headline became 49 fonts under vendor terms from several foundries — Inter and Lato were false positives found by reading name ID 13 instead of the folder path. |
| [Identifying the undocumented 13%](2026-08-08-identifying-the-undocumented-13-percent.md) | How 121 fonts entered the corpus without provenance, and how they were traced back. |
| [OFL derivative-work constraint](2026-07-27-ofl-derivative-work-constraint.md) | SIL's position: fonts from a model trained on OFL sources are derivatives and must themselves be OFL. |
| [Klein licensing and the 4B port](2026-07-27-klein-licensing-and-4b-port.md) | The production base is non-commercial; the Apache-2.0 alternative is also the speed win. |
| `2026-08-01-bfl-commercial-licensing.md` | Available, but this architecture cannot use the cheap tier. **Held in the private archive** — it ranks commercial routes with price estimates. |
| `2026-04-09-legal-font-sources.md` | Early survey of where a corpus can legitimately come from. **Held in the private archive** — an LLM-scout report asserting named vendors' licence terms with "high confidence", and carrying foundry contact addresses. |

## Base models and runtime

| note | |
|---|---|
| [Successor-model survey](2026-07-31-successor-model-survey.md) | Is there anything better than FLUX.2 for this task? |
| How to generate the reference (`2026-08-22-how-to-generate-the-reference.md`) | **held privately — product recipe** · Options for producing the two reference glyphs from a description. Generate BOTH in one call. VecGlypher is purpose-built; GLM-Image int4 is already on disk and our objection to it inverts. |
| Two-letter reference generation options (`2026-08-22-two-letter-reference-generation-options.md`) | **held privately — product recipe** · Speed and fit for the named candidates. Nano Banana Pro 2-5s; GPT Image 2 ~195s at high quality. Ideogram 4 shipped OPEN WEIGHTS and fits a 3090. VecGlypher's weights are out but 27B does not fit. |
| Ideogram 4, fully explored (`2026-08-23-ideogram-4-fully-explored.md`) | **held privately — product recipe** · The best technical fit for reference generation -- bbox JSON places both glyphs in one call, NF4 fits a 3090 -- and its weight licence is NON-COMMERCIAL. Permitted for R&D now, blocked for the SaaS. Corrects the previous note, which ranked it first without reading the licence. |
| Restyle, don't generate (`2026-08-23-restyle-not-generate-the-reference.md`) | **held privately — product recipe** · **Qwen-Image-Edit-2511 is Apache-2.0 and fits at INT4 (11-16 GB)**, which revives restyling a neutral pair — consistency by construction, and no licence blocker. Also: NO typeface-invention benchmark exists, so our gate has no published equivalent. |
| The permissive local field opened up (`2026-08-23-the-permissive-local-field-opened-up.md`) | **held privately — product recipe** · Three Apache-2.0 models now fit this GPU. **Z-Image-Turbo gained img2img** (reopening a closed track): 6B, 6 GB GGUF, 3.4s -- ~10x faster than Qwen-Image-Edit's ~36s on a 3090. |
| Round 3: the numbers that were missing (`2026-08-23-round3-the-numbers-that-were-missing.md`) | **held privately — product recipe** · Z-Image-Turbo finally has text numbers: 0.917 LongTextBench and the **highest CLIP score of any model tested**. Plus the img2img strength band to restyle in (0.30-0.45). Research has converged. |
| Candidate evaluation, round 1 (`2026-08-23-candidate-evaluation-round-1.md`) | **held privately — product recipe** · **Our own base model already does it.** FLUX.2-klein-base-4B generates two-glyph references that read correctly 100% of the time and clear the gate 12/12, at 25s and zero download. |
| [The loop closes](2026-08-23-the-loop-closes.md) | **A style described in words produces a coherent 94-glyph typeface**, end to end on local Apache-2.0 weights at ~90s per font. Synthetic references do NOT break the generator -- the main risk is retired. Style adherence is the one axis with no instrument. |
| [Style adherence + its retraction](2026-08-24-style-adherence-the-wrong-formulation-failed.md) | ⚠ **Partly retracted after adversarial review.** I invented a third label after seeing the data, and the 'different question' defence was false -- win_rate == (n-rank)/(n-1) exactly. What survives is an exploratory association on one fixed set, not a gate. |
| [CLIP does not read the decisive clause](2026-08-24-clip-does-not-read-the-decisive-clause.md) | **Pre-registered and committed before running.** Minimal pairs differing in ONE attribute: 6/12, p=0.61, exactly chance. Generic CLIP is ruled out for style adherence. The decisive clause moves cosine by ~1%. |
| [What the atlas carries](2026-08-24-what-the-atlas-carries.md) | **Pre-registered, bar committed before the run.** Six existing features separate weight (0.970), mono (0.946), slant (0.915) and width (0.839) on held-out FAMILIES. Stencil and inline have only 10 families each, so the corpus cannot label the two attributes that actually failed. Two of my own counts were wrong: PANOSE read without bFamilyType overstated serif labels 3.5x. |
| [The transfer test passed, and that is not the finding](2026-08-24-the-transfer-test-passed-and-that-is-not-the-finding.md) | Pre-registered primary CONSISTENT -- both recorded hits rank 1/12, neither miss does. But the descriptive column shows the STENCIL model's favourite generated atlas is the INLINE one: `parts` counts pieces and cannot tell a break from a stripe. Ranks transfer, absolute probabilities do not. |
| [A break is not a stripe](2026-08-25-a-break-is-not-a-stripe.md) | **10/11 real held-out typefaces, p=0.0059**, bar committed before the run. Components VERSUS holes separate stencil from inline; BigShoulders is correct on both sides. On the twelve generated atlases it calls the stencil request SOLID -- the first measure here to read an adherence failure as a failure. Unrestricted 4-way is 4/11: it ranks, it does not calibrate. |
| [Two glyphs are enough, barely](2026-08-25-two-glyphs-are-enough.md) | **9/11, p=0.0327 -- exactly the bar, not a margin.** The adherence measure survives seeing only the two glyphs a user is shown, so the picker can select at the cheap stage. The one extra error lands on BigShouldersInline, the only row where the typeface is held constant. |
| The picker works, except where it is needed most (`2026-08-25-the-picker-works-except-where-it-is-needed.md`) | **held privately — product recipe** · **Ratio 0.518, p=0.0005** -- four seeds of one description ARE a real choice. But spread runs 0.454-3.960 and is NARROWEST where the generator fails: four seeds of 'a stencil sans with deliberate breaks' produce four solid faces. Re-rolling cannot rescue a systematic miss. |
| The style reaches the letters nobody chose (`2026-08-25-the-style-reaches-the-letters-nobody-chose.md`) | **held privately — product recipe** · **11/16, p=0.0003** -- an atlas matches its OWN reference more than the other three of its description, scored on the 92 cells EXCLUDING the copied K and g. The picker is not theatre. Also: a truncation landing on an underscore silently dropped the widest description from the first run. |
| [The weak attribute was a sample](2026-08-25-the-weak-attribute-was-a-sample.md) | serif-vs-sans was 0.733 on one 50+50 family sample and is **0.869 on a disjoint one**. The terminal-shape feature built to fix it scores **-0.024**. A 0.136 AUC swing, and every other attribute number is a SINGLE sample. |
| Eight of twelve offer no real choice (`2026-08-25-eight-of-twelve-offer-no-real-choice.md`) | **held privately — product recipe** · **8 of 12 descriptions produce four candidates the gate would call one typeface.** Cut taken from the gate's own 1.875, not invented. The picker is sound and rarely load-bearing. |
| The second arm fails the same way (`2026-08-25-the-second-arm-fails-the-same-way.md`) | **held privately — product recipe** · **Eight seeds, two independent models, not one break.** The stencil failure is not a property of our generator -- it is the task. Z-Image-Turbo works but separates the twelve descriptions less than HALF as well (between 1.172 vs 2.514); 11/12 narrow. Both GLM paths dead. |
| The edit path does not break a stroke either (`2026-08-25-the-edit-path-does-not-break-a-stroke-either.md`) | **held privately — product recipe** · Restyling a neutral Kg fails the same way, and the sweep shows why: up to strength 0.70 the model returns the source UNTOUCHED, at 0.90 it makes a heavier solid face. No middle. Closes img2img-on-a-t2i-model, NOT edit-native models. |
| [The gate clears its bar — and the seed clears it higher](2026-09-13-the-gate-clears-its-bar-and-the-seed-clears-it-higher.md) | **Calibration round 2, registered bar PASSED verbatim:** on 96 owner labels (Z-Image 25 usable / 23 not, the owner "slightly lenient") the gate's distance predicts acceptance at AUC 0.839, p = 0.0001; at the 1.875 cut precision 0.90, recall 0.85, specificity 0.70. Then the unregistered part: every negative is Z-Image (set effect AUC 0.76); within Z-Image the gate reads 0.73, but each seed index is one noise draw shared across the twelve descriptions (seed 1 rejected 12/12, seed 2 accepted 10/12 at distance 0.61), and with the seed held fixed the gate reads **0.36, p = 0.89** — the whole correlation runs through the draw. Two of the seven false passes rank first and eighth of 96 on coherence: coherent wrong styles, the gate's known blind spot. No threshold cut; the fresh sample needs one seed per reference and the generator hidden. |
| [The dose is graded; the order holds and the share does not](2026-09-13-the-dose-is-graded-and-the-order-holds.md) | **Registered before the run; two predictions held in full, one in part.** Fattening the `i` alone to 1.5× / 2× / 3.1× moves the ink-width CV by +0.022 / +0.044 / +0.105 — monotone and roughly proportional. Under Lato the prediction *widen_narrow ~ equalised >> condense* held in full; under seed 43 the sign, the rank order and the IDENTIFIED verdict reproduced but the middle clause failed (0.64 of the fall against 0.97 and 0.96), so the `i`-alone share is quoted as 0.64–0.97. The fall in width spread (−36 to −39%) is the constant across runs; the delivered face is heavier every time (bbox fill 0.51 / 0.65 / 0.67 against 0.45 / 0.51 / 0.40 plain) and by a different route each time — seed 43 reaches CV 0.241 by adding weight, not by condensing. |
| [Forty-eight of forty-eight: the calibration set has no negatives](2026-09-12-forty-eight-of-forty-eight-the-calibration-set-has-no-negatives.md) | The owner judged every klein-base candidate reference usable, so the pre-registered AUC bar is NOT EVALUABLE (one class; the script's first pass had printed FAILED with p = 0.0001 from no information — fixed and pinned). What the set measures: the gate's recall at its 1.875 cut is 0.96 — `02-s1` and `04-s1` would be sent back. Negatives have to come from the Z-Image and external sets. |
| [Six seeds for the other three metrics](2026-09-12-six-seeds-for-the-other-three-metrics.md) | The twelve six-seed candidate sets re-scored with `eval_checkpoint`, the registered statistic applied unchanged: IDENTITY resolves for the 9B by a hair (+0.0056, CI [+0.0007, +0.0107]); R-ACC (+0.0084) and the README composite (+0.0099) do not, their seed-blocked intervals including zero even where the font-paired Wilcoxon says otherwise; DINOv2 and LPIPS reproduce the 2026-08-08 intervals exactly. |
| [A relational treatment transfers when the pair can carry it — and what carries it is each glyph's deviation](2026-09-12-a-relational-treatment-transfers-when-the-pair-can-carry-it.md) | **Pre-registered twice, before each run.** Draw the monospace reference from `Mi` (ink widths 301 / 57 px, ratio 5.28) instead of `Kg` (1.08) and the same checkpoint pulls the other ninety-two widths together: CV 0.382 → 0.272, PARTIAL, stencil control intact. The registered controls say what was read: both glyphs scaled by one factor with the ratio kept reproduces 26% of the fall, the `i` fattened alone 97%, the `M` narrowed alone 61%. Not the equality, then, but each glyph's departure from its normal width, applied to the letters of its kind — the hallmarks a monospace designer draws. "Local yes, relational no" does not hold; neither does "the model reads equality". One seed, one source face. |
| [A relational treatment does not transfer — under a weak signal](2026-09-11-a-relational-treatment-does-not-transfer-under-a-weak-signal.md) | **Pre-registered, amended before the run to declare the weak signal.** Equalise the `Kg` widths and the LoRA returns the plain atlas to within 0.7/255 (ink-width CV 0.402 → 0.403) while the stencil control reproduces its signature. Bounds the stencil finding to LOCAL treatments, conditionally: the pair is fixed at `Kg`, whose widths already nearly agree. Monospace does not join the constructed vocabulary. |
| [Hand it a stencil and it propagates one](2026-08-28-hand-it-a-stencil-and-it-propagates-one.md) | **The stencil problem has an answer, and it was never a model problem.** No generator will INVENT a stencil, but hand the LoRA one and it propagates the treatment to the 92 letters it was not given: parts 0.74 -> 2.15, holes 0.20 -> 0.02. The inline positive control moved the OTHER way. |
| [The distilled 4-step path](2026-07-30-distilled-4step-path.md) | 9× faster, but the LoRA does not transfer to it. |
| [Training the LoRA on the distilled model](2026-07-31-distilled-trained-lora.md) | Recovers most of the transfer loss. |
| [The 4B de-risk gate](2026-07-30-klein-4b-derisk-gate.md) | Passes, but the 4B is behind at a matched checkpoint. |
| [Sub-minute feasibility](2026-05-31-beat-v3-subminute-feasibility.md) | What sub-minute inference would require. |
| [Making the 3090 work](2026-06-02-3090-solutions.md) | Fitting a 9B transformer into 24 GB. |
| [Inference step scaling](2026-04-12-step-scaling-test.md) | Closed — more steps do not help. |

## Early design and post-processing

[Post-processing techniques](2026-04-02-post-processing-techniques.md) ·
[Atlas quality and raster-to-vector](2026-04-03-atlas-quality-improvements.md) ·
[Cutting-edge font tools](2026-04-03-cutting-edge-font-tools.md) ·
[Hybrid approaches](2026-04-03-hybrid-font-approaches.md) ·
[FLUX.2 LoRA training framework](2026-04-04-flux2-lora-training-framework.md) ·
[Adversarial analysis](2026-04-12-adversarial-analysis.md) ·
[round 2](2026-04-12-adversarial-analysis-round2.md) ·
[round 3](2026-04-30-adversarial-analysis-round3.md)

## Literature scouting

Twenty-one parallel-agent survey rounds from March 2026, plus three later
sweeps. Useful for what was considered and rejected early; superseded on every
empirical question by the notes above.

`2026-03-26-oracle-round{2..12}-report.md` ·
`2026-03-28-oracle-round{13..20}-report.md` ·
`2026-03-29-oracle-round21-report.md` ·
`2026-03-26-oracle-full-report.md` — **the twenty-one March rounds, the
synthesis `RESEARCH.md` and `BRAINSTORM.md` are market and business research
for a possible commercial direction, and are held in the private archive
(`digital-rain-private`) rather than published; see
[`docs/public-release.md`](../docs/public-release.md)** ·
[cutting edge](2026-07-17-oracle-cutting-edge.md) ·
[solutions sweep](2026-07-27-oracle-solutions-sweep.md) ·
[last mile and generator](2026-07-27-oracle-sweep2-lastmile-and-generator.md)

---

## Data artifacts

The notes cite these; the tools regenerate them.

| file | produced by |
|---|---|
| `training_variance_{char_acc,dinov2,composite,racc,lpips}.json` | `analysis/training_variance.py` |
| `claim_ledger.json` | `analysis/claim_ledger.py` |
| `calibration_labels.csv`, `calibrate_instruments.json`, `2026-09-12-calibrate_instruments.json` | the owner's usable / not-usable labels over the candidate references (`analysis/calibration_sheet.py` builds the sheet), the registered analysis's current record (`analysis/calibrate_instruments.py`), and the round-1 record preserved when round 2 replaced it |
| `2026-08-13-training_variance_*.json`, `2026-08-13-claim_ledger.json` | the three-run versions of the two rows above, preserved when the five-run regeneration replaced them on 2026-09-13 — the 2026-08-13 notes tabulate these |
| `retrieval_baseline.json` | `analysis/retrieval_baseline.py` |
| `corpus_provenance.json`, `corpus_exclusions.json`, `unlicensed_corpus_fonts.json` | `analysis/audit_corpus_provenance.py` |
| `font_distinctiveness.json`, `holdout_distinctiveness.json`, `pool_distinctiveness.json` | `analysis/score_holdout_distinctiveness.py` and the selectors |
| `per_cell_medoid.json`, `per_cell_classifier.json` | the best-of-N selection probes |
| `expansion_set.json`, `replacement_set*.json` | `analysis/select_expansion_set.py` |
| `2026-*-wilcoxon_*.json` | `analysis/compare_runs.py`, one per A/B — **read the variance notes before quoting any of them** |
