"""Build the sheet and CSV a human uses to label 48 candidate references usable or not.

WHY THIS EXISTS. The two instruments that touch the product track --
`analysis/reference_gate.py` (coherence) and the adherence measure in
`analysis/synthesize_rare_attributes.py` -- both have thresholds cut from the
instruments' OWN score spread, never from a human judging the actual images.
CLAUDE.md is explicit about this: the gate's 1.875 cutoff is "provisional and
its recall is a floor", and adherence is "eyeballed" with no calibrated
threshold. Neither can be fixed by more math on the existing scores; both need
a judgment that only a person can make -- "would I hand this to a user as a
starting point for the style they asked for?" -- against a fixed, labelled set
of images. This script builds the thing the owner labels: one page per
description showing its four seeds side by side, an overview page for a fast
first pass, and a CSV template with the 48 rows to fill in. It does not label
anything itself and does not compute or touch either instrument's threshold --
that is downstream work, once `research/calibration_labels.csv` has answers in
it.

INPUT. `eval_runs/_candidate_refs/klein-base-n4/`: 12 descriptions (styles, in
`research/candidate_references.json`) times 4 seeds = 48 PNGs, named like
`10-an_inline_face_with_a_white___s0.png`. The `NN-` prefix is the description
index; the seed suffix is `__sK`. Do NOT split on `__`: the style slug is
truncated to 28 characters and that cut can land on an underscore, so index 10
carries three underscores before `s0` and a naive split returns the wrong
prefix (`tests/test_candidate_labels.py`). `parse_label` below strips the seed
with a regex anchored at the end and reads the index from the first two
characters instead.

  python analysis/calibration_sheet.py
  python analysis/calibration_sheet.py --dir path/to/pngs --out-dir path/to/out
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import csv
import glob
import json
import os
import re

from PIL import Image, ImageDraw, ImageFont

try:
    from viz._common import label_font as _viz_label_font
except ImportError:
    _viz_label_font = None

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATES_DIR = os.path.join(REPO, "eval_runs", "_candidate_refs", "klein-base-n4")
STYLES_JSON = os.path.join(REPO, "research", "candidate_references.json")
OUT_DIR = os.path.join(REPO, "eval_runs", "_calibration")
CSV_PATH = os.path.join(REPO, "research", "calibration_labels.csv")

N_DESCRIPTIONS = 12
N_SEEDS = 4
EXPECTED_TOTAL = N_DESCRIPTIONS * N_SEEDS

TILE_W = 340                    # legible tile width, per spec
SEED_RE = re.compile(r"__s(\d+)$")

CSV_FIELDS = ["id", "set", "description_index", "seed", "description", "usable", "note"]
DEFAULT_SET = "klein-base-n4"   # the set the registration named; rows without a
                                # `set` cell (the original template) belong to it

# Quiet, restrained palette -- no colour except the greyscale glyphs themselves,
# and nothing that ranks or highlights a candidate over another.
BG = (250, 249, 246)
INK_TEXT = (38, 38, 36)
MUTED_TEXT = (122, 121, 117)
HAIRLINE = (223, 222, 217)

MARGIN = 48
HEADER_GAP = 34
TILE_GAP = 44
CAPTION_GAP = 14


def parse_label(stem):
    """(description_index, seed) from a candidate PNG stem.

    NOT `stem.split("__")`. See the module docstring: the style slug is
    truncated to 28 characters and that truncation can land on an underscore,
    so some stems carry three consecutive underscores before the seed. Strip
    the seed suffix with a regex anchored at the string's end, and read the
    index from the leading two characters, which are always the zero-padded
    `NN-` prefix `build_prompts` writes.
    """
    m = SEED_RE.search(stem)
    if not m:
        raise ValueError(f"{stem!r} has no trailing __sN seed suffix")
    seed = int(m.group(1))
    if len(stem) < 3 or not stem[:2].isdigit() or stem[2] != "-":
        raise ValueError(f"{stem!r} has no leading NN- description index")
    return int(stem[:2]), seed


def discover_candidates(candidates_dir):
    """Group candidate PNGs into {description_index: {seed: path}}.

    Refuses (raises ValueError) unless there are exactly 48 PNGs, every label
    parses under `parse_label`, and each of the 12 indices has exactly the 4
    seeds 0-3 -- a partial or malformed run should stop this script, not
    silently produce a sheet missing a seed.
    """
    paths = sorted(glob.glob(os.path.join(candidates_dir, "*.png")))
    if len(paths) != EXPECTED_TOTAL:
        raise ValueError(
            f"expected exactly {EXPECTED_TOTAL} PNGs in {candidates_dir!r}, "
            f"found {len(paths)}")

    by_index = {}
    for path in paths:
        stem = os.path.splitext(os.path.basename(path))[0]
        index, seed = parse_label(stem)
        by_index.setdefault(index, {})[seed] = path

    expected_indices = set(range(N_DESCRIPTIONS))
    if set(by_index) != expected_indices:
        raise ValueError(
            f"description indices found {sorted(by_index)} != expected "
            f"{sorted(expected_indices)}")
    for index, seeds in by_index.items():
        if set(seeds) != set(range(N_SEEDS)):
            raise ValueError(
                f"description {index:02d} has seeds {sorted(seeds)}, expected "
                f"{list(range(N_SEEDS))}")
    return by_index


def load_styles(styles_json):
    """The 12 description strings, index i is `styles[i]`."""
    with open(styles_json, encoding="utf-8") as fh:
        data = json.load(fh)
    styles = data["styles"]
    if len(styles) != N_DESCRIPTIONS:
        raise ValueError(
            f"{styles_json!r} has {len(styles)} styles, expected "
            f"{N_DESCRIPTIONS}")
    return styles


def _font(size, bold=False):
    """A readable label font: `viz._common.label_font` if importable, else a
    system font, else PIL's built-in default."""
    if _viz_label_font is not None:
        try:
            return _viz_label_font(size, bold=bold)
        except Exception:
            pass
    for name in (["arialbd.ttf"] if bold else []) + ["arial.ttf", "DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _line_height(draw, font):
    top, bottom = draw.textbbox((0, 0), "Ag", font=font)[1::2]
    return bottom - top + 6


def _wrap_text(draw, text, font, max_width):
    """Greedy word wrap to `max_width`, measured with the real font metrics."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if not cur or draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def render_page(index, description, seed_paths, out_path, tile_w=TILE_W):
    """One page: a header naming the description, then its 4 seeds in a row.

    Deliberately bare: light background, hairline separators between tiles,
    a small quiet caption (`NN-sK`) under each -- nothing that ranks or
    highlights a candidate, since the owner's judgment is the whole point.
    """
    seeds = sorted(seed_paths)
    n = len(seeds)
    content_w = n * tile_w + (n - 1) * TILE_GAP
    page_w = content_w + 2 * MARGIN

    index_font = _font(30, bold=True)
    desc_font = _font(23)
    caption_font = _font(17)

    probe = ImageDraw.Draw(Image.new("RGB", (1, 1), BG))
    index_h = _line_height(probe, index_font)
    desc_h = _line_height(probe, desc_font)
    caption_h = _line_height(probe, caption_font)
    header_lines = _wrap_text(probe, description, desc_font, content_w)
    header_h = index_h + len(header_lines) * desc_h

    page_h = (MARGIN + header_h + HEADER_GAP + tile_w + CAPTION_GAP
              + caption_h + MARGIN)

    page = Image.new("RGB", (page_w, page_h), BG)
    draw = ImageDraw.Draw(page)

    y = MARGIN
    draw.text((MARGIN, y), f"Description {index:02d}", font=index_font,
               fill=INK_TEXT)
    y += index_h
    for line in header_lines:
        draw.text((MARGIN, y), line, font=desc_font, fill=INK_TEXT)
        y += desc_h

    y = MARGIN + header_h + HEADER_GAP
    for i, seed in enumerate(seeds):
        x = MARGIN + i * (tile_w + TILE_GAP)
        if i > 0:
            sep_x = x - TILE_GAP // 2
            draw.line([(sep_x, y), (sep_x, y + tile_w)], fill=HAIRLINE, width=1)
        with Image.open(seed_paths[seed]) as im:
            tile = im.convert("L").resize((tile_w, tile_w), Image.LANCZOS)
        page.paste(tile.convert("RGB"), (x, y))
        caption = f"{index:02d}-s{seed}"
        cw = draw.textlength(caption, font=caption_font)
        draw.text((x + (tile_w - cw) / 2, y + tile_w + CAPTION_GAP), caption,
                   font=caption_font, fill=MUTED_TEXT)

    page.save(out_path)


def render_overview(by_index, styles, out_path, tile_w=140):
    """All 12 descriptions on one tall page, smaller tiles, for a first pass."""
    label_w = 360
    row_pad = 30

    label_font_ = _font(19, bold=True)
    caption_font = _font(13)

    probe = ImageDraw.Draw(Image.new("RGB", (1, 1), BG))
    label_line_h = _line_height(probe, label_font_)
    caption_h = _line_height(probe, caption_font)

    content_w = label_w + N_SEEDS * tile_w + (N_SEEDS - 1) * TILE_GAP
    page_w = content_w + 2 * MARGIN
    row_h = tile_w + CAPTION_GAP + caption_h + row_pad
    page_h = 2 * MARGIN + N_DESCRIPTIONS * row_h

    page = Image.new("RGB", (page_w, page_h), BG)
    draw = ImageDraw.Draw(page)

    y = MARGIN
    for index in sorted(by_index):
        label_lines = _wrap_text(draw, f"{index:02d}  {styles[index]}",
                                 label_font_, label_w)[:3]
        block_h = len(label_lines) * label_line_h
        ly = y + (tile_w - block_h) / 2
        for line in label_lines:
            draw.text((MARGIN, ly), line, font=label_font_, fill=INK_TEXT)
            ly += label_line_h

        x = MARGIN + label_w
        for seed in sorted(by_index[index]):
            with Image.open(by_index[index][seed]) as im:
                tile = im.convert("L").resize((tile_w, tile_w), Image.LANCZOS)
            page.paste(tile.convert("RGB"), (x, y))
            caption = f"s{seed}"
            cw = draw.textlength(caption, font=caption_font)
            draw.text((x + (tile_w - cw) / 2, y + tile_w + CAPTION_GAP),
                       caption, font=caption_font, fill=MUTED_TEXT)
            x += tile_w + TILE_GAP

        sep_y = y + row_h - row_pad / 2
        draw.line([(MARGIN, sep_y), (page_w - MARGIN, sep_y)], fill=HAIRLINE,
                  width=1)
        y += row_h

    page.save(out_path)


def build_csv_rows(by_index, styles, set_name=DEFAULT_SET):
    rows = []
    for index in sorted(by_index):
        for seed in sorted(by_index[index]):
            rows.append({"id": f"{index:02d}-s{seed}", "set": set_name,
                        "description_index": index, "seed": seed,
                        "description": styles[index], "usable": "", "note": ""})
    return rows


def append_csv_rows(rows, csv_path):
    """Add a second set's rows to a CSV that already carries labels.

    Round 2 of the calibration (2026-09-13, issue #29): the first set came
    back all usable, so more sets are labelled into the SAME file and scored
    as one sample. Existing rows keep every cell as written; a row that
    predates the `set` column is assigned DEFAULT_SET; a row already present
    for (set, id) is left alone. Returns the number of rows added.
    """
    existing = []
    if os.path.isfile(csv_path):
        with open(csv_path, encoding="utf-8", newline="") as fh:
            for rec in csv.DictReader(fh):
                rec = {k: rec.get(k, "") for k in CSV_FIELDS}
                rec["set"] = rec["set"] or DEFAULT_SET
                existing.append(rec)
    have = {(r["set"], r["id"]) for r in existing}
    added = [r for r in rows if (r["set"], r["id"]) not in have]
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing + added)
    return len(added)


def csv_has_labels(csv_path):
    """True if `csv_path` exists and any row's `usable` cell is non-empty."""
    if not os.path.isfile(csv_path):
        return False
    with open(csv_path, encoding="utf-8", newline="") as fh:
        return any((row.get("usable") or "").strip()
                   for row in csv.DictReader(fh))


def write_csv_template(rows, csv_path):
    """Write the labelling template -- but never over a filled-in one.

    This is the owner's thirty minutes of work; clobbering it would destroy
    labels that cannot be regenerated.
    """
    if csv_has_labels(csv_path):
        raise RuntimeError(
            f"refusing to overwrite {csv_path!r}: it already has at least one "
            "non-empty 'usable' label. Move it aside first if you really mean "
            "to regenerate the template.")
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--dir", default=CANDIDATES_DIR,
                    help="directory of the 48 candidate reference PNGs")
    ap.add_argument("--styles", default=STYLES_JSON,
                    help="research/candidate_references.json")
    ap.add_argument("--out-dir", default=OUT_DIR,
                    help="where the per-description and overview PNGs go")
    ap.add_argument("--csv", default=CSV_PATH,
                    help="where the labelling CSV template goes")
    ap.add_argument("--tile-width", type=int, default=TILE_W)
    ap.add_argument("--skip-csv", action="store_true",
                    help="render sheets only; do not touch the CSV template")
    ap.add_argument("--set", default=DEFAULT_SET,
                    help="name recorded in the CSV's `set` column for these rows")
    ap.add_argument("--append", action="store_true",
                    help="add this set's rows to a CSV that already carries labels, "
                         "keeping every existing row (round 2 and later)")
    args = ap.parse_args(argv)
    if args.set != DEFAULT_SET and args.out_dir == OUT_DIR:
        args.out_dir = os.path.join(OUT_DIR, args.set)

    try:
        by_index = discover_candidates(args.dir)
        styles = load_styles(args.styles)
    except (ValueError, OSError) as exc:
        print(f"calibration_sheet: {exc}", file=_sys.stderr)
        return 1

    os.makedirs(args.out_dir, exist_ok=True)
    for index in sorted(by_index):
        out_path = os.path.join(args.out_dir, f"sheet_{index:02d}.png")
        render_page(index, styles[index], by_index[index], out_path,
                    tile_w=args.tile_width)
        print(f"  wrote {out_path}")

    overview_path = os.path.join(args.out_dir, "sheet_all.png")
    render_overview(by_index, styles, overview_path)
    print(f"  wrote {overview_path}")

    if not args.skip_csv:
        rows = build_csv_rows(by_index, styles, args.set)
        if args.append:
            added = append_csv_rows(rows, args.csv)
            print(f"  appended {added} row(s) for set {args.set!r} to {args.csv}")
        else:
            try:
                write_csv_template(rows, args.csv)
            except RuntimeError as exc:
                print(f"calibration_sheet: {exc}", file=_sys.stderr)
                return 1
            print(f"  wrote {args.csv} ({len(rows)} rows)")

    return 0


if __name__ == "__main__":
    _sys.exit(main())
