import json
from pathlib import Path

import pytest


def test_pending_jobs_skips_existing(tmp_path):
    from candidate_gen import pending_jobs, candidate_path
    fonts = ["FontA", "FontB"]
    specs = {"baseline": {}, "glyph": {}}
    seeds = {"baseline": [0], "glyph": [0, 1]}
    out = str(tmp_path)
    all_jobs = pending_jobs(fonts, specs, seeds, out)
    assert len(all_jobs) == 2 * (1 + 2)  # 2 fonts x (1 baseline + 2 glyph seeds)
    # simulate one done
    p = Path(candidate_path(out, "FontA", "glyph", 1)); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b"x")
    remaining = pending_jobs(fonts, specs, seeds, out)
    assert len(remaining) == 2 * 3 - 1
    assert all(not (j["font"] == "FontA" and j["model"] == "glyph" and j["seed"] == 1) for j in remaining)


def test_candidate_key_format():
    from candidate_gen import candidate_key
    assert candidate_key("FontA", "glyph", 3) == "FontA__glyph__seed3"


def test_candidate_path_format():
    from candidate_gen import candidate_path
    assert candidate_path("out", "FontA", "baseline", 0) == "out/candidates/FontA/baseline__seed0.png"


def test_load_fonts_from_manifest(tmp_path):
    """Holdout-style manifest.json: top-level {"fonts": [{"name", "reference"}]},
    reference paths are relative to the manifest's own directory."""
    from candidate_gen import load_fonts_from_manifest
    (tmp_path / "references").mkdir()
    (tmp_path / "references" / "FontA.png").write_bytes(b"x")
    manifest = {"fonts": [{"name": "FontA", "reference": "references/FontA.png"}]}
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    fonts, refs = load_fonts_from_manifest(str(manifest_path))

    assert fonts == ["FontA"]
    assert refs["FontA"] == str(tmp_path / "references" / "FontA.png")


def test_load_fonts_from_glob(tmp_path):
    """dataset_v2-style layout: font list built from atlases/*.png (name = stem),
    references at a sibling references/<name>.png. Fonts missing a reference
    image are skipped."""
    from candidate_gen import load_fonts_from_glob
    (tmp_path / "atlases").mkdir()
    (tmp_path / "references").mkdir()
    (tmp_path / "atlases" / "FontA.png").write_bytes(b"x")
    (tmp_path / "references" / "FontA.png").write_bytes(b"x")
    (tmp_path / "atlases" / "FontB.png").write_bytes(b"x")  # no matching reference

    fonts, refs = load_fonts_from_glob(str(tmp_path / "atlases" / "*.png"))

    assert fonts == ["FontA"]
    assert refs["FontA"] == str(tmp_path / "references" / "FontA.png")


def test_resolve_conditioning_reads_the_checkpoint(tmp_path):
    """prompt_style/reference_chars come from the CHECKPOINT, not the defaults.

    Regression: candidate_gen used to call load_generation_pipe without either,
    silently taking its "structured"/"Kg" defaults while every train_lora_kg.py
    lineage checkpoint is "trained-short"/"Rg". That mis-conditioning is
    invisible to char_acc but measurably suppresses IDENTITY.
    """
    from candidate_gen import resolve_conditioning

    ckpt = tmp_path / "checkpoint-5000"
    ckpt.mkdir()
    (tmp_path / "conditioning.json").write_text(json.dumps({
        "prompt_style": "trained-short", "reference_chars": "Rg",
        "use_template": True, "template_pt": "dataset_v2/cache/template.pt",
    }))

    spec = resolve_conditioning({"checkpoint": str(ckpt), "use_template": True,
                                 "template_pt": "t.pt"})
    assert spec["prompt_style"] == "trained-short"
    assert spec["reference_chars"] == "Rg"


def test_resolve_conditioning_defaults_when_unknown(tmp_path):
    """An unrecognizable checkpoint falls back to load_generation_pipe's defaults."""
    from candidate_gen import resolve_conditioning, BASE_9B

    spec = resolve_conditioning({"checkpoint": str(tmp_path / "nope"),
                                 "use_template": False, "template_pt": None})
    assert spec["prompt_style"] == "structured"
    assert spec["reference_chars"] == "Kg"
    assert spec["model"] == BASE_9B


def test_resolve_conditioning_preserves_explicit_base_model(tmp_path):
    """A caller-supplied --base-model (the 4B) survives resolution."""
    from candidate_gen import resolve_conditioning

    spec = resolve_conditioning({"checkpoint": str(tmp_path), "use_template": True,
                                 "template_pt": None,
                                 "model": "black-forest-labs/FLUX.2-klein-base-4B"})
    assert spec["model"] == "black-forest-labs/FLUX.2-klein-base-4B"


def test_cli_glyph_overrides_require_glyph_model():
    """--glyph-checkpoint without 'glyph' in --models is a clear error, not a KeyError."""
    from candidate_gen import main
    with pytest.raises(SystemExit):
        main(["--fonts-manifest", "a.json", "--models", "baseline",
              "--glyph-checkpoint", "some/ckpt"])


def test_cli_requires_exactly_one_fonts_source():
    """--fonts-manifest and --fonts-glob are mutually exclusive and one is required."""
    from candidate_gen import _build_arg_parser
    ap = _build_arg_parser()
    with pytest.raises(SystemExit):
        ap.parse_args([])  # neither given
    with pytest.raises(SystemExit):
        ap.parse_args(["--fonts-manifest", "a.json", "--fonts-glob", "b/*.png"])  # both given
    args = ap.parse_args(["--fonts-manifest", "a.json"])
    assert args.fonts_manifest == "a.json"
    assert args.fonts_glob is None
