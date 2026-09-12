# analysis/

**Post-hoc analysis of eval runs and checkpoints.**

Read existing artifacts (per_cell.json, atlases, adapters) and report. No GPU training.

Run from the repo root, either way:

```bash
python analysis/<script>.py --help
python -m analysis.<script> --help
```

Scripts import repo-root modules (`atlas_constants`, `eval_checkpoint`, ...); a two-line
`sys.path` bootstrap at the top of each makes direct-path invocation work too.

## Contents (59)

- `advance_survives_atlas.py` — Does MONOSPACE survive the atlas, when the atlas throws advance width away?
- `analyze_caption_probe.py` — Score caption A/B probe outputs and decide whether captions move the model's output in a style-aware way.
- `analyze_holdout_bestofn.py` — Best-of-N ceiling analysis: is a model's single-seed char_acc architectural, or partly variance-bound and reco...
- `analyze_multiref.py` — Score multi-reference outputs and decide whether passing 2+ refs helps.
- `analyze_per_cell.py` — Per-cell failure heatmap analysis.
- `analyze_ref_ablation.py` — Score the reference-ablation outputs and report whether oracle references beat Times references on hard fonts.
- `attribute_label_supply.py` — What style attributes can this corpus label for FREE, and at what n?
- `attribute_separation.py` — Does the ATLAS FORMAT carry each labelled style attribute?
- `attribute_transfer.py` — Does a measure trained on REAL fonts read a GENERATED atlas the way the eye did?
- `audit_corpus_provenance.py` — Emit a TRACKED, auditable licence manifest for the training corpus.
- `audit_dataset.py` — Standalone dataset auditor.
- `build_comparison_page.py` — Assemble the comparison artifact, injecting real numbers and the specimen.
- `build_degraded_holdout.py` — Build holdout variants whose REFERENCES look like something a user uploaded.
- `build_synthetic_references.py` — Build reference images that did NOT come from one real font.
- `calibrate_instruments.py` — Score the reference gate and the two-glyph adherence measure against HUMAN labels.
- `calibration_sheet.py` — Build the sheet and CSV a human uses to label 48 candidate references usable or not.
- `check_env.py` — Probe the env for Nunchaku feasibility: Python / torch / CUDA / GPU arch / whether nunchaku is already importa...
- `check_holdout_integrity.py` — Is the 50-font holdout actually 50 independent observations? No.
- `check_identity_vs_fidelity_gap.py` — Is the +0.1483 same-model best-of-4 char_acc gap mostly about IDENTITY (reads as the right letter -- a no-GT-n...
- `claim_ledger.py` — Every headline claim, on EVERY metric, against that metric's training noise.
- `compare_experiments.py` — Compare two experiments side by side.
- `compare_runs.py` — Paired Wilcoxon signed-rank comparison between two eval runs.
- `compare_v3_vs_ours.py` — Build a side-by-side comparison page: our LoRA vs Ref2Font V3 vs GT.
- `corpus_licence_exclusions.py` — Decide, per training font, whether its licence permits this project's use.
- `dump_block_tree.py` — Dump SVDQW4A4Linear paths in block 0 (double) and single block 0, to fix the key map.
- `fit_cap_height.py` — Fit the cap height the font builder has to assume.
- `fit_sidebearing_prior.py` — Fit a per-character sidebearing prior from real fonts.
- `identify_unlicensed_corpus_fonts.py` — Identify the corpus fonts whose licence could not be read from the font.
- `inspect_v3_converted.py` — Run diffusers' kohya->diffusers FLUX converter on V3 and inspect how it decomposes the single-block linear1/li...
- `inspect_v3_full.py` — Full V3 target inventory: every distinct module suffix (block-index stripped), so the Route B key map is exact...
- `inspect_v3_lora.py` — Inspect the Ref2Font V3 LoRA key format to plan a transformer-only merge.
- `inspect_v3_targets.py` — Categorize V3 LoRA target modules to scope Route B (which linears, fused-QKV?).
- `measure_ink.py` — Mean ink coverage of a run's generated atlases against holdout ground truth.
- `multiseed_compare.py` — Pre-registered cross-model analysis for the matched multi-seed run.
- `multiseed_rescore.py` — The six-seed 4B-vs-9B comparison on the metrics the multiseed run never scored.
- `per_cell_classifier_select.py` — Per-cell best-of-N selection by GLYPH-CLASSIFIER CONFIDENCE.
- `per_cell_medoid.py` — Per-cell medoid selection in DINOv2 space -- the untried best-of-N selector.
- `reference_gate.py` — Reject a reference whose two glyphs disagree, BEFORE spending a generation.
- `reference_stage_adherence.py` — Can TWO glyphs carry the adherence signal, or must the picker wait for an atlas?
- `resolve_pool_by_repo.py` — Resolve the last unknown-licence pool fonts from their SOURCE REPOSITORY.
- `resolve_pool_unknowns.py` — Resolve the font pool's `license: unknown` entries from embedded licences.
- `resource_recovered_fonts.py` — Replace recovered fonts with their canonical OFL copies, and record it.
- `retrieval_baseline.py` — The floor nobody measured: return a REAL font instead of generating one.
- `sanitize_for_publish.py` — Scan (and optionally fix) the tracked tree for things that must not go public.
- `score_finished_font.py` — Score the artefact the user receives: the traced OTF, not the atlas.
- `score_font_distinctiveness.py` — Score how structurally distinctive each TRAINING font is.
- `score_holdout_distinctiveness.py` — Score holdout fonts for structural distinctiveness, non-circularly.
- `score_pool_distinctiveness.py` — Score structural distinctiveness of fonts NOT in the training corpus.
- `seed_variance.py` — How much of a run's holdout score is the seed, and what does that cost?
- `select_expansion_set.py` — Select the corpus-expansion set: new OFL fonts + variable-font instances.
- `select_replacement_set.py` — Pick replacements for the 87 fonts the licence filter removed.
- `style_adherence.py` — Did the model produce the style that was ASKED FOR?
- `style_adherence_minimal_pairs.py` — Does CLIP read the DECISIVE clause, or just "typeface-ness"?
- `style_coherence.py` — A ground-truth-free measure of whether an atlas is ONE typeface.
- `synthesize_rare_attributes.py` — Can a measure tell a stencil BREAK from an inline STRIPE? Train it to.
- `synthetic_reference_probe.py` — Does the generator survive a reference that did not come from one real font?
- `terminal_shape.py` — Can a terminal-shape feature make serif-vs-sans readable?
- `training_variance.py` — Measure TRAINING-run variance, and calibrate the comparison gate against it.
- `verify_identity_definitions.py` — Recompute IDENTITY under each matching definition, from committed per-cell data.
