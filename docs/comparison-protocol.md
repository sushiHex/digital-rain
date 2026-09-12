# Reference Character Comparison Protocol

> **Resolved 2026-07-28 — reference-glyph identity does not matter.**
> Measured on the shipped rank-32 model rather than the rank-16/step-300
> protocol below: swapping Rg for Kg reference images moves nothing
> (paired Wilcoxon, n=50 fonts, **p=0.625**). The related *prompt* mismatch,
> found at the same time, mattered a great deal — IDENTITY 0.9780 → 0.9936,
> all 50 fonts better, r=0.870. Conditioning is now recorded per checkpoint
> and enforced at eval time by `conditioning_config.py`.
> Full analysis: [`../research/2026-07-28-reference-char-mismatch.md`](../research/2026-07-28-reference-char-mismatch.md).
>
> The protocol below is kept as the design of a controlled A/B — the control
> variables and integrity checklist still apply to any future comparison —
> but its specific question is closed, and its stated conditions (rank 16,
> step 300) are two generations behind the current model.
>
> **Two additions to the control list, from 2026-08-13.** "Same seed (42)" is
> necessary and nowhere near sufficient. (a) Changing the corpus changes the
> dataset size and therefore the shuffle sequence, so two runs with the same
> `--seed` are still different training runs. (b) Even with everything held
> fixed, three runs differing *only* in `--seed` landed 0.1157 apart on
> char_acc, and the paired Wilcoxon called two of the three pairs significant.
> **One run per arm cannot resolve a training-time difference** — budget ~3, or
> require an effect above 2× that metric's own SD.
> See [`../research/2026-08-13-training-run-variance-measured-at-last.md`](../research/2026-08-13-training-run-variance-measured-at-last.md).

## Objective
Compare Rg vs Kg as reference characters for font atlas LoRA training.

## Control Variables (must be identical)
- Atlas images: same 923 fonts, same 12x8 grid, same rendering
- Training script: same hyperparameters, same seed (42)
- Model: same FLUX.2-klein-base-9B, same INT8 quantization
- LoRA config: same rank 16, same target modules
- Steps: both trained to step 300 minimum
- Evaluation: same reference font (Times New Roman) for generation

## Independent Variable
- Reference images only: Rg (2 columns) vs Kg (2 columns)
- Prompt text: "Rg" vs "Kg" in the conditioning prompt

## Evaluation
1. Render atlas from each checkpoint (100, 200, 300) using Times New Roman reference
2. Visual comparison of grid structure, character accuracy, style fidelity
3. Loss curve comparison from metrics.csv

## Dataset Integrity Checklist
- [ ] Both datasets have identical font count
- [ ] Both datasets have identical atlas images (byte-identical)
- [ ] Both datasets have matching stems (1:1 pairing verified)
- [ ] Cache regenerated for both after any dataset changes
- [ ] Training launched with identical seed and hyperparameters
