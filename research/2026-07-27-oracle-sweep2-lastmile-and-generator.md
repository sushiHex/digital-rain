============================================================
## Chain A — Anderson Report
============================================================

# ANDERSON SYNTHESIS BRIEF — CHAIN A (10 SMITHS)
## Prepared for Opus Final Synthesis | Date: 2026-07-27

---

## PREFLIGHT NOTES

- **Smiths received:** #1 (HTLetterspacer), #2 (algorithmic sidebearings), #3 (automated kerning tools), #4 (fontspector), #5 (fontTools assembly pitfalls), #6 (outline cleanup), #7 (variable fonts from masters), #8 (OFL + ML training), #9 (AI font provenance/marketplace), #10 (non-Latin charset generation)
- **Dedup merges executed:** 6 (documented in Part II)
- **Corrections flagged:** 2 (one HIGH confidence, one MEDIUM)
- **Disputes flagged:** 1 genuine, 2 tension notes
- **Coverage gaps noted:** 12

---

---

# PART I — THEMATIC FINDINGS

---

## THEME 1 — HTLetterspacer: Algorithm, Configuration & Architecture

**Primary source:** Smith #1 | **Supporting:** Smith #2 (contextualizes as area-based approach)

### 1.1 Algorithm Overview
- **Type:** Polygon-area glyph spacing — NOT fixed-margin-based. Measures *visual white area* at vertical intervals; derives sidebearings to match a target area value.
- **Smith #1, HIGH**

### 1.2 Five-Step Engine Pipeline
1. **Vertical Scan** — Samples glyph outline at intervals controlled by `paramFreq` (default: **5 units**). Source: ARCHITECTURE.md + engine.py. **Smith #1, HIGH**
2. **White Space Calculation** — Shoelace formula: `area = abs(Σ(x[i]·y[i+1] − x[i+1]·y[i])) / 2`. Source: engine.py extraction. **Smith #1, HIGH**
3. **Depth Constraint** — `paramDepth` as percentage of x-height limits measurement penetration into open counters (prevents over-spacing of *c*, *e*, *r*). **Smith #1, HIGH**
4. **Sidebearing Derivation** — Solves for LSB/RSB values producing target white area. **Smith #1, HIGH**
5. **Italic Handling** — De-slants points for area math (requires axis-aligned geometry), then re-slants results. **Smith #1, HIGH**
6. **Component Preservation** — Maintains visual position of composites via topological reordering. Source: engine.py. **Smith #1, HIGH**

### 1.3 Configuration Parameters (Master-Level, stored under `com.htfonts.letterspacer`)

| Parameter | Default | Unit | Function | Confidence |
|-----------|---------|------|----------|------------|
| `paramArea` | **400** | thousand-units | Target white space per unit height (typical range 200–400 for text fonts) | HIGH |
| `paramDepth` | **15** | % of x-height | Max inward margin penetration | HIGH |
| `paramOver` | **0** | units | Vertical overshoot for ascenders/descenders | HIGH |
| `paramFreq` | **5** | units | Vertical measurement frequency | HIGH |

**Per-Rule Overrides:** Area & Depth support absolute values OR percentages of master defaults. Source: rules.py. **Smith #1, HIGH**

### 1.4 Rule System / Specificity Scoring

Glyphs matched by highest specificity score (highest wins):

| Filter Type | Points | Match Behavior |
|-------------|--------|----------------|
| Glyphlist | 8 | Direct name match |
| Category | 4 | Glyphs classification (uppercase/lowercase/etc.) |
| Script / Subcategory / Case | 2 each | Exact match only |
| Filter | 1 | Substring patterns; comma-separated alternatives |

Each rule specifies: Area, Depth, reference glyph (measuring zone), LSB/RSB toggles, fixed-width flag. Source: rules.py. **Smith #1, HIGH**

### 1.5 Storage & Configuration Formats
- Rules and parameters live in **font userData** (not sidecar files)
- Import/export: **.json** (recommended, v2 versioned format); legacy **.yml** and **.py** (backward compatible)
- **v1→v2 migration** flattens nested categories; "may not reproduce previous results exactly" per README
- Source: config.py + README. **Smith #1, HIGH**

### 1.6 Interface & Availability
- **NO standalone CLI or Python API outside Glyphs App**
- **NO fontTools port, NO UFO library, NO pip package** — Glyphs-only
- Interfaces: GUI rules editor + parameter tab; live preview reporter; helper scripts (*Apply HTLS Config*, *Apply HTLS Values*)
- GitHub issue #56 (closed Jan 9, 2021): Attempted UFO refactor; author noted compatibility issues with UFO's italic sidebearing measurement (differs from Glyphs.app's x-height-midline convention); marked resolved without public UFO release. **Smith #1, MEDIUM** (resolved but no artifact)

### 1.7 Requirements
- Glyphs 3 with Python enabled (primary); Glyphs 2 via manual script installation
- No external dependencies (self-contained plugin)
- **Smith #1, HIGH**

### 1.8 Repository Status & Activity
- **Repo:** github.com/huertatipografica/HTLetterspacer | **License:** GPL-3.0 code, CC BY 4.0 docs | **Org:** Huerta Tipográfica
- **Latest commit:** June 24, 2026 (README: License)
- **Key recent updates:** PR #61 (May 2026) — multi-master batch spacing script; bracket layer handling improvements (June 2026); reporter preview tuning (20-glyph cache limit)
- **Primary contributor:** Andrés Torresi (andrestelex); co-creators: Sebastian Carewe (eweracs, 2021–22), Juan del Peral (juandelperal, 2021)
- **Smith #1, HIGH** (fetched 2026-07-27)

### 1.9 Contextual Placement Among Spacing Algorithms
- Smith #2 independently classifies HTLetterspacer-style computation as an "Area/Optical-Center Approach" (alongside CounterSpace), contrasting it with Distance-Based and Systematic/Pattern-Based approaches. This confirms Smith #1's characterization.
- **Smiths #1 + #2, AGREE, HIGH**

---

## THEME 2 — Algorithmic Sidebearing Computation: Non-ML Survey

**Primary source:** Smith #2 | **Supporting:** Smith #1 (HTLetterspacer detail), Smith #3 (ML approaches overlap — see Dedup D-1)

### 2.1 Distance-Based Approaches

#### A. Character Overlap Analysis (Patent US5803629A)
- Analyzes multiple intersection zones through progressive bounding-box overlap at varying degrees until complete overlap
- Measures actual character overlap as percentage of character height across superposed regions
- **Authors:** Paul H. Neville, William J. Fox | **Date:** March 14, 1997 (USPTO)
- **Open implementation:** None found
- **Smith #2, HIGH**

#### B. TypeFacet Autokern (Charles M. Chen)
- Constructs "facade profiles" by inflating outlines at min/max distance thresholds (in ems)
- Min-distance profiles moved together until touching → "minimum advance"; max-distance profiles balanced for "intruding advance"
- **Status:** Free, open-source CLI Python tool | **Input:** UFO files | **Output:** kerning values + optional adjusted sidebearings
- Emphasis on designer transparency — every decision logged
- **Smith #2, MEDIUM** (algorithm details from manual/discussion posts, not primary code)

#### C. FontForge Auto-Spacing
- Preprocesses contours into edge-maps at multiple vertical regions (typically 1/100th of em-size per region)
- For each y-coordinate: extracts min/max x from contour data; computes weighted visual separation across regions
- **Status:** Open source (FontForge)
- **Smith #2, HIGH** (documented in official FontForge code/docs)

#### D. Distance Contours (Patent US5623593, US5937420)
- Generates contour lines at multiple distance units from character edges
- **Manhattan distance (city-block):** Von Neumann neighborhood, 2-pass raster scan
- **Euclidean distance:** Weighted neighbor contributions
- **Smith #2, MEDIUM** (from patent abstracts; implementation details sparse)

### 2.2 Area / Optical-Center Approaches

#### E. CounterSpace (Simon Cozens)
- Models counterspace as **influence field radiating from counter center** (not solid block)
- Uses Gaussian blur + convex hulls to measure influence intensity
- Calculates spacing by matching total influence intensity between reference and candidate glyph pairs
- **Status:** Experimental proof-of-concept | **Open source:** Yes (github.com/simoncozens/CounterSpace)
- **Accuracy:** 80–90% automated; remainder requires manual refinement
- **Smith #2, HIGH** (code available, peer-discussed on TypeDrawers)

#### F. HTLetterspacer (Huerta Tipográfica)
- [See Theme 1 for full detail]
- Shoelace-formula area measurement at vertical intervals; parameterized by Area, Depth, Freq, Over
- **Smiths #1 + #2, HIGH**

### 2.3 Systematic / Pattern-Based Approaches

#### G. LS Cadencer (Lukas Schneider, based on Frank Blokland PhD)
- Based on **Renaissance type systematization** principles (Gutenberg/Renaissance type production)
- Uses **stem-interval measurement** (typically from 'm' or 'n' glyph) to parameterize proportional spacing via spacing tables
- **PhD:** Frank Blokland, October 11, 2016, Leiden University ("Renaissance Standardisation, Systematisation, and Unitisation of Textura and Roman Type")
- **Implementation:** LS Cadencer & LS Cadenculator (Python extensions for RoboFont/GlyphsApp v2)
- **Open source:** Yes (Glyphs/RoboFont plugins) | **Site:** lettermodel.org, revolvertype.com/tools/cadencer.html
- **Smith #2, HIGH** (PhD dissertation + published tools)

#### H. BubbleKern (Toshi Omagari, 2015)
- Designer draws custom "bubble" outlines in a separate layer; algorithm kerns pairs by calculating overlap of bubble shapes
- **Clamp:** Maximum kerning adjustment = ½ of narrower glyph's width
- **Implementation:** Glyphs.app plugin | **Open source:** Yes (github.com/Tosche/BubbleKern)
- **Practical effectiveness:** 80–90% automated; 10–20% manual refinement
- **Smith #2, HIGH**

### 2.4 Commercial / Proprietary Approaches (Lower Confidence)

#### I. Adobe InDesign Optical Kerning
- Licensed from Hermann Zapf/URW hz-program algorithm (patented 1992)
- Analyzes character shapes for spacing; scales glyphs per justification settings; **size-specific** (optical scaling to point size)
- Derived from URW hz-program (Hermann Zapf + Peter Karow research, URW Software & Type GmbH, Hamburg; 1970s–1990s)
- **Smith #2, MEDIUM** (algorithm details proprietary)

#### J. FontLab 8 Optical Metrics
- Analyzes glyph shape; intelligently sets sidebearings. Method not disclosed.
- **Smith #2, LOW** (proprietary, limited technical documentation)

#### K. DTL KernMaster (Dutch Type Library)
- Converts glyphs to extremely high-resolution bitmaps; applies "sophisticated algorithms" for kerning; class kerning with kern.fea output
- **Smith #2, LOW** (vendor description sparse)

#### L. Roboto Flex SPAC (Google Fonts)
- Proportional tracking: fixed units added to all glyph margins; proportional scaling of margins; separate kerning sets per spacing state
- **Smith #2, MEDIUM** (documented demo; simpler than algorithmic spacing)

### 2.5 Historical Context
- **Peter Karow (URW, 1972–1990s):** Developed Ikarus system (1975) for digitizing type contours; published "Optical Scaling" (URW Verlag, 1991)
- **Smith #2, HIGH**

---

## THEME 3 — Automated Kerning Tools (Production & Experimental)

**Primary source:** Smith #3 | **Overlapping:** Smith #2 (ML approaches — see Dedup D-1)

### 3.1 Kern On (Tim Ahrens)
- **URL:** kern-on.com
- **Interface:** Glyphs plugin only (macOS) — NO CLI/API
- **Workflow:** Designer sets 5–10 model pairs → plugin learns patterns → auto-applies to entire font
- **Output:** Real glyph-pair GPOS kerning; optimizes for smaller GPOS tables (addresses 64KB overflow risk)
- **Kerning type:** Glyph-glyph pairs only (no class-based groups); auto-generates groups
- **Cost:** €199 one-time | **Trial:** 30-day free
- **Latest version:** 1.38 (released 2026-07-26, supports Glyphs 4) — most current tool in the survey
- **Prior versions:** v1.37 (2025-04-08), v1.36 (2025-03-23)
- **Smith #3, HIGH**

### 3.2 kernagic (Øyvind Kolås)
- **Interface:** Standalone GUI application; also has CLI (`kernagic --help`, `kernagic --ipsumat`)
- **Output:** UFO format only — modifies advance widths and left/right bearings (XML metrics); does **NOT** generate OpenType kern/GPOS features
- **Compilation step required:** Must pipe UFO through FontForge, afdko, or fontTools to get compiled font
- **Cost:** FREE (open source)
- **Last update:** 2019-03-27 (**6.4 years outdated as of 2026-07-27**)
- **Status:** Created 2013; maintained but not actively developed
- **Smith #3, HIGH**

### 3.3 atokern / Kerncritic (Simon Cozens)
- **Interface:** Python 3 CLI (`--left`, `--right` options; outputs word image discrimination results)
- **Output:** UNCLEAR — outputs kerning pairs with >70% confidence; format not explicitly documented; likely plain pairs (not FEA/GPOS)
- **Claimed accuracy:** 92% validation accuracy on training set
- **Known failure rate:** ~2% of pairs can be "completely wrong"
- **Cost:** FREE (open source, GitHub)
- **Status:** Research/experimental — NOT production-ready. Cozens: "basically had autokerning working, concept proven"
- Real bottleneck: training on larger variety of well-kerned fonts on more powerful hardware
- **Smith #3, MEDIUM** (output format unverified; accuracy from TypeDrawers discussion)
- **⚠️ Note:** This is a DIFFERENT Cozens tool from CounterSpace (spacing, Smith #2). Distinct products.

### 3.4 iKern (Igino Marini)
- **Type:** Service-based (font submitted to vendor) — not software download
- **Output:** Returns fully kerned OTF/TTF with GPOS kern feature
- **Cost:** NOT publicly listed — contact for quote (custom/per-project)
- **Algorithm:** Proprietary (Marini has not published methodology)
- **Customer base:** Google, major type foundries (since 2008)
- **Smith #3, HIGH** (existence/service model HIGH; algorithm MEDIUM-proprietary)

### 3.5 FontCreator (High-Logic)
- **Interface:** Integrated autokerning wizard (GUI; Home Edition excluded)
- **Output:** YES — exports OpenType GPOS kerning
- **Cost:** Commercial (30-day free trial)
- **Smith #3, HIGH**

### 3.6 FontLab 8
- **Interface:** Integrated autokerning in Kerning mode (GUI)
- **Output:** YES — "Create [kern] Feature" generates GPOS lookups from visual kerning
- **Cost:** Commercial (subscription)
- **Smith #3, HIGH**

### 3.7 2026 Market Summary (Smith #3 Assessment)
- **No production neural-kerning tool** exists: atokern experimental; "Learning to Kern" academic (no code release); no commercial ML kerning service
- **kernagic outputs spacing only** — does not generate OpenType features
- **Pricing opacity:** iKern custom-quote only; Kern On only transparent standalone tool (€199)
- **Only CLI kerning tool with any activity:** atokern (experimental)

| Tool | Real GPOS/Kern? | GUI | CLI/API | Cost | Status 2026 |
|------|----------------|-----|---------|------|-------------|
| Kern On | ✅ YES | ✅ | ❌ | €199 | Active (v1.38, Jul 2026) |
| kernagic | ❌ NO (UFO metrics only) | ✅ | ✅ | FREE | Unmaintained (2019) |
| atokern | ⚠️ UNCLEAR | ❌ | ✅ | FREE | Experimental |
| iKern | ✅ YES | N/A (service) | N/A | Custom | Service-based |
| FontCreator | ✅ YES | ✅ | ❌ | Commercial | Active |
| FontLab 8 | ✅ YES | ✅ | ❌ | Commercial | Active |

---

## THEME 4 — ML-Based Spacing & Kerning (Neural/Learning Approaches)

**Sources:** Smiths #2, #3 (MERGED — see Dedup D-1) | **Cross-reference:** Smith #10 (non-Latin ML synthesis)

### 4.1 "Learning to Kern: Set-wise Estimation of Optimal Letter Space" (Nakatsuru & Uchida)
*[Merged from Smith #2 and Smith #3 — see Dedup D-1]*
- **Paper:** arXiv 2402.14313 (v2 latest) | **Published:** ICDAR 2024 | **Submission:** February 22, 2024
- **Authors:** Kyushu University, Fukuoka, Japan
- **Two models:**
  - *Pairwise:* Deep NN; accepts two letter images; estimates spacing for pair
  - *Set-wise:* Transformer-based; accepts 3+ letter images; uses self-attention for consistency across all pairs — **superior to pairwise**
- **Performance:** Mean Absolute Error **5.318 pixels** (vs. average letter space ~115 pixels) across ~2,500 Google Fonts
- **Scale of problem:** 2,704 different spaces needed for 52 Latin letters (26 caps + 26 lowercase)
- **Open implementation:** NOT found/released as of 2026
- **No commercial tool released as of 2026**
- **Smiths #2 + #3, HIGH**

### 4.2 atokern / Kerncritic (Simon Cozens)
*[See Theme 3.3 for full production-tool detail; summarized here for ML context]*
- 92% validation accuracy claimed; 2% gross failures; research/experimental only
- **Smith #3, MEDIUM**

### 4.3 CounterSpace (Simon Cozens) — Spacing (not kerning)
*[See Theme 2.2-E for full detail]*
- Influence-field model; Gaussian blur + convex hull; 80–90% automated
- **Smith #2, HIGH**

---

## THEME 5 — Font Outline Cleanup & Assembly (Traced Glyphs)

**Primary sources:** Smiths #5 and #6 (MERGED throughout — see Dedup D-2, D-3, D-4)
**Scope:** Both Smiths address outline cleanup, but from different entry angles: Smith #5 focuses on image-tracing-specific failure modes in TTF/OTF assembly; Smith #6 covers the broader cleanup toolkit with library-level detail. Both are preserved in full.

### 5.1 Contour Winding & Direction

**Format conventions:**
- **TrueType (glyf):** Non-zero winding rule. Outer contours = clockwise (filled); inner = counter-clockwise (unfilled). Source: Microsoft OpenType Spec. **Smith #5, HIGH**
- **CFF/PostScript:** Outer contours = counter-clockwise; inner = clockwise. **Smith #5 states "even-odd rule" for CFF — see Correction C-1 below.**

**fontTools fix:**
- `ReverseContourPointPen` — reverses winding while keeping first point as starting point; handles closed contours only; components pass through unchanged
- Source: fontTools/pens/pointPen.py (commit a6568bb7) **Smith #5, HIGH**

**Image tracing issue:** Auto-trace tools collect points in arbitrary order → incorrect winding frequent. Explicit reversal required before TTF serialization. **Smith #5, HIGH**

### 5.2 Overlap Removal
*[Merged — see Dedup D-2]*

**Primary tool: skia-pathops**
- `simplify()` — traces overlapping contours; returns non-overlapping path describing same area
- Reduces curve order where possible (cubics→quadratics, quadratics→lines)
- Handles complex, self-intersecting polygons, holes, degenerate paths
- **Known Skia bug (#11958):** Float coordinate failure → retry with `_round_path()` (integer rounding). Workaround in fontTools. **Smiths #5 + #6, HIGH (both confirm)**

**fontTools pipeline (TrueType):**
1. `skPathFromGlyph()` — converts glyph to Skia path
2. `pathops.simplify(path, clockwise=path.clockwise)` — applies with winding fix
3. Integer retry if float fails (rare Skia bug)
4. `ttfGlyphFromSkPath()` or `T2CharStringPen` — convert back
- `RemoveOverlapsError` raised on failure; pass `ignoreErrors=True` to skip and keep originals
- **⚠️ Invalidates TrueType hinting when applied**
- Source: fontTools/ttLib/removeOverlaps.py (commit f324629) **Smith #5, HIGH**

**Alternative: booleanOperations library**
- Cython wrapper around pyclipper (Angus Johnson's C++ Clipper library)
- `BooleanOperationManager`: Union, Difference, Intersection, XOR
- **Algorithm:** Vatti polygon clipping via Clipper — scanbeams bottom-to-top; no full edge search needed
- Coordinate handling: Clipper uses integers; `scale_to_clipper()` / `scale_from_clipper()` helpers required
- **Smith #6, HIGH**

**fontmake behavior:** RemoveOverlaps called automatically in preprocessing pass; **skipped for variable fonts** to preserve interpolation. **Smith #6, HIGH**

**Usage snippet (Smith #5):**
```python
from fontTools.ttLib import TTFont
from fontTools.ttLib.removeOverlaps import removeOverlaps

font = TTFont("traced.ufo.ttf")
removeOverlaps(font, ignoreErrors=True, removeHinting=True)
font['maxp'].recalcMaxpValues(font['glyf'])
font['head'].recalcBoundingBox()
font.save("cleaned.ttf")
```

### 5.3 Extrema Points
*[Merged — see Dedup D-3]*

**Requirement:** TrueType and PostScript specs recommend on-curve points at all curve extrema (min/max x and y). Improves hinting accuracy, bounding box calculation, rendering consistency. **Smiths #5 + #6, HIGH (AGREE)**

**fontTools support:**
- `calcCubicBounds()` and `calcQuadraticBounds()` in `fontTools.misc.bezierTools` — calculate extrema per curve segment
- `dropImpliedOnCurvePoints()` in `_g_l_y_f.py` — opposite operation (point removal)
- `SegmentToPointPen` + `addPoint()` chain can inject extrema programmatically

**Critical gap (AGREE between Smiths #5 and #6):**
- **No dedicated `addExtrema()` function in fontTools core** — confirmed by both Smiths
- FontForge / FontLab have "Element → Add Extrema" but not ported to fontTools Python API
- Workarounds: custom filter pens; Cu2Qu conversion (side effect: may add control points near extrema); Bezier curve analysis to locate mathematically
- **Manual intervention typically required for production fonts**
- **Smiths #5 + #6, MEDIUM** (pattern common but not standardized; noted as documentation gap)

### 5.4 Off-Curve Point Limits

**TrueType hard limit:** 65,535 points per glyph (encoded in `maxp` as `uint16` for `maxPoints` and `maxContours`; `endPtsOfContours` uses 16-bit indices). Source: Microsoft OpenType Spec. **Smith #5, HIGH**

**CFF:** No equivalent hard point limit (Type 2 charstrings); fontTools processes via `T2CharStringPen`. **Smith #5, HIGH**

**Image tracing risk:** High-resolution/high-precision traces may exceed 65,535 point limit; point decimation required **before** fontTools assembly. **Smith #5, MEDIUM** (estimated from resolution/precision trade-offs)

### 5.5 Pen Functions for Assembly Pipeline

**SegmentToPointPen** — adapts Segment protocol → PointPen protocol; `guessSmooth=True` auto-detects smooth points via angle calculation. **Smith #5, HIGH**

**PointToSegmentPen** — reverse adapter; default removes implied closing line (last point == first point); `outputImpliedClosingLine=True` to preserve. Image tracers may produce duplicate start/end points → this pen drops them. PR #1720. **Smith #5, HIGH**

**TTGlyphPen** (TrueType):
```python
from fontTools.pens.ttGlyphPen import TTGlyphPen
pen = TTGlyphPen(glyphSet=None)
path.draw(pen)
glyph = pen.glyph(dropImpliedOnCurves=False)
glyph.recalcBounds(glyfTable=None)  # REQUIRED after synthesis
```
- `handleOverflowingTransforms=True` — clamps transform values to F2Dot14 range (-2 to +2) or decomposes components
- `dropImpliedOnCurves` — removes on-curve points at segment midpoints (optimization, but **loses data**)
- Source: ttGlyphPen.py (commit de2ccaee) **Smith #5, HIGH**

**T2CharStringPen** (CFF):
- `roundTolerance` controls float→int rounding
- `getCharString()` optimizes via `specializeCommands` and `commandsToProgram`
- **Smith #5, HIGH**

**GuessSmoothPointPen** — estimates smooth flag via angle heuristic (error tolerance = 0.05 radians ≈ 3°). **Smith #5, HIGH**

**FilterPointPen** & **ContourFilterPointPen** — enable buffered contour manipulation and in-place or replacement filtering. **Smith #6, HIGH**

**OnCurveFirstPointPen** — rotates point list to ensure closed contours start with on-curve points; handles degenerate point sequences. **Smith #6, HIGH**

### 5.6 Required Metadata Tables (Minimum Set for TTF/OTF)

Both formats require: `head`, `maxp`, `post`, `hhea`, `hmtx`, `cmap`, `name`, `OS/2`

TrueType additionally: `loca`, `glyf`
CFF additionally: `CFF` or `CFF2`

fontTools auto-generates missing tables on `TTFont.save()` but explicit setup ensures correctness:
```python
font['head'].recalcBoundingBox()
font['maxp'].recalcMaxpValues(font['glyf'])  # TrueType only
```
Source: Google Fonts guide (googlefonts.github.io/gf-guide/fonttables.html). **Smith #5, HIGH**

### 5.7 Contour Simplification & Point Reduction

**Ramer-Douglas-Peucker (RDP) Algorithm:**
- Recursively subdivides polygon until points fit within tolerance (epsilon parameter)
- Fewer points retain original shape better than naive decimation
- 1972–1973 algorithm; widely implemented; no fontTools native integration found
- **Smith #6, HIGH**

**Potrace Algorithm** (Peter Selinger, 2003):
- Decomposes bitmap into paths; fits optimal polygon; minimizes segment count; converts to smooth curves
- Reduces unnecessary points during curve-fitting phase
- Source: potrace.sourceforge.net/potrace.pdf
- **Smith #6, HIGH**

No specific RDP implementation found in fontTools core; point reduction typically delegated to Bezier fitting or boolean ops. **Smith #6, HIGH**

### 5.8 Cu2Qu (Cubic-to-Quadratic Conversion)
*[Merged — see Dedup D-4]*

**Primary method:** `curve_to_quadratic(cubic_points, max_error, name=None)`
- Chops cubic curve into multiple segments; converts each to quadratic spline; iteratively increases segment count until error < tolerance
- Preserves end-curve tangents of original cubic

**Parameters:**
- `max_err`: Max approximation error in font units; recommend `UPEM / 1000` (e.g., 1.0 FU for 1000-UPEM font). **Smith #6, MEDIUM** (derived from docs)
- `all_quadratic`: If `True` (default), quadratic-only output; if `False`, mixed quadratic/cubic allowed by economy
- `reverse_direction`: Flip contour direction while preserving start point

**Module structure:**
- `fontTools.cu2qu.cu2qu` — basic curve conversion routines
- `fontTools.cu2qu.ufo` — applies to entire UFO files
- `fontTools.cu2qu.cli` — CLI: `fonttools cu2qu <font.ufo>`

**Cu2QuPen** — filter pen for in-pipeline conversion via SegmentPen protocol; integrates with fontmake preprocessing pass. **Smiths #5 + #6, HIGH**

### 5.9 Complete Cleanup Workflow (Google Fonts fontmake Order)

From Smith #6 (fontmake preprocessing pass):
1. **Overlap removal** → `fontTools.ttLib.removeOverlaps()` (requires skia-pathops)
2. **Cubic-to-quadratic** → `cu2quPen` or Cu2Qu UFO module
3. **Extrema addition** → custom PointPen filter (**not built-in**)
4. **Final validation** → component decomposition, glyph consistency checks

**⚠️ Warning (Smith #6):** Add extrema + remove overlap sequence can produce inaccurate output if algorithms applied selectively; recommend sequential application on entire font. MEDIUM confidence — noted in FontForge developers mailing list.

### 5.10 Image-Tracing-Specific Failure Mode Table

| Failure | Cause | fontTools Fix | Source |
|---------|-------|--------------|--------|
| Wrong winding | Autotrace collects points in arbitrary order | `ReverseContourPointPen` | Smith #5, HIGH |
| Self-intersecting contours | Vectorizer overshoots edges | `removeOverlaps()` + pathops | Smith #5, HIGH |
| Duplicate points | Autotrace includes start point twice | `PointToSegmentPen` drops auto | Smith #5, HIGH |
| Degenerate curves | 3+ colinear points; ambiguous fill | `pathops.simplify()` + manual inspection | Smith #5, HIGH |
| Missing extrema | No points at curve max/min x/y | **Manual fix required; no fontTools automation** | Smiths #5 + #6, AGREE |
| Too many points | High-precision trace → >65,535 | Point decimation **before** fontTools | Smith #5, MEDIUM |
| Floating-point coords | Autotrace outputs floats; TrueType needs ints | `TTGlyphPen.glyph(round=otRound)` or pathops integer retry | Smith #5, HIGH |
| Overflowing transforms | Component matrix outside F2Dot14 | `TTGlyphPen(handleOverflowingTransforms=True)` | Smith #5, HIGH |

### 5.11 Library Dependency Matrix

| Library | Version | Algorithm | License |
|---------|---------|-----------|---------|
| fontTools | v4.49.0+ (PyPI) | Skia/Vatti | MIT |
| skia-pathops | 0.8.0.post2+ | Google Skia PathOps | BSD/Apache |
| booleanOperations | ~3.1+ | Clipper (Vatti) | MIT |
| pyclipper | 1.3.0.post5+ | Angus Johnson Clipper | MIT |
| Cu2Qu | 1.6.7+ | Iterative segmentation | MIT |

**Install:** `pip install fonttools skia-pathops booleanOperations cu2qu`
**Smith #6, HIGH**

---

## THEME 6 — Variable Font Construction from Masters

**Primary source:** Smith #7

### 6.1 Process Overview
Variable fonts are built from multiple master fonts positioned at specific locations in a design space:
1. **Designspace file** (.designspace) — specifies master file paths, axes (weight, width, etc.), and locations
2. **Master fonts** — individual font files at specific design space coordinates
3. **varLib/fontmake toolchain** — compiles masters into a single interpolatable variable font

**Example fontmake workflow:**
```bash
fontmake -o ttf-interpolatable -g Font.glyphs   # Generate masters
fonttools varLib master_ufo/Font.designspace    # Build variable font
fontmake -m Font.designspace -o variable        # Alternate: direct compilation
```
**Smith #7, HIGH**

### 6.2 Point Compatibility Requirements (Critical)

All masters must be **point-compatible** — identical on all of:
- Contour count per glyph
- Point count per contour
- Point order (on-curve and off-curve in same sequence)
- Node types (curve vs. line at each index)
- Component structure (same base glyph references)

**Why:** Variable fonts store delta values (differences from default master) using point-to-point correspondence. Mismatch = interpolation impossible. **Smith #7, HIGH**

### 6.3 What Breaks When Masters Are Independently Generated

#### A. Point Count Mismatches (Issue #3928, closed Sep 11, 2025)
- **Symptom:** Different point counts when building variable vs. static fonts
- **Root cause:** Floating-point precision differences in cu2qu conversion between Cythonized (C compiler-optimized) and pure Python implementations
- **Specific mechanism:** Apple clang on M1 Macs optimizes complex division as reciprocal multiplication (`z * (1/v)` instead of `z/v`) → 1 ULP (Unit in Last Place) difference → affects `dropImpliedOnCurvePoints` logic differently across platforms
- **Impact:** Breaks varLib's gvar table generation
- **Smith #7, HIGH** (GitHub issue #3928)

#### B. Point Type Mismatches (Issue #4114, closed Jun 29, 2026)
- **Symptom:** `VarLibCFFPointTypeMergeError` during CFF2 variable font generation
- **Root cause:** Edge case where contour endpoints coincide with startpoints. Some masters generate explicit closing line commands; others rely on implied closing → incompatible charstring operations
- **Fix:** Force `outputImpliedClosingLine=True` in PointToSegmentPen (implemented in ufo2ft PR #993)
- **Impact:** CFF2 variable fonts fail to build even when compatibility checks pass
- **Smith #7, HIGH** (GitHub issue #4114, most recent: Jun 2026)

#### C. Contour Order Reversal
- Detection: `interpolatable.py` detects "wrong contour order between different masters"
- Impact: Glyph at midpoint shows kinks or distortion
- **Smith #7, HIGH**

#### D. Starting Point Misalignment
- Detection: `interpolatable.py` finds misaligned starting points on contours
- Impact: Smooth interpolation corrupted; creates discontinuities in variable space
- **Smith #7, HIGH**

#### E. Missing Glyphs
- varLib allows sparse masters (omitted axes default to default values) but glyphs themselves must be present across all masters
- **Smith #7, HIGH**

#### F. Component Reference Changes
- Composite glyph references different base glyphs across masters → cannot interpolate component transforms consistently
- **Smith #7, HIGH**

### 6.4 varLib Toolchain Architecture

| Component | Purpose |
|-----------|---------|
| **designspaceLib** | Parses .designspace XML; defines axes, masters, instances, locations |
| **varLib.build()** | Main function; loads masters, validates compatibility, builds variation tables |
| **varLib.interpolatable.py** | Pre-build checker; detects 9 problem classes before compilation |
| **varLib.models.py** | VariationModel; computes interpolation scalars, normalization (-1 to 1 range) |
| **varLib.gvar.py** | TrueType glyph variations table; stores point deltas |
| **varLib.cvar.py** | CVT (control value) variations for TrueType hinting |
| **varLib.HVAR/VVAR.py** | Horizontal/vertical metrics variations |
| **varLib.iup.py** | Interpolation Upon Points; reduces delta data by computing implied points |
| **varLib.featureVars.py** | Feature variations; conditional GSUB rules per design space region |
| **varLib.merger.py** | Merges GDEF/GPOS/GSUB; handles sparse masters, format conversions |

**Smith #7, HIGH** (from fontTools repository structure and docstrings, 2026-07-27)

### 6.5 Compatibility Checking — interpolatable.py

**Detects 9 problem categories:**
1. Missing glyphs across masters
2. Differing path/node counts
3. Incompatible node types
4. Open contours where closed expected
5. Wrong contour ordering
6. Incorrect starting points
7. Underweight/overweight interpolations (tolerance default: 0.95)
8. "Kinks" (sharp deviations in smooth curves via handle ratio analysis)
9. Discrete axes (non-continuous design space)

**CLI usage:**
```bash
fonttools varLib.interpolatable Font.designspace [--output-path report.html]
```
**Output formats:** text, JSON, PDF, PostScript, HTML
**Smith #7, HIGH**

### 6.6 fontmake Integration
- **Accepts:** .glyphs, .ufo, .designspace files
- **Outputs:** .otf, .ttf, variable fonts, CFF2 variants
- **Requires:** Python 3.10+
- **Key flags:** `-i` (generate instances), `-f` (flatten components), `-m` (designspace file), `-o variable`
- **GitHub:** 883 stars; actively maintained by Google Fonts
- **Smith #7, HIGH**

### 6.7 Key Dates
- fonttools: 5,180 stars, 530 forks, 420 open issues; created July 2013; last updated 2026-07-27
- Issue #3928 resolved: Sep 11, 2025
- Issue #4114 resolved: Jun 29, 2026
- UFO specification: Version 4 in active development (MEDIUM — no specific date)
- **Smith #7, HIGH**

---

## THEME 7 — Font QA Tooling: fontspector

**Primary source:** Smith #4 (sole coverage)

### 7.1 Overview
- **Repo:** github.com/fonttools/fontspector | Skrifa/Read-Fonts-based font QA tool written in Rust
- **Version:** 1.7.1 (current as of 2026-07-27) | **Last commit:** 2026-07-24
- **Status:** Active successor to FontBakery; actively maintained; no deprecation warnings
- **Smith #4, HIGH**

### 7.2 Installation
**Binary download (recommended):**
- Platforms: `aarch64-apple-darwin`, `x86_64-apple-darwin`, `x86_64-pc-windows-gnu`, `x86_64-unknown-linux-gnu`
- Place in PATH (`/usr/local/bin/` on Unix)
- Source: INSTALLATION.md (last updated 2026-07-24) **Smith #4, HIGH**

**Via cargo-binstall:**
```bash
cargo-binstall fontspector
# macOS prerequisite: brew install cargo-binstall
```

**Build from source:**
```bash
cargo install --release git+https://github.com/fonttools/fontspector
# Optional features:
cargo install --release --features python git+...   # enables --use-python flag
cargo install --release --features duckdb git+...   # enables --duckdb file.db logging
```
**Smith #4, HIGH**

### 7.3 CLI Invocation

```bash
fontspector [OPTIONS] <INPUTS>...
```

| Option | Description |
|--------|-------------|
| `--profile <PROFILE>` | Profile to check (default: `universal`) |
| `-L, --list-checks` | List available checks in selected profile |
| `--list-checks-json` | List checks in JSON format |
| `-c, --checkid <CHECKID>` | Run specific checks |
| `-x, --exclude-checkid` | Exclude specific checks |
| `-e, --error-code-on <STATUS>` | Exit code 1 threshold (default: `fail`); values: skip/pass/info/warn/fail/error |
| `-l, --loglevel <LOGLEVEL>` | Log level (default: `warn`) |
| `-q, --quiet` | Suppress terminal output |
| `--succinct` | Compact output |
| `--skip-network` | Skip network checks |
| `--timeout <TIMEOUT>` | Network operation timeout (seconds) |
| `--json <JSON>` | Write JSON report |
| `--csv <CSV>` | Write CSV report |
| `--ghmarkdown <GHMARKDOWN>` | Write GitHub Markdown report |
| `--html <HTML>` | Write HTML report |
| `--badges <BADGES>` | Write JSON badges to directory |
| `--hotfix` | Fix found problems in binaries |
| `--fix-sources` | Fix source files |
| `--configuration <CONFIGURATION>` | Read TOML/JSON config file |
| `--plugins <PLUGINS>` | Load plugins (dynamic libraries) |

**Example:** `fontspector --html report.html --profile googlefonts *.ttf`
**Smith #4, HIGH**

### 7.4 Check Profiles

**Built-in (5 embedded in binary):**

| Profile | Purpose |
|---------|---------|
| `opentype` | OpenType Specification compliance |
| `universal` | **Default**; community best practices |
| `googlefonts` | Google Fonts Guide compliance |
| `iso15008` | ISO 15008 (in-car display standard) |
| `fontwerk` | Fontwerk foundry expectations |

**External profiles** (loaded via plugins at runtime):
`adobe`, `microsoft`, `designspace`, `fontbureau` — built as `.fontspectorplugin` files

```bash
fontspector --plugins microsoft.fontspectorplugin --profile microsoft MyFont.ttf
```

**Custom TOML profiles:** `fontspector --profile /path/to/custom.toml files...`
**Smith #4, HIGH**

### 7.5 Output Formats
1. Terminal (default) — human-readable; `--succinct` for compact
2. JSON — `--json <filename>`
3. CSV — `--csv <filename>`
4. HTML — `--html <filename>` (bundled templates; customizable via `--update-templates`)
5. GitHub Markdown — `--ghmarkdown <filename>`
6. Badges — `--badges <directory>` (JSON badges for CI integration)
**Smith #4, HIGH**

### 7.6 fontspector vs. FontBakery

| Aspect | FontBakery | fontspector |
|--------|-----------|-------------|
| Language | Python | Rust |
| Speed | Minutes per font | Seconds (entire families) |
| Execution | Desktop/CLI only | CLI + WebAssembly (browser at fonttools.github.io/fontspector) |
| Status | Maintained, but superseded | **Active successor (current)** |
| FontBakery check compatibility | Native | `--use-python` flag (requires `--features python` build) |
| Web data uploads | N/A | "Runs entirely in browser, no fonts uploaded" |

**Speed claim note:** Reports suggest ~100x+ faster than FontBakery on large projects ("several minutes" vs. "seconds" per family). **No official benchmarks found.** **Smith #4, LOW confidence on exact speedup**

---

## THEME 8 — OFL Licensing & ML Training

**Primary source:** Smith #8 | **Supplementary:** Smith #9 (IP/copyright aspects of AI fonts)

### 8.1 Official OFL Position: FAQ 1.25 (Authoritative, November 2023)
**Source:** openfontlicense.org/ofl-faq/ (v1.1-update7, November 2023 — still current July 2026)

**Explicit answer to ML training question:**
> Any font produced from systems whose input or training data contains any source file from an OFL-licensed font project should be considered a **derivative work**.

**Requirements per FAQ 1.25:**
- All Font Software released under OFL must remain under OFL regardless of how sources are transformed
- Derivative fonts must be licensed under OFL even if part of a commercial service or if source code access is restricted
- Cannot release ML-generated fonts under any other license
- **Smith #8, HIGH** (direct from official OFL FAQ)

### 8.2 OFL Definition of Derivative Works
- **"Modified Version"** includes: adding to / deleting / substituting components; changing formats; porting to new environment
- FAQ 1.25 explicitly extends this to ML-trained outputs (model output = "Modified Version")
- Source: SIL Open Font License Official Text (openfontlicense.org)
- **Smith #8, HIGH**

### 8.3 Scope Clarification: What OFL Applies To

| Question | OFL Position | Legal Status |
|----------|-------------|--------------|
| Can I train on OFL fonts? | **YES** — no usage restriction | SETTLED ✓ |
| Must outputs be OFL? | **YES** (FAQ 1.25) | Formally settled; copyright paradox caveat |
| Do model weights count as derivatives? | **Not explicitly addressed** | UNSETTLED ⚠️ |
| Can US courts enforce OFL on non-copyrightable AI output? | **Unknown** | UNSETTLED ⚠️ |
| Can OFL be updated retroactively? | **NO mechanism exists** | SETTLED (negative) ✓ |

**Smith #8, HIGH/MEDIUM per row**

### 8.4 US Copyright Law Complication
- Under US copyright law, **AI-generated materials have no copyright**
- AI-generated fonts cannot legally be copyrighted in the US
- Consequently, they may not be *licensable* under OFL, which is a copyright license
- Creates legal paradox: OFL FAQ says outputs must be OFL, but they may not be copyrightable to license
- **Smith #8, MEDIUM** (documented limitation; not litigated)
- **Cross-reference:** Smith #9 also notes typefaces themselves are NOT eligible for copyright under US law (utilitarian object); digital font files may receive protection if human authorship of "expressive elements" demonstrated

### 8.5 Structural Legal Gaps

**OFL License Stability:**
- OFL unchanged since 2007 (version 1.1); confirmed at November 2025 20th anniversary
- Google Fonts fonts locked under OFL v1.1 permanently — no retroactive update mechanism
- Even if OFL were updated with ML restrictions, existing fonts cannot be re-licensed
- **Smith #8, HIGH**

**Community Concern (Predictive):**
- AI systems can generate fonts "stylistically derived from OFL sources yet not meeting the legal definition of 'derivative works'" under copyright law
- Community consensus: OFL's original intent could be undermined within 10–15 years if not updated
- **Smith #8, MEDIUM-LOW** (predictive, not current law)

**Policy Inertia:**
- Google (which operates Google Fonts under OFL) is "strongly pushing AI" and has "hardly an incentive" to restrict ML training on OFL fonts
- **Smith #8, MEDIUM** (speculative community observation)

### 8.6 AI Font Generation State (June 2026 — Simon Cozens)
- **Latin** font generation: NOT yet production-ready (as of June 2026)
- **Chinese/Japanese** font generation: IS production-ready (with foundry support)
- Much R&D happening in China/Japan, not Western foundries
- Source: simoncozens.github.io/state-of-ai-font-generation/ (June 22, 2026)
- **Smith #8, HIGH** (cross-reference: Smith #9 cites same source)

### 8.7 Published Legal Analysis: Notable Absence
- **No dedicated law firm memos or law journal articles** specifically analyzing OFL + ML font training found (as of 2024–2026)
- FOSSA Blog: general OFL overview, no ML analysis
- "Navigating the Legal Risks of Fonts" (FKKS law firm PDF): general font licensing risks, no OFL-ML analysis
- Knobbe Martens: no specific OFL + ML publication found
- **Smith #8, HIGH** (confirmed absence)

### 8.8 Timeline

| Date | Event |
|------|-------|
| 2005 | OFL first released |
| 2007 | OFL v1.1 published (last update to license text) |
| Nov 2023 | OFL FAQ v1.1-update7 released (Q1.25 on ML added) |
| April 2024 | SIL releases general AI Ethics Statement (no OFL-ML specifics) |
| June 2026 | Cozens: Latin AI font generation still not production-ready |
| Nov 2025 | OFL website redesigned; 20th anniversary; FAQ v1.1-update7 remains current |

---

## THEME 9 — AI Font Provenance, Disclosure & Marketplace Policies

**Primary source:** Smith #9 | **Supplementary:** Smith #8 (OFL/copyright overlap)

### 9.1 Regulatory Frameworks

#### EU AI Act — Code of Practice on Transparency
- First draft: December 17, 2025 | Enforcement deadline: **August 2, 2026**
- Requires AI providers to mark all AI-generated content in machine-readable format
- Deployers must label deepfakes and AI-generated public interest text
- **Scope:** Generative AI outputs including text, images, video, audio — fonts not explicitly carved out but covered under general AI content requirements
- **No font-specific exemption stated**
- Second draft: mid-March 2026; feedback deadline January 23, 2026
- **Smith #9, HIGH**

#### U.S. FTC AI Disclosure Requirements
- "Double disclosure" required for AI-involved sponsored content (paid relationship + AI use)
- Penalties: **$53,088 per violation in 2026**
- Scope: AI-written copy, AI images, AI translations, AI video in ads; excludes grammar checking, analytics
- **Font/typeface application:** Not explicitly addressed in FTC guidance
- **Smith #9, MEDIUM** (FTC rules apply to advertising/sponsored content, not necessarily product distribution)

#### U.S. Copyright Office — AI Authorship Standard (January 29, 2025)
- "Prompting alone does not constitute sufficient human authorship"
- **Typefaces:** NOT eligible for copyright protection under U.S. law (utilitarian object)
- Digital font files **may** receive protection if human authorship of "expressive elements" demonstrated
- Alternative protections: trademark, trade dress, contractual licensing; trade dress requires non-functional design + secondary market meaning
- **Smith #9, HIGH** (longstanding U.S. law confirmed)

### 9.2 Technical Standards for Provenance Metadata

#### C2PA (Coalition for Content Provenance & Authenticity)
- Standard: ISO 22144 (draft); C2PA v2.2+ now supports **fonts explicitly**
- Embeds cryptographic metadata into media files including fonts; records AI tool use, editing history, provenance chain
- **Current adoption (2026):** Adobe Firefly, OpenAI DALL-E 3, Sora, Bing Image Creator embed C2PA by default
- **Font metadata:** Uses standard IPTC/XMP assertion framework; **no dedicated "AI-generation" field in OpenType** itself
- **Limitation:** Does not detect AI use — relies on signer honesty
- **Smith #9, HIGH**

#### OpenType Specification
- Supports copyright, designer, version, license metadata fields
- **No dedicated "AI-generation provenance" field** in current spec
- **Smith #9, MEDIUM** (derived from documentation; spec may evolve)

#### ISO/IEC/ITU Collaboration (July 2025)
- Technical Report on AI and Multimedia Authenticity; participants: ISO, IEC, ITU, C2PA
- Defines watermarking, fingermarking, metadata for content authenticity
- No font-specific subset identified
- **Smith #9, HIGH**

### 9.3 Marketplace Policies

#### Google Fonts
- **No explicit published policy** accepting or rejecting AI-generated fonts
- Community discussion of "Gothic Gumdrop" (100% AI-generated submission, June 2026) reflects ongoing uncertainty
- Contribution standard: requires "statement confirming sole original author"
- Community consensus: important that Google Fonts does not publish AI-generated fonts — **but NOT official policy**
- **Smith #9, HIGH** (CONTRIBUTING.md) / **MEDIUM** (community interpretation)

#### Adobe Fonts (TypeKit)
- **No specific policy statement found** on AI-generated fonts
- General font licensing terms apply
- **Smith #9, LOW** (policy may exist unpublished)

#### MyFonts / Monotype
- Monotype positions against typical AI-generated font suggestions
- MyFonts app (launched May 27, 2026): integrates fonts into AI workflows for *discovery*, not generation
- **No explicit published policy on AI-generated font acceptance/rejection found**
- FAQ updated June 18, 2026 lacks AI-generation guidance
- **Smith #9, MEDIUM**

#### Creative Fabrica Font Generator
- Users **retain ownership** of AI-generated fonts
- Flexible commercial license: no attribution or additional fees required
- No explicit AI-disclosure requirement in Studio Terms for distributed fonts
- Processes takedown complaints from rights holders
- **Smith #9, HIGH**

#### Foundry Virtual Tabletop (FVT) — Marketplace Policy
- Committed to "genuine human creative effort"
- Previous policy required AI-usage disclosure
- Most recent substantive change: **March 18, 2026**
- Existing packages: must comply by **September 14, 2026** or face de-listing
- Not font-specific, but affects font packages
- **Smith #9, HIGH**

### 9.4 Attribution & Provenance Norms by Platform

| Platform | Attribution Required? |
|----------|----------------------|
| Simplified AI Font Generator | NO — "yours to use commercially, no license fees or attribution required" |
| Font AI | Optional — gives artist credit via source listings |
| Creative Fabrica | No explicit requirement |

- No ISO, IPTC, or C2PA **mandatory** attribution field for fonts specifically
- No unified industry attribution standard
- **Smith #9, MEDIUM**

### 9.5 Community & Expert Signals

- **TypeDrawers community:** Strong preference against AI-generated submissions to major platforms; no official TypeDrawers policy document found
- **Enforcement pattern emerging (2026):** Foundries sending C&D letters for suspected AI-font IP infringement; no consistent legal framework yet. Source: whatfontis.com/blog/designers-are-punishing-ai-fonts-in-2026... (DATE: 2026, HIGH)
- **Training data transparency:** "The training-data question hasn't been answered cleanly by any major AI font generator." (whatfontis.com, 2026, HIGH)
- **ILT Trust:** Published "Fonts and AI" — analytical, not prescriptive; no formal recommendation for or against. **Smith #9, MEDIUM**

### 9.6 Critical Gaps in Provenance Infrastructure (Smith #9 Assessment)
1. No explicit font-specific standard across EU AI Act, FTC, Copyright Office, or C2PA
2. No unified marketplace policy — Google Fonts (ambiguous), MyFonts (no published policy), Adobe Fonts (no published policy), Creative Fabrica (permissive but no disclosure requirement)
3. Training data provenance entirely opaque across all major AI font tools
4. Copyright protection for AI + human hybrid fonts: case-by-case; not tested specifically for typefaces
5. Enforcement pattern emerging but no consistent legal framework

### 9.7 Recommended Compliance Baseline (Smith #9, July 2026)
- **EU (by Aug 2, 2026):** Embed C2PA Content Credentials or equivalent machine-readable mark identifying font as AI-generated
- **U.S.:** Maintain documented evidence of sufficient human authorship if copyright claim intended; expect trademark/trade dress scrutiny
- **Marketplace:** Check individual platform contribution guidelines; expect increasing scrutiny post-2026

---

## THEME 10 — AI Font Synthesis: Non-Latin Script Coverage

**Primary source:** Smith #10

### 10.1 Papers Explicitly Handling Multiple Scripts (2023–2026)

#### VecFusion (arXiv:2312.10540, Dec 2023–updated 2024)
- Scripts: **Latin, CJK, Indic** — tested across all three
- Approach: Raster→vector cascaded diffusion model with mixed discrete-continuous control point representation
- **Limitation:** Demonstrates versatility but no comparative accuracy metrics reported by script
- **Smith #10, MEDIUM**

#### VecGlypher (arXiv:2602.21461, Feb 2026, CVPR 2026)
- Scripts: **Broad Unicode support** (Latin, Greek, Cyrillic, CJK mentioned implicitly through "extended Unicode character sets")
- Approach: Autoregressive language model generating SVG path tokens
- Training: 39K Envato fonts → 2.5K Google Fonts expert-annotated
- **Limitation:** Out-of-distribution evaluation outperforms DeepVecFont-v2; specific script-level accuracy metrics NOT reported
- **Smith #10, LOW** (script-level metrics absent)

#### One-Shot Multilingual Font Generation Via ViT (arXiv:2412.11342, Dec 2024)
- Scripts: **Chinese, Japanese, Korean (CJK) + English**
- Approach: Vision Transformer with MAE pretraining + Retrieval-Augmented Guidance
- Metrics: L1 Loss, RMSE, SSIM, LPIPS, FID reported; **no inter-script comparison provided**
- **Smith #10, MEDIUM**

#### Beyond Patches: Global-aware Autoregressive Model (arXiv:2601.01593, Jan 2026)
- Scripts: **Cross-language** (Chinese, Korean, Latin, English in supplementary materials)
- Approach: Global-aware tokenizer capturing local+global patterns + multimodal style encoder
- **Limitation:** Specific benchmark results by script unavailable in search results
- **Smith #10, MEDIUM**

#### StyleTextGen (arXiv:2605.14708, May 2026, CVPR 2026)
- Scripts: **Chinese + English** (bilingual)
- Dataset: StyleText-CE benchmark for monolingual & cross-lingual evaluation
- Approach: Dual-branch style encoder with text style consistency loss
- "Significantly outperforms" on cross-lingual generalization — **exact metrics not extracted**
- **Smith #10, LOW**

### 10.2 Quantified Accuracy Drop vs. Latin (Critical Finding)

**Cross-lingual font generation (ScienceDirect, June 2025):**
- Unseen language performance: **~50% content accuracy, ~20% style accuracy**
- Authors propose patch-level contrastive learning + relative position awareness to address gap
- **Smith #10, HIGH** — only quantified cross-lingual penalty found in 2025–2026 literature

**FontCLIP (arXiv:2403.06453, March 2024; Computer Graphics Forum):**
- Roman-to-CJK: **better performance** than CJK-to-Roman
- Explanation: Model trained only on Roman dataset → asymmetric transfer → inherent Latin bias
- **Smith #10, HIGH**

**MX-Font++ (March 2025):**
- Character accuracy: **0.7519–0.8564** | Sequence accuracy: **0.4033–0.6521** (benchmark comparison)
- **Smith #10, MEDIUM** (context: these may be within-script metrics, not cross-lingual)

### 10.3 Cyrillic & Greek Coverage: Critical Gap

**Finding:** 2025–2026 literature provides **minimal explicit data on Cyrillic and Greek synthesis**

- VecGlypher (2026) lists Cyrillic/Greek as covered via Unicode but provides **no script-level metrics**
- One 2025 publication tested "Cyrillic and Latin alphabets used by ethnic minorities" cross-lingually with Chinese model — **no accuracy metrics disclosed**
- GAS-NeXt (arXiv:2212.02886, Dec 2022) tested English→Chinese; Cyrillic/Greek NOT evaluated
- Chinese font survey (arXiv:2508.06900, Aug 2025): 42-page survey, 106 articles, notes "noticeable gap in studies addressing Indic scripts, **Cyrillic scripts**, and multilingual handwriting generation"
- **Smith #10, MEDIUM** (from survey scope analysis)

### 10.4 Standard Evaluation Metrics (2025–2026)
- **Visual quality:** SSIM, LPIPS, FID (Fréchet Inception Distance)
- **Character accuracy:** Per MX-Font++ (March 2025)
- **Cross-lingual:** Content accuracy ~50%, style ~20% for unseen languages (June 2025)
- **TMNIST dataset:** Spans 150+ scripts (Latin, Cyrillic, Greek, Arabic, Devanagari, etc.) — primarily for recognition, not synthesis
- **Smith #10, MEDIUM-HIGH**

### 10.5 CJK Dominance in 2025–2026 Research
- Chinese font survey (arXiv:2508.06900, Aug 2025): 42 pages, 25 figures, 106 articles reviewed (2017–2025)
- CJK receives the most attention after Western scripts; Indic and Cyrillic notably underrepresented
- Simon Cozens (June 2026): Chinese/Japanese font generation IS production-ready; Latin is NOT
- **Smith #10, HIGH** / **Smith #8 cross-confirms, HIGH**

### 10.6 Critical Limitation (Current State, July 2026)
- Field lacks systematic benchmarks comparing Latin, Cyrillic, Greek, and CJK under identical conditions
- The ~50%/~20% content/style accuracy is the ONLY quantified cross-lingual penalty; composition of "unseen" test sets not publicly detailed
- Cyrillic and Greek remain under-explored in generative font synthesis
- **Smith #10, HIGH** (confirmed gap)

---

---

# PART II — DEDUP LOG (Merged Findings)

## D-1 | "Learning to Kern" Paper — Smiths #2 and #3

**Overlap:** Both Smiths independently covered arXiv 2402.14313 (Nakatsuru & Uchida, 2024).

**Reconciliation:**
- **Consistent facts (all HIGH):** arXiv 2402.14313; ICDAR 2024; February 22, 2024; ~2,500 Google Fonts; MAE figures consistent (Smith #2: "≈5.3 pixels"; Smith #3: "5.318 pixels" — same, different rounding)
- **Smith #3 adds:** v2 is latest version; explicitly confirms no tool released in 2026; set-wise model superior to pairwise
- **Smith #2 adds:** Scale of problem framing (2,704 spaces for 52 Latin letters); contextualizes within broader spacing algorithm survey

**Merged finding:** Placed in Theme 4. Both versions' unique details preserved.
**No conflicts.**

---

## D-2 | Overlap Removal (skia-pathops + fontTools) — Smiths #5 and #6

**Overlap:** Both Smiths covered `removeOverlaps()`, skia-pathops `simplify()`, and the Skia float/integer retry workaround.

**Reconciliation:**
- **Consistent facts:** skia-pathops required; `simplify()` primary method; float→integer retry for Skia bug; `ignoreErrors=True` for error tolerance; invalidates TrueType hinting; fontmake skips for variable fonts
- **Smith #5 adds:** Exact process steps (`skPathFromGlyph()`, `pathops.simplify()`, `ttfGlyphFromSkPath()`); specific parameters (`fix_winding=False`, `keep_starting_points=False`); `RemoveOverlapsError` behavior; code snippet
- **Smith #6 adds:** booleanOperations library as alternative (Vatti/Clipper algorithm); v4.22 as when removeOverlaps added; v4.53.0+ for CFF table support; `scale_to_clipper()` helpers

**Merged finding:** Placed in Theme 5.2. Both versions' unique details preserved.
**No conflicts.**

---

## D-3 | Extrema Points — Smiths #5 and #6

**Overlap:** Both Smiths addressed the requirement for extrema points and fontTools' handling.

**AGREE:** Both independently confirm:
- No dedicated `addExtrema()` function exists in fontTools core
- FontForge/FontLab have the feature; not ported to fontTools Python API
- Manual intervention typically required for production fonts

**Smith #5 adds:** Image tracing specific context; `calcCubicBounds()` / `calcQuadraticBounds()` in bezierTools
**Smith #6 adds:** Workaround patterns (filter pens, cu2qu side effect, Bezier analysis); `addPoint()` chaining via PointPen

**Merged finding:** Placed in Theme 5.3. AGREE signal explicitly noted.
**No conflicts.**

---

## D-4 | Cu2Qu — Smiths #5 and #6

**Overlap:** Both Smiths mentioned cu2qu / Cu2QuPen.

**Reconciliation:**
- Smith #5: Mentions cu2quPen and T2CharStringPen in context of assembly pipeline; no module-level detail
- Smith #6: Full module structure (`cu2qu.cu2qu`, `cu2qu.ufo`, `cu2qu.cli`); parameters (`max_err`, `all_quadratic`, `reverse_direction`); `max_err` recommendation of `UPEM / 1000`

**Merged finding:** Placed in Theme 5.8. Smith #6's detail is primary; Smith #5's pipeline context preserved.
**No conflicts.**

---

## D-5 | Simon Cozens — Three Distinct Contributions Across Smiths

**Risk of confusion:** Smiths #2, #3, and #9 all reference Simon Cozens. These are THREE DISTINCT works:

| Smith | Tool/Work | Domain | Date |
|-------|----------|--------|------|
| #2 | CounterSpace | Spacing (influence-field model) | ~2018+ |
| #3 | atokern / Kerncritic | ML Kerning (CLI, 92% accuracy) | Pre-2024 |
| #9 | Blog: "State of AI Font Generation" | Industry assessment | June 22, 2026 |

**Not merged** — three separate signals, all preserved. Referenced in Themes 2.2-E, 3.3, and 8.6 respectively.

---

## D-6 | OFL / AI Legal Landscape — Smiths #8 and #9

**Overlap:** Both Smiths address IP/copyright for AI-generated fonts. Substantially complementary rather than duplicative.

**Smith #8 unique:** OFL FAQ 1.25 detailed analysis; "Modified Version" definition; model weights question; retroactive update impossibility; legal scholarship absence; full OFL timeline
**Smith #9 unique:** EU AI Act enforcement; FTC penalties; C2PA technical standard; marketplace-specific policies (Google, Adobe, MyFonts, Creative Fabrica, FVT); attribution platform table; C&D letter enforcement trend (2026)
**Shared:** US Copyright Office AI authorship standard; typefaces not copyrightable in US; Cozens June 2026 AI generation state (both cite same source)

**No conflicts.** Both preserved in full across Themes 8 and 9.

---

---

# PART III — CORRECTIONS

## C-1 | CFF/PostScript Fill Rule — Smith #5 [HIGH CONFIDENCE CORRECTION]

**Smith #5 states:**
> "CFF/Type 1: Uses **even-odd rule**. Counter-clockwise = filled; clockwise = unfilled."

**Correction:**
CFF (OpenType CFF and CFF2) and Type 2 charstrings use the **non-zero winding rule**, NOT the even-odd rule. This is explicitly stated in the OpenType CFF2 specification. PostScript does support both `fill` (non-zero winding) and `eofill` (even-odd) operators, but Type 1 fonts by convention use non-zero winding fill, and OpenType CFF inherits this.

The practical difference between TrueType and CFF is in **winding direction convention**, not in the fill rule:
- TrueType: outer contours = **clockwise** (non-zero winding, fills)
- CFF/PostScript: outer contours = **counter-clockwise** (non-zero winding, fills)

Both formats use non-zero winding. Smith #5's statement that CFF uses "even-odd rule" is a commonly propagated misconception (possibly arising from the fact that CFF uses opposite direction conventions from TrueType, which some sources shorthand as "even-odd").

**Impact:** The practical advice in Smith #5 (ReverseContourPointPen, winding awareness) remains correct — the direction convention difference is real and important. Only the fill rule terminology is wrong. Smith #5's code and workflow recommendations are unaffected.

**Confidence:** HIGH. Source: OpenType spec CFF2 section (Microsoft); PostScript Language Reference Manual.

---

## C-2 | fontTools Version Reference Ambiguity — Smith #6 [MEDIUM CONFIDENCE NOTE]

**Smith #6 states** `removeOverlaps` was "added ~v4.22." It also references "v4.53.0+ added CFF table support" and "Date: 2022–2023 range."

**Note:** Smith #6 cites PyPI changelog for these version numbers but marks them HIGH confidence without a direct link to a specific changelog entry. The version ranges are plausible and not contradicted, but Opus should be aware these specific sub-version dates (v4.22, v4.38, v4.53) are derived rather than sourced from a primary dated changelog entry.

**No contradiction with Smith #5** (which does not specify fontTools version for removeOverlaps).

**Confidence of concern:** MEDIUM. Current version (v4.49.0+) cross-confirmed by both Smiths.

---

---

# PART IV — DISPUTES

## GENUINE DISPUTE: None found between Smiths on factual matters.

## TENSION NOTE T-1 | Cleanup Workflow Order — Smiths #5 and #6

**Smith #5** (image-tracing pipeline): winding fix → overlap removal → assembly
**Smith #6** (fontmake preprocessing pass): overlap removal → cu2qu → extrema → validation

**Assessment:** These are NOT contradictory — they describe different contexts. Smith #5's winding correction before overlap removal is specific to image-tracing workflows where contours arrive with incorrect winding. Smith #6's order reflects fontmake's automated build pipeline for clean source files.

**Opus note:** For image-traced glyphs specifically, winding should be verified/corrected BEFORE overlap removal (since `pathops.simplify()` is winding-aware and may produce incorrect results on mis-wound input). For clean design-tool sources, Smith #6's fontmake order applies.
**Not a factual dispute — context-dependent.**

---

## TENSION NOTE T-2 | OFL FAQ Status vs. Legal Enforceability — Smith #8

**Within Smith #8:** The FAQ formally states ML-generated fonts must be OFL (HIGH confidence), but the same Smith notes that US courts have not tested this and AI-generated materials may not be copyrightable (MEDIUM confidence), creating an internal paradox.

**Assessment:** This is a documented, acknowledged legal tension within Smith #8 — not a dispute between Smiths. Preserved as a compound finding for Opus to synthesize. The FAQ position and the enforcement uncertainty are both real and simultaneously true.

---

---

# PART V — GAPS

Across all 10 Smiths, the following topics were NOT covered or were only tangentially mentioned:

### Font Engineering Gaps

| # | Topic | Closest Coverage | Signal Strength |
|---|-------|-----------------|-----------------|
| G-1 | TrueType hinting (CVT, fpgm, prep) | Smith #7 mentions varLib.cvar (CVT variations) | Near-zero |
| G-2 | PostScript hinting (stems, blue zones, alignment zones) | Not mentioned | Zero |
| G-3 | OpenType feature code compilation (GSUB, GDEF rules beyond kerning) | Smith #7 touches GPOS/GSUB merging in varLib context | Very limited |
| G-4 | Font subsetting (pyftsubset, woff2) | Not mentioned | Zero |
| G-5 | Color font formats (SBIX, CBDT/CBLC, COLR, SVG-in-OTF) | Not mentioned | Zero |
| G-6 | Variable font instance naming and fvar/avar table construction | Smith #7 covers varLib architecture; instance naming not addressed | Partial |
| G-7 | Font interpolation debugging beyond compatibility checks | Smith #7's `interpolatable.py` coverage is good; visual output/glyph-level debug not covered | Partial |
| G-8 | Bitmap/raster fallback workflows | Not mentioned | Zero |

### Legal / Licensing Gaps

| # | Topic | Closest Coverage | Signal Strength |
|---|-------|-----------------|-----------------|
| G-9 | OFL v1.1 reserved font name restrictions | Smith #8 covers OFL broadly but not the reserved name mechanism | Near-zero |
| G-10 | Comparison of OFL vs. SIL vs. Apache vs. CC licensing for fonts | Smith #8 covers OFL only | Zero |

### AI / ML Gaps

| # | Topic | Closest Coverage | Signal Strength |
|---|-------|-----------------|-----------------|
| G-11 | Arabic / Hebrew (RTL) script synthesis | Smith #10 mentions TMNIST dataset includes Arabic; no synthesis papers cited | Near-zero |
| G-12 | Devanagari / Indic script synthesis | Smith #10 notes "noticeable gap" in Indic; VecFusion tested on Indic without metrics | Near-zero |

### Tool Ecosystem Gaps

| # | Topic | Closest Coverage | Signal Strength |
|---|-------|-----------------|-----------------|
| G-13 | RoboFont ecosystem and Extensions API | Smith #2 mentions LS Cadencer for RoboFont; no deeper coverage | Near-zero |
| G-14 | Glyphs 4 vs. Glyphs 3 API compatibility changes | Smith #1 notes Kern On v1.38 "supports Glyphs 4"; no deeper coverage | Near-zero |

---

---

# PART VI — CROSS-CUTTING SIGNALS (for Opus synthesis)

These signals appear across multiple Smiths and may carry elevated synthesis weight:

### Signal X-1: "No Add Extrema in fontTools" (Smiths #5 + #6, AGREE, MEDIUM)
Both independently confirmed the same gap. Elevated to HIGH confidence by convergence. Critical for any traced-glyph assembly pipeline.

### Signal X-2: "Kern On is the only transparent, active, CLI-less commercial kerning tool" (Smith #3, HIGH)
No contradiction. Sole production-quality automated kerning option outside full-service (iKern). Neural/ML alternatives remain experimental or academic.

### Signal X-3: "CJK AI font generation is production-ready; Latin is not" (Smiths #8 + #10, AGREE, HIGH)
Both Smiths cite this independently (Smith #8 from Cozens blog June 2026; Smith #10 from research literature). Strong convergence on a non-obvious finding.

### Signal X-4: "OFL legal paradox: FAQ requires OFL on outputs; US law may not allow copyrighting those outputs" (Smith #8, MEDIUM)
Unresolved paradox with no external adjudication. No other Smith contradicts or confirms; stands alone.

### Signal X-5: "fontspector is actively maintained and Rust-fast; FontBakery is superseded but still compatible via flag" (Smith #4, HIGH)
No contradiction. Sole coverage but internally consistent and recent (last commit 2026-07-24).

### Signal X-6: "varLib CFF2 point type mismatch bug (#4114) was fixed Jun 2026" (Smith #7, HIGH)
Most recent technical development in the dataset (June 2026). Directly relevant to anyone building CFF2 variable fonts with independently-generated masters.

### Signal X-7: "No unified AI font disclosure standard exists anywhere in the stack" (Smith #9, HIGH)
EU AI Act covers AI content generally but has no font-specific field; C2PA supports fonts but no mandatory attribution; all major marketplaces lack explicit AI-generated font policies. Convergent signal from regulatory, technical, and market dimensions within one Smith.

---

*End of Anderson Brief. All unique signal preserved. Corrections, disputes, and gaps enumerated. Ready for Opus synthesis.*

============================================================
## Chain B — Anderson Report
============================================================

Filesystem write isn't permitted in this environment, so here is the complete organized findings document directly — all signal preserved, structured for Opus:

---

# CHAIN B ORGANIZED FINDINGS — Anderson Triage Layer
**Smiths #11–#20 | Compiled: 2026-07-27 | For Opus Synthesis**

---

## TRIAGE KEY
- **[AGREE]** Multiple Smiths converge → highest confidence
- **[DEDUP]** Overlapping facts merged; all source Smiths cited
- **[RECENCY]** Conflict resolved by preferring more recent source
- **[DISAGREE]** Genuine unresolved dispute; both versions preserved for Opus
- **[CORRECT]** Error or inconsistency identified and fixed
- **[GAP]** Uncovered topic flagged

---

---

# PART I: THEMATIC FINDINGS

---

## THEME A — TOPOLOGY-PRESERVING LOSS FUNCTIONS
*Primary source: Smith #11*

### A1. Skeleton-Based Losses

**A1.1 Skeleton Recall Loss**
- arXiv: 2404.03010 | ECCV 2024 | Submitted: 2024-04-03
- Measures skeletal structure and connectivity preservation in thin/tubular structures (vessels, nerves, cracks)
- CPU-efficient operations; addresses gap where Dice/Cross-Entropy fail for connectivity
- Confidence: HIGH [Smith #11]

**A1.2 Skea-Topo (Skeleton-Aware Loss)**
- arXiv: 2404.18539 | IJCAI 2024 | Submitted: 2024-04-18
- Two components: (1) skeleton-aware weighted loss using object geometry via skeletons; (2) boundary rectified term emphasizing topologically critical pixels using foreground + background skeletons
- Performance: up to 7-point improvement in VI metric over 13 SOTA methods
- GitHub: github.com/clovermini/Skea_topo
- Confidence: HIGH [Smith #11]

**A1.3 TopoSinGAN**
- MDPI Applied Sciences (doi: 10.3390/app14219944) | 2024-10-30 | No arXiv ID
- Terminal node loss: minimizes terminal node counts along predicted segmentation boundaries; differentiable; designed for single-image generation
- Novel metric: Node Topology Clustering (NTC) index — assesses topological attributes independent of geometric variation
- Results: NTC 15.15→3.94 (agriculture), 14.55→2.44 (dendrology); lower FID scores
- Confidence: HIGH [Smith #11]

### A2. Persistent Homology Losses

**A2.1 TopoDiffusionNet**
- arXiv: 2410.16646 | ICLR 2025 (accepted) | Submitted: 2024-10-16
- Topology-based auxiliary loss using persistent homology; enforces exact Betti number constraints (β₀ connected components, β₁ holes, β₂ voids)
- Loss formulation: Wasserstein distance between persistence diagrams; conditions diffusion model on target Betti count during denoising
- GitHub: github.com/Saumya-Gupta-26/TopoDiffusionNet
- Confidence: HIGH [Smith #11]

**A2.2 PFlow-T: Persistence-Driven Forward Process**
- arXiv: 2605.17555 | Submitted: 2025-06-05
- Novel formulation: persistent homology IS the forward diffusion process (not an auxiliary loss)
- Time parameter τ measures fraction of H₁ persistence-mass destroyed; forward operator eliminates H₁ features (holes) in ascending persistence order
- First generative model where persistent homology is the core forward process substrate
- Performance on MNIST (digits 0, 1, 8): requested Betti numbers honored in 99.6%, 96.0%, 84.8% of generations vs. DDPM baseline: 96.4%, 3.2%, 0.0%
- Confidence: HIGH [Smith #11]

**A2.3 PHINN: Persistent Homology Inspired Neural Network**
- arXiv: 2606.15452 | Submitted: 2026-06-13 (very recent at compilation)
- Flow-matching framework; persistence landscape loss (ensures homology consistency across time series); dynamic Betti curves as conditioning signals
- Loss captures topological "fingerprints" (Betti transitions) as more stable/discriminative than statistical moments
- Performance: beta-RMSE down 41–63%, transition accuracy up 84% on financial/epidemiological data
- Confidence: HIGH [Smith #11]

**A2.4 Topology-Aware Graph Diffusion with Persistent Homology**
- NeurIPS 2025 | OpenReview: openreview.net/forum?id=sye27MizdM
- Persistence Diagram Matching (PDM) loss: ensures generated graphs match topology of originals; captures connected components and loops via persistent homology
- Topology-aware attention module (TAM) induces denoising network to capture homological characteristics
- Scope: graph generation specifically
- Confidence: HIGH [Smith #11]

**A2.5 TopoGen: 3D Generation with Persistence Points**
- Computer Graphics Forum (Pacific Graphics 2025)
- Discrete (Betti numbers) + continuous (persistence points) topological descriptors via persistent homology; used as conditional guidance via cross-attention in latent diffusion model
- Application: 3D shape synthesis; explicit topology control by modifying persistence points
- Confidence: HIGH [Smith #11]

**A2.6 Towards Scalable Topological Regularizers**
- arXiv: 2501.14641 | ICLR 2025 | Submitted: 2025-01-14
- Principal persistence measure regularizer; computes persistent homology on large numbers of small subsamples; GPU-parallelized with continuous gradients for smooth densities
- Addresses cost/gradient discontinuity issues that previously blocked large-scale PH losses
- Applications: shape matching, image generation, semi-supervised learning
- **Significance: solves the scalability bottleneck that was the primary blocker for PH loss adoption at scale**
- Confidence: HIGH [Smith #11]

**A2.7 Persistent Homology Design Space for 3D Point Clouds**
- arXiv: 2604.04299 | Submitted: 2026-04-05
- Unified framework identifying 6 injection points for topology as structural inductive bias: (1) Sampling, (2) Neighborhood graph construction, (3) Optimization dynamics, (4) Self-supervision, (5) Output calibration, (6) Network regularization
- Features used: persistence diagrams, images, and landscapes
- Empirical focus: ModelNet40 classification, ShapeNetPart segmentation; augments PointNet, DGCNN, Point Transformer
- Confidence: HIGH [Smith #11]
- **[CORRECT]** This item appears in Smith #11's body as entry #16 but is entirely **absent from Smith #11's own summary table**. Included here in full.

### A3. Key Trajectory Observations from Smith #11
1. **Skeleton-based losses (2024):** Shift from volumetric overlap (Dice/CE) to structural connectivity via CPU-efficient skeletonization
2. **Persistent homology surge (2024–2026):** Betti numbers and persistence diagrams become native constraints, not auxiliary losses; PFlow-T is first to embed PH as the forward diffusion process itself
3. **Scalability solved (ICLR 2025):** arXiv 2501.14641 removes the computational/gradient bottleneck that blocked large-scale PH loss adoption
4. **LLM-based glyphs (2026):** VecGlypher and LVGM leverage next-token prediction on SVG/stroke embeddings, inheriting sequence-based topology preservation from language models

### A4. Loss Function Type Summary Table (Smith #11)
| Loss Type | Paper | arXiv | Date | Confidence |
|---|---|---|---|---|
| Skeleton Recall | Skeleton Recall Loss | 2404.03010 | Apr 2024 | HIGH |
| Skeleton-Aware | Skea-Topo | 2404.18539 | Apr 2024 | HIGH |
| Terminal Node | TopoSinGAN | — | Oct 2024 | HIGH |
| Persistent Homology (Wasserstein/Betti) | TopoDiffusionNet | 2410.16646 | Oct 2024 | HIGH |
| Persistence-Driven Forward Process | PFlow-T | 2605.17555 | Jun 2025 | HIGH |
| Persistence Landscape | PHINN | 2606.15452 | Jun 2026 | HIGH |
| Persistence Diagram Matching | Topology-Aware Graph Diffusion | — | 2025 | HIGH |
| Principal Persistence Measure | Scalable Topological Regularizers | 2501.14641 | Jan 2025 | HIGH |
| Betti + Persistence Points (3D) | TopoGen | — | 2025 | HIGH |
| PH Design Space (6 injection points) | PH Design Space | 2604.04299 | Apr 2026 | HIGH |
| Stroke Embedding (next-stroke) | LVGM | 2511.11119 | Nov 2025 | HIGH |
| Stroke Potential Fusion | SPFont | — | 2024 | HIGH |
| Radical-Level Feature Alignment | SFGN | 2501.08062 | Jan 2025 | HIGH |
| Per-Point Displacement (multi-axis) | NIV | 2606.05261 | Jun 2026 | HIGH |
| SVG Token Sequence (autoregressive) | VecGlypher | 2602.21461 | Feb 2026 | HIGH |
| Cascaded Diffusion (genus preservation) | VecFusion | 2312.10540 | Dec 2023 | HIGH |

---

## THEME B — DIFFUSION MODEL DISTILLATION METHODS
*Primary source: Smith #12*

### B1. Core Distillation Methods

**B1.1 LCM-LoRA (Latent Consistency Model + LoRA)**
- arXiv: 2311.05556 | Published: 2023-10-06
- Method: One-stage guided distillation in latent space; solves augmented Probability Flow ODE; LoRA freezes base model; fine-tunes only low-rank adaptation matrices
- Training data: LAION-Aesthetics-6+ (12M images) + LAION-Aesthetics-6.5+ (650K images)
- Compute: ~32 A100 GPU hours at 768×768; ~4,000 training steps to convergence
- Consumer GPU compatible: LoRA reduces memory; feasible on 16 GB VRAM
- Repos: github.com/luosiallen/latent-consistency-model; HF diffusers
- Confidence: HIGH [Smith #12]
- Note: Foundational; still widely used despite 2023 date

**B1.2 Hyper-SD (Trajectory Segmented Consistency)**
- arXiv: 2404.13686 | Published: 2024-04-21
- Method: Trajectory segmented consistency distillation with progressive step compression
- Training data: LAION + COYO subsets (size unspecified, MEDIUM); ~140K artist-style text images via SDXL-Base for RLHF (HIGH); COCO2017 train split with instance annotations (HIGH)
- Compute: 32 NVIDIA A100 80GB GPUs; trains LoRA only (not full UNet); specific iteration count NOT DISCLOSED (LOW)
- Checkpoints: 1-step, 2-step, 4-step, 8-step provided
- Confidence: Data HIGH; iterations LOW [Smith #12]

**B1.3 DMD2 (Distribution Matching Distillation v2)**
- arXiv: 2405.14867 | NeurIPS 2024 Oral | Published: 2024-05
- Method: Eliminates expensive noise-image pair regression; two-timescale update rule + GAN discriminator loss; trains on real data
- Training data: ~10,000 COCO images (varies by setup, MEDIUM)
- Compute: ~350K training iterations at batch size 392 (HIGH); ~59 seconds per 20 iterations on 2× A100 GPUs (HIGH); total ~200–300 A100 hours (MEDIUM est.)
- Key advantage: avoids pre-computation of synthetic noise-image pairs
- GitHub: github.com/tianweiy/dmd2
- Confidence: Steps/batch HIGH; total compute MEDIUM [Smith #12]

**B1.4 pi-Flow (Policy-Based Imitation Distillation)**
- arXiv: 2510.14974 | Submitted: 2024-10
- Method: Student predicts network-free policy at one timestep; policy generates dynamic flow velocities at future substeps without additional network evaluations; imitation matching of policy velocity to teacher
- Training data: ImageNet 256² (for 1-NFE testing); scales to 20B parameter models (Qwen-Image)
- Performance: 1-NFE FID 2.85 on ImageNet DiT; outperforms prior 1-NFE methods
- Compute: NOT disclosed
- GitHub: github.com/Lakonik/piFlow | HF: Lakonik/pi-Flow-ImageNet
- Confidence: Performance HIGH; compute LOW [Smith #12]

**B1.5 TLCM (Training-Efficient Latent Consistency Model)**
- arXiv: 2406.05768 | Published: 2024-06 (v6 revised 2024-11)
- Method: Data-free multistep latent consistency distillation (MLCD) + distribution matching + adversarial learning + preference learning
- Training data: ZERO real image-text pairs required (data-free)
- Compute: 70 A100 GPU hours total
- Achieves 2–8 step inference
- GitHub: github.com/oppo-mente-lab/tlcm
- Confidence: HIGH [Smith #12]

**B1.6 Consistency Models (Song et al.)**
- arXiv: 2303.04461 (original); 2310.14189 (improved, ICLR 2024)
- Two variants: Consistency Distillation (CD) from pre-trained teacher; Consistency Training (CT) from scratch
- Compute (Improved Techniques): 400,000 training iterations; batch size 1,024; discretization steps doubled every 50K iterations (curriculum: 10→1,280)
- FID: 2.51 (CIFAR-10), 3.25 (ImageNet 64×64) in 1-step
- CD specifics: 800K+ iterations; batch size 512; ~1,155.6 A100 hours (MEDIUM — derived)
- Confidence: Iterations/batch HIGH; estimated compute MEDIUM [Smith #12]

**B1.7 Adversarial Diffusion Distillation (ADD)**
- arXiv: 2311.17042 | ECCV 2024 | Published: 2023-11
- Method: Score distillation + adversarial GAN loss between student and discriminator
- Training data: noise-image pairs from teacher forward diffusion + real images for discriminator
- Outperforms LCM in 1-step; reaches SDXL quality in 4 steps
- Compute: NOT disclosed
- Confidence: Method HIGH; compute LOW [Smith #12]

**B1.8 Progressive Distillation**
- arXiv: 2202.00512 | ICLR 2022 | Published: 2022-02
- Method: Multi-stage 1000→500→...→1 step distillation
- Compute: 50,000 updates per stage (8 stages) + 100,000 for final stages; total ~600K iterations; ~195.1 A100 hours (MEDIUM est.)
- **Flag: >2.5 years old; superseded by consistency/adversarial methods** [Smith #12]

**B1.9 SDXL-Lightning (Progressive Adversarial Distillation)**
- arXiv: 2402.13929 | Published: 2024-02
- Method: Progressive distillation + adversarial training for 1,024px text-to-image
- Checkpoints: 1-step, 2-step, 4-step, 8-step; released as LoRA + full UNet weights
- HF: ByteDance/SDXL-Lightning
- Compute: NOT disclosed
- Confidence: Availability HIGH; compute LOW [Smith #12]

**B1.10 Align Your Flow (Continuous-Time Flow Map Distillation)** ← Most Recent
- arXiv: 2506.14603 | Published: 2025-06-17 | Authors: NVIDIA, U of Toronto, Vector Institute
- Method: Continuous-time flow map distillation; autoguidance + adversarial fine-tuning
- Key innovation: flow maps generalize consistency models; **performance does not degrade with more steps** (unlike consistency models)
- SOTA on ImageNet 64×64 and 512×512; outperforms non-adversarial few-step methods for T2I
- Training data and compute: NOT disclosed
- Confidence: Performance HIGH; details LOW [Smith #12]

### B2. Synthetic vs. Real Data in Distillation (Smith #12)
- Synthetic data needs ~10× volume to match real data when used alone — HIGH confidence (arXiv:2305.12954, 2405.03243)
- Hybrid approach: pre-train early layers on synthetic, fine-tune on real — MEDIUM confidence
- DMD2 trains entirely on real data, avoiding synthetic pair generation bottleneck — HIGH confidence

### B3. LoRA Rank Recommendations for Distillation (Smith #12)
| Method | Rank | Alpha | Target Layers | Confidence |
|---|---|---|---|---|
| LCM-LoRA (distillation task) | 64 | 128 | Cross-attn, linear | HIGH |
| SDXL-Lightning LoRA | Variable | 2× rank | UNet blocks | MEDIUM |
| General LoRA fine-tuning of distilled models | 8–16 | Half rank | All weight matrices | HIGH |
| Timestep-dependent (T-LoRA) | 4–16 (stepped) | Variable | Query, value per timestep | MEDIUM |

- Rule of thumb: Rank ~20% of feature dimension — HIGH confidence
- **[CORRECT]** Smith #12 presents these as potentially contradictory (rank 64 in the table, rank 8–16 in the body text). They are NOT contradictory: rank 64 is for full distillation tasks; rank 8–16 is for fine-tuning already-distilled models. Both facts are valid; the framing distinction matters.

### B4. Training Cost Comparison Table (Smith #12)
| Method | Steps | Batch Size | A100 hrs | Data | Year |
|---|---|---|---|---|---|
| LCM-LoRA | 4,000 | — | 32 | LAION 12M | 2023 |
| Hyper-SD | — | — | 32+ multi-GPU | LAION + 140K synthetic | 2024 |
| DMD2 | ~350,000 | 392 | ~200–300 est. | 10K real | 2024 |
| Progressive Distill | ~600,000 | — | 195 | Teacher samples | 2022 |
| Consistency Distill | 400K–800K | 512–1,024 | ~1,155 | Pre-trained teacher | 2023 |
| TLCM | — | — | 70 | Zero real data | 2024 |
| pi-Flow | — | — | — | ImageNet scale | 2024 |
| SDXL-Lightning | — | — | — | LAION subsets | 2024 |
| Align Your Flow | — | — | — | — | 2025 |

### B5. Selection Guide (Smith #12)
| Constraint | Best Method | Reason |
|---|---|---|
| Minimum training time | LCM-LoRA | 32 A100 hrs; proven convergence |
| No real data available | TLCM | Data-free; 70 A100 hrs |
| Largest scale (20B+ params) | pi-Flow | Demonstrated at scale |
| Single-step inference | ADD or DMD2 | Optimized for 1-step |
| Few-step (2–8) flexibility | Align Your Flow | Step-count agnostic |
| Consumer GPU training | LCM-LoRA | LoRA reduces memory; feasible on 16 GB VRAM |

### B6. Surveys (Smith #12)
- Pre-Trained Diffusion Model Distillations Survey (Feb 2025): arXiv 2502.08364 — most comprehensive recent overview
- Efficient Diffusion Models Survey (Oct 2024): arXiv 2410.11795

---

## THEME C — FLUX.2 KLEIN ARCHITECTURE: TEXT ENCODER, LoRA INFRASTRUCTURE, INFERENCE CODE
*Primary sources: Smith #13 (text encoder) + Smith #14 (inference code)*
**[DEDUP]** Smiths #13 and #14 overlap substantially on model variants and VRAM; merged here with both cited.

### C1. Model Variants
| Variant | Params | Inference Steps | Guidance Scale | Inference VRAM | Behavior |
|---|---|---|---|---|---|
| FLUX.2-klein-9B (distilled) | 9B | 4 | 1.0 | ~29 GB | Guidance-distilled; ignored if >1.0 |
| FLUX.2-klein-4B (distilled) | 4B | 4 | 1.0 | ~13 GB | Guidance-distilled; ignored if >1.0 |
| FLUX.2-klein-base-9B (undistilled) | 9B | 50 | 4.0 | — | Guidance-enabled |

- Sources: BFL official docs (2026-01-20), HF model cards, diffusers pipeline code [Smith #13, #14]
- Confidence: HIGH

### C2. Qwen3 Text Encoder — Role During LoRA Training
- **The Qwen3 text encoder is FROZEN during all LoRA fine-tuning** — HIGH confidence [Smith #13]
- Only the transformer DiT is trainable; no toolchain lists text encoder as a trainable component
- Confirming sources: HF blog (2024–2025), SimpleTuner docs (2024), Fizgig README (2026), kohya-ss musubi-tuner docs (2024)
- Replacement at load time (not training time) is supported; see C5 below

### C3. Text Encoder VRAM Footprint [Smith #13]
| Model | Config | VRAM | Confidence |
|---|---|---|---|
| Qwen3-4B | 8-bit | ~4 GB | HIGH |
| Qwen3-4B | 4-bit | ~2 GB | HIGH |
| Qwen3-8B | 8-bit | ~8 GB | HIGH |
| Qwen3-8B | 4-bit | ~4 GB | HIGH |
| Klein-4B LoRA train | bf16 total | ~12 GB | HIGH |
| Klein-4B LoRA train | fp8 + int8 total | ~8 GB | HIGH |
| Klein-9B LoRA train | bf16 total | ~22 GB | HIGH |
| Klein-9B LoRA train | fp8 + int8 total | ~14 GB | HIGH |
| Klein-9B LoRA train | fp8 + 4-bit NF4 base total | ~7.5 GB | HIGH |
| Per-image batch cost | — | ~2.4 GB | HIGH |

Note: Inference VRAM (~29 GB / ~13 GB from Smith #14) is for full-precision inference; training VRAM above is for frozen-base LoRA with quantization. Not contradictory — different operating modes.

### C4. Prompt Embedding Precomputation and Caching [Smith #13]
- Fully supported — HIGH confidence
- Pre-caching script: `flux_2_cache_text_encoder_outputs.py` in kohya-ss musubi-tuner (2024)
- Pipeline accepts `prompt_embeds` parameter to bypass text encoder at inference
- Qwen3-4B (Klein-4B): layers [9, 18, 27] → 2,560 dims each → **7,680-dim output** per token; max 512 tokens
- Qwen3-8B (Klein-9B): layers [9, 18, 27] → 4,096 dims each → **12,288-dim output** per token; max 512 tokens
- Cache file per prompt: ~20–24 MB (4B) or ~32 MB (8B) at fp16/bf16

### C5. Text Encoder Replacement and Fixed-Prompt Use Cases [Smith #13]
- Pruned alternative: SearchingMan/FLUX.2-klein-9B-Text-Encoder-Pruned-5.1B (8.19B → 5.1B params, 40% reduction) — HIGH confidence
- Abliterated uncensored variants confirm encoder is architecturally swappable — HIGH confidence
- Fixed-prompt pre-compute: embeddings are deterministic; can bake precomputed tensor into pipeline and skip loading Qwen3 entirely at inference — HIGH confidence
- No official diffusers example, but architecturally trivial via `prompt_embeds` parameter

### C6. Inference Pipeline Class and Code [Smith #14]
- **Pipeline class:** `Flux2KleinPipeline` from `diffusers.pipelines.flux2.pipeline_flux2_klein`
- Inherits from `DiffusionPipeline` and `Flux2LoraLoaderMixin`; available in diffusers ≥ 0.30
- Pipeline explicitly checks: "Guidance scale {guidance_scale} is ignored for step-wise distilled models" (pipeline_flux2_klein.py ~line 450)

**Standard LoRA loading pattern (text-to-image):**
```python
from diffusers import Flux2KleinPipeline
import torch

pipe = Flux2KleinPipeline.from_pretrained(
    "black-forest-labs/FLUX.2-klein-9B",
    torch_dtype=torch.bfloat16,
).to("cuda")

pipe.load_lora_weights(
    "dx8152/Flux2-Klein-9B-Consistency",
    weight_name="Klein-consistency.safetensors",
    adapter_name="klein-consistency"
)
pipe.set_adapters(["klein-consistency"], adapter_weights=[1.0])

image = pipe(
    prompt="your prompt here",
    guidance_scale=1.0,       # CRITICAL for distilled models
    num_inference_steps=4,    # CRITICAL for distilled models
    height=1024,
    width=1024,
    generator=torch.Generator(device="cuda").manual_seed(42),
).images[0]
```
- Source: PRITHIVSAKTHIUR/FLUX.2-Klein-LoRA-Studio (commit 3b31f59, last updated 2026-07-17 — 10 days before compilation) [Smith #14]
- Confidence: HIGH

**[CORRECT]** Smith #14's first code example includes `image=input_image` — this is an img2img-specific parameter absent from the second (correct text-to-image) example. Including `image=input_image` in a generic text-to-image template will cause errors. Both examples are preserved here; Opus should flag for downstream users.

**Key implementation parameters:**
| Parameter | Distilled Value | Undistilled Value | Confidence |
|---|---|---|---|
| `guidance_scale` | 1.0 (ignored if >1.0) | 4.0 | HIGH |
| `num_inference_steps` | 4 | 50 | HIGH |
| `torch_dtype` | torch.bfloat16 | torch.bfloat16 | HIGH |
| `adapter_weights` typical range | 1.0–1.5 | — | HIGH |
| `load_lora_weights()` location | `pipe` object | `pipe` object | HIGH |

**Code recency:** diffusers pipeline: active main branch; FLUX.2-Klein-LoRA-Studio: updated 2026-07-17; BFL official docs: current as of 2026-01-20.

---

## THEME D — GLYPH/CHARACTER-SPECIFIC GENERATION & STROKE TOPOLOGY
*Primary sources: Smith #11 (glyph section), Smith #17 (zero-shot style adaptation)*
**[DEDUP]** Papers appearing in both Smiths are merged with both cited.

### D1. Stroke-Level Character Generation Models

**D1.1 SFGN: Skeleton and Font Generation Network**
- arXiv: 2501.08062 | Submitted: 2025-01-14
- Method: (1) skeleton builder synthesizes content features from low-resource text without content images; (2) radical-level feature alignment aligns content + style at radical component level (not global)
- Addresses structural bias causing character mutations in prior methods; zero-shot Chinese character generation
- Code: NOT CONFIRMED [Smith #17]
- Confidence: HIGH for method; MEDIUM for zero-shot reference requirement (Smith #17 notes "0 or minimal" — unclear if reference style images are needed)
- **[DEDUP]** Appears in Smith #11 (radical-level feature alignment loss type) and Smith #17 (zero-shot methods list) — both framed correctly

**D1.2 LVGM: Large Vectorized Glyph Model**
- arXiv: 2511.11119 | Submitted: 2025-11-11
- Method: Next-stroke prediction via next-token prediction; strokes encoded into discrete stroke embeddings (latent quantization); DeepSeek LLM backbone
- Dataset: 907K-sample Chinese SVG dataset organized by stroke structure
- Topology preserved through sequential generation paradigm
- Confidence: HIGH [Smith #11]

**D1.3 NIV: Neural Axis Variations for Variable Font Generation**
- arXiv: 2606.05261 | Submitted: 2026-06-03 (very recent)
- Method: Per-point displacement prediction for skeleton-guided interpolation along semantic design axes (weight, width, slant, optical size); Property Embedding captures multi-axis interactions while maintaining topological consistency
- Operates directly on vector glyph geometry (not raster intermediates)
- Dataset: 1M+ variation tuples from Google Fonts; generalizes to unseen code points, CJK, handwriting
- Code: GitHub ndvbd/NIV (confirmed)
- Task: variable font interpolation, NOT style transfer — correctly scoped
- Confidence: HIGH [Smith #11, #17]
- **[DEDUP]** Appears in Smith #11 (topology-preserving per-point displacement) and Smith #17 (zero-shot style adaptation context, correctly flagged as different task)

**D1.4 VecGlypher: Unified Vector Glyph Generation with LLMs**
- arXiv: 2602.21461 | CVPR 2026 | Submitted: 2026-02-25
- Method: Multi-modal LLM generates SVG path tokens directly (no raster intermediate); autoregressive SVG path emission preserves stroke structure implicitly via token sequence
- Training: 39K noisy fonts (SVG syntax mastery) + 2.5K expert Google Fonts (geometry/descriptive tags)
- Evaluation: Relative OCR Accuracy (R-ACC); OOD cross-family evaluation
- Performance: Substantially outperforms DeepVecFont-v2, DualVector on cross-family OOD evaluation
- GitHub: github.com/xk-huang/VecGlypher
- Confidence: HIGH [Smith #11, #16]
- **[DEDUP]** Appears in Smith #11 (SVG token sequence topology loss) and Smith #16 (human eval R-ACC metric) — both framings correct and complementary

**D1.5 VecFusion: Vector Font Generation with Diffusion**
- arXiv: 2312.10540 | CVPR 2024 | Submitted: 2023-12-10
- Method: Cascaded diffusion — (1) raster stage (global style/shape + control points); (2) vector stage (transformer, predicts precise control points)
- Preserves structural and topological properties (genus) while interpolating artistic properties
- Confidence: HIGH [Smith #11]

**D1.6 SPFont: Stroke Potential Features Embedded GAN**
- ChinaMM 2024; published in Displays journal | 2024
- Method: Stroke potential feature fusion module (SPFM) overlays style + content features at stroke level (not global)
- Preserves fine stroke details: thickness, curve shapes, inter-stroke relationships, layout
- Confidence: HIGH [Smith #11]

### D2. Zero-Shot and Few-Shot Font Generation Methods [Smith #17]

**Definitional note from Smith #17:** Most 2025–2026 "zero-shot" claims actually require 1 reference image at inference. True zero-shot = no per-font training data AND no reference at inference. Only 2 methods confirmed. See DISPUTES section.

**D2.1 Emuru — Borderline Zero-Shot (1 reference image required)**
- arXiv: 2503.17074 | CVPR 2025 | Published: 2025-03
- Requires: 1 style image at inference; VAE + autoregressive Transformer trained on 100,000+ fonts; no per-font fine-tuning
- Code: YES — GitHub aimagelab/Emuru-autoregressive-text-img
- Confidence: HIGH [Smith #17]
- **[CORRECT]** See DISPUTES §2 — Smith #17 labels this zero-shot while simultaneously requiring 1 reference; definitional inconsistency noted

**D2.2 One-Shot and Few-Shot Methods (context only — not zero-shot)**
- One-Shot Multilingual Font Generation Via ViT: arXiv 2412.11342 | 2024-12-15 | 1 reference; includes CJK + English | Code: NOT CONFIRMED
- InkDiffuser (one-shot Chinese calligraphy): arXiv 2605.05865 | 2026-05-07 | 1 reference | Code: NOT CONFIRMED
- SLD-Font (structure-level disentangled diffusion): arXiv 2602.18874 | 2026-02-21 | Few references (exact count unavailable, MEDIUM confidence) | Code: NOT CONFIRMED
- DRG-Font (dynamic reference-guided few-shot): arXiv 2604.13797 | 2026-04-15 | Few references; dynamic selection | Project: rejoycs.github.io/drg-font | Code: NOT CONFIRMED

**D2.3 Key Finding (Smith #17)**
- True zero-shot font style transfer without ANY reference at inference is extremely rare in 2025–2026 literature
- Confirmed zero-shot: 2 methods (Emuru with definitional caveat + SFGN with MEDIUM confidence)
- With confirmed code release: 1 (Emuru only)

---

## THEME E — GLYPH CONDITIONING + LoRA COMPOSITION
*Primary source: Smith #15*

### E1. Confirmed Glyph-Method + LoRA Compositions

**E1.1 TextFlux**
- arXiv: 2505.17778 | Published: 2025-05-23
- Composition: Spatial glyph concatenation + LoRA fine-tuning of FLUX.1-Fill-dev base (rank 128 on single A100 80 GB)
- Result: "Remarkable performance"; glyph concatenation demonstrates "effectiveness of glyphs as contextual cues even with limited parameter updates"
- Sequence accuracy (ReCTS Chinese): No concat + LoRA baseline: 5.2% → Concat + LoRA: significantly higher (exact number not in abstract)
- Interference: None reported; composition appears synergistic
- GitHub: github.com/yyyyyxie/textflux
- Confidence: MEDIUM (improvement documented; comparative metrics quoted selectively) [Smith #15]

**E1.2 UniGlyph**
- arXiv: 2507.00992 | ICCV 2025 | Published: 2025-07
- Composition: Segmentation masks + LoRA for coordinate regression + style classification subtasks
- Framing: "leveraged LoRA to preserve pretrained knowledge while adapting to coordinate regression and constrained style classification"
- Interference: Not explicitly reported; framed as efficient knowledge preservation
- Confidence: LOW (no quantitative composition metrics in abstracts) [Smith #15]

**E1.3 FontFusion**
- arXiv: 2606.06066 | Published: 2026-06
- Method: Hierarchical token binding + position-aware embeddings; plug-and-play DiT design
- LoRA: NOT MENTIONED in any source
- Confidence: N/A for LoRA composition [Smith #15]

**E1.4 HDGlyph**
- arXiv: 2505.06543 | Published: 2025-05-10 | Authors: USTC / Zhejiang University
- Composition: Language-specific expert LoRAs injected into GlyphControlNet (input conv layer + control blocks); multiple language LoRAs aggregated
- Result: Positive transfer — language experts enhance glyph sensitivity and integration
- Performance gain: +5.08% accuracy gain (English), +11.7% (Chinese) over baselines
- Interference: None reported
- Confidence: MEDIUM (performance numbers direct; LoRA-specific interaction not isolated) [Smith #15]

**Critical gap noted by Smith #15:** NO papers found testing (TextFlux OR FontFusion OR UniGlyph OR GlyphDraw) + independently pre-fine-tuned base model LoRA simultaneously. This specific combination is uncharted.

### E2. LoRA Composition Interference — Broader Research [Smith #15]

**E2.1 LILAC: Layer-Wise Independent LoRAs**
- arXiv: 2607.04801 | Published: 2026-07-27 (same day as this compilation) | Adobe Research
- Problem: Naive LoRA merging causes cross-concept parameter-level interference
- Solution: Bind exactly one adapter per forward pass; cascade conditioning on frozen composite of prior subjects
- Result: ArcFace detection rate 0.861 (LILAC) vs. 0.745 (prior best) = **+15.6% absolute improvement**
- Confidence: HIGH [Smith #15]

**E2.2 QR-LoRA: Disentangled Content-Style Fusion**
- arXiv: 2507.04599 | ICCV 2025
- Problem: Unstructured weight modifications lead to feature entanglement between content and style
- Solution: QR decomposition — orthogonal Q matrix minimizes interference; trainable task-specific ΔR matrices for content/style separately
- Result: 50% parameter reduction vs. standard LoRA; no cross-contamination
- Insight: Orthogonal basis Q ensures different feature transformations remain independent
- Confidence: HIGH [Smith #15]

**E2.3 Cached Multi-LoRA Composition (CMLoRA)**
- arXiv: 2502.04923 | ICLR 2025
- Problem: "Semantic conflicts in LoRA composition"; "diminished generated image quality" as number of LoRAs increases
- Root cause: Different LoRAs amplify different frequencies (high-freq: edges/textures; low-freq: structure/color); frequency overlap causes conflict
- Solution: Frequency-domain analysis + caching to reduce conflict
- Result: CLIPScore +2.19% average improvement; MLLM win rate +11.25% improvement
- Confidence: HIGH [Smith #15]

**E2.4 CLoRA: Contrastive Test-Time Composition**
- ICCV 2025 | Project: clora-diffusion.github.io
- Problem: Attention mechanisms of different LoRA models overlap; one concept may be completely ignored or incorrectly combined
- Solution: Test-time attention map adjustment to separate attentions of distinct concept LoRAs; resolves attention crosstalk without retraining
- Confidence: HIGH [Smith #15]

**E2.5 Simple Drop-in LoRA Conditioning**
- arXiv: 2405.03958 | Published: 2024-05
- Method: Apply LoRA to attention layers as conditioning mechanism
- Result (CIFAR-10): Unconditional FID 1.91 vs. 1.97 baseline; class-conditional FID 1.75 vs. 1.79 (~3% FID improvement)
- Finding: "Simply adding LoRA conditioning to attention layers improves image generation quality"
- Confidence: HIGH [Smith #15]

**E2.6 Orthogonal LoRA — Meta-Finding**
- Finding: Orthogonality reduces but does NOT eliminate interference
- "Strict orthogonality alone does not yield the semantic disentanglement assumed in earlier compositional adaptation work"
- Crosstalk occurs when LoRA weights are similar regardless of orthogonal design intent
- Confidence: MEDIUM (meta-analysis across multiple papers) [Smith #15]

### E3. Composition Outcomes Summary Table [Smith #15]
| Method | Glyph Conditioning | Base LoRA | Interference? | Benefit? | Confidence |
|---|---|---|---|---|---|
| TextFlux | Concat glyphs | Yes (r=128) | Not reported | Synergistic | MEDIUM |
| UniGlyph | Segmentation masks | Yes (coord/style tasks) | Not reported | Efficient preservation | LOW |
| FontFusion | Hierarchical tokens | Not mentioned | — | — | N/A |
| HDGlyph | Multi-linguistic GlyphNet | Language expert LoRAs | None | +5–12% accuracy | MEDIUM |
| LILAC | — (general LoRA) | Layer-wise isolation | Mitigated | +15.6% ArcFace | HIGH |
| QR-LoRA | — (general LoRA) | Content-style LoRAs | Eliminated | No cross-contamination | HIGH |
| CMLoRA | — (general LoRA) | Multiple LoRAs | "Semantic conflicts" | +2.19% CLIPScore, +11.25% MLLM | HIGH |
| CLoRA | — (general LoRA) | Multiple LoRAs | Attention overlap | Resolved via attention editing | HIGH |
| Simple LoRA Conditioning | — | Conditioning LoRA | Not reported | ~3% FID improvement | HIGH |

---

## THEME F — MULTI-REFERENCE CONDITIONING & STYLE AGGREGATION
*Primary source: Smith #18*

### F1. FLUX.2 Native Multi-Reference Architecture
- Released: 2025-11-25 by Black Forest Labs
- Architecture: Mistral-3 24B VLM + rectified flow transformer; rectified flow captures spatial relationships, material properties, compositional logic (arXiv: 2507.09595, Jul 2025)
- Reference capacity: 2–10 images processed simultaneously via shared multimodal attention pipeline
- Optimal practical range: 4–6 images; below 3 = insufficient; above 8 = diminishing returns
- Output resolution: up to 4MP
- Consistency targets: face, build, clothing, lighting across outputs
- Performance claim: 92/100 on consistency metrics, +8 points over Midjourney V7 in multi-pose tests
- Confidence: Architecture HIGH; 4–6 range MEDIUM (blog source, no methodology); 92/100 score MEDIUM (unverified by primary research)
- Sources: aifilms.ai, Promptus, Apatero (2025), selfielab (Mar 2026) [Smith #18]

### F2. FLUX.2 Multi-Reference Failure Modes [Smith #18]
| Mode | Cause | Fix | Confidence |
|---|---|---|---|
| Reference strength too low | <0.6 | Increase to 0.75–0.8 | HIGH |
| Redundant references | Same angle/expression | Add distinctly different angle | HIGH |
| Artifact propagation | Flawed/compressed reference images | Use clean references | HIGH |
| Complex mixed references | Conflicting visual cues | Best model (OmniGen) achieves only 66.6% on synthetic | HIGH |
| Compositional freedom reduction | Strength >0.9 | Stay within 0.6–0.8 | MEDIUM |
| Starting point | — | 0.7 recommended | MEDIUM |

### F3. Reference Set Aggregation Methods

**F3.1 EasyRef (ICML 2025)**
- arXiv: 2412.09618 | ICML 2025 | Preprint: 2024-12
- Core problem: Conventional methods average image embeddings — "image-independent operation that cannot capture consistent visual elements"
- Solution: Qwen2-VL-2B multimodal LLM encodes multiple reference images + text prompt; captures consistent visual elements through cross-image reasoning
- Components: pretrained diffusion model + Qwen2-VL-2B + condition projector + trainable adapters + efficient reference aggregation + progressive approach
- Introduces MRBench (new multi-reference benchmark)
- Surpasses both tuning-free (IP-Adapter) and tuning-based (LoRA) methods in aesthetic quality and zero-shot generalization
- GitHub: github.com/TempleX98/EasyRef
- Confidence: HIGH [Smith #18]
- **Note:** EasyRef uses Qwen2-VL-2B — distinct from the Qwen3 text encoder in FLUX.2 Klein (Smith #13). Different models, different pipelines.

**F3.2 MultiRef Benchmark (ACM MM 2025)**
- arXiv: 2508.06905 | ACM MM 2025 | Published: 2025-08
- Scale: 990 synthetic samples across 10 reference types + 33 combinations; 1,000 real-world samples; 38K high-quality images via RefBlend data engine
- Three-dimensional evaluation: (1) Reference Fidelity (IoU, MSE, CLIPScore); (2) Image Quality (FID, aesthetic); (3) Overall Assessment
- Novel SGScore metric: MLLM chain-of-thought reasoning for object presence + relationship accuracy — more effective than FID/CLIPScore for factual consistency
- Key findings: sequence of processing conditions more critical than overall realism; captions improve depth fidelity and aesthetic quality across all models; best model (OmniGen) achieves only 66.6% on synthetic / 79.0% on real samples
- Confidence: HIGH [Smith #18]

**F3.3 RB-Modulation: Attention Feature Aggregation (ICLR 2025 Oral)**
- arXiv: 2405.17401 | ICLR 2025
- Method: Training-free; stochastic optimal controller + Attention Feature Aggregation (AFA) module; cross-attention-based AFA decouples content and style from reference; incorporates style into controller's terminal cost; modulates drift field in diffusion reverse dynamics
- Solves: style extraction difficulty; content leakage from style reference; effective style + content composition
- Outperforms SOTA in human preference and prompt-alignment while maintaining style fidelity
- Project: rb-modulation.github.io
- Confidence: HIGH [Smith #18]

**F3.4 MS-Diffusion: Multi-Subject Zero-Shot Personalization (ICLR 2025)**
- arXiv: 2406.07209 | ICLR 2025
- Method: Grounding Resampler + Multi-subject Cross-attention; adaptive cross-attention enables each subject condition to act on specific spatial areas (mitigates subject neglect and conflict)
- GitHub: github.com/MS-Diffusion/MS-Diffusion
- Confidence: MEDIUM (exact metrics not in abstract) [Smith #18]

**F3.5 ICAS: IP-Adapter + ControlNet Framework**
- arXiv: 2504.13224 | Published: 2025-04
- Method: IP-Adapter for multi-subject style injection + ControlNet for structural conditioning; cyclic multi-subject content embedding; ~0.4M trainable parameters
- Results: FID 20.1 (vs. baseline 28.2, ~29% improvement); CLIP style similarity 0.72; identity preservation 0.71; CLIPIqa 0.463 (highest among tested)
- Confidence: HIGH [Smith #18]

**F3.6 ConsiStyle (ACM TOG 2025)**
- arXiv: 2505.20626 | ACM TOG 2025 | Published: 2025-05
- Method: Training-free; decouples style from subject (color, structure, patterns, markings); manipulates attention matrices — Queries + Keys from anchor image(s); Values from parallel non-anchored copy; cross-image components added to self-attention; Value statistics aligned to prevent style shift
- Confidence: HIGH [Smith #18]

**F3.7 InstantStyle-Plus**
- arXiv: 2407.00788 | Published: 2024-07
- Method: Decomposes into Style/Spatial Structure/Semantic Content; lightweight InstantStyle + inverted content latent + tile ControlNet for layout preservation
- **Flag: >12 months old as of 2026-07-27** [Smith #18]

**F3.8 FLUX.1 Kontext: Multi-Image In-Context Learning**
- arXiv: 2506.15742 | Published: 2025-06
- Flow matching approach; unifies generation and editing; conditions on multiple images
- Confidence: HIGH [Smith #18]

**F3.9 IP-Adapter Plus XL Reference**
- Ada-Adapter Plus using IP-Adapter Plus XL: Art FID 5.187; outperforms TextualInversion, LoRA, and their combination
- arXiv: 2407.05552 | Published: 2024-07
- Confidence: HIGH [Smith #18]

### F4. Evaluation Metrics for Multi-Reference [Smith #18]
- Gram Matrix Similarity + AdaIN Distance (5 ReLU layers, VGG-19): style consistency
- SGScore (MultiRef, Aug 2025): preferred for factual consistency; MLLM chain-of-thought based
- **Known limitation:** FID improvements do not reliably correlate with downstream improvements (arXiv 2605.29335, Jun 2025)
- **Known limitation:** CLIPScore insensitive to image quality; artifact-heavy images may score high if semantically matching text

### F5. Failure Mode Summary Table [Smith #18]
| Mode | Cause | Evidence | Confidence |
|---|---|---|---|
| Reference strength too low | <0.6 | Identity drift | HIGH |
| Redundant references | Same angle/expression | No additional constraint | HIGH |
| Artifact propagation | Flawed reference images | Downstream corruption | HIGH |
| Complex mixed references | Conflicting visual cues | Best model 66.6% on synthetic | HIGH |
| Embedding averaging collapse | Simple averaging, no cross-image interaction | Cannot capture consistent elements | HIGH |
| Attention homogenization | Global attention decay at depth | Tokens attend to nearly identical areas | HIGH |

---

## THEME G — HUMAN EVALUATION PROTOCOLS FOR FONT/TYPOGRAPHY GENERATION
*Primary source: Smith #16*

### G1. Pairwise Preference Protocols
| Study | Participants | Responses | Dimensions | Venue/Date | Confidence |
|---|---|---|---|---|---|
| FontAdapter (arXiv 2506.05843) | 46 | 4,600 | Font similarity; visual text quality | Jun 2025 | HIGH |
| Frontiers VR Study | Not specified | — | Legibility; cross-language (EN/ZH/JA) | Feb 2025 | HIGH |
| Typography Generation (arXiv 2309.02099) | 10 | 1,000 | Verified metrics match human perception | WACV 2024 | HIGH |
| DiffFont (arXiv 2212.05895) | 64 | — | Style + Content (10 fonts) | IJCV 2024 | HIGH |
| DS-Fusion (arXiv 2303.09604) | 32 + 42 | — | Vs. CLIPDraw/DALL-E 2; vs. artist-crafted | ICCV 2023 | HIGH |

Win-rates from FontAdapter: 91.4% vs. Qwen-VL, 83.2% vs. IPAdapter on font similarity.

### G2. Likert Scale Protocols
**AI-Driven Typography (MDPI Information 17(2) + CHI 2025) — Published: 2025-02**
- **5-point Likert** across three dimensions:
  - **Visual Fidelity:** preservation of reference style structure/details
  - **Stylistic Coherence:** stroke weight and serif consistency across characters
  - **Usability:** legibility + professional suitability
- Participants: 5 professional type designers + 5 design graduate students
- Finding: designers rated Stylistic Coherence 25% higher than diffusion baselines
- Confidence: HIGH [Smith #16]

### G3. Expert Panels + Turing Test
| Study | Expert N | Non-Expert N | Key Result | Date | Confidence |
|---|---|---|---|---|---|
| HFH-Font (arXiv 2410.06488) | 11 font designers | 93 (Turing test) | 51.07% avg accuracy ≈ random chance; AI indistinguishable | Oct 2024 | HIGH |
| DeepVecFont | 11 designers | 20 non-designers | <45% recall for both groups | Oct 2021 ⚠️ outdated | HIGH |
| Attribute2Font | 10 professional designers (Founder Group) | 50 students/faculty | Style similarity judgment | 2020 ⚠️ >48 months | HIGH |

**Critical finding:** AI-generated glyphs now essentially indistinguishable from professional work (HFH-Font: 51.07% Turing accuracy ≈ random chance).

### G4. Multimodal/LLM-Based Evaluation
- TASTE Dataset (arXiv 2605.20731, 2026): 6 binary pairwise judgments → strict 4-way ranking via Bradley-Terry model; GPT-4 + Gemini as evaluators — MEDIUM confidence
- CANVAS (arXiv 2511.20737, 2024-11): blinded expert pairwise; one-sided binomial tests — MEDIUM confidence

### G5. Specialized/Mixed Methodologies
| Study | Method | Key Detail | Date | Confidence |
|---|---|---|---|---|
| MetaDesigner (arXiv 2406.19859, ICLR 2025) | 11 participants | Text Accuracy + Creativity; 77.2% Creativity vs. DALL-E 3 at 7.3% | Jun 2024 | HIGH |
| FontStudio (arXiv 2406.08392, CVPR 2024) | Win-rate | 78% aesthetics vs. Adobe Firefly | Jun 2024 | MEDIUM |
| FontCraft (arXiv 2502.11399, CHI 2025) | 60-min session | 10 min tutorial + 7 min per session + 10 min survey | Feb 2025 | HIGH |
| GlyphWeaver (arXiv 2509.08444) | Case study + interviews | 13 participants | Sep 2025 | HIGH |
| MX-Font++ (arXiv 2503.02799) | User preference | 20 participants | Mar 2025 | HIGH |
| VecGlypher (arXiv 2602.21461, CVPR 2026) | R-ACC (OCR proxy) | OOD cross-family split evaluation | Feb 2026 | MEDIUM |

### G6. Standard Quantitative Metrics Complementing Human Eval [Smith #16]
- FID (Fréchet Inception Distance): distribution-wise similarity
- SSIM, LPIPS, RMSE: pixel/perceptual fidelity
- Chamfer distance, Dice similarity, CKA similarity: structural/geometric
- OCR accuracy: legibility (imperfect proxy for stylistic fonts)
- R-ACC (Relative OCR Accuracy): OCR normalized by ground-truth accuracy (VecGlypher)
- Survey finding (2024): "no single metric captures both style fidelity and diversity"

### G7. Protocol Gaps and Emerging Standards [Smith #16]
- **Emerging standard:** pairwise preference + 5-point Likert on three dimensions (Fidelity/Coherence/Usability) across 2024–2025 literature
- **MOS (Mean Opinion Score) NOT standard** in font generation; papers use Likert instead
- **Expert availability bottleneck:** 11 professional font designers = typical accessible maximum
- **Inconsistent participant reporting:** many papers lack explicit N, demographics, recruitment details
- **No consensus legibility metric:** OCR proxies common but imperfect for stylistic fonts
- **Recommended expert panel size:** 11–42 designers for validity; 46–93 non-experts for ecological generalization

### G8. arXiv ID Reference Table (Smith #16)
| Paper | arXiv | Date | N | Method |
|---|---|---|---|---|
| FontAdapter | 2506.05843 | Jun 2025 | 46 | Pairwise (4.6K responses) |
| HFH-Font | 2410.06488 | Oct 2024 | 93+11 | Turing test + Expert |
| MetaDesigner | 2406.19859 | Jun 2024 | 11 | Likert (Creativity/Accuracy) |
| DiffFont | 2212.05895 | Dec 2022 | 64 | Style+Content (10 fonts) |
| DS-Fusion | 2303.09604 | Mar 2023 | 32, 42 | Comparative preference |
| MX-Font++ | 2503.02799 | Mar 2025 | 20 | User preference |
| FontCraft | 2502.11399 | Feb 2025 | — | 60-min session |
| VecGlypher | 2602.21461 | Feb 2026 | — | R-ACC + OOD eval |
| GlyphWeaver | 2509.08444 | Sep 2025 | 13 | Case study + interviews |
| TASTE Dataset | 2605.20731 | 2026 | — | Bradley-Terry aggregation |
| Typography Generation | 2309.02099 | Sep 2023 | 10 | Pairwise (1K responses) |

---

## THEME H — SELF-TRAINING & PSEUDO-LABELING SAFEGUARDS
*Primary source: Smith #19*

### H1. Confidence Filtering — Threshold Values

| Method | Threshold | Confidence | Date |
|---|---|---|---|
| FixMatch (de facto standard) | 0.95 | HIGH | 2020 (arXiv 2001.07685) ⚠️ 6 years old |
| Noisy Student (filtering) | Remove < 0.3 | MEDIUM | Original paper |
| Self-Adaptive Pseudo-Label Filter (SPF) | Online mixture model (no static value) | HIGH | Sep 2023 (arXiv 2309.09774) |
| FreeMatch | Per-class adaptive (20th percentile of per-class confidence) | HIGH | May 2022 (arXiv 2205.07246) |
| CoVar (Confidence-Variance) | MC + RCV via SVD-based spectral relaxation | HIGH | Jan 2026 (arXiv 2601.11670) |

### H2. Data Mixing Ratios — Model Collapse Prevention

| Finding | Value | Source | Confidence | Date |
|---|---|---|---|---|
| Golden Ratio (min-ℓ₂) | 61.8% real (1/φ) | arXiv 2509.22341 | HIGH | Sep 2025 |
| Ridge Regression minimum | ≥50% real | arXiv 2509.22341 | HIGH | Sep 2025 |
| Accumulation strategy | Append; never replace real | arXiv 2404.01413 | HIGH | Apr 2024 |
| Collapse trigger | 1% synthetic alone sufficient | arXiv 2410.04840 | HIGH | Oct 2024 |

"Test error has finite upper bound independent of iterations if data accumulate." — arXiv 2404.01413
See DISPUTES §1 for interaction with Smith #12's synthetic data volume finding.

### H3. Confidence-Based Filtering Mechanisms

**H3.1 Entropy-Based Filtering** — arXiv 2606.16811 (2026-06) — HIGH confidence
- Filter rule: entropy(p) > threshold → remove; retain if entropy(p) ≤ threshold
- Entropy filtering + lightweight verification classifier → performance ≈ 10–15× more labeled data equivalent

**H3.2 Margin-Based Filtering (MarginMatch)** — arXiv 2308.09037 — MEDIUM confidence
- Margin = max_confidence – second_max_confidence; dynamic masking as training progresses

**H3.3 Multi-View Consistency** — arXiv 2310.01634 — HIGH confidence
- Dual-criteria: high confidence + multi-view consistency; only pseudo-label samples with agreement across multiple prediction views

### H4. Noise Robustness and Error Amplification Safeguards

- Critical threshold: **30–50% noisy pseudo-labels → severe performance collapse** (both standard and adversarial accuracy) — arXiv 2409.12946 (2024-09) — HIGH confidence
- Bootstrapping loss: L_bootstrap = α × L_CE(y_true) + (1-α) × L_CE(y_pred); α ∈ [0.5, 0.9]
- Co-training dual models: Model 1 (robust, high-confidence samples only) + Model 2 (conventional, full dataset); accept pseudo-label only when both agree — HIGH confidence

### H5. Early Stopping and Signal Degradation

**IGCV (Iterated Generalized Cross-Validation)** — arXiv 2602.14029 (2026-02) — HIGH confidence
- Creates U-shaped risk curve with optimal stopping point
- Iteration acts as spectral filter: preserves strong eigendirections, suppresses weak ones
- Trade-off: systematic component grows (signal forgetting) vs. stochastic component decays (denoising); IGCV criterion selects data-driven stopping time

### H6. Temperature-Based Confidence Sharpening
- Formula: p_sharpened = softmax(log(p) / T); T ∈ [0.5, 1.0]
- Trade-off: too sharp = noisy labels; too soft = uninformative
- Confidence-Informative Soft-Label Temperature (sample-aware adaptive T): arXiv 2605.20357 (2026-06) — HIGH confidence

### H7. Class-Conditional and Energy-Based Strategies (2024–2025)
- FlexMatch: threshold = f(per-class learning status); prevents class imbalance from skewing threshold
- Unreliable Sample Contrastive Loss: arXiv 2407.03596 (2024-07) — mine discriminative information from low-confidence samples via contrastive learning; prevents complete discard of potentially informative samples
- Energy Score-Based Selection: arXiv 2411.03959 (2024-11) — replaces simple confidence; better for long-tailed/imbalanced data

### H8. Self-Training for LLMs (2025–2026)
- High-confidence reasoning path selection: arXiv 2505.17454 (2025-05) — generate K paths; filter by reasoning-level (not answer-level) confidence; Policy Optimization via CORE-PO
- Lightweight verifier for reasoning traces: arXiv 2606.16811 (2026-06) — few-shot classifier on intermediate reasoning validity + entropy filtering; achieves 10–15× labeled-data-equivalent gains
- Reward hacking prevention: arXiv 2505.21444 (2025) — majority voting feedback can cause sudden collapse; hybrid real-synthetic + verification recommended
- Confidence: HIGH for all three [Smith #19]

### H9. Synthetic Data Verification
- External verifier prevents collapse from synthetic data alone: arXiv 2510.16657 (2025-10) — HIGH confidence
- Token-level editing of human text (semi-synthetic): arXiv 2412.14689 (2024-12) — avoids distributional shift of fully synthetic text; better collapse prevention; addresses n-gram over-concentration

### H10. Safeguards Summary Table [Smith #19]
| Safeguard | Mechanism | Typical Value | Status |
|---|---|---|---|
| Confidence threshold | High-conf only | 0.95 | Standard (FixMatch) |
| Real data mixing | Prevent collapse | ≥50–62% | Latest (2025) |
| Entropy filtering | Remove uncertain | entropy ≤ τ | Active (2024–2026) |
| Multi-view agreement | Consistency | ≥2 models agree | Robust |
| Temperature sharpening | Reduce noise | T ∈ [0.5, 1.0] | Standard |
| Early stopping | Signal preservation | IGCV criterion | Data-driven |
| Class-conditional threshold | Per-class balance | Adaptive | Recent (2023+) |
| Lightweight verification | Trace-level check | Few-shot classifier | LLM-era (2026) |

### H11. Potentially Outdated Sources [Smith #19]
- MixMatch (arXiv 1905.02249, 2019) — 7 years old
- ReMixMatch (arXiv 1911.09785, 2019) — 7 years old
- FixMatch (arXiv 2001.07685, 2020) — still de facto standard; check recent adaptive variants
- Self-Training Survey (arXiv 2202.12040, Feb 2022) — 4+ years old; may lack 2024–2025 innovations

---

## THEME I — DEEPCOMPRESSOR / SVDQUANT ARCHITECTURE PORTING
*Primary source: Smith #20*
- Paper: SVDQuant (ICLR 2025 Spotlight) — arXiv: 2411.05007
- Main Repo: nunchaku-ai/deepcompressor (last updated 2026-03-07)

### I1. Required Configuration Files

**I1.1 Model-Specific Config** (`/examples/diffusion/configs/model/{model_name}.yaml`)
- `pipeline.name` — model identifier
- `pipeline.dtype` — torch.float16, torch.bfloat16, etc.
- `eval.num_steps` — 4 (Schnell), 20 (SANA), 50 (dev models)
- `eval.guidance_scale` — 0 (Schnell), 4.5 (SANA)
- `quant.calib.batch_size` — 16–256
- `quant.wgts.skips` — layer names to exclude; typically 11–14 layers including "embed", "resblock_shortcut", "transformer_proj_in", "transformer_proj_out", "transformer_norm", "down_sample", "up_sample"
- `quant.ipts.skips` — input layers to skip
- Confidence: HIGH [Smith #20]

**I1.2 SVDQuant Algorithm Config** (`/examples/diffusion/configs/svdquant/__default__.yaml`)
- `quant.enable_smooth: true`
- `quant.wgts.enable_low_rank: true`
- `quant.wgts.low_rank.rank: 32` (default)
- `quant.wgts.low_rank.early_stop: true`
- Confidence: HIGH [Smith #20]

**I1.3 Precision Config** (`int4.yaml` or `nvfp4.yaml`)
- `quant.wgts.dtype: sint4` or `fvfp4` (NVIDIA FP4)
- `quant.ipts.dtype: sint4`
- `pipeline.shift_activations: true` — **required for SVDQuant**; shifts outliers from activations to weights
- Confidence: HIGH [Smith #20]

### I2. Calibration Data Requirements [Smith #20]
- Minimum: 128 samples — HIGH confidence
- Typical: 256 samples — HIGH confidence
- Full quality evaluation: 5,000+ samples (MJHQ-30K) — MEDIUM confidence
- Standard source: COCO Captions 2024 (randomly sampled prompts)
- Calibration command:
```bash
python -m deepcompressor.app.diffusion.dataset.collect.calib \
    configs/model/flux.1-schnell.yaml configs/collect/qdiff.yaml
```

### I3. Model Architecture Registration [Smith #20]
- `DiffusionPipelineConfig.register_pipeline_factory()` — custom model loaders
- `DiffusionPipelineConfig.register_text_extractor()` — text encoder extraction
- Source: `/deepcompressor/app/diffusion/pipeline/config.py`
- Confidence: HIGH

### I4. Currently Supported Models (as of 2026-03-07) [Smith #20]
- **Supported:** flux.1-dev, flux.1-schnell, flux.1-canny-dev, flux.1-depth-dev, flux.1-fill-dev (BFL); sana-1.6b (Alibaba); pixart-sigma; sdxl, sdxl-turbo
- **MISSING:** Qwen-based models — explicitly unsupported as of 2025-10-08 (GitHub Issue #752)
- Repo status: "hasn't been updated for a long time" (community feedback, MEDIUM confidence)
- Confidence: Supported list HIGH; Qwen exclusion HIGH [Smith #20]

### I5. SANA vs. FLUX Porting Comparison [Smith #20]
| Aspect | FLUX.1-Schnell | SANA-1.6B |
|---|---|---|
| Loading | `AutoPipelineForText2Image.from_pretrained()` | `SanaPipeline.from_pretrained()` with BF16 variant handling |
| Calibration batch | 16 | 256 (8× larger) |
| Inference steps | 4 | 20 |
| Skip list | 11 layers | 14 layers (includes `attn_add`, `ffn_add`) |
| Guidance scale | 0 | 4.5 |

SANA required specialized loading code (config.py lines 289–292); architecture-specific loading is required per model family.

### I6. Difficulty Assessment for Novel Architecture Porting [Smith #20]
- **Similar-to-existing (e.g., another FLUX variant):** Config changes only; "relatively easy to set up... taking a few hours on an H200 GPU" — GitHub Issue #752, 2025-10-08 — HIGH confidence
- **Truly novel:** Requires (1) identifying 11–14 skip layer names via architectural analysis; (2) registering pipeline factory; (3) potentially model-specific fused kernel work
- Nunchaku engine "gets much of its speed from model-specific fused execution paths (fused QKV, fused GELU/MLP) tied to each architecture's module layout and checkpoint format, so supporting a new model family usually requires model-specific integration work" — HIGH confidence
- **Overall difficulty: MEDIUM-HIGH for genuinely new architectures**

### I7. Recommended Path for New Architecture Porting (Smith #20)
1. Similar to existing FLUX variant → copy model config, adjust skip list, test with 128 calibration samples
2. Truly novel → use Nunchaku Lite + Diffusers (architecture-agnostic scanner; auto-detects transformer blocks → SVDQ W4A4; modulation linears → AWQ W4A16; HF blog ~2024-11, MEDIUM confidence)
3. Modifying DeepCompressor directly → register pipeline factory AND identify skip layer names manually

### I8. Repository Paths [Smith #20]
- Main: nunchaku-ai/deepcompressor (updated 2026-03-07)
- Quantization configs: /examples/diffusion/configs/
- Model definitions: /deepcompressor/app/diffusion/pipeline/config.py (lines 63–110)
- NN structures: /deepcompressor/app/diffusion/nn/struct.py (87 KB)
- Confidence: HIGH

---

---

# PART II: CORRECTIONS

## CORRECTION 1 — Smith #11: Summary Table Missing Item #16
Smith #11's body includes item #16 (Persistent Homology Design Space for 3D Point Clouds, arXiv 2604.04299, Apr 2026) but this entry is entirely absent from Smith #11's own summary table. The entry is valid and HIGH confidence. Included in full under Theme A2.7 above.

## CORRECTION 2 — Smith #12: Internal LoRA Rank Tension (Not a True Error)
Smith #12's body text states "LoRA rank: Typically 8–16 for efficient adaptation | MEDIUM confidence" while the table states "LCM-LoRA: Rank 64 | HIGH confidence." These appear contradictory but are not: rank 64 applies to full distillation tasks; rank 8–16 applies to fine-tuning already-distilled models. Both facts are valid. Smith #12's framing is ambiguous rather than wrong. Preserved with clarifying note above.

## CORRECTION 3 — Smith #14: Img2Img Parameter in Text-to-Image Code Template
Smith #14's primary code example (sourced from FLUX.2-Klein-LoRA-Studio lines 93–130) includes `image=input_image` in the `pipe(...)` call. This is an img2img-specific parameter. Including it in a text-to-image template will cause errors when no input image is available. Smith #14's second code example (4B distilled) correctly omits it. Both examples preserved; flagged for downstream users.

## CORRECTION 4 — Smith #17: "Zero-Shot" Definitional Inconsistency in Emuru
Smith #17 classifies Emuru (arXiv 2503.17074) as "zero-shot" while simultaneously stating it "requires 1 style image." Requiring any reference image at inference is conventionally one-shot, not zero-shot. Smith #17 itself acknowledges this tension ("True zero-shot would need 0 references"). Corrected framing: Emuru is a one-shot method (no per-font fine-tuning, but 1 reference image at inference). SFGN's zero-shot status remains MEDIUM confidence due to unclear reference requirements in available sources.

## CORRECTION 5 — Smith #11: TopoSinGAN Missing arXiv ID
Smith #11 lists TopoSinGAN without an arXiv ID in both the body and summary table (listed as "—"). Source is confirmed as MDPI Applied Sciences (doi: 10.3390/app14219944, October 2024). No arXiv preprint exists or has been located. Not an error per se, but Opus should note the absence when citing.

---

---

# PART III: DISPUTES

## DISPUTE 1 — Synthetic Data: Volume Parity vs. Collapse Threshold
**Smith #12 (HIGH confidence, arXiv 2305.12954, 2405.03243):** "Synthetic data needs ~10× volume to match real data performance when used alone."
**Smith #19 (HIGH confidence, arXiv 2410.04840, Oct 2024):** "1% synthetic data alone can trigger model collapse."

**Assessment:** These are not directly contradictory but create surface-level tension. They address different phenomena in potentially different model families and task types:
- Smith #12 addresses quality-parity volume thresholds in diffusion distillation contexts
- Smith #19 addresses contamination-triggered distributional collapse in self-training/generative contexts (potentially language models or generative models during iterative retraining)

**Opus should verify:** whether the collapse trigger (Smith #19) applies in the same regime as the volume guidance (Smith #12), or whether they concern different training paradigms. Both facts are preserved as stated.

## DISPUTE 2 — "Zero-Shot" Definition in Font Generation
**Smith #17:** Classifies methods requiring 1 reference image as "zero-shot" (Emuru as primary example).
**Standard ML convention:** Zero-shot = no examples at all at inference time.

**Assessment:** This is a genuine field-specific definitional inconsistency, not a stale-vs-fresh data issue. In font generation literature, "zero-shot" appears to mean "no per-font fine-tuning required" rather than "no reference image." No other Smith directly uses or contradicts this definition, but Smith #11 frames SFGN's reference requirement as MEDIUM confidence ("0 or minimal — unclear").

**Opus should establish a working definition** before integrating: the most defensible framing is "zero additional training on new fonts; may require 1 reference image at inference."

## DISPUTE 3 — FLUX.2 Multi-Reference Consistency Score (Unverified Metric)
**Smith #18 (MEDIUM confidence, selfielab blog Mar 2026):** "FLUX.2 scores 92/100 on consistency metrics, beating Midjourney V7 by 8 points in multi-pose tests."
**No other Smith corroborates this specific figure.**
**No primary research methodology disclosed in source.**

**Assessment:** Not a cross-Smith dispute, but a confidence concern. This figure comes from a third-party blog with no disclosed benchmark methodology. Opus should treat as indicative/anecdotal rather than authoritative.

## DISPUTE 4 — Qwen Version Confusion Risk (Not a Dispute, but Collision Risk)
**Smith #18:** EasyRef uses **Qwen2-VL-2B** as multi-reference aggregation LLM.
**Smith #13:** FLUX.2 Klein uses **Qwen3** as text encoder.

**Assessment:** These are factually correct and apply to completely different systems. However, because both Qwen versions appear in close proximity to FLUX.2-related research, there is a risk of conflation in synthesis. Both facts are preserved with explicit disambiguation above. Opus should maintain separation.

---

---

# PART IV: GAPS

## GAP 1 — Topology-Aware Losses Applied Directly to Font/Glyph Generation
Smith #11 covers topology-preserving losses for segmentation, 3D, and graph generation. Smith #11's glyph section covers stroke-level modeling methods. **No Smith covers the direct application of persistent homology losses or skeleton-based losses (from the general PH/skeleton section) to font or character generation models.** The intersection — using PH losses or Betti number constraints to supervise stroke correctness, glyph connectivity, or radical topology — is entirely uncovered across all 10 Smiths.

## GAP 2 — FLUX.2 Klein + SVDQuant/DeepCompressor Compatibility
Smiths #13 and #14 cover FLUX.2 Klein in depth. Smith #20 covers DeepCompressor/SVDQuant in depth. **No Smith addresses whether FLUX.2 Klein (with its Qwen3 text encoder, novel DiT architecture) can be ported to DeepCompressor.** Smith #20 explicitly notes Qwen-based models are unsupported (GitHub Issue #752, 2025-10-08). This is a direct, unaddressed operational question given the apparent focus on FLUX.2 Klein deployment. The Nunchaku Lite alternative (Smith #20) may provide a path but is only MEDIUM confidence.

## GAP 3 — Automated Stroke Topology Evaluation Metrics for Generated Characters
Smith #16 covers human evaluation protocols. Smith #11 covers topology-preserving losses. **No Smith covers automated metrics for evaluating stroke topology quality in generated characters** (e.g., correct stroke count, junction consistency, stroke order integrity, radical completeness). The NTC index from Smith #11 (TopoSinGAN) is the closest, but it addresses image-level node topology in natural images, not character-stroke topology specifically.

## GAP 4 — Self-Training Applied to Glyph/Font Generation Specifically
Smith #19 covers self-training safeguards broadly (LLMs, image models, time series). Smith #15 covers glyph conditioning + LoRA composition. **No Smith covers applying self-training or pseudo-labeling to glyph or font generation** — e.g., using generated characters as pseudo-labeled training data to iteratively improve a font generation model. The safeguards from Smith #19 would theoretically apply, but no evidence is cited for this domain.

## GAP 5 — End-to-End Training Cost for Combined Pipeline
Multiple Smiths cover partial costs: Smith #12 (distillation compute), Smith #13 (LoRA training VRAM), Smith #20 (calibration sample counts). **No Smith integrates these into a full pipeline cost estimate** covering topology-aware loss addition + multi-reference conditioning + glyph conditioning + LoRA fine-tuning of a distilled FLUX.2 Klein model simultaneously.

## GAP 6 — Multi-Language Font Generation Beyond CJK
Most papers across Smiths #11, #16, #17 focus on Chinese/CJK character generation. **Coverage of Arabic, Devanagari, Hebrew, Korean (non-CJK), Thai, or other complex script systems is sparse across all 10 Smiths.** HDGlyph (Smith #15, arXiv 2505.06543) addresses multi-language LoRA experts but does not detail non-CJK specifics. Frontiers VR Study (Smith #16) includes Japanese but at a surface level.

## GAP 7 — Real-Time Inference Latency for Combined Glyph + Multi-Reference + LoRA Stack
Smith #14 covers FLUX.2 Klein inference (4 steps). Smith #18 covers multi-reference conditioning. Smith #15 covers glyph conditioning. **No Smith addresses latency, throughput, or memory overhead when all three are combined** (glyph conditioning + multi-reference + LoRA) for production/real-time use.

## GAP 8 — GlyphDraw Specifically
Smith #15 explicitly notes: "NO EVIDENCE FOUND of papers directly studying TextFlux, FontFusion, UniGlyph, or GlyphDraw composed simultaneously with independently LoRA-fine-tuned base models." **GlyphDraw receives no dedicated coverage in any of the 10 Smiths** — neither its architecture, training procedure, nor compositional behavior.

## GAP 9 — Benchmark Jointly Evaluating Topology + Generation Quality
No Smith covers a benchmark suite that jointly evaluates **both** topology preservation AND visual generation quality for character generation models. MultiRef (Smith #18) benchmarks multi-reference fidelity. Smith #16 covers visual quality. Smith #11 covers topology loss objectives. No benchmark spans all three dimensions simultaneously.

---

---

# PART V: CROSS-SMITH AGREEMENTS (Highest-Confidence Convergent Signals)

## [AGREE 1] Qwen3 Text Encoder Is Frozen During FLUX.2 Klein LoRA Training
**[Smith #13, #14]** — Multiple independent sources (HF blog, SimpleTuner, Fizgig, kohya-ss) all confirm the Qwen3 text encoder in FLUX.2 Klein is frozen during LoRA fine-tuning. No contradicting source found anywhere. **Confidence: HIGH.**

## [AGREE 2] FLUX.2 Klein Distilled Models Use 4 Inference Steps and guidance_scale=1.0
**[Smith #13, #14]** — BFL official docs, HF model cards, and diffusers pipeline source code all independently confirm: 4 inference steps; guidance_scale=1.0 (pipeline explicitly ignores values >1.0 for distilled variants). **Confidence: HIGH.**

## [AGREE 3] Naive LoRA Composition Causes Interference Without Mitigation
**[Smith #15, #18]** — LILAC, QR-LoRA, CMLoRA, CLoRA, and EasyRef (addressing the averaging collapse problem) all confirm that naive LoRA merging or simple embedding averaging causes cross-concept interference or quality degradation. Mitigation methods exist (layer-wise isolation, orthogonal design, frequency routing, attention editing, MLLM-based aggregation). **Confidence: HIGH.**

## [AGREE 4] VecGlypher Generates SVG Via Autoregressive Token Prediction
**[Smith #11, #16]** — Both Smiths describe arXiv 2602.21461 (CVPR 2026) consistently: multi-modal LLM generates SVG path tokens autoregressively with no raster intermediate. Smith #11 frames this as topology preservation; Smith #16 frames this via R-ACC evaluation. Both framings are correct. **Confidence: HIGH.**

## [AGREE 5] Persistent Homology Scalability Was the Key Bottleneck (Now Partially Solved)
**[Smith #11, internal convergence]** — Multiple papers within Smith #11 independently establish: PH losses were previously impractical at scale due to compute cost and gradient discontinuities. arXiv 2501.14641 (ICLR 2025) specifically addresses this with GPU-parallelized subsampling and continuous gradients. **Confidence: HIGH.**

## [AGREE 6] Precomputed Prompt Embeddings Are Supported Across FLUX.2 Toolchains
**[Smith #13]** — Multiple independent toolchains (kohya-ss musubi-tuner, SimpleTuner, diffusers FLUX2 pipeline) all support `prompt_embeds` bypass and/or dedicated caching scripts. Embeddings are deterministic. Pre-computation avoids re-running Qwen3 per epoch or inference call. **Confidence: HIGH.**

## [AGREE 7] Real Data Outperforms or Stabilizes vs. Pure Synthetic in Training
**[Smith #12, #19]** — Both Smiths independently support real-data priority: Smith #12 states synthetic needs ~10× volume to match real data; Smith #19 states 1% synthetic alone can trigger collapse; Smith #19's accumulation strategy ("append, don't replace") prevents collapse. Both converge on the same directional guidance. **Confidence: HIGH** (with the caveat in DISPUTES §1 regarding different operational regimes).

## [AGREE 8] Font Generation Evaluation Is Converging on Pairwise + Likert with Expert Panels
**[Smith #16, internal convergence]** — Multiple 2024–2025 papers (FontAdapter, AI-Driven Typography, HFH-Font, Frontiers VR) independently use pairwise preference or 5-point Likert with three dimensions (Fidelity/Coherence/Usability) plus small expert panels (11 designers) + larger non-expert cohorts (46–93). This is an emerging community standard. **Confidence: HIGH.**

---

---

# DOCUMENT METADATA
- **Compiled by:** Anderson (Chain B Triage Layer)
- **Date:** 2026-07-27
- **Source Smiths:** #11 (topology losses), #12 (distillation), #13 (FLUX.2 Klein text encoder), #14 (FLUX.2 Klein inference code), #15 (glyph+LoRA composition), #16 (human eval fonts), #17 (zero-shot style adaptation), #18 (multi-reference conditioning), #19 (self-training safeguards), #20 (DeepCompressor porting)
- **Total unique papers catalogued:** 70+
- **Total arXiv IDs preserved:** 50+
- **Corrections issued:** 5
- **Disputes flagged:** 4
- **Gaps identified:** 9
- **Cross-Smith agreements:** 8
- **All arXiv IDs, GitHub links, confidence ratings, and quantitative metrics from source Smiths preserved verbatim unless correction noted above**
- **Intended recipient:** Opus (final synthesis)

---
**Oracle SDK Execution Metrics**
- Architecture: 20 Smiths -> 2 Andersons -> Opus (you)
- Total time: 1266s
- Total tokens: 341,423 (in: 136,264 | out: 205,159)
- Quota: 0.62% weekly (4.7% session)
- Smiths: 20 (0 errors)
- Andersons: 2 (0 errors)
- Phase timing: scout: 257s | compress: 1008s
- Phase costs: decompose: 0.00% | scout: 0.19% | compress: 0.43%

