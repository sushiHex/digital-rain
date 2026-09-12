# The oracle-reference gap is small; per-cell medoid is real but weak

2026-08-12. Two experiments from the strategy in `docs/strategy-2026-08.md`.

---

## 1. Degrading the reference costs almost nothing

Checkpoint `training_glyph_4b_r32_5000_lrfix/final`, oracle baseline 0.6183.
Ground truth identical across tiers; **only the reference image changed**.

| tier | effective ref px | char_acc | Δ | dinov2 Δ | identity Δ |
|---|---|---|---|---|---|
| oracle (published) | 1280 | 0.6183 | — | — | — |
| screenshot | 704 | 0.6140 | −0.0043 | +0.0032 | −0.0005 |
| upload | 486 | 0.6202 | +0.0019 | +0.0075 | +0.0005 |
| photo | 409 | 0.5930 | **−0.0253** | −0.0005 | +0.0018 |

Every delta is inside single-seed noise (SE ≈ 0.037). The worst case — 409px,
±1.8° rotation, Gaussian blur, JPEG-45, uneven lighting and sensor noise —
costs **0.7 SE**.

**The May prediction that quality "WILL drop sharply" on non-oracle references
does not hold for these inputs.** This is the first clearly good news the
project has had in a while.

### Why, and the design flaw that limits the claim

`generation_lib` resizes every reference to **512×512 LANCZOS** before the VAE.
The model never sees more than 512px, so degradation *above* that resolution is
erased before it reaches anything.

That makes the `screenshot` tier (704px) close to a no-op — a wasted arm, and
my error in calibrating the tiers against a bottleneck I had not checked. Only
`upload` (486px) and `photo` (409px) probed below it, and even they held.

So the honest claim is narrower than the table suggests:

- **Established:** input degradation down to ~410px, with realistic photo
  artefacts, costs at most ~0.025 char_acc.
- **Not established:** where the breaking point is. The test never found one,
  because no tier was hard enough. 256px, heavier compression and larger
  rotations would be needed to locate it.
- **Not tested at all:** input *provenance*. Every reference here is still the
  target font's own glyphs rendered by this pipeline, merely degraded. A real
  user's reference differs in rasteriser, hinting, anti-aliasing and ink
  spread. This isolates fidelity, not origin.

The mechanism is itself a useful product fact: **the 512px bottleneck buys
robustness for free.** Anything a user uploads above that resolution is
equivalent to the oracle.

---

## 2. Per-cell medoid: the granularity hypothesis is right, the signal is weak

`analysis/per_cell_medoid.py`, on the 6 seeds × 48 fonts already in
`bestofn_4b/`. No generation, no training.

| strategy | char_acc | vs seed0 | % of headroom |
|---|---|---|---|
| seed0 (shipped behaviour) | 0.6496 | — | — |
| atlas_medoid (known-failure control) | 0.6299 | −0.0197 | −16.2% |
| **cell_medoid (the candidate)** | **0.6547** | **+0.0051** | **4.2%** |
| oracle_cell (ceiling, not deployable) | 0.7711 | +0.1215 | 100% |

Paired Wilcoxon on per-font means:

- `atlas_medoid` vs seed0: p=0.115, 18 better / 25 worse — reproduces its
  recorded failure directionally, so the harness is behaving.
- **`cell_medoid` vs `atlas_medoid`: +0.0248, p=0.00037, 34 better / 11 worse.**
- `cell_medoid` vs seed0: +0.0051, p=0.422, r=0.116 — **fails** the project's
  p<0.05 ∧ r≥0.3 gate.

### What that means

**The granularity hypothesis is confirmed.** Choosing per cell beats choosing
per atlas decisively (p=0.0004). The repo's own conclusion — *"the style lottery
is per-cell… only a per-cell signal can work"* — is correct, and this is the
first direct test of it.

**But the signal is not strong enough to matter.** Per-cell medoid does not
beat a single seed by any standard this project accepts, and captures 4.2% of a
+0.1215 reserve. Consensus in DINOv2 space is a weak proxy for correctness:
seeds agree on plausible-looking cells as readily as on right ones.

So this is a negative result with a positive sub-finding. The direction is
validated; medoid is the wrong estimator.

### A bug worth recording

The first run scored **36 of 48** fonts. `glob` reads the brackets in
variable-font stems (`InterTight[wght]`, `MirandaSans[wght]`) as a character
class, so those directories matched nothing and were silently skipped —
including every variable font in the holdout. Replaced with `os.listdir`.

Fixing it made the result **worse**: captured headroom fell 7.3% → 4.2%. A
silent subset had flattered the candidate.

---

---

## 3. The classifier selector fails too — and it closes a whole family

Predicted above that `glyph_classifier`'s per-cell confidence would beat the
OCR selectors because it is trained on this domain. **It does not. It loses to
doing nothing** (`analysis/per_cell_classifier_select.py`, same 48 fonts):

| strategy | char_acc | vs seed0 | % of headroom |
|---|---|---|---|
| seed0 | 0.6496 | — | — |
| cell_medoid (DINOv2 consensus) | 0.6547 | +0.0051 | 4.2% |
| **cell_conf (classifier)** | **0.6394** | **−0.0102** | **−8.4%** |
| cell_combo (conf, medoid tie-break) | 0.6507 | +0.0011 | 0.9% |
| oracle_cell (ceiling) | 0.7711 | +0.1215 | 100% |

### The measured reason, on 8,460 cells

Per-cell classifier confidence in the expected character, against per-cell
DINOv2 similarity to the ground-truth cell:

    Spearman rho = +0.038   (p = 5e-4 only because n = 8,460)

**Not anti-correlated — orthogonal.** Identity confidence carries essentially
no information about whether a cell is close to the target in the space the
headroom is defined in. So selecting on it is, with respect to that headroom,
approximately random.

That also explains the exact magnitude of the loss. Random selection among six
seeds lands near the seed *mean*, and seed 0 is an above-average draw (0.6304
against a 0.6116 six-seed mean, `bestofn_4b`). Selecting randomly therefore
scores slightly *below* just keeping seed 0 — which is what −0.0102 is.

### What this closes

**One mechanism now explains three failures**: TrOCR (4.3%), GOT-OCR2 (4.7%)
and this classifier (−8.4%) are all *identity* signals, and identity is
orthogonal to style proximity at ρ = 0.038. No amount of making the identity
recogniser better will help, because the axis is wrong. This is the two-axis
rule from CLAUDE.md reappearing as a selection problem.

**Do not try further OCR or classifier variants for best-of-N selection.**

### What is left

The reserve is still +0.12 and the constraints are now sharp: the signal must be
**per-cell** (granularity confirmed, p=0.0004) and **in style space** (identity
space measured useless). The only style-space per-cell signal tried is
consensus, at 4.2%. Untried candidates in that intersection:

- per-cell coherence with the style implied by the font's *other* cells —
  though note this risks gaming char_acc, which is itself a within-font
  nearest-neighbour statistic, so it needs a second metric to be believed;
- a learned per-cell quality head trained on GT similarity directly, which is
  the honest version of "predict the oracle";
- accepting that a no-GT selector may simply not exist at useful strength, and
  spending the effort on the base model instead.
