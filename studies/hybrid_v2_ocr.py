"""Drop-in replacement candidates for cleanup/models.py:build_trocr_ocr_fn.

De-risk spike: does a symbol-capable OCR beat TrOCR at reading single-glyph
cells from generated font atlases? See docs/superpowers or
.superpowers/sdd/task-6-report.md for the full writeup.

Each build_*_ocr_fn(device) returns a callable ocr_fn(cell: np.ndarray) -> str
matching cleanup/models.py:build_trocr_ocr_fn's exact signature/contract:
  - cell is a single-glyph atlas cell, grayscale or RGB numpy array,
    white glyph on black background (uint8, HxW or HxWxC).
  - returns the decoded character string (stripped).
"""
import numpy as np
from PIL import Image


def _prep_cell_for_ocr(cell: np.ndarray, upscale: int = 4) -> Image.Image:
    """Shared preprocessing: invert to dark-on-light, upscale, square-pad white.

    Mirrors eval_checkpoint._ocr_decode_cell's TrOCR preprocessing so the
    comparison isolates the OCR model itself, not the image prep.
    """
    if cell.ndim == 3:
        gray = np.array(Image.fromarray(cell).convert("L"))
    else:
        gray = cell
    inv = 255 - gray
    img = Image.fromarray(inv).convert("RGB")
    w, h = img.size
    img = img.resize((w * upscale, h * upscale), Image.LANCZOS)
    side = max(img.size)
    pad = Image.new("RGB", (side, side), (255, 255, 255))
    pad.paste(img, ((side - img.size[0]) // 2, (side - img.size[1]) // 2))
    return pad


GOT_OCR_MODEL_ID = "stepfun-ai/GOT-OCR-2.0-hf"


def build_got_ocr_fn(device="cuda"):
    """GOT-OCR2 (stepfun-ai/GOT-OCR-2.0-hf), Apache-2.0, via transformers."""
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor

    processor = AutoProcessor.from_pretrained(GOT_OCR_MODEL_ID)
    model = AutoModelForImageTextToText.from_pretrained(
        GOT_OCR_MODEL_ID, dtype=torch.float16
    ).to(device).eval()

    def ocr_fn(cell: np.ndarray) -> str:
        pad = _prep_cell_for_ocr(cell)
        inputs = processor(pad, return_tensors="pt").to(device)
        with torch.no_grad():
            generate_ids = model.generate(
                **inputs,
                do_sample=False,
                tokenizer=processor.tokenizer,
                stop_strings="<|im_end|>",
                max_new_tokens=8,
            )
        text = processor.decode(
            generate_ids[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True
        )
        return text.strip()

    return ocr_fn
