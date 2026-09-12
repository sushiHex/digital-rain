# Stacking rank 64 + oversampling overshoots; rank 64 alone is the lever (2026-08-05)

> **The title's two clauses did not age the same way. The note is kept
> unrewritten as the dated record.**
>
> *"Rank 64 alone is the lever"* — **retracted.** It rested on the
> redistribution statistic, shown biased on 2026-08-07. At the headline gate
> rank 64 shows no difference on any metric (composite p=0.53, char_acc p=0.96),
> and against training-run variance measured on 2026-08-13 its composite effect
> is +0.5×SE. There is no lever here to be.
>
> *"Stacking overshoots"* — **this became the best-supported claim in the
> project.** Scored against each metric's own run-to-run SD, the stacked run
> regresses at **−13.5×SE on LPIPS** and **−7.8×SE on composite**, the largest
> resolvable effect anywhere in the repository. It is mechanically confirmed
> too: the stacked run is **over-inked by 20%**.
> See [the claim ledger](2026-08-13-the-claim-ledger-corrected.md).
>
> **Correction to this note's own ink table (below).** It records ground truth
> 0.0712 and the stacked run 0.0820, i.e. +15%. Re-measured on 2026-08-18 from
> the committed artifacts — mean bright-pixel fraction over all 50 atlases in
> `eval_holdout/atlases/` against `eval_runs/glyph_4b_r64_distinct_5000/generated/`
> — the figures are **ground truth 0.0652, stacked 0.0780, +19.7%**, matching
> the claim-ledger note. The direction and the conclusion are unchanged; the
> absolute values here are not reproducible and the +15% figure propagated into
> `README.md`, `CLAUDE.md` and `docs/quality-roadmap-v3.md`, all now corrected.
>
> "Do not stack levers" survives. "Rank 64 is the lever it should be replaced
> with" does not.

**Question.** Against the 9B, the 4B's deficit is entirely in the distinctive
tail — on the easier half the 9B's dinov2 advantage is **+0.0007**, i.e.
nothing. The real target is **hard-half +0.0702 char_acc / +0.0599 dinov2**.
Rank 64 and distinctiveness oversampling each moved the hard half alone, and
their per-font gains did not overlap. Does combining them add?

**Partially on char_acc, not at all on dinov2, and the cost is prohibitive.**

## Result: significant regression on 5 of 6 metrics

| run | char_acc | dinov2 | lpips | composite | identity |
|---|---|---|---|---|---|
| r32 baseline | 0.6460 | 0.8485 | 0.1381 | 0.8158 | 0.9893 |
| rank 64 | 0.6464 | **0.8540** | **0.1342** | **0.8187** | 0.9905 |
| oversampling | 0.6391 | 0.8406 | 0.1351 | 0.8131 | 0.9880 |
| **r64 + oversampling** | 0.6045 | 0.8192 | **0.1868** | 0.7805 | 0.9891 |
| 9B | 0.6917 | 0.8788 | 0.1457 | 0.8137 | 0.9936 |

Against baseline the combination is SIG worse on composite, char_acc, racc,
dinov2 and lpips (r = 0.37–0.62); identity alone is unchanged.

## The hard half did improve — sub-additively

| lever | hard-half char_acc | hard-half dinov2 | easy-half char_acc |
|---|---|---|---|
| rank 64 | +0.0298 | **+0.0301** | −0.0289 |
| oversampling | +0.0221 | +0.0077 | −0.0357 |
| **combined** | **+0.0400** | **+0.0004** | **−0.1230** |
| *(target)* | *+0.0702* | *+0.0599* | |

So char_acc on the hard half is genuinely additive-ish (0.0400 against 0.0298
and 0.0221 alone — more than either, less than their sum). **dinov2 is not:
combining destroyed rank 64's +0.0301, leaving +0.0004.**

And the trade collapsed. Rank 64 trades ~1:1 (+0.0298 hard for −0.0289 easy)
with composite *rising* +0.0029. The combination trades **1:3** (+0.0400 hard
for −0.1230 easy) with composite falling −0.0353.

## Mechanism: it over-inks

lpips 0.1868 with identity unchanged is the same signature as the earlier
`dataset_v3` @6016 failure — a global stroke-weight shift, letters still
correct. But in the opposite direction:

| | ink fraction |
|---|---|
| ground truth | 0.0712 |
| r32 baseline | 0.0682 |
| rank 64 | 0.0724 |
| oversampling | 0.0635 |
| **r64 + oversampling** | **0.0820 (+15% vs GT)** |

**A hypothesis worth killing:** I expected the opposite, reasoning that
distinctive fonts are sparse. They are not. Distinctiveness and ink are
essentially uncorrelated across the corpus (Spearman rho=0.060, p=0.069), and
the distinctive tail is *heavier* than the rest (0.0790 vs 0.0622) — dot-grid
Bitcount, blackletter Jacquard and the Rubik distress faces are dense, not
thin. So oversampling biases the weight prior heavier, and doubling adapter
capacity lets the model commit to it.

Neither lever alone over-inks. Only the combination does, which is why this was
not predictable from the standalone runs.

## What rank 64 is actually worth

Measured directly against the 9B, after rank 64 the remaining hard-half gap is
**+0.0483 char_acc / +0.0434 dinov2**, down from +0.0702 / +0.0599. Rank 64
closes roughly **31% / 28% of the gap on the half that matters**, at composite
+0.0029 (slightly positive), +1% training time and no extra memory.

It was filed as "not a general improvement ... should not be adopted as a
default on the gate's evidence." On the stratified read that verdict is wrong:
it is the best lever measured, and it is close to free.

## Five levers, one ceiling

| lever | hard char_acc | hard dinov2 | easy char_acc | composite | verdict |
|---|---|---|---|---|---|
| **rank 64** | +0.0298 | **+0.0301** | −0.0289 | **+0.0029** | **adopt** |
| oversampling | +0.0221 | +0.0077 | −0.0357 | −0.0027 | no |
| corpus expansion | +0.0077 | +0.0028 | −0.0834 | −0.0334 | no |
| corpus @ matched budget | — | — | — | — | invalid (hairlines) |
| r64 + oversampling | +0.0400 | +0.0004 | −0.1230 | −0.0353 | no |

Every lever redistributes; none creates. Stacking two redistributors does not
compound their benefits, it compounds their costs. **Adapter capacity, sampling
pressure and corpus composition have all now been tested and the ceiling is the
same.**

## Recommendation

1. **Adopt rank 64** as the default 4B configuration. It is a free ~30% of the
   hard-half gap with composite slightly up.
2. **Stop stacking.** The combination is the fourth consecutive redistribution
   result and the first to make the aggregate materially worse.
3. **Treat the generator track as closed on the local path.** With rank 64
   banked, the 4B is at parity with the 9B on composite, racc, lpips and
   identity, and on the entire easier half; the residue is ~+0.048 char_acc /
   ~+0.043 dinov2 on 25 distinctive fonts. Five levers have failed to move it.

## Artifacts

- `eval_runs/glyph_4b_r64_distinct_5000/`, `training_glyph_4b_r64_distinct_5000/`
- `research/2026-08-05-wilcoxon_glyph_4b_r32_5000_vs_glyph_4b_r64_distinct_5000.json`
