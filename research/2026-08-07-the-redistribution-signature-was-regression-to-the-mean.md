# The redistribution signature was largely regression to the mean (2026-08-07)

**How this surfaced.** A cross-review by an independent model (Codex,
gpt-5.6-sol, repo mounted read-only) was asked to attack the plan for the next
experiment. It did not attack the plan; it attacked the statistic every recent
conclusion rests on.

## The bias

`analysis/compare_runs.redistribution()` correlated each font's delta `b - a`
against its **baseline** `a`. Because `a` appears on both sides:

    Cov(a, b - a) = Cov(a, b) - Var(a)

Ordinary measurement noise therefore drives the correlation negative *even when
the true effect is completely unrelated to difficulty*. Splitting "hard vs easy"
on the same noisy baseline compounds it: a font lands in the hard half partly
because its baseline drew a negative error, and then regresses upward.

## Measured, not argued

The project has four seeds of the **same** 4B model on the same holdout
(`bestofn_4b/scores.json`), so the true effect between any two is **exactly
zero**. Running the statistic on all 12 ordered pairs:

| conditioning | mean rho | mean abs(hard - easy) gap |
|---|---|---|
| **baseline** (the old form) | **-0.253** | **0.038** |
| **midpoint (a+b)/2** (the fix) | -0.000 | 0.013 |

One same-model pair reached rho=-0.296, p=0.037 — a "significant
redistribution" between a model and itself.

## What it invalidated

Re-derived with midpoint conditioning, against the 0.038 noise floor:

| lever | char_acc gap | xnull | dinov2 gap | xnull |
|---|---|---|---|---|
| rank 64 | +0.0587 | 1.5x | +0.0280 | 0.7x |
| distinctiveness oversampling | +0.0281 | 0.7x | +0.0238 | 0.6x |
| corpus expansion | +0.0391 | 1.0x | +0.0259 | 0.7x |
| rank 64 + oversampling | +0.1374 | 3.6x | +0.0548 | 1.4x |
| **9B vs 4B (the target itself)** | **+0.0370** | **1.0x** | **+0.0397** | **1.0x** |

Three consequences, in order of how much they cost:

1. **"Every lever redistributes" is mostly the artefact.** rho values of -0.40
   to -0.85 were quoted as five independent confirmations of a capacity
   ceiling. They share one noisy baseline and a statistic biased toward exactly
   that reading. Unbiased, three of the five sit at or below the noise floor.
2. **The headline reframing was wrong.** "On ordinary typefaces the two models
   are indistinguishable — dinov2 advantage +0.0007, nothing" appeared in
   `README.md`, `CLAUDE.md` and `docs/quality-roadmap-v3.md`. Unbiased, the
   easy-half advantage is +0.0105 (dinov2) and +0.0272 (char_acc), and the
   hard-vs-easy gap is at 1.0x the floor. **The gap being confined to the
   distinctive tail is not established.**
3. **"rank 64 closes ~30% of the hard-half gap"** — the basis for recommending
   its adoption — is computed from the biased statistic on both numerator and
   target. rank 64 remains the most plausible lever (1.5x on char_acc, and it
   costs +1% training time with composite slightly up), but the 30% figure
   should not be repeated.

## What still stands

- The aggregate paired-Wilcoxon results are untouched: the 4B trails the 9B by
  0.0457 char_acc (r=0.563) and 0.0303 dinov2 (r=0.556), and shows no
  significant difference on composite, R-ACC, LPIPS or IDENTITY. That test
  never conditioned on the baseline.
- The two-axis rule, the conditioning guard, the ink-coverage check and the
  loader fix are all independent of this.

## The fix

`redistribution()` now conditions on the midpoint and reports `gap` plus
`gap_vs_null` (the `xnull` column). `tests/test_redistribution_null.py` asserts
the statistic reads ~0 under synthetic nulls, that it still detects a genuine
easy-to-hard transfer, and — deliberately — pins the OLD form as visibly biased,
so the reason for the change stays legible.

## What the review got right that I have NOT adopted, and why

- **"Aggregate CIs resample 4,700 cells as independent"** (`eval_checkpoint.py`
  bootstrap). Correct, and pre-existing; `compare_runs.py` exists precisely
  because of it and is what every headline uses. Worth fixing, not urgent.
- **`paired_wilcoxon` takes direction from the unweighted mean of nonzero
  diffs while significance comes from signed ranks.** Real, and it can disagree
  under skew. But the field exists because the median delta is 0.0 on
  near-ceiling metrics; the fix is to rank-weight it, not to revert.
- **R-ACC cache key omits holdout identity.** Real latent hazard, no evidence
  it has fired.
- **"compare_runs silently intersects font sets."** True; it warns. Should hard
  fail on n != 50.

## Consequence for the next experiment

The reviewer's ordering is adopted: **establish the target before chasing it.**
A matched multi-seed 4B-vs-9B comparison comes first. Chasing a 1.0x-of-noise
hard-half gap with a 13-hour training run would have produced another confident
but uninterpretable null.
