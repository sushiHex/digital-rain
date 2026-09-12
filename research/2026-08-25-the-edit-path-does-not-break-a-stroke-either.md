# The edit path does not break a stroke either (2026-08-25)

**No break at any strength.** Rendering a neutral `Kg` and asking Z-Image to
restyle it into *"a stencil sans with deliberate breaks"* fails the same way
text-to-image did — and the sweep shows *why* the middle ground people hope for
does not exist here.

Tool: `analysis/edit_path_probe.py`, committed **before** it ran. Data:
`research/edit_path_probe.json`.

## Why this was the only untried mechanism

Eight seeds across two independent text-to-image models produce no break
([note](2026-08-25-the-second-arm-fails-the-same-way.md)), which relocated the
failure from the model to the **task**: asking a general image model to *draw* a
rare typographic treatment from a description.

The edit path asks a different question of the same weights. Start from a real
letterform and say *"make this stencilled"*. Both glyphs get one transformation
in one pass, so consistency is structural rather than hoped-for — the argument
`2026-08-23-restyle-not-generate-the-reference.md` made and nothing had tested.

## The sweep, and the tension it resolves

`strength` controls how far the output may leave the source. Low preserves the
letterform; high approaches plain text-to-image. The useful setting would be a
middle where the letterform survives *and* the strokes break.

Measured as mean absolute difference from the 0.30 output, over 8 images:

| strength | change from source | parts | holes |
|---|---|---|---|
| source | — | 0.693 | 0.347 |
| 0.30 | ~0 | 0.693 | 0.347 |
| 0.50 | 0.3 / 255 | 0.693 | 0.347 |
| 0.70 | 1.5 / 255 | 0.693 | 0.347 |
| **0.90** | **~50 / 255** | 0.896 · 1.040 | 0.347 |

**There is no middle.** Up to 0.70 the model returns the source essentially
untouched — the topology numbers are identical to three decimals because the
images are. At 0.90 it finally changes the letterform, and what it produces is a
*heavier sans*, still solid.

`parts` does rise at 0.90 (0.693 → 0.896, 1.040), which is the stencil
direction — but `holes` does not fall, and the stencil signature is **both**.
The eye agrees with the arithmetic: those two images are bolder, not broken.

## What this closes, stated precisely

**It closes image-to-image on a text-to-image model.** Both directions on the
same weights decline to break a stroke, and the strength axis offers no setting
where structure survives and topology changes.

**It does NOT close edit models.** Z-Image-Turbo is a text-to-image model with
an img2img pipeline attached, not a purpose-built editor. Qwen-Image-Edit-2511
is edit-native, Apache-2.0, and fits at INT4 — and it remains untested. The
distinction matters and this note should not be cited as ruling it out.

That said, the prior has moved. Three independent attempts — two generators
drawing from text, one restyling from an image — all produce solid faces. A
fourth attempt should be justified by something more than "it is a different
model".

## Caveats

- **One description, one source font, 8 images.** The stencil prompt only.
- **8 inference steps**, because Turbo is distilled for it. At strength 0.30
  that is ~2 denoising steps, which may be too few to change anything by
  construction rather than by unwillingness — a higher step count with low
  strength is untested and is the one cheap thing left in this direction.
- **`normalise()` rescales outputs to 1280²** while the source is 1024², which
  is why the first comparison I attempted returned nothing. Outputs are
  compared to each other, not to the source.

## Where this leaves the stencil problem

Unsolved, and better understood. It is not our LoRA, not the base model, and not
the text-versus-image framing. The remaining candidates, in order of prior:

1. **A purpose-built edit model** (Qwen-Image-Edit-2511 INT4).
2. **Synthesis at the reference stage** — the project can already *make* a
   stencil `Kg` geometrically (`synthesize_rare_attributes.py` does exactly this
   to build training data). Feeding a synthesised stencil reference into the
   glyph model is untested, needs no new weights, and sidesteps the generator
   entirely for the rare treatments.

The second is cheaper and was not on the plan. It is now the more interesting
one, because the thing the generator cannot draw is precisely the thing this
repository can already construct.
