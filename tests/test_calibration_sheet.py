"""GPU-free, network-free tests for analysis/calibration_sheet.py.

Pins three things that would silently ruin a real labelling session: the
label-parsing rule on the exact truncation case that has broken this same
parsing logic elsewhere in the repo (`tests/test_candidate_labels.py`), the
shape of the CSV template the owner fills in, and the refuse-to-overwrite
guard that protects a filled-in label set from being clobbered by a rerun.
"""
import csv
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.calibration_sheet import (
    CSV_FIELDS,
    N_DESCRIPTIONS,
    N_SEEDS,
    build_csv_rows,
    csv_has_labels,
    discover_candidates,
    parse_label,
    render_overview,
    render_page,
    write_csv_template,
)

STYLES = [f"style {i:02d} description text" for i in range(N_DESCRIPTIONS)]


# ---------------------------------------------------------------------------
# label parsing
# ---------------------------------------------------------------------------

def test_the_truncation_case_that_broke_elsewhere():
    """`10-an_inline_face_with_a_white___s0` -> index 10, seed 0.

    The style slug is truncated to 28 characters and that cut lands on an
    underscore here, leaving three consecutive underscores before the seed.
    `stem.split("__")[0]` returns the wrong prefix; this must not.
    """
    assert parse_label("10-an_inline_face_with_a_white___s0") == (10, 0)


@pytest.mark.parametrize("stem,expected", [
    ("00-a_heavy_geometric_sans_serif__s0", (0, 0)),
    ("04-a_condensed_grotesque__s3", (4, 3)),
    ("10-an_inline_face_with_a_white___s0", (10, 0)),
    ("11-a_heavy_angular_blackletter-__s12", (11, 12)),
])
def test_parse_label_cases(stem, expected):
    assert parse_label(stem) == expected


@pytest.mark.parametrize("bad", ["no-seed-suffix", "missing_index__s0", "__s0"])
def test_parse_label_rejects_malformed_stems(bad):
    with pytest.raises(ValueError):
        parse_label(bad)


# ---------------------------------------------------------------------------
# discovery: refuse on anything other than exactly 48 well-formed PNGs
# ---------------------------------------------------------------------------

def _make_candidate_set(root, n_descriptions=N_DESCRIPTIONS, n_seeds=N_SEEDS,
                        size=64):
    root.mkdir(parents=True, exist_ok=True)
    for i in range(n_descriptions):
        slug = f"{i:02d}-style_slug"
        for s in range(n_seeds):
            Image.new("L", (size, size), 0).save(root / f"{slug}__s{s}.png")


def test_discover_candidates_happy_path(tmp_path):
    _make_candidate_set(tmp_path / "refs")
    by_index = discover_candidates(tmp_path / "refs")
    assert set(by_index) == set(range(N_DESCRIPTIONS))
    for seeds in by_index.values():
        assert set(seeds) == set(range(N_SEEDS))


def test_discover_candidates_refuses_wrong_count(tmp_path):
    _make_candidate_set(tmp_path / "refs", n_descriptions=11)
    with pytest.raises(ValueError, match="expected exactly 48"):
        discover_candidates(tmp_path / "refs")


def test_discover_candidates_refuses_missing_seed(tmp_path):
    refs = tmp_path / "refs"
    _make_candidate_set(refs, n_descriptions=N_DESCRIPTIONS, n_seeds=N_SEEDS)
    # Remove one seed and add an extra one for a different description instead,
    # keeping the total at 48 but breaking the per-description seed set.
    (refs / "00-style_slug__s0.png").unlink()
    Image.new("L", (64, 64), 0).save(refs / "01-style_slug__s4.png")
    with pytest.raises(ValueError, match="seeds"):
        discover_candidates(refs)


# ---------------------------------------------------------------------------
# CSV template
# ---------------------------------------------------------------------------

def test_csv_template_has_48_rows_with_empty_usable(tmp_path):
    _make_candidate_set(tmp_path / "refs")
    by_index = discover_candidates(tmp_path / "refs")
    rows = build_csv_rows(by_index, STYLES)
    assert len(rows) == N_DESCRIPTIONS * N_SEEDS
    for row in rows:
        assert row["usable"] == ""
        assert set(row) == set(CSV_FIELDS)


def test_csv_template_is_sorted_by_description_then_seed(tmp_path):
    _make_candidate_set(tmp_path / "refs")
    by_index = discover_candidates(tmp_path / "refs")
    rows = build_csv_rows(by_index, STYLES)
    keys = [(r["description_index"], r["seed"]) for r in rows]
    assert keys == sorted(keys)


def test_write_csv_template_round_trips(tmp_path):
    _make_candidate_set(tmp_path / "refs")
    by_index = discover_candidates(tmp_path / "refs")
    rows = build_csv_rows(by_index, STYLES)
    out = tmp_path / "calibration_labels.csv"
    write_csv_template(rows, out)

    assert out.read_bytes().count(b"\r\n") == 0, "must be LF line endings"

    with open(out, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == CSV_FIELDS
        read_rows = list(reader)
    assert len(read_rows) == N_DESCRIPTIONS * N_SEEDS
    assert all(r["usable"] == "" for r in read_rows)
    assert not csv_has_labels(out)


def test_write_csv_template_refuses_to_clobber_filled_labels(tmp_path):
    _make_candidate_set(tmp_path / "refs")
    by_index = discover_candidates(tmp_path / "refs")
    rows = build_csv_rows(by_index, STYLES)
    out = tmp_path / "calibration_labels.csv"
    write_csv_template(rows, out)

    # The owner fills in one label.
    with open(out, encoding="utf-8", newline="") as fh:
        filled_rows = list(csv.DictReader(fh))
    filled_rows[0]["usable"] = "yes"
    with open(out, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(filled_rows)

    assert csv_has_labels(out)
    before = out.read_text(encoding="utf-8")
    with pytest.raises(RuntimeError, match="refusing to overwrite"):
        write_csv_template(rows, out)
    assert out.read_text(encoding="utf-8") == before, "must not touch the file"


def test_csv_has_labels_false_for_missing_or_empty_file(tmp_path):
    missing = tmp_path / "missing.csv"
    assert not csv_has_labels(missing)

    _make_candidate_set(tmp_path / "refs")
    by_index = discover_candidates(tmp_path / "refs")
    rows = build_csv_rows(by_index, STYLES)
    out = tmp_path / "empty_usable.csv"
    write_csv_template(rows, out)
    assert not csv_has_labels(out)


# ---------------------------------------------------------------------------
# sheet rendering: small synthetic PNGs, just check it produces valid images
# ---------------------------------------------------------------------------

def test_render_page_produces_a_readable_image(tmp_path):
    refs = tmp_path / "refs"
    _make_candidate_set(refs, n_descriptions=1, n_seeds=N_SEEDS, size=64)
    by_index = discover_candidates_single(refs)
    out = tmp_path / "sheet_00.png"
    render_page(0, "a made-up test style for rendering", by_index[0], out,
                tile_w=64)
    assert out.is_file()
    with Image.open(out) as im:
        assert im.size[0] > 4 * 64
        assert im.size[1] > 64


def discover_candidates_single(refs_dir):
    """A single-description candidate set doesn't pass the full 48-file
    `discover_candidates` guard, so build the {index: {seed: path}} mapping
    directly for the rendering-only test."""
    by_index = {}
    for path in sorted(refs_dir.glob("*.png")):
        index, seed = parse_label(path.stem)
        by_index.setdefault(index, {})[seed] = str(path)
    return by_index


def test_render_overview_produces_a_readable_image(tmp_path):
    refs = tmp_path / "refs"
    _make_candidate_set(refs, size=48)
    by_index = discover_candidates(refs)
    out = tmp_path / "sheet_all.png"
    render_overview(by_index, STYLES, out, tile_w=48)
    assert out.is_file()
    with Image.open(out) as im:
        assert im.size[0] > 4 * 48
        assert im.size[1] > N_DESCRIPTIONS * 48
