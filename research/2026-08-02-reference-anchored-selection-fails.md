# Reference-anchored no-GT selection fails: the style lottery is per-cell, not per-atlas (2026-08-02)

**Question.** The 4B trails the 9B by 0.0457 char_acc. That deficit is only
~28% of the 9B's *own* best-of-4 sampling headroom (0.6738 seed-0 -> 0.8366
oracle, +0.1628), so the quality is already inside the sample distribution and
the problem is **selection**, not capacity.

Three no-GT selectors had been tried and filed as failures: TrOCR (4.3%),
GOT-OCR2 (4.7%), DINOv2 medoid (14.1%). All three ignore the one piece of
genuine ground truth available at inference: **the reference image the user
supplies contains 2 glyphs (`reference_chars`, "Kg") in the target style.**
Those are real GT for 2 of 95 cells, in the actual target style, no leak.

Hypothesis: anchoring selection on that reference beats the unanchored proxies
— and specifically avoids medoid's *mode-seeking* bias ("most typical of N"),
which pushes toward canonical letterforms, the wrong direction for exactly the
distinctive faces the 4B is weakest on.

**It does not. The hypothesis is refuted.**

## Result (n=4,700 cells, 50 holdout fonts, 4 seeds)

| selector | char_acc | capture of the seed0->oracle gap |
|---|---|---|
| seed-0 only (no selection) | 0.6738 | — |
| **DINOv2 medoid** (existing) | **0.6968** | **14.1%** |
| ref-anchor per-cell | 0.6813 | 4.6% |
| hybrid medoid + ref prior, lam=0.25 | 0.6909 | 10.5% |
| hybrid medoid + ref prior, lam=0.5 | 0.6919 | 11.1% |
| hybrid medoid + ref prior, lam=1.0 | 0.6866 | 7.8% |
| hybrid medoid + ref prior, lam=2.0 | 0.6817 | 4.8% |
| ref-best-seed (font-level) | 0.6698 | **-10.2%** of the font-level oracle |
| *ceiling: best single seed per font* | *0.7134* | |
| *ceiling: per-cell best-of-4 oracle* | *0.8366* | |

Every reference-anchored variant loses to plain medoid. The hybrid degrades
monotonically as the reference prior is weighted more heavily. The font-level
selector is **worse than no selection at all**.

## Why: the lottery is per-cell

`ref-best-seed` picks the single seed whose K and g best match the reference,
like-for-like, then uses that seed for all 94 glyphs. It scores *below seed-0*.
So a seed that renders the reference characters well is not systematically
better on the rest of the atlas — the per-seed quality prior carries no
per-cell information.

That is consistent with what this project already established: char_acc
variance is a **per-cell style lottery**
(`research/2026-07-18-wrong-letters-are-a-metric-artifact.md`), not an
atlas-level quality difference. A global style prior has nothing to transfer to
an individual cell. Medoid works, as far as it works, precisely because it is
computed *per cell*.

**Consequence for future selector work: the signal must be per-cell.** Any
selector built on a font-level or seed-level quality estimate is refuted by
this result before it is built.

## A methodology trap worth recording

The first implementation tight-cropped each cell to its ink bounding box before
embedding, to make cells comparable to the (differently framed) reference
glyph. That **collapsed the medoid control from 14.1% to 1.2%** on identical
data — and would have been read as "the reference anchor is competitive with
medoid," since both were crippled equally.

Tight-cropping normalizes away size and placement, which are part of the
quality signal: a malformed glyph with wrong proportions is normalized until it
looks fine. The fix is to normalize in the other direction — keep cells in
native cell geometry for typicality, and confine the tight crop to the
like-for-like reference match, which needs its own embedding space.

The control reproducing the recorded 14.1% *exactly* (0.6738 -> 0.6968) is what
caught it. **Always re-derive the known baseline inside a new harness.**

## What stands

- **Medoid remains the best no-GT selector**, at +0.0230 char_acc. Filed as
  "captures only 14.1%," which is true against the oracle — but against the
  0.0457 gap to the 9B it is **50%**. It was measured against the wrong
  yardstick for the commercial question.
- The per-cell oracle (0.8366) is far above the font-level oracle (0.7134), so
  per-cell mixing across seeds is where the headroom lives, not atlas picking.

## Untried after this

A **learned per-cell predictor** — the remaining candidate, and the only one
this result does not rule out, because it can be made per-cell. Features must
be per-cell: candidate typicality, ink/stroke statistics relative to the
font's own other 93 cells, etc. Prior attempts were all zero-shot proxies;
none was trained to predict the target metric, and per-cell labels already
exist in every `scores.json`.

**Not** worth trying: anything that scores a whole seed or whole atlas.

## Artifacts

- `studies/select_reference_anchored.py`
- `research/2026-08-02-selector-dev-9b.json` (aggregate + per-font)
- Dev data: `dpo_holdout_bestofn/` (9B candidates; note these were generated
  before the `candidate_gen` conditioning fix, so absolute values are from a
  mis-conditioned model — the selector *comparison* is unaffected, all arms
  share the same candidates)
