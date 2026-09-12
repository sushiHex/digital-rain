# The 4B's spare VRAM is not spendable — only rank is (2026-07-30)

**Question.** The rank-32 4B run peaked at 7.8 GB of 24 with grad checkpointing
still on, and rank 32 cost the same as rank 16. That looked like headroom the
9B never had (15.6 GB peak). Which training levers does it actually buy?

`run_throughput_probe.sh`: four arms, 120 steps each into throwaway dirs,
read for wall-derived s/step and peak VRAM. Nothing here measures quality.

The control reproduces the full run — 7.56 s/step and 7.8 GB against the real
run's 7.49 / 7.8 — so the method is sound and the other arms are trustworthy.

| arm | s/step | s/sample | peak GB | result |
|---|---|---|---|---|
| A rank 32, ckpt on, batch 1 | 7.56 | **3.78** | 7.8 | control |
| B rank 32, **ckpt off**, batch 1 | — | — | — | **did not fit** |
| C rank 32, ckpt on, **batch 2** | 17.10 | 4.28 | 9.2 | **+13% worse** |
| D **rank 64**, ckpt on, batch 1 | 7.67 | **3.84** | **7.8** | **+1% — free** |

s/sample normalises for grad_accum 2 and batch size: arm C does 4 samples per
optimizer step against the control's 2.

## Grad checkpointing off does not OOM — it thrashes

Arm B saturated VRAM to **39 MiB free** and paged to system RAM. It ran 45
minutes without completing a single logged step, against the control's 16
minutes for all 120. It was killed once the result was unambiguous.

This is a nastier failure mode than a crash: it presents as slow progress, not
as a broken config. **It also retroactively explains the 9B de-risk anomaly** —
that run (2026-06-04) predates the `--grad-checkpointing` flag (`ec3d166`,
2026-06-06) and clocked 70.96 s/step against the properly-configured 9B's
15.76. Same pathology, reproduced deliberately here.

## Batch 2 is worse, which says the GPU is already saturated

4.28 s/sample against 3.78, at 9.2 GB instead of 7.8. Larger batches normally
amortise per-step overhead; that they don't here means the GPU is
compute-bound at batch 1 already, so batching only adds memory pressure.

## Correction

An earlier note called these levers "newly affordable and never possible on the
9B." Two of the three are not affordable at all — only rank is. The 7.8 GB of
apparent headroom is not spendable on activations; it is simply what this model
needs at this sequence length.

## What this leaves

**Rank is the only lever with headroom, and it is essentially free** — double
the adapter capacity for 1% throughput and no extra memory, so a rank-64 run
costs ~10.8 h against the rank-32 run's 10.7 h.

Whether it *helps* is untested and uncertain. The 4B's loss plateaued by ~2000
steps (steep to 1500, then flat at 0.040–0.043 through 5000 with bands
oscillating upward), so the model is converged and the constraint is capacity —
but that may be the *base's* 3.9B parameters rather than the adapter's rank, in
which case no rank raises it.

The other open lever is not on this list because the distilled-path test
surfaced it: **train the LoRA on the distilled model directly** rather than
transferring a base-trained adapter — see
`research/2026-07-30-distilled-4step-path.md`, where the model swap alone costs
0.089 identity.

## Artifacts

- `run_throughput_probe.sh`
- `probe_{A_ckpt_on_b1,C_ckpt_on_b2,D_rank64}/metrics.csv`
