"""Score the reference gate and the two-glyph adherence measure against HUMAN labels.

PRE-REGISTERED. Committed while `research/calibration_labels.csv` is an EMPTY
template -- not one label existed when this analysis was fixed, so the labels
cannot have shaped it. The commit timestamp is the proof.

WHY THIS IS THE MISSING PIECE. Both instruments the product depends on are
uncalibrated. The reference gate's threshold (1.875) was cut from the coherent
references' OWN spread, not from references a person rejected, so its recall
is a floor and its precision is unknown. The adherence measure ranks (10/11
real held-out typefaces) but cannot say "this one failed": unrestricted it
calls 4/11. Neither can be calibrated by any measurement this repository can
make on its own, because the quantity they are meant to predict -- would a
person accept this reference as a starting point for the described style --
has never been recorded. That recording is the owner's half hour
(`analysis/calibration_sheet.py` builds the sheet). This file is everything
else, written first.

=== PRE-REGISTRATION, fixed before any label ===

SAMPLE     The 48 candidate references in eval_runs/_candidate_refs/klein-base-n4
           (12 descriptions x 4 seeds), labelled in
           research/calibration_labels.csv with `usable` in {1, 0}. Rows left
           blank are EXCLUDED and their count is REPORTED. Fewer than 30
           labelled rows: the analysis runs but every result is marked
           "underpowered" and no verdict is printed.

GATE       Statistic: the AUC of the gate's own distance
           (`reference_gate.reference_consistency`, lower = more coherent)
           for usable vs not, oriented so that AUC > 0.5 means usable
           references are MORE coherent. Significance: a permutation test,
           10,000 label shuffles, one-sided. Also reported, NOT optimised:
           precision, recall and specificity of the EXISTING 1.875 cut
           against the labels. No new threshold is fitted here; a cut chosen
           by looking at the labels would need a fresh sample to test.

ADHERENCE  Secondary, restricted to the descriptions that name a constructible
           treatment -- stencil (#09) and inline (#10), n = 8 -- because only
           there does "usable" have a treatment to be about. Statistic: the
           two-glyph model's probability of the REQUESTED treatment
           (`reference_stage_adherence.fit_reference_stage_model`, the same
           fit the registered 9/11 came from), AUC for usable vs not. With
           n = 8 this is REPORTED, never claimed.

BAR        Gate AUC >= 0.70 AND permutation p < 0.05 reads as "coherence
           predicts usability" and licenses the next step: cutting a
           threshold on a FRESH labelled sample. Below that, the gate's
           threshold is NOT evidence about usability and stays what it is --
           a coherence check with a provisional cut -- and the product's
           "usable" signal has to come from somewhere else. For scale, with
           ~24 vs ~24 labels the SE of an AUC near 0.7 is about 0.08, so an
           AUC of 0.60 is indistinguishable from chance.

IF IT FAILS Reported as a failure, verbatim, in a dated note. Nothing about
           the gate changes.

  python analysis/calibrate_instruments.py
  python analysis/calibrate_instruments.py --labels research/calibration_labels.csv
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import csv
import glob
import json
import os
import re

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_REFS = os.path.join(REPO, "eval_runs", "_candidate_refs", "klein-base-n4")
DEFAULT_LABELS = os.path.join(REPO, "research", "calibration_labels.csv")
DEFAULT_JSON = os.path.join(REPO, "research", "calibrate_instruments.json")

# analysis/reference_gate.py's provisional cut, recorded in
# research/2026-08-21-the-reference-gate.md. Not fitted here.
GATE_THRESHOLD = 1.875
# Descriptions whose text names a treatment the adherence model can read.
TREATMENT_OF = {9: "stencil", 10: "inline"}
MIN_LABELLED = 30
PERMUTATIONS = 10_000
BAR_AUC, BAR_P = 0.70, 0.05

ID_RX = re.compile(r"^(\d\d)-s(\d+)$")
SEED_SUFFIX = re.compile(r"__s(\d+)$")


def auc(scores, labels):
    """Mann-Whitney AUC: P(score of a usable > score of a not-usable), ties 0.5."""
    scores, labels = np.asarray(scores, float), np.asarray(labels, int)
    pos, neg = scores[labels == 1], scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    gt = (pos[:, None] > neg[None, :]).sum()
    eq = (pos[:, None] == neg[None, :]).sum()
    return float((gt + 0.5 * eq) / (len(pos) * len(neg)))


def permutation_p(scores, labels, observed, n=PERMUTATIONS, seed=0):
    """One-sided: how often a label shuffle reaches the observed AUC."""
    rng = np.random.default_rng(seed)
    labels = np.asarray(labels, int)
    hits = 0
    for _ in range(n):
        hits += auc(scores, rng.permutation(labels)) >= observed
    return (hits + 1) / (n + 1)


def cut_report(distances, labels, threshold=GATE_THRESHOLD):
    """Precision / recall / specificity of 'distance <= threshold' as 'usable'."""
    d, y = np.asarray(distances, float), np.asarray(labels, int)
    pred = d <= threshold
    tp = int((pred & (y == 1)).sum())
    fp = int((pred & (y == 0)).sum())
    fn = int((~pred & (y == 1)).sum())
    tn = int((~pred & (y == 0)).sum())
    div = lambda a, b: float(a / b) if b else float("nan")  # noqa: E731
    return {"threshold": threshold, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": div(tp, tp + fp), "recall": div(tp, tp + fn),
            "specificity": div(tn, tn + fp)}


def read_labels(path):
    """(labelled rows, n_blank). A row counts only if `usable` is 0 or 1."""
    rows, blank = [], 0
    with open(path, encoding="utf-8", newline="") as fh:
        for rec in csv.DictReader(fh):
            m = ID_RX.match(rec.get("id", ""))
            if not m:
                raise SystemExit(f"bad id {rec.get('id')!r}: expected NN-sK")
            val = (rec.get("usable") or "").strip()
            if val == "":
                blank += 1
                continue
            if val not in ("0", "1"):
                raise SystemExit(f"row {rec['id']}: usable must be 0, 1 or blank, "
                                 f"got {val!r}")
            rows.append({"id": rec["id"], "index": int(m.group(1)),
                         "seed": int(m.group(2)), "usable": int(val),
                         "description": rec.get("description", "")})
    return rows, blank


def find_reference(refs_dir, index, seed):
    hits = [p for p in glob.glob(os.path.join(refs_dir, f"{index:02d}-*.png"))
            if SEED_SUFFIX.search(os.path.splitext(os.path.basename(p))[0])
            and int(SEED_SUFFIX.search(
                os.path.splitext(os.path.basename(p))[0]).group(1)) == seed]
    if len(hits) != 1:
        raise SystemExit(f"expected one reference for {index:02d}-s{seed}, "
                         f"found {len(hits)}")
    return hits[0]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--labels", default=DEFAULT_LABELS)
    ap.add_argument("--refs", default=DEFAULT_REFS)
    ap.add_argument("--pool", default=os.path.join(REPO, "font_pool"))
    ap.add_argument("--json", default=DEFAULT_JSON)
    ap.add_argument("--skip-adherence", action="store_true",
                    help="gate only (the adherence fit needs the font pool)")
    args = ap.parse_args(argv)

    rows, blank = read_labels(args.labels)
    n = len(rows)
    print(f"labels: {n} labelled, {blank} blank (excluded)")
    if n == 0:
        print("nothing to score yet: the template is empty. That is the "
              "registered state; come back once the owner has judged.")
        return 0
    underpowered = n < MIN_LABELLED
    if underpowered:
        print(f"  UNDERPOWERED: fewer than {MIN_LABELLED} labels; results are "
              "reported, no verdict is printed.")

    # --- GATE ----------------------------------------------------------
    from analysis.reference_gate import reference_consistency
    from analysis.style_coherence import load_stats

    stats = load_stats()
    for r in rows:
        r["path"] = find_reference(args.refs, r["index"], r["seed"])
        rc = reference_consistency(r["path"], stats)
        r["distance"] = None if rc is None else rc["distance"]
    scored = [r for r in rows if r["distance"] is not None]
    dropped = n - len(scored)
    if dropped:
        print(f"  {dropped} labelled reference(s) unscoreable by the gate; excluded")
    labels = [r["usable"] for r in scored]
    # Oriented: usable should be MORE coherent, i.e. LOWER distance.
    gate_auc = auc([-r["distance"] for r in scored], labels)
    gate_p = permutation_p([-r["distance"] for r in scored], labels, gate_auc)
    cut = cut_report([r["distance"] for r in scored], labels)
    print(f"\n  GATE  usable {sum(labels)} / not {len(labels) - sum(labels)}")
    print(f"        AUC (usable more coherent) = {gate_auc:.3f}   "
          f"permutation p = {gate_p:.4f}")
    print(f"        at the existing cut {GATE_THRESHOLD}: precision "
          f"{cut['precision']:.2f}  recall {cut['recall']:.2f}  "
          f"specificity {cut['specificity']:.2f}")

    verdict = "not scored"
    if not underpowered:
        passed = gate_auc >= BAR_AUC and gate_p < BAR_P
        verdict = ("PASSED -- coherence predicts usability; a threshold may be "
                   "cut on a FRESH sample" if passed else
                   "FAILED -- the gate is a coherence check, not a usability "
                   "signal; its cut stays as it is")
        print(f"\n  PRE-REGISTERED BAR AUC>={BAR_AUC} and p<{BAR_P}: {verdict}")

    # --- ADHERENCE (secondary, n = 8) ------------------------------------
    adherence = None
    treated = [r for r in scored if r["index"] in TREATMENT_OF]
    if treated and not args.skip_adherence:
        from analysis.reference_gate import glyph_cells
        from analysis.reference_stage_adherence import fit_reference_stage_model
        from analysis.synthesize_rare_attributes import CLASSES, vector_from_cells

        model, _real, _records = fit_reference_stage_model(args.pool, verbose=False)
        probs, ys = [], []
        for r in treated:
            cells = glyph_cells(r["path"], 2)
            v = vector_from_cells([c for c in cells if c is not None], min_cells=2)
            if v is None:
                continue
            p = model.predict_proba(v.reshape(1, -1))[0]
            r["p_requested"] = float(p[CLASSES.index(TREATMENT_OF[r["index"]])])
            probs.append(r["p_requested"])
            ys.append(r["usable"])
        if len(set(ys)) == 2:
            adherence = {"n": len(ys), "auc": auc(probs, ys)}
            print(f"\n  ADHERENCE (secondary, n={len(ys)}): AUC of P(requested "
                  f"treatment) for usable = {adherence['auc']:.3f} -- reported, "
                  "not claimed")
        else:
            adherence = {"n": len(ys), "auc": None}
            print(f"\n  ADHERENCE (secondary): only one class among the {len(ys)} "
                  "treated candidates; nothing to rank")

    payload = {"preregistered": True, "labels_csv": os.path.relpath(args.labels, REPO).replace("\\", "/"),
               "n_labelled": n, "n_blank": blank, "n_scored": len(scored),
               "underpowered": underpowered, "gate": {
                   "auc": gate_auc, "permutation_p": gate_p, "cut": cut},
               "adherence": adherence, "verdict": verdict,
               "rows": [{k: v for k, v in r.items() if k != "path"} for r in scored]}
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1)
    print(f"\nwrote {os.path.relpath(args.json, REPO)}")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
