"""Best-of-N ceiling analysis: is a model's single-seed char_acc architectural,
or partly variance-bound and recoverable by sampling the SAME model N times?
No cross-model comparison here -- one checkpoint's own seeds only.

The headline number is the WITHIN-RUN headroom (best-of-N ceiling minus this
run's own best single seed), which needs no external baseline and is directly
comparable across checkpoints. Measured so far:

  9B glyph  0.6738 seed0 -> 0.8366 best-of-4   (+0.1628)
  4B glyph  0.6304 seed0 -> 0.7943 best-of-4   (+0.1639)

--official-single-seed additionally compares against a separately measured
seed=42 eval. It MUST match the checkpoint being analyzed: it was previously
hardcoded to the 9B's 0.6883, which silently reported the 4B's ceiling against
the 9B's baseline.

  python analysis/analyze_holdout_bestofn.py bestofn_4b/scores.json \
      --official-single-seed 0.6460
"""
import argparse
import json
from collections import defaultdict

# Officially measured seed=42 char_acc per eval run, for the optional
# cross-check. Keyed by the eval_runs/ directory that produced it.
OFFICIAL_SINGLE_SEED = {
    "prompt_trained_short": 0.6917,   # 9B glyph, README results table
    "glyph_r32_5000": 0.6883,         # 9B glyph-cond@5000+disambig
    "glyph_4b_r32_5000": 0.6460,      # 4B glyph, rank 32
}


def main(scores_path, official=None):
    s = json.load(open(scores_path))
    cell_any = defaultdict(bool)
    per_seed = defaultdict(lambda: [0, 0])  # seed -> [matches, total]
    for key, cells in s.items():
        font, model, seed = key.rsplit("__", 2)
        for c in cells:
            cell_any[(font, c["char"])] |= bool(c["char_acc_match"])
            per_seed[seed][0] += bool(c["char_acc_match"])
            per_seed[seed][1] += 1

    n = len(cell_any)
    best_of_n = sum(cell_any.values()) / n if n else 0.0
    print(f"cells: {n}")
    seed_accs = {}
    for seed in sorted(per_seed):
        m, t = per_seed[seed]
        seed_accs[seed] = m / t
        print(f"  {seed}: single-seed char_acc = {m/t:.4f}  ({m}/{t})")

    best_seed = max(seed_accs, key=seed_accs.get) if seed_accs else None
    print(f"\nBEST-OF-{len(per_seed)} (same-model) ceiling = {best_of_n:.4f}")
    if best_seed is not None:
        print(f"best single seed in this run ({best_seed}) = {seed_accs[best_seed]:.4f}")
        print(f"WITHIN-RUN headroom = {best_of_n - seed_accs[best_seed]:+.4f}")

    if official is not None:
        print(f"\nvs official single-seed (seed=42) = {official:.4f}")
        print(f"recoverable-by-sampling delta = {best_of_n - official:+.4f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("scores_path", nargs="?", default="dpo_holdout_bestofn/scores.json")
    ap.add_argument("--official-single-seed", type=float, default=None,
                    help=f"Separately measured seed=42 char_acc for THIS checkpoint. "
                         f"Known values: {OFFICIAL_SINGLE_SEED}")
    a = ap.parse_args()
    main(a.scores_path, a.official_single_seed)
