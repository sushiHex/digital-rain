# studies/

**Research probes and one-off experiment drivers.**

Hybrid selection, OCR measurement, repair, self-consistency. Mostly superseded -- kept as the record behind research/.

Run from the repo root, either way:

```bash
python studies/<script>.py --help
python -m studies.<script> --help
```

Scripts import repo-root modules (`atlas_constants`, `eval_checkpoint`, ...); a two-line
`sys.path` bootstrap at the top of each makes direct-path invocation work too.

## Contents (16)

- `eval_build_holdout.py` — Build a held-out evaluation set for font LoRA quality measurement.
- `eval_cleanup.py` — Measure cleanup's char-acc lift on the GT-bearing holdout, two ways:
- `eval_cleanup_quality.py` — QUALITY-mode cleanup eval: measure best-of-N's lift THROUGH the pipeline.
- `eval_route_b.py` — Route B quality eval: INT4 base vs INT4 + V3 (runtime LoRA via forward-hooks), on the hard fonts, scored with...
- `eval_route_b_holdout.py` — Broader Route B quality eval: INT4 + V3 on N holdout fonts, single-seed vs best-of-N (dual metric).
- `hybrid_replay.py` — hybrid_replay.py -- realizable (no-GT) OCR-swap hybrid replay + accounting.
- `hybrid_v2_ocr.py` — Drop-in replacement candidates for cleanup/models.py:build_trocr_ocr_fn.
- `hybrid_v2_replay.py` — hybrid_v2_replay.py -- COMBINED-OCR (TrOCR + GOT-OCR2) no-GT swap hybrid replay.
- `measure_ocr_symbols.py` — Focused de-risk: does GOT-OCR2 read SYMBOLS/confusables on single glyph cells better than TrOCR? Decodes only...
- `probe_glm_image.py` — Zero-shot probe: does GLM-Image capture ABSTRACT typeface style?
- `repair_sdedit.py` — Style-preserving latent-inpaint repair for systematic-failure cells (Route B).
- `score_self_consistency.py` — Can a NO-GT heuristic capture the +0.1483 same-model best-of-4 headroom found on the holdout? Tests self-consi...
- `score_v3_seeds_ref.py` — Score the existing bf16+V3 reference atlases (experiments/v3_seeds/*_seed42.png) with the SAME metric as eval_...
- `select_reference_anchored.py` — Reference-anchored no-GT selection: use the glyphs the USER supplies.
- `validate_route_b_rotary.py` — Validate the unfused-qkv rotary plumbing: same seed, fused vs unfused, no LoRA. Correct rotary => images near-...
- `validate_select.py` — Cheap validation of consensus_best_of_n vs best_of_n on the SAVED v3_seeds atlases (3 fonts x 4 seeds) — no ge...
