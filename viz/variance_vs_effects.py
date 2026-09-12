"""Plot the run-to-run noise against every effect this project ever claimed.

TOP    three training runs whose configs are identical except `--seed`.
       char_acc lands at 0.4914 / 0.6070 / 0.5869. Nothing distinguishes them
       but the shuffle order.

BOTTOM every claim scored on every metric, each divided by THAT metric's own
       run-to-run SD. Columns are ordered by that SD, most stable first, so
       resolvability falls left to right -- and the saturated cells collect on
       the left, on the two metrics nobody was chasing.

Read it honestly. This is NOT "nothing resolves". Six cells clear 2xSE, and
five of them are regressions. What does not resolve is char_acc and dinov2 --
the two metrics every headline in this repo was quoted against.

sigma rests on 2 df with a ~12x-wide CI. xSE ranks claims; it does not
establish them.

  python viz/variance_vs_effects.py
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from viz._common import ensure_out  # noqa: E402

LEDGER = os.path.join(REPO, "research", "claim_ledger.json")
VARIANCE = os.path.join(REPO, "research", "training_variance_{}.json")

SURFACE = "#121214"
INK = "#ffffff"
INK_2 = "#c3c2b7"
MUTED = "#898781"
GRIDLINE = "#2c2c2a"
BLUE = "#3987e5"      # improvement
RED = "#e66767"       # regression
NEUTRAL = "#383835"   # diverging midpoint -- recedes toward the surface

# Colour saturates at this |xSE|; the exact value is printed in every cell, so
# clipping costs no information. rank64+oversampling reaches -13.5 and would
# otherwise flatten every other cell to grey.
CLIP = 4.0
RESOLVE = 2.0         # the bar an effect must clear to be called resolvable

CMAP = LinearSegmentedColormap.from_list("regression_improvement",
                                         [RED, NEUTRAL, BLUE])


def load():
    ledger = json.load(open(LEDGER, encoding="utf-8"))
    sd = ledger["training_sd"]
    # Most stable metric first. This ordering is the argument: everything that
    # resolves lives at the left end.
    metrics = sorted(sd, key=lambda m: sd[m])
    claims = ledger["claims"]
    var = json.load(open(VARIANCE.format("char_acc"), encoding="utf-8"))
    return metrics, sd, claims, var


def draw_runs(ax, var):
    means = var["run_means"]
    lo, hi = min(means), max(means)
    ax.set_xlim(lo - 0.055, hi + 0.055)
    ax.set_ylim(-1.0, 1.25)

    ax.plot(means, [0] * len(means), "o", ms=13, color=BLUE,
            markeredgecolor=SURFACE, markeredgewidth=2, zorder=3)
    for m in means:
        ax.annotate(f"{m:.4f}", (m, 0), textcoords="offset points",
                    xytext=(0, -22), ha="center", color=INK, fontsize=11)

    ax.annotate("", xy=(lo, 0.72), xytext=(hi, 0.72),
                arrowprops=dict(arrowstyle="|-|,widthA=0.4,widthB=0.4",
                                color=MUTED, lw=1.2))
    # Quote the stored gap, not hi-lo: run_means are rounded for the record, so
    # recomputing here prints 0.1156 against the 0.1157 every doc cites.
    ax.text((lo + hi) / 2, 0.86,
            f"{var['largest_observed_gap']:.4f} apart  —  SD {var['run_mean_sd']:.4f}",
            ha="center", color=INK_2, fontsize=11)

    ax.set_title("Three training runs. Identical config. Only --seed differs.",
                 color=INK, fontsize=14, fontweight="bold", loc="left", pad=12)
    ax.text(0, 1.30, "holdout char_acc, 48 fonts", transform=ax.transAxes,
            color=MUTED, fontsize=10.5, va="bottom")

    for side in ("left", "right", "top"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRIDLINE)
    ax.set_yticks([])
    ax.tick_params(axis="x", colors=MUTED, labelsize=10, length=3)


def draw_grid(ax, metrics, sd, claims):
    n_rows, n_cols = len(claims), len(metrics)
    norm = TwoSlopeNorm(vmin=-CLIP, vcenter=0.0, vmax=CLIP)

    for r, claim in enumerate(claims):
        for c, metric in enumerate(metrics):
            cell = claim["metrics"].get(metric)
            if cell is None:
                continue
            x_se = cell["x_se"]
            colour = CMAP(norm(max(-CLIP, min(CLIP, x_se))))
            # 2px surface gap between fills, per the mark spec.
            ax.add_patch(Rectangle((c + 0.03, r + 0.03), 0.94, 0.94,
                                   facecolor=colour, edgecolor=SURFACE,
                                   linewidth=2, zorder=2))
            if abs(x_se) >= RESOLVE:
                # Secondary encoding: what resolves is ringed, not just coloured.
                ax.add_patch(Rectangle((c + 0.03, r + 0.03), 0.94, 0.94,
                                       facecolor="none", edgecolor=INK,
                                       linewidth=1.6, zorder=4))
            label = f"{x_se:+.1f}"
            if label in ("+0.0", "-0.0"):
                label = "0.0"          # a rounded zero has no sign to report
            ax.text(c + 0.5, r + 0.5, label, ha="center", va="center",
                    color=INK if abs(x_se) >= 1.2 else MUTED,
                    fontsize=11, fontweight="bold" if abs(x_se) >= RESOLVE else "normal",
                    zorder=5)

    ax.set_xlim(0, n_cols)
    ax.set_ylim(n_rows, 0)
    ax.set_xticks([c + 0.5 for c in range(n_cols)])
    ax.set_xticklabels([f"{m}\nSD {sd[m]:.4f}" for m in metrics])
    ax.set_yticks([r + 0.5 for r in range(n_rows)])
    ax.set_yticklabels([c["claim"] for c in claims])
    ax.tick_params(axis="both", colors=INK_2, labelsize=10.5, length=0)
    ax.xaxis.set_ticks_position("top")
    for side in ("left", "right", "top", "bottom"):
        ax.spines[side].set_visible(False)

    ax.set_title("Every claim ÷ that metric's own run-to-run SD",
                 color=INK, fontsize=14, fontweight="bold", loc="left", pad=44)
    return norm


def main():
    metrics, sd, claims, var = load()

    fig = plt.figure(figsize=(10.6, 9.4), dpi=100, facecolor=SURFACE)
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 3.5], hspace=0.42,
                          left=0.20, right=0.965, top=0.90, bottom=0.175)
    ax_runs = fig.add_subplot(gs[0], facecolor=SURFACE)
    ax_grid = fig.add_subplot(gs[1], facecolor=SURFACE)

    draw_runs(ax_runs, var)
    norm = draw_grid(ax_grid, metrics, sd, claims)

    fig.text(0.20, 0.128,
             "Columns ordered by stability. Everything that resolves sits at "
             "the left end —",
             color=INK_2, fontsize=10.5)
    fig.text(0.20, 0.104,
             "char_acc and dinov2, the two metrics every headline was quoted "
             "against, resolve nothing.",
             color=INK_2, fontsize=10.5)

    cax = fig.add_axes([0.20, 0.043, 0.36, 0.015])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=CMAP), cax=cax,
                      orientation="horizontal")
    cb.set_ticks([-CLIP, -RESOLVE, 0, RESOLVE, CLIP])
    cb.set_ticklabels([f"≤ -{CLIP:.0f}", "-2", "0", "+2", f"≥ +{CLIP:.0f}"])
    cb.ax.tick_params(colors=MUTED, labelsize=9.5, length=0)
    cb.outline.set_visible(False)
    cb.set_label("regression  ←   xSE   →  improvement",
                 color=INK_2, fontsize=10)

    fig.text(0.615, 0.055,
             "□ ringed = |xSE| ≥ 2, the resolvability bar",
             color=INK_2, fontsize=10)
    fig.text(0.615, 0.031,
             "LPIPS sign flipped, so + is always better",
             color=MUTED, fontsize=9.5)

    ensure_out()
    out = os.path.join(REPO, "viz", "out", "variance_vs_effects.png")
    fig.savefig(out, facecolor=SURFACE)
    print(f"wrote {out}")

    resolved = [(c["claim"], m, c["metrics"][m]["x_se"])
                for c in claims for m in metrics
                if m in c["metrics"] and abs(c["metrics"][m]["x_se"]) >= RESOLVE]
    print(f"\n{len(resolved)} of {len(claims) * len(metrics)} cells clear {RESOLVE:.0f}xSE:")
    for claim, metric, x in sorted(resolved, key=lambda t: t[2]):
        print(f"  {claim:<26} {metric:<10} {x:+6.1f}"
              f"  {'REGRESSION' if x < 0 else 'improvement'}")


if __name__ == "__main__":
    main()
