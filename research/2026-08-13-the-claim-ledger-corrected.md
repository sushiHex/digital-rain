# The claim ledger, corrected: six effects DO clear 2 SE, and most are negative

2026-08-13. Supersedes the effect table in
`research/2026-08-13-training-run-variance-measured-at-last.md`, which was wrong
in three ways. `analysis/claim_ledger.py`, `research/claim_ledger.json`.

> **Records note, 2026-09-13.** `research/claim_ledger.json` was regenerated
> against a five-run σ, on which four effects clear 2 xSE rather than six
> ([`2026-09-13-five-runs-and-the-noise-floor-moved.md`](2026-09-13-five-runs-and-the-noise-floor-moved.md)).
> The three-run ledger this note describes is preserved as
> `research/2026-08-13-claim_ledger.json`.

---

## What the earlier note got wrong

1. **"Nothing reaches 2 SE" is false.** It tabulated each claim against only the
   single metric it had originally been reported on. Scored on **every** metric,
   six effects clear 2 xSE.
2. **One row divided a dinov2 effect by char_acc's SD** (0.50 xSE published;
   1.36 metric-matched). The same mistake hit the lever rows, quoted at
   "0.03 SE" using char_acc's SD for composite effects — off by ~20x.
3. **Two sign errors.** The LR-horizon fix is a *regression* on every metric,
   not +0.0277; oversampling is −0.0027 composite, not +0.0030.

Training-run SD, 3 runs, 2 df (~12x-wide CI on each):

    composite 0.0035   char_acc 0.0618   dinov2 0.0228   racc 0.0080   lpips 0.0027

---

## The ledger

Every claim on every metric, in quality space (LPIPS sign flipped), each divided
by **its own** metric's training-run SD. Cells are `delta / xSE`.

| claim | composite | char_acc | dinov2 | racc | lpips |
|---|---|---|---|---|---|
| glyph vs baseline LoRA | −0.0003 / −0.1 | +0.0235 / +0.3 | +0.0243 / +0.8 | −0.0124 / −1.1 | +0.0009 / +0.2 |
| 4B → 9B | −0.0025 / −0.5 | +0.0368 / +0.4 | +0.0192 / +0.6 | +0.0082 / +0.7 | **−0.0164 / −4.3** |
| rank 64 | +0.0024 / +0.5 | −0.0002 / −0.0 | +0.0037 / +0.1 | −0.0000 / −0.0 | +0.0036 / +0.9 |
| oversampling | −0.0033 / −0.7 | −0.0095 / −0.1 | −0.0109 / −0.3 | −0.0089 / −0.8 | +0.0029 / +0.8 |
| rank64 + oversampling | **−0.0389 / −7.8** | −0.0443 / −0.5 | −0.0340 / −1.1 | **−0.0226 / −2.0** | **−0.0517 / −13.5** |
| corpus expansion v3 | +0.0011 / +0.2 | −0.0419 / −0.5 | −0.0213 / −0.7 | +0.0060 / +0.5 | +0.0045 / +1.2 |
| LR-horizon fix | −0.0080 / −1.6 | −0.0293 / −0.3 | −0.0087 / −0.3 | −0.0082 / −0.7 | **−0.0077 / −2.0** |
| licence filter (838) | **−0.0088 / −2.2** | −0.0723 / −1.0 | −0.0396 / −1.5 | −0.0092 / −1.0 | +0.0008 / +0.3 |

`xSE` **ranks** effects; it establishes none. σ rests on 2 df with a ~12x CI, so
treating 2.0 as a significance threshold would be false precision.

---

## The pattern nobody was looking for

**Every resolvable effect lives on LPIPS or composite — the two stable metrics —
and ALL SIX are NEGATIVE.**

> **Corrected 2026-08-18.** This section originally read "five of the six are
> NEGATIVE". That was a miscount: `analysis/claim_ledger.py` lists six cells at
> ≥2 xSE and every one of them is a regression (the sixth, rank64 + oversampling
> on R-ACC, is −2.00). The error propagated to `CLAUDE.md`, `README.md` and
> `docs/what-happened.md`, all now fixed. Caught while building
> `viz/variance_vs_effects.py`, which recomputes the list from the ledger JSON
> instead of quoting the prose.

The project spent its life optimising char_acc and DINOv2. Those two are the
noisiest instruments here (SD 0.0618 and 0.0228 against LPIPS's 0.0027), and a
retrieval baseline that returns a *different real font* beats every model on
both. Meanwhile the metrics that *could* resolve differences were quietly
reporting that several changes made things worse:

- **rank 64 + oversampling: −13.5 xSE on LPIPS, −7.8 on composite.** The
  largest real effect in the repository, and it is a regression. Confirmed
  mechanically: generated ink 0.0780 against a GT 0.0652, +20% over-inked,
  exactly the defect CLAUDE.md documents. "Do not stack levers" was right, and
  is now the best-supported claim the project has.
- **4B → 9B: the 9B is WORSE on LPIPS by 4.3 xSE** (0.1532 vs 0.1381), while
  its char_acc and dinov2 advantages sit under 1 xSE. Not an ink artifact —
  ink is 0.0638 vs 0.0632, essentially identical. So the flagship "the 9B is
  better" rests entirely on the two metrics that cannot resolve it, and the one
  metric that can says the opposite.
- **The LR-horizon fix is a regression at −2.0 xSE on LPIPS**, on every metric.
  It remains correct on first principles — a cosine schedule that never anneals
  is a bug whatever the score — but it should stop being described as an
  improvement. It has never been measured as one.
- **The licence filter costs −2.2 xSE on composite** (−0.0088). This is the one
  claim that survives, at roughly a *tenth* of the originally published −0.133.

---

## What this changes

- **"Nothing reaches 2 SE" is retracted.** Some things do. They are mostly
  regressions, and they were invisible because the project was reading the
  wrong instruments.
- **Composite and LPIPS should be the headline metrics**, not char_acc and
  DINOv2. They are 8–20x more stable, they are the only ones that detect
  anything here, and they are not beaten by trivial retrieval.
- **"The 9B is the quality model" is not supported** by the metrics able to
  test it. That does not make the 4B better; it makes the comparison unresolved
  in a way the earlier six-seed work could not see, because it too was scored on
  char_acc and dinov2.
- **The strongest empirical result in the project is a negative one**: stacking
  rank 64 with oversampling makes the model measurably, largely worse.

## Method note

Every number here is computed by a committed tool from committed artifacts, and
the two counter-narrative results (9B worse on LPIPS; stacking catastrophic)
were checked against generated ink before being written down, because both are
the shape an ink-weight artefact would take. Only the stacking one is.
