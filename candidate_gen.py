"""Cross-model, N-seed, resumable candidate-atlas generation.

Generates candidate atlases per font from both the baseline (no-template)
and glyph+disambig checkpoints, plus N seeded glyph samples, into a
resumable cache under `<out-dir>/candidates/<font>/<model>__seed<seed>.png`.

Reuses the validated pipe-setup and per-font inference path factored out
into generation_lib.py (load_generation_pipe / generate_one_atlas) so
generation here is byte-identical to eval_checkpoint.py's in-process path.

Two ways to supply the font list (mutually exclusive, exactly one required):
  --fonts-manifest <path>   Holdout-style manifest.json: top-level
                            {"fonts": [{"name": ..., "reference": <relpath>}, ...]}.
                            Reference paths are relative to the manifest's
                            own directory. Use eval_holdout/manifest.json
                            for Gate -1.
  --fonts-glob <glob>       dataset_v2 has no manifest.json. Build the font
                            list from a glob over atlas PNGs (font name =
                            file stem), e.g. "dataset_v2/atlases/*.png".
                            References are expected at a sibling
                            references/<name>.png next to the glob's
                            atlases directory (i.e. dataset_v2/references/).
                            Fonts with no matching reference image are
                            skipped.

Usage:
  python candidate_gen.py --fonts-manifest eval_holdout/manifest.json \
      --out-dir dpo_data --models baseline,glyph --glyph-seeds 4 --steps 20

  python candidate_gen.py --fonts-glob "dataset_v2/atlases/*.png" \
      --out-dir dpo_data --models baseline,glyph --glyph-seeds 4 --steps 20
"""
import argparse
import glob as globmod
import json
from pathlib import Path
import os

# Checkpoint + template config per model, per Global Constraints.
BASELINE_CKPT = "experiments/20260412-215340_Kg_structured_prompt_5000/checkpoints/checkpoint-5000"
GLYPH_CKPT = "training_glyph_r32_5000/checkpoint-5000"
DISAMBIG_PT = "dataset_v2/cache/template_disambig_mild.pt"
BASE_9B = "black-forest-labs/FLUX.2-klein-base-9B"

MODEL_SPECS = {
    "baseline": {"checkpoint": BASELINE_CKPT, "use_template": False, "template_pt": None},
    "glyph":    {"checkpoint": GLYPH_CKPT,    "use_template": True,  "template_pt": DISAMBIG_PT},
}


def resolve_conditioning(spec):
    """Fill a spec's prompt_style / reference_chars from the CHECKPOINT.

    Never hardcode these: load_generation_pipe defaults to prompt_style
    "structured" / reference_chars "Kg", but every train_lora_kg.py lineage
    checkpoint (both glyph models) was trained on "trained-short" / "Rg".
    Generating with the wrong prompt style is silent and measurably
    suppresses IDENTITY (0.9936 -> 0.9780, all 50 fonts worse) while barely
    moving char_acc -- see conditioning_config.check_eval_conditioning.
    """
    from conditioning_config import expected_conditioning

    exp = expected_conditioning(spec["checkpoint"]) or {}
    out = dict(spec)
    out.setdefault("model", BASE_9B)
    out["prompt_style"] = exp.get("prompt_style") or "structured"
    out["reference_chars"] = exp.get("reference_chars") or "Kg"
    return out


def candidate_key(font, model, seed):
    return f"{font}__{model}__seed{seed}"


def parse_candidate_key(key):
    """Inverse of candidate_key(): "font__model__seedN" -> (font, model, int(N)).

    rsplit so a font name containing "__" still parses (model and "seedN"
    never contain it). Single source of truth -- several analysis scripts
    used to re-derive this inline and had already drifted.
    """
    font, model, seed = key.rsplit("__", 2)
    return font, model, int(seed.replace("seed", ""))


def candidate_path(out_dir, font, model, seed):
    return f"{out_dir}/candidates/{font}/{model}__seed{seed}.png"


def pending_jobs(fonts, model_specs, seeds, out_dir):
    """List the (font, model, seed) jobs that haven't been generated yet.

    Idempotent/resumable: a job is skipped if its candidate_path already
    exists on disk, regardless of how it got there (prior run, manual copy).
    """
    jobs = []
    for font in fonts:
        for model in model_specs:
            for seed in seeds[model]:
                p = candidate_path(out_dir, font, model, seed)
                if not os.path.exists(p):
                    jobs.append({"font": font, "model": model, "seed": seed, "out": p})
    return jobs


def run(fonts, ref_paths, model_specs, seeds, out_dir, steps):
    """Generate all pending candidates, grouped by model so each pipe loads once."""
    from generation_lib import load_generation_pipe, generate_one_atlas

    jobs = pending_jobs(fonts, model_specs, seeds, out_dir)
    for model, spec in model_specs.items():
        model_jobs = [j for j in jobs if j["model"] == model]
        if not model_jobs:
            continue
        spec = resolve_conditioning(spec)
        print(f"[{model}] {spec['checkpoint']} base={spec['model']} "
              f"prompt_style={spec['prompt_style']} ref_chars={spec['reference_chars']} "
              f"template_pt={spec['template_pt']}", flush=True)
        pipe, pe, ne = load_generation_pipe(
            spec["checkpoint"], use_template=spec["use_template"], template_pt=spec["template_pt"],
            model=spec["model"], reference_chars=spec["reference_chars"],
            prompt_style=spec["prompt_style"],
        )
        for j in model_jobs:
            generate_one_atlas(pipe, pe, ne, ref_paths[j["font"]], j["out"], steps=steps, seed=j["seed"])
        del pipe
        import torch
        torch.cuda.empty_cache()


def load_fonts_from_manifest(manifest_path):
    """Load fonts + reference paths from a holdout-style manifest.json.

    Expects top-level {"fonts": [{"name": ..., "reference": <relpath>}, ...]}
    (eval_holdout/manifest.json's format). Reference paths are resolved
    relative to the manifest file's own directory.
    """
    with open(manifest_path, encoding="utf-8") as f:
        m = json.load(f)
    base = Path(manifest_path).parent
    fonts = [e["name"] for e in m["fonts"]]
    refs = {e["name"]: str(base / e["reference"]) for e in m["fonts"]}
    return fonts, refs


def load_fonts_from_glob(atlas_glob):
    """Build the font list from a dataset_v2-style atlases/*.png glob.

    dataset_v2 has no manifest.json. Font name = file stem. References are
    expected at a sibling `references/<name>.png` next to the glob's
    atlases directory (e.g. glob "dataset_v2/atlases/*.png" ->
    references at "dataset_v2/references/<name>.png"). Fonts with no
    matching reference image are skipped (can't generate without one).
    """
    paths = sorted(globmod.glob(atlas_glob))
    if not paths:
        raise ValueError(f"--fonts-glob matched no files: {atlas_glob}")
    atlases_dir = Path(paths[0]).parent
    refs_dir = atlases_dir.parent / "references"

    fonts = []
    refs = {}
    for p in paths:
        name = Path(p).stem
        ref_path = refs_dir / f"{name}.png"
        if not ref_path.exists():
            continue
        fonts.append(name)
        refs[name] = str(ref_path)
    return fonts, refs


def _build_arg_parser():
    ap = argparse.ArgumentParser()
    fonts_source = ap.add_mutually_exclusive_group(required=True)
    fonts_source.add_argument("--fonts-manifest", default=None,
                               help="Holdout-style manifest.json (name/reference keys).")
    fonts_source.add_argument("--fonts-glob", default=None,
                               help='Glob over atlas PNGs, e.g. "dataset_v2/atlases/*.png".')
    ap.add_argument("--out-dir", default="dpo_data")
    ap.add_argument("--models", default="baseline,glyph")
    ap.add_argument("--glyph-seeds", type=int, default=4)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--glyph-checkpoint", default=None,
                    help="Override the 'glyph' checkpoint (e.g. a 4B run's final/).")
    ap.add_argument("--base-model", default=None,
                    help="Base model for the 'glyph' checkpoint, e.g. "
                         "black-forest-labs/FLUX.2-klein-base-4B. Defaults to the 9B.")
    return ap


def main(argv=None):
    args = _build_arg_parser().parse_args(argv)

    specs = {k: dict(MODEL_SPECS[k]) for k in args.models.split(",")}
    if (args.glyph_checkpoint or args.base_model) and "glyph" not in specs:
        raise SystemExit("--glyph-checkpoint/--base-model require 'glyph' in --models")

    if args.fonts_manifest:
        fonts, refs = load_fonts_from_manifest(args.fonts_manifest)
    else:
        fonts, refs = load_fonts_from_glob(args.fonts_glob)

    if args.glyph_checkpoint:
        specs["glyph"]["checkpoint"] = args.glyph_checkpoint
    if args.base_model:
        specs["glyph"]["model"] = args.base_model
    seeds = {"baseline": [0], "glyph": list(range(args.glyph_seeds))}
    seeds = {k: seeds[k] for k in specs}

    run(fonts, refs, specs, seeds, args.out_dir, args.steps)


if __name__ == "__main__":
    main()
