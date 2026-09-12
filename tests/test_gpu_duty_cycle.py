"""Duty-cycle throttling, the only way to leave the desktop GPU headroom here.

A saturating CUDA job takes ~98% of the GPU's 3d engine (measured), and
dwm.exe -- which composites every window on screen -- time-slices into what is
left. Nothing on this hardware can RESERVE capacity:

  * NVIDIA MPS, whose CUDA_MPS_ACTIVE_THREAD_PERCENTAGE caps SM share, is
    Linux-only; nvidia-cuda-mps-control is not present on Windows.
  * MIG is datacenter-only (A100/H100), not consumer Ampere.
  * The Ryzen 9 3950X has NO integrated GPU, so the display cannot be moved off
    the compute card -- Win32_VideoController lists the 3090 alone.
  * Power and clock caps slow the whole GPU equally; they free no slices.

So the training loop yields wall-clock instead. These tests pin the arithmetic
and the flag surface; the synchronize that makes it real is asserted on the
source, since it cannot be exercised without a GPU.
"""
import inspect

import pytest

import train_lora_kg


def sleep_for(busy, duty):
    """The formula used in the loop: idle so busy/(busy+idle) == duty."""
    return busy * (1.0 - duty) / duty


def test_full_duty_means_no_sleep():
    assert sleep_for(1.0, 1.0) == 0.0


def test_ninety_percent_duty_costs_about_eleven_percent():
    s = sleep_for(1.0, 0.9)
    assert s == pytest.approx(0.1111, abs=1e-4)
    assert 1.0 / (1.0 + s) == pytest.approx(0.9), "GPU must be busy 90% of wall-clock"


def test_the_resulting_busy_fraction_is_the_requested_duty():
    """The property that matters, across the useful range."""
    for duty in (0.5, 0.75, 0.9, 0.95, 0.99):
        for busy in (0.4, 1.0, 3.7):
            idle = sleep_for(busy, duty)
            assert busy / (busy + idle) == pytest.approx(duty)


def test_lower_duty_sleeps_longer():
    s = [sleep_for(1.0, d) for d in (0.95, 0.9, 0.75, 0.5)]
    assert s == sorted(s), s


def test_flag_exists_with_an_env_override_and_defaults_to_off():
    src = inspect.getsource(train_lora_kg.main)
    assert "--gpu-duty-cycle" in src
    assert 'os.environ.get("GPU_DUTY_CYCLE", "1.0")' in src, \
        "runners must be able to set it without editing the script"


def test_the_loop_synchronizes_before_sleeping():
    """Load-bearing: without it the CPU sleeps while the GPU drains its queue.

    A throttle that forgets this looks correct, logs correctly, and does
    absolutely nothing -- the async CUDA queue keeps the device busy for the
    whole sleep.
    """
    src = inspect.getsource(train_lora_kg.main)
    # Anchor on the step-level throttle's own guard. Anchoring on the duty
    # value instead would match the startup log line and let a throttle with no
    # synchronize pass.
    i = src.find("if throttle_at_step:")
    assert i != -1, "step-level throttle block not found"
    block = src[i:i + 400]
    assert "torch.cuda.synchronize()" in block
    assert block.index("torch.cuda.synchronize()") < block.index("time.sleep("), \
        "synchronize must come BEFORE the sleep or the throttle is a no-op"


class _Blk:
    pass


def _fake_model(n_double=19, n_single=38, wrapped=False):
    """A stand-in exposing the same module PATHS as the real transformer."""
    import torch.nn as nn

    class Blk(nn.Module):
        def forward(self, x):
            return x

    class Inner(nn.Module):
        def __init__(self):
            super().__init__()
            self.transformer_blocks = nn.ModuleList([Blk() for _ in range(n_double)])
            self.single_transformer_blocks = nn.ModuleList(
                [Blk() for _ in range(n_single)])

    if not wrapped:
        return Inner()

    class PeftLike(nn.Module):
        def __init__(self):
            super().__init__()
            self.base_model = nn.Module()
            self.base_model.model = Inner()

    return PeftLike()


def test_block_hooks_are_installed_on_every_nth_block():
    h = train_lora_kg.install_block_throttle(_fake_model(), duty=0.9, every_n=4)
    assert len(h) == len(range(0, 19 + 38, 4)) == 15
    for x in h:
        x.remove()


def test_blocks_are_found_THROUGH_the_peft_wrapper():
    """The real transformer is PEFT-wrapped by the time this runs.

    Attribute access can resolve through a proxy or not at all, and a miss
    would silently downgrade to step-level throttling -- the very thing the
    block hooks exist to replace. So the search goes by module path.
    """
    bare = train_lora_kg.install_block_throttle(_fake_model(), 0.9, 4)
    wrapped = train_lora_kg.install_block_throttle(
        _fake_model(wrapped=True), 0.9, 4)
    assert len(wrapped) == len(bare) == 15
    for x in bare + wrapped:
        x.remove()


def test_throttle_is_disabled_in_the_obvious_ways():
    import torch.nn as nn

    assert train_lora_kg.install_block_throttle(_fake_model(), 1.0, 4) == []
    assert train_lora_kg.install_block_throttle(_fake_model(), 0.9, 0) == []
    assert train_lora_kg.install_block_throttle(nn.Linear(2, 2), 0.9, 4) == []


def test_step_and_block_throttles_are_mutually_exclusive():
    """Both active would double the idle and halve throughput for nothing."""
    src = inspect.getsource(train_lora_kg.main)
    assert "throttle_at_step = gpu_duty_cycle < 1.0 and not throttle_handles" in src
    assert "if throttle_at_step:" in src, \
        "the step-level sleep must be guarded by the fallback flag, not by duty"


def test_block_hook_synchronizes_before_sleeping():
    src = inspect.getsource(train_lora_kg.install_block_throttle)
    assert src.index("torch.cuda.synchronize()") < src.index("time.sleep("), \
        "without the sync the GPU drains its queue through the sleep"


def test_block_hook_ignores_implausibly_long_gaps():
    """First call, and any pause between steps, must not cause a huge sleep."""
    src = inspect.getsource(train_lora_kg.install_block_throttle)
    assert "0.0 < busy < 5.0" in src


def test_out_of_range_duty_is_rejected():
    src = inspect.getsource(train_lora_kg.main)
    assert "0.05 <= gpu_duty_cycle <= 1.0" in src, \
        "a duty of 0 would sleep forever; a duty above 1 is meaningless"
