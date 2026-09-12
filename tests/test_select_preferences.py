def _rows(**by_key): return by_key

# NOTE: select() now defaults to require_correct_winner=True, so fixtures must
# mark the intended winner char_acc-correct or the cell is (correctly) dropped.

def test_select_gap_filter_and_distinctive_exemption():
    from select_preferences import select
    scores = {
      "PlainFont__baseline__seed0":[{"char":"A","score":0.90,"char_acc_match":True},
                                    {"char":"z","score":0.80,"char_acc_match":True}],
      "PlainFont__glyph__seed0":   [{"char":"A","score":0.895,"char_acc_match":True},
                                    {"char":"z","score":0.10,"char_acc_match":False}],
      "RubikDistressed__baseline__seed0":[{"char":"A","score":0.50,"char_acc_match":True}],
      "RubikDistressed__glyph__seed0":   [{"char":"A","score":0.499,"char_acc_match":False}],
    }
    out = select(scores, eps=0.05, upweight=3)
    pairs = {(p["font"], p["char"]) for p in out["pref_pairs"]}
    assert ("PlainFont", "A") not in pairs         # gap 0.005 < eps, plain font → dropped
    assert ("PlainFont", "z") in pairs             # gap 0.70 >= eps → kept
    assert ("RubikDistressed", "A") in pairs       # tiny gap but distinctive → exempt, kept

def test_regression_char_upweight():
    from select_preferences import select
    scores = {"F__baseline__seed0":[{"char":"\\","score":0.9,"char_acc_match":True}],
              "F__glyph__seed0":[{"char":"\\","score":0.2,"char_acc_match":False}]}
    out = select(scores, eps=0.0, upweight=3)
    assert out["pref_pairs"][0]["weight"] == 3

def test_drops_cells_whose_winner_is_also_wrong():
    """Both candidates fail char_acc -> there is no good winner, so the cell
    must NOT emit a pair (it would teach 'prefer this failure over that one').
    Measured at 39% of pairs on the 80-font pilot before this filter."""
    from select_preferences import select
    scores = {
      "F__baseline__seed0": [{"char": "A", "score": 0.40, "char_acc_match": False},
                             {"char": "B", "score": 0.90, "char_acc_match": True}],
      "F__glyph__seed0":    [{"char": "A", "score": 0.10, "char_acc_match": False},
                             {"char": "B", "score": 0.20, "char_acc_match": False}],
    }
    out = select(scores, eps=0.0, upweight=3)
    got = {(p["font"], p["char"]) for p in out["pref_pairs"]}
    assert ("F", "A") not in got   # both wrong -> dropped
    assert ("F", "B") in got       # winner correct -> kept

def test_allow_incorrect_winner_restores_old_behaviour():
    from select_preferences import select
    scores = {
      "F__baseline__seed0": [{"char": "A", "score": 0.40, "char_acc_match": False}],
      "F__glyph__seed0":    [{"char": "A", "score": 0.10, "char_acc_match": False}],
    }
    assert select(scores, eps=0.0, require_correct_winner=True)["pref_pairs"] == []
    assert len(select(scores, eps=0.0, require_correct_winner=False)["pref_pairs"]) == 1
