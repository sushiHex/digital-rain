import numpy as np
import torch
from PIL import Image
from eval_checkpoint import TROCR_MODEL_ID, DINOV2_MODEL_ID, _ocr_decode_cell

def build_trocr_ocr_fn(device="cuda"):
    from eval_checkpoint import load_trocr
    processor, model = load_trocr(device)
    def ocr_fn(cell: np.ndarray) -> str:
        gray = np.array(Image.fromarray(cell).convert("L"))
        return _ocr_decode_cell(gray, processor, model, device)
    return ocr_fn

def build_dino_embed_fn(device="cuda", batch=64):
    from transformers import AutoImageProcessor, AutoModel
    processor = AutoImageProcessor.from_pretrained(DINOV2_MODEL_ID)
    model = AutoModel.from_pretrained(DINOV2_MODEL_ID).to(device).eval()
    def embed_fn(cells):
        feats = []
        with torch.no_grad():
            for i in range(0, len(cells), batch):
                imgs = [Image.fromarray(c) for c in cells[i:i + batch]]
                inp = processor(images=imgs, return_tensors="pt").to(device)
                out = model(**inp).last_hidden_state[:, 0]
                feats.append(out.cpu().numpy())
        return np.concatenate(feats, axis=0)
    return embed_fn
