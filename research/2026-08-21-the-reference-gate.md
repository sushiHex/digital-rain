# The reference gate: catch it before generating (2026-08-21)

**The first piece of product rather than measurement.** Score the two reference
glyphs for mutual style agreement, reject before spending a generation. It
separates at **r=0.678** and, more importantly, **predicts the atlas it would
have produced at ρ=+0.666**.

Tool: `analysis/reference_gate.py`. Data:
`research/reference_gate_validation.json`.

## A correction to my own framing

I described the coherence work as "one measure, two uses". That was loose, and
the difference is the whole design:

| | input | statistic |
|---|---|---|
| `style_coherence.py` | 94 atlas cells | **dispersion** |
| `reference_gate.py` | **2** glyphs | **distance** between two style vectors |

Dispersion over n=2 is meaningless. They share features and nothing else, which
is why the gate is its own module.

## Why a gate is possible at all

The model transfers whatever style it is given. Two reference glyphs that
disagree produce an atlas split along the K-like / g-like seam — a light `H`
then bold `amburg` (`2026-08-21-two-styles-in-two-styles-out.md`). Identity
scored that **0.9034 against a coherent control's 0.8910**, above it, so nothing
downstream catches it.

But the reference is the *cause*. Reading it costs milliseconds.

## The result

Everything needed was already on disk: 50 oracle and 50 mixed references, and
the atlas dispersion each produced.

| | oracle | mixed |
|---|---|---|
| reference distance | 0.793 | 1.842 |

```
separates the arms   p=0.0000   r=0.678   n=50
predicts the atlas   rho=+0.666 p=0.0000  n=100
```

**Prediction is what makes it a gate rather than a description.** Separation
alone would only say the two label groups differ; prediction says the reference
score tells you what the atlas will look like *before you generate it*.

Note the gate's signal is **stronger than the atlas measure it protects**
(r=0.678 against 0.435). That is the expected direction: the reference is the
cause and the atlas a noisy downstream effect of it.

## Operating points

Cut from the coherent references' own spread:

| percentile | threshold | catches mixed | rejects coherent |
|---|---|---|---|
| 99 | 1.875 | 44% | 2% |
| 95 | 1.626 | 48% | 6% |
| **90** | **1.328** | **54%** | **10%** |
| 80 | 1.057 | 64% | 20% |
| 75 | 0.971 | 64% | 26% |

Two things this table is not.

**It is provisional by construction.** The thresholds are cut from the coherent
spread, not from references a human judged unacceptable. That calibration set
does not exist, and building it is a human-judgment task, not a measurement one.

**Recall is a floor, not a ceiling.** The `mixed` label includes *benign*
pairings — sans meeting sans — which produce a perfectly usable font and
**should** pass. A perfect gate would not catch 100% of this label, so "54%" is
not 46% of failures escaping.

## The domain trap, which was load-bearing

The per-character statistics are fitted on **106×160 atlas cells**. A reference
column is **640×1280**. The features are mostly scale-normalised — `stroke`
divides by glyph height, `slant` and `fill` are ratios — but the distance
transform and the connected-component count behave differently at six times the
resolution.

So each reference glyph is trimmed to its ink and rescaled to atlas-cell
proportions before features are taken. Skipping that step compares numbers from
two different domains and would have produced a confident, meaningless score.
`tests/test_reference_gate.py` pins it.

## What it gives a user

The score reports **which feature disagrees**, so a rejection is actionable
rather than a refusal: `stroke` means the two glyphs differ in weight, `slant`
that one is italic, `parts` that one is dotted or inline and the other solid.
That maps directly onto a re-roll instruction.

## Caveats

- **Validated against constructed mismatches**, not real generated references.
  A text-to-image model trying to be consistent fails more subtly.
- The `chars` argument must match what the image really contains, because each
  glyph is z-scored against its own character. The shipped references render
  `Kg` while the checkpoints' conditioning records `Rg` — the documented
  train/eval mismatch, immaterial to generation and decisive here.
- One checkpoint, one seed behind the atlas scores it is validated against.
- Two glyphs is a thin sample. The gate sees weight, slant, fill and topology;
  it does not see anything those four features miss.
