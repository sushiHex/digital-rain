"""Build holdout variants whose REFERENCES look like something a user uploaded.

THE GAP THIS MEASURES. Every number this project has published is an
ORACLE-REFERENCE number: the reference image is rendered from the target font's
own TTF, through the same code that produced the ground-truth atlas. It is
pixel-exact, noiseless, perfectly framed, and made by the same pipeline being
evaluated. A real user uploads a screenshot or a photo.

`docs/quality-roadmap-v3.md` said in May that "if users supply non-oracle refs,
quality WILL drop sharply". That has never been measured, and it is the single
largest gap between these results and a usable product.

WHY DEGRADE THE ORACLE RATHER THAN SUBSTITUTE A DIFFERENT FONT. A reference
from some *other* typeface has no ground truth to score against -- the model
would be asked to produce a style whose correct answer does not exist in the
holdout. Degrading the oracle reference keeps the ground truth exactly valid
while removing the same-pipeline, pixel-exact advantage. It isolates one
variable: input fidelity.

TIERS, so the result is a dose-response curve and not one arbitrary point:

  screenshot  a clean screen capture: downscale/upscale resample, light JPEG.
  upload      a typical user file: smaller resample, visible JPEG, slight blur.
  photo       a phone photo of print: the above plus rotation, perspective-ish
              contrast shift, and sensor noise.

Ground-truth atlases are COPIED UNCHANGED. Only references differ.

  python analysis/build_degraded_holdout.py
  python analysis/build_degraded_holdout.py --tier upload --out eval_holdout_upload
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import io
import json
import os
import shutil

import numpy as np
from PIL import Image, ImageFilter

SRC = "eval_holdout"


def _jpeg(im, quality):
    buf = io.BytesIO()
    im.convert("L").save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return Image.open(buf).convert("L")


def _resample(im, factor):
    """Downscale then back up -- the detail loss of a rescaled screenshot."""
    w, h = im.size
    small = im.resize((max(1, int(w * factor)), max(1, int(h * factor))),
                      Image.LANCZOS)
    return small.resize((w, h), Image.LANCZOS)


def tier_screenshot(im, rng):
    return _jpeg(_resample(im, 0.55), 85)


def tier_upload(im, rng):
    im = _resample(im, 0.38)
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    return _jpeg(im, 60)


def tier_photo(im, rng):
    im = _resample(im, 0.32)
    im = im.rotate(rng.uniform(-1.8, 1.8), resample=Image.BICUBIC,
                   fillcolor=0, expand=False)
    a = np.asarray(im).astype(np.float32)
    # Uneven lighting: a soft horizontal gradient, as when photographing a page.
    h, w = a.shape
    grad = np.linspace(0.86, 1.14, w, dtype=np.float32)[None, :]
    a = a * grad
    a = a + rng.normal(0.0, 4.0, a.shape).astype(np.float32)   # sensor noise
    a = np.clip(a, 0, 255).astype(np.uint8)
    im = Image.fromarray(a, mode="L").filter(ImageFilter.GaussianBlur(0.8))
    return _jpeg(im, 45)


TIERS = {"screenshot": tier_screenshot, "upload": tier_upload, "photo": tier_photo}


def build(tier, out, src=SRC, seed=0):
    fn = TIERS[tier]
    rng = np.random.default_rng(seed)
    if os.path.isdir(out):
        shutil.rmtree(out)
    shutil.copytree(src, out)

    ref_dir = os.path.join(out, "references")
    n, diffs = 0, []
    for name in sorted(os.listdir(ref_dir)):
        if not name.lower().endswith(".png"):
            continue
        p = os.path.join(ref_dir, name)
        with Image.open(p) as im:
            orig = im.convert("L")
            deg = fn(orig, rng)
        diffs.append(float(np.abs(np.asarray(orig, dtype=np.int16)
                                  - np.asarray(deg, dtype=np.int16)).mean()))
        deg.save(p)          # same filename, so the manifest still resolves
        n += 1

    meta = os.path.join(out, "degradation.json")
    with open(meta, "w", encoding="utf-8") as f:
        json.dump({"tier": tier, "source": src, "n_references": n,
                   "mean_abs_diff_vs_oracle": round(float(np.mean(diffs)), 3),
                   "note": "GROUND-TRUTH ATLASES ARE UNCHANGED; only the "
                           "reference images are degraded."}, f, indent=1)
    return n, float(np.mean(diffs))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tier", choices=sorted(TIERS) + ["all"], default="all")
    ap.add_argument("--out", default=None,
                    help="output dir (default eval_holdout_<tier>)")
    ap.add_argument("--src", default=SRC)
    args = ap.parse_args(argv)

    tiers = sorted(TIERS) if args.tier == "all" else [args.tier]
    for t in tiers:
        out = args.out or f"eval_holdout_{t}"
        n, d = build(t, out, args.src)
        print(f"{t:<11} -> {out:<28} {n} references, "
              f"mean |diff| vs oracle {d:.2f}/255")
    print("\nGround truth is untouched in every tier. Only the model's INPUT "
          "changed.")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
