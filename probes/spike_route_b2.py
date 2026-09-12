"""Route B spike #2 — pin down WHY column-append failed.

Test 1 (decisive): append ZERO columns (rank 32 -> 48 / 64) with all-zero values.
  If y is unchanged -> the kernel tolerates extra rank; the earlier failure was
  layout/packing of the VALUES. If y changes -> the kernel is rank-locked
  (reads proj with a stride/layout keyed to rank=32) and proj-injection is dead.

Test 2: is proj_down/proj_up stored PACKED? Try the converter's
  unpack_lowrank_weight / pack_lowrank_weight and check round-trip + shapes.

Test 3: parallel bf16 branch correctness on a non-fused linear (the fallback
  mechanism for to_out / FF): y_wrapped - y_base == scale*x@A.T@B.T ?
"""
import torch


def main():
    from nunchaku.models.transformers.transformer_flux2 import NunchakuFlux2Transformer2DModel
    from nunchaku.models.linear import SVDQW4A4Linear
    from nunchaku.utils import get_precision
    from huggingface_hub import hf_hub_download

    prec = get_precision()
    repo, name = "tonera/FLUX.2-klein-9B-Nunchaku", "FLUX.2-klein-9B-Nunchaku"
    tpath = hf_hub_download(repo, f"svdq-{prec}_r32-{name}.safetensors")
    tf = NunchakuFlux2Transformer2DModel.from_pretrained(tpath, torch_dtype=torch.bfloat16).to("cuda")

    layer = None
    lname = None
    for nm, ch in tf.named_modules():
        if isinstance(ch, SVDQW4A4Linear) and nm.endswith("to_out.0"):
            layer, lname = ch, nm
            break
    dev, dt = layer.proj_down.device, layer.proj_down.dtype
    in_f, out_f = layer.in_features, layer.out_features
    print(f"layer {lname}  in={in_f} out={out_f} rank={layer.rank} "
          f"proj_down.shape={tuple(layer.proj_down.shape)} proj_up.shape={tuple(layer.proj_up.shape)} dtype={dt}")

    torch.manual_seed(0)
    x = torch.randn(1, 256, in_f, dtype=dt, device=dev) * 0.5
    with torch.no_grad():
        y0 = layer(x).float().clone()

    orig_down, orig_up, orig_rank = layer.proj_down, layer.proj_up, layer.rank

    # ---- TEST 1: append ZERO columns ----
    print("\n[TEST 1] append zero columns (expect no-op if rank is flexible):")
    for extra in (16, 32):
        d = torch.cat([orig_down.data, torch.zeros(in_f, extra, dtype=dt, device=dev)], dim=1).contiguous()
        u = torch.cat([orig_up.data, torch.zeros(out_f, extra, dtype=dt, device=dev)], dim=1).contiguous()
        try:
            layer.proj_down = torch.nn.Parameter(d, requires_grad=False)
            layer.proj_up = torch.nn.Parameter(u, requires_grad=False)
            layer.rank = orig_rank + extra
            with torch.no_grad():
                y1 = layer(x).float()
            rel = (y1 - y0).norm().item() / (y0.norm().item() + 1e-9)
            print(f"  +{extra} zeros (rank {orig_rank}->{orig_rank+extra}): rel_change={rel:.5f}  "
                  f"{'NO-OP (good)' if rel < 1e-3 else 'CHANGED -> rank-locked'}")
        except Exception as e:
            print(f"  +{extra} zeros: EXC {type(e).__name__}: {str(e)[:140]}")
        finally:
            layer.proj_down, layer.proj_up, layer.rank = orig_down, orig_up, orig_rank

    # ---- TEST 2: is proj packed? ----
    print("\n[TEST 2] packing round-trip via converter helpers:")
    try:
        from nunchaku.lora.flux.nunchaku_converter import pack_lowrank_weight, unpack_lowrank_weight
        for tag, w, down in (("proj_down", orig_down.data, True), ("proj_up", orig_up.data, False)):
            try:
                un = unpack_lowrank_weight(w, down=down)
                re_p = pack_lowrank_weight(un, down=down)
                rt = (re_p.float() - w.float()).norm().item() / (w.float().norm().item() + 1e-9)
                changed = (un.float() - w.float()).norm().item() / (w.float().norm().item() + 1e-9)
                print(f"  {tag}: unpack ok shape {tuple(un.shape)}; pack(unpack)==orig rel={rt:.5f}; "
                      f"unpack-changed-values rel={changed:.5f} "
                      f"-> {'PACKED layout' if changed>1e-3 and rt<1e-3 else 'plain or N/A'}")
            except Exception as e:
                print(f"  {tag}: unpack/pack EXC {type(e).__name__}: {str(e)[:140]}")
    except Exception as e:
        print(f"  import EXC: {e}")

    # ---- TEST 3: parallel bf16 branch on this (non-fused) linear ----
    print("\n[TEST 3] parallel bf16 branch correctness (fallback for non-fused linears):")
    rank_l, scale = 16, 0.7
    A = torch.randn(rank_l, in_f, dtype=dt, device=dev) * 0.02
    B = torch.randn(out_f, rank_l, dtype=dt, device=dev) * 0.02
    base_fwd = layer.forward
    def wrapped(xx, output=None, _b=base_fwd, _A=A, _B=B, _s=scale):
        y = _b(xx)
        lo = _s * (xx.to(_A.dtype) @ _A.t()) @ _B.t()
        return y + lo.to(y.dtype)
    layer.forward = wrapped
    with torch.no_grad():
        y1 = layer(x).float()
    layer.forward = base_fwd
    d_raw = (scale * (x.float() @ A.float().t()) @ B.float().t())
    rel = ((y1 - y0) - d_raw).norm().item() / (d_raw.norm().item() + 1e-9)
    print(f"  parallel-branch rel_err vs scale*x@A.T@B.T = {rel:.5f}  "
          f"{'CORRECT' if rel < 0.05 else 'WRONG'}")


if __name__ == "__main__":
    main()
