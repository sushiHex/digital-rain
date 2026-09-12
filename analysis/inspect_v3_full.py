"""Full V3 target inventory: every distinct module suffix (block-index stripped),
so the Route B key map is exact, not guessed. CPU-only."""
import re, collections
from huggingface_hub import hf_hub_download
from safetensors import safe_open

p = hf_hub_download("SnJake/Ref2Font", "Ref2FontV3.safetensors")
suffixes = collections.Counter()
blocks = collections.defaultdict(set)   # prefix kind -> set of indices
with safe_open(p, "pt") as f:
    keys = list(f.keys())
    for k in keys:
        stem = k
        for suf in (".alpha", ".lora_down.weight", ".lora_up.weight", ".lora_A.weight", ".lora_B.weight"):
            if stem.endswith(suf):
                stem = stem[: -len(suf)]
                break
        # strip block index
        m = re.match(r"(lora_unet_)?(double|single)_blocks_(\d+)_(.+)$", stem)
        if m:
            kind, idx, suffix = m.group(2), int(m.group(3)), m.group(4)
            suffixes[f"{kind}:{suffix}"] += 1
            blocks[kind].add(idx)
        else:
            suffixes[f"OTHER:{stem}"] += 1

print("distinct (kind:suffix) -> tensor count:")
for s, c in sorted(suffixes.items()):
    print(f"  {s:40s} {c}")
for kind, idxs in blocks.items():
    print(f"\n{kind}_blocks: {len(idxs)} blocks, indices {min(idxs)}..{max(idxs)}")
