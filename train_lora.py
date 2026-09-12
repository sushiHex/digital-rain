"""Train a LoRA adapter for FLUX.2-klein-base-9B font atlas generation.

Reference-conditioned training with pre-cached VAE latents.
All confirmed optimizations from 10-agent review applied:

  - Cosine LR schedule with 100-step warmup (prevents late overfitting)
  - SNR loss weighting w(t) = (1-t)^(-2) (16% FID improvement over uniform)
  - Gradient accumulation 2 (effective batch 2, safe on 24GB)
  - 3,500 steps default (3.8 epochs for 927 images)
  - Front-loaded checkpointing (every 100 steps in peak zone 500-1500)
  - CSV metrics logging (loss, lr, grad_norm, vram — Python 3.14 safe)
  - OOM protection with graceful skip
  - Full transformer LoRA coverage (double + single stream blocks)

Pre-cache latents first:
  python cache_latents.py --dataset-dir dataset_v2 --ref-resolution 512

Then train:
  python train_lora.py --dataset-dir dataset_v2 --output-dir training_output
  python train_lora.py --resume training_output/checkpoint-1000
"""
import argparse
import csv
import gc
import json
import logging
import math
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

log = logging.getLogger("train")


# ===========================================================================
# Dataset
# ===========================================================================

class CachedLatentDataset(Dataset):
    """Load pre-cached (reference, atlas) latent pairs from .pt files."""

    def __init__(self, cache_dir):
        cache_dir = Path(cache_dir)
        atlas_dir = cache_dir / "atlases"
        ref_dir = cache_dir / "references"

        self.pairs = []
        for atlas_pt in sorted(atlas_dir.glob("*.pt")):
            ref_pt = ref_dir / atlas_pt.name
            if ref_pt.exists():
                self.pairs.append((ref_pt, atlas_pt))

        meta_path = cache_dir / "cache_meta.json"
        self.meta = json.load(open(meta_path)) if meta_path.exists() else {}

        log.info(f"Dataset: {len(self.pairs)} cached latent pairs from {cache_dir}")
        if self.meta:
            a, r = self.meta.get('atlas_seq_len', 0), self.meta.get('ref_seq_len', 0)
            log.info(f"  Atlas: {a} tokens, Ref: {r} tokens, Total: {a + r}/step")

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        ref_pt, atlas_pt = self.pairs[idx]
        ref_data = torch.load(ref_pt, map_location="cpu", weights_only=True)
        atlas_data = torch.load(atlas_pt, map_location="cpu", weights_only=True)
        return (
            ref_data["latents"], ref_data["h"], ref_data["w"],
            atlas_data["latents"], atlas_data["h"], atlas_data["w"],
        )


def collate_latents(batch):
    return (
        torch.stack([b[0] for b in batch]), batch[0][1], batch[0][2],
        torch.stack([b[3] for b in batch]), batch[0][4], batch[0][5],
    )


# ===========================================================================
# Position IDs
# ===========================================================================

def prepare_latent_ids(height, width, device, dtype):
    t = torch.arange(1, device=device, dtype=dtype)
    h = torch.arange(height, device=device, dtype=dtype)
    w = torch.arange(width, device=device, dtype=dtype)
    l = torch.arange(1, device=device, dtype=dtype)
    return torch.cartesian_prod(t, h, w, l).unsqueeze(0)


def prepare_ref_ids(height, width, device, dtype, scale=10):
    t = torch.tensor([scale], device=device, dtype=dtype)
    h = torch.arange(height, device=device, dtype=dtype)
    w = torch.arange(width, device=device, dtype=dtype)
    l = torch.arange(1, device=device, dtype=dtype)
    return torch.cartesian_prod(t, h, w, l).unsqueeze(0)


# ===========================================================================
# Flow matching (FLUX.2 Klein dynamic exponential shift + SNR weighting)
# ===========================================================================

def compute_sigmas(timesteps, image_seq_len, num_train_timesteps=1000,
                   base_shift=0.5, max_shift=1.15, base_seq=256, max_seq=4096):
    """Compute sigmas with FLUX.2 Klein's dynamic exponential shift."""
    t = timesteps.float() / num_train_timesteps
    t = t.clamp(1e-6, 1.0 - 1e-6)
    m = (max_shift - base_shift) / (max_seq - base_seq)
    b = base_shift - m * base_seq
    mu = image_seq_len * m + b
    exp_mu = math.exp(mu)
    return exp_mu / (exp_mu + (1.0 / t - 1.0))


def compute_snr_weights(sigmas):
    """SNR loss weighting: w(sigma) = (1 - sigma)^(-2).

    Upweights low-noise timesteps where the model should produce precise output.
    March 2026 paper (arXiv 2603.06454) shows 16% FID improvement over uniform.
    Clamped to avoid explosion near sigma=1.
    """
    weights = (1.0 - sigmas.clamp(max=0.999)) ** (-2.0)
    # Normalize to mean=1 so loss magnitude stays comparable
    weights = weights / weights.mean()
    return weights


def sample_timesteps(batch_size, device, num_train_timesteps=1000):
    """Logit-normal timestep sampling (standard for FLUX)."""
    u = torch.sigmoid(torch.randn(batch_size, device=device))
    return (u * num_train_timesteps).long().clamp(1, num_train_timesteps - 1)


# ===========================================================================
# Checkpoint save strategy (front-loaded for quality peak detection)
# ===========================================================================

def should_save(step, total_steps):
    """Front-loaded checkpoint strategy:
    - Every 100 steps in [100, 1500] (quality peak zone)
    - Every 250 steps in [1500, 2500]
    - Every 500 steps after 2500
    """
    if step <= 0:
        return False
    if step <= 1500:
        return step % 100 == 0
    if step <= 2500:
        return step % 250 == 0
    return step % 500 == 0


# ===========================================================================
# CSV metrics logger (Python 3.14 safe, no TensorBoard dependency)
# ===========================================================================

class MetricsLogger:
    """Log training metrics to CSV for post-hoc analysis."""

    def __init__(self, output_dir):
        self.path = output_dir / "metrics.csv"
        self.file = open(self.path, "w", newline="")
        self.writer = csv.writer(self.file)
        self.writer.writerow([
            "step", "epoch", "time_s", "loss", "lr", "grad_norm",
            "vram_gb", "peak_vram_gb", "sec_per_step",
        ])
        self.start_time = time.time()

    def log(self, step, epoch, loss, lr, grad_norm, vram_gb, peak_vram_gb, sps):
        elapsed = time.time() - self.start_time
        self.writer.writerow([
            step, epoch, f"{elapsed:.0f}", f"{loss:.6f}", f"{lr:.2e}",
            f"{grad_norm:.4f}", f"{vram_gb:.2f}", f"{peak_vram_gb:.2f}",
            f"{1/sps:.1f}" if sps > 0 else "0",
        ])
        if step % 50 == 0:
            self.file.flush()

    def close(self):
        self.file.flush()
        self.file.close()


# ===========================================================================
# Main
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="Train LoRA for FLUX.2-klein-base-9B font atlas")
    parser.add_argument("--dataset-dir", default="dataset_v2")
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--output-dir", default="training_output")
    parser.add_argument("--model", default="black-forest-labs/FLUX.2-klein-base-9B")
    parser.add_argument("--steps", type=int, default=3500,
                        help="Number of training steps to run THIS execution")
    parser.add_argument("--lr-schedule-steps", type=int, default=None,
                        help="Total planned training steps for LR schedule (defaults to --steps). "
                             "Set this to the FINAL planned step count when doing partial/A-B runs "
                             "that will be resumed and continued.")
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--warmup-steps", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--weight-decay", type=float, default=1e-5)
    parser.add_argument("--max-grad-norm", type=float, default=1.0)
    parser.add_argument("--num-train-timesteps", type=int, default=1000)
    parser.add_argument("--reference-chars", default="Rg",
                        help="Reference characters used in prompt (must match dataset references)")
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.cache_dir) if args.cache_dir else Path(args.dataset_dir) / "cache"

    with open(output_dir / "train_config.json", "w") as f:
        json.dump(vars(args), f, indent=2)

    # Record CONDITIONING explicitly (see conditioning_config.py). This trainer
    # uses make_prompt() -> the STRUCTURED prompt, unlike train_lora_kg.py.
    from conditioning_config import write_conditioning, PROMPT_STRUCTURED
    write_conditioning(
        output_dir,
        prompt_style=PROMPT_STRUCTURED,
        reference_chars=args.reference_chars,
        use_template=False,
    )

    # Logging: console + file
    log_path = output_dir / "training.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(log_path), mode="a"),
        ],
    )

    # CSV metrics
    metrics = MetricsLogger(output_dir)

    log.info(f"GPU: {torch.cuda.get_device_name(0)}")
    log.info(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    if not (cache_dir / "cache_meta.json").exists():
        log.info(f"ERROR: No latent cache at {cache_dir}")
        log.info(f"Run: python cache_latents.py --dataset-dir {args.dataset_dir}")
        return

    # ==================================================================
    # Load model
    # ==================================================================
    from diffusers import Flux2KleinPipeline
    from optimum.quanto import quantize, qint8, freeze
    from peft import LoraConfig, get_peft_model

    log.info("Loading pipeline...")
    t0 = time.time()
    pipe = Flux2KleinPipeline.from_pretrained(args.model, torch_dtype=torch.bfloat16)
    transformer = pipe.transformer

    # ==================================================================
    # Cache text embeddings, free text encoder
    # ==================================================================
    log.info(f"Caching text embeddings (reference_chars={args.reference_chars})...")
    from atlas_constants import make_prompt
    prompt = make_prompt(args.reference_chars)
    pipe.text_encoder.to("cuda")
    with torch.no_grad():
        cached_prompt_embeds, cached_text_ids = pipe.encode_prompt(prompt=prompt)
    cached_prompt_embeds = cached_prompt_embeds.cpu()
    cached_text_ids = cached_text_ids.cpu()
    log.info(f"  prompt_embeds: {cached_prompt_embeds.shape}, text_ids: {cached_text_ids.shape}")

    pipe.text_encoder.to("cpu")
    del pipe.text_encoder, pipe.tokenizer, pipe.vae, pipe
    gc.collect()
    torch.cuda.empty_cache()

    # ==================================================================
    # Quantize + LoRA (full transformer coverage)
    # ==================================================================
    log.info("Quantizing transformer to INT8...")
    quantize(transformer, weights=qint8)
    freeze(transformer)

    log.info(f"Adding LoRA (rank={args.rank})...")
    lora_target_regex = (
        r'.*\.attn\.to_[qkv]$|'
        r'.*\.attn\.to_out\.0$|'
        r'.*\.attn\.add_[qkv]_proj$|'
        r'.*\.attn\.to_add_out$|'
        r'.*\.ff(?:_context)?\.linear_(?:in|out)$|'
        r'.*\.attn\.to_qkv_mlp_proj$|'
        r'.*single_transformer_blocks\.\d+\.attn\.to_out$'
    )
    lora_config = LoraConfig(
        r=args.rank, lora_alpha=args.rank,
        target_modules=lora_target_regex, lora_dropout=0.0,
    )
    transformer = get_peft_model(transformer, lora_config)
    transformer.print_trainable_parameters()
    transformer.enable_gradient_checkpointing()
    transformer.to("cuda", dtype=torch.bfloat16)
    transformer.train()

    load_time = time.time() - t0
    log.info(f"Model loaded in {load_time:.0f}s, VRAM: {torch.cuda.memory_allocated()/1024**3:.1f} GB")

    # ==================================================================
    # Optimizer + Cosine LR with warmup
    # ==================================================================
    trainable_params = [p for p in transformer.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(
        trainable_params, lr=args.lr, weight_decay=args.weight_decay,
        betas=(0.9, 0.999), eps=1e-8,
    )

    # Cosine schedule with linear warmup.
    # The LR scheduler ticks once per OPTIMIZER step (not per training step),
    # so when grad_accum > 1, we must scale total ticks accordingly.
    # CRITICAL: If this is a partial run that will be resumed (e.g., A/B test
    # before full training), pass --lr-schedule-steps with the FULL planned
    # training length so the cosine schedule matches the full intended run.
    schedule_total_steps = args.lr_schedule_steps if args.lr_schedule_steps is not None else args.steps
    total_scheduler_ticks = max(schedule_total_steps // args.grad_accum, 1)

    def cosine_with_warmup(step):
        if step < args.warmup_steps:
            return step / max(args.warmup_steps, 1)
        progress = (step - args.warmup_steps) / max(total_scheduler_ticks - args.warmup_steps, 1)
        progress = min(progress, 1.0)  # clamp in case we somehow exceed schedule
        return 0.5 * (1.0 + math.cos(math.pi * progress))

    lr_scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=cosine_with_warmup)
    log.info(
        f"LR schedule: cosine with warmup\n"
        f"  Run-this-execution steps: {args.steps}\n"
        f"  Schedule total (for cosine): {schedule_total_steps}\n"
        f"  Scheduler ticks total: {total_scheduler_ticks}\n"
        f"  Warmup ticks: {args.warmup_steps} (= {args.warmup_steps * args.grad_accum} global steps)"
    )

    # ==================================================================
    # Dataset (with explicit generator for reproducible shuffle order)
    # ==================================================================
    dataset = CachedLatentDataset(cache_dir)
    data_generator = torch.Generator()
    data_generator.manual_seed(args.seed)
    dataloader = DataLoader(
        dataset, batch_size=args.batch_size, shuffle=True,
        num_workers=2, pin_memory=True, drop_last=True,
        collate_fn=collate_latents,
        generator=data_generator,
    )

    with open(cache_dir / "cache_meta.json") as f:
        cache_meta = json.load(f)
    atlas_seq_len = cache_meta["atlas_seq_len"]
    ref_seq_len = cache_meta["ref_seq_len"]
    atlas_h, atlas_w = cache_meta["atlas_spatial"]
    ref_h, ref_w = cache_meta["ref_spatial"]

    # ==================================================================
    # Resume
    # ==================================================================
    global_step = 0
    if args.resume:
        resume_path = Path(args.resume)
        adapter_file = resume_path / "adapter_model.safetensors"
        if adapter_file.exists():
            from peft import set_peft_model_state_dict
            from safetensors.torch import load_file
            log.info(f"Resuming LoRA from {resume_path}")
            set_peft_model_state_dict(
                transformer, load_file(str(adapter_file)), adapter_name="default"
            )
        state_path = resume_path / "training_state.pt"
        if state_path.exists():
            state = torch.load(state_path, map_location="cpu", weights_only=True)
            # Move optimizer state tensors to GPU (except step counters which stay CPU)
            opt_state = state["optimizer"]
            for param_state in opt_state.get("state", {}).values():
                for k, v in param_state.items():
                    if isinstance(v, torch.Tensor) and v.is_floating_point():
                        param_state[k] = v.to("cuda")
            optimizer.load_state_dict(opt_state)
            lr_scheduler.load_state_dict(state["lr_scheduler"])
            global_step = state["global_step"]
            log.info(f"Resumed at step {global_step}")

    # Pre-compute position IDs
    atlas_ids_t = prepare_latent_ids(atlas_h, atlas_w, "cuda", torch.bfloat16)
    ref_ids_t = prepare_ref_ids(ref_h, ref_w, "cuda", torch.bfloat16, scale=10)

    # ==================================================================
    # Training loop
    # ==================================================================
    total_tokens = atlas_seq_len + ref_seq_len
    epochs_total = args.steps / max(len(dataset), 1)
    log.info(f"\n{'='*60}")
    log.info(f"Training: {args.steps} steps, lr={args.lr}, rank={args.rank}")
    log.info(f"Dataset: {len(dataset)} pairs, batch={args.batch_size}, accum={args.grad_accum}")
    log.info(f"Effective batch: {args.batch_size * args.grad_accum}")
    log.info(f"Epochs: ~{epochs_total:.1f}")
    log.info(f"Tokens/step: {total_tokens} (atlas={atlas_seq_len} + ref={ref_seq_len})")
    log.info(f"LR schedule: cosine, warmup={args.warmup_steps} steps")
    log.info(f"Loss weighting: SNR w(t)=(1-t)^(-2)")
    log.info(f"Checkpoints: front-loaded (every 100 in peak zone)")
    log.info(f"{'='*60}\n")

    running_loss = 0.0
    running_grad_norm = 0.0
    log_interval = 10
    start_time = time.time()
    epoch = 0
    best_loss = float("inf")

    while global_step < args.steps:
        epoch += 1
        for ref_lats, r_h, r_w, atlas_lats, a_h, a_w in dataloader:
            if global_step >= args.steps:
                break

            bsz = atlas_lats.shape[0]

            try:
                atlas_latents = atlas_lats.to("cuda", dtype=torch.bfloat16)
                ref_latents = ref_lats.to("cuda", dtype=torch.bfloat16)

                a_ids = atlas_ids_t.expand(bsz, -1, -1)
                r_ids = ref_ids_t.expand(bsz, -1, -1)
                text_embeds = cached_prompt_embeds.expand(bsz, -1, -1).to("cuda", dtype=torch.bfloat16)
                txt_ids = cached_text_ids.expand(bsz, -1, -1).to("cuda", dtype=torch.bfloat16)

                # ── Flow matching ──
                noise = torch.randn_like(atlas_latents)
                timesteps = sample_timesteps(bsz, "cuda", args.num_train_timesteps)
                sigmas = compute_sigmas(timesteps, atlas_seq_len, args.num_train_timesteps)
                sigmas = sigmas.to(dtype=atlas_latents.dtype)

                sigmas_bc = sigmas[:, None, None]
                noisy_atlas = (1.0 - sigmas_bc) * atlas_latents + sigmas_bc * noise

                # ── Transformer forward ──
                hidden_states = torch.cat([noisy_atlas, ref_latents], dim=1)
                img_ids = torch.cat([a_ids, r_ids], dim=1)

                model_pred = transformer(
                    hidden_states=hidden_states,
                    encoder_hidden_states=text_embeds,
                    timestep=sigmas,
                    img_ids=img_ids,
                    txt_ids=txt_ids,
                    guidance=None,
                    return_dict=False,
                )
                if isinstance(model_pred, tuple):
                    model_pred = model_pred[0]

                # ── SNR-weighted loss on atlas tokens ──
                atlas_pred = model_pred[:, :atlas_seq_len, :]
                target = noise - atlas_latents

                # Per-sample MSE
                per_sample_loss = ((atlas_pred.float() - target.float()) ** 2).mean(dim=(1, 2))

                # SNR weighting
                snr_weights = compute_snr_weights(sigmas)
                loss = (per_sample_loss * snr_weights).mean()
                loss = loss / args.grad_accum

                loss.backward()

                if (global_step + 1) % args.grad_accum == 0:
                    grad_norm = torch.nn.utils.clip_grad_norm_(trainable_params, args.max_grad_norm)
                    running_grad_norm += grad_norm.item()
                    optimizer.step()
                    lr_scheduler.step()
                    optimizer.zero_grad()

                running_loss += loss.item() * args.grad_accum

            except torch.cuda.OutOfMemoryError:
                log.info(f"  OOM at step {global_step + 1}, skipping")
                optimizer.zero_grad(set_to_none=True)
                torch.cuda.empty_cache()
                gc.collect()
                continue

            global_step += 1

            # ── Logging ──
            if global_step % log_interval == 0:
                avg_loss = running_loss / log_interval
                avg_gnorm = running_grad_norm / max(log_interval // args.grad_accum, 1)
                elapsed = time.time() - start_time
                sps = global_step / elapsed
                eta_hr = (args.steps - global_step) / sps / 3600 if sps > 0 else 0
                cur_lr = lr_scheduler.get_last_lr()[0]
                vram_gb = torch.cuda.memory_allocated() / 1024**3
                peak_gb = torch.cuda.max_memory_allocated() / 1024**3

                log.info(
                    f"step {global_step:5d}/{args.steps} | "
                    f"loss {avg_loss:.4f} | "
                    f"lr {cur_lr:.2e} | "
                    f"gnorm {avg_gnorm:.2f} | "
                    f"{sps:.3f} it/s | "
                    f"ETA {eta_hr:.1f}h | "
                    f"VRAM {vram_gb:.1f}/{peak_gb:.1f} GB"
                )
                metrics.log(global_step, epoch, avg_loss, cur_lr, avg_gnorm, vram_gb, peak_gb, sps)

                if avg_loss < best_loss:
                    best_loss = avg_loss
                running_loss = 0.0
                running_grad_norm = 0.0

            # ── Front-loaded checkpoints ──
            if should_save(global_step, args.steps):
                _save_checkpoint(transformer, optimizer, lr_scheduler, global_step, output_dir)

    # Final
    _save_checkpoint(transformer, optimizer, lr_scheduler, global_step, output_dir, final=True)
    _export_diffusers_lora(transformer, output_dir)
    metrics.close()

    total_time = (time.time() - start_time) / 3600
    log.info(f"\nTraining complete. {total_time:.1f} hours, best loss: {best_loss:.4f}")
    log.info(f"Metrics saved: {output_dir / 'metrics.csv'}")


# ===========================================================================
# Checkpoint + export
# ===========================================================================

def _save_checkpoint(transformer, optimizer, lr_scheduler, step, output_dir, final=False):
    name = "final" if final else f"checkpoint-{step}"
    ckpt_dir = output_dir / name
    ckpt_dir.mkdir(exist_ok=True)

    transformer.save_pretrained(str(ckpt_dir))

    # Deep copy optimizer state with CPU tensors (don't mutate live state!)
    import copy
    live_state = optimizer.state_dict()
    opt_state = {
        "state": {},
        "param_groups": copy.deepcopy(live_state["param_groups"]),
    }
    for k, v in live_state.get("state", {}).items():
        opt_state["state"][k] = {}
        for kk, vv in v.items():
            if isinstance(vv, torch.Tensor):
                opt_state["state"][k][kk] = vv.detach().cpu().clone()
            else:
                opt_state["state"][k][kk] = vv

    torch.save({
        "optimizer": opt_state,
        "lr_scheduler": lr_scheduler.state_dict(),
        "global_step": step,
    }, ckpt_dir / "training_state.pt")

    # SAFETY: Never auto-delete checkpoints. Disk is cheap, training is expensive.
    # If disk space becomes an issue, manually clean up after a successful run.

    log.info(f"  Saved: {ckpt_dir}")


def _export_diffusers_lora(transformer, output_dir):
    from peft import get_peft_model_state_dict
    from safetensors.torch import save_file

    peft_sd = get_peft_model_state_dict(transformer)
    state_dict = {f"transformer.{k}": v.cpu().contiguous() for k, v in peft_sd.items()}

    export_path = output_dir / "font_atlas_lora.safetensors"
    save_file(state_dict, str(export_path))
    log.info(f"  Exported: {export_path} ({export_path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
