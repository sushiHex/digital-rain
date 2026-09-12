# Forty-eight of forty-eight: the calibration set has no negatives (2026-09-12)

**The owner's judgement, recorded.** Asked "would you hand this pair to a user
as a starting point for the style they asked for?" over the 48 candidate
references in `eval_runs/_candidate_refs/klein-base-n4` (12 descriptions × 4
seeds, the sheet `analysis/calibration_sheet.py` builds), the owner judged
**all 48 usable**. `research/calibration_labels.csv` carries the labels.

**What the pre-registered analysis can then say.**
`analysis/calibrate_instruments.py`, fixed before a single label existed,
scores the reference gate's distance against the labels by AUC with a
permutation test, bar AUC ≥ 0.70 and p < 0.05. With one class the AUC is
undefined, so the bar is **NOT EVALUABLE** — neither passed nor failed. (The
script's first pass printed FAILED with a permutation p of 0.0001: with one
class every shuffle is also one class, `nan >= nan` is false, and the count
read as significance from no information. Fixed, and the one-class verdict
is now its own case, pinned by a test.)

The one thing the set does measure is the gate's **recall at its existing
cut**. Of 48 references a person would accept, the 1.875 cut passes 46 and
would send two back:

| id | description | gate distance |
|---|---|---|
| `02-s1` | a chunky slab serif with blunt rectangular serifs | 2.395 |
| `04-s1` | a condensed grotesque, tight spacing, large x-height | 2.055 |

Recall 0.96, precision 1.00 by construction, specificity undefined. The
gate's cut was drawn from the coherent references' own spread, and this is
the first evidence about it from a person: it refuses roughly one usable
reference in twenty-five, and nothing here says what it would do with an
unusable one. The adherence secondary (the eight stencil and inline
candidates) has one class too; nothing to rank.

**What this says about the generator, not the gate.** The klein-base
candidate set contains no reference the owner would reject. That is a
finding about the description-to-reference stage — every one of the twelve
descriptions produced four acceptable starting points — and it is also why
this set cannot calibrate anything: a calibration needs the misses. The
picker note already measured that misses concentrate where the generator
fails systematically (the stencil request), and those failures are
*wrong-style* references that still look like one coherent typeface, which
is exactly the case a coherence gate cannot see.

**Next, registered here in outline.** Negatives have to come from somewhere
the owner will actually reject: the Z-Image arm (`_candidate_refs/zimage-n4`,
48 references, worse on every picker axis), the externally generated set,
and deliberately degraded references. Label those the same way, then re-run
the same analysis unchanged on the union; the bar, statistic and cut stay as
registered. Until then the gate's threshold stays what it is, a provisional
coherence cut, and the product's "usable" signal has no calibration.

Record: `research/calibrate_instruments.json`.
