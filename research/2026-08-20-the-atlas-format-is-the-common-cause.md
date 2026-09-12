# Three finished-font defects, one cause: the atlas format discards what a font needs (2026-08-20)

Scoring the finished font found three defects in eight days. They look
unrelated. They are the same defect three times.

| defect | the builder had to invent | why |
|---|---|---|
| space **2× too wide** | the space advance | the space has no cell — it is blank by definition |
| sidebearings **all equal** | one constant for every glyph | `build_dataset` centres each glyph in its cell |
| cap height **assumed** | absolute em scale | each font is rendered at a size that *fits* the cell |

Every one of them is a number the atlas does not carry, so `atlas_to_font` has
to make it up. And every one is invisible to every metric in this project,
because cell-space comparison never sees advances, sidebearings, or em scale.

That is not three bugs. It is one design property with three symptoms, and it
sets the agenda for anything that comes next.

## It also explains the failure of the fix that should have worked

`research/2026-08-19-the-sidebearing-prior-that-did-not-pay.md` records a
correct per-character letterfitting model that gained 0.3% and made text width
6 points worse. The reason is now clear: **it corrected one invented constant
while the other two stayed wrong**, and the constant it replaced had been
absorbing their error. Fixing an invented constant in isolation is a regression
whenever another one is compensating for it.

## The cap-height constant, measured — and it is already right

`TARGET_CAP_EM = 0.70` was set as "typical cap height for a text face", never
measured. `analysis/fit_cap_height.py` measures it from the yMax of flat-topped
capitals (`HEFTILNM` — round caps overshoot the cap line and would bias it up),
over 975 licence-clean corpus fonts with holdout superfamilies excluded:

| | corpus (n=975) | holdout (n=50) |
|---|---|---|
| median | **0.7000** | 0.7105 |
| mean | 0.6988 | 0.7358 |
| SD | 0.0909 | 0.0993 |
| range | 0.273 – 1.453 | 0.600 – 1.035 |

**The constant is exactly the corpus median. Do not change it.** An earlier
reading of this put 38% of the ink deficit on the constant being too low; that
came from the holdout's 0.7105 median, and the corpus says 0.7000. Refitting to
the holdout would have been leakage and would have made the constant worse.

## What the residual actually is

Traced ink is a median 0.9606 of real ink on holdout letters. Scaling applies
**per font** — each font's widths are multiplied by `0.70 / that font's cap` —
so the right statistic is the mean of that ratio, not the ratio of the medians:

```
0.70 / cap, over the 50 holdout fonts
  mean    0.9655     <- accounts for 88% of the 0.9606 ink deficit
  median  0.9853
  sd      0.1060     <- larger than the bias itself
```

So the deficit is **almost entirely cap-height scaling**, and almost none of it
is tracing loss — which also kills the earlier hypothesis that the tracer's
morphological `binary_opening` was eroding glyphs. Tested directly: removing the
opening moves traced/real ink from 0.9606 to 0.9612, and 8× upscale gives
0.9613. Neither matters.

**The SD is the finding.** At 0.1060 it is three times the mean bias, and no
constant can touch it. A fit-to-cell atlas does not carry per-font cap height,
so per-font size error is not recoverable — in exactly the same way per-glyph
sidebearings are not.

## A fourth way the 50-font holdout is unrepresentative

The holdout's mean cap height is 0.7358 against the corpus mean of 0.6988: a
difference of +0.0358 em at **2.52 SE, p=0.015**. Its distribution is
right-skewed where the corpus is symmetric.

That joins the list in `docs/benchmark-v2-spec.md`: 46 unique atlases rather
than 50, two fonts unscoreable by construction, 32 of 50 sharing a superfamily
with training, and now systematically taller caps than the corpus it is meant to
generalise from.

## What this means for a next pass

**An atlas format v2 has to carry per-glyph advance and the font's em scale.**
Not as a metric change — as a data-format change, which means a retrain. Until
then:

- every finished-font metric has a floor set by three invented constants;
- fixing any one of them in isolation can regress the others;
- and `gt_traced`, the ceiling with model error exactly zero, will keep sitting
  at advance MAE 0.1168 no matter how good the generator becomes.

That last point is the one worth carrying forward. **The pipeline's own error is
74% of the finished font's total**, so the model is not the binding constraint on
the artefact a user receives, and no amount of model work will make it one.

## Tools

- `analysis/fit_cap_height.py` — the measurement above, with the same
  holdout-superfamily and licence guards as the sidebearing fitter.
- `research/cap_height.json` — the distribution.
- `analysis/score_finished_font.py` — where all three defects surfaced.
