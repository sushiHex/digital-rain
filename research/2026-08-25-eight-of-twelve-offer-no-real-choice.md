# Eight of twelve descriptions offer no real choice (2026-08-25)

**Two-thirds of the descriptions produce four candidates that the project's own
validated instrument would call the same typeface.** The picker works, and on
most prompts it has nothing to pick between.

Tool: `analysis/narrow_descriptions.py`. Data:
`research/narrow_descriptions.json`.

## The cut, and where it comes from

No new instrument and **no invented constant**. `reference_gate` rejects a
reference whose own two glyphs sit more than **1.875** apart, because at that
distance they stop reading as one typeface. For a pair of *candidates*, the same
number is the distance at which the gate would call them different styles.

> A description offers a **choice** when at least one of its candidate pairs
> reaches 1.875. A description where **no** pair does is **narrow**.

The cut is `0 of N pairs` — not a percentile, not a number fitted to these
twelve, and not a judgement about where "enough" begins.

## The result

| description | mean | max | pairs > 1.875 | |
|---|---|---|---|---|
| an ultra-light hairline sans | 0.454 | 0.778 | 0/6 | **narrow** |
| a stencil sans with deliberate breaks | 0.572 | 0.792 | 0/6 | **narrow** |
| a heavy geometric sans serif | 0.679 | 0.832 | 0/6 | **narrow** |
| a wide low-contrast monospace | 0.916 | 1.263 | 0/6 | **narrow** |
| a wedge-serif face, flared terminals | 0.897 | 1.483 | 0/6 | **narrow** |
| a high-contrast didone | 0.844 | 1.505 | 0/6 | **narrow** |
| a rounded soft sans | 0.935 | 1.673 | 0/6 | **narrow** |
| a humanist sans, open apertures | 1.034 | 1.689 | 0/6 | **narrow** |
| a condensed grotesque | 1.584 | 2.879 | 1/6 | choice |
| a chunky slab serif | 1.764 | 3.307 | 3/6 | choice |
| a heavy angular blackletter | 1.984 | 3.669 | 3/6 | choice |
| an inline face with a white stripe | 3.960 | 7.324 | 4/6 | choice |

**8 of 12 narrow.** Both recorded misses — stencil and monospace — are among
them, and so are six descriptions the generator handled *well*. Narrow is not
the same as bad: *"a heavy geometric sans serif"* came out correctly every time,
and every time much the same way.

The eye agrees on the rows already rendered: in
`viz/out/candidate_options.png` the four hairline candidates are near-identical
outlines and the four stencil candidates are near-identical solid faces, while
the inline row shows four visibly different treatments.

## What the interface should do

| verdict | behaviour |
|---|---|
| choice | show all candidates |
| **narrow** | show them, and say the model draws this style much the same way every time — **offer to reword rather than re-roll** |

That is the whole deliverable. It costs nothing to compute and it converts a
measured limitation into something a user can act on, rather than four
near-identical thumbnails and an implied promise that one of them is different.

## What this is not

- **Not calibrated against human judgement.** Nobody has labelled a candidate
  set as offering a real choice or not. The gate's own 1.875 carries exactly the
  same caveat, for the same reason, and says so.
- **A conservative cut.** 1.875 is a *rejection* threshold for one reference's
  two glyphs. Two candidates 1.5 apart may still look different to a person even
  though the gate would not call them different typefaces. So "narrow" here
  means *not different enough to clear a high bar*, and a gentler cut would
  classify fewer.
- **n=4 seeds, one backend, twelve prompts written by me.** Whether the same
  two-thirds ratio holds for a user's vocabulary is untested.

## Why it matters more than it looks

The architecture work established that the picker is sound: options differ
(ratio 0.518), two glyphs can be scored (9/11), and the atlas tracks the pick
(11/16). This says the picker is sound **and rarely load-bearing** — on 8 of 12
prompts the user is choosing between four renderings of the same idea.

That reframes where the next effort belongs. Making the *selection* better
matters less than making the *generator* produce genuinely different attempts —
which is the same conclusion the diversity note reached from the other end, and
the reason a second generator arm is worth measuring.
