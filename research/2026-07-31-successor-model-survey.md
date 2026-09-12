# Successor-model survey: is there anything better than FLUX.2 for this task? (2026-07-31)

**Question.** The 4B trails the 9B on structurally distinctive typefaces, and
the 9B is non-commercial. Is there a newer base — FLUX 3 or otherwise — that
would give better results?

Our constraints are narrow, so general "best open model" rankings mostly do not
apply:

1. **reference-image conditioning** — the task is style-reference → 95-glyph atlas
2. **LoRA-trainable on one 24 GB 3090** (we quantise to int8)
3. **commercially usable weights** — the entire point of the 4B exercise
4. **fine structural detail** — the axis where the 4B falls short

## FLUX 3 — released, but not available

Released **2026-07-23**. Video and Action are in early access; per MarkTechPost,
"Image follows, open weights come last." **`black-forest-labs/FLUX.3` does not
exist on HuggingFace** (RepositoryNotFoundError) — confirming no open weights.
Licence unstated. BFL says faster and open-weight versions ship "later this
year."

**Not actionable. Worth re-checking when the image model and weights land.**

## Candidates that do exist

Weight sizes from the HuggingFace API, per component:

| model | licence | transformer | other | 3090-trainable? |
|---|---|---|---|---|
| **zai-org/GLM-Image** | **MIT** | **12.9 GB** | VLE 18.8 GB | maybe — see below |
| Qwen/Qwen-Image-Edit-2511 | apache-2.0 | 38.1 GB | TE 15.5 GB | **no** — ~19 GB at int8 before activations |
| Tongyi-MAI/Z-Image-Turbo | apache-2.0 | 22.9 GB | TE 7.5 GB | maybe, but **text-to-image only** |
| black-forest-labs/FLUX.2-dev | other (non-commercial) | 165 GB total | | no |

Reference points from this project: klein-base-9B's transformer is 17.7 GB bf16
and trained at 15.6 GB peak; klein-base-4B is 7.2 GB and peaks at 7.8 GB.

Z-Image-Turbo has no `processor` component, i.e. no image-conditioning path —
it does not fit our architecture regardless of its other merits.

## GLM-Image is the interesting one — and the caveat is important

- **MIT licence** — more permissive than Apache-2.0, and it moots the entire
  licensing problem.
- **It ships a native Glyph Encoder**, "a text module for improving accurate
  text rendering within images." That is conceptually the same idea this
  project built by hand as glyph-latent channel conditioning.
- Best-in-class text benchmarks: **0.9116** word accuracy on CVTG-2K, **0.9557**
  on LongText-Bench, reported as significantly ahead of Qwen-Image and Z-Image.
- Supports image-to-image, style transfer, and identity-preserving generation.
- 33 adapters and 13 finetunes already exist on the Hub.

**The caveat, and it is a real one.** Those benchmarks measure *legible text
rendering* — can the model write readable words. Our task is *style-faithful
glyph generation* — can it reproduce an unusual typeface's letterforms. A glyph
encoder optimised for legibility plausibly pushes output toward **canonical**
letterforms, which is exactly the wrong bias for Fascinate Inline or a dot-grid
face. This project already established that legibility and style fidelity are
independent axes (`research/2026-07-18-wrong-letters-are-a-metric-artifact.md`);
a model tuned hard for the first could well be *worse* on the second.

That is a hypothesis, not a finding. It is also cheap to test: run GLM-Image
zero-shot on a few holdout references and score with the existing harness.

## Other blockers before any switch

- **Hybrid AR + diffusion architecture** (9B GLM-4-9B autoregressive generator +
  7B single-stream DiT decoder). Our `x_embedder` channel-concat hook does not
  port directly; the conditioning would need redesigning.
- **VRAM is not obviously fine.** The 12.9 GB transformer is comfortable, but
  the 18.8 GB vision-language encoder is not, and unlike our text encoder — which
  we encode once and free — a VLE used for reference conditioning may need to
  stay resident.
- **50 default inference steps**, against klein-4B distilled at 4.
- **Switching bases invalidates everything measured.** Different VAE means
  re-caching the dataset and the glyph template; every quality number would need
  re-establishing, exactly as with the 4B port.

## Recommendation

No drop-in upgrade exists today. In priority order:

1. **Get a commercial-licence quote from BFL** (https://bfl.ai/licensing). It is
   the only path to *actual* 9B quality rather than an approximation, and it
   costs one email.
2. **Cheap GLM-Image probe** — zero-shot on a handful of holdout references,
   scored with the existing harness, to test the legibility-vs-style hypothesis
   before committing to anything. Hours, not days.
3. **Re-check FLUX 3** when the image model and open weights land.

---

# GLM-Image follow-up: has anyone done this on it, and would its Glyph Encoder help?

## Nobody has done anything similar — and the ecosystem is a mirage

Queried the Hub for everything built on `zai-org/GLM-Image`:

- **33 "adapters"** — almost entirely NSFW character LoRAs, plus several
  *mislabelled Wan 2.2 video* LoRAs carrying wrong base-model metadata.
  Downloads 0–105. **Zero font, glyph, or typography work.**
- **13 "finetunes"** — mostly spam with incoherent tag soup (`allennlp`,
  `asteroid`, `fasttext`, `chemistry`, `medical`) and 0 downloads. Not real
  finetunes.
- The one genuinely useful derivative: **`Intel/GLM-Image-int4-AutoRound`**
  (MIT, 57 downloads) — an int4 quantisation, relevant to the VRAM question.

**Correction to the section above**, which cited "33 adapters and 13 finetunes"
from the model card as evidence of a healthy ecosystem. It is not one.

The wider literature is no help either: font-generation research is dominated by
CJK few-shot synthesis (HFH-Font, DiffCJK, Diff-Font, FontDiffuser) and font
*effects* (FontStudio), using purpose-built models rather than the newest
general ones. Latin 95-glyph style transfer on a large general model is an
unusual thing to be doing.

## Its Glyph Encoder is Glyph-ByT5 — the pattern we already implemented

GLM-Image "incorporates a Glyph-ByT5 encoder that performs character-level
encoding for rendered text regions… glyph embeddings are **added to the visual
tokens**."

`docs/superpowers/plans/2026-06-03-glyph-latent-conditioning.md` describes this
project's own architecture as "the TextFlux/FLUX-Text/**Glyph-ByT5** pattern
(reported char-acc <20%→~90%), realized via FLUX.2's existing multi-image
reference mechanism." `docs/quality-roadmap-v3.md` named the same pivot.

**So GLM-Image ships natively the exact pattern we built by hand.** We add
glyph-template latents by channel-concat; it adds ByT5 glyph embeddings to the
visual tokens. Same family, different injection.

**Which means its headline advantage is one we have already banked.** The
"<20% → ~90% char-acc" figure describes models that could not render letters at
all. Our identity is **0.9893–0.9936**. That headroom is spent. Glyph-ByT5
encodes *canonical character shape derived from text* — it tells the model
*which* letter, not *in whose style*. It offers nothing for the axis we are
actually failing: style fidelity on structurally distinctive typefaces.

## The counter-argument, which is why this is still worth a probe

GLM-Image's "decoder, in conjunction with the text encoder of Glyph Encoder,
focuses on **restoring high-frequency details** of images and text strokes."

High-frequency structural detail is *precisely* our failure mode — Fascinate
Inline's inline stroke, Bitcount's dot-grid, and the degradation visible at 4
steps. A decoder explicitly tuned for that could help where Glyph-ByT5
conditioning would not.

So the two considerations point opposite ways:

| | effect on our problem |
|---|---|
| Glyph-ByT5 conditioning | canonical-letterform bias — **wrong direction** for abstract faces |
| High-frequency-detail decoder | **right direction** for inline/dot-grid structure |

Net effect is genuinely uncertain, which is what makes a cheap zero-shot probe
the right next step rather than a base switch.

## Verdict

Not a drop-in upgrade, and the reason is now mechanistic rather than a guess:
its signature feature solves a problem we already solved. Worth a few hours of
zero-shot probing on holdout references — scored with the existing harness —
to test whether its detail-restoring decoder helps abstract typefaces. Not
worth a base switch on present evidence.

---

# GLM-Image probe result (2026-08-01): not viable here

## Getting it to run at all took four attempts

| approach | outcome |
|---|---|
| bf16 + `enable_model_cpu_offload` | **fails** — a module stays on CPU (`CUDABFloat16Type` vs `CPUBFloat16Type`) |
| bf16 + `enable_sequential_cpu_offload` | **fails** — leaves meta tensors, and the pipeline calls `.item()` on them |
| `Intel/GLM-Image-int4-AutoRound` | **fails** — diffusers supports `bitsandbytes_4bit/8bit, gguf, modelopt, quanto, torchao`, **not** `auto-round` |
| bf16 + our own `optimum-quanto` int8 | **works** — the pattern `generation_lib` already uses for FLUX |

Two smaller API mismatches first: `image=` must be a list (the pipeline calls
`len()` on it), and `height`/`width` are mandatory — it builds an internal
`target_h` and dies on `None`.

**That both offload paths are broken matters beyond this probe.** It means bf16
GLM-Image cannot run on a 24 GB card with current diffusers at all; any real
work would need hand-quantisation or a bigger GPU.

## It is ~2000× slower than our model per unit of output

**98 s/step, 2149 s (36 min) for ONE 1024×1024 image at 20 steps**, sitting at
23.7 GB of 24.5 — almost certainly paging, the same pathology as the
grad-checkpointing-off arm in
`research/2026-07-31-...` / the throughput probe.

For scale: our 4B renders an entire **95-glyph atlas** in 62.7 s at 20 steps.
Per glyph produced, GLM-Image here is roughly three orders of magnitude slower.
The full 5-font probe would have taken ~7.5 h.

## What it actually produced

Given a holdout reference (Wonky's "Kg" glyphs) and a prompt asking for
"Hamburg" in that typeface, it **kept the reference glyphs as image content and
added the word beside them** — behaving as an image *editor*, not a
style-transfer model. The rendered "Hamburg" is clean generic sans-serif, not
Wonky's wobble.

Legible text, canonical letterforms. That is the Glyph-ByT5 bias predicted
above: it optimises *which letter*, not *in whose style*.

**Weaknesses of this test, stated plainly:** one font, and the *control* font at
that (Wonky is comparatively plain); 20 steps rather than the default 50; int8
quantisation; and a prompt it evidently read as an edit instruction rather than
a style transfer. A better prompt might do better. What it does not change is
the throughput result, which is disqualifying on its own.

## Verdict: stop here

Not viable on this hardware, and the mechanistic prediction held on the one
sample obtained. Pursuing it further would mean prompt engineering at ~36 min
per sample, on a model whose signature feature addresses a problem this project
already solved, to reach a base that is three orders of magnitude slower per
glyph and needs its conditioning architecture redesigned.

Re-check if BFL releases FLUX 3 open weights, or if GLM-Image gets working
offload in diffusers and a distilled/faster variant.

## Sources

- MarkTechPost, FLUX 3 release — https://www.marktechpost.com/2026/07/26/black-forest-labs-releases-flux-3-a-multimodal-flow-model-for-image-video-audio-and-robot-action-prediction/
- VentureBeat, FLUX 3 limited release — https://venturebeat.com/technology/black-forest-labs-launches-flux-3-capable-of-generating-images-and-20-second-video-with-audio-but-in-limited-release-to-start
- GLM-Image model card — https://huggingface.co/zai-org/GLM-Image
- Diffusion Doodles model rundown — https://diffusiondoodles.substack.com/p/model-rundown-z-image-turbo-qwen
- Weight sizes, licences, adapter/finetune lists: HuggingFace API, queried 2026-07-31
- deeplearning.ai on GLM-Image's architecture — https://www.deeplearning.ai/the-batch/zhipus-glm-image-blends-transformer-and-diffusion-architectures-for-better-text-in-images
- GLM-Image repo — https://github.com/zai-org/GLM-Image
- Diffusion text-image paper collection — https://github.com/yeungchenwa/Recommendations-Diffusion-Text-Image
