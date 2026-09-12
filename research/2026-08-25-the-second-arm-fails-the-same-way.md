# The second arm fails the same way — it is the task, not the model (2026-08-25)

**Eight seeds, two independent models, not one break.** FLUX.2-klein-base-4B and
Z-Image-Turbo — different architectures, different training data, both
Apache-2.0 — both return a solid face for *"a stencil sans with deliberate
breaks"*. The failure that motivated the whole adherence programme is **not a
property of our generator.**

Tool: `analysis/generate_candidate_references.py --backend z-image-turbo`.
Figure: `viz/arm_comparison.py`.

## Why a second arm existed

The generator cannot draw a stencil, and re-rolling cannot rescue it: that
description's spread is second-narrowest of twelve, so four seeds give four
solid faces. A second arm was the only task on the plan that could **lift the
ceiling rather than describe it**.

The bar was registered as a yes/no, not a score: **does any candidate show a
break?**

## The answer

**No.** Not in four klein-base seeds, and not in four Z-Image-Turbo seeds.

That is worth more than a marginal score difference. Two models that share
nothing but the task fail identically, which relocates the problem: it is not
*this* generator being weak at *this* attribute, it is **a general
text-to-image model being asked for two isolated glyphs in a rare typographic
treatment**. A third arm is unlikely to change it.

## Getting there cost two dead ends, both worth recording

| path | outcome |
|---|---|
| `Intel/GLM-Image-int4-AutoRound`, 13 GB **already on disk** | **unloadable** — diffusers 0.38 has no `auto-round` quantizer. Installing `auto_round` (0.14.2, with `py-cpuinfo`) does **not** register one; the gap is on the diffusers side, not a missing dependency |
| `zai-org/GLM-Image` bf16 + quanto int8 | **SIGSEGV, exit 139**, after the pipeline loaded and before any image |
| `Tongyi-MAI/Z-Image-Turbo` | **works** — `ZImagePipeline` ships natively in diffusers 0.38, no workaround |

So `CLAUDE.md`'s stale *~36 min/image* for GLM remains **unre-measured**, and the
reason is not that GLM is slow. It does not run here at all. The entry should
say that rather than carrying a speed figure it cannot support.

## Z-Image as an arm, scored on everything that exists

48 candidates, 12 descriptions, 4 seeds. **48 usable of 48**, mean **28.5 s** per
image at 8 steps — against a claimed 3.4 s on a 4090, so the 3090 costs roughly
8×.

| | klein-base-4B | Z-Image-Turbo |
|---|---|---|
| usable | 48/48 | 48/48 |
| seconds per image | ~25 | ~28.5 |
| within-description spread | 1.302 | 0.820 |
| **between-description spread** | **2.514** | **1.172** |
| ratio (within/between) | 0.518 | **0.700** |
| pairs above the gate's 1.875 | 15% | **4%** |
| **narrow descriptions** | **8/12** | **11/12** |

**Z-Image is worse on every picker axis**, and the informative column is
*between*-description spread: at 1.172 against 2.514, it separates the twelve
descriptions **less than half as well**. Its outputs cluster in a narrower
region of style space, so both the styles and the seeds look more alike.

Its ratio of 0.700 sits closer to the "description not controlling style" edge
(0.85) than klein's 0.518, and only one of its twelve descriptions offers a
choice by the gate's own cut.

## What this settles, and what it does not

**Settles.** The stencil failure is not fixed by swapping the generator, and
klein-base remains the better arm — which was not a foregone conclusion, since
klein-base was chosen originally because it was already on disk rather than
because it won a comparison. It now has won one.

**Does not settle.**

- **One prompt set, mine, and n=4 seeds per description.**
- **Z-Image was run at 8 steps** because Turbo is distilled for it. A
  non-Turbo Z-Image at 20+ steps is untested and might differ.
- **The edit path is untested.** `2026-08-23-restyle-not-generate-the-reference.md`
  argues for *restyling* a neutral `Kg` rendered from one real font rather than
  generating from text — consistency by construction. Both arms here are
  text-to-image. **That is the remaining untried idea**, and after this result
  it is the more interesting one: an edit model told to "break the strokes" of
  an existing letterform is a different request from "draw a stencil face".

## Consequence

The plan said Task A was *the only task that can lift the ceiling*. It did not
lift it — but it converted a suspicion into a measured fact, and it points the
next attempt at a different mechanism rather than a different model.
