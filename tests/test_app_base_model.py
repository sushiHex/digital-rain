"""The demo must load each adapter against the base model it was trained on.

app.py derives the base from the checkpoint's own train_config.json rather than
assuming one, the same principle conditioning_config applies to prompt_style.

Note on the justification: the 4B and 9B adapters have different hidden dims
(3072 vs 4096), so crossing them raises a shape error rather than running
silently. An earlier version of this docstring claimed otherwise. The guard is
still worth having -- it resolves the right base instead of surfacing a shape
traceback, and a DIMENSION-COMPATIBLE mismatch (another revision, a distilled
variant of the same size) would be genuinely silent.

The default matters for licensing, not just quality: the demo defaults to the
Apache-2.0 4B because the 9B carries the FLUX Non-Commercial Licence, which
makes a hosted demo a licensing problem.
"""
import json

import pytest


def test_default_checkpoint_and_model_are_the_apache_4b():
    import app
    assert "4b" in app.DEFAULT_CHECKPOINT.lower()
    assert app.DEFAULT_MODEL.endswith("klein-base-4B")


def test_resolve_reads_base_from_checkpoint_train_config(tmp_path):
    """A 9B checkpoint must resolve to the 9B even though the default is 4B."""
    from app import resolve_base_model
    ckpt = tmp_path / "final"
    ckpt.mkdir()
    (tmp_path / "train_config.json").write_text(
        json.dumps({"model": "black-forest-labs/FLUX.2-klein-base-9B", "rank": 32}))
    assert resolve_base_model(str(ckpt)) == "black-forest-labs/FLUX.2-klein-base-9B"


def test_resolve_finds_train_config_beside_the_checkpoint_dir(tmp_path):
    """train_config.json sits in the run directory, not inside final/."""
    from app import resolve_base_model
    (tmp_path / "checkpoint-5000").mkdir()
    (tmp_path / "train_config.json").write_text(
        json.dumps({"model": "black-forest-labs/FLUX.2-klein-base-4B"}))
    got = resolve_base_model(str(tmp_path / "checkpoint-5000"))
    assert got == "black-forest-labs/FLUX.2-klein-base-4B"


def test_explicit_model_wins_over_the_checkpoint(tmp_path):
    from app import resolve_base_model
    ckpt = tmp_path / "final"
    ckpt.mkdir()
    (tmp_path / "train_config.json").write_text(
        json.dumps({"model": "black-forest-labs/FLUX.2-klein-base-4B"}))
    assert resolve_base_model(str(ckpt), "some/other-base") == "some/other-base"


def test_resolve_falls_back_when_nothing_is_recorded(tmp_path):
    from app import DEFAULT_MODEL, resolve_base_model
    assert resolve_base_model(str(tmp_path / "nope")) == DEFAULT_MODEL


def test_blurb_reports_the_licence_of_whatever_is_loaded(tmp_path):
    """The UI must not claim Apache-2.0 while running the non-commercial 9B."""
    import app
    app._config["checkpoint"] = str(tmp_path)
    app._config["model"] = "black-forest-labs/FLUX.2-klein-base-9B"
    assert "Non-Commercial" in app._pipeline_blurb()
    app._config["model"] = "black-forest-labs/FLUX.2-klein-base-4B"
    blurb = app._pipeline_blurb()
    assert "Apache-2.0" in blurb and "Non-Commercial" not in blurb


def test_cli_exposes_model_flag():
    """--model must exist; without it the demo is pinned to one base."""
    import inspect

    import app
    src = inspect.getsource(app.main)
    assert '"--model"' in src
    assert "resolve_base_model" in src
