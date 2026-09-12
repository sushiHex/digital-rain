# ML Experiment Workflow

## Core principles

1. **Nothing is ever auto-deleted.** Disk is cheap. Experiments are expensive.
2. **Every run is immutable.** Once started, the manifest cannot be modified.
3. **Datasets are snapshotted at run start.** If the dataset changes later, old runs still have their original snapshot.
4. **All runs go in `experiments/`.** Never in `training_output/`, never overwriting. (`experiments/` is a gitignored *output* directory — not to be confused with the `studies/` package, which holds research probes.)
5. **Naming includes timestamps.** No collisions, no accidental overwrites.

## Standard workflow

### 1. Build dataset
```bash
python build_dataset.py --font-dir google-fonts --output-dir dataset_v2
python cache_latents.py --dataset-dir dataset_v2 --ref-resolution 512
```

### 2. Launch experiment via runner (NOT raw train_lora.py)
```bash
python pipeline/experiment_runner.py --name Rg_full --dataset-dir dataset_v2 --steps 3500
```

This creates `experiments/20260406-153000_Rg_full/` with:
- `manifest.json` (locked at start, contains git commit + dataset hash)
- `dataset_snapshot.json` (every font file used)
- `checkpoints/` (training output, never auto-pruned)
- `training.log` (full console output)
- `metrics.csv` (machine-readable per-step data)

### 3. Resume a crashed run
```bash
python pipeline/experiment_runner.py --resume experiments/20260406-153000_Rg_full
```

The runner finds the latest checkpoint in `checkpoints/` and continues from there.

### 4. Generate validation samples
```bash
python pipeline/render_checkpoint.py experiments/20260406-153000_Rg_full/checkpoints/checkpoint-500 \
    --reference-font C:/Windows/Fonts/times.ttf \
    --out experiments/20260406-153000_Rg_full/samples/step_00500_times.png
```

### 5. Compare two experiments

Two different questions, two different tools — run both.

**Is the comparison fair?** `compare_experiments.py` checks *provenance*:

```bash
python analysis/compare_experiments.py \
    experiments/20260406-103000_Rg_baseline \
    experiments/20260406-150000_Kg_test
```

This reports:
- Whether datasets are identical
- Whether hyperparameters are identical
- Common checkpoints available for visual comparison
- Verdict: CLEAN / PARTIAL / DIRTY

**Is B better on more fonts than A?** `compare_runs.py` runs a paired Wilcoxon on per-font means:

```bash
python analysis/compare_runs.py \
    eval_runs/<run_a>/per_cell.json \
    eval_runs/<run_b>/per_cell.json --label-a a --label-b b
```

Gate: **p<0.05 AND r≥0.3**. Do not read a win off aggregate means alone — and do not use cell bootstrap, whose effective n is the fonts, not the 4,700 cells. (Effective n is ~46, not 50: `analysis/check_holdout_integrity.py` found two byte-identical GT triples.)

> **That heading is the question the tool answers, and it is narrower than "is the difference real?"** Run unmodified on two runs differing **only in `--seed`**, `compare_runs.py` returns char_acc `p=0.0000 r=0.731 SIG` and dinov2 `p=0.0000 r=0.742 SIG`. The tool is not broken — it pairs by font, so any component shifting every font together is invisible to it, and here that common shift is 43–52% of the difference.
>
> **Never report a SIG verdict between two TRAINING runs as an established difference without replicates.** Its verdict is interpretable when both arms share a training run (i.e. for inference-seed comparisons), or when the effect is large against run-level noise.

**Is it real?** That needs `analysis/training_variance.py` and `analysis/claim_ledger.py`: divide the effect by **that metric's own** run-to-run SD. Measured over three identical-config runs — char_acc SD 0.0618, dinov2 0.0228, racc 0.0080, composite 0.0035, lpips 0.0027. Training noise is metric-dependent by ~20×, and the two metrics chased hardest here are the least stable. Budget ~3 runs per arm, or require an effect above 2× that metric's SD.

## Anti-patterns (things that broke us before)

| Mistake | Consequence | Prevention |
|---|---|---|
| Modifying dataset after training started | Lost original conditions for old checkpoints | Snapshot dataset in experiment manifest |
| Auto-deleting old checkpoints | Lost the only Rg checkpoints | Never auto-delete; manual cleanup only |
| Reusing output directory across runs | Overwrote previous results | Timestamp every experiment dir |
| Loading optimizer state to wrong device | Crashed training mid-run | `weights_only=True` + selective device migration |
| Mutating optimizer state during save | Crashed next training step | Deep-copy state before saving |
| Background processes with `&` | Process killed unexpectedly | Use `experiment_runner.py` which manages the process properly |
| No git commit recorded | Couldn't reproduce code state | Manifest captures `git rev-parse HEAD` |
| Evaluating a checkpoint with a prompt it wasn't trained on | Silent accuracy loss — IDENTITY 0.9936 → 0.9780, invisible to char_acc (p=0.948) | `conditioning_config.py` derives conditioning from the checkpoint; `eval_checkpoint --strict-conditioning` refuses a mismatch |
| Judging a run by aggregate means | Differences inside training noise read as wins | Paired Wilcoxon via `analysis/compare_runs.py`, gate p<0.05 ∧ r≥0.3 |
| Reporting a `compare_runs.py` SIG verdict between two **training** runs as an established difference | The tool fires on runs differing only in `--seed`, at r=0.731 / r=0.742 — against a flagship result of r=0.768 | Replicate runs, and divide by that metric's own SD (`analysis/claim_ledger.py`) |
| Dividing an effect by a **different** metric's SD | Understated resolvability 2.7× on a published claim; logged three times in this repo | `analysis/claim_ledger.py` scores every claim on every metric against its own SD |
| Comparing two runs on `char_acc` or `dinov2` alone | They are the noisiest metrics here (SD 0.0618 / 0.0228) and resolve nothing; a zero-GPU retrieval baseline beats every model on both | Headline on composite (SD 0.0035) and LPIPS (0.0027) |
| Judging a global stroke-weight shift by eye or by loss | Two runs shipped at −32.5% and +19.7% ink with healthy loss and a passing conditioning guard | `python analysis/measure_ink.py` — and note ink is the **bright**-pixel fraction on these light-on-dark atlases |

## Manifest schema

```json
{
  "name": "Rg_full",
  "timestamp": "20260406-153000",
  "git_commit": "abc1234567...",
  "dataset_dir": "dataset_v2",
  "dataset_hash": "1a2b3c4d5e6f7890",
  "steps": 3500,
  "hyperparameters": {
    "rank": 16,
    "lr": 0.0001,
    "warmup_steps": 100,
    "seed": 42,
    "reference_chars": "Rg"
  },
  "started_at": "2026-04-06 15:30:00",
  "finished_at": "2026-04-07 08:30:00",
  "status": "completed"
}
```

## Comparing experiments scientifically

For valid A/B comparisons:
1. **Same git commit** (or at minimum, the variable being tested is the only difference)
2. **Same dataset hash** (or document the diff explicitly)
3. **Same hyperparameters except the variable being tested**
4. **Six inference seeds per checkpoint**, not one. Superseded 2026-08-07: the
   seed MAIN effect is ~90% of a run's holdout-mean variance and does NOT
   average out across fonts, so a single-seed A/B carries SE ≈ 0.037 against a
   0.0457 observed gap. Six takes it to ≈3.1 SE. An *architecture* claim needs
   independent TRAINING seeds too — inference seeds only compare checkpoints.
   See `research/2026-08-07-single-seed-comparisons-cannot-resolve-the-4b-9b-gap.md`.
5. **Same evaluation prompts and inference seed** — and each model must be
   evaluated on the prompt *it* was trained with, not a shared one. Using one
   prompt for both is not "controlling the variable"; it is handicapping
   whichever model didn't train on it.

6. **Replicate TRAINING runs, or accept that the comparison is unresolved.**
   Added 2026-08-13, and it supersedes the framing of everything above it.
   Three runs identical except `--seed` gave char_acc holdout means of
   0.4914 / 0.6070 / 0.5869. Two of the three pairs pass the significance gate.
   No single-arm-per-configuration comparison in this repository resolved
   anything on char_acc or DINOv2, and the effects that *do* resolve, on the
   stable metrics, are all regressions.
   See `research/2026-08-13-training-run-variance-measured-at-last.md`.

`analysis/compare_experiments.py` checks 1-3 automatically and outputs
CLEAN/PARTIAL/DIRTY. `analysis/compare_runs.py` then tests whether B beats A on
more fonts. Neither answers whether the effect exceeds run-to-run noise — that
is `analysis/training_variance.py` and `analysis/claim_ledger.py`.

**Seed variance is large enough to matter.** Same-model best-of-4 lifts
char_acc by +0.148, and 88.6% of the cells that "recovered" were already
identity-correct at seed 0 — so a single-seed A/B is measuring a style
lottery as much as a model difference. See
`research/2026-07-18-wrong-letters-are-a-metric-artifact.md`.
