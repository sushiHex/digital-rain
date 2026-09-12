# Six seeds for the other three metrics (2026-09-12)

**The gap that was.** The matched six-seed run of 2026-08-08 settled the
4B-versus-9B question on char_acc (+0.0731), DINOv2 (+0.0440) and LPIPS (a
tie) — and left R-ACC, IDENTITY and the README composite where they were,
single-seed, because `score_candidates` never recorded the first two and its
`score` is a different composite from `eval_checkpoint.compute_composite`.
Issue #12. The fix is cheap: the twelve candidate sets exist, so re-score
them with `eval_checkpoint` — no generation — and apply the registered
statistic unchanged.

**What was run.** `runners/run_rescore_multiseed.sh` lays each seed's fifty
atlases out as an evaluation run and scores it with `--identity`; twelve
runs, `eval_runs/multiseed_{4b,9b}_s{0..5}`. `analysis/multiseed_rescore.py`
then does exactly what `analysis/multiseed_compare.py` does — per-font means
over seeds, 9B − 4B per font, the two fonts that share a reference image
dropped, byte-identical ground-truth atlases collapsed to one observation,
paired Wilcoxon, and the seed-blocked bootstrap that resamples fonts and
seeds — through the same function, extracted from it rather than rewritten.
The metrics were named in the issue before anything was scored. Record:
`research/multiseed_rescore.json`.

## Result — 9B minus 4B, six inference seeds each, 44 unique fonts

| metric | 4B | 9B | 9B − 4B | 95% CI, fonts + seeds | Wilcoxon p |
|---|---|---|---|---|---|
| R-ACC | 0.7369 | 0.7454 | +0.0084 | [−0.0063, +0.0233] includes zero | 0.13 |
| IDENTITY | 0.9853 | 0.9909 | **+0.0056** | **[+0.0007, +0.0107]** | 0.013 |
| composite | 0.8085 | 0.8184 | +0.0099 | [−0.0033, +0.0227] includes zero | 0.0016 |
| LPIPS | 0.1479 | 0.1472 | −0.0007 | [−0.0175, +0.0166] | 0.72 |
| DINOv2 | 0.8304 | 0.8744 | +0.0440 | [+0.0325, +0.0555] | 1.6e-12 |

The arm means are over the same 44 collapsed observations as the difference,
so the columns subtract. The last two rows reproduce the 2026-08-08 intervals
to the fourth decimal, which is the check that the reader and the statistic
are the ones that were registered.

## Reading

- **IDENTITY resolves, barely, in the 9B's favour**: +0.0056 with a lower
  bound of +0.0007. Both models sit above 0.985 on the lenient, GT-gated
  definition; this is about 25 cells of 4,400, real and negligible in the
  same breath, exactly the shape the baseline-versus-glyph comparison had.
- **R-ACC and the README composite do not resolve** at six seeds. The
  composite's font-paired Wilcoxon says p = 0.0016 while its seed-blocked
  interval includes zero: the two answers to two different questions that
  `CLAUDE.md` warns about under `compare_runs.py`. The Wilcoxon asks whether
  the 9B is better on more fonts; the interval asks whether the difference
  survives the seed main effect, and on this metric it does not. Quote the
  interval.
- So the 4B-versus-9B ledger now reads: DINOv2 and char_acc resolved for the
  9B, IDENTITY resolved by a hair, LPIPS a tie, R-ACC and the composite
  unresolved. The README's earlier "no significant difference on composite,
  R-ACC, LPIPS or IDENTITY" was single-seed and is, three of four times,
  what six seeds also say.

**Estimand, once more.** Two checkpoints, one training seed each. Inference
seeds cannot separate architecture from training luck; the training-variance
runs (issue #13) are what would.
