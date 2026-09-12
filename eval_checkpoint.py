"""Evaluate a font LoRA checkpoint against a held-out test set.

Single-file eval runner. Loads the FLUX.2-klein pipeline + LoRA ONCE,
generates one atlas per holdout font (caching results to disk), then scores
generated vs ground-truth atlases with three metrics:

  - R-ACC   (OCR round-trip accuracy via TrOCR; catches glyph swap/drop/dup)
  - LPIPS   (perceptual similarity, AlexNet backbone; field-standard)
  - DINOv2  (feature cosine similarity; robust to small geometric jitter)

Composite: 0.5*(1-LPIPS) + 0.35*R-ACC + 0.15*DINOv2_cos

Per-metric ranges: LPIPS lower-is-better (0=identical), R-ACC and DINOv2
higher-is-better. Composite higher-is-better, theoretical max 1.0.

Optionally also reports IDENTITY (--identity): a font-invariant glyph
classifier's GT-gated read of whether each cell is the right LETTER,
independent of char_acc. NOTE: char_acc is a WITHIN-FONT NEAREST-NEIGHBOUR
match, not style fidelity -- its own docstring says style is largely controlled
for, and a retrieval baseline that returns a DIFFERENT real font outscores
every model here on it (research/2026-08-13-a-retrieval-baseline-beats-every-model.md). See glyph_classifier.py
and research/2026-07-18-wrong-letters-are-a-metric-artifact.md. Not part of
the composite; reported alongside it. Default ON if glyph_classifier.pt
exists, else skipped with a printed note (backward compatible).

Usage:
  # Generate + score from scratch
  python eval_checkpoint.py \
      --checkpoint experiments/.../checkpoint-3500 \
      --holdout eval_holdout \
      --out eval_runs/checkpoint-3500 \
      --reference-chars Kg

  # Re-score existing generations without re-running the LoRA
  python eval_checkpoint.py --skip-generate \
      --holdout eval_holdout \
      --out eval_runs/checkpoint-3500

  # Quick smoke test on 5 fonts
  python eval_checkpoint.py \
      --checkpoint experiments/.../checkpoint-3500 \
      --holdout eval_holdout \
      --out eval_runs/smoke \
      --count 5
"""
import argparse
import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image

# Atlas geometry + CHARSET imported from atlas_constants — single source of truth.
# A drift here would silently corrupt every cell crop.
from atlas_constants import CHARSET, GRID_COLS, GRID_ROWS, CANVAS, CELL_W, CELL_H, BLANK_INDICES, DRAWN_INDICES

# Hugging Face model IDs for the scoring metrics.
TROCR_MODEL_ID = "microsoft/trocr-small-printed"
DINOV2_MODEL_ID = "facebook/dinov2-base"

# Per-device scoring-model caches. compute_dinov2/compute_lpips are called once
# per run by the eval, but ONCE PER CANDIDATE by score_candidates (240x in a
# pilot) — rebuilding those GPU models each time fragments VRAM until the job
# wedges. Keyed by str(device) so a cpu/cuda mix stays correct.
_DINOV2_CACHE = {}
_LPIPS_CACHE = {}

# Composite metric weights. R-ACC catches glyph-identity errors, LPIPS measures
# perceptual style fidelity, DINOv2 captures macro-style similarity. Sum to 1.0
# (LPIPS contributes (1 - LPIPS) so the composite is always higher-is-better).
METRIC_WEIGHTS = {"lpips": 0.5, "racc": 0.35, "dinov2": 0.15}

# IDENTITY pass (optional, --identity): font-invariant glyph classifier
# (glyph_classifier.py). Separate from char_acc — char_acc is a within-font
# nearest-neighbour match (NOT style fidelity, see the module docstring);
# identity is whether the cell reads as the right LETTER at all. See
# research/2026-07-18-wrong-letters-are-a-metric-artifact.md. NOT part of the
# composite; reported alongside it.
IDENTITY_MODEL_DEFAULT = "glyph_classifier.pt"
IDENTITY_MODEL_SMOKE_FALLBACK = "glyph_classifier_smoke.pt"
IDENTITY_CONF_THRESHOLD = 0.5  # GT-read confidence below this abstains the cell

# Safety thresholds for the in-process generate path. Set conservatively so we
# bail before the OS swap-thrashes; CLI flags below let users tune them.
DEFAULT_RAM_ABORT_PCT = 85.0
DEFAULT_RSS_GROWTH_ABORT_GB = 12.0

# Cell-batch sizes for scoring. Tuned for a 24 GB GPU; lower if you OOM.
LPIPS_BATCH = 32
DINOV2_BATCH = 16


def compute_composite(lpips: float, racc: float, dinov2: float) -> float:
    """Composite quality score, higher better. Theoretical max 1.0."""
    return (
        METRIC_WEIGHTS["lpips"] * (1.0 - lpips)
        + METRIC_WEIGHTS["racc"] * racc
        + METRIC_WEIGHTS["dinov2"] * dinov2
    )


def char_category(ch: str) -> str:
    """Bucket a CHARSET character into one of 5 categories for breakdown reporting."""
    if ch.isupper():
        return "uppercase"
    if ch.islower():
        return "lowercase"
    if ch.isdigit():
        return "digit"
    if ch in "()[]{}<>":
        return "bracket"
    return "punctuation"


CATEGORIES = ["uppercase", "lowercase", "digit", "punctuation", "bracket"]

# Bootstrap parameters for confidence intervals on the aggregate metrics.
DEFAULT_BOOTSTRAP_SAMPLES = 2000
DEFAULT_BOOTSTRAP_CI = 0.95


def bootstrap_ci(per_cell_values, n_samples: int, ci: float, rng: np.random.Generator,
                 font_cell_ranges=None):
    """Bootstrap a (mean, lower, upper) tuple over per-cell values.

    RESAMPLES FONTS, NOT CELLS, when `font_cell_ranges` is supplied -- and it
    should always be supplied. The 94 cells of one font are not independent
    observations: they share a typeface, a reference image, a generation seed
    and a sampling trajectory. Resampling cells treats n as ~4,700 when the
    effective n is the ~50 fonts, which makes every interval far too narrow.

    This is the project's own stated rule ("Effective n is the 50 fonts, not
    the 4,700 cells. Never cell-bootstrap." -- CLAUDE.md, and the reason
    analysis/compare_runs.py pairs by font), and until 2026-08-08 the eval
    harness that produces the headline numbers violated it.

    Falls back to the old per-cell resample only when no font structure is
    given, so callers with genuinely exchangeable values still work.
    """
    arr = np.asarray(per_cell_values, dtype=np.float64)
    n = len(arr)
    if n == 0:
        return 0.0, 0.0, 0.0
    alpha = (1.0 - ci) / 2.0

    if font_cell_ranges:
        # Cluster (block) bootstrap: resample whole fonts with replacement and
        # take the mean over the cells they carry.
        blocks = [arr[s:e] for _name, s, e in font_cell_ranges if e > s]
        if blocks:
            nb = len(blocks)
            sums = np.array([b.sum() for b in blocks])
            counts = np.array([len(b) for b in blocks], dtype=np.float64)
            idx = rng.integers(0, nb, size=(n_samples, nb))
            resample_means = sums[idx].sum(axis=1) / counts[idx].sum(axis=1)
            return (float(arr.mean()),
                    float(np.percentile(resample_means, alpha * 100)),
                    float(np.percentile(resample_means, (1 - alpha) * 100)))

    # Vectorized resample: (n_samples, n) integer indices, gather, mean per row.
    idx = rng.integers(0, n, size=(n_samples, n))
    resample_means = arr[idx].mean(axis=1)
    lower = float(np.percentile(resample_means, alpha * 100))
    upper = float(np.percentile(resample_means, (1 - alpha) * 100))
    return float(arr.mean()), lower, upper


def crop_cell(img_np, idx):
    """Crop a single cell from a 1280x1280 atlas numpy array (H, W, C or H, W).

    Uses the same cell_w = size // GRID_COLS math as build_dataset.render_atlas
    (line 241-242). Returns (H, W, C) uint8.
    """
    size = img_np.shape[0]
    cell_w = CELL_W
    cell_h = CELL_H
    row = idx // GRID_COLS
    col = idx % GRID_COLS
    y0 = row * cell_h
    x0 = col * cell_w
    return img_np[y0:y0 + cell_h, x0:x0 + cell_w]


# ===========================================================================
# Phase 1: generate atlases for each holdout font
# ===========================================================================

def generate_phase_subprocess(args, holdout, gen_dir):
    """Generate one atlas per holdout font by SUBPROCESSING render_checkpoint.py.

    Memory-safe default path. Each subprocess loads the pipeline, runs one
    inference, and exits — full memory release between iterations. This is
    the same pattern continuous_train.py used reliably for 14 hours of 18
    sequential cycles. ~3 min per font (60-90s of pipeline reload overhead).

    Use this when stability matters more than speed, or when you haven't
    yet verified that generate_phase_inprocess is stable for the target
    inference count.
    """
    import subprocess
    import sys

    fonts = holdout["fonts"]
    if args.count is not None:
        fonts = fonts[:args.count]

    holdout_dir = Path(args.holdout)
    fonts_dir = holdout_dir / "fonts"

    print(f"\nGenerating {len(fonts)} atlases via subprocess (memory-stable)...")
    overall_start = time.time()

    for i, entry in enumerate(fonts):
        name = entry["name"]
        out_path = gen_dir / f"{name}.png"
        if args.skip_existing and out_path.exists():
            print(f"  [{i+1}/{len(fonts)}] {name} (skip, exists)")
            continue

        font_path = fonts_dir / entry["font_file"]
        if not font_path.exists():
            print(f"  [{i+1}/{len(fonts)}] {name} (SKIP - missing TTF: {font_path})")
            continue

        cmd = [
            sys.executable, "render_checkpoint.py",
            str(args.checkpoint),
            "--out", str(out_path),
            "--reference-chars", args.reference_chars,
            "--reference-font", str(font_path),
            "--steps", str(args.steps),
            "--seed", str(args.seed),
        ]

        t0 = time.time()
        # DEVNULL stdout/stderr so nothing accumulates in our parent process.
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - t0

        if result.returncode != 0:
            print(f"  [{i+1}/{len(fonts)}] {name} FAILED (rc={result.returncode}, {elapsed:.1f}s)")
            continue
        if not out_path.exists():
            print(f"  [{i+1}/{len(fonts)}] {name} FAILED (no output, {elapsed:.1f}s)")
            continue

        total_elapsed = time.time() - overall_start
        print(f"  [{i+1}/{len(fonts)}] {name} OK ({elapsed:.1f}s | total {total_elapsed/60:.1f}m)")

    print(f"  Generation phase complete in {(time.time()-overall_start)/60:.1f}m")


def _mem_snapshot():
    """Return (system_ram_pct, process_rss_gb, gpu_alloc_gb, gpu_reserved_gb)."""
    import psutil
    proc = psutil.Process()
    sys_ram_pct = psutil.virtual_memory().percent
    rss_gb = proc.memory_info().rss / 1024**3
    if torch.cuda.is_available():
        gpu_alloc = torch.cuda.memory_allocated() / 1024**3
        gpu_reserved = torch.cuda.memory_reserved() / 1024**3
    else:
        gpu_alloc = gpu_reserved = 0.0
    return sys_ram_pct, rss_gb, gpu_alloc, gpu_reserved


# _expand_x_embedder_to_256 and _install_glyph_channel_hook moved to
# generation_lib.py (they're needed there by load_generation_pipe, and
# generation_lib must not import back from this module — this module already
# imports FROM generation_lib inside generate_phase_inprocess, so the reverse
# import used to form a cycle that re-executed this module's top-level code
# whenever eval_checkpoint.py ran as __main__). Re-exported here for
# back-compat with any other code importing them from eval_checkpoint.
from generation_lib import _expand_x_embedder_to_256, _install_glyph_channel_hook


def generate_phase_inprocess(args, holdout, gen_dir):
    """Fast in-process path: load pipeline ONCE, reuse for all generations.

    Revised after the original version froze the OS twice. Key changes vs
    the broken version:
      1. NO enable_model_cpu_offload — hook state in the offload callbacks
         is the prime suspect for the original CPU RAM leak.
      2. Cache prompt embeddings ONCE, then DELETE the text encoder. We
         only need text encoding for the first prompt; the prompt is the
         same for every holdout font. Frees ~5-10 GB of VRAM.
      3. After encoding the prompt, move only transformer + VAE to CUDA.
         Pipeline VRAM: ~9 GB (INT8 transformer) + ~0.3 GB (VAE) +
         ~4-6 GB activations during inference = ~15 GB. Fits comfortably.
      4. Print psutil RAM + torch GPU memory snapshots with flush=True so
         we have visibility into a buffered subprocess.
      5. Abort cleanly if system RAM > RAM_ABORT_PCT or proc RSS grows
         > RSS_GROWTH_ABORT_GB — preserves the OS instead of swap-thrashing.

    If this path runs stable for a --count 5 smoke test, it's safe to scale
    up. Saves ~60-90s per font vs the subprocess fallback.

    The pipe-setup (pipeline build, prompt encoding/caching, text-encoder
    free, quantize+freeze, LoRA load, glyph-hook install) and the per-font
    inference call now live in generation_lib.py (load_generation_pipe /
    generate_one_atlas) so candidate_gen.py can reuse the exact same
    validated generation path. This function keeps the per-font loop,
    skip_existing, the RAM/RSS abort guards, and all logging.
    """
    from generation_lib import load_generation_pipe, generate_one_atlas

    def log(msg):
        print(msg, flush=True)

    ram_abort_pct = args.ram_abort_pct
    rss_growth_abort_gb = args.rss_growth_abort_gb

    fonts = holdout["fonts"]
    if args.count is not None:
        fonts = fonts[:args.count]
    holdout_dir = Path(args.holdout)

    # Baseline memory.
    sys_pct0, rss0, gpu_a0, gpu_r0 = _mem_snapshot()
    log(f"[mem] baseline: sys={sys_pct0:.1f}% rss={rss0:.2f}GB gpu={gpu_a0:.2f}GB")

    log(f"\nLoading FLUX.2-klein pipeline + LoRA...")
    t0 = time.time()
    pipe, cached_prompt_embeds, cached_neg_embeds = load_generation_pipe(
        args.checkpoint,
        use_template=args.use_template,
        template_pt=args.template_pt,
        model=args.model,
        reference_chars=args.reference_chars,
        template_zero=args.template_zero,
        prompt_style=args.prompt_style,
    )
    log(f"  pipeline + LoRA ready ({time.time()-t0:.0f}s)")
    log(f"  prompt embeds shape: {tuple(cached_prompt_embeds.shape)}")
    log(f"  negative embeds shape: {tuple(cached_neg_embeds.shape)}")

    sys_pct, rss, gpu_a, gpu_r = _mem_snapshot()
    rss_after_load = rss
    log(f"[mem] ready-to-generate: sys={sys_pct:.1f}% rss={rss:.2f}GB gpu={gpu_a:.2f}GB (reserved {gpu_r:.2f})")

    log(f"\nGenerating {len(fonts)} atlases in-process...")
    overall_start = time.time()
    aborted = False

    for i, entry in enumerate(fonts):
        name = entry["name"]
        out_path = gen_dir / f"{name}.png"
        if args.skip_existing and out_path.exists():
            log(f"  [{i+1}/{len(fonts)}] {name} (skip, exists)")
            continue

        # Safety check before each generation.
        sys_pct, rss, gpu_a, gpu_r = _mem_snapshot()
        rss_growth = rss - rss_after_load
        if sys_pct > ram_abort_pct:
            log(f"  [ABORT] sys RAM {sys_pct:.1f}% > {ram_abort_pct}%")
            aborted = True
            break
        if rss_growth > rss_growth_abort_gb:
            log(f"  [ABORT] proc RSS grew {rss_growth:.2f}GB > {rss_growth_abort_gb}GB")
            aborted = True
            break

        ref_path = holdout_dir / entry["reference"]

        t0 = time.time()
        generate_one_atlas(
            pipe, cached_prompt_embeds, cached_neg_embeds,
            str(ref_path), str(out_path),
            steps=args.steps, seed=args.seed,
        )
        elapsed = time.time() - t0

        # GC + cache flush every 5 iterations is enough — the smoke test
        # confirmed memory is flat per iteration with the no-offload design,
        # so per-iter gc.collect() (~0.5-2s each) was paying for nothing.
        if (i + 1) % 5 == 0:
            gc.collect()
            torch.cuda.empty_cache()

        sys_pct2, rss2, gpu_a2, _ = _mem_snapshot()
        total_elapsed = time.time() - overall_start
        log(
            f"  [{i+1}/{len(fonts)}] {name} OK ({elapsed:.1f}s | total {total_elapsed/60:.1f}m)  "
            f"sys={sys_pct2:.1f}% rss={rss2:.2f}GB ({rss2-rss_after_load:+.2f}) "
            f"gpu={gpu_a2:.2f}GB"
        )

    log(f"  Generation phase {'ABORTED' if aborted else 'complete'} in {(time.time()-overall_start)/60:.1f}m")

    del pipe
    gc.collect()
    torch.cuda.empty_cache()


def generate_phase(args, holdout, gen_dir):
    """Dispatch between subprocess (default) and in-process paths."""
    if args.in_process:
        generate_phase_inprocess(args, holdout, gen_dir)
    else:
        generate_phase_subprocess(args, holdout, gen_dir)


# ===========================================================================
# Phase 2: scoring
# ===========================================================================

def _cells_to_tensor(cells):
    """Stack a list of (H, W, 3) uint8 numpy cells into a single (N, 3, H, W)
    bf16 tensor in [-1, 1]. All cells must share the same H, W (they do —
    crop_cell uses fixed cell_w/cell_h)."""
    arr = np.stack(cells, axis=0)  # (N, H, W, 3) uint8
    t = torch.from_numpy(arr).float().permute(0, 3, 1, 2) / 127.5 - 1.0
    return t  # (N, 3, H, W) on CPU; caller moves to device per batch


def compute_lpips(gt_cells, gen_cells, device):
    """LPIPS per cell, averaged. Lower is better. Returns (mean, list).

    Batched (LPIPS_BATCH at a time) so we issue ~150 forward passes for a
    50-font / 4700-cell run instead of 4700 individual calls.
    """
    import lpips
    # Cache the net per-device. score_candidates calls this ONCE PER CANDIDATE
    # (240x in a pilot); rebuilding a GPU model each time churns and fragments
    # VRAM until generation wedges. The eval path calls it once per run, so
    # caching is a behavioural no-op there (same weights, same .eval() mode).
    _k = str(device)
    if _k not in _LPIPS_CACHE:
        _LPIPS_CACHE[_k] = lpips.LPIPS(net='alex', verbose=False).to(device).eval()
    net = _LPIPS_CACHE[_k]

    gt_t = _cells_to_tensor(gt_cells)
    gen_t = _cells_to_tensor(gen_cells)
    scores = []
    with torch.no_grad():
        for i in range(0, len(gt_cells), LPIPS_BATCH):
            gt_batch = gt_t[i:i + LPIPS_BATCH].to(device)
            gen_batch = gen_t[i:i + LPIPS_BATCH].to(device)
            d = net(gt_batch, gen_batch).view(-1)  # (B,)
            scores.extend(d.cpu().tolist())

    # net is cached in _LPIPS_CACHE — do NOT delete it. Still drop transient
    # activations so per-call peak memory is unchanged.
    torch.cuda.empty_cache()
    return float(np.mean(scores)), scores


def _ocr_decode_cell(cell_np, processor, model, device):
    """Decode a single white-on-black atlas cell with TrOCR.

    TrOCR is trained on dark-text-on-light-background, so we invert colors and
    pad with white. We also upscale before padding because our cells are small
    (106x160 at canvas=1280) relative to TrOCR's 384 input resolution.
    """
    # Invert to get dark glyph on white background.
    inv = 255 - cell_np
    img = Image.fromarray(inv).convert("RGB")
    # Upscale 4x to give TrOCR more pixels to chew on.
    w, h = img.size
    img = img.resize((w * 4, h * 4), Image.LANCZOS)
    # Square-pad with white.
    side = max(img.size)
    pad = Image.new("RGB", (side, side), (255, 255, 255))
    pad.paste(img, ((side - img.size[0]) // 2, (side - img.size[1]) // 2))

    pixel_values = processor(images=pad, return_tensors="pt").pixel_values.to(device)
    generated_ids = model.generate(pixel_values, max_length=4)
    decoded = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
    return decoded


_GT_OCR_CACHE_VERSION = 1


def _gt_ocr_cache_path(holdout_dir: Path) -> Path:
    return holdout_dir / "gt_ocr_cache.json"


def _load_gt_ocr_cache(holdout_dir: Path, expected_count: int) -> list[str] | None:
    """Load cached GT TrOCR decodings if the cache is valid.

    The cache is keyed on (cache version, TrOCR model, cell count). If any of
    those drift, we return None and force a recompute. The cache stores GT
    decodings as a flat list aligned with the score_phase cell extraction
    order (per-font, then DRAWN_INDICES).
    """
    cache_path = _gt_ocr_cache_path(holdout_dir)
    if not cache_path.exists():
        return None
    try:
        with open(cache_path) as f:
            payload = json.load(f)
    except json.JSONDecodeError:
        return None
    if (
        payload.get("version") != _GT_OCR_CACHE_VERSION
        or payload.get("trocr_model") != TROCR_MODEL_ID
        or payload.get("count") != expected_count
    ):
        return None
    decodings = payload.get("decodings")
    if not isinstance(decodings, list) or len(decodings) != expected_count:
        return None
    return decodings


def _save_gt_ocr_cache(holdout_dir: Path, decodings: list[str]) -> None:
    payload = {
        "version": _GT_OCR_CACHE_VERSION,
        "trocr_model": TROCR_MODEL_ID,
        "count": len(decodings),
        "decodings": decodings,
    }
    with open(_gt_ocr_cache_path(holdout_dir), "w") as f:
        json.dump(payload, f)


def compute_racc(gt_cells, gen_cells, expected_chars, device, holdout_dir: Path | None = None):
    """OCR consistency: does TrOCR decode the generated cell the same way it
    decodes the ground-truth cell?

    This is NOT pure accuracy — TrOCR is case-insensitive on our font set and
    hallucinates most symbols, so we sidestep its per-char limits by using the
    GT cell as the oracle. A cell "matches" if TrOCR produces the same decoded
    string from GT and Gen. This catches gross glyph corruption (wrong letter,
    swap, drop) while tolerating TrOCR's own OCR errors.

    GT decodings are deterministic and depend only on the holdout, so we cache
    them to disk and skip the GT pass on subsequent runs. This roughly halves
    the OCR cost across iterative experiments since the holdout is fixed.

    Returns (mean_score, per_cell_results).
    """
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel

    processor = TrOCRProcessor.from_pretrained(TROCR_MODEL_ID)
    model = VisionEncoderDecoderModel.from_pretrained(TROCR_MODEL_ID).to(device).eval()

    cached_gt = _load_gt_ocr_cache(holdout_dir, len(gt_cells)) if holdout_dir else None

    with torch.no_grad():
        if cached_gt is not None:
            print(f"  (using cached GT OCR decodings: {_gt_ocr_cache_path(holdout_dir)})")
            gt_decoded_list = cached_gt
        else:
            gt_decoded_list = [
                _ocr_decode_cell(gt, processor, model, device) for gt in gt_cells
            ]
            if holdout_dir is not None:
                _save_gt_ocr_cache(holdout_dir, gt_decoded_list)
                print(f"  (saved GT OCR cache: {_gt_ocr_cache_path(holdout_dir)})")

        gen_decoded_list = [
            _ocr_decode_cell(gen, processor, model, device) for gen in gen_cells
        ]

    matches = 0
    per_cell_results = []
    for expected, gt_decoded, gen_decoded in zip(expected_chars, gt_decoded_list, gen_decoded_list):
        match = gt_decoded == gen_decoded
        if match:
            matches += 1
        per_cell_results.append({
            "expected": expected,
            "gt_decoded": gt_decoded,
            "gen_decoded": gen_decoded,
            "match": match,
        })

    del model, processor
    torch.cuda.empty_cache()
    total = len(per_cell_results)
    return (matches / total if total else 0.0), per_cell_results


def compute_dinov2(gt_cells, gen_cells, device):
    """DINOv2 feature cosine similarity per cell, averaged. Higher is better.

    Returns (mean_cos_sim, per_cell_sims, gt_embeds, gen_embeds). The
    embeddings are returned so the template-matching metric (char-acc) can
    reuse them without re-running the encoder.

    Batched (DINOV2_BATCH cell-pairs at a time). Each batch encodes 2*B images
    in one forward pass — GT cells and Gen cells stacked together — then we
    compute pairwise cosine similarity inside the batch.
    """
    from transformers import AutoImageProcessor, AutoModel

    # Cache processor+model per-device — see the note in compute_lpips. This is
    # the "Loading weights: 223/223" that was repeating once per candidate.
    _k = str(device)
    if _k not in _DINOV2_CACHE:
        _DINOV2_CACHE[_k] = (
            AutoImageProcessor.from_pretrained(DINOV2_MODEL_ID),
            AutoModel.from_pretrained(DINOV2_MODEL_ID).to(device).eval(),
        )
    processor, model = _DINOV2_CACHE[_k]

    sims = []
    gt_embed_chunks = []
    gen_embed_chunks = []
    with torch.no_grad():
        for i in range(0, len(gt_cells), DINOV2_BATCH):
            gt_batch = [Image.fromarray(c) for c in gt_cells[i:i + DINOV2_BATCH]]
            gen_batch = [Image.fromarray(c) for c in gen_cells[i:i + DINOV2_BATCH]]
            n = len(gt_batch)
            inputs = processor(images=gt_batch + gen_batch, return_tensors="pt").to(device)
            out = model(**inputs)
            feats = out.last_hidden_state[:, 0]  # (2*n, D)
            gt_feats = feats[:n]
            gen_feats = feats[n:]
            cos = torch.nn.functional.cosine_similarity(gt_feats, gen_feats, dim=-1)  # (n,)
            sims.extend(cos.cpu().tolist())
            gt_embed_chunks.append(gt_feats.cpu())
            gen_embed_chunks.append(gen_feats.cpu())

    # model/processor are cached in _DINOV2_CACHE — do NOT delete them. Still
    # drop transient activations so per-call peak memory is unchanged.
    torch.cuda.empty_cache()
    gt_embeds = torch.cat(gt_embed_chunks, dim=0)   # (N_cells, D)
    gen_embeds = torch.cat(gen_embed_chunks, dim=0)
    return float(np.mean(sims)), sims, gt_embeds, gen_embeds


def compute_char_acc(gt_embeds, gen_embeds, font_cell_ranges):
    """Per-font template-matching accuracy via DINOv2 embeddings.

    For each font, build a 94x94 cosine-similarity matrix between its 94 gen
    cells and its 94 GT cells. For each gen cell at row position i, the
    "predicted" position is argmax_j sim(gen[i], gt[j]). The cell matches if
    that argmax equals i, meaning the LoRA's output for cell i is closer to
    its OWN ground truth cell than to any other glyph in the same font.

    Reuses the embeddings already computed by compute_dinov2 — zero new
    inference. Reports per-cell match (1.0 / 0.0) and per-font accuracy.

    The intuition: within a single font, all 94 cells share the same style,
    so cosine similarity within a font is dominated by glyph identity. A
    LoRA that generates the right shape will be most similar to its own GT;
    a LoRA that drops/swaps a glyph will be most similar to a different
    glyph's GT.

    Returns (mean_acc, per_cell_match_list_aligned_to_dinov2_order).
    """
    per_cell_match = [0] * gt_embeds.shape[0]
    matches = 0
    total = 0
    # Normalize once so cosine sim becomes a single matmul per font.
    gt_norm = torch.nn.functional.normalize(gt_embeds, dim=-1)
    gen_norm = torch.nn.functional.normalize(gen_embeds, dim=-1)
    for _name, start, end in font_cell_ranges:
        gen_block = gen_norm[start:end]   # (94, D)
        gt_block = gt_norm[start:end]     # (94, D)
        sim = gen_block @ gt_block.T      # (94 gen, 94 gt) cosine since both normalized
        pred = sim.argmax(dim=1)          # (94,) — which gt index each gen cell is closest to
        for local_i, p in enumerate(pred.tolist()):
            global_i = start + local_i
            ok = (p == local_i)
            per_cell_match[global_i] = 1 if ok else 0
            if ok:
                matches += 1
            total += 1
    return (matches / total if total else 0.0), per_cell_match


def compute_identity(gt_cells, gen_cells, expected_chars, model, idx_to_char,
                      conf_threshold: float = IDENTITY_CONF_THRESHOLD):
    """Font-invariant glyph-classifier IDENTITY pass, GT-gated.

    Runs the classifier ONCE on the GT cells and ONCE on the generated cells
    (glyph_classifier.classify/classify_conf), then applies the GT-gating
    principle from identity_score.py: a cell is only SCORED if the classifier
    itself reads the GT cell as the expected character (case-insensitive,
    with the small confusable-equivalence allowance in identity_score.reads_as)
    at or above `conf_threshold` confidence. If the reader can't even read the
    ground-truth glyph, it can't be trusted to judge the generation, so the
    cell abstains (identity_scored=False, identity_match=None). Among scored
    cells, identity_match is whether the classifier reads the GENERATED cell
    as the expected character.

    This is a DIFFERENT axis from char_acc (DINOv2 template match = style
    fidelity): identity asks "is it the right letter", not "does it render
    exactly like GT's own style".

    Returns (identity_mean, identity_scored_frac, per_cell_identity):
      - identity_mean: mean identity_match over SCORED cells only (0.0 if none scored)
      - identity_scored_frac: scored cells / total cells
      - per_cell_identity: list aligned to expected_chars/gt_cells/gen_cells, each
        {"identity_gt_pred", "identity_gen_pred", "identity_scored", "identity_match"}
        (identity_match is None for abstained cells)
    """
    from identity_score import reads_as
    from glyph_classifier import classify, classify_conf

    gt_preds_conf = classify_conf(model, idx_to_char, gt_cells)
    gen_preds = classify(model, idx_to_char, gen_cells)

    per_cell = []
    n_scored = 0
    n_match = 0
    for (gt_pred, gt_conf), gen_pred, expected in zip(gt_preds_conf, gen_preds, expected_chars):
        scored = reads_as(gt_pred, expected, lenient=True) and gt_conf >= conf_threshold
        match = reads_as(gen_pred, expected, lenient=True) if scored else None
        per_cell.append({
            "identity_gt_pred": gt_pred,
            "identity_gen_pred": gen_pred,
            "identity_scored": scored,
            "identity_match": match,
        })
        if scored:
            n_scored += 1
            if match:
                n_match += 1

    identity_mean = n_match / n_scored if n_scored else 0.0
    identity_scored_frac = n_scored / len(expected_chars) if expected_chars else 0.0
    return identity_mean, identity_scored_frac, per_cell


def score_phase(args, holdout, gen_dir, out_dir):
    """Load GT + generated atlases, extract drawn cells, run 3 metrics."""
    device = "cuda" if torch.cuda.is_available() else "cpu"

    holdout_dir = Path(args.holdout)
    fonts = holdout["fonts"]
    if args.count is not None:
        fonts = fonts[:args.count]

    # Load all atlas pairs into memory (94 cells each, 50 atlases = 4700 cells).
    # At 106x160x3 uint8 each, that's ~240 MB — fine.
    print(f"\nExtracting cells from {len(fonts)} atlas pairs...")
    all_gt_cells = []
    all_gen_cells = []
    all_expected = []
    font_cell_ranges = []  # (name, start_idx, end_idx) per font for per-font scoring
    for entry in fonts:
        name = entry["name"]
        gt_path = holdout_dir / entry["atlas"]
        gen_path = gen_dir / f"{name}.png"
        if not gen_path.exists():
            print(f"  MISSING: {gen_path}")
            continue
        gt = np.array(Image.open(gt_path).convert("RGB"))
        gen = np.array(Image.open(gen_path).convert("RGB"))
        # If sizes differ (e.g., 1280 vs 1152), resize gen to match gt.
        if gen.shape != gt.shape:
            gen_img = Image.fromarray(gen).resize((gt.shape[1], gt.shape[0]), Image.LANCZOS)
            gen = np.array(gen_img)

        start = len(all_gt_cells)
        for idx in DRAWN_INDICES:
            all_gt_cells.append(crop_cell(gt, idx))
            all_gen_cells.append(crop_cell(gen, idx))
            all_expected.append(CHARSET[idx])
        end = len(all_gt_cells)
        font_cell_ranges.append((name, start, end))

    if not all_gt_cells:
        print("ERROR: no cells extracted (no generated atlases?). Run without --skip-generate first.")
        return

    print(f"  {len(all_gt_cells)} cells total across {len(font_cell_ranges)} fonts")

    # ========================================================================
    # LPIPS
    # ========================================================================
    print("\nComputing LPIPS (perceptual similarity)...")
    t0 = time.time()
    lpips_mean, lpips_per_cell = compute_lpips(all_gt_cells, all_gen_cells, device)
    print(f"  LPIPS mean: {lpips_mean:.4f} (lower better) [{time.time()-t0:.1f}s]")

    # ========================================================================
    # R-ACC
    # ========================================================================
    print("\nComputing R-ACC (TrOCR GT-vs-Gen consistency)...")
    t0 = time.time()
    racc, racc_per_cell = compute_racc(
        all_gt_cells, all_gen_cells, all_expected, device, holdout_dir=holdout_dir
    )
    print(f"  R-ACC: {racc:.4f} (higher better) [{time.time()-t0:.1f}s]")

    # ========================================================================
    # DINOv2
    # ========================================================================
    print("\nComputing DINOv2 cosine similarity...")
    t0 = time.time()
    dino_mean, dino_per_cell, gt_embeds, gen_embeds = compute_dinov2(
        all_gt_cells, all_gen_cells, device
    )
    print(f"  DINOv2: {dino_mean:.4f} (higher better) [{time.time()-t0:.1f}s]")

    # Char-acc reuses the embeddings — zero extra inference.
    print("\nComputing char-acc (per-font template matching via DINOv2)...")
    t0 = time.time()
    char_acc, char_acc_per_cell = compute_char_acc(gt_embeds, gen_embeds, font_cell_ranges)
    print(f"  char-acc: {char_acc:.4f} (higher better) [{time.time()-t0:.2f}s]")

    # ========================================================================
    # IDENTITY (font-invariant glyph classifier, GT-gated) — optional, gated
    # behind --identity. Runs ALONGSIDE char_acc/DINOv2, does not replace them.
    # ========================================================================
    identity_mean = identity_scored_frac = None
    identity_per_cell = None
    if getattr(args, "identity", False):
        from glyph_classifier import load_classifier

        print(f"\nComputing IDENTITY (glyph classifier: {args.classifier_path})...")
        t0 = time.time()
        identity_model, identity_idx_to_char = load_classifier(args.classifier_path, device=device)
        identity_mean, identity_scored_frac, identity_per_cell = compute_identity(
            all_gt_cells, all_gen_cells, all_expected, identity_model, identity_idx_to_char
        )
        del identity_model
        if device == "cuda":
            torch.cuda.empty_cache()
        print(f"  identity: {identity_mean:.4f} over {identity_scored_frac:.1%} scored cells "
              f"(higher better, not in composite) [{time.time()-t0:.2f}s]")

    # ========================================================================
    # Composite
    # ========================================================================
    composite = compute_composite(lpips_mean, racc, dino_mean)

    # ========================================================================
    # Bootstrap CIs on each per-cell metric
    # ========================================================================
    rng = np.random.default_rng(args.bootstrap_seed)
    racc_match_per_cell = [1.0 if r["match"] else 0.0 for r in racc_per_cell]
    char_acc_per_cell_f = [float(x) for x in char_acc_per_cell]
    # Every CI here resamples FONTS, not cells -- see bootstrap_ci's docstring.
    _, lpips_lo, lpips_hi = bootstrap_ci(lpips_per_cell, args.bootstrap_samples,
                                         args.bootstrap_ci, rng, font_cell_ranges)
    _, racc_lo, racc_hi = bootstrap_ci(racc_match_per_cell, args.bootstrap_samples,
                                       args.bootstrap_ci, rng, font_cell_ranges)
    _, dino_lo, dino_hi = bootstrap_ci(dino_per_cell, args.bootstrap_samples,
                                       args.bootstrap_ci, rng, font_cell_ranges)
    _, char_acc_lo, char_acc_hi = bootstrap_ci(char_acc_per_cell_f, args.bootstrap_samples,
                                               args.bootstrap_ci, rng, font_cell_ranges)
    # Composite CI by resampling FONTS and recomputing each metric on the
    # resample, so the CI reflects correlated uncertainty in lpips/racc/dino
    # while still respecting that fonts, not cells, are the sampling unit.
    arr_lpips = np.asarray(lpips_per_cell, dtype=np.float64)
    arr_racc = np.asarray(racc_match_per_cell, dtype=np.float64)
    arr_dino = np.asarray(dino_per_cell, dtype=np.float64)
    _blocks = [(s, e) for _n, s, e in font_cell_ranges if e > s]
    if _blocks:
        _counts = np.array([e - s for s, e in _blocks], dtype=np.float64)
        _bidx = rng.integers(0, len(_blocks), size=(args.bootstrap_samples, len(_blocks)))
        _den = _counts[_bidx].sum(axis=1)

        def _blockmean(a):
            sums = np.array([a[s:e].sum() for s, e in _blocks])
            return sums[_bidx].sum(axis=1) / _den
        m_lpips, m_racc, m_dino = (_blockmean(arr_lpips), _blockmean(arr_racc),
                                   _blockmean(arr_dino))
    else:
        n_cells = len(arr_lpips)
        idx = rng.integers(0, n_cells, size=(args.bootstrap_samples, n_cells))
        m_lpips, m_racc, m_dino = (arr_lpips[idx].mean(axis=1),
                                   arr_racc[idx].mean(axis=1),
                                   arr_dino[idx].mean(axis=1))
    composite_resamples = (
        METRIC_WEIGHTS["lpips"] * (1.0 - m_lpips)
        + METRIC_WEIGHTS["racc"] * m_racc
        + METRIC_WEIGHTS["dinov2"] * m_dino
    )
    alpha = (1.0 - args.bootstrap_ci) / 2.0
    composite_lo = float(np.percentile(composite_resamples, alpha * 100))
    composite_hi = float(np.percentile(composite_resamples, (1 - alpha) * 100))

    # Per-font breakdown: re-aggregate each metric over each font's 94 cells.
    per_font = []
    for name, start, end in font_cell_ranges:
        n = end - start
        font_lpips = float(np.mean(lpips_per_cell[start:end]))
        font_racc = sum(1 for r in racc_per_cell[start:end] if r["match"]) / n
        font_dino = float(np.mean(dino_per_cell[start:end]))
        font_char_acc = sum(char_acc_per_cell[start:end]) / n
        per_font.append({
            "name": name,
            "lpips": font_lpips,
            "racc": font_racc,
            "dinov2": font_dino,
            "char_acc": font_char_acc,
            "composite": compute_composite(font_lpips, font_racc, font_dino),
        })

    # Sort worst-to-best for quick inspection of failure modes.
    per_font.sort(key=lambda d: d["composite"])

    # ========================================================================
    # Per-category breakdown — bucket every cell by char_category(expected)
    # then aggregate each metric inside the bucket. Reveals which glyph
    # classes the LoRA is weakest at, which the per-font composite hides.
    # ========================================================================
    cells_by_cat = {cat: [] for cat in CATEGORIES}
    for cell_idx, expected in enumerate(all_expected):
        cells_by_cat[char_category(expected)].append(cell_idx)

    per_category = {}
    for cat, idxs in cells_by_cat.items():
        if not idxs:
            continue
        cat_lpips = float(np.mean([lpips_per_cell[i] for i in idxs]))
        cat_racc = sum(1 for i in idxs if racc_per_cell[i]["match"]) / len(idxs)
        cat_dino = float(np.mean([dino_per_cell[i] for i in idxs]))
        cat_char_acc = sum(char_acc_per_cell[i] for i in idxs) / len(idxs)
        per_category[cat] = {
            "n_cells": len(idxs),
            "lpips": cat_lpips,
            "racc": cat_racc,
            "dinov2": cat_dino,
            "char_acc": cat_char_acc,
            "composite": compute_composite(cat_lpips, cat_racc, cat_dino),
        }

    # ========================================================================
    # Persist
    # ========================================================================
    result = {
        "checkpoint": str(args.checkpoint) if args.checkpoint else None,
        "holdout": str(args.holdout),
        "num_fonts": len(font_cell_ranges),
        "cells_per_font": len(DRAWN_INDICES),
        "aggregate": {
            "lpips": lpips_mean,
            "racc": racc,
            "dinov2": dino_mean,
            "char_acc": char_acc,
            "composite": composite,
        },
        "ci_95": {
            "samples": args.bootstrap_samples,
            "level": args.bootstrap_ci,
            "lpips": [lpips_lo, lpips_hi],
            "racc": [racc_lo, racc_hi],
            "dinov2": [dino_lo, dino_hi],
            "char_acc": [char_acc_lo, char_acc_hi],
            "composite": [composite_lo, composite_hi],
        },
        "per_category": per_category,
        "per_font": per_font,
    }
    if getattr(args, "identity", False):
        result["aggregate"]["identity"] = identity_mean
        result["aggregate"]["identity_scored_frac"] = identity_scored_frac
        result["identity_classifier"] = str(args.classifier_path)
    scores_path = out_dir / "scores.json"
    with open(scores_path, "w") as f:
        json.dump(result, f, indent=2)

    # Per-cell dump for failure heatmap analysis
    per_cell_records = []
    cell_to_font = {}
    for name, start, end in font_cell_ranges:
        for i in range(start, end):
            cell_to_font[i] = name
    for i, expected in enumerate(all_expected):
        record = {
            "font": cell_to_font[i],
            "char": expected,
            "category": char_category(expected),
            "lpips": float(lpips_per_cell[i]),
            "racc_match": bool(racc_per_cell[i]["match"]),
            "racc_gt_decoded": racc_per_cell[i]["gt_decoded"],
            "racc_gen_decoded": racc_per_cell[i]["gen_decoded"],
            "dinov2": float(dino_per_cell[i]),
            "char_acc_match": int(char_acc_per_cell[i]),
        }
        if getattr(args, "identity", False):
            record["identity_gt_pred"] = identity_per_cell[i]["identity_gt_pred"]
            record["identity_gen_pred"] = identity_per_cell[i]["identity_gen_pred"]
            record["identity_scored"] = identity_per_cell[i]["identity_scored"]
            record["identity_match"] = identity_per_cell[i]["identity_match"]
        per_cell_records.append(record)
    per_cell_path = out_dir / "per_cell.json"
    with open(per_cell_path, "w") as f:
        json.dump(per_cell_records, f)
    print(f"Per-cell records: {per_cell_path} ({len(per_cell_records)} cells)")

    print(f"\n{'='*60}")
    print(f"RESULT: composite = {composite:.4f}  [95% CI: {composite_lo:.4f}, {composite_hi:.4f}]")
    print(f"  LPIPS:    {lpips_mean:.4f}  [{lpips_lo:.4f}, {lpips_hi:.4f}]  (lower better)")
    print(f"  R-ACC:    {racc:.4f}  [{racc_lo:.4f}, {racc_hi:.4f}]  (higher better)")
    print(f"  DINOv2:   {dino_mean:.4f}  [{dino_lo:.4f}, {dino_hi:.4f}]  (higher better)")
    print(f"  char-acc: {char_acc:.4f}  [{char_acc_lo:.4f}, {char_acc_hi:.4f}]  (not in composite)")
    if getattr(args, "identity", False):
        print(f"  identity: {identity_mean:.4f}  (scored {identity_scored_frac:.1%} of cells)  (not in composite)")
    print(f"{'='*60}")
    print(f"\nPer-character-category:")
    print(f"  {'category':<14} {'n':>4}  {'compos':>7}  {'lpips':>7}  {'r-acc':>7}  {'dinov2':>7}  {'chr-acc':>7}")
    for cat in CATEGORIES:
        if cat not in per_category:
            continue
        c = per_category[cat]
        print(f"  {cat:<14} {c['n_cells']:>4}  {c['composite']:>7.4f}  {c['lpips']:>7.4f}  {c['racc']:>7.4f}  {c['dinov2']:>7.4f}  {c['char_acc']:>7.4f}")
    print(f"\nWorst 5 fonts by composite:")
    for d in per_font[:5]:
        print(f"  {d['composite']:.4f}  {d['name']:40s}  R-ACC={d['racc']:.3f}  LPIPS={d['lpips']:.4f}")
    print(f"\nBest 5 fonts by composite:")
    for d in per_font[-5:]:
        print(f"  {d['composite']:.4f}  {d['name']:40s}  R-ACC={d['racc']:.3f}  LPIPS={d['lpips']:.4f}")
    print(f"\nScores written to {scores_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default=None,
                        help="LoRA checkpoint dir (skip with --skip-generate to re-score)")
    parser.add_argument("--holdout", required=True, help="Holdout dir from eval_build_holdout.py")
    parser.add_argument("--out", required=True, help="Output dir for generated atlases + scores")
    # PROMPT LABEL ONLY -- this does NOT choose the reference image. The
    # reference image comes from <holdout>/references/, pre-rendered by
    # eval_build_holdout.py (whose identically-named flag DOES control the
    # image). This only substitutes into make_prompt()'s
    # '...derived from the reference image "<X>"' string.
    #
    # Keep "Kg": train_lora_kg.py's prompt is hardcoded to "Kg" (see its
    # comment), so this must match the TRAINED prompt even though the
    # training images showed Rg. Changing it here would put the prompt out
    # of distribution. See research/2026-07-28-reference-char-mismatch.md.
    parser.add_argument("--reference-chars", default="Kg",
                        help="Label substituted into the text prompt (NOT the reference image; "
                             "keep 'Kg' to match the trained prompt)")
    parser.add_argument("--strict-conditioning", action="store_true",
                        help="Abort if the eval's conditioning does not match what the "
                             "checkpoint was trained with (default: warn loudly and proceed)")
    parser.add_argument("--prompt-style", default=None,
                        choices=["structured", "trained-short"],
                        help="Override the prompt style. DEFAULT: derived from the checkpoint's "
                             "training config, which is almost always what you want. "
                             "structured = make_prompt() (what the BASELINE trained on); "
                             "trained-short = the verbatim prompt train_lora_kg.py trained "
                             "the glyph model on")
    parser.add_argument("--use-template", action="store_true",
                        help="glyph-latent conditioning: channel-concat the neutral glyph template")
    parser.add_argument("--template-pt", default="dataset_v2/cache/template.pt",
                        help="cached glyph-template latent for channel-concat conditioning")
    parser.add_argument("--template-zero", action="store_true",
                        help="ablation: feed ZEROS for the template channels (isolates template content vs capacity)")
    # Apache-2.0 4B by default (2026-09-11); the base is normally derived from
    # the checkpoint's conditioning record anyway. See docs/licensing.md.
    parser.add_argument("--model", default="black-forest-labs/FLUX.2-klein-base-4B")
    parser.add_argument("--steps", type=int, default=20, help="Inference steps per atlas")
    parser.add_argument("--seed", type=int, default=42, help="Inference seed (fixed for reproducibility)")
    parser.add_argument("--count", type=int, default=None, help="Eval only first N holdout fonts")
    parser.add_argument("--skip-generate", action="store_true", help="Only score existing generations")
    parser.add_argument("--skip-existing", action="store_true", help="Skip fonts whose output already exists")
    parser.add_argument("--skip-score", action="store_true", help="Only generate, don't score")
    parser.add_argument("--in-process", action="store_true",
                        help="Load pipeline once and loop in-process (fast, has safety guards). "
                             "Default is subprocess-per-font (slow but bulletproof).")
    parser.add_argument("--ram-abort-pct", type=float, default=DEFAULT_RAM_ABORT_PCT,
                        help="In-process: abort if system RAM exceeds this percent")
    parser.add_argument("--rss-growth-abort-gb", type=float, default=DEFAULT_RSS_GROWTH_ABORT_GB,
                        help="In-process: abort if process RSS grows by this many GB since load")
    parser.add_argument("--bootstrap-samples", type=int, default=DEFAULT_BOOTSTRAP_SAMPLES,
                        help="Number of bootstrap resamples for CI estimation")
    parser.add_argument("--bootstrap-ci", type=float, default=DEFAULT_BOOTSTRAP_CI,
                        help="Confidence level for bootstrap CIs (e.g. 0.95)")
    parser.add_argument("--bootstrap-seed", type=int, default=0,
                        help="RNG seed for bootstrap resampling (fixed for reproducibility)")
    parser.add_argument("--identity", dest="identity", action="store_true", default=None,
                        help="Run the IDENTITY pass (font-invariant glyph classifier, GT-gated; see "
                             "glyph_classifier.py / research/2026-07-18-wrong-letters-are-a-metric-artifact.md). "
                             f"Default: ON if {IDENTITY_MODEL_DEFAULT} exists, else skipped with a printed note.")
    parser.add_argument("--no-identity", dest="identity", action="store_false",
                        help="Force-disable the IDENTITY pass even if a classifier checkpoint exists.")
    parser.add_argument("--classifier-path", default=IDENTITY_MODEL_DEFAULT,
                        help=f"Glyph classifier checkpoint for the IDENTITY pass (default: {IDENTITY_MODEL_DEFAULT})")
    args = parser.parse_args()

    # Resolve the IDENTITY pass. Three states from the CLI: not mentioned
    # (args.identity is None) -> default ON only if the full checkpoint
    # exists; --identity -> forced on, falls back to the smoke checkpoint if
    # the requested (default) path is missing (real model not trained yet);
    # --no-identity -> always off. Backward compat: when identity ends up
    # off, args.identity is a plain False and score_phase's `getattr(args,
    # "identity", False)` checks make the rest of the pipeline byte-identical
    # to before this feature existed.
    identity_explicit = args.identity is not None
    identity_requested = True if args.identity is None else args.identity
    resolved_path = None
    if identity_requested:
        candidate = Path(args.classifier_path)
        if candidate.exists():
            resolved_path = candidate
        elif identity_explicit and args.classifier_path == IDENTITY_MODEL_DEFAULT \
                and Path(IDENTITY_MODEL_SMOKE_FALLBACK).exists():
            print(f"[identity] {args.classifier_path} not found; falling back to smoke checkpoint "
                  f"{IDENTITY_MODEL_SMOKE_FALLBACK} (plumbing only -- expect nonsense predictions "
                  "until the real classifier lands)")
            resolved_path = Path(IDENTITY_MODEL_SMOKE_FALLBACK)
        elif identity_explicit:
            print(f"[identity] --identity requested but no classifier checkpoint found at "
                  f"{args.classifier_path} (nor smoke fallback {IDENTITY_MODEL_SMOKE_FALLBACK}) "
                  "-- skipping IDENTITY pass")
        else:
            print(f"[identity] {IDENTITY_MODEL_DEFAULT} not found -- skipping IDENTITY pass by default "
                  "(pass --identity --classifier-path <path> to force one)")
    args.identity = resolved_path is not None
    if args.identity:
        args.classifier_path = str(resolved_path)

    if args.use_template and not args.in_process:
        parser.error("--use-template requires --in-process: the subprocess path "
                     "(render_checkpoint.py) has no template support and crashes silently")

    if args.skip_generate and args.skip_score:
        print("ERROR: --skip-generate and --skip-score together leave nothing to do")
        return 2
    if not args.skip_generate and args.checkpoint is None:
        print("ERROR: --checkpoint required unless --skip-generate is set")
        return 2

    # ---- train/eval conditioning guard --------------------------------
    # This project shipped two silent conditioning mismatches (reference
    # image Rg-vs-Kg, and prompt structured-vs-trained-short). The prompt one
    # suppressed IDENTITY on all 50 fonts and flipped a headline comparison.
    # See conditioning_config.py and
    # research/2026-07-28-reference-char-mismatch.md.
    if not args.skip_generate and args.checkpoint is not None:
        from conditioning_config import check_eval_conditioning, expected_conditioning

        # Default the prompt style FROM THE CHECKPOINT rather than from a
        # global constant. The correct value is a property of the model being
        # evaluated, not of the eval invocation -- making the caller remember
        # it is what produced the original mismatch. An explicit --prompt-style
        # still wins (and is still checked below).
        if args.prompt_style is None:
            exp = expected_conditioning(args.checkpoint)
            args.prompt_style = (exp or {}).get("prompt_style") or "structured"
            src = "checkpoint" if exp else "fallback default"
            print(f"  [conditioning] prompt_style={args.prompt_style} (derived from {src})")

        problems, notes, expected = check_eval_conditioning(
            args.checkpoint, prompt_style=args.prompt_style, holdout_dir=args.holdout,
            template_pt=args.template_pt if args.use_template else None)
        for n in notes:
            print(f"  [conditioning] note: {n}")
        if problems:
            print("\n" + "!" * 72)
            for p in problems:
                print(f"  CONDITIONING MISMATCH: {p}")
            print("!" * 72 + "\n")
            if args.strict_conditioning:
                print("ERROR: aborting (--strict-conditioning). "
                      "Re-run with the prompt style the checkpoint was trained on.")
                return 3
        elif expected:
            print(f"  [conditioning] OK: eval matches training "
                  f"(prompt_style={expected['prompt_style']})")

    out_dir = Path(args.out)
    gen_dir = out_dir / "generated"
    gen_dir.mkdir(parents=True, exist_ok=True)

    # Load holdout manifest.
    holdout_path = Path(args.holdout) / "manifest.json"
    with open(holdout_path) as f:
        holdout = json.load(f)
    print(f"Holdout: {holdout['count']} fonts, ref_chars='{holdout['reference_chars']}'")

    if not args.skip_generate:
        generate_phase(args, holdout, gen_dir)

    if not args.skip_score:
        score_phase(args, holdout, gen_dir, out_dir)


if __name__ == "__main__":
    # sys.exit(main() or 0), NOT a bare main(). Every failure path below returns
    # a non-zero code, but until 2026-08-13 the exit status was ALWAYS 0, so
    # every runner's `|| fail "eval" $?` was inert and each one wrote its _DONE
    # marker after an eval that had refused to run. CLAUDE.md's rule "never
    # infer success from the absence of a crash" was unenforceable here.
    sys.exit(main() or 0)
