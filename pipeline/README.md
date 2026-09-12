# pipeline/

**Dataset construction, rendering, and run orchestration.**

Building atlases/holdouts, rendering checkpoints, caching, experiment runners.

Run from the repo root, either way:

```bash
python pipeline/<script>.py --help
python -m pipeline.<script> --help
```

Scripts import repo-root modules (`atlas_constants`, `eval_checkpoint`, ...); a two-line
`sys.path` bootstrap at the top of each makes direct-path invocation work too.

## Contents (16)

- `backfill_dataset_registry.py` — Backfill experiments/_dataset_registry.json from existing manifests.
- `build_comparison.py` — Build model_comparison.html with all font test results embedded as base64 WOFF2.
- `build_expansion.py` — Build dataset_v3 = dataset_v2 + the expansion set, without re-rendering.
- `build_rg_holdout.py` — Build eval_holdout_rg: identical to eval_holdout except the reference images are re-rendered with REF_CHARS='R...
- `cache_template.py` — Cache the font-independent glyph-template latent (atlas resolution, T=20 grid) and add template_seq_len/templa...
- `continuous_train.py` — Continuous training with pause/render/resume per checkpoint.
- `experiment_runner.py` — Experiment runner — wraps training with proper organization and immutability.
- `fetch_base_model.py` — Download a FLUX.2-klein base model into the HF cache, diffusers layout only.
- `fetch_fonts.py` — fetch_fonts.py — Font pool builder with multiple source adapters.
- `gen_v3_seeds.py` — Generate V3 best-of-N seed atlases on distilled klein-9B for the hard fonts.
- `list_flux2_models.py` — Enumerate all black-forest-labs FLUX.2 / klein models with size + gating + local-cache state, so we can pick t...
- `merge_v3.py` — Step 1 of the offline Nunchaku path: merge Ref2Font V3 into distilled klein-9B's transformer (bf16) and save i...
- `render_checkpoint.py` — Render a sample atlas from a LoRA checkpoint.
- `run_multiref.py` — Render multi-reference variants on the hard fonts.
- `run_ref_ablation.py` — Render the hard fonts under three reference variants.
- `train_font_model.py` — QLoRA fine-tune StarCoder2-3B on VecGlypher Google Fonts dataset.
