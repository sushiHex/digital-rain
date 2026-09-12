"""Font quality scoring library.

Pure functions for evaluating font suitability and rendered atlas quality.
No CLI, no disk I/O beyond what callers pass in. Every check returns a
CheckResult; the composite gate returns a QualityResult.

Thresholds are module-level constants — tune by editing them here or
passing overrides via the `thresholds` dict to score_font().
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from atlas_constants import CHARSET, GRID_COLS, GRID_ROWS, CANVAS, CELL_W, CELL_H, BLANK_INDICES, DRAWN_INDICES

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CheckResult:
    passed: bool
    name: str
    detail: dict


@dataclass
class QualityResult:
    passed: bool
    font_name: str
    checks: list[CheckResult] = field(default_factory=list)
    failed: list[CheckResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Thresholds — starting values, tuned against dataset_Kg
# ---------------------------------------------------------------------------

# Font-level
SMALL_CAPS_SIM_THRESHOLD = 0.80
SMALL_CAPS_HEIGHT_RATIO_THRESHOLD = 0.65
SMALL_CAPS_MIN_FLAGGED_PAIRS = 3
RENDER_VISIBILITY_MIN_WHITE = 0.04

# Atlas-level
CELL_OCC_MIN_WHITE = 0.001          # per-cell absolute minimum (catches truly empty cells)
CELL_OCC_NEAR_EMPTY_THRESH = 0.005  # "near-empty" threshold (period=0.006 should pass)
CELL_OCC_MAX_NEAR_EMPTY = 12        # thin fonts legitimately have 8-10 small punctuation cells
BASELINE_MAX_STDEV_FRAC = 0.20      # fraction of cell_h (mono fonts + punctuation rows push stdev ~25-28px)
DUP_CELL_SIM_THRESHOLD = 0.995      # o/0=0.99, l/!=0.97 are legit similarities, not dupes
DUP_CELL_MAX_PAIRS = 3              # some fonts have 1-2 truly identical pairs (rare)
STROKE_WEIGHT_MIN = 0.015
STROKE_WEIGHT_MAX = 0.35

# Blocklist patterns (compiled regexes, case-insensitive)
BLOCKLIST_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"Flow", r"Content", r"LibreBarcode", r"Linefont", r"Wavefont",
        r"Chenla", r"BetaniaPatmos", r"jsMath", r"Lohit", r"Allkin",
        r"Yarndings", r"Souliyo", r"Redacted", r"Noto", r"Hind",
        r"webdings", r"wingding", r"Segoelcons",
        r"Noto.?Emoji", r"MaterialSymbols", r"MaterialIcons",
        r"Playwrite.*Guides", r"FascinateInline",
        r"SC[\-\[]",  # small-caps variants: SC- or SC[
    ]
]

# Letter pairs for small-caps detection
SMALL_CAPS_PAIRS = [("A", "a"), ("B", "b"), ("G", "g"),
                    ("R", "r"), ("E", "e"), ("N", "n")]


# ---------------------------------------------------------------------------
# Font-level checks
# ---------------------------------------------------------------------------

def _render_char(font_path, char, size=120, canvas=100):
    """Render a single character as a (canvas, canvas) uint8 numpy array."""
    font = ImageFont.truetype(str(font_path), size)
    img = Image.new("L", (canvas, canvas), 0)
    ImageDraw.Draw(img).text((10, 10), char, fill=255, font=font)
    return np.array(img, dtype=np.float32)


def check_blocklist(font_path) -> CheckResult:
    """Reject fonts matching known-bad name patterns."""
    stem = Path(font_path).stem
    for pat in BLOCKLIST_PATTERNS:
        if pat.search(stem):
            return CheckResult(
                passed=False, name="blocklist",
                detail={"stem": stem, "matched_pattern": pat.pattern},
            )
    return CheckResult(passed=True, name="blocklist", detail={"stem": stem})


def check_small_caps(font_path) -> CheckResult:
    """Reject small-caps fonts via multi-pair shape + height-ratio test."""
    font_path = Path(font_path)
    flagged = 0
    pair_details = []

    try:
        font = ImageFont.truetype(str(font_path), 120)
    except Exception as e:
        return CheckResult(passed=False, name="small_caps",
                           detail={"error": str(e)})

    for upper, lower in SMALL_CAPS_PAIRS:
        try:
            arr_U = _render_char(font_path, upper)
            arr_l = _render_char(font_path, lower)
        except Exception:
            pair_details.append({"pair": f"{upper}/{lower}", "sim": 0.0,
                                 "height_ratio": 0.0, "flagged": False})
            continue

        # Cosine similarity
        n_U, n_l = np.linalg.norm(arr_U), np.linalg.norm(arr_l)
        if n_U == 0 or n_l == 0:
            pair_details.append({"pair": f"{upper}/{lower}", "sim": 0.0,
                                 "height_ratio": 0.0, "flagged": False})
            continue
        sim = float(np.dot(arr_U.flatten(), arr_l.flatten()) / (n_U * n_l))

        # Height ratio via bounding box
        bbox_U = font.getbbox(upper)
        bbox_l = font.getbbox(lower)
        h_U = bbox_U[3] - bbox_U[1] if bbox_U else 1
        h_l = bbox_l[3] - bbox_l[1] if bbox_l else 0
        height_ratio = h_l / h_U if h_U > 0 else 0.0

        is_flagged = (sim > SMALL_CAPS_SIM_THRESHOLD
                      and height_ratio > SMALL_CAPS_HEIGHT_RATIO_THRESHOLD)
        if is_flagged:
            flagged += 1

        pair_details.append({
            "pair": f"{upper}/{lower}", "sim": round(sim, 4),
            "height_ratio": round(height_ratio, 4), "flagged": is_flagged,
        })

    passed = flagged < SMALL_CAPS_MIN_FLAGGED_PAIRS
    return CheckResult(
        passed=passed, name="small_caps",
        detail={"flagged_pairs": flagged, "pairs": pair_details},
    )


def check_cmap_coverage(font_path) -> CheckResult:
    """Verify all 94 non-space CHARSET codepoints have real glyph mappings."""
    from fontTools.ttLib import TTFont
    tt = None
    try:
        tt = TTFont(str(font_path), fontNumber=0)
        cmap = tt.getBestCmap()
        if cmap is None:
            return CheckResult(passed=False, name="cmap_coverage",
                               detail={"error": "no cmap table"})
        missing = []
        for ch in CHARSET:
            if ch == ' ':
                continue
            glyph_name = cmap.get(ord(ch))
            if glyph_name is None or glyph_name == ".notdef":
                missing.append(ch)
        return CheckResult(
            passed=len(missing) == 0, name="cmap_coverage",
            detail={"missing_count": len(missing), "missing_chars": missing},
        )
    except Exception as e:
        return CheckResult(passed=False, name="cmap_coverage",
                           detail={"error": str(e)})
    finally:
        if tt is not None:
            tt.close()


def check_render_visibility(font_path) -> CheckResult:
    """Reject fonts whose reference chars render too faintly."""
    try:
        font = ImageFont.truetype(str(font_path), 120)
        img = Image.new("L", (500, 200), 0)
        ImageDraw.Draw(img).text((20, 20), "Rg", fill=255, font=font)
        arr = np.array(img)
        white_ratio = float(arr.sum() / (255.0 * arr.size))
        passed = white_ratio >= RENDER_VISIBILITY_MIN_WHITE
        return CheckResult(
            passed=passed, name="render_visibility",
            detail={"white_ratio": round(white_ratio, 6)},
        )
    except Exception as e:
        return CheckResult(passed=False, name="render_visibility",
                           detail={"error": str(e)})


# ---------------------------------------------------------------------------
# Atlas-level checks
# ---------------------------------------------------------------------------

def _crop_cell(atlas_np, idx):
    """Crop cell at flat index from a (CANVAS, CANVAS) atlas. Returns (cell_h, cell_w) array."""
    row = idx // GRID_COLS
    col = idx % GRID_COLS
    y0 = row * CELL_H
    x0 = col * CELL_W
    return atlas_np[y0:y0 + CELL_H, x0:x0 + CELL_W]


def check_cell_occupancy(atlas_np) -> CheckResult:
    """Reject atlases with missing or near-empty glyphs."""
    cell_area = CELL_W * CELL_H
    empty_cells = []
    near_empty_cells = []

    for idx in DRAWN_INDICES:
        cell = _crop_cell(atlas_np, idx)
        white_frac = float(cell.sum()) / (255.0 * cell_area)
        if white_frac < CELL_OCC_MIN_WHITE:
            empty_cells.append({"idx": idx, "white_frac": round(white_frac, 6)})
        elif white_frac < CELL_OCC_NEAR_EMPTY_THRESH:
            near_empty_cells.append({"idx": idx, "white_frac": round(white_frac, 6)})

    passed = (len(empty_cells) == 0
              and len(near_empty_cells) <= CELL_OCC_MAX_NEAR_EMPTY)
    return CheckResult(
        passed=passed, name="cell_occupancy",
        detail={"empty": empty_cells, "near_empty": near_empty_cells},
    )


def check_baseline_consistency(atlas_np) -> CheckResult:
    """Reject atlases with jagged baselines (inconsistent vertical placement per row)."""
    bad_rows = []

    for row_idx in range(GRID_ROWS):
        centers = []
        for col_idx in range(GRID_COLS):
            flat_idx = row_idx * GRID_COLS + col_idx
            if flat_idx in BLANK_INDICES:
                continue
            cell = _crop_cell(atlas_np, flat_idx)
            col_sum = cell.astype(np.float64)
            total = col_sum.sum()
            if total == 0:
                continue
            # Vertical center of mass (row indices weighted by brightness)
            rows = np.arange(cell.shape[0], dtype=np.float64)
            v_com = float(np.dot(rows, col_sum.sum(axis=1)) / total)
            centers.append(v_com)

        if len(centers) >= 2:
            stdev = float(np.std(centers))
            if stdev > BASELINE_MAX_STDEV_FRAC * CELL_H:
                bad_rows.append({
                    "row": row_idx, "stdev": round(stdev, 2),
                    "threshold": round(BASELINE_MAX_STDEV_FRAC * CELL_H, 2),
                })

    passed = len(bad_rows) == 0
    return CheckResult(
        passed=passed, name="baseline_consistency",
        detail={"bad_rows": bad_rows},
    )


def check_duplicate_cells(atlas_np) -> CheckResult:
    """Reject atlases where distinct characters render identically."""
    # Downsample each cell to 16x16 for fast comparison
    thumbs = []
    for idx in DRAWN_INDICES:
        cell = _crop_cell(atlas_np, idx)
        thumb = np.array(Image.fromarray(cell).resize((16, 16)), dtype=np.float32).flatten()
        norm = np.linalg.norm(thumb)
        thumbs.append(thumb / norm if norm > 0 else thumb)

    dup_pairs = []
    n = len(thumbs)
    for i in range(n):
        for j in range(i + 1, n):
            sim = float(np.dot(thumbs[i], thumbs[j]))
            if sim > DUP_CELL_SIM_THRESHOLD:
                dup_pairs.append({
                    "idx_a": DRAWN_INDICES[i], "idx_b": DRAWN_INDICES[j],
                    "char_a": CHARSET[DRAWN_INDICES[i]] if DRAWN_INDICES[i] < len(CHARSET) else "?",
                    "char_b": CHARSET[DRAWN_INDICES[j]] if DRAWN_INDICES[j] < len(CHARSET) else "?",
                    "sim": round(sim, 4),
                })

    passed = len(dup_pairs) <= DUP_CELL_MAX_PAIRS
    return CheckResult(
        passed=passed, name="duplicate_cells",
        detail={"duplicate_pairs": dup_pairs},
    )


def check_stroke_weight(atlas_np) -> CheckResult:
    """Reject atlases with glyphs too thin (hairline) or too thick (blobby)."""
    total_white = 0.0
    total_area = 0.0

    for idx in DRAWN_INDICES:
        cell = _crop_cell(atlas_np, idx)
        total_white += cell.sum() / 255.0
        total_area += cell.size

    mean_weight = total_white / total_area if total_area > 0 else 0.0
    passed = bool(STROKE_WEIGHT_MIN <= mean_weight <= STROKE_WEIGHT_MAX)
    return CheckResult(
        passed=passed, name="stroke_weight",
        detail={"mean_weight": round(float(mean_weight), 6)},
    )


# ---------------------------------------------------------------------------
# Composite gate
# ---------------------------------------------------------------------------

FONT_CHECKS = [check_blocklist, check_small_caps, check_cmap_coverage,
               check_render_visibility]
ATLAS_CHECKS = [check_cell_occupancy,
                check_baseline_consistency, check_duplicate_cells,
                check_stroke_weight]


def score_font(font_path, atlas_np=None, early_exit=True):
    """Run all applicable quality checks on a font.

    Args:
        font_path: Path to TTF/OTF file.
        atlas_np: Optional (H, W) uint8 atlas render. If None, skips atlas checks.
        early_exit: If True and any font-level check fails, skip atlas checks.
                    Set False for audit mode where you want all diagnostics.

    Returns:
        QualityResult with pass/fail verdict and per-check details.
    """
    font_path = Path(font_path)
    checks = []
    failed = []

    # Font-level checks
    font_failed = False
    for check_fn in FONT_CHECKS:
        result = check_fn(font_path)
        checks.append(result)
        if not result.passed:
            failed.append(result)
            font_failed = True

    # Atlas-level checks (skip if early_exit and font already failed, or no atlas)
    if atlas_np is not None and (not font_failed or not early_exit):
        if atlas_np.dtype != np.uint8:
            raise ValueError(f"atlas_np must be uint8, got {atlas_np.dtype}")
        if atlas_np.shape[:2] != (CANVAS, CANVAS):
            raise ValueError(f"atlas_np shape {atlas_np.shape[:2]} != ({CANVAS}, {CANVAS})")
        for check_fn in ATLAS_CHECKS:
            result = check_fn(atlas_np)
            checks.append(result)
            if not result.passed:
                failed.append(result)

    passed = len(failed) == 0
    return QualityResult(
        passed=passed,
        font_name=font_path.stem,
        checks=checks,
        failed=failed,
    )
