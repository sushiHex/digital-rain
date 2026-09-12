# "Incorrect letters" are largely a measurement artifact, not a generator failure (2026-07-18)

**Question:** the diversity figure showed a generated RubikDistressed `R` that reads as `K`. Is wrong-letter identity a glaring failure in the generator?

**Answer: No.** After separating letterform IDENTITY from style FIDELITY, the genuine wrong-letter rate is small and concentrated on extreme topology-breaking fonts. The "31% wrong" implied by char-accuracy is an artifact of two flawed metrics.

## The two metrics were conflated
- `char_acc` (the reported headline, 0.688 on the best generator) is **DINOv2 template-match = STYLE FIDELITY**: does the cell render like GT's exact glyph? It penalizes correct letters drawn in a different style — case forms, cursive flourishes, GT practice guide-lines the gen omits, dot patterns. Visually confirmed: PlaywriteCO cursive A/D/E/F/G are correct letters marked "wrong"; PlaywriteUST letters are correct but GT has guide-lines.
- **IDENTITY** (does it read as the right letter?) is a different axis. Measured with a class-routed, **GT-gated** OCR check (`identity_score.py`): only score a cell if the reader (TrOCR; GOT-OCR2 for symbols) correctly reads the **GT** glyph — otherwise the reader can't be trusted to judge the generation, so abstain.

## Numbers (best generator = glyph-cond@5000 + disambig template, 50-font holdout)
| metric | value | meaning |
|---|---|---|
| FIDELITY (DINOv2 char-acc) | 0.688 | the headline; style-match, not identity |
| IDENTITY (GT-gated OCR, scored set) | **0.931** | reads as the right letter, 93%+ |
| genuine wrong-letter target | **~3.2%** of all cells | 151 cells, not the 31% char-acc implied |
| baseline IDENTITY | 0.936 | **~identical** — glyph-cond and disambig moved FIDELITY, not identity |

- Of the 1465 char-acc "failures", ~560 scored cells are the **correct letter** penalized only on style; ~1350 are symbols (OCR-blind, abstained), ~500 thin strokes (abstained), ~660 cells the reader can't even read in the GT (abstained).
- **Even the 3.2% residual is mostly TrOCR instability**, not model error: eyeballed the 151 gold-gated targets — AveriaSerif `h`/`n`/`u` are perfect (TrOCR read each as "1"), AlikeAngular `T`/`k`, NovaSquare `J`/`K`/`L` all correct. TrOCR is a document/line OCR; on single centered glyphs it systematically misreads isolated capitals (J→1, K→6, L→:, N→Z, T→7). So true model identity is **higher** than 0.931 — TrOCR undercounts.

## What is genuinely wrong (the small real residue)
Topology-breaking styles where the style itself deletes the identifying stroke: dot-grid (BitcountGrid/Prop) and heavy distress (Rubik) — the R→K case. These are the fonts already flagged for scope-out (forcing legibility fabricates a glyph the font doesn't draw and fights the 0.87 diversity gate). Genuine, in-scope, readable-font wrong letters are ~1% or less.

## Implication
- **No expensive generation fix is justified.** The panel-designed Phase 3 (hardened structure channel) and R-GDPO were sized to fix a ~11% wrong-letter problem; the real in-scope rate is ~1%. A multi-day GPU run to chase it is poor EV.
- **The fix is the METRIC, not the model.** Report IDENTITY and FIDELITY as two first-class numbers (never one). char-acc alone made correct letters look wrong and drove a phantom research direction.
- **For a clean identity number** (TrOCR undercounts on isolated glyphs), the small missing piece is a single-glyph character classifier (not a document OCR) — the only measurement infra worth building. Optional: the qualitative conclusion is already certain from the visuals.

## Tool
`identity_score.py <per_cell.json>` — dual scorecard: FIDELITY (DINOv2) + GT-gated IDENTITY (class-routed OCR, abstains where the reader can't read the GT), emits `identity_scorecard.json` with the wrong-letter target list. Reuses stored TrOCR decodes (free); `--got-decodes` upgrades symbol cells; `--classifier` swaps the TrOCR reader for the purpose-built glyph classifier below.

## Update (2026-07-21): the finding recurs at the seed level — same-model best-of-N "headroom" is mostly style-lottery too

A separate investigation (GT-guided cross-model preference optimization, `docs/superpowers/plans/2026-07-19-fidelity-push-gt-guided-preference.md`) set out to lift char_acc above 0.688 by distilling a cross-model advantage into the weights. Along the way it surfaced a much bigger, cheaper, and more fundamental discovery:

- **Every char_acc number in that investigation (0.688, all Stage A variants) was a single-fixed-seed measurement** (`--seed 42`, "fixed for reproducibility"). Nobody had checked the model's own seed-to-seed variance.
- **Same-model best-of-4 (4 independent glyph seeds, same font, same conditioning) reaches char_acc 0.8366 on the 50-font holdout** — +0.1483 over the single-seed 0.6883, and *exceeding* the cross-model oracle ceiling (0.7719) that had motivated the whole DPO track.
- **But IDENTITY (glyph classifier) is already near-ceiling at a single seed: 0.9619, moving to only 0.9970 at best-of-4** (+0.035). **Of the 765 cells where char_acc "failed" at seed0 but a different seed fixed it, 88.6% were already identity-correct at seed0** — same letter, just not the exact stroke/style nuance this particular font's GT happens to have.

**This is the same conflation as the 2026-07-18 finding, playing out one level deeper.** char_acc's "ceiling" isn't primarily about the model failing to produce correct letters (identity is already ~0.96–0.98 and barely moves with more samples) — it's about which of several equally-correct renders happens to land closest to a given font's idiosyncratic style. Trying more seeds mostly plays the style-lottery again, not fixing genuine errors.

**Practical consequence:** a cheap no-GT self-consistency selector (pick the most-typical of N candidates via pairwise DINOv2 similarity) captured only **14.1%** of the best-of-4 gap — close to the ~4-5% capture that already killed the cross-model hybrid-selection track (HD-Task 6) for the same underlying reason: no-GT selectors can't reliably realize a metric-space advantage that char_acc itself only rewards by GT-relative luck.

**Conclusion (extends the 2026-07-18 verdict): the char_acc "ceiling" is not worth chasing further, by any mechanism.** Not training-based distillation (Stage A/SFT showed a real, if shrinking, regression across three tries — training-set composition bias, not a fixable signal), not no-GT test-time selection (both cross-model and same-model variants plateau at low single-digit-to-teens capture rates), and not more seed sampling (recovers style-luck, not correctness). IDENTITY — the metric that actually reflects generator quality — is already excellent on the current production generator (glyph-cond@5000+disambig) and has little real headroom left. Report FIDELITY and IDENTITY as the dual scorecard, as already established, and stop treating FIDELITY's gap as a target.

## Update (2026-07-18): clean identity number from a purpose-built classifier
The doc's own Implication called for "a single-glyph character classifier (not a document OCR)" as the one piece of measurement infra worth building. Built it.

- **`glyph_classifier.py`** — font-invariant single-glyph 94-class CNN (4-block conv 32-64-128-256, adaptive-pool 2x2, FC head w/ dropout, ~1.46M params; cosine LR, label smoothing, best-val checkpoint). Trained on 700 google-fonts, validated on **60 held-out fonts** (disjoint from training): **val_acc 0.9385**. Its residual errors concentrate on `O/0`, `I/l/1`, `V/v`, `X/x`, `W`, `Z` — exactly the confusables the identity metric already folds via `EQUIV` + case, so the *effective* identity-reader accuracy is higher than 0.9385.
- **Wired into `eval_checkpoint.py --identity`** — GT-gated (score a cell only if the classifier reads the GT glyph as the expected char at conf ≥ 0.5), shares `identity_score.reads_as` so the eval and the standalone tool agree on one identity definition. Purely additive: identity is reported alongside, never inside, the composite; char_acc/lpips/racc/dinov2 unchanged.
- **Clean number on the best generator** (glyph-cond@5000 + disambig template, 50-font holdout):

  | metric | value | meaning |
  |---|---|---|
  | FIDELITY (DINOv2 char-acc) | 0.688 | style-match, not identity |
  | IDENTITY (classifier, GT-gated) | **0.978** | reads as the right letter |
  | scored fraction | **93.6%** | vs 67% under the TrOCR reader |

- This **confirms and tightens** the 0.931 TrOCR estimate above: TrOCR undercounted (systematic isolated-glyph misreads) and could only score 67% of cells; the purpose-built classifier reads the GT confidently on 93.6% of cells and finds the generation is the right letter 97.8% of the time. True in-scope identity is ~0.98.
- **Conclusion stands, now on a clean instrument:** the "wrong letters" were a metric artifact. No expensive generation fix (Phase 3 / R-GDPO) is justified; the fix was the metric, and the metric is now built and reported as two first-class numbers.
