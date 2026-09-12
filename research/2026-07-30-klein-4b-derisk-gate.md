# The 4B port's de-risk gate passes, but the 4B is well behind at a matched checkpoint (2026-07-30)

**Question.** `research/2026-07-27-klein-licensing-and-4b-port.md` argued the
Apache-2.0 `klein-base-4B` is both the licensing fix and the speed win. Before
committing to a full retrain: does glyph-latent channel-concat conditioning
work on that base at all, and what does the port actually cost?

## Verified before spending GPU time

| claim | result |
|---|---|
| `klein-base-4B` license | **apache-2.0**, not gated (HF API, not the card prose) |
| arch matches distilled 4B | yes — `in_channels` 128, inner 3072 (24×128), 5/20 layers, `joint_attention_dim` 7680 |
| **VAE weights** across base-9B / base-4B / 4B | **byte-identical** (same sha256, matching the local file the caches were built with) |
| cache portability | `dataset_v2/cache` + glyph template port with **no re-encoding**; `cache_meta.json` records only geometry, and the cache holds no prompt embeds |
| `train_lora_kg.py` on a new base | already architecture-agnostic — widens `x_embedder` from `inner = _old_xemb_w.shape[0]`, targets LoRA by name regex, not layer index |

The VAE identity is the claim the whole cost estimate rested on. It holds, and
was confirmed in use: the run loaded 925 cached latent pairs and a
`(1, 6400, 128)` template unchanged.

**Correction to the 07-27 doc:** it stated both 4B variants were already in the
local HF cache. Only the distilled `FLUX.2-klein-4B` was; `base-4B`, the LoRA
training base, had to be fetched (14.88 GB via `pipeline/fetch_base_model.py`,
which skips the 7.2 GB flat single-file transformer variant the klein repos ship
alongside `transformer/`).

## Protocol

`run_derisk_4b.sh` mirrors the original 9B de-risk exactly — 400 steps, rank 16,
lr 1e-4, grad_accum 2, seed 42, `dataset_v2`, `--use-template`, recovered from
`training_glyph_cc_400/train_config.json` — with `--model` as the only changed
variable. The same checkpoint is then evaluated twice on 3 fonts, with and
without the template channel.

**The historical 9B de-risk was re-scored** (`run_rescore_9b_derisk.sh`) because
`eval_runs/glyph_cc_400{,_zero}` were scored 2026-06-04 and `--prompt-style` did
not exist until 2026-07-28 — those runs used the structured prompt against a
model trained on `TRAINED_SHORT_PROMPT`. The mismatch turned out to cost only
+0.0106 char_acc at this early checkpoint, but the re-score makes the comparison
clean. New dirs; the 2026-06 runs are left as the historical record.

## Result: the gate passes

400 steps, rank 16, 3 fonts (Akaya / AlikeAngular / AveriaLibre), prompt-matched:

| | with template | zeroed | retains |
|---|---|---|---|
| char_acc 9B | 0.5000 | 0.0248 | 5.0% |
| char_acc 4B | 0.3050 | 0.0284 | 9.3% |
| **identity 9B** | **0.9004** | 0.0148 | 1.6% |
| **identity 4B** | **0.5609** | 0.0406 | 7.2% |
| racc 9B | 0.6702 | 0.0674 | 10.1% |
| racc 4B | 0.4149 | 0.0638 | 15.4% |
| dinov2 9B | 0.7989 | 0.5434 | 68.0% |
| dinov2 4B | 0.7295 | 0.5887 | 80.7% |

**The mechanism transfers.** Zeroing the template collapses the 4B on every
axis; identity falls to 0.0406, i.e. without the template the model cannot
produce the right letter at all. It demonstrably reads letterforms from the
conditioning channel.

**But the 4B is well behind the 9B at the same checkpoint** — identity 0.5609
vs 0.9004, char_acc 0.3050 vs 0.5000. The 9B's collapse is also *cleaner*
(retains 5.0% vs 9.3% on char_acc). At 400 steps the 9B is a strictly
better-conditioned model on every axis.

## Cost, measured

Wall-clock derived from each run's own `time_s` deltas. Note the
`sec_per_step` column in `training_glyph_r32_5000/metrics.csv` disagrees with
its own wall clock by ~8× and must not be used.

| run | s/step (wall) | peak VRAM |
|---|---|---|
| 9B r16 @400 de-risk | 70.96 | 15.6 GB |
| 9B r32 @5000 | 15.76 | 15.6 GB |
| **4B r16 @400** | **7.54** | **7.8 GB** |

The 9B de-risk's 71 s/step is **not** a fair 9B baseline: it ran 2026-06-04, two
days before `--grad-checkpointing` landed (`ec3d166`, "3090 rank-32 memory
verified"), so it was training in a bad memory regime. Against the properly
configured 9B r32 run, the 4B is roughly **2× faster**, not the ~9× a naive
de-risk-to-de-risk comparison suggests.

Inference at equal steps: ~87 s/font (4B) vs ~118 s/font (9B), ~1.4×. The
4-step distilled win is separate and **untested**.

Peak VRAM of 7.8 GB out of 24 — with grad checkpointing still on — means there
is real headroom to raise rank or drop checkpointing, which the 9B never
allowed. Untested; deliberately not touched during a single-variable gate.

## Decision: run the full 4B rank-32 5000-step training

`run_glyph_4b_r32.sh`, hyperparameters copied from
`training_glyph_r32_5000/train_config.json` so the result is comparable to the
shipped 9B model. Conditioning mirrors the shipped protocol: train on the
neutral `template.pt` (hardcoded in `train_lora_kg.py`), eval with
`template_disambig_mild.pt` — the zero-shot win the 9B banked. ~12 h projected,
`--checkpoint-every 500`, resume-on-eviction, watchdog.

**The case against** is that 34-point identity gap at a matched checkpoint,
which is real. What makes it weak evidence rather than decisive: identity
*saturates* on the 9B (0.9004 @400 → 0.9936 @5000), so the curve is steep early
then flattens, and 400 steps is 8% of the run with 100 of those being warmup.

**The case for** is that the licensing blocker is absolute. No quality achieved
on `klein-base-9B` unblocks commercial use, so if a commercial product is the
goal this experiment has to happen; ~12 h is cheap to resolve it.

**What this does not establish:** that the 4B will match the shipped model.
Every quality number would need re-establishing on the new base — none of the
9B findings transfer as claims.

---

# OUTCOME (2026-07-30, same day): the full run landed better than predicted

Training: 5000 steps, rank 32, **10.7 h**, best loss 0.0264. Rank 32 cost the
same as rank 16 — 7.49 s/step, 7.8 GB peak — because activations dominate, not
adapter parameters. Against the 9B rank-32 run (15.76 s/step, 15.6 GB) that is
**~2.1× faster on half the memory**.

## What Apache-2.0 costs: style fidelity, not letter correctness

50-font holdout, both models rank-32 @5000, disambig-mild template,
each evaluated on its own trained prompt. Paired Wilcoxon, gate p<0.05 ∧ r≥0.3:

| metric | 9B glyph | 4B glyph | p | r | verdict |
|---|---|---|---|---|---|
| char_acc | 0.6917 | 0.6460 | 0.0001 | 0.563 | **9B better (large)** |
| dinov2 | 0.8788 | 0.8485 | 0.0001 | 0.556 | **9B better (large)** |
| identity | 0.9936 | 0.9893 | 0.1272 | 0.436 | no diff |
| racc | 0.7279 | 0.7360 | 0.1248 | 0.237 | no diff |
| lpips | 0.1457 | 0.1381 | 0.2077 | 0.178 | no diff |
| composite | 0.8137 | 0.8158 | 0.5722 | 0.080 | no diff |

The 9B wins both *style* axes decisively. On **identity — the primary axis —
there is no significant difference**. The 34-point identity gap at 400 steps
(0.5609 vs 0.9004) closed almost entirely by 5000; identity saturated as the
9B's own curve predicted.

**Caveat on that "no diff":** the identity row has only **13 non-tied font
pairs** (r=0.436, medium). That is *no evidence of a difference*, not evidence
of equivalence — underpowered at this tie rate, and the 13 that differ favour
the 9B.

Against the non-conditioned 9B baseline, the 4B is statistically
indistinguishable on **every** style/structure axis and loses only identity
(0.9968 vs 0.9893, p=0.0134, r=0.669). All three models read the correct letter
**>98.9%** of the time.

## Where the style loss actually lives

Per-font, it is concentrated in typefaces with fine structural detail, not
spread evenly:

| font | char_acc Δ | dinov2 Δ |
|---|---|---|
| Fascinate Inline | **−0.298** | −0.148 |
| IBMPlexSerif | −0.245 | — |
| Dangrek | −0.181 | −0.075 |
| BitcountGridDoubleInk (dot-grid) | −0.064 | **−0.183** |
| BitcountPropDoubleInk (dot-grid) | −0.085 | **−0.162** |
| Rubik Distressed | −0.032 | +0.007 |
| PlaywriteMXGuides | **+0.085** | — |

Diversity audit, same tool on both runs' outputs (`audit_diversity.py`):

| | inter-font diversity ratio | BitcountGrid target_sim |
|---|---|---|
| 9B shipped | **0.88** | 0.874 |
| 4B | 0.81 | 0.691 |

Drift is negative for every font in both models — generated leans toward the
target font, not the neutral Arial template — so **there is no
template-skeleton collapse** in either. The 4B simply compresses inter-font
variety somewhat more.

**Visual check** (`viz/compare_9b_4b.py` → `viz/out/compare_9b_4b.png`): the
loss is visible and specific. Fascinate Inline's thin inline stroke is rendered
by the 9B and filled solid by the 4B. Bitcount's **dot-grid topology is
preserved** by both — it has not collapsed to solid strokes — but the 4B's
letterforms within the grid are thinner and less well-formed. On ordinary
typefaces (Wonky control, Dangrek, Averia) the difference is subtle to
invisible.

## Bottom line

An Apache-2.0 model that matches the shipped 9B on letter correctness, matches
the non-conditioned 9B baseline on every style axis, and gives up measurable
style fidelity against the best 9B — concentrated in structurally distinctive
typefaces, which is precisely where a font product would want to differentiate.
It trains in half the time on half the memory.

**Untested levers, all newly available:** 7.8 GB of 24 with grad checkpointing
still on, and rank 32 cost nothing over rank 16. Grad checkpointing off, larger
batch, and higher rank are all now affordable and were never possible on the
9B. Deliberately untouched here so the comparison to `training_glyph_r32_5000`
stayed single-variable.

**Also untested:** the distilled 4-step `FLUX.2-klein-4B` inference path, which
was half the original motivation. At equal 20 steps the 4B generates ~87 s/font
against the 9B's ~118 s/font (~1.4×); the 4-step win is separate and unmeasured.

## Artifacts

- `run_derisk_4b.sh`, `run_rescore_9b_derisk.sh`, `run_glyph_4b_r32.sh`
- `pipeline/fetch_base_model.py`
- `eval_runs/derisk_4b{,_zero}/scores.json`
- `eval_runs/glyph_cc_400_matched{,_zero}/scores.json`
- `training_derisk_4b/{train_config,conditioning}.json`, `metrics.csv`
