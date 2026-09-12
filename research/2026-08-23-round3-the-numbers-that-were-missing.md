# Round 3: the numbers that were missing, and where to set the dial (2026-08-23)

Third oracle run, 20 Smiths / 2 chains, 191 s scouting, 0 errors. Raw report:
`2026-08-23-oracle-raw-round3.md`.

Two rounds of model discovery had converged on the same names, so this round was
pointed at the **gaps that block a build** rather than at finding more models.
That was the right call: the biggest gap — Z-Image had a licence and a speed but
**no text-rendering number at all** — is now closed.

## Z-Image's text capability, finally measured

**LongTextBench (English):**

| model | LongText-EN | date |
|---|---|---|
| ERNIE-Image | **0.973** | May 2026 |
| JoyAI-Image | 0.963 | 2026 |
| Qwen-Image 2.0 | 0.943 | May 2026 |
| **Z-Image** | **0.935** | Nov 2025 |
| Ovis-Image (7B) | 0.922 | Nov 2025 |
| **Z-Image-Turbo** | **0.917** | Nov 2025 |

**CVTG-2K word accuracy:**

| model | word accuracy | CLIP |
|---|---|---|
| Ovis-Image (7B) | **0.920** | — |
| Z-Image | 0.8671 | — |
| **Z-Image-Turbo** | 0.8585 | **0.8048 — highest of all models** |
| Qwen-Image 2.0 | 0.829 | — |

**Z-Image-Turbo holds up.** It is behind ERNIE-Image on LongTextBench but ahead
of Qwen-Image 2.0 on CVTG-2K word accuracy, and it has the **highest CLIP score
of any model in the table** — the best prompt adherence measured, which is the
property that matters most when the prompt is a style description.

Its own paper also reports internal typography scores of 0.987 EN / 0.988 ZH.
Those are self-defined metrics, not comparable to the two benchmarks above, and
should not be quoted alongside them.

**A caution the run's own triage caught.** One Smith wrote "Z-Image: highest
score" on CVTG-2K while its own table showed Ovis-Image higher at 0.920. Anderson
flagged the contradiction. The claim appears to hold only within the Z-Image
paper's chosen baseline set — the usual hazard of self-reported leaderboards,
and every number in both tables is self-reported.

**Ovis-Image (7B)** is new here and tops CVTG-2K at 0.920. Single-Smith, MEDIUM
confidence, no licence or VRAM found. Worth one lookup before the bake-off.

## Where to set the img2img dial

The restyle plan needs a strength value, and the run gives a practical range
[MEDIUM, consistent across 2025–2026 guides]:

| strength | effect |
|---|---|
| 0.10–0.25 | light polish — artifact removal, sharpening |
| **0.30–0.45** | **strong refinement: restyle while preserving composition** |
| 0.50–0.65 | major changes, some compositional drift |

**0.30–0.45 is the band this project wants**, and it is exactly the tension
already named: enough change to be a different typeface, little enough that the
letters stay the letters. `glyph_classifier.py` measures the second half of that
directly, so the dial can be *tuned against identity* rather than guessed.

Mechanically, `strength=1.0` ignores the input entirely and `strength=0.0`
returns it — the parameter scales `init_timestep = min(steps × strength, steps)`.

A working Z-Image img2img call from the run:

```python
image = pipe(
    prompt=...,
    image=init_image,
    strength=0.6,
    num_inference_steps=8,
    guidance_scale=0.0,      # Turbo-specific
    generator=torch.Generator("cuda").manual_seed(42),
).images[0]
```

Note `guidance_scale=0.0` for the Turbo variant. This project has been bitten by
guidance assumptions before — the roadmap records guidance-scale sweeps as dead
because Klein is guidance-distilled.

## The two candidates control structure differently

- **Z-Image img2img** controls structure by *denoising strength on the latent* —
  one scalar, single-stream S3-DiT with lightweight modality adapters.
- **Qwen-Image-Edit** feeds the image through *two* pathways: Qwen2.5-VL for
  semantics and a VAE encoder with Global Skip Connections for fine detail, with
  explicit appearance and semantic editing modes.

The run's own conclusion is the honest one: *"fundamentally different control
mechanisms; not directly comparable without controlled experiments."* No direct
head-to-head exists.

That is precisely what `analysis/reference_gate.py` would supply. A controlled
experiment between them is a few hours of GPU, and nobody has published one.

## What this round did not find

- No licence or VRAM for Ovis-Image.
- No direct Z-Image-vs-Qwen structure-preservation comparison.
- Nothing in August 2026 that changes the shortlist.

## Where this leaves it

The research has converged. Three Apache-2.0 candidates, all with numbers now:

| | text | speed | conditioning |
|---|---|---|---|
| **Z-Image-Turbo** | 0.917 LongText, best CLIP | **3.4 s** | img2img + ControlNet |
| ERNIE-Image | **0.973 LongText** | 8-step turbo | not established |
| Qwen-Image-Edit-2511 | strong, edit-native | ~36 s @3090 | dual-pathway edit |

**Further rounds are unlikely to change this.** Three sweeps have produced the
same shortlist, and the remaining unknowns — does any of them draw a coherent
`K` and `g` in an invented style — are not answerable from the literature,
because the previous round established **no benchmark for that question exists**.

The next useful step is not research. It is downloading Z-Image-Turbo, generating
a batch at strength 0.30–0.45, and scoring it through the gate.
