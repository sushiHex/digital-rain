"""Phase 0 dual scorecard: split letterform IDENTITY (reads as the right letter)
from style FIDELITY (DINOv2 char-acc). Class-routed identity, abstaining where
OCR is blind (thin strokes) or unreliable (dot-grid / heavy-distress fonts).

IDENTITY uses the TrOCR decode already stored in per_cell.json (racc_gen_decoded),
so the core is free -- no re-inference. Symbol cells can be upgraded later with a
GOT-OCR2 pass (see --got-decodes); until then they abstain.

Usage:  python identity_score.py eval_runs/glyph_r32_disambig50_mild/per_cell.json
"""
import argparse, json, sys
from collections import defaultdict
from pathlib import Path

# --- routing sets ---
THIN = set("'`\\|/lI1ij")          # OCR reads these ~0% -> abstain (measurement-blind)
SYMBOLS = set("!\"#$%&()*+,-./:;<=>?@[]^_{}~")
GT_LEGIBLE_MIN = 0.55              # if TrOCR can't read the GT font's OWN glyphs this well,
#   it can't fairly judge the generation -> abstain the whole font. Self-calibrating: catches
#   cursive/handwriting (Playwrite), dot-grid, and heavy-distress alike, by evidence not by name.

# isolated-glyph confusions we do NOT punish for the LENIENT identity read (case already folded)
EQUIV = [set("0oO"), set("1lLiI|"), set("5sS"), set("2zZ"), set("8bB"), set("9gG"), set("uUvV")]
def _norm(s):
    return (s or "").strip().lower()
def _canon(ch):
    ch = ch.lower()
    for g in EQUIV:
        if ch in {c.lower() for c in g}:
            return frozenset(c.lower() for c in g)
    return ch
def reads_as(decoded, expected, lenient):
    d = _norm(decoded)
    if not d:
        return False
    d0 = d[0]                                  # first decoded char (tolerate trailing OCR noise)
    e = expected.lower()
    if d == e or d0 == e:
        return True
    if lenient and _canon(d0) == _canon(e):
        return True
    return False

def _load_classifier_decodes(records, holdout_dir, eval_out, classifier_path, device="cuda"):
    """Alternative reader to the TrOCR decodes stored in per_cell.json: the
    font-invariant glyph classifier (glyph_classifier.py), the SAME reader
    eval_checkpoint.py's --identity pass uses -- so the standalone tool and
    the eval share one identity definition.

    Unlike the TrOCR path (free -- decodes are already stored in per_cell.json),
    this needs the actual pixels: the GT atlases under `holdout_dir` and the
    generated atlases under `eval_out/generated/<font>.png`. Groups the
    requested (font, char) cells by font so each atlas pair is opened once,
    and loads the classifier once (not per font).

    Returns (gt_decoded, gen_decoded): dicts keyed by (font, char) -> the
    classifier's predicted character (single char, case as trained).
    Fonts whose atlas pair isn't found are silently skipped (records for that
    font just won't get classifier decodes -- caller falls back to whatever
    stored decode is available).
    """
    import numpy as np
    from PIL import Image
    from atlas_constants import CHARSET
    from eval_checkpoint import crop_cell
    from glyph_classifier import load_classifier, classify

    model, idx_to_char = load_classifier(classifier_path, device=device)

    by_font = defaultdict(set)
    for r in records:
        by_font[r["font"]].add(r["char"])

    manifest = json.load(open(Path(holdout_dir) / "manifest.json"))
    atlas_by_font = {e["name"]: e["atlas"] for e in manifest["fonts"]}

    gt_decoded, gen_decoded = {}, {}
    for font, chars in by_font.items():
        atlas_rel = atlas_by_font.get(font)
        if atlas_rel is None:
            continue
        gt_path = Path(holdout_dir) / atlas_rel
        gen_path = Path(eval_out) / "generated" / f"{font}.png"
        if not gt_path.exists() or not gen_path.exists():
            print(f"  [classifier] skip {font}: missing atlas ({gt_path.exists()=}, {gen_path.exists()=})")
            continue
        gt_atlas = np.array(Image.open(gt_path).convert("RGB"))
        gen_atlas = np.array(Image.open(gen_path).convert("RGB"))
        if gen_atlas.shape != gt_atlas.shape:
            gen_atlas = np.array(Image.fromarray(gen_atlas).resize(
                (gt_atlas.shape[1], gt_atlas.shape[0]), Image.LANCZOS))
        ordered_chars = sorted(chars)
        idxs = [CHARSET.index(c) for c in ordered_chars]
        gt_cells = [crop_cell(gt_atlas, idx) for idx in idxs]
        gen_cells = [crop_cell(gen_atlas, idx) for idx in idxs]
        gt_preds = classify(model, idx_to_char, gt_cells)
        gen_preds = classify(model, idx_to_char, gen_cells)
        for ch, gp, gnp in zip(ordered_chars, gt_preds, gen_preds):
            gt_decoded[(font, ch)] = gp
            gen_decoded[(font, ch)] = gnp

    return gt_decoded, gen_decoded

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("per_cell")
    ap.add_argument("--got-decodes", default=None, help="optional GOT-OCR2 decode json to un-abstain symbols")
    ap.add_argument("--classifier", default=None,
                     help="Use the font-invariant glyph classifier (glyph_classifier.py) as the identity "
                          "reader INSTEAD OF the TrOCR decodes stored in per_cell.json -- the same reader "
                          "eval_checkpoint.py's --identity pass uses, so this tool and the eval agree. "
                          "Needs the actual atlases (requires --holdout; per_cell.json alone only has "
                          "stored TrOCR strings, not pixels) -- eval_checkpoint.py --identity already has "
                          "both atlases in-process, so prefer that for a from-scratch eval.")
    ap.add_argument("--holdout", default=None, help="Holdout dir (GT atlases); required with --classifier")
    ap.add_argument("--eval-out", default=None,
                     help="Eval-run out dir containing generated/<font>.png (default: per_cell.json's parent dir)")
    ap.add_argument("--device", default="cuda", help="Device for --classifier")
    args = ap.parse_args()
    d = json.load(open(args.per_cell))
    got = {}
    if args.got_decodes:
        raw = json.load(open(args.got_decodes))
        for run in raw:  # {run:{font:{char:decode}}} shape from hybrid_v2
            for f, cc in raw[run].items():
                for ch, dec in cc.items():
                    got[(f, ch)] = dec

    clf_gt, clf_gen = {}, {}
    if args.classifier:
        if not args.holdout:
            print("ERROR: --classifier requires --holdout (GT atlases) -- the classifier reads pixels, "
                  "not the TrOCR strings already stored in per_cell.json. Pass --holdout <dir> (and "
                  "--eval-out if the generated/ atlases aren't next to per_cell.json).")
            sys.exit(1)
        eval_out = args.eval_out or str(Path(args.per_cell).parent)
        print(f"[identity_score] --classifier given: reading GT+gen atlases "
              f"(holdout={args.holdout}, eval_out={eval_out}) -- classifier replaces TrOCR as the identity reader")
        clf_gt, clf_gen = _load_classifier_decodes(d, args.holdout, eval_out, args.classifier, device=args.device)

    n = len(d)
    fidelity = sum(r["char_acc_match"] for r in d) / n
    scored = abstain = ident_ok = 0
    ab_reason = defaultdict(int)
    target = []                     # non-abstained wrong-letter cells (the fix list)
    reclassified = 0                # char-acc FAIL but identity OK (the metric-artifact count)
    by_font_id = defaultdict(lambda: [0, 0])
    for r in d:
        ch, font = r["char"], r["font"]
        # GOLD-STANDARD GATE: only score a cell if the reader (TrOCR, or GOT for symbols)
        # correctly reads the GT glyph. If it misreads the GT (NovaSquare J -> '1'),
        # it can't be trusted to judge the generation -> abstain. Kills the systematic
        # isolated-glyph misread noise (J K L N T, cursive, dot, distress) by evidence.
        if args.classifier and (font, ch) in clf_gt:
            gt_dec = clf_gt[(font, ch)]
        elif (font, ch) in got:
            gt_dec = got[(font, ch)]
        else:
            gt_dec = r.get("racc_gt_decoded", "")
        abst = None
        if ch == " ":
            abst = "space"
        elif ch in THIN:
            abst = "thin-stroke (OCR-blind)"
        elif ch in SYMBOLS and (font, ch) not in got:
            abst = "symbol (needs GOT pass)"
        elif not reads_as(gt_dec, ch, lenient=True):
            abst = "reader misreads GT glyph (can't judge)"
        if abst:
            abstain += 1; ab_reason[abst] += 1; continue

        if args.classifier and (font, ch) in clf_gen:
            decoded = clf_gen[(font, ch)]
        else:
            decoded = got.get((font, ch), r.get("racc_gen_decoded", ""))
        ok = reads_as(decoded, ch, lenient=True)
        scored += 1
        ident_ok += ok
        by_font_id[font][0] += ok; by_font_id[font][1] += 1
        if not ok:
            target.append({"font": font, "char": ch, "decoded": decoded,
                           "fidelity_match": r["char_acc_match"]})
        if ok and not r["char_acc_match"]:
            reclassified += 1

    identity = ident_ok / scored if scored else 0.0
    fails = [r for r in d if not r["char_acc_match"]]

    print(f"=== DUAL SCORECARD  ({args.per_cell})  n={n} cells ===")
    print(f"  FIDELITY (DINOv2 char-acc, matches GT rendering): {fidelity:.3f}   <- the headline")
    print(f"  IDENTITY (reads as the right letter, scored set): {identity:.3f}   over {scored} scored cells")
    print(f"  ABSTAINED: {abstain} cells ({abstain/n:.0%}) -- OCR can't fairly score:")
    for k, v in sorted(ab_reason.items(), key=lambda x: -x[1]):
        print(f"      {v:5d}  {k}")
    print(f"\n  The reframe: of {len(fails)} char-acc FAILURES, {reclassified} scored cells are the CORRECT LETTER")
    print(f"      (right letter, penalized only on style/rendering).")
    print(f"  GENUINE wrong-letter target: {len(target)} cells = {len(target)/scored:.1%} of scored, {len(target)/n:.1%} of all.")

    # concentration of the target list
    by_char = defaultdict(int); by_font = defaultdict(int)
    for t in target:
        by_char[t["char"]] += 1; by_font[t["font"]] += 1
    print("\n  wrong-letter target by CHAR (top 12):",
          [(c, k) for c, k in sorted(by_char.items(), key=lambda x: -x[1])[:12]])
    print("  wrong-letter target by FONT (top 8):",
          [(f.split('[')[0][:16], k) for f, k in sorted(by_font.items(), key=lambda x: -x[1])[:8]])

    out = args.per_cell.replace("per_cell.json", "identity_scorecard.json")
    json.dump({"fidelity": fidelity, "identity": identity, "scored": scored,
               "abstained": abstain, "abstain_reasons": dict(ab_reason),
               "reclassified_correct_letter": reclassified,
               "wrong_letter_target": target}, open(out, "w"), indent=1)
    print(f"\n  wrote {out}  ({len(target)}-cell target list for the fix steps)")

if __name__ == "__main__":
    main()
