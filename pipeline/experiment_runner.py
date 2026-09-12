"""Experiment runner — wraps training with proper organization and immutability.

Every run gets a timestamped directory under experiments/ with:
  - Immutable manifest with git commit, dataset hash, hyperparameters
  - Frozen dataset snapshot (list of every font file)
  - Training log + metrics
  - Checkpoints (never auto-deleted)
  - Inference samples at each checkpoint
  - Final exported LoRA

Note: `experiments/` is the *output* directory (gitignored). It is unrelated
to the `studies/` package, which holds research probes.

Usage:
  python pipeline/experiment_runner.py --name Rg_v2 --dataset-dir dataset_v2 --steps 3500
  python pipeline/experiment_runner.py --name Kg_test --dataset-dir dataset_Kg --steps 300

Resume a crashed run:
  python pipeline/experiment_runner.py --resume experiments/20260406-143000_Rg_v2
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


def git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def dataset_hash(dataset_dir):
    """Compute a hash of (atlas filename, atlas filesize) tuples.

    LIMITATION: does NOT read file contents. A byte-level edit that preserves
    filename and size will not be detected. The hash exists to catch the
    common drift mode (files added, removed, or regenerated with different
    pixel content but different byte count) — not to defeat tampering.
    """
    h = hashlib.sha256()
    atlas_dir = Path(dataset_dir) / "atlases"
    if not atlas_dir.exists():
        return None
    files = sorted(atlas_dir.glob("*.png"))
    for f in files:
        h.update(f.name.encode())
        h.update(str(f.stat().st_size).encode())
    return h.hexdigest()[:16]


def _atomic_write_json(path: Path, data) -> None:
    """Write JSON to path atomically (tmp file + os.replace)."""
    import os
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, path)


def snapshot_dataset(dataset_dir):
    """List every font file in the dataset for full reproducibility."""
    dataset_dir = Path(dataset_dir)
    snapshot = {
        "dataset_dir": str(dataset_dir),
        "fonts": [],
    }
    atlas_dir = dataset_dir / "atlases"
    ref_dir = dataset_dir / "references"
    for atlas in sorted(atlas_dir.glob("*.png")):
        ref = ref_dir / atlas.name
        snapshot["fonts"].append({
            "stem": atlas.stem,
            "atlas_size": atlas.stat().st_size,
            "ref_size": ref.stat().st_size if ref.exists() else None,
        })
    snapshot["count"] = len(snapshot["fonts"])

    # Cache metadata if present
    cache_meta = dataset_dir / "cache" / "cache_meta.json"
    if cache_meta.exists():
        snapshot["cache_meta"] = json.loads(cache_meta.read_text())

    return snapshot


DATASET_REGISTRY = Path("experiments") / "_dataset_registry.json"


def _load_registry() -> dict:
    if not DATASET_REGISTRY.exists():
        return {}
    return json.loads(DATASET_REGISTRY.read_text(encoding="utf-8"))


def verify_dataset_unchanged(dataset_dir, current_hash, allow_mismatch=False):
    """Abort if dataset_dir's hash differs from the recorded canonical hash.

    Returns whether this is a first-time registration (True if no prior entry
    exists yet). Caller must call record_dataset after exp_dir creation.
    """
    if current_hash is None:
        return False
    prior = _load_registry().get(str(dataset_dir))
    if prior and prior["hash"] != current_hash:
        msg = (
            f"\nDATASET HASH MISMATCH for {dataset_dir}\n"
            f"  Previously seen hash: {prior['hash']} (from {prior['first_seen_in']})\n"
            f"  Current hash:         {current_hash}\n"
            f"  Contents have changed since the last training run that used this directory.\n"
            f"  Either:\n"
            f"    - Restore the original contents, OR\n"
            f"    - Rename to a versioned directory (e.g. {dataset_dir}_$(date +%Y%m%d)), OR\n"
            f"    - Pass --allow-dataset-mismatch to override (NOT recommended)\n"
        )
        if allow_mismatch:
            print("WARNING:" + msg)
        else:
            raise SystemExit("ABORT:" + msg)
    return prior is None


def record_dataset(dataset_dir, current_hash, exp_name) -> None:
    if current_hash is None:
        return
    DATASET_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    registry = _load_registry()
    key = str(dataset_dir)
    if key not in registry:
        registry[key] = {"hash": current_hash, "first_seen_in": exp_name}
        _atomic_write_json(DATASET_REGISTRY, registry)


def create_experiment(name, dataset_dir, steps, allow_dataset_mismatch=False, **kwargs):
    """Create a new experiment directory with frozen manifest."""
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    exp_name = f"{timestamp}_{name}"
    exp_dir = Path("experiments") / exp_name

    current_hash = dataset_hash(dataset_dir)
    verify_dataset_unchanged(dataset_dir, current_hash, allow_dataset_mismatch)

    exp_dir.mkdir(parents=True, exist_ok=False)  # fail if exists

    (exp_dir / "checkpoints").mkdir()
    (exp_dir / "samples").mkdir()

    record_dataset(dataset_dir, current_hash, exp_name)

    # Manifest
    manifest = {
        "name": name,
        "timestamp": timestamp,
        "git_commit": git_commit(),
        "dataset_dir": str(dataset_dir),
        "dataset_hash": current_hash,
        "steps": steps,
        "hyperparameters": kwargs,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "running",
    }
    with open(exp_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    # Dataset snapshot
    snapshot = snapshot_dataset(dataset_dir)
    with open(exp_dir / "dataset_snapshot.json", "w") as f:
        json.dump(snapshot, f, indent=2)

    print(f"Created experiment: {exp_dir}")
    print(f"  Git: {manifest['git_commit'][:8]}")
    print(f"  Dataset hash: {manifest['dataset_hash']}")
    print(f"  Fonts: {snapshot['count']}")

    return exp_dir, manifest


def main():
    parser = argparse.ArgumentParser(description="Experiment runner with immutable tracking")
    parser.add_argument("--name", required=True, help="Experiment name (e.g., Rg_v2)")
    parser.add_argument("--dataset-dir", default="dataset_v2")
    parser.add_argument("--steps", type=int, default=3500,
                        help="Steps to run THIS execution")
    parser.add_argument("--lr-schedule-steps", type=int, default=None,
                        help="Total planned steps for LR schedule (for partial/A-B runs to be resumed)")
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--warmup-steps", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--reference-chars", default="Rg",
                        help="Reference characters (must match dataset references)")
    parser.add_argument("--resume", type=str, default=None,
                        help="Path to existing experiment directory to resume")
    parser.add_argument("--dry-run", action="store_true",
                        help="Create experiment dir without running training")
    parser.add_argument("--allow-dataset-mismatch", action="store_true",
                        help="Override the dataset-hash registry check (NOT recommended). "
                             "Use only when you intend to retrain on a mutated dataset directory.")
    args = parser.parse_args()

    if args.resume:
        exp_dir = Path(args.resume)
        if not exp_dir.exists():
            print(f"ERROR: Resume path not found: {exp_dir}")
            return
        manifest = json.loads((exp_dir / "manifest.json").read_text())
        print(f"Resuming experiment: {exp_dir.name}")
        # Find latest checkpoint. Skip directories with non-numeric suffixes
        # (e.g. checkpoint-final, checkpoint-best) so they don't crash int().
        def _ckpt_step(p):
            try:
                return int(p.name.split("-")[1])
            except (IndexError, ValueError):
                return None
        checkpoints = sorted(
            (p for p in (exp_dir / "checkpoints").glob("checkpoint-*") if _ckpt_step(p) is not None),
            key=_ckpt_step,
        )
        if not checkpoints:
            print("No checkpoints found. Starting from scratch.")
            resume_arg = None
        else:
            resume_arg = str(checkpoints[-1])
            print(f"Resuming from: {resume_arg}")
    else:
        exp_dir, manifest = create_experiment(
            args.name,
            args.dataset_dir,
            args.steps,
            allow_dataset_mismatch=args.allow_dataset_mismatch,
            rank=args.rank,
            lr=args.lr,
            warmup_steps=args.warmup_steps,
            seed=args.seed,
            reference_chars=args.reference_chars,
        )
        resume_arg = None

    if args.dry_run:
        print(f"Dry run: experiment dir created at {exp_dir}")
        return

    # Build training command
    cmd = [
        sys.executable, "train_lora.py",
        "--dataset-dir", args.dataset_dir,
        "--output-dir", str(exp_dir / "checkpoints"),
        "--steps", str(args.steps),
        "--rank", str(args.rank),
        "--lr", str(args.lr),
        "--warmup-steps", str(args.warmup_steps),
        "--seed", str(args.seed),
    ]
    if args.lr_schedule_steps is not None:
        cmd.extend(["--lr-schedule-steps", str(args.lr_schedule_steps)])
    cmd.extend(["--reference-chars", args.reference_chars])
    if resume_arg:
        cmd.extend(["--resume", resume_arg])

    print(f"\nLaunching: {' '.join(cmd)}\n")

    # Stream training output to both console and experiment log
    log_path = exp_dir / "training.log"
    with open(log_path, "ab") as log_file:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        try:
            for line in iter(process.stdout.readline, b""):
                sys.stdout.buffer.write(line)
                sys.stdout.buffer.flush()
                log_file.write(line)
                log_file.flush()
        except KeyboardInterrupt:
            print("\n\nInterrupted. Killing training process...")
            process.terminate()
            process.wait()

    # Update manifest with completion status
    manifest = json.loads((exp_dir / "manifest.json").read_text())
    manifest["status"] = "completed" if process.returncode == 0 else f"failed (exit {process.returncode})"
    manifest["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(exp_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    # Copy metrics.csv if it exists
    src_metrics = exp_dir / "checkpoints" / "metrics.csv"
    if src_metrics.exists():
        shutil.copy2(src_metrics, exp_dir / "metrics.csv")

    print(f"\nExperiment {exp_dir.name} status: {manifest['status']}")


if __name__ == "__main__":
    main()
