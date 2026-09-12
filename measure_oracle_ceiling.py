import argparse, json, sys
from collections import defaultdict

def _parse_key(k):
    """Delegates to candidate_gen.parse_candidate_key (single source of truth)."""
    from candidate_gen import parse_candidate_key
    return parse_candidate_key(k)

def _by_cell(scores):
    # cell -> {model -> best-over-seeds char_acc_match}
    cells = defaultdict(lambda: defaultdict(bool))
    for key, rows in scores.items():
        font, model, _ = _parse_key(key)
        for r in rows:
            cells[(font, r["char"])][model] |= bool(r["char_acc_match"])
    return cells

def oracle_ceiling(scores):
    cells = _by_cell(scores)
    n = len(cells); realizable = glyph = base = ob = og = bf = 0
    for _, m in cells.items():
        b, g = m.get("baseline", False), m.get("glyph", False)
        realizable += (b or g); glyph += g; base += b
        ob += (b and not g); og += (g and not b); bf += (not b and not g)
    return {"realizable_ceiling": realizable / n, "glyph_alone": glyph / n,
            "baseline_alone": base / n, "only_baseline_cells": ob,
            "only_glyph_cells": og, "both_fail": bf, "n_cells": n}

def seed_variance_on_failing(scores):
    # glyph cells: per-cell list of per-seed matches
    per = defaultdict(list)
    for key, rows in scores.items():
        font, model, _ = _parse_key(key)
        if model != "glyph": continue
        for r in rows:
            per[(font, r["char"])].append(int(bool(r["char_acc_match"])))
    spreads = []
    for _, seeds in per.items():
        if len(seeds) < 2: continue
        m = sum(seeds) / len(seeds)
        if m < 1.0:  # failing/mixed cells
            spreads.append(max(seeds) - m)
    return {"mean_failing_seed_spread": (sum(spreads) / len(spreads)) if spreads else 0.0,
            "n_failing_cells": len(spreads)}

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252; decision line has non-ASCII arrow
    ap = argparse.ArgumentParser(); ap.add_argument("--scores", default="dpo_data/scores.json")
    ap.add_argument("--go-threshold", type=float, default=0.71)
    args = ap.parse_args()
    s = json.load(open(args.scores))
    oc = oracle_ceiling(s); sv = seed_variance_on_failing(s)
    print(json.dumps({**oc, **sv}, indent=2))
    verdict = "GO" if oc["realizable_ceiling"] >= args.go_threshold else "RECONSIDER"
    print(f"\nREALIZABLE CEILING = {oc['realizable_ceiling']:.3f}  "
          f"(glyph-alone {oc['glyph_alone']:.3f})  → {verdict} (threshold {args.go_threshold})")
