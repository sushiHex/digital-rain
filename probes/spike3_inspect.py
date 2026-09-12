"""Inspect how FLUX.2-klein-9b-kv-fp8 is packaged so we load it correctly
(pre-quantized fp8 -- do NOT re-quantize) and know if torchao is required.
"""
from huggingface_hub import HfApi

print("=== dependency check ===")
for mod in ["torchao", "optimum.quanto"]:
    try:
        m = __import__(mod, fromlist=["__version__"])
        print(f"  {mod}: available ({getattr(m, '__version__', '?')})")
    except Exception as e:
        print(f"  {mod}: NOT available ({type(e).__name__})")

api = HfApi()
for repo in ["black-forest-labs/FLUX.2-klein-9b-kv-fp8",
             "black-forest-labs/FLUX.2-klein-9b-fp8"]:
    print(f"\n=== {repo} ===")
    try:
        info = api.model_info(repo, files_metadata=True)
        print(f"  gated={getattr(info,'gated','?')}")
        for f in sorted(info.siblings, key=lambda s: -(s.size or 0))[:25]:
            print(f"    {(f.size or 0)/1e9:7.3f}GB  {f.rfilename}")
        # surface any quantization hints from config files
        for f in info.siblings:
            if f.rfilename.endswith(("config.json", "model_index.json")):
                pass
    except Exception as e:
        print(f"  info failed: {type(e).__name__}: {str(e)[:120]}")
