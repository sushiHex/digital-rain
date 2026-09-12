# Font Glyph Post-Processing Techniques

Research report: 2026-04-02 | Post-processing pipeline for AI-generated font quality improvement

---

## 1. Detecting and Fixing Inconsistent Stroke Widths

### Problem

AI-generated glyphs frequently exhibit non-uniform stroke widths -- stems that should be identical (e.g., the two verticals in H) differ by several units, or thick/thin contrast ratios vary unpredictably across the character set.

### Detection: Medial Axis Transform (MAT)

The most reliable programmatic approach uses rasterization + medial axis skeletonization to measure local stroke thickness.

**Pipeline:**

1. **Rasterize** the glyph outline to a high-resolution binary image (e.g., 1000x1000 px for a 1000 UPM font)
2. **Compute medial axis** with skimage.morphology.medial_axis(image, return_distance=True) -- returns skeleton pixels + distance to nearest boundary at each skeleton point
3. **Stroke width = 2 * distance** at each skeleton pixel (distance is radius to boundary)
4. **Aggregate per-stroke**: cluster skeleton pixels into connected segments, compute mean/median/stddev width per segment
5. **Cross-glyph comparison**: compare stem widths of H, I, l, d, b etc. -- these should match within tolerance

**Key tools:**
- scikit-image: medial_axis(), skeletonize() (Lee algorithm preferred for glyph shapes)
- fontTools.pens.t2Pen or reportlab for rasterizing outlines to images
- Pillow / numpy for image manipulation

**Alternative (vector-based):** For CFF/PostScript outlines, measure distances between parallel contour segments at known anatomical points (stem midpoints). More precise but requires contour topology analysis. The fontTools.pens.pointPen can extract raw point data for this.

### Fixing Strategy

1. **Define target stem widths** from reference glyphs (usually H vertical stem = primary stem width, O thinnest point = thin stroke width)
2. **Classify each stroke** as stem (thick) or hairline (thin) based on MAT measurements
3. **Scale contour segments** to match targets -- this requires careful interpolation:
   - Identify the two contour edges forming a stroke
   - Shift the wrong edge to achieve target width while preserving the stroke center
   - Use fontTools.pens.transformPen.TransformPen for affine transforms on sub-paths

### Statistical Detection with fontTools

fontTools.pens.statisticsPen.StatisticsPen computes per-glyph:
- **area** (signed, negative if clockwise contours)
- **meanX, meanY** (center of mass)
- **varianceX, varianceY, stddevX, stddevY** (spread metrics)
- **covariance, correlation** (shape skew)
- **slant** (derived from covariance/variance)

Use stddevX across similar glyphs (e.g., all lowercase) as a proxy for width consistency. Outliers indicate glyphs with anomalous stroke distributions.

fontTools.pens.areaPen.AreaPen uses the shoelace formula for linear segments and Bezier-specific formulas for quadratic/cubic curves. Area-to-perimeter ratios can estimate average stroke weight.

---

## 2. Normalizing X-Height and Cap-Height Alignment

### Problem

AI-generated glyphs may have inconsistent vertical alignment -- some lowercase letters overshoot the x-height line, others undershoot it, and uppercase letters may not share a consistent cap-height.

### Detection

1. **Extract bounding boxes** for all glyphs using fontTools.pens.boundsPen.BoundsPen
2. **Measure reference characters:**
   - **x-height**: yMax of flat-top lowercase: x, z, v, w
   - **cap-height**: yMax of flat-top uppercase: H, I, E, F
   - **baseline**: yMin of flat-bottom characters: x, z, H
   - **descender line**: yMin of p, g, q, y
3. **Check consistency**: all flat-top lowercase should have identical yMax (within 1-2 units). Compute stddev across the set -- anything > 5 units at 1000 UPM is suspicious.

### Correction

**Vertical scaling per glyph:**

1. Calculate the correction factor: scale_y = target_xheight / actual_yMax
2. Apply using fontTools.pens.transformPen.TransformPen with matrix (1, 0, 0, scale_y, 0, dy) where dy adjusts baseline alignment
3. Re-round coordinates after transform

**Important**: after vertical scaling, re-run addExtrema() and simplify() to maintain outline quality.

### Metric Tables

Update the OS/2 table values to match corrected metrics:
- sxHeight -- x-height value
- sCapHeight -- cap-height value
- sTypoAscender, sTypoDescender -- typographic extents
- usWinAscent, usWinDescent -- clipping boundaries

FontBakery validates these: typoAscender - CapsHeight = abs(typoDescender) for balanced padding.

---

## 3. Auto-Correcting Optical Issues (Overshoot)

### Problem

Round characters (O, C, G, S, e, o, c, s, etc.) and pointed characters (A, V, W, v, w) must extend slightly beyond alignment lines (baseline, x-height, cap-height) to appear optically aligned. AI generators often fail to add this overshoot, or add it inconsistently.

### Overshoot Conventions

- **Typical overshoot**: 1-2% of UPM (10-20 units at 1000 UPM)
- **Consistency rule**: in digital fonts, all overshoots at a given zone should be identical to avoid hinting rounding errors
- **Characters requiring overshoot at baseline**: O, C, G, Q, S, e, o, c, s, and any character with a curved or pointed bottom
- **Characters requiring overshoot at x-height/cap-height**: O, C, G, S, A, V, W (top), e, o, c, s (top)

### Detection

1. Measure yMax/yMin of reference flat characters to establish alignment lines
2. Measure yMax/yMin of round/pointed characters
3. Compare: overshoot = yMax(round) - yMax(flat). If less than 50% of expected overshoot, flag as missing.

### Correction

1. **Identify extrema points** at the top/bottom of round contours
2. **Shift only those points** (and neighboring control points) by the missing overshoot amount
3. Alternatively, apply a **non-uniform vertical scale** to just the top/bottom portion of the glyph

### Storage in Font Files

Overshoot values are stored as alignment zones for hinting:
- **CFF/OTF**: BlueValues and OtherBlues in the CFF Private Dict
- **TTF**: cvt (Control Value Table)

These zones tell the rasterizer where overshoots exist so it can suppress them at small pixel sizes.

---

## 4. Tools for Automatic Glyph Outline Cleanup

### fontTools (Python, Primary Recommendation)

The core library for font manipulation. Key modules for post-processing:

| Module | Purpose |
|--------|--------|
| fontTools.ttLib.removeOverlaps | Merge overlapping contours via skia-pathops |
| fontTools.pens.transformPen | Affine transforms on outlines |
| fontTools.pens.statisticsPen | Area, center of mass, variance, slant |
| fontTools.pens.areaPen | Signed area calculation (shoelace formula) |
| fontTools.pens.boundsPen | Bounding box computation |
| fontTools.pens.pointPen | Raw point-level access for contour surgery |
| fontTools.pens.recordingPen | Record and replay drawing operations |

**removeOverlaps API:**

The primary function signature is:
- removeOverlaps(font, glyphNames=None, removeHinting=True, ignoreErrors=False, removeUnusedSubroutines=True)
- font: a TTFont object
- glyphNames: iterable of glyph names, or None for all glyphs
- removeHinting: simplified glyphs lose hinting data; True removes all hinting for consistency
- The implementation decomposes composite glyphs only if components overlap, processes simple glyphs before complex ones, and has a fallback that rounds float coordinates to integers if pathops fails

Requires skia-pathops. Falls back to integer rounding if float coords cause failures.

### FontForge (Python scripting)

Full glyph-level cleanup suite accessible via Python:

| Method | Purpose |
|--------|--------|
| glyph.simplify(error, flags) | Remove excess points within error tolerance |
| glyph.removeOverlap() | Boolean union of overlapping contours |
| glyph.addExtrema() | Add on-curve points at curve extrema |
| glyph.correctDirection() | Fix contour winding (outer=CW, inner=CCW) |
| glyph.canonicalContours() | Order contours by leftmost x-coordinate |
| glyph.canonicalStart() | Set contour start to leftmost point |
| glyph.round(factor) | Round coordinates to grid |
| glyph.cluster(within, max) | Snap nearby coordinates to common values |
| glyph.autoHint() | Generate PostScript hints |
| glyph.autoInstr() | Generate TrueType instructions |

**Simplify flags**: ignoreslopes, ignoreextrema, smoothcurves, choosehv, forcelines, nearlyhvlines, mergelines, setstarttoextremum, removesingletonpoints

### fontmake / ufo2ft (Google Fonts pipeline)

The production font build system with a two-pass filter architecture:

**Preprocessing pass** (on UFO sources):
- DecomposeComponents -- flatten component references
- FlattenComponents -- resolve nested components
- RemoveOverlaps -- boolean union (backend: booleanOperations or skia-pathops)
- CubicToQuadratic -- convert cubic to quadratic curves for TTF via cu2qu
- ExplodeColorLayerGlyphs -- split color layers

**Postprocessing pass** (on compiled binaries):
- Glyph renaming to production names
- Subroutinization for CFF
- Custom filters injected via com.github.googlei18n.ufo2ft.filters lib key or --filter CLI flag

### FontBakery (Automated QA)

Validates font files against ~200 checks:
- Vertical metrics consistency across family members
- x-height and cap-height reasonableness
- Line spacing consistency
- Visual sizing relative to common fonts
- Contour direction and self-intersection detection

### skia-pathops

Python bindings for Skia boolean path operations:
- pathops.op -- union, intersection, difference, XOR
- pathops.simplify -- remove self-intersections and merge overlapping regions
- Used internally by fontTools.ttLib.removeOverlaps

### scikit-image (raster-based analysis)

- skimage.morphology.medial_axis -- skeleton + local width (with return_distance=True)
- skimage.morphology.skeletonize (method=lee) -- topological skeleton
- Required for stroke width measurement when vector analysis is insufficient

---

## 5. Recommended Post-Processing Pipeline

For this project, the recommended pipeline order:

1. OVERLAP REMOVAL -- fontTools removeOverlaps with skia-pathops backend
2. CONTOUR CLEANUP -- correctDirection, addExtrema, canonicalContours, canonicalStart
3. POINT SIMPLIFY -- FontForge simplify or manual point reduction
4. COORDINATE ROUNDING -- round to integer grid at 1 UPM unit
5. METRIC ALIGNMENT -- normalize x-height, cap-height, baseline across all glyphs
6. OVERSHOOT CHECK -- detect/add missing overshoots on round/pointed characters
7. STROKE CONSISTENCY -- MAT-based stroke width analysis + correction
8. HINTING -- autoHint for PS or autoInstr for TT
9. QA VALIDATION -- FontBakery checks

Steps 1-4 are mechanical cleanup. Steps 5-7 are optical quality. Step 8 is rendering optimization. Step 9 is verification.

For a Python-only implementation without FontForge dependency, all steps can be accomplished with fontTools + skia-pathops + scikit-image + fontbakery, though FontForge simplify is notably more capable than a pure fontTools approach for point reduction.

---

## Sources

- [fontTools documentation](https://fonttools.readthedocs.io/)
- [fontTools pens overview](https://fonttools.readthedocs.io/en/latest/pens/index.html)
- [fontTools StatisticsPen source](https://github.com/fonttools/fonttools/blob/main/Lib/fontTools/pens/statisticsPen.py)
- [fontTools AreaPen source](https://github.com/fonttools/fonttools/blob/main/Lib/fontTools/pens/areaPen.py)
- [fontTools removeOverlaps source](https://github.com/fonttools/fonttools/blob/main/Lib/fontTools/ttLib/removeOverlaps.py)
- [skia-pathops repository](https://github.com/fonttools/skia-pathops)
- [FontForge Python scripting API](https://fontforge.org/docs/scripting/python/fontforge.html)
- [fontmake architecture](https://deepwiki.com/googlefonts/fontmake)
- [fontmake usage](https://github.com/googlefonts/fontmake/blob/main/USAGE.md)
- [ufo2ft preProcessor source](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/preProcessor.py)
- [Google Fonts vertical metrics guide](https://googlefonts.github.io/gf-guide/metrics.html)
- [scikit-image skeletonize](https://scikit-image.org/docs/stable/auto_examples/edges/plot_skeleton.html)
- [Stroke Width Transform Python](https://github.com/sunsided/stroke-width-transform)
- [Monotype overshoot guidance](https://foundrysupport.monotype.com/hc/en-us/articles/360029597112-Lack-of-Overshoots)
- [FontForge: Creating o and n](http://designwithfontforge.com/en-US/Creating_o_and_n.html)
- [Overshoot - Wikipedia](https://en.wikipedia.org/wiki/Overshoot_(typography))
- [TypeDrawers: Under- and overshoot](https://typedrawers.com/discussion/4317/under-and-overshoot)
- [FontBakery vertical metrics](https://github.com/fonttools/fontbakery/issues/1487)
- [AI font generation challenges](https://trust.ilovetypography.com/fonts-and-ai/)
- [Stroke-based font generation](https://www.sciencedirect.com/science/article/abs/pii/S0957417424025247)
