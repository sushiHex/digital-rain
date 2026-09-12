"""Focused de-risk: does GOT-OCR2 read SYMBOLS/confusables on single glyph cells
better than TrOCR? Decodes only the decisive char set across 6 fonts x 2 runs.
Writes measure_ocr_symbols_results.json + prints the per-class table + capture analysis."""

# repo root on sys.path so `python studies/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import json
import numpy as np
from PIL import Image
from atlas_constants import CHARSET
from eval_checkpoint import crop_cell
from cleanup.models import build_trocr_ocr_fn
from studies.hybrid_v2_ocr import build_got_ocr_fn

CONF = list("\\/'\"O0()[]{}<>|Il1")
LETTERS = list("aeRQgk")   # control
DIGITS = list("47")
TARGET = CONF + LETTERS + DIGITS
IDX = {c: CHARSET.index(c) for c in TARGET if c in CHARSET}

FONTS = ["NovaSquare", "AveriaSerifLibre", "IBMPlexSerif-Regular",
         "RubikDistressed-Regular", "KosugiMaru-Regular", "ProtestStrike-Regular"]
RUNS = {"baseline": "eval_runs/structured_prompt_5000/generated",
        "glyph":    "eval_runs/glyph_r32_5000/generated"}

def match(dec, exp):
    d = dec.strip().lower()
    e = exp.lower()
    return d == e or d.startswith(e)   # tolerate trailing OCR noise like 'A.'

print("loading OCR models...", flush=True)
trocr = build_trocr_ocr_fn(device="cuda")
got = build_got_ocr_fn(device="cuda")

def atlas(run, font):
    from pathlib import Path
    p = Path(RUNS[run]) / f"{font}.png"
    if not p.exists():
        # variable-font bracket names may differ; glob
        import glob
        g = glob.glob(str(Path(RUNS[run]) / f"{font}*.png"))
        p = Path(g[0]) if g else p
    return np.array(Image.open(p).convert("RGB")) if p.exists() else None

rows = []
for font in FONTS:
    for run in RUNS:
        a = atlas(run, font)
        if a is None:
            print(f"  MISSING {run}/{font}", flush=True); continue
        for c, idx in IDX.items():
            cell = crop_cell(a, idx)
            t = trocr(cell); g = got(cell)
            rows.append({"font": font, "run": run, "char": c, "expected": c,
                         "trocr": t, "got": g,
                         "trocr_ok": match(t, c), "got_ok": match(g, c)})
        print(f"  done {run}/{font}", flush=True)

json.dump(rows, open("measure_ocr_symbols_results.json", "w"), indent=1)

def acc(rows, chars, key):
    sub = [r for r in rows if r["char"] in chars]
    return (sum(r[key] for r in sub) / len(sub), len(sub)) if sub else (0, 0)

print("\n==== per-char-class decode accuracy (both runs pooled) ====")
for lab, chars in [("CONFUSABLE/SYMBOL", CONF), ("letters(ctrl)", LETTERS), ("digits(ctrl)", DIGITS)]:
    ta, n = acc(rows, chars, "trocr_ok")
    ga, _ = acc(rows, chars, "got_ok")
    print(f"  {lab:20s} TrOCR={ta:.3f}  GOT-OCR2={ga:.3f}  delta={ga-ta:+.3f}  (n={n})")

print("\n==== per-symbol (confusables) TrOCR vs GOT ====")
for c in CONF:
    sub = [r for r in rows if r["char"] == c]
    if not sub: continue
    t = sum(r["trocr_ok"] for r in sub) / len(sub)
    g = sum(r["got_ok"] for r in sub) / len(sub)
    flag = "  <==GOT better" if g > t + 1e-9 else ("  (trocr better)" if t > g + 1e-9 else "")
    print(f"  {c!r:5s} TrOCR={t:.2f} GOT={g:.2f}{flag}  n={len(sub)}")
print("\nDONE")
