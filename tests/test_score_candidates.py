import json

import numpy as np
from PIL import Image


def test_topology_penalty_prefers_faithful_dotgrid():
    from score_candidates import topology_penalty
    # GT: sparse dot-grid (many components, low ink); faithful keeps dots, smoothed fills solid
    gt = np.zeros((160, 106), np.uint8); gt[::8, ::8] = 255
    faithful = gt.copy()
    smoothed = np.zeros((160, 106), np.uint8); smoothed[40:120, 30:76] = 255  # solid blob
    assert topology_penalty(gt, faithful) < topology_penalty(gt, smoothed)


def test_cell_score_monotone():
    from score_candidates import cell_score
    hi = cell_score(0.9, 0.1, 0.0, lam=0.5, mu=0.5)
    lo = cell_score(0.9, 0.1, 0.4, lam=0.5, mu=0.5)  # more topology penalty
    assert hi > lo


def test_score_all_writes_bare_cell_lists_consumed_by_downstream(tmp_path, monkeypatch):
    """Boundary-crossing regression test (Final-review FIX C1).

    score_all() used to write scores[key] = {"font":..., "model":..., "seed":...,
    "cells": cells} -- a wrapper dict. Every real downstream consumer
    (measure_oracle_ceiling._by_cell / seed_variance_on_failing,
    select_preferences.select) does `for r in rows: ... r["char"]` over
    scores[key], re-deriving font/model/seed from the dict KEY itself via
    `key.rsplit("__", 2)`. A wrapper dict there makes `for r in rows` iterate
    the wrapper's own string keys ("font"/"model"/"seed"/"cells"), so
    `r["char"]` raises TypeError ("string indices must be integers") the
    moment real data reaches either consumer -- a unit test on score_all alone
    (or on the consumers alone, with hand-built bare-list fixtures) can't catch
    this; it only shows up crossing the producer -> consumer boundary.

    This test drives score_all() for real (score_font faked out so no
    GPU/DINOv2/LPIPS dependency is needed), writes a real scores.json to disk,
    reloads it, and feeds it through both real consumers.
    """
    import score_candidates

    candidates_dir = tmp_path / "candidates"
    gt_dir = tmp_path / "gt"
    gt_dir.mkdir()

    tiny = np.zeros((8, 8, 3), np.uint8)
    for font in ("FontA", "FontB"):
        fdir = candidates_dir / font
        fdir.mkdir(parents=True)
        Image.fromarray(tiny).save(fdir / "baseline__seed0.png")
        Image.fromarray(tiny).save(fdir / "glyph__seed0.png")
        Image.fromarray(tiny).save(gt_dir / f"{font}.png")

    def fake_score_font(gt_atlas, cand_atlas, device, lam=0.5, mu=0.5):
        # Fixed 2-cell result, standing in for the real DINOv2/LPIPS pipeline.
        return [
            {"char": "A", "char_acc_match": True, "dino_cos": 0.9, "lpips": 0.1,
             "topo_pen": 0.0, "score": 0.8},
            {"char": "B", "char_acc_match": False, "dino_cos": 0.5, "lpips": 0.3,
             "topo_pen": 0.1, "score": 0.3},
        ]

    monkeypatch.setattr(score_candidates, "score_font", fake_score_font)

    out_path = tmp_path / "scores.json"
    n_scored = score_candidates.score_all(
        str(candidates_dir), str(gt_dir), str(out_path), device="cpu")
    assert n_scored == 4  # 2 fonts x {baseline, glyph}

    on_disk = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(on_disk) == 4
    for key, rows in on_disk.items():
        assert isinstance(rows, list), f"{key}: value must be a bare list of cell dicts, not a wrapper dict"
        for r in rows:
            assert isinstance(r, dict)
            assert "char" in r and "char_acc_match" in r

    # Cross into the real consumers -- must not raise TypeError.
    from measure_oracle_ceiling import oracle_ceiling
    ceiling = oracle_ceiling(on_disk)
    assert isinstance(ceiling["realizable_ceiling"], float)

    from select_preferences import select
    result = select(on_disk)
    assert isinstance(result["pref_pairs"], list)
