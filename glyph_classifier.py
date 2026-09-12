"""Font-invariant single-glyph character classifier.

Reads which of the 94 non-space CHARSET characters an isolated glyph cell
shows. Built to REPLACE TrOCR as the trustworthy identity reader for isolated
atlas cells: TrOCR is a line-OCR model and routinely misreads single glyphs
out of context (J->1, K->6, cursive letterforms -> digits). This model is
trained directly on isolated CELL_W x CELL_H glyph crops -- the exact object
it will be asked to read at inference time -- with augmentation that bridges
clean font renders to the model's own imperfect generated glyphs.

Pipeline
--------
1. BUILD: render every (font, char) pair from a train/val font split drawn
   from the google-fonts corpus (holdout fonts excluded) into a fresh
   CELL_W x CELL_H cell using the EXACT fit/centering logic from
   render_glyph_template.py (lines 138-152), resize to 64x64 grayscale, and
   cache to an .npz so re-runs skip rendering.
2. TRAIN: a small CNN (3 conv blocks -> global-avg-pool -> FC) trained with
   on-the-fly augmentation (affine jitter, blur, morphological erode/dilate,
   light noise) applied ONLY to the train split. Val split is never augmented
   and is drawn from a font set disjoint from train.
3. READ: load_classifier() + classify()/classify_conf() -- the interface
   identity scoring imports. Cells can be any size HxW or HxWxC uint8 (white
   glyph on black); they are grayscaled + resized to 64x64 internally, with
   NO augmentation, matching the val-time normalization used in training.

CLI
---
  python glyph_classifier.py --build            # render + cache dataset only
  python glyph_classifier.py --train            # train from cached dataset, save checkpoint
  python glyph_classifier.py                    # both (default)
  python glyph_classifier.py --smoke            # 3 train fonts + 2 val fonts + 1 epoch, tiny end-to-end check
  python glyph_classifier.py --n-train 450 --n-val 50 --epochs 12   # full run (see report for exact command)
"""
import argparse
import random
import re
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageDraw, ImageFilter
from torch.utils.data import DataLoader, Dataset

from atlas_constants import CHARSET, CELL_W, CELL_H, load_truetype_pinned

# ===========================================================================
# Constants / charset (94 non-space characters -- CHARSET has 95 entries
# including one literal space; classification targets are the drawn glyphs).
# ===========================================================================
CHARS = [c for c in CHARSET if c != " "]
assert len(CHARS) == 94, f"expected 94 non-space chars, got {len(CHARS)}"
CHAR_TO_IDX = {c: i for i, c in enumerate(CHARS)}
IDX_TO_CHAR = {i: c for i, c in enumerate(CHARS)}

IMG_SIZE = 64
SEED = 1234

FONTS_ROOT_DEFAULT = "google-fonts"
HOLDOUT_FONTS_DEFAULT = "eval_holdout/fonts"
DATA_CACHE_DEFAULT = "glyph_clf_data.npz"
MODEL_OUT_DEFAULT = "glyph_classifier.pt"
DATA_CACHE_SMOKE_DEFAULT = "glyph_clf_data_smoke.npz"
MODEL_OUT_SMOKE_DEFAULT = "glyph_classifier_smoke.pt"

N_TRAIN_FONTS_DEFAULT = 450
N_VAL_FONTS_DEFAULT = 50
EPOCHS_DEFAULT = 12
BATCH_SIZE_DEFAULT = 256


# ===========================================================================
# Font corpus discovery + holdout exclusion
# ===========================================================================

_STYLE_SUFFIX_RE = re.compile(r"\[[^\]]*\]")  # variable-font axis tag, e.g. "[wght]"


def _normalize_font_key(stem: str) -> str:
    """Collapse a font filename stem to a family key for leakage checks.

    Strips variable-font axis tags ("[wght]") and any trailing "-Style"
    suffix (Regular/Bold/Italic/...), then lowercases. Family names in this
    corpus don't contain dashes, so splitting on the first "-" isolates the
    family reliably and, if anything, over-excludes (safe direction, per
    spec: "when unsure, exclude").
    """
    s = _STYLE_SUFFIX_RE.sub("", stem)
    s = s.split("-")[0]
    return s.strip().lower()


def _holdout_exclude_keys(holdout_dir: str) -> set:
    keys = set()
    for p in Path(holdout_dir).glob("*.ttf"):
        keys.add(_normalize_font_key(p.stem))
    return keys


def discover_font_corpus(fonts_root: str, holdout_dir: str):
    """Return (train_eligible_sorted_paths, total_count, excluded_count)."""
    all_fonts = sorted(str(p) for p in Path(fonts_root).rglob("*.ttf"))
    exclude_keys = _holdout_exclude_keys(holdout_dir)
    eligible = [p for p in all_fonts if _normalize_font_key(Path(p).stem) not in exclude_keys]
    return eligible, len(all_fonts), len(all_fonts) - len(eligible)


def split_fonts(eligible_sorted, n_train: int, n_val: int, seed: int = SEED):
    """Deterministic, disjoint train/val font split via a seeded shuffle of
    the (already sorted, for reproducibility) eligible font list."""
    if len(eligible_sorted) < n_train + n_val:
        raise ValueError(
            f"only {len(eligible_sorted)} eligible fonts, need {n_train + n_val}"
        )
    shuffled = eligible_sorted[:]
    random.Random(seed).shuffle(shuffled)
    train_fonts = shuffled[:n_train]
    val_fonts = shuffled[n_train:n_train + n_val]
    return train_fonts, val_fonts


# ===========================================================================
# Glyph rendering (matches render_glyph_template.py lines 138-152 exactly)
# ===========================================================================

def _render_glyph_cell(font_path: str, char: str):
    """Render `char` into a fresh CELL_W x CELL_H black cell, white glyph,
    using the binary-search largest-fit-size + centering logic from
    render_glyph_template.py. Returns a PIL "L" image, or None if the font
    lacks the glyph (empty/zero-area bbox) or rendering raises."""
    cw, ch = CELL_W, CELL_H
    try:
        # Cheap presence check at the largest candidate size first.
        f0 = load_truetype_pinned(font_path, ch)
        b0 = f0.getbbox(char)
        if not b0 or b0[2] <= b0[0] or b0[3] <= b0[1]:
            return None

        lo, hi = 8, ch
        while lo < hi:                       # largest font size that fits the cell
            mid = (lo + hi + 1) // 2
            f = load_truetype_pinned(font_path, mid)
            b = f.getbbox(char)
            if b and (b[2] - b[0]) <= cw * 0.8 and (b[3] - b[1]) <= ch * 0.6:
                lo = mid
            else:
                hi = mid - 1
        f = load_truetype_pinned(font_path, lo)
        b = f.getbbox(char)
        if not b or b[2] <= b[0] or b[3] <= b[1]:
            return None
        gw, gh = b[2] - b[0], b[3] - b[1]
        x = (cw - gw) // 2 - b[0]
        y = (ch - gh) // 2 - b[1]

        img = Image.new("L", (cw, ch), 0)
        ImageDraw.Draw(img).text((x, y), char, fill=255, font=f)
        return img
    except Exception:
        return None


# ===========================================================================
# Dataset build + cache
# ===========================================================================

def _render_split(fonts, chars, label: str):
    images, labels = [], []
    rendered, skipped = 0, 0
    t0 = time.time()
    for fi, fp in enumerate(fonts):
        for ch in chars:
            cell = _render_glyph_cell(fp, ch)
            if cell is None:
                skipped += 1
                continue
            arr = np.asarray(cell.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR), dtype=np.uint8)
            images.append(arr)
            labels.append(CHAR_TO_IDX[ch])
            rendered += 1
        if (fi + 1) % 50 == 0 or (fi + 1) == len(fonts):
            print(f"  [{label}] {fi + 1}/{len(fonts)} fonts, {rendered} cells rendered, "
                  f"{skipped} skipped ({time.time() - t0:.0f}s)")
    images_arr = np.stack(images).astype(np.uint8) if images else np.zeros((0, IMG_SIZE, IMG_SIZE), np.uint8)
    labels_arr = np.asarray(labels, dtype=np.int16)
    return images_arr, labels_arr, rendered, skipped


def build_dataset(fonts_root, holdout_dir, n_train, n_val, out_path, seed: int = SEED):
    eligible, total, excluded = discover_font_corpus(fonts_root, holdout_dir)
    print(f"corpus: {total} fonts under {fonts_root}, {excluded} excluded (holdout collision), "
          f"{len(eligible)} eligible")
    train_fonts, val_fonts = split_fonts(eligible, n_train, n_val, seed=seed)
    print(f"split: {len(train_fonts)} train fonts, {len(val_fonts)} val fonts (disjoint, seed={seed})")

    train_images, train_labels, tr_rendered, tr_skipped = _render_split(train_fonts, CHARS, "train")
    val_images, val_labels, va_rendered, va_skipped = _render_split(val_fonts, CHARS, "val")

    print(f"train: {tr_rendered} cells ({tr_skipped} skipped) from {len(train_fonts)} fonts")
    print(f"val:   {va_rendered} cells ({va_skipped} skipped) from {len(val_fonts)} fonts")

    np.savez(
        out_path,
        train_images=train_images,
        train_labels=train_labels,
        val_images=val_images,
        val_labels=val_labels,
        train_fonts=np.array(train_fonts),
        val_fonts=np.array(val_fonts),
        chars=np.array(CHARS),
    )
    print(f"saved {out_path}")
    return out_path


def load_npz_dataset(path):
    with np.load(path, allow_pickle=False) as d:
        return {
            "train_images": d["train_images"],
            "train_labels": d["train_labels"],
            "val_images": d["val_images"],
            "val_labels": d["val_labels"],
            "train_fonts": d["train_fonts"],
            "val_fonts": d["val_fonts"],
            "chars": d["chars"],
        }


# ===========================================================================
# Augmentation (train split only) -- bridges clean renders to the model's
# own imperfect generated glyphs.
# ===========================================================================

def augment_cell(img_u8: np.ndarray) -> np.ndarray:
    """img_u8: HxW uint8 grayscale, white glyph on black. Returns HxW float32
    in [0, 1] with random affine jitter, blur, morphological erode/dilate,
    and light noise applied."""
    h, w = img_u8.shape
    img = Image.fromarray(img_u8, mode="L")

    # Affine: random scale (0.85-1.12) + translate (+-10%), resize-then-paste
    # onto a fresh black canvas (PIL clips paste offsets automatically).
    scale = random.uniform(0.85, 1.12)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    resized = img.resize((new_w, new_h), Image.BILINEAR)
    canvas = Image.new("L", (w, h), 0)
    tx = int(round(random.uniform(-0.10, 0.10) * w))
    ty = int(round(random.uniform(-0.10, 0.10) * h))
    px = (w - new_w) // 2 + tx
    py = (h - new_h) // 2 + ty
    canvas.paste(resized, (px, py))
    img = canvas

    # Random Gaussian blur, 0-1.2px.
    blur_r = random.uniform(0.0, 1.2)
    if blur_r > 0.05:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_r))

    # Random morphological erode/dilate, +-1px (simulates stroke thinning/thickening).
    op = random.choice(("none", "erode", "dilate"))
    if op == "dilate":
        img = img.filter(ImageFilter.MaxFilter(3))
    elif op == "erode":
        img = img.filter(ImageFilter.MinFilter(3))

    arr = np.asarray(img, dtype=np.float32) / 255.0

    # Light noise.
    noise_std = random.uniform(0.0, 0.03)
    if noise_std > 0:
        arr = arr + np.random.normal(0.0, noise_std, arr.shape).astype(np.float32)
        arr = np.clip(arr, 0.0, 1.0)

    return arr


class GlyphDataset(Dataset):
    def __init__(self, images: np.ndarray, labels: np.ndarray, augment: bool):
        self.images = images
        self.labels = labels
        self.augment = augment

    def __len__(self):
        return len(self.images)

    def __getitem__(self, i):
        img = self.images[i]
        if self.augment:
            arr = augment_cell(img)
        else:
            arr = img.astype(np.float32) / 255.0
        t = torch.from_numpy(arr).unsqueeze(0)  # (1, H, W)
        return t, int(self.labels[i])


# ===========================================================================
# Model
# ===========================================================================

class GlyphCNN(nn.Module):
    """4-block conv (32->64->128->256), adaptive pool to 2x2 (keeps spatial
    detail needed to tell O/Q/0, i/j, c/e apart), FC head with dropout.
    Input: (N, 1, 64, 64)."""

    def __init__(self, n_classes: int = 94):
        super().__init__()
        def block(ci, co):
            return [nn.Conv2d(ci, co, 3, padding=1), nn.BatchNorm2d(co), nn.ReLU(inplace=True),
                    nn.Conv2d(co, co, 3, padding=1), nn.BatchNorm2d(co), nn.ReLU(inplace=True), nn.MaxPool2d(2)]
        self.features = nn.Sequential(
            *block(1, 32), *block(32, 64), *block(64, 128), *block(128, 256),
        )
        self.pool = nn.AdaptiveAvgPool2d(2)          # 256 x 2 x 2 = 1024, spatial detail retained
        self.head = nn.Sequential(
            nn.Flatten(), nn.Linear(256 * 4, 256), nn.ReLU(inplace=True), nn.Dropout(0.3),
            nn.Linear(256, n_classes),
        )

    def forward(self, x):
        return self.head(self.pool(self.features(x)))


def _resolve_device(device: str) -> torch.device:
    if device == "cuda" and not torch.cuda.is_available():
        print("[glyph_classifier] CUDA not available, falling back to CPU")
        return torch.device("cpu")
    return torch.device(device)


# ===========================================================================
# Training
# ===========================================================================

def train_model(data: dict, epochs: int, batch_size: int, device: str, model_out: str):
    dev = _resolve_device(device)
    train_ds = GlyphDataset(data["train_images"], data["train_labels"], augment=True)
    val_ds = GlyphDataset(data["val_images"], data["val_labels"], augment=False)
    print(f"train samples: {len(train_ds)}, val samples: {len(val_ds)}, device: {dev}")

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    model = GlyphCNN(n_classes=len(CHARS)).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    crit = nn.CrossEntropyLoss(label_smoothing=0.05)

    import copy
    best_val_acc, best_state = 0.0, None
    final_val_acc = 0.0
    for epoch in range(epochs):
        model.train()
        total_loss, n = 0.0, 0
        for x, y in train_loader:
            x, y = x.to(dev), y.to(dev)
            opt.zero_grad()
            out = model(x)
            loss = crit(out, y)
            loss.backward()
            opt.step()
            total_loss += loss.item() * x.size(0)
            n += x.size(0)
        train_loss = total_loss / max(n, 1)

        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(dev), y.to(dev)
                pred = model(x).argmax(dim=1)
                correct += (pred == y).sum().item()
                total += y.size(0)
        val_acc = correct / max(total, 1)
        final_val_acc = val_acc
        sched.step()
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_state = copy.deepcopy(model.state_dict())
        print(f"epoch {epoch + 1}/{epochs}  train_loss={train_loss:.4f}  val_acc={val_acc:.4f}  lr={sched.get_last_lr()[0]:.2e}")

    # restore the BEST checkpoint (not the last epoch) for the per-char eval + save
    if best_state is not None:
        model.load_state_dict(best_state)
    final_val_acc = best_val_acc

    # Per-char val accuracy (worst-10).
    n_classes = len(CHARS)
    per_char_correct = np.zeros(n_classes, dtype=np.int64)
    per_char_total = np.zeros(n_classes, dtype=np.int64)
    model.eval()
    with torch.no_grad():
        for x, y in val_loader:
            x = x.to(dev)
            pred = model(x).argmax(dim=1).cpu().numpy()
            yn = y.numpy()
            for p, t in zip(pred, yn):
                per_char_total[t] += 1
                if p == t:
                    per_char_correct[t] += 1

    seen = per_char_total > 0
    per_char_acc = np.zeros(n_classes, dtype=np.float64)
    per_char_acc[seen] = per_char_correct[seen] / per_char_total[seen]
    seen_idx = np.where(seen)[0]
    worst_order = seen_idx[np.argsort(per_char_acc[seen_idx])]
    worst10 = [(IDX_TO_CHAR[int(i)], float(per_char_acc[i]), int(per_char_total[i])) for i in worst_order[:10]]

    print(f"final overall val_acc = {final_val_acc:.4f}")
    print("worst-10 per-char val accuracy:")
    for ch, acc, n_seen in worst10:
        print(f"  {ch!r:>4}  acc={acc:.3f}  n={n_seen}")
    unseen = [IDX_TO_CHAR[int(i)] for i in np.where(~seen)[0]]
    if unseen:
        print(f"  (never seen in val: {unseen!r})")

    ckpt = {
        "state_dict": model.state_dict(),
        "arch_cfg": {"n_classes": n_classes, "input_size": IMG_SIZE, "in_channels": 1},
        "char_to_idx": CHAR_TO_IDX,
        "idx_to_char": IDX_TO_CHAR,
    }
    torch.save(ckpt, model_out)
    print(f"saved {model_out}")
    return model, final_val_acc, worst10


# ===========================================================================
# Reader interface -- what identity scoring imports.
# ===========================================================================

def load_classifier(model_path: str = MODEL_OUT_DEFAULT, device: str = "cuda"):
    """Load a trained checkpoint. Returns (model, idx_to_char)."""
    dev = _resolve_device(device)
    ckpt = torch.load(model_path, map_location=dev, weights_only=False)
    cfg = ckpt["arch_cfg"]
    model = GlyphCNN(n_classes=cfg["n_classes"])
    model.load_state_dict(ckpt["state_dict"])
    model.to(dev).eval()
    return model, ckpt["idx_to_char"]


def _to_gray_64(cell) -> np.ndarray:
    """Normalize an arbitrary-size HxW or HxWxC uint8 cell (white glyph on
    black) to a 64x64 uint8 grayscale array."""
    arr = np.asarray(cell)
    if arr.ndim == 3:
        c = arr.shape[-1]
        arr = arr[..., :3].max(axis=-1) if c >= 3 else arr[..., 0]
    elif arr.ndim != 2:
        raise ValueError(f"expected HxW or HxWxC array, got shape {arr.shape}")
    arr = arr.astype(np.uint8)
    img = Image.fromarray(arr, mode="L")
    if img.size != (IMG_SIZE, IMG_SIZE):
        img = img.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
    return np.asarray(img, dtype=np.uint8)


def _batched_logits(model, cells, batch_size):
    device = next(model.parameters()).device
    was_training = model.training
    model.eval()
    try:
        with torch.no_grad():
            for i in range(0, len(cells), batch_size):
                batch = cells[i:i + batch_size]
                arrs = np.stack([_to_gray_64(c) for c in batch]).astype(np.float32) / 255.0
                t = torch.from_numpy(arrs).unsqueeze(1).to(device)
                yield model(t)
    finally:
        if was_training:
            model.train()


def classify(model, idx_to_char, cells, batch_size: int = 256):
    """cells: list of HxW or HxWxC uint8 arrays (white glyph on black, any
    size). Returns a list of predicted characters, one per cell."""
    if len(cells) == 0:
        return []
    out = []
    for logits in _batched_logits(model, cells, batch_size):
        pred_idx = logits.argmax(dim=1).cpu().numpy()
        out.extend(idx_to_char[int(p)] for p in pred_idx)
    return out


def classify_conf(model, idx_to_char, cells, batch_size: int = 256):
    """Same as classify(), but returns a list of (char, softmax_prob) tuples
    so callers can threshold low-confidence reads."""
    if len(cells) == 0:
        return []
    out = []
    for logits in _batched_logits(model, cells, batch_size):
        probs = torch.softmax(logits, dim=1)
        conf, pred_idx = probs.max(dim=1)
        pred_idx = pred_idx.cpu().numpy()
        conf = conf.cpu().numpy()
        out.extend((idx_to_char[int(p)], float(c)) for p, c in zip(pred_idx, conf))
    return out


# ===========================================================================
# Smoke self-test: round-trip classify() against real GT holdout cells.
# ===========================================================================

def _smoke_selftest(model_path: str, device: str):
    from eval_checkpoint import crop_cell

    print("\n--- smoke self-test: classify() on real GT holdout cells ---")
    model, idx_to_char = load_classifier(model_path, device=device)

    probe_fonts_chars = [
        ("eval_holdout/atlases/KosugiMaru-Regular.png", ["K", "g", "5", "&", "a"]),
        ("eval_holdout/atlases/NovaSquare.png", ["N", "o", "v", "4", "Q"]),
    ]
    cells, expected = [], []
    for atlas_path, chars in probe_fonts_chars:
        p = Path(atlas_path)
        if not p.exists():
            print(f"  (skip, missing: {atlas_path})")
            continue
        arr = np.asarray(Image.open(p).convert("RGB"))
        cw, ch = CELL_W, CELL_H
        for ch_ in chars:
            idx = CHARSET.index(ch_)
            row, col = idx // 12, idx % 12
            y0, x0 = row * ch, col * cw
            cells.append(arr[y0:y0 + ch, x0:x0 + cw])
            expected.append(ch_)

    if not cells:
        print("  no GT cells available, skipping round-trip check")
        return

    preds = classify(model, idx_to_char, cells)
    n_correct = 0
    for exp, pred in zip(expected, preds):
        mark = "OK" if exp == pred else "MISS"
        if exp == pred:
            n_correct += 1
        print(f"  expected={exp!r:>4}  predicted={pred!r:>4}  {mark}")
    print(f"  round-trip: {n_correct}/{len(expected)} correct")


# ===========================================================================
# CLI
# ===========================================================================

def _parse_args():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true", help="render + cache dataset")
    ap.add_argument("--train", action="store_true", help="train + save classifier from cached dataset")
    ap.add_argument("--smoke", action="store_true",
                     help="tiny end-to-end check: 3 train fonts + 2 val fonts + 1 epoch")
    ap.add_argument("--n-train", type=int, default=N_TRAIN_FONTS_DEFAULT, help="number of TRAIN fonts")
    ap.add_argument("--n-val", type=int, default=N_VAL_FONTS_DEFAULT, help="number of VAL fonts")
    ap.add_argument("--epochs", type=int, default=EPOCHS_DEFAULT)
    ap.add_argument("--batch-size", type=int, default=BATCH_SIZE_DEFAULT)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--fonts-root", default=FONTS_ROOT_DEFAULT)
    ap.add_argument("--holdout-dir", default=HOLDOUT_FONTS_DEFAULT)
    ap.add_argument("--data-cache", default=None, help=f"default: {DATA_CACHE_DEFAULT} ({DATA_CACHE_SMOKE_DEFAULT} for --smoke)")
    ap.add_argument("--model-out", default=None, help=f"default: {MODEL_OUT_DEFAULT} ({MODEL_OUT_SMOKE_DEFAULT} for --smoke)")
    ap.add_argument("--seed", type=int, default=SEED)
    return ap.parse_args()


def main():
    args = _parse_args()

    data_cache = args.data_cache or (DATA_CACHE_SMOKE_DEFAULT if args.smoke else DATA_CACHE_DEFAULT)
    model_out = args.model_out or (MODEL_OUT_SMOKE_DEFAULT if args.smoke else MODEL_OUT_DEFAULT)

    if args.smoke:
        n_train, n_val, epochs = 3, 2, 1
        do_build, do_train = True, True
    else:
        n_train, n_val, epochs = args.n_train, args.n_val, args.epochs
        do_build, do_train = (args.build, args.train) if (args.build or args.train) else (True, True)

    if do_build:
        build_dataset(args.fonts_root, args.holdout_dir, n_train, n_val, data_cache, seed=args.seed)

    if do_train:
        if not Path(data_cache).exists():
            raise FileNotFoundError(f"data cache {data_cache} not found; run with --build first")
        data = load_npz_dataset(data_cache)
        train_model(data, epochs=epochs, batch_size=args.batch_size, device=args.device, model_out=model_out)

    if args.smoke:
        _smoke_selftest(model_out, args.device)


if __name__ == "__main__":
    main()
