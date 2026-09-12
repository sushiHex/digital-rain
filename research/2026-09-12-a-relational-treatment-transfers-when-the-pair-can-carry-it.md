# A relational treatment transfers when the pair can carry it — and what carries it is each glyph's deviation, not the equality (2026-09-12)

**Pre-registered twice, both times before the run.** The second pair in
`analysis/relational_transfer_probe.py` (tag `prereg-relational-mi`, commit
`74a667a`), and then, after an adversarial review of the first draft of this
note, the three control arms that unbundle it (tag
`prereg-relational-mi-controls`, commit `50d159e`). Follow-up to
`research/2026-09-11-a-relational-treatment-does-not-transfer-under-a-weak-signal.md`,
whose own amendment said its failure could not separate "relational treatments
do not propagate" from "this pair could not carry the signal". Issue #21.

**Answer, in three sentences.** Draw the monospace reference from a
width-disparate pair and the same checkpoint pulls the other ninety-two ink
widths together: CV 0.382 → 0.272, the registered verdict **PARTIAL**, the
stencil control intact. The controls then show that the equality itself is not
what the model reads: scaling both glyphs by one factor with the ratio
preserved reproduces only 26% of the fall, while fattening the `i` alone
reproduces 97% of it and narrowing the `M` alone 61%. What transfers is each
glyph's *deviation from its normal width*, applied to the letters of its kind —
a narrower-than-normal `M` condenses the wide letters, a fatter-than-normal
`i` emboldens the thin ones — which is a set-level effect produced by local
cues, and it is why `Kg`, whose equalised glyphs deviate by 4%, carried
nothing.

## The registered run: Mi against Kg

| | Kg run (2026-09-11) | Mi run (2026-09-12) |
|---|---|---|
| reference pair, ink widths in the neutral source | K 231 / g 214 px, ratio 1.08 | M 301 / i 57 px, ratio 5.28 |
| what equalising removes | 4% of the wider glyph | 40% of the M's width; the i becomes 3.1× wider |
| checkpoint, seed, steps, source font, transform, statistic, bar | identical | identical |

The reference pair is a convention, not a constraint: the checkpoint's
conditioning names `Rg`, the shipped references draw `Kg`, and the one test of
reference-glyph identity (`K`→`R`, ten fonts, p = 0.625) found no effect —
though that test does not license *any* pair, and `Mi` is out of the training
distribution. Wi (ratio 7.4) and Ml (2.5) were rejected before the run as, in
turn, more extreme than any real monospace face asks of its widest letter and
the weaker cue; both are assertions, not measurements.

| arm | ink-width CV | parts | holes |
|---|---|---|---|
| plain | 0.382 | 0.732 | 0.210 |
| stencil (control) | 0.387 | **2.309** | **0.015** |
| monospace | **0.272** | 0.772 | 0.158 |

Control first, as registered: stencil parts +1.577 and holes −0.195 reproduce
the local-treatment signature, so the pipeline worked and an unfamiliar pair was
readable *for a local treatment*. Then the monospace arm: **−0.110** against
the plain arm. The real-monospace band is 0.209–0.240 and the real-proportional
band 0.326–0.394 (`research/advance_survives_atlas.json` — four and three named
faces, a mechanism demonstration rather than a population), so 0.272 is between
them: PARTIAL by the registered rule. Under `Kg` the same arm moved +0.001.
Scored over the 92 cells excluding the two drawn glyphs, one seed, 20 steps,
`training_glyph_4b_r32_5000/checkpoint-5000`.

## What the fall is made of

Per-cell ink widths, plain arm against monospace arm, over the same 92 cells.
The record is `research/relational_widths.json` (written by
`viz/relational_widths.py`, which also draws `viz/out/relational_widths.png`
from it); the widest and narrowest twenty cells are fixed groups named there.

| | Kg run | Mi run |
|---|---|---|
| cells narrowed / widened / within 3 px | 0 / 1 / 91 | **57 / 9 / 26** |
| widest 20 by plain width | 61.6 → 62.4 px | **59.8 → 43.4 px** |
| narrowest 20 by plain width | 17.6 → 17.7 px | **18.4 → 22.9 px** |
| mean width | 39.5 → 40.0 (+1%) | 39.2 → 33.8 (−14%) |
| spread of widths (sd) | 15.9 → 16.1 (+1%) | **15.0 → 9.2 (−39%)** |
| ink pixels, bounding-box fill | +1.5%, 0.435 → 0.436 | **+20%**, 0.450 → 0.508 |
| affine fit, mono ≈ a + b·plain | −0.0 + 1.01·plain, R² 0.997 | 13.8 + 0.51·plain, R² 0.69 |

A uniform condensing keeps a face's proportions — mean and spread fall by the
same fraction and the CV does not move — so the spread falling almost three
times as far as the mean rules that out, and the control arm below confirms
it directly. It does not rule out a condensing plus an additive stroke
expansion: the affine fit has exactly that shape, and the monospace arm is
20% heavier in ink. The fall is robust to the ink threshold (32 to 224:
−0.109 to −0.114) and to dropping the suspect cells (`I` and `l` out: 0.366 →
0.266; alphanumerics only: 0.295 → 0.197), so literal copying does not
explain it — but it contaminates it: `I` goes 9 → 42 px as a copy of the
reference's slab `i`, and is about a third of the narrowest group's gain
(`l`, by contrast, is 14 → 14). The correlation of a cell's change with its
plain width (−0.82) is reported in the record and is evidence of nothing:
`Cov(x, y−x) = Cov(x, y) − Var(x)` is negative by construction, and choosing
the extreme groups by their plain width invites regression to the mean.

## The controls: what the model actually read

Same pair, checkpoint, seed and steps. The regenerated plain and monospace
arms reproduce the run above exactly (registered validity check), and the
stencil control passes again.

| reference | pair after the transform | CV | fall vs plain | share of the equalised fall | mean | sd | ink |
|---|---|---|---|---|---|---|---|
| equalised (monospace) | M 179 / i 179 | 0.272 | −0.110 | 1.00 | 33.8 | 9.2 | +20% |
| **condense** — both by one factor, ratio kept | M 179 / i 34 | 0.354 | −0.029 | **0.26** | 31.0 | 11.0 | −5% |
| narrow_wide — only the M | M 179 / i 57 | 0.316 | −0.066 | 0.61 | 32.1 | 10.1 | +6% |
| **widen_narrow** — only the i | M 301 / i 179 | 0.276 | −0.106 | **0.97** | 42.2 | 11.6 | +17% |

The registered primary is the condense arm against the equalised one: at 26%
of the fall it is under the 50% line, so the equality carries signal beyond
condensing — **IDENTIFIED**, per the rule fixed before the run. The
condense reference is the uniform condensing the section above could only
argue against: the face it produces is 21% narrower with its proportions
nearly kept (sd and mean fall together), and the CV barely moves.

The secondary arms say what the signal is. Fattening the `i` alone — the
`M` untouched, the pair still disagreeing by 1.7× — reproduces 97% of the
fall, and it does so from the other side: the face gets *heavier and wider*
(mean +8%, ink +17%), the thin letters are emboldened into slabs (`I`, `i`,
`l`, `1`, `|`), and the spread closes from below. Narrowing the `M` alone
reproduces 61%, from above: the face condenses (mean −18%) and the wide
letters lose most. Equalising does both at once, which is why its mean falls
while its ink rises. The two effects overlap rather than add.

So the model is not reading "these two agree". It is reading each glyph's
departure from the shape it expects, and applying that departure to the
letters of the same kind: a thin letter drawn fat means *draw thin letters
fat*; a wide letter drawn narrow means *draw wide letters narrow*. That is
still a set-level consequence of a two-glyph instruction — the ninety-two
untouched letters moved by class — and it is the same mechanism the stencil
finding showed for a local treatment, now producing what looks relational.
It is also exactly what a monospace designer draws: the `i` gets slab serifs
and the `m` is squeezed, which is why the attribute survives an atlas that
discards advances at AUC 0.946 (`analysis/advance_survives_atlas.py`). The
model has seen those hallmarks in the corpus and answers to them.

## What this overturns, and what it does not

- The Kg note's boundary — the LoRA propagates local treatments and not
  relational ones — does not hold as stated, and the reason is sharper than
  "the signal was weak": an equalised `Kg` deviates each glyph by 4% from its
  normal width, which is no departure to read. The correct statement is that
  **a two-glyph reference steers the set through each glyph's deviation from
  its expected shape**, and a relational treatment transfers exactly when it
  is expressed as such deviations. Equality with proportions kept transfers
  nothing.
- This is one seed, one source font, one checkpoint, a pair the model never
  saw as a reference, and an ink-width statistic whose "real" bands are
  seven named faces. PARTIAL means the widths moved most of the way to the
  monospace band and stopped short, with a heavier face and literal slab
  copies riding along. A second seed and a second source face, and a graded
  fattening of the `i` on this pair, are the next measurements; the
  `Kg`-versus-`Mi` contrast confounds glyph identity with cue strength and
  cannot locate a threshold on its own.
- Ink width is not advance width. `render_atlas` centres every glyph on its
  ink and discards advances, so ink is the only channel a reference has; a
  finished font would still need its advances set.

## For the product

`analysis/constructed_reference.py` does not offer monospace, and this note
does not change that by itself: it motivates a *width-steering* construction
— fatten the thin glyph, narrow the wide one — as a registered follow-up on
the picker path, with the seed and source replications above before anything
is offered.

## Reproduce

Private archive only: the probe and its result records are withheld from the
public repository (`misc/export_public.py`, RECIPE), and the atlases live
under the gitignored `eval_runs/`. The public checkout reproduces the figure
from the record: `python viz/relational_widths.py --record`.

```
python analysis/relational_transfer_probe.py --pair Mi
python analysis/relational_transfer_probe.py --pair Mi --controls
python viz/relational_widths.py
```

Records: `research/relational_transfer_probe_Mi.json`,
`research/relational_transfer_probe_Mi_controls.json`,
`research/relational_widths.json`.
