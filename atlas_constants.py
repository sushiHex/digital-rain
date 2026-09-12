# atlas_constants.py
"""Shared atlas geometry constants.

Single source of truth for grid layout used by build_dataset.py,
font_quality.py, and eval_checkpoint.py.
"""
from PIL import ImageFont


def load_truetype_pinned(font_path, size):
    """Load a TrueType font and pin its variation axes to the 'Regular'
    instance (or each axis's default) when supported.

    Variable fonts can otherwise behave differently across PIL/FreeType
    versions because the "default instance" picker depends on table order.
    Pinning makes rasters reproducible. Non-variable fonts are unaffected.
    """
    font = ImageFont.truetype(str(font_path), size)
    if hasattr(font, "set_variation_by_name"):
        try:
            font.set_variation_by_name("Regular")
            return font
        except Exception:
            pass
    if hasattr(font, "set_variation_by_axes"):
        try:
            axes = font.get_variation_axes()
            font.set_variation_by_axes([ax["default"] for ax in axes])
        except Exception:
            pass
    return font


CHARSET = (
    'ABCDEFGHIJKL'
    'MNOPQRSTUVWX'
    'YZabcdefghij'
    'klmnopqrstuv'
    'wxyz01234567'
    '89!?.,;:\'"- '
    '@#$%&()/+=[]'
    '{}*_<>|\\~^`'
)

GRID_COLS = 12
GRID_ROWS = 8
CANVAS = 1280

CELL_W = CANVAS // GRID_COLS
CELL_H = CANVAS // GRID_ROWS
BLANK_INDICES = {i for i, ch in enumerate(CHARSET) if ch == ' '} | {len(CHARSET)}
DRAWN_INDICES = [i for i in range(GRID_COLS * GRID_ROWS) if i not in BLANK_INDICES]


# The EXACT prompt train_lora_kg.py trained the glyph-conditioned model with
# (208 chars, no Layout block). make_prompt() below produces a DIFFERENT,
# structured 534-char prompt that train_lora.py used for the baseline model.
# Evaluating the glyph model with make_prompt() therefore feeds it text
# conditioning it never saw. Kept here as the single source of truth; a test
# asserts it still matches the literal in train_lora_kg.py.
# See research/2026-07-28-reference-char-mismatch.md.
TRAINED_SHORT_PROMPT = (
    'A technical font atlas grid of 95 printable ASCII characters in a 12x8 grid. '
    'White glyphs on black background. Rectangular cells, taller than wide. '
    'The style is strictly derived from the reference image "Kg".'
)


def make_prompt(reference_chars="Kg"):
    """Build the structured training/inference prompt.

    Includes row-by-row character layout so the model knows WHERE
    each character goes, not just that 95 characters exist in a grid.
    """
    rows = []
    for r in range(GRID_ROWS):
        start = r * GRID_COLS
        chars = []
        for c in range(GRID_COLS):
            idx = start + c
            if idx < len(CHARSET):
                ch = CHARSET[idx]
                if ch == ' ':
                    chars.append('[space]')
                elif ch == '"':
                    chars.append('[quote]')
                elif ch == "'":
                    chars.append('[apos]')
                elif ch == '\\':
                    chars.append('[backslash]')
                else:
                    chars.append(ch)
            else:
                chars.append('[blank]')
        rows.append(f'Row {r+1}: {" ".join(chars)}')

    row_text = '\n'.join(rows)
    return (
        f'A technical font atlas grid of 95 printable ASCII characters in a {GRID_COLS}x{GRID_ROWS} grid. '
        f'White glyphs on black background. Rectangular cells, taller than wide. '
        f'Characters share a baseline per row. '
        f'The style is strictly derived from the reference image "{reference_chars}". '
        f'Layout:\n{row_text}'
    )
