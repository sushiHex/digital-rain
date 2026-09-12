# Benchmark v2 — a confirmatory panel to replace the 50-font holdout

Status: **spec, not built.** 2026-08-08. Derived from an adversarial
benchmark-design review, with the claims it rests on verified locally.

## Why the current holdout cannot be the test any more

Six independent defects, each already documented:

1. **It is 46 fonts, not 50.** Three IBMPlex and three Tiro faces are
   byte-identical as 95-char ASCII atlases, so those typefaces carry triple
   weight (`analysis/check_holdout_integrity.py`).
2. **Two fonts are unscoreable.** `BitcountGridDoubleInk` and
   `BitcountPropDoubleInk` share a byte-identical *reference* — the model's only
   input — but have different ground truth. The model emits identical output
   scored against two different answers, so it cannot do well on both by
   construction. Both were repeatedly cited as per-font evidence.
3. **The estimand is not what it claims.** 32 of the 50 share a superfamily
   with a training font. It is a *file* holdout, not family-OOD.
4. **Confirmatory status is gone.** Fifteen-plus runs of adaptive use, with
   several conclusions reversed on re-analysis. Repeated testing against one
   panel selects on its noise.
5. **Its intervals were wrong.** The harness cell-bootstrapped, making every
   published CI 4–8× too narrow (fixed 2026-08-08, `aedbff6`).
6. **Its cap heights are not the corpus's.** Holdout mean cap height is
   0.7358 em against the corpus's 0.6988 — **2.52 SE, p=0.015** — and
   right-skewed where the corpus is symmetric (`analysis/fit_cap_height.py`).
   A panel meant to estimate generalisation should not differ systematically
   from the training distribution on a basic metric.

The tempting replacement — another 50 files picked by DINOv2 distinctiveness,
filtered by name prefix, then reused indefinitely — reproduces defects 3, 4
and 5 in cleaner packaging.

## The panel

**60 fonts, one per superfamily, none seen in training.** Sixty gives six per
distinctiveness decile without materially changing GPU cost. More does not help
much: the seed main effect does not average out across fonts (~90% of run-mean
variance, `analysis/seed_variance.py`), so fonts are not the binding constraint.

### Selection

1. **Freeze the eligible universe first** — a pinned Google Fonts commit, OFL
   families covering the full evaluated charset. For scoring existing
   checkpoints, no candidate may come from `dataset_v2`: a post-hoc split cannot
   make a training font held out.
2. **Build a versioned `superfamily_id` table** from family metadata, upstream
   project/release URLs, designer/copyright evidence and canonical outline
   fingerprints — adjudicating ambiguous cases by hand and recording why.
   **A name prefix may flag a case for review but must never decide
   eligibility.** The current rule is a six-character `startswith`
   (`analysis/select_expansion_set.py:61`); metadata already catches cases it
   only approximates — Playwrite AU QLD and Playwrite CO point at the same
   upstream release. Repository URL alone is insufficient, since one repo can
   hold several projects. **When lineage is uncertain, exclude.**
3. **Instantiate one exact face per superfamily**, static upright Regular where
   possible, otherwise instantiate named-Regular or recorded axis coordinates
   into a static font. Render reference *and* ground truth from that one
   instance through one loader — this repo has already shipped a defect where
   the two halves picked different variable instances
   (`tests/test_build_dataset_pairing.py`).
4. **Fatal integrity gates, before sampling.** SHA-256 the font, the GT atlas
   and the reference PNG; additionally hash the decoded reference *after* the
   512×512 Lanczos preprocessing, because that tensor — not the PNG bytes — is
   the model input. Same GT ⇒ keep one. Same preprocessed reference **and**
   same GT ⇒ keep one. **Same preprocessed reference but different GT ⇒ exclude
   the whole collision group** (this is the Bitcount failure; it must be
   impossible by construction, not caught afterwards).
5. **Stratify; do not take the most distinctive.** Score candidates against the
   frozen 925-font centroid, form ten equal bins, draw six superfamilies per bin
   with a pre-declared seed, and within that minimise deviation from the
   eligible universe's category mix. Taking the top 60 builds a stress test, not
   an estimate of ordinary performance. **Distinctiveness is for blocking and
   moderator analysis only** — never as a selection target, and never as an
   outcome.
6. **Seal it and use it once.** Pre-register the model contrast, the metric, the
   guards and the analysis before generating.

7. **Retrieval must fail on it. This is a hard acceptance gate, added
   2026-08-13.** Before the panel is sealed, run the non-generative baseline
   against it: for each candidate font, find the nearest font in the *training*
   corpus by DINOv2 on the reference image and hand back that font's ground-truth
   atlas unchanged (`analysis/retrieval_baseline.py`). On the current 50-font
   holdout that baseline scores **char_acc 0.7768 / DINOv2 0.9389**, beating
   every model this project trained (best: 0.6917 / 0.8788).

   A benchmark a nearest-neighbour lookup can win does not measure generation;
   it measures whether the output resembles *some* real typeface. **If retrieval
   is competitive on the candidate panel, the panel is not fit for purpose** —
   fix the panel, not the threshold. Record the retrieval score beside every
   model score permanently, as the floor, so no future result can be reported
   without it.

   Note this is a constraint on the *panel*, not only on the metric in §"The
   primary metric should move to the finished font": a distance-based style
   score will always reward a clean similar font. Whether an atlas-space metric
   can clear this gate at all is genuinely open, and is the reason §"Open
   questions" is not a formality.

If fewer than 60 clean superfamilies survive, **stop** — get a newer snapshot,
or group-split `dataset_v2` and retrain the anchors. Do not relax the leakage
rule to reach a round number.

### Analysis, fixed in advance

Average six seeds within each font, then compare 60 superfamily-level
observations. Bootstrap **superfamilies and paired seed blocks** — never cells.
`analysis/multiseed_compare.py` already implements this shape and is the
starting point.

Keep six seeds, but **do not assume six is enough for the new primary metric.**
That number was derived from char_acc's variance on the old panel; the new
endpoint's variance has to be estimated before any power claim.

## The primary metric should move to the finished font

The current evaluator scores **atlas cells**; the product then traces them into
an OTF/WOFF2 whose spacing is naive and unkerned. An atlas can therefore win
while producing the less usable font — the two are not the same ranking, and
nothing here has ever measured the second.

Proposed endpoint: **the probability that a target user picks one generated
font as the more usable, coherent extension of the supplied reference**, judged
on rendered text specimens at several sizes rather than on cells. A missing,
unparsable, unmapped or unrenderable font automatically loses to a valid one.

For routine automated use, fit a **frozen, monotone human-preference
surrogate** over interpretable feature differences — not another opaque encoder,
which would reintroduce exactly the "the metric is the model's own encoder"
problem that char_acc and DINOv2 already have (they share an encoder and
correlate 0.93/0.74, so they are one evidence family, not two).

Calibrate the surrogate against real human judgements, freeze it, and re-verify
it on a held-out slice. An uncalibrated surrogate is a third unvalidated
instrument, and this project already has enough of those.

## What happens to the old holdout

Retire it into two explicitly labelled roles, and **attach no fresh
confirmatory p-values to either**:

- **`v1-raw50`** — bitwise/code regression only. Catches conditioning breakage
  and catastrophic quality loss.
- **`v1-repaired44`** — descriptive historical comparison. Collapse the two
  duplicate-GT groups and exclude *both* Bitcount cases, rather than choosing
  post hoc which target to keep.

For continuity, re-run exactly **two frozen anchors** — one shipped baseline,
one strongest contender — on the new panel and report old-repaired and new
scores side by side. **Do not fit a conversion between them.**

## Cost

Linear from the current 50-font timings, six seeds per arm:

| comparison | GPU-hours |
|---|---:|
| one 4B arm | 7.2 |
| one 9B arm | 14.4 |
| 4B vs 9B | 21.6 |
| two 9B arms | 28.8 |

## Open questions

- The existing distinctiveness recipe uses only 12 "telling" glyphs. Whether
  that is the right basis for *stratifying* a benchmark — as opposed to ranking
  fonts — is untested.
- The glyph classifier's corpus guard strips axes and `-Style` but does not
  exclude superfamilies, so it must be retrained after the superfamily map is
  frozen or it leaks across the new split too.
- Building the human-preference surrogate is the largest single piece of work
  here and has no design yet beyond "monotone and frozen".
