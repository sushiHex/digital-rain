"""Inspect the Ref2Font V3 LoRA key format to plan a transformer-only merge."""
from collections import Counter
from huggingface_hub import hf_hub_download
from safetensors import safe_open

p = hf_hub_download("SnJake/Ref2Font", "Ref2FontV3.safetensors")
print("path:", p)
with safe_open(p, framework="pt") as f:
    keys = list(f.keys())
print("total keys:", len(keys))
print("\nfirst 12 keys:")
for k in keys[:12]:
    print("  ", k)
# prefix histogram (first 2 dotted segments)
pref = Counter(".".join(k.split(".")[:2]) for k in keys)
print("\ntop prefixes:")
for pre, n in pref.most_common(8):
    print(f"  {n:>5}  {pre}")
print("\nany 'transformer.' prefix:", any(k.startswith("transformer.") for k in keys))
print("any 'lora_' token:", any("lora" in k.lower() for k in keys))
