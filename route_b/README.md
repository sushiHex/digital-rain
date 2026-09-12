# Route B — runtime V3 LoRA on INT4 FLUX.2-klein-9B (Nunchaku)

Runs the Ref2Font **V3 LoRA on the INT4-quantized** FLUX.2-klein-9B Nunchaku
transformer on an RTX 3090: **≈ bf16+V3 quality at ~8 s/step (4-step ≈ 32s),
~4× faster than the quanto bf16 path.** See `research/2026-06-02-3090-solutions.md`
for the full investigation and validation numbers.

## How it works
- **LoRA injection = parallel bf16 forward-hooks** on each quantized `SVDQW4A4Linear`:
  `out += scale·(x @ Aᵀ) @ Bᵀ` (rel-err 0.03 vs reference). Implemented in
  `../nunchaku_v3_lora.py` (`load_v3_into_nunchaku`). Proj-injection into
  `proj_down/proj_up` is impossible (the kernel low-rank is rank-locked + fragment-packed).
- **QKV needs the unfused path.** `to_qkv`/`to_added_qkv`/`qkv_proj` are consumed
  *inside* the fused `fused_qkv_norm_rottary` kernel (it calls `proj.quantize`, not
  `__call__`), so a hook won't fire. Setting `NUNCHAKU_FORCE_UNFUSED_QKV=1` routes
  qkv through `proj(x)` + torch norm/rotary so the hook fires. This requires the
  **unpacked `(cos,sin)`** rotary (the kernel form is packed) — the patch plumbs it down.
- **Key map** (`nunchaku_v3_lora.py`): 8 double blocks map directly; 24 single
  blocks split FLUX.1-style fused `linear1`→`attn.{qkv_proj[:12288], mlp_fc1[12288:]}`
  (shared down) and `linear2`→`attn.{out_proj[:,:4096], mlp_fc2[:,4096:]}` (shared up).

## The vendored patch
The qkv-bypass edits live in a file **inside the gitignored venv**:
`.venv-nunchaku/Lib/site-packages/nunchaku/models/transformers/transformer_flux2.py`.
Base = nunchaku 1.2.1 + **tonera PR #926** (`feat/flux2-klein_nunchaku`) hot-patched in.

This dir preserves it:
- `route_b.patch` — unified diff vs the pristine PR #926 file (11 hunks: the
  `_FORCE_UNFUSED_QKV` flag, 4 gated fused-path conditions, the unfused double-block
  branch, and the unpacked-rotary selection/rewiring).
- `transformer_flux2.patched.py` — the full patched file (copy-apply fallback).
- `apply_route_b_patch.py` — restores the patch into a freshly-rebuilt venv.

### Re-apply after rebuilding the venv
```
./.venv-nunchaku/Scripts/python.exe route_b/apply_route_b_patch.py
```
or, if the upstream base is unchanged, `patch -p1 < route_b/route_b.patch` from the
nunchaku package root.

## Usage
```python
import os
os.environ["NUNCHAKU_FORCE_UNFUSED_QKV"] = "1"   # MUST precede nunchaku import
# ... build the INT4 Flux2KleinPipeline (see eval_route_b.py) ...
from nunchaku_v3_lora import load_v3_into_nunchaku
load_v3_into_nunchaku(pipe.transformer, strength=1.0)   # applies all 160 V3 specs
```

## Eval / repro scripts
- `benchmarks/benchmark_route_b.py` — fused vs unfused s/step.
- `studies/eval_route_b.py` — INT4 base vs INT4+V3 char-acc (hard fonts).
- `studies/eval_route_b_holdout.py` — broader best-of-N holdout eval.
- `studies/validate_route_b_rotary.py` — fused-vs-unfused equivalence (rotary correctness).
- `nunchaku_v3_lora.py` (repo root) `_validate_geometry()` — asserts all 160 specs match the model.

## Why the hooks exist at all (re-verified 2026-07-27)

Nunchaku exposes **no runtime-LoRA API** for the FLUX.2-klein quantized
transformer. `update_lora_params` / `set_lora_strength` are absent; the
`load_lora_adapter` / `fuse_lora` methods that *appear* available are
inherited from diffusers' `PeftAdapterMixin` and do not drive the quantized
kernels. The forward-hook injection documented above is the workaround, not a
convenience wrapper over a supported path.

Consequence for the speed track: sub-minute inference on our *own* trained
LoRA would need an **offline merge + SVDQuant**, not runtime loading. See
`research/2026-07-27-klein-licensing-and-4b-port.md`.
