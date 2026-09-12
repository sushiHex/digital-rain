# Hybrid Replay: no-GT OCR-swap realization of the oracle hybrid (Task 2)

**Verdict: GATE FAIL** (char_acc gate and Wilcoxon-vs-glyph@5000 gate both fail; diversity-ratio
gate also fails but is inherited from the baseline substrate, not caused by the swap rule).
Per the task-2 brief's FAIL-on-char_acc branch: **the OCR-selectable headroom implied by the
oracle hybrid (0.7711) is unrealizable at n=1/model using a no-GT OCR-swap selector. Hybrid is
demoted; Tasks 3→5 (template track) become primary.**

Code: `hybrid_replay.py` (repo root). Outputs: `eval_runs/hybrid_replay/{generated/, per_cell.json,
scores.json}` (scores.json force-added to git; the rest is gitignored/reproducible).

---

## 0. Setup recap

Two generators evaluated on the same 50-font holdout, one per_cell record per (font, char):
- baseline: `eval_runs/structured_prompt_5000/`
- glyph-cond: `eval_runs/glyph_r32_5000/`

The **oracle hybrid** (picks whichever model's cell has `char_acc_match==1`, a DINOv2
template-match signal that needs GT atlas embeddings and is therefore *not* realizable at
inference time) reaches char_acc = 0.7711 over the split:

| | both_ok | only_base | only_glyph | both_fail |
|---|---|---|---|---|
| cells (of 4700) | 2730 | 408 | 486 | 1076 |

`hybrid_replay.py --step accounting` reproduces this split exactly from the raw per_cell.json
files (`matches known facts (2730/408/486/1076): True`), confirming the join logic is sound
before building anything on top of it.

This task builds the **realizable** version: a swap rule using only `racc_gen_decoded` (TrOCR's
read of the *generated* cell) compared case-insensitively against the expected character —
never `racc_gt_decoded`, which is GT-derived. See `hybrid_replay.py` module docstring for the
full metric-discipline statement.

**Swap rule:** take the glyph-cond model's cell iff `baseline.racc_gen_decoded.lower() !=
char.lower()` AND `glyph.racc_gen_decoded.lower() == char.lower()`.

---

## 1. Step-1 accounting

### (a) racc_match vs char_acc_match agreement matrix

`racc_match` = TrOCR(gt_decoded) == TrOCR(gen_decoded) (GT-consistency, not the swap rule's own
signal). `char_acc_match` = DINOv2 template-match (the research/oracle metric).

| model | racc=T,char_acc=T | racc=T,char_acc=F | racc=F,char_acc=T | racc=F,char_acc=F | agreement |
|---|---:|---:|---:|---:|---:|
| baseline | 2441 | 1042 | 697 | 520 | 63.0% |
| glyph-cond | 2542 | 949 | 674 | 535 | 65.5% |

The two metric spaces agree ~63-66% of the time — meaningfully less than perfect, which is the
whole reason a no-GT accounting step is needed before trusting an OCR-only selector as a proxy
for the DINOv2-space oracle.

### (b) No-GT rule capture rate, in BOTH metric spaces

**char_acc (DINOv2) space** — the space the 486/408/2730/1076 oracle split lives in:
- Of the **486 only-glyph** cells (glyph right, baseline wrong per DINOv2): rule captures
  **21/486 = 4.3%**.
- Of the **408 only-baseline** cells (baseline right, glyph wrong per DINOv2): rule wrongly
  swaps away **12/408 = 2.9%** of them.
- Net: 21 helpful swaps − 12 harmful swaps = **+9 cells**, i.e. a predicted char_acc delta of
  `+9/4700 = +0.0019` over baseline. **This capture rate is the central finding: the OCR signal
  barely overlaps with the DINOv2-defined complementarity set.**

**racc-native space** (correctness defined the same way the rule itself is defined — does
`racc_gen_decoded` match the expected char):
- both_ok=2654, only_base=275, **only_glyph=198**, both_fail=1573
- rule captures 198/198 (100%) of racc-only-glyph and wrongly swaps 0/275 (0%) of
  racc-only-baseline — **tautological by construction** (the rule's firing condition *is* the
  definition of racc-only-glyph), included as a self-consistency check, not a finding.
- Cross-tab: of the 198 racc-only-glyph cells, only **21 (10.6%)** are also DINOv2-verified good
  (char_acc-space only-glyph); of the 275 racc-only-baseline cells, only **33 (12.0%)** are also
  DINOv2-verified good-baseline. Roughly 88-90% of what the OCR rule "sees" as a clear win/loss
  doesn't correspond to a DINOv2-space win/loss at all — TrOCR's read-back success on a 4-char-max
  decode is a much noisier, more permissive signal than DINOv2 template matching.

**Total swaps fired:** 198 (all `n=1/model`, no consensus-medoid at n=2 — see Step 2 note).
Forecast (helpful=21, harmful=12, neutral=165) predicted a char_acc delta of **+0.0019**; the
real scored delta (0.6696 − 0.6677 = **+0.0019**) matched exactly, validating the accounting.

### (c) TrOCR-blind symbol table

| char | n | base racc_ok | glyph racc_ok | base char_acc | glyph char_acc |
|---|---:|---:|---:|---:|---:|
| `"` | 50 | 0.00 | 0.00 | 0.76 | 0.60 |
| `'` | 50 | 0.00 | 0.00 | 0.54 | 0.28 |
| `0` | 50 | 1.00 | 1.00 | 0.72 | 0.60 |
| `O` | 50 | 0.02 | 0.02 | 0.56 | 0.30 |
| `\` | 50 | 0.00 | 0.00 | 0.78 | 0.06 |

Quotes and backslash are read correctly by TrOCR essentially **never** (0.00-0.02), regardless of
how good the underlying glyph is per DINOv2 (baseline `\` char_acc is 0.78 — mostly correct
glyphs — yet racc_ok is 0.00). The no-GT rule cannot confirm OR rescue these symbol cells: it
will never fire "helpful" on them (glyph's decode can't read back correctly either) but also
never "harmful" in a way visible to this table. `0` is the one exception where TrOCR reads
cleanly both ways. This is an honest, pre-registered blind spot of the whole approach, not a
defect introduced here.

### (d) Both-fail ceiling

**1076 / 4700 = 22.9%** of cells have neither model producing a DINOv2-correct glyph. This is a
hard ceiling: no 2-candidate selector (oracle or realized) can rescue these cells; the true
"reachable" ceiling for ANY hybrid built from just these two runs is `1 − 0.229 = 77.1%` (matches
the oracle's 0.7711 exactly, as expected).

---

## 2. Swap statistics (Step 2 compositing)

`python hybrid_replay.py --step composite` wrote 50 atlases to
`eval_runs/hybrid_replay/generated/` (all 50 holdout fonts; unswapped fonts are byte-identical
baseline copies).

- **Total swaps: 198** across **48/50 fonts** (2 fonts — Dangrek-Regular, RubikDistressed-Regular
  — had zero swaps).
- **Max swaps in one font: 10** (PlaywriteUSTradGuides-Regular, out of 94 drawn cells = 10.6%).
- Per-font swap counts range 0-10, median ~4 (full per-font list printed by the script; see
  verification evidence below). **No font reaches the 40-cell high-mixing-risk proxy threshold**
  — the highest is 4x below it.

NOTE (per brief): pool is n=1/model here — this tests the OCR-swap rule only. The
consensus-medoid mechanism is vacuous at n=2 and is explicitly not exercised by this task.

---

## 3. Scoring (Step 3)

`python eval_checkpoint.py --skip-generate --holdout eval_holdout --out eval_runs/hybrid_replay`
(verified against `--help`: `--skip-generate` only requires `--holdout` + `--out`, no
`--checkpoint`; re-scores the composited PNGs already on disk).

| run | lpips | racc | dinov2 | char_acc | composite |
|---|---:|---:|---:|---:|---:|
| baseline (structured_prompt_5000) | 0.1514 | 0.7411 | 0.8487 | 0.6677 | 0.8110 |
| glyph-cond (glyph_r32_5000) | 0.1532 | 0.7428 | 0.8738 | **0.6843** | 0.8144 |
| **hybrid_replay** | 0.1513 | 0.7438 | 0.8501 | **0.6696** | 0.8122 |

Hybrid's char_acc (0.6696) is **below baseline's own char_acc (0.6677) by only +0.0019** — matching
the Step-1 forecast exactly — and **below glyph-cond's char_acc (0.6843)**. Hybrid's aggregate
DINOv2 (0.8501) sits close to baseline (0.8487), far from glyph's 0.8738 — expected, since only
4.2% of cells (198/4700) actually changed.

95% CI on hybrid char_acc: [0.6562, 0.6828] (2000 bootstrap resamples) — does not reach 0.70.

## 4. Comparison vs glyph@5000 (Step 3, paired Wilcoxon, n=50 fonts)

`python compare_runs.py eval_runs/glyph_r32_5000/per_cell.json eval_runs/hybrid_replay/per_cell.json --label-a glyph_r32 --label-b hybrid_replay`

| metric | med(glyph) | med(hybrid) | delta | p | eff_r | verdict |
|---|---:|---:|---:|---:|---:|---|
| composite | 0.8462 | 0.8406 | −0.0044 | 0.8431 | 0.028 | no diff |
| **char_acc** | **0.7713** | **0.7287** | **−0.0160** | **0.0749** | **0.257** | **no diff (trend: hybrid worse)** |
| racc | 0.7979 | 0.8085 | +0.0000 | 0.9781 | 0.004 | no diff |
| dinov2 | 0.8938 | 0.8702 | −0.0165 | 1.9e-06 | 0.674 | SIG (glyph better) |
| lpips | 0.1364 | 0.1324 | −0.0110 | 0.0384 | 0.293 | sig but small effect (hybrid better) |

Full JSON: `research/2026-07-17-wilcoxon_glyph_r32_vs_hybrid_replay.json`.

---

## 5. Style coherence (Step 4)

### Diversity ratio (metric)

`python audit_diversity.py --gen-dir eval_runs/hybrid_replay/generated`:

| run | inter-font diversity (gen) | GT | ratio |
|---|---:|---:|---:|
| baseline | 0.221 | 0.273 | **0.81** |
| glyph-cond | 0.236 | 0.273 | **0.87** |
| **hybrid_replay** | 0.221 | 0.273 | **0.81** |

Hybrid's diversity ratio is **identical to baseline's**, not a regression the swap rule
introduced — expected, since 95.8% of hybrid's cells are unchanged baseline pixels, so the
per-font mean embedding driving this metric is dominated by baseline. It fails the 0.85 gate
threshold, but that failure is inherited from the baseline substrate, not caused by swapping.

### Visual sheets (eyeball, ransom-note check)

`audit_diversity.py --visual` (fixed probe chars a/g/e/R/Q/4/&) was run per the brief's
prescribed invocation — sheets in `audit_diversity/`. Because that tool's probe chars are fixed
and don't necessarily coincide with the actually-swapped cells, a supplementary targeted check
was also built (ad hoc, not committed) that renders **only the actually-swapped chars** per font,
row-stacked [baseline | glyph | hybrid], for the 6 highest-swap-count non-variable-font-named
fonts: PlaywriteUSTradGuides-Regular (10 swaps), KaiseiOpti-Regular (8), Suwannaphum-Regular (7),
IBMPlexSansArabic-Regular (6), Telex-Regular (6), UoqMunThenKhung-Regular (6).

**Finding: no visible ransom-note mixing in any of the 6 sheets checked.** Baseline and
glyph-cond render visually near-identical glyph style (stroke weight, slant, serif/sans
character) for every swapped char in every font checked — both models condition on the same
target-font reference image, so their outputs already share style; they differ mainly on
per-glyph *legibility*, not macro style. This is consistent with the diversity-ratio finding
above (macro style is a baseline-inherited property, and swaps don't disturb it locally either).

Controller/user follow-up: the remaining 42 fonts with nonzero swaps were not individually
eyeballed; if a full audit is wanted before shipping anything downstream, the swap-count
distribution (Section 2) is the actionable proxy — none exceed the 40-cell risk threshold, and
the two zero-swap fonts (Dangrek-Regular, RubikDistressed-Regular) need no review at all.

Three bracket-named variable fonts (MirandaSans[wght], MomoTrustSans[wght], PlaywriteCO[wght],
StackSansText[wght], Vazirmatn[wght]) could not be rendered by the ad hoc visual script because
`glob.glob()` treats literal `[...]` in a font name as a character class when concatenated into
a wildcard pattern — a pre-existing quirk of `audit_diversity.py`'s `_font_file()` helper, not
introduced by this task. These fonts' swap counts (2-7 each) are still covered by the numeric
swap-count proxy.

---

## 6. Gate evaluation (criterion-by-criterion)

| # | Criterion | Threshold | Actual | Verdict |
|---|---|---|---|---|
| 1 | hybrid char_acc | ≥ 0.70 | 0.6696 (95% CI [0.6562, 0.6828]) | **FAIL** |
| 2 | Wilcoxon char_acc vs glyph@5000 (0.6843) | p<0.05 ∧ r≥0.3, improvement | p=0.0749, r=0.257, delta **negative** (hybrid worse) | **FAIL** |
| 3 | lpips/composite non-inferior vs glyph@5000 | no significant degradation | lpips: hybrid better (p=0.038, r=0.293); composite: no diff (p=0.843, r=0.028) | **PASS** |
| 4 | diversity ratio | ≥ 0.85 | 0.81 (= baseline's own ratio) | **FAIL** |
| 5 | visual sheets free of ransom-note mixing | eyeball clean | 6/6 top-swap-count sheets checked, all clean; swap-count proxy max=10/94, well under 40-cell risk line | **PASS** |

**Overall: FAIL** (criteria 1, 2, and 4 fail; the brief's decision tree routes on char_acc first).

Per the brief: *"FAIL on char_acc → OCR-selectable headroom unrealizable at n=1/model; hybrid
demoted; Tasks 3→5 (template track) become primary."*

### Why it fails: the core mechanism

The oracle's 486-cell "only-glyph" advantage is a DINOv2 template-match signal — essentially "is
the generated glyph closer to its own font's GT embedding than to any other glyph's". TrOCR's
read-back of the generated cell is a much coarser, much more permissive signal (a 4-token OCR
decode that hallucinates readily on symbols and only weakly correlates with the DINOv2 measure —
see the 63-66% agreement in Section 1a). The result: the OCR-swap rule fires on only 198 cells
total (vs. the 894 cells where either model has a real complementary advantage per DINOv2), and
of those 198, only 21 are real DINOv2 wins — the other 177 are either neutral (both-already-ok or
both-still-fail) or actively harmful (12 cells where it swaps away a DINOv2-correct baseline
glyph for a DINOv2-incorrect glyph-cond one, because TrOCR happened to misread the baseline and
correctly read the glyph-cond cell, or vice versa). Net effect: +9 cells out of 4700, an
improvement so small it's statistically indistinguishable from noise and doesn't even clear
glyph-cond's own solo score.

The complementarity accounting itself (join + agreement matrix + capture-rate machinery in
`hybrid_replay.py`) is validated (exact match on 2730/408/486/1076 and on the forecasted vs
scored char_acc delta) and is intended to be reused as the standing diagnostic for future model
pairs, per the brief — a different pair of models (e.g. two independently-trained checkpoints
with more genuinely-different failure modes, or a higher-fidelity per-cell confidence signal than
a 4-token OCR decode) could plausibly produce a much higher capture rate.

---

## 7. File pointers

- Code: `hybrid_replay.py` (repo root)
- Generated hybrid atlases: `eval_runs/hybrid_replay/generated/*.png` (50 files)
- Scores: `eval_runs/hybrid_replay/scores.json` (force-added to git), `per_cell.json`
- Wilcoxon comparison: `research/2026-07-17-wilcoxon_glyph_r32_vs_hybrid_replay.json`
- Visual sheets (prescribed tool): `audit_diversity/*.png`
- This note: `research/2026-07-17-hybrid-replay-analysis.md`
