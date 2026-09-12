# The sidebearing prior that did not pay: two wrong terms were cancelling (2026-08-19)

**Negative result, shipped as an opt-in flag rather than a default.** The
per-character sidebearing model is correct, measurably better in isolation, and
worth nothing in this pipeline — because the constant it replaced was silently
compensating for a different defect.

Tools: `analysis/fit_sidebearing_prior.py`, `analysis/score_finished_font.py`.
Data: `research/sidebearing_prior.json`.

## The premise, and it was sound

`analysis/score_finished_font.py` had just established that **letterfitting is
74% of the finished font's error** — with model error exactly zero, the
ground-truth-traced arm still missed its source by 0.1168 em per glyph.

`atlas_to_font` gave every glyph the *same* sidebearing: one constant, 0.05 em,
both sides. Real letterfitting is not remotely like that. Measured over 600
licence-clean fonts, holdout superfamilies excluded:

| char | LSB (em) | RSB (em) | cross-font SD |
|---|---|---|---|
| `H` | +0.0540 | +0.0480 | 0.0420 |
| `O` | +0.0490 | +0.0410 | 0.0406 |
| `T` | +0.0240 | +0.0110 | 0.0400 |
| `A` | **+0.0070** | +0.0160 | 0.0402 |
| `V` | +0.0181 | **+0.0020** | 0.0602 |

A vertical stem needs air beside it; a diagonal does not. The constant is about
right for `H` and `O` and **8× too wide for `A`** — and `A`, `T` and `V` were
among the worst glyphs the finished-font scoring flagged.

**Measured in isolation, the prior works.** Predicting advance as
`real ink width + prior sidebearings`, evaluated on 4,699 holdout glyphs:

| model | advance MAE |
|---|---|
| constant 0.05 em | 0.1090 |
| per-character prior | **0.0931** (−14.6%) |

## What happened when it was applied

Nothing, and then something worse. All three arms rebuilt, 50 fonts:

| | constant | prior |
|---|---|---|
| `gt_traced` advance MAE | 0.1168 | 0.1165 |
| `gt_traced` text width err | **−0.0030** | **−0.0622** |
| `retrieval` text width err | +0.0119 | −0.0472 |
| `model` text width err | −0.0764 | −0.1354 |

A 0.3% gain on the metric it targeted, and a 6-point regression on total text
width across every arm.

## Why: the tracer under-measures ink, and the constant was absorbing it

Comparing each traced glyph's ink extents against the same glyph in the source
font, 4,700 glyphs over 50 fonts:

```
traced ink / real ink    median 0.9646    narrower for 73.9% of glyphs
```

And the bias is not uniform. Letters trace **narrow**; small punctuation traces
**wide**:

| narrowest | | widest | |
|---|---|---|---|
| `W` | 0.944 | `` ` `` | 1.129 |
| `&` | 0.945 | `:` | 1.172 |
| `Q` | 0.947 | `.` | 1.276 |
| `%` | 0.948 | `'` | **1.378** |

That is a resolution effect: a period occupies a handful of pixels in a 106×160
cell, and the 4× upscale, threshold and curve fit all round it outward, while a
large glyph loses a little at every edge.

So the flat 0.05 em sidebearing was doing two jobs. It was a sidebearing, and it
was a fudge factor for a ~3.5% ink deficit on letters. Replace it with correctly
*tighter* per-character values and the fudge disappears with it — the glyphs get
narrower, the text gets narrower, and the letterfitting gain is cancelled out.

**Both terms were wrong, in opposite directions, and the sum was closer to right
than either part.** Fixing one alone is a regression.

## The decision

The prior ships **off by default**, reachable with
`build_font(..., use_sidebearing_prior=True)` or `--sidebearing-prior`. The
fitted values, the fitter and the tests are all kept, because the finding is
real and the next attempt should not have to re-derive it.

Shipping it as the default would have been defensible on the isolated 14.6%
number and wrong on the pipeline evidence. That is the whole reason
`score_finished_font.py` exists.

## What would actually fix it

The two terms have to be fitted **jointly against traced ink**, not against real
ink — a per-character linear model `advance ≈ a_c · ink_traced + b_c`, fitted on
corpus atlases traced through the same path.

This was not built. It needs an atlas → source-font mapping, and `dataset_v2`
does not record one: `manifest.txt` holds 2 lines against 925 atlases and no
source paths. Reconstructing it by stem search runs straight into the loader
hazard `CLAUDE.md` documents — `build_dataset` pins variable fonts to their
Regular instance and the reference opens them raw, which already mismatched ~110
of 177 additions once. Doing it carelessly would fit the correction on the wrong
renders.

Two smaller things also stayed unmeasured:

- **Per-font fitting tightness.** Cross-font SD is 0.022–0.060 em, comparable to
  the medians themselves, so most of the residual variance is per-font rather
  than per-character. A traced atlas carries ink extents, not advances, so there
  is no obvious signal for it.
- **Kerning**, still absent from every arm.

## The pattern, for the third time

`docs/what-happened.md` records three error families. This is the third again:
**a compound quantity hiding two cancelling defects.** Yesterday it was the
model's narrow glyphs cancelling 2×-wide spaces and briefly reading as the model
beating retrieval. Today it is a sidebearing constant cancelling a tracer bias.

The tell is the same both times: a *sum* that looks healthier than any of its
terms. The habit that catches it is also the same — measure the parts
separately, and be suspicious when a total is better than it has any right to be.
