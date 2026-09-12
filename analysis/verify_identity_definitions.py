"""Recompute IDENTITY under each matching definition, from committed per-cell data.

The project reports IDENTITY = 0.9936 and for a long time described it as
"the model produces the correct letter 99.4% of the time" off a "94-class CNN".
Those are different statements. The reported number is computed after:

  1. case folding, and
  2. `identity_score.EQUIV` merging isolated-glyph confusions
     (0/o/O, 1/l/L/i/I/|, 5/s/S, 2/z/Z, 8/b/B, 9/g/G, u/U/v/V), and
  3. a GT gate that scores only cells where the classifier reads the GROUND
     TRUTH glyph correctly with confidence >= 0.5.

Each step is individually defensible -- an isolated `O` and `0` really are
undecidable without word context, and a reader that cannot identify the GT
glyph cannot fairly judge the generation. Stacked and then described as
"94-class identity", they are not.

This prints every definition so the gap is visible rather than argued about,
and so the README's table can be regenerated instead of trusted.

  python analysis/verify_identity_definitions.py
  python analysis/verify_identity_definitions.py eval_runs/glyph_4b_r32_5000/per_cell.json
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json

from identity_score import reads_as


def _rate(rows, fn):
    ok = sum(1 for r in rows if fn(r))
    return ok, (ok / len(rows) if rows else float("nan"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("per_cell", nargs="?",
                    default="eval_runs/prompt_trained_short/per_cell.json")
    args = ap.parse_args(argv)

    recs = json.load(open(args.per_cell, encoding="utf-8"))
    if not recs or "identity_gen_pred" not in recs[0]:
        raise SystemExit(f"{args.per_cell} has no identity records "
                         "(was the eval run with --identity?)")
    scored = [r for r in recs if r.get("identity_scored")]
    excluded = [r for r in recs if not r.get("identity_scored")]

    exact = lambda r: (r["identity_gen_pred"] or "") == r["char"]
    fold = lambda r: (r["identity_gen_pred"] or "").lower() == r["char"].lower()
    lenient = lambda r: reads_as(r["identity_gen_pred"], r["char"], lenient=True)

    print(f"{args.per_cell}")
    print(f"  {len(recs)} cells; GT-gated in {len(scored)}, excluded {len(excluded)} "
          f"({len(scored) / len(recs):.4f} scored_frac)\n")

    print(f"  {'definition':34} {'on gated cells':>16} {'on ALL cells':>16}")
    for name, fn in (("exact 94-class", exact),
                     ("case-insensitive", fold),
                     ("case + EQUIV  (reported IDENTITY)", lenient)):
        ns, ps = _rate(scored, fn)
        na, pa = _rate(recs, fn)
        print(f"  {name:34} {ps:>10.4f} ({ns:>4}) {pa:>10.4f} ({na:>4})")

    if excluded:
        print(f"\n  the {len(excluded)} EXCLUDED cells are materially harder:")
        for m in ("char_acc_match", "racc_match"):
            a = sum(1 for r in scored if r.get(m)) / len(scored)
            b = sum(1 for r in excluded if r.get(m)) / len(excluded)
            print(f"    {m:16} kept {a:.4f}   excluded {b:.4f}")
        for m in ("dinov2", "lpips"):
            if m not in recs[0]:
                continue
            a = sum(r[m] for r in scored) / len(scored)
            b = sum(r[m] for r in excluded) / len(excluded)
            print(f"    {m:16} kept {a:.4f}   excluded {b:.4f}")
        n, p = _rate(excluded, lenient)
        print(f"    lenient agreement on the excluded cells: {n}/{len(excluded)} = {p:.4f}")
        print("\n  So the gate lifts the reported number, and the excluded cells are\n"
              "  exactly the ones where the reader is least trustworthy. The GT\n"
              "  confidence is not persisted, so the 0.5 threshold's sensitivity\n"
              "  cannot be reproduced from these records.")


if __name__ == "__main__":
    main()
