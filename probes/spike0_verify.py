"""Verify the FLUX.2-klein model variants exist and report sizes / cache state.

Run before Spike 1 so we don't build a script around a hallucinated repo ID
or trigger a surprise ~18GB download blindly.
"""
from huggingface_hub import HfApi, scan_cache_dir

CANDIDATES = [
    "black-forest-labs/FLUX.2-klein-base-9B",   # what we currently use (50-step)
    "black-forest-labs/FLUX.2-klein-9B",         # claimed distilled (4-step)
    "black-forest-labs/FLUX.2-klein-9b-kv",      # claimed KV variant
]

api = HfApi()

print("=" * 70)
print("REMOTE MODEL CHECK")
print("=" * 70)
for repo in CANDIDATES:
    try:
        info = api.model_info(repo, files_metadata=True)
        total = sum((f.size or 0) for f in info.siblings) / 1e9
        gated = getattr(info, "gated", "?")
        print(f"OK    {repo}")
        print(f"        gated={gated}  ~{total:.1f} GB across {len(info.siblings)} files")
    except Exception as e:
        print(f"FAIL  {repo}: {type(e).__name__}: {str(e)[:120]}")

print()
print("=" * 70)
print("LOCAL HF CACHE (flux/klein only)")
print("=" * 70)
try:
    cache = scan_cache_dir()
    found = False
    for repo in cache.repos:
        if "flux" in repo.repo_id.lower() or "klein" in repo.repo_id.lower():
            found = True
            print(f"  {repo.repo_id}  {repo.size_on_disk / 1e9:.1f} GB  ({repo.repo_path})")
    if not found:
        print("  (no flux/klein repos cached)")
    print(f"\n  Total HF cache size: {cache.size_on_disk / 1e9:.1f} GB")
except Exception as e:
    print(f"  cache scan failed: {type(e).__name__}: {e}")
