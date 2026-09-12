"""The redistribution statistic must read ~0 when the true effect is zero.

This exists because the original version did not. Conditioning the delta on the
BASELINE makes Cov(a, b-a) = Cov(a,b) - Var(a), so seed noise alone drives rho
negative. Measured on 12 same-model seed pairs: mean rho -0.253 with a spurious
hard-vs-easy gap of 0.038. That artefact was reported for months as "every
lever redistributes quality from easy fonts to hard ones".

These tests pin the fix (conditioning on the midpoint) against synthetic nulls,
so the bias cannot be reintroduced silently.
"""
import numpy as np
import pytest


def _null_pair(rng, n=50, true=None, noise=0.06):
    """Two independent noisy measurements of the SAME underlying quality."""
    if true is None:
        true = rng.uniform(0.2, 0.95, n)
    return (np.clip(true + rng.normal(0, noise, n), 0, 1),
            np.clip(true + rng.normal(0, noise, n), 0, 1))


def test_null_effect_gives_rho_near_zero():
    """No true effect -> rho must not be systematically negative."""
    from analysis.compare_runs import redistribution
    rng = np.random.default_rng(0)
    rhos = [redistribution(*_null_pair(rng), True)["rho"] for _ in range(60)]
    assert abs(np.mean(rhos)) < 0.10, f"biased under the null: mean rho={np.mean(rhos):.3f}"


def test_null_effect_gives_small_hard_easy_gap():
    """No true effect -> the hard/easy split must not manufacture a gap."""
    from analysis.compare_runs import redistribution
    rng = np.random.default_rng(1)
    gaps = [abs(redistribution(*_null_pair(rng), True)["gap"]) for _ in range(60)]
    assert np.mean(gaps) < 0.03, f"spurious gap under the null: {np.mean(gaps):.4f}"


def test_baseline_conditioning_would_have_failed_these():
    """Pin the bias itself, so the reason for the fix stays legible.

    Reproduces the OLD statistic (condition on `a`) and asserts it is strongly
    negative on data with no true effect -- i.e. the fix was necessary, not
    cosmetic.
    """
    from scipy import stats
    rng = np.random.default_rng(2)
    rhos = []
    for _ in range(60):
        a, b = _null_pair(rng)
        rhos.append(stats.spearmanr(a, b - a).statistic)
    assert np.mean(rhos) < -0.15, (
        "the old baseline-conditioned statistic should be visibly biased here; "
        f"got mean rho={np.mean(rhos):.3f}")


def test_real_redistribution_is_still_detected():
    """A genuine easy->hard transfer must still register."""
    from analysis.compare_runs import redistribution
    rng = np.random.default_rng(3)
    n = 50
    true = rng.uniform(0.2, 0.95, n)
    a = np.clip(true + rng.normal(0, 0.02, n), 0, 1)
    # move quality from the top half to the bottom half, well above the noise
    b = np.clip(a + np.where(true < np.median(true), 0.08, -0.08), 0, 1)
    res = redistribution(a, b, True)
    assert res["rho"] < -0.5, f"real redistribution missed: rho={res['rho']:.3f}"
    assert res["gap"] > 0.10, f"real gap understated: {res['gap']:.4f}"


def test_lpips_direction_is_still_inverted():
    """smaller-is-better metrics stay in quality space."""
    from analysis.compare_runs import redistribution
    rng = np.random.default_rng(4)
    a, b = _null_pair(rng)
    hi = redistribution(a, b, True)
    lo = redistribution(a, b, False)
    assert hi["mean_delta"] == pytest.approx(-lo["mean_delta"])
