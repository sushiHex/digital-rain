"""The cosine LR schedule that never annealed, drawn from the training logs.

`--steps` counts MICROBATCHES. The scheduler advances once per OPTIMIZER step.
At `bs=1 accum=2 steps=5000` the run therefore took 2,500 updates against a
5,000-step horizon, and stopped half way down the cosine -- at 51.6% of peak
rather than at zero.

Both curves are parsed out of real logs, not modelled:

  glyph_4b.log        the bug, ending at lr 5.16e-05
  glyph_4b_lrfix.log  the fix, same 5000 steps, ending at lr 0.00e+00

Nothing in the loss curve shows this. Over the last 50 logged points the buggy
run averages 0.0406 against the fixed run's 0.0416 -- it ends at LOWER training
loss, which is what a permanently-high learning rate looks like when you are
only watching the training objective. (Quoted as a tail mean, not as the final
log line: one point off a series that swings 0.03-0.07 establishes nothing,
which is the mistake this whole repo exists to document.)

Every checkpoint produced before 2026-08-08 carries the bug.
`--legacy-lr-horizon` reproduces it on purpose.

  python viz/lr_horizon_bug.py
"""
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from viz._common import ensure_out  # noqa: E402

SURFACE = "#121214"
INK = "#ffffff"
INK_2 = "#c3c2b7"
MUTED = "#898781"
GRIDLINE = "#2c2c2a"
BUG = "#d95926"       # categorical slot 2
FIXED = "#3987e5"     # categorical slot 1

STEP_RE = re.compile(r"step\s*(\d+)/(\d+) \| loss ([0-9.]+) \| lr ([0-9.e+-]+)")

RUNS = [
    ("glyph_4b.log", "the bug — horizon in microbatches", BUG),
    ("glyph_4b_lrfix.log", "the fix — horizon in optimizer steps", FIXED),
]


WINDOW = 21          # rolling-mean width over logged points, in log lines
TAIL = 50            # logged points averaged for the end-of-run loss comparison


def rolling_mean(xs, ys, window):
    """Centred rolling mean, trimmed to the fully-covered span."""
    if len(ys) < window:
        return xs, ys
    kernel = np.ones(window) / window
    smoothed = np.convolve(np.asarray(ys, dtype=float), kernel, mode="valid")
    half = window // 2
    return xs[half:half + len(smoothed)], smoothed


def parse(path):
    """Pull (step, loss, lr) triples out of a training log."""
    steps, losses, lrs = [], [], []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = STEP_RE.search(line)
            if m:
                steps.append(int(m.group(1)))
                losses.append(float(m.group(3)))
                lrs.append(float(m.group(4)))
    if not steps:
        raise SystemExit(f"no step lines parsed from {path}")
    return steps, losses, lrs


def main():
    series = []
    for name, label, colour in RUNS:
        path = os.path.join(REPO, name)
        if not os.path.isfile(path):
            raise SystemExit(f"missing training log: {path}")
        steps, losses, lrs = parse(path)
        series.append((name, label, colour, steps, losses, lrs))

    peak = max(max(s[5]) for s in series)

    fig, (ax, ax_loss) = plt.subplots(
        2, 1, figsize=(10.2, 7.4), dpi=100, facecolor=SURFACE,
        gridspec_kw=dict(height_ratios=[2.3, 1.0], hspace=0.34,
                         left=0.105, right=0.955, top=0.855, bottom=0.115))

    for name, label, colour, steps, losses, lrs in series:
        ax.plot(steps, lrs, lw=2, color=colour, label=label, zorder=3)
        # Raw loss is two overlapping noise bands and reads as a hairball; the
        # rolling mean is what makes "these two runs are indistinguishable"
        # legible rather than merely crowded.
        ax_loss.plot(steps, losses, lw=0.7, color=colour, alpha=0.16, zorder=2)
        sm_steps, sm_losses = rolling_mean(steps, losses, WINDOW)
        ax_loss.plot(sm_steps, sm_losses, lw=1.8, color=colour, zorder=3)

    # The gap between the two curves is the annealing that never happened.
    bug_steps, bug_lrs = series[0][3], series[0][5]
    fix_lrs = series[1][5]
    n = min(len(bug_lrs), len(fix_lrs))
    ax.fill_between(bug_steps[:n], fix_lrs[:n], bug_lrs[:n],
                    color=BUG, alpha=0.13, zorder=1, linewidth=0)

    end_step, end_lr = bug_steps[-1], bug_lrs[-1]
    ax.plot([end_step], [end_lr], "o", ms=9, color=BUG,
            markeredgecolor=SURFACE, markeredgewidth=2, zorder=4)
    ax.annotate(f"stops at {end_lr:.2e}\n{end_lr / peak:.1%} of peak",
                xy=(end_step, end_lr), xytext=(-32, 34),
                textcoords="offset points", ha="right", color=INK, fontsize=11,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
    ax.plot([end_step], [0], "o", ms=9, color=FIXED,
            markeredgecolor=SURFACE, markeredgewidth=2, zorder=4)
    ax.annotate("reaches 0.00e+00", xy=(end_step, 0), xytext=(-32, 26),
                textcoords="offset points", ha="right", color=INK, fontsize=11,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))

    ax.set_title("The cosine schedule never annealed",
                 color=INK, fontsize=15, fontweight="bold", loc="left", pad=52)
    ax.text(0, 1.012,
            "--steps counts microbatches; the scheduler advances per optimizer step.\n"
            "At accum=2 the run got half the horizon it asked for.",
            transform=ax.transAxes, color=MUTED, fontsize=10.5, va="bottom",
            linespacing=1.5)
    ax.set_ylabel("learning rate", color=INK_2, fontsize=11)
    leg = ax.legend(loc="lower left", frameon=False, fontsize=11,
                    labelcolor=INK_2)
    leg.set_zorder(5)

    ax_loss.set_title("Training loss over the same steps — the bug is invisible here",
                      color=INK_2, fontsize=11.5, loc="left", pad=8)
    ax_loss.set_ylabel("loss", color=INK_2, fontsize=11)
    ax_loss.set_xlabel("microbatch step", color=INK_2, fontsize=11)
    # A single final log line is one draw from a visibly noisy series; quote the
    # mean of the last TAIL points instead, or this figure repeats the
    # single-sample mistake it exists to document.
    tail_bug = float(np.mean(series[0][4][-TAIL:]))
    tail_fix = float(np.mean(series[1][4][-TAIL:]))
    ax_loss.text(0.985, 0.86,
                 f"mean loss over the last {TAIL} logged points   "
                 f"{tail_bug:.4f} (bug)  vs  {tail_fix:.4f} (fix)",
                 transform=ax_loss.transAxes, ha="right", color=MUTED,
                 fontsize=10)

    for a in (ax, ax_loss):
        a.set_facecolor(SURFACE)
        a.grid(True, color=GRIDLINE, lw=0.8, zorder=0)
        a.set_axisbelow(True)
        for side in ("top", "right"):
            a.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            a.spines[side].set_color(GRIDLINE)
        a.tick_params(colors=MUTED, labelsize=10)

    ensure_out()
    out = os.path.join(REPO, "viz", "out", "lr_horizon_bug.png")
    fig.savefig(out, facecolor=SURFACE)
    print(f"wrote {out}")
    for name, label, _, steps, losses, lrs in series:
        print(f"  {name:<22} {len(steps):>4} points  peak {max(lrs):.2e}  "
              f"final lr {lrs[-1]:.2e}  final loss {losses[-1]:.4f}  "
              f"last-{TAIL} mean {np.mean(losses[-TAIL:]):.4f}")
    print(f"\n  the bug stopped at {end_lr / peak:.1%} of peak learning rate")
    print(f"  loss over the last {TAIL} points: {tail_bug:.4f} (bug) vs "
          f"{tail_fix:.4f} (fix) -- delta {tail_bug - tail_fix:+.4f}")


if __name__ == "__main__":
    main()
