# Training-run variance, measured — and it swallows the project's record

> **SUPERSEDED IN PART, 2026-08-13** by
> [`2026-08-13-the-claim-ledger-corrected.md`](2026-08-13-the-claim-ledger-corrected.md).
> The variance MEASUREMENT below stands. The effect table does not: it scored
> each claim against only the one metric it was first reported on, divided a
> dinov2 effect by char_acc's SD, and carried two sign errors. **"Nothing
> reaches 2 SE" is retracted** — scored on every metric, six effects clear it,
> and five of the six are regressions.

2026-08-13. Three runs, config identical except `--seed` (42/43/44), on the
838-font licence-clean corpus at 4530 steps. ~24 GPU-hours. The first time this
project has had an error bar on a checkpoint-vs-checkpoint comparison.

`analysis/training_variance.py`, `research/training_variance_*.json`.

---

## The measurement

char_acc run means: **0.4914 / 0.6070 / 0.5869**

| metric | run-mean SD | 95% CI on that SD (2 df) | largest observed gap | gate fires on identical configs |
|---|---|---|---|---|
| **char_acc** | 0.0618 | [0.0322, 0.3884] | 0.1157 | 2/3 |
| **dinov2** | 0.0228 | [0.0119, 0.1435] | 0.0439 | **3/3** |
| racc | 0.0080 | [0.0041, 0.0500] | 0.0151 | 1/3 |
| composite | 0.0035 | [0.0018, 0.0222] | 0.0070 | 0/3 |
| lpips | 0.0027 | [0.0014, 0.0168] | 0.0049 | 1/3 |

**Training noise is metric-dependent by ~20x.** The two metrics this project
chased hardest, char_acc and dinov2, are the two least stable. The composite is
an order of magnitude steadier.

Every SD here rests on 2 degrees of freedom and carries a **12x-wide** CI. Treat
the numbers below as orders of magnitude, not test statistics.

---

## Every headline claim, against its own metric's noise

| claim | metric | effect | SE | ×SE | ×largest observed gap |
|---|---|---|---|---|---|
| 4B→9B multiseed | dinov2 | +0.0440 | 0.0322 | **1.36** | **1.00** |
| licence filter (corrected) | char_acc | −0.0765 | 0.0714 | 1.07 | 0.66 |
| 4B→9B multiseed | char_acc | +0.0731 | 0.0874 | 0.84 | 0.63 |
| oversampling | composite | +0.0030 | 0.0049 | 0.61 | 0.43 |
| rank 64 | composite | +0.0029 | 0.0049 | 0.59 | 0.41 |
| LR-horizon fix | char_acc | +0.0277 | 0.0874 | 0.32 | 0.24 |

**Nothing reaches 2 SE. Nothing exceeds the gap two identical runs actually
produced, except the 4B→9B dinov2 gap, which exactly equals it (1.00x).**

Read that last row precisely: it does not say the 9B is no better. It says the
9B–4B dinov2 difference is *the same size as the difference between two runs of
one config*, so this evidence cannot separate them.

### The licence filter was inflated by an unlucky seed

The published −0.1330 used clean seed 42, which the three-run set now shows was
the low outlier (0.4914 against 0.6070 and 0.5869). Against the 3-run mean the
cost is **−0.0765**, a 1.7x inflation, at 1.07 SE. **Not established.**

Four confounds were eliminated for that finding across three earlier rounds —
steps, the GPU throttle, a baseline artefact, leakage-removal — and all four
eliminations were correct. The thing that undid it was the one repeatedly named
as unmeasured.

---

## The gate does not survive contact with noise

Run `analysis/compare_runs.py` — unmodified, the project's only comparison
tool — on two runs differing solely in `--seed`:

```
 composite  p=0.0688  r=0.257   no diff
  char_acc  p=0.0000  r=0.731   SIG  (B better)
      racc  p=0.0958  r=0.251   no diff
    dinov2  p=0.0000  r=0.742   SIG  (B better)
     lpips  p=0.7318  r=0.048   no diff
  identity  p=0.0346  r=0.473   SIG  (B better)
```

**Three metrics declare a significant improvement, at large effect sizes, for a
difference that does not exist.** For scale, README's flagship row is
*"DINOv2, 9B better, p<1e-5, r=0.768"*, against r=0.742 here for nothing.

The mechanism is the one already documented for inference seeds: the paired
Wilcoxon pairs by **font** and treats fonts as independent replicates, so any
component that shifts every font together is invisible to it. Here that common
shift is 43–52% of the difference on char_acc.

**The gate answers "is B better on more fonts than A", which is a real question,
and not the question anyone was using it for.** It was never broken; it was
misread. Its output is only interpretable when the two runs are the same
training run — i.e. for inference-seed comparisons — or when the effect is
large relative to run-level noise, which nothing in this repo has been.

---

## Corrections to my own analysis, found by adversarial review

An independent review (5 attack angles, each finding verified separately)
caught three errors in the first draft of this note. They are recorded because
the pattern matters more than the numbers:

1. **I divided a dinov2 effect by char_acc's standard deviation.** Published
   "+0.0440 (0.50 SE)"; metric-matched it is **1.36 SE** — a 2.7x understatement
   of resolvability, on the load-bearing number. This is precisely the error
   CLAUDE.md already logs twice: quoting one metric under another's name. It
   also affected the lever rows, where I quoted "0.03 SE" using char_acc's SD
   for composite effects; correctly matched they are ~0.6 SE, a 20x error.
2. **I called the largest observed gap a "noise floor".** It is the range of a
   3-sample set: it grows with the number of runs (E[range] ≈ 1.69σ at n=3,
   2.06σ at n=4) and guarantees nothing. Now reported as *largest observed
   difference*, descriptive only.
3. **The tool silently produced NaN for `identity`,** which lives in
   `aggregate` but not `per_font` — so it found zero fonts and wrote a
   results file anyway. It now fails loudly. A variance tool that reports NaN
   as an answer is worse than one that refuses.

I also rejected one of the review's recommendations: it proposed quoting the
*lower* 95% bound on σ to argue the dinov2 gap is resolvable at 2.62 SE. That is
a one-sided cherry-pick — the upper bound gives 0.22 SE — and is the same class
of error as the retracted redistribution finding.

---

## What this means for the project

- **No comparison of two training runs in this repository is established.** Not
  the levers, not 4B vs 9B, not the LR fix, not the licence filter. The
  direction of several may well be right; none has been measured.
- **The multi-seed 4B/9B work remains valid as written.** Its pre-registered
  docstring said it "cannot separate architecture from training-run luck". That
  was correct, and this quantifies it.
- **Sample size was never the binding constraint.** More holdout fonts, more
  inference seeds, better bootstraps — none of it touches a run-level shift.
  Only replicate training runs do.
- **A single training run cannot support a claim on char_acc or dinov2 at the
  scale of any effect this project has pursued.** The composite is a stabler
  instrument and should probably be the headline metric.

### The cost of finding out

Two extra training runs, ~24 GPU-hours. Against roughly six months of lever
experiments whose effects sit between 0.24 and 0.61 times the noise of the
instrument that measured them.

### Caveats

σ was measured on one config (4B, rank 32, clean 838-font corpus, 4530 steps).
Applying it to 9B comparisons assumes equal training variance across
architectures, which is unmeasured. It is also an *over*estimate to the extent
it contains the inference-seed component, which was not separated out. And 2 df
is very few: a fourth and fifth run would cost ~24 GPU-h and would halve the CI
width.
