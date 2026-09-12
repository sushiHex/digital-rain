# CLIP does not read the decisive clause (2026-08-24)

The pre-registered minimal-pair test failed at exactly chance. **CLIP does not
read the clause that decides the style**, and per the registration this line of
work stops here.

Tool: `analysis/style_adherence_minimal_pairs.py`, committed at `44dfddb`
**before** the numbers existed. Data:
`research/style_adherence_minimal_pairs.json`.

## The result

Each prompt was paired with a negative differing in **one decisive attribute**,
wording otherwise held close so the prompt-column confound cancels.

```
own prompt wins 6/12    exact binomial p = 0.6128    BAR p<0.05: FAILED
```

| attribute | own | negative | margin | |
|---|---|---|---|---|
| terminal (blackletter) | 0.255 | 0.219 | **+0.036** | ✓ |
| terminal (rounded) | 0.250 | 0.229 | +0.021 | ✓ |
| weight (hairline) | 0.266 | 0.254 | +0.012 | ✓ |
| serifs (slab) | 0.236 | 0.234 | +0.003 | ✓ |
| **inline stripe** | 0.254 | 0.256 | **−0.002** | ✗ |
| **breaks (stencil)** | 0.207 | 0.216 | **−0.008** | ✗ |
| contrast (didone) | 0.226 | 0.252 | −0.026 | ✗ |

**The margins are the finding.** The decisive clause moves cosine similarity by
±0.001 to ±0.036 — at most about 1% of a ~0.24 baseline. Whatever the earlier
permutation result (p ≈ 2e-05) was detecting, it was not this.

## Two individual cases worth keeping

**The inline failure is the damning one.** That image visibly *has* a white
stripe inset in each stroke — it is the most obvious attribute in the whole set —
and CLIP scored "solid, filled strokes and no inline stripe" **higher**.

**The stencil "failure" is CLIP being right.** It preferred "solid, unbroken
continuous strokes" to "stencil with deliberate breaks" — and the generated
image *is* solid, because that generation missed. Counted as a loss under the
registration, which is correct: the test asks whether the own prompt wins, and
here it should not have.

That single case is the entire adherence problem in miniature. A measure that
scores an image against the prompt that *requested* it cannot distinguish "the
model obeyed" from "the model disobeyed and CLIP noticed" without a label saying
which. It is exactly why the earlier own-score reading was circular.

## What this retires

The style-adherence-via-generic-CLIP approach. Three results in sequence:

| test | result |
|---|---|
| ranking, 1-of-12 | 17% top-1 vs 8% chance — failed |
| permutation over assignments | p ≈ 2e-05 — real, but not adherence |
| **minimal pairs, pre-registered** | **6/12, p = 0.61 — chance** |

The middle result stands as arithmetic and falls as interpretation. The pairing
is non-random; the thing making it non-random is not the decisive attribute.

## What the pre-registration bought

The previous attempt produced three analyses on one matrix and reported the one
that passed. This one fixed the hypothesis, statistic, bar, model and
tie-handling in a docstring, committed it, and then ran once. The result is a
clean failure that needs no correction, no multiplicity argument, and no
defence — which is worth more than the ambiguous pass it replaced.

**Ties counted as losses**, registered in advance as conservative. Two margins
were within ±0.002, so under a tie-tolerant rule this would read 6–8 wins and
still fail.

## Next, and it is not another statistic over this matrix

**FontCLIP** (arXiv 2403.06453) — a vision-language model adapted to font
attributes, which exists precisely because generic CLIP lacks this vocabulary.
That is the registered next candidate.

Failing that, adherence may need a **discriminative** approach rather than an
embedding one: train a small classifier per attribute (stencil vs solid,
inline vs filled, light vs heavy) on rendered real fonts, where labels are free
because the fonts' own metadata supplies them. That is a different and more
tractable problem than open-vocabulary alignment, and this project already has
925 licence-clean fonts with which to build it.

## Status of the three axes

| axis | instrument | state |
|---|---|---|
| coherence | `reference_gate.py`, `style_coherence.py` | **validated** |
| identity | `glyph_classifier.py` | **validated** |
| adherence | — | **no instrument.** Generic CLIP is ruled out, pre-registered |
