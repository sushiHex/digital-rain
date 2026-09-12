# How to generate the reference (2026-08-22)

Research, not a build. The product concept needs the two reference glyphs to
come from a description rather than from an existing font. This is what the
options are, what the project already knows about them, and what to test.

## The organising principle, which comes from our own data

**Generate both glyphs in ONE call. Never two.**

`2026-08-21-two-styles-in-two-styles-out.md` established the mechanism: the
model transfers whatever style it is given, so two glyphs that disagree produce
an atlas split along the K-like / g-like seam. Consistency is therefore a
property of *how the reference is produced*, not of how good the generator is.

Two independent generations of `K` and `g` have no mechanism forcing agreement.
One generation of an image containing both does — the same thing that makes a
model draw a coherent scene. The reference format is already a single
1280×1280 image with both glyphs, so this costs nothing.

External work agrees from the other direction. A 2026 comparison of frontier
text-in-image models finds they "**can't reconcile conflicting construction
logics to invent a coherent system**" — the same failure, in hosted models that
are far larger than anything runnable here.

## Ranked options

### 1. VecGlypher — purpose-built for exactly this

[CVPR 2026](https://xk-huang.github.io/VecGlypher/). A multimodal language model
that emits **editable SVG glyph outlines directly from a natural-language style
prompt**, autoregressively, in one pass with no raster-to-vector step. Trained
on 39K Envato fonts plus 2.5K tagged Google Fonts.

Why it fits:

- Text prompt → letterforms is its actual task, not a side effect.
- **Multi-character SEP syntax generates several glyphs in one call** — the
  consistency mechanism above, for free (`docs/archive/PROMPT.md`).
- Vector output. Our pipeline's own measurements say the raster→trace path costs
  a median 3.5% of ink and 74% of the finished font's letterfitting error
  (`2026-08-20-the-atlas-format-is-the-common-cause.md`); a reference that never
  rasterises avoids importing that.
- Q (quadratic) commands map straight onto `TTGlyphPen`.

**This project already rejected it — for a different job.** The archive records
a whole service built on `fal-ai VecGlypher → SVG → fontTools → WOFF2`, pivoted
away from in favour of FLUX.2 + Ref2Font. That comparison was *whole-font
generation*. Producing two reference glyphs from a description is the job it was
designed for and the one it was never evaluated on here.

**Unconfirmed and decisive:** the GitHub repo is Apache-2.0 and carries a
HuggingFace badge, but I could not confirm that **weights are released for local
inference**, and the archive's access path was hosted (fal-ai). The archive also
warns that as of March 2026 every R-ACC/FID/speed number was self-reported with
zero third-party reproduction. Check the weights before planning around it.

### 2. GLM-Image int4 — already on this disk, and our objection to it inverts

`Intel/GLM-Image-int4-AutoRound` is **already in the local HF cache**. MIT
licence. It ships a native **Glyph-ByT5 encoder** — character-level conditioning,
conceptually the same idea this project built by hand.

`2026-07-31-successor-model-survey.md` rejected it, on the grounds that a glyph
encoder optimised for legibility "plausibly pushes output toward **canonical**
letterforms, which is exactly the wrong bias for Fascinate Inline or a dot-grid
face."

**That objection was about reproducing an existing unusual typeface. It inverts
here.** Inventing a plausible new face from a description does not need to
recover a specific odd letterform; a bias toward canonical, legible shapes is
mostly harmless and arguably wanted.

**Correct the speed figure before dismissing it.** `CLAUDE.md` records "~36
min/image". The survey's own measurement says that was **bf16 sitting at 23.7 GB
of 24.5 — "almost certainly paging"**. That is the speed of a model that does
not fit, not the model's speed. The int4 build exists precisely to fit, and is
already downloaded. Its real throughput is unmeasured.

### 3. FLUX.1-dev — the fast local baseline

Also already on disk. A general text-to-image model, weakest of the three on
letterform construction, but it is the cheap control every other option should
have to beat. Generate both glyphs in one image.

### 4. Parametric / variable-font sampling — consistent by construction, and a licensing trap

Sampling a variable font's axes gives two glyphs that are guaranteed
consistent, with no model at all. It is also the option to be most careful with:
the output lives inside an existing typeface's design space, which walks back
into the derivative-work problem the product reframing was supposed to escape
(`2026-07-27-ofl-derivative-work-constraint.md`). Useful as a control arm, not
as the product.

### 5. A local LLM straight to SVG — nearly free to try

`hermes-4.3-36b` and `qwen3.5:9b` are installed. Geometry quality will probably
be poor, but the probe costs minutes and the failure mode is informative.

## The evaluation harness already exists

This is the part worth noticing. **`analysis/reference_gate.py` scores exactly
what these methods must produce**, with no ground truth and no human judgement:

```
separates coherent from mixed   p=0.0000  r=0.678
predicts the atlas it produces  rho=+0.666
```

So candidate references from each method can be scored quantitatively, against
the 50 real references as the coherent control. `analysis/build_synthetic_references.py --external-dir`
already accepts a directory of generated PNGs. That is a method bake-off with a
pre-existing, validated instrument — which is not a position this project has
often been in.

## Recommended order

1. **Measure GLM-Image int4's real speed.** It is on disk, MIT, has a glyph
   encoder, and the figure currently in `CLAUDE.md` describes a paging bf16 run.
   One image settles whether it is viable.
2. **Confirm whether VecGlypher's weights are locally runnable.** If they are, it
   is the strongest candidate on task fit; if they are not, it is a hosted
   dependency and a different product decision.
3. **Run the bake-off through the reference gate**, with FLUX.1-dev as the
   control and the 50 real references as the coherent baseline.

Whatever wins, generate both glyphs in one call.

## Caveats

- Every ranking above is on *task fit and availability*, not on measured output
  quality. Nothing here has been run.
- The gate is validated against **constructed** mismatches. Real generated
  references are a different distribution, and scoring them is itself the first
  real test of the gate.
- Frontier hosted models (Ideogram v3, GPT Image 2) reportedly lead on
  typography but are not local, which the concept requires.

Sources: [VecGlypher (CVPR 2026)](https://xk-huang.github.io/VecGlypher/) ·
[VecGlypher paper](https://arxiv.org/pdf/2602.21461) ·
[VecGlypher code](https://github.com/xk-huang/VecGlypher) ·
[Best AI text-in-image models 2026](https://ropewalk.ai/blog/best-ai-text-in-image-models-2026) ·
[DeepVecFont-v2](https://arxiv.org/pdf/2303.14585)
