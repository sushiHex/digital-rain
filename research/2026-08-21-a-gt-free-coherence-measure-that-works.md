# A ground-truth-free coherence measure that works (2026-08-21)

**The instrument the product needs, validated twice at n=50.** It detects the
failure identity scored *above* the control, and the fix was one idea: remove
the character effect before measuring style.

Tool: `analysis/style_coherence.py`. Data:
`research/style_feature_stats.json`, `research/style_coherence_validation.json`.

## The gap it fills

The product concept — user describes a style, a generative model draws the two
reference characters, the user selects and iterates — has **no target font**. So
char_acc, DINOv2, LPIPS, R-ACC and composite, all of which compare against a
ground-truth atlas, cannot score it at all.

Identity survives and is blind to the failure that actually happens: given a
reference whose two glyphs disagree, the model transfers both and the atlas
splits along the K-like / g-like seam. Identity scored that **0.9034 against a
coherent control's 0.8910** — above it
(`2026-08-21-two-styles-in-two-styles-out.md`).

## Why the first attempt failed, and what fixed it

The first coherence statistic was the spread of ink fraction across cells. It
returned **p=0.970**.

The reason: `.` and `M` differ enormously for reasons that have nothing to do
with style, so the statistic measured *which letters these are*. The fix is
per-character normalisation — z-score every feature against **that character's**
distribution over 250 real corpus fonts, and measure only the residual.

That single change is the whole difference between p=0.970 and p=0.0021.

Features, chosen to be interpretable and to target what was observed:

| feature | what it captures |
|---|---|
| `stroke` | mean stroke width from the distance transform, over glyph height |
| `slant` | shear from second-order image moments |
| `fill` | ink area over bounding-box area |
| `parts` | log connected-component count — dot-grid versus solid |

## The result

50 fonts, `oracle` (one real font) against `mixed` (two superfamilies):

| metric | oracle | mixed | p | r | |
|---|---|---|---|---|---|
| **dispersion** | 0.3368 | 0.4064 | **0.0021** | **0.435** | **detects** |
| split | 4.0813 | 4.0252 | 0.3131 | 0.143 | no |
| split_max | 4.9854 | 4.8157 | 0.0718 | 0.255 | no |

**A second, independent validation.** The labels are *graded*, not binary — the
pairings run from serif-meets-dot-grid to sans-meets-sans. Severity is the
distance between the two source fonts' style vectors:

```
Spearman rho = +0.407    p = 0.0034    n = 50
```

The measure does not merely separate two groups; it tracks **how mismatched each
pair actually was**. That is harder to explain by anything other than working.

## A hypothesis I got wrong, kept as the record

I predicted the defect was **bimodal** — the atlas splits into two groups, so a
two-means separation statistic should beat plain dispersion. It does not:
`split` scores p=0.313 and `split_max` p=0.072, while plain `dispersion` clears
both gates.

**The shape of the statistic did not matter. Removing the character effect did.**
Both statistics are still computed and reported, so the claim stays checkable
rather than being quietly dropped.

## The n=12 stage, which is the methodological point

The first run used 12 fonts and reached **neither** significance threshold:

| | n=12 | n=50 |
|---|---|---|
| paired | r=0.408, p=0.176 | r=0.435, **p=0.0021** |
| severity | rho=+0.424, p=0.170 | rho=+0.407, **p=0.0034** |

**The effect sizes barely moved. Only the power did.** Two independent signals
both sitting at r≈0.41 with p≈0.17 is the signature of an underpowered
comparison, not of a null — and this project has a long record of concluding
from exactly that shape. Spending 88 more generations was the cheaper error.

## What it is for

Two uses, one measure:

1. **At the reference, before generating.** Score the two supplied glyphs for
   mutual consistency and re-roll rather than producing a split atlas. This is
   the feature the previous note implied; the measure now exists to build it.
2. **At the atlas, as the quality score.** The product cannot use any metric
   that needs a target font. This one needs none.

## Caveats

- **Validated against constructed incoherence, not real generated references.**
  `mixed` deliberately pairs two superfamilies. A text-to-image model trying to
  be consistent will fail more subtly, and this has not been tested on that.
- **One checkpoint, one seed.** The paired design cancels the seed across arms,
  but no run-to-run variance is estimated for this metric.
- The per-character prior is fitted on 250 corpus atlases. Characters with fewer
  than 20 readable instances are dropped rather than trusted.
- `dispersion` is a *relative* score. It has no absolute threshold yet — turning
  it into a reject/accept gate needs a calibration set of references judged by a
  human, which does not exist.
