# The gate clears its bar — and the seed clears it higher

2026-09-13. Calibration round 2 (issue #29). The owner judged the 48
Z-Image candidate references (`eval_runs/_candidate_refs/zimage-n4`, the
same twelve descriptions × four seeds as the klein-base set) with the same
question — *would you hand this pair to a user as a starting point for the
style they asked for?* — and the pre-registered analysis
(`analysis/calibrate_instruments.py`, fixed before any label existed; the
`set` amendment of 2026-09-13 scores the union as one sample with the
statistic, bar and cut unchanged) ran on the union of both sets.

The owner's caveat, recorded with the labels: *"I was slightly lenient on
the judging."* Read every "usable" below as "usable or marginal" — and
read the precision figures as **upper bounds**: leniency turns true
rejections into recorded acceptances and never the reverse, so under any
stricter relabelling the accepted-and-usable count can only fall and the
accepted-and-not count only rise. Recall and specificity can move either
way, and the AUC's direction is indeterminate, since the marginal
acceptances sit on both sides of the cut.

---

## The labels

Z-Image: **25 usable, 23 not**, of 48. With the 48 klein-base references
(all usable, 2026-09-12) the union holds 73 usable and 23 not.

The 23 misses are not spread evenly. By generation seed:

| Z-Image seed | usable | mean gate distance | refused at the 1.875 cut |
|---|---|---|---|
| 0 | 5 / 12 | 2.608 | 10 |
| **1** | **0 / 12** | 2.535 | 8 |
| **2** | **10 / 12** | **0.610** | **0** |
| 3 | 10 / 12 | 2.113 | 7 |

Every seed-1 reference was rejected, whatever the description; ten of
twelve seed-2 references were accepted, and seed 2 is also the most
coherent *group* in either set (mean distance 0.610; klein-base's most
coherent seed averages 0.814). By description the spread is 1/4 to 3/4
with no description at 4/4 — the slab serif, the condensed grotesque and
the stencil each yielded one acceptable reference in four.

What "seed" is here matters for everything below. Both candidate sets were
generated with one fixed random seed per seed index, **shared across the
twelve descriptions**: `s1` is the same initial noise for all twelve
prompts, and so is each of the other three. The four seed rows are four
noise draws, not forty-eight independent ones. A seed that fails for every
description is one draw the model could not steer with any of twelve
prompts; the effective sample behind any seed effect is four, and the
labels within a seed row are not independent of each other.

## The registered result, verbatim

```
GATE  usable 73 / not 23
      AUC (usable more coherent) = 0.839   permutation p = 0.0001
      at the existing cut 1.875: precision 0.90  recall 0.85  specificity 0.70
PRE-REGISTERED BAR AUC>=0.7 and p<0.05: PASSED -- coherence predicts usability; a threshold may be cut on a FRESH sample
ADHERENCE (secondary, n=16): AUC of P(requested treatment) for usable = 0.345 -- reported, not claimed
```

**PASSED, as registered.** The registration says the bar "reads as
'coherence predicts usability' and licenses the next step: cutting a
threshold on a FRESH labelled sample". Both halves are the registration's;
the section after this one is about what the first half means on this
particular sample. No threshold is cut here, and the 1.875 cut stays what
it was.

At that cut, on the union: 62 accepted and usable, 7 accepted and not, 11
refused and usable, 16 refused and not. The recall of 0.96 measured on the
klein set alone becomes 0.85 on the union, because the gate refuses nine of
the twenty-five Z-Image references the owner would accept.

## What the union cannot tell apart — unregistered, descriptive

Everything in this section uses the registered script's own functions on
the registered record; none of it was registered and none of it is a
verdict.

**Class is confounded with set.** All 23 negatives are Z-Image and all 48
klein-base references are positive, so an AUC on the union rewards any
statistic that tells the two generators apart. The gate does: with labels
ignored, AUC(klein more coherent than Z-Image) = **0.762** (mean distance
1.009 against 1.967). Within the Z-Image set alone, where both classes
exist, the gate reads **AUC 0.732, permutation p = 0.0027** — it would
clear the same bar on its own, at the cut precision 0.70, recall 0.64,
specificity 0.70.

**Class is confounded with seed, and once seed is held fixed the gate has
no signal.** Hold the seed constant — count only usable-versus-not pairs
that share a seed (75 such pairs), and shuffle labels only within each
seed row — and the gate reads **AUC 0.360, permutation p = 0.892**; per
seed 0.514, 0.150 and 0.300 (seed 1 has one class). The residual points
the wrong way, at sizes where that means nothing either. So the within-set
0.732 is not "mostly" the seed contrast, it is all of it: the gate
separates the four noise draws from one another, and the owner's
acceptances separate the same four draws, and that is the whole
correlation. The post-hoc description of the same table — "the seed is 2
or 3" — reads AUC 0.813, but it is the best of the fourteen ways of
splitting four seeds, chosen with the labels in hand, on an effective
sample of four; it describes this table and predicts nothing.

**Class is confounded with the sitting, too.** The klein-base set was
judged from the sheet on 2026-09-12 and the Z-Image set from the labelling
page on 2026-09-13 — a different presentation on a different day, recorded
in the `note` column. Whatever part of the set effect is the judge rather
than the generator cannot be separated out here.

**The rows the cut gets wrong say what the gate is.** Seven references the
owner rejected pass the cut; the two most coherent of them are `04-s2`
(distance 0.112, the most coherent reference in either set) and `02-s2`
(0.409, eighth of 96) — a condensed grotesque and a slab serif, each one
coherent typeface that is not the typeface asked for. That is the blind
spot the picker analysis named (held privately; its result is in the
README's product-loop section): a wrong-style reference that still looks
like one face is invisible to a coherence check, and the gate cannot be
calibrated into seeing it. The eleven usable references it refuses are nine
Z-Image draws from seeds 0 and 3 (distances 2.56–3.09) and the two klein
references already recorded.

**"Usable" is not "adherent".** The adherence secondary reads 0.345 on the
union (0.467 within Z-Image, n = 8): the four klein stencil references the
owner accepted score P(stencil) 0.002–0.003 — the model calls them solid, and
the transfer note already established they are. A solid face is an
acceptable starting point for a person and a failed stencil for the
adherence measure; the labels answer the first question, and #9 needs
labels that answer the second.

## What it means

1. As registered, the gate's distance correlates with a person's
   acceptance on this sample and the bar is passed. What the sample then
   shows is that the correlation runs through the generator and the noise
   draw, not through the references: with both held fixed there is none
   left. The gate is a coherence check. Its cut is still provisional, and
   the union AUC is not its accuracy.
2. The fresh sample the bar licenses has to break all three confounds: a
   different seed per reference, seeds outside 0–3, both generators mixed,
   the owner judging with the seed and the generator hidden, in one
   presentation in one sitting. Cut the threshold there, once, and test it
   on nothing that was seen.
3. For the generator: the "48/48 usable" recorded for Z-Image on
   2026-08-25 was the automatic malformed-candidate check; a person rejects
   23 of the same 48. At the reference stage Z-Image's usability is a noise
   lottery before it is a description lottery — one initial-noise draw
   produced nothing acceptable under any of twelve prompts, another
   produced acceptable references under ten. Where the prompt steers the
   draw weakly, the draw decides. And since the same four draws serve every
   description in these sets, a bad draw is bad for all twelve at once —
   which is a property of how the sets were built, not a fact about
   descriptions.

## Reproduce

```
python analysis/calibrate_instruments.py            # the registered run; writes research/calibrate_instruments.json
```

Labels: `research/calibration_labels.csv` (96 rows, `set` column, the
owner's caveat in `note`). Record: `research/calibrate_instruments.json`
(per-row distances; the descriptive figures above recompute from it with
the script's `auc`, `permutation_p` and `cut_report`; the seed-stratified
AUC pools the within-seed pairs and shuffles labels within each seed row,
10,000 times). The round-1 record it replaced is preserved as
`research/2026-09-12-calibrate_instruments.json`.
