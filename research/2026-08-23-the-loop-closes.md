# The loop closes: description to reference to font, end to end (2026-08-23)

> **CORRECTION, 2026-08-24.** The chain block below labels a *single* font's
> trace with the twelve-font **means**. For `"a rounded soft sans"` the real
> values are gate **0.811** and identity **0.9043**; 0.958 and 0.9379 are the arm
> means, correct in the table under them. The conclusion is unaffected — the
> chain ran and the atlas is usable — but a number that is right about a set was
> presented as though it were about a member, which is a shape this project has
> logged before. Verified against `research/candidate_references.json` and
> `research/synthetic_reference_probe.json`.
>
> Also worth recording from the same data: the **stencil** prompt — the clearest
> style *miss* in the set — scored identity **0.9787**, among the highest of the
> twelve. The instruments were not merely quiet about the failure; the one that
> spoke rewarded it.

**A style described in words produces a coherent 94-glyph typeface.** The full
product concept now runs, on two Apache-2.0 local models, with no downloads and
no licence question.

Data: `research/candidate_references.json`, `research/synthetic_reference_probe.json`.

## The chain that ran

```
"a rounded soft sans with fully rounded stroke ends"
  -> FLUX.2-klein-base-4B, 25s          -> two-glyph reference (Kg)
  -> analysis/reference_gate.py         -> coherence 0.958, passes
  -> glyph-conditioned LoRA, 62s        -> 94-glyph atlas
  -> identity 0.9379, coherence 0.3137  -> a usable font
```

Twelve style descriptions, twelve references, twelve atlases. Nothing hand-picked.

## The numbers, all ground-truth-free

| arm | n | identity | lenient | confidence | ink CV | coherence |
|---|---|---|---|---|---|---|
| **oracle** (real font references) | 50 | 0.9081 | 0.9855 | 0.868 | 0.4458 | 0.3368 |
| **external** (references invented from text) | 12 | **0.9379** | **0.9982** | **0.886** | **0.4330** | **0.3137** |

Atlases built from *invented* references beat atlases built from *real held-out
font* references on every metric available.

## That comparison is confounded, and the confound is the point

**This is not evidence that invented references are better.** The oracle arm's
50 fonts include the genuinely hard cases — dot-grid Bitcount, heavy distress,
cursive Playwrite — while all twelve invented styles came back as conventional
letterforms. **The generated set is easier**, and both instruments reward that.

The same caveat applies to the reference-level 100% identity in
`2026-08-23-candidate-evaluation-round-1.md`. Stated once more because it will
be tempting to quote the table without it.

**What the comparison does establish is the thing that was actually at risk.**
The live question was whether a reference *not rendered from a font file* would
be out of distribution and break the generator — the reference-degradation study
never found a breaking point because no tier was hard enough, and a synthetic
reference is a distribution shift rather than a degradation. It does not break.
Identity holds, coherence holds, and no arm needed a single rejected candidate.

That risk is retired. It was the main one.

## Rendered, and looked at

![Twelve fonts from twelve descriptions](../viz/out/loop_closes_words.png)

Twelve legible words, **each internally consistent** — one typeface per row, no
splitting along the K-like / g-like seam that an inconsistent reference produces.

The unusual styles survive the full chain, which is the real test of transfer:
the *ultra-light hairline* prompt produced a light outlined reference and a light
outlined atlas; the *inline stripe* prompt carried its inset stroke through to
the font.

## Style adherence is the weak axis, and nothing measures it

Eyeballed across both stages, roughly nine or ten of twelve hit the described
style. Two consistently missed:

- **"stencil sans with deliberate breaks"** — solid strokes, no breaks, at both
  the reference and the atlas stage.
- **"wide low-contrast monospace"** — an ordinary heavy sans.

And one was reinterpreted rather than failed: *"ultra-light hairline"* became an
**outline**, which is a fair reading of the words and not what was asked.

Neither the gate nor the classifier measures this. Coherence says the font hangs
together; identity says the letters are right; **nothing says the font is the
font you asked for.** That is the next missing instrument, and unlike the
previous two it needs a text-image alignment measure rather than a
self-consistency one.

## Caveats

- **n=12 against n=50**, one seed, one checkpoint. The paired design that made
  earlier comparisons trustworthy is not available here: the arms have different
  fonts, so this is two independent samples, not paired.
- The 12 style prompts are mine, not a user's, and were written knowing what the
  model is good at.
- Only one generator arm has been run. GLM-Image int4, Z-Image-Turbo and
  Qwen-Image-Edit are all still unmeasured.
- Nothing here scores the **finished OTF**. Everything above is atlas-space, and
  `2026-08-20-the-atlas-format-is-the-common-cause.md` established that 74% of
  the finished font's error is the pipeline's invented constants regardless.

## Where this leaves the project

The concept is no longer hypothetical. It runs, locally, on permissively
licensed weights, at about 90 seconds per font end to end.

The remaining gaps are ranked honestly:

1. **A style-adherence measure.** The one axis with no instrument.
2. **The other generator arms** — three candidates, all cheap now the harness
   exists.
3. **The finished font**, which the atlas metrics cannot see.
