# Two glyphs are enough, barely — the picker can select at the reference stage (2026-08-25)

**9 of 11, p = 0.0327, exactly at the pre-registered bar.** The adherence
measure still works when it sees only the two glyphs a user is actually shown,
so selection can happen at the cheap stage. It is a fragile pass and the note
says so.

Tool: `analysis/reference_stage_adherence.py`, committed at `9608419` **before**
execution. Data: `research/reference_stage_adherence.json`.

## Why this was blocking

The product decision is that the interface shows several candidates for one
description and lets the user pick and iterate. That makes the arithmetic
matter:

| select at | cost for 4 options | wasted |
|---|---|---|
| **reference stage** | 4 × 25 s = 100 s, then one atlas at 62 s | nothing |
| atlas stage | 4 × 62 s = 248 s | three atlases |

But `synthesize_rare_attributes.py` aggregates over 94 cells and refuses fewer
than 40. **A reference has two.** Nothing established that two glyphs carry
enough, and building an interface on that assumption would have put the whole
design on an unmeasured premise.

## The trap that had to be avoided first

`reference_gate.glyph_cells` crops each glyph to its ink and **rescales it to a
fixed height** before centring. An atlas cell is *not* rescaled — it is drawn at
the atlas's own size, baseline-aligned, so `K` is cap-height and `g` is
x-height plus a descender.

Train on raw atlas cells, test on reference images, and the two sides disagree
about what a glyph's height means. That silently changes `width_cv` and every
feature that compares the two glyphs. So both sides go through one
normalisation: `normalise_like_reference` mirrors `glyph_cells` and is applied
to the **training** cells too.

This repository has shipped exactly this bug before — `render_atlas` and
`render_reference` had different variable-font defaults and mismatched ~110 of
177 additions to `dataset_v3`. `tests/test_reference_stage_adherence.py` pins
the mirror, including a test that fails if the docstring stops declaring it a
copy.

## The result

Same 11 real superfamilies, scored from their `K` and `g` cells alone:

```
9/11 correct    exact binomial p = 0.0327    BAR >=9/11 and p<0.05: PASSED
```

| | 94 cells | 2 glyphs |
|---|---|---|
| correct | 10/11 | **9/11** |
| p | 0.0059 | **0.0327** |

**Exactly one more error, and it lands on the hardest row.**
`BigShouldersInline` — whose stencil sibling the measure still gets right — now
reads as stencil at P=0.770. That is the only pair in the set where the typeface
is held constant, so it is the one case where the measure must separate
*treatment* from *face*. With 94 cells it did. With `K` and `g` it does not.

`FascinateInline` fails again; it also failed at 94 cells.

**9/11 is the bar, not a margin.** One further error and this reads p=0.113 and
fails. Do not quote this as a comfortable pass.

## What it licenses, and what it does not

**Licenses:** selecting candidates at the reference stage. Four options and one
atlas is ~2.7 minutes end to end, against 90 s for the current single-shot path
— a real cost, and far below the 4-minute atlas-stage alternative.

**Does not license:** treating the reference score as equivalent to the atlas
score. The measure is demonstrably weaker at n=2, and it is weaker precisely
where treatment and typeface have to be told apart.

**Second use of these 11 faces**, recorded in the registration rather than
discovered later. The first was `synthesize_rare_attributes.py`. Reusing a
held-out set across models erodes its independence, and a **third** use would
make it a validation set rather than a test set.

## Still open, and blocked on the shared GPU

The two remaining steps both need generation, and the 3090 filled with other
work mid-run — throughput fell from **1.3 s/step to 281 s/step**, which is 94
minutes per image. The run was stopped rather than allowed to contend, and a
VRAM-gated retry is armed. Never evict; wait.

1. **Within-prompt diversity.** Do four seeds of one description differ enough
   to constitute a choice? `analysis/within_prompt_diversity.py` is registered
   and unrun. A collapse would be blocking for the whole design.
2. **Reference → atlas style transfer.** Does the atlas keep the style of the
   reference the user picked? Encouraging but unmeasured: the hairline and
   inline-stripe prompts both carried through the full chain on 2026-08-23.

## Status of the three axes

| axis | instrument | state |
|---|---|---|
| coherence | `reference_gate.py`, `style_coherence.py` | validated, and valid at n=2 by construction |
| identity | `glyph_classifier.py` | validated |
| adherence | `synthesize_rare_attributes.py`, `reference_stage_adherence.py` | **partial** — 4 treatments; 10/11 on atlases, 9/11 on two glyphs; uncalibrated |
