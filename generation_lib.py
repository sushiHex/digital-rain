"""Reusable single-font FLUX.2-klein + LoRA generation path.

Factored out of eval_checkpoint.py's generate_phase_inprocess so
candidate_gen.py (and any other caller) can reuse the exact validated
pipe-setup and per-font inference steps. eval_checkpoint.py retains the
per-font loop, skip_existing, RAM/RSS abort guards, and logging around
these calls; this module owns only the one-time pipeline setup
(load_generation_pipe) and the single-atlas inference call
(generate_one_atlas).

Every step and its order here mirrors eval_checkpoint.py's
generate_phase_inprocess EXACTLY (as it existed before this refactor) so
generation remains byte-identical to the validated in-process eval path.
"""
import gc
import os

import torch
from PIL import Image

from atlas_constants import make_prompt, CANVAS


def _expand_x_embedder_to_256(transformer):
    """Replace x_embedder (Linear 128->inner) with a fresh bf16 Linear(256->inner)
    so PeftModel.from_pretrained's modules_to_save can load the trained 256-ch
    weights (the channel-concatenated glyph conditioning)."""
    inner = transformer.x_embedder.out_features
    transformer.x_embedder = torch.nn.Linear(256, inner, bias=False).to(torch.bfloat16)


def _install_glyph_channel_hook(transformer, template_pt, zero=False):
    """Forward-pre-hook on x_embedder: channel-concat the (grid-aligned) template
    onto the atlas tokens and zeros onto the rest, matching training. Atlas tokens
    are the first `na` (= template length, atlas-aligned). zero=True ablates the
    template (feeds zeros) to isolate template content vs added capacity."""
    td = torch.load(template_pt, map_location="cpu", weights_only=True)
    tmpl = td["latents"]            # (atlas_seq, 128)
    if zero:
        tmpl = torch.zeros_like(tmpl)
    na = tmpl.shape[0]

    def pre_hook(module, args):
        hs = args[0]                # (B, S, 128)
        B = hs.shape[0]
        t = tmpl.to(hs.device, hs.dtype).unsqueeze(0).expand(B, -1, -1)
        atlas_part = torch.cat([hs[:, :na], t], dim=-1)                       # (B, na, 256)
        rest = torch.cat([hs[:, na:], torch.zeros_like(hs[:, na:])], dim=-1)  # (B, S-na, 256)
        return (torch.cat([atlas_part, rest], dim=1),) + args[1:]

    target = next(m for n, m in transformer.named_modules() if n.endswith("x_embedder"))
    return target.register_forward_pre_hook(pre_hook)


def load_generation_pipe(
    checkpoint,
    *,
    use_template,
    template_pt,
    model="black-forest-labs/FLUX.2-klein-base-9B",
    reference_chars="Kg",
    template_zero=False,
    prompt_style="structured",
):
    """Load the FLUX.2-klein pipeline + LoRA checkpoint once, ready to generate.

    Step order (do not reorder — see eval_checkpoint.py history for why):
      1. Build the pipeline (bf16, stays on CPU except where noted below).
      2. Move ONLY the text encoder to CUDA and encode the positive prompt
         plus the empty negative prompt (FLUX.2-klein is not distilled, so
         classifier-free guidance at the default guidance_scale needs a
         negative embed on every pipe(...) call). Cache both embeddings,
         then permanently free the text encoder + tokenizer — the prompt
         is identical for every holdout font, so we only need this once.
      3. Quantize the transformer to INT8 (quanto qfloat8) and freeze it.
      4. If use_template: expand x_embedder 128->256 BEFORE loading the
         LoRA, so PeftModel.from_pretrained's modules_to_save can load the
         trained 256-channel glyph-conditioning weights.
      5. Load the LoRA via PeftModel.from_pretrained(adapter_name="default").
      6. Move transformer + VAE to CUDA.
      7. If use_template: install the glyph channel-concat forward-pre-hook
         AFTER the move to CUDA.

    Returns (pipe, prompt_embeds, neg_embeds) ready to pass into
    generate_one_atlas for each font.
    """
    from diffusers import Flux2KleinPipeline
    from optimum.quanto import quantize, qfloat8, freeze
    from peft import PeftModel

    pipe = Flux2KleinPipeline.from_pretrained(model, torch_dtype=torch.bfloat16)

    # "structured" = make_prompt() (what train_lora.py/the baseline trained on).
    # "trained-short" = the verbatim prompt train_lora_kg.py trained the
    # glyph model on. See research/2026-07-28-reference-char-mismatch.md.
    if prompt_style == "trained-short":
        from atlas_constants import TRAINED_SHORT_PROMPT
        prompt = TRAINED_SHORT_PROMPT
    elif prompt_style == "structured":
        prompt = make_prompt(reference_chars)
    else:
        raise ValueError(f"unknown prompt_style: {prompt_style!r}")
    # Encode BOTH the positive and the empty negative prompt once, with the
    # text encoder still alive on CUDA.
    pipe.text_encoder.to("cuda")
    with torch.no_grad():
        prompt_embeds, _ = pipe.encode_prompt(prompt=prompt, device="cuda")
        neg_embeds, _ = pipe.encode_prompt(prompt="", device="cuda")
    prompt_embeds = prompt_embeds.to("cuda")
    neg_embeds = neg_embeds.to("cuda")

    # Free the text encoder + tokenizer permanently — they account for
    # several GB and we don't need them again.
    pipe.text_encoder.to("cpu")
    del pipe.text_encoder
    pipe.text_encoder = None  # so check_inputs doesn't try to use it
    if hasattr(pipe, "tokenizer"):
        del pipe.tokenizer
        pipe.tokenizer = None
    gc.collect()
    torch.cuda.empty_cache()

    # Now quantize transformer to INT8 (in place), apply LoRA, move to GPU.
    quantize(pipe.transformer, weights=qfloat8)
    freeze(pipe.transformer)

    if use_template:
        _expand_x_embedder_to_256(pipe.transformer)

    pipe.transformer = PeftModel.from_pretrained(
        pipe.transformer, checkpoint, adapter_name="default"
    )

    pipe.transformer.to("cuda")
    pipe.vae.to("cuda")
    if use_template:
        _install_glyph_channel_hook(pipe.transformer, template_pt, zero=template_zero)

    return pipe, prompt_embeds, neg_embeds


def generate_one_atlas(
    pipe,
    prompt_embeds,
    neg_embeds,
    ref_path,
    out_path,
    *,
    steps=20,
    seed=42,
    canvas=CANVAS,
):
    """Generate a single atlas from one reference image and save it to disk.

    Mirrors eval_checkpoint.py's generate_phase_inprocess per-font inference
    body exactly: same reference preprocessing (RGB, LANCZOS-resize to
    512x512), same pipe(...) call kwargs, same CPU-seeded generator.
    """
    ref = Image.open(ref_path).convert("RGB")
    ref_small = ref.resize((512, 512), Image.LANCZOS)

    result = pipe(
        prompt_embeds=prompt_embeds,
        negative_prompt_embeds=neg_embeds,
        image=[ref_small],
        height=canvas, width=canvas,
        num_inference_steps=steps,
        generator=torch.Generator("cpu").manual_seed(seed),
    ).images[0]

    out_path = str(out_path)
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    result.save(out_path)
