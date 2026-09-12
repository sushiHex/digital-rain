"""Download a FLUX.2-klein base model into the HF cache, diffusers layout only.

The klein repos ship the transformer twice: once as the diffusers component
folder (`transformer/`) and once as a flat single-file variant at the repo root
(`flux-2-klein-base-4b.safetensors`, same 7.2 GB). `Flux2KleinPipeline.from_pretrained`
reads the component folders, so fetching both wastes ~7 GB.

Usage:
  python pipeline/fetch_base_model.py black-forest-labs/FLUX.2-klein-base-4B
  python pipeline/fetch_base_model.py <repo> --dry-run
"""

# repo root on sys.path so `python pipeline/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse

# Component folders a diffusers pipeline loads, plus the top-level index.
# Covers FLUX-style repos and the extra components GLM-Image ships
# (vision_language_encoder for its autoregressive stage, processor for image
# conditioning). Anything not listed -- flat single-file weight variants,
# sample images -- is skipped; see the docstring.
ALLOW = [
    "model_index.json",
    "transformer/*",
    "text_encoder/*",
    "text_encoder_2/*",
    "tokenizer/*",
    "tokenizer_2/*",
    "scheduler/*",
    "vae/*",
    "vision_language_encoder/*",
    "processor/*",
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be fetched and its size, download nothing")
    args = ap.parse_args()

    from huggingface_hub import HfApi, snapshot_download

    info = HfApi().model_info(args.repo, files_metadata=True)
    license_tag = (info.card_data or {}).get("license", "(unknown)")

    import fnmatch
    wanted = [s for s in info.siblings
              if any(fnmatch.fnmatch(s.rfilename, p) for p in ALLOW)]
    total = sum(s.size or 0 for s in wanted)
    skipped = [s for s in info.siblings if s not in wanted and (s.size or 0) > 1 << 20]

    print(f"repo    : {args.repo}")
    print(f"license : {license_tag}")
    print(f"fetching: {len(wanted)} files, {total / 2**30:.2f} GB")
    for s in skipped:
        print(f"skipping: {s.rfilename}  ({(s.size or 0) / 2**30:.2f} GB)")

    if args.dry_run:
        return

    path = snapshot_download(args.repo, allow_patterns=ALLOW)
    print(f"\ncached at: {path}")


if __name__ == "__main__":
    main()
