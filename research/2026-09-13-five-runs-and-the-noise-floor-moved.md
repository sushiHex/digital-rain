# Five runs, and the noise floor moved

2026-09-13. Two more training runs, config identical to the three of
2026-08-13 except `--seed` (45 and 46, joining 42/43/44), on the 838-font
licence-clean corpus at 4530 steps. ~13 GPU-hours each on the shared card,
gated at 12 GB free, nothing evicted. Issue #13. Nothing new was registered:
this is a precision improvement on the measurement in
[`2026-08-13-training-run-variance-measured-at-last.md`](2026-08-13-training-run-variance-measured-at-last.md),
and every claim in the ledger is divided by the number it refines (one claim,
the licence filter, also averages over the runs themselves; see below).

`analysis/training_variance.py` over the five runs;
`research/training_variance_*.json` regenerated; `analysis/claim_ledger.py`
re-run against the five-run σ. The seed-46 eval was scored by hand after a
transformers upgrade in the shared site-packages broke the TrOCR loader
mid-run (PR #36); the fifty atlases were already generated and are the ones
scored. That leaves seeds 42–45 scored under transformers 4 and seed 46
under transformers 5 through `eval_checkpoint.load_trocr`, which is two
scoring stacks, not one — so seed 45's fifty atlases were re-scored under
the new stack into a scratch directory (`--skip-generate`, same GT cache).
**Every per-font value of char_acc, DINOv2, LPIPS, R-ACC and the composite
is identical on all 50 fonts**, TrOCR's 4,700 decodings included; the only
difference the new loader reports is an encoder pooler it initialises and
generation never uses. The five runs are comparable.

---

## The measurement

Run means, seeds 42 / 43 / 44 / 45 / 46:

| metric | 42 | 43 | 44 | 45 | 46 |
|---|---|---|---|---|---|
| char_acc | 0.4914 | 0.6070 | 0.5869 | 0.6031 | **0.6558** |
| dinov2 | 0.7775 | 0.8104 | 0.8213 | 0.8178 | **0.8792** |
| racc | 0.7298 | 0.7418 | 0.7267 | 0.7352 | 0.7309 |
| composite | 0.8030 | 0.8100 | 0.8060 | 0.8082 | 0.8104 |
| lpips (lower is better) | 0.1381 | 0.1423 | 0.1430 | 0.1435 | **0.1545** |

| metric | run-mean SD, 3 runs | **5 runs** | 95% CI on σ (4 df) | largest observed gap | gate fires on identical pairs |
|---|---|---|---|---|---|
| char_acc | 0.0618 | **0.0603** | [0.036, 0.173] | 0.1645 | 7/10 |
| dinov2 | 0.0228 | **0.0368** | [0.022, 0.106] | 0.1017 | **8/10** |
| racc | 0.0080 | **0.0058** | [0.003, 0.017] | 0.0151 | 1/10 |
| composite | 0.0035 | **0.0031** | [0.002, 0.009] | 0.0074 | 1/10 |
| lpips | 0.0027 | **0.0061** | [0.004, 0.018] | 0.0164 | 3/10 |

The interval on σ is **4.8× wide** now, against 12.1× on 2 df. That was the
point of the exercise and it happened. The point estimates are another
matter: three fell a little and two rose a lot — DINOv2 by 61%, LPIPS by
126% — and the reason is one run.

**Training noise is still metric-dependent by ~20×** (char_acc 0.0603
against composite 0.0031), and the two metrics chased hardest here are still
the two least stable. The comparison tool still calls most pairs of
*identical* configs a significant char_acc or DINOv2 difference: 7 and 8 of
the ten pairs.

For four of the five metrics the two estimates of σ sit inside each other's
interval. LPIPS is the exception: the three-run 0.0027 falls below the
five-run interval's floor of 0.0037, so on that metric the five runs do say
the first estimate was too small, not merely uncertain. For the rest, nothing
here says the three-run numbers were wrong; it says 2 df was too few to know
how wrong they could be, and the answer is "by a factor of two on the metrics
that drew a lucky triple".

---

## Seed 46

Seed 46 has the **best** char_acc and DINOv2 of the five and the **worst**
LPIPS, and `analysis/measure_ink.py` says why:

| run | ink (bright fraction) | vs GT 0.0652 |
|---|---|---|
| seed 42 | 0.0572 | −12.2% |
| seed 43 | 0.0666 | +2.3% |
| seed 44 | 0.0504 | −22.7% |
| seed 45 | 0.0616 | −5.5% |
| **seed 46** | **0.0483** | **−25.8%** |

That is the stroke-weight signature the ink check was built to catch — LPIPS
up, letters still right — and here it is on a run whose only difference from
the others is `--seed`. **Stroke weight is itself a seed lottery.** Three of
the five identical-config runs trip the script's 10% flag. The five-run SD
of ink is 0.0076, 11.7% of ground truth, on the same 4 df.

Read against that, the two runs the ink check condemned are harder to call
than they were. The corpus-expansion run (1,113 fonts, 6,016 steps) drew
0.0440, −32.5% of GT; the rank64 + oversampling run (925 fonts with the
distinctive tail oversampled, 5,000 steps) drew 0.0780, +19.7%. Measured from
the five clean runs' mean they sit 1.7 SD below and 2.8 SD above it — but
that mean is itself 13% under GT, so measured from GT the same two sit 2.8 SD
below and 1.7 SD above, and the asymmetry swaps. Five runs of a third corpus
(838 fonts) do not settle which centre is the right one, so the reading that
survives is the modest one: **stroke weight moves by seed alone with an SD of
about 12% of GT, and an ink shift of two or three of those needs a replicate
before it is called a training failure.** The mechanisms recorded for those
two runs — near-blank selection, a heavier distinctive tail — stand as
mechanisms; the size of their effect has no error bar yet.

The coincidence that the thinnest strokes score best on char_acc and DINOv2
is noted and not interpreted. One run is one run.

---

## The claim ledger, re-scored

Every effect divided by its own metric's five-run σ
(`analysis/claim_ledger.py`, `research/claim_ledger.json`). The six that
cleared 2 xSE on three runs:

| effect | metric | xSE, 3 runs | **xSE, 5 runs** | clears 2? |
|---|---|---|---|---|
| rank64 + oversampling | composite | −7.8 | **−8.9** | yes |
| rank64 + oversampling | lpips | −13.5 | **−6.0** | yes |
| rank64 + oversampling | racc | −2.0 | **−2.8** | yes |
| licence filter (838) | composite | −2.2 | **−2.2** | yes |
| 4B → 9B | lpips | −4.3 | **−1.9** | **no** |
| LR-horizon fix | lpips | −2.0 | **−0.9** | **no** |

**Four effects clear 2 xSE, not six. All four are still regressions.** The
LPIPS σ more than doubled, so every LPIPS xSE shrank by 2.3×; the composite
σ fell slightly, so rank64 + oversampling firmed up on the composite.
Stacking the two "improvements" remains the largest real effect in the
project, now led by its composite row rather than its LPIPS row, and the two
that dropped out were the two nearest the line.

The licence-filter row is the one whose *arm* moved as well as its
denominator. Its clean side is the mean of the replicate runs — the same runs
σ is estimated from — and it now averages all five rather than the first
three (`CLEAN` in `analysis/claim_ledger.py`, SE = σ√(1 + 1/5)). Seeds 45 and
46 score above the three-run mean, so the composite effect shrank from
−0.0088 to −0.0076 while its SE fell from 0.0040 to 0.0034, and the two
movements cancel: −2.17 became −2.23, the same −2.2 in the table. Left on the
three-run arm against the five-run σ it would have read −2.5, which is a
number about an arm that ignores two of the runs its own denominator counts,
and is why the arm had to move with the σ.

The 4B → 9B LPIPS row deserves a sentence, because CLAUDE.md carried it as
"the 9B is WORSE" for a month. Its single-run delta has not moved: on that
pair of checkpoints the 9B's LPIPS is 0.0164 higher than the 4B's. What moved
is the denominator — a σ of 0.0027 from three runs whose LPIPS happened to
land within 0.005 of each other became 0.0061 — so −4.3 became −1.9. The
six-inference-seed comparison of 2026-08-08 measured something else, the
same two checkpoints under inference-seed noise, and put the raw gap at
−0.0007 with an interval [−0.0175, +0.0166]; the single-run +0.0164 sits at
the top edge of it. The two point estimates differ in sign, and neither
measurement now excludes zero. That is the whole claim: on LPIPS, nothing
separates the 4B from the 9B. The LR-horizon fix's LPIPS regression goes the
same way, to −0.9.

**"xSE ranks, it does not establish"** was written on the ledger when σ had
2 df. Five runs made it literal: two of six verdicts flipped from a
precision improvement alone, with no new evidence about the effects
themselves. A threshold of 2.0 on an interval that is still 4.8× wide
should be read as the ledger's docstring says, and nowhere else.

---

## What the five runs decide

The shipping checkpoint (#11). The rule was stated before seeds 45 and 46
finished: the clean-corpus run with the **median composite** ships. Composites
0.8030 / 0.8100 / 0.8060 / 0.8082 / 0.8104 — the median is **seed 45**,
`training_glyph_4b_r32_clean_s45`, with the five-run σ beside every number it
is quoted with. Not the best seed; the one a replicate is most likely to
reproduce.

The registered comparisons that follow (#6, #7) inherit this σ as their error
bar, and the one lesson that generalises: **a single-run A/B on char_acc or
DINOv2 cannot resolve anything smaller than ~0.17 and ~0.10** (2 xSE, with
SE = σ√2 for two single runs), which is larger than every lever ever tried
here.

---

## What it does not decide

- σ is measured on **one** config — 4B, rank 32, clean corpus, 4530 steps.
  The 9B side has no replicate training runs, and nothing here says its
  noise is the same.
- 4 df is still wide. The upper bound on char_acc's σ is 0.173; on
  DINOv2's, 0.106. Two more runs would take the interval to ~3.4×; the
  return is diminishing and the card is shared.
- The largest observed gap grew with n, as it must (char_acc 0.1157 →
  0.1645). It remains a range, not a threshold.

Records: `research/training_variance_{char_acc,dinov2,racc,composite,lpips}.json`,
`research/claim_ledger.json` — regenerated in place, as the scripts that write
them intend; the three-run versions the 2026-08-13 notes tabulate are
preserved as `research/2026-08-13-training_variance_*.json` and
`research/2026-08-13-claim_ledger.json`. Runs
`eval_runs/glyph_4b_r32_clean{,_s43,_s44,_s45,_s46}` and their training
records are in the private `backup/`.
