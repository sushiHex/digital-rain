# Single-seed comparisons cannot resolve the 4B-9B gap (2026-08-07)

Companion to `2026-08-07-the-redistribution-signature-was-regression-to-the-mean.md`.
That note corrected the *stratified* statistic. This one corrects the
**aggregate** result, which the earlier note said "survives untouched". It does
not.

## The measurement

`analysis/seed_variance.py`, on the four 4B seeds in `bestofn_4b/scores.json`
where every difference is noise by construction. Two-way (font x seed)
decomposition of per-font char_acc:

| component | SD | behaviour |
|---|---|---|
| **seed MAIN effect** | **0.0248** | shifts every font together; does **not** average out |
| font x seed residual | 0.0534 | averages out as 1/sqrt(50) |
| a run's holdout mean | 0.0259 | **91% of it the seed main effect** |

Seed means: 0.6304, 0.5770, 0.5943, 0.6270 — one model, one checkpoint, one
holdout.

## What that does to the headline

A single-seed A/B carries `SE = sqrt(2 x 0.0259^2) = 0.0366` on the difference.

| seeds/model | SE(diff) | observed gap / SE | min detectable @80% |
|---|---|---|---|
| **1 (what we have)** | **0.0366** | **1.2** | 0.1025 |
| 2 | 0.0259 | 1.8 | 0.0725 |
| 4 | 0.0183 | 2.5 | 0.0513 |
| 6 | 0.0149 | 3.1 | 0.0419 |
| 8 | 0.0129 | 3.5 | 0.0362 |

**The observed 4B->9B char_acc gap of 0.0457 is 1.2 standard errors from zero.**

`compare_runs.py` reports p=0.0001, r=0.563 on that same comparison. The two are
not in conflict — they answer different questions. The paired Wilcoxon pairs by
**font** and treats fonts as independent replicates, so it measures "is B better
on more fonts than A". With one seed per model, a seed effect that lifts all 50
fonts together is *perfectly confounded* with the model effect, and no
font-paired test can see it. The Wilcoxon is not wrong; it is being read as
evidence for a claim it does not address.

This applies to **every single-seed A/B in this project**, including all five
generator levers.

## Independent review, verified

A cross-review (Codex gpt-5.6-sol, repo read-only) reached the same seed-count
conclusion from the same data and added four corrections, each checked here:

1. **`research/font_distinctiveness.json` cannot define holdout difficulty.**
   It scores the **925 training fonts**; exact overlap with the 50 holdout
   fonts is **zero** (verified). Its `--validate` path computes a centroid from
   the holdout itself and discards the scores. A non-circular difficulty
   measure has to be built: holdout GT atlases scored against the **frozen
   training-corpus centroid**.
2. **The 9B generates at ~119 s/atlas, not the ~65 s/atlas of the 4B.**
   Verified from the run logs: 9B `holdout_bestofn.log` 03:17:39 -> 09:55:42
   for 200 atlases; 4B `bestofn_4b.log` 02:13:30 -> 05:49:58. Any 9B seed budget
   costs roughly double what the 4B timing implies.
3. **The midpoint fix is unbiased only under equal variance.**
   `Cov((A+B)/2, B-A) = (Var(B) - Var(A))/2` — confirmed algebraically. The null
   test in `tests/test_redistribution_null.py` uses same-model pairs, which have
   equal variance by construction, so it validates the fix only for that case.
   Whether the 4B and 9B have equal sampling variance is unknown and is one of
   the things the multi-seed run measures.
4. **Both checkpoints are single training-seed-42 instances.** Inference-seed
   replication establishes a difference between *these two checkpoints*, not
   between the 4B and 9B *architectures*. Claiming the latter needs independent
   training runs; the claim should be narrowed instead.

## Rejected from the same review, with reasons

- **"Use a beta-binomial on successes out of 94 rather than a Gaussian on
  proportions."** Correct in principle. Not adopted now: the project's entire
  comparison history is per-font means, and switching the outcome model at the
  same moment as adding seeds would confound the methodological change with the
  measurement. Worth a follow-up on the finished data.
- **"The holdout has become a development set; a confirmatory claim needs a
  fresh frozen font set."** True and important, but changing the holdout breaks
  comparability with every prior run — the same reason `CLAUDE.md` already
  gives for not fixing the superfamily overlap. Recorded as a limitation.
- **"Drop the median split entirely."** Adopted for the primary test
  (continuous moderator), but the split is kept as a secondary reported
  contrast because every prior writeup is expressed in those terms.

## Consequence

The next experiment is **50 fonts x 6 inference seeds per model** (86% power on
the main effect, 90% on the interaction, ~11.7 GPU-hours reusing the four
existing 4B seeds), with difficulty entering as a frozen continuous moderator.
Not another training lever: at 1.2 SE, the target itself is not yet established.
