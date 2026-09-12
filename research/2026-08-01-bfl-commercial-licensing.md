# The BFL commercial route: available, but our architecture can't use the cheap version (2026-08-01)

**Question.** Every technical lever has hit the 4B's ceiling. The 9B is
non-commercial. What does a commercial licence actually cost, and is there a
cheaper route?

## BFL does sell commercial licences — four tiers

From https://bfl.ai/licensing, models listed verbatim:

| tier | models | volume | how to buy |
|---|---|---|---|
| Builder | "FLUX.2 [klein] models" | 10K images/mo, 1 domain | **self-serve**, from the dashboard |
| **Platform** | "FLUX.2 [klein] **Base 9B** + FLUX.2 [dev]" | 100K images/mo, 1 domain | **contact sales** |
| Professional | "FLUX.2 [dev]" | 100K images/mo, 3 domains | contact sales |
| Enterprise | "All models + new releases" | custom | contact sales |

All tiers include **10 licensed users, fine-tuning and LoRA rights**, and
self-hosting of weights on your own infrastructure.

**The tier we need is Platform, not Builder.** `klein Base 9B` — what our
model is trained on — appears *only* under Platform. Builder's generic
"FLUX.2 [klein] models" excludes it. So the self-serve path does not cover us.

**No pricing is published** for any tier. The only public anchor found:
BFL's knowledge base reportedly lists a self-hosted commercial licence for
**Dev at $999/mo including 100K images, $0.01/image after** — *reported via
search, not verified first-hand*. Platform bundles klein Base 9B *and* dev at
the same 100K volume, so it is plausibly at or above that. Treat as an order of
magnitude, not a quote.

Note also that public sources repeat a blanket "Klein is Apache 2.0, no licence
fee" claim. That is **true for the 4B variants and false for both 9B
variants**, which the HF API and `LICENSE.md` confirm directly — the same
ambiguity `research/2026-07-27-klein-licensing-and-4b-port.md` already
corrected once.

## The cheaper route exists — and we cannot use it

**fal.ai hosts `fal-ai/flux-2/klein/9b/base/lora`** — klein 9B *Base* with
custom LoRA, text-to-image and image-to-image (`.../9b/base/edit/lora`).
Third-party providers include commercial usage rights in their terms because
they hold commercial agreements with BFL. Pricing ~**$0.02 per megapixel** of
input and output.

For our workload that is roughly **$0.04 per font** (1280² atlas out = 1.64 MP,
512² reference in = 0.26 MP), with no licence negotiation and no minimum. For
anything short of very high volume that is dramatically cheaper than a Platform
licence.

**But our architecture is not a standard LoRA, so it cannot be served this way.**

The adapter does carry the widened embedder — `base_model.model.x_embedder.weight`
is in the 289-tensor checkpoint via `modules_to_save`. What does *not* travel is
`generation_lib._install_glyph_channel_hook`: runtime Python that loads
`dataset_v2/cache/template.pt` and channel-concatenates a (6400, 128) template
onto the atlas tokens on every forward pass. A managed endpoint runs standard
LoRA inference. It will not run our hook, cannot be handed a template latent
file, and our embedder expects **256 input channels where the base supplies
128** — so loading the adapter bare would mismatch, not merely degrade.

## The strategic cost of a decision made for training speed

`docs/superpowers/plans/2026-06-03-glyph-latent-conditioning.md` chose
channel-concat over token-concat specifically to keep the sequence at 7424
instead of 13824, which would have made training ~9 days instead of ~4.

That choice bought training speed and **cost portability**. Token-concat would
have expressed the same conditioning through FLUX.2's *native multi-image
reference* mechanism — exactly what fal's `edit/lora` endpoints already accept —
and would therefore be servable on managed infrastructure today, on the 9B,
commercially, at ~$0.04/font.

This was not a foreseeable error: the portability consequence only becomes
visible once managed 9B-Base-with-LoRA hosting exists. But it is now the single
highest-leverage architectural fact in the project.

## Options, honestly ranked

1. **Retrain with token-concat conditioning on klein-9B-Base, serve via fal.**
   Gets 9B quality, commercially, at ~$0.04/font, no licence negotiation, no
   GPU to own. Costs a retrain at roughly 2× the sequence length — the ~9-day
   figure from the original plan, though on rented hardware that is a cost not a
   calendar. **This is the path to what was actually asked for.**
2. **Contact BFL sales for Platform.** Gets 9B quality with our existing
   architecture intact, self-hosted, no retrain. Unknown price, likely
   four figures monthly. One email to find out.
3. **Ship the 4B.** Free, Apache-2.0, works today, ~4 points of style fidelity
   below the 9B and concentrated in abstract typefaces.

Option 1 is the one this research surfaces that was not previously on the table.

## Sources

- BFL licensing tiers — https://bfl.ai/licensing
- BFL self-serve licence knowledge base — https://help.bfl.ai/articles/9272590838-self-serve-dev-license-overview-pricing
- fal.ai klein 9B Base LoRA — https://fal.ai/models/fal-ai/flux-2/klein/9b/base/lora/api
- fal.ai klein 9B Base edit LoRA — https://fal.ai/models/fal-ai/flux-2/klein/9b/base/edit/lora
- FLUX Non-Commercial Licence v2.1, `LICENSE.md` in the model repo
