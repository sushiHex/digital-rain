# Candidate evaluation, round 1: our own base model already does it (2026-08-23)

**The first arm of the bake-off passes, and it needed no download, no new
dependency, and no licence.** FLUX.2-klein-base-4B — this project's own
Apache-2.0 base, already on disk — generates two-glyph references that read
correctly 100% of the time and clear the gate 12 out of 12.

Tool: `analysis/generate_candidate_references.py`. Data:
`research/candidate_references.json`.

## The result

12 style prompts, one generation each, `Kg` in one call, 20 steps, seed 42:

| method | n | coherence mean | median | worst | reads as `Kg` |
|---|---|---|---|---|---|
| **REAL (control)** | 50 | **0.793** | 0.734 | 2.036 | 98% |
| **flux2-klein-base** | 12 | 0.958 | 0.971 | **1.331** | **100%** |

- **100% of glyphs read as the right character**, by the font-invariant
  classifier. Above the real references' 98%.
- **12 of 12 pass the reference gate** at its 99th-percentile threshold of 1.875.
- Slightly less coherent than real font renderings (0.958 against 0.793) — the
  right direction and a sensible magnitude, not a collapse.
- The **worst** candidate (1.331) is better than the **worst real reference**
  (2.036).
- **25.4 s per image** on the shared 3090.

## Read the 100% honestly

It is not evidence that generation beats real typefaces. The real reference set
contains genuinely hard faces — the dot-grid Bitcounts, heavy distress — that
the classifier misreads, while every generated candidate is a conventional
letterform. **100% partly reflects the generated set being more ordinary, not
better.** The number that matters is that identity is not a failure mode here at
all, which was a live risk.

## What the styles actually did

Eyeballed against the twelve prompts, roughly nine or ten clearly hit the
described style. Rounded terminals, inline stripe, didone contrast, slab serifs
and the condensed grotesque all came through legibly.

Two missed. **"Stencil sans with deliberate breaks"** produced a solid face with
no breaks at all, and **"wide low-contrast monospace"** produced an ordinary
heavy sans. Interestingly **"ultra-light hairline"** was interpreted as an
*outline* rather than thin strokes — arguably a reasonable reading of the words,
and not what was asked for.

So style *adherence* is good but not reliable, and it is not what either
instrument measures. That is a separate axis and currently only eyeballed.

## Why this arm exists at all

Three rounds of research produced a shortlist (Z-Image-Turbo, Qwen-Image-Edit,
ERNIE-Image) and established that **no benchmark for inventing a coherent
typeface exists**, so the comparison had to be run rather than reasoned about.
Before downloading anything, the two complete local models were worth trying:
this one and GLM-Image int4.

It turns out the obvious candidate was the one already loaded every day.

## Two design decisions worth recording

**Both glyphs in one call, always.** The method rule from
`2026-08-21-two-styles-in-two-styles-out.md`. Every candidate here is a single
generation containing both letters, which is why coherence lands near the real
references instead of splitting.

**Malformed candidates are rejected and reported, never silently scored.** A
generated image is not guaranteed to hold one letter per half, and the gate
would return a confident number about nothing. `normalise()` checks polarity,
ink fraction and per-half balance, and gives a reason on rejection. On this run
nothing was rejected — but a method that produced 80% malformed output would
have told us something important, and hiding that would make the bake-off
measure the wrong thing.

## What is measured, and what is not

**Measured, GT-free:** coherence between the two glyphs
(`reference_gate.py`), and whether they read as `K` and `g`
(`glyph_classifier.py`).

**Not measured:**

- **Style adherence** — did it produce the style asked for? Eyeballed only.
- **The downstream atlas.** The gate *predicts* atlas coherence at ρ=0.666; it
  is not a substitute for generating the 94-glyph atlas from these references
  and scoring it. That is the real test and it has not been run.
- **Anything about the other arms.** One method is not a bake-off.

## Next

1. **GLM-Image int4** — the other complete local model, MIT, with a Glyph-ByT5
   encoder. Zero download. Also settles the ~36 min figure, which
   `CLAUDE.md` records from a bf16 run that was paging.
2. **Feed these 12 references through the generator** and score the resulting
   atlases. That closes the loop the gate only predicts.
3. Then the downloads: Z-Image-Turbo (6 GB, 3.4 s) and Qwen-Image-Edit INT4.
4. Hosted arms via `--from-dir`, which needs no client code here.
