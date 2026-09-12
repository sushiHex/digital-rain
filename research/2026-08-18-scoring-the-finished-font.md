# Scoring the finished font: a 2x word-spacing bug, and the model still does not beat retrieval (2026-08-18)

Every metric in this repository scores atlas **cells**. The product is an
OpenType font, rendered as running text. Nothing had ever measured that.
`docs/strategy-2026-08.md` called it "arguably the more damning" gap and listed
it as open item 4; the README lists it as open item 2.

Tool: `analysis/score_finished_font.py`. Figure: `viz/finished_font_specimens.py`.
Data: `research/finished_font_scores.json`.

## The design

Three arms are traced through the **same** atlas → OTF pipeline, and all three
are scored against the holdout font's own **source TTF**:

| arm | what it is |
|---|---|
| `source` | the real `.ttf` — the target |
| `gt_traced` | ground-truth atlas → OTF. Model error is exactly **zero**, so any gap is the PIPELINE's |
| `model` | generated atlas → OTF. The product |
| `retrieval` | nearest *training* font's atlas → OTF. The non-generative floor |

`gt_traced` is the ceiling any atlas-based method can reach. Atlas metrics
conflate pipeline cost with model cost and can see neither.

Metrics chosen because atlas scoring is blind to them by construction:

- **advance_mae** — mean `|built advance / source advance − 1|` per glyph, in em.
  This is letterfitting. `build_dataset` centres every glyph in its cell, so
  left and right sidebearings are equal by construction.
- **text_width_err** — relative width of a rendered 63-character specimen.
- **ink_err** — relative ink of that specimen, i.e. weight *at text size*.

## A correction to the premise, stated first

The stated reason to build this was that retrieval "hands back a real font with
real sidebearings", so a finished-font metric should separate it from the model.
**That was wrong.** `analysis/retrieval_baseline.py` returns the corpus font's
*atlas*, so retrieval goes through this same tracer and loses its letterfitting
exactly as the model does. The metric's actual value is different and better: it
separates the **pipeline's** cost from the **model's**.

## What it found first: every generated font had 2x word spacing

The space is the one glyph nothing is ever traced for — it is a blank cell — so
its advance is **assigned**, not measured. The rule was `cell_w * scale * 0.5`,
half a grid cell, which is not a typographic quantity.

| | built | source (50 holdout fonts) |
|---|---|---|
| space advance | **0.49–0.54 em** | **0.2635 em** (sd 0.077, range 0.130–0.600) |

The space was the single worst glyph in **42 of 50 fonts**. Every font this
project ever generated set running text at roughly double word spacing, for its
whole life, and no atlas metric could see it — the cell is blank by definition.

Fitted on the 50 source fonts, space is best predicted by the font's own
lowercase widths:

| basis | k | relative MAE |
|---|---|---|
| **0.50 × mean lowercase advance** | 0.5022 | **0.167** |
| advance of `n` | 0.4439 | 0.172 |
| advance of `i` | 0.9010 | 0.185 |
| fixed em fraction | 0.2635 | 0.190 |

Font-adaptive beats a constant, so `atlas_to_font._space_advance` now derives it
from the traced lowercase, falling back to 0.26 em when no lowercase is
readable. `tests/test_atlas_to_font_space.py` pins it — including a test that
the synthetic geometry still reproduces the old bug, because at an unrealistic
cap height the old rule yields 0.371 em and would slip under any plain "not
double" threshold.

## The result, after the fix

50 fonts, each against its own source TTF. Lower is better on every column.

| arm | advance MAE | adv p90 | width err | ink err |
|---|---|---|---|---|
| `gt_traced` | **0.1168** | **0.2132** | **−0.0030** | +0.0454 |
| `retrieval` | 0.1451 | 0.2804 | +0.0119 | +0.0243 |
| `model` | 0.1582 | 0.2854 | −0.0764 | **−0.0309** |

Paired Wilcoxon over fonts, gate `p<0.05 AND r≥0.3`, via
`analysis.compare_runs.paired_wilcoxon`:

| contrast | metric | p | r | verdict |
|---|---|---|---|---|
| model vs gt_traced | advance_mae | 0.0000 | 0.791 | **gt_traced better** |
| model vs gt_traced | text_width_err | 0.0101 | 0.367 | **gt_traced better** |
| model vs gt_traced | ink_err | 0.1167 | 0.222 | no difference |
| model vs retrieval | advance_mae | 0.0173 | 0.337 | **retrieval better** |
| model vs retrieval | text_width_err | 0.5023 | 0.095 | no difference |
| model vs retrieval | ink_err | 0.1167 | 0.222 | no difference |
| retrieval vs gt_traced | advance_mae | 0.0000 | 0.670 | **gt_traced better** |
| retrieval vs gt_traced | text_width_err | 0.0297 | 0.331 | **gt_traced better** |

Three things follow.

**1. The pipeline dominates letterfitting.** With model error exactly zero,
`gt_traced` still misses the source by 0.1168 em per glyph — 74% of the model's
0.1582. Equal sidebearings are most of that, and they need a different atlas
format and a retrain, not a tuning pass.

**2. The model still does not beat retrieval.** Retrieval wins advance_mae
(p=0.017, r=0.337); the other two are ties. **No metric in this project — atlas
or finished-font — shows the model beating the non-generative floor.** The
README's gate is unmet.

**3. The pipeline ceiling is excellent on total width** (−0.0030 after the space
fix) and poor per-glyph. Those are different defects: cumulative width is now
right, individual letterfitting is not.

## The artefact I nearly published

Before the space fix, the same tool reported:

| | before fix | after fix |
|---|---|---|
| model text-width err | +0.0054 | −0.0764 |
| retrieval text-width err | +0.1025 | +0.0119 |
| paired verdict | **"model better, p=0.006, r=0.388"** | **no difference, p=0.502** |

The model's apparent win was its systematically **narrow** glyphs cancelling the
2x-wide spaces. Two errors of opposite sign summed to a near-perfect total
width, and the metric read it as quality. Had the space bug been fixed a day
later, "the first metric where the model beats retrieval" would have been
written down and would have been false.

This is the third family member of the two in `docs/what-happened.md`: not a
statistic conditioned on its own baseline, and not a silent contract mismatch,
but **a compound metric hiding two cancelling defects**. A sum is not evidence
that its terms are right.

## Caveats

- The `model` arm is **one training run at one inference seed**. Training-run
  variance on these metrics is unmeasured; the char_acc SD of 0.0618 does not
  transfer. Retrieval and `gt_traced` are deterministic.
- `advance_mae` is unsigned and per-glyph; `text_width_err` is signed and
  cumulative. A font can be good on one and bad on the other, and the model is.
- The specimen is a single 63-character string at 48px. Kerning is absent from
  every traced arm, so this measures letterfitting only.
- The holdout is 46 unique GT atlases, not 50 (`check_holdout_integrity.py`).
- The tracer cannot do connected scripts at all: the six Playwrite/Jaini faces
  have `gt_traced` advance MAE above 0.20, and the figure shows the GT ATLAS row
  breaking a cursive identically to the MODEL row.

## What this changes

`atlas_to_font.py` had two deterministic defects that no atlas metric could see,
both found by rendering the artefact and looking at it: cap height 41% too small
(fixed 2026-08-14) and space 2x too wide (fixed here). That is the argument for
moving the primary metric to the finished font, independent of any model result.
