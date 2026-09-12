"""Run diffusers' kohya->diffusers FLUX converter on V3 and inspect how it
decomposes the single-block linear1/linear2 (the split we must replicate for
nunchaku). CPU-only."""
import re, collections
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file

p = hf_hub_download("SnJake/Ref2Font", "Ref2FontV3.safetensors")
sd = load_file(p)
print("raw V3 single-block-0 keys:")
for k in sorted(sd):
    if "single_blocks_0_" in k:
        print(f"  {k}  {tuple(sd[k].shape)}")

from diffusers.loaders.lora_conversion_utils import _convert_kohya_flux_lora_to_diffusers
try:
    out = _convert_kohya_flux_lora_to_diffusers(sd)
    conv = out[0] if isinstance(out, tuple) else out
    print(f"\nconverted: {len(conv)} tensors")
    # distinct module suffixes
    suf = collections.Counter()
    for k in conv:
        stem = re.sub(r"\.(lora_A|lora_B|alpha).*$", "", k)
        stem = re.sub(r"\.(\d+)\.", ".N.", stem)
        suf[stem] += 1
    print("distinct converted module stems:")
    for s, c in sorted(suf.items()):
        print(f"  {s:60s} {c}")
    print("\nconverted single_transformer_blocks.0 keys:")
    for k in sorted(conv):
        if "single_transformer_blocks.0." in k:
            print(f"  {k}  {tuple(conv[k].shape)}")
except Exception as e:
    import traceback; traceback.print_exc()
    print("converter failed:", e)
