# viz/

Figure generators. Run from the repo root; every script writes a PNG to
`viz/out/`. Shared paths and the font table live in `_common.py`, not in the
individual scripts.

This README is hand-written rather than generated (see
`misc/sync_package_readmes.py`, which skips it) because what matters about a
figure is the claim it carries, not its filename.

## The figures in the README and `docs/what-happened.md`

| script | what it shows |
|---|---|
| `stylized_showcase.py` | **The hero.** Ten stylized holdout typefaces, ground truth beside generated, "Hamburg" composed from the atlas cells themselves. Carries no metric on purpose: `char_acc` is the one number the README then spends a section discrediting, so it has no business under the first image anyone sees. Writes `viz/stylized_showcase.png`, not `viz/out/`. |
| `variance_vs_effects.py` | Three training runs identical but for `--seed`, over one char_acc axis; below them, every claim ÷ that metric's own run-to-run SD, columns ordered by that SD. The ringed cells clear 2×SE — all six are regressions. |
| `retrieval_vs_model.py` | Three word-strips per holdout font: ground truth, model, and the nearest *training* font handed back unchanged. Retrieval outscores the model, and the figure shows why — the retrieved face is genuinely similar, not nonsense. |
| `lr_horizon_bug.py` | The cosine LR schedule that never annealed, parsed out of two real training logs. The loss panel below is the point: the buggy and fixed runs are indistinguishable there. |
| `synthetic_reference_probe.py` | The reference the model was given beside the font it produced, for three reference arms. Shows the model splitting an atlas along K-like vs g-like letters when the two reference glyphs disagree — a defect identity scored ABOVE the control. Needs `analysis/synthetic_reference_probe.py` run first. |
| `finished_font_specimens.py` | The same word set in the finished OTFs — source, ground-truth-traced, model, retrieval. The GT row carries zero model error, so its gap from source is the pipeline's. Needs `analysis/score_finished_font.py` run first, which builds and caches the fonts. |
| `adherence_transforms.py` | What the adherence measure sees. One real face transformed four ways -- solid / stencil / inline / outline, all from the SAME source so only the treatment differs -- with the features that separate them, above the real held-out typefaces and the verdict on each. Shows why `parts` alone confused a break with a stripe. |
| `reference_to_atlas.py` | Each candidate reference above the atlas it produced, for the two widest-spread descriptions. The strip shows a-m-b-e-r and NEVER K or g, which the model is conditioned to copy -- so every letter drawn is one the user never chose. Green frames matched their own reference. Needs `analysis/reference_to_atlas_transfer.py` run first. |
| `candidate_options.py` | Four candidates for one description, rows spanning the measured spread range. Row 2 is the finding: four seeds of a stencil prompt, not one with a break. Needs `analysis/within_prompt_diversity.py` run first. |
| `arm_comparison.py` | Two generators, one description, four seeds each. The bar is a yes/no: does ANY candidate show what the words asked for? Defaults to the stencil prompt, where eight seeds across two independent models all come back solid. |
| `description_to_font.py` | **Words in, typeface out** — one row per description: the text, the `Kg` it produced, and a word set in the finished font. `K` and `g` are the only glyphs the model was given and neither appears in "Hamburg", so every letterform shown is invented. Recorded misses are marked, not dropped. Replaces the two generator-less halves below. |
| `generation_progression.py` | **The denoising trajectory**, one frame per step of a single run, as a GIF. Decodes the intermediate latents by copying the pipeline's own final block, and VALIDATES that copy against the image the pipeline returned before writing anything. Also caches the latents, because the decode is the fiddly half and a bug there should not cost another generation. |
| `synthesised_reference.py` | **Hand it a stencil and it propagates one.** Three arms -- plain, inline (positive control), stencil -- each a constructed reference beside the letters the model was NOT given. The word is "Amber" precisely because it contains no `K` and no `g`, the two glyphs the model copies. Needs `analysis/synthesised_reference_probe.py` run first. |
| `relational_widths.py` | **Where the CV fall came from.** Per-cell ink width, plain arm against monospace arm, one panel per registered pair. Under `Kg` every cell sits on the diagonal; under `Mi` the widest cells fall far below it and the narrowest rise above it, the spread of widths falling 39% against a 14% fall in the mean -- a uniform condensing would shrink both alike -- with the whole cloud a little left of where it started, the condensing that rode along. Needs both probe runs on disk. |
| `relational_transfer.py` | **A local treatment propagates; a relational one did not.** The same three-arm shape as `synthesised_reference.py` with monospace in place of inline: the stencil control reproduces its signature (parts 0.74 → 2.15) while the monospace arm returns the plain atlas (CV 0.402 → 0.403). The word is "minimal10" -- no `K`, no `g`, and ink widths running 14 px to 70 px, which is exactly what a monospace treatment would have to close. The boxed note is the pre-registered weakness rather than a hedge: the reference pair is fixed at `Kg`, whose widths already nearly agree. Needs `analysis/relational_transfer_probe.py` run first. |

## Comparison specimens

| script | what it shows |
|---|---|
| `showcase_grids.py` | Full 94-glyph atlas grids, GT beside generated, one PNG per font. |
| `compare_9b_4b.py` | Side by side: the 9B glyph model against the Apache-2.0 4B, both against GT. |
| `compare_methods.py` | Compact 4-row specimen (GT / 9B / 4B / 4B-weighted), sized to base64-inline into a report page. |

## Committed outputs

`*.png` is gitignored, so the figures used by the documentation are force-added
on purpose. List them with `git ls-files viz/out/`; add another with `git add -f`.

Two committed PNGs have no generator here; each was produced during an
investigation and is kept as its evidence:

- `ref_chars_mismatch_evidence.png` — the Rg/Kg train-eval mismatch, documented
  in `research/2026-07-28-reference-char-mismatch.md`.
- `out/glm_probe_wonky.png` — output from `studies/probe_glm_image.py`, behind
  the finding that GLM-Image edits rather than restyles.
- `out/candidate_refs_klein_base.png` — the twelve `Kg` reference pairs, and
  `out/loop_closes_words.png` — the twelve finished typefaces they produced.
  **The gap these two represented is CLOSED**: `description_to_font.py` draws
  both halves together from the committed artifacts, so the claim now rebuilds
  from a clean clone. The originals are kept as the dated record.

`stylized_showcase.png` opens both the README and Act 1 of the narrative. It is
the one committed figure that lives at `viz/` rather than `viz/out/`, because
that is where both documents link it; `stylized_showcase.py` writes it there.
The version committed before 2026-09-11 carried a `char_acc` label under each
font name and came from a since-removed generator (`showcase_words.py`, in the
history); its provenance was verified by regenerating it and diffing
pixel-for-pixel, 0 of 3,136,616 pixels different, against
`eval_runs/glyph_r32_disambig50_mild/`. `stylized_showcase.py` reads the same
run and drops the labels: they argued against the image with the metric the
README goes on to discredit.
