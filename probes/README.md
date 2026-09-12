# probes/

**Small targeted probes (spikes).**

Short scripts that answer one question, usually feeding a research/ note.

Run from the repo root, either way:

```bash
python probes/<script>.py --help
python -m probes.<script> --help
```

Scripts import repo-root modules (`atlas_constants`, `eval_checkpoint`, ...); a two-line
`sys.path` bootstrap at the top of each makes direct-path invocation work too.

## Contents (21)

- `run_caption_probe.py` — Render the caption A/B grid: 4 prompt prefixes x 3 reference fonts.
- `spike0_verify.py` — Verify the FLUX.2-klein model variants exist and report sizes / cache state.
- `spike1_distilled.py` — Spike 1: does the Ref2Font V3 LoRA survive a FAST klein variant with grid integrity, at sub-minute latency?
- `spike2_analyze.py` — Spike 2 (part 2): measure cross-seed per-cell failure independence.
- `spike2_analyze_template.py` — Spike 2 re-score with DINOv2 template matching (style-invariant), the same metric as our composite's char-acc...
- `spike2_seeds.py` — Spike 2 (part 1): render K fonts x N seeds with OUR structured-5000 LoRA so we can measure cross-seed per-cell...
- `spike3_inspect.py` — Inspect how FLUX.2-klein-9b-kv-fp8 is packaged so we load it correctly (pre-quantized fp8 -- do NOT re-quantiz...
- `spike3_nooffload.py` — Spike 3: disambiguate the KV slowdown -- offload-bound vs intrinsic per-step.
- `spike4_promptcache.py` — Spike 4: prompt-embed caching to break the ~27s/step wall on distilled-9B.
- `spike5_quantcheck.py` — Spike 5: confirm WHY distilled-9B runs at 27s/step (vs base 8s/step).
- `spike_batch.py` — Spike: batched best-of-N on the INT4+V3 (Route B) path.
- `spike_bestofn.py` — Spike: best-of-N quality curve at 8 steps (QUALITY config) — does N>4 climb?
- `spike_cache.py` — Spike: FBCache step-caching on the INT4+V3 (Route B) path — benefit curve.
- `spike_promptcache_int4.py` — Spike: prompt-embed caching on the INT4+V3 (Route B) path.
- `spike_repair_ssweep.py` — Is the SDEdit-repair negative result an s-tuning artifact? Sweep s on one font.
- `spike_route_b.py` — Route B spike: can we inject a LoRA into a FLUX.2 Nunchaku SVDQW4A4Linear by APPENDING columns to proj_down/pr...
- `spike_route_b2.py` — Route B spike #2 — pin down WHY column-append failed.
- `spike_sdedit.py` — De-risk spike for latent-inpaint repair: SDEdit ROUND-TRIP on the INT4+V3 pipe.
- `spike_select_confirm.py` — Confirm consensus_best_of_n vs best_of_n on the REAL config: INT4+V3, 8 seeds, 8 steps.
- `spike_selector_variants.py` — Cheap selector tuning on SAVED 8-seed atlases (no generation).
- `spike_variable_instances.py` — Do variable-font named instances carry STRUCTURAL diversity, or cosmetic?
