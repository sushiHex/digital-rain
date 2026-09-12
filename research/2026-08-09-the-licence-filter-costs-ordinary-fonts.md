# Removing the proprietary fonts cost 0.14 char_acc, concentrated in ORDINARY faces

2026-08-09. First training run on the licence-clean corpus
(`training_glyph_4b_r32_clean`, 838 fonts, 4530 steps, LR-horizon fix).

| metric | LR-fixed, 925 fonts | LR-fixed, **clean 838** | delta |
|---|---|---|---|
| char_acc | 0.6183 | **0.4785** | **−0.1398** |
| dinov2 | 0.8388 | **0.7770** | −0.0618 |
| composite | 0.8076 | 0.7968 | −0.0108 |
| identity | 0.9836 | 0.9793 | −0.0043 |
| LPIPS | 0.1457 | 0.1422 | +0.0035 (better) |

**45 of 50 fonts got worse.** The four that improved are the unscoreable
Bitcount pair and Playwrite handwriting faces.

> ## CORRECTION, 2026-08-10
>
> Two claims below were overstated when first written, and both were checked
> only after the fact. The corrected findings:
>
> **1. The corpus cost is CONFIRMED and slightly larger.** The original
> comparison (lrfix@5000 vs clean@4530) confounded corpus with total steps. I
> dismissed that using training LOSS at matched steps, which was sloppy — loss
> is velocity MSE, char_acc is a DINOv2 nearest-neighbour rate, and equal loss
> does not imply equal char_acc. Both runs kept `checkpoint-4500`, so the
> comparison was made directly:
>
> | | lrfix (925) | clean (838) | delta |
> |---|---|---|---|
> | char_acc @4500 | 0.6134 | 0.4804 | **−0.1330** |
>
> The 470 steps accounted for **0.0068** of the original −0.1398. The step
> argument was badly supported but its conclusion was right. Note the test is
> biased *toward* clean — at step 4500 clean is fully annealed while lrfix
> still has ~3e-06 of LR to spend — so −0.133 is a floor, not a ceiling.
>
> **2. "Concentrated in ORDINARY fonts" is much weaker than stated.** Ordinary
> fonts have higher baseline char_acc, and baseline and distinctiveness are
> entangled at rho = −0.774, so proportional loss alone would manufacture the
> correlation. On the step-matched pair, Bitcount excluded (n=48):
>
> | statistic | value |
> |---|---|
> | absolute delta vs distinctiveness | +0.691 |
> | ratio vs distinctiveness | +0.587 |
> | **partial rho, controlling for baseline** | **+0.247** |
> | delta vs midpoint quality (the unbiased form) | −0.557 |
>
> Once baseline is controlled the moderator adds **+0.247**, not the +0.761
> originally published. The honest reading is that **the loss concentrates
> where the model was already doing well**, and ordinary fonts are simply where
> it was doing well. Distinctiveness contributes something beyond that, but
> modestly.
>
> This is the same trap this repo retracted a finding for once before
> (`research/2026-08-07-the-redistribution-signature-was-regression-to-the-mean.md`).
> I ran the midpoint-conditioned form only when challenged; it should have been
> the first analysis, not the third.
>
> **3. Leakage-removal ruled out.** 32 of the 50 holdout fonts share a
> superfamily with a training font, so if the filter had deleted the holdout's
> own siblings the drop would be an artefact of removing near-duplicates rather
> than a statement about corpus quality. Checked with `shares_family` over all
> 87 removed stems against all 50 holdout fonts: **zero holdout fonts lost a
> sibling.** The worst-hit faces (MuktaMahee −0.404, Tirra −0.404,
> StackSansText −0.372) each kept every sibling they had.
>
> **4. WHAT IS STILL NOT ESTABLISHED: training-run variance.** This is the real
> remaining gap and it is not small. Everything measured in this repo about
> run-to-run variance is *inference*-seed variance (`analysis/seed_variance.py`,
> main-effect SD 0.0248). **The variance between two TRAINING runs has never
> been measured here at all.** Both arms used `--seed 42`, but the corpora are
> different sizes, so the shuffle sequences and therefore the trajectories
> differ regardless. Every eval is also single-inference-seed, which alone
> carries SE ≈ 0.037.
>
> So −0.133 is ~3.6 inference-SE — unlikely as inference noise — plus an
> unknown amount of training-run noise. It is probably real. It is not
> established.
>
> The sections below are the original text, kept as written.

## The drop lands on ORDINARY fonts, as predicted

Against the frozen, model-independent moderator
(`research/holdout_distinctiveness.json`):

    Spearman rho = +0.761, p = 1.4e-10, n = 50

    ordinary half    mean delta  −0.2443
    distinctive half mean delta  −0.0353     (7x smaller)

Worst hit: MuktaMahee (−0.447), StackSansText (−0.372), the IBMPlex family
(−0.372), Wonky (−0.340), Tirra (−0.309), MirandaSans (−0.309) — workhorse
text faces, every one.

**This was a prediction, not a post-hoc story.** The 87 removed fonts include
`arial`, `georgia`, `verdana`, `times`, `tahoma`, `consola`, `segoeui*` — the
archetypal text designs. The multi-seed run had already established that the 4B
is weakest on ordinary typefaces
(`research/2026-08-08-multiseed-the-4b-9b-gap-is-real-and-bigger.md`, rho =
−0.536). Removing the most canonical ordinary faces should therefore hurt
ordinary faces specifically. It did, at rho = +0.761.

## Why this is not seed luck

The run is single-seed, and this project has been burned by exactly that. But
the seed main effect **shifts all fonts together** — that is its measured
signature (`analysis/seed_variance.py`: it does not average out across fonts
because it is common to them). A seed effect cannot manufacture a **+0.761
correlation with a frozen, model-independent moderator**. The structure is the
evidence, not the magnitude.

## Confounds, honestly

Three things differed between the two runs. Two are eliminated:

1. **Steps 5000 → 4530.** Eliminated by matched-step comparison: lrfix at step
   4530 had loss 0.0496; clean finished at 0.0480. Training tracked normally.
   (The earlier reading that clean was "under-trained" compared its final loss
   against lrfix's final loss at a *different* step count.)
2. **The GPU duty-cycle throttle**, which ran for the first time in this run and
   was therefore perfectly confounded with the corpus change. Eliminated by a
   control: 10 steps, seed 42, unthrottled → `loss 0.0873, gnorm 0.16`;
   throttled → `loss 0.0873, gnorm 0.16`. Identical. **Both earlier smoke runs
   had been throttled, so they compared two throttle variants and never tested
   this.** The control was the missing arm.
3. **Corpus 925 → 838.** Remains, and is the leading explanation.

Not eliminated: single-seed, and the 470-step difference is argued away by loss
rather than by a matched-length run.

## What it means

**The proprietary fonts were disproportionately valuable training data.** Not
because they are better designs, but because they are the *canonical* ones —
Arial, Times, Georgia, Verdana and Segoe UI are the reference points that most
ordinary text typefaces sit near in design space. Removing them thins the region
of the distribution where most real usage lives.

Consequences:

- **The licence filter is expensive, and expensive in the worst place.** The
  product's market is workhorse text faces, which is exactly where the loss is.
- **A replacement set is now essential, not optional.** Restoring corpus size
  with faces drawn from the same region is the whole remediation.
- **The ordinary-skewed replacement set is the right medicine** — by luck of
  reasoning rather than design. `research/replacement_set.json` selects at
  median distinctiveness 0.0250 against the corpus's 0.0467, i.e. deliberately
  toward the region this run shows was gutted. The `--match-dropped` control set
  (median 0.0420) now looks like the *wrong* choice: it matches what was
  removed by distinctiveness, but the removed faces' value was their
  canonicality, which that moderator does not measure.

## Next

Train the clean corpus **plus the 87 ordinary replacements at 5000 steps** —
same length as lrfix, so the only difference from lrfix is *which* fonts, not
how many or how long. If the replacements recover most of the 0.14, the licence
problem is solved at acceptable cost. If they do not, the canonical-face
hypothesis is wrong or the loss is not recoverable from OFL sources, and that is
a much harder problem for the project.

**Post-correction note on that plan.** The replacement run is still the right
next step, and if anything it is now the *only* way to test the mechanism —
because the moderator evidence for the canonical-face story is weak (partial
rho +0.247), the interpretation cannot be settled by re-analysing these two
runs. Practically the ordinary-skewed set remains the right choice, but for a
weaker reason than originally given: the damage is concentrated where the model
scored well, and ordinary faces are where it scored well. That is a
targeting argument, not evidence that canonicality is the mechanism.

Worth stating plainly: **the corpus cost (−0.133, step-matched, 41 of 48 fonts
worse) is the solid result here.** Everything about *why* it lands where it
lands is interpretation, on a single seed.
