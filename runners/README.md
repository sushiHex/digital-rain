# runners/

**The detached-run shell runners and their watchdogs.** Moved off the repo
root on 2026-09-11; they were the 43 files that made the root unreadable.

Every runner self-locates with `cd "$(dirname "$0")/.."` and then works from
the **repo root**, so every relative path inside them — `dataset_v2`,
`eval_runs/…`, the `*_DONE` / `*_FAIL` marker files, the `*.log` files — is
exactly what it was when they lived at the root. Launch them as
`./runners/<name>.sh` from anywhere. `tests/test_runners_self_locate.py` pins
the line, pins that no `.sh` has crept back onto the root, and pins that this
index lists every runner.

The pattern they share is described in `CLAUDE.md` under *Long runs*: detach
via PowerShell `Start-Process`, gate on free VRAM before starting, write the
exit code into a marker file, and let a `watchdog_*.sh` relaunch the outer
loop if a harness task-kill takes it down. Parameters come from env vars set
in the same PowerShell call (`$env:RANK='64'; Start-Process bash
-ArgumentList '-lc','./runners/run_glyph_4b_r32.sh'`).

## Model track — training and evaluation (24)

- `run_glyph_4b_r32.sh` — the parameterised klein-base-4B training runner: `RANK OUT EVAL_OUT LOG DATASET STEPS MARKER EXTRA_TRAIN_ARGS NEED_MB`. Every 4B training run here is this script with different env vars.
- `run_glyph_4b_clean_corpus.sh` — retrain on the licence-clean corpus (838 of 925 fonts); sets the env and `exec`s `run_glyph_4b_r32.sh`.
- `run_training_variance.sh` — three runs identical but for `--seed`, the measurement that set the noise floor for every claim.
- `run_glyph_4b_distilled.sh` — train the LoRA on the distilled 4B rather than transferring a base-trained adapter.
- `run_distilled_4b.sh` — lever 1: the distilled 4-step inference path on a base-trained adapter.
- `run_derisk_4b.sh` — the 400-step de-risk gate: does channel-concat conditioning transfer to the 4B at all?
- `run_rescore_9b_derisk.sh` — re-score the 9B de-risk checkpoint with the prompt it was trained on, for a same-protocol baseline.
- `run_multiseed_4b_vs_9b.sh` — matched six-inference-seed comparison on the 50-font holdout.
- `run_rescore_multiseed.sh` — re-score those twelve candidate sets with `eval_checkpoint`, no generation, so R-ACC, IDENTITY and the README composite get six seeds too (issue #12).
- `run_throughput_probe.sh` — levers 2 and 3: training throughput left on the table on the 4B.
- `resume_glyph_r32.sh` — auto-resume wrapper for the 9B rank-32 run on a contended GPU.
- `run_eval_glyph_r32.sh` — the gated, restartable 50-font eval of checkpoint-5000.
- `run_baseline_identity.sh` — re-score the existing baseline atlases with `--identity`.
- `run_prompt_test.sh` — the prompt-mismatch test: generate with the string the model was actually trained on.
- `run_rg_test.sh` — the Rg-reference test (reference identity does not matter, p=0.625).
- `run_nonoracle_eval.sh` — the oracle-reference gap: screenshot, upload and phone-photo references against identical ground truth.
- `run_glyph_clf.sh` — train the font-invariant glyph classifier, the identity instrument.
- `run_ocr_measure.sh` — the focused OCR symbol measurement.
- `run_caption_probe.sh` — April caption A/B probe; hardcodes three Windows system fonts as references and predates the env-var convention.
- `run_disambig_probes.sh` — 10-font zero-shot probes of the mild and strong disambiguated templates.
- `run_disambig50_mild.sh` — the 50-font extension of the mild probe.
- `run_hybrid_v2.sh` — the full 50-font hybrid-v2 replay (GOT-OCR2 swap).
- `run_per_cell_medoid.sh` — per-cell medoid selection in DINOv2 space, queued behind the non-oracle eval.
- `score_pool.sh` — score the structural distinctiveness of every OFL family not already in the corpus, for the expansion set.

## Best-of-N and selection — closed (2)

- `bestofn_4b.sh` — does the 4B have the 9B's sampling headroom, and can a no-GT selector harvest it? (It has; nothing harvests it.)
- `holdout_bestofn.sh` — is the 0.6883 char_acc ceiling architectural or variance-bound?

## GT-guided preference optimisation — closed track (9)

`research/2026-06-03-generator-track-decision.md`. Kept as the reproduction path for a recorded negative result.

- `dpo_smoke.sh` — end-to-end GPU smoke of the DPO pipeline on 3 fonts.
- `pilot_prep.sh` — cross-model candidate generation, scoring and selection on 80 training fonts.
- `widen_candidates.sh` — widen the pilot pool from 3 to 5 renders per cell.
- `stage_a.sh` — Stage A: SFT self-distillation on cross-model winner atlases.
- `stage_a_eval.sh` — complete the Stage A holdout eval past the RAM guard.
- `stage_a_lite.sh` — the cheaper re-test of Stage A on the same cached data.
- `stage_a_lite_eval.sh` — its holdout eval.
- `stage_a_v2.sh` — Stage A on the widened pool.
- `stage_a_v2_eval.sh` — its holdout eval.

## Watchdogs (8)

Each polls for its runner's terminal marker and relaunches the runner's outer loop if the process is gone. **A watchdog's VRAM threshold must match its runner's gate** — a mismatch twice made a legitimately parked runner read as stalled.

**Fixed 2026-09-12 (was broken 2026-09-11): they counted the runner with `wmic`, which this Windows build no longer ships**, so the count read 0 and a watchdog would have relaunched a runner that was still running, every poll. They now count with `python misc/count_running.py "<pattern>"` — psutil, cross-platform, tested against a live dummy. It prints `-1` rather than `0` when it cannot read the process table, because every watchdog's `[ "${outer:-0}" -eq 0 ]` treats any non-zero count as "alive": a count that fails must not relaunch.

The same line hid a second defect pointing the other way. Five of these eight are named after the runner they watch, so `watchdog_stage_a_eval.sh` matched its own `wmic` line and its `outer` could never reach 0 — a genuinely dead runner would never have been relaunched. The replacement excludes the asking process and its whole ancestor chain by pid.

- `watchdog_derisk_4b.sh` — for `run_derisk_4b.sh`.
- `watchdog_glyph_4b.sh` — for `run_glyph_4b_r32.sh`.
- `watchdog_glyph_r32.sh` — for the 9B rank-32 run.
- `watchdog_holdout_bestofn.sh` — for `holdout_bestofn.sh`.
- `watchdog_stage_a_eval.sh` — for `stage_a_eval.sh`.
- `watchdog_stage_a_lite_eval.sh` — for `stage_a_lite_eval.sh`.
- `watchdog_stage_a_v2_eval.sh` — for `stage_a_v2_eval.sh`.
- `watchdog_widen_candidates.sh` — for `widen_candidates.sh`.

## Other (1)

- `oracle_run.sh` — a detached Oracle research run; prompts come from `ORACLE_PROMPTS`.
