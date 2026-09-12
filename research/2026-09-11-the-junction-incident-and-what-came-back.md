# The junction incident, and what came back (2026-09-11)

**What happened.** To run a GPU probe on a parked branch in parallel with
other work, the gitignored data directories were linked into a `git worktree`
with NTFS junctions. When the branch merged, `git worktree remove --force`
recursed *through* the junctions and emptied their targets in the real
repository: `dataset_v2/`, `font_pool/`, `eval_holdout/`, `google-fonts/`,
`training_glyph_4b_r32_5000/checkpoint-5000/` and
`eval_runs/_relational_refs/`. None of it is in git, by design.

The first check afterwards used a glob tool that honours `.gitignore`, came
back empty for a *different* reason, and nearly produced an "intact" report.
Only a literal directory listing showed the truth. The rule that follows is in
`CLAUDE.md` ("Worktrees and the data directories").

**What came back, and from where.** Everything, with two small exceptions
listed below. No regeneration from scratch was needed: each directory had a
byte-identical sibling somewhere that a derived artefact had left behind.

| directory | restored from | how verified |
|---|---|---|
| `dataset_v2/` (925 atlases, references, latents, templates) | hard links out of `dataset_v3/`, which `pipeline/build_expansion.py` had built *from* v2 by `os.link` — the bytes are v2's own | 925/925 stems present in all four subdirectories; `cache_meta.json` rewritten to `num_pairs: 925`; `manifest.txt` regenerated in `build_dataset`'s format |
| `checkpoint-5000/` | copy of `final/` in the same run | the undeleted copy had 200/201 adapter tensors identical to `final/`; its `x_embedder` tensor and `training_state.pt` were corrupt, so `final/` (same step) is the faithful source |
| `eval_holdout/` atlases, fonts, `manifest.json`, `gt_ocr_cache.json` | `eval_holdout_photo/`, a `shutil.copytree` of the holdout made by `analysis/build_degraded_holdout.py` (only its `references/` differ) | atlases byte-identical across all four surviving copies; `analysis/check_holdout_integrity.py` reproduces the documented structure: 46 unique atlases, 45 unique references, same groups |
| `eval_holdout/references/` (Kg) | re-rendered from the holdout's own TTFs with `build_dataset.render_reference` | pixel-identical, 50/50, to the verbatim copies `analysis/build_synthetic_references.py` had kept in `eval_runs/_synthetic_refs/oracle/` |
| `google-fonts/` | blob-less re-clone at `85f52fd19ff9649d8d173a9401c289e0f59befab` | all 50 holdout fonts and 2,061 of the 2,972 files in `font_pool_selected` byte-identical to the clone; none differ |
| `font_pool/` | the 5,270 undeleted files that still parse, plus the 925 corpus fonts placed under their stems from `font_pool_selected` (804), `extra-fonts` (69) and `C:\Windows\Fonts` (51) | every corpus font parses; `analysis/audit_corpus_provenance.py --check` reproduces the committed record (OFL 805, proprietary 49, unresolved 45, Apache 23, UFL 3) |
| `font_pool/source_manifest.json` | rebuilt: corpus entries carry the licence from `research/corpus_provenance.json`, the undeleted files carry their own name-ID-13 licence | the 121 corpus fonts that were never manifested are left out on purpose, so `find_fonts` refuses them exactly as before |
| `eval_runs/_relational_refs/` | re-run of `analysis/relational_transfer_probe.py` | its JSON is identical to the tracked `research/relational_transfer_probe.json`, all 27 values |

**What did not come back.**

- The font file `unispace_bd` (one of the 45 unresolved-licence corpus fonts).
  Its atlas, reference and latents survive in `dataset_v2`, so training is
  unaffected; only a rebuild of the corpus from fonts would miss it.
- 148 of the 5,418 undeleted pool files no longer parse and were left out
  (listed in `font_pool/RESTORE_NOTE.txt`). None is a corpus font. The
  original manifest had 6,141 entries; the rebuilt one has 6,074.
- The undeleted `checkpoint-5000` adapter itself: replaced by `final/`, which
  is the same training step.

**Undelete notes, for next time.** Windows File Recovery 0.1 takes
`/ntfs /n Users\<path>\ /a /o:b /e` — no leading backslash on the filter;
`/regular` is the old mode, ignores the filter, runs signature scanning and
blocks on an overwrite prompt. Write nothing to the affected volume until it
finishes.

**Follow-up.** The private repository now carries a `backup/` directory for
the data that cannot be re-downloaded or re-derived exactly (issue #22); it
is excluded from the public export. This note is CC BY 4.0 like the other
notes; it names no home path.
