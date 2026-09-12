# The 4B→9B gap is real, and larger than the single-seed A/B showed

2026-08-08. Six inference seeds per checkpoint, matched protocol.
`run_multiseed_4b_vs_9b.sh` → `analysis/multiseed_compare.py`.

This is the run the whole "single-seed cannot resolve this" thread was pointing
at (`research/2026-08-07-single-seed-comparisons-cannot-resolve-the-4b-9b-gap.md`).
The answer is not the one the single-seed A/B suggested.

## Result

Analysis was **pre-registered** — `analysis/multiseed_compare.py` was written and
committed (`14138c5`) before the 9B arm finished generating. Fonts are the unit;
byte-identical holdout fonts collapse to one observation (48 → 44); the Bitcount
pair is excluded; the CI resamples fonts *and* seeds, because the seed main
effect does not average out across fonts.

| metric | 9B − 4B | 95% CI (fonts+seeds) | Wilcoxon | vs single-seed |
|---|---|---|---|---|
| char_acc | **+0.0731** | [+0.0473, +0.0993] | p=2.8e-08 | was +0.0457 |
| dinov2 | **+0.0440** | [+0.0325, +0.0555] | p=1.6e-12 | was +0.0303 |
| candidate composite | +0.0444 | [+0.0262, +0.0627] | p=1.6e-12 | — |
| LPIPS | −0.0007 | [−0.0175, +0.0166] | p=0.72 | ties |

n=44 unique fonts, 6 seeds/model.

**The gap is ~60% bigger than the single-seed estimate, and it excludes zero.**
That is consistent with the seed accounting rather than surprising given it:
seed 42 is *lucky for the 4B* (0.6460 against a 0.6116 six-seed mean), so the
single-seed A/B compared the 9B against the 4B's best face and understated the
difference. The direction of the earlier error was predictable; its size was not.

### Three cautions on that table

1. **The composite here is NOT the README's composite.** `score_candidates`
   computes `dino_cos − λ·lpips − μ·topo_pen`; `eval_checkpoint.compute_composite`
   takes `(lpips, racc, dinov2)`. Different metrics with the same name.
2. **It is not independent evidence.** With the LPIPS delta at ~0, the candidate
   composite is dominated by `dino_cos` — hence the identical p-value to four
   significant figures. Count char_acc and dinov2 as the two findings, not four.
3. **R-ACC and IDENTITY were not scored in this run at all.** `scores.json`
   records only `char, char_acc_match, dino_cos, lpips, score, topo_pen`. The
   standing claim of "no significant difference on R-ACC or IDENTITY" is
   *untouched* by this run — neither confirmed nor refuted.

## The moderator reverses the retracted narrative

Distinctiveness is the frozen, model-independent moderator built for this
purpose (`research/holdout_distinctiveness.json`: holdout GT atlases against the
frozen training-corpus centroid), so it is not the circular
condition-on-the-outcome statistic that
`research/2026-08-07-the-redistribution-signature-was-regression-to-the-mean.md`
retracted.

| metric | ρ (48, with dupes) | ρ (44, collapsed) |
|---|---|---|
| char_acc | −0.518 (p=1.6e-4) | **−0.536** (p=1.8e-4) |
| composite | −0.345 (p=0.016) | −0.359 (p=0.017) |
| dinov2 | −0.230 (p=0.12) | −0.291 (p=0.055) |

Negative ρ, and it survives collapsing duplicates. **The 9B's advantage is
concentrated in ORDINARY fonts, not distinctive ones** — the opposite of the
long-running "the gap is in the distinctive tail" story, which CLAUDE.md had
already downgraded to *not established*. It is now established with the sign
inverted, on char_acc.

Note the rank/linear disagreement on char_acc: ρ is strong and highly
significant while the OLS slope is −0.193 (SE 0.127, p=0.135). A monotone but
non-linear relationship, or leverage from a few extreme-distinctiveness fonts.
Trust the rank statistic; do not quote the slope as an effect size.

## A defect in the pre-registered script, found by running it

The first pass printed **exactly +0.0000, p=nan** for dinov2, LPIPS and the
composite. That reads as a clean null, and a clean null on three of four metrics
is exactly the "the 4B is not a quality compromise" story the project already
believed — which is what made it worth distrusting.

`per_font_per_seed` read every cell as `bool(c[metric])`. Correct for
`char_acc_match`, which genuinely is a per-cell boolean; wrong for everything
else, because `bool(0.87)` is `True`. Every font mean became 1.0, every
difference 0.0, and the Wilcoxon got zero-variance input.

Fixed in `25bc520`; `tests/test_multiseed_compare.py` pins it. The 9B's real
+0.0440 dinov2 advantage had been reading as zero.

**Pre-registration protected the design, not the arithmetic.** Committing the
analysis before the data is a guard against choosing a favourable test; it is no
guard at all against the code being wrong. The tell was not statistical — it was
that a result agreeing with the prior belief arrived suspiciously tidy.

## What this changes

- The 4B **is** a quality compromise on char_acc and dinov2 — resolved, not
  borderline. The case for shipping it rests on the Apache-2.0 licence and the
  4-step speed win, which are the reasons that actually motivated it. It should
  no longer be defended as quality-neutral.
- Where the 4B loses is on **ordinary typefaces**, which is the worse half of
  the distribution to lose on for a product — distinctive display faces are a
  narrower market than workhorse text faces.
- The estimand is unchanged and still limiting: **two checkpoints, each trained
  with a single training seed.** Six *inference* seeds resolve which checkpoint
  is better on this holdout. They cannot separate architecture from
  training-run luck; that needs independent training seeds.
- Both arms remain oracle-reference evaluations (README Limitations).

## Outstanding

- Re-score both arms with `eval_checkpoint` to get R-ACC, IDENTITY and the
  README composite at 6 seeds. Those three are the remaining single-seed claims.
- The rank/linear disagreement on the char_acc moderator is unexplained.
