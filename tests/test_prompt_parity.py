"""Guard the two prompt strings against silent drift.

atlas_constants.TRAINED_SHORT_PROMPT must stay byte-identical to the literal
train_lora_kg.py actually trains with. If someone edits one and not the other,
`eval_checkpoint.py --prompt-style trained-short` would quietly stop
reproducing the training condition, which is exactly the class of bug
research/2026-07-28-reference-char-mismatch.md documents.
"""
import ast
from pathlib import Path

from atlas_constants import TRAINED_SHORT_PROMPT, make_prompt


def _trainer_prompt_literal():
    """Extract the string assigned to `prompt` in train_lora_kg.py's main()."""
    tree = ast.parse(Path("train_lora_kg.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Name) and t.id == "prompt":
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    return node.value.value
    return None


def test_trained_short_prompt_matches_trainer():
    literal = _trainer_prompt_literal()
    assert literal is not None, "could not find `prompt = <str>` in train_lora_kg.py"
    assert literal == TRAINED_SHORT_PROMPT, (
        "atlas_constants.TRAINED_SHORT_PROMPT has drifted from train_lora_kg.py's prompt.\n"
        f"  trainer:  {literal!r}\n"
        f"  constant: {TRAINED_SHORT_PROMPT!r}"
    )


def test_no_module_re_hardcodes_the_trained_prompt():
    """Only the constant and the trainer may spell the prompt out literally.

    A third copy is exactly how the prompt mismatch shipped in the first place:
    a test that guards two files does not stop a fourth from drifting.
    """
    marker = "strictly derived from the reference image \"Kg\""
    allowed = {"atlas_constants.py", "train_lora_kg.py"}
    offenders = []
    for path in Path(".").glob("*.py"):
        if path.name in allowed:
            continue
        try:
            if marker in path.read_text(encoding="utf-8"):
                offenders.append(path.name)
        except Exception:
            pass
    assert not offenders, (
        f"{offenders} hardcode the trained prompt; import "
        "atlas_constants.TRAINED_SHORT_PROMPT instead"
    )


def test_the_two_prompt_styles_really_differ():
    """Sanity: the mismatch this flag exists to test is real, not imagined."""
    structured = make_prompt("Kg")
    assert structured != TRAINED_SHORT_PROMPT
    assert "Layout:" in structured, "structured prompt should carry the row layout block"
    assert "Layout:" not in TRAINED_SHORT_PROMPT, "trained prompt should have no layout block"
    assert len(structured) > len(TRAINED_SHORT_PROMPT)
