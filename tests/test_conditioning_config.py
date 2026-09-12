"""Tests for the train/eval conditioning guard.

These encode the two real mismatches this project shipped, so a regression
would fail here rather than silently suppressing eval numbers again.
"""
import json

import pytest

from conditioning_config import (
    PROMPT_STRUCTURED,
    PROMPT_TRAINED_SHORT,
    check_eval_conditioning,
    expected_conditioning,
    infer_legacy,
    read_conditioning,
    write_conditioning,
)


def _mk(tmp_path, name, cfg):
    d = tmp_path / name
    (d / "checkpoint-5000").mkdir(parents=True)
    (d / "train_config.json").write_text(json.dumps(cfg), encoding="utf-8")
    return d / "checkpoint-5000"


def test_infers_glyph_lineage_from_train_config(tmp_path):
    """train_lora_kg.py: has use_template, no reference_chars -> trained-short."""
    ck = _mk(tmp_path, "glyph_run", {"dataset_dir": "dataset_v2", "rank": 32, "use_template": True})
    got = infer_legacy(ck)
    assert got["prompt_style"] == PROMPT_TRAINED_SHORT
    assert got["reference_chars"] == "Rg"


def test_infers_baseline_lineage_from_train_config(tmp_path):
    """train_lora.py: has reference_chars -> structured."""
    ck = _mk(tmp_path, "base_run", {"dataset_dir": "dataset_Kg", "rank": 16, "reference_chars": "Kg"})
    got = infer_legacy(ck)
    assert got["prompt_style"] == PROMPT_STRUCTURED
    assert got["reference_chars"] == "Kg"


def test_explicit_conditioning_beats_inference(tmp_path):
    ck = _mk(tmp_path, "run", {"use_template": True})
    write_conditioning(ck.parent, prompt_style=PROMPT_STRUCTURED,
                       reference_chars="Ho", use_template=False)
    got = expected_conditioning(ck)
    assert got["prompt_style"] == PROMPT_STRUCTURED   # explicit file wins
    assert got["reference_chars"] == "Ho"
    assert read_conditioning(ck) is not None


def test_flags_the_real_prompt_mismatch(tmp_path):
    """The exact bug: glyph checkpoint evaluated with the structured prompt."""
    ck = _mk(tmp_path, "glyph_run", {"use_template": True})
    problems, notes, exp = check_eval_conditioning(ck, prompt_style=PROMPT_STRUCTURED)
    assert exp["prompt_style"] == PROMPT_TRAINED_SHORT
    assert any("PROMPT MISMATCH" in p for p in problems)
    assert any("--prompt-style trained-short" in p for p in problems)


def test_matching_prompt_is_clean(tmp_path):
    ck = _mk(tmp_path, "glyph_run", {"use_template": True})
    problems, notes, _ = check_eval_conditioning(ck, prompt_style=PROMPT_TRAINED_SHORT)
    assert problems == []


def test_reference_char_diff_is_a_note_not_a_problem(tmp_path):
    """Rg/Kg measured harmless (p=0.625) -> informational, must NOT block."""
    ck = _mk(tmp_path, "glyph_run", {"use_template": True})
    hold = tmp_path / "holdout"
    hold.mkdir()
    (hold / "manifest.json").write_text(json.dumps({"reference_chars": "Kg"}), encoding="utf-8")
    problems, notes, _ = check_eval_conditioning(
        ck, prompt_style=PROMPT_TRAINED_SHORT, holdout_dir=hold)
    assert problems == []
    assert any("reference-image chars differ" in n for n in notes)


def test_unknown_conditioning_is_reported(tmp_path):
    d = tmp_path / "mystery" / "checkpoint-1"
    d.mkdir(parents=True)
    problems, notes, exp = check_eval_conditioning(d, prompt_style=PROMPT_STRUCTURED)
    assert exp is None
    assert any("UNKNOWN" in n for n in notes)


def test_real_repo_checkpoints_resolve_correctly():
    """Guard the two actual checkpoints this project evaluates."""
    import os
    glyph = "training_glyph_r32_5000/checkpoint-5000"
    base = "experiments/20260412-215340_Kg_structured_prompt_5000/checkpoints/checkpoint-5000"
    if os.path.isdir(glyph):
        assert expected_conditioning(glyph)["prompt_style"] == PROMPT_TRAINED_SHORT
    if os.path.isdir(base):
        assert expected_conditioning(base)["prompt_style"] == PROMPT_STRUCTURED
