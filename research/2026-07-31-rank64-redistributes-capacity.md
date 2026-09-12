# Rank 64 doesn't add capacity — it reallocates it toward hard fonts (2026-07-31)

> **The title's claim was retracted on 2026-08-07. This note is kept unrewritten
> as the dated record.**
>
> "Reallocates toward hard fonts" rests on the redistribution statistic, which
> conditioned each font's delta on the **baseline** run and is biased by
> construction: `Cov(a, b−a) = Cov(a, b) − Var(a)`. Measured on pairs of
> different seeds of the *same* model, where the true effect is exactly zero,
> the biased form returns ρ = −0.253 and a spurious hard-vs-easy gap of 0.038.
> Re-derived against the unbiased midpoint form, rank 64's char_acc gap is 1.5×
> that noise floor and its dinov2 gap 0.7× — under ~1× is not distinguishable
> from seed noise. See
> [the retraction](2026-08-07-the-redistribution-signature-was-regression-to-the-mean.md);
> `tests/test_redistribution_null.py` pins the biased form as biased.
>
> **What survives is this note's own first section**, headed *"The population
> answer: no"*. That measurement was correct and still stands: rank 64 shows no
> difference on any metric at the headline gate. Against training-run variance
> measured later, its best effect is +0.5×SE on composite.

**Question.** The throughput probe found rank 64 costs +1% time and no extra
memory on the 4B. Does doubling adapter capacity close the style gap against
the 9B, which is concentrated in structurally distinctive typefaces?

`run_glyph_4b_r32.sh` parameterised via `RANK=64`; single variable against
`training_glyph_4b_r32_5000`. 11.6 h, best loss 0.0270 (rank 32: 0.0264).

## The population answer: no

Paired Wilcoxon, n=50, gate p<0.05 ∧ r≥0.3 — **no difference on any metric**:

| metric | rank 32 | rank 64 | p | r | |
|---|---|---|---|---|---|
| composite | 0.8158 | 0.8187 | 0.5335 | 0.088 | no diff |
| char_acc | 0.6460 | 0.6464 | 0.9608 | 0.007 | no diff |
| dinov2 | 0.8485 | 0.8540 | 0.2818 | 0.152 | no diff |
| racc | 0.7360 | 0.7364 | 0.3335 | 0.146 | no diff |
| lpips | 0.1381 | 0.1342 | 0.0645 | 0.261 | no diff |
| identity | 0.9893 | 0.9905 | 0.8209 | 0.065 | no diff |

Training loss agreed in advance: the rank-64 curve was indistinguishable from
rank 32 by 2000 steps and ended marginally higher (0.0414 vs 0.0404 over the
final 1000 steps).

## The structural answer: a significant reallocation

The per-font deltas were not random. Abstract faces gained while the control
*lost*, which suggested redistribution rather than noise. Tested across all 50
fonts by correlating each font's delta against its rank-32 baseline — if
capacity is being moved from easy to hard fonts, the correlation must be
negative:

| metric | mean delta | Spearman ρ | p | harder half | easier half |
|---|---|---|---|---|---|
| char_acc | +0.0004 | **−0.491** | 0.0003 | **+0.0298** | −0.0289 |
| dinov2 | +0.0055 | **−0.683** | <0.0001 | **+0.0301** | −0.0191 |

Strong, monotonic, and significant. **Rank 64 does not add capacity — it moves
it.** The harder half of the holdout gains ~+0.03 on both style axes; the
easier half loses about the same. That is why the aggregate is flat.

Per-font, on the faces that motivated this:

| font | char_acc Δ | dinov2 Δ | gap to 9B remaining (char_acc) |
|---|---|---|---|
| Fascinate Inline | **+0.064** | +0.021 | +0.234 |
| Dangrek | **+0.074** | +0.043 | +0.106 |
| Bitcount Prop (dot-grid) | +0.032 | **+0.045** | +0.053 |
| Bitcount Grid (dot-grid) | 0.000 | **+0.054** | +0.064 |
| Rubik Distressed | −0.043 | −0.009 | +0.074 |
| Wonky (control) | −0.074 | −0.044 | +0.043 |

## Why this matters more than the gate result

For a font product the value is in distinctive typefaces — nobody needs a
generative model to produce another Helvetica. Trading easy-font fidelity for
hard-font fidelity is plausibly the *right* trade for this use case, even
though it registers as "no improvement" on a holdout that is mostly ordinary
fonts. The 50-font holdout's composition is doing a lot of work in that verdict.

**It also converts the data-distribution hypothesis from speculation into a
supported lead.** The earlier reasoning was that abstract faces are a minority
of the 925-font corpus, so they contribute a minority of the gradient and get
underfit. This run shows the model's capacity allocation is *malleable and
responds to where the pressure is* — rank 64 shifted it toward hard fonts
without being asked. Deliberately oversampling distinctive fonts should push
further in the same direction, on purpose rather than as a side effect.

## Verdict

- **Rank 64 is not a general improvement** and should not be adopted as a
  default on the gate's evidence.
- **It is a real improvement on the fonts that matter here** (+0.03 on the
  harder half, ρ=−0.68), at the cost of the easier half, for +1% training time.
- **Adapter capacity was never the binding constraint** — doubling it moved
  quality around rather than creating it. The remaining gap to the 9B is base
  capacity or data distribution, not rank.

Next lever, now evidence-backed rather than speculative: a weighted sampler in
`train_lora_kg.py` that oversamples structurally distinctive fonts. Needs a
distinctiveness score over the training corpus — the DINOv2 spread machinery in
`audit_diversity.py` already does something close, applied to holdout fonts.

## Artifacts

- `eval_runs/glyph_4b_r64_5000/`
- `training_glyph_4b_r64_5000/{train_config,conditioning}.json`, `metrics.csv`
- `research/2026-07-31-wilcoxon_r32_vs_r64.json`
