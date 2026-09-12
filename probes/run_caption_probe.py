"""Render the caption A/B grid: 4 prompt prefixes x 3 reference fonts."""

# repo root on sys.path so `python probes/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from pathlib import Path

from probe_utils import (
    CAPTION_CLASH,
    CAPTION_CONTROL,
    CAPTION_MATCH,
    CAPTION_NULL,
    run_render_grid,
)


CKPT = "experiments/20260412-215340_Kg_structured_prompt_5000/checkpoints/checkpoint-5000"
OUT_DIR = Path("experiments/caption_probe")

PREFIXES = {
    CAPTION_CONTROL: "",
    CAPTION_MATCH: "A regular serif typeface.",
    CAPTION_CLASH: "A thin script handwriting font.",
    CAPTION_NULL: "abc xyz qrs.",
}

FONTS = {
    "times": "C:/Windows/Fonts/times.ttf",
    "arial": "C:/Windows/Fonts/arial.ttf",
    "consol": "C:/Windows/Fonts/consola.ttf",
}


def main():
    jobs = []
    for variant, prefix in PREFIXES.items():
        for fontname, font_path in FONTS.items():
            jobs.append({
                "out_name": f"{fontname}_{variant}.png",
                "label": f"{fontname} / {variant}",
                "extra_args": [
                    "--reference-chars", "Kg",
                    "--reference-font", font_path,
                    "--prompt-prefix", prefix,
                ],
            })
    run_render_grid(jobs, ckpt=CKPT, out_dir=OUT_DIR)


if __name__ == "__main__":
    main()
