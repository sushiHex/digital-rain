# The dose is graded; under a second seed and a second face the order holds and the share does not

2026-09-13. The follow-up registered on the `Mi` finding
([`2026-09-12-a-relational-treatment-transfers-when-the-pair-can-carry-it.md`](2026-09-12-a-relational-treatment-transfers-when-the-pair-can-carry-it.md)),
issue #30, the probe's fourth registration (tag
`prereg-relational-mi-followup`, committed before any of it ran). Three
arms, same checkpoint (`training_glyph_4b_r32_5000/checkpoint-5000`), same
20 steps, about seven minutes of GPU each once the variance runs released
the card:

- **Dose.** The `i` fattened alone to 1.5×, 2× and 3.1× its ink width, the
  `M` untouched. Prediction: the fall in ink-width CV is monotone in the dose.
- **Second seed.** The registered arms and the three controls under
  inference seed 43. Prediction, verbatim: *"the sign and the ORDER
  reproduce -- widen_narrow ~ equalised >> condense. Magnitudes are
  reported, not predicted."*
- **Second source face.** The same under Lato-Regular instead of ABeeZee.
  Prediction as for the seed.

The dose and source predictions held in full. The seed prediction held on
the sign and the rank order and **failed its middle clause**: under seed 43
the fattened `i` alone is 0.64 of the equalised fall, which is not
"~ equalised". The previous note had quoted 97% for that share.

---

## The dose is graded

Source ABeeZee, seed 42, the `i` alone (`--pair Mi --dose 1.5 2 3.1`):

| arm | ink-width CV | fall vs plain | affine slope | ink |
|---|---|---|---|---|
| plain | 0.382 | — | — | — |
| `i` × 1.5 | 0.361 | +0.022 | 0.96 | +5.8% |
| `i` × 2 | 0.338 | +0.044 | 0.90 | +8.9% |
| `i` × 3.1 | 0.277 | +0.105 | 0.74 | +16.2% |
| equalised (`Mi` to one width) | 0.272 | +0.110 | 0.51 | +20.1% |

**MONOTONE**, as registered — and close to proportional over this range:
per unit of fattening (factor − 1) the fall is 0.043, 0.044, 0.050, rising
15% at the top dose. Three points, no variance estimate; "graded" is what
they support, "linear" is not. The affine slope of generated width against
plain width falls with the dose, 0.96 → 0.90 → 0.74: the compression of the
width distribution grows with the cue rather than tripping at some strength.

The registration described the 3.1× arm as "the widen_narrow arm already
run, regenerated here as its own check". It is not quite that:
`widen_narrow` sets the `i` to the pair mean, 179 px
(`synthesise_transforms.control_targets`), and 3.1 × 57 rounds to 177 px,
so the two references differ by two pixels. They land 0.0013 apart in CV
(0.277 against 0.276), and that gap is the two pixels, not run-to-run
noise — so the 3.1× arm cannot serve as the regeneration check the
registration called it. What does serve is stricter: the arms whose
references *are* identical came back **bit-identical**. The plain and
equalised atlases of this run carry the same md5 as the 2026-09-12 ones,
which also says the generation path is unchanged by the transformers-5
upgrade of the shared site-packages that broke the eval loader mid-run this
week (#36).

## The order holds; the 97% does not

The three runs of the registered arms and controls, each summarised against
its own plain arm:

| run | plain | equalised | fall | narrow_wide | widen_narrow | condense | verdict |
|---|---|---|---|---|---|---|---|
| ABeeZee, seed 42 (the record) | 0.382 | 0.272 | −0.110 | 0.61 | **0.97** | 0.26 | IDENTIFIED |
| ABeeZee, **seed 43** | 0.368 | **0.241** | −0.127 | 0.48 | **0.64** | 0.15 | IDENTIFIED |
| **Lato-Regular**, seed 42 | 0.404 | 0.263 | −0.141 | 0.57 | **0.96** | 0.29 | IDENTIFIED |

The control columns are each arm's share of the equalised fall. Against the
registered prediction — *sign and order reproduce, widen_narrow ~ equalised
>> condense*:

- **Lato-Regular: held in full.** Every arm falls; `widen_narrow` at 0.96
  is ~ equalised; condense at 0.29 is far below it.
- **Seed 43: held on the sign and the rank order, failed on the middle
  clause.** Every arm falls, and the ranking `widen_narrow` (0.64) >
  `narrow_wide` (0.48) ≫ `condense` (0.15) is the record's ranking — but
  0.64 is not "~ equalised". The fattened `i` reproduces two-thirds of the
  fall under this seed, not all of it, and the narrowed `M` correspondingly
  more of the remainder.

The verdict rule — condense at or under half the equalised fall — returns
IDENTIFIED in all three runs, with condense at 0.15–0.29. The equality
carries signal beyond condensing, under a second seed and a second face.

The share the `i` alone accounts for is therefore **0.64–0.97** across the
three runs, and "97%" is retired as the number. "Fattening the thin glyph
does the whole job" was one seed talking. "Each glyph's departure from its
normal width is read, and the thin glyph's departure is the larger lever"
survives all three.

Two things the summaries add
(`viz/relational_widths.py`, `research/relational_widths.json`):

- **The fall in spread is repeatable; what it is stays open.** The sd of the
  92 generated widths falls 15.0 → 9.2, 14.9 → 9.6 and 15.9 → 9.6 — by
  39%, 36% and 39% — whichever seed or face draws the equalised pair. The
  affine fit of generated width on plain width is also the same three
  times over (13.8 + 0.51·x, 19.1 + 0.51·x, 17.3 + 0.49·x; r ≈ 0.8). Read
  that fit as the script's docstring reads it: an intercept plus a slope
  under one is exactly the shape a condensing plus an additive stroke or
  terminal expansion would produce, with no set-level reading involved. Its
  constancy says the model does the same thing every time; it does not say
  what the thing is. The slope is a regression coefficient, not a ratio of
  spreads: the spread falls by about a third, not by half — and the slope
  looks steadier than the spread ratio only because the correlation (0.83 /
  0.79 / 0.82) and the ratio (0.61 / 0.64 / 0.61) each move ~5% and offset.
  Three runs; there is no variance estimate behind "repeatable".
- **The face comes back heavier every time, and not by the same route.**
  Within each run the equalised arm's ink rose +20%, +50% and +91% — but
  those are ratios against plain arms that themselves differ (bbox fill
  0.450 / 0.510 / 0.401), so most of that range is baseline. Measured where
  a product would gate, the delivered face, the three equalised arms sit at
  fill **0.508 / 0.653 / 0.670**: heavier than every plain, by a third to
  two-thirds, and Lato's counters largely close (holes 0.215 → 0.030). The
  route differs too. On the record run the mean width fell 14% and the
  spread 39%; under Lato the mean fell 7%; under seed 43 the mean barely
  moved (40.6 → 39.8) and the whole CV fall is spread — that run reached
  0.241, one thousandth above the real-monospace band (0.209–0.240), by
  adding weight rather than by condensing. The width-steering a product
  would want comes bundled with a weight it did not ask for, and which of
  the two the model reaches for is not fixed.

---

## Deviations from the registration, stated

- `--source Lato-Regular` found no such file: `font_pool/` holds the Lato
  2.0 web build as `LatoWeb-Regular.ttf`, and the `NEUTRAL` list that named
  `Lato-Regular` had never been exercised past its first entry. The run took
  the registered stem from the pinned Google Fonts checkout instead
  (`--pool google-fonts/ofl/lato`, the same OFL Lato at the pinned commit);
  the pool argument feeds nothing but the source face. The output keeps the
  registered name.
- The replications skip the reproduce-the-record check by design (their
  plain arms are new draws) and carry no bar of their own beyond the verdict
  rule; the dose arms carry none. Nothing here was re-scored or re-run.

## What it does not decide

- Three runs of one checkpoint and one statistic. The verdict rule is
  stable under them; the shares are not, and a fourth run could put the
  `i`-alone share anywhere in its range.
- The real-monospace band is seven named faces. Seed 43's 0.241 against a
  band edge of 0.240 is a coincidence of rounding, not a crossing.
- The heaviness is measured, not explained. Whether the model fattens the
  face because a wide `i` reads as a bold cue, or because equalising two
  glyphs of one size leaves more ink in the reference, is a different probe.

## For the product

The conditional step in #30 stands: a width-steering construction on the
picker path — fatten the thin glyph, narrow the wide one — registered before
it is offered, now with the dose curve to size the fattening and the ink
cost to gate it. It is product recipe, private.

## Reproduce

Private archive only (the probe and its records are withheld from the public
repository; the atlases live under the gitignored `eval_runs/`). The public
checkout draws the figure from the record: `python viz/relational_widths.py --record`.

```
python analysis/relational_transfer_probe.py --pair Mi --dose 1.5 2 3.1
python analysis/relational_transfer_probe.py --pair Mi --controls --seed 43
python analysis/relational_transfer_probe.py --pair Mi --controls --source Lato-Regular --pool google-fonts/ofl/lato
python viz/relational_widths.py
```

Records: `research/relational_transfer_probe_Mi_dose.json`,
`research/relational_transfer_probe_Mi_controls_s43.json`,
`research/relational_transfer_probe_Mi_controls_Lato-Regular.json`,
`research/relational_widths.json` (keys `Mi_dose`, `Mi_controls_s43`,
`Mi_controls_Lato-Regular`). Atlases and references in the private `backup/`
(`relational_refs_mi_dose`, `relational_refs_mi_controls_s43`,
`relational_refs_mi_controls_lato`).
