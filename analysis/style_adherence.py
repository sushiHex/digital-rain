"""Did the model produce the style that was ASKED FOR?

=== VERDICT, 2026-08-24: THIS DOES NOT WORK. KEPT AS THE RECORD. ===

The approach below was ruled out by a PRE-REGISTERED minimal-pair test --
`style_adherence_minimal_pairs.py`, committed before it was run. Pairing each
prompt with a negative differing in ONE decisive attribute, the own prompt won
6 of 12, exact binomial p=0.6128: exactly chance. Flipping the decisive clause
moves cosine by +/-0.001 to +/-0.036, about 1% of a ~0.24 baseline.

Do NOT run another statistic over this 12x12 matrix, and do not read `--score`
as a gate. Both backbones are already tested (ViT-B-32 is exactly chance;
ViT-L-14 reaches 17% top-1 against an 8% floor), so "try a bigger model" is a
closed question here. The next candidate is FontCLIP (arXiv 2403.06453) or a
per-attribute discriminative classifier trained on rendered real fonts.

`research/2026-08-24-clip-does-not-read-the-decisive-clause.md`

THE LAST UNMEASURED AXIS. This project now has two ground-truth-free
instruments, and neither answers this question:

  reference_gate.py    do the two glyphs AGREE with each other?     (coherence)
  glyph_classifier.py  are they the right LETTERS?                  (identity)
  --                   is it the TYPEFACE that was requested?       (nothing)

The gap is not hypothetical. In `2026-08-23-the-loop-closes.md`, the prompt
"a stencil sans with deliberate breaks in the strokes" produced a solid face
with no breaks at all, at BOTH the reference and the atlas stage -- and every
metric available called it excellent. Coherence says the font hangs together.
Identity says the letters are right. Nothing said it was the wrong font.

WHY THIS ONE IS A DIFFERENT SHAPE. Coherence and identity are SELF-CONSISTENCY
measures: they read the image alone. Adherence is an ALIGNMENT measure -- it has
to compare the image against the text that asked for it. That is CLIP's native
job, so this is a text-image similarity, not another statistic over glyph
features.

WHAT IS EMBEDDED, AND WHY NOT THE WHOLE PROMPT. The generation prompt is mostly
boilerplate -- "on a plain solid black background", "pure white on black",
"no shadow" -- identical across every candidate. Embedding it whole would make
all twelve texts near-identical and destroy the discrimination being measured.
Only the STYLE CLAUSE is embedded, under a short typographic prefix.

THE VALIDATION, which is the point. Twelve images and twelve prompts give
twelve correct pairings and 132 wrong ones, for free and with no generation. A
measure that works must rank an image's OWN prompt first. Chance top-1 is 1/12
= 8.3%. Anything near that means CLIP does not have the typographic vocabulary
for this, which is a real possibility worth finding out cheaply: CLIP was
trained on natural images with everyday captions, and an isolated white-on-black
letterform described as "a high-contrast didone with vertical stress" is far
from that distribution.

  python analysis/style_adherence.py --validate
  python analysis/style_adherence.py --score eval_runs/_candidate_refs/flux2-klein-base
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import json
import os

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATES = os.path.join(REPO, "eval_runs", "_candidate_refs", "flux2-klein-base")
SPEC = os.path.join(REPO, "research", "candidate_references.json")

# Mid-size and widely mirrored. Bigger backbones may hold more typographic
# vocabulary; --model exists so that is testable rather than assumed.
DEFAULT_MODEL = "ViT-B-32"
DEFAULT_PRETRAINED = "laion2b_s34b_b79k"

# A short typographic frame. CLIP responds to a phrase, not a bare noun list,
# and naming the domain ("typeface", "letterforms") is what steers it away from
# reading these as abstract shapes.
TEXT_TEMPLATE = "a typeface specimen of letterforms: {style}"


def win_rates(sim, perm=None):
    """Per-image rate at which the assigned prompt beats the other prompts.

    Ties score HALF. Strict `>` charged every tie as a loss, which matters here
    because n-1 comparisons make the statistic coarse and tie-prone.

    This is a RANKING statistic, not an absolute score: with no ties it equals
    (n - rank) / (n - 1) exactly. Recording that plainly because an earlier
    version of this file claimed it was a different question from ranking, and
    it is not.
    """
    sim = np.asarray(sim, dtype=float)
    n = len(sim)
    perm = np.arange(n) if perm is None else np.asarray(perm)
    return np.array([
        np.mean([(sim[i, perm[i]] > sim[i, perm[j]])
                 + 0.5 * (sim[i, perm[i]] == sim[i, perm[j]])
                 for j in range(n) if j != i])
        for i in range(n)])


def permutation_p(sim, iters=20000, seed=0):
    """Is THIS image<->prompt assignment unusually aligned?

    Permutes the bijection, preserving the whole matrix and the shared prompts.
    No distributional assumption, unlike the Wilcoxon this replaced. The +1s are
    the standard finite-sample correction, so p can never be reported as 0.
    """
    sim = np.asarray(sim, dtype=float)
    n = len(sim)
    rng = np.random.default_rng(seed)
    obs = float(win_rates(sim).mean())
    null = np.array([float(win_rates(sim, rng.permutation(n)).mean())
                     for _ in range(iters)])
    return obs, float(((null >= obs).sum() + 1) / (len(null) + 1))


def load_clip(model_name, pretrained, device="cuda"):
    import open_clip
    import torch
    model, _, preprocess = open_clip.create_model_and_transforms(
        model_name, pretrained=pretrained, device=device)
    model.eval()
    return model, preprocess, open_clip.get_tokenizer(model_name), torch


def embed(paths, styles, model_name, pretrained, device="cuda"):
    """Returns (image_embeddings, text_embeddings), both L2-normalised."""
    model, preprocess, tokenizer, torch = load_clip(model_name, pretrained, device)
    with torch.no_grad():
        ims = torch.stack([preprocess(Image.open(p).convert("RGB"))
                           for p in paths]).to(device)
        img = model.encode_image(ims)
        img = img / img.norm(dim=-1, keepdim=True)

        toks = tokenizer([TEXT_TEMPLATE.format(style=s) for s in styles]).to(device)
        txt = model.encode_text(toks)
        txt = txt / txt.norm(dim=-1, keepdim=True)
    return img.float().cpu().numpy(), txt.float().cpu().numpy()


def validate(model_name, pretrained):
    """Cross-pair every image against every prompt. The correct one must win."""
    if not os.path.isfile(SPEC):
        print(f"missing {SPEC} -- run generate_candidate_references.py first",
              file=_sys.stderr)
        return None
    spec = json.load(open(SPEC, encoding="utf-8"))
    styles = spec["styles"]

    paths = sorted(glob.glob(os.path.join(CANDIDATES, "*.png")))
    if len(paths) != len(styles):
        print(f"have {len(paths)} images for {len(styles)} styles; the "
              "cross-pairing needs them aligned by index", file=_sys.stderr)
        return None

    img, txt = embed(paths, styles, model_name, pretrained)
    sim = img @ txt.T                       # (n_images, n_prompts)
    n = len(styles)

    ranks, top1 = [], 0
    print(f"\nstyle adherence, {model_name}/{pretrained}\n")
    print(f"  {'prompt (its own image)':<46} {'own':>7} {'best':>7} {'rank':>5}")
    for i in range(n):
        order = np.argsort(-sim[i])
        rank = int(np.where(order == i)[0][0]) + 1
        ranks.append(rank)
        top1 += rank == 1
        best = int(order[0])
        flag = "" if rank == 1 else f"  <- reads as #{best:02d}"
        print(f"  {styles[i][:44]:<46} {sim[i, i]:>7.3f} "
              f"{sim[i, best]:>7.3f} {rank:>5}{flag}")

    # THE PAIRED TEST, which is the question the product actually asks.
    #
    # The ranking test above demands the correct prompt beat ELEVEN rivals. The
    # product never asks that: it asks "does this image match ITS prompt", which
    # is a within-image comparison against wrong prompts. Comparing within one
    # image also removes the confound that sank the cross-image reading -- some
    # images are generically more CLIP-friendly than others, and that offset
    # cancels when both scores come from the same image.
    #
    # Clustered by IMAGE, not by pair. The 132 pairs share 12 images and are not
    # independent; a plain binomial over them reports p=6e-07 and is wrong for
    # the same reason cell-bootstrapping was wrong in eval_checkpoint.
    # Extracted to win_rates()/permutation_p() so the estimator is TESTABLE
    # without CLIP or images. The previous tests only read recorded JSON and
    # never executed the statistic at all.
    per_image = win_rates(sim)
    obs, paired_p = permutation_p(sim)
    paired_ok = obs > 0.5 and paired_p < 0.05

    mrr = float(np.mean([1.0 / r for r in ranks]))
    chance = 1.0 / n
    print(f"\n  PAIRED (the product's question): the correct prompt beats a wrong")
    print(f"  one {per_image.mean():.1%} of the time, median {np.median(per_image):.1%}, "
          f"{(per_image > 0.5).sum()}/{n} images above chance")
    print(f"  permutation over image<->prompt assignments p={paired_p:.4f}  ->  "
          f"{'non-random pairing' if paired_ok else 'not distinguishable'}")
    print(f"\n  RANKING (a stricter bar, kept for the record):")
    print(f"  top-1 {top1}/{n} = {top1/n:.0%}   (chance {chance:.0%})")
    print(f"  mean reciprocal rank {mrr:.3f}   (chance {np.mean([1/r for r in range(1, n+1)]):.3f})")
    works = top1 / n >= 0.5
    print(f"\n  ranking verdict: {'usable' if works else 'NOT usable'}")
    if not works:
        print("  CLIP cannot pick one prompt from twelve. See FontCLIP")
        print("  (arXiv 2403.06453) for a model adapted to font attributes.")
    # NOT "usable". A significant permutation result is an ASSOCIATION on this
    # fixed set; a usable gate needs a held-out threshold and error rates, and
    # this has neither. Calling significance "usable" pinned a category error
    # into application language.
    print(f"  association on this set: "
          f"{'PRESENT' if paired_ok else 'not detected'}"
          "  -- NOT a validated gate; no threshold, no held-out error rates")
    print("  Note this is still a RANKING statistic: win_rate == (n-rank)/(n-1)")
    print("  exactly, so it is not the absolute per-image score a gate needs.")

    # Where the paired test 'fails' is worth reading before calling it a flaw:
    # the images it cannot match to their own prompt are largely the ones whose
    # STYLE GENERATION failed. A measure that matched a solid face to "stencil
    # with deliberate breaks" would be broken, not working.
    weak = [styles[i][:40] for i in range(n) if per_image[i] <= 0.5]
    if weak:
        print("\n  images the measure could not match to their own prompt:")
        for s in weak:
            print(f"    {s}")
        print("  Check these against whether the GENERATION missed the style.")

    return {"model": f"{model_name}/{pretrained}", "n": n,
            "top1": top1 / n, "mrr": mrr, "chance_top1": chance,
            "ranks": ranks, "usable": bool(works),
            "paired_win_rate": float(per_image.mean()),
            "paired_p": paired_p, "paired_usable": bool(paired_ok),
            "per_image_win_rate": [float(v) for v in per_image],
            "similarity": sim.tolist(), "styles": styles,
            "images": [os.path.basename(p) for p in paths]}


def score(directory, model_name, pretrained):
    """Score a directory of references against the style prompts they came from."""
    spec = json.load(open(SPEC, encoding="utf-8"))
    styles = spec["styles"]
    paths = sorted(glob.glob(os.path.join(directory, "*.png")))
    if len(paths) != len(styles):
        print("image count does not match the prompt list", file=_sys.stderr)
        return None
    img, txt = embed(paths, styles, model_name, pretrained)
    sim = img @ txt.T
    own = np.diag(sim).copy()
    n = len(styles)

    # THE VALIDATED QUANTITY IS THE ROW-RELATIVE ONE, NOT RAW COSINE. An earlier
    # version returned raw diagonal cosine here while validate() tested a
    # row-relative statistic -- so the deployed number was not the measured one.
    # Raw cosine is also prompt-confounded: column means span 0.202-0.263 and
    # "condensed grotesque" is the top match for 11 of 12 images, so a low
    # diagonal can mean the PROMPT scores low against everything rather than
    # that this image failed. Ties count as half, not as losses.
    win = np.array([
        np.mean([(sim[i, i] > sim[i, j]) + 0.5 * (sim[i, i] == sim[i, j])
                 for j in range(n) if j != i])
        for i in range(n)])

    print(f"\n  {'image':<38} {'raw cos':>8} {'win rate':>9}")
    for p, c, w in zip(paths, own, win):
        print(f"  {os.path.basename(p)[:36]:<38} {c:>8.3f} {w:>9.2f}")
    print(f"\n  mean raw cosine {own.mean():.3f}   mean win rate {win.mean():.3f}")
    print("\n  NEITHER IS A CALIBRATED GATE. There is no held-out threshold, and")
    print("  win rate depends on which decoy prompts are in the bank -- adding or")
    print("  removing prompts changes the score of an unchanged image.")
    return {"raw_cosine": {os.path.basename(p): float(c)
                           for p, c in zip(paths, own)},
            "win_rate": {os.path.basename(p): float(w)
                         for p, w in zip(paths, win)}}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--score", help="directory of references to score")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--pretrained", default=DEFAULT_PRETRAINED)
    ap.add_argument("--json", default=os.path.join(REPO, "research",
                                                   "style_adherence.json"))
    args = ap.parse_args()
    if not (args.validate or args.score):
        ap.error("pass --validate or --score")

    payload = None
    if args.validate:
        payload = validate(args.model, args.pretrained)
        if payload is None:
            return 3
    if args.score:
        payload = score(args.score, args.model, args.pretrained) or payload

    if args.json and payload:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=1)
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
