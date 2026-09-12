"""Task 7: Diffusion-DPO trainer — fine-tune the glyph-cond LoRA to prefer
higher-fidelity renders.

Design (adversarial-review-hardened):

  * POLICY  adapter = trainable PEFT adapter "default", initialised from
    glyph-cond@5000 (training_glyph_r32_5000/checkpoint-5000).
  * REFERENCE adapter = a SECOND, frozen PEFT adapter "reference", ALSO loaded
    from glyph-cond@5000 via ``transformer.load_adapter(..., adapter_name=
    "reference")``. This is deliberately NOT ``disable_adapter()`` — disabling
    would expose base FLUX (wrong reference); Diffusion-DPO's reference must be
    the *un-fine-tuned policy*, i.e. glyph@5000.
  * Per step we sample ONE ``(noise, timesteps, sigmas)`` from the WINNER atlas
    latents (reusing train_lora_kg.sample_timesteps / compute_sigmas) and build
    BOTH ``noisy_win`` and ``noisy_lose`` with the SAME noise and sigmas. The
    policy forwards (win & lose, grad, checkpointed) and the reference forwards
    (win & lose, ``torch.no_grad()``) all consume that identical noised
    construction — so the reference "loss" is a proper constant baseline for the
    exact same (noise, t) the policy sees. It is recomputed INLINE each step (it
    depends on (noise, t); a single cached scalar per pair would be wrong).
  * Template-dropout: with prob ``--template-dropout`` the template channels are
    zeroed for the whole step (both policy and reference forwards), so the model
    doesn't over-trust the disambiguation template.

Per-font DPO: ``pref_pairs.json`` is per-(font,char). Pairs are grouped by font;
per font we assemble a WINNER atlas (paste each cell's ``winner_key`` crop) and a
LOSER atlas (paste each cell's ``loser_key`` crop) by reusing
``build_sft_cache.assemble_winner_atlas`` (with ``key_field``), VAE-encode both to
(6400,128) latents, and cache the (winner,loser) latent pair to disk (resumable,
like Task 6). One DPO example per font = (winner_latent, loser_latent) sharing the
font's reference latents + the disambig template. Each font's cache entry also
carries a ``font_weight`` scalar (mean of that font's ``pref_pairs.json``
per-cell ``weight`` — the REGRESSION_CHARS up-weighting from
select_preferences.py); the training loop multiplies the font's DPO loss by it
before ``.backward()``, so fonts touching a regression cell get a proportionally
larger gradient. All-1 weights (the default) give ``font_weight == 1.0``, i.e. no
behavior change.

Pure-function loss surrogates (``dpo_loss`` / ``per_sample_flow_loss``) are CPU
unit-tested in tests/test_dpo_train.py. The GPU trainer glue is
correct-by-construction against train_lora_kg.py (same pipe/quant/x_embedder/PEFT
setup, same flow-matching math, same checkpoint/resume) and is GPU-smoked by the
controller before the multi-day run.

Build the per-font pair cache first (GPU; VAE encode):
  python dpo_train.py --build-cache --pairs dpo_data/pref_pairs.json \
      --candidate-dir dpo_data/candidates --pair-cache dpo_data/pair_cache

Then train (GPU):
  python dpo_train.py --pairs dpo_data/pref_pairs.json \
      --resume training_glyph_r32_5000/checkpoint-5000 \
      --output-dir training_dpo_r32 --steps 3000 --checkpoint-every 100 \
      --beta 0.1 --template-dropout 0.1
"""
import argparse
import gc
import json
import logging
import math
import os
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

# Reuse the proven train_lora_kg building blocks VERBATIM (import, do not clone):
# pipe/quant/x_embedder setup happens inline below (mirrors train_lora_kg.main),
# but the position-id, flow-matching, checkpoint and metrics helpers are shared.
from train_lora_kg import (
    prepare_latent_ids,
    prepare_ref_ids,
    compute_sigmas,
    compute_snr_weights,
    sample_timesteps,
    _save_checkpoint,
    MetricsLogger,
)
# Reuse (and generalise via key_field) the Task-6 per-font atlas compositor.
from build_sft_cache import assemble_winner_atlas, _fonts_in

log = logging.getLogger("dpo")

# Import rather than re-declare: candidate_gen.MODEL_SPECS is the one place
# checkpoint paths are defined, so a moved checkpoint updates in a single spot.
from candidate_gen import GLYPH_CKPT as GLYPH_CKPT_DEFAULT


# ===========================================================================
# Pure loss functions (CPU-unit-tested in tests/test_dpo_train.py) — verbatim
# from the Task-7 brief.
# ===========================================================================

def per_sample_flow_loss(model_pred_atlas, target, snr_weights):
    """SNR-weighted per-sample flow-matching MSE over the atlas tokens.

    model_pred_atlas, target: (bsz, atlas_seq, C); snr_weights: (bsz,).
    Returns (bsz,) — the flow "loss" surrogate DPO contrasts across win/lose.
    """
    per = ((model_pred_atlas.float() - target.float()) ** 2).mean(dim=(1, 2))  # (bsz,)
    return per * snr_weights


def dpo_loss(policy_win_loss, policy_lose_loss, ref_win_loss, ref_lose_loss, beta):
    """Diffusion-DPO objective on the flow-loss surrogate.

    Prefer the winner => the policy should reduce the winner's flow loss (and/or
    raise the loser's) *relative to the frozen reference*. margin>0 means the
    policy already prefers the winner more than the reference does, so the loss
    is small.
    """
    margin = (policy_win_loss - ref_win_loss) - (policy_lose_loss - ref_lose_loss)
    return -F.logsigmoid(-beta * margin).mean()


# ===========================================================================
# Per-font (winner, loser) latent pair cache — resumable (Task-6 style)
# ===========================================================================

def _pairs_for_font(pairs, font):
    return [p for p in pairs if p["font"] == font]


def font_weight_for(fpairs):
    """Per-font DPO scalar weight = mean of this font's pref_pairs.json
    per-(font,char) ``weight`` (the REGRESSION_CHARS up-weighting
    select_preferences.select() assigns, default 1 / upweight otherwise).

    Pure/CPU-unit-tested (tests/test_dpo_train.py) — a font with no
    up-weighted cells has font_weight == 1.0 (no-op on the DPO loss); a font
    with some regression-char pairs gets a >1 scalar the training loop
    multiplies its DPO loss by before ``.backward()``.
    """
    if not fpairs:
        return 1.0
    return sum(p.get("weight", 1) for p in fpairs) / len(fpairs)


def build_pair_cache(pairs_path, candidate_dir, out_cache_dir,
                     model="black-forest-labs/FLUX.2-klein-base-9B",
                     atlas_resolution=1280, max_fonts=None):
    """VAE-encode per-font WINNER and LOSER atlases into a resumable pair cache.

    For each font referenced by ``pref_pairs.json`` we composite two atlases off
    the same glyph__seed0 base — one pasting ``winner_key`` cells, one pasting
    ``loser_key`` cells (via build_sft_cache.assemble_winner_atlas's key_field) —
    then encode both through the SAME cache_latents.encode_and_cache path every
    other atlas uses (no reimplemented pack/normalise math), writing
    ``<out_cache_dir>/<font>.pt = {"winner": (6400,128) fp16, "loser": (6400,128)
    fp16, "h":80, "w":80}``. Idempotent: a font whose .pt already exists is
    skipped, so an interrupted cache build (or a --resume'd training run that
    finds a partial cache) picks up where it left off.

    GPU (VAE). Not exercised by this task's CPU tests; correct-by-construction
    against cache_latents.py + build_sft_cache.py and GPU-smoked by the
    controller.
    """
    import tempfile

    from PIL import Image
    from cache_latents import encode_and_cache

    pairs = json.loads(Path(pairs_path).read_text())
    out_cache_dir = Path(out_cache_dir)
    out_cache_dir.mkdir(parents=True, exist_ok=True)

    fonts = _fonts_in(pairs)
    if max_fonts is not None:
        fonts = fonts[:max_fonts]

    # Load VAE + batch-norm stats exactly as cache_latents.main() / build_sft_cache.
    from diffusers import Flux2KleinPipeline
    pipe = Flux2KleinPipeline.from_pretrained(model, torch_dtype=torch.bfloat16)
    vae = pipe.vae.to("cuda", dtype=torch.bfloat16)
    vae.eval()
    bn_eps = getattr(vae.config, "batch_norm_eps", 1e-4)
    bn_mean = vae.bn.running_mean.to("cuda", dtype=torch.bfloat16)
    bn_std = (vae.bn.running_var + bn_eps).sqrt().to("cuda", dtype=torch.bfloat16)
    del pipe
    gc.collect()
    torch.cuda.empty_cache()

    n_done = 0
    with tempfile.TemporaryDirectory() as scratch:
        scratch = Path(scratch)
        for font in fonts:
            out_pt = out_cache_dir / f"{font}.pt"
            if out_pt.exists():
                continue
            fpairs = _pairs_for_font(pairs, font)
            # One decode per source atlas, shared across the winner and loser
            # composites (both draw from the same ~5 candidate files per font).
            _ac = {}
            win_atlas = assemble_winner_atlas(font, fpairs, candidate_dir,
                                              key_field="winner_key", _atlas_cache=_ac)
            los_atlas = assemble_winner_atlas(font, fpairs, candidate_dir,
                                              key_field="loser_key", _atlas_cache=_ac)
            # Computed once here (not re-derived at train time) and cached
            # alongside the atlases so it survives --resume the same way the
            # atlases do.
            font_weight = font_weight_for(fpairs)

            win_png = scratch / f"{font}__win.png"
            los_png = scratch / f"{font}__lose.png"
            Image.fromarray(win_atlas).save(win_png)
            Image.fromarray(los_atlas).save(los_png)

            win_packed, h, w = encode_and_cache(vae, bn_mean, bn_std, win_png, atlas_resolution, "cuda")
            los_packed, _, _ = encode_and_cache(vae, bn_mean, bn_std, los_png, atlas_resolution, "cuda")
            # Atomic write: a crash mid-torch.save would otherwise leave a truncated
            # <font>.pt that the "out_pt.exists()" resume-skip check above treats as
            # complete, silently corrupting training. Write to a temp file in the SAME
            # directory (same filesystem => os.replace is an atomic rename) and only
            # then swap it into place.
            tmp_pt = out_cache_dir / f"{font}.pt.tmp"
            torch.save(
                {"winner": win_packed, "loser": los_packed, "h": h, "w": w,
                 "weight": font_weight},
                tmp_pt,
            )
            os.replace(tmp_pt, out_pt)
            win_png.unlink()
            los_png.unlink()
            n_done += 1

    return fonts


class DPOPairDataset(Dataset):
    """One item per font: (winner_latents, loser_latents, reference_latents,
    font_weight).

    winner/loser come from the pre-built pair cache; the reference latents are
    reused verbatim from the base cache's references/<font>.pt (same reference
    image the glyph checkpoint was trained with). Fonts whose reference latent is
    missing are skipped (can't condition without it). ``font_weight`` is the
    per-font DPO scalar computed by build_pair_cache() (mean of pref_pairs.json's
    per-cell "weight"); a pair-cache entry written before this field existed
    defaults to 1.0 (no up-weighting, i.e. unchanged behavior).
    """

    def __init__(self, pair_cache_dir, ref_cache_dir):
        pair_cache_dir = Path(pair_cache_dir)
        ref_cache_dir = Path(ref_cache_dir)
        self.items = []
        missing = 0
        for pt in sorted(pair_cache_dir.glob("*.pt")):
            ref_pt = ref_cache_dir / pt.name
            if ref_pt.exists():
                self.items.append((pt, ref_pt))
            else:
                missing += 1
        log.info(f"DPO dataset: {len(self.items)} font pairs from {pair_cache_dir}"
                 + (f" ({missing} skipped: no reference latent)" if missing else ""))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        pair_pt, ref_pt = self.items[idx]
        d = torch.load(pair_pt, map_location="cpu", weights_only=True)
        r = torch.load(ref_pt, map_location="cpu", weights_only=True)
        font_weight = torch.tensor(float(d.get("weight", 1.0)))
        return d["winner"], d["loser"], r["latents"], font_weight


def collate_dpo(batch):
    return (
        torch.stack([b[0] for b in batch]),  # winner (bsz, atlas_seq, C)
        torch.stack([b[1] for b in batch]),  # loser  (bsz, atlas_seq, C)
        torch.stack([b[2] for b in batch]),  # reference (bsz, ref_seq, C)
        torch.stack([b[3] for b in batch]),  # font_weight (bsz,)
    )


# ===========================================================================
# Model setup (mirrors train_lora_kg.main; adds the frozen reference adapter)
# ===========================================================================

def _is_under(path, parent):
    try:
        return Path(parent).resolve() in Path(path).resolve().parents \
            or Path(path).resolve() == Path(parent).resolve()
    except Exception:
        return False


def _freeze_adapter(transformer, adapter_name):
    """Hard-freeze every parameter belonging to ``adapter_name`` (LoRA layers +
    modules_to_save copies). set_adapter() also toggles requires_grad, but this
    guarantees the reference never receives grads even if the active adapter is
    switched, and keeps it out of the optimizer's param list."""
    tag = f".{adapter_name}."
    n = 0
    for name, p in transformer.named_parameters():
        if tag in name or name.endswith(f".{adapter_name}"):
            p.requires_grad_(False)
            n += 1
    return n


def build_transformer(args):
    """Load + quantize the transformer, expand x_embedder, attach the trainable
    'default' policy adapter and the frozen 'reference' adapter (both init from
    glyph@5000), and cache the text embeddings. Returns
    (transformer, cached_prompt_embeds, cached_text_ids)."""
    from diffusers import Flux2KleinPipeline
    from optimum.quanto import quantize, qint8, freeze
    from peft import LoraConfig, get_peft_model, set_peft_model_state_dict
    from safetensors.torch import load_file

    log.info("Loading pipeline...")
    pipe = Flux2KleinPipeline.from_pretrained(args.model, torch_dtype=torch.bfloat16)
    transformer = pipe.transformer

    # --- cache text embeddings, free text encoder + vae (same prompt as glyph) ---
    log.info("Caching text embeddings...")
    # Single source of truth -- this MUST match what train_lora_kg.py trained
    # with, or DPO conditions on text the policy never saw. Guarded by
    # tests/test_prompt_parity.py. See research/2026-07-28-reference-char-mismatch.md.
    from atlas_constants import TRAINED_SHORT_PROMPT
    prompt = TRAINED_SHORT_PROMPT
    pipe.text_encoder.to("cuda")
    with torch.no_grad():
        cached_prompt_embeds, cached_text_ids = pipe.encode_prompt(prompt=prompt)
    cached_prompt_embeds = cached_prompt_embeds.cpu()
    cached_text_ids = cached_text_ids.cpu()
    pipe.text_encoder.to("cpu")
    del pipe.text_encoder, pipe.tokenizer, pipe.vae, pipe
    gc.collect()
    torch.cuda.empty_cache()

    # --- quantize, then expand x_embedder 128->256 (channel-concat template) ---
    _old_xemb_w = transformer.x_embedder.weight.data.clone()  # (inner_dim, 128)
    log.info("Quantizing transformer to INT8...")
    quantize(transformer, weights=qint8)
    freeze(transformer)
    inner = _old_xemb_w.shape[0]
    new_xemb = torch.nn.Linear(256, inner, bias=False)
    with torch.no_grad():
        new_xemb.weight.zero_()
        new_xemb.weight[:, :128].copy_(_old_xemb_w)
    transformer.x_embedder = new_xemb.to("cuda", dtype=torch.bfloat16)
    log.info("  x_embedder expanded 128->256 (channel-concat glyph conditioning; new channels=0)")

    # --- LoRA config: identical coverage to train_lora_kg (rank 32 for glyph@5000) ---
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
        modules_to_save=["x_embedder"],
    )
    transformer = get_peft_model(transformer, lora_config)  # creates adapter "default"

    # --- init the POLICY ("default") weights: from the DPO resume ckpt when
    #     resuming this run, else from glyph@5000 (fresh start). ---
    resume_is_dpo = bool(args.resume) and _is_under(args.resume, args.output_dir)
    policy_init = args.resume if resume_is_dpo else args.glyph_ckpt
    policy_adapter_file = Path(policy_init) / "adapter_model.safetensors"
    if policy_adapter_file.exists():
        log.info(f"Init policy adapter 'default' from {policy_init}")
        set_peft_model_state_dict(transformer, load_file(str(policy_adapter_file)), adapter_name="default")
    else:
        log.warning(f"No adapter_model.safetensors at {policy_init} — 'default' keeps fresh LoRA init")

    # --- REFERENCE adapter: a SECOND frozen PEFT adapter, ALWAYS glyph@5000.
    #     (NOT disable_adapter(): that would give base FLUX, the wrong reference.) ---
    log.info(f"Loading frozen reference adapter 'reference' from {args.glyph_ckpt}")
    transformer.load_adapter(args.glyph_ckpt, adapter_name="reference")
    n_ref = _freeze_adapter(transformer, "reference")
    log.info(f"  reference adapter frozen ({n_ref} params, requires_grad=False)")

    # Policy is the active/trainable adapter for optimizer construction + forwards.
    transformer.set_adapter("default")

    if args.grad_checkpointing:
        transformer.enable_gradient_checkpointing()
    else:
        log.info("  gradient checkpointing OFF (faster; uses more VRAM)")
    transformer.to("cuda", dtype=torch.bfloat16)
    transformer.train()
    transformer.print_trainable_parameters()
    return transformer, cached_prompt_embeds, cached_text_ids


# ===========================================================================
# Forward helpers (shared noised construction for policy + reference)
# ===========================================================================

def _build_hidden_states(noisy_atlas, ref_latents, template_channels, bsz):
    """Channel-concat the template into the atlas input (256ch), zero-pad the
    reference channels, concat atlas+ref along the sequence — identical to
    train_lora_kg's use_template forward. ``template_channels`` is either the real
    (1, atlas_seq, 128) template or a zeros tensor of that shape (template-dropout).
    """
    t_lat = template_channels.expand(bsz, -1, -1)
    atlas_in = torch.cat([noisy_atlas, t_lat], dim=-1)                      # (bsz, atlas_seq, 256)
    ref_in = torch.cat([ref_latents, torch.zeros_like(ref_latents)], dim=-1)  # (bsz, ref_seq, 256)
    return torch.cat([atlas_in, ref_in], dim=1)                            # (bsz, atlas_seq+ref_seq, 256)


def _forward_atlas_pred(transformer, hidden_states, text_embeds, txt_ids, img_ids, sigmas, atlas_seq_len):
    """One transformer forward; returns the atlas-token velocity prediction
    (bsz, atlas_seq_len, C). The ACTIVE PEFT adapter (default/reference) selects
    which LoRA + x_embedder copy is used."""
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
    return model_pred[:, :atlas_seq_len, :]


# ===========================================================================
# Main
# ===========================================================================

def _build_arg_parser():
    p = argparse.ArgumentParser(description="Diffusion-DPO trainer for the glyph-cond FLUX.2 LoRA")
    p.add_argument("--pairs", default="dpo_data/pref_pairs.json")
    p.add_argument("--candidate-dir", default="dpo_data/candidates")
    p.add_argument("--pair-cache", default="dpo_data/pair_cache",
                   help="per-font (winner,loser) latent cache dir (built resumably before training)")
    p.add_argument("--ref-cache", default="dataset_v2/cache/references",
                   help="reference latents reused from the base cache (references/<font>.pt)")
    p.add_argument("--template-pt", default="dataset_v2/cache/template_disambig_mild.pt",
                   help="disambig template latents (the glyph checkpoint's template)")
    p.add_argument("--cache-meta", default="dataset_v2/cache/cache_meta.json")

    p.add_argument("--build-cache", action="store_true",
                   help="only build the per-font (winner,loser) pair cache (GPU/VAE), then exit")
    p.add_argument("--max-fonts", type=int, default=None,
                   help="cache/train on only the first N fonts (e.g. 5 for a smoke run)")

    p.add_argument("--output-dir", default="training_dpo_r32")
    p.add_argument("--model", default="black-forest-labs/FLUX.2-klein-base-9B")
    p.add_argument("--glyph-ckpt", default=GLYPH_CKPT_DEFAULT,
                   help="glyph-cond@5000 checkpoint: frozen reference adapter + fresh-start policy init")
    p.add_argument("--resume", default=None,
                   help="fresh start: glyph@5000 (policy init only). crash-recovery: a checkpoint UNDER "
                        "--output-dir (restores policy weights + optimizer + lr_scheduler + global_step).")

    p.add_argument("--steps", type=int, default=3000)
    p.add_argument("--rank", type=int, default=32)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--warmup-steps", type=int, default=100)
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--grad-accum", type=int, default=1)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--weight-decay", type=float, default=1e-5)
    p.add_argument("--max-grad-norm", type=float, default=1.0)
    p.add_argument("--num-train-timesteps", type=int, default=1000)
    p.add_argument("--beta", type=float, default=0.1, help="Diffusion-DPO temperature")
    p.add_argument("--template-dropout", type=float, default=0.1,
                   help="probability of zeroing the template channels for a step")

    p.add_argument("--grad-checkpointing", dest="grad_checkpointing", action="store_true", default=True)
    p.add_argument("--no-grad-checkpointing", dest="grad_checkpointing", action="store_false")
    p.add_argument("--checkpoint-every", type=int, default=100,
                   help="save every N steps (crash-safe; caps lost progress per interruption)")
    return p


def main(argv=None):
    args = _build_arg_parser().parse_args(argv)

    # ---- build-cache mode: encode per-font (winner,loser) latents, then exit ----
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s | %(message)s", datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    if args.build_cache:
        fonts = build_pair_cache(args.pairs, args.candidate_dir, args.pair_cache,
                                 model=args.model, max_fonts=args.max_fonts)
        log.info(f"pair cache ready: {len(fonts)} fonts -> {args.pair_cache}")
        return

    torch.manual_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "dpo_config.json", "w") as f:
        json.dump(vars(args), f, indent=2)

    # add a file handler now that the output dir exists
    logging.getLogger().addHandler(logging.FileHandler(str(output_dir / "dpo_train.log"), mode="a"))
    metrics = MetricsLogger(output_dir)

    log.info(f"GPU: {torch.cuda.get_device_name(0)}")
    log.info(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # ---- ensure the per-font pair cache exists (resumable) ----
    pair_cache = Path(args.pair_cache)
    if not pair_cache.exists() or not any(pair_cache.glob("*.pt")):
        log.info(f"No pair cache at {pair_cache} — building it (VAE encode)...")
        build_pair_cache(args.pairs, args.candidate_dir, args.pair_cache,
                         model=args.model, max_fonts=args.max_fonts)

    # ---- cache_meta geometry ----
    with open(args.cache_meta) as f:
        cache_meta = json.load(f)
    atlas_seq_len = cache_meta["atlas_seq_len"]
    atlas_h, atlas_w = cache_meta["atlas_spatial"]
    ref_h, ref_w = cache_meta["ref_spatial"]

    # ---- model: policy (trainable) + frozen reference adapter ----
    t0 = time.time()
    transformer, cached_prompt_embeds, cached_text_ids = build_transformer(args)
    log.info(f"Model ready in {time.time() - t0:.0f}s, VRAM: {torch.cuda.memory_allocated()/1024**3:.1f} GB")

    # ---- optimizer over ONLY the trainable policy ('default') params ----
    trainable_params = [p for p in transformer.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(
        trainable_params, lr=args.lr, weight_decay=args.weight_decay,
        betas=(0.9, 0.999), eps=1e-8,
    )

    def cosine_with_warmup(step):
        if step < args.warmup_steps:
            return step / max(args.warmup_steps, 1)
        progress = (step - args.warmup_steps) / max(args.steps - args.warmup_steps, 1)
        return 0.5 * (1.0 + math.cos(math.pi * progress))

    lr_scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=cosine_with_warmup)

    # ---- template (disambig) latents (channel-concat conditioning) ----
    tdata = torch.load(args.template_pt, map_location="cpu", weights_only=True)
    tmpl_latents = tdata["latents"].unsqueeze(0).to("cuda", dtype=torch.bfloat16)  # (1, atlas_seq, 128)
    log.info(f"  glyph template: {tuple(tmpl_latents.shape)} (channel-concat conditioning)")

    # ---- resume optimizer/lr/step ONLY when resuming a DPO checkpoint of THIS run ----
    global_step = 0
    resume_is_dpo = bool(args.resume) and _is_under(args.resume, args.output_dir)
    if resume_is_dpo:
        state_path = Path(args.resume) / "training_state.pt"
        if state_path.exists():
            state = torch.load(state_path, map_location="cpu", weights_only=True)
            opt_state = state["optimizer"]
            for param_state in opt_state.get("state", {}).values():
                for k, v in param_state.items():
                    if isinstance(v, torch.Tensor) and v.is_floating_point():
                        param_state[k] = v.to("cuda")
            optimizer.load_state_dict(opt_state)
            lr_scheduler.load_state_dict(state["lr_scheduler"])
            global_step = state["global_step"]
            log.info(f"Resumed DPO run at step {global_step} (from {args.resume})")
    elif args.resume:
        log.info(f"Fresh DPO run: policy initialised from {args.resume}; optimizer/step start at 0")

    # ---- position ids (same as train_lora_kg; template rides atlas channels) ----
    atlas_ids_t = prepare_latent_ids(atlas_h, atlas_w, "cuda", torch.bfloat16)
    ref_ids_t = prepare_ref_ids(ref_h, ref_w, "cuda", torch.bfloat16, scale=10)

    # ---- dataset ----
    dataset = DPOPairDataset(args.pair_cache, args.ref_cache)
    if args.max_fonts is not None:
        dataset.items = dataset.items[:args.max_fonts]
    if len(dataset) == 0:
        log.info("ERROR: DPO dataset is empty (no pair-cache/reference matches). Aborting.")
        return
    dataloader = DataLoader(
        dataset, batch_size=args.batch_size, shuffle=True,
        num_workers=2, pin_memory=True, drop_last=True, collate_fn=collate_dpo,
    )

    log.info(f"\n{'='*60}")
    log.info(f"Diffusion-DPO: {args.steps} steps, beta={args.beta}, lr={args.lr}, rank={args.rank}")
    log.info(f"Dataset: {len(dataset)} font pairs, batch={args.batch_size}, accum={args.grad_accum}")
    log.info(f"Template-dropout p={args.template_dropout}; grad-checkpointing={args.grad_checkpointing}")
    log.info(f"Reference = frozen glyph@5000 adapter; policy = trainable adapter (both init glyph@5000)")
    log.info(f"{'='*60}\n")

    running_loss = 0.0
    running_gnorm = 0.0
    running_margin = 0.0
    log_interval = 10
    start_time = time.time()
    epoch = 0
    asserted = False

    while global_step < args.steps:
        epoch += 1
        for winner_lats, loser_lats, ref_lats, font_weights in dataloader:
            if global_step >= args.steps:
                break
            bsz = winner_lats.shape[0]

            try:
                winner_latents = winner_lats.to("cuda", dtype=torch.bfloat16)
                loser_latents = loser_lats.to("cuda", dtype=torch.bfloat16)
                ref_latents = ref_lats.to("cuda", dtype=torch.bfloat16)
                # Per-font REGRESSION_CHARS up-weighting (pref_pairs.json "weight",
                # cached per font by build_pair_cache): batch_size defaults to 1, so
                # this is exactly that font's weight; for bsz>1 it's the batch mean.
                # All-1 weights (the default/common case) => 1.0 => no-op.
                font_weight = font_weights.to("cuda", dtype=torch.float32).mean()

                a_ids = atlas_ids_t.expand(bsz, -1, -1)
                r_ids = ref_ids_t.expand(bsz, -1, -1)
                img_ids = torch.cat([a_ids, r_ids], dim=1)
                text_embeds = cached_prompt_embeds.expand(bsz, -1, -1).to("cuda", dtype=torch.bfloat16)
                txt_ids = cached_text_ids.expand(bsz, -1, -1).to("cuda", dtype=torch.bfloat16)

                # ── ONE shared (noise, timestep, sigma) sampled from the WINNER latents ──
                noise = torch.randn_like(winner_latents)
                timesteps = sample_timesteps(bsz, "cuda", args.num_train_timesteps)
                sigmas = compute_sigmas(timesteps, atlas_seq_len, args.num_train_timesteps)
                sigmas = sigmas.to(dtype=winner_latents.dtype)
                sigmas_bc = sigmas[:, None, None]

                # SAME noise + SAME sigmas → both noised atlases
                noisy_win = (1.0 - sigmas_bc) * winner_latents + sigmas_bc * noise
                noisy_lose = (1.0 - sigmas_bc) * loser_latents + sigmas_bc * noise
                target_win = noise - winner_latents
                target_lose = noise - loser_latents
                snr_weights = compute_snr_weights(sigmas)

                # ── template-dropout: zero template channels for the WHOLE step ──
                if torch.rand(()).item() < args.template_dropout:
                    template_channels = torch.zeros_like(tmpl_latents)
                else:
                    template_channels = tmpl_latents

                # Build the shared noised inputs ONCE; the SAME tensor object feeds
                # both the policy and the reference forward for each of win/lose.
                hs_win = _build_hidden_states(noisy_win, ref_latents, template_channels, bsz)
                hs_lose = _build_hidden_states(noisy_lose, ref_latents, template_channels, bsz)

                # ── REFERENCE forwards FIRST (frozen adapter, no_grad → detached constants).
                #    Doing reference before switching back to 'default' means that at
                #    backward() the policy ('default') params are the active, requires_grad
                #    ones — no mid-step requires_grad toggle can strand the policy graph. ──
                transformer.set_adapter("reference")
                with torch.no_grad():
                    if not asserted:
                        # Capture the winner input tensor's identity RIGHT AT the reference
                        # forward's call site (not just "hs_win is hs_win", which is a
                        # tautology regardless of what the code does) — this is what would
                        # actually FAIL if a future refactor rebuilt hs_win separately for
                        # the reference vs. policy forward.
                        ref_win_hs_id, ref_win_hs_ptr = id(hs_win), hs_win.data_ptr()
                    ref_pred_win = _forward_atlas_pred(
                        transformer, hs_win, text_embeds, txt_ids, img_ids, sigmas, atlas_seq_len)
                    ref_win_loss = per_sample_flow_loss(ref_pred_win, target_win, snr_weights)
                    ref_pred_lose = _forward_atlas_pred(
                        transformer, hs_lose, text_embeds, txt_ids, img_ids, sigmas, atlas_seq_len)
                    ref_lose_loss = per_sample_flow_loss(ref_pred_lose, target_lose, snr_weights)

                # ── POLICY forwards (trainable adapter, grad, grad-checkpointed) ──
                transformer.set_adapter("default")
                if not asserted:
                    # Same capture, at the policy forward's call site.
                    pol_win_hs_id, pol_win_hs_ptr = id(hs_win), hs_win.data_ptr()
                pol_pred_win = _forward_atlas_pred(
                    transformer, hs_win, text_embeds, txt_ids, img_ids, sigmas, atlas_seq_len)
                policy_win_loss = per_sample_flow_loss(pol_pred_win, target_win, snr_weights)
                pol_pred_lose = _forward_atlas_pred(
                    transformer, hs_lose, text_embeds, txt_ids, img_ids, sigmas, atlas_seq_len)
                policy_lose_loss = per_sample_flow_loss(pol_pred_lose, target_lose, snr_weights)

                # ── shared-input assertion (once): winner's policy & reference forwards
                #    consumed the IDENTICAL noised tensor, and win/lose share the SAME noise. ──
                if not asserted:
                    assert ref_win_hs_id == pol_win_hs_id and ref_win_hs_ptr == pol_win_hs_ptr, \
                        "winner hidden-states tensor differed between the reference and policy " \
                        "forward — hs_win must be built ONCE and reused (by object identity) for both"
                    # Reconstruct sigma*noise from each side in fp32. Both equal
                    # sigma*noise by construction (the single `noise` sampled above),
                    # differing ONLY by bf16 rounding residual (~1e-2, and winner!=loser
                    # so the residuals don't match); a genuinely different noise would
                    # differ by O(1). The loose atol distinguishes the two robustly —
                    # the default rtol/atol falsely fails on the bf16 residual.
                    win_noise = noisy_win.float() - (1.0 - sigmas_bc.float()) * winner_latents.float()
                    lose_noise = noisy_lose.float() - (1.0 - sigmas_bc.float()) * loser_latents.float()
                    assert torch.allclose(win_noise, lose_noise, atol=1e-1, rtol=1e-2), \
                        "winner/loser must be noised from the SAME sampled noise"
                    log.info("  [assert] winner policy+reference forwards shared the identical noised "
                             "input; winner/loser share one sampled noise. OK")
                    asserted = True

                loss = dpo_loss(policy_win_loss, policy_lose_loss, ref_win_loss, ref_lose_loss, args.beta)
                # Scale the resulting scalar DPO loss by this font's up-weight —
                # dpo_loss/per_sample_flow_loss themselves stay untouched (no
                # weight argument threaded into the margin/logsigmoid math).
                loss = loss * font_weight
                loss = loss / args.grad_accum
                loss.backward()

                if (global_step + 1) % args.grad_accum == 0:
                    gnorm = torch.nn.utils.clip_grad_norm_(trainable_params, args.max_grad_norm)
                    running_gnorm += gnorm.item()
                    optimizer.step()
                    lr_scheduler.step()
                    optimizer.zero_grad()

                running_loss += loss.item() * args.grad_accum
                running_margin += ((policy_win_loss - ref_win_loss)
                                   - (policy_lose_loss - ref_lose_loss)).mean().item()

            except torch.cuda.OutOfMemoryError:
                log.info(f"  OOM at step {global_step + 1}, skipping")
                optimizer.zero_grad(set_to_none=True)
                torch.cuda.empty_cache()
                gc.collect()
                continue

            global_step += 1

            if global_step % log_interval == 0:
                avg_loss = running_loss / log_interval
                avg_gnorm = running_gnorm / max(log_interval // args.grad_accum, 1)
                avg_margin = running_margin / log_interval
                elapsed = time.time() - start_time
                sps = global_step / elapsed
                cur_lr = lr_scheduler.get_last_lr()[0]
                vram_gb = torch.cuda.memory_allocated() / 1024**3
                peak_gb = torch.cuda.max_memory_allocated() / 1024**3
                log.info(
                    f"step {global_step:5d}/{args.steps} | dpo {avg_loss:.4f} | "
                    f"margin {avg_margin:+.4f} | lr {cur_lr:.2e} | gnorm {avg_gnorm:.2f} | "
                    f"{sps:.3f} it/s | VRAM {vram_gb:.1f}/{peak_gb:.1f} GB"
                )
                metrics.log(global_step, epoch, avg_loss, cur_lr, avg_gnorm, vram_gb, peak_gb, sps)
                running_loss = running_gnorm = running_margin = 0.0

            if global_step > 0 and args.checkpoint_every and global_step % args.checkpoint_every == 0:
                transformer.set_adapter("default")  # persist the POLICY adapter at root
                _save_checkpoint(transformer, optimizer, lr_scheduler, global_step, output_dir)

    transformer.set_adapter("default")
    _save_checkpoint(transformer, optimizer, lr_scheduler, global_step, output_dir, final=True)
    metrics.close()
    total_h = (time.time() - start_time) / 3600
    log.info(f"\nDPO complete. {total_h:.2f} h, {global_step} steps.")


if __name__ == "__main__":
    main()
