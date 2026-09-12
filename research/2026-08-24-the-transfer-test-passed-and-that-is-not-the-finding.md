# The transfer test passed, and that is not the finding (2026-08-24)

**The pre-registered primary came back consistent. One descriptive column,
added because I suspected a confound, shows the measures are not reading the
attributes they appear to be reading.** The second result is the important one.

Tool: `analysis/attribute_transfer.py`, committed at `2f71122` **before** the
run. Data: `research/attribute_transfer.json`.

## What was registered, and its ceiling

The labels have the one property nothing else in this project has: they were
written down **before the instrument existed**.
`research/2026-08-23-the-loop-closes.md` records which of twelve style prompts
the generator obeyed and which it missed. The measures were built the next day.
Git proves the ordering — which is exactly what the
[style-adherence retraction](2026-08-24-style-adherence-the-wrong-formulation-failed.md)
lacked, where I labelled a third prompt "missed" *after* seeing it score
third-lowest.

The registration also fixed its own ceiling: with 2 recorded hits and 2 recorded
misses, the best attainable p is **1/C(4,2) = 0.1667**. This test cannot reach
p<0.05, no significance is claimed for it, and it was registered as a check that
can **falsify but not validate**.

## The primary: consistent

| atlas | attribute | recorded | rank | p |
|---|---|---|---|---|
| 10 inline stripe | inline | **HIT** | **1/12** | 0.717 |
| 4 condensed grotesque | width | **HIT** | **1/12** | 0.957 |
| 6 wide monospace | mono | **MISS** | 3/12 | 0.241 |
| 9 stencil, deliberate breaks | stencil | **MISS** | 5/12 | 0.269 |

Both hits rank first. Neither miss does. **Not falsified.**

And the excluded case behaves well. *"Ultra-light hairline"*, recorded as
**reinterpreted rather than failed** and therefore kept out of the primary,
ranks **12 of 12** on P(heavy) at p=0.001 — the lightest of all twelve. An
outline is thin ink, and the measure says so.

## The descriptive column, which is the finding

The tool prints the three atlases each model ranks highest, whether or not the
requesting one is among them. It exists because a rank of 1 says nothing about
*why*.

| model | its top three generated atlases |
|---|---|
| stencil | **10 (inline, 0.70)** · 7 (outline, 0.49) · 4 (0.33) |
| mono | **10 (inline, 0.82)** · 7 (outline, 0.80) · 6 (0.24) |
| weight | 2 (0.99) · 9 (0.97) · 6 (0.97) |

**The stencil model's favourite generated atlas is the INLINE one.** Its second
favourite is the outline. `parts` is a connected-component count, so it reads
"this glyph is in many pieces" — and a break, a stripe and a hollow contour are
all many pieces. The 0.910 separation reported yesterday was stencil against
**ordinary** fonts, not stencil against other multi-part styles.

**So the inline "hit" at rank 1 is not evidence the measure reads *inline*.** It
is evidence the measure reads *many pieces*, on the atlas that has the most. A
real stencil generation would rank there too. The measure cannot tell a user
*"you asked for stencil and got inline"*, which is the sentence the product
needs.

**The mono model is worse.** It scored 0.946 over 98 real families and its top
two generated picks are the inline and outline atlases, at 0.82 and 0.80,
against 0.24 for the atlas that actually asked for monospace. Whatever it learnt
about ink-width uniformity in real fonts, an outlined face satisfies it for
unrelated reasons.

**Weight saturates.** The three heavy prompts score 0.934, 0.988 and 0.950 — all
confidently heavy — yet rank 7th, 1st and 6th, because nearly every generated
atlas scores near 1.0. **Absolute probabilities do not transfer; ranks do.** The
measure can order candidates and cannot yet say "heavy enough", which is another
way of saying it has no calibrated threshold.

## Why the primary passed anyway

Both facts are consistent with a measure that only counts pieces. Inline ranks
first because it genuinely has the most pieces. Stencil ranks 5th because that
generation **was solid** — the eye was right, and the measure agrees for a
reason unrelated to stencil-ness. The primary is satisfied and the mechanism
behind it is not the one the name implies.

That is precisely why the descriptive column was registered as part of the test
rather than added afterwards. Reporting only the primary here would have been
true, pre-registered, and misleading.

## What this changes about the plan

The synthesis step was already the next item. It now has a requirement it did
not have this morning:

**Train the rare attributes against HARD NEGATIVES, not against ordinary
fonts.** A stencil classifier whose negatives are Roboto and Lato learns "many
pieces". A stencil classifier whose negatives include synthesized **inline** and
**outline** faces has to learn what a break is. Synthesis makes that possible
and cheap — all three are geometric operations on real outlines, so all three
can be generated in the same quantity from the same faces, which also controls
for typeface.

Two further consequences:

- **Report ranks, never absolute probabilities**, until a calibration set
  exists. The saturation above is not a rounding detail; 0.934 read as "heavy"
  and ranked 7th of 12.
- **A per-attribute AUC on real fonts is not a claim about generations.** Mono
  went from 0.946 to picking the outline. Any future attribute must be checked
  on generated atlases before it is believed, and this tool is how.

## What is not being done

The registration says: *"whatever this returns, the measures are not retuned
against these twelve and re-scored. A different generator arm is the next data,
not a second pass over this one."* That stands. The hard-negative design above
is a change to the **training set**, evaluated against real held-out stencil
families and a *different* generator arm — not a refit against these twelve.

## Status of the three axes

| axis | instrument | state |
|---|---|---|
| coherence | `reference_gate.py`, `style_coherence.py` | validated |
| identity | `glyph_classifier.py` | validated |
| adherence | — | **still none.** Four attributes are readable from a real atlas; on generated atlases two of them read the wrong thing |
