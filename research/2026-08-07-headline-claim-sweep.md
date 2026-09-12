# Headline claim sweep: what survives (2026-08-07)

Eight adversarial audits (Codex gpt-5.6-sol, read-only, max effort) swept every
load-bearing number in the repo against three recently-found error classes:

- **(A)** the redistribution statistic was regression to the mean;
- **(B)** single-seed A/B carries SE ~0.033-0.037 against a 0.0457 gap;
- **(C)** IDENTITY 0.9936 is lenient + gated, not 94-class accuracy.

Findings below were **re-verified locally**. Where I did not verify, it says so.

## Verified, and corrected in README/CLAUDE.md

**1. `char_acc` is not "style fidelity" (the project's central framing).**
`eval_checkpoint.compute_char_acc` builds a 94x94 cosine matrix within each font
against that font's OWN GT cells and matches when `argmax_j sim(gen[i],gt[j])==i`.
Its docstring: *"within a single font, all 94 cells share the same style, so
cosine similarity within a font is dominated by glyph identity."* Style is
**controlled for** by construction. The two-axis story survives only in its
narrow form — char_acc is not exact letter correctness — not in the form that
names the residual "style".

**2. R-ACC is OCR consistency, not correctness.** `match = gt_decoded ==
gen_decoded`. Recomputed on committed data: **30.7%** (baseline) and **31.9%**
(glyph) of R-ACC "successes" are the OCR emitting the *same wrong string* for
both images. The README labelled it "OCR reads it back".

**3. DPO was never run.** `research/2026-06-03-generator-track-decision.md:133`
records the three negative runs as **Stage A SFT self-distillation**; line 149
says *"Do not pursue Stage B (the multi-day diffusion-DPO run)"*. The README
said "DPO — closed ... Stage A regressed three times". DPO is **untested**.

**4. The 0.87 diversity ratio is 7 fonts, not 50.** `audit_diversity.DISTINCTIVE`
is a hand-picked list of seven. No CI, no seed replication.

**5. char_acc and DINOv2 are one evidence family.** Same encoder; per-font
Pearson 0.925 (baseline) / 0.736 (glyph) per the audit. Reporting both as
independent confirmation double-counts one representation.

**6. The `atlas_to_font` CLI sliced trained-model atlases with the superseded
`compute_grid()`**, and its `--charset` default was the 71-char V3 set against
95 cells. Fixed in `086e622`; verified 72 -> 95 glyphs.

## Reported by the audit, NOT independently verified

Recorded so they are not mistaken for confirmed:

- The wrong-letter rate: audit recomputes 151/2,191 scored = **6.89%**, not
  151/4,700 = 3.2%, because ~2,509 cells are abstentions counted as correct.
  Mechanically dropping Bitcount/Rubik gives ~2.49%, not the claimed ~1%.
  README corrected to state this, flagged as the audit's arithmetic.
- The "88.6% already identity-correct at seed 0" script
  (`analysis/check_identity_vs_fidelity_gap.py`) is said to label itself
  GT-gated while never loading GT.
- Exact-identity recomputations (4B 0.9207 vs 9B 0.9355; baseline-vs-glyph
  p~0.77 under exact identity).

## Standing

The honest summary of this repo's quantitative record: **a development log, not
a confirmatory evaluation.** Point estimates describe specific stored
checkpoints at specific seeds. What survives strongly:

- the template-zeroing mechanism (9B .5000->.0248, 4B .3050->.0284 — replicated
  on both bases, three fonts);
- the conditioning-mismatch defect (exact identity .9164->.9355, 42 fonts
  better, none worse);
- the qualitative two-axis point: char_acc 0.69 against identity 0.92-0.99 on
  every definition.

## Not audited

`audit-prepublication` was refused by a safety filter for asking to scan for
credentials; the metrics audit's threshold/caching sections and the tests and
doc-coherence audits are extracted but not yet acted on.
