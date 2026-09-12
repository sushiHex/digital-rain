# A break is not a stripe — the first instrument that reads an adherence failure (2026-08-25)

**10 of 11 real held-out typefaces classified correctly, p = 0.0059, against a
bar committed before the run.** And on the twelve generated atlases it recovers,
unprompted, all three judgments the eye recorded two days before the instrument
existed — including calling the stencil request **solid**.

Tool: `analysis/synthesize_rare_attributes.py`, committed at `e28c47f` **before**
execution. Data: `research/synthesize_rare_attributes.json`.

## The problem this fixes

Yesterday's transfer test passed its primary and its descriptive column killed
the interpretation: **the stencil model's favourite generated atlas was the
inline one**, the outline second
([note](2026-08-24-the-transfer-test-passed-and-that-is-not-the-finding.md)).
`parts` counts connected components, so it reads *"in many pieces"* — and a
break, a stripe and a hollow contour are all many pieces.

More training data cannot fix a feature that cannot express the difference. The
difference is topological, and one `binary_fill_holes` away. Measured on a single
face, all four variants synthesised from it:

| class | parts | holes | hole_area |
|---|---|---|---|
| solid | 0.735 | 0.190 | 0.087 |
| **stencil** | **1.458** | **0.007** | 0.000 |
| **inline** | 0.735 | **2.169** | 0.196 |
| **outline** | 0.840 | 0.910 | **0.515** |

Components alone conflate all three. Components *versus* holes separate them.
The stencil signature is the interesting one and was not predicted: erasing
bands cuts the counters **open**, so a stencil face has *fewer* holes than a
solid one, not more.

**Two things make this a feature addition rather than a goalpost move.** The
negatives are each other — every class is synthesised from the *same* source
faces, so the typeface is controlled for and only the treatment is left to
learn. And the primary runs on real faces the model never sees. Yesterday I
refused to add a terminal-shape feature to rescue serif-vs-sans, because that
would have been a new feature set on the *same failed data*; this is a new
registration on data held out from it.

## The primary: 10 of 11

Collapsed to **superfamily**, because `BigShouldersStencil*` and
`BigShouldersInline*` are one typeface and three Sairas are another — the census
counted 10 and 10 "families"; there are really 5 and 6.

| superfamily | true | predicted | P(stencil) | P(inline) |
|---|---|---|---|---|
| allerta | stencil | **stencil** | 0.688 | 0.001 |
| **bigshoulders** | **stencil** | **stencil** | 0.288 | 0.024 |
| **bigshoulders** | **inline** | **inline** | 0.050 | 0.809 |
| saira | stencil | **stencil** | 0.829 | 0.016 |
| sirin | stencil | **stencil** | 0.741 | 0.004 |
| stardos | stencil | **stencil** | 0.438 | 0.000 |
| alumnisans | inline | **inline** | 0.045 | 0.177 |
| bungee | inline | **inline** | 0.008 | 0.151 |
| runicsans | inline | **inline** | 0.051 | 0.333 |
| ostrichsans | inline | **inline** | 0.006 | 0.298 |
| **fascinate** | inline | ✗ stencil | 0.061 | 0.000 |

```
10/11 correct    exact binomial p = 0.0059    BAR >=9/11 and p<0.05: PASSED
```

**BigShoulders is correct on both sides.** The same underlying typeface, once
with a stencil treatment and once with an inline treatment, and the model
separates them. That pair was kept deliberately because it is the only one in
the set where the typeface is held constant, and it is the strongest single row
in the table.

The one failure, `FascinateInline`, is decided between two near-zero
probabilities (0.061 against 0.000). The model is not confidently wrong about
it; it has no opinion.

## The caveat, and it is large

**Unrestricted 4-way accuracy is 4 of 11.** Seven real faces read as `solid`
(or, once, `outline`) when the model is allowed to pick any class:

| | registered 2-way | unrestricted 4-way |
|---|---|---|
| correct | **10/11** | **4/11** |

The registered primary took the larger of P(stencil) and P(inline), which is the
question that broke yesterday and the one the product asks once a style has been
requested. But the gap between 10/11 and 4/11 says plainly what the measure is:
**it ranks and it does not calibrate.** A real inline face gets P(inline) = 0.177
and loses to `solid` — the same failure mode the transfer test found for weight,
where 0.934 read as "heavy" and ranked 7th of 12.

That is consistent, it is now twice-observed, and it is the outstanding work:
**absolute probabilities do not transfer from synthetic training to real faces.**

## The descriptive column, which is why this matters

Registered as descriptive only, carrying no claim. The twelve generated atlases:

| atlas | prompt asked for | 4-way | recorded 2026-08-23 |
|---|---|---|---|
| **09** | **a stencil sans with deliberate breaks** | **solid** | **MISS — "solid, no breaks"** |
| **10** | **an inline face with a white stripe** | **inline** (0.642) | **HIT** |
| **07** | an ultra-light hairline sans | **outline** | **"reinterpreted as an outline"** |
| the other nine | — | solid | — |

**Three for three, against labels written down before the instrument existed.**

The stencil row is the one that matters. *"A stencil sans with deliberate
breaks"* produced a solid face, every prior instrument in this project called it
excellent, and identity scored it **0.9787 — among the highest of the twelve**.
This measure says `solid`. It is the first thing here that reads a style
adherence failure as a failure.

The outline row was not asked for and is arguably better evidence, because
nothing pointed the measure at it: the note independently described that
generation as *"reinterpreted as an outline"*, and the 4-way argmax says
`outline`.

And P(stencil) across all twelve is flat noise, 0.126–0.205, with atlas 09 at
0.192 — third, in a band with no structure. The measure is not saying *"somewhat
stencil"*; it is saying *"none of these are stencil"*, which is correct.

## What this is not

- **n = 11.** Five stencil superfamilies and six inline is what the pool holds.
  A replication needs fonts this corpus does not contain.
- **Four treatments, not twelve styles.** Solid, stencil, inline, outline. It
  says nothing about didone contrast, humanist apertures or flared terminals —
  most of the vocabulary a user would type.
- **The generated column carries no claim.** It is registered as descriptive,
  it is n=12 with one generation each, and it is the same twelve atlases used
  yesterday. Three-for-three on pre-existing labels is striking and it is not a
  validation.
- **Still no threshold.** 4/11 on the unrestricted question is the proof.
- **The artifact risk is mitigated, not eliminated.** A band eraser makes
  grid-aligned gaps where a designer breaks at junctions. The defence is that
  the primary ran on real faces and passed — not that the transforms are
  faithful.
- 232 training atlases from 60 sources rather than 240: eight transforms of
  hairline faces fell below the 40-scoreable-cell floor and were dropped.

## Next

1. **Calibration is now the bottleneck, not separation.** Two independent
   results say the same thing: ranks transfer, absolute probabilities do not.
   A held-out threshold with error rates is what turns this into a gate.
2. **Widen the vocabulary.** Four treatments is a start; contrast, aperture and
   terminal shape are untouched, and the terminal-shape feature registered
   yesterday for serif-vs-sans is the obvious shared piece.
3. **A different generator arm** is the next data for the descriptive column,
   as the transfer registration required — not a second pass over these twelve.

## Status of the three axes

| axis | instrument | state |
|---|---|---|
| coherence | `reference_gate.py`, `style_coherence.py` | validated |
| identity | `glyph_classifier.py` | validated |
| adherence | `synthesize_rare_attributes.py` | **partial** — 4 treatments, 10/11 on real held-out faces, uncalibrated, and the first measure here to read an adherence failure correctly |
