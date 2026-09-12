# The distilled 4-step path is 9× faster but the LoRA does not transfer to it (2026-07-30)

**Question.** Half the motivation for the 4B port was the natively-distilled
4-step `FLUX.2-klein-4B`: the standing sub-minute-inference goal. Does the LoRA
trained on `klein-base-4B` work when applied to the distilled model?

The workflow is architecturally sound — `in_channels` 128, inner 3072, 5/20
layers, `joint_attention_dim` 7680, and **identical scheduler configs** on both.

## Design

Two arms so "distilled" and "4 steps" are not confounded. `run_distilled_4b.sh`,
3 fonts, same LoRA (`training_glyph_4b_r32_5000/final`), disambig-mild template,
prompt derived from the checkpoint.

| arm | char_acc | racc | dinov2 | lpips | **identity** | s/atlas |
|---|---|---|---|---|---|---|
| base-4B @20 (control) | 0.5709 | 0.7482 | 0.8078 | 0.1193 | **0.9893** | 62.7 |
| distilled-4B @20 | 0.4645 | 0.7021 | 0.8237 | 0.1912 | **0.9004** | 31.6 |
| distilled-4B @4 | 0.4468 | 0.6135 | 0.8151 | 0.2300 | **0.7860** | **7.0** |

## The distillation costs more than the step reduction

- **Model swap alone** (base@20 → distilled@20): identity **−0.089**,
  char_acc −0.106. The LoRA does *not* transfer cleanly.
- **Step reduction** (distilled@20 → distilled@4): identity **−0.114**,
  char_acc only −0.018.

Note the asymmetry: going 20 → 4 steps barely touches *style* fidelity but
badly damages *letter correctness*. Few-step sampling appears to cost identity
specifically — consistent with this project's two-axis finding that the axes
move independently.

**Speed: 7.0 s/atlas at 4 steps versus 62.7 s for base-4B @20 — 9×.** A full
95-glyph atlas in seven seconds comfortably clears the sub-minute goal.

Distilled @20 (31.6 s) is 1.98× faster than base @20 (62.7 s) at the same step
count. That ratio of almost exactly 2 is consistent with the base running
classifier-free guidance — two forward passes per step, as `generation_lib`'s
docstring notes klein base requires — while the distilled model is
guidance-distilled and runs one. Inferred from the ratio, not instrumented.

## Verdict

**Not shippable as-is.** identity 0.7860 against 0.9893 on the base is a large
regression on the axis this project treats as primary.

**The fix this points to:** most of the loss is the model swap, not the step
count, so the remedy is to **train the LoRA on the distilled model directly**
rather than transferring a base-trained adapter. That is a new lever this test
surfaced, and it is more promising than raising rank — untested.

A cheaper intermediate also remains untested: step counts between 4 and 20 on
the distilled model (8, 12), which would trade some of the 9× back for identity.

## Artifacts

- `run_distilled_4b.sh`
- `eval_runs/distill_4b_s4/scores.json`, `eval_runs/distill_4b_s20/scores.json`
