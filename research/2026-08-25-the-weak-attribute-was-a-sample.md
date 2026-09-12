# The weak attribute was a sample, and the feature I built for it does not help (2026-08-25)

**The premise of this task was wrong.** `serif vs sans` was recorded at AUC
0.733 — "carried weakly" — and that number motivated building a terminal-shape
feature. On a **disjoint** set of families the same six features score **0.869**.
The attribute was already carried. The feature I added makes it slightly
**worse**.

Tool: `analysis/terminal_shape.py`, committed **before** it ran. Data:
`research/terminal_shape.json`.

## The result

50 serif + 50 sans families taken from index **50 onward** in sorted order, so
the families scored by the run that returned 0.733 are excluded entirely.
Baseline and new feature measured on that **same** fresh sample.

| | AUC | p | families |
|---|---|---|---|
| six features (baseline) | **0.869** | 0.0005 | 99 |
| + terminal shape | **0.844** | 0.0005 | 99 |
| | **−0.024** | | |

```
PRE-REGISTERED BAR AUC >= 0.75: PASSED
```

**The bar passed and the feature failed.** Comparing baseline and feature on one
fresh sample is what makes that visible. Had I compared the new 0.844 against
the old 0.733 — the obvious thing, and what a less careful registration would
have licensed — I would have reported *"the terminal feature lifts serif-vs-sans
by +0.111"*. It does the opposite.

## The finding that outlives the task

**A 0.136 AUC swing between two disjoint 50+50 family samples of the same
attribute, with the same features.**

Every AUC in `research/attribute_separation.json` is a **single** such sample:

| attribute | AUC | samples |
|---|---|---|
| weight | 0.970 | 1 |
| mono | 0.946 | 1 |
| slant | 0.915 | 1 |
| width | 0.839 | 1 |
| serif vs sans | 0.733 → **also 0.869** | 2 |

Only one of them has ever been measured twice, and the two measurements differ
by more than the gap between "carried" and "weak". **The others are quoted
without their variance**, which is the oldest lesson in this repository arriving
in a new place — it took three identical training runs to learn it for char_acc,
and the same shape is here in the attribute AUCs.

## Two readings, and I cannot separate them

1. **Sampling variance.** 50 families is a small sample and AUC on 99 points is
   noisy. Then every attribute number above carries a similar interval.
2. **The halves differ systematically.** The split is by *sorted family name*,
   which is not random. Alphabetically-early Google Fonts families are not a
   random draw from the corpus — they may differ in vintage, foundry or script
   coverage.

Both readings undermine quoting a single AUC, so the practical conclusion is the
same. Distinguishing them needs a randomised re-split, which is cheap and is not
done here because it was not registered.

## What is not being done

The registration says: *"the feature is NOT iterated against this sample — no
second definition scored on the same families."* A different terminal statistic
scored against these 99 families is exactly the move that produced the
style-adherence retraction. Any further attempt needs the remaining untouched
families and its own bar.

## The feature, for the record

Two numbers, because the obvious guess was wrong. *"A serif is extra ink at the
stroke end, so the distance transform is larger there"* is false: a serif is a
**crossbar**, so the skeleton of a serifed stem is a **T**, not a line. It
therefore multiplies skeleton endpoints and makes them **thinner**. `term_count`
and `term_ratio` capture those and move in opposite directions.

The reasoning is sound and the feature still does not help. That is worth
recording as its own small lesson: a mechanism argument is a hypothesis, not a
result.

## Consequence for the plan

Task B is closed. **The vocabulary gap it was built to fill does not exist as
stated** — serif-vs-sans is carried at 0.869 on families that were not cherry-
picked by an earlier failure. The remaining vocabulary work is contrast,
aperture and the rest, none of which has labels, and all of which would need
synthesis rather than a feature.

**The higher-value follow-up is now variance, not vocabulary:** re-measure the
four "carried" attributes on a second sample before any of them is built upon.
