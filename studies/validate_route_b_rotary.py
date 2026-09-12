"""Validate the unfused-qkv rotary plumbing: same seed, fused vs unfused, no LoRA.
Correct rotary => images near-identical (low MAE). Broken rotary => garbage/large MAE.
Also reports the unfused s/step (the number the crashed gate run never produced)."""
import time
import numpy as np
import torch


def main():
    import nunchaku.models.transformers.transformer_flux2 as tfmod
    from nunchaku.models.transformers.transformer_flux2 import NunchakuFlux2Transformer2DModel
    from nunchaku.utils import get_precision
    from diffusers import Flux2KleinPipeline
    from huggingface_hub import hf_hub_download

    assert tfmod._FORCE_UNFUSED_QKV is False, "run WITHOUT the env flag; we toggle live"
    prec = get_precision()
    repo, name = "tonera/FLUX.2-klein-9B-Nunchaku", "FLUX.2-klein-9B-Nunchaku"
    tpath = hf_hub_download(repo, f"svdq-{prec}_r32-{name}.safetensors")
    tf = NunchakuFlux2Transformer2DModel.from_pretrained(tpath, torch_dtype=torch.bfloat16)
    pipe = Flux2KleinPipeline.from_pretrained(repo, torch_dtype=torch.bfloat16, transformer=tf)
    pipe.enable_model_cpu_offload()

    prompt = ("a technical font atlas grid of latin letters A to Z, "
              "clean black glyphs on a white background")
    steps = 8

    def render(seed):
        return pipe(prompt=prompt, height=1280, width=1280, num_inference_steps=steps,
                    generator=torch.Generator("cpu").manual_seed(seed)).images[0]

    # warm both code paths
    tfmod._FORCE_UNFUSED_QKV = False
    render(1000)

    img_fused = render(42)
    img_fused.save("route_b_fused.png")

    tfmod._FORCE_UNFUSED_QKV = True
    render(1001)  # warm unfused
    t0 = time.time()
    img_unfused = render(42)
    dt = time.time() - t0
    img_unfused.save("route_b_unfused.png")

    a = np.asarray(img_fused, dtype=np.float32)
    b = np.asarray(img_unfused, dtype=np.float32)
    mae = float(np.abs(a - b).mean())
    maxd = float(np.abs(a - b).max())
    print("\n=== ROTARY VALIDATION ===")
    print(f"  unfused: {dt:.1f}s  (~{dt/steps:.1f}s/step)")
    print(f"  MAE(fused, unfused) = {mae:.2f} / 255   maxdiff={maxd:.0f}")
    print(f"  verdict: {'ROTARY OK (near-identical)' if mae < 8 else 'BROKEN (large diff -> rotary wrong)'}")
    print("  saved route_b_fused.png / route_b_unfused.png for eyeball")


if __name__ == "__main__":
    main()
