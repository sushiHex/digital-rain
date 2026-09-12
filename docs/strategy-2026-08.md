# Forward strategy, August 2026

Written 2026-08-10, after a session that produced 17 corrections to the
published record — six of them to work done in that same session. This is an
attempt to turn that into direction rather than a list of apologies.

---

## Outcome, recorded 2026-08-18

**Every item in §5's ordered plan was executed.** The document is left standing
as a dated position paper; this section is the scorecard, because a plan that
can be checked against what happened is worth more than one quietly revised.

| § 5 item | outcome |
|---|---|
| 1. Oracle-reference gap | **Done, and it was a non-issue.** All degradation tiers inside noise; the pipeline's 512px resize confers the robustness. Caveat: the screenshot tier degraded *above* 512 and was nearly a no-op, so the breaking point was never found. |
| 2. Training-run variance | **Done, and it was the whole story.** char_acc SD 0.0618 across three identical-config runs; `compare_runs.py` fires on two of the three pairs. |
| 3. Per-cell DINOv2 medoid | **Built, and it is weak.** Captures 4.2% of the reserve; classifier confidence scores *worse than doing nothing*. Three selectors, one mechanism, family closed. |
| 4. Evaluate the finished font | **Not done, and still the top open item.** The font *builder* was fixed — cap height was 41% too small — but scoring still happens on atlas cells. Now item 2 of the README's "To be continued". |
| 5. Corpus / replacement, with error bars | **Audited, not retrained.** Provenance resolved and committed; the replacement-set training run was never justified once the noise floor was known. |

**The prediction in §2 was correct**, and stronger than it was stated: *"might
show that the entire lever programme was noise."* It did. Scored on every metric
against its own SD, six effects clear 2×SE and **all six are regressions**.

**Two claims in this document did not survive.**

- §1 calls the licence-clean corpus *"the one surviving effect, 2.2 xSE"*. It is
  **−2.2×SE** — a regression — and it is one of six resolvable effects, not one
  of one. The table's own value (−0.0088 composite) already carried the sign.
- §3's *"best-of-N may be the only route to a shippable commercial model"* was
  overtaken on 2026-08-13. A zero-GPU retrieval baseline — hand back the nearest
  *training* font — beats every model here on both style metrics. The bottleneck
  is not the reserve; it is that the instrument cannot tell generation from
  returning a similar real font.

§6's portfolio judgement stands, and the four decisions it named have been made:
the repo is `digital-rain`, on `main`, private, all rights reserved pending a
licence choice.

---

## Outcome, recorded 2026-08-24 — the framing itself was the stale part

The scorecard above grades this document against its own plan. Six days later
the plan's *frame* is what expired: every item in §5 assumes a target font, and
the product does not have one.

**§4 is now half-closed, and the half that closed is not the half it named.**
Gap 1 (oracle references) is answered — no degradation tier broke the model, and
a reference *invented from a text description* does not break it either, which
is a distribution shift rather than a degradation and was the larger risk. Gap 2
(the finished font) is scored and remains open: `analysis/score_finished_font.py`
found a 2× word-spacing defect and established that **74% of the finished font's
letterfitting error is the pipeline**, not the model.

**What §4 did not anticipate is the axis that decides the product.** With no
target font there is no ground truth, so three GT-free axes replace the six
metrics: *coherence* (is it one typeface), *identity* (are they the right
letters), and *adherence* (is it the typeface asked for). The first two now have
validated instruments. The third has **none** — generic CLIP was tried and ruled
out at exactly chance on a pre-registered minimal-pair test (6/12, p=0.6128),
and adherence currently rests on the author's eye.

**§2's judgement — "the measurement problem is the bottleneck" — survives the
reframing intact, and is the reason to trust it.** It was written about the
model track and it transferred unchanged: the loop runs end to end in ~90 s on
Apache-2.0 weights, and the thing stopping it from being a claim is still an
instrument, not a model.

One correction to the frame, for the record: **the retrieval floor does not
apply to the product track.** There is nothing to retrieve against when no
target font exists. The floor that closed the model track must not be quoted as
a bar the product has to clear, nor its absence as evidence the product works.

---

## 1. Where quality actually lives

Rank the effects the project has measured, by size:

| effect | size (char_acc) | status |
|---|---|---|
| **best-of-N oracle headroom** | **+0.164** | real; per-cell medoid captures 4.2%, identity-space selectors are orthogonal (rho=0.038) |
| 4B → 9B | +0.073 char_acc | **not established** — 0.4 xSE; and the 9B is WORSE on LPIPS at 4.3 xSE |
| **licence-clean corpus** | **−0.0088 composite** | the one surviving effect, 2.2 xSE (the −0.133 char_acc figure used an unlucky seed) |
| oracle → realistic reference | ~−0.02 char_acc | measured: small; the 512px resize confers robustness |
| every training lever tried | ~0.003 | at or below noise — EXCEPT stacking rank64+oversampling, −7.8 xSE composite |

The project spent most of its effort on the bottom row. The levers — rank,
oversampling, corpus composition, stacking — move composite by ~0.003 against
an inference SE of ~0.037. **They were never measurable.** That is not a
failure of the levers; it is a failure to check the noise floor before
optimising against it.

Everything large is in: the base model, sample selection, input fidelity, and
corpus licensing. Only one of those four is a training-time concern at all.

**Strategic consequence: stop running lever experiments.** No plausible lever
produces an effect this instrument can resolve.

---

## 2. The measurement problem is the bottleneck

Errors found this session cluster into exactly two families, and both are
invisible to the headline metric:

**(a) Statistics conditioned on the thing being measured.** The redistribution
signature (retracted), the hard/easy split, the distinctiveness moderator on the
licence result (+0.761 → +0.247 once baseline was controlled). Each looked like
a finding and was partly arithmetic.

**(b) Silent contract mismatches.** Prompt style, template drift, the LR
horizon in microbatch units, the SNR weighting divided to 1.0, cell-clustered
bootstraps, `bool()` on continuous metrics. Each ran for months without a
failing test, because nothing checked the contract — only the loss.

The unifying property: **the primary metric cannot see either family.** Loss was
healthy through the LR bug. char_acc was healthy through the conditioning bug.
That is why adversarial review, not more experiments, has been the productive
activity.

**The single largest hole remaining: training-run variance has never been
measured.** Every variance number here is *inference* variance. No
checkpoint-vs-checkpoint comparison in this repo — past or future — has a known
error bar. Two runs on one corpus with different seeds (~22 GPU-h) would
retroactively calibrate every comparison the project has ever made, and might
show that the entire lever programme was noise. That is a reason to run it, not
a reason to avoid it.

---

## 3. The best idea nobody has tried

**Per-cell medoid selection in DINOv2 space.**

The best-of-N headroom is **+0.164** — 2.2× the 4B→9B gap and 50× any lever.
It is the largest known quality reserve in the project and nothing harvests it.
Read the two closure notes together:

- *Seed- and atlas-level DINOv2 medoid*: fails. "the style lottery is
  **per-cell, not per-atlas**, which rules out every seed-level and atlas-level
  selector. **Only a per-cell signal can work.**"
- *Per-cell OCR selection* (TrOCR 4.3%, GOT-OCR2 4.7%): fails. "The oracle
  headroom is defined in **DINOv2 space**; OCR-based selectors optimize a
  different space they agree with only ~65% of the time."

**These are orthogonal failures.** One had the right space and the wrong
granularity; the other had the right granularity and the wrong space. The
combination — per-cell, in DINOv2 space — was never built, and the project's own
notes point straight at it.

The mechanism is self-consistency: if each cell's errors are idiosyncratic
across seeds, the medoid cell is the consensus cell, and consensus should track
correctness. It needs no ground truth, so it is deployable, and it is testable
on **data already on disk** (`bestofn_4b/`: 6 seeds × 50 fonts of generated
atlases) for the cost of DINOv2 embeddings — no generation, no training.

This matters more now than it did a week ago. If the licence-clean 4B really
sits near 0.48 char_acc against the 9B's ~0.69, **best-of-N may be the only
route to a shippable commercial model.** It moves from "closed track" to
"critical path".

Caveat, stated up front: per-cell selection changes inference cost by N× and
composes an atlas from cells drawn from different samples, which may introduce
seams the atlas-level metrics do not see. Check ink and inspect output, not just
char_acc.

---

## 4. Product reality, still unmeasured

Two gaps between every number in this repo and a working product:

1. **Oracle references.** Every published score renders the reference from the
   target font's own TTF via the pipeline that made the ground truth. Users
   upload screenshots. Being measured now (`run_nonoracle_eval.sh`).
2. **The finished font has never been evaluated.** Scoring happens on atlas
   cells; the product traces them into an OTF with naive spacing and no
   kerning. An atlas can win while producing the less usable font, and nothing
   has ever scored the artefact the user actually receives.

Gap 2 is arguably the more damning, and it is cheap to start: render the traced
OTF as text specimens and compare against the same text set in the real font.

---

## 5. Ordered plan

1. **Oracle-reference gap** — in flight. If quality collapses, the product
   thesis needs rethinking before anything else is worth doing.
2. **Training-run variance** — 2 runs, one corpus, different seeds. Calibrates
   everything retroactively.
3. **Per-cell DINOv2 medoid** — cheap, targets the largest known reserve, and
   may be what makes a licence-clean model viable.
4. **Evaluate the finished font**, not the atlas.
5. **Then** revisit the corpus/replacement question, with error bars.

Explicitly deprioritised: further levers, benchmark v2 (do not build a new
instrument before the old one's noise floor is known), the replacement-set
training run (it tests a mechanism on an uncalibrated instrument).

---

## 6. On the portfolio goal

The most valuable artefact in this repository is not the font generator. It is
the record of a project repeatedly catching and correcting its own errors —
including a retraction of its headline "five levers, one ceiling" finding, and a
published correction to a result the author had announced two hours earlier.
That is rare, and the README already opens by saying so.

**It is publishable now.** The licensing blockers prevent shipping *weights* and
a *hosted demo*; they do not prevent publishing code and findings. The four
decisions (repo name, `master`→`main`, licence, visibility) are the owner's.
