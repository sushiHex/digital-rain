"""Stage A: build a CachedLatentDataset-compatible SFT cache from cross-model
winner atlases.

Task 6 of the fidelity-push plan
(docs/superpowers/plans/2026-07-19-fidelity-push-gt-guided-preference.md).

Consumes `dpo_data/sft_targets.json` (select_preferences.py's output) and the
winner candidate PNGs candidate_gen.py wrote under
`<candidate_dir>/<font>/<model>__seed<N>.png` (candidate_gen.candidate_path's
layout). A font's per-char winners can come from different models, but SFT
trains on whole-atlas targets, so for each font we assemble one composite
"winner atlas": start from that font's `glyph__seed0` render (untouched
cells keep the glyph-model look), then paste each sft_target's WINNER crop
over its cell using the grid geometry from atlas_constants. That composite
is then VAE-encoded into a cache train_lora_kg.CachedLatentDataset reads
unchanged.

`assemble_winner_atlas()` is pure numpy/PIL (CPU-only, unit tested in
tests/test_build_sft_cache.py). `build_cache()` additionally needs the VAE
(GPU) to encode -- it does not reimplement cache_latents.py's encode/pack
math; it calls cache_latents.encode_and_cache directly (via a scratch PNG of
the assembled atlas) so the on-disk .pt format -- patchify_latents,
pack_latents, the batch-norm normalize, and the final `.cpu().half()` --
is the literal same code path cache_latents.py uses for every other atlas,
not a parallel reimplementation that could drift.

Usage (GPU; not run by this task -- the controller runs it):
  python build_sft_cache.py --sft-targets dpo_data/sft_targets.json \
      --candidate-dir dpo_data/candidates --existing-cache dataset_v2/cache \
      --out-cache dpo_data/sft_cache
"""
import argparse
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from atlas_constants import CHARSET, GRID_COLS, CELL_W, CELL_H


def _cell_box(idx):
    row, col = idx // GRID_COLS, idx % GRID_COLS
    return col * CELL_W, row * CELL_H


def _char_to_index(ch):  # inverse of CHARSET
    return CHARSET.index(ch)


def assemble_winner_atlas(font, sft_targets, candidate_dir, key_field="winner_key",
                          _atlas_cache=None):
    """Composite per-font atlas: glyph__seed0 base + pasted cells from `key_field`.

    `sft_targets` is the full list from sft_targets.json / pref_pairs.json (or any
    subset); entries for other fonts are skipped. `key_field` selects which key to
    paste — "winner_key" (default, the SFT/DPO winner atlas) or "loser_key" (the
    DPO loser atlas). The key value is "font__model__seedN"
    (select_preferences._parse_key's format); the candidate PNG lives at
    candidate_gen.candidate_path's layout:
    `<candidate_dir>/<font>/<model>__seed<N>.png`.
    """
    cache = {} if _atlas_cache is None else _atlas_cache

    def load(key):
        # One decode per distinct source atlas, not per cell: a font has ~5
        # candidate atlases but up to 94 target cells naming them, so the
        # naive form re-decoded each 1280x1280 PNG ~18x.
        _, model, seed = key.rsplit("__", 2)
        path = f"{candidate_dir}/{font}/{model}__{seed}.png"
        if path not in cache:
            cache[path] = np.array(Image.open(path).convert("RGB"))
        return cache[path]

    base = load(f"{font}__glyph__seed0")  # canvas base: unpasted cells keep the glyph render
    out = base.copy()
    for t in sft_targets:
        if t["font"] != font:
            continue
        idx = _char_to_index(t["char"])
        x, y = _cell_box(idx)
        cell = load(t[key_field])
        out[y:y + CELL_H, x:x + CELL_W] = cell[y:y + CELL_H, x:x + CELL_W]
    return out


def _fonts_in(sft_targets):
    """Ordered, de-duplicated font list from an sft_targets list."""
    seen = []
    for t in sft_targets:
        if t["font"] not in seen:
            seen.append(t["font"])
    return seen


def build_cache(sft_targets_path, candidate_dir, existing_cache_dir, out_cache_dir,
                 model="black-forest-labs/FLUX.2-klein-base-9B", atlas_resolution=1280,
                 max_fonts=None):
    """Build the Stage-A SFT cache. Requires a GPU (VAE encode) -- the CPU test
    covers only assemble_winner_atlas(); this function is correct-by-construction
    against cache_latents.py (see module docstring) and is exercised by the
    controller's GPU smoke run, not by this task's test suite.

    - `<out_cache_dir>/atlases/<font>.pt`: one composite winner atlas per font,
      encoded via cache_latents.encode_and_cache -- same dict shape as every
      other atlas in the existing cache: {"latents": (6400,128) fp16, "h":80, "w":80}.
    - `<out_cache_dir>/references/*.pt`: copied verbatim from `existing_cache_dir`
      (same reference images / resolution as the base cache -- nothing to re-encode).
    - `<out_cache_dir>/cache_meta.json`: copied verbatim from `existing_cache_dir`
      (seq-len/spatial metadata is resolution-derived, not content-derived).
    - `<out_cache_dir>/template.pt`: copied from
      `<existing_cache_dir>/template_disambig_mild.pt` (Stage A keeps the
      disambig template the glyph checkpoint was trained/evaled with).
    """
    from cache_latents import encode_and_cache
    import torch

    sft_targets = json.loads(Path(sft_targets_path).read_text())
    existing_cache_dir = Path(existing_cache_dir)
    out_cache_dir = Path(out_cache_dir)
    atlas_out_dir = out_cache_dir / "atlases"
    ref_out_dir = out_cache_dir / "references"
    atlas_out_dir.mkdir(parents=True, exist_ok=True)
    ref_out_dir.mkdir(parents=True, exist_ok=True)

    # references/*.pt + cache_meta.json + template.pt: reused/copied verbatim.
    for ref_pt in (existing_cache_dir / "references").glob("*.pt"):
        shutil.copy2(ref_pt, ref_out_dir / ref_pt.name)
    shutil.copy2(existing_cache_dir / "cache_meta.json", out_cache_dir / "cache_meta.json")
    shutil.copy2(existing_cache_dir / "template_disambig_mild.pt", out_cache_dir / "template.pt")

    fonts = _fonts_in(sft_targets)
    if max_fonts is not None:
        fonts = fonts[:max_fonts]

    # Load VAE (mirrors cache_latents.main()'s load + bn_mean/bn_std extraction).
    from diffusers import Flux2KleinPipeline
    pipe = Flux2KleinPipeline.from_pretrained(model, torch_dtype=torch.bfloat16)
    vae = pipe.vae.to("cuda", dtype=torch.bfloat16)
    vae.eval()
    bn_eps = getattr(vae.config, "batch_norm_eps", 1e-4)
    bn_mean = vae.bn.running_mean.to("cuda", dtype=torch.bfloat16)
    bn_std = (vae.bn.running_var + bn_eps).sqrt().to("cuda", dtype=torch.bfloat16)
    del pipe
    import gc
    gc.collect()
    torch.cuda.empty_cache()

    with tempfile.TemporaryDirectory() as scratch:
        scratch = Path(scratch)
        for font in fonts:
            atlas_out = atlas_out_dir / f"{font}.pt"
            if atlas_out.exists():
                continue
            winner_atlas = assemble_winner_atlas(font, sft_targets, candidate_dir)
            scratch_png = scratch / f"{font}.png"
            Image.fromarray(winner_atlas).save(scratch_png)
            packed, h, w = encode_and_cache(vae, bn_mean, bn_std, scratch_png, atlas_resolution, "cuda")
            torch.save({"latents": packed, "h": h, "w": w}, atlas_out)
            scratch_png.unlink()

    return fonts


def _build_arg_parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sft-targets", default="dpo_data/sft_targets.json")
    ap.add_argument("--candidate-dir", default="dpo_data/candidates")
    ap.add_argument("--existing-cache", default="dataset_v2/cache")
    ap.add_argument("--out-cache", default="dpo_data/sft_cache")
    ap.add_argument("--model", default="black-forest-labs/FLUX.2-klein-base-9B")
    ap.add_argument("--max-fonts", type=int, default=None,
                     help="cache only the first N fonts (e.g. 5 for a training smoke run)")
    return ap


def main(argv=None):
    args = _build_arg_parser().parse_args(argv)
    fonts = build_cache(
        args.sft_targets, args.candidate_dir, args.existing_cache, args.out_cache,
        args.model, max_fonts=args.max_fonts,
    )
    print(f"cached {len(fonts)} winner atlases -> {args.out_cache}")


if __name__ == "__main__":
    main()
