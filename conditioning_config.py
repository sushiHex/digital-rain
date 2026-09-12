"""Guard against silent train/eval conditioning mismatches.

This project shipped TWO of them undetected for months, and no test caught
either (see research/2026-07-28-reference-char-mismatch.md):

  1. Reference IMAGE: training rendered "Rg", the holdout rendered "Kg".
     Measured impact: none (p=0.625, median delta 0.000). Harmless, but it
     was invisible -- K and R are both cap-height with no descender, so even
     ink-bbox checks match.

  2. PROMPT: the glyph model (train_lora_kg.py) trains on a 208-char prompt
     with no layout block, but eval always fed it make_prompt()'s 534-char
     structured prompt -- text conditioning it had never seen. Impact:
     IDENTITY 0.9780 -> 0.9936 once corrected, better on ALL 50 fonts
     (p<1e-6, r=0.870). It also flipped the glyph-vs-baseline char_acc
     comparison from a near-miss (r=0.266, failing the r>=0.3 gate) to a
     pass (p=0.0156, r=0.353).

The lesson is that conditioning drift is silent and expensive. This module
records what a checkpoint was trained with, and lets eval assert a match.

Going forward trainers call write_conditioning(). For checkpoints predating
that, infer_legacy() reconstructs it from train_config.json, which is
`vars(args)` and therefore identifies the trainer: train_lora.py has a
`reference_chars` arg, train_lora_kg.py has `use_template` and no
`reference_chars`.
"""
import json
from pathlib import Path

CONDITIONING_FILENAME = "conditioning.json"

# Prompt styles understood by generation_lib.load_generation_pipe().
PROMPT_STRUCTURED = "structured"      # make_prompt(); train_lora.py / baseline
PROMPT_TRAINED_SHORT = "trained-short"  # train_lora_kg.py's hardcoded string


def write_conditioning(output_dir, *, prompt_style, reference_chars,
                       use_template, template_pt=None, prompt_text=None):
    """Record the conditioning a training run actually used, next to its output."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "prompt_style": prompt_style,
        "reference_chars": reference_chars,
        "use_template": bool(use_template),
        "template_pt": str(template_pt) if template_pt else None,
        "prompt_text": prompt_text,
    }
    with open(out / CONDITIONING_FILENAME, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return payload


def _search_dirs(checkpoint_dir):
    """A checkpoint dir and its parent run dir (configs live at either level)."""
    p = Path(checkpoint_dir)
    seen, out = set(), []
    for cand in (p, p.parent, p.parent.parent):
        if cand and str(cand) not in seen:
            seen.add(str(cand))
            out.append(cand)
    return out


def read_conditioning(checkpoint_dir):
    """Explicit conditioning.json, if the run wrote one."""
    for d in _search_dirs(checkpoint_dir):
        f = d / CONDITIONING_FILENAME
        if f.exists():
            try:
                return json.load(open(f, encoding="utf-8"))
            except Exception:
                return None
    return None


def infer_legacy(checkpoint_dir):
    """Reconstruct conditioning for checkpoints predating conditioning.json.

    Discriminator: train_config.json is `vars(args)`, so the trainer is
    identifiable by which flags exist.
    """
    for d in _search_dirs(checkpoint_dir):
        f = d / "train_config.json"
        if not f.exists():
            continue
        try:
            cfg = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if "use_template" in cfg and "reference_chars" not in cfg:
            return {
                "prompt_style": PROMPT_TRAINED_SHORT,
                "reference_chars": "Rg",   # build_dataset.REF_CHARS
                "use_template": bool(cfg.get("use_template")),
                "template_pt": None,
                "source": f"inferred from {f} (train_lora_kg.py lineage)",
            }
        if "reference_chars" in cfg:
            return {
                "prompt_style": PROMPT_STRUCTURED,
                "reference_chars": cfg.get("reference_chars"),
                "use_template": False,
                "template_pt": None,
                "source": f"inferred from {f} (train_lora.py lineage)",
            }
    return None


def expected_conditioning(checkpoint_dir):
    """Explicit record if present, else a legacy inference, else None."""
    if checkpoint_dir is None:
        return None
    return read_conditioning(checkpoint_dir) or infer_legacy(checkpoint_dir)


def _same_template(a, b):
    """Do two template paths name the same file? Tolerates \\ vs / and case."""
    if not a or not b:
        return None
    return Path(str(a).replace("\\", "/")).resolve() == \
        Path(str(b).replace("\\", "/")).resolve()


def check_eval_conditioning(checkpoint_dir, *, prompt_style, holdout_dir=None,
                            template_pt=None):
    """Compare an eval's conditioning against the checkpoint's training config.

    Returns (problems, notes, expected):
      problems -- mismatches with MEASURED material impact (prompt style)
      notes    -- mismatches measured as harmless (reference chars), or
                  unmeasured but real (template)
      expected -- the resolved training conditioning, or None if unknown

    The TEMPLATE was unchecked until 2026-08-08, and it had in fact drifted:
    the glyph checkpoints record `template.pt` while the standard eval path
    passes `template_disambig_mild.pt`. Those differ in 79.93% of elements
    (RMS 0.0506 against the template's own RMS 0.7384, cosine 0.9976) -- a
    mild perturbation rather than a different conditioning, but the same CLASS
    of silent train/eval drift as the prompt-style mismatch, which cost
    IDENTITY 0.9936 -> 0.9780 while char_acc barely moved. Reported as a NOTE,
    not a problem, because its impact is unmeasured; see the research note
    before promoting it.
    """
    expected = expected_conditioning(checkpoint_dir)
    problems, notes = [], []
    if expected is None:
        notes.append(
            f"conditioning for {checkpoint_dir} is UNKNOWN (no conditioning.json, "
            "no recognizable train_config.json) -- cannot verify eval matches training"
        )
        return problems, notes, None

    exp_prompt = expected.get("prompt_style")
    if exp_prompt and prompt_style and exp_prompt != prompt_style:
        problems.append(
            f"PROMPT MISMATCH: checkpoint trained with prompt_style={exp_prompt!r} "
            f"but eval is using {prompt_style!r}. This measurably suppresses IDENTITY "
            f"(0.9936 -> 0.9780 on the glyph model, all 50 fonts worse). "
            f"Pass --prompt-style {exp_prompt}."
        )

    if holdout_dir:
        mf = Path(holdout_dir) / "manifest.json"
        if mf.exists():
            try:
                got = json.load(open(mf, encoding="utf-8")).get("reference_chars")
            except Exception:
                got = None
            exp_ref = expected.get("reference_chars")
            if got and exp_ref and got != exp_ref:
                notes.append(
                    f"reference-image chars differ: trained on {exp_ref!r}, holdout "
                    f"rendered {got!r}. Measured impact: none (p=0.625) -- informational."
                )

    exp_tpl = expected.get("template_pt")
    same = _same_template(exp_tpl, template_pt)
    if same is False:
        notes.append(
            f"TEMPLATE DRIFT: checkpoint trained with {Path(str(exp_tpl)).name!r} "
            f"but eval is using {Path(str(template_pt)).name!r}. Impact UNMEASURED. "
            f"This is the axis the validator missed until 2026-08-08."
        )
    elif template_pt and exp_tpl is None and expected.get("use_template"):
        notes.append(
            f"checkpoint records use_template=True but no template path; cannot "
            f"verify the eval's {Path(str(template_pt)).name!r} matches training."
        )
    return problems, notes, expected
