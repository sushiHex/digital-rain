"""Enumerate all black-forest-labs FLUX.2 / klein models with size + gating +
local-cache state, so we can pick the right Stage-2 generator for a 24GB 3090.
"""
from huggingface_hub import HfApi, scan_cache_dir

api = HfApi()

print("=" * 80)
print("BLACK-FOREST-LABS MODELS (flux2 / klein / flux.2)")
print("=" * 80)
models = list(api.list_models(author="black-forest-labs", limit=200))
hits = []
for m in models:
    mid = m.id.lower()
    if "flux2" in mid or "flux.2" in mid or "klein" in mid or "flux-2" in mid:
        hits.append(m.id)

for repo in sorted(hits):
    try:
        info = api.model_info(repo, files_metadata=True)
        total = sum((f.size or 0) for f in info.siblings) / 1e9
        gated = getattr(info, "gated", "?")
        dl = getattr(info, "downloads", "?")
        print(f"{repo}")
        print(f"    gated={gated}  ~{total:.1f}GB  downloads={dl}")
    except Exception as e:
        print(f"{repo}  -- info failed: {type(e).__name__}: {str(e)[:80]}")

print()
print("=" * 80)
print("LOCAL CACHE (flux/klein)")
print("=" * 80)
try:
    cache = scan_cache_dir()
    for repo in cache.repos:
        if "flux" in repo.repo_id.lower() or "klein" in repo.repo_id.lower():
            print(f"  CACHED {repo.repo_id}  {repo.size_on_disk/1e9:.1f}GB")
except Exception as e:
    print(f"  cache scan failed: {e}")
