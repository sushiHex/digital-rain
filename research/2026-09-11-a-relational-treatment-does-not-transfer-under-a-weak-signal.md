# A relational treatment does not transfer — under a weak signal

**Pre-registered** in `analysis/relational_transfer_probe.py` at `f9b4c93`,
amended (before running) at `092cb5e`, run unmodified at `092cb5e` on
2026-09-11. Record: `research/relational_transfer_probe.json`. Figure:
`viz/out/relational_transfer.png`.

## The question

The LoRA propagates a **stencil** it is handed: give it a two-glyph reference
with the bands erased and all ninety-two other letters come back banded
(`2026-08-28-hand-it-a-stencil-and-it-propagates-one.md`). Stencil is a *local*
treatment — every stroke is altered, and each glyph carries the whole
instruction alone. **Monospace is relational**: it is a statement about the
set, that all letters share a width, and two glyphs can only hint at it by
agreeing with each other. Nothing about the stencil result implied the model
would generalise "these two match" into "make all ninety-four match", which is
why it was asked separately. Monospace is also the other description recorded
as missed on 2026-08-23, so a positive result would have extended the
constructed-reference answer to both recorded misses.

## What was registered

Three arms from one neutral source (ABeeZee), one seed (42), twenty steps, the
`checkpoint-5000` of `training_glyph_4b_r32_5000`: `plain`, `stencil` (the
positive control, which must reproduce parts UP and holes DOWN or the arms say
nothing), and `monospace` (both reference glyphs rescaled horizontally to the
same ink width). Primary statistic: ink-width CV over the 92 cells *excluding*
`K` and `g`, since the model is conditioned to copy those two. Bar: the
monospace arm's CV must fall below the plain arm's; real monospace faces sit at
0.209–0.240 and real proportional faces at 0.326–0.394
(`research/advance_survives_atlas.json`).

**The amendment, committed before the run.** The reference pair is fixed at
`Kg` by the conditioning, and in ABeeZee those two glyphs are already nearly
the same width: 231 and 214 px, a ratio of 1.079. Equalising them to 222/222
moves 48% of the ink pixels but removes very little *disagreement*, because
there was little to remove. So a positive result would stand as registered,
while a failure is the weaker claim "not transferred under a weak signal" and
cannot separate "relational treatments do not propagate" from "this reference
pair could not carry the signal".

## Result

| arm | ink-width CV | parts | holes |
|---|---|---|---|
| plain | 0.402 | 0.736 | 0.203 |
| stencil (control) | 0.393 | **2.148** | **0.015** |
| monospace | **0.403** | 0.736 | 0.207 |

Monospace: CV 0.402 → 0.403, +0.001. **FAILED**, as the script printed.
Control: parts +1.412, holes −0.188 — the stencil signature reproduced in
full, so the pipeline was working and the arms are comparable.

The monospace atlas is not merely un-monospaced; it is the plain atlas. Mean
absolute pixel difference between the two, over the whole 1280×1280 canvas, is
0.739 of 255. The `i`, `l` and `j` are bare and narrow, the `m` and `w` are as
wide as ever, and `parts` is bit-identical between the two arms. The model saw
a reference whose two glyphs had been made the same width and drew the same
proportional face it draws for the untouched reference.

## What this does and does not say

**It says**: under the only relational cue a `Kg` reference can carry, the
LoRA changed nothing. The stencil result therefore does not generalise by
itself; "hand it a treatment and it propagates" is established for a local
treatment and, so far, for nothing else.

**It does not say** that relational treatments cannot propagate. The signal
was weak by construction — declared before the run, not discovered after — and
the pair was `Kg`. A proper test needs a reference whose glyphs naturally
disagree in width by a lot, so that equalising them is a large relational
change. That makes the question **closed under `Kg`**, not answered in general.

> **Correction after review, 2026-09-11.** The first draft of this section
> said the architecture *fixes* the pair at `Kg` and that a stronger pair
> would need retraining. Both were wrong, and the project's own record says
> so: the checkpoint's `conditioning.json` records `reference_chars: "Rg"`,
> the training references were rendered as `Rg`, and the evaluation and
> product path use `Kg` by convention — a mismatch measured immaterial to
> generation on 2026-07-28 (`Rg` vs `Kg`, p=0.625). So `Kg` is a convention,
> not a constraint, and a width-disparate pair such as `Mi` is a cheap
> follow-up on this same checkpoint. It is registered separately (issue #21 on
> the working repository), not folded into this note, because the bar for it
> is written after this result was seen. Also noted by the same review and
> fixed in the script after the run, without changing any number: the
> monospace verdict is now assigned only after the control passes, as the
> registration always required, and cached atlases carry a manifest of the
> parameters that made them so a re-run cannot mislabel them. The record was
> regenerated with `--score-only` after the fix; every value is identical.

**A side observation, not a claim.** The plain arm's CV of 0.402 sits *above*
the real proportional band (0.326–0.394). Generated atlases from a neutral
reference disperse their ink widths more than real proportional fonts do. One
font, one seed; recorded because it is the kind of number that later turns out
to matter.

## Consequence for the product

`monospace` does **not** join the constructed-reference vocabulary.
`analysis/constructed_reference.py` detects only the three treatments the
probe of 2026-08-28 showed propagate; the monospace transform stays in
`analysis/synthesise_transforms.py` as the record of what was tried, marked as
such. For a user who asks for a monospace, the picker's honest answer remains
what it was on 2026-08-23: the generator does not draw one and the constructor
cannot make one.

## Cost

Three atlases at 70 s each, 4 min 36 s wall, 21.8 GB free at launch on the
shared card, nothing evicted.
