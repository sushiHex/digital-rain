# Oversampling distinctive fonts: the redistribution replicates, and beats the 9B on one font (2026-08-02)

> **Both claims in this title were later voided. The note is kept unrewritten as
> the dated record.**
>
> - *"the redistribution replicates"* — the redistribution statistic conditioned
>   each font's delta on the baseline run and is biased by construction; it
>   returns ρ = −0.253 on same-model seed pairs where the true effect is zero.
>   Re-derived unbiased, oversampling's gaps are 0.7× and 0.6× that noise floor.
>   See [the retraction](2026-08-07-the-redistribution-signature-was-regression-to-the-mean.md).
> - *"beats the 9B on one font"* — that font is **Bitcount Grid**.
>   `analysis/check_holdout_integrity.py` later established that
>   `BitcountGridDoubleInk` and `BitcountPropDoubleInk` share a **byte-identical
>   reference image** — the model's only input — while carrying *different*
>   ground-truth atlases (mean |diff| 36.6/255). The model necessarily emits
>   identical output for both and is scored against two different answers, so it
>   cannot do well on both by construction. No per-font comparison involving
>   either font is interpretable, and this pair was cited as per-font evidence
>   more than once.
>
> At the headline gate this lever showed **no difference on any metric**, and
> against training-run variance its best effect is +0.8×SE on LPIPS.

**Question.** `research/2026-07-31-rank64-redistributes-capacity.md` found that
rank 64 moved quality toward hard fonts without being asked (Spearman ρ=−0.68
on dinov2), and that only ~10% of the 925-font corpus is structurally
distinctive. Does applying that pressure *deliberately* — oversampling
distinctive fonts — push further in the same direction?

`run_glyph_4b_r32.sh` with `--distinctiveness research/font_distinctiveness.json
--distinct-alpha 0.5`, rank 32, single variable against
`training_glyph_4b_r32_5000`. Sampler logged: weights 0.46–3.37, **top-decile
share of draws 19.9% against 10.0% uniform**. 11.6 h, best loss 0.0276.

Training loss ran consistently *higher* than the uniform run (+0.009 → +0.005
across bands). That is expected, not a regression: the sampler changed the
training distribution, so the loss is computed on a harder mixture. A weighted
run matching uniform loss would mean the sampler wasn't doing anything.

## The population answer: no, again

Paired Wilcoxon, n=50 — **no difference on any metric**; aggregate is slightly
negative (char_acc −0.0068, dinov2 −0.0079).

| metric | uniform | weighted | p | r |
|---|---|---|---|---|
| composite | 0.8158 | 0.8131 | 0.4840 | 0.099 |
| char_acc | 0.6460 | 0.6391 | 0.5647 | 0.086 |
| dinov2 | 0.8485 | 0.8406 | 0.0978 | 0.234 |
| identity | 0.9893 | 0.9880 | 0.8552 | 0.067 |

## The structural answer: the redistribution replicates

Same test as rank 64 — correlate each font's delta against its uniform-run
baseline:

| metric | mean | Spearman ρ | p | harder half | easier half |
|---|---|---|---|---|---|
| char_acc | −0.0068 | **−0.468** | 0.0006 | **+0.0221** | −0.0357 |
| dinov2 | −0.0079 | **−0.456** | 0.0009 | **+0.0077** | −0.0234 |

(rank 64 for comparison: ρ=−0.491 / −0.683.)

So this is a **second, independent confirmation** that the 4B's capacity
allocation is malleable and that pressure moves it toward hard fonts. It is
still redistribution, not creation — and this run pays *more* for it on the
easy half (−0.0357 vs rank 64's −0.0289).

## Per-font: this is where it matters

char_acc on the faces that motivated the whole investigation:

| font | uniform | rank 64 | **weighted** | 9B |
|---|---|---|---|---|
| Fascinate Inline | 0.191 | 0.255 | **0.287** | 0.489 |
| **Bitcount Grid (dot-grid)** | 0.074 | 0.074 | **0.191** | *0.138* |
| Dangrek | 0.511 | 0.585 | **0.649** | 0.691 |
| Bitcount Prop (dot-grid) | 0.181 | 0.213 | 0.181 | 0.266 |
| Rubik Distressed | 0.234 | 0.191 | 0.234 | 0.266 |
| Wonky (control) | 0.872 | 0.798 | 0.830 | 0.840 |

**On Bitcount Grid the weighted 4B beats the 9B outright** (0.191 vs 0.138) —
the first time anything on the Apache-2.0 path has exceeded the non-commercial
model on any font. Fascinate Inline closed 39% of its gap; Dangrek is within
0.04.

Not uniform: Bitcount Prop and Rubik Distressed are unmoved, and the control
pays 0.042.

## What this means

For a font product whose value is in distinctive typefaces, this is the trade
worth making, and it is now demonstrated twice by independent mechanisms. But
the honest framing is unchanged from rank 64: **the 50-font holdout is mostly
ordinary fonts, so a change that helps distinctive ones scores as "no
difference" or slightly negative.** The benchmark is measuring a population the
product does not care equally about.

Two things follow:

1. **The holdout is now the limiting instrument.** Any further work on this axis
   should be evaluated on a distinctiveness-stratified split — reporting the
   hard-half and easy-half separately as a matter of course — or the gate will
   keep returning "no diff" for changes that matter.
2. **rank 64 and oversampling are separate mechanisms** and were tested
   independently. Combining them is untested and is the obvious next
   experiment: ρ is similar for both, and their per-font gains do not fully
   overlap (rank 64 helped Bitcount Prop, oversampling helped Bitcount Grid).

**Untested:** α=1.0 (30.7% top-decile share) rather than 0.5; rank 64 +
oversampling combined.

## Artifacts

- `eval_runs/glyph_4b_distinct_5000/`
- `training_glyph_4b_distinct_5000/{train_config,conditioning}.json`, `metrics.csv`
- `research/2026-08-02-wilcoxon_uniform_vs_weighted.json`
