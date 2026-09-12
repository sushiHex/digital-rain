"""The cosine LR horizon must be counted in OPTIMIZER steps, not microbatches.

`--steps` counts microbatch iterations (the loop increments global_step once
per microbatch, and checkpoint names follow it), but the LR scheduler only
advances on the accumulation boundary. Using args.steps as the cosine horizon
therefore runs the schedule at 1/grad_accum speed and stops it partway.

Every checkpoint in this repo was trained under that bug -- bs=1, accum=2,
steps=5000 -- so all of them got 2,500 optimizer updates against a 5,000-step
horizon and ended at 51.6% of peak LR, never reaching an annealing phase.
Training loss cannot show this: it was the LOWEST of any run in one case.

These tests reconstruct the scheduler exactly as train_lora_kg builds it.
"""
import math

import pytest


def _lambda(steps, accum, warmup, legacy=False):
    """Rebuild the lr_lambda for the given config (mirrors train_lora_kg)."""
    sched_total = steps if legacy else max(1, math.ceil(steps / max(accum, 1)))

    def f(step):
        if step < warmup:
            return step / max(warmup, 1)
        progress = (step - warmup) / max(sched_total - warmup, 1)
        return 0.5 * (1.0 + math.cos(math.pi * min(progress, 1.0)))
    return f


def _final_lr(steps, accum, warmup, base_lr=1e-4, legacy=False):
    """LR after the run's LAST optimizer step."""
    return base_lr * _lambda(steps, accum, warmup, legacy)(steps // accum)


def test_legacy_horizon_reproduces_the_observed_final_lr():
    """Pin the bug against the number in the real training log: 5.16e-05."""
    got = _final_lr(5000, 2, 100, legacy=True)
    assert got == pytest.approx(5.1603e-05, rel=1e-3), got
    assert got / 1e-4 == pytest.approx(0.516, abs=0.001), \
        "the legacy schedule should end at ~51.6% of peak"


def test_fixed_horizon_actually_anneals():
    """The whole point: the corrected schedule must reach ~0 by the end."""
    got = _final_lr(5000, 2, 100)
    assert got < 1e-4 * 0.001, f"schedule did not anneal: final LR {got}"


def test_accum_one_is_unaffected():
    """With no accumulation the two forms coincide -- the bug needs accum>1."""
    assert _final_lr(5000, 1, 100) == pytest.approx(_final_lr(5000, 1, 100, legacy=True))


def test_higher_accumulation_made_the_bug_worse():
    """accum=4 would have stopped even earlier; monotone in accum."""
    lrs = [_final_lr(5000, a, 100, legacy=True) for a in (1, 2, 4, 8)]
    assert lrs == sorted(lrs), f"legacy final LR should rise with accum: {lrs}"
    assert lrs[0] < lrs[-1]


def test_warmup_is_unchanged_by_the_fix():
    """Warmup was already in optimizer-step units; the fix must not move it."""
    fixed, legacy = _lambda(5000, 2, 100), _lambda(5000, 2, 100, legacy=True)
    for s in (0, 1, 50, 99):
        assert fixed(s) == pytest.approx(legacy(s))
    # At exactly step == warmup both are at progress 0, i.e. peak LR; they
    # coincide there by construction. Divergence starts on the next step.
    assert fixed(100) == pytest.approx(1.0) == pytest.approx(legacy(100))
    assert fixed(101) < legacy(101), "the fixed schedule must decay faster"


def test_the_schedule_never_turns_back_up():
    """Past the horizon a raw cosine RISES again; the clamp must prevent that."""
    f = _lambda(1000, 2, 100)
    end = f(500)
    for over in (600, 900, 5000):
        assert f(over) <= end + 1e-12, f"LR rose after the horizon at step {over}"
        assert f(over) >= 0.0


def test_source_uses_an_optimizer_step_horizon_and_clamps():
    """Guard the real module, not just this reconstruction."""
    import inspect

    import train_lora_kg
    src = inspect.getsource(train_lora_kg.main)
    assert "sched_total" in src, "horizon must be computed, not taken from args.steps"
    assert "math.ceil(args.steps / max(args.grad_accum, 1))" in src
    assert "min(progress, 1.0)" in src, "cosine must be clamped at the horizon"


def test_legacy_flag_exists_so_old_checkpoints_stay_reproducible():
    import inspect

    import train_lora_kg
    assert "--legacy-lr-horizon" in inspect.getsource(train_lora_kg.build_parser) \
        if hasattr(train_lora_kg, "build_parser") \
        else "--legacy-lr-horizon" in inspect.getsource(train_lora_kg)
