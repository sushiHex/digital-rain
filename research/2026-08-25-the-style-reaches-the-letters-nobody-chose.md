# The style reaches the letters nobody chose (2026-08-25)

**11 of 16 atlases matched their own reference more closely than the other three
of the same description — p = 0.0003, mean rank 1.50 against 2.50 chance.** The
picker is not theatre: the reference a user selects determines the ninety-two
glyphs they never saw.

Tool: `analysis/reference_to_atlas_transfer.py`, committed at `56eb25e`
**before** any atlas was generated. Data:
`research/reference_to_atlas_transfer.json`. Figure: `viz/reference_to_atlas.py`.

## The defect, first, because it changed the result

**The first run scored 12 atlases against a registration that said 16, and
nothing raised.**

The style prefix in a candidate filename is truncated to 28 characters, and for
one description that cut lands **on an underscore**:

```
10-an_inline_face_with_a_white_  +  __s0  ->  10-an_inline_face_with_a_white___s0
                              ^^^ three underscores
```

`stem.split("__")[0]` returns `...white` instead of `...white_`. **Grouping
still worked** — every candidate of that description loses the same character —
so `within_prompt_diversity.py` produced correct statistics under a *wrong key*.
Then this tool built a glob from that key, matched nothing, and silently skipped
the **widest-spread description**, which is the most informative one in the set.

That is the third glob/label mismatch on this record — a `[wght]` font name read
as a character class once dropped 12 of 48 fonts — and the shape is always the
same: **the wrong answer looked like a smaller correct one.**

Fixed with a regex rather than a split, `glob.escape` on every pattern, and a
guard in `widest_descriptions` that treats an unmatched key as a **bug** rather
than an empty arm. `tests/test_candidate_labels.py` pins it, including a test
that fails if the naive split ever starts agreeing — so the guard cannot rot
into a tautology.

**Re-running the diversity check gave byte-identical numbers** (ratio 0.518,
within 1.302, between 2.514), confirming that only the key was wrong and the
statistics were not.

Both counts are on the record: **9/12 before the fix, 11/16 after.** The bar was
fixed in advance at ≥8/16, and completing the registered set is what the
registration demanded, not a deviation from it.

## The test

Generate an atlas from each of a description's four candidate references, then
ask whether each atlas resembles **its own** reference more than the other three
**of the same description**. The words are held constant; only the reference
varies. One seed for all sixteen, so the arms cannot differ by the style lottery
(SD 0.0248 on the seed main effect alone).

**The atlas's own `K` and `g` are excluded.** The model is conditioned to copy
those two glyphs, so matching an atlas's `K` to its reference's `K` measures the
conditioning, not the transfer. The atlas vector is built from the **other 92
cells** — did the style reach the letters the user never saw?

```
11/16 matched their own reference    p = 0.0003    mean rank 1.50 (chance 2.50)
BAR >=8/16 and p<0.05: PASSED
```

| description | matched | spread |
|---|---|---|
| a chunky slab serif | **4/4** | 1.764 |
| a condensed grotesque | 3/4 | 1.584 |
| a heavy angular blackletter | 2/4 | 1.984 |
| an inline face with a white stripe | 2/4 | 3.960 |

The one large failure is worth naming: inline seed 43 sits at **own distance
5.93 against a best of 1.05**. That is a genuine drift, not a near-tie — the
atlas went somewhere its reference did not.

## Best-case by construction, and said so in advance

The registration fixed the four **widest-spread** descriptions, because matching
is only meaningful when the four references actually differ. Spread runs
0.454–3.960, and on a narrow description the four references are near-identical
and nothing could match them.

That caveat is not a footnote. The
[diversity result](2026-08-25-the-picker-works-except-where-it-is-needed.md)
showed spread is **narrowest exactly where the generator fails**, so the
descriptions this test excludes are the ones where the picker helps least
anyway. Transfer is demonstrated where there is something to transfer.

## What this does not establish

- **n=16, one seed, one checkpoint, four of twelve descriptions.**
- **Nearest-of-four is not "faithful".** An atlas can be closer to its own
  reference than to three others and still be a poor rendering of it. This
  measures *tracking*, not fidelity.
- **The style vector is the four coherence features** — stroke, slant, fill,
  parts. An attribute none of them expresses (a serif's shape, say) could fail
  to transfer and this test would not see it.
- **No claim about the eight narrow descriptions.** Untested by design.

## The architecture, end to end

All four steps of the options-and-iterate design are now measured:

| | step | result |
|---|---|---|
| 1 | N candidates per description | `--n`, with `n=1` labels preserved |
| 2 | do the options differ? | **ratio 0.518, p=0.0005** |
| 3 | does the atlas track the pick? | **11/16, p=0.0003** |
| 4 | can two glyphs be scored? | **9/11, p=0.0327** |

Four options at ~25 s each, selection on two glyphs, one atlas at ~62 s — about
**2.7 minutes** per font, against 90 s for the current single-shot path and
about 4 minutes for atlas-stage selection.

**And the limit is on the record beside it:** re-rolling cannot rescue a prompt
the model systematically misses, because the descriptions it misses are the ones
whose candidates barely differ. The picker amplifies capability; it does not
create it.
