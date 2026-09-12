# Gate −1: realizable cross-model oracle ceiling for the disambig base (2026-07-19)

**Decision gate before the multi-day GT-guided preference (DPO) run** (plan `docs/superpowers/plans/2026-07-19-fidelity-push-gt-guided-preference.md`, Task 4). Computed FREE from existing 50-font holdout `per_cell.json` — no GPU generation.

## Inputs
- baseline = structured-5000 (`eval_runs/structured_prompt_5000/per_cell.json`, char_acc 0.6677)
- glyph = glyph-cond@5000 + `template_disambig_mild` (`eval_runs/glyph_r32_disambig50_mild/per_cell.json`, char_acc 0.6883)

## Result (via the tested `measure_oracle_ceiling.oracle_ceiling`)
| metric | value | meaning |
|---|---|---|
| **realizable_ceiling** | **0.7719** | fraction of cells where baseline ∪ glyph char_acc-matches |
| glyph_alone | 0.6883 | current best generator |
| baseline_alone | 0.6677 | structured baseline |
| **cross-model headroom** | **+0.0836** | 393 only-baseline cells / 4700 |
| only_glyph | 490 cells | glyph wins, baseline fails |
| both_fail | 1072 cells | neither renders — the architectural floor |

## Verdict: **GO** (threshold 0.71; realizable 0.7719)

- The adversarial review (`wf_6eb0f35a-680`) correctly identified the +0.087 headroom as CROSS-model (baseline↔glyph), unreachable by single-model self-distillation. This gate confirms it for the CURRENT disambig base: **+0.0836**, essentially intact vs the pre-disambig +0.0868 (408→393 only-baseline cells; disambig recovered a handful). The multi-model candidate pool (baseline + glyph) is the mechanism to access it.
- Upside if DPO fully captures the oracle: char_acc 0.688 → 0.772 (+0.084 = ~5× the entire 5000-step run's +0.017). Even partial capture (+0.04) is a decisive win over the 0.688 baseline.
- **Caveat:** 0.772 is the perfect-selection oracle. DPO distillation is lossy — the model must learn to render the baseline's shape on the 393 only-baseline cells while KEEPING its 490 only-glyph wins (net, not just additive). The 1072 both-fail cells are unreachable (architectural floor) — no cross-model lever helps them.
- Seed-variance diagnostic skipped here (only 1 stored seed per model); the DPO run generates multiple seeds on training fonts.

## Implication for the run
Candidate generation on all 925 training fonts × 2 models × N seeds is infeasible (~days of pure inference). Per spec §7, scope to a training-font SAMPLE (start with a pilot, expand if Stage A is promising). The holdout ceiling proves the headroom exists and generalizes; training distills it on `dataset_v2` fonts.
