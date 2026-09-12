# Corpus expansion v3: the targets improved, the majority regressed, and the run has a confound I introduced (2026-08-03)

**What ran.** `dataset_v3` (925 -> 1,113 fonts: +168 OFL fonts and +13
variable-font instances, distinctive tail 93 -> 122) at rank 32, 5000 steps,
every other hyperparameter identical to `training_glyph_4b_r32_5000`. Single
variable: the dataset.

## The gate: a significant regression

Paired Wilcoxon, n=50, gate p<0.05 AND r>=0.3:

| metric | v2 (925) | v3 (1113) | p | r | verdict |
|---|---|---|---|---|---|
| composite | 0.8158 | 0.8186 | 0.4037 | 0.118 | no diff |
| **char_acc** | 0.6460 | **0.6081** | **0.0036** | **0.434** | **SIG (v2 better)** |
| **dinov2** | 0.8485 | **0.8314** | **0.0022** | **0.433** | **SIG (v2 better)** |
| racc | 0.7360 | 0.7443 | 0.2216 | 0.186 | no diff |
| lpips | 0.1381 | 0.1331 | 0.0849 | 0.244 | no diff |
| identity | 0.9893 | 0.9855 | 0.2744 | 0.291 | no diff |

## The structure: a fourth redistribution, on the worst terms yet

| metric | mean delta | Spearman rho | p | harder half | easier half |
|---|---|---|---|---|---|
| char_acc | −0.0379 | **−0.549** | <0.0001 | **+0.0077** | **−0.0834** |
| dinov2 | −0.0172 | **−0.650** | <0.0001 | +0.0028 | −0.0371 |
| racc | +0.0083 | −0.487 | 0.0003 | +0.0221 | −0.0066 |
| composite | +0.0028 | −0.395 | 0.0045 | +0.0080 | −0.0024 |

Compare the trade against the three prior levers:

| lever | harder half | easier half | ratio |
|---|---|---|---|
| rank 64 | +0.0298 | −0.0289 | ~1:1 |
| oversampling | +0.0221 | −0.0357 | ~1:1.6 |
| **corpus expansion** | **+0.0077** | **−0.0834** | **~1:11** |

Same signature, far worse terms. The easy half paid eleven times what the hard
half gained.

## But the targeted fonts did move, and toward the 9B

char_acc on the faces that motivated the whole investigation:

| font | v2 | v3 | delta | 9B |
|---|---|---|---|---|
| **Bitcount Prop Double Ink** | 0.181 | **0.255** | **+0.074** | 0.266 |
| **Bitcount Grid Double Ink** | 0.074 | **0.117** | **+0.043** | 0.138 |
| Fascinate Inline | 0.191 | 0.234 | +0.043 | 0.489 |
| Rubik Distressed | 0.234 | 0.234 | 0.000 | 0.266 |
| Dangrek | 0.511 | 0.479 | −0.032 | 0.691 |
| Wonky (control) | 0.872 | 0.691 | −0.181 | 0.840 |

Bitcount Prop is now within 0.011 of the 9B. Both Bitcount faces improved
*without* their superfamily being instanced -- that was excluded as a leak, so
these gains come from genuinely unrelated added data.

The losses are concentrated in ordinary, previously well-fit faces: Telex
−0.277, KosugiMaru −0.181, EncodeSansSemiExpanded −0.181, Wonky −0.181,
InterTight −0.160. Nothing in the added data resembles those; they simply got
worse.

## The confound, which is mine

**I held steps at 5000 while growing the corpus 20%.**

| | fonts | steps | per-font budget |
|---|---|---|---|
| v2 | 925 | 5000 | 5.41 steps/font |
| v3 | 1,113 | 5000 | **4.49 steps/font (−16.9%)** |

So this run does not test "more data." It tests "more data AND 17% less
training per font," and those pull in opposite directions.

That mechanism has bitten this project before and is on the record:
`docs/quality-roadmap-v2.md` finding 1 — "Lower LR + fewer steps was a disaster
(V4). LR 9.5e-5 at 2500 steps gave only 64% of the per-font learning budget."
The V4 collapse was per-font budget, not data. The damage pattern here matches
it: the fonts that suffered are the ones that were already well-fit and needed
their remaining updates to stay there, while the newly-added hard fonts — with
the most headroom — still gained.

I should have set steps to 5000 x 1113/925 = **6,016** to hold the budget
constant. The strengthening pass caught the holdout leak, the duplicate
instances and the multi-variable design, and missed this.

## What is and is not established

- **Established:** at fixed step count, expanding the corpus 20% significantly
  regresses char_acc and dinov2, and redistributes on ~1:11 terms.
- **Established:** the redistribution signature has now appeared four times
  from four independent mechanisms. The 4B's allocation is malleable; that is
  no longer in question.
- **Established:** the specific abstract faces targeted improved, one to within
  0.011 of the 9B, from data that shares no family with them.
- **NOT established:** whether corpus expansion helps or hurts at matched
  per-font budget. This run cannot answer it.

## Next

Re-run at **6,016 steps** (~13.9 h at 8.3 s/step), everything else unchanged.
That isolates data from budget and is the experiment I intended. If the easy
half recovers and the hard-half gains hold, expansion is a win; if the easy
half stays down, the added data genuinely hurts and the corpus lever closes
alongside rank and oversampling.

## Artifacts

- `eval_runs/glyph_4b_v3_5000/`, `training_glyph_4b_v3_5000/`
- `research/2026-08-03-wilcoxon_glyph_4b_r32_5000_vs_glyph_4b_v3_5000.json`
- `analysis/compare_runs.py` now reports the redistribution block itself
  (Spearman rho + hard/easy halves, in quality space so lpips is not inverted),
  instead of it being hand-rolled per writeup as it was for rank 64 and
  oversampling.
