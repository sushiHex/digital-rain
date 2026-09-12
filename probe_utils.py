"""Shared helpers for caption / ref-ablation / multi-ref / V3-benchmark probes."""
from __future__ import annotations

import hashlib
import html
import inspect
import os
import platform
import subprocess
import sys
from base64 import b64encode
from collections import namedtuple
from io import BytesIO
from pathlib import Path
from typing import Iterable, Mapping

import lpips
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModel
import torchvision.transforms as T

from atlas_constants import CANVAS


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------

# Five fonts that consistently land in the bottom decile of our LoRA's composite
# score on the 50-font holdout. Iteration order is the figure / table order
# used by callers, so this dict's insertion order is part of the contract.
HARD_FONTS = {
    "BitcountGridDoubleInk":  "google-fonts/ofl/bitcountgriddoubleink/BitcountGridDoubleInk[CRSV,ELSH,ELXP,SZP1,SZP2,XPN1,XPN2,YPN1,YPN2,slnt,wght].ttf",
    "PlaywriteUSTradGuides":  "google-fonts/ofl/playwriteustradguides/PlaywriteUSTradGuides-Regular.ttf",
    "PlaywriteMXGuides":       "google-fonts/ofl/playwritemxguides/PlaywriteMXGuides-Regular.ttf",
    "RubikDistressed":          "google-fonts/ofl/rubikdistressed/RubikDistressed-Regular.ttf",
    "BitcountPropDoubleInk":  "google-fonts/ofl/bitcountpropdoubleink/BitcountPropDoubleInk[CRSV,ELSH,ELXP,SZP1,SZP2,XPN1,XPN2,YPN1,YPN2,slnt,wght].ttf",
}


# ---------------------------------------------------------------------------
# Probe constants used across analyzers
# ---------------------------------------------------------------------------

# LPIPS deltas in the same units the analyzers use to compare runs.
LPIPS_NOISE_FLOOR = 0.005          # below this is indistinguishable from training noise
LPIPS_MARGINAL_DELTA = 0.005       # alias kept for older imports
LPIPS_MEANINGFUL_DELTA = 0.01
LPIPS_STRONG_DELTA = 0.02
DINO_MEANINGFUL_DELTA = 0.01

# Caption-probe variant names. Hoisted so analyzers and runners share spellings.
CAPTION_CONTROL = "A_control"
CAPTION_MATCH = "B_match"
CAPTION_CLASH = "C_clash"
CAPTION_NULL = "D_null"
CAPTION_VARIANTS = (CAPTION_CONTROL, CAPTION_MATCH, CAPTION_CLASH, CAPTION_NULL)

# Reference-ablation variant names.
REF_TIMES = "times"
REF_ORACLE = "oracle"
REF_ROBOTO = "roboto"
REF_VARIANTS = (REF_TIMES, REF_ORACLE, REF_ROBOTO)

# Multi-reference variant names. "REF1_KG" = 1 ref of "Kg". "REF2_KG_MN" =
# 2 refs in order [Kg, Mn]. Etc.
REF1_KG = "1_kg"
REF2_KG_MN = "2_kg_mn"
REF2_MN_KG = "2_mn_kg"
MULTIREF_VARIANTS = (REF1_KG, REF2_KG_MN, REF2_MN_KG)


# ---------------------------------------------------------------------------
# Reference font for non-oracle baselines (Times-equivalent on each platform)
# ---------------------------------------------------------------------------

_PLATFORM_TIMES = {
    "Windows": "C:/Windows/Fonts/times.ttf",
    "Darwin":  "/Library/Fonts/Times.ttc",
    "Linux":   "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
}


def default_reference_font() -> str:
    """Return a platform-appropriate path to a Times-equivalent serif TTF."""
    return _PLATFORM_TIMES.get(platform.system(), _PLATFORM_TIMES["Linux"])


# ---------------------------------------------------------------------------
# Scoring models
# ---------------------------------------------------------------------------

ScoringModels = namedtuple("ScoringModels", "lpips dino dino_proc device")


_SCORING_TRANSFORM = T.Compose([
    T.Resize((CANVAS, CANVAS)),
    T.ToTensor(),
    T.Normalize([0.5] * 3, [0.5] * 3),
])


def load_scoring_models(device: str | None = None) -> ScoringModels:
    """Load LPIPS-Alex + DINOv2-base. Tries the local HF cache first; falls
    back to network only if that fails."""
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    def _load(name: str, factory):
        try:
            return factory(local_files_only=True)
        except Exception:
            print(f"  ({name}) local HF cache miss, falling back to network")
            return factory()

    lpips_model = lpips.LPIPS(net="alex").to(device).eval()
    dino_proc = _load(
        "dinov2 processor",
        lambda local_files_only=False: AutoImageProcessor.from_pretrained(
            "facebook/dinov2-base", local_files_only=local_files_only
        ),
    )
    dino_model = _load(
        "dinov2 model",
        lambda local_files_only=False: AutoModel.from_pretrained(
            "facebook/dinov2-base", local_files_only=local_files_only
        ),
    ).to(device).eval()
    return ScoringModels(lpips_model, dino_model, dino_proc, device)


def score_atlas_pair(gen_img: Image.Image, gt_img: Image.Image, models: ScoringModels):
    """Return (lpips, dinov2_cos) for a generated atlas vs its GT.

    Recovers from CUDA OOM by emptying the cache and returning NaNs for that
    pair so the analyzer can continue scoring the rest.
    """
    try:
        gen_t = _SCORING_TRANSFORM(gen_img).unsqueeze(0).to(models.device)
        gt_t = _SCORING_TRANSFORM(gt_img).unsqueeze(0).to(models.device)
        with torch.no_grad():
            lp = float(models.lpips(gen_t, gt_t).item())
        del gen_t, gt_t

        inputs = models.dino_proc(images=[gen_img, gt_img], return_tensors="pt").to(models.device)
        with torch.no_grad():
            out = models.dino(**inputs).last_hidden_state[:, 0]
        out = torch.nn.functional.normalize(out, dim=-1)
        dino = float((out[0] @ out[1]).item())
        del inputs, out
        return lp, dino
    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        print("  WARN: CUDA OOM during scoring -- returning NaN for this pair")
        return float("nan"), float("nan")


# Backwards-compatibility alias for the old positional signature.
def score_pair(gen_img, gt_img, lpips_model, dino_model, dino_proc, device):
    """Deprecated: prefer score_atlas_pair(gen, gt, ScoringModels)."""
    return score_atlas_pair(
        gen_img, gt_img,
        ScoringModels(lpips_model, dino_model, dino_proc, device),
    )


# ---------------------------------------------------------------------------
# GT atlas cache
# ---------------------------------------------------------------------------

_GT_CACHE_DIR = Path("experiments/gt_cache")


def _render_version_tag() -> str:
    """Short hash of build_dataset.render_atlas source.

    When render_atlas changes (different cell size, baseline, padding etc.)
    the version tag changes and cached GT atlases are bypassed automatically.
    """
    from build_dataset import render_atlas
    src = inspect.getsource(render_atlas)
    return hashlib.md5(src.encode("utf-8")).hexdigest()[:8]


def render_gt_atlas(font_path) -> Image.Image:
    """Render or load the cached ground-truth atlas for a font.

    Cache key combines font stem, filesize, mtime, and a short hash of
    render_atlas's source so a TTF update or render-logic change invalidates
    the cache automatically. Writes are atomic (tmp + os.replace).
    """
    from build_dataset import render_atlas

    p = Path(font_path)
    stat = p.stat()
    key = f"{p.stem}__{stat.st_size}__{stat.st_mtime_ns}__{_render_version_tag()}"
    _GT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = _GT_CACHE_DIR / f"{key}.png"
    if cached.exists():
        return Image.open(cached).convert("RGB")
    img = render_atlas(font_path).convert("RGB")
    tmp = cached.with_suffix(".png.tmp")
    img.save(tmp, format="PNG")
    os.replace(tmp, cached)
    return img


# ---------------------------------------------------------------------------
# Table printers used by analyzers
# ---------------------------------------------------------------------------

def print_per_font_table(
    by_font: Mapping[str, Mapping[str, Mapping[str, float]]],
    variants: Iterable[str],
    *,
    font_col_width: int = 8,
    val_col_width: int = 8,
    title: str = "PER-FONT TABLE",
) -> None:
    """Print a per-font x per-variant table with two metric blocks (lpips
    lower-better, dino higher-better)."""
    variants = list(variants)
    total_width = font_col_width + 3 + 2 * (len(variants) * (val_col_width + 1) + 2)
    print()
    print("=" * total_width)
    print(title + "  (lpips lower better, dino higher better)")
    print("=" * total_width)

    lpips_block = " ".join(f"{v:>{val_col_width}}" for v in variants)
    dino_block = " ".join(f"{v:>{val_col_width}}" for v in variants)
    metric_w = len(lpips_block)
    print(f"{'font':>{font_col_width}} | {'lpips':^{metric_w}} | {'dino':^{metric_w}}")
    print(f"{'':>{font_col_width}} | {lpips_block} | {dino_block}")
    print("-" * total_width)
    for font, by_variant in by_font.items():
        lp_row = " ".join(
            f"{by_variant[v]['lpips']:>{val_col_width}.4f}" if v in by_variant
            else f"{'-':>{val_col_width}}"
            for v in variants
        )
        dn_row = " ".join(
            f"{by_variant[v]['dinov2']:>{val_col_width}.4f}" if v in by_variant
            else f"{'-':>{val_col_width}}"
            for v in variants
        )
        print(f"{font:>{font_col_width}} | {lp_row} | {dn_row}")


# ---------------------------------------------------------------------------
# Subprocess driver shared by run_caption_probe / run_ref_ablation / run_multiref
# ---------------------------------------------------------------------------

RENDER_TIMEOUT_S = 600  # 10 min/render is generous; longer than that means a stall


def run_render_grid(
    jobs: Iterable[dict],
    *,
    ckpt: str,
    out_dir: Path,
    base_args: tuple[str, ...] = ("--steps", "20", "--seed", "42"),
) -> None:
    """Drive a grid of render_checkpoint.py invocations.

    Each job is {"out_name": str, "label": str, "extra_args": list[str]}.
    Existing outputs are skipped (idempotent resume). Each subprocess gets
    RENDER_TIMEOUT_S to complete; a timeout aborts the run rather than
    silently hanging. stdout is filtered for "Saved"/"Generating" lines.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = list(jobs)
    total = len(jobs)
    for i, job in enumerate(jobs, 1):
        out_path = out_dir / job["out_name"]
        if out_path.exists():
            print(f"[{i}/{total}] SKIP {out_path.name} (exists)", flush=True)
            continue
        print(f"[{i}/{total}] === {job['label']} ===", flush=True)
        cmd = [sys.executable, "render_checkpoint.py", ckpt, "--out", str(out_path)]
        cmd.extend(base_args)
        cmd.extend(job["extra_args"])
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=RENDER_TIMEOUT_S
            )
        except subprocess.TimeoutExpired:
            print(f"  TIMED OUT after {RENDER_TIMEOUT_S}s -- skipping", flush=True)
            continue
        if result.returncode != 0:
            print(f"  FAILED (exit {result.returncode})", flush=True)
            print(f"  stderr tail: {result.stderr[-800:]}", flush=True)
            sys.exit(1)
        for line in result.stdout.splitlines():
            if "Saved" in line or "Generating" in line or "reference image" in line:
                print(f"  {line}", flush=True)
    print(f"\nAll done. Outputs in {out_dir}/")


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def img_to_data_uri(img: Image.Image, max_width: int | None = None) -> str:
    """Encode a PIL image as a base64 PNG data URI, optionally downsizing."""
    if max_width and img.size[0] > max_width:
        ratio = max_width / img.size[0]
        img = img.resize((max_width, int(img.size[1] * ratio)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + b64encode(buf.getvalue()).decode()


def html_escape(text: str) -> str:
    """Escape user / data-derived text before embedding in HTML."""
    return html.escape(text, quote=True)
