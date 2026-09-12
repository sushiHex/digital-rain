"""Step 1 of the offline Nunchaku path: merge Ref2Font V3 into distilled
klein-9B's transformer (bf16) and save it, so it can be SVDQuant-quantized
with V3 baked in. Transformer-only to avoid loading FLUX.2's ~24B text encoder.
"""
import inspect
from pathlib import Path

import torch
from huggingface_hub import hf_hub_download
from diffusers import Flux2KleinPipeline, Flux2Transformer2DModel

MODEL = "black-forest-labs/FLUX.2-klein-9B"
OUT = Path("experiments/klein9b_v3_merged")


def main():
    v3 = hf_hub_download("SnJake/Ref2Font", "Ref2FontV3.safetensors")
    print("loading transformer (bf16)...", flush=True)
    t = Flux2Transformer2DModel.from_pretrained(
        MODEL, subfolder="transformer", torch_dtype=torch.bfloat16
    ).to("cuda")

    print("converting V3 kohya LoRA -> diffusers...", flush=True)
    res = Flux2KleinPipeline.lora_state_dict(v3)
    sd, alphas = res if isinstance(res, tuple) else (res, None)
    print(f"  converted: {len(sd)} keys; sample: {list(sd)[:2]}", flush=True)

    params = list(inspect.signature(Flux2KleinPipeline.load_lora_into_transformer).parameters)
    print("  load_lora_into_transformer params:", params, flush=True)
    kw = {"transformer": t, "adapter_name": "v3"}
    if "network_alphas" in params:
        kw["network_alphas"] = alphas
    Flux2KleinPipeline.load_lora_into_transformer(sd, **kw)
    print("  LoRA loaded into transformer", flush=True)

    t.fuse_lora(lora_scale=1.0) if "lora_scale" in inspect.signature(t.fuse_lora).parameters else t.fuse_lora()
    print("  fused", flush=True)
    try:
        t.unload_lora()
    except Exception:
        pass

    dest = OUT / "transformer"
    dest.mkdir(parents=True, exist_ok=True)
    t.save_pretrained(dest)
    print(f"SAVED merged transformer -> {dest}", flush=True)


if __name__ == "__main__":
    main()
