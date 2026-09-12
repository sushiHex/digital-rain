"""Render multi-reference variants on the hard fonts.

Pipeline natively supports image=[ref1, ref2, ...]. The LoRA was trained T=10
single-ref, so refs 2+ use out-of-distribution position IDs -- the analyzer
decides whether the model used them, ignored them, or got confused.
"""

# repo root on sys.path so `python pipeline/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from pathlib import Path

from probe_utils import (
    HARD_FONTS,
    REF1_KG,
    REF2_KG_MN,
    REF2_MN_KG,
    run_render_grid,
)


CKPT = "experiments/20260412-215340_Kg_structured_prompt_5000/checkpoints/checkpoint-5000"
OUT_DIR = Path("experiments/multiref")

# Each variant is a list of (chars, font_template). "{target}" is substituted
# with the target font's path so all refs are oracle (target-font-rendered).
VARIANT_REFS = {
    REF1_KG:    [("Kg", "{target}")],
    REF2_KG_MN: [("Kg", "{target}"), ("Mn", "{target}")],
    REF2_MN_KG: [("Mn", "{target}"), ("Kg", "{target}")],
}


def main():
    jobs = []
    for target_name, target_path in HARD_FONTS.items():
        for variant_name, refs in VARIANT_REFS.items():
            extra_args = []
            for chars, template in refs:
                extra_args.extend([
                    "--reference-chars", chars,
                    "--reference-font", template.format(target=target_path),
                ])
            jobs.append({
                "out_name": f"{target_name}__{variant_name}.png",
                "label": f"{target_name} / {variant_name}",
                "extra_args": extra_args,
            })
    run_render_grid(jobs, ckpt=CKPT, out_dir=OUT_DIR)


if __name__ == "__main__":
    main()
