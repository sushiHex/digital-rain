from dataclasses import dataclass
from typing import Callable
import numpy as np
from atlas_constants import CHARSET, DRAWN_INDICES

STYLE_Z_THRESH = 3.0
DEFAULT_QUALITY_N = 4

class Provenance:
    ORIGINAL = "original"
    ENSEMBLE = "ensemble"
    INPAINTED = "inpainted"
    UNRESOLVED = "unresolved"

@dataclass
class CellVerdict:
    index: int
    expected: str
    ocr_text: str
    ocr_pass: bool
    style_z: float
    flagged: bool

OcrFn = Callable[[np.ndarray], str]
EmbedFn = Callable[[list], np.ndarray]
GenerateFn = Callable[[int], np.ndarray]

def expected_chars(drawn_indices=DRAWN_INDICES) -> dict:
    return {i: CHARSET[i] for i in drawn_indices}
