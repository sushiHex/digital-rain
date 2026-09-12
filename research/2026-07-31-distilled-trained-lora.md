# Training the LoRA on the distilled model recovers most of the transfer loss (2026-07-31)

**Question.** `research/2026-07-30-distilled-4step-path.md` found that a LoRA
trained on `klein-base-4B` does not transfer cleanly to the distilled
`FLUX.2-klein-4B`: the model swap alone cost 0.089 identity, more than the
20→4 step reduction cost. Does training the adapter *on* the distilled model
fix that?

`run_glyph_4b_distilled.sh` — single variable against
`training_glyph_4b_r32_5000`: same rank 32, 5000 steps, lr 1e-4, warmup 100,
batch 1, grad_accum 2, seed 42, wd 1e-5, same neutral `template.pt`. Only
`--model` changes.

## Plain flow-matching works on a distilled base

The stated risk was that few-step distilled models need an LCM-style objective.
They do not, here. The loss tracked the base-trained run throughout and ended
marginally *lower*:

| steps | base-trained | distilled-trained |
|---|---|---|
| 1–1000 | 0.0540 | 0.0523 |
| 1001–2000 | 0.0443 | 0.0429 |
| 2001–3000 | 0.0417 | 0.0398 |
| 3001–4000 | 0.0408 | 0.0400 |
| 4001–5000 | 0.0404 | 0.0396 |
| best | 0.0264 | **0.0258** |

10.7 h, same as the base-trained run.

## It recovers most of the transfer loss

Same 3 fonts, both at 4 steps (exploratory — 3 fonts is below the paired gate's
threshold, so no significance is claimed):

| | char_acc | racc | dinov2 | lpips |
|---|---|---|---|---|
| transferred (base-trained) | 0.4468 | 0.6135 | 0.8151 | 0.2300 |
| **distilled-trained** | **0.5355** | **0.7340** | **0.8354** | **0.1557** |

On the full 50-font holdout the distilled-trained adapter reaches **identity
0.9461 at 4 steps**, against the transferred adapter's 0.7860 — and that
understates it, since the transferred arm was measured on the three
alphabetically-first (easier) fonts.

## The quality/speed frontier

50 fonts, prompt-matched, disambig-mild template:

| arm | char_acc | identity | dinov2 | racc | s/atlas | license |
|---|---|---|---|---|---|---|
| 9B glyph @20 | 0.6917 | 0.9936 | 0.8788 | 0.7279 | 118 | **non-commercial** |
| base-4B @20 | 0.6460 | 0.9893 | 0.8485 | 0.7360 | 62.7 | Apache-2.0 |
| distilled @20 | 0.6136 | 0.9714 | **0.8661** | 0.7021 | 31.6 | Apache-2.0 |
| distilled @4 | 0.5728 | 0.9461 | 0.8276 | 0.6802 | **7.0** | Apache-2.0 |

**The 9× speedup is not free.** Gated (paired Wilcoxon, n=50), distilled @4 vs
base-4B @20 loses significantly on every axis except DINOv2:

| metric | p | r | |
|---|---|---|---|
| composite | <0.0001 | 0.865 | base better |
| racc | <0.0001 | 0.857 | base better |
| identity | <0.0001 | 0.848 | base better (n_nz=33) |
| lpips | <0.0001 | 0.835 | base better |
| char_acc | <0.0001 | 0.690 | base better |
| dinov2 | 0.1689 | 0.195 | no diff |

That identity test has 33 non-tied pairs — unlike the 9B-vs-4B comparison's 13,
this one is well powered and the difference is real.

**At 20 steps the distilled model beats base-4B on DINOv2** (p=0.0005, r=0.492)
while losing char_acc, racc and identity — the same style-versus-identity split
this project keeps finding, trading in the opposite direction, at 2× the speed.

## What 4-step output actually looks like

`viz/compare_9b_4b.py` → `viz/out/compare_9b_4b.png`, bottom row.

Few-step sampling costs **high-frequency structural detail** specifically.
Bitcount's dot-grid degrades badly — irregular dots, blobby malformed
letterforms — and Rubik Distressed gets noisier. But Dangrek, Averia Serif
Libre and the Wonky control are essentially indistinguishable from the 20-step
output, and Fascinate Inline's inline stroke is actually rendered *better* at
4 steps than by base-4B at 20.

## Bottom line

There is now a real Apache-2.0 quality/speed frontier, from 7 s/atlas at
identity 0.946 to 62.7 s at 0.989. Which point to ship is a product decision,
not a research one. Fonts with fine repeating structure are the ones that
suffer at 4 steps; ordinary typefaces are close to free.

**Untested:** step counts between 4 and 20 (8, 12) on the distilled-trained
adapter, which would land between these points and are cheap to measure. Rank
64 also remains untested for quality — the throughput probe showed it costs
only +1% time and no extra memory.

## Artifacts

- `run_glyph_4b_distilled.sh`
- `eval_runs/distill_trained_s4/`, `eval_runs/distill_trained_s20/`
- `research/2026-07-31-wilcoxon_base4B20_vs_distilled4.json`
