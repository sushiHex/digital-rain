"""Does the atlas keep the style of the reference the user PICKED?

PRE-REGISTERED. Written and committed before any atlas was generated.

WHY THIS IS THE LAST BLOCKING QUESTION. The picker selects at the reference
stage because that is cheap (~25 s against ~62 s) and because
`reference_stage_adherence.py` showed two glyphs carry the adherence signal.
But the user does not receive the reference. They receive the 94-glyph atlas
generated from it. If the atlas does not track the reference they chose, the
choice was theatre.

The evidence so far is encouraging and indirect: the reference gate predicts
atlas coherence at rho=0.666, and on 2026-08-23 the hairline and inline-stripe
prompts both carried their treatment through the whole chain. Neither is a
measurement of TRANSFER.

THE TEST. Generate an atlas from each of a description's four candidate
references. Then ask, for each atlas, whether it resembles ITS OWN reference
more than the other three of the SAME description. Same description throughout,
so "which words were used" is held constant and only the reference varies.

WHAT IS COMPARED, AND WHY NOT THE OBVIOUS THING. The atlas's own K and g are
excluded. The model is conditioned to copy the two reference glyphs, so matching
an atlas's K to its reference's K is close to trivial and would measure the
conditioning rather than the transfer. The atlas vector is therefore built from
the OTHER 92 CELLS. The question is whether the style reached the letters the
user never saw.

Both sides are z-scored per character and normalised through
`reference_stage_adherence.normalise_like_reference`, so the reference's
rescaled glyphs and the atlas's raw cells live in one space.

=== PRE-REGISTRATION, fixed before running ===

DESCRIPTIONS  The FOUR WIDEST-SPREAD descriptions from
              `research/within_prompt_diversity.json`. This is deliberate and it
              makes the test BEST-CASE: matching is only meaningful when the
              four references actually differ, and spread runs 0.454-3.960, so
              on a narrow description the references are near-identical and
              nothing could match them. Stated here rather than discovered
              later.
SAMPLE        4 descriptions x 4 candidates = 16 atlases, one seed, so the
              arms differ by the REFERENCE only. A per-atlas seed would fold
              the style lottery (SD 0.0248 on the seed main effect) into the
              comparison.
PRIMARY       For each atlas, the rank of its own reference among that
              description's four, by style distance. Chance rank is 2.5 and
              chance P(rank 1) = 0.25.
STATISTIC     Count of rank-1 matches out of 16. Exact binomial, one-sided,
              H0: p = 0.25.
BAR           >= 8 of 16. Exact binomial: 8/16 = 0.0271, 7/16 = 0.0796. Below
              8 is a failure.
IF IT FAILS   Reported as "the atlas does not track the chosen reference". The
              consequence is architectural and is stated, not worked around:
              the picker would have to select at the ATLAS stage, at 4x the
              cost, or the reference choice is decoration.
SECONDARY     Mean rank, and the per-description breakdown. DESCRIPTIVE ONLY.

  python analysis/reference_to_atlas_transfer.py
  python analysis/reference_to_atlas_transfer.py --score-only
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import json
import os
import subprocess
import time

import numpy as np

from analysis.reference_gate import glyph_cells
from analysis.reference_stage_adherence import normalise_like_reference
from analysis.style_coherence import FEATURES, cell_features

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(REPO, "eval_runs", "_candidate_refs", "klein-base-n4")
OUT = os.path.join(REPO, "eval_runs", "_transfer_atlases")
SPREAD = os.path.join(REPO, "research", "within_prompt_diversity.json")

CHECKPOINT = os.path.join("training_glyph_4b_r32_5000", "checkpoint-5000")
MODEL_4B = "black-forest-labs/FLUX.2-klein-base-4B"
REF_CHARS = "Kg"
N_DESCRIPTIONS = 4
NEED_MB = 12000
STEPS, SEED = 20, 42


def free_vram_mb():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30)
        return int(out.stdout.strip().splitlines()[0])
    except Exception:                                  # noqa: BLE001
        return None


def widest_descriptions(n=N_DESCRIPTIONS):
    """The n widest-spread descriptions. Matching needs distinguishable refs.

    EVERY KEY IS VERIFIED AGAINST THE CANDIDATE DIRECTORY, because a key that
    matches no files is a BUG rather than an empty arm. The first run of this
    tool globbed with a key whose trailing underscore had been eaten by
    `split("__")`, matched nothing for the widest-spread description, and
    scored 12 atlases against a registration that said 16 -- without erroring.
    """
    d = json.load(open(SPREAD, encoding="utf-8"))["per_style"]
    keys = [k for k, _ in sorted(d.items(), key=lambda kv: -kv[1]["mean"])[:n]]
    missing = [k for k in keys
               if not glob.glob(os.path.join(REFS, glob.escape(k) + "__s*.png"))]
    if missing:
        raise SystemExit(
            f"no candidate references match {missing}.\n"
            f"The description keys in {SPREAD} do not address files in {REFS}. "
            "Re-run within_prompt_diversity.py; do not score a silently short set.")
    return keys


def reference_vector(path, stats, chars=REF_CHARS):
    """Mean z-scored style vector over a reference's two glyphs."""
    vecs = []
    for ch, cell in zip(chars, glyph_cells(path, len(chars))):
        if cell is None:
            return None
        f, s = cell_features(cell), stats.get(ch)
        if f is None or s is None:
            return None
        vecs.append([(f[k] - s[k]["mean"]) / s[k]["sd"] for k in FEATURES])
    return np.clip(np.asarray(vecs, dtype=float), -8, 8).mean(axis=0)


def atlas_vector(path, stats, exclude=REF_CHARS):
    """Mean z-scored style vector over the atlas cells the user never saw.

    `exclude` drops the reference characters. The model is conditioned to copy
    them, so including them would measure the conditioning, not the transfer.
    """
    from atlas_constants import BLANK_INDICES, CELL_H, CELL_W, CHARSET, GRID_COLS
    from PIL import Image

    arr = np.asarray(Image.open(path).convert("L"))
    vecs = []
    for idx, ch in enumerate(CHARSET):
        if idx in BLANK_INDICES or ch in exclude:
            continue
        r, c = idx // GRID_COLS, idx % GRID_COLS
        cell = arr[r * CELL_H:(r + 1) * CELL_H, c * CELL_W:(c + 1) * CELL_W]
        norm = normalise_like_reference(cell)
        if norm is None:
            continue
        f, s = cell_features(norm), stats.get(ch)
        if f is None or s is None:
            continue
        vecs.append([(f[k] - s[k]["mean"]) / s[k]["sd"] for k in FEATURES])
    if len(vecs) < 40:
        return None
    return np.clip(np.asarray(vecs, dtype=float), -8, 8).mean(axis=0)


def generate(descriptions):
    from conditioning_config import expected_conditioning
    from generation_lib import generate_one_atlas, load_generation_pipe

    free = free_vram_mb()
    if free is not None and free < NEED_MB:
        print(f"refusing to start: {free} MiB free, need {NEED_MB}. The 3090 is "
              "shared -- wait, do not evict.", file=_sys.stderr)
        return None

    wanted = []
    for desc in descriptions:
        wanted.extend(sorted(glob.glob(os.path.join(REFS, glob.escape(desc) + "__s*.png"))))
    todo = [r for r in wanted
            if not os.path.isfile(os.path.join(
                OUT, os.path.splitext(os.path.basename(r))[0] + ".png"))]
    if not todo:
        print(f"  all {len(wanted)} atlases already generated")
        return wanted

    cond = expected_conditioning(CHECKPOINT)
    print(f"conditioning: prompt_style={cond['prompt_style']} "
          f"ref_chars={cond['reference_chars']} use_template={cond['use_template']}")
    pipe, pe, ne = load_generation_pipe(
        CHECKPOINT, use_template=cond["use_template"],
        template_pt=cond["template_pt"], model=MODEL_4B,
        reference_chars=cond["reference_chars"],
        prompt_style=cond["prompt_style"])

    os.makedirs(OUT, exist_ok=True)
    for i, ref in enumerate(todo, 1):
        name = os.path.splitext(os.path.basename(ref))[0]
        t0 = time.time()
        # ONE seed for every atlas: the arms must differ by the REFERENCE only.
        generate_one_atlas(pipe, pe, ne, ref, os.path.join(OUT, name + ".png"),
                           steps=STEPS, seed=SEED)
        print(f"  [{i}/{len(todo)}] {name[:40]:<42} {time.time()-t0:5.1f}s",
              flush=True)
    return wanted


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--json", default=os.path.join(REPO, "research",
                                                   "reference_to_atlas_transfer.json"))
    args = ap.parse_args()

    from scipy import stats as st

    from analysis.style_coherence import load_stats

    descriptions = widest_descriptions()
    print(f"\ndescriptions (widest spread first): {descriptions}\n")
    if not args.score_only and generate(descriptions) is None:
        return 2

    stats = load_stats()
    rows, hits, ranks = [], 0, []
    for desc in descriptions:
        refs = sorted(glob.glob(os.path.join(REFS, glob.escape(desc) + "__s*.png")))
        pairs = []
        for ref in refs:
            name = os.path.splitext(os.path.basename(ref))[0]
            atlas = os.path.join(OUT, name + ".png")
            if not os.path.isfile(atlas):
                continue
            rv, av = reference_vector(ref, stats), atlas_vector(atlas, stats)
            if rv is None or av is None:
                continue
            pairs.append((name, rv, av))
        if len(pairs) < 2:
            continue
        for i, (name, _, av) in enumerate(pairs):
            d = [float(np.linalg.norm(av - rv)) for _, rv, _ in pairs]
            rank = int(np.argsort(np.argsort(d))[i]) + 1
            ok = rank == 1
            hits += ok
            ranks.append(rank)
            rows.append({"description": desc, "candidate": name, "rank": rank,
                         "of": len(pairs), "ok": bool(ok),
                         "own_distance": d[i],
                         "best_distance": float(min(d))})

    n = len(rows)
    if n == 0:
        print("nothing scored", file=_sys.stderr)
        return 2
    p = float(st.binomtest(hits, n, 0.25, alternative="greater").pvalue)

    print(f"  {'description':<34} {'candidate':<6} {'rank':>5} {'own d':>8} "
          f"{'best d':>8}")
    for r in rows:
        print(f"{' ' if r['ok'] else 'X'} {r['description'][:33]:<34} "
              f"{r['candidate'].split('__')[1]:<6} {r['rank']:>2}/{r['of']:<2} "
              f"{r['own_distance']:>8.3f} {r['best_distance']:>8.3f}")

    passed = hits >= 8 and p < 0.05
    print(f"\n  PRIMARY  {hits}/{n} matched their own reference   "
          f"exact binomial p = {p:.4f}   mean rank {np.mean(ranks):.2f} "
          f"(chance 2.50)")
    print(f"  PRE-REGISTERED BAR >=8/16 and p<0.05: "
          f"{'PASSED' if passed else 'FAILED'}")
    if not passed:
        print("\n  THE ATLAS DOES NOT TRACK THE CHOSEN REFERENCE. The picker")
        print("  would have to select at the ATLAS stage, at 4x the cost, or")
        print("  the reference choice is decoration.")

    payload = {"preregistered": True, "bar": "8/16 and p<0.05",
               "descriptions": descriptions, "excluded_chars": REF_CHARS,
               "hits": hits, "n": n, "p": p, "passed": bool(passed),
               "mean_rank": float(np.mean(ranks)), "rows": rows}
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
