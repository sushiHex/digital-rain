"""Spike 5: confirm WHY distilled-9B runs at 27s/step (vs base 8s/step).

Hypothesis from Spike 4 (23.2GB resident): quanto's quantize() silently no-ops
on the distilled/KV checkpoints, leaving bf16 weights. Here we quantize both
base-9B (control, known to hit 8s/step) and distilled-9B and count how many
Linear layers actually became quanto QModules + the transformer byte footprint.
If base quantizes but distilled doesn't, root cause confirmed -> fix = force
quant or load BFL pre-fp8. No rendering.
"""
from collections import Counter

import torch


def inspect(model_id):
    from diffusers import Flux2KleinPipeline
    from optimum.quanto import quantize, qfloat8, freeze

    print(f"\n=== {model_id} ===", flush=True)
    pipe = Flux2KleinPipeline.from_pretrained(model_id, torch_dtype=torch.bfloat16)
    t = pipe.transformer

    def footprint_gb(mod):
        tot = 0
        for p in mod.parameters():
            try:
                tot += p.numel() * p.element_size()
            except Exception:
                tot += p.numel()  # quanto tensors may report element_size=1
        return tot / 1e9

    before = footprint_gb(t)
    quantize(t, weights=qfloat8)
    freeze(t)
    after = footprint_gb(t)

    linear_total = 0
    q_modules = 0
    module_types = Counter()
    weight_types = Counter()
    for name, m in t.named_modules():
        cls = type(m).__name__
        is_linear_like = hasattr(m, "weight") and getattr(m, "weight", None) is not None \
            and m.weight.ndim == 2
        if is_linear_like:
            linear_total += 1
            module_types[cls] += 1
            weight_types[type(m.weight).__name__] += 1
            if "Q" in cls or "quant" in cls.lower() or "Q" in type(m.weight).__name__:
                q_modules += 1

    print(f"  transformer footprint: before {before:.1f}GB -> after {after:.1f}GB", flush=True)
    print(f"  Linear-like modules: {linear_total}, quantized: {q_modules} "
          f"({100*q_modules/max(linear_total,1):.0f}%)", flush=True)
    print(f"  module types: {dict(module_types)}", flush=True)
    print(f"  weight types: {dict(weight_types)}", flush=True)
    verdict = "QUANTIZED OK" if q_modules > linear_total * 0.5 else "NOT QUANTIZED (no-op!)"
    print(f"  -> {verdict}", flush=True)
    del pipe, t
    torch.cuda.empty_cache()


if __name__ == "__main__":
    inspect("black-forest-labs/FLUX.2-klein-base-9B")     # control: should quantize
    inspect("black-forest-labs/FLUX.2-klein-9B")          # distilled: suspect
