"""Task 5: turn candidate scores into winner/loser preference pairs for DPO
(and SFT targets), with an eps-gap filter, a distinctive-font exemption, and
regression-char up-weighting.

Consumes: dpo_data/scores.json (produced by score_candidates.py).
Produces: dpo_data/pref_pairs.json, dpo_data/sft_targets.json.
"""
import argparse
import json
from collections import defaultdict

# One source of truth. The previous silent `except: <inline copy>` fallback
# would diverge from audit_diversity's list without anyone noticing, and the
# two must agree — the eps-gap exemption here is what keeps exactly those
# fonts in the training signal that the diversity guard later checks.
from audit_diversity import DISTINCTIVE as _DISTINCTIVE

DISTINCTIVE = set(_DISTINCTIVE)
REGRESSION_CHARS = set("\\'O")


def _parse_key(k):
    """Delegates to candidate_gen.parse_candidate_key (single source of truth)."""
    from candidate_gen import parse_candidate_key
    return parse_candidate_key(k)


def _is_distinctive(font):
    return any(font.startswith(d) for d in DISTINCTIVE)


def select(scores, eps=0.05, upweight=3, require_correct_winner=True):
    """Build preference pairs from candidate scores.

    require_correct_winner: drop a cell unless its WINNER is actually
    char_acc-correct. Without this, cells where every candidate fails still
    emit a pair, teaching the model to "prefer this failure over that
    failure" — measured at 39% of pairs (2545/6523) on the 80-font pilot,
    i.e. a large fraction of the training signal was noise.
    """
    # (font,char) -> list of (key, score, char_acc_match)
    cand = defaultdict(list)
    for key, rows in scores.items():
        font, _, _ = _parse_key(key)
        for r in rows:
            cand[(font, r["char"])].append(
                (key, float(r["score"]), bool(r.get("char_acc_match", False)))
            )
    pref, sft = [], []
    for (font, ch), lst in cand.items():
        lst.sort(key=lambda x: x[1], reverse=True)
        win_key, win_s, win_ok = lst[0]
        lose_key, lose_s, _ = lst[-1]
        if require_correct_winner and not win_ok:
            continue
        if (win_s - lose_s) < eps and not _is_distinctive(font):
            continue
        w = upweight if ch in REGRESSION_CHARS else 1
        pref.append({"font": font, "char": ch, "winner_key": win_key,
                     "loser_key": lose_key, "weight": w})
        sft.append({"font": font, "char": ch, "winner_key": win_key, "weight": w})
    return {"pref_pairs": pref, "sft_targets": sft}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default="dpo_data/scores.json")
    ap.add_argument("--out", default="dpo_data")
    ap.add_argument("--eps", type=float, default=0.05)
    ap.add_argument("--upweight", type=int, default=3)
    ap.add_argument("--allow-incorrect-winner", action="store_true",
                    help="Keep cells whose winner is itself char_acc-wrong (trains 'prefer one "
                         "failure over another'). Off by default — see select() docstring.")
    a = ap.parse_args()
    s = json.load(open(a.scores))
    out = select(s, a.eps, a.upweight, require_correct_winner=not a.allow_incorrect_winner)
    json.dump(out["pref_pairs"], open(f"{a.out}/pref_pairs.json", "w"), indent=1)
    json.dump(out["sft_targets"], open(f"{a.out}/sft_targets.json", "w"), indent=1)
    print(f"pairs={len(out['pref_pairs'])}  sft={len(out['sft_targets'])}")
