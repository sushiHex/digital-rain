"""Build font atlas training dataset for LoRA training.

Renders (Rgo reference, full atlas) pairs from TTF/OTF fonts with:
  - Proper baseline alignment (shared baseline per row, not centered per cell)
  - Per-font style captions extracted from font metadata
  - Horizontal flip augmentation (doubles effective dataset)

Reference: 1280x1280, 2-column Rg layout (white on black)
Atlas: 1280x1280, 12x8 grid of 95 printable ASCII chars (white on black)

Usage:
  python build_dataset.py --font-dir google-fonts --output-dir dataset_v2 --limit 2000
  python build_dataset.py --font-dir google-fonts --output-dir dataset_v2 --limit 2000 --augment-flip
"""
import argparse
import json
import os
from pathlib import Path

import numpy as np
from numpy.linalg import norm as np_norm
from PIL import Image, ImageDraw, ImageFont

from atlas_constants import CHARSET, GRID_COLS, GRID_ROWS, CANVAS, load_truetype_pinned

# Characters drawn into the reference IMAGE. The training corpus (dataset_v2)
# was built with "Rg" -- verified physically, not just from this constant:
# every sampled dataset_v2/references/*.png shows R+g.
#
# Do not confuse with eval_checkpoint.py's --reference-chars, which only sets
# the prompt LABEL and is (historically) "Kg". Training was internally
# inconsistent that way -- image Rg, prompt "Kg" -- and measurement showed the
# reference glyph's identity does not matter (p=0.625, median delta 0.000).
# See research/2026-07-28-reference-char-mismatch.md.
REF_CHARS = "Rg"
REF_COLS = 2

# Baseline position as fraction from top of cell (0.72 gives room for ascenders + descenders)
BASELINE_RATIO = 0.72


def _get_font_style(font_path):
    """Extract style descriptor from font metadata.
    Returns something like 'bold sans-serif italic' or 'regular serif'.
    """
    try:
        from fontTools.ttLib import TTFont
        tt = TTFont(str(font_path), fontNumber=0)
        os2 = tt['OS/2']

        # Weight
        wc = os2.usWeightClass
        weights = {
            100: 'thin', 200: 'extra-light', 300: 'light', 400: 'regular',
            500: 'medium', 600: 'semi-bold', 700: 'bold', 800: 'extra-bold', 900: 'black'
        }
        weight = weights.get(wc, weights.get(round(wc / 100) * 100, 'regular'))

        # Italic
        italic = 'italic' if (os2.fsSelection & 0x01) else ''

        # Serif classification from Panose
        panose = os2.panose
        if panose.bFamilyType == 2:
            if panose.bSerifStyle >= 11:  # 11-14 are sans-serif variants
                category = 'sans-serif'
            else:
                category = 'serif'
        elif panose.bFamilyType == 3:
            category = 'script'
        elif panose.bFamilyType == 4:
            category = 'decorative'
        else:
            category = ''

        # Width
        width_map = {1: 'ultra-condensed', 2: 'extra-condensed', 3: 'condensed',
                     4: 'semi-condensed', 5: '', 6: 'semi-expanded', 7: 'expanded',
                     8: 'extra-expanded', 9: 'ultra-expanded'}
        width = width_map.get(os2.usWidthClass, '')

        # Monospace detection
        post = tt.get('post')
        mono = 'monospace' if (post and post.isFixedPitch) else ''

        parts = [p for p in [weight, width, category, mono, italic] if p and p != 'regular']
        tt.close()
        return ' '.join(parts) if parts else 'regular'
    except Exception:
        return ''


def _make_caption(style_desc):
    """Build training caption. Uses the structured prompt from atlas_constants."""
    from atlas_constants import make_prompt
    return make_prompt(REF_CHARS)


def font_supports_charset(font_path):
    """Check if a font supports all required characters AND passes quality checks.

    Uses font_quality.py for blocklist, small-caps, cmap, and visibility checks.
    Keeps the fast PIL bbox check as the first gate (cheapest).
    """
    from font_quality import (check_blocklist, check_small_caps,
                              check_cmap_coverage, check_render_visibility)

    font_path = Path(font_path)

    # 1. Blocklist (instant, regex only)
    if not check_blocklist(font_path).passed:
        return False

    # 2. Fast PIL bbox check (original, cheap)
    try:
        font = ImageFont.truetype(str(font_path), 40)
        for ch in CHARSET:
            if ch == ' ':
                continue
            bbox = font.getbbox(ch)
            if bbox is None or (bbox[2] - bbox[0]) < 1:
                return False
    except Exception:
        return False

    # 3. cmap coverage (fontTools, slightly more expensive)
    if not check_cmap_coverage(font_path).passed:
        return False

    # 4. Render visibility
    if not check_render_visibility(font_path).passed:
        return False

    # 5. Small-caps detection (most expensive font-level check)
    if not check_small_caps(font_path).passed:
        return False

    return True


def _raw_truetype_loader(font_path, size):
    """Open a face with no variable-axis pinning at all.

    The convention dataset_v2 was actually built with -- verified, not assumed:
    a plain render of Doto[ROND,wght] is byte-identical to its corpus atlas,
    while load_truetype_pinned's "Regular" render differs by 17.6/255.
    """
    return ImageFont.truetype(str(font_path), size)


def render_reference(font_path, size=CANVAS, loader=None):
    """Render Rg in 2 columns at the SAME font size with shared baseline.

    All characters use one font size (determined by the widest/tallest),
    preserving natural proportions: R is taller than g and o, g has a
    descender, o shows x-height. This proportional relationship is
    critical style information for the model.

    `loader(font_path, size) -> ImageFont` overrides how the face is opened.
    **A caller pinning variable-font axes must pass it here as well as to
    render_atlas.** This function opens the face directly rather than through
    load_truetype_pinned, so swapping that global -- as the expansion tooling
    briefly did -- pins the atlas and leaves the reference at the default
    instance. That produced a dataset whose instanced pairs all shared one
    byte-identical reference while their atlases differed, i.e. "same
    reference, different style", the exact inverse of the training signal.

    The default is deliberately ImageFont.truetype rather than
    load_truetype_pinned: dataset_v2's 925 references were rendered that way
    and changing it would silently re-render the corpus.
    """
    loader = loader or (lambda p, s: ImageFont.truetype(str(p), s))
    img = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(img)

    cell_w = size // REF_COLS

    # Find ONE font size that fits ALL characters within their cells
    max_w_target = int(cell_w * 0.80)
    max_h_target = int(size * 0.45)

    lo, hi = 10, 800
    while lo < hi:
        mid = (lo + hi + 1) // 2
        font = loader(font_path, mid)
        fits = True
        for ch in REF_CHARS:
            bbox = font.getbbox(ch)
            if (bbox[2] - bbox[0]) > max_w_target or (bbox[3] - bbox[1]) > max_h_target:
                fits = False
                break
        if fits:
            lo = mid
        else:
            hi = mid - 1

    font = loader(font_path, lo)
    ascent, descent = font.getmetrics()

    # Shared baseline at 60% from top of canvas
    baseline_y = int(size * 0.60)

    for idx, ch in enumerate(REF_CHARS):
        cx = idx * cell_w

        # Vertical: align on shared baseline
        draw_y = baseline_y - ascent

        # Horizontal: center in column
        bbox = font.getbbox(ch)
        if bbox is None:
            continue
        ch_w = bbox[2] - bbox[0]
        draw_x = cx + (cell_w - ch_w) // 2 - bbox[0]

        draw.text((draw_x, draw_y), ch, fill=255, font=font)

    return img


def render_atlas(font_path, size=CANVAS, loader=None):
    """Render 12x8 atlas with proper baseline alignment and no cell overflow.

    `loader(font_path, size) -> ImageFont` overrides how the face is opened, so
    a caller can pin variable-font axes. Pass the SAME loader to
    render_reference(), or the pair will disagree — see its docstring.
    """
    loader = loader or load_truetype_pinned
    img = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(img)

    cell_w = size // GRID_COLS  # 106px
    cell_h = size // GRID_ROWS  # 160px

    # Find font size that fits the WIDEST character within cell width
    # AND the tallest within cell height. Both constraints must be satisfied.
    # Test against widest chars: M, W, @, %, #
    test_chars = "MW@%#"
    max_w_target = int(cell_w * 0.85)  # 85% of cell width max
    max_h_target = int(cell_h * 0.60)  # 60% of cell height for cap height

    lo, hi = 10, 200
    while lo < hi:
        mid = (lo + hi + 1) // 2
        font = loader(font_path, mid)

        # Check height constraint (cap height)
        h_bbox = font.getbbox("H")
        cap_h = h_bbox[3] - h_bbox[1]

        # Check width constraint (widest character)
        max_w = 0
        for tc in test_chars:
            try:
                w_bbox = font.getbbox(tc)
                max_w = max(max_w, w_bbox[2] - w_bbox[0])
            except Exception:
                pass

        if cap_h <= max_h_target and max_w <= max_w_target:
            lo = mid
        else:
            hi = mid - 1

    font = loader(font_path, lo)
    ascent, descent = font.getmetrics()

    for idx, ch in enumerate(CHARSET):
        if ch == ' ':
            continue

        row = idx // GRID_COLS
        col = idx % GRID_COLS
        cx = col * cell_w
        cy = row * cell_h

        # Baseline position: consistent within each row
        baseline_y = cy + int(cell_h * BASELINE_RATIO)
        draw_y = baseline_y - ascent

        # Horizontal centering within cell (clamped to cell bounds)
        bbox = font.getbbox(ch)
        if bbox is None:
            continue
        ch_w = bbox[2] - bbox[0]
        draw_x = cx + (cell_w - ch_w) // 2 - bbox[0]

        # Clamp: ensure character doesn't exceed cell boundaries
        draw_x = max(cx + 2, min(draw_x, cx + cell_w - ch_w - 2))

        draw.text((draw_x, draw_y), ch, fill=255, font=font)

    return img


# Licences that permit BOTH training on a font and redistributing the
# derivative fonts this model produces. Anything else -- unknown, CC-BY-NC
# (non-commercial), GPL (copyleft, font exception must be read), or a
# vendor-supplied rendering-only licence -- is not enough for this project.
PERMISSIVE_LICENCES = {"OFL-1.1", "OFL", "Apache-2.0", "UFL", "MIT"}


def load_provenance_stems(manifest="font_pool/source_manifest.json",
                          permissive_only=True):
    """Stems the fetch manifest records, optionally only the usable ones.

    Recording a licence is not the same as having an acceptable one: the pool
    contains 4 CC-BY-NC fonts (non-commercial), 2 GPL, and 1 whose repository
    states no licence at all. All are properly manifested and none may be
    trained on for a product that distributes its outputs.
    """
    if not os.path.isfile(manifest):
        return None
    with open(manifest, encoding="utf-8") as f:
        entries = json.load(f)
    return {os.path.splitext(e["filename"])[0].lower() for e in entries
            if not permissive_only or e.get("license") in PERMISSIVE_LICENCES}


def find_fonts(font_dir, limit=None, require_provenance=True,
               manifest="font_pool/source_manifest.json", permissive_only=True):
    """Find fonts with full ASCII support. Returns all passing fonts.

    REFUSES fonts that have no entry in the fetch manifest, because that is
    exactly how this corpus acquired an undocumented 13%.

    `pipeline/fetch_fonts.py` records source, licence and origin for every font
    it copies -- including via its `directory` adapter. 121 of the 925 training
    fonts have no manifest entry at all, meaning they were copied straight into
    the scanned folder, bypassing the only thing that writes provenance. Among
    them were 48 vendor-supplied Windows faces and 36 Fontshare closed-source
    fonts whose licence forbids redistributing derivative works.

    The defect was never the licences. It was that a path existed to add a font
    without recording where it came from. This closes that path.
    See research/2026-08-08-identifying-the-undocumented-13-percent.md.
    """
    font_dir = Path(font_dir)
    all_fonts = []
    for ext in [".ttf", ".otf"]:
        all_fonts.extend(font_dir.rglob(f"*{ext}"))

    known = (load_provenance_stems(manifest, permissive_only=permissive_only)
             if require_provenance else None)
    if require_provenance and known is None:
        raise SystemExit(
            f"provenance manifest {manifest} is missing, so no font's licence can "
            "be established. Build the pool with pipeline/fetch_fonts.py, or pass "
            "--allow-unprovenanced to accept an unauditable corpus.")

    valid, unprovenanced = [], []
    for fp in sorted(all_fonts):
        if known is not None and fp.stem.lower() not in known:
            unprovenanced.append(fp)
            continue
        if font_supports_charset(fp):
            valid.append(fp)
            if limit and len(valid) >= limit:
                break

    if unprovenanced:
        shown = ", ".join(p.name for p in unprovenanced[:8])
        what = ("no manifest entry, or a licence that does not permit "
                "redistributing derivatives" if permissive_only
                else "no manifest entry")
        print(f"  REFUSED {len(unprovenanced)} font(s) with {what}: "
              f"{shown}{' ...' if len(unprovenanced) > 8 else ''}")
        print("  Add them through pipeline/fetch_fonts.py so their source and "
              "licence are recorded, and check the licence is one of "
              f"{sorted(PERMISSIVE_LICENCES)}.")
    return valid


def main():
    parser = argparse.ArgumentParser(description="Build font atlas training dataset")
    parser.add_argument("--font-dir", required=True)
    parser.add_argument("--allow-unprovenanced", action="store_true",
                        help="accept fonts with no entry in the fetch manifest. This "
                             "is how the corpus acquired an undocumented 13%% "
                             "including 84 fonts that forbid redistributing "
                             "derivatives -- only for reproducing old datasets.")
    parser.add_argument("--output-dir", default="dataset_v2")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--canvas", type=int, default=CANVAS)
    parser.add_argument("--augment-flip", action="store_true", help="Add horizontally flipped copies")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--quarantine-dir", default=None,
                        help="Directory for rejected fonts (default: {output-dir}/quarantine)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    quarantine_dir = Path(args.quarantine_dir) if args.quarantine_dir else output_dir / "quarantine"
    ref_dir = output_dir / "references"
    atlas_dir = output_dir / "atlases"
    ref_dir.mkdir(parents=True, exist_ok=True)
    atlas_dir.mkdir(parents=True, exist_ok=True)

    print(f"Scanning {args.font_dir}...")
    fonts = find_fonts(args.font_dir, limit=args.limit,
                       require_provenance=not args.allow_unprovenanced)
    print(f"Found {len(fonts)} fonts with full ASCII support")

    if not fonts:
        return

    pairs = []
    fingerprints = []  # cached during render for dedup (avoids re-reading from disk)
    styles_found = {"serif": 0, "sans-serif": 0, "mono": 0, "other": 0}

    for i, font_path in enumerate(fonts):
        name = font_path.stem.replace(" ", "_")
        try:
            # Extract style metadata
            style_desc = _get_font_style(font_path)

            # Track diversity
            if "sans-serif" in style_desc:
                styles_found["sans-serif"] += 1
            elif "serif" in style_desc:
                styles_found["serif"] += 1
            elif "monospace" in style_desc:
                styles_found["mono"] += 1
            else:
                styles_found["other"] += 1

            # Render BOTH halves through ONE loader. The two functions have
            # different defaults -- render_atlas pins to the "Regular" named
            # instance, render_reference opens the face raw at axis defaults --
            # so calling them bare gives a VARIABLE font an atlas from one
            # instance and a reference from another. The reference is the
            # style-conditioning input the model is trained to copy, so that
            # pair teaches "this reference -> a different style".
            #
            # `pair_loader` is the raw open, because that is empirically what
            # dataset_v2's 925 atlases were built with: a plain
            # ImageFont.truetype render of Doto[ROND,wght] is byte-identical to
            # dataset_v2/atlases/Doto[ROND,wght].png, while the pinned render
            # differs by 17.6/255. Anything added to that corpus must match it.
            pair_loader = _raw_truetype_loader
            ref_img = render_reference(font_path, size=args.canvas, loader=pair_loader)
            atlas_img = render_atlas(font_path, size=args.canvas, loader=pair_loader)

            # Atlas quality gate (font-level already passed in find_fonts)
            from font_quality import ATLAS_CHECKS
            atlas_np = np.array(atlas_img, dtype=np.uint8)
            _checks = []
            _failed = []
            for _fn in ATLAS_CHECKS:
                _r = _fn(atlas_np)
                _checks.append(_r)
                if not _r.passed:
                    _failed.append(_r)
            if _failed:
                q_ref = quarantine_dir / "references"
                q_atlas = quarantine_dir / "atlases"
                q_ref.mkdir(parents=True, exist_ok=True)
                q_atlas.mkdir(parents=True, exist_ok=True)
                ref_img.save(str(q_ref / f"{name}.png"))
                atlas_img.save(str(q_atlas / f"{name}.png"))
                reasons = ", ".join(c.name for c in _failed)
                print(f"  QUARANTINE {font_path.stem}: {reasons}")
                continue

            # Save original (clean up partial writes on failure)
            ref_path = ref_dir / f"{name}.png"
            atlas_path = atlas_dir / f"{name}.png"
            caption_path = atlas_dir / f"{name}.txt"

            try:
                ref_img.save(str(ref_path))
                atlas_img.save(str(atlas_path))
                caption_path.write_text(_make_caption(style_desc))
            except Exception:
                # Clean up any partial writes to keep dataset consistent
                ref_path.unlink(missing_ok=True)
                atlas_path.unlink(missing_ok=True)
                caption_path.unlink(missing_ok=True)
                raise  # re-raise so the outer except catches it

            pairs.append((name, str(ref_path), str(atlas_path), style_desc))

            # Cache fingerprint for dedup
            fp_img = np.array(atlas_img.resize((64, 64)), dtype=np.float32).flatten() / 255.0
            fingerprints.append(fp_img)

            # Horizontal flip augmentation
            if args.augment_flip:
                flip_name = f"{name}_flip"
                ref_flip = ref_img.transpose(Image.FLIP_LEFT_RIGHT)
                atlas_flip = atlas_img.transpose(Image.FLIP_LEFT_RIGHT)

                flip_ref_path = ref_dir / f"{flip_name}.png"
                flip_atlas_path = atlas_dir / f"{flip_name}.png"
                flip_caption_path = atlas_dir / f"{flip_name}.txt"

                try:
                    ref_flip.save(str(flip_ref_path))
                    atlas_flip.save(str(flip_atlas_path))
                    flip_caption_path.write_text(_make_caption(style_desc))
                except Exception:
                    flip_ref_path.unlink(missing_ok=True)
                    flip_atlas_path.unlink(missing_ok=True)
                    flip_caption_path.unlink(missing_ok=True)
                    raise

                pairs.append((flip_name, str(flip_ref_path),
                             str(flip_atlas_path), style_desc))

                # Cache fingerprint for flip (mirrored, same content similarity as original)
                fp_flip = np.array(atlas_flip.resize((64, 64)), dtype=np.float32).flatten() / 255.0
                fingerprints.append(fp_flip)

            if (i + 1) % 100 == 0 or i == 0:
                print(f"  [{i+1}/{len(fonts)}] {font_path.stem} ({style_desc})")

        except Exception as e:
            print(f"  SKIP {font_path.stem}: {e}")

    # Deduplicate: remove fonts that render nearly identical atlases
    if len(pairs) > 1:
        print(f"\nDeduplicating {len(pairs)} fonts...")

        # fingerprints already cached during render loop
        assert len(fingerprints) == len(pairs), f"Fingerprint count mismatch: {len(fingerprints)} vs {len(pairs)}"

        vecs = np.array(fingerprints)
        norms = np_norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1
        vecs_norm = vecs / norms

        keep = set(range(len(pairs)))
        for i in range(len(pairs)):
            if i not in keep:
                continue
            for j in range(i + 1, len(pairs)):
                if j not in keep:
                    continue
                # Don't compare a font with its own flip
                name_i = pairs[i][0]
                name_j = pairs[j][0]
                if name_i + "_flip" == name_j:
                    continue
                if np.dot(vecs_norm[i], vecs_norm[j]) > 0.995:
                    keep.discard(j)
                    # Remove duplicate files
                    Path(pairs[j][1]).unlink(missing_ok=True)
                    Path(pairs[j][2]).unlink(missing_ok=True)
                    caption_path = Path(pairs[j][2]).with_suffix('.txt')
                    caption_path.unlink(missing_ok=True)

        removed = len(pairs) - len(keep)
        pairs = [pairs[i] for i in sorted(keep)]
        print(f"  Removed {removed} near-duplicates, {len(pairs)} unique fonts remain")

    print(f"\nDataset: {len(pairs)} pairs")
    print(f"Style distribution: {styles_found}")
    print(f"  References: {ref_dir}")
    print(f"  Atlases: {atlas_dir}")

    # Manifest
    with open(output_dir / "manifest.txt", "w") as f:
        for name, ref, atlas, style in pairs:
            f.write(f"{name}\t{ref}\t{atlas}\t{style}\n")

    if args.preview and pairs:
        _build_preview(pairs[:20], output_dir)


def _build_preview(pairs, output_dir):
    import base64

    rows = []
    for name, ref_path, atlas_path, style in pairs:
        with open(ref_path, "rb") as f:
            ref_b64 = base64.b64encode(f.read()).decode()
        with open(atlas_path, "rb") as f:
            atlas_b64 = base64.b64encode(f.read()).decode()
        rows.append(
            f'<div style="display:flex;gap:8px;margin:8px 0;align-items:center">'
            f'<span style="width:180px;font-size:12px;color:#888">{name}</span>'
            f'<span style="width:180px;font-size:11px;color:#e94560">{style}</span>'
            f'<img src="data:image/png;base64,{ref_b64}" style="width:128px;height:128px;border:1px solid #333">'
            f'<img src="data:image/png;base64,{atlas_b64}" style="width:256px;height:256px;border:1px solid #333">'
            f'</div>'
        )

    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Dataset Preview</title>'
        '<style>body{background:#111;color:#eee;font-family:system-ui;padding:20px}'
        'h1{color:#e94560}</style></head><body>'
        f'<h1>Training Dataset ({len(pairs)} samples)</h1>'
        f'<p style="color:#888">Reference: Rg 2-column | Atlas: 12x8, 95 ASCII, baseline-aligned</p>'
        + "\n".join(rows)
        + '</body></html>'
    )

    with open(output_dir / "preview.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Preview: {output_dir / 'preview.html'}")


if __name__ == "__main__":
    main()
