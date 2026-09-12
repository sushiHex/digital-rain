import torch


def test_dpo_loss_prefers_winner():
    from dpo_train import dpo_loss
    # winner has LOWER policy loss than reference (improved), loser unchanged → positive preference, low loss
    good = dpo_loss(torch.tensor(0.2), torch.tensor(0.5), torch.tensor(0.4), torch.tensor(0.4), beta=1.0)
    bad  = dpo_loss(torch.tensor(0.6), torch.tensor(0.2), torch.tensor(0.4), torch.tensor(0.4), beta=1.0)
    assert good < bad


def test_per_sample_flow_loss_shape():
    from dpo_train import per_sample_flow_loss
    pred = torch.randn(2, 6400, 128); target = torch.randn(2, 6400, 128); w = torch.ones(2)
    out = per_sample_flow_loss(pred, target, w)
    assert out.shape == (2,)


# ==========================================================================
# Final-review FIX M5: regression-char up-weighting (pref_pairs.json's
# per-cell "weight") must reach the per-font DPO loss, not be silently
# dropped. font_weight_for() is the pure per-font aggregation; DPOPairDataset
# + collate_dpo are the plumbing that carries it from the pair-cache .pt
# files into the training loop's batch.
# ==========================================================================

def test_font_weight_for_default_all_ones_is_noop():
    from dpo_train import font_weight_for
    fpairs = [{"font": "F", "char": "A", "weight": 1}, {"font": "F", "char": "B", "weight": 1}]
    assert font_weight_for(fpairs) == 1.0


def test_font_weight_for_mean_of_regression_upweight():
    from dpo_train import font_weight_for
    # One regression-char pair (weight=3, e.g. REGRESSION_CHARS) among plain (weight=1) pairs.
    fpairs = [{"font": "F", "char": "A", "weight": 1}, {"font": "F", "char": "\\", "weight": 3}]
    assert font_weight_for(fpairs) == 2.0  # mean(1, 3)


def test_font_weight_for_empty_defaults_to_one():
    from dpo_train import font_weight_for
    assert font_weight_for([]) == 1.0


def test_dpo_pair_dataset_carries_font_weight(tmp_path):
    """DPOPairDataset must surface each font's cached font_weight (not just
    winner/loser/reference latents), and default missing "weight" (a
    pair-cache entry written before this fix) to 1.0 -- no behavior change
    for pre-existing caches/fonts with no up-weighted cells."""
    from dpo_train import DPOPairDataset, collate_dpo

    pair_cache = tmp_path / "pair_cache"; pair_cache.mkdir()
    ref_cache = tmp_path / "ref_cache"; ref_cache.mkdir()

    # Font "Up": explicit up-weighted cache entry (regression char present).
    torch.save({"winner": torch.zeros(4, 8), "loser": torch.ones(4, 8),
                "h": 2, "w": 2, "weight": 3.0}, pair_cache / "Up.pt")
    torch.save({"latents": torch.zeros(2, 8)}, ref_cache / "Up.pt")

    # Font "Plain": no "weight" key at all (simulates a cache built before this
    # fix, or a font with no regression-char pairs) -- must default to 1.0.
    torch.save({"winner": torch.zeros(4, 8), "loser": torch.ones(4, 8),
                "h": 2, "w": 2}, pair_cache / "Plain.pt")
    torch.save({"latents": torch.zeros(2, 8)}, ref_cache / "Plain.pt")

    ds = DPOPairDataset(pair_cache, ref_cache)
    assert len(ds) == 2

    by_font = {}
    for i in range(len(ds)):
        winner, loser, ref, weight = ds[i]
        stem = ds.items[i][0].stem
        by_font[stem] = weight
        assert isinstance(weight, torch.Tensor)

    assert float(by_font["Up"]) == 3.0
    assert float(by_font["Plain"]) == 1.0

    batch = [ds[i] for i in range(len(ds))]
    winners, losers, refs, weights = collate_dpo(batch)
    assert weights.shape == (2,)
    assert set(weights.tolist()) == {1.0, 3.0}
