"""Can an EDIT model break the strokes that a text-to-image model will not?

PRE-REGISTERED. Written and committed before any image was generated.

THE ONLY UNTRIED MECHANISM. Eight seeds across two independent text-to-image
models -- FLUX.2-klein-base-4B and Z-Image-Turbo -- produce no break at all for
"a stencil sans with deliberate breaks"
(`research/2026-08-25-the-second-arm-fails-the-same-way.md`). That relocated the
failure from the model to the TASK: asking a general image model to DRAW a rare
typographic treatment from a description.

This asks a different question of the same weights. Render a neutral `Kg` from
one real font, then run image-to-image with the same description. The request
becomes "make THIS letterform stencilled" rather than "draw a stencil face",
and the two glyphs receive one transformation in one pass -- consistency by
construction rather than by hope. That is the argument
`2026-08-23-restyle-not-generate-the-reference.md` made and nothing has tested.

AND IT COSTS NOTHING TO TRY. `ZImageImg2ImgPipeline` ships in diffusers 0.38 and
the Z-Image-Turbo weights are already cached from the second-arm run. Qwen-
Image-Edit-2511 is the stronger candidate on paper, but it is a fresh download
AND an INT4 build -- the exact shape that killed both GLM paths.

THE TENSION THIS SWEEPS. `strength` controls how far the output may leave the
source. Low strength preserves the letterform and may change too little to
break a stroke; high strength approaches plain text-to-image and throws away
the consistency that made this worth trying. The research note nominates
0.30-0.45; that is a guess about a different model, so the sweep is wider.

=== PRE-REGISTRATION, fixed before running ===

SOURCE        One neutral `Kg` rendered from a single licence-clean sans, two
              columns at one font size on a shared baseline -- the conventions
              `build_dataset.render_reference` uses, with `Kg` rather than its
              hardcoded `Rg` so this matches the candidate arms.
SWEEP         strength in {0.30, 0.50, 0.70, 0.90} x 2 seeds = 8 images, on the
              stencil description only.
PRIMARY       A YES/NO, as in the second-arm test: does ANY output show a break
              in a stroke? Judged by eye against the figure, because a break is
              visible or it is not.
EVIDENCE      `parts` and `holes` per output, beside the SOURCE's own values.
              A stencil signature is parts UP and holes DOWN -- breaking bands
              cut the counters open. Reported as evidence for the yes/no, NOT
              as a threshold: these are two numbers on eight images.
IF IT FAILS   Reported as a failure, and it closes the mechanism rather than
              the model: text-to-image and image-to-image on the same weights
              would both have declined to break a stroke. The next candidate is
              then a purpose-built edit model, not another sweep.

  python analysis/edit_path_probe.py
  python analysis/edit_path_probe.py --style 09 --strengths 0.4 0.6
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
import os
import subprocess
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from analysis.generate_candidate_references import (PROMPT_TEMPLATE, REF_CHARS,
                                                    STYLE_PROMPTS, Z_IMAGE,
                                                    normalise)
from analysis.reference_gate import glyph_cells
from analysis.style_coherence import cell_features

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "eval_runs", "_edit_path")
CANVAS = 1024
NEUTRAL = ["ABeeZee-Regular", "Lato-Regular", "Lato-Black"]
STRENGTHS = (0.30, 0.50, 0.70, 0.90)
SEEDS = (42, 43)
STYLE = "09"                     # the stencil description
NEED_MB = 12000
STEPS = 8                        # Z-Image-Turbo is distilled for ~8


def free_vram_mb():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30)
        return int(out.stdout.strip().splitlines()[0])
    except Exception:                                  # noqa: BLE001
        return None


def neutral_reference(pool, chars=REF_CHARS, size=CANVAS):
    """A plain `Kg`, two columns, ONE font size, shared baseline.

    Mirrors `build_dataset.render_reference`'s conventions -- one size for both
    glyphs so their natural proportions survive -- but draws `Kg`, because that
    function hardcodes `Rg` and every candidate arm here uses `Kg`.
    """
    for stem in NEUTRAL:
        for ext in ("ttf", "otf"):
            path = os.path.join(pool, f"{stem}.{ext}")
            if os.path.isfile(path):
                break
        else:
            continue
        break
    else:
        return None, None

    img = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(img)
    col_w = size // len(chars)
    font = ImageFont.truetype(path, int(size * 0.45))
    ascent, _ = font.getmetrics()
    baseline = int(size * 0.62)
    for i, ch in enumerate(chars):
        bbox = font.getbbox(ch)
        w = bbox[2] - bbox[0]
        x = i * col_w + (col_w - w) // 2 - bbox[0]
        draw.text((x, baseline - ascent), ch, fill=255, font=font)
    return img.convert("RGB"), os.path.basename(path)


def topology(img, chars=REF_CHARS):
    """(parts, holes) averaged over a reference's two glyphs."""
    from scipy import ndimage

    tmp = os.path.join(OUT, "_probe_tmp.png")
    img.convert("L").save(tmp)
    cells = glyph_cells(tmp, len(chars))
    parts, holes = [], []
    for cell in cells:
        if cell is None:
            continue
        f = cell_features(cell)
        if f is None:
            continue
        parts.append(f["parts"])
        ink = cell > 128
        gap = ndimage.binary_fill_holes(ink) & ~ink
        holes.append(float(np.log1p(ndimage.label(gap)[1])))
    if not parts:
        return None
    return float(np.mean(parts)), float(np.mean(holes))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pool", default=os.path.join(REPO, "font_pool"))
    ap.add_argument("--style", default=STYLE)
    ap.add_argument("--strengths", type=float, nargs="*", default=list(STRENGTHS))
    ap.add_argument("--steps", type=int, default=STEPS)
    ap.add_argument("--json", default=os.path.join(REPO, "research",
                                                   "edit_path_probe.json"))
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    style = STYLE_PROMPTS[int(args.style)]
    prompt = PROMPT_TEMPLATE.format(a=REF_CHARS[0], b=REF_CHARS[1], style=style)
    print(f"\nstyle {args.style}: {style}\n")

    src, src_font = neutral_reference(args.pool)
    if src is None:
        print(f"no neutral font found among {NEUTRAL}", file=_sys.stderr)
        return 2
    src.save(os.path.join(OUT, "00-source.png"))
    src_topo = topology(src)
    print(f"  source {src_font}   parts {src_topo[0]:.3f}  holes {src_topo[1]:.3f}\n")

    free = free_vram_mb()
    if free is not None and free < NEED_MB:
        print(f"refusing to start: {free} MiB free, need {NEED_MB}. The 3090 is "
              "shared -- wait, do not evict.", file=_sys.stderr)
        return 2

    import torch
    from diffusers import ZImageImg2ImgPipeline

    pipe = ZImageImg2ImgPipeline.from_pretrained(Z_IMAGE,
                                                 torch_dtype=torch.bfloat16)
    pipe = pipe.to("cuda")

    rows = []
    for strength in args.strengths:
        for seed in SEEDS:
            name = f"s{strength:.2f}_seed{seed}"
            t0 = time.time()
            img = pipe(prompt=prompt, image=src, strength=float(strength),
                       num_inference_steps=args.steps,
                       generator=torch.Generator("cpu").manual_seed(seed)).images[0]
            img.save(os.path.join(OUT, name + "_raw.png"))
            norm, reason = normalise(img)
            secs = time.time() - t0
            if norm is None:
                rows.append({"name": name, "strength": strength, "seed": seed,
                             "rejected": reason, "seconds": secs})
                print(f"  {name:<18} {secs:5.1f}s  REJECTED: {reason}", flush=True)
                continue
            norm.save(os.path.join(OUT, name + ".png"))
            topo = topology(norm)
            rows.append({"name": name, "strength": strength, "seed": seed,
                         "parts": topo[0] if topo else None,
                         "holes": topo[1] if topo else None,
                         "seconds": secs})
            print(f"  {name:<18} {secs:5.1f}s  parts {topo[0]:.3f}  "
                  f"holes {topo[1]:.3f}", flush=True)

    print("\n  A stencil signature is parts UP and holes DOWN against the "
          "source:")
    print(f"  source parts {src_topo[0]:.3f}  holes {src_topo[1]:.3f}")
    print("\n  THE PRIMARY IS A YES/NO AND IT IS JUDGED BY EYE. These two "
          "numbers")
    print("  are evidence for that judgement, not a threshold: eight images.")

    payload = {"preregistered": True, "style": args.style, "prompt": style,
               "source_font": src_font, "steps": args.steps,
               "source_parts": src_topo[0], "source_holes": src_topo[1],
               "rows": rows}
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
