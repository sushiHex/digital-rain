# The production base is non-commercially licensed — and the Apache-2.0 alternative is also the speed win (2026-07-27)

**Question:** before productionizing the banked quality win (`glyph-cond@5000 + template_disambig_mild`), is the base model we've built everything on actually licensed for the intended use?

**Answer: our base prohibits commercial use.** The Apache-2.0 alternative would require a retrain — but that retrain is *cheaper* than the original and simultaneously delivers the long-standing sub-minute inference goal.

## Verified licensing (from the HuggingFace model cards, not secondhand)

| model | role | license | commercial? |
|---|---|---|---|
| **`FLUX.2-klein-base-9B`** | **what all 19 of our scripts load today** | **`flux-non-commercial-license`** | **NO** |
| `FLUX.2-klein-base-4B` | undistilled, for LoRA training | **Apache 2.0** | YES |
| `FLUX.2-klein-4B` | distilled 4-step, for inference | **Apache 2.0** | YES |

This corrects a genuine ambiguity in the Oracle sweep (`research/2026-07-17-oracle-cutting-edge.md`), which carried a correction that the "blanket Apache 2.0 claim for the Klein family is incorrect for the 9B variant." Confirmed directly: the 9B **base** we use — not just the distilled 9B — is non-commercial. The 4B line is Apache 2.0 in **both** base and distilled form, which matters because it supports the standard workflow: **train the LoRA on base-4B, apply it on distilled-4B.**

## Architecture delta (both already in the local HF cache)

| | klein-base-9B (current) | klein-base-4B / 4B |
|---|---|---|
| `in_channels` | **128** | **128 — identical** |
| `inner_dim` (heads × head_dim) | 4096 (32 × 128) | 3072 (24 × 128) |
| `num_layers` / `num_single_layers` | 8 / 24 | 5 / 20 |
| `joint_attention_dim` | 12288 | 7680 |
| inference steps | 20 | **4 (distilled)** |

## What a 4B port would actually cost

**Ports unchanged (the expensive artifacts):**
- **The glyph template cache** — `template_disambig_mild.pt` is `(6400, 128)`, and `in_channels` is **128 on both models**. The whole channel-concat conditioning *mechanism* (atlas 128 ⊕ template 128 → 256) transfers conceptually intact, and the cached disambig template — the banked zero-shot win — is reusable **as-is**.
- The dataset + atlas pipeline, `eval_holdout`, the identity classifier (`glyph_classifier.py`), the dual-scorecard eval harness, `audit_diversity.py`, and every research finding.

**Needs retraining (weights are architecture-specific):**
- `x_embedder` becomes `Linear(256, 3072)` instead of `Linear(256, 4096)` — same construction (`_expand_x_embedder_to_256` generalizes; it already reads `out_features` from the existing layer), but the trained values don't transfer.
- The rank-32 LoRA adapter itself. The `target_modules` regex matches by name pattern so it should still resolve, but 5+20 layers ≠ 8+24 layers → fresh training.
- Cached prompt embeds (`joint_attention_dim` 12288 → 7680) — regenerated automatically by `encode_prompt`, no work.

**Why the retrain is cheaper than the original 4.4h/5000-step run:**
- 4B vs 9B — under half the parameters; likely more headroom on the 3090 (possibly grad-checkpointing off, which was previously impossible at 51GB peak).
- **Inference drops from 20 steps to 4.** This compounds hard on our workflow: eval generation was ~120s/font × 50 fonts ≈ 1.7h per eval, and we ran *many* evals. A 4-step model plausibly cuts that ~5×, making the whole iterate-and-measure loop dramatically faster.

## Implication

The 4B port is not merely a licensing workaround — it collapses two roadmap items into one:
1. **Licensing:** unblocks any commercial use (Apache 2.0, both variants).
2. **Sub-minute inference:** the standing goal that `project_lora_training` notes requires "offline merge-V3 + SVDQuant" because Nunchaku has no runtime-LoRA support for FLUX.2 (PR #926 still unmerged). A natively-distilled 4-step 4B model attacks that directly, without depending on an unmerged quantization path.

**Caveat:** this is a *retrain*, so all of the quality findings (char_acc 0.688, IDENTITY 0.978, the disambig win's significance, the 0.87 diversity ratio) would need re-establishing on the new base — they are not transferable claims. The de-risking gate is cheap though: the original channel-concat de-risk (400 steps, ablation showing template-zeroing collapses char-acc 0.489→0.174) is a known-good protocol to re-run, and it cost ~8h on the slower 9B.

**Decision this informs:** whether HD-Task 4 (productionize glyph-cond+disambig) should target the current 9B base at all. If commercial use is ever intended, productionizing on `klein-base-9B` builds further on a base that cannot ship — and the alternative path is faster at inference anyway.
