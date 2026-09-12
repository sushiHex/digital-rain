# Corpus expansion is small; variable-font instancing is the real lever (2026-08-02)

**Question.** Three levers — rank 64, distinctiveness oversampling, and the V5
source swap — all produced the same signature: gains on hard fonts, matching
losses on easy ones, flat aggregate. That is **redistribution at fixed
information**. Only 93 of 925 corpus fonts sit above p90 distinctiveness. Can
the corpus supply more information, rather than have its existing information
reweighted?

## First: the V5 "more data didn't help" result does not say that

`docs/quality-roadmap-v2.md` records "more diverse data didn't help (V5)". Its
own caveats undercut the headline:

- **908 fonts vs 870** — a source *swap at constant size*, not an addition.
- **The holdout is Google-Fonts-only and so was the baseline.** The same doc
  files this under "critical eval methodology problems found by adversarial
  review": V5 was measured out-of-distribution against an in-distribution
  baseline.
- **Perceptual dedup was "actively harmful"** — it removed 123 fonts that were
  in the successful baseline.
- **Rank 16**, and an LR schedule that "decays too early" (best loss at step
  3130/3500, at ~3% of peak LR).

And char_acc — the style-fidelity axis — **improved +0.021**. The composite
drop was 77% LPIPS. This is not evidence that adding fonts fails.

## Expansion alone: real, but small

`analysis/score_pool_distinctiveness.py`, scoring every OFL family not already
in the corpus, anchored to the **corpus centroid** so scores are directly
comparable to `research/font_distinctiveness.json`. Holdout fonts are excluded
by an explicit guard — they are absent from `dataset_v2` and would otherwise
read as fresh candidates, silently contaminating every future eval.

| | count |
|---|---|
| candidate OFL families (one-per-family, corpus + holdout removed) | 1,226 |
| rejected on the 95-char/quality gate | 1,021 |
| **usable new fonts** | **205** |
| of those, above corpus p90 (0.1315) | **18** |
| above 0.25 (genuinely abstract) | 10 |

So expansion grows the corpus +22% but the **distinctive tail only 93 -> 111
(+19%)**. `google-fonts/ofl` is mostly non-Latin scripts, which legitimately
fail a 95-char Latin gate. An earlier estimate of "+63%" was made by counting
font *files* in distinctive family names; measured, most are variants that fail
the gate or are near-duplicates. **The name-based estimate was wrong by 3x.**

+19% is unlikely to move a model that plateaued on redistribution.

## The lever that is actually there: variable-font instancing

`atlas_constants.load_truetype_pinned` pins every variable font to the
"Regular" instance, for raster reproducibility. Consequence: **every structural
axis in the corpus is unused** — Bitcount's `ELSH`/`ELXP` (element shape and
expansion), Sixtyfour/Workbench's `BLED`/`SCAN` (bleed, scanline), Doto's
`ROND`. These are not weight axes; they change letterform *structure*, which is
precisely the failure mode.

`probes/spike_variable_instances.py` renders every named instance and compares
the within-font spread against the spread across 12 *distinct* distinctive
fonts (mean pairwise DINOv2 cosine distance, 0.4003):

| font | instances | spread | vs across-font |
|---|---|---|---|
| Workbench[BLED,SCAN] | 8 | 0.2511 | **62.7%** |
| Bitcount[CRSV,ELSH,ELXP,slnt,wght] | 18 | 0.2213 | **55.3%** |
| Sixtyfour[BLED,SCAN] | 8 | 0.1871 | **46.7%** |
| Doto[ROND,wght] | 9 | 0.0929 | 23.2% |

Instances of one Bitcount are **~55% as structurally different from each other
as entirely unrelated distinctive typefaces are**. That is not cosmetic
variation. Doto (ROND + wght only) is the weak case and sets the cosmetic floor
at ~23%.

### Sizing it

| | fonts | training examples |
|---|---|---|
| corpus distinctive tail today | 93 | 93 |
| of those, variable | 9 | 77 named instances |
| **distinctive tail, instancing only distinctive variable fonts** | 93 | **161 (+73%)** |
| plus 18 new static distinctive fonts from the OFL sweep | 111 | 179 |
| plus 4 distinctive variable fonts in the pool (51 instances) | 115 | **~226 (2.4x)** |

**Instancing must be selective.** Corpus-wide there are 177 variable fonts
holding 1,086 instances; instancing everything would inflate the ordinary
majority too and reproduce the redistribution ceiling. The point is to grow the
*tail*, not the corpus.

## Recommended experiment

Corpus expansion + selective instancing of distinctive variable fonts + a rank
increase, together. Each alone has now been shown to redistribute; expansion
supplies information and rank supplies capacity to absorb it rather than trade
against existing quality.

Two prerequisites, or the result will be unreadable:

1. **A distinctiveness-stratified holdout**, reporting hard-half and easy-half
   separately. `research/2026-08-02-distinctiveness-oversampling.md` already
   called the current holdout "the limiting instrument," and holdout bias is
   what made V5 uninterpretable.
2. **Licence filtering.** The corpus is 97.5% OFL and that underpins the
   output-licensing position. `google-fonts/ofl` is verifiable per family;
   the flat `font_pool/` (5,220 googlefonts- plus github/silnrsi/mozilla/IBM
   prefixes) carries no licence metadata and is marked `licence: unknown`.

## Artifacts

- `analysis/score_pool_distinctiveness.py`, `research/pool_distinctiveness.json`
- `probes/spike_variable_instances.py`
- `score_pool.sh`
