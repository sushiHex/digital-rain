# The permissive local field opened up (2026-08-23, round 2)

Second oracle run, 20 Smiths / 2 chains, 192 s scouting, 0 errors. Raw report:
`2026-08-23-oracle-raw-round2.md`.

The picture from this morning — "nothing local is both good at type and
commercially usable" — is **no longer true**. Three Apache-2.0 models now fit
this GPU, and one of them corrects a closed track in `CLAUDE.md`.

## The field, as of today

| model | licence | size | VRAM | speed | image conditioning |
|---|---|---|---|---|---|
| **Z-Image-Turbo** | **Apache 2.0** | **6B** | **6 GB GGUF** · 8 GB FP8 | **3.4 s** @4090, 8 steps | **yes, as of Aug 2026** |
| **ERNIE-Image** | **Apache 2.0** | 8B DiT | GGUF builds exist | 8-step Turbo variant | not established |
| Qwen-Image-Edit-2511 | Apache 2.0 | 20B | 11–14 GB INT4 | **~36 s** @3090, 8-step | edit-native |
| FLUX.2-klein-4B | Apache 2.0 | 4B | ~13 GB | sub-second | our own base |

## Correction: Z-Image now has an image-conditioning path

`CLAUDE.md`'s closed-tracks list says **"Z-Image-Turbo has no image-conditioning
path."** That was true when `2026-07-31-successor-model-survey.md` checked, and
it is not true now:

- Native **`ZImageImg2ImgPipeline`** for both Z-Image and Z-Image-Turbo.
- **ControlNet Union 2.1** (Jan 2026) — canny, depth, pose, MLSD, HED, scribble,
  gray, inpaint. Lite models are 1.9 GB.
- Resolutions 512–2048, any aspect ratio.

That reopens the track, and on unusually good terms: **6B, Apache 2.0, 6 GB
quantised, 3.4 seconds.** It is the closest thing found to the stated ideal of a
small, purposeful, fast local model.

## Speed is the axis that separates them

The restyle plan from this morning nominated Qwen-Image-Edit-2511. The measured
number is worse than hoped:

> **RTX 3090, 8-step LoRA, 1024×1024: ~36 seconds, 17 GB+** [MEDIUM confidence]

A four-candidate round is then ~2.4 minutes. Usable, not pleasant.

Two mitigations, both real but unconfirmed on this card:

- **Nunchaku SVDQuant INT4 builds exist** — `QuantFunc/Nunchaku-Qwen-Image-EDIT-2511`
  (community, not official), 11.5–14.2 GB, claiming **2×–11× speedup** and, with
  per-layer offload, **3–4 GB VRAM**. Official `nunchaku-tech` builds cover the
  2509 base, not 2511. Pre-Blackwell support is stated, so a 3090 qualifies.
- GGUF builds from Unsloth and others.

Note this project's own Nunchaku history: `route_b/` closed because the
FLUX.2-klein quantised transformer had no runtime-LoRA API. That was a
FLUX-specific finding and says nothing about Qwen — but it is a reminder that
"a Nunchaku build exists" and "it does what you need" are different claims.

**Z-Image-Turbo at 3.4 s is roughly ten times faster than Qwen-Image-Edit at 36 s**,
on comparable hardware. If its img2img is good enough for restyling a letterform
pair, it wins on every axis this project cares about.

## The trade the two candidates represent

- **Qwen-Image-Edit-2511** is an *edit* model. Restyling a neutral `Kg` pair is
  its native operation, so consistency is structural. It is 20B and slow.
- **Z-Image-Turbo** is a *generation* model that has grown img2img. Restyling is
  adjacent to its training, not central. It is 6B and fast.

Neither has been tested on letterforms. That is what the gate is for.

## ERNIE-Image is the text-rendering leader among permissive models

Apache 2.0, 8B DiT, released 15 April 2026, **LongTextBench 0.9733** — above the
0.9557 that made GLM-Image interesting in the July survey, and GLM-Image is MIT
but did not fit. Two Smiths agree on licence, size and score.

Its image-conditioning story is not established here, so it is a text-to-image
arm rather than a restyle arm.

For scale, the run also records **Seedream 4.5 at 0.9882** on the same
benchmark — the leader overall, and API-only.

## What this does not change

Every one of these is benchmarked on **legible text rendering**, not on
inventing a coherent typeface. The run's previous round established that **no
benchmark for the latter exists**. LongTextBench 0.9733 says ERNIE-Image writes
words accurately; it says nothing about whether it can invent a `K` and a `g`
that belong to the same imaginary typeface.

That gap is the reason `analysis/reference_gate.py` exists, and it is why the
bake-off has to be run rather than reasoned about.

## Revised order of work

1. **Z-Image-Turbo, GGUF or FP8.** Cheapest to try, fastest, smallest, Apache.
   Test both text-to-image (two glyphs in one call) and img2img restyle.
2. **Qwen-Image-Edit-2511**, Nunchaku INT4 if the community build works. The
   principled restyle arm, if its speed can be made tolerable.
3. **ERNIE-Image** as the text-rendering-strong text-to-image arm.
4. **Nano Banana Pro** as the hosted control at 2–5 s.

All four score through `analysis/reference_gate.py` against the 50 real
references. That is the comparison; the rest is prior.

## Disputes and gaps the run flagged

- Nunchaku's official org name is given as both `nunchaku-tech` and
  `nunchaku-ai` by different Smiths.
- No AWQ or GPTQ quantisation of Qwen-Image-Edit-2511 exists (comprehensive
  search, HIGH confidence).
- No documented minimum diffusers version for Qwen-Image-Edit-2511 — only
  "install from GitHub main", which is a reproducibility hazard.
- No independent 3090/4090 benchmark at 1024×1024 exists for Qwen-Image-Edit;
  the ~36 s figure is a community report at MEDIUM confidence.
