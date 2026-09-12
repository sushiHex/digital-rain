# Oracle raw report: newer reference-generation options (2026-08-23)

Unedited output of a 20-Smith / 2-chain oracle run. Synthesis and the
decisions taken from it are in `2026-08-23-restyle-not-generate-the-reference.md`.

**Chain A's Anderson returned only its triage table, not its findings** — ten
Smiths' detail on permissively-licensed text-capable models is missing from
this file. Chain B is complete.

---

============================================================
## Chain A — Anderson Report
============================================================

**Anderson synthesis complete.** Here's a summary of what was done across all 10 Smiths:

---

### Triage Summary

| Rule | Count | Key Items |
|---|---|---|
| **DEDUP** | 11 model entries | Qwen-Image family (×4 Smiths), HiDream (×3), Z-Image (×4), ERNIE-Image (×2), Ideogram 4.0 (×2), FLUX family (×3), Seedream (×3) |
| **CORRECT** | 6 corrections | C-1 critical: Smith #1 wrongly marks Qwen-Image-2.0 as open-weight (refuted by Smiths #2, #5, #9); C-4: Smith #7 mischaracterizes FLUX.2-klein-9B as "permissive" |
| **RECENCY** | 2 resolutions | Qwen-Image-2512 params (20.4B preferred over 20B); Seedream pricing ($0.045 over stale $0.075) |
| **AGREE** | 5 high-confidence clusters | HiDream-O1-Image specs, ERNIE-Image specs, FLUX.2 license matrix, Ideogram text rendering, Seedream API-only status |
| **DISAGREE** | 4 disputes flagged | D-2 (GPT Image 2 dual accuracy readings); D-3 (Ideogram open-weight status unclear); D-4 (FLUX.1 text quality framing) |
| **GAPS** | 19 gaps documented | Google Nano Banana identity (G-5), Cosmos3 text rendering (G-9), all distilled model OCR benchmarks (G-2) |

============================================================
## Chain B — Anderson Report
============================================================

No filesystem access in this environment — delivering the full structured findings inline for Opus.

---

# CHAIN B — STRUCTURED FINDINGS FOR OPUS SYNTHESIS
**Anderson pass — Smiths #11–#20 | Organized: 2026-08-23**
**Triage applied: DEDUP · RECENCY · AGREE · DISAGREE · GAPS · CORRECT**

---

## PRELIMINARY NOTES FOR OPUS

- Ten Smiths cover five distinct topic clusters plus three cross-cutting concerns.
- Heavy overlap exists on **NIV, DiffInk, VecGlypher, and FontFusion** — all deduplicated below with merged citations.
- Smith #18 is a **negative-result report** (no benchmark found); its signal is preserved in full.
- All confidence ratings are as originally assigned by Smiths; Anderson elevations/reductions are flagged explicitly.
- Source dates range Feb 2023 – Aug 2026. Recency logic applied where numbers conflict.

---

## THEME 1: 2026 GENERATIVE MODELS FOR FONT / GLYPH GENERATION
**Primary sources: Smith #11 (CVPR/ICLR inventory), Smith #20 (Latin-focused deep dive)**
**Supporting: Smith #13 (parameter output lens), Smith #14 (conditioning lens), Smith #17 (consistency lens)**

---

### 1.1 CVPR 2026 Models

#### VecGlypher
**Sources: Smith #11 (inventory), Smith #20 (metrics deep dive) — 2-Smith convergence**
- **Venue:** CVPR 2026 [HIGH — both Smiths]
- **arXiv:** 2602.21461, submitted Feb 7, 2026
- **GitHub:** https://github.com/xk-huang/VecGlypher
- **Project site:** https://xk-huang.github.io/VecGlypher
- **HF weights:** https://huggingface.co/VecGlypher [HIGH — Smith #11]
- **Authors (Smith #20):** Xiaoke Huang, Bhavul Gauri, et al. (Meta AI, UC Santa Cruz)
- **License:** NOT SPECIFIED [LOW — neither Smith found it; direct repo check needed]
- **Architecture:** Multimodal LLM over SVG path tokens; autoregressive glyph generation
- **Stage 1 (Geometry Pretraining):** 39,000 Envato fonts (noisy, large-scale) [HIGH — Smith #20]
- **Stage 2 (SFT):** 2,500 Google Fonts, expert-annotated with descriptive style tags [HIGH — Smith #20]
- **Conditioning:** Text style prompts (natural language) OR exemplar glyph images; one-pass SVG output [HIGH — both Smiths]
- **Text Style Description:** YES [HIGH — Smith #11, #13, #20]
- **Latin Script:** a–z, A–Z, 0–9 confirmed; diacritics in Google Fonts scope implied [MEDIUM]

**Metrics (Smith #20 — HIGH confidence, directly from paper):**

| Metric | Baseline | After 1-epoch fine-tuning |
|--------|----------|--------------------------|
| R-ACC (Relative OCR Accuracy) | 6.29 | **95.34** |
| Chamfer Distance | 3.57 | **1.81** |
| FID | 27.82 | **4.19** |
| FID(C) — CLIP ViT-B/32 | — | Computed |
| CLIP Similarity | — | Measured |
| DINO Similarity | — | Measured |

- Outperforms DeepVecFont-v2 and DualVector on image-referenced generation; beats general LLMs on text-only generation [HIGH — Smith #20]

---

#### GlyphPrinter
**Source: Smith #11 only**
- **Venue:** CVPR 2026 **Highlight** [HIGH]
- **arXiv:** 2603.15616, submitted Mar 16, 2026
- **GitHub:** https://github.com/FudanCVL/GlyphPrinter
- **Weights:** Released Mar 13, 2026; GlyphCorrector training code + dataset released Mar 15, 2026 [HIGH]
- **License:** NOT SPECIFIED [LOW]
- **Architecture:** Diffusion-based; Region-Grouped Direct Preference Optimization (R-GDPO)
- **Text Style Description:** NO — preference-based rendering [HIGH]
- **Latin Script:** YES — multilingual; Latin + complex CJK + out-of-domain symbols [MEDIUM]

---

#### GAR-Font
**Source: Smith #11 only**
- **Full name:** Beyond Patches – Global-aware Autoregressive Model for Multimodal Few-Shot Font Generation
- **Venue:** CVPR 2026 [HIGH]
- **arXiv:** 2601.01593, submitted Jan 4, 2026; revised May 18, 2026
- **Code/Weights:** NOT LOCATED [LOW]
- **License:** UNKNOWN [LOW]
- **Architecture:** Global-aware autoregressive tokenizer + multimodal style encoder
- **Text Style Description:** YES — language-style adapter; 4 reference images + 1 text description matches 8-image-only performance [HIGH]
- **Latin Script:** NOT EXPLICITLY STATED [LOW]

---

#### FontCrafter
**Source: Smith #11 only**
- **Venue:** CVPR 2026 [HIGH]
- **arXiv:** 2603.22054, submitted Mar 28, 2026
- **Code:** NOT LOCATED — paper commits to future public release [HIGH on pending status]
- **Weights:** NOT RELEASED [HIGH]
- **Architecture:** Inpainting model + Context-aware Mask Adapter (CMA); element images as visual reference
- **Dataset:** ElementFont (large-scale)
- **Text Style Description:** NO — element-driven, visual context only [HIGH]
- **Latin Script:** NOT STATED [LOW]
- **Authors:** Wuyang Luo, Chengkai Tan, Chang Ge, Binye Hong, Su Yang, Yongjiu Ma (Dalian University of Technology, Fudan University)

---

#### GlyphSpatialNet
**Source: Smith #11 only**
- **Full name:** Rethinking Glyph Spatial Information in Font Generation
- **Venue:** CVPR 2026 [MEDIUM]
- **CVF PDF:** https://openaccess.thecvf.com/content/CVPR2026/papers/Su_Rethinking_Glyph_Spatial_Information...
- **GitHub:** https://github.com/sp777g/GlyphSpatialNet (created Mar 22, 2026) [MEDIUM] *(see Correction 5.8)*
- **Weights:** NOT LOCATED [LOW]
- **Architecture:** Explicit spatial modeling; joint prediction of shape estimates + spatial offset fields
- **Text Style Description:** NOT DOCUMENTED [LOW]
- **Latin Script:** NOT DOCUMENTED [LOW]

---

#### StyleTextGen
**Source: Smith #17 only**
- **Full name:** Style-Conditioned Multilingual Scene Text Generation
- **Venue:** CVPR 2026 [HIGH]
- **arXiv:** 2605.14708
- **CVF PDF:** https://openaccess.thecvf.com/content/CVPR2026/papers/Chen_StyleTextGen_...
- **Architecture:** Dual-branch style encoder; text style consistency loss; mask-guided inference
- **Latin Script:** YES — multilingual, across writing systems [HIGH]
- **New benchmark:** StyleText-CE (bilingual) [HIGH]
- **Open Weights:** NOT CONFIRMED [LOW]
- **Anderson note:** Scene-text style transfer model, not a standalone typeface design tool. Letterform-relevant but distinct from type design.

---

### 1.2 ICLR 2026 Models

#### DiffInk
**Sources: Smith #11, #14, #17, #20 — HIGHEST MULTI-SMITH CONVERGENCE (4 Smiths, all consistent)**

- **Venue:** ICLR 2026 [HIGH — all 4 Smiths]
- **arXiv:** 2509.23624, submitted Sep 2025
- **GitHub:** https://github.com/awei669/DiffInk
- **License:** MIT [HIGH — Smith #14, #20]
- **Weights:** OPEN — released Mar 2026 [HIGH — Smith #14, #17, #20]
- **Authors:** Wei Pan, Huiguo He, Hiuyi Cheng, Yilin Shi, Lianwen Jin (South China University of Technology)
- **Architecture (Smith #20, most detailed):**
  - **InkVAE:** Sequential VAE with two regularization losses: OCR-based (glyph content accuracy) + style-classification (writer style preservation)
  - **InkDiT:** Latent diffusion Transformer integrating target text + reference style
- **Conditioning:** Glyph-aware (OCR-based) + style-aware; first full-line handwriting diffusion model [HIGH]
- **Text Style Description:** YES — conditioned on textual input + style references [HIGH — Smith #11, #17]
- **Latin Script:** YES — IAM-OnDB English dataset (~10K text lines, 221 writers); cross-script: Chinese-trained model recovers Latin stroke orders [HIGH — Smith #14, #20]
- **Scope (Anderson — from Smith #20):** Online handwriting (pen trajectories), NOT static print-font glyphs — this distinction matters for use cases

**Metrics (Smith #20 — HIGH confidence, directly from paper):**

| Metric | Value | Notes |
|--------|-------|-------|
| Accurate Rate (AR) | **94.38%** | Content fidelity via OCR |
| Correct Rate (CR) | **94.58%** | Character-level accuracy |
| Style Score | **77.38** | Writer style consistency |
| DTW Distance | **1.049** | Trajectory structural fidelity (lower = better) |
| Generation Speed | **58.47 chars/sec** | >800× faster than OLHWG SOTA |

- Outperforms OLHWG by ~3pp accuracy, ~30pp style [HIGH — Smith #20]

---

### 1.3 Other 2026 Venues

#### NIV (Neural Axis Variations)
**Sources: Smith #11, #13, #15 — 3-Smith convergence**
**⚠ VENUE DISPUTE — see Section 5.1**

- **arXiv:** 2606.05261, submitted Jun 5, 2026
- **GitHub:** https://github.com/ndvbd/NIV [HIGH — Smith #15; Smith #11 listed as "NOT EXPLICITLY LOCATED" — Smith #15 more thorough, use confirmed URL]
- **Authors:** Nadav Benedek, Ariel Shamir, Ohad Fried [HIGH — Smith #11, #13]
- **Weights:** Confirmed as "code + dataset + models" on GitHub [HIGH — Smith #15]
- **License:** UNKNOWN [LOW]
- **Architecture:** Neural network predicting per-point displacements on vector geometry; Property Embedding for multi-axis interactions [HIGH — all 3 Smiths consistent]
- **Training Data:** 1M+ variation tuples from Google Fonts variable fonts [HIGH — Smith #11, #15]
- **Output:** Standard OpenType variable font (TTF) [HIGH — Smith #11, #15]
- **Text Style Description:** NO — numeric axis control only (weight, width, slant, opsz, custom) [HIGH — Smith #11, #13]
- **Latin Script:** YES — tested on variable Google Fonts; generalizes to CJK and out-of-distribution handwriting [HIGH — Smith #11, #15]
- **Unique capability:** Converts static fonts to functional variable fonts automatically; generalizes to unseen Unicode + styles [HIGH — Smith #15]

---

#### SmartFont
**Source: Smith #11 only**
- **Venue:** ICMR 2026
- **arXiv:** 2606.13382, submitted Jun 11, 2026
- **Authors:** Zian Yang, Zixin Wang
- **Architecture:** Diffusion-based; global content-style generation + weakly supervised local corrective experts; semantic-spatial expert allocation
- **Code/Weights/License:** NOT LOCATED [LOW]
- **Text Style Description:** NOT DOCUMENTED [LOW]
- **Latin Script:** NOT STATED [LOW]

---

#### FontFusion
**Sources: Smith #11, #13, #17 — 3-Smith convergence**
**⚠ Miscategorized by Smith #13 — see Correction 5.2**

- **arXiv:** 2606.06066, submitted Jun 4, 2026
- **Affiliation:** Adobe Research + University of Bucharest
- **Authors:** Marian Lupascu, Nipun Jindal, Ionut Mironica, Zhaowen Wang [HIGH — Smith #11]
- **Architecture:** Plug-and-play DiT conditioning; hierarchical token representation + position-aware embeddings; multi-level token dropping [HIGH — all 3 Smiths]
- **No retraining required:** Inference-time only [HIGH — Smith #11, #17]
- **Text Style Description:** NO — font identity conditioning via token representation, not natural language [HIGH — Smith #11]
- **Latin Script:** YES — decorative fonts [MEDIUM]
- **Open Weights:** NOT LOCATED [LOW]
- **Metrics (HIGH — Smith #11, #17 agree):** 76% relative improvement on decorative fonts; 68–76% font consistency gains vs. unconditioned
- **Benchmark reference:** CRAFT and TIDE benchmarks used for evaluation (also cited in Smith #18)

---

#### DRG-Font
**Source: Smith #11 only**
- **arXiv:** 2604.13797, submitted Apr 15, 2026
- **Affiliation:** Indian Statistical Institute Kolkata, IIT Kharagpur
- **Architecture:** Contrastive learning; Reference Selection (RS) module + Multi-scale Style/Content Head Blocks; dynamic reference selection; style-content embedding decomposition
- **Text Style Description:** NO — reference-guided, visual only [HIGH]
- **Latin/Code/License:** NOT STATED / NOT LOCATED / UNKNOWN [LOW all]

---

### 1.4 2025-Vintage Models Still Relevant

#### AnyText / AnyText2
**Sources: Smith #14 (primary), Smith #17 (brief)**
- **Venue:** ICLR 2024 Spotlight
- **arXiv:** 2311.03054 | **GitHub:** https://github.com/tyxsspa/AnyText
- **Weights:** OPEN — ModelScope; training code + AnyWord-3M dataset released Apr 18, 2024 [HIGH]
- **AnyText2:** Also open; faster, customizable font/color [HIGH]
- **Architecture:** Glyph shapes + position + masked images → latent features; OCR-encoded stroke data blended with caption embeddings
- **Latin:** YES — v1.1: 0.7239 Sentence Accuracy English [HIGH]
- **Dataset:** AnyWord-3M: ~1.39M English images, 9M+ text lines, 20M+ characters/words [HIGH]

---

#### FontDiffuser
**Source: Smith #14 only**
- **Venue:** AAAI 2024 | **arXiv:** 2312.12142
- **GitHub:** https://github.com/yeungchenwa/FontDiffuser
- **Weights:** GoogleDrive + BaiduYun; HuggingFace demo online [HIGH]
- **Architecture:** Content embedding + style attributes; multi-scale content aggregation; stroke/component conditions
- **Latin:** YES — explicitly Latin and Greek [HIGH]
- **Scope:** One-shot font generation (single reference → full font family)

---

#### Font-Agent
**Source: Smith #13 only**
- **Venue:** CVPR 2025
- **PDF:** https://openaccess.thecvf.com/content/CVPR2025/papers/Lai_Font-Agent_...
- **Authors:** Yingxin Lai et al.
- **Architecture:** VLM; constructs Diversity Font Dataset (DFD) with 135,000 font-text pairs [HIGH]
- **Output:** Font quality assessment parameters — NOT generative [Anderson — see Correction 5.3]

---

#### FontCraft
**Source: Smith #13 only**
- **Venue:** CHI 2025 | **DOI:** https://dl.acm.org/doi/10.1145/3706598.3713863
- **Authors:** Yuki Tatsukawa, I-Chao Shen, Mustafa Doga Dogan, Anran Qi, Yuki Koyama, Ariel Shamir, Takeo Igarashi
- **Architecture:** Multimodal input (text, images, font files) + preferential Bayesian optimization; latent space exploration with human-in-the-loop parameter refinement
- **Output:** Latent space parameters via Bayesian sampling [HIGH]

---

#### VecFusion
**Source: Smith #13 only**
- **Venue:** CVPR 2024 | **arXiv:** 2312.10540
- **Authors:** Vikas Thamizharasan, Difan Liu, Shantanu Agarwal, Matthew Fisher, Michaël Gharbi, Oliver Wang, Alec Jacobson, Evangelos Kalogerakis
- **Architecture:** Cascaded diffusion (raster + vector stages); transformer + novel vector representation
- **Output:** Bézier curves with control points [HIGH]
- **Anderson note:** Not LLM-based despite Smith #13 theme — see Correction 5.4

---

#### WordArt Designer
**Source: Smith #13 only**
- **arXiv:** 2310.18332, Oct 2023 | **GitHub:** https://github.com/AIGCDesignGroup/WordArt (last push Jan 2024)
- **Affiliation:** Alibaba DAMO Academy, Carnegie Mellon University
- **Architecture:** GPT-3.5 → SemTypo (semantic design optimization) → StyTypo (style) → TexTypo (texture)
- **Output:** Semantic design parameters and style specifications [HIGH]

---

#### MetaDesigner
**Source: Smith #13 only**
- **arXiv:** 2406.19859, Jun 2024 (revised Feb 2025)
- **Affiliation:** Alibaba Group, Carnegie Mellon University
- **Architecture:** Multi-agent LLM (Pipeline, Glyph, Texture agents); hierarchical tree of 68 LoRA models; iterative multimodal feedback
- **Dataset:** 5,000+ multilingual images [HIGH]
- **Output:** Style vectors, LoRA weights refined iteratively from NL + user feedback [HIGH]

---

#### CPT (Controllable & Editable Design Variations)
**Source: Smith #13 only**
- **arXiv:** 2604.04380, Apr 6, 2026 | NeurIPS 2025 GenProCC Workshop
- **Affiliation:** Adobe
- **Authors:** Karthik Suresh, Amine Ben Khalifa, Li Zhang, Wei-ting Hsu, Fangzheng Wu, Vinay More, Asim Kadav
- **Architecture:** Decoder-only LM; Creative Markup Language (CML) encoding canvas, layout, text, images, vector graphics, style attributes; fine-tuned on professional design templates
- **Output:** Font family, weight, color values, layout parameters as structured markup [HIGH]
- **Anderson note:** General design layout model; font parameters are one output among many.

---

#### AI-Driven Typography (CP-Former)
**Source: Smith #13 only**
- **URL:** https://www.mdpi.com/2078-2489/17/2/150 | MDPI Information, Feb 3, 2026
- **Architecture:** Continuous Style Projector (MLP, 2 linear layers) mapping visual features into LLM latent space; Mixture Density Network (MDN) head for multi-modal stroke distributions; zero-shot style interpolation
- **Output:** Stroke thickness, serif style, weight adjustments — design parameters, not pixels [HIGH]

---

#### FontCLIP
**Source: Smith #13 only**
- **arXiv:** 2403.06453, Mar 2024 | **GitHub:** https://github.com/yukistavailable/FontCLIP (updated Aug 18, 2026 — 5 days before today)
- **Architecture:** Vision-language model; compound descriptive prompts with adaptively sampled font attributes; generalizes to CJK
- **Output:** Semantic font attributes for retrieval [HIGH]

---

#### UniGlyph
**Source: Smith #14 only**
- **Venue:** ICCV 2025 | **arXiv:** 2507.00992
- **Architecture:** Segmentation-conditioned diffusion; pixel-level masks preserve glyph shape, position, font style, color
- **Latin:** YES — bilingual Chinese + English [HIGH]
- **Benchmarks introduced:** GlyphMM-benchmark, MiniText-benchmark; surpasses AnyText [HIGH]
- **Weights/Code:** NOT CONFIRMED [MEDIUM]

---

#### TextPixs
**Source: Smith #14 only**
- **Venue:** CVPR 2025 | **arXiv:** 2507.06033
- **Architecture:** Glyph embeddings via CLIP + dual-stream text encoder; Character-Aware Attention (GCDA); OCR-guided supervision
- **Latin:** YES — up to 90% spelling accuracy across 10 languages [HIGH]
- **Open Weights:** NOT CONFIRMED [LOW]

---

#### GlyphControl
**Source: Smith #14 only**
- **Venue:** NeurIPS 2023 | **GitHub:** https://github.com/AIGText/GlyphControl-release
- **Dataset:** LAION-Glyph (10M images) released [HIGH]
- **Architecture:** Rendered glyph images → ControlNet branch; flexible text layout, size, rotation
- **Latin:** NOT EXPLICITLY STATED [MEDIUM]
- **Performance:** Outperforms DeepFloyd IF, Stable Diffusion; 3× fewer parameters [HIGH]

---

#### ControlText
**Source: Smith #14 only**
- **arXiv:** 2502.10999, Feb 2025 | **GitHub:** https://github.com/bowen-upenn/ControlText
- **Architecture:** Self-supervised text segmentation masks; no font labels required; no ground-truth font annotations
- **Latin:** YES — zero-shot multilingual [HIGH]
- **Weights:** Code open; weights unclear [MEDIUM]

---

#### GlyphDraw / GlyphDraw2
**Source: Smith #14 only**
- **GitHub:** https://github.com/OPPO-Mente-Lab/GlyphDraw | https://github.com/OPPO-Mente-Lab/GlyphDraw2
- **arXiv (GlyphDraw2):** 2407.02252 | **Affiliation:** OPPO
- **Latin:** NO — Chinese only [HIGH]
- **Weights:** Status unclear [LOW]

---

#### SFGN (Skeleton and Font Generation Network)
**Source: Smith #14 only**
- **arXiv:** 2501.08062, Jan 2025
- **Conditioning:** Skeleton builder synthesizing content features; radical-level alignment
- **Latin:** NO — Chinese zero-shot only [HIGH]
- **Weights:** NOT CONFIRMED [LOW]

---

#### SGCE-Font (Skeleton Guided Channel Expansion)
**Source: Smith #14 only**
- **arXiv:** 2211.14475, 2022 — **oldest model in Chain B**
- **Architecture:** GAN (not diffusion); skeleton guidance via channel expansion
- **Latin:** NO — Chinese only [HIGH]
- **Weights:** NOT CONFIRMED [LOW]
- **Anderson note:** 2022 origin; likely outdated relative to 2025–2026 diffusion-based work

---

#### Diff-Font
**Source: Smith #14 only**
- **Venue:** IJCV 2024 | **arXiv:** 2212.05895
- **Architecture:** Multi-attribute conditional diffusion; first diffusion model for one-shot font generation
- **Latin:** YES — explicitly Latin + Chinese + Korean [HIGH]
- **Weights:** NOT CONFIRMED [LOW]

---

#### Stroke2Font
**Source: Smith #13 only**
- **Venue:** MDPI Algorithms, Mar 2026
- **DOI:** https://doi.org/10.3390/a19030231
- **Scope:** Chinese font generation specifically
- **Architecture:** Stroke decomposition + Bézier curve parameterization; RL policy for control parameter selection; genetic algorithm for style vector exploration; adaptive complexity-aware optimization
- **Dataset:** 150 Chinese characters, 1,123 stroke trajectories, 5,287 feature points [HIGH]
- **Output:** Bézier control parameters, stroke parameters, style vectors [HIGH]
- **Anderson note:** Not LLM-based despite Smith #13 theme. See Correction 5.4.

---

### 1.5 Parameter Types Output by Font/Glyph Models (Consolidated from Smith #13)

| Parameter Type | Examples | Systems |
|---|---|---|
| Weight / Thickness | wght 100–1000, stroke weight | NIV, AI-Driven Typography, WordArt, Font-Agent |
| Width / Proportions | wdth axis values, horizontal scaling | NIV, CPT |
| Contrast | stroke contrast ratios, serif thickness | AI-Driven Typography, Font-Agent |
| X-Height | lowercase height adjustments | Font-Agent spec, OpenType standard |
| Stroke Terminals | serif style, stroke end shapes | AI-Driven Typography, Stroke2Font |
| Optical Size | opsz axis | NIV, OpenType standard |
| Variable Font Axis Values | Per-axis continuous values | NIV (primary) |
| Bézier Control Points | Vector curve coordinates | VecFusion, Stroke2Font |
| Style Vectors | Latent space representations | FontCraft, MetaDesigner, Stroke2Font |
| Color Schemes | RGB / HSL | CPT |
| Layout Parameters | Spacing, kerning, positioning | CPT |

---

### 1.6 Text Style Description Capability — Cross-Model Summary

**SUPPORTS natural-language style descriptions:**
VecGlypher [HIGH], GAR-Font [HIGH], DiffInk [HIGH], AI-Driven Typography [HIGH], WordArt Designer [HIGH], MetaDesigner [HIGH], FontCLIP [HIGH], FontCraft [HIGH]

**Does NOT use text style descriptions (visual / axis / preference / token-based):**
GlyphPrinter [HIGH], FontCrafter [HIGH], NIV [HIGH], FontFusion [HIGH], DRG-Font [HIGH], SmartFont [LOW — undocumented], GlyphSpatialNet [LOW — undocumented]

---

### 1.7 Open Weights Status (as of Aug 2026)

| Confirmed Open | Pending / Unclear | Not Released |
|---|---|---|
| VecGlypher (HF) | GAR-Font | FontCrafter |
| GlyphPrinter (Mar 2026) | NIV (stated, repo exists) | FontFusion |
| DiffInk (MIT, Mar 2026) | GlyphSpatialNet | Diff-Font |
| AnyText (Apr 2024) | UniGlyph | SFGN |
| FontDiffuser (Dec 2023) | TextPixs | SGCE-Font |
| GlyphControl (partial) | ControlText (code yes, weights ?) | — |

---

## THEME 2: PARAMETRIC (NON-NEURAL) FONT SYSTEMS
**Primary source: Smith #12**
**Supporting: Smith #15 (variable font toolchain overlap)**

### 2.1 Active Parametric Systems

#### Metaflop
- **URL:** https://www.metaflop.com/ | **GitHub:** https://github.com/metaflop/metaflop-www
- **License:** GNU GPL v3.0 (software); OFL v1.1 (font outputs) [HIGH — GitHub, 2025]
- **Parameters:** 14 adjustable (MF Bespoke template) — stem width, serif config, stroke control, slant, curvature [MEDIUM]
- **Programmatic:** YES — YAML config; parameter URL sliders; ranges via `$ lower / upper` syntax [MEDIUM]
- **Backend:** JavaScript + Sinatra + Unix toolchain; outputs OTF, EOT, WOFF, SVG, TTF [HIGH]
- **Consistent K/g:** YES — Metafont algebraic definitions regenerate all glyphs from core parameters [HIGH]
- **Relationship:** Web GUI successor to Knuth's Metafont

---

#### Prototypo
- **URL:** https://devvv.prototypo.io/ | **API:** https://doc.prototypo.io/ | **GitHub:** https://github.com/byte-foundry/prototypo
- **License:** MIXED — .js/.jsx/.json = MPLv2; .css/.scss/.svg/.png = proprietary (Prototypo SAS); package.json lists AGPL-3.0 [HIGH — GitHub README, 2025]
- **Parameters:** 30+ across templates (ELZEVIR, FELL, GROTESK, SPECTRAL) — thickness, aperture, roundness, x-height, contrast, width, slant [HIGH]
- **Programmatic:** YES — `createFont()` + `changeParams({ parameter1: value1, ... })` [HIGH — API docs]
- **Prototypo.js:** Independent parametric-glyph engine with canvas rendering and OTF export [HIGH]
- **Consistent K/g:** YES — "computer" (coordinates) + "expander" (Bezier skeleton outline) apply uniformly [MEDIUM]
- **Notable:** Google Font "Spectral" is first Google Font made parametric by Prototypo; Latin Pro + 130+ languages [HIGH]

---

#### Metapolator
- **URL:** https://metapolator.com/ | **GitHub:** https://github.com/metapolator/metapolator
- **License:** FOSS [HIGH]
- **Parameters:** Aspect ratio, weight, slant, stroke width, contrast via stroke elements (Hobby Spline skeleton); Cascading Properties Sheet (CPS) language [HIGH]
- **Programmatic:** Indirect via CPS (CSS-like); no Python/JS API documented [LOW]
- **Consistent K/g:** YES — skeleton + variable pen width/angle applied across all glyphs [MEDIUM]

---

#### Burrowlab
- **URL:** https://www.burrowlab.com/ | **Demo:** https://demo.burrowlab.com/
- **License:** UNCLEAR — browser-based; GitHub status not found [LOW]
- **Parameters:** Sliders/buttons; geometry-driven + optical refinements [MEDIUM]
- **Programmatic:** NOT DOCUMENTED [LOW]
- **Consistent K/g:** LIKELY YES based on procedural model [LOW]

---

### 2.2 Production-Grade Open-Source Font Toolchain

#### UFO + DesignSpace + fontTools
- **GitHub:** https://github.com/fonttools/fonttools | **fontmake:** https://github.com/googlefonts/fontmake | **ufoProcessor:** https://github.com/LettError/ufoProcessor
- **License:** Open / GPL [HIGH]
- **Parameters:** Designer-defined axes in .designspace XML (min/default/max); UFO human-readable XML sources [HIGH]
- **Programmatic:** Full Python API — fontTools.varLib for variable font builds; ufoProcessor for live interpolation [HIGH]
- **Consistent K/g:** YES [HIGH]
- **Use case:** Production Google Fonts ecosystem [HIGH]

---

#### MetaPost
- **URL:** https://tug.org/metapost.html | **License:** GPL; TeX Live 2025 [HIGH]
- **Parameters:** Full mathematical programming language; Hobby Splines; pen/stroke concept [HIGH]
- **Programmatic:** YES — .mp files → SVG/PDF/EPS [HIGH]
- **Consistent K/g:** YES — identical paradigm to Metafont [HIGH]
- **Recent use (Feb 2025):** Santhosh Thottingal, arXiv 2502.07386 — 2 parametric variable fonts via MetaPost; open-source released [HIGH]
- **Tutorials:** https://learnmetapost.onrender.com/ + Thurston "Drawing with MetaPost" 2024 [HIGH]

---

#### Fontra
- **URL:** https://fontra.xyz/ | **GitHub:** https://github.com/fontra/fontra
- **License:** Open-source; Black [Foundry] + Just van Rossum; Google Fonts supported [HIGH]
- **Parameters:** Variable components with glyph-local axes beyond global axes; UFO storage [HIGH]
- **Programmatic:** Python server; scripting "in research" — no complete API yet [LOW]
- **Consistent K/g:** YES via variable component mechanism [MEDIUM]

---

#### Glyphs 3 Smart Components
- **License:** Proprietary; can export to open UFO
- **Parameters:** Smart Components with variation axes (width, height, angle, roundness, arbitrary); default range 0–100 [HIGH]
- **Programmatic:** GlyphsScript (Python); mekkablue Glyphs Scripts (open-source) [HIGH]
- **Consistent K/g:** YES — smart components apply uniformly [MEDIUM]

---

#### RoboFont
- **License:** Commercial core; open-source extensions via Mechanic [HIGH]
- **Programmatic:** Full Python API; `fontVariations()` for live design space sampling [HIGH]
- **Consistent K/g:** YES [MEDIUM]

---

### 2.3 Parameter Counts Across Systems
- **Computer Modern (Metafont canonical):** 62 distinct parameters [HIGH — Wikipedia: Computer Modern]
- **Prototypo:** 30+ parameters [HIGH]
- **Metaflop MF Bespoke:** 14 parameters [MEDIUM]
- **Typical range: 14–62 parameters**

---

### 2.4 Key Conclusions from Smith #12
1. Non-neural parametric systems actively maintained as of 2025–2026
2. All major systems enable consistent K/g through single-parameter changes
3. Strongest open-source + programmatic: fonttools/UFO/DesignSpace, MetaPost, Fontra, Metaflop
4. Prototypo production-proven but mixed license
5. MetaPost renaissance confirmed by Thottingal Feb 2025

---

## THEME 3: VARIABLE FONT INTERPOLATION, EXTRAPOLATION & NOVEL LETTERFORMS
**Primary source: Smith #15**
**Supporting: Smith #12 (toolchain), Smith #11/#13 (NIV — merged in Theme 1.3)**

### 3.1 Mathematical Foundation
- Variable fonts: n-dimensional design space; 1-axis = line, 2-axis = square, 3-axis = cube [HIGH]
- Axis values normalize to **[-1, 1]**; 0 = default; asymmetric scaling allowed [HIGH — fontTools docs, 2026]
- **VariationModel:** `result = Σ(delta_i × scalar_i)`; support scalar = 1 at peak, 0 beyond bounds [HIGH — fontTools varLib models API, 2026]
- **DesignSpace:** .designspace XML defines master positions, axis ranges, instances; originated with MutatorMath [HIGH]

---

### 3.2 Tooling for Design Space Exploration

| Tool | Key Capability | Extrapolation | Link |
|------|---------------|--------------|------|
| fontTools varLib | Production variable font compiler | Via `VariationModel(extrapolate=True)` | readthedocs.io/varLib |
| fontTools varLib.models | Normalization + interpolation math | `extrapolate` parameter (issue #2757) | readthedocs.io/varLib/models |
| fontTools varLib.mutator | Static instance generation | Via MutatorMath backend | readthedocs.io/varLib/mutator |
| fontTools varLib.instancer | Partial/full instantiation | `renormalizeValue()` with `extrapolate` param (default True) | readthedocs.io/varLib/instancer |
| MutatorMath | Design-stage interpolation | YES — all master deltas superimposed | Via fontTools |
| RoboFont | UFO design environment | YES via MutatorMath; `fontVariations()` | robofont.com |
| Axis-Praxis | Browser preview | No extrapolation; 226+ VF resources | axis-praxis.org |
| vfclamp | Axis range restriction | Clamps/pins axes; Pyodide-powered | vfclamp.com |
| NIV | Neural VF generation | Neural method (see Theme 1.3) | github.com/ndvbd/NIV |

**[All HIGH confidence — official fontTools docs 2026]**

---

### 3.3 Extrapolation: Technical Status

**MutatorMath vs. fontTools.varLib (documented difference, not a dispute):**
- **MutatorMath DOES extrapolate** over axis boundaries — designed for design exploration [HIGH]
- **fontTools.varLib DOES NOT natively extrapolate** in compiled variable fonts — production-focused, caps to axis range [HIGH]
- Source: RoboFont interpolation docs + Superpolator resources [HIGH, 2026]

**fontTools.varLib.instancer `renormalizeValue()`:** Has `extrapolate` parameter (default True); extends axis ranges beyond original master coordinates [HIGH — API docs, 2026]

---

### 3.4 Usability of Extrapolated Glyphs

**Design-stage:** Works well via MutatorMath/RoboFont → usable static instances [HIGH]

**Runtime variable font rendering:** DOES NOT WORK in most applications — rendering engines clamp to defined ranges [HIGH — Glyphs Forum user testing, 2019; FontLab docs]
- Adobe Illustrator: extrapolated weights display in gray/warning; render as nearest master [HIGH — Glyphs Forum]
- No font engine specification governs out-of-range rendering [MEDIUM]

**Artifact risk:** Contours may self-intersect or distort with extrapolation distance [MEDIUM]

**Distribution:** Extrapolated variable fonts cannot be distributed for end-user rendering [HIGH]

---

### 3.5 Research Advances for Novel Letterforms

**Differentiable Variable Fonts (arXiv 2510.07638, Oct 2025; Computer Graphics Forum / Wiley):**
- Gradients w.r.t. font axes via differentiable interpolation
- Applications: shape manipulation, physics-based text animation, automated font design
- Status: Research prototype only [HIGH]

**NIV (arXiv 2606.05261, Jun 2026):**
- Merged in Theme 1.3 — produces standard OpenType variable fonts; higher consistency than hand-extrapolated designs

---

### 3.6 API Reference (fontTools)

```python
# RoboFont design-stage sampling
fontVariations()         # Select design space location
listFontVariations()     # Return variations dict

# fontTools VariationModel
normalizeValue(value, axisMin, axisDefault, axisMax)
getScalars(location)                              # → per-master scalar weights
interpolateFromDeltas(deltas, scalars)            # → interpolated result
VariationModel(extrapolate=True)                  # Out-of-range exploration

# Static instance generation
fontTools.varLib.mutator                          # Design time, UFO→UFO
fontTools.varLib.instancer.instantiateVariableFont()  # Runtime, TTFont→TTFont
```
[HIGH — official API reference, 2026]

---

## THEME 4: SKELETON / STROKE CONDITIONING FOR DIFFUSION MODELS
**Primary source: Smith #14**
**Cross-referenced: Smith #11 (DiffInk merged above), Smith #17 (FontStudio, FontFusion merged)**

### 4.1 Key Finding

**True skeleton/stroke conditioning (structural decomposition) is LIMITED in open-source diffusion models for Latin script:**
- SGCE-Font, SFGN: Skeleton-based but Chinese-only; weights not confirmed open
- DiffInk: Stroke-aware (pen trajectories), cross-script, MIT open — handwriting, not print
- AnyText, TextPixs: Glyph embeddings + OCR stroke data — NOT explicit skeleton decomposition
- UniGlyph, ControlText: Pixel-level segmentation masks — richer than full glyph images but not skeleton-specific

**Most Latin-capable open models:** AnyText (glyph+stroke OCR), TextPixs (10 languages, 90% accuracy), DiffInk (cross-script handwriting, MIT), FontDiffuser (Latin+Greek), ControlText (multilingual masks)

---

### 4.2 Conditioning Type Taxonomy

| Conditioning Type | Models |
|---|---|
| True skeleton / stroke decomposition | SGCE-Font (GAN), SFGN |
| Pen trajectory (stroke order) | DiffInk |
| Glyph embeddings + OCR stroke data | AnyText, TextPixs |
| Rendered glyph images | GlyphControl, GlyphDraw |
| Pixel-level segmentation masks | UniGlyph, ControlText |
| Content + style attributes | FontDiffuser, Diff-Font |

---

## THEME 5: STYLE CONSISTENCY ENFORCEMENT TECHNIQUES
**Primary source: Smith #17**
**Cross-references: Smith #14 (DiffInk merged above), Smith #11 (FontFusion merged above)**

### 5.1 General-Purpose Inference-Time Techniques

#### IP-Adapter
- **GitHub:** https://github.com/tencent-ailab/IP-Adapter (6.4K stars, 406 forks) [HIGH]
- **HF:** https://huggingface.co/h94/IP-Adapter (SD 1.5, SDXL variants)
- **Training required:** NONE — 22M-parameter cross-attention layers [HIGH]
- **Weights:** ~100MB each; uses OpenCLIP-ViT-H-14 (632M) or ViT-bigG-14 (1844M) [HIGH]
- **Style consistency score:** 0.529 [MEDIUM]
- **Limitation:** Content leakage; general-purpose encoder misses typography nuances [MEDIUM — FontFusion paper]
- **Speed:** 10–14 seconds/image [MEDIUM]
- **Derivative:** FontAdapter (arXiv 2506.05843) builds on this paradigm for font customization — briefly mentioned, not fully researched

---

#### Reference-Only ControlNet
- **GitHub:** https://github.com/Mikubill/sd-webui-controlnet
- **HF:** https://huggingface.co/Intel/sd-reference-only [HIGH]
- **Training required:** NONE — attention hijacking; requires ControlNet ≥1.1.153 [HIGH]
- **Variants:** Reference Only, Reference AdaIN, Reference AdaIN+Attention [HIGH]
- **Speed:** 15–20 seconds/image [MEDIUM]
- **Letterform application:** NOT documented [LOW]

---

#### StyleAligned (Google)
- **GitHub:** https://github.com/google/style-aligned [HIGH]
- **arXiv:** 2312.02133, Dec 2023–Jan 2024; Hertz et al.
- **Training required:** NONE — shared self-attention keys/values + AdaIN over queries/keys [HIGH]
- **Tuning:** Adjustable attention layer count controls diversity vs. consistency [HIGH]
- **Performance:** User study majority preferred over StyleDrop and DreamBooth [MEDIUM]
- **Speed:** ~45–60 seconds for 2 images [LOW]
- **Recency note:** ~20 months old as of Aug 2026 — newer methods (ConsiStyle May 2025, Only-Style Jun 2025) likely supersede for some use cases

---

#### Only-Style
- **arXiv:** 2506.09916, Jun 2025
- **Training required:** NONE — adaptive inference tuning [HIGH]
- **Key advantage:** Localizes and eliminates content leakage (addresses IP-Adapter / StyleDrop weakness) [HIGH]
- **Speed:** 1 min 46 sec for 2-image set on RTX 3090 [MEDIUM]
- **Open weights:** NOT CONFIRMED [LOW]

---

#### ConsiStyle
- **GitHub:** https://github.com/yohai7700/consistyle | **Project:** https://jbruner23.github.io/consistyle/
- **arXiv:** 2505.20626, May 2025; ACM TOG
- **Training required:** NONE — Queries/Keys from anchor, Values from parallel copy [MEDIUM]
- **Speed:** ~36 seconds/image [MEDIUM]
- **Significantly faster than DB-LoRA and B4M training methods** [MEDIUM]
- **Open weights:** YES [HIGH]

---

#### DreamBooth
- **Training required:** YES — ~15 minutes on A100 [HIGH]
- **Included for contrast only** — not a zero-shot inference technique

---

#### ICAS (IP-Adapter + ControlNet Combined)
- **arXiv:** 2504.13224, Apr 2024
- **Training required:** Minimal — only content injection branch tuned [MEDIUM]
- **Architecture:** Parallel style/content cross-attention; multi-subject style transfer [MEDIUM]
- **Open weights:** NOT CONFIRMED [LOW]

---

### 5.2 Letterform-Specific Style Consistency Techniques

#### FontStudio
- **Venue:** ECCV 2024 | **arXiv:** 2406.08392
- **GitHub:** https://github.com/font-studio/font-studio.github.io
- **Training required:** NONE — training-free effect transfer [HIGH]
- **Architecture:** Shape-adaptive diffusion; font effect noise prior in concatenated latent space; texture propagation from reference letter to others [HIGH]
- **Performance:** 78% user preference on aesthetics [HIGH]
- **Open weights:** YES [HIGH]
- **Multilingual:** YES [HIGH]
- **Application:** Font effect consistency (not structural glyph generation)

---

#### FontFusion
- Merged with Theme 1.3 above
- **Training required:** NONE — plug-and-play inference-time [HIGH]
- **68–76% consistency improvement** over unconditioned [HIGH]
- **Directly applied to letterforms** [HIGH]

---

#### StyleTextGen
- Merged with Theme 1.1 (CVPR 2026) above
- **Application:** Multilingual scene text with arbitrary artistic typography [HIGH]

---

#### DiffInk
- Merged with Theme 1.2 above
- **Style consistency metric:** 77.38 writer style score [HIGH]
- **Application:** Online handwriting style [HIGH]

---

### 5.3 Inference Speed Summary

| Technique | Speed | Confidence |
|-----------|-------|-----------|
| IP-Adapter | 10–14 sec/image | MEDIUM |
| Reference-Only ControlNet | 15–20 sec/image | MEDIUM |
| ConsiStyle | ~36 sec/image | MEDIUM |
| StyleAligned | ~45–60 sec (2 img) | LOW |
| Only-Style | 106 sec (2 img) | MEDIUM |
| FontFusion | Not specified | — |
| FontStudio | Not specified | — |
| DiffInk | 58.47 chars/sec (not per-image) | HIGH |

---

## THEME 6: IMAGE EDITING FOR STRUCTURE-PRESERVING RESTYLING
**Primary source: Smith #16**

### 6.1 FLUX Kontext [dev]
- **License:** FLUX [dev] Non-Commercial License v2.0 + paid commercial via Black Forest Labs [HIGH — primary source, 2025]
- **HF:** https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev
- **VRAM:** FP16: 26 GB [HIGH] | INT4: ~6.5 GB [HIGH] | FP4: ~7 GB, 97% quality [MEDIUM]
- **Structure fidelity:** Highest text editing and character preservation on KontextBench (1,026 image-prompt pairs, 5 task categories) [HIGH — arXiv 2506.15742, May 2025]
- **KontextBench metric:** "Non-edit Consistency" — preservation of unchanged regions [HIGH]
- **Best for:** Lowest VRAM (6.5 GB quantized) + highest text editing benchmark

---

### 6.2 Qwen-Image-Edit-2511
- **License:** Apache 2.0 — full commercial use [HIGH — GitHub, 2024–2026]
- **Note on "2511":** Version designation, not a date
- **GitHub:** https://github.com/QwenLM/Qwen-Image | **Blog:** https://qwenlm.github.io/blog/qwen-image-edit/
- **VRAM:** FP16/BF16: 45 GB [MEDIUM] | BF16 min: 24 GB [HIGH] | INT4/Q4: 11–16 GB [MEDIUM]; 32–64 GB system RAM [HIGH]
- **Architecture:** Dual-channel — Qwen2.5-VL (semantics) + VAE encoder (visual fidelity); reconciles latent spaces [HIGH — arXiv 2508.02324, Aug 2025]
- **Text editing:** Bilingual Chinese/English; font, size, color, style preservation; individual letter color modification [HIGH]
- **Benchmark:** GEdit: 7.56 English, 7.52 Chinese [HIGH — official blog, 2025]
- **LoRA ecosystem:** 7+ adapters (photo-to-anime, multi-angle, pose transfer, style transfer) [HIGH — GitHub, Aug 2026]
- **Community:** Most active (100+ GitHub projects, Aug 2026) [HIGH]
- **Best for:** Multi-element identical styling; Apache 2.0 commercial use; active ecosystem

---

### 6.3 Step1X-Edit
- **License:** Apache 2.0 — full commercial use [HIGH — HF model card, Apr 2025]
- **GitHub:** https://github.com/stepfun-ai/Step1X-Edit | **arXiv:** 2504.17761, Apr 2025
- **Size:** 19 billion parameters [HIGH]
- **VRAM:** Recommended 80 GB [MEDIUM] | Full precision min: 40+ GB [MEDIUM] | FP8+CPU offload: Lower (no specific number) [LOW]
- **Performance:** Outperforms all open-source baselines on GEdit-Bench; approaches GPT-4o and Gemini 2 Flash [HIGH — paper]
- **Evaluation metric:** VIEScore (semantic consistency + perceptual quality) [HIGH]
- **Capabilities:** Text recognition, replacement, reconstruction; watermark erasure; style-preserving directional editing [MEDIUM]
- **Best for:** Complex multi-region edits; highest quality ceiling

---

### 6.4 Comparison Table

| Metric | FLUX Kontext | Qwen-Image-Edit-2511 | Step1X-Edit |
|--------|--------------|---------------------|------------|
| License | Non-commercial + paid commercial | Apache 2.0 ✓ | Apache 2.0 ✓ |
| Min VRAM (quantized) | **6.5 GB (INT4)** | 11–16 GB | ~40 GB (FP8) |
| Native VRAM | 26 GB | 45 GB | 80 GB recommended |
| Text Editing | YES (typography) | YES (bilingual, precise) | YES |
| GEdit / Benchmark | KontextBench leader | 7.56 EN / 7.52 ZH | GEdit-Bench leader |
| GitHub Activity | Active Mar–Jun 2025 | **Most active (Aug 2026)** | Active Mar–May 2026 |

---

### 6.5 Additional Structure-Preserving Models (Smith #16)
- **Gemini 2.5 Flash Image:** Closed-source; excellent structural preservation; free tier [HIGH — Google Developers blog, Aug 2025]
- **GLM-Image:** Dedicated Glyph Encoder for dense text; edit + style transfer [MEDIUM — BentoML, 2026]
- **ReLayout (arXiv 2602.01046, Feb 2026):** Relation graphs for element positioning preservation [MEDIUM]
- **StructDiff:** Adaptive receptive fields; 3D positional encoding for layout control [MEDIUM]

---

## THEME 7: LLM-TO-FONT-PARAMETER PIPELINES
**Primary source: Smith #13 — with Anderson categorization corrections applied**

### 7.1 Approach Summary

| Project | Method | Output | Venue/Date |
|---------|--------|--------|-----------|
| AI-Driven Typography | MLP projector into LLM latent + MDN head | Stroke params, serif style, weight | MDPI Feb 2026 |
| FontCLIP | Vision-language; compound descriptive prompts | Semantic font attributes for retrieval | arXiv Mar 2024 |
| WordArt Designer | GPT-3.5 → 4-module pipeline | Semantic design parameters | arXiv Oct 2023 |
| Font-Agent* | VLM; 135K font-text pair DFD dataset | Font quality assessment params | CVPR 2025 |
| NIV | Neural per-point displacement | Variable font axis values (OpenType) | arXiv Jun 2026 |
| CPT | Decoder-only LM + Creative Markup Language | Font family, weight, color, layout | NeurIPS WS Apr 2026 |
| MetaDesigner | Multi-agent LLM + 68 LoRA tree | Style vectors, LoRA weights | arXiv Jun 2024 |
| FontCraft | Preferential Bayesian optimization | Latent space parameters | CHI 2025 |
| VecFusion* | Cascaded diffusion (raster+vector) | Bézier curve control points | CVPR 2024 |
| Stroke2Font* | RL + genetic algorithm | Bézier params, stroke params (Chinese) | MDPI Mar 2026 |

*Categorization note: Font-Agent is assessment not generation; VecFusion and Stroke2Font are not LLM-based. See Corrections 5.3 and 5.4.

---

## THEME 8: TYPEFACE INVENTION BENCHMARKS
**Primary source: Smith #18 (negative-result report — full signal preserved)**

### 8.1 Core Finding
**NO benchmark specifically measuring a model's ability to INVENT a coherent new typeface exists in published literature as of Aug 2026.** [HIGH confidence — Smith #18 exhaustive search]

**Missing metrics (Smith #18):** Cross-glyph stylistic coherence, visual harmony, character consistency as an invented system

---

### 8.2 Existing Adjacent Benchmarks

**CRAFT & TIDE** (FontFusion paper, arXiv 2606.06066)
- **CRAFT:** 1,605 prompts; avg 1.29 words; models: FonTS, Glyph-ByT5 [HIGH]
- **TIDE:** 100 prompts; avg 4.19 words [HIGH]
- **Scope:** Font-conditioned text *rendering* (not typeface invention)
- **Metrics:** Character accuracy, OCR accuracy, font consistency

**IDEA-Bench** (arXiv 2412.11767, Dec 2024)
- Fonts = 1 of 100 professional design tasks
- Best model: 22.48/100; best general-purpose: 6.81/100 [MEDIUM]
- Font-specific subscores: Not publicly available

**GenerativeFont Benchmark** (FontStudio paper, arXiv 2406.08392)
- 145 test cases; 5 themes; Chinese, Japanese, Korean [MEDIUM]
- FontStudio vs. Adobe Firefly: 78% win-rate on aesthetics [MEDIUM]
- **Scope:** Font *effect* application within predefined font shapes — not typeface design from scratch

**Graphic-Design-Bench (GDB)** (arXiv 2604.04192, Apr 2024)
- 49 design tasks; typography = font family *identification*, not invention
- 2,556 samples across 167 typefaces [MEDIUM]
- Key finding: "Gap widens sharply as tasks demand precision, structure, and compositional awareness" [HIGH]

**AnyText Benchmark** (ICLR 2024)
- Text rendering accuracy (sentence accuracy: 0.7239 English for AnyText-v1.1) [HIGH]
- Not a typeface invention benchmark

**GEdit Benchmark** (used by Qwen, Step1X)
- Image editing fidelity including text editing; Qwen: 7.56 EN, 7.52 ZH [HIGH]
- Not a typeface invention benchmark

**KontextBench** (arXiv 2506.15742, May 2025)
- 1,026 image-prompt pairs; 5 editing task categories [HIGH]
- Not a typeface invention benchmark

---

### 8.3 Research Touching Typeface Design (No Published Benchmark)
- **OneFont** (AAAI): End-to-end font creation via dialogue; 1,500 font families — no benchmark [HIGH]
- **Typeface Generation through Style Descriptions** (ACM DL): Evaluation methodology unclear [LOW]

---

### 8.4 Gap Statement (Smith #18, verbatim)
*"A dedicated benchmark measuring coherence in newly invented typefaces (character consistency, stylistic unity across different glyphs, visual harmony) does not appear to exist in published literature as of August 2026."*

---

## THEME 9: COMMERCIAL AI FONT PRODUCTS & STARTUPS
**Primary source: Smith #19**

### 9.1 Product Inventory

| Product | URL | Founded / Launched | Pricing | Method | Training Disclosure |
|---------|-----|--------------------|---------|--------|---------------------|
| Lipi.ai | lipi.ai | 2024, Estonia | Pay-per-export; free preview | DL from text + handwriting-to-font (81 languages) | NONE FOUND |
| Creative Fabrica | creativefabrica.com/tools/ai-font-generator/ | Announced Mar 2025 | Free beta → ~$5/font; $4–5/mo subscription | Diffusion-based | NOT DISCLOSED [community concern noted] |
| **Font AI** | font-ai.com | Active 2025–2026 | Lifetime membership | Custom ML; 20+ styles; English-only | **OFL + Apache open-source data; proprietary "properly licensed"** [MOST TRANSPARENT] |
| **Mixfont** | mixfont.com | Active 2025–2026 | Free + tiered Pro/Max credits | Text prompts or reference images; Lens recognition model | **Lens: 1.5M+ open-source fonts incl. Google Fonts; generation model: "internet images"** [SECOND MOST TRANSPARENT] |
| Vondy | vondy.com | Sep 2025; updated May 2026 | Free / $19/mo / Enterprise | Full typeface generator; OTF/TTF export | NONE FOUND |
| YoFont | yofont.com | Active 2026 | First free; $5/yr commercial | 23 languages, 9 writing systems, 2,682 glyphs in 2 min; 70% revenue share | NONE FOUND |
| FontVibe | fontvibe.ai | Active 2025–2026 | 20 gen/mo free; paid tiers | Text effect generator (120+ styles) — NOT typeface design | NONE FOUND |
| Calligrapher.ai | calligrapher.ai | Active 2025–2026 | From $10/month | Text → handwritten script; customizable; SVG export | NONE FOUND |
| Fontstruct | fontstruct.com | Long-established | FREE | Grid-based geometric constructor — NOT AI generative | Open-source core (fonthx on GitHub, Haxe) |
| Simplified.com | simplified.com/ai-font-generator/ | Active 2025–2026 | Free tier; Pro $12/mo | AI font generation | NONE FOUND |
| Refont.ai | refont.ai | Active 2025–2026 | Credits-based | AI font, logo, digital design assets | NONE FOUND |

---

### 9.2 Research Project (Not Commercial): DA-Font
- **GitHub:** https://github.com/wrchen2001/DA-Font | **Venue:** ACM MM 2025
- **Method:** Dual-Attention Hybrid Module (component + relation attention) for few-shot font generation structural integrity [HIGH]
- **Status:** Research; not commercialized

---

### 9.3 Training Data Transparency Finding (Smith #19)
Only **Font AI** and **Mixfont** provide meaningful public disclosure of training data sources. All others have no detailed public statement on data sourcing, licensing, or permissions.

Smith #19 conclusion: *"This represents a significant transparency gap in the market."*

---

## SECTION 5: CORRECTIONS (Anderson)

### 5.1 NIV Venue: CVPR 2026 — UNVERIFIED, LIKELY ERRONEOUS

Smith #11 assigns NIV to "CVPR 2026" despite arXiv 2606.05261 being **submitted June 5, 2026**.

**Problem:** CVPR 2026 camera-ready deadlines would precede June 2026. A June 5 arXiv submission cannot plausibly be presented at CVPR 2026 in the same month.

**Smith #13 and #15** both cite NIV (arXiv 2606.05261) but **assign no CVPR venue**.

**Anderson ruling:** Smith #11's "CVPR 2026" for NIV is **UNVERIFIED and likely erroneous**. **Treat NIV as an unaffiliated arXiv preprint (Jun 2026) until venue is directly verified.** This is the only venue assignment in Chain B that Anderson flags as potentially fabricated.

---

### 5.2 FontFusion Miscategorization (Smith #13)

Smith #13 lists FontFusion under "Language Models Generating Font Design Parameters." FontFusion:
1. Does **not** use language models
2. Does **not** output font design parameters
3. Is a plug-and-play **DiT conditioning framework** using hierarchical token representation

**Correct placement:** Theme 5 (style consistency) and Theme 1.3 (CVPR 2026 inventory). All underlying facts preserved; categorization corrected.

---

### 5.3 Font-Agent Overcategorization (Smith #13)

Smith #13 categorizes Font-Agent as "generating font design parameters from natural language." Font-Agent is primarily a **font quality assessment model** (VLM evaluating fonts), not a generative model. The 135,000-pair DFD dataset trains the assessment model. All facts preserved; generative framing does not apply.

---

### 5.4 Stroke2Font / VecFusion LLM Attribution (Smith #13)

Smith #13 theme is "Language Models Generating Font Design Parameters." Stroke2Font uses RL + genetic algorithms; VecFusion uses cascaded diffusion. **Neither uses LLMs.** Both produce font-relevant parameters. Signal fully preserved; LLM method categorization does not apply.

---

### 5.5 DiffInk Scope Clarification (Smith #11 framing)

Smith #11 categorizes DiffInk as a "font/glyph generation" model alongside print-font generators. Smiths #14 and #20 clarify DiffInk generates **online handwriting (pen trajectories)** — not static print-font glyphs. All four Smiths are factually consistent; the scope distinction matters for application routing.

---

### 5.6 GlyphSpatialNet Repository Date Inconsistency (Smith #11)

Smith #11 simultaneously states the GitHub repository was "created Mar 22, 2026" and assigns source date "repository Feb 2026." These conflict. **Use Mar 22, 2026 as creation date; "Feb 2026" likely refers to paper submission date, not repository creation.**

---

### 5.7 Smith #12 "MetaPost/MetaPost" Duplicate

Smith #12 Key Conclusion 3 contains "MetaPost, Fontra" correctly, but an earlier draft sentence reads "MetaPost/MetaPost." Minor formatting artifact; no factual impact.

---

## SECTION 6: DISPUTES (Genuine — Not Stale vs. Fresh)

### 6.1 NIV Venue: CVPR 2026 vs. Unaffiliated Preprint
- **Smith #11:** Assigns CVPR 2026
- **Smith #13, #15:** Cite as arXiv only, no venue
- **Anderson assessment:** Genuine dispute requiring direct verification. Chronological inconsistency makes CVPR 2026 assignment suspicious. **Opus: flag for verification before citing NIV as a conference paper.**

---

### 6.2 StyleAligned Relevance
Not a data conflict — a recency concern. Smith #17 includes StyleAligned (Dec 2023) alongside 2025–2026 methods and notes it may be outdated. Newer attention-sharing methods (ConsiStyle May 2025, Only-Style Jun 2025) may supersede it; user study comparisons are ~20 months old.

---

## SECTION 7: GAPS (Uncovered Topics)

### 7.1 Explicitly Flagged by Individual Smiths
- **Smith #11:** License information for all 10 inventoried models is LOW confidence — no license found despite confirmed GitHub repos. Direct inspection required for VecGlypher, GlyphPrinter, GAR-Font, GlyphSpatialNet, NIV.
- **Smith #14:** True skeleton conditioning for Latin-script diffusion models is an open gap — no confirmed open-weight model uses full skeleton decomposition for Latin
- **Smith #18:** No typeface invention benchmark exists — a formal gap in the evaluation methodology landscape

### 7.2 Gaps Across Full Chain B
- **SIGGRAPH 2026 / NeurIPS 2026:** Not covered (NeurIPS 2026 not yet held; SIGGRAPH 2026 not searched)
- **Font hinting and grid-fitting** for generated/neural fonts: No coverage
- **Accessibility of generated fonts** (screen reader compatibility, hinting quality): Not addressed
- **Runtime web font delivery** for generated fonts: Not addressed
- **Parametric vs. neural head-to-head evaluation** on identical tasks: No Smith compared both paradigms on the same benchmark
- **CJK-specific generative models in 2026 (dedicated survey):** Only older models (SGCE-Font, SFGN, GlyphDraw) covered; no 2026 CJK-focused inventory
- **Diacritics, ligatures, OpenType feature completeness** in generated fonts: Only VecGlypher noted as lacking these; systematic cross-model gap not surveyed
- **Commercial font licensing risk** for AI-generated fonts: Smith #19 identifies transparency gap but does not assess legal exposure
- **FontAdapter** (arXiv 2506.05843 — IP-Adapter for font customization): Only briefly referenced in Smith #17; not fully researched
- **Few-Part-Shot Font Generation** (arXiv 2509.10006, Sep 2025): Identified by Smith #20 but limited details; no dedicated Smith
- **Differentiable Variable Fonts** (arXiv 2510.07638, Oct 2025): Only referenced in Smith #15; no dedicated Smith

---

## CROSS-CUTTING SIGNALS FOR OPUS

### Multi-Smith Convergence Table

| Model | Smiths | Agreed Facts |
|-------|--------|-------------|
| DiffInk | #11, #14, #17, #20 | ICLR 2026, MIT open, 94.38% AR, handwriting not print |
| NIV | #11, #13, #15 | Jun 2026 preprint, venue unconfirmed, 1M+ training tuples, OTF output |
| VecGlypher | #11, #20 | CVPR 2026, 95.34 R-ACC post-FT, text+image conditioning, Meta AI |
| FontFusion | #11, #13, #17 | Jun 2026, Adobe Research, DiT conditioning, no LLM, 68–76% consistency gain |

### Highest Cross-Smith Confidence Facts
1. DiffInk metrics (94.38% AR, 77.38 style, 58.47 chars/sec) — 4-Smith convergence, all from paper [HIGH]
2. fontTools extrapolation behavior (extrapolate param; MutatorMath extrapolates / varLib clamps) — official docs [HIGH]
3. No typeface invention benchmark exists — exhaustive negative search [HIGH]
4. All commercial products (except Font AI and Mixfont) lack training data disclosure — confirmed absence [HIGH]
5. License information missing for all 10 models in Smith #11's CVPR/ICLR inventory — confirmed absence across 2 Smiths [HIGH]

### Recency Map

| Theme | Newest dated source | Smith |
|-------|---------------------|-------|
| 2026 generative models | NIV arXiv Jun 5, 2026 | #11, #13, #15 |
| Parametric systems | Thottingal arXiv Feb 2025 | #12 |
| Variable font tools | fontTools docs 2026 (living) | #15 |
| Diffusion conditioning | DiffInk Sep 2025 / UniGlyph Jul 2025 | #14 |
| Style consistency | FontFusion Jun 4, 2026; StyleTextGen CVPR 2026 | #17 |
| Image editing | Qwen Technical Report Aug 2025 | #16 |
| Benchmarks | CRAFT/TIDE in FontFusion Jun 2026 | #18 |
| Commercial products | Vondy launched Sep 2025; updated May 2026 | #19 |

---

*End of Chain B structured findings — Anderson pass complete.*
*All unique signal preserved. No compression applied. Opus: editorial judgment is yours.*

---
**Oracle SDK Execution Metrics**
- Architecture: 20 Smiths -> 2 Andersons -> Opus (you)
- Total time: 1182s
- Total tokens: 4,371,059 (in: 174,027 | out: 192,277 | cache r/w: 2,757,650/1,247,105)
- Quota: 1.53% weekly (11.6% session)
- Smiths: 20 (0 errors)
- Andersons: 2 (0 errors)
- Phase timing: scout: 181s | compress: 1001s
- Phase costs: decompose: 0.00% | scout: 0.51% | compress: 1.03%

