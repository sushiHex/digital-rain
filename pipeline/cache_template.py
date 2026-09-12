"""Cache the font-independent glyph-template latent (atlas resolution, T=20 grid)
and add template_seq_len/template_spatial to an existing cache_meta.json. Reuses
cache_latents.encode_and_cache so the latent matches the atlas/ref encoding
exactly (same VAE, patchify, batchnorm). Does NOT touch already-cached latents."""

# repo root on sys.path so `python pipeline/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import gc
import json
from pathlib import Path

import torch

from cache_latents import encode_and_cache
from render_glyph_template import render_glyph_template


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset-dir", default="dataset_v2")
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("--model", default="black-forest-labs/FLUX.2-klein-base-9B")
    ap.add_argument("--atlas-resolution", type=int, default=None)
    ap.add_argument("--disambig", choices=["mild", "strong"], default=None,
                     help="Cache a disambiguated template variant to "
                          "template_disambig_<variant>.pt instead of the "
                          "default template.pt. Never touches template.pt or "
                          "cache_meta.json's template_* fields when set.")
    args = ap.parse_args()

    cache_dir = Path(args.cache_dir) if args.cache_dir else Path(args.dataset_dir) / "cache"
    meta_path = cache_dir / "cache_meta.json"
    meta = json.load(open(meta_path))
    res = args.atlas_resolution or meta.get("atlas_resolution", 1280)
    print(f"caching template at atlas resolution {res} -> {res // 16}x{res // 16} latent")

    from diffusers import Flux2KleinPipeline
    pipe = Flux2KleinPipeline.from_pretrained(args.model, torch_dtype=torch.bfloat16)
    vae = pipe.vae.to("cuda", dtype=torch.bfloat16)
    vae.eval()
    bn_eps = getattr(vae.config, "batch_norm_eps", 1e-4)
    bn_mean = vae.bn.running_mean.to("cuda", dtype=torch.bfloat16)
    bn_std = (vae.bn.running_var + bn_eps).sqrt().to("cuda", dtype=torch.bfloat16)
    del pipe.transformer, pipe.text_encoder, pipe.tokenizer, pipe
    gc.collect()
    torch.cuda.empty_cache()

    if args.disambig:
        tag = f"disambig_{args.disambig}"
        tmpl_png = cache_dir / f"glyph_template_{tag}.png"
        out_pt = cache_dir / f"template_{tag}.pt"
    else:
        tmpl_png = cache_dir / "glyph_template.png"
        out_pt = cache_dir / "template.pt"

    render_glyph_template(size=res, disambig=args.disambig).save(tmpl_png)
    packed, th, tw = encode_and_cache(vae, bn_mean, bn_std, tmpl_png, res, "cuda")
    torch.save({"latents": packed, "h": th, "w": tw}, out_pt)
    print(f"template latent {tuple(packed.shape)} ({th}x{tw}) -> {out_pt}")

    if args.disambig:
        # Disambig variants share the base template's resolution, so
        # template_seq_len/template_spatial in cache_meta.json are unchanged
        # and identical for this variant -- do not touch template.pt or meta.
        assert int(packed.shape[0]) == meta.get("template_seq_len", packed.shape[0]), (
            "disambig variant seq_len does not match cache_meta.json's "
            "template_seq_len -- resolution mismatch vs the original template.pt"
        )
    else:
        meta["template_seq_len"] = int(packed.shape[0])
        meta["template_spatial"] = [int(th), int(tw)]
        json.dump(meta, open(meta_path, "w"), indent=2)
        print(f"meta updated -> {meta_path}")


if __name__ == "__main__":
    main()
