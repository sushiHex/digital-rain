# Hand it a stencil and it propagates one (2026-08-28)

**The stencil problem has an answer, and it was never a model problem.** No
text-to-image model will *invent* a stencil. Hand the glyph-conditioned LoRA a
reference that already carries one and it propagates the treatment to the
ninety-two letters nobody supplied.

Tool: `analysis/synthesised_reference_probe.py`, committed **before** it ran.
Data: `research/synthesised_reference_probe.json`. Figure:
`viz/synthesised_reference.py`.

## What every previous attempt had in common

| attempt | mechanism | result |
|---|---|---|
| FLUX.2-klein-base-4B, 4 seeds | text-to-image | solid |
| Z-Image-Turbo, 4 seeds | text-to-image | solid |
| Z-Image img2img, 4 strengths × 2 seeds | image-to-image | solid |

Sixteen images, three mechanisms, no break anywhere. All of them asked a
**general image model to draw a rare typographic treatment from a
description**.

This repository never needed one drawn. `synthesize_rare_attributes.py` already
**constructs** stencil glyphs geometrically — that is how it builds its training
data. The untested question was whether the LoRA can **transfer** a treatment it
is *handed*.

## The result

Three arms, one seed, so they differ by the reference only. Scored over the
**92 cells excluding `K` and `g`** — the model is conditioned to copy those two,
so including them would measure the conditioning rather than the transfer.

| arm | parts | holes | vs plain |
|---|---|---|---|
| plain | 0.736 | 0.203 | — |
| **inline** (positive control) | 0.754 | **1.332** | parts +0.018, holes **+1.129** |
| **stencil** | **2.148** | **0.015** | parts **+1.412**, holes **−0.188** |

**Both arms moved in their own predicted directions, and only in those.** That
is the part that makes this a transfer rather than a reaction:

- **Stencil** nearly tripled `parts` and collapsed `holes` to near zero — the
  signature established on synthetic data, where breaking bands cut the counters
  **open**.
- **Inline** left `parts` flat and multiplied `holes` sixfold — the mirror
  image.

A model that merely reacted to *any* altered reference would have moved both
arms the same way. These moved orthogonally, each toward its own treatment.

By eye the primary is unambiguous: "Amber" comes back solid, hollow, and broken
across the three arms, and none of those five letters was given to the model.

## Why the positive control earned its place, and what it cost

Inline is the control because the generator carried an inline stripe through the
whole chain unaided on 2026-08-23. Without it, a stencil null would have been
uninterpretable — did the model refuse, or does it ignore reference topology in
general?

**It was nearly inert, and that was caught before any GPU time was spent.** The
first inline reference changed **6.58%** of the ink where removing each stroke's
spine should take roughly half. My first diagnosis — apply the transform per
glyph rather than across both — was **wrong**; it moved the number to 7.07%.

The real cause: `_inline` thresholds against a **global** `dist.max()`. That is
correct in a 106×160 atlas cell where a glyph is ~100px and roughly uniform. On
a 1024px reference the thick junction of a `K` sets the peak and the stems fall
below the threshold entirely.

**The shared transform was left alone on purpose** — the 10/11 classifier result
was trained on its output, so changing it would invalidate that. The probe uses
a local-ridge variant instead (a maximum filter over a few stroke widths), and
says plainly that this is the same *idea* at a different scale, **not the same
operator**. Inline then changed 21.03% and read as an inline treatment.

That iteration is **pre-data** — an instrument repaired before measuring, not a
result reinterpreted after seeing one. The distinction is the whole difference
between this and the style-adherence retraction.

## Caveats, registered in advance

- **The band eraser makes grid-aligned gaps**; a designer breaks strokes at
  junctions. The reference is therefore out of distribution in a *new* way, even
  though synthetic references were already shown not to break the generator.
- **The corpus contains stencil families**, so this partly reflects training
  exposure rather than pure generalisation. That does not weaken it as a product
  answer, but it is not evidence the LoRA would propagate a treatment it has
  never seen.
- **One source font, one seed, three atlases.** The effect is large and the
  directions are orthogonal, which is why it is reported without a p-value
  rather than with a fragile one.
- **Nothing here scores the finished OTF.** This is atlas space, and 74% of the
  finished font's letterfitting error belongs to the pipeline regardless.

## What this changes

The product answer for rare treatments is **synthesise the reference, do not
generate it**. Zero new weights, zero download, and it sidesteps the generator
entirely for exactly the attributes the generator cannot produce.

It also reframes three days of negative results. The stencil failure was never
evidence that the *system* cannot make a stencil font — only that the
**reference-drawing stage** cannot. That stage is the one part of the pipeline
this repository can replace with geometry.

Two consequences worth following:

1. **The picker gains a synthetic arm.** When a description names a treatment
   the generator misses, offer a constructed reference beside the drawn ones.
   The narrow-description advisory already identifies when that is needed.
2. **The rare-attribute vocabulary is now bounded by what can be CONSTRUCTED,
   not by what a model will draw** — a much larger and more tractable set.
