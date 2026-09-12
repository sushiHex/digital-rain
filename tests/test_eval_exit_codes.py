"""The eval must be able to FAIL. Until 2026-08-13 it could not.

`eval_checkpoint.py` ended with a bare `main()`, so the process exit status was
ALWAYS 0 no matter which error path ran. Every runner in the repo does

    python eval_checkpoint.py ... || fail eval $?

so every one of those guards was inert, and each runner wrote its `_DONE`
marker after an eval that had refused to run. CLAUDE.md's rule -- "Never infer
success from the absence of a crash" -- was unenforceable in the one place it
mattered most.

Also pins the reader-duplication fix: analysis/seed_variance.py carried its own
copy of per_font_per_seed including the bool() coercion that
analysis/multiseed_compare.py fixed. Two copies of a reader means a fix lands
in one of them.
"""
import subprocess
import sys

import pytest


def _run(*args):
    return subprocess.run([sys.executable, "eval_checkpoint.py", *args],
                          capture_output=True, text=True, timeout=300)


def test_contradictory_flags_exit_nonzero(tmp_path):
    """argparse's own required-arg errors already exited 2; the point is the
    hand-written guards further in, which used a bare `return`."""
    r = _run("--skip-generate", "--skip-score",
             "--holdout", "eval_holdout", "--out", str(tmp_path / "o"))
    assert r.returncode != 0, "an eval that does nothing must not report success"
    assert "nothing to do" in (r.stdout + r.stderr).lower()


def test_missing_checkpoint_exits_nonzero():
    r = _run("--holdout", "eval_holdout")
    assert r.returncode != 0, "a missing --checkpoint must not report success"


def test_help_still_exits_zero():
    """The fix must not make ordinary invocations look like failures."""
    assert _run("--help").returncode == 0


def test_entrypoint_propagates_the_return_value():
    import inspect

    import eval_checkpoint
    src = inspect.getsource(eval_checkpoint)
    assert "sys.exit(main() or 0)" in src, \
        "a bare main() call discards every failure code"


def test_seed_variance_shares_the_fixed_reader():
    """Not its own copy -- the bool() coercion lived in the duplicate."""
    import inspect

    from analysis import seed_variance
    src = inspect.getsource(seed_variance.per_font_per_seed)
    assert "multiseed_compare" in src, "must import the shared reader"
    # Check the BODY, not the docstring -- which legitimately names the bug.
    body = src.split('"""')[-1]
    assert "bool(" not in body, "the coercion bug is back in the duplicate"


def test_seed_variance_reports_real_variance_for_a_continuous_metric(tmp_path):
    """The symptom the duplicate produced: SD 0.0000 and gap/SE = inf."""
    import json

    import numpy as np

    from analysis.seed_variance import per_font_per_seed

    p = tmp_path / "scores.json"
    p.write_text(json.dumps({
        "FontA__glyph__seed0": [{"dino_cos": 0.20}],
        "FontA__glyph__seed1": [{"dino_cos": 0.80}],
        "FontB__glyph__seed0": [{"dino_cos": 0.55}],
        "FontB__glyph__seed1": [{"dino_cos": 0.65}],
    }), encoding="utf-8")
    out = per_font_per_seed(str(p), "dino_cos")
    vals = [v for per_seed in out.values() for v in per_seed.values()]
    assert np.std(vals) > 1e-6, "continuous metric collapsed to a constant"
    assert out["FontA"][0] == pytest.approx(0.20)
