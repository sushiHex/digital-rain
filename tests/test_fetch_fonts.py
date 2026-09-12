import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_fetch_fonts_help():
    result = subprocess.run(
        [sys.executable, "pipeline/fetch_fonts.py", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--source" in result.stdout
    assert "--output" in result.stdout


def test_directory_adapter_copies_fonts(tmp_path):
    src = tmp_path / "source"
    src.mkdir()
    fake_font = src / "TestFont-Regular.ttf"
    fake_font.write_bytes(b"\x00\x01\x00\x00" + b"\x00" * 100)

    pool = tmp_path / "pool"

    result = subprocess.run(
        [sys.executable, "pipeline/fetch_fonts.py",
         "--source", "directory", "--path", str(src), "--output", str(pool)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert (pool / "TestFont-Regular.ttf").exists()

    manifest_path = pool / "source_manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert len(manifest) == 1
    assert manifest[0]["filename"] == "TestFont-Regular.ttf"
    assert manifest[0]["source"] == "directory"


def test_directory_adapter_idempotent(tmp_path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "Font.ttf").write_bytes(b"\x00\x01\x00\x00" + b"\x00" * 100)

    pool = tmp_path / "pool"

    for _ in range(2):
        subprocess.run(
            [sys.executable, "pipeline/fetch_fonts.py",
             "--source", "directory", "--path", str(src), "--output", str(pool)],
            capture_output=True, text=True,
        )

    manifest = json.loads((pool / "source_manifest.json").read_text())
    assert len(manifest) == 1
    font_files = list(pool.glob("*.ttf"))
    assert len(font_files) == 1


def test_google_fonts_adapter_prefixes_family(tmp_path):
    """Google Fonts adapter should prefix filenames with family directory name."""
    # Simulate google-fonts layout: ofl/<family>/<font>.ttf
    gf_root = tmp_path / "google-fonts"
    family_dir = gf_root / "ofl" / "testfamily"
    family_dir.mkdir(parents=True)
    fake_font = family_dir / "TestFamily-Regular.ttf"
    fake_font.write_bytes(b"\x00\x01\x00\x00" + b"\x00" * 100)

    pool = tmp_path / "pool"
    result = subprocess.run(
        [sys.executable, "pipeline/fetch_fonts.py",
         "--source", "google-fonts", "--path", str(gf_root), "--output", str(pool)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert (pool / "testfamily_TestFamily-Regular.ttf").exists()
    manifest = json.loads((pool / "source_manifest.json").read_text())
    assert len(manifest) == 1
    assert manifest[0]["filename"] == "testfamily_TestFamily-Regular.ttf"
    assert manifest[0]["source"] == "google-fonts"
    assert manifest[0]["license"] == "OFL-1.1"
