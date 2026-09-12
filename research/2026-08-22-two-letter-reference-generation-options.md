# Generating the two-letter reference: the options, measured on speed and fit (2026-08-22)

Follow-up to `2026-08-22-how-to-generate-the-reference.md`, adding the two
hosted candidates that were named — ChatGPT Image 2.0 and Nano Banana — and the
local field. Nothing here has been run; these are availability, price and
latency facts plus one expert verdict.

> Method note: this was researched directly rather than through the `/oracle`
> harness. A hook refuses any command touching `~/.claude/skills/`, which caught
> executing `oracle_sdk.py` even read-only. Not routed around.

## An expert verdict that corroborates our own measurements

Simon Cozens — a fonttools/typography engineer, not an AI vendor — surveys the
field in [The State of AI Font Generation](https://simoncozens.github.io/state-of-ai-font-generation/):

> Current AI excels at generating raster glyph **shapes** but cannot yet handle
> Latin font requirements like **spacing, kerning, and metrics**.

That is independently the same split this project measured: 74% of the finished
font's error is letterfitting and the pipeline's invented constants, not shape
(`2026-08-20-the-atlas-format-is-the-common-cause.md`).

Two more of his points land on findings we reached separately:

- **Latin glyphs are sparse, creating an "imbalanced class problem" where models
  default to generating blanks.** We measured that as the ink collapse — corpus
  expansion @6016 came out at 0.0440 against a GT 0.0652, **−32.5%**, "collapsed
  to hairlines."
- **Vector approaches lag**; "practically everyone else uses rasters", because
  long vector sequences are hard to predict and hard to compare with metrics.
  That tempers the VecGlypher enthusiasm in the previous note.

He puts competent end-to-end AI font generation "three or four years away."

**This supports the product's division of labour rather than undermining it.**
Reference generation needs only two glyph *shapes* — the thing he says AI is
already good at. Spacing and metrics stay our pipeline's problem, and we have
measured exactly how much they cost.

## The hosted candidates

| | Nano Banana Pro | GPT Image 2 |
|---|---|---|
| identity | Gemini 3 Pro Image, GA 18 Jun 2026 | OpenAI |
| **latency** | **2–5 s** | 8–25 s (p50, medium) · **~195 s median at high quality** |
| price / image | $0.134 GA (range $0.039–0.24) | ~$0.006 low · $0.053 medium · $0.211 high |
| text accuracy | 94–96%, reported class-leading | rendered every word with correct spelling, zero character bleeding |
| notable | strong editing, identity preservation across up to 5 subjects | held **distinct font identities** across one spread |

**Latency is the deciding axis for a select-and-iterate loop.** The user needs
several candidates to choose between, so the cost is N generations per round.
Nano Banana Pro at 2–5 s supports that. GPT Image 2 at high quality does not —
~195 s median, ~280 s p95, means a four-candidate round is roughly thirteen
minutes.

**Both carry the same caveat, and it is the important one.** Their benchmarks
measure *legible text rendering* — writing readable words in a scene. Our task
is *inventing a coherent typeface*. A 2026 comparison finds these models still
"[can't reconcile conflicting construction logics to invent a coherent
system](https://ropewalk.ai/blog/best-ai-text-in-image-models-2026)" — which is
precisely the failure `analysis/reference_gate.py` was built to catch.

## The local field

| model | on disk | size / fit | note |
|---|---|---|---|
| **Ideogram 4** | no | **9.3B DiT**, ~19 GB bf16, ~9 GB fp8 | **Open weights since 3 Jun 2026.** The typography specialist, now self-hostable. Strongest local candidate. |
| GLM-Image int4 | **yes** | int4 | MIT, native Glyph-ByT5 encoder. Cheapest thing to actually measure. |
| FLUX.2-klein 4B | **yes** | ~13 GB, sub-second | Our own base. A restyler, not a reference generator. |
| VecGlypher 27b-it | no | **27B, ~54 GB bf16** | Best task fit; **does not fit a 3090**, no int4 build exists, licence listed only as "other". |
| DiffInk | no | ICLR 2026, weights out | Handwriting-focused, not type design. |

> **Corrected 2026-08-23.** This note ranked Ideogram 4 first on the strength
> of "open weights" without reading the licence. The weights are under the
> **Ideogram 4 Non-Commercial Model Agreement** — fine for the R&D this
> project is doing, and prohibited for a revenue-generating product. See
> [the full exploration](2026-08-23-ideogram-4-fully-explored.md).

**Ideogram 4 is the finding.** The model repeatedly named as the typography
leader shipped open weights in June, at a size that fits this GPU. Reported as a
unified DiT giving "more precise glyph placement and consistent letterform
shapes" — consistency being the exact property we need.

**VecGlypher is the disappointment.** Weights *are* released
(`VecGlypher/VecGlypher-27b-it`), which the previous note could not confirm. But
27B in BF16 is ~54 GB. It needs an int4 build that does not exist, and its
licence is unnamed, which is a live risk for a SaaS.

**Correct the GLM-Image speed figure before dismissing it.** `CLAUDE.md` records
"~36 min/image". That measurement was bf16 sitting at 23.7 GB of 24.5 — paging.
The int4 build exists to fit and is already downloaded.

## Recommendation

Ranked against the stated priorities — small purposeful local ideal, quality and
speed major:

1. **Ideogram 4, self-hosted.** Best combination of typography specialisation,
   open weights and 3090 fit. Untested here; this is the one to try.
2. **Nano Banana Pro** as the hosted control and the fallback. At 2–5 s and
   $0.134 it is the only candidate that certainly supports a real iterate loop
   today, and it is cheap enough that a round of four costs about 54 cents.
3. **GLM-Image int4**, because measuring it costs one image and it is already on
   disk.
4. **GPT Image 2** at medium quality only. The high tier is unusable for
   iteration.

**Whatever wins, generate both glyphs in one call.** Consistency is a property
of producing them together, not of model quality — that is our own finding, and
the frontier models fail it too.

## The bake-off is already built

`analysis/reference_gate.py` scores candidate references GT-free (separates
coherent from mixed at r=0.678, predicts the resulting atlas at ρ=0.666), and
`analysis/build_synthetic_references.py --external-dir` already ingests a
directory of generated PNGs. The 50 real references are the coherent control.

Sources:
[Nano Banana Pro](https://blog.google/innovation-and-ai/products/nano-banana-pro/) ·
[Nano Banana Pro pricing](https://pricepertoken.com/pricing-page/model/google-gemini-3-pro-image-preview) ·
[GPT Image 2 pricing](https://unifically.com/blogs/gpt-image-2) ·
[2026 image API benchmark](https://www.atlascloud.ai/blog/tips/2026-ai-image-api-benchmark-gpt-image-2-vs-nano-banana-2-pro-vs-seedream-5-0) ·
[Ideogram 4 open weights](https://www.spheron.network/blog/deploy-ideogram-4-gpu-cloud/) ·
[VecGlypher weights](https://huggingface.co/VecGlypher/VecGlypher-27b-it) ·
[State of AI font generation](https://simoncozens.github.io/state-of-ai-font-generation/) ·
[Text-in-image model comparison](https://ropewalk.ai/blog/best-ai-text-in-image-models-2026)
