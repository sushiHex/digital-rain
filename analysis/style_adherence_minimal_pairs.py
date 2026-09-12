"""Does CLIP read the DECISIVE clause, or just "typeface-ness"?

PRE-REGISTERED. This file was written and committed BEFORE the numbers were
seen. That is a direct response to an adversarial review which established that
the previous style-adherence result was an outcome-generated hypothesis: I set a
bar, failed it, ran a second statistic on the same matrix, passed, and defended
it with a distinction that turned out to be false
(`win_rate == (n-rank)/(n-1)` exactly). See the retraction in
`research/2026-08-24-style-adherence-the-wrong-formulation-failed.md`.

THE QUESTION. The cross-pair test could be passed by generic typeface-likeness:
"condensed grotesque" was the top match for 11 of 12 images, and prompt-column
means span 0.202-0.263, so a prompt can score low against EVERYTHING. Neither
result showed that CLIP reads the clause that actually decides the style.

A minimal pair isolates exactly that. Each negative below differs from its
prompt in ONE decisive attribute and shares the rest of the wording, so the
column-baseline confound largely cancels:

    stencil, deliberate breaks   vs   solid, unbroken continuous strokes
    ultra-light, thin strokes    vs   ultra-bold, thick strokes
    inline, white stripe inset   vs   solid, filled, no stripe

If CLIP cannot tell "with deliberate breaks" from "unbroken", it is not reading
the decisive clause, and no amount of further statistics rescues the approach.

=== PRE-REGISTRATION, fixed before running ===

HYPOTHESIS       For each image, sim(image, own prompt) > sim(image, its
                 minimal-pair negative).
STATISTIC        Number of images where the own prompt wins, out of 12.
TEST             Exact binomial, one-sided, H0: p = 0.5. Ties score as losses,
                 which is conservative for the hypothesis.
BAR              p < 0.05 => CLIP reads the decisive attribute.
                 Otherwise it does not, and this line of work stops.
MODEL            ViT-L-14 / laion2b_s32b_b82k. Fixed: the better of the two
                 already measured. No other backbone will be tried on this data.
TEMPLATE         `style_adherence.TEXT_TEMPLATE`, unchanged.
SECONDARY        Per-attribute breakdown is DESCRIPTIVE ONLY and carries no
                 claim. No other analysis will be run on this data.
IF IT FAILS      Reported as a failure. FontCLIP or a domain-adapted model is
                 the next candidate, not another statistic over this matrix.

  python analysis/style_adherence_minimal_pairs.py
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import json
import os

import numpy as np

from analysis.style_adherence import CANDIDATES, SPEC, TEXT_TEMPLATE, embed

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL, PRETRAINED = "ViT-L-14", "laion2b_s32b_b82k"

# One decisive attribute flipped, wording otherwise held as close as possible.
# Index-aligned with candidate_references.json["styles"].
NEGATIVES = [
    ("weight",   "a light geometric sans serif, open apertures, flat terminals"),
    ("contrast", "a low-contrast face with uniform-width serifs and no stress"),
    ("serifs",   "a chunky sans serif with no serifs at all"),
    ("aperture", "a humanist sans with closed apertures and a vertical axis"),
    ("width",    "an extended grotesque, wide spacing, large x-height"),
    ("terminal", "an angular hard sans with sharply cut stroke ends"),
    ("spacing",  "a wide low-contrast proportional face with prominent spurs"),
    ("weight",   "an ultra-bold heavy sans, uniform thick strokes"),
    ("terminal", "a wedge-serif face with blunt, straight-cut terminals"),
    ("breaks",   "a solid sans with unbroken continuous strokes"),
    ("inline",   "a solid face with filled strokes and no inline stripe"),
    ("terminal", "a heavy rounded humanist sans with soft curved terminals"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", default=os.path.join(REPO, "research",
                                                   "style_adherence_minimal_pairs.json"))
    args = ap.parse_args()

    from scipy import stats

    styles = json.load(open(SPEC, encoding="utf-8"))["styles"]
    paths = sorted(glob.glob(os.path.join(CANDIDATES, "*.png")))
    if len(paths) != len(styles) or len(NEGATIVES) != len(styles):
        print("images, styles and negatives must be index-aligned",
              file=_sys.stderr)
        return 2

    # Embed positives and negatives together so both use one identical pass.
    texts = list(styles) + [neg for _, neg in NEGATIVES]
    img, txt = embed(paths, texts, MODEL, PRETRAINED)
    n = len(styles)
    pos = np.array([img[i] @ txt[i] for i in range(n)])
    neg = np.array([img[i] @ txt[n + i] for i in range(n)])

    wins = int((pos > neg).sum())                 # ties count as losses
    p = float(stats.binomtest(wins, n, 0.5, alternative="greater").pvalue)

    print(f"\nminimal-pair forced choice, {MODEL}/{PRETRAINED}\n")
    print(f"  {'attribute':<10} {'own':>7} {'neg':>7} {'margin':>8}  prompt")
    for i, (attr, _) in enumerate(NEGATIVES):
        mark = " " if pos[i] > neg[i] else "X"
        print(f"{mark} {attr:<10} {pos[i]:>7.3f} {neg[i]:>7.3f} "
              f"{pos[i]-neg[i]:>+8.3f}  {styles[i][:40]}")

    print(f"\n  own prompt wins {wins}/{n}   exact binomial p = {p:.4f}")
    passed = p < 0.05
    print(f"  PRE-REGISTERED BAR p<0.05: {'PASSED' if passed else 'FAILED'}")
    if not passed:
        print("\n  CLIP does not read the decisive clause. Per the registration,")
        print("  this line stops here; a domain-adapted model (FontCLIP) is the")
        print("  next candidate, not another statistic over this matrix.")

    payload = {"preregistered": True, "model": f"{MODEL}/{PRETRAINED}",
               "n": n, "wins": wins, "p": p, "passed": bool(passed),
               "own": [float(v) for v in pos], "neg": [float(v) for v in neg],
               "attributes": [a for a, _ in NEGATIVES],
               "negatives": [s for _, s in NEGATIVES], "styles": styles}
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
