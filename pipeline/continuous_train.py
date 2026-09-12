"""Continuous training with pause/render/resume per checkpoint.

Walks the front-loaded checkpoint schedule (every 100 in [100,1500],
every 250 in [1500,2500], every 500 in [2500,target]). After each new
checkpoint is written, pauses training, launches render_checkpoint.py
to generate a sample, then resumes training from where it left off.

Each train/render is its own subprocess, so VRAM is fully released
between phases.

Usage:
  python pipeline/continuous_train.py \
    --experiment experiments/20260406-204250_Kg_300_ab \
    --target-steps 3500 \
    --lr-schedule-steps 3500 \
    --reference-chars Kg \
    --dataset-dir dataset_Kg
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path


def latest_checkpoint(checkpoints_dir):
    """Return (path, step) of the highest-numbered checkpoint, or (None, 0)."""
    ckpts = []
    for p in checkpoints_dir.glob("checkpoint-*"):
        try:
            step = int(p.name.split("-")[1])
            ckpts.append((p, step))
        except (ValueError, IndexError):
            continue
    if not ckpts:
        return None, 0
    ckpts.sort(key=lambda t: t[1])
    return ckpts[-1]


def next_checkpoint_step(current, target):
    """Return the next checkpoint step on the front-loaded schedule, capped at target.

    Schedule mirrors train_lora.should_save:
      - every 100 in (0, 1500]
      - every 250 in (1500, 2500]
      - every 500 in (2500, ...]
    Returns None when current >= target.
    """
    if current >= target:
        return None
    if current < 1500:
        nxt = ((current // 100) + 1) * 100
    elif current < 2500:
        nxt = ((current // 250) + 1) * 250
    else:
        nxt = ((current // 500) + 1) * 500
    return min(nxt, target)


def stream_subprocess(cmd, log_file):
    """Run cmd, streaming stdout to console + log_file. Return exit code."""
    header = f"\n>>> {' '.join(cmd)}\n"
    print(header, flush=True)
    log_file.write(header.encode())
    log_file.flush()
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0
    )
    try:
        for line in iter(proc.stdout.readline, b""):
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
            log_file.write(line)
            log_file.flush()
    except KeyboardInterrupt:
        print("\n[continuous_train] Interrupted, terminating child...", flush=True)
        proc.terminate()
        proc.wait()
        raise
    proc.wait()
    return proc.returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", required=True,
                        help="Experiment dir (must contain checkpoints/, samples/)")
    parser.add_argument("--target-steps", type=int, default=3500,
                        help="Final training step to reach")
    parser.add_argument("--lr-schedule-steps", type=int, default=3500,
                        help="Total step count used for cosine LR schedule")
    parser.add_argument("--reference-chars", required=True)
    parser.add_argument("--reference-font", default="C:/Windows/Fonts/times.ttf")
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--warmup-steps", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--render-steps", type=int, default=20,
                        help="Inference steps for sample rendering")
    parser.add_argument("--render-seed", type=int, default=42,
                        help="Inference seed for sample rendering (kept fixed)")
    parser.add_argument("--skip-render", action="store_true",
                        help="Train through checkpoints without rendering samples")
    args = parser.parse_args()

    exp_dir = Path(args.experiment)
    if not exp_dir.exists():
        print(f"ERROR: experiment dir does not exist: {exp_dir}")
        sys.exit(1)
    ckpt_dir = exp_dir / "checkpoints"
    samples_dir = exp_dir / "samples"
    samples_dir.mkdir(exist_ok=True)

    orch_log_path = exp_dir / "continuous.log"
    orch_log = open(orch_log_path, "ab")

    def logprint(msg):
        line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
        print(line, flush=True)
        orch_log.write((line + "\n").encode())
        orch_log.flush()

    logprint("=" * 60)
    logprint("Continuous orchestrator started")
    logprint(f"  experiment:        {exp_dir}")
    logprint(f"  target_steps:      {args.target_steps}")
    logprint(f"  lr_schedule_steps: {args.lr_schedule_steps}")
    logprint(f"  reference_chars:   {args.reference_chars}")
    logprint(f"  dataset_dir:       {args.dataset_dir}")
    logprint(f"  skip_render:       {args.skip_render}")
    logprint("=" * 60)

    cycle_count = 0
    overall_start = time.time()

    try:
        while True:
            latest_ckpt, current_step = latest_checkpoint(ckpt_dir)
            next_step = next_checkpoint_step(current_step, args.target_steps)
            if next_step is None:
                logprint(f"Reached target step {args.target_steps}. Done.")
                break

            cycle_count += 1
            cycle_start = time.time()
            logprint(f"--- Cycle {cycle_count}: step {current_step} -> {next_step} ---")
            if latest_ckpt is None:
                logprint("  No starting checkpoint found; starting from scratch.")
            else:
                logprint(f"  Resuming from: {latest_ckpt}")

            # ============================
            # Train to next checkpoint
            # ============================
            train_cmd = [
                sys.executable, "train_lora.py",
                "--dataset-dir", args.dataset_dir,
                "--output-dir", str(ckpt_dir),
                "--steps", str(next_step),
                "--lr-schedule-steps", str(args.lr_schedule_steps),
                "--rank", str(args.rank),
                "--lr", str(args.lr),
                "--warmup-steps", str(args.warmup_steps),
                "--seed", str(args.seed),
                "--reference-chars", args.reference_chars,
            ]
            if latest_ckpt is not None:
                train_cmd.extend(["--resume", str(latest_ckpt)])

            train_start = time.time()
            rc = stream_subprocess(train_cmd, orch_log)
            train_elapsed = time.time() - train_start
            if rc != 0:
                logprint(f"FATAL: training exited rc={rc} after {train_elapsed/60:.1f}m. Aborting.")
                sys.exit(1)

            new_ckpt_path = ckpt_dir / f"checkpoint-{next_step}"
            if not new_ckpt_path.exists():
                logprint(f"FATAL: expected {new_ckpt_path} but it was not created. Aborting.")
                sys.exit(1)
            logprint(f"  Training complete: {new_ckpt_path} ({train_elapsed/60:.1f}m)")

            # ============================
            # Render sample
            # ============================
            if args.skip_render:
                logprint("  --skip-render set; not rendering this cycle")
            else:
                render_out = samples_dir / f"step_{next_step:05d}_times.png"
                render_cmd = [
                    sys.executable, "render_checkpoint.py",
                    str(new_ckpt_path),
                    "--out", str(render_out),
                    "--reference-chars", args.reference_chars,
                    "--reference-font", args.reference_font,
                    "--steps", str(args.render_steps),
                    "--seed", str(args.render_seed),
                ]
                render_start = time.time()
                rc = stream_subprocess(render_cmd, orch_log)
                render_elapsed = time.time() - render_start
                if rc != 0:
                    # Don't abort the run for a render failure — sample is recoverable later.
                    logprint(f"  WARN: render failed rc={rc} after {render_elapsed/60:.1f}m. Continuing training.")
                else:
                    logprint(f"  Sample rendered: {render_out} ({render_elapsed/60:.1f}m)")

            cycle_elapsed = time.time() - cycle_start
            total_elapsed = time.time() - overall_start
            logprint(f"  Cycle {cycle_count} done in {cycle_elapsed/60:.1f}m | total {total_elapsed/3600:.2f}h")
    except KeyboardInterrupt:
        logprint("Orchestrator interrupted by user.")
        sys.exit(130)
    finally:
        total_elapsed = time.time() - overall_start
        logprint(f"Orchestrator exit. Cycles completed: {cycle_count}, total elapsed: {total_elapsed/3600:.2f}h")
        orch_log.close()


if __name__ == "__main__":
    main()
