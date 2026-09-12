
"""Standalone dataset auditor.

Walks an existing dataset, scores every font+atlas with font_quality,
quarantines rejects, and writes visual + machine-readable reports.

Usage:
    python analysis/audit_dataset.py --dataset-dir dataset_Kg --font-dir google-fonts
    python analysis/audit_dataset.py --dataset-dir dataset_Kg --font-dir google-fonts --dry-run
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import argparse
import base64
import json
import shutil
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

from font_quality import score_font, ATLAS_CHECKS, QualityResult


def _find_font(stem, font_dir):
    """Find a TTF/OTF file matching stem in font_dir (recursive).

    Handles common naming mismatches:
    - Atlas stem "Anton" -> font file "Anton-Regular.ttf"
    - Atlas stem "Font-Regular" -> font file "Font.ttf"
    """
    if font_dir is None:
        return None
    font_dir = Path(font_dir)

    # Build lookup if not cached
    if not hasattr(_find_font, '_cache') or _find_font._cache_dir != font_dir:
        _find_font._cache = {}
        _find_font._cache_dir = font_dir
        for ext in [".ttf", ".otf"]:
            for fp in font_dir.rglob(f"*{ext}"):
                if fp.stem not in _find_font._cache or len(fp.parts) < len(_find_font._cache[fp.stem].parts):
                    _find_font._cache[fp.stem] = fp

    cache = _find_font._cache
    # Exact match
    if stem in cache:
        return cache[stem]
    # Try adding -Regular
    if f"{stem}-Regular" in cache:
        return cache[f"{stem}-Regular"]
    # Try removing -Regular
    if stem.endswith("-Regular") and stem[:-8] in cache:
        return cache[stem[:-8]]
    return None


def _build_html_report(entries, image_source_fn):
    """Build an HTML visual review page for rejected fonts.

    image_source_fn(stem, kind) -> Path  where kind is 'atlas' or 'reference'
    """
    failed = [e for e in entries if not e["passed"]]
    if not failed:
        return "<html><body><h1>No rejections</h1></body></html>"

    rows = []
    for entry in failed:
        stem = entry["font_name"]

        atlas_b64 = ""
        atlas_path = image_source_fn(stem, "atlas")
        if atlas_path and atlas_path.exists():
            with open(atlas_path, "rb") as f:
                atlas_b64 = base64.b64encode(f.read()).decode()

        ref_b64 = ""
        ref_path = image_source_fn(stem, "reference")
        if ref_path and ref_path.exists():
            with open(ref_path, "rb") as f:
                ref_b64 = base64.b64encode(f.read()).decode()

        reasons = ", ".join(c["name"] for c in entry["failed_checks"])
        rows.append(
            f'<div style="display:flex;gap:12px;margin:12px 0;align-items:flex-start;'
            f'border-bottom:1px solid #333;padding-bottom:12px">'
            f'<span style="width:250px;font-size:13px;color:#e94560;word-break:break-all">'
            f'{stem}</span>'
            f'<img src="data:image/png;base64,{ref_b64}" style="width:100px;height:100px;'
            f'border:1px solid #333;background:#000">'
            f'<img src="data:image/png;base64,{atlas_b64}" style="width:200px;height:200px;'
            f'border:1px solid #333;background:#000">'
            f'<span style="width:300px;font-size:12px;color:#f88">{reasons}</span>'
            f'</div>'
        )

    n_failed = len(failed)
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<title>Quarantine Report</title>'
        '<style>body{background:#111;color:#eee;font-family:system-ui;padding:20px}'
        'h1{color:#e94560}h2{color:#888}</style></head><body>'
        f'<h1>Quarantine Report ({n_failed} rejected fonts)</h1>'
        f'<h2>Review each rejection. Move false positives back with: '
        f'mv quarantine/atlases/Name.png atlases/</h2>'
        + "\n".join(rows)
        + '</body></html>'
    )


def main():
    parser = argparse.ArgumentParser(description="Audit a font dataset for quality issues")
    parser.add_argument("--dataset-dir", required=True, help="Path to the dataset directory")
    parser.add_argument("--font-dir", default=None,
                        help="Path to font files for font-level checks (e.g., google-fonts)")
    parser.add_argument("--quarantine-dir", default=None,
                        help="Where to move rejected files (default: {dataset-dir}/quarantine)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Score and report only, don't move files")
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    quarantine_dir = Path(args.quarantine_dir) if args.quarantine_dir else dataset_dir / "quarantine"
    atlas_dir = dataset_dir / "atlases"
    ref_dir = dataset_dir / "references"

    if not atlas_dir.exists():
        print(f"ERROR: {atlas_dir} does not exist")
        return

    atlases = sorted(atlas_dir.glob("*.png"))
    print(f"Auditing {len(atlases)} atlases in {atlas_dir}")
    if args.dry_run:
        print("  (dry-run mode -- no files will be moved)")

    results = []
    for i, atlas_path in enumerate(atlases):
        stem = atlas_path.stem
        try:
            atlas_np = np.array(Image.open(atlas_path).convert("L"), dtype=np.uint8)
        except Exception as e:
            failed_rec = {"name": "image_load", "passed": False, "detail": {"error": str(e)}}
            results.append({
                "font_name": stem, "passed": False, "font_found": False,
                "checks": [failed_rec],
                "failed_checks": [{"name": "image_load", "detail": {"error": str(e)}}],
            })
            continue

        font_path = _find_font(stem, args.font_dir)
        if font_path:
            qr = score_font(font_path, atlas_np=atlas_np, early_exit=False)
        else:
            # No font file found -- run atlas-level checks only
            checks = []
            failed = []
            for check_fn in ATLAS_CHECKS:
                r = check_fn(atlas_np)
                checks.append(r)
                if not r.passed:
                    failed.append(r)
            qr = QualityResult(
                passed=len(failed) == 0, font_name=stem,
                checks=checks, failed=failed,
            )

        results.append({
            "font_name": stem,  # use atlas stem, not TTF stem
            "passed": qr.passed,
            "font_found": font_path is not None,
            "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail}
                        for c in qr.checks],
            "failed_checks": [{"name": c.name, "detail": c.detail}
                               for c in qr.failed],
        })

        if (i + 1) % 100 == 0:
            n_fail = sum(1 for r in results if not r["passed"])
            print(f"  [{i+1}/{len(atlases)}] {n_fail} rejected so far")

    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]
    n_no_font = sum(1 for r in results if not r["font_found"])
    print(f"\nResults: {len(passed)} passed, {len(failed)} rejected")
    print(f"  ({n_no_font} fonts not found in --font-dir, atlas-only checks used)")

    # Per-check breakdown
    check_counts = Counter()
    for r in failed:
        for c in r["failed_checks"]:
            check_counts[c["name"]] += 1
    if check_counts:
        print("\nRejection reasons:")
        for name, count in check_counts.most_common():
            print(f"  {name}: {count}")

    # Move rejected files and create quarantine dirs (unless dry-run)
    if not args.dry_run:
        q_atlas = quarantine_dir / "atlases"
        q_ref = quarantine_dir / "references"
        q_atlas.mkdir(parents=True, exist_ok=True)
        q_ref.mkdir(parents=True, exist_ok=True)
        moved = 0
        for r in failed:
            stem_name = r["font_name"]
            for src, dst_dir in [
                (atlas_dir / f"{stem_name}.png", q_atlas),
                (atlas_dir / f"{stem_name}.txt", q_atlas),
                (ref_dir / f"{stem_name}.png", q_ref),
            ]:
                if src.exists():
                    dst = dst_dir / src.name
                    if dst.exists():
                        print(f"  WARNING: {dst.name} already in quarantine, skipping")
                    else:
                        shutil.move(str(src), str(dst))
                        moved += 1
        print(f"\nMoved {moved} files to {quarantine_dir}")

    # Write reports — to dataset_dir on dry-run, quarantine_dir otherwise
    report_dir = dataset_dir if args.dry_run else quarantine_dir
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / "report.json"
    with open(report_path, "w") as f:
        json.dump({
            "total": len(results), "passed": len(passed),
            "rejected": len(failed), "fonts_not_found": n_no_font,
            "fonts": results,
        }, f, indent=2)
    print(f"Report: {report_path}")

    # Write HTML report
    if args.dry_run:
        def img_src(stem_name, kind):
            if kind == "atlas":
                return atlas_dir / f"{stem_name}.png"
            return ref_dir / f"{stem_name}.png"
    else:
        q_atlas_dir = quarantine_dir / "atlases"
        q_ref_dir = quarantine_dir / "references"
        def img_src(stem_name, kind):
            if kind == "atlas":
                q = q_atlas_dir / f"{stem_name}.png"
                return q if q.exists() else atlas_dir / f"{stem_name}.png"
            q = q_ref_dir / f"{stem_name}.png"
            return q if q.exists() else ref_dir / f"{stem_name}.png"

    html = _build_html_report(results, img_src)
    html_path = report_dir / "report.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Visual report: {html_path}")


if __name__ == "__main__":
    main()
