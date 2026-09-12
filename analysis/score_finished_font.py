"""Score the artefact the user receives: the traced OTF, not the atlas.

WHY THIS EXISTS. Every metric in this repository scores atlas *cells*. The
product is an OpenType font, rendered as running text. Nothing had ever measured
that. `docs/strategy-2026-08.md` called it "arguably the more damning" gap, and
it is: the font builder shipped glyphs 41% too small for months while every
atlas metric passed, because cap height is invisible to a cell-space comparison.

THE DECOMPOSITION, which is the point of the tool. Three arms are traced through
the SAME atlas -> OTF pipeline and all are scored against the holdout font's own
source TTF:

  source       the real .ttf                      the target
  gt_traced    ground-truth atlas -> OTF          the PIPELINE's cost, model error zero
  model        generated atlas -> OTF             the product
  retrieval    nearest TRAINING font's atlas      the non-generative floor

`gt_traced` is the ceiling any atlas-based method can reach. The gap from
`source` to `gt_traced` is charged to the pipeline; the gap from `gt_traced` to
`model` is charged to the model. Atlas metrics conflate the two and can see
neither.

A CORRECTION TO AN EARLIER ASSUMPTION. It is tempting to expect this metric to
beat the retrieval baseline automatically, on the reasoning that retrieval hands
back a real font with real sidebearings. It does not: `retrieval_baseline.py`
returns the corpus font's ATLAS, so retrieval goes through this same pipeline and
loses its letterfitting exactly as the model does. Whether retrieval still wins
here is an open empirical question, and this tool is how it gets answered.

WHAT IS MEASURED. Metrics chosen because atlas scoring is blind to them by
construction:

  advance_mae     mean |built advance / source advance - 1| per glyph, in em.
                  This is letterfitting. `build_dataset` centres every glyph in
                  its cell, so left and right sidebearings are equal by
                  construction and no cell-space metric can notice.
  text_width_err  relative width error of a rendered specimen string --
                  letterfitting error accumulated over real text.
  ink_err         relative ink error of that specimen, i.e. weight AT TEXT SIZE
                  rather than in a 160px cell.

  python analysis/score_finished_font.py --limit 3
  python analysis/score_finished_font.py --run glyph_4b_r32_5000 --json out.json
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

from atlas_constants import CELL_H, CELL_W, CHARSET
from atlas_to_font import build_font, setup_potrace, trace_atlas_cells

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOLDOUT_ATLASES = os.path.join(REPO, "eval_holdout", "atlases")
HOLDOUT_FONTS = os.path.join(REPO, "eval_holdout", "fonts")
CORPUS_ATLASES = os.path.join(REPO, "dataset_v2", "atlases")
RETRIEVAL_JSON = os.path.join(REPO, "research", "retrieval_baseline.json")
CACHE = os.path.join(REPO, "eval_runs", "_finished_fonts")

# Long enough that per-glyph noise averages out, and drawn only from characters
# every holdout font is guaranteed to carry.
SPECIMEN = "Hamburgefonstiv 123 the quick brown fox jumps over the lazy dog"
RENDER_PX = 48
PAD = 20


def build_otf(atlas_path, out_path, name):
    """Trace an atlas into an OTF. Cached -- tracing costs ~8s per atlas."""
    if os.path.isfile(out_path):
        return out_path
    with Image.open(atlas_path) as img:
        cells = trace_atlas_cells(img)
    if not any(cells):
        return None
    font = build_font(cells, CHARSET, CELL_W, CELL_H, font_name=name)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    font.save(out_path)
    return out_path


def advances(path):
    """char -> advance width, in em units so upm differences do not matter."""
    tt = TTFont(path, fontNumber=0, lazy=True)
    try:
        upm = tt["head"].unitsPerEm
        cmap = tt.getBestCmap()
        metrics = tt["hmtx"].metrics
        out = {}
        for ch in CHARSET:
            gname = cmap.get(ord(ch))
            if gname and gname in metrics:
                out[ch] = metrics[gname][0] / upm
        return out
    finally:
        tt.close()


def render_specimen(path, text=SPECIMEN, px=RENDER_PX):
    """Render `text`, cropped to its ink. Returns (image, width, ink_fraction)."""
    pil = ImageFont.truetype(path, px)
    canvas = Image.new("L", (px * len(text), px * 4), 255)
    ImageDraw.Draw(canvas).text((PAD, PAD), text, font=pil, fill=0)
    arr = np.asarray(canvas)
    dark = arr < 128
    if not dark.any():
        return None, 0.0, 0.0
    rows, cols = np.where(dark)
    crop = canvas.crop((cols.min(), rows.min(), cols.max() + 1, rows.max() + 1))
    a = np.asarray(crop)
    return crop, float(crop.width), float((a < 128).mean())


def score_pair(built_path, src_adv, src_width, src_ink):
    """Score one built font against the source font's measurements."""
    adv = advances(built_path)
    common = [c for c in src_adv if c in adv and src_adv[c] > 0]
    if not common:
        return None
    errs = np.array([abs(adv[c] / src_adv[c] - 1.0) for c in common])
    _, width, ink = render_specimen(built_path)
    worst = sorted(((abs(adv[c] / src_adv[c] - 1.0), c) for c in common),
                   reverse=True)[:5]
    return {
        "advance_mae": float(errs.mean()),
        "advance_p90": float(np.percentile(errs, 90)),
        "text_width_err": (width / src_width - 1.0) if src_width else None,
        "ink_err": (ink / src_ink - 1.0) if src_ink else None,
        "n_glyphs": len(common),
        "worst_glyphs": [{"char": c, "err": round(e, 4)} for e, c in worst],
    }


def retrieval_map():
    if not os.path.isfile(RETRIEVAL_JSON):
        return {}
    data = json.load(open(RETRIEVAL_JSON, encoding="utf-8"))
    return {r["font"]: r["retrieved"] for r in data.get("per_font", [])}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", default="glyph_4b_r32_5000",
                    help="eval_runs/<run>/generated to score as the model arm")
    ap.add_argument("--limit", type=int, help="score only the first N fonts")
    ap.add_argument("--json", help="write per-font results here")
    ap.add_argument("--cache", default=CACHE, help="where built OTFs are kept")
    args = ap.parse_args()

    setup_potrace()
    model_dir = os.path.join(REPO, "eval_runs", args.run, "generated")
    retrieved = retrieval_map()

    names = sorted(os.path.splitext(os.path.basename(p))[0]
                   for p in glob.glob(os.path.join(HOLDOUT_ATLASES, "*.png")))
    if args.limit:
        names = names[:args.limit]

    rows, skipped = [], []
    for i, name in enumerate(names, 1):
        src = os.path.join(HOLDOUT_FONTS, name + ".ttf")
        if not os.path.isfile(src):
            src = os.path.join(HOLDOUT_FONTS, name + ".otf")
        if not os.path.isfile(src):
            skipped.append((name, "no source font"))
            continue
        try:
            src_adv = advances(src)
            _, src_width, src_ink = render_specimen(src)
        except Exception as exc:
            skipped.append((name, f"source unreadable: {type(exc).__name__}"))
            continue
        if not src_adv or not src_width:
            skipped.append((name, "source has no usable metrics"))
            continue

        arms = {
            "gt_traced": os.path.join(HOLDOUT_ATLASES, name + ".png"),
            "model": os.path.join(model_dir, name + ".png"),
        }
        if name in retrieved:
            arms["retrieval"] = os.path.join(CORPUS_ATLASES,
                                             retrieved[name] + ".png")

        row = {"font": name, "arms": {}}
        for arm, atlas in arms.items():
            if not os.path.isfile(atlas):
                continue
            out = os.path.join(args.cache, arm, name + ".otf")
            try:
                built = build_otf(atlas, out, f"{name}-{arm}")
                if built:
                    row["arms"][arm] = score_pair(built, src_adv, src_width, src_ink)
            except Exception as exc:
                row["arms"][arm] = None
                skipped.append((f"{name}/{arm}", type(exc).__name__ + f": {exc}"))
        if row["arms"]:
            rows.append(row)
        print(f"  [{i}/{len(names)}] {name:<34} "
              + "  ".join(f"{a}={row['arms'][a]['advance_mae']:.3f}"
                          for a in ("gt_traced", "model", "retrieval")
                          if row["arms"].get(a)))

    print(f"\nscored {len(rows)} fonts against their own source TTF")
    print(f"specimen: {RENDER_PX}px, {len(SPECIMEN)} chars\n")
    print(f"  {'arm':<12} {'advance MAE':>12} {'adv p90':>9} "
          f"{'width err':>10} {'ink err':>9} {'n':>4}")
    summary = {}
    for arm in ("gt_traced", "model", "retrieval"):
        vals = [r["arms"][arm] for r in rows if r["arms"].get(arm)]
        if not vals:
            continue
        summary[arm] = {
            "advance_mae": float(np.mean([v["advance_mae"] for v in vals])),
            "advance_p90": float(np.mean([v["advance_p90"] for v in vals])),
            "text_width_err": float(np.mean([v["text_width_err"] for v in vals
                                             if v["text_width_err"] is not None])),
            "ink_err": float(np.mean([v["ink_err"] for v in vals
                                      if v["ink_err"] is not None])),
            "n_fonts": len(vals),
        }
        s = summary[arm]
        print(f"  {arm:<12} {s['advance_mae']:>12.4f} {s['advance_p90']:>9.4f} "
              f"{s['text_width_err']:>+10.4f} {s['ink_err']:>+9.4f} {s['n_fonts']:>4}")

    # Paired tests, reusing compare_runs' own implementation and gate rather
    # than re-deriving one. CLAUDE.md: do not hand-roll a Wilcoxon.
    from analysis.compare_runs import paired_wilcoxon

    print("\npaired Wilcoxon over fonts, lower is better on every row "
          "(gate p<0.05 AND r>=0.3)")
    print(f"  {'contrast':<28} {'metric':<16} {'p':>9} {'r':>7}  verdict")
    contrasts = [("model vs gt_traced", "model", "gt_traced"),
                 ("model vs retrieval", "model", "retrieval"),
                 ("retrieval vs gt_traced", "retrieval", "gt_traced")]
    metrics = [("advance_mae", False), ("text_width_err", True),
               ("ink_err", True)]
    comparisons = []
    for title, arm_a, arm_b in contrasts:
        for metric, use_abs in metrics:
            pairs = [(r["arms"][arm_a][metric], r["arms"][arm_b][metric])
                     for r in rows
                     if r["arms"].get(arm_a) and r["arms"].get(arm_b)
                     and r["arms"][arm_a].get(metric) is not None
                     and r["arms"][arm_b].get(metric) is not None]
            if len(pairs) < 5:
                continue
            a = [abs(x) if use_abs else x for x, _ in pairs]
            b = [abs(y) if use_abs else y for _, y in pairs]
            res = paired_wilcoxon(b, a)     # b=arm_a's values, a=arm_b's
            sig = res.p < 0.05 and res.effect_r >= 0.3
            better = arm_a if float(np.mean(a)) < float(np.mean(b)) else arm_b
            verdict = f"SIG - {better} better" if sig else "no difference"
            print(f"  {title:<28} {metric:<16} {res.p:>9.4f} "
                  f"{res.effect_r:>7.3f}  {verdict}")
            comparisons.append({"contrast": title, "metric": metric,
                                "p": res.p, "effect_r": res.effect_r,
                                "n": len(pairs), "significant": sig,
                                "better": better if sig else None})

    if skipped:
        print(f"\nskipped {len(skipped)}:")
        for what, why in skipped[:10]:
            print(f"  {what:<34} {why}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"run": args.run, "specimen": SPECIMEN,
                       "render_px": RENDER_PX, "summary": summary,
                       "comparisons": comparisons,
                       "per_font": rows, "skipped": skipped}, fh, indent=1)
        print(f"\nwrote {args.json}")

    return 0 if rows else 3


if __name__ == "__main__":
    _sys.exit(main())
