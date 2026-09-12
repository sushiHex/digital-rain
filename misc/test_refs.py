"""Quick 10-step training test comparing reference character candidates."""

# repo root on sys.path so `python misc/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import torch, torch.nn.functional as F, numpy as np, time, math, gc
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

candidates = {"gK": "gK", "gR": "gR", "Rgo": "Rgo", "Aa": "Aa", "m": "m"}

def render_ref(font_path, chars, size=512):
    img = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(img)
    n = max(len(chars), 1)
    cell_w = size // n
    lo, hi = 10, 400
    while lo < hi:
        mid = (lo + hi + 1) // 2
        font = ImageFont.truetype(str(font_path), mid)
        fits = all(
            (font.getbbox(ch)[2] - font.getbbox(ch)[0]) <= cell_w * 0.8
            and (font.getbbox(ch)[3] - font.getbbox(ch)[1]) <= size * 0.45
            for ch in chars
        )
        if fits:
            lo = mid
        else:
            hi = mid - 1
    font = ImageFont.truetype(str(font_path), lo)
    ascent, _ = font.getmetrics()
    baseline_y = int(size * 0.6)
    for i, ch in enumerate(chars):
        cx = i * cell_w
        bbox = font.getbbox(ch)
        draw.text((cx + (cell_w - (bbox[2]-bbox[0]))//2 - bbox[0], baseline_y - ascent),
                  ch, fill=255, font=font)
    return img

def encode_img(vae, img, bn_mean, bn_std):
    arr = np.array(img.convert("RGB"), dtype=np.float32) / 255.0
    t = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0) * 2.0 - 1.0
    t = t.to("cuda", dtype=torch.bfloat16)
    with torch.no_grad():
        lat = vae.encode(t).latent_dist.mode()
        B, C, H, W = lat.shape
        lat = lat.view(B, C, H//2, 2, W//2, 2).permute(0,1,3,5,2,4).reshape(B, C*4, H//2, W//2)
        lat = (lat - bn_mean[None,:,None,None]) / bn_std[None,:,None,None]
        h, w = lat.shape[2], lat.shape[3]
        packed = lat.reshape(B, C*4, h*w).permute(0, 2, 1)
    return packed.squeeze(0).cpu().half(), h, w

def make_ids(h, w, t_val=0):
    t = torch.tensor([t_val], device="cuda", dtype=torch.bfloat16)
    hh = torch.arange(h, device="cuda", dtype=torch.bfloat16)
    ww = torch.arange(w, device="cuda", dtype=torch.bfloat16)
    l = torch.arange(1, device="cuda", dtype=torch.bfloat16)
    return torch.cartesian_prod(t, hh, ww, l).unsqueeze(0)

def compute_sigma(timesteps, seq_len):
    t = timesteps.float() / 1000
    t = t.clamp(1e-6, 1.0 - 1e-6)
    m = (1.15 - 0.5) / (4096 - 256)
    b = 0.5 - m * 256
    mu = seq_len * m + b
    exp_mu = math.exp(mu)
    return exp_mu / (exp_mu + (1.0 / t - 1.0))

def main():
    from build_dataset import find_fonts, render_atlas
    from diffusers import Flux2KleinPipeline
    from optimum.quanto import quantize, qint8, freeze
    from peft import LoraConfig, get_peft_model

    fonts = find_fonts(Path("google-fonts"), limit=50, one_per_family=True)
    print(f"Using {len(fonts)} fonts\n")

    # Load model
    pipe = Flux2KleinPipeline.from_pretrained(
        "black-forest-labs/FLUX.2-klein-base-9B", torch_dtype=torch.bfloat16
    )
    vae = pipe.vae.to("cuda", dtype=torch.bfloat16)
    vae.eval()

    bn_eps = getattr(vae.config, "batch_norm_eps", 1e-4)
    bn_mean = vae.bn.running_mean.to("cuda", dtype=torch.bfloat16)
    bn_std = (vae.bn.running_var + bn_eps).sqrt().to("cuda", dtype=torch.bfloat16)

    # Cache atlas latents (shared)
    print("Caching atlas latents...")
    atlas_cache = []
    for fp in fonts:
        atlas_img = render_atlas(fp)
        packed, _, _ = encode_img(vae, atlas_img, bn_mean, bn_std)
        atlas_cache.append(packed)
    atlas_seq_len = atlas_cache[0].shape[0]

    # Cache ref latents per candidate
    print("Caching reference latents...")
    ref_caches = {}
    for name, chars in candidates.items():
        refs = []
        rh = rw = 0
        for fp in fonts:
            ref_img = render_ref(fp, chars)
            packed, rh, rw = encode_img(vae, ref_img, bn_mean, bn_std)
            refs.append(packed)
        ref_caches[name] = (refs, rh, rw)
        print(f"  {name}: {refs[0].shape}")

    # Free VAE
    del vae
    gc.collect()
    torch.cuda.empty_cache()

    # Cache text embeddings
    print("Caching text embeddings...")
    pipe.text_encoder.to("cuda")
    with torch.no_grad():
        prompt_embeds, text_ids = pipe.encode_prompt(prompt="A font atlas grid.")
    prompt_embeds = prompt_embeds.cpu()
    text_ids = text_ids.cpu()
    pipe.text_encoder.to("cpu")
    del pipe.text_encoder, pipe.tokenizer
    gc.collect()
    torch.cuda.empty_cache()

    # Quantize transformer
    transformer = pipe.transformer
    quantize(transformer, weights=qint8)
    freeze(transformer)

    lora_target = (
        r".*\.attn\.to_[qkv]$|"
        r".*\.attn\.to_out\.0$|"
        r".*\.attn\.add_[qkv]_proj$|"
        r".*\.attn\.to_add_out$|"
        r".*\.ff(?:_context)?\.linear_(?:in|out)$|"
        r".*\.attn\.to_qkv_mlp_proj$|"
        r".*single_transformer_blocks\.\d+\.attn\.to_out$"
    )

    atlas_ids = make_ids(80, 80, t_val=0)

    # Run test for each candidate
    print(f"\n{'='*60}")
    print(f"10-step training test | {len(fonts)} fonts | 5 candidates")
    print(f"{'='*60}\n")

    results = {}
    for cand_name, chars in candidates.items():
        config = LoraConfig(r=16, lora_alpha=16, target_modules=lora_target, lora_dropout=0.0)
        model = get_peft_model(transformer, config)
        model.enable_gradient_checkpointing()
        model.to("cuda", dtype=torch.bfloat16)
        model.train()

        params = [p for p in model.parameters() if p.requires_grad]
        opt = torch.optim.AdamW(params, lr=1e-4, weight_decay=1e-5)

        refs, ref_h, ref_w = ref_caches[cand_name]
        ref_ids = make_ids(ref_h, ref_w, t_val=10)

        losses = []
        torch.manual_seed(42)
        t0 = time.time()

        for step in range(10):
            idx = step % len(fonts)
            atlas_lat = atlas_cache[idx].unsqueeze(0).to("cuda", dtype=torch.bfloat16)
            ref_lat = refs[idx].unsqueeze(0).to("cuda", dtype=torch.bfloat16)
            te = prompt_embeds.to("cuda", dtype=torch.bfloat16)
            ti = text_ids.to("cuda", dtype=torch.bfloat16)

            noise = torch.randn_like(atlas_lat)
            ts = torch.randint(1, 999, (1,), device="cuda")
            sigma = compute_sigma(ts, atlas_seq_len).to(dtype=atlas_lat.dtype)

            noisy = (1.0 - sigma[:, None, None]) * atlas_lat + sigma[:, None, None] * noise
            hidden = torch.cat([noisy, ref_lat], dim=1)
            img_ids = torch.cat([atlas_ids, ref_ids], dim=1)

            pred = model(
                hidden_states=hidden, encoder_hidden_states=te, timestep=sigma,
                img_ids=img_ids, txt_ids=ti, guidance=None, return_dict=False,
            )
            if isinstance(pred, tuple):
                pred = pred[0]

            atlas_pred = pred[:, :atlas_seq_len, :]
            target = noise - atlas_lat
            loss = F.mse_loss(atlas_pred.float(), target.float())
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            opt.zero_grad()
            losses.append(loss.item())

        elapsed = time.time() - t0

        avg_loss = sum(losses[-5:]) / 5
        results[cand_name] = {"final": avg_loss, "losses": losses, "time": elapsed}

        # Cleanup
        model.cpu()
        del model, opt, params
        gc.collect()
        torch.cuda.empty_cache()

        curve = " ".join(f"{l:.3f}" for l in losses)
        print(f"{cand_name:5s}: final={avg_loss:.4f} | {curve} | {elapsed:.0f}s")

    print(f"\n{'='*60}")
    print("RANKING (lower loss = reference carries more useful info)")
    print(f"{'='*60}")
    for name, r in sorted(results.items(), key=lambda x: x[1]["final"]):
        drop = r["losses"][0] - r["final"]
        print(f"  {name:5s}: final={r['final']:.4f}  convergence_speed={drop:.4f}")


if __name__ == "__main__":
    main()
