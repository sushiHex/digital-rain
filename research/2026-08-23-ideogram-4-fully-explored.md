# Ideogram 4, fully explored: the best technical fit, and it cannot ship (2026-08-23)

**Verdict up front.** Ideogram 4 is the strongest local candidate for generating
the two reference glyphs, and its weight licence forbids the one thing this
project was reframed to become. It is usable *now*, for research, and it is a
dead end for the SaaS unless a separate commercial agreement is obtained.

This corrects the previous note
(`2026-08-22-two-letter-reference-generation-options.md`), which recommended it
first on the strength of "open weights" without reading the licence.

## The licence, from the primary source

Released 3 June 2026 as Ideogram's first open-weight text-to-image model, under
a **split licence**: inference code Apache-2.0, weights under the **Ideogram 4
Non-Commercial Model Agreement**. Weights are gated on HuggingFace.

Two clauses matter, and they say different things about two different objects.

**On running the model** — [LICENSE-IDEOGRAM-4-NON-COMMERCIAL](https://github.com/ideogram-oss/ideogram4/blob/main/model_licenses/LICENSE-IDEOGRAM-4-NON-COMMERCIAL):

> "activity or use that fits in any of the following categories: (i) use that
> does not directly or indirectly generate revenue…"

and it explicitly excludes *"training, fine tuning, or distilling AI models for
commercial use."* Secondary reporting of the same agreement puts it plainly:
*"any use that involves generating Output to include in, or to advertise or
promote, revenue-generating products or services, in each case, is not a
Non-Commercial Purpose."*

**On the output it produces:**

> "We claim no rights in outputs you generate using the Model. You are
> responsible for outputs and their subsequent uses."

> "You may not use any Output to develop, train, fine-tune or distill a model or
> other product or services that is competitive with the Model or any of
> Company's other products or services."

**Resolving the apparent contradiction.** Ideogram claims no ownership of your
images. But *operating the weights* in service of a revenue-generating product
is outside "Non-Commercial Purposes" regardless of who owns the pixels. The
"outputs are yours" clause is about title, not about permission to run the
model. Commercial deployment goes through the paid API, a subscription, or a
separate agreement the Company "may grant or not grant in its sole discretion."

**What IS permitted, and it covers us today.** For-profit entities may use it
for *"testing, evaluation, or research and development in a non-production
environment."* Evaluating Ideogram 4 as a reference generator, measuring it
against the gate, and writing up the result is squarely inside that.

**A second, subtler risk if a commercial licence were obtained.** A font
generator built on Ideogram-generated references may be "competitive with… any
of Company's other products or services" — Ideogram sells design-image
generation. That is not clearly true, and not clearly false. It would need
counsel, not my reading.

## This is the same trap the project already escaped once

`FLUX.2-klein-base-9B` is non-commercial. That single fact drove the entire port
to the Apache-2.0 klein-4B, which `CLAUDE.md` records as "the licensing fix and
also the 4-step speed win."

Adopting Ideogram 4 would **reintroduce exactly that constraint one layer
upstream**, at the reference generator. The project would be back to a
non-commercial dependency it had already paid to remove.

## The technical fit, which is genuinely good

| property | value | relevance here |
|---|---|---|
| parameters | 9.3B DiT, 34 layers | — |
| runnable variant | **`ideogram-ai/ideogram-4-nf4`** | NF4 is documented as fitting a **24 GB GPU** |
| framework | `Ideogram4Pipeline` in diffusers (git main) | drop-in; no custom runtime |
| resolution | native **256–2048**, multiples of 16 | our reference canvas is 1280×1280 — a multiple of 16, natively supported |
| prompting | trained **exclusively on structured JSON captions** | see below |
| layout control | **`bbox` coordinates to place text elements**, `compositional_deconstruction` with per-element descriptions | directly expresses our two-column format |
| image-to-image | **not documented** | rules out "restyle a neutral Kg pair" |
| speed | **not published** | the main unmeasured risk |

**The `bbox` interface is the standout.** Our reference is two glyphs in two
columns on one canvas, and the whole method rule from
`2026-08-21-two-styles-in-two-styles-out.md` is *generate both in one call*.
Ideogram 4 lets you name each element and place it explicitly, in a single
generation. No other candidate exposes that.

**No image-to-image is a real loss.** It removes the approach with the best a
priori consistency guarantee — take a neutral `Kg` rendered from one font and
restyle it with a single edit, so both glyphs receive the same transformation.
With text-to-image only, consistency has to come from the model's own
compositional coherence, which is precisely what the gate exists to check.

## The capability question no benchmark answers

Every Ideogram number is about **text in a scene** — words on posters, signs,
book covers. Practitioner guidance is explicit that its training emphasised
"typography in context — not just isolated letters, but words forming sentences."

Our task is two *isolated* letterforms on a black ground, in an invented style.
That is a different distribution from anything it was optimised for.

Two signals point in opposite directions:

- **Favourable:** "short lines render far more reliably than longer ones", and
  two characters is the shortest possible string. Also, prompting practice is to
  strip font *names* in favour of **letterform descriptions** — which is exactly
  the interface the product wants a user to speak in.
- **Unfavourable:** the same guidance says Ideogram "renders type faithfully",
  which describes reproducing a described face, not inventing a coherent new
  one. The general 2026 finding that these models "cannot reconcile conflicting
  construction logics to invent a coherent system" has not been shown to exclude
  Ideogram.

**This is measurable here, cheaply, and permitted by the licence.** The gate
separates coherent from incoherent references at r=0.678 and predicts the atlas
at ρ=0.666, and `build_synthetic_references.py --external-dir` already ingests a
directory of PNGs.

## Recommendation

**Use it as the research instrument it is licensed to be, and do not build the
product on it.**

1. Pull `ideogram-ai/ideogram-4-nf4` (accept the HF gate), generate a batch of
   two-glyph references from JSON prompts with `bbox` placement, and score them
   through `analysis/reference_gate.py` against the 50 real references.
2. That answers the capability question and measures the missing speed figure in
   the same run. Both are R&D in a non-production environment.
3. **If it wins**, the finding is "a 9.3B open-weight DiT can generate usable
   references" — which is worth knowing, transfers as evidence to whatever ships,
   and makes the case for either a commercial licence or a comparable
   permissively-licensed model.
4. **For anything revenue-generating**, the candidates remain Nano Banana Pro
   (2–5 s, $0.134, commercial terms available) or a permissively-licensed local
   model.

## What I got wrong yesterday

I ranked Ideogram 4 first on "open weights" without reading what the licence
permitted. "Open weights" and "usable in a product" are different claims, and
this project has a documented history of paying for that exact conflation — the
non-commercial base model is the reason the 4B port exists.

Sources:
[Ideogram 4 code](https://github.com/ideogram-oss/ideogram4) ·
[the licence](https://github.com/ideogram-oss/ideogram4/blob/main/model_licenses/LICENSE-IDEOGRAM-4-NON-COMMERCIAL) ·
[nf4-diffusers card](https://huggingface.co/ideogram-ai/ideogram-4-nf4-diffusers) ·
[nf4 weights](https://huggingface.co/ideogram-ai/ideogram-4-nf4) ·
[prompting guide](https://pixeldojo.ai/guides/ideogram-4-prompting-guide) ·
[deployment notes](https://www.spheron.network/blog/deploy-ideogram-4-gpu-cloud/)
