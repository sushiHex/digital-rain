"""If no model will INVENT a stencil, can ours TRANSFER one it is handed?

PRE-REGISTERED. Written and committed before any atlas was generated.

THE QUESTION NOTHING HAS ASKED. Every stencil test so far pointed a GENERAL
image model at the problem: two text-to-image generators, eight seeds, no break
(`2026-08-25-the-second-arm-fails-the-same-way.md`); then image-to-image on the
same weights, four strengths, no break
(`2026-08-25-the-edit-path-does-not-break-a-stroke-either.md`). All of them
asked a model to DRAW a rare treatment from a description.

But this repository does not need to draw one. `synthesize_rare_attributes.py`
already CONSTRUCTS stencil glyphs geometrically -- that is how it builds its
training data. So the untested question is a different one:

    can the glyph-conditioned LoRA TRANSFER a treatment it is HANDED,
    to the ninety-two letters nobody supplied?

If it can, the product answer for rare treatments is to synthesise the reference
rather than generate it. Zero new weights, zero download, one GPU session.

THREE ARMS, AND THE MIDDLE ONE IS A POSITIVE CONTROL.

    plain     the neutral Kg, untouched          -- the baseline
    inline    a medial stripe removed            -- POSITIVE CONTROL
    stencil   bands erased across the strokes    -- the case that matters

Inline is the control because the generator DID carry an inline stripe through
the whole chain unaided on 2026-08-23. If inline transfers and stencil does not,
the limit is specific to breaks. If NEITHER transfers, reference synthesis is
the wrong idea and the arms say so together.

All three share ONE SEED, so the arms differ by the reference only. A per-arm
seed would fold the style lottery (SD 0.0248 on the seed main effect alone)
into the comparison.

=== PRE-REGISTRATION, fixed before running ===

SOURCE        One neutral `Kg` from a single licence-clean sans, then the
              stencil and inline transforms from `synthesize_rare_attributes`
              applied to the ink bounding box, so band spacing scales to the
              LETTER rather than to the canvas.
PRIMARY       A YES/NO, as in the two tests before it: do the ninety-two
              letters the model was NOT given show breaks in the stencil arm?
              Judged by eye, because a break is visible or it is not.
EVIDENCE      `parts` and `holes` over the 92 NON-REFERENCE cells, per arm.
              `K` and `g` are excluded throughout: the model is conditioned to
              copy them, so including them would measure the conditioning
              rather than the transfer. A stencil signature is parts UP and
              holes DOWN against the plain arm.
IF IT FAILS   Reported as a failure, and it closes reference synthesis for rare
              treatments -- the model would have declined to propagate a
              treatment placed directly in front of it. There is then no
              cheap route to a stencil and the honest product answer is to say
              the style is unavailable.

TWO CAVEATS, STATED BEFORE THE RESULT RATHER THAN AFTER.

  * The band eraser makes GRID-ALIGNED gaps; a designer breaks strokes at
    junctions. So the reference is out of distribution in a NEW way, even
    though synthetic references were shown not to break the generator.
  * The 925-font corpus contains some stencil families, so a success would
    partly reflect training exposure rather than pure transfer. That does not
    make it less useful as a product answer, but it is not evidence of
    generalisation.

  python analysis/synthesised_reference_probe.py
  python analysis/synthesised_reference_probe.py --score-only
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
from PIL import Image
from scipy import ndimage

from analysis.edit_path_probe import neutral_reference
from analysis.reference_stage_adherence import normalise_like_reference
from analysis.style_coherence import cell_features
from analysis.synthesise_transforms import draw_params, transform_reference

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "eval_runs", "_synthesised_refs")
CHECKPOINT = os.path.join("training_glyph_4b_r32_5000", "checkpoint-5000")
MODEL_4B = "black-forest-labs/FLUX.2-klein-base-4B"
REF_CHARS = "Kg"
ARMS = ("plain", "inline", "stencil")
SEED = 42
STEPS = 20
NEED_MB = 12000


def free_vram_mb():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30)
        return int(out.stdout.strip().splitlines()[0])
    except Exception:                                  # noqa: BLE001
        return None


def atlas_topology(path, exclude=REF_CHARS):
    """(parts, holes) over the cells the model was NOT given."""
    from atlas_constants import BLANK_INDICES, CELL_H, CELL_W, CHARSET, GRID_COLS

    arr = np.asarray(Image.open(path).convert("L"))
    parts, holes = [], []
    for idx, ch in enumerate(CHARSET):
        if idx in BLANK_INDICES or ch in exclude:
            continue
        r, c = idx // GRID_COLS, idx % GRID_COLS
        cell = arr[r * CELL_H:(r + 1) * CELL_H, c * CELL_W:(c + 1) * CELL_W]
        norm = normalise_like_reference(cell)
        if norm is None:
            continue
        f = cell_features(norm)
        if f is None:
            continue
        parts.append(f["parts"])
        ink = norm > 128
        gap = ndimage.binary_fill_holes(ink) & ~ink
        holes.append(float(np.log1p(ndimage.label(gap)[1])))
    if not parts:
        return None
    return float(np.mean(parts)), float(np.mean(holes)), len(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pool", default=os.path.join(REPO, "font_pool"))
    ap.add_argument("--checkpoint", default=CHECKPOINT)
    ap.add_argument("--steps", type=int, default=STEPS)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--json", default=os.path.join(REPO, "research",
                                                   "synthesised_reference_probe.json"))
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    src, src_font = neutral_reference(args.pool)
    if src is None:
        print("no neutral font found", file=_sys.stderr)
        return 2
    print(f"\nsource font: {src_font}")

    params = draw_params(np.random.default_rng(0))
    refs = {}
    for arm in ARMS:
        ref_path = os.path.join(OUT, f"ref_{arm}.png")
        transform_reference(src, arm, params).save(ref_path)
        refs[arm] = ref_path
        print(f"  reference {arm:<8} -> {os.path.basename(ref_path)}")

    if not args.score_only:
        free = free_vram_mb()
        if free is not None and free < NEED_MB:
            print(f"refusing to start: {free} MiB free, need {NEED_MB}. The "
                  "3090 is shared -- wait, do not evict.", file=_sys.stderr)
            return 2

        from conditioning_config import expected_conditioning
        from generation_lib import generate_one_atlas, load_generation_pipe

        cond = expected_conditioning(args.checkpoint) or {}
        print(f"\nconditioning: prompt_style={cond.get('prompt_style')} "
              f"ref_chars={cond.get('reference_chars')} "
              f"use_template={cond.get('use_template')}")
        pipe, pe, ne = load_generation_pipe(
            args.checkpoint,
            use_template=cond.get("use_template", True),
            template_pt=cond.get("template_pt"), model=MODEL_4B,
            reference_chars=cond.get("reference_chars"),
            prompt_style=cond.get("prompt_style"))

        for arm in ARMS:
            dst = os.path.join(OUT, f"atlas_{arm}.png")
            if os.path.isfile(dst):
                print(f"  atlas {arm:<8} already generated")
                continue
            t0 = time.time()
            # ONE seed for every arm: they must differ by the REFERENCE only.
            generate_one_atlas(pipe, pe, ne, refs[arm], dst,
                               steps=args.steps, seed=args.seed)
            print(f"  atlas {arm:<8} {time.time() - t0:5.1f}s", flush=True)

    rows = {}
    print(f"\n  {'arm':<10} {'parts':>8} {'holes':>8} {'cells':>6}")
    for arm in ARMS:
        dst = os.path.join(OUT, f"atlas_{arm}.png")
        if not os.path.isfile(dst):
            continue
        topo = atlas_topology(dst)
        if topo is None:
            continue
        rows[arm] = {"parts": topo[0], "holes": topo[1], "cells": topo[2]}
        print(f"  {arm:<10} {topo[0]:>8.3f} {topo[1]:>8.3f} {topo[2]:>6}")

    if "plain" in rows:
        base = rows["plain"]
        print("\n  against the plain arm (92 cells the model was NOT given):")
        for arm in ARMS:
            if arm == "plain" or arm not in rows:
                continue
            dp = rows[arm]["parts"] - base["parts"]
            dh = rows[arm]["holes"] - base["holes"]
            print(f"    {arm:<8} parts {dp:+.3f}   holes {dh:+.3f}")
        print("\n  A stencil signature is parts UP and holes DOWN. INLINE is the")
        print("  POSITIVE CONTROL -- the generator carried an inline stripe")
        print("  unaided on 2026-08-23, so it should move if anything does.")
    print("\n  THE PRIMARY IS A YES/NO, JUDGED BY EYE. These numbers are")
    print("  evidence for that judgement, not a threshold: three atlases.")

    payload = {"preregistered": True, "source_font": src_font,
               "seed": args.seed, "steps": args.steps,
               "excluded_chars": REF_CHARS, "arms": rows}
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
