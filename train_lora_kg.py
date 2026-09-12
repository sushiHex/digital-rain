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
import os
import re
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

def _build_distinctiveness_sampler(dataset, scores_path, alpha, clip):
    """WeightedRandomSampler favouring structurally distinctive fonts.

    weight_i = clamp((score_i / median_score) ** alpha, 1/clip, clip)

    Normalising by the median keeps the mean weight near 1 regardless of the
    score scale, alpha tunes aggressiveness (0 = uniform, 1 = proportional),
    and the clamp stops any single outlier font dominating an epoch. Fonts
    missing from the score file get the median score rather than being dropped.
    """
    import numpy as np
    from torch.utils.data import WeightedRandomSampler

    with open(scores_path, encoding="utf-8") as f:
        scores = json.load(f)["scores"]

    stems = dataset.stems
    med = float(np.median(list(scores.values())))
    missing = [s for s in stems if s not in scores]
    raw = np.array([scores.get(s, med) for s in stems], dtype=np.float64)
    w = np.clip((raw / med) ** alpha, 1.0 / clip, clip)

    # Report the shift the way it actually matters: what share of draws now
    # goes to the most distinctive decile, versus 10% under uniform sampling.
    p90 = np.percentile(raw, 90)
    share = w[raw >= p90].sum() / w.sum()
    log.info(f"Distinctiveness sampling: alpha={alpha} clip={clip} from {scores_path}")
    log.info(f"  weights: min {w.min():.2f}  median {np.median(w):.2f}  max {w.max():.2f}")
    log.info(f"  top-decile share of draws: {share:.1%} (uniform would be 10.0%)")
    if missing:
        log.info(f"  {len(missing)} font(s) not in score file, given median score")

    return WeightedRandomSampler(w.tolist(), num_samples=len(stems), replacement=True)


class CachedLatentDataset(Dataset):
    """Load pre-cached (reference, atlas) latent pairs from .pt files."""

    def __init__(self, cache_dir, exclude_stems=None):
        cache_dir = Path(cache_dir)
        atlas_dir = cache_dir / "atlases"
        ref_dir = cache_dir / "references"

        exclude = set(exclude_stems or ())
        self.excluded = []
        self.pairs = []
        for atlas_pt in sorted(atlas_dir.glob("*.pt")):
            ref_pt = ref_dir / atlas_pt.name
            if not ref_pt.exists():
                continue
            if atlas_pt.stem in exclude:
                self.excluded.append(atlas_pt.stem)
                continue
            self.pairs.append((ref_pt, atlas_pt))
        if exclude:
            log.info(f"  licence filter: excluded {len(self.excluded)} of "
                     f"{len(self.excluded) + len(self.pairs)} cached fonts")

        meta_path = cache_dir / "cache_meta.json"
        self.meta = json.load(open(meta_path)) if meta_path.exists() else {}

        log.info(f"Dataset: {len(self.pairs)} cached latent pairs from {cache_dir}")
        if self.meta:
            a, r = self.meta.get('atlas_seq_len', 0), self.meta.get('ref_seq_len', 0)
            log.info(f"  Atlas: {a} tokens, Ref: {r} tokens, Total: {a + r}/step")

    @property
    def stems(self):
        """Font stem per index, for aligning external per-font weights."""
        return [atlas_pt.stem for _, atlas_pt in self.pairs]

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


def install_block_throttle(transformer, duty, every_n=4):
    """Spread GPU idle ACROSS a step instead of pooling it at the end.

    Throttling at the step boundary is arithmetically correct and perceptually
    useless here: a microbatch takes ~9s, so a 90% duty cycle produces one ~0.9s
    gap every ~9s -- eight seconds of stutter, then a moment of smoothness. The
    desktop compositor needs frequent small windows, not one large one.

    So sleep a little at every Nth transformer block instead. Each hook sleeps
    in proportion to the time since the previous hook, so the TOTAL idle is
    identical -- only its distribution changes, from one 900ms gap to roughly
    thirty 30ms gaps.

    The synchronize is load-bearing for the same reason as at the step level:
    without it the CPU sleeps while the async queue keeps the device busy. It
    costs some CPU-side queue-ahead, which is cheap here because the GPU is the
    bottleneck and the CPU is mostly waiting anyway.

    Hooks also fire during gradient-checkpoint recomputation in the backward
    pass, which is wanted -- that is where much of the time goes.

    Returns the handles (never removed; the process ends with the run) or an
    empty list if the model does not expose the expected blocks, in which case
    the caller falls back to step-level throttling.
    """
    if duty >= 1.0 or every_n <= 0:
        return []
    # Find blocks by MODULE PATH, not attribute access: by this point the
    # transformer is wrapped by PEFT, so `transformer.transformer_blocks` may
    # resolve through a proxy or not at all, and a miss would silently downgrade
    # to step-level throttling -- the exact thing this is meant to replace.
    pattern = re.compile(r"(^|\.)(single_)?transformer_blocks\.\d+$")
    blocks = [m for name, m in transformer.named_modules() if pattern.search(name)]
    if not blocks:
        return []

    ratio = (1.0 - duty) / duty
    state = {"last": time.time()}

    def _yield():
        torch.cuda.synchronize()
        busy = time.time() - state["last"]
        # Guard the first call and any pause between steps: a long gap would
        # otherwise translate into a proportionally absurd sleep.
        if 0.0 < busy < 5.0:
            time.sleep(busy * ratio)
        state["last"] = time.time()

    def hook(_module, _inputs, output):
        _yield()
        # ALSO yield during the BACKWARD pass. Forward hooks alone covered only
        # the forward phase, which measured 92.4% of unthrottled speed against a
        # 90% target and left mean utilisation at 97.1% with all the idle
        # clustered in one phase of the step -- backward is where most of the
        # time goes. Hooking the output tensor's grad puts sleeps in the
        # backward pass too, which is what actually spreads the idle.
        t = output[0] if isinstance(output, (tuple, list)) and output else output
        if torch.is_tensor(t) and t.requires_grad:
            def _bwd(grad):
                _yield()
                return None          # None leaves the gradient untouched
            try:
                t.register_hook(_bwd)
            except RuntimeError:
                pass                 # non-leaf edge cases: forward-only is fine
        return None                  # never replace the module's output

    handles = [b.register_forward_hook(hook)
               for i, b in enumerate(blocks) if i % every_n == 0]
    return handles


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
    parser.add_argument("--gpu-duty-cycle", type=float,
                        default=float(os.environ.get("GPU_DUTY_CYCLE", "1.0")),
                        help="Fraction of wall-clock the GPU may stay busy, 0.05-1.0. "
                             "1.0 (default) is unthrottled. 0.9 leaves ~10%% of the "
                             "time idle so the Windows compositor can render, at ~11%% "
                             "longer training. Reads GPU_DUTY_CYCLE from the "
                             "environment so runners can set it without editing.")
    parser.add_argument("--gpu-throttle-every-n-blocks", type=int,
                        default=int(os.environ.get("GPU_THROTTLE_BLOCKS", "4")),
                        help="Sleep at every Nth transformer block so the idle is "
                             "spread across the step rather than pooled at its end. "
                             "0 falls back to throttling at the step boundary, which "
                             "gives one ~0.9s gap per ~9s step and does not feel like "
                             "headroom. Ignored when --gpu-duty-cycle is 1.0.")
    parser.add_argument("--exclusions", default="research/corpus_exclusions.json",
                        help="tracked keep/drop decision per font; filtered by default")
    parser.add_argument("--no-licence-filter", action="store_true",
                        help="train on the UNFILTERED corpus, including fonts whose "
                             "licences forbid redistributing derivative works. Only "
                             "for reproducing pre-2026-08-08 checkpoints.")
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--output-dir", default="training_output")
    parser.add_argument("--model", default="black-forest-labs/FLUX.2-klein-base-9B")
    parser.add_argument("--steps", type=int, default=3500)
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--warmup-steps", type=int, default=100,
                        help="linear warmup, in OPTIMIZER steps (not microbatches)")
    parser.add_argument("--legacy-lr-horizon", action="store_true",
                        help="reproduce the pre-2026-08-08 LR bug: use --steps as the "
                             "cosine horizon even though it counts microbatches, so the "
                             "schedule stops at 51.6%% of peak under accum=2. Only for "
                             "reproducing the existing checkpoints.")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--weight-decay", type=float, default=1e-5)
    parser.add_argument("--max-grad-norm", type=float, default=1.0)
    parser.add_argument("--num-train-timesteps", type=int, default=1000)
    parser.add_argument("--use-template", dest="use_template", action="store_true", default=True,
                        help="glyph-latent conditioning: feed the neutral template as a 2nd reference (T=20)")
    parser.add_argument("--no-use-template", dest="use_template", action="store_false")
    parser.add_argument("--grad-checkpointing", dest="grad_checkpointing", action="store_true", default=True,
                        help="gradient checkpointing (saves VRAM, ~1.3-1.5x slower)")
    parser.add_argument("--no-grad-checkpointing", dest="grad_checkpointing", action="store_false")
    parser.add_argument("--distinctiveness", default=None,
                        help="JSON from analysis/score_font_distinctiveness.py; enables "
                             "weighted sampling that favours structurally distinctive fonts")
    parser.add_argument("--distinct-alpha", type=float, default=0.5,
                        help="0 = uniform, 1 = proportional to score (default 0.5)")
    parser.add_argument("--distinct-clip", type=float, default=5.0,
                        help="max weight ratio either way, so one outlier font cannot "
                             "dominate an epoch (default 5.0)")
    parser.add_argument("--checkpoint-every", type=int, default=None,
                        help="if set, save every N steps (overrides the front-loaded schedule; "
                             "use on a contended GPU to cap lost progress per interruption)")
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.cache_dir) if args.cache_dir else Path(args.dataset_dir) / "cache"

    with open(output_dir / "train_config.json", "w") as f:
        json.dump(vars(args), f, indent=2)

    # Record the CONDITIONING explicitly so eval can assert it matches, instead
    # of inferring it from which argparse flags happen to exist. Two silent
    # mismatches shipped before this existed -- see conditioning_config.py.
    from conditioning_config import write_conditioning, PROMPT_TRAINED_SHORT
    import build_dataset as _bd
    write_conditioning(
        output_dir,
        prompt_style=PROMPT_TRAINED_SHORT,   # the hardcoded prompt below, not make_prompt()
        reference_chars=_bd.REF_CHARS,       # what the reference IMAGES were rendered with
        use_template=args.use_template,
        template_pt=str(cache_dir / "template.pt") if args.use_template else None,
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
    log.info("Caching text embeddings...")
    # NOTE the "Kg" below is a historical quirk: the reference IMAGES this
    # model trains on are rendered with build_dataset.REF_CHARS == "Rg", so
    # the prompt label and the image have always disagreed. Measured impact:
    # none (p=0.625, median delta 0.000) -- the model reads style from the
    # reference, not the glyph's identity.
    # DO NOT "fix" this string on an existing checkpoint: it is baked into the
    # cached prompt embeds the model was trained against, and eval must match
    # it (eval_checkpoint.py --reference-chars defaults to "Kg" for this
    # reason). Only change it alongside a full retrain.
    # See research/2026-07-28-reference-char-mismatch.md.
    prompt = (
        'A technical font atlas grid of 95 printable ASCII characters in a 12x8 grid. '
        'White glyphs on black background. Rectangular cells, taller than wide. '
        'The style is strictly derived from the reference image "Kg".'
    )
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
    if args.use_template:
        _old_xemb_w = transformer.x_embedder.weight.data.clone()  # (inner_dim, 128)
    log.info("Quantizing transformer to INT8...")
    quantize(transformer, weights=qint8)
    freeze(transformer)
    if args.use_template:
        # Expand the input embedder 128->256 so the channel-concatenated template
        # feeds in. New channels init 0 (warm-neutral). Fresh bf16 Linear -> not
        # quantized; saved via LoraConfig modules_to_save below.
        inner = _old_xemb_w.shape[0]
        new_xemb = torch.nn.Linear(256, inner, bias=False)
        with torch.no_grad():
            new_xemb.weight.zero_()
            new_xemb.weight[:, :128].copy_(_old_xemb_w)
        transformer.x_embedder = new_xemb.to("cuda", dtype=torch.bfloat16)
        log.info("  x_embedder expanded 128->256 (channel-concat glyph conditioning; new channels=0)")

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
        # persist + train the expanded x_embedder alongside the LoRA adapter
        modules_to_save=["x_embedder"] if args.use_template else None,
    )
    transformer = get_peft_model(transformer, lora_config)
    transformer.print_trainable_parameters()
    if args.grad_checkpointing:
        transformer.enable_gradient_checkpointing()
    else:
        log.info("  gradient checkpointing OFF (faster; uses more VRAM)")
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
    #
    # THE HORIZON IS IN OPTIMIZER-STEP UNITS, and that is the whole point of
    # this block. `--steps` counts MICROBATCH iterations (the training loop
    # increments global_step once per microbatch, and checkpoint names follow
    # it), but the scheduler only advances on the accumulation boundary. Using
    # args.steps directly as the horizon -- which is what this did until
    # 2026-08-08 -- makes the cosine run at 1/grad_accum speed and stop partway.
    #
    # Every checkpoint in the repo was trained under that bug: bs=1, accum=2,
    # steps=5000 gave 2,500 optimizer updates against a 5,000-step horizon, so
    # the schedule reached progress 0.4898 and the final LR was 51.6% of peak
    # (derived 5.1603e-05; glyph_4b.log records 5.16e-05). The model never got
    # an annealing phase, and training loss cannot show that.
    #
    # It handicapped every arm equally, so no A/B here is invalidated -- see
    # research/2026-08-08-training-loop-audit-three-confirmed-silent-defects.md.
    sched_total = max(1, math.ceil(args.steps / max(args.grad_accum, 1)))
    if args.legacy_lr_horizon:
        sched_total = args.steps
        log.warning(
            "--legacy-lr-horizon: reproducing the pre-2026-08-08 LR bug "
            f"(cosine horizon {args.steps} optimizer steps, but only "
            f"{math.ceil(args.steps / max(args.grad_accum, 1))} will happen)")

    def cosine_with_warmup(step):
        if step < args.warmup_steps:
            return step / max(args.warmup_steps, 1)
        progress = (step - args.warmup_steps) / max(sched_total - args.warmup_steps, 1)
        # Clamp: past the horizon cosine turns back UP, which would silently
        # re-raise the LR on any run that overshoots.
        return 0.5 * (1.0 + math.cos(math.pi * min(progress, 1.0)))

    lr_scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=cosine_with_warmup)
    log.info(f"LR horizon: {sched_total} optimizer steps "
             f"({args.steps} microbatches / accum {args.grad_accum})")

    # ==================================================================
    # Dataset
    # ==================================================================
    # Licence filter. 87 of the 925 cached fonts carry terms that do not permit
    # creating and redistributing derivative works, which is exactly what this
    # model does -- 48 vendor-supplied Windows faces and 36 Fontshare
    # closed-source (ITF-FFL), which explicitly claims derivative works as the
    # foundry's property. See
    # research/2026-08-08-identifying-the-undocumented-13-percent.md.
    #
    # ON BY DEFAULT: a run that quietly trains on them is the failure mode worth
    # preventing, and the flag to opt out is named so it cannot happen by
    # accident.
    exclude_stems = ()
    if not args.no_licence_filter:
        p = Path(args.exclusions)
        if p.exists():
            exclude_stems = json.load(open(p, encoding="utf-8"))["exclude_stems"]
        else:
            log.warning(f"{p} missing -- training on the UNFILTERED corpus. "
                        "Run analysis/corpus_licence_exclusions.py.")
    else:
        log.warning("--no-licence-filter: training on fonts whose licences do "
                    "NOT permit redistributing derivative works. Do not publish "
                    "weights or outputs from this run.")
    dataset = CachedLatentDataset(cache_dir, exclude_stems=exclude_stems)

    # Optional distinctiveness-weighted sampling. Structurally distinctive
    # fonts are ~10% of the corpus (analysis/score_font_distinctiveness.py), so
    # under uniform sampling they contribute ~10% of the gradient and get
    # underfit -- which is where the 4B trails the 9B. rank-64 showed capacity
    # allocation responds to pressure; this applies it deliberately.
    sampler = None
    if args.distinctiveness:
        sampler = _build_distinctiveness_sampler(
            dataset, args.distinctiveness, args.distinct_alpha, args.distinct_clip)

    dataloader = DataLoader(
        dataset, batch_size=args.batch_size,
        shuffle=(sampler is None),          # mutually exclusive with sampler
        sampler=sampler,
        num_workers=2, pin_memory=True, drop_last=True,
        collate_fn=collate_latents,
    )

    with open(cache_dir / "cache_meta.json") as f:
        cache_meta = json.load(f)
    atlas_seq_len = cache_meta["atlas_seq_len"]
    ref_seq_len = cache_meta["ref_seq_len"]
    atlas_h, atlas_w = cache_meta["atlas_spatial"]
    ref_h, ref_w = cache_meta["ref_spatial"]

    # Glyph-latent conditioning: the font-independent neutral template (2nd reference).
    tmpl_latents = None
    t_h = t_w = None
    if args.use_template:
        t_h, t_w = cache_meta["template_spatial"]
        tdata = torch.load(cache_dir / "template.pt", map_location="cpu", weights_only=True)
        tmpl_latents = tdata["latents"].unsqueeze(0).to("cuda", dtype=torch.bfloat16)  # (1, tseq, C)
        log.info(f"  glyph template: {tuple(tmpl_latents.shape)} ({t_h}x{t_w}, T=20 conditioning)")

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
    # (channel-concat conditioning: template uses no extra position ids — it rides
    #  the atlas tokens' channels, so img_ids stays atlas+ref)

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
    log.info(f"LR schedule: cosine, warmup={args.warmup_steps} optimizer steps")
    if args.batch_size == 1:
        # compute_snr_weights normalizes by the batch mean, so a one-element
        # batch is w/mean(w) == 1.0 exactly. Every checkpoint in this repo was
        # trained at batch_size=1: the objective is plain unweighted velocity
        # MSE, whatever the docstring says. Say so rather than advertising a
        # weighting that is not applied.
        log.info("Loss weighting: SNR w(t)=(1-t)^(-2) -- INERT at batch_size=1 "
                 "(normalized by the batch mean => exactly 1.0). Objective is "
                 "unweighted velocity MSE.")
    else:
        log.info(f"Loss weighting: SNR w(t)=(1-t)^(-2), batch-mean normalized")
    log.info(f"Checkpoints: front-loaded (every 100 in peak zone)")
    log.info(f"{'='*60}\n")

    gpu_duty_cycle = float(args.gpu_duty_cycle)
    if not 0.05 <= gpu_duty_cycle <= 1.0:
        raise SystemExit(f"--gpu-duty-cycle must be in [0.05, 1.0], got {gpu_duty_cycle}")
    # Prefer BLOCK-level throttling; fall back to step-level only if the model
    # does not expose transformer blocks. The two must never both be active --
    # each sleeps proportionally to elapsed busy time, so running both would
    # double the idle and halve throughput for no extra benefit.
    throttle_handles = install_block_throttle(
        transformer, gpu_duty_cycle, args.gpu_throttle_every_n_blocks)
    throttle_at_step = gpu_duty_cycle < 1.0 and not throttle_handles
    if gpu_duty_cycle < 1.0:
        where = (f"{len(throttle_handles)} block hooks (idle spread across the step)"
                 if throttle_handles else
                 "step boundary (blocks not found -- idle arrives in one lump)")
        log.info(f"GPU duty cycle: {gpu_duty_cycle:.0%} via {where}; "
                 f"~{(1/gpu_duty_cycle - 1):.0%} longer wall-clock")

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

            step_start = time.time()
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
                # Glyph-latent conditioning = CHANNEL-concat the (grid-aligned)
                # template into the atlas input channels (seq length UNCHANGED ->
                # feasible on the 3090). ref tokens zero-pad the template channels.
                if args.use_template:
                    t_lat = tmpl_latents.expand(bsz, -1, -1)               # (bsz, atlas_seq, 128)
                    atlas_in = torch.cat([noisy_atlas, t_lat], dim=-1)     # (bsz, atlas_seq, 256)
                    ref_in = torch.cat([ref_latents, torch.zeros_like(ref_latents)], dim=-1)
                    hidden_states = torch.cat([atlas_in, ref_in], dim=1)   # seq = 7424 (unchanged)
                else:
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

            # ── Desktop headroom ──
            # A saturating CUDA job takes ~98% of the GPU's 3d engine, and on a
            # single-GPU Windows box dwm.exe -- which composites every window on
            # screen -- has to time-slice into what's left. There is no way to
            # RESERVE capacity on this hardware: MPS (the mechanism that caps SM
            # share) is Linux-only, MIG is datacenter-only, and the Ryzen 9
            # 3950X has no iGPU to move the display to. Power and clock caps
            # slow the whole GPU down equally rather than freeing slices.
            #
            # So: yield wall-clock instead. Sleeping between steps gives the
            # compositor real idle windows. The synchronize is load-bearing --
            # without it the CPU sleeps while the async queue keeps the GPU busy
            # and the throttle does nothing at all.
            if throttle_at_step:
                torch.cuda.synchronize()
                busy = time.time() - step_start
                time.sleep(busy * (1.0 - gpu_duty_cycle) / gpu_duty_cycle)

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

            # ── Checkpoints: --checkpoint-every override, else front-loaded ──
            if global_step > 0 and (
                (args.checkpoint_every and global_step % args.checkpoint_every == 0)
                or (not args.checkpoint_every and should_save(global_step, args.steps))
            ):
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

    # Keep more checkpoints in peak zone, prune tail
    if not final:
        import shutil
        checkpoints = sorted(
            [d for d in output_dir.iterdir() if d.name.startswith("checkpoint-")],
            key=lambda d: int(d.name.split("-")[1])
        )
        # Keep all checkpoints in peak zone (<=1500), prune older tail checkpoints
        peak_zone = [c for c in checkpoints if int(c.name.split("-")[1]) <= 1500]
        tail_zone = [c for c in checkpoints if int(c.name.split("-")[1]) > 1500]
        while len(tail_zone) > 5:
            shutil.rmtree(tail_zone.pop(0))

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
