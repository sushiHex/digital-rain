"""Categorize V3 LoRA target modules to scope Route B (which linears, fused-QKV?)."""
import re, collections
from huggingface_hub import hf_hub_download
from safetensors import safe_open

p = hf_hub_download("SnJake/Ref2Font", "Ref2FontV3.safetensors")
cnt = collections.Counter(); ranks = collections.Counter(); ex = collections.defaultdict(list)
TOKS = ["to_q", "to_k", "to_v", "to_out", "add_q_proj", "add_k_proj", "add_v_proj",
        "to_add_out", "ff.net", "linear_in", "linear_out", "proj_mlp", "proj_out",
        "img_mod", "txt_mod", "norm", "qkv", "mlp"]
with safe_open(p, "pt") as f:
    keys = list(f.keys())
    for k in keys:
        if k.endswith(".alpha"):
            continue
        for tok in TOKS:
            if tok in k:
                cnt[tok] += 1
                if not ex[tok]:
                    ex[tok].append(k)
                break
        else:
            cnt["<other>"] += 1
            if len(ex["<other>"]) < 4:
                ex["<other>"].append(k)
        if k.endswith("lora_down.weight") or k.endswith("lora_A.weight"):
            ranks[f.get_slice(k).get_shape()[0]] += 1
print("total tensors:", len(keys))
print("lora ranks (rows of lora_down/A):", dict(ranks))
print("target-token counts:")
for t, c in cnt.most_common():
    print(f"  {t:14s} {c:5d}   e.g. {ex[t][0] if ex[t] else ''}")
print("\n<other> examples:")
for e in ex["<other>"]:
    print("  ", e)
print("\nsample keys:")
for k in keys[:8]:
    print("  ", k)
