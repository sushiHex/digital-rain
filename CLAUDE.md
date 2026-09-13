# CLAUDE.md — fonts

*What this file is: the working brief for the coding agents that do the work in
this repository. It is written in the imperative, and most of it is a list of
mistakes already made once — which is why it reads as a series of warnings
rather than as documentation. It ships in the public export because every fact
in it is public-safe, not because it is an introduction. **If you are a human
arriving here, start with [`README.md`](README.md) and
[`docs/what-happened.md`](docs/what-happened.md) instead**; this file will make
more sense afterwards.*

Glyph-conditioned font generation: FLUX.2-klein-9B (qint8 train / qfloat8 infer) + rank-32 LoRA with a
glyph-latent conditioning channel. Research repo, single RTX 3090.

Current state and results: `README.md`. Dated findings: `research/`.

---

## The two-axis rule — read this before touching any metric

`char_acc` is **not** letter correctness — but it is also **not "style
fidelity"**, which this file claimed until 2026-08-07. Read
`eval_checkpoint.compute_char_acc`: within one font it builds a 94x94 cosine
matrix against that font's OWN GT cells and scores cell *i* as a match when
`argmax_j sim(gen[i], gt[j]) == i`. Its own docstring says *"within a single
font, all 94 cells share the same style, so cosine similarity within a font is
dominated by glyph identity"* — style is largely **controlled for**, not
measured. It is within-font shape discriminability, validated as neither axis.

Say "char_acc is not exact letter correctness". Do not say it measures style.

**IDENTITY** (`glyph_classifier.py`, font-invariant 94-class CNN, val_acc 0.9385,
GT-gated) is what answers "is it the right letter": **0.9936**.

**But know what that 0.9936 is, and do not call it 94-class accuracy.** On the
same 4,400 gated cells (`analysis/verify_identity_definitions.py`):

| definition | gated | all 4,700 |
|---|---|---|
| exact 94-class | 0.9355 | 0.9243 |
| case-insensitive | 0.9889 | 0.9785 |
| case + `EQUIV` (**the reported number**) | **0.9936** | 0.9879 |

`identity_score.EQUIV` merges `0/o/O`, `1/l/L/i/I/|`, `5/s/S`, `2/z/Z`, `8/b/B`,
`9/g/G`, `u/U/v/V` after folding case — fair for **isolated** glyphs, where `O`
vs `0` is genuinely undecidable, but it is a *recognizability* score, not
identity. The GT gate also drops the 300 hardest cells (char_acc 0.40 there vs
0.71 kept), lifting the number further, and GT confidence is not persisted so
the 0.5 threshold cannot be re-examined from the records.

The two-axis conclusion is unaffected — identity is 0.92–0.99 against char_acc
0.69 on every definition — but quote the definition you mean.

So `char_acc ≈ 0.69` does **not** mean 31% of characters are wrong. From
`research/2026-07-18-wrong-letters-are-a-metric-artifact.md`: the genuine
wrong-letter rate is **~3.2% of cells** (151 cells, and even those are largely
TrOCR misreads of isolated capitals), against the ~31% char_acc implies. In
scope — excluding dot-grid and heavy-distress fonts whose style deletes the
identifying stroke — it is ~1%. Independently, same-model best-of-4 lifts
char_acc +0.148 by resampling alone, and **88.6%** of the cells a different seed
"fixed" were already identity-correct at seed 0.

Consequences that keep getting rediscovered the hard way:

- **Never treat a char_acc delta as a correctness delta.** Report both axes.
- **char_acc is blind to identity-only regressions.** A real conditioning bug
  showed p=0.948 on char_acc and p<1e-6 on IDENTITY. Score with `--identity`.
- **Single-seed A/B measures a style lottery** as much as a model difference.
- Do not resurrect a "char_acc ≥ 0.85" ship gate. See the SUPERSEDED section of
  `docs/quality-roadmap-v3.md`.

## A single-seed A/B cannot resolve a model difference

**Read this before quoting any p-value from `compare_runs.py`.**

Decomposing four seeds of ONE 4B checkpoint (`analysis/seed_variance.py`, on
`bestofn_4b/scores.json`, where every difference is noise by construction):

| component | SD | behaviour |
|---|---|---|
| **seed MAIN effect** | **0.0248** | shifts every font together; does NOT average out |
| font x seed residual | 0.0534 | averages out as 1/sqrt(50) |
| a run's holdout mean | 0.0259 | **91% is the seed main effect** |

So a single-seed A/B carries **SE ≈ 0.037** on the difference, and the headline
4B→9B char_acc gap of 0.0457 is **≈1.2 SE**. Six seeds per model takes it to
3.1 SE.

The paired Wilcoxon pairs by **font** and treats fonts as independent
replicates, so it answers "is B better on more fonts than A" — with one seed
each, a seed effect lifting all 50 fonts is perfectly confounded with the model
effect and no font-paired test can see it. p=0.0001 and 1.2 SE are both true of
the same data; they are different questions.

This applies to **every single-seed A/B here, including all five levers.**

## TRAINING-run variance — MEASURED 2026-08-13, and it swallows the record

Three runs, config identical except `--seed`, clean corpus, 4530 steps
(`analysis/training_variance.py`, `research/training_variance_*.json`):

char_acc run means **0.4914 / 0.6070 / 0.5869**.

| metric | run-mean SD | 95% CI (2 df) | largest observed gap | gate fires on IDENTICAL configs |
|---|---|---|---|---|
| char_acc | 0.0618 | [0.032, 0.388] | 0.1157 | 2/3 |
| dinov2 | 0.0228 | [0.012, 0.144] | 0.0439 | **3/3** |
| racc | 0.0080 | [0.004, 0.050] | 0.0151 | 1/3 |
| composite | 0.0035 | [0.002, 0.022] | 0.0070 | 0/3 |
| lpips | 0.0027 | [0.001, 0.017] | 0.0049 | 1/3 |

**Training noise is metric-dependent by ~20x, and char_acc/dinov2 — the two
metrics chased hardest here — are the least stable.**

Every headline claim, each against **its own** metric's noise (the 3-run σ;
the five-run re-score is below):

| claim | metric | effect | ×SE | ×largest observed gap |
|---|---|---|---|---|
| 4B→9B | dinov2 | +0.0440 | 1.36 | **1.00** |
| licence filter (corrected) | char_acc | −0.0765 | 1.07 | 0.66 |
| 4B→9B | char_acc | +0.0731 | 0.84 | 0.63 |
| oversampling / rank 64 | composite | ~+0.003 | 0.6 | 0.4 |
| LR-horizon fix | char_acc | +0.0277 | 0.32 | 0.24 |

**Corrected 2026-08-13** (`research/2026-08-13-the-claim-ledger-corrected.md`,
`analysis/claim_ledger.py`): scored on EVERY metric rather than one each, **six
effects do clear 2 xSE — and ALL SIX are regressions**:

| effect | metric | xSE |
|---|---|---|
| rank64 + oversampling | lpips / composite / racc | **−13.5 / −7.8 / −2.0** |
| 4B → 9B | lpips | **−4.3** (the 9B is WORSE) |
| licence filter | composite | −2.2 |
| LR-horizon fix | lpips | −2.0 |

Every resolvable effect lives on **LPIPS or composite** — the stable metrics.
char_acc and dinov2 resolve nothing, and a retrieval baseline beats every model
on both. Use composite and LPIPS as the headline metrics.

**Re-measured on FIVE runs, 2026-09-13** (seeds 42–46, 4 df, issue #13;
`research/2026-09-13-five-runs-and-the-noise-floor-moved.md`). The interval
on σ narrowed from ~12× wide to ~5×, and two point estimates moved the wrong
way for the record:

| metric | run-mean SD, 3 runs | **5 runs** | 95% CI (4 df) | gate fires on identical pairs |
|---|---|---|---|---|
| char_acc | 0.0618 | **0.0603** | [0.036, 0.173] | 7/10 |
| dinov2 | 0.0228 | **0.0368** | [0.022, 0.106] | 8/10 |
| racc | 0.0080 | **0.0058** | [0.003, 0.017] | 1/10 |
| composite | 0.0035 | **0.0031** | [0.002, 0.009] | 1/10 |
| lpips | 0.0027 | **0.0061** | [0.004, 0.018] | 3/10 |

Seed 46 is the outlier — best char_acc (0.6558) and DINOv2 (0.8792) of the
five, worst LPIPS (0.1545) — which is what widened the DINOv2 and LPIPS σ.
Re-scored against the five-run σ (`analysis/claim_ledger.py`, whose
licence-filter arm now averages all five clean runs, not the first three),
**four effects clear 2 xSE, not six**, still all regressions: rank64 +
oversampling (composite −8.9, lpips −6.0, racc −2.8) and the licence filter
(composite −2.2). **The 4B → 9B LPIPS regression (now −1.9) and the
LR-horizon fix's (−0.9) no longer clear it.** Do not quote the "six effects"
line above as current; the table there is the 3-run record.

Rules that follow:

- **Divide an effect by ITS OWN metric's SD.** Quoting a dinov2 effect against
  char_acc's SD understated resolvability 2.7x in the first draft of this very
  note — the third time this repo has logged a cross-metric mix-up.
- **Do not treat the largest observed gap as a threshold.** It is the range of
  a 3-sample set; it grows with the number of runs and guarantees nothing.
- Changing the corpus changes the dataset size, hence the shuffle sequence —
  so two runs with the same `--seed` are still different training runs.
- σ rests on 4 df with a ~5x-wide CI (2 df and 12x until 2026-09-13), and was
  measured on ONE config — 4B, rank 32, clean corpus. The 9B has no replicate
  training runs. `analysis/claim_ledger.py` reads `n_runs` from the records
  and prints the df and CI width it is actually using; quote those, not this
  line.

## `compare_runs.py` passes on runs that differ by NOTHING

Run unmodified on two runs differing only in `--seed`:

    char_acc  p=0.0000  r=0.731  SIG (B better)
    dinov2    p=0.0000  r=0.742  SIG (B better)
    identity  p=0.0346  r=0.473  SIG (B better)
    composite p=0.0688  r=0.257  no diff

For scale, README's flagship row is *"DINOv2, 9B better, p<1e-5, r=0.768"* —
against r=0.742 here for **no difference at all**.

The tool is not broken; it is being misread. It pairs by **font** and answers
*"is B better on more fonts than A"*. Any component shifting every font together
is invisible to it, and here that common shift is 43–52% of the difference. Its
verdict is only interpretable when the two arms share a training run (i.e. for
inference-seed comparisons), or when the effect is large against run-level
noise — which nothing here has been.

**Never report a `compare_runs.py` SIG verdict between two training runs as an
established difference without replicate runs.**

## Comparing two runs

One tool: `python analysis/compare_runs.py A/per_cell.json B/per_cell.json`.
Paired Wilcoxon on **per-font means**. Gate: **p<0.05 AND r≥0.3**.

- Effective n is the **50 fonts**, not the 4,700 cells. Never cell-bootstrap.
- Direction comes from `result.direction`, not `sign(median_delta)` — on a
  near-ceiling metric like IDENTITY most fonts tie exactly and the median delta
  is 0.0 while p=0.002.
- `analysis/compare_experiments.py` is a different question: run *provenance*
  (same dataset hash / hyperparameters), CLEAN/PARTIAL/DIRTY. Run both.
- Do not hand-roll a Wilcoxon. It has been re-implemented ad hoc several times
  and the tool found a significant R-ACC result every ad-hoc pass had missed.

## The redistribution statistic was biased — check `xnull` before believing it

`compare_runs.py` prints a REDISTRIBUTION block (Spearman ρ of each font's
delta against difficulty, plus hard/easy halves). **Until 2026-08-07 it
conditioned on the BASELINE, which is biased by construction:**

    Cov(a, b - a) = Cov(a, b) - Var(a)

so seed noise alone drives ρ negative and manufactures a hard-vs-easy gap.
Measured on 12 pairs of *different seeds of the same model* — true effect zero —
the old form returned **ρ = −0.253** and a spurious gap of **0.038**, one pair
reaching p=0.037. Conditioning on the midpoint `(a+b)/2` returns ρ = −0.000 on
the same data. `tests/test_redistribution_null.py` pins this.

**What that invalidated.** "Every lever redistributes quality from easy fonts to
hard ones" was substantially this artefact. Re-derived unbiased, against the
0.038 floor (`xnull` column):

| lever | char_acc gap | dinov2 gap |
|---|---|---|
| rank 64 | 1.5x | 0.7x |
| oversampling | 0.7x | 0.6x |
| corpus expansion | 1.0x | 0.7x |
| rank64 + oversampling | 3.6x | 1.4x |
| **9B vs 4B (the target)** | **1.0x** | **1.0x** |

Under ~1x is not distinguishable from seed noise. Do not quote a hard-half
number without its `xnull`.

**The midpoint fix is unbiased only when both runs have equal variance** —
`Cov((a+b)/2, b-a) = (Var(b) - Var(a))/2`. The null test uses same-model pairs,
which satisfy that by construction; whether the 4B and 9B do is unknown and is
one of the things the multi-seed run measures. And **difficulty defined from
the outcome is circular either way**: `research/font_distinctiveness.json`
scores the 925 TRAINING fonts and has **zero** overlap with the holdout, so a
non-circular moderator has to be built by scoring holdout GT atlases against
the frozen training-corpus centroid (`analysis/score_holdout_distinctiveness.py`).

## Where the 4B's remaining gap actually is — RESOLVED 2026-08-08

The matched multi-seed run landed. **Six inference seeds per checkpoint**,
44 unique fonts, pre-registered analysis (`analysis/multiseed_compare.py`):

| metric | 9B − 4B | 95% CI (fonts+seeds) | single-seed said |
|---|---|---|---|
| char_acc | **+0.0731** | [+0.0473, +0.0993] | +0.0457 |
| dinov2 | **+0.0440** | [+0.0325, +0.0555] | +0.0303 |
| LPIPS | −0.0007 | [−0.0175, +0.0166] | ties |

**The gap is real and ~60% BIGGER than the single-seed A/B showed.** That is
what the seed accounting predicted: seed 42 is lucky for the 4B (0.6460 vs a
0.6116 six-seed mean), so the old comparison used the 4B's best face.

Do not repeat "the 4B is not a quality compromise". It is one, on both metrics
that were ever in question. Shipping it rests on the Apache-2.0 licence and the
4-step speed win — which are good reasons, and are the actual ones.

**R-ACC, IDENTITY and the README composite were NOT scored in this run.**
`scores.json` carries only `char/char_acc_match/dino_cos/lpips/score/topo_pen`,
and that `score` is `score_candidates`' composite (`dino − λ·lpips − μ·topo`),
**not** `eval_checkpoint.compute_composite(lpips, racc, dinov2)` — same word,
different metric. **Re-scored at six seeds on 2026-09-12**
(`runners/run_rescore_multiseed.sh`, `analysis/multiseed_rescore.py`, the
registered statistic through the same function, record
`research/multiseed_rescore.json`): IDENTITY 9B − 4B **+0.0056 [+0.0007,
+0.0107]** resolves by a hair; R-ACC +0.0084 [−0.0063, +0.0233] and the README
composite +0.0099 [−0.0033, +0.0227] do **not**; DINOv2 and LPIPS reproduce the
intervals above to the fourth decimal. The composite's font-paired Wilcoxon
reads p = 0.0016 while its seed-blocked interval includes zero — the
`compare_runs.py` trap below, live. Quote the interval.

**The gap is concentrated in ORDINARY fonts, not distinctive ones** — the
reverse of the long-running story. Against the frozen, model-independent
moderator, char_acc ρ = **−0.536** (p=1.8e-4, collapsed n=44; −0.518 uncollapsed).
Quote the rank statistic, not the OLS slope: they disagree (slope −0.193,
SE 0.127, p=0.135), so the relationship is monotone but not linear.

`research/2026-08-08-multiseed-the-4b-9b-gap-is-real-and-bigger.md`

- **rank 64** is still the best candidate (+1% training time, no extra memory,
  composite +0.0029) but "closes ~30% of the hard-half gap" rests on the biased
  statistic and should not be repeated as fact.
- **Do not stack levers.** rank 64 + oversampling regressed 5 of 6 metrics.

## The training loop had three silent defects — two fixed, one deliberate

Audited 2026-08-08 (`research/2026-08-08-training-loop-audit-three-confirmed-silent-defects.md`).
None was visible in the loss curve.

- **The cosine LR horizon was in the wrong units, so it never annealed.**
  `--steps` counts MICROBATCHES; the scheduler advances per OPTIMIZER step. At
  `bs=1 accum=2 steps=5000` every checkpoint got 2,500 updates against a
  5,000-step horizon and stopped at **51.6% of peak LR** (derived 5.1603e-05;
  the log records 5.16e-05). Fixed: the horizon is now
  `ceil(steps/grad_accum)` and the cosine is clamped. `--legacy-lr-horizon`
  reproduces the old behaviour. **Every pre-2026-08-08 checkpoint has this.**
- **The SNR loss weighting is inert.** `compute_snr_weights` divides by the
  batch mean, which at `batch_size=1` is identically 1.0. The real objective in
  every checkpoint is unweighted velocity MSE. NOT changed — the formula's sign
  convention is disputed and needs checking against the paper first; the startup
  log now says so instead of advertising a weighting that is not applied.
- **Resume is not reproducible**: RNG, sampler position and pending gradients
  are not persisted, and the metrics file is truncated before resume handling.
  Prefer a fresh start over `--resume` when comparability matters.

## Two guards that must not be weakened

- **`build_dataset.find_fonts` refuses fonts without a permissive manifest
  licence.** This is how the corpus acquired an undocumented 13%: 121 fonts had
  no `font_pool/source_manifest.json` entry because they were copied straight
  into the scanned folder, bypassing `pipeline/fetch_fonts.py` — the only thing
  that records provenance. A recorded licence is not automatically an
  acceptable one; only OFL/Apache-2.0/UFL/MIT pass.
- **`train_lora_kg.py` filters the corpus by licence** via the tracked
  `research/corpus_exclusions.json` (838 keep / 87 drop). On by default;
  `--no-licence-filter` is the named opt-out.

## Eval CIs cluster by FONT, never by cell

`eval_checkpoint.bootstrap_ci` takes `font_cell_ranges` and resamples whole
fonts. It resampled CELLS until 2026-08-08, contradicting this file's own rule
and making every published interval **4.3x (dinov2) to 7.6x (lpips) too
narrow**. The 94 cells of one font share a typeface, a reference, a seed and a
trajectory; they are not independent observations.

## Check generated ink before believing a training result

Two runs failed in a way **training loss and the conditioning guard both
missed**: the model's stroke weight shifted globally. Loss was healthy — in one
case the *lowest* of any run.

The tell is lpips blowing out (0.18 vs ~0.13) while IDENTITY stays ~0.99 —
letters still correct, drawn at the wrong weight. Diagnose by comparing the
mean ink fraction. Use `python analysis/measure_ink.py` — do not hand-roll it.
Ink is the **bright**-pixel fraction, because the atlases are light glyphs on a
dark ground; measuring dark pixels returns ~0.93 for every run, preserves the
ratios between runs, and therefore survives review. Re-measured 2026-08-18 over
all 50 atlases (**GT 0.0652**):

- corpus expansion @6016 steps: **0.0440 (−32.5%)** — collapsed to hairlines
- rank 64 + oversampling: **0.0780 (+19.7%)** — over-inked
- baseline rank 32: 0.0632 (−2.9%) — for scale

Earlier revisions of this file recorded GT 0.0712 with 0.0527 (−27%) and 0.0820
(+15%). Those absolute values do not reproduce from the committed artifacts; the
direction and the conclusion are unchanged.

Two causes, both worth knowing. Selecting fonts by DINOv2 distance from the
corpus centroid selects for **near-blank** atlases, because the cheapest way to
be far from a centroid is to draw nothing (Amstelvar's `XOPQ` axis is literally
stem thickness). And distinctiveness does **not** correlate with sparseness
(ρ=0.060) — the distinctive tail is *heavier* than the corpus (0.0790 vs
0.0622), so oversampling it shifts the weight prior up.

`analysis/select_expansion_set.py` now enforces an ink floor. Any future
generated-font selection needs one too.

## Rendering a font pair: use ONE loader for atlas AND reference

`build_dataset.render_atlas` and `render_reference` have **different defaults**:
the atlas pins a variable font to its "Regular" named instance
(`load_truetype_pinned`), the reference opens it raw at axis defaults. For a
variable font those disagree, and the reference is the style-conditioning input
the model is trained to copy.

Letting each pick its own default mismatched **~110 of 177** additions in
`dataset_v3` — every instance plus 101 of 168 variable statics — teaching "this
reference → a different style". Both functions now take an explicit `loader`;
pass the same one to both. `build_expansion.loader_for()` is the example.

Also: **`dataset_v2` predates the pin.** A plain `ImageFont.truetype` render of
`Doto[ROND,wght]` is byte-identical to its corpus atlas; the pinned render
differs by 17.6/255. Anything added to that corpus must use
`select_expansion_set.corpus_default_loader`, or it introduces a second
convention. The same trap bit the *seed* render inside the selector, silently
changing which instances survive.

## The 50-font holdout is not 50 independent observations

`analysis/check_holdout_integrity.py`, by hashing the committed artifacts:

- **46 unique GT atlases, not 50.** IBMPlexSansArabic/Thai/ThaiLooped are
  byte-identical, as are TiroGurmukhi/Tamil/Telugu — non-Latin families whose
  *Latin* glyphs are shared, so a 95-char ASCII atlas is the same file. Those
  typefaces carry triple weight in every aggregate, and the paired Wilcoxon's
  n=50 is inflated.
- **45 unique reference images.** `BitcountGridDoubleInk` and
  `BitcountPropDoubleInk` share a byte-identical reference — the model's only
  input — but have *different* GT atlases (mean |diff| 36.6/255). The model
  therefore emits **byte-identical output** for both and is scored against two
  different answers. It cannot do well on both by construction; their char_acc
  split (0.1383 vs 0.2660) measures the target, not the model.

**Those two Bitcount fonts were repeatedly cited as per-font evidence** for the
oversampling and corpus-expansion work ("the weighted 4B beat the 9B on Bitcount
Grid"). Any per-font comparison between them is meaningless. Run the checker
before quoting a per-font number.

## The holdout excluded font FILES, not families

**32 of the 50 holdout fonts share a superfamily with a training font** — five
Playwrite holdout faces have 46 Playwrite siblings in the corpus; the holdout
carries `BitcountGridDoubleInk[...]` while the corpus carries `Bitcount[...]`
with the same structural axes. This is pre-existing and is not being changed,
because changing the holdout breaks comparability with every prior run.

Consequences: holdout scores are more in-distribution than they look, and any
corpus expansion must exclude candidates sharing a holdout *superfamily*, not
just exact stems. `analysis/select_expansion_set.py` does this and refuses to
run without the guard.

## Atlas geometry — `atlas_constants.py` is the only source of truth

95 chars, **12x8** grid, `CELL_W=106`, `CELL_H=160`, `BLANK_INDICES={71, 95}`
(the space, and one padding cell that pads 95 chars up to 96 slots), 94 drawn.

- Crop with `eval_checkpoint.crop_cell` (re-exported as `cleanup.cells.crop_cell`).
- **Never use `atlas_to_font.compute_grid()` on a trained-model atlas.** It infers
  a near-square layout from the character count — the superseded Ref2Font V3
  geometry — and slices between cells. Use `atlas_to_font.trace_atlas_cells()`.
- Glyph names need the Adobe Glyph List map in `atlas_to_font._GLYPH_NAMES`.
  33 of the 95 characters, every digit included, are illegal as literal
  OpenType glyph names.

## Conditioning must match training

Evaluating a checkpoint with a prompt it was not trained on is silent and
expensive: IDENTITY 0.9936 → 0.9780, all 50 fonts worse, invisible to char_acc.

`conditioning_config.py` records conditioning per checkpoint and infers it for
legacy ones. Derive `prompt_style` / `use_template` from the checkpoint — do not
hardcode them (`app.py::get_pipeline`, `eval_checkpoint`, and
`candidate_gen.resolve_conditioning` all do this). Pass `--strict-conditioning`
on evals.

This is not hypothetical twice over: `candidate_gen.py` called
`load_generation_pipe` without `prompt_style` for its whole life, silently
taking the `"structured"` default while **both** glyph checkpoints are
`train_lora_kg.py` lineage and want `"trained-short"`. Every candidate it ever
produced was mis-conditioned, including the best-of-N data behind the
`+0.148` headroom figure. Fixed in `f93b233`; the pre-fix artifacts under
`dpo_holdout_bestofn/` are still mis-conditioned, so their absolute values are
depressed — within-run comparisons on that data are still valid, cross-model
ones are not.

Do not reorder the steps in `generation_lib.load_generation_pipe`. The order
(encode prompt → free text encoder → quantize → widen `x_embedder` → load LoRA →
move to CUDA → install hook) is load-bearing; its docstring says why.

## Shared GPU

The 3090 is shared with other agents' sessions. Other work — Ollama models,
Unreal Editor — lands on it mid-run.

- **Gate before starting**, don't grab: poll `nvidia-smi --query-gpu=memory.free`
  until there's headroom. Runners use a 12 GB gate; measured need is ~9 GB.
- **Never force-evict** someone else's model to make room. Wait.
- `vram-mcp` (`vram_status`) shows claims and per-process usage.
- Grad checkpointing is mandatory for training; the 9B transformer does not fit
  in 24 GB otherwise.

## Long runs

Harness task-kills happen. The pattern in the 43 `.sh` runners under
`runners/` (moved off the root 2026-09-11; `runners/README.md` groups them by
track):

- `cd "$(dirname "$0")/.."` — runners self-locate and work from the repo
  root, so every relative path inside them (`dataset_v2`, `eval_runs/…`,
  marker files, logs) is unchanged by the move. Launch as `./runners/x.sh`.
  `tests/test_runners_self_locate.py` pins the line and that no `.sh` has
  crept back onto the root.
- Detach via PowerShell `Start-Process` so the run outlives the session.
- Terminal state is a **marker file**: `*_DONE` / `*_FAIL` (gitignored). Write
  the exit code into it. Never infer success from the absence of a crash.
- A `watchdog_*.sh` polls for the marker and relaunches if the outer loop dies.
- Watchdog thresholds must **match the runner's VRAM gate**. A mismatch made a
  legitimately-parked runner read as stalled — twice.
- **The watchdogs count the live runner with `python misc/count_running.py
  "<pattern>"`** (psutil), since 2026-09-12. They used `wmic`, which this
  Windows build no longer ships (checked 2026-09-11: `where wmic` finds
  nothing): the count read 0, so a watchdog would have relaunched a runner
  that was still running, every poll. **The helper prints `-1`, never `0`,
  when it cannot read the process table** — `[ "${outer:-0}" -eq 0 ]` treats
  any non-zero count as "alive", and a count that fails must not relaunch.
  It excludes the asking process and its whole **ancestor chain** by pid,
  which fixes a second defect the same line hid, pointing the other way: five
  of the eight watchdogs are named after the runner they watch, so
  `watchdog_stage_a_eval.sh` matched its own `wmic` line and could never have
  relaunched a dead one. Tested against a live dummy (issue #4); the residual
  is that a `python` missing from PATH still leaves `outer` empty, hence 0.
- Manifests and other inputs come from env vars (`PILOT_MANIFEST`,
  `SMOKE_MANIFEST`, `ORACLE_PROMPTS`), never a hardcoded path.
- **The global site-packages is shared with other projects on this machine
  and can change under a running job.** On 2026-09-12 another session
  upgraded `transformers` 4 → 5 (pulled in by `sentence-transformers`) while
  seed 45 was training; seed 45's eval had already run, seed 46's died on a
  tokenizer the new version could no longer build. The TrOCR loader is now
  `eval_checkpoint.load_trocr`, built from explicit classes that work on
  both, and every TrOCR user goes through it (seed 45 re-scored under both
  stacks: every per-font metric identical on all 50 fonts, 2026-09-13).
  When an eval dies mid-run on
  an import or tokenizer error, check the site-packages mtimes (`pip list`
  and `ls -la --time-style=long-iso`) before anything else. Do not downgrade
  the shared environment to fix a run: other projects pin against it.

## Layout and imports

Repo root holds the ~32 core modules; one-off scripts live in topical packages
(`analysis/ studies/ pipeline/ probes/ benchmarks/ misc/ cleanup/ viz/ route_b/`),
each with its own README listing contents.

- **Local imports are package-qualified**: `from analysis.compare_runs import …`.
  A bare `from compare_runs import …` works when run as a script and breaks
  under `-m`; six such imports were silently broken by an earlier refactor.
- Package modules carry a two-line `sys.path` bootstrap so both
  `python pkg/x.py` and `python -m pkg.x` work. Keep it when adding a module.
- When moving files, an import-graph scan is not sufficient: `tests/test_fetch_fonts.py`
  and `tests/test_font_quality.py` invoke scripts as **subprocesses**, so the
  path lives in a string. Grep for the filename too.
- Keep self-documented usage lines (`python pkg/x.py …`) accurate when moving.

## Outputs, and what is committed

`eval_runs/ training_*/ dataset_*/ experiments/ dpo_*/ tools/ models/` are
gitignored, as are `*.pt *.safetensors *.png *.log`.

A few files inside those trees **are** tracked, force-added on purpose: the
`per_cell.json` / `scores.json` for the two runs in the README results table, so
`analysis/compare_runs.py` reproduces it from a clean clone. List them with
`git ls-files -i -c --exclude-standard`. Add another with `git add -f`.

`experiments/` is a gitignored *output* directory — unrelated to the `studies/`
package.

## Worktrees and the data directories

On 2026-09-11 the gitignored data directories were junctioned into a
`git worktree` so a parked branch could run a GPU probe in parallel, and
`git worktree remove --force` then recursed **through** the junctions and
emptied `dataset_v2`, `font_pool`, `eval_holdout`, `google-fonts`, a
checkpoint and a probe's references. Everything came back from surviving
copies (`research/2026-09-11-the-junction-incident-and-what-came-back.md`),
which was luck, not design.

- **Never junction or symlink data into a worktree or any disposable
  directory.** A parallel tree gets the real directories by path argument, or
  the work runs sequentially in the main tree.
- **Before any recursive delete, enumerate reparse points**
  (`Get-ChildItem -Attributes ReparsePoint -Recurse`) and remove links with
  `rmdir`, which drops the link and not the target. `git worktree remove
  --force`, `rm -rf` and `Remove-Item -Recurse` all follow NTFS junctions.
- **Glob-style tools honour `.gitignore`.** Verify a gitignored directory with
  a literal `ls` / `Get-ChildItem`; an empty glob result there means nothing.
- After an incident: stop writing to the volume, report immediately and
  completely, and let the owner decide on undelete before regenerating
  anything. The private repository's `backup/` holds the data that cannot be
  re-downloaded or re-derived exactly (`misc/backup_private.py restore`).

## Licensing — hard constraints, not preferences

- **The repository's own licence, since 2026-09-11** (`docs/licensing.md`,
  `NOTICE`): code, configuration and calibration data **AGPL-3.0-only**
  (`LICENSE` is the verbatim text — never append project prose to it, a test
  pins this); notes, docs and figures **CC BY 4.0**; raw measurement records
  **CC0 1.0**; `route_b/` stays Apache-2.0. The line between the parts is
  function, not extension: a JSON that code LOADS is AGPL configuration, a
  JSON that code only WRITES is CC0 data. **No outside pull request is merged
  until its author's line is in `.github/CLA-signatures.md`** — an
  AGPL-only contribution would cloud any later commercial licence.
- The base model (**FLUX.2-klein-base-9B**) is **non-commercial**. The
  Apache-2.0 **klein-4B** port is the licensing fix and also the 4-step speed
  win; `in_channels=128` on both, so the template cache ports unchanged.
  `train_lora_kg.py` and `eval_checkpoint.py` default to the **4B** since
  2026-09-11 so a deployment that forgets `--model` cannot pick up the
  non-commercial base by accident; the shipped 9B runs pass it explicitly.
- The training corpus is **87.0% OFL**, NOT 97.5% — that number counted a raw
  Google Fonts checkout, not the 925 fonts trained on. **49 fonts (5.3%) carry
  vendor-supplied terms** permitting rendering but not redistribution or
  conversion (`arial`, `georgia`, `segoeui*`, `verdana`, `consola`, …); 4.9%
  is still unknown. Read the licence from the font's own name ID 13 —
  **never infer it from where the file lives**, as Inter and Lato are OFL and
  also sit in `C:\Windows\Fonts`. Two separate constraints: generated
  fonts are OFL derivatives per SIL FAQ 1.25 (an *output* constraint), AND
  there is an unresolved **right-to-train** question about the inputs that no
  output licence fixes. See `research/2026-08-08-the-corpus-is-not-97-percent-ofl.md`
  and `research/2026-07-27-ofl-derivative-work-constraint.md`.
- Consequence: do not publish weights or host a demo without addressing both.
  `LICENSE` states the downstream scope.

## The product has no ground truth — three axes, two instruments

Every metric above needs a target font. The product does not have one: the user
describes a style, a model draws the two reference glyphs, and a *similar real
font is the wrong answer, not a near-miss*. So the retrieval floor does not
apply to the product track, and neither do char_acc, DINOv2, LPIPS, R-ACC or the
composite. **Never quote a model-track result as evidence about the product
track, or the reverse.**

| axis | question | instrument | state |
|---|---|---|---|
| coherence | is this **one** typeface? | `analysis/style_coherence.py`, `analysis/reference_gate.py` | validated |
| identity | are these the right **letters**? | `glyph_classifier.py` | validated |
| adherence | is it the typeface **asked for**? | `analysis/synthesize_rare_attributes.py` | **partial**, uncalibrated |

- **The two coherence tools are different statistics; do not substitute one for
  the other.** `style_coherence` is a *dispersion* over 94 cells;
  `reference_gate` is a *distance* between two style vectors. Dispersion over
  n=2 is meaningless. Both z-score each feature against **that character's**
  distribution over 250 corpus fonts — the naive version measured which letters
  these are and returned p=0.970.
- **The gate must run before `get_pipeline()`** in `app.py`, and it **fails
  open**: anything unscoreable is generated normally. A test pins the ordering,
  because the first version was correct and useless. Its threshold (1.875) is
  cut from the coherent references' own spread, not from human judgement, so it
  is provisional and its recall is a floor. **Calibrated against 96 owner
  labels on 2026-09-13** (`analysis/calibrate_instruments.py`, registered
  first): the bar PASSED on the union (AUC 0.839, p = 0.0001; at the cut
  precision 0.90 / recall 0.85 / specificity 0.70), but every negative is
  Z-Image and each seed index is ONE noise draw shared across all twelve
  descriptions; with the seed held fixed the gate has no signal (AUC 0.36
  over within-seed pairs, within-seed permutation p 0.89), and two of the
  seven false passes rank first and eighth of 96 on coherence (coherent
  wrong styles). The cut stays 1.875 until a fresh sample with one seed per
  reference and the generator hidden; do not quote the union AUC as the
  gate's accuracy, and do not generate calibration sets with a seed shared
  across descriptions again.
  `research/2026-09-13-the-gate-clears-its-bar-and-the-seed-clears-it-higher.md`
- **Adherence is eyeballed.** ~9 or 10 of 12 prompts hit their style. *"Stencil
  sans with deliberate breaks"* produced a solid face at both stages — and
  **identity scored it 0.9787, among the highest of the twelve.** The instrument
  did not merely miss the clearest failure in the set; it rewarded it. Do not
  write "validated" next to this axis, and do not read a high identity score as
  evidence a style was delivered.
- **The owner's criterion for a starting point (2026-09-13): it should
  represent the prompt accurately.** The 96 usability labels in
  `research/calibration_labels.csv` were judged as "starting point" and were
  lenient on adherence, so they calibrate coherence, not adherence — a
  coherent wrong style counts as usable there and as a miss here. Any
  further labelling asks both questions per reference (usable as a starting
  point; represents the description), in one sitting, one seed per
  reference. The second answer is what #9 needs and what the picker should
  select on.
- **The 12-vs-50 comparison is confounded.** Atlases from invented references
  beat the 50-font oracle arm on every GT-free metric — but the oracle arm holds
  the hard cases (dot-grid Bitcount, heavy distress, cursive Playwrite) and all
  twelve invented styles came back conventional. **The generated set is easier.**
  Quote the table only with this sentence attached.
- Both reference glyphs go in **one generation call**, always. That is why
  coherence lands near the real references instead of splitting.
- `analysis/generate_candidate_references.py` **rejects malformed candidates
  with a reason** rather than scoring them. Keep that in any new arm: a method
  producing 80% garbage would otherwise measure as merely mediocre.

### Building the adherence instrument — what is settled

`research/2026-08-24-what-the-atlas-carries.md`. Four attributes are readable
from a rendered atlas by six features reused unchanged from `style_coherence`,
held out by FAMILY: weight 0.970, **mono 0.946**, slant 0.915, width 0.839.
serif/sans is 0.733 and **weak because no feature measures terminal shape** —
that is a feature limit, not an atlas limit, and the registration forbids fixing
it on the same data.

- **Count FAMILIES, not files.** Width is 4,556 files and **59 families**;
  variants cluster in superfamilies. Every holdout splits by family.
- **PANOSE `bSerifStyle` is meaningless unless `bFamilyType == 2`.** Read
  unguarded it overstated serif labels **3.5x** and mislabelled every decorative
  face. `tests/test_attribute_supply.py` pins this.
- **The corpus cannot label the attributes that failed.** stencil 10 families,
  inline 10, outline 3. Synthesis is the route: erase bands for stencil, remove
  a medial stripe for inline. Train on synthetic, **test on the real families
  held out entirely** — a classifier that learns "grid-aligned gaps" fails that.
- **An attribute is carried by what a designer DREW to express it, not by the
  metric that defines it.** I reasoned that ink-centring destroys monospace,
  because mono is equal *advances*. Advance CV is 0.0000 and destroyed; the
  attribute scores 0.946, because mono designers compensate in the ink. That
  reasoning would have dropped it. `analysis/advance_survives_atlas.py`.
- **FontCLIP is priced out**, not untried: no downloadable weights on the
  official repo, and the `optimizer` / VPT components are CC-BY-NC. A third
  licensing blocker is not worth it.
- **Readable is not an instrument, and the transfer test proved it.**
  `analysis/attribute_transfer.py` (pre-registered, `2f71122`) passed its
  primary — both recorded hits rank 1/12, neither miss does — and its
  descriptive column killed the interpretation. **The STENCIL model's
  favourite generated atlas is the INLINE one** (0.70), the outline second
  (0.49). `parts` counts components: a break, a stripe and a hollow contour are
  all "many pieces". The **mono** model, 0.946 on real fonts, likewise picks
  inline (0.82) and outline (0.80) over the atlas that asked for monospace
  (0.24). `research/2026-08-24-the-transfer-test-passed-and-that-is-not-the-finding.md`
- **Report RANKS, never absolute probabilities.** On generated atlases the
  weight model saturates: the three heavy prompts score 0.934–0.988 and rank
  7th, 1st and 6th. There is no calibrated threshold.
- **Train rare attributes against HARD NEGATIVES** — done, and it worked.
  `synthesize_rare_attributes.py` synthesises solid/stencil/inline/outline from
  the SAME source faces, so only the treatment is left to learn. **10/11 real
  held-out superfamilies, p=0.0059**, and `BigShoulders` — one typeface with
  both treatments — is correct on both sides. On the twelve generated atlases it
  calls the stencil request **solid**, the inline request **inline**, and the
  hairline **outline**: three for three against labels dated 2026-08-23.
  `research/2026-08-25-a-break-is-not-a-stripe.md`
- **`parts` alone conflates stencil, inline and outline.** Add `holes` and
  `hole_area` (`binary_fill_holes`). The stencil signature is counter-intuitive:
  breaking bands cuts counters OPEN, so stencil has FEWER holes than solid.
- **Collapse the rare attributes to SUPERFAMILY, not `family_of`.**
  `BigShouldersStencil*` and `BigShouldersInline*` are one typeface and three
  Sairas are another: 10+10 "families" are really 5+6.
- **CALIBRATION is the bottleneck now, not separation.** The same measure that
  scores 10/11 on the registered 2-way question scores **4/11** unrestricted —
  seven real rare faces read as `solid`. Twice-observed: the weight model
  saturated identically. Report ranks; there is still no threshold.
- **Any new attribute must be checked on GENERATED atlases before it is
  believed.** A per-attribute AUC on real fonts is not a claim about
  generations; mono went from 0.946 to picking the outline.
- **Two glyphs carry the measure, barely.** 9/11 at p=0.0327 against 10/11 at
  p=0.0059 for 94 cells, so the picker can select at the reference stage
  (~25 s) rather than the atlas stage (~62 s). **9/11 is the bar, not a
  margin** — one more error reads p=0.113. The extra error is
  `BigShouldersInline`, the only pair where the typeface is held constant.
  `analysis/reference_stage_adherence.py`.
- **Mirror `glyph_cells`' normalisation on BOTH sides.** It crops to ink and
  RESCALES to a fixed height; an atlas cell does not. Training on raw atlas
  cells and testing on reference images silently changes `width_cv`.
  `normalise_like_reference` is the copy, and a test fails if its docstring
  stops declaring it one.

### The picker — measured, and its limit

`research/2026-08-25-the-picker-works-except-where-it-is-needed.md`.
Within-description spread is **0.518** of between-description spread
(p=0.0005), so four seeds of one description ARE a real choice.

- **Spread runs 0.454-3.960 and is NARROWEST where the generator fails.** Four
  seeds of *"a stencil sans with deliberate breaks"* give four solid faces
  (spread 0.572); both recorded misses sit in the bottom half. **Re-rolling
  cannot rescue a prompt the model systematically misses.** The picker
  amplifies capability, it does not create it.
- **`--n` on `generate_candidate_references.py` keeps n=1 labels UNCHANGED.**
  `_synthetic_probe/external/`, `attribute_transfer.py` and the twelve atlases
  index by the `NN-` prefix. `--limit` cuts STYLES, not the flat list.
- **Kill GPU jobs by PROCESS, and verify.** `TaskStop` killed the wrapper shell
  and not the Python child; a run reported as stopped kept holding the card for
  an hour. Contention took one image from 1.3 s/step to 281 s/step.
- **The pick REACHES the atlas**: 11/16 atlases match their own reference more
  than the other three of their description, p=0.0003, mean rank 1.50 against
  2.50. Scored on the 92 cells EXCLUDING `K` and `g` — the model is conditioned
  to copy those two, so including them measures the conditioning, not the
  transfer. `analysis/reference_to_atlas_transfer.py`. Best-case by
  construction: only the four widest-spread descriptions.
- **NEVER split a candidate label on `__`.** The style prefix is truncated to 28
  characters and that cut can land ON AN UNDERSCORE, so
  `10-an_inline_face_with_a_white___s0` has three. `split("__")[0]` silently
  returns the wrong key; grouping still worked, so the diversity statistics were
  right under a wrong key, and a downstream glob then dropped the widest
  description from the transfer test WITHOUT ERRORING. Use
  `within_prompt_diversity.description_of`, `glob.escape` every pattern, and
  treat an unmatched key as a bug rather than an empty arm. Third glob/label
  mismatch here; the shape is always **the wrong answer looking like a smaller
  correct one**. `tests/test_candidate_labels.py`.

## A survey verdict is a measurement with a date

Two entries in the closed-tracks list below went stale within a month, and
nothing in the repository signalled it (`2026-08-23`). Qwen-Image-Edit-2511 "does
not fit 24 GB" was true at BF16 and false at INT4; Z-Image-Turbo "has no
image-conditioning path" was true when checked and is not now. **Before acting on
a closed track that rests on an external model's capabilities, re-check it.** A
track closed on our own measurement (DPO, best-of-N, reference-anchored
selection) does not expire this way.

## Closed tracks — don't redo these

- **GT-guided preference optimization (DPO)**: full pipeline built, reviewed,
  GPU-validated; Stage A regressed char_acc three times. Closed once
  seed-variance analysis showed the target gap was mostly style lottery.
  `research/2026-06-03-generator-track-decision.md`.
- **Nunchaku runtime LoRA**: no API for the FLUX.2-klein quantized transformer.
  `update_lora_params` / `set_lora_strength` are absent; `load_lora_adapter` /
  `fuse_lora` look available but are inherited from diffusers'
  `PeftAdapterMixin` and do not drive the quantized kernels. Sub-minute
  inference needs an offline merge + SVDQuant. `route_b/README.md`.
- **Generic CLIP as a style-adherence measure**: ruled out on a **pre-registered**
  minimal-pair test — 6/12, exact binomial p=0.6128, exactly chance
  (`analysis/style_adherence_minimal_pairs.py`, committed at `44dfddb` before it
  was run). Flipping the one decisive attribute moves cosine by ±0.001 to ±0.036,
  about 1% of a ~0.24 baseline; on an image that visibly carries an inline
  stripe, CLIP scored *"no inline stripe"* higher. Both backbones were tried
  (ViT-B-32 is exactly chance, ViT-L-14 reaches 17% top-1 against an 8% floor),
  so "try a bigger model" is tested, not untried. **Do not run another statistic
  over that 12x12 matrix** — the registration named FontCLIP (arXiv 2403.06453)
  or a per-attribute discriminative classifier as the next candidate, and that
  still stands. `research/2026-08-24-clip-does-not-read-the-decisive-clause.md`.
- **Inference-time style captions**: dead. The matching caption perturbs *most*.
- **Multi-reference at inference**: a wash. Reference-glyph identity does not
  matter either (Rg vs Kg, p=0.625).
- Also dead, per `docs/quality-roadmap-v3.md`: step-scaling, resolution sweeps,
  guidance-scale sweeps (Klein is guidance-distilled).
- **Best-of-N + no-GT selection on the 4B**: the headroom is real and matches
  the 9B's (+0.1638 within-run, 3.6x the whole 4B→9B gap), but nothing
  harvests it. The DINOv2 medoid that captures 14.1% on the 9B scores −4.9% on
  the 4B, whose seeds differ 6x more in overall quality. Medoid best-of-4
  = 0.6223 against the shipped single seed's 0.6460: 4x the inference cost,
  worse result.
- **Reference-anchored selection**: loses to plain medoid everywhere, and the
  font-level variant scores *below* no-selection. A seed that renders the
  reference glyphs well is not better on the other 93 — the style lottery is
  **per-cell, not per-atlas**, which rules out every seed-level and
  atlas-level selector. Only a per-cell signal can work.
- **Corpus expansion** (925 → 1,113, distinctive tail 93 → 122): significant
  regression, ~1:11 trade. `dataset_v3c/` is built and cached if anyone wants
  to retry; do not without a reason the ink floor did not already fix.
- **THE STENCIL PROBLEM IS SOLVED, and not by a generator.** No model will
  INVENT a stencil, but the LoRA **propagates one it is handed**. Three arms,
  one seed, scored over the 92 cells EXCLUDING `K` and `g`: stencil took parts
  0.736 → **2.148** and holes 0.203 → **0.015**; the inline positive control did
  the mirror image (parts flat, holes 0.203 → 1.332). Both moved in their OWN
  directions, which is what separates a transfer from a model reacting to any
  altered reference. **For rare treatments, SYNTHESISE the reference rather than
  generate it** — `synthesize_rare_attributes.py` already constructs them.
  `research/2026-08-28-hand-it-a-stencil-and-it-propagates-one.md`
- **A RELATIONAL treatment propagates too — through each glyph's deviation,
  not through the equality.** Equalising `Kg` (ink widths 231 / 214, ratio
  1.08) left the atlas untouched (CV 0.402 → 0.403). Equalising `Mi` (301 / 57,
  ratio 5.28) on the same checkpoint, seed and transform pulled the other 92
  widths together, CV 0.382 → 0.272, PARTIAL against the real-monospace band,
  stencil control intact. The registered controls then said what was read:
  both glyphs scaled by one factor with the ratio kept reproduces 26% of the
  fall; the `i` fattened alone reproduces **0.64–0.97** of it across three
  runs (0.97 on the record run; the face gets heavier and the thin letters
  become slabs); the `M` narrowed alone 61% (the face condenses). The model applies each glyph's departure from its normal width
  to the letters of its kind — what a monospace designer draws, not the
  metric that defines monospace. Do not quote "local yes, relational no", and
  do not quote "the model reads equality" either. Literal slab copies in
  `I`; the correlation of change with width proves nothing (`Cov(x, y−x)` is
  negative by construction). **Replicated 2026-09-13** (#30, registered
  first): the dose is graded (`i` × 1.5 / 2 / 3.1 → CV −0.022 / −0.044 /
  −0.105, monotone); under Lato the registered prediction held in full;
  under seed 43 the sign, the rank order and the IDENTIFIED verdict
  reproduce but the registered "widen_narrow ~ equalised" clause failed
  (0.64), so **do not quote "97%"** as the number. The equalised face comes
  back heavier every run (bbox fill 0.51 / 0.65 / 0.67 against plain 0.45 /
  0.51 / 0.40 — quote the delivered fill, not the within-run "+20/+50/+91%
  ink", whose range is mostly the differing plains), and by a different
  route each time (seed 43 adds weight without condensing). The constant
  across runs is the fall in width spread (−36 to −39%); the affine fit
  with slope ~0.5 is the shape the viz docstring names as the unexcluded
  alternative, not evidence for the reading.
  Records in `research/relational_widths.json`;
  `research/2026-09-12-a-relational-treatment-transfers-when-the-pair-can-carry-it.md`,
  `research/2026-09-13-the-dose-is-graded-and-the-order-holds.md`
- **Do not reuse `synthesize_rare_attributes._inline` at reference scale.** It
  thresholds against a GLOBAL `dist.max()`, which is right in a 106x160 cell and
  wrong on a 1024px reference, where a `K`'s junction sets the peak and the
  stems keep their cores — it erased 6.58% of the ink instead of half. The
  shared transform is NOT to be changed: the 10/11 classifier was trained on its
  output. `synthesised_reference_probe.inline_at_reference_scale` is the
  local-ridge variant for reference-sized glyphs.
- **A second generator arm does NOT fix the stencil failure.** Eight seeds
  across FLUX.2-klein-base-4B and Z-Image-Turbo — different architectures,
  different data, both Apache-2.0 — and not one break. **It is the task, not the
  model:** a general text-to-image model asked for two isolated glyphs in a rare
  typographic treatment. A third arm is unlikely to change it; the untried idea
  is the EDIT path (restyle a neutral `Kg`), which is a different request.
  Z-Image works (48/48 pass the malformed-candidate check, 28.5 s at 8 steps —
  but the owner rejects **23 of the same 48** as starting points, 2026-09-13,
  with one seed rejected 12/12) and is **worse on every picker axis** — between-description spread 1.172 against klein's 2.514, so it
  separates the twelve styles less than half as well, and 11/12 of its
  descriptions are narrow against klein's 8/12.
  `research/2026-08-25-the-second-arm-fails-the-same-way.md`
- **GLM-Image does not run here, so the ~36 min/image figure below is
  UNRE-MEASURED, not confirmed.** `Intel/GLM-Image-int4-AutoRound` (13 GB, on
  disk) is unloadable — diffusers 0.38 has no `auto-round` quantizer and
  installing the package does not register one. The bf16 checkout with quanto
  int8 **segfaults (exit 139)** after loading. Do not quote a GLM speed.
- **Successor bases**: FLUX 3 has no open weights; GLM-Image is ~36 min/image
  and edits rather than restyles; Qwen-Image-Edit-2511 does not fit 24 GB **at BF16 (45 GB) -- but INT4 is 11-16 GB and does fit, and it is Apache-2.0. Corrected 2026-08-23; it is now the leading reference-generator candidate, see research/2026-08-23-restyle-not-generate-the-reference.md**;
  Z-Image-Turbo has no image-conditioning path **-- NO LONGER TRUE. As of Aug 2026 both Z-Image and Z-Image-Turbo ship ZImageImg2ImgPipeline plus ControlNet Union 2.1. 6B, Apache-2.0, 6 GB GGUF, 3.4s at 8 steps on a 4090. Track reopened 2026-08-23; see research/2026-08-23-the-permissive-local-field-opened-up.md**

## Runners are parameterised — use the env vars, don't fork the script

`runners/run_glyph_4b_r32.sh` takes `RANK OUT EVAL_OUT LOG DATASET STEPS MARKER
EXTRA_TRAIN_ARGS NEED_MB`. Two traps, both hit for real:

- **`STEPS` must scale with corpus size.** 5000 steps over 925 fonts is 5.41
  steps/font. Running a 1,113-font corpus at the same 5000 silently cuts that
  to 4.49 (−17%) — the same per-font-budget mechanism that sank V4.
- **Launch detached with the env set in the same PowerShell call**, e.g.
  `$env:RANK='64'; Start-Process bash -ArgumentList '-lc','./runners/run_x.sh'`.
  `Start-Process -ArgumentList` joins its array with spaces, so passing
  `'-lc','VAR=x ./runners/run.sh'` makes bash take only `VAR=x` as the command and
  exit 0 with no log. Always verify the log exists before reporting a run
  as started.
- **Name Git's bash by full path in `Start-Process`.** From PowerShell 7
  here, bare `bash` resolves to `C:\Windows\System32\bash.exe` (WSL), which
  starts nothing and reports nothing (2026-09-13: no log, no process, no
  error). Use `Start-Process "C:\Program Files\Git\bin\bash.exe"
  -ArgumentList '-lc','<script>'`, then check the log and the process.

## Two repositories — the PRIVATE one is the working one

Since 2026-09-11 (`docs/public-release.md`): `sushiHex/digital-rain-private`
(this clone, `repos/fonts`) is the **working repository** — issues, pull
requests, CI and every day-to-day change. `sushiHex/digital-rain` is a
**fresh** history built from it by `misc/export_public.py` and is a
**showcase**: it receives an export when there is real progress to show, not
on every change. Rules that are easy to break by habit:

- **Work by pull request against an issue, in private.** Open work is
  tracked as GitHub Issues on `digital-rain-private`; a branch closes an
  issue through a PR. Do not accumulate work in local branches with no
  issue.
- **Export deliberately, not routinely.** A finding written up, an
  instrument validated, a figure made — that earns an export. The public
  history must stay export-only; the exporter refuses a destination holding
  a commit it did not write. An outside PR on the public repository is
  re-applied on a private branch (attribution in the commit, CLA line on
  file), never merged in public.
- **Private CI is deliberately light** (Actions minutes are the owner's):
  tests run on pull requests only, on Python 3.12 only, and a docs-only PR
  runs a thirty-second subset without installing torch; the audit runs on
  every event. A push to private `main` is NOT tested — run `python -m
  pytest` locally first. The public repository runs the full matrix.
- **Refresh the backup when a result lands.** `backup/` in the private
  repository holds the data that cannot be re-derived
  (`misc/backup_private.py`, `backup/README.md`). A new run, probe output or
  adapter worth keeping goes in with `python misc/backup_private.py make`
  (add an item first if it is a new directory), then `verify`, then commit
  `backup/`; CI re-verifies it whenever `backup/**` changes.
- **What is withheld is stated, not hidden**: `misc/export_public.py --list`.
  Session captures, the March 2026 business research, `docs/archive/`,
  `docs/superpowers/`, `docs/PUSH-PREP.md` — and, since 2026-09-11, **the
  product recipe**: `app.py`, `analysis/generate_candidate_references.py`,
  the constructed-reference code and its probes, the picker analyses, and
  the fifteen late-August notes that spell out which reference generators
  were tried, at what speed and licence, and how the picker behaves. The
  RESULTS of all of that stay public (README narrative, figures, the
  loop-closes and stencil notes, every instrument); the code and the
  how-to do not. A rule that matches nothing makes the script refuse — a
  dead guard is a bug, the same shape as the glob mismatches above.
- **This file still describes the recipe**, because it is the working brief
  for the private archive too. A public reader gets the ideas in prose and
  the instruments in code; the implementation is the part kept back.
- **Four gates before any visibility change**, every time: the listing read,
  the sanitizer passing *on the export* (it has now missed a leak once —
  JSON-escaped paths — and caught one once), the test suite green *in the
  export*, and the export's author emails checked.
- **Pre-registration SHAs cited in notes before the cutover resolve in the
  private archive**, not in the public repository. From the cutover on,
  registrations are committed in public first.
- `research/sessions/` is gitignored; the three captures already in the
  archive stay there.

## Conventions

- Findings go in `research/YYYY-MM-DD-slug.md`; architecture and specs in
  `docs/`. No loose `.md` in the repo root except `README.md`, `AGENTS.md`
  (a pointer to this file for non-Claude agents) and this file. Community
  files (`CONTRIBUTING`, `SECURITY`, `CODE_OF_CONDUCT`) live in `.github/`,
  where GitHub also finds them.
- `research/`, `docs/superpowers/plans/`, `docs/superpowers/specs/` and
  `docs/archive/` (the last two: private archive only) are **dated records**.
  Don't rewrite them to match new findings — add a new dated document, or a
  clearly-marked superseding section.
- Negative results are recorded, not deleted. The README has a section for them.
