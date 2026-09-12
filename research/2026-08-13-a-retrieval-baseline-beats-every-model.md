# Handing back a different real font beats every model here

2026-08-13. Two findings from a six-axis audit, both reproduced independently
before being written down.

---

## 1. A zero-GPU retrieval baseline outscores every trained checkpoint

For each holdout font: embed its **reference image** with DINOv2, find the
nearest font in the 925-font training corpus, and return **that font's ground
truth atlas** as if it were a generation. No model, no GPU training, no
adapter.

`analysis/retrieval_baseline.py`, leak-guarded (see §2):

| | retrieval | 9B glyph | 4B r32 lrfix | 4B r32 clean (3 seeds) |
|---|---|---|---|---|
| char_acc | **0.7768** | 0.6917 | 0.6183 | 0.4914–0.6070 |
| dinov2 | **0.9389** | 0.8788 | 0.8388 | 0.7770–0.8213 |

Against the measured training-run SDs (char_acc 0.0618, dinov2 0.0228), the
margin over the *best* model is **+1.4 SD on char_acc and +2.6 SD on dinov2** —
larger than any effect this project has ever pursued, in the wrong direction.

### What this does and does not mean

It does **not** mean retrieval is a product. Retrieval cannot produce a typeface
that does not already exist — which is the entire point of the model — and
shipping it would mean redistributing someone else's font.

It means: **the metric suite cannot distinguish "generated this typeface" from
"returned a different, clean, real font."** Every model comparison in this
repository is built on char_acc and DINOv2. A trivial non-generative baseline
scores higher on both. So those metrics have been measuring *general
font-likeness*, not the thing the project cares about.

This reframes several earlier findings rather than contradicting them:

- `char_acc` was already known not to be letter correctness, and its own
  docstring says style is largely controlled for. This shows it is not style
  fidelity either, in the sense that matters: a *different* typeface scores
  better than the model's attempt at *the right* one.
- The two-axis rule (identity vs style) survives — IDENTITY is the one metric
  where the model leads retrieval, and it is the one already documented as
  lenient.
- The training-variance result is unaffected and, if anything, reinforced: we
  now know the instrument is both noisy *and* pointed at the wrong quantity.

**The first question a sceptical reviewer asks is "what does your model beat?"
The honest answer today is: nothing this instrument can measure.**

---

## 2. Eight holdout ground-truth atlases are byte-identical to training atlases

Verified by SHA-256 over `eval_holdout/atlases/` against `dataset_v2/atlases/`:

| holdout font | identical training atlas |
|---|---|
| AkayaTelivigala-Regular | AkayaKanadaka-Regular |
| BitcountPropDoubleInk[…] | BitcountPropDouble[…] |
| JainiPurva-Regular | Jaini-Regular |
| KaiseiOpti-Regular | KaiseiDecol-Regular |
| MochiyPopPOne-Regular | MochiyPopOne-Regular |
| ReemKufiFun[wght] | ReemKufi[wght] |
| Tirra-Regular | Akatab-Regular |
| WDXLLubrifontTC-Regular | WDXLLubrifontJPN-Regular |

**This is exact answer leakage**, and it is strictly worse than the documented
caveat that "32 of the 50 holdout fonts share a superfamily with a training
font". These are not siblings — the 95-character ASCII atlases are the same
bytes. For 8 of 50 fonts, the correct answer was in the training set.

All eight corpus twins are in the 838-font licence-clean keep set
(`research/corpus_exclusions.json`), so the leak is present in the shipped
lineage too, not only in historical runs.

`analysis/check_holdout_integrity.py` hashes the holdout **against itself** —
which is how it found the 46-unique-atlases and shared-reference problems — but
it never hashed the holdout against the *corpus*. That is the gap.

---

## Consequences

1. **The holdout cannot demonstrate generation.** Between the retrieval floor
   and the exact leakage, a strong score on this benchmark is not evidence that
   the model generated anything.
2. **Every benchmark built from here needs one hard acceptance criterion:
   nearest-neighbour retrieval must FAIL on it.** `docs/benchmark-v2-spec.md`
   does not contain that criterion and must not be built until it does.
3. **The metric problem is upstream of the noise problem.** Measuring training
   variance told us the instrument is imprecise; this tells us it is aimed
   somewhere else. Fixing precision on a mis-aimed instrument is not progress.

## Method note

Both findings came from an adversarial audit, and both were reproduced from
scratch before being recorded — the retrieval numbers by re-implementing the
baseline independently (`analysis/retrieval_baseline.py`), the leakage by
direct SHA-256 comparison. The audit also caught three errors in
`research/2026-08-13-training-run-variance-measured-at-last.md`, including the
false claim "Nothing reaches 2 SE": the licence filter is **2.16 SE on
composite**, because that note tabulated each claim against only the single
metric it was originally reported on. Corrections to that note are pending.
