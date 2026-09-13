"""Where the CV fall came from: per-cell ink width, plain arm against monospace arm.

One panel per registered pair. A point is one of the 92 cells the model was not
given, placed by its ink width in the plain arm (x) and in the monospace arm
(y), labelled with its character. On the diagonal a cell kept its width. The
Kg panel is the 2026-09-11 failure: every cell on the line. The Mi panel is the
2026-09-12 result: the widest cells fall far below the line and the narrowest
rise above it, and the whole cloud sits a little left of where it started.

THE RECORD, NOT THE PNGs, IS THE EVIDENCE. The atlases live under the
gitignored `eval_runs/`, so this script writes everything it measures to
`research/relational_widths.json` -- per-cell widths for both pairs, the
summary numbers the note quotes, and the affine fit -- and draws from that
record when the atlases are absent. A public checkout reproduces the figure
from the record; the private archive regenerates the record from the atlases.

WHAT THE SUMMARY CAN AND CANNOT SAY. A uniform horizontal condensing keeps a
face's proportions, so mean and spread fall by the same fraction and the CV
does not move; the spread falling far more than the mean rules THAT out. It
does not rule out a condensing plus an additive stroke or terminal expansion
(the affine fit `mono ~ a + b * plain` is exactly that shape), which lowers
mean and CV together without any set-level reading. The correlation of a
cell's change with its plain width is reported but is not evidence of either:
`Cov(x, y - x) = Cov(x, y) - Var(x)` is negative by construction (CLAUDE.md,
the redistribution statistic), and picking the widest and narrowest cells by
their plain width invites regression to the mean.

  python viz/relational_widths.py           # measures the atlases if present, writes the record, draws
  python viz/relational_widths.py --record  # draws from research/relational_widths.json only
"""
import argparse
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                        # noqa: E402
from PIL import Image                     # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from atlas_constants import BLANK_INDICES, CELL_H, CELL_W, CHARSET, GRID_COLS  # noqa: E402
from viz._common import OUT, REPO                                              # noqa: E402

PAIRS = (("Kg", os.path.join(REPO, "eval_runs", "_relational_refs"),
          "Kg — the pair whose widths already agreed (ratio 1.08)"),
         ("Mi", os.path.join(REPO, "eval_runs", "_relational_refs_Mi"),
          "Mi — a pair that disagrees (ratio 5.28)"))
RECORD = os.path.join(REPO, "research", "relational_widths.json")
MOVED_PX = 3
GROUP = 20            # the widest and narrowest N cells of the PLAIN arm
INK = "#1c1b18"
MOVED = "#b3512f"
LINE = "#9a978f"


def cells(path, exclude):
    """{char: (ink width, ink pixels, bbox fill)} over the cells not drawn in the reference."""
    arr = np.asarray(Image.open(path).convert("L"))
    out = {}
    for idx, ch in enumerate(CHARSET):
        if idx in BLANK_INDICES or ch in exclude:
            continue
        r, c = idx // GRID_COLS, idx % GRID_COLS
        cell = arr[r * CELL_H:(r + 1) * CELL_H, c * CELL_W:(c + 1) * CELL_W] > 128
        cols = np.where(cell.any(axis=0))[0]
        rows = np.where(cell.any(axis=1))[0]
        if not len(cols):
            continue
        w, h = int(cols[-1] - cols[0] + 1), int(rows[-1] - rows[0] + 1)
        out[ch] = (w, int(cell.sum()), float(cell.sum() / (w * h)))
    return out


def summarise(pair, plain, mono):
    chars = sorted(set(plain) & set(mono))
    x = np.array([plain[c][0] for c in chars], float)
    y = np.array([mono[c][0] for c in chars], float)
    d = y - x
    order = np.argsort(x, kind="stable")
    widest = [chars[i] for i in order[-GROUP:]]
    narrowest = [chars[i] for i in order[:GROUP]]
    slope, intercept = np.polyfit(x, y, 1)
    resid = y - (intercept + slope * x)
    r2 = 1 - float((resid ** 2).sum() / ((y - y.mean()) ** 2).sum())
    ink_p = sum(plain[c][1] for c in chars)
    ink_m = sum(mono[c][1] for c in chars)
    return {
        "pair": pair, "n_cells": len(chars),
        "cv_plain": float(x.std() / x.mean()), "cv_mono": float(y.std() / y.mean()),
        "mean_plain": float(x.mean()), "mean_mono": float(y.mean()),
        "sd_plain": float(x.std()), "sd_mono": float(y.std()),
        "narrowed": int((d < -MOVED_PX).sum()), "widened": int((d > MOVED_PX).sum()),
        "within": int((np.abs(d) <= MOVED_PX).sum()), "moved_px": MOVED_PX,
        "widest": {"chars": "".join(widest),
                   "mean_plain": float(np.mean([plain[c][0] for c in widest])),
                   "mean_mono": float(np.mean([mono[c][0] for c in widest]))},
        "narrowest": {"chars": "".join(narrowest),
                      "mean_plain": float(np.mean([plain[c][0] for c in narrowest])),
                      "mean_mono": float(np.mean([mono[c][0] for c in narrowest]))},
        "corr_width_change": float(np.corrcoef(x, d)[0, 1]),
        "affine_fit": {"intercept": float(intercept), "slope": float(slope), "r2": r2},
        "ink_pixels_plain": ink_p, "ink_pixels_mono": ink_m,
        "ink_pixels_change": float(ink_m / ink_p - 1),
        "fill_plain": float(np.mean([plain[c][2] for c in chars])),
        "fill_mono": float(np.mean([mono[c][2] for c in chars])),
        "cells": {c: {"plain": plain[c][0], "mono": mono[c][0]} for c in chars},
    }


CONTROL_ARMS = ("narrow_wide", "widen_narrow", "condense")
PAIR_KEYS = tuple(p for p, _src, _title in PAIRS)
# The control and follow-up runs on the Mi pair, each summarised against ITS
# OWN plain arm. Every run regenerates plain; the controls and dose runs
# reproduce the Mi one bit-for-bit (same seed, same source), while the seed
# and source replications are new draws whose plain differs (CV 0.368 and
# 0.404 against 0.382), which is why each run is summarised against its own.
# Third registration: the controls. Fourth (2026-09-13, issue #30): the dose
# series, and the controls replicated under a second inference seed and a
# second source face.
DOSE_ARMS = ("widen_narrow_x1.5", "widen_narrow_x2", "widen_narrow_x3.1")
RUNS = (
    ("Mi_controls", "_relational_refs_Mi_controls", ("monospace",) + CONTROL_ARMS),
    ("Mi_dose", "_relational_refs_Mi_dose", ("monospace",) + DOSE_ARMS),
    ("Mi_controls_s43", "_relational_refs_Mi_controls_s43", ("monospace",) + CONTROL_ARMS),
    ("Mi_controls_Lato-Regular", "_relational_refs_Mi_controls_Lato-Regular",
     ("monospace",) + CONTROL_ARMS),
)


def summarise_run(src, arms):
    """{arm: summary} for every arm atlas present in `src`, against its plain."""
    plain = os.path.join(src, "atlas_plain.png")
    if not os.path.isfile(plain):
        return None
    base = cells(plain, "Mi")
    out = {}
    for arm in arms:
        atlas = os.path.join(src, f"atlas_{arm}.png")
        if os.path.isfile(atlas):
            s = summarise("Mi", base, cells(atlas, "Mi"))
            del s["cells"]
            out[arm] = s
    return out


def measure():
    out = {}
    for pair, src, _title in PAIRS:
        plain = os.path.join(src, "atlas_plain.png")
        mono = os.path.join(src, "atlas_monospace.png")
        if not (os.path.isfile(plain) and os.path.isfile(mono)):
            return None
        out[pair] = summarise(pair, cells(plain, pair), cells(mono, pair))
    for key, dirname, arms in RUNS:
        run = summarise_run(os.path.join(REPO, "eval_runs", dirname), arms)
        if run:
            out[key] = run
    return out


def draw(record):
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 5.6), facecolor="white", sharex=True, sharey=True)
    for ax, (pair, _src, title) in zip(axes, PAIRS):
        s = record[pair]
        chars = sorted(s["cells"])
        x = np.array([s["cells"][c]["plain"] for c in chars], float)
        y = np.array([s["cells"][c]["mono"] for c in chars], float)
        moved = np.abs(y - x) > s["moved_px"]
        lim = 80
        ax.plot([0, lim], [0, lim], color=LINE, lw=1, zorder=1)
        ax.scatter(x[~moved], y[~moved], s=14, color=INK, zorder=3)
        ax.scatter(x[moved], y[moved], s=18, color=MOVED, zorder=3)
        for c, xi, yi, mv in zip(chars, x, y, moved):
            ax.annotate(c, (xi, yi), xytext=(3, 3), textcoords="offset points",
                        fontsize=7, color=MOVED if mv else LINE, family="monospace")
        ax.set_title(title, fontsize=11, loc="left", color=INK)
        ax.text(0.03, 0.97,
                f"ink-width CV {s['cv_plain']:.3f} → {s['cv_mono']:.3f}\n"
                f"cells moved > {s['moved_px']} px: {s['narrowed'] + s['widened']} of {s['n_cells']}\n"
                f"mean {s['mean_plain']:.1f} → {s['mean_mono']:.1f} px, "
                f"spread {s['sd_plain']:.1f} → {s['sd_mono']:.1f} px",
                transform=ax.transAxes, va="top", fontsize=9.5, color=INK,
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=LINE, lw=0.8))
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
        ax.set_aspect("equal")
        ax.set_xlabel("ink width in the plain arm (px)", fontsize=9.5, color=INK)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(labelsize=8.5, colors=INK)
        ax.grid(True, color="#ecebe6", lw=0.8, zorder=0)
    axes[0].set_ylabel("ink width in the monospace arm (px)", fontsize=9.5, color=INK)
    fig.suptitle("Same checkpoint, seed and transform; only the reference pair differs. "
                 "Orange cells moved more than 3 px.",
                 fontsize=10.5, color=INK, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, "relational_widths.png")
    fig.savefig(dest, dpi=150)
    print(f"wrote {dest}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--record", action="store_true",
                    help="draw from research/relational_widths.json without touching the atlases")
    args = ap.parse_args(argv)
    record = None if args.record else measure()
    if record is None:
        if not os.path.isfile(RECORD):
            print(f"neither the atlases nor {RECORD} are present", file=sys.stderr)
            return 2
        with open(RECORD, encoding="utf-8") as fh:
            record = json.load(fh)["pairs"]
        record = {k: v for k, v in record.items() if k in PAIR_KEYS}
        print(f"drawing from {RECORD}")
    else:
        # The atlas directories are gitignored, so a checkout may hold the
        # record and only some of the runs. Measuring must never shrink the
        # record: keys for runs whose atlases are absent here are carried
        # over from the file, and only the runs measured now are replaced.
        if os.path.isfile(RECORD):
            with open(RECORD, encoding="utf-8") as fh:
                kept = json.load(fh).get("pairs", {})
            for key, value in kept.items():
                record.setdefault(key, value)
        payload = {"_comment": "Generated by viz/relational_widths.py from the plain and monospace "
                               "atlases of the two registered relational-transfer runs, plus the "
                               "per-arm summaries of the Mi controls, dose series and replications "
                               "(keys other than the pairs). Per-cell ink widths over the 92 cells "
                               "not drawn in the reference; the summary numbers the 2026-09-12 and "
                               "2026-09-13 notes quote.",
                   "moved_px": MOVED_PX, "group": GROUP, "pairs": record}
        with open(RECORD, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=1)
        print(f"wrote {RECORD}")
        for key in [k for k in record if k not in PAIR_KEYS]:
            for arm, s in record[key].items():
                print(f"{key}/{arm:<18} cv {s['cv_plain']:.3f} -> {s['cv_mono']:.3f}  mean "
                      f"{s['mean_plain']:.1f} -> {s['mean_mono']:.1f}  sd {s['sd_plain']:.1f} -> "
                      f"{s['sd_mono']:.1f}  ink {s['ink_pixels_change']:+.1%}  fill "
                      f"{s['fill_plain']:.3f} -> {s['fill_mono']:.3f}  affine "
                      f"{s['affine_fit']['intercept']:.1f} + {s['affine_fit']['slope']:.2f} x")
        for pair in [p for p in record if p in PAIR_KEYS]:
            s = record[pair]
            print(f"{pair}: cv {s['cv_plain']:.3f} -> {s['cv_mono']:.3f}  mean {s['mean_plain']:.1f} -> "
                  f"{s['mean_mono']:.1f}  sd {s['sd_plain']:.1f} -> {s['sd_mono']:.1f}  "
                  f"narrowed/widened/within {s['narrowed']}/{s['widened']}/{s['within']}")
            print(f"   widest {GROUP} ({s['widest']['chars']}): {s['widest']['mean_plain']:.1f} -> "
                  f"{s['widest']['mean_mono']:.1f}")
            print(f"   narrowest {GROUP} ({s['narrowest']['chars']}): {s['narrowest']['mean_plain']:.1f} -> "
                  f"{s['narrowest']['mean_mono']:.1f}")
            f = s["affine_fit"]
            print(f"   affine mono = {f['intercept']:.2f} + {f['slope']:.3f} plain, R2 {f['r2']:.3f};  "
                  f"ink pixels {s['ink_pixels_change']:+.1%}; fill {s['fill_plain']:.3f} -> {s['fill_mono']:.3f}")
    draw({k: v for k, v in record.items() if k in PAIR_KEYS})
    return 0


if __name__ == "__main__":
    sys.exit(main())
