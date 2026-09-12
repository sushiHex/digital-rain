"""Render the hard fonts under three reference variants.

The analyzer compares oracle vs Times to decide whether the model is
reference-attentive on hard fonts.
"""

# repo root on sys.path so `python pipeline/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from pathlib import Path

from probe_utils import (
    HARD_FONTS,
    REF_ORACLE,
    REF_ROBOTO,
    REF_TIMES,
    default_reference_font,
    run_render_grid,
)


CKPT = "experiments/20260412-215340_Kg_structured_prompt_5000/checkpoints/checkpoint-5000"
OUT_DIR = Path("experiments/ref_ablation")

ROBOTO_PATH = "google-fonts/ofl/roboto/Roboto[wdth,wght].ttf"


def main():
    jobs = []
    for target_name, target_path in HARD_FONTS.items():
        ref_paths = {
            REF_TIMES: default_reference_font(),
            REF_ORACLE: target_path,
            REF_ROBOTO: ROBOTO_PATH,
        }
        for variant, ref_path in ref_paths.items():
            jobs.append({
                "out_name": f"{target_name}__ref_{variant}.png",
                "label": f"{target_name} / ref={variant}",
                "extra_args": [
                    "--reference-chars", "Kg",
                    "--reference-font", ref_path,
                ],
            })
    run_render_grid(jobs, ckpt=CKPT, out_dir=OUT_DIR)


if __name__ == "__main__":
    main()
