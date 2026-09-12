# Restyle, don't generate: an Apache-2.0 edit model changes the answer (2026-08-23)

Oracle run, 20 Smiths over 2 chains, ~181 s of scouting. Raw report kept at
`research/2026-08-23-oracle-raw-newer-options.md`.

Two findings matter more than the rest of the survey combined.

## 1. Qwen-Image-Edit-2511 is Apache-2.0 and fits a 3090

| | |
|---|---|
| licence | **Apache 2.0 — full commercial use** |
| VRAM | BF16 45 GB · **INT4/Q4 11–16 GB** (plus 32–64 GB system RAM) |
| architecture | dual channel — Qwen2.5-VL for semantics + VAE encoder for visual fidelity |
| text editing | bilingual, with *"font, size, color, style preservation"* and per-letter modification |
| benchmark | GEdit 7.56 EN / 7.52 ZH |
| ecosystem | most active of the edit models as of Aug 2026 |

**This corrects `CLAUDE.md`**, which records "Qwen-Image-Edit-2511 does not fit
24 GB". True at BF16; false at INT4, where 11–16 GB leaves headroom on this card.

**And it revives the approach I had written off.** The Ideogram note concluded
that no image-to-image path was available, which "rules out restyling a neutral
`Kg` pair — the approach with the best a priori consistency guarantee." That
approach is back, and on better terms than anything else found:

1. Render `Kg` **from one neutral font**. The two glyphs are consistent by
   construction, not by hope — they came from the same typeface.
2. Apply **one edit instruction to the whole image**: "make this a heavy
   geometric sans with flat terminals".
3. Both glyphs receive the *same* transformation, in the *same* pass.

Compare that with text-to-image, where consistency depends on the model's
compositional coherence — the thing `2026-08-21-two-styles-in-two-styles-out.md`
showed frontier models fail at, and which the reference gate exists to catch.
Restyling makes consistency **structural** rather than emergent.

It also clears the blocker from the Ideogram exploration: Apache 2.0 permits the
SaaS. No non-commercial dependency, no separate agreement, no repeat of the
FLUX.2-klein-base-9B problem.

**The edit-model field, for the record:**

| | licence | min VRAM | note |
|---|---|---|---|
| **Qwen-Image-Edit-2511** | **Apache 2.0** | **11–16 GB (INT4)** | most active ecosystem |
| FLUX Kontext [dev] | non-commercial + paid | 6.5 GB (INT4) | best structure preservation (KontextBench leader) |
| Step1X-Edit | Apache 2.0 | ~40 GB (FP8) | highest ceiling, does not fit |

FLUX Kontext preserves structure best and repeats the licence problem. Step1X-Edit
is permissive and too large. Qwen is the only one that is both usable and legal
here.

## 2. No typeface-invention benchmark exists

From an exhaustive search, rated HIGH confidence:

> **NO benchmark specifically measuring a model's ability to INVENT a coherent
> new typeface exists in published literature as of Aug 2026.**

Everything found measures font-conditioned text *rendering* — can the model
write legible words in a specified face. Nothing measures whether an invented
typeface hangs together as one design.

Two consequences.

**The gate is not a reinvention.** `analysis/reference_gate.py` (separates
coherent from incoherent at r=0.678, predicts the resulting atlas at ρ=0.666)
and `analysis/style_coherence.py` (p=0.0021, ρ=+0.407) appear to have no
published equivalent. That is worth stating plainly in the README.

**And the README's open item has no prior art to borrow.** "Build a benchmark
retrieval cannot solve" cannot be met by adopting someone else's; it has to be
built, and the two instruments here are the start of one.

## What the run also corrected

- **Qwen-Image-2.0 is NOT open-weight.** One Smith claimed it was; three others
  refuted it. Do not plan around it.
- **FLUX.2-klein-9B is not "permissive."** A Smith described it that way; it is
  the non-commercial base this project already ported away from.
- Seedream 5.0 is API-only, ~$0.045/image.

## What the run failed to deliver

**Chain A's Anderson returned only its triage table, not its findings.** Ten
Smiths' worth of detail on permissively-licensed text-capable models — HiDream-O1,
ERNIE-Image, Z-Image, the FLUX.2 licence matrix — was summarised as "5
high-confidence clusters" and then not written out. Those specifics are lost;
the model names are recorded here so a future pass can go straight to them.
Chain B delivered in full.

## Recommendation, revised

**Restyle a neutral pair with Qwen-Image-Edit-2511, INT4, locally.**

It is the only option found that is simultaneously commercially licensed, small
enough for this GPU, and structurally consistent by construction rather than by
the model's good behaviour.

Order of work:
1. Pull Qwen-Image-Edit-2511 INT4; measure VRAM and seconds per edit on the 3090.
2. Render neutral `Kg` pairs; restyle each with one instruction.
3. Score through `analysis/reference_gate.py` against the 50 real references.
4. Keep **Nano Banana Pro** (2–5 s, $0.134, commercial terms) as the hosted
   control, and **text-to-image** as the comparison arm rather than the default.

**The open risk, unmeasured:** an edit model is built to *preserve* while
changing appearance. Whether it will change a letterform's style enough to be
interesting, without breaking the letter's identity, is exactly the tension
`glyph_classifier.py` measures. Identity is already the instrument for that.

Sources: [Qwen-Image-Edit](https://github.com/QwenLM/Qwen-Image) ·
[Qwen-Image-Edit paper](https://arxiv.org/abs/2508.02324) ·
[FLUX Kontext](https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev) ·
[Step1X-Edit](https://github.com/stepfun-ai/Step1X-Edit)
