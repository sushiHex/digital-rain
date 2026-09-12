"""The conditioning validator must check the TEMPLATE, not just the prompt.

Until 2026-08-08 `check_eval_conditioning` compared prompt_style and reference
chars and never looked at the template. It had in fact drifted: the glyph
checkpoints record `dataset_v2/cache/template.pt`, while the standard eval path
(`run_glyph_4b_r32.sh`) passes `template_disambig_mild.pt`. So an eval could
print "conditioning OK: eval matches training" while feeding the model a
conditioning tensor differing in 79.93% of its elements.

Mild in magnitude (cosine 0.9976) but the same CLASS of silent drift as the
prompt-style mismatch, which cost IDENTITY 0.9936 -> 0.9780 while char_acc
barely moved -- i.e. exactly the kind of regression this project's headline
metric cannot see.
"""
import json

import pytest

from conditioning_config import check_eval_conditioning


def _ckpt(tmp_path, **over):
    d = tmp_path / "ckpt"
    d.mkdir()
    cfg = {"prompt_style": "trained-short", "reference_chars": "Rg",
           "use_template": True, "template_pt": "dataset_v2\\cache\\template.pt",
           "prompt_text": None}
    cfg.update(over)
    (d / "conditioning.json").write_text(json.dumps(cfg), encoding="utf-8")
    return str(d)


def test_a_different_template_is_reported(tmp_path):
    """The exact drift that shipped: neutral trained, disambig-mild evaluated."""
    _, notes, _ = check_eval_conditioning(
        _ckpt(tmp_path), prompt_style="trained-short",
        template_pt="dataset_v2/cache/template_disambig_mild.pt")
    assert any("TEMPLATE DRIFT" in n for n in notes), \
        f"template drift went unreported; notes={notes}"


def test_the_matching_template_is_silent(tmp_path):
    _, notes, _ = check_eval_conditioning(
        _ckpt(tmp_path), prompt_style="trained-short",
        template_pt="dataset_v2/cache/template.pt")
    assert not any("TEMPLATE" in n for n in notes), notes


def test_separator_and_case_differences_are_not_drift(tmp_path):
    """The record uses Windows backslashes; callers pass forward slashes."""
    _, notes, _ = check_eval_conditioning(
        _ckpt(tmp_path), prompt_style="trained-short",
        template_pt="dataset_v2\\cache\\template.pt")
    assert not any("TEMPLATE" in n for n in notes), notes


def test_template_drift_is_a_note_not_a_hard_problem(tmp_path):
    """Impact is unmeasured, so it must not trip --strict-conditioning yet."""
    problems, notes, _ = check_eval_conditioning(
        _ckpt(tmp_path), prompt_style="trained-short",
        template_pt="dataset_v2/cache/template_disambig_mild.pt")
    assert problems == [], f"unmeasured drift must not block: {problems}"
    assert notes


def test_prompt_mismatch_still_dominates(tmp_path):
    """The template check must not displace the measured prompt-style check."""
    problems, _, _ = check_eval_conditioning(
        _ckpt(tmp_path), prompt_style="structured",
        template_pt="dataset_v2/cache/template.pt")
    assert any("PROMPT MISMATCH" in p for p in problems)


def test_no_template_supplied_is_not_flagged(tmp_path):
    """Callers that do not use a template must not be nagged about drift."""
    _, notes, _ = check_eval_conditioning(
        _ckpt(tmp_path), prompt_style="trained-short", template_pt=None)
    assert not any("TEMPLATE DRIFT" in n for n in notes), notes


def test_the_real_checkpoint_records_the_neutral_template():
    """Guard the fact the finding rests on, so a re-record is noticed."""
    import os

    p = "training_glyph_4b_r32_5000/conditioning.json"
    if not os.path.isfile(p):
        pytest.skip("4B checkpoint not present in this checkout")
    rec = json.load(open(p, encoding="utf-8"))
    assert rec["template_pt"].replace("\\", "/").endswith("cache/template.pt"), \
        f"the 4B checkpoint no longer records the neutral template: {rec['template_pt']}"
