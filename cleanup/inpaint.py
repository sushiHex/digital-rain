from typing import Protocol, Optional
import numpy as np
from cleanup.glyph_guide import render_neutral_glyph

class CellRepairer(Protocol):
    def repair(self, cell: np.ndarray, expected_char: str,
               context_atlas: Optional[np.ndarray]) -> np.ndarray:
        """Return a repaired cell (same HxWx3 shape) for `expected_char`."""
        ...

class NeutralPasteRepairer:
    """Fallback/baseline repairer: replace the bad cell with the correct
    letterform in a neutral font. Loses target style but guarantees the right
    glyph; also the deterministic default for tests and for vectorization
    when the diffusion repairer is unavailable."""
    def repair(self, cell, expected_char, context_atlas=None):
        return render_neutral_glyph(expected_char, size=(cell.shape[1], cell.shape[0]))
