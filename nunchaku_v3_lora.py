"""Route B: apply the Ref2Font V3 LoRA to the INT4 FLUX.2-klein-9B Nunchaku
transformer at runtime, via parallel bf16 forward-hooks on the quantized linears.

V3 uses FLUX.1-style kohya names but klein-9B dimensions (hidden=4096, inner=4096):
  DOUBLE blocks (0..7): img/txt x {attn_qkv (fused), attn_proj, mlp_0, mlp_2}
  SINGLE blocks (0..23): linear1 = [qkv 12288 | mlp_fc1 24576] (split up rows, shared down)
                         linear2 = [out_proj in 4096 | mlp_fc2 in 12288] (split down cols, shared up)

The fused-qkv projections (to_qkv/to_added_qkv/qkv_proj) are consumed inside the
fused_qkv_norm_rottary kernel, which does NOT call the module's __call__ -- so a
forward-hook only fires when NUNCHAKU_FORCE_UNFUSED_QKV=1 routes qkv through the
torch path. Set that env var BEFORE importing nunchaku to apply qkv LoRA.

See docs/superpowers/plans/2026-06-02-route-b-nunchaku-v3-lora.md and
research/2026-06-02-3090-solutions.md.
"""
from __future__ import annotations

import dataclasses
import re

import torch
from safetensors.torch import load_file

# klein-9B single-block split geometry (asserted against the live model in
# _validate_geometry). inner_dim = 3*inner = 12288 for qkv; mlp_hidden = 12288.
_QKV_OUT = 12288          # 3 * inner_dim  -> qkv_proj rows of linear1.up
_INNER = 4096             # out_proj input cols of linear2.down (attn branch)

_DBL_MAP = {
    "img_attn_qkv": "attn.to_qkv",
    "txt_attn_qkv": "attn.to_added_qkv",
    "img_attn_proj": "attn.to_out.0",
    "txt_attn_proj": "attn.to_add_out",
    "img_mlp_0": "ff.linear_in",
    "img_mlp_2": "ff.linear_out",
    "txt_mlp_0": "ff_context.linear_in",
    "txt_mlp_2": "ff_context.linear_out",
}

_FUSED_QKV_SUFFIXES = ("attn.to_qkv", "attn.to_added_qkv", "qkv_proj")


@dataclasses.dataclass
class LoRASpec:
    module_path: str       # dotted path under the transformer
    A: torch.Tensor        # (rank, in_features)  -- lora_down
    B: torch.Tensor        # (out_features, rank) -- lora_up
    scale: float           # alpha / rank * strength
    is_qkv: bool           # target consumed by the fused qkv kernel


def _stems(sd: dict) -> list[str]:
    out = set()
    for k in sd:
        for suf in (".lora_down.weight", ".lora_up.weight", ".alpha"):
            if k.endswith(suf):
                out.add(k[: -len(suf)])
                break
    return sorted(out)


def _scale(sd: dict, stem: str, rank: int, strength: float) -> float:
    alpha = float(sd.get(f"{stem}.alpha", rank))
    return (alpha / rank) * strength


def load_v3_specs(path: str, strength: float = 1.0) -> list[LoRASpec]:
    """Parse V3 into per-nunchaku-module LoRASpecs (double direct, single split)."""
    sd = load_file(path)
    specs: list[LoRASpec] = []
    for stem in _stems(sd):
        m = re.match(r"lora_unet_double_blocks_(\d+)_(.+)$", stem)
        if m and m.group(2) in _DBL_MAP:
            i, suffix = m.group(1), m.group(2)
            A = sd[f"{stem}.lora_down.weight"].to(torch.bfloat16)
            B = sd[f"{stem}.lora_up.weight"].to(torch.bfloat16)
            path_i = f"transformer_blocks.{i}.{_DBL_MAP[suffix]}"
            specs.append(LoRASpec(path_i, A, B, _scale(sd, stem, A.shape[0], strength),
                                  is_qkv=path_i.endswith(_FUSED_QKV_SUFFIXES)))
            continue
        m = re.match(r"lora_unet_single_blocks_(\d+)_(linear1|linear2)$", stem)
        if m:
            i, which = m.group(1), m.group(2)
            A = sd[f"{stem}.lora_down.weight"].to(torch.bfloat16)
            B = sd[f"{stem}.lora_up.weight"].to(torch.bfloat16)
            sc = _scale(sd, stem, A.shape[0], strength)
            base = f"single_transformer_blocks.{i}.attn"
            if which == "linear1":
                # in=4096; up rows [0:12288]=qkv, [12288:]=mlp_fc1; shared down A
                specs.append(LoRASpec(f"{base}.qkv_proj", A, B[:_QKV_OUT, :].contiguous(),
                                      sc, is_qkv=True))
                specs.append(LoRASpec(f"{base}.mlp_fc1", A, B[_QKV_OUT:, :].contiguous(),
                                      sc, is_qkv=False))
            else:  # linear2: down cols [0:4096]=attn(out_proj), [4096:]=mlp_fc2; shared up B
                specs.append(LoRASpec(f"{base}.out_proj", A[:, :_INNER].contiguous(), B,
                                      sc, is_qkv=False))
                specs.append(LoRASpec(f"{base}.mlp_fc2", A[:, _INNER:].contiguous(), B,
                                      sc, is_qkv=False))
            continue
        raise ValueError(f"unmapped V3 stem: {stem}")
    return specs


def _get_module(root, dotted: str):
    m = root
    for part in dotted.split("."):
        m = m[int(part)] if part.isdigit() else getattr(m, part)
    return m


def _install_lora_hook(module, A: torch.Tensor, B: torch.Tensor, scale: float):
    # Fold the transpose AND the scale into install-time tensors so the per-step
    # hook (fires for every targeted linear, every block, every step) is just two
    # matmuls: lo = (x @ AdT) @ BdT. AdT:(in,rank) from Aᵀ; BdT:(rank,out) from (scale·B)ᵀ.
    # Hold them device-agnostic; under cpu-offload the module moves cpu<->cuda, so
    # resolve+cache to the INPUT's device on first use.
    dt = module.proj_down.dtype
    AdT = A.t().to(dt).contiguous()
    BdT = (scale * B.to(torch.float32)).t().to(dt).contiguous()
    cache: dict = {}

    def hook(_m, inp, out):
        x = inp[0]
        moved = cache.get(x.device)
        if moved is None:
            moved = (AdT.to(x.device), BdT.to(x.device))
            cache[x.device] = moved
        aT, bT = moved
        lo = (x.to(aT.dtype) @ aT) @ bT
        return out + lo.to(out.dtype)

    return module.register_forward_hook(hook)


def apply_specs(transformer, specs: list[LoRASpec]):
    import nunchaku.models.transformers.transformer_flux2 as tfmod
    needs_unfused = any(s.is_qkv for s in specs)
    if needs_unfused and not tfmod._FORCE_UNFUSED_QKV:
        raise RuntimeError(
            "qkv LoRA requires the unfused path: set NUNCHAKU_FORCE_UNFUSED_QKV=1 "
            "BEFORE importing nunchaku (or set tfmod._FORCE_UNFUSED_QKV=True before forward)."
        )
    handles = []
    for s in specs:
        mod = _get_module(transformer, s.module_path)
        # in/out sanity: A is (rank, in), B is (out, rank)
        assert s.A.shape[1] == mod.in_features, (s.module_path, s.A.shape, mod.in_features)
        assert s.B.shape[0] == mod.out_features, (s.module_path, s.B.shape, mod.out_features)
        handles.append(_install_lora_hook(mod, s.A, s.B, s.scale))
    return handles


def load_v3_into_nunchaku(transformer, v3_path: str | None = None, strength: float = 1.0):
    if v3_path is None:
        from huggingface_hub import hf_hub_download
        v3_path = hf_hub_download("SnJake/Ref2Font", "Ref2FontV3.safetensors")
    specs = load_v3_specs(v3_path, strength)
    handles = apply_specs(transformer, specs)
    return {"applied": len(specs), "handles": handles}


# ---- product wiring: a generate_fn for the cleanup pipeline ----

V3_PROMPT = ('A technical font atlas grid of the Latin charset: '
             '"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
             '0123456789!?.,;:-\"&". The style is strictly derived from '
             'the reference image "Aa".')

_PIPE = None
_PIPE_STRENGTH = None


def get_int4_v3_pipe(strength: float = 1.0):
    """Load (once) the INT4 FLUX.2-klein-9B pipe with V3 applied via Route B.
    Forces the unfused-qkv path at runtime so the qkv LoRA hooks fire.
    Strength is process-level (the singleton is built once); requesting a
    different strength after the pipe exists is an error — restart to change."""
    global _PIPE, _PIPE_STRENGTH
    if _PIPE is not None:
        if strength != _PIPE_STRENGTH:
            raise RuntimeError(
                f"INT4+V3 pipe already built at strength={_PIPE_STRENGTH}; "
                f"requested {strength}. Strength is process-level — restart to change."
            )
        return _PIPE
    import nunchaku.models.transformers.transformer_flux2 as tfmod
    tfmod._FORCE_UNFUSED_QKV = True  # forwards read this global at call time
    from diffusers import Flux2KleinPipeline
    tf = _load_transformer()
    pipe = Flux2KleinPipeline.from_pretrained(
        "tonera/FLUX.2-klein-9B-Nunchaku", torch_dtype=torch.bfloat16, transformer=tf)
    pipe.enable_model_cpu_offload()
    load_v3_into_nunchaku(pipe.transformer, strength=strength)
    _PIPE = pipe
    _PIPE_STRENGTH = strength
    return _PIPE


_PROMPT_EMBEDS = None


def _cached_prompt_embeds(pipe):
    """Encode the FIXED V3 prompt once and reuse forever. Saves ~12s/generation
    (the encode + the 24B-encoder load/offload swap) — the margin that takes a
    3-step render under 60s. Cached at module level since the prompt never changes."""
    global _PROMPT_EMBEDS
    if _PROMPT_EMBEDS is None:
        enc = pipe.encode_prompt(V3_PROMPT, device="cuda")
        _PROMPT_EMBEDS = (enc[0] if isinstance(enc, (tuple, list)) else enc).to("cuda")
    return _PROMPT_EMBEDS


def build_nunchaku_generate_fn(reference, strength: float = 1.0, steps: int = 4,
                               height: int = 1280, width: int = 1280):
    """Return generate_fn(seed) -> np.ndarray (V3-layout RGB atlas), matching the
    cleanup pipeline's run_cleanup(generate_fn=...) contract. `reference` is a PIL
    image (e.g. the per-font "Aa" reference from render_aa_reference). Uses cached
    prompt embeds (the prompt is fixed) so the text encoder runs at most once."""
    import numpy as np
    pipe = get_int4_v3_pipe(strength)
    embeds = _cached_prompt_embeds(pipe)
    ref = reference.convert("RGB")

    def generate_fn(seed: int):
        img = pipe(prompt_embeds=embeds, image=ref, height=height, width=width,
                   num_inference_steps=steps,
                   generator=torch.Generator("cpu").manual_seed(seed)).images[0]
        return np.asarray(img.convert("RGB"))

    return generate_fn


# ---- debug / one-off helpers ----

def _v3_path() -> str:
    from huggingface_hub import hf_hub_download
    return hf_hub_download("SnJake/Ref2Font", "Ref2FontV3.safetensors")


def _load_transformer():
    from nunchaku.models.transformers.transformer_flux2 import NunchakuFlux2Transformer2DModel
    from nunchaku.utils import get_precision
    from huggingface_hub import hf_hub_download
    prec = get_precision()
    repo, name = "tonera/FLUX.2-klein-9B-Nunchaku", "FLUX.2-klein-9B-Nunchaku"
    tpath = hf_hub_download(repo, f"svdq-{prec}_r32-{name}.safetensors")
    return NunchakuFlux2Transformer2DModel.from_pretrained(tpath, torch_dtype=torch.bfloat16)


def _validate_geometry():
    """Load the model and assert every spec's module exists with matching dims."""
    tf = _load_transformer()
    specs = load_v3_specs(_v3_path())
    by_path = {}
    for s in specs:
        mod = _get_module(tf, s.module_path)
        ok = s.A.shape[1] == mod.in_features and s.B.shape[0] == mod.out_features
        by_path[s.module_path] = (tuple(s.A.shape), tuple(s.B.shape),
                                   mod.in_features, mod.out_features, ok)
    bad = {k: v for k, v in by_path.items() if not v[-1]}
    print(f"specs: {len(specs)}  modules matched: {sum(v[-1] for v in by_path.values())}/{len(by_path)}")
    for k in sorted(by_path)[:12]:
        print(f"  {k:48s} A{by_path[k][0]} B{by_path[k][1]} in={by_path[k][2]} out={by_path[k][3]} ok={by_path[k][4]}")
    if bad:
        print("MISMATCHES:")
        for k, v in bad.items():
            print(f"  {k}: {v}")
    else:
        print("ALL GEOMETRY OK")


if __name__ == "__main__":
    _validate_geometry()
