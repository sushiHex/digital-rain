def test_oracle_ceiling_arithmetic():
    from measure_oracle_ceiling import oracle_ceiling
    # 4 cells: both-ok, only-baseline, only-glyph, both-fail
    scores = {
        "F__baseline__seed0": [{"char":"A","char_acc_match":True},{"char":"B","char_acc_match":True},
                               {"char":"C","char_acc_match":False},{"char":"D","char_acc_match":False}],
        "F__glyph__seed0":    [{"char":"A","char_acc_match":True},{"char":"B","char_acc_match":False},
                               {"char":"C","char_acc_match":True},{"char":"D","char_acc_match":False}],
    }
    r = oracle_ceiling(scores)
    assert abs(r["realizable_ceiling"] - 0.75) < 1e-9   # A,B,C matchable
    assert abs(r["glyph_alone"] - 0.5) < 1e-9           # A,C
    assert r["only_baseline_cells"] == 1                # B
    assert r["only_glyph_cells"] == 1                   # C
    assert r["both_fail"] == 1                          # D
