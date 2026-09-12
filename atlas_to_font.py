"""Convert a Ref2Font atlas image to OTF font using Potrace CLI vectorization.

Uses the real potrace binary for proper cubic Bezier curve output.

Usage:
  python atlas_to_font.py --input test_atlas.png --output output/myfont.otf
  python atlas_to_font.py --input test_atlas.png --output output/myfont.otf --preprocess
"""
import argparse
import json
import math
import os
import re
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from svgpathtools import parse_path, CubicBezier, Line

from atlas_constants import (
    BLANK_INDICES, CELL_H, CELL_W, CHARSET as ATLAS_CHARSET,
    GRID_COLS, GRID_ROWS,
)

POTRACE = str(Path(__file__).parent / "tools" /
               ("potrace.exe" if os.name == "nt" else "potrace"))
# The 71-character set the superseded Ref2Font V3 path emitted. The trained
# glyph-conditioned model emits atlas_constants.CHARSET (95 chars) on a fixed
# 12x8 grid instead -- see trace_atlas_cells().
CHARSET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!?.,;:-"&'


def setup_potrace():
    """Ensure potrace binary is available."""
    potrace_path = Path(POTRACE)
    if potrace_path.exists():
        return str(potrace_path)

    # Check system path
    import shutil
    system_potrace = shutil.which("potrace")
    if system_potrace:
        return system_potrace

    # Unpacked-but-not-installed download, e.g. the Windows zip extracted to a
    # temp dir. POTRACE_HOME points at the directory holding the binary; without
    # it we look in the OS temp dir, which is where the zip usually lands.
    exe = Path(POTRACE).name
    roots = []
    if os.environ.get("POTRACE_HOME"):
        roots.append(Path(os.environ["POTRACE_HOME"]))
    roots.append(Path(tempfile.gettempdir()) / "potrace")
    for root in roots:
        for tmp in sorted(root.rglob(exe)) if root.is_dir() else []:
            # Cache it in the project tools dir so later runs skip the search.
            potrace_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(tmp, potrace_path)
            print(f"Copied potrace from {tmp} to {potrace_path}")
            return str(potrace_path)

    raise FileNotFoundError(
        f"potrace not found. Install it and put it on PATH, place it at {POTRACE}, "
        "or set POTRACE_HOME to the directory containing it. "
        "Download: https://potrace.sourceforge.net/"
    )


def compute_grid(count, width, height):
    """Find optimal grid layout (cols, rows, cell_size, offset_x, offset_y)."""
    best = None
    best_grid = (1, count, min(width, height) // count if count else 1, 0, 0)
    for cols in range(1, count + 1):
        rows = math.ceil(count / cols)
        cell = min(width // cols, height // rows)
        if cell <= 0:
            continue
        used_w = cell * cols
        used_h = cell * rows
        unused = (width - used_w) + (height - used_h)
        aspect_diff = abs((cols / rows) - (width / height))
        candidate = (cell, -unused, -aspect_diff)
        if best is None or candidate > best:
            best = candidate
            offset_x = (width - used_w) // 2
            offset_y = (height - used_h) // 2
            best_grid = (cols, rows, cell, offset_x, offset_y)
    return best_grid


def trace_atlas_cells(atlas, potrace_bin=None, upscale=4):
    """Trace every drawn cell of a *trained-model* atlas into subpaths.

    The trained model emits the fixed grid in atlas_constants: 95 characters
    laid out 12x8 in CELL_W x CELL_H cells. Do NOT use compute_grid() on these
    -- it infers a near-square layout from the character count, which is the
    Ref2Font V3 geometry and slices the wrong pixels here.

    Cells listed in BLANK_INDICES (the space, and the one padding cell that
    pads 95 characters up to 96 grid slots) are skipped and returned as empty
    subpath lists, so the result stays index-aligned with CHARSET and can be
    passed straight to build_font(..., CHARSET, CELL_W, CELL_H).
    """
    # Local import: eval_checkpoint owns crop_cell and pulls in the heavy eval
    # stack, which the atlas_to_font CLI has no reason to load.
    from eval_checkpoint import crop_cell

    if potrace_bin is None:
        potrace_bin = setup_potrace()
    invert = detect_invert(atlas)
    atlas_np = np.asarray(atlas.convert("RGB"))

    cells_data = []
    for idx in range(len(ATLAS_CHARSET)):
        if idx in BLANK_INDICES:
            cells_data.append([])
            continue
        cell = Image.fromarray(crop_cell(atlas_np, idx))
        processed, factor = preprocess_cell(cell, upscale=upscale)
        cells_data.append(
            trace_cell_potrace(potrace_bin, processed, invert=invert, upscale=factor)
        )
    return cells_data


def detect_invert(img):
    """Detect if atlas has white-on-black (needs inversion for potrace)."""
    arr = np.array(img.convert("L"), dtype=np.float32)
    border = 4
    edges = np.concatenate([
        arr[:border].ravel(), arr[-border:].ravel(),
        arr[:, :border].ravel(), arr[:, -border:].ravel()
    ])
    return edges.mean() < 128


def preprocess_cell(cell_img, upscale=4):
    """Upscale + binarize + morphological cleanup for cleaner tracing."""
    gray = cell_img.convert("L")

    if upscale > 1:
        w, h = gray.size
        gray = gray.resize((w * upscale, h * upscale), Image.LANCZOS)

    arr = np.array(gray)
    threshold = int(np.mean(arr))
    binary = (arr > threshold).astype(np.uint8) * 255

    from scipy.ndimage import binary_closing, binary_opening
    struct = np.ones((3, 3))
    mask = binary > 128
    mask = binary_closing(mask, structure=struct, iterations=1)
    mask = binary_opening(mask, structure=struct, iterations=1)

    return Image.fromarray((mask.astype(np.uint8) * 255), mode="L"), upscale


def trace_cell_potrace(potrace_bin, cell_img, invert=False, upscale=1):
    """Trace a glyph cell with potrace CLI, returning subpaths.

    Uses svgpathtools for reliable SVG path parsing.
    Returns list of subpaths. Each subpath is a list of (cmd, points) tuples.
    Coordinates are in cell-local pixels (y-down, origin top-left).
    """
    arr = np.array(cell_img.convert("L"))

    # Potrace traces BLACK pixels in a BMP
    if invert:
        binary = np.where(arr > 128, 0, 255).astype(np.uint8)
    else:
        binary = np.where(arr < 128, 0, 255).astype(np.uint8)

    bmp_img = Image.fromarray(binary, mode="L").convert("1")

    with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as tmp_bmp:
        bmp_path = tmp_bmp.name
        bmp_img.save(bmp_path)

    svg_path = bmp_path.replace(".bmp", ".svg")
    try:
        subprocess.run(
            [potrace_bin, bmp_path, "-s", "-o", svg_path,
             "--alphamax", "1.34", "--opttolerance", "0.2", "--turdsize", "5"],
            check=True, capture_output=True
        )
        with open(svg_path, "r") as f:
            svg_content = f.read()
    finally:
        Path(bmp_path).unlink(missing_ok=True)
        Path(svg_path).unlink(missing_ok=True)

    # Parse SVG transform: translate(0, H) scale(0.1, -0.1)
    scale_match = re.search(r'scale\(([-\d.]+),([-\d.]+)\)', svg_content)
    sx = float(scale_match.group(1)) if scale_match else 1.0
    sy = float(scale_match.group(2)) if scale_match else 1.0

    trans_match = re.search(r'translate\(([-\d.]+),([-\d.]+)\)', svg_content)
    tx = float(trans_match.group(1)) if trans_match else 0.0
    ty = float(trans_match.group(2)) if trans_match else 0.0

    def xform(pt_complex):
        """Apply potrace SVG transform to a complex point, normalize by upscale."""
        raw_x, raw_y = pt_complex.real, pt_complex.imag
        px = (raw_x * sx + tx) / upscale
        py = (raw_y * sy + ty) / upscale
        return (px, py)

    # Extract all path d-attributes and parse with svgpathtools
    path_ds = re.findall(r'd="([^"]+)"', svg_content)

    all_subpaths = []
    for d in path_ds:
        svg_path_obj = parse_path(d)

        # Convert to our subpath format, splitting at discontinuities
        current_subpath = []
        prev_end = None

        for seg in svg_path_obj:
            start = xform(seg.start)

            # New subpath if start doesn't match previous end
            if prev_end is None or abs(start[0] - prev_end[0]) > 0.1 or abs(start[1] - prev_end[1]) > 0.1:
                if current_subpath:
                    current_subpath.append(('Z', []))
                    all_subpaths.append(current_subpath)
                current_subpath = [('M', [start])]

            if isinstance(seg, CubicBezier):
                c1 = xform(seg.control1)
                c2 = xform(seg.control2)
                end = xform(seg.end)
                current_subpath.append(('C', [c1, c2, end]))
            elif isinstance(seg, Line):
                end = xform(seg.end)
                current_subpath.append(('L', [end]))
            else:
                # QuadraticBezier or Arc — convert to line
                end = xform(seg.end)
                current_subpath.append(('L', [end]))

            prev_end = xform(seg.end)

        if current_subpath:
            current_subpath.append(('Z', []))
            all_subpaths.append(current_subpath)

    return all_subpaths


def subpaths_bounds(subpaths):
    """Get bounding box of all subpaths."""
    all_x, all_y = [], []
    for subpath in subpaths:
        for cmd, pts in subpath:
            for x, y in pts:
                all_x.append(x)
                all_y.append(y)
    if not all_x:
        return None
    return (min(all_x), min(all_y), max(all_x), max(all_y))


def auto_baseline(cells_data, cell_h, charset):
    """Detect baseline from uppercase letter bottoms."""
    return _uppercase_metrics(cells_data, cell_h, charset)[0]


def _uppercase_metrics(cells_data, cell_h, charset):
    """(baseline_px, cap_height_px) from the uppercase cells.

    cap_height is what fixes the size bug: `scale = upm / cell_h` assumed the em
    equals the 160px cell, but `build_dataset` binary-searches a per-font pixel
    size (measured 55-93px, width-bound on 48 of 50 fonts). Cap height therefore
    landed at a median 0.422 em against a source median of 0.703 -- text set
    ~41% too small at any point size, deterministically, with model error zero.
    """
    tops, bottoms = [], []
    for i, subpaths in enumerate(cells_data):
        if i >= len(charset):
            break
        if not charset[i].isupper() or not subpaths:
            continue
        bounds = subpaths_bounds(subpaths)
        if bounds:
            tops.append(bounds[1])       # min_y = top of glyph
            bottoms.append(bounds[3])    # max_y = bottom (the baseline)
    if not bottoms:
        return cell_h * 0.75, None
    baseline = float(np.percentile(bottoms, 90))
    cap = baseline - float(np.percentile(tops, 10))
    return baseline, (cap if cap > 1.0 else None)


def _draw_glyph(subpaths, baseline_px, min_x, scale, side_bearing, width):
    """Draw a glyph using T2CharStringPen, return a T2CharString."""
    pen = T2CharStringPen(width, None)

    for subpath in subpaths:
        for cmd, pts in subpath:
            if cmd == 'M':
                x, y = pts[0]
                fx = (x - min_x) * scale + side_bearing
                fy = (baseline_px - y) * scale
                pen.moveTo((fx, fy))
            elif cmd == 'L':
                x, y = pts[0]
                pen.lineTo(((x - min_x) * scale + side_bearing,
                            (baseline_px - y) * scale))
            elif cmd == 'C':
                c1, c2, end = pts
                pen.curveTo(
                    ((c1[0] - min_x) * scale + side_bearing, (baseline_px - c1[1]) * scale),
                    ((c2[0] - min_x) * scale + side_bearing, (baseline_px - c2[1]) * scale),
                    ((end[0] - min_x) * scale + side_bearing, (baseline_px - end[1]) * scale),
                )
            elif cmd == 'Q':
                c1, end = pts
                pen.qCurveTo(
                    ((c1[0] - min_x) * scale + side_bearing, (baseline_px - c1[1]) * scale),
                    ((end[0] - min_x) * scale + side_bearing, (baseline_px - end[1]) * scale),
                )
            elif cmd == 'Z':
                pen.closePath()

    return pen.getCharString()


# Adobe Glyph List names for every non-alphabetic character in
# atlas_constants.CHARSET. An OpenType glyph name must match
# [A-Za-z_][A-Za-z0-9._]* -- so digits and every punctuation mark need a name,
# not the literal character. Letters pass through as themselves.
_GLYPH_NAMES = {
    ' ': 'space',
    '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
    '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine',
    '!': 'exclam', '"': 'quotedbl', '#': 'numbersign', '$': 'dollar',
    '%': 'percent', '&': 'ampersand', "'": 'quotesingle', '(': 'parenleft',
    ')': 'parenright', '*': 'asterisk', '+': 'plus', ',': 'comma',
    '-': 'hyphen', '.': 'period', '/': 'slash', ':': 'colon',
    ';': 'semicolon', '<': 'less', '=': 'equal', '>': 'greater',
    '?': 'question', '@': 'at', '[': 'bracketleft', '\\': 'backslash',
    ']': 'bracketright', '^': 'asciicircum', '_': 'underscore',
    '`': 'grave', '{': 'braceleft', '|': 'bar', '}': 'braceright',
    '~': 'asciitilde',
}


def _char_to_glyph_name(ch):
    return _GLYPH_NAMES.get(ch, ch)


# A generated font is a derivative of an OFL training corpus (SIL OFL FAQ
# 1.25), so it must itself carry OFL terms. These defaults put that in the
# font's own name table rather than relying on a README the downloaded file
# never travels with. Callers that have taken separate legal advice can
# override them; passing None for all three restores the old bare output.
DEFAULT_LICENSE_DESCRIPTION = (
    "This font is a derivative work of fonts licensed under the SIL Open Font "
    "License, Version 1.1, and is itself licensed under the SIL Open Font "
    "License, Version 1.1. This licence is available with an FAQ at "
    "https://openfontlicense.org/"
)
DEFAULT_LICENSE_URL = "https://openfontlicense.org/"
DEFAULT_COPYRIGHT = (
    "Generated by a glyph-conditioned diffusion model trained on a "
    "predominantly SIL Open Font License corpus."
)


# Typographic conventions the atlas cannot supply. The atlas is rendered to FIT
# a cell, so it carries no information about the source font's cap-to-em ratio,
# ascender budget, or sidebearings -- those must come from convention.
# VERIFIED 2026-08-20, do not "fix" this from the holdout. Chosen originally as
# "typical for a text face", it turns out to be exactly the corpus median:
# `analysis/fit_cap_height.py` over 975 licence-clean fonts gives median 0.7000,
# mean 0.6988, SD 0.0909.
#
# The holdout says 0.7105 (median) / 0.7358 (mean), which is a REAL property of
# that 50-font benchmark -- its caps are taller than the corpus at 2.52 SE,
# p=0.015 -- and not evidence about the constant. Refitting to it is leakage and
# makes the constant worse.
#
# What this constant cannot do: the atlas is rendered fit-to-cell, so it carries
# no absolute em scale, and per-font cap height is unrecoverable from it. The
# per-font scaling error (0.70/cap) has SD 0.1060, three times its mean bias.
# That is an atlas-format limit, not a tuning problem -- see
# research/2026-08-20-the-atlas-format-is-the-common-cause.md.
TARGET_CAP_EM = 0.70
ASCENT_EM = 0.80          # ascent - descent == 1.0 em by construction
SIDE_BEARING_EM = 0.05

# The space is a BLANK cell -- nothing is ever traced for it -- so its advance
# is assigned, not measured, and no atlas-space metric can see it being wrong.
# It was `cell_w * scale * 0.5`, half a grid cell, which is not a typographic
# quantity: it produced 0.49-0.54 em against a 0.2635 em mean across the 50
# holdout source fonts, so every generated font set text at roughly DOUBLE word
# spacing. Fitted on those 50 fonts (research/2026-08-18-...), space is best
# predicted by the font's own lowercase widths:
#
#   basis                 k       relative MAE
#   0.50 x mean lowercase 0.5022  0.167   <- chosen
#   advance of 'n'        0.4439  0.172
#   fixed em fraction     0.2635  0.190
#
# Font-adaptive beats a constant, and it degrades gracefully: a font whose
# lowercase is wide gets a wider space, which is what type designers do.
SPACE_TO_LOWERCASE = 0.50
SPACE_FALLBACK_EM = 0.26      # no readable lowercase: the fitted mean

# Per-character sidebearings, median over 600 real fonts
# (analysis/fit_sidebearing_prior.py). One constant for every glyph is wrong in
# a way that shows up immediately in running text: measured, `H` wants LSB
# 0.054 em and `A` wants 0.007 em, an 8x difference, because a vertical stem
# needs air beside it and a diagonal does not. Letterfitting is 74% of the
# finished font's error (research/2026-08-18-scoring-the-finished-font.md), and
# `A`, `T` and `V` were among its worst glyphs.
#
# This is a per-CHARACTER effect only. Cross-font SD is 0.022-0.060 em,
# comparable to the medians, so much of the remaining variance is per-font
# fitting tightness, which a traced atlas carries no signal for.
SIDEBEARING_PRIOR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "research", "sidebearing_prior.json")
_SIDEBEARING_PRIOR = None


def load_sidebearing_prior(path=None):
    """char -> (lsb_em, rsb_em). Cached; {} when the prior is unavailable."""
    global _SIDEBEARING_PRIOR
    if _SIDEBEARING_PRIOR is not None and path is None:
        return _SIDEBEARING_PRIOR
    target = path or SIDEBEARING_PRIOR_PATH
    prior = {}
    try:
        with open(target, encoding="utf-8") as fh:
            for ch, rec in json.load(fh).get("chars", {}).items():
                prior[ch] = (float(rec["lsb"]), float(rec["rsb"]))
    except (OSError, ValueError, KeyError):
        prior = {}          # fall back to the constant; never fail the build
    if path is None:
        _SIDEBEARING_PRIOR = prior
    return prior


def _space_advance(cells_data, charset, scale, side_bearing, upm):
    """Advance for the space, derived from the font's own lowercase widths."""
    widths = []
    for i, subpaths in enumerate(cells_data):
        if i >= len(charset) or not subpaths:
            continue
        ch = charset[i]
        if not (ch.isalpha() and ch.islower()):
            continue
        bounds = subpaths_bounds(subpaths)
        if not bounds:
            continue
        widths.append(max((bounds[2] - bounds[0]) * scale + 2 * side_bearing,
                          upm * 0.15))
    if not widths:
        return int(SPACE_FALLBACK_EM * upm)
    return int(SPACE_TO_LOWERCASE * float(np.mean(widths)))


def build_font(cells_data, charset, cell_w, cell_h, upm=1000, side_bearing=None,
               font_name="Ref2Font", style_name="Regular",
               license_description=DEFAULT_LICENSE_DESCRIPTION,
               license_url=DEFAULT_LICENSE_URL,
               copyright_notice=DEFAULT_COPYRIGHT,
               use_sidebearing_prior=False):
    """Build an OTF font from traced glyph cells using CFF outlines.

    Sidebearings default to one constant for every glyph.
    `use_sidebearing_prior=True` switches to the fitted per-character values in
    `research/sidebearing_prior.json`.

    THE PRIOR IS OFF BY DEFAULT, AND THAT IS A MEASURED RESULT, NOT AN
    OVERSIGHT. Per-character fitting is real and large -- over 600 fonts `H`
    wants LSB 0.054 em and `A` 0.007 em -- and against REAL ink widths it cuts
    advance error 14.6%. In this pipeline it delivers nothing:

      arm/metric              constant    prior
      gt_traced advance MAE     0.1168   0.1165
      gt_traced text width     -0.0030  -0.0622

    The tracer under-measures ink by a median 3.5% on letters (and OVER-measures
    small punctuation: `.` by 28%, `'` by 38%, a resolution effect). The flat
    0.05 em sidebearing was silently absorbing that bias. Replace it with
    correctly tighter values and the compensation disappears, so text comes out
    narrower and nothing is gained.

    Both terms are wrong and were cancelling. Fixing one alone is a regression;
    they have to be fitted jointly against traced ink, which needs an
    atlas-to-source-font mapping `dataset_v2` does not record.
    See research/2026-08-19-the-sidebearing-prior-that-did-not-pay.md.

    The licence arguments populate OpenType name IDs 13, 14 and 0. They are
    NOT cosmetic: the demo hands users a bare .otf/.woff2, and without these
    the file carries no licence at all -- see
    research/2026-08-08-the-corpus-is-not-97-percent-ofl.md.
    """

    baseline_px, cap_px = _uppercase_metrics(cells_data, cell_h, charset)

    # SCALE FROM CAP HEIGHT, not from the cell. `upm / cell_h` assumed the em
    # equals the 160px cell; it does not, because build_dataset renders each
    # font at a binary-searched size that FITS the cell (width-bound on 48 of
    # 50 holdout fonts). Measured on ground-truth atlases, where model error is
    # exactly zero, that produced a median cap height of 0.422 em against a
    # source median of 0.703 -- every generated font set ~41% too small.
    #
    # The atlas cannot reveal the font's true cap-to-em ratio, so normalise to
    # a conventional TARGET_CAP_EM. That is the right trade: the true ratio is
    # unknowable here, and 0.70 is close to typical for text faces.
    if cap_px:
        scale = TARGET_CAP_EM * upm / cap_px
        # Clamp against pathological traces (e.g. a font whose only uppercase
        # cells failed to vectorise) so a bad measurement cannot produce a
        # font 5x too large.
        scale = float(np.clip(scale, 0.5 * upm / cell_h, 4.0 * upm / cell_h))
    else:
        scale = upm / cell_h            # no readable caps: previous behaviour
    side_bearing = side_bearing if side_bearing is not None else SIDE_BEARING_EM * upm

    prior = load_sidebearing_prior() if use_sidebearing_prior else {}

    blank_advance = _space_advance(cells_data, charset, scale, side_bearing, upm)

    glyph_names = [".notdef", "space"]
    char_map = {32: "space"}
    glyph_advances = {".notdef": 500, "space": blank_advance}
    charstrings_dict = {}

    # .notdef
    pen = T2CharStringPen(500, None)
    pen.moveTo((50, 0)); pen.lineTo((50, 700)); pen.lineTo((450, 700)); pen.lineTo((450, 0)); pen.closePath()
    pen.moveTo((100, 50)); pen.lineTo((400, 50)); pen.lineTo((400, 650)); pen.lineTo((100, 650)); pen.closePath()
    charstrings_dict[".notdef"] = pen.getCharString()

    # space
    pen = T2CharStringPen(glyph_advances["space"], None)
    charstrings_dict["space"] = pen.getCharString()

    for i, subpaths in enumerate(cells_data):
        if i >= len(charset):
            break
        ch = charset[i]
        glyph_name = _char_to_glyph_name(ch)
        if glyph_name in charstrings_dict:
            # Already emitted -- the charset contains ' ', and "space" is
            # pre-defined above. A duplicate name in glyph_names makes
            # FontBuilder raise, so skip rather than redefine.
            continue
        glyph_names.append(glyph_name)
        char_map[ord(ch)] = glyph_name

        if not subpaths:
            # An empty cell is either a declared blank or a glyph the tracer
            # found nothing in; both are better served by the space width than
            # by half a grid cell.
            advance = blank_advance
            glyph_advances[glyph_name] = advance
            pen = T2CharStringPen(advance, None)
            charstrings_dict[glyph_name] = pen.getCharString()
            continue

        bounds = subpaths_bounds(subpaths)
        min_x = bounds[0] if bounds else 0
        max_x = bounds[2] if bounds else cell_w
        content_w = max_x - min_x

        # Per-character fitting when the prior has this glyph, the flat constant
        # otherwise. The LEFT value also positions the outline, so an asymmetric
        # pair (`V` is 0.018 / 0.002) shifts the glyph as well as sizing it.
        left, right = prior.get(ch, (None, None))
        if left is None:
            left = right = side_bearing
        else:
            left, right = left * upm, right * upm

        advance = int(content_w * scale + left + right)
        advance = max(advance, int(upm * 0.15))
        glyph_advances[glyph_name] = advance

        charstrings_dict[glyph_name] = _draw_glyph(
            subpaths, baseline_px, min_x, scale, left, advance
        )

    fb = FontBuilder(upm, isTTF=False)
    fb.setupGlyphOrder(glyph_names)
    fb.setupCharacterMap(char_map)
    fb.setupCFF(
        psName=font_name.replace(" ", ""),
        fontInfo={"FullName": font_name},
        charStringsDict=charstrings_dict,
        privateDict={"defaultWidthX": 500, "nominalWidthX": 0},
    )

    metrics = {name: (glyph_advances[name], 0) for name in glyph_names}
    fb.setupHorizontalMetrics(metrics)

    # VERTICAL METRICS ARE DECOUPLED FROM `scale`, deliberately. They used to be
    # baseline_px*scale / (baseline_px-cell_h)*scale, so raising the scale to fix
    # the cap height would have dragged the line height up with it -- a ~1.7x em
    # and absurdly loose leading. Set them from a fixed em budget instead, so
    # ascent - descent == upm exactly whatever the scale turns out to be.
    ascent = int(round(ASCENT_EM * upm))
    descent = int(round((ASCENT_EM - 1.0) * upm))     # negative, by convention
    fb.setupHorizontalHeader(ascent=ascent, descent=descent)
    # Licence metadata travels INSIDE the font, because a downloaded .otf
    # arrives with no README beside it. This repo's own position is that a
    # font generated by a model trained on an OFL corpus is an OFL derivative
    # (SIL OFL FAQ 1.25), so shipping a bare font file with an empty name
    # table contradicts the licensing section of its own documentation.
    # nameIDs 0 / 13 / 14 are the OpenType fields for exactly this.
    name_records = {"familyName": font_name, "styleName": style_name}
    if copyright_notice:
        name_records["copyright"] = copyright_notice
    if license_description:
        name_records["licenseDescription"] = license_description
    if license_url:
        name_records["licenseInfoURL"] = license_url
    fb.setupNameTable(name_records)
    fb.setupOS2(
        sTypoAscender=ascent, sTypoDescender=descent, sTypoLineGap=0,
        usWinAscent=ascent, usWinDescent=abs(descent),
    )
    fb.setupPost()
    return fb.font


def main():
    parser = argparse.ArgumentParser(description="Atlas to OTF font with Potrace vectorization")
    parser.add_argument("--input", required=True, help="Atlas image path")
    parser.add_argument("--output", default="output/ref2font.otf", help="Output font path")
    # Default depends on the grid: the trained model emits ATLAS_CHARSET (95)
    # and trace_atlas_cells returns cells index-aligned to it, while the legacy
    # V3 path emitted CHARSET (71). Mixing them silently mislabels punctuation
    # -- the two agree on A-Z/a-z/0-9 and then diverge.
    parser.add_argument("--charset", default=None,
                        help="Defaults to the 95-char atlas charset, or the "
                             "71-char V3 charset with --legacy-square-grid.")
    parser.add_argument("--upm", type=int, default=1000)
    parser.add_argument("--side-bearing", type=int, default=50,
                        help="sidebearing in font units, applied to every glyph")
    parser.add_argument("--sidebearing-prior", action="store_true",
                        help="use the fitted per-character sidebearings in "
                             "research/sidebearing_prior.json instead. OFF by "
                             "default: it measures no better in this pipeline, "
                             "because the tracer's ink bias was being absorbed "
                             "by the flat value. See the build_font docstring.")
    parser.add_argument("--font-name", default="Ref2Font")
    parser.add_argument("--preprocess", action="store_true", help="Upscale + cleanup before tracing")
    parser.add_argument("--upscale", type=int, default=4)
    parser.add_argument("--legacy-square-grid", action="store_true",
                        help="Infer a near-square grid with compute_grid(). This is "
                             "the superseded Ref2Font V3 geometry and SLICES BETWEEN "
                             "CELLS on a trained-model atlas -- only for old V3 "
                             "renders. The default uses the fixed 12x8 grid.")
    args = parser.parse_args()
    if args.charset is None:
        args.charset = CHARSET if args.legacy_square_grid else ATLAS_CHARSET

    potrace_bin = setup_potrace()
    print(f"Using potrace: {potrace_bin}")

    img = Image.open(args.input)
    w, h = img.size
    print(f"Atlas: {w}x{h}")

    invert = detect_invert(img)
    print(f"Background: {'black (white-on-black)' if invert else 'white (black-on-white)'}")

    n_chars = len(args.charset)

    if args.legacy_square_grid:
        # Superseded Ref2Font V3 geometry. Kept only for old V3 renders; it
        # infers a near-square layout from the character count and slices
        # BETWEEN cells on a trained-model atlas.
        cols, rows, cell_size, off_x, off_y = compute_grid(n_chars, w, h)
        print(f"Grid (LEGACY square): {cols}x{rows}, cell: {cell_size}px")
        cell_w = cell_h = cell_size
        cells_data = []
        for idx in range(n_chars):
            r, c = divmod(idx, cols)
            x0, y0 = off_x + c * cell_size, off_y + r * cell_size
            cell = img.crop((x0, y0, x0 + cell_size, y0 + cell_size))
            upscale_factor = 1
            if args.preprocess:
                cell, upscale_factor = preprocess_cell(cell, upscale=args.upscale)
            cells_data.append(
                trace_cell_potrace(potrace_bin, cell, invert=invert,
                                   upscale=upscale_factor))
    else:
        # The trained model's fixed 12x8 / CELL_W x CELL_H grid -- the same path
        # app.py and the eval harness use. This CLI used to call compute_grid()
        # unconditionally, which CLAUDE.md explicitly forbids for these atlases:
        # it produced a technically-valid OTF built from mis-sliced pixels.
        print(f"Grid: {GRID_COLS}x{GRID_ROWS}, cell: {CELL_W}x{CELL_H}px "
              "(trained-model geometry)")
        cell_w, cell_h = CELL_W, CELL_H
        cells_data = trace_atlas_cells(img, potrace_bin=potrace_bin,
                                       upscale=args.upscale)

    for idx, subpaths in enumerate(cells_data):
        ch = args.charset[idx] if idx < len(args.charset) else '?'
        if idx < 10 or ch in 'AaMm':
            n_cubics = sum(sum(1 for cmd, _ in sp if cmd == 'C') for sp in subpaths)
            print(f"  {ch}: {len(subpaths)} subpaths, {n_cubics} cubic Beziers")

    print("Building OTF font...")
    font = build_font(
        cells_data, args.charset, cell_w, cell_h,
        upm=args.upm, side_bearing=args.side_bearing, font_name=args.font_name,
        use_sidebearing_prior=args.sidebearing_prior,
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    font.save(str(out_path))
    print(f"Saved: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")

    font.flavor = "woff2"
    woff2_path = out_path.with_suffix(".woff2")
    font.save(str(woff2_path))
    print(f"Saved: {woff2_path} ({woff2_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
