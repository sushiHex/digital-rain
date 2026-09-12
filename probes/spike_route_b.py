"""Route B spike: can we inject a LoRA into a FLUX.2 Nunchaku SVDQW4A4Linear by
APPENDING columns to proj_down/proj_up, and does the fused INT4 kernel apply it
correctly?

This is the make-or-break question for runtime V3-LoRA on the quantized FLUX.2
transformer. FLUX.2 fuses q/k/v into one SVDQW4A4Linear consumed by a fused
proj+norm+rotary kernel, so a Python parallel branch can't reach QKV — the LoRA
must live in proj_down/proj_up. SVDQuant already carries a low-rank branch there
(base rank 32); we test whether appending LoRA columns (rank 32 -> 48):
  (1) is accepted by the kernel at all (rank > 32), and
  (2) produces the intended delta  scale * x @ A.T @ B.T,
and whether the low-rank input space is RAW x or SMOOTHED (smooth_factor * x).

Method: isolate the LoRA contribution as a DELTA (y_with_lora - y_baseline) so
4-bit quantization error cancels and we test only the injected low-rank term.

Run in the 3.13 nunchaku env:
  .venv-nunchaku/Scripts/python.exe spike_route_b.py
"""
import time

import torch


def find_svdq_linears(module, prefix=""):
    from nunchaku.models.linear import SVDQW4A4Linear
    out = []
    for name, child in module.named_modules():
        if isinstance(child, SVDQW4A4Linear):
            out.append((name, child))
    return out


def test_layer(name, layer, rank_l=16, scale=0.7):
    dev = layer.proj_down.device
    dt = layer.proj_down.dtype
    in_f, out_f = layer.in_features, layer.out_features
    base_rank = layer.proj_down.shape[1]
    print(f"\n=== {name} ===")
    print(f"  in={in_f} out={out_f} base_rank={base_rank} dtype={dt} dev={dev} "
          f"has_smooth={hasattr(layer,'smooth_factor') and layer.smooth_factor is not None}")

    torch.manual_seed(0)
    x = torch.randn(1, 256, in_f, dtype=dt, device=dev) * 0.5

    with torch.no_grad():
        y0 = layer(x).float().clone()

    # Random LoRA: A (rank_l, in), B (out, rank_l) -- diffusers convention
    A = (torch.randn(rank_l, in_f, dtype=dt, device=dev) * 0.02)
    B = (torch.randn(out_f, rank_l, dtype=dt, device=dev) * 0.02)

    # Intended deltas in two candidate input spaces
    xf = x.float()
    d_raw = scale * (xf @ A.float().t()) @ B.float().t()
    if hasattr(layer, "smooth_factor") and layer.smooth_factor is not None:
        sm = layer.smooth_factor.float().view(1, 1, -1)
        d_smooth = scale * ((xf * sm) @ A.float().t()) @ B.float().t()
        d_invsmooth = scale * ((xf / sm) @ A.float().t()) @ B.float().t()
    else:
        d_smooth = d_invsmooth = None

    # Append columns: proj_down gets A.T (in, rank_l); proj_up gets scale*B (out, rank_l)
    new_down = torch.cat([layer.proj_down.data, A.t().contiguous()], dim=1).contiguous()
    new_up = torch.cat([layer.proj_up.data, (scale * B).contiguous()], dim=1).contiguous()

    orig_down, orig_up, orig_rank = layer.proj_down, layer.proj_up, layer.rank
    err = None
    for pad_to in (None, 16, 32):
        d = new_down; u = new_up
        if pad_to is not None:
            tot = d.shape[1]
            padded = ((tot + pad_to - 1) // pad_to) * pad_to
            if padded != tot:
                dpad = torch.zeros(in_f, padded - tot, dtype=dt, device=dev)
                upad = torch.zeros(out_f, padded - tot, dtype=dt, device=dev)
                d = torch.cat([d, dpad], dim=1).contiguous()
                u = torch.cat([u, upad], dim=1).contiguous()
        try:
            layer.proj_down = torch.nn.Parameter(d, requires_grad=False)
            layer.proj_up = torch.nn.Parameter(u, requires_grad=False)
            layer.rank = d.shape[1]
            with torch.no_grad():
                y1 = layer(x).float()
            delta = y1 - y0
            def rel(ref):
                return (delta - ref).norm().item() / (ref.norm().item() + 1e-9)
            r_raw = rel(d_raw)
            line = f"  pad_to={pad_to} new_rank={d.shape[1]} -> rel_err(raw)={r_raw:.4f}"
            if d_smooth is not None:
                line += f"  rel_err(smooth)={rel(d_smooth):.4f}  rel_err(invsmooth)={rel(d_invsmooth):.4f}"
            print(line)
            err = min(err, r_raw) if err is not None else r_raw
        except Exception as e:
            print(f"  pad_to={pad_to} new_rank={d.shape[1]} -> EXC {type(e).__name__}: {str(e)[:160]}")
        finally:
            layer.proj_down, layer.proj_up, layer.rank = orig_down, orig_up, orig_rank
    return err


def main():
    print("torch", torch.__version__, "cuda", torch.cuda.is_available(),
          torch.cuda.get_device_name(0) if torch.cuda.is_available() else "")
    from nunchaku.models.transformers.transformer_flux2 import NunchakuFlux2Transformer2DModel
    from nunchaku.utils import get_precision
    from huggingface_hub import hf_hub_download

    prec = get_precision()
    repo, name = "tonera/FLUX.2-klein-9B-Nunchaku", "FLUX.2-klein-9B-Nunchaku"
    weight = f"svdq-{prec}_r32-{name}.safetensors"
    print("precision:", prec, "weight:", weight)
    tpath = hf_hub_download(repo, weight)
    t0 = time.time()
    tf = NunchakuFlux2Transformer2DModel.from_pretrained(tpath, torch_dtype=torch.bfloat16)
    tf = tf.to("cuda")
    print(f"loaded transformer in {time.time()-t0:.0f}s")

    layers = find_svdq_linears(tf)
    print(f"\nfound {len(layers)} SVDQW4A4Linear layers")
    # Pick representative layers: a fused qkv, a to_out, an ff linear
    picks = {}
    for nm, ly in layers:
        if "to_qkv" in nm and "added" not in nm and "qkv" not in picks:
            picks["qkv"] = (nm, ly)
        elif nm.endswith("to_out.0") and "out" not in picks:
            picks["out"] = (nm, ly)
        elif ("linear_in" in nm or "mlp" in nm) and "ff" not in picks:
            picks["ff"] = (nm, ly)
    if not picks:  # fallback: just take the first 3
        for nm, ly in layers[:3]:
            picks[nm] = (nm, ly)

    for kind, (nm, ly) in picks.items():
        test_layer(f"[{kind}] {nm}", ly)

    print("\nVERDICT: rel_err(raw) ~0 on the lowest-pad row => proj-append injection "
          "works in RAW input space. Note which pad_to was required (kernel rank granularity).")


if __name__ == "__main__":
    main()
