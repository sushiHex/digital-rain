============================================================
## Chain E — Anderson Report
============================================================

# Chain E — Structured Findings for Opus Synthesis
**Smiths #41–#50 | Organized by Anderson | 2026-04-09**
*All unique signal preserved. Deduplication cited. Corrections and disputes flagged separately.*

---

## THEME 1: Design Tool Companies & OFL Font Releases

**Source: Smith #41**

### Adobe — Active OFL Releases ✅
- **Source Sans Pro** — OFL, designed by Paul D. Hunt, released 2012 | [Typekit Blog](https://blog.typekit.com/2012/08/02/source-sans-pro/)
- **Source Serif** — OFL, designed by Frank Grießhammer & Robert Slimbach
- **Source Mono** — OFL | Part of Source family
- **Source Han Sans & Source Han Serif** — OFL, pan-CJK, co-commissioned Adobe + Google | Designed by Ryoko Nishizuka & Ken Lunde
- **Active GitHub**: https://github.com/adobe-fonts
- **Confidence: HIGH** (5+ confirmed OFL releases)

*Note: Source Han details expanded in Theme 4 (Smith #44) — cross-reference.*

### Figma — No Official Release; Employee Connection ⚠️
- **Inter Font** — OFL, designed by Rasmus Andersson (Figma employee), released August 2017 as **independent project, NOT official Figma release**
  - 414 billion accesses on Google Fonts in 12 months ending May 2025; 57% YoY growth; 16th most-accessed Google Font
  - Source: [Figma Blog](https://www.figma.com/blog/the-birth-of-inter/), [Figma resource library](https://www.figma.com/resource-library/best-fonts-for-websites/)
  - GitHub: https://github.com/rsms/inter
- **Confidence: HIGH** (employee link confirmed, independent-project status confirmed)

### Framer — Monthly OFL Curation ✅ (no proprietary releases)
- Monthly "Font Drop" series curating existing OFL fonts
  - Font Drop 6 (April 13, 2025): DT Getai Grotesk, Utara, Aileron, Bagnard | [Framer Updates](https://www.framer.com/updates/font-drop-6)
  - Font Drop 16 (2026, most recent): Tiny 5×3, Xx Stardust, Wavetosh, St. Martin | [Design Zig](https://designzig.com/framer-font-drop-16-4-new-open-source-fonts-for-modern-websites/)
  - Other drops include: Coaster Sans, Neutral Sans, Schroffer Mono, Elstob, Mluvka, Cesare, Karrik, Aspekta
- **Confidence: HIGH** (active, monthly cadence, recent drop 2026 confirmed)

### No OFL Releases — Confirmed Negatives
| Company | Status | Notes |
|---|---|---|
| **Canva** | ❌ | Integrates Google Fonts (OFL) but releases none |
| **Sketch** | ❌ | Supports OpenType/TrueType; no proprietary releases |
| **Affinity Designer/Publisher** | ❌ | 100+ free fonts + proprietary packs (Creative/Fontsmith), no OFL |
| **Penpot** | ❌ | Includes Google Fonts by default; allows custom uploads; no releases |
- **Confidence: HIGH** per Smith #41

### Watch List for Future Releases (Smith #41)
- Adobe GitHub: ongoing Source family expansions
- Framer Font Drop: monthly cadence, most recent = Drop 16 (2026)

---

## THEME 2: OFL Font Registries, Aggregators & Discovery Platforms

**Sources: Smith #42 (primary), Smith #48 (secondary), Smith #49 (secondary)**

### Primary Registries

**Open Font Library — fontlibrary.org**
- **927 OFL-licensed fonts**; 1,000+ across all licenses (GNU GPL, MIT, CC-BY, Apache 2.0, Public Domain)
  - Source: Smith #42 | Confidence: MEDIUM (2024 data)
- Category breakdown (Smith #49, accessed 2026): 435 sans-serif, 427 serif, 219 display, **125 handwriting**
  - Sum = 1,206 — see ⚠️ DISPUTE #1
- Launched 2006; features CSS embedding, web-font support
- **Confidence: HIGH** for OFL catalog existence; MEDIUM for exact counts

**Velvetyne Type Foundry — velvetyne.fr** *(also in Theme 3 & 8)*
- Active since 2010; all fonts OFL-licensed, modifiable and redistributable
- Released "Ouvrières" March 2024
- Display fonts include: Terminal Grotesque, BackOut, Typefesse (Smith #48)
- GitHub: https://github.com/velvetyne
- **Confidence: HIGH** (Smith #42 + Smith #48, both agree)

**Fontesk — fontesk.com**
- **2,200+ OFL-licensed fonts** | License filter enables OFL-specific discovery
  - Cited by Smith #42, #48, #49 — **AGREE across 3 Smiths**
- 4,000+ fonts in display category — ⚠️ see CORRECTION #1 (likely not all OFL)
- Handles commercial licensing verification per-font
- **Confidence: HIGH** for 2,200+ OFL figure (triple-sourced)

**The League of Moveable Type — theleagueof.github.io** *(also in Theme 8)*
- Founded 2009 by Micah Rich; first "free & open-source type foundry"
- All fonts OFL-licensed; 6 families (5 display + 1 decorative per Font Squirrel)
- On GitHub, Adobe Fonts, Font Squirrel
  - Cited by Smith #42 and Smith #48 — **AGREE**
- **Confidence: HIGH**

**Font Squirrel — fontsquirrel.com**
- Top-5000 site; filters for open-source licenses; curated (not comprehensive)
- Notable fonts: Open Sans, Lato, Roboto, Montserrat, Source Sans Pro
- GitHub snapshot: [Jolg42/FontSquirrel-Fonts](https://github.com/Jolg42/FontSquirrel-Fonts)
- **Confidence: HIGH** (Smith #42)

**Noto Fonts** *(also in Themes 4 & 5)*
- 100+ individual typefaces covering ~1,000 languages, 162 writing systems
- OFL-licensed (switched from Apache 2.0, September 2015)
- Google + Adobe collaboration (CJK variants with Adobe Source Han)
  - Cited by Smith #42 and with deeper detail in Smith #44 and Smith #45
- **Confidence: HIGH** (triple-sourced)

**Font Awesome (Free tier)**
- OFL license for font files; CC-BY-4.0 for SVG/JS; MIT for non-font files
- 100,000+ downloads | GitHub: [FortAwesome/Font-Awesome](https://github.com/FortAwesome/Font-Awesome)
- **Confidence: HIGH** (Smith #42)

### Secondary Discovery Platforms

**Fontsource — fontsource.org**
- NPM packages + web; 1,500+ fonts; OFL + other licenses
- **Confidence: MEDIUM** (Smith #42, single citation)

**Adobe Fonts (open-source section) — fonts.adobe.com/foundries/open-source**
- ~100 open-source families; OFL and Apache 2.0
- **Confidence: HIGH** (Smith #42)

**GitHub Topic Tags (direct discovery)**
- [`github.com/topics/open-font-license`](https://github.com/topics/open-font-license) — explicitly tagged OFL
- [`github.com/topics/ofl`](https://github.com/topics/ofl)
- Examples: Urbanist, Mona Sans (GitHub house font), Hubot Sans
- **Confidence: HIGH** (Smith #42)

**Google Fonts Submission Pipeline (for rejected/stalled fonts)**
- Open issues/PRs on `google/fonts` GitHub show stalled submissions
- GitHub Issue #2022: documents approval process opacity
- No canonical registry of rejections exists
- Contributing guide: `fonts/CONTRIBUTING.md`
- **Confidence: MEDIUM** (Smith #42)

**OFL Official Registry — openfontlicense.org/ofl-fonts/**
- Maintained by SIL; **no unified master registry** — official docs acknowledge this
- "No official master registry exists" — fonts scattered across independent foundries, GitHub, aggregators
- **Confidence: HIGH** (Smith #42)

### Curated OFL Collections for Display/Non-Google-Fonts Fonts
**Smith #48 specific:**
- **Open Foundry** (open-foundry.com) — Curated display typefaces 10+ years; links to originals, does not distribute directly; active 2024–2025 | Confidence: HIGH
- **Use & Modify** (usemodify.com) — Personal curation by Raphaël Bastide; all libre/OFL | Confidence: HIGH
- **awesome-oss-fonts** (GitHub: [drwpow/awesome-oss-fonts](https://github.com/drwpow/awesome-oss-fonts)) — Explicitly excludes Google Fonts; credits designers | Confidence: HIGH
- **FontSpace OFL filter** — 49 OFL fonts listed; 27 in "Open Source" category | Confidence: MEDIUM (counts variable)

---

## THEME 3: Independent Type Foundries

**Sources: Smith #43 (primary), Smith #48 (secondary)**

### OFL-Releasing Foundries

**Production Type**
- **Spectral** — SIL OFL, Google Fonts, serif for screen reading, 7 weights + small caps | [GitHub](https://github.com/productiontype/Spectral) | Confidence: HIGH
- **Newsreader** — SIL OFL, Google Fonts, 42 styles (3 optical sizes × 7 weights), commissioned by Google for long-form on-screen reading | [GitHub](https://github.com/productiontype/Newsreader) | Confidence: HIGH

**DJR (David Jonathan Ross)** *(cross-referenced with Theme 8)*
- **Bungee** — SIL OFL, released ~2015, multi-color + vertical typography | [djr.com/bungee](https://djr.com/bungee) | GitHub: [djrrb/Bungee](https://github.com/djrrb/Bungee)
  - Smith #43 and Smith #48 agree on Bungee details — **AGREE**
- Also released **fbOpenTools** (open-source font-making tools)
- Consulted on Google's variable font conversions
- **Confidence: HIGH**

**Indestructible Type** *(Smith #48 only)*
- GitHub: [indestructible-type](https://github.com/indestructible-type)
- Migrating entire library to variable fonts
- Display fonts include **Gnomon** (retro WWII poster style)
- **Confidence: HIGH**

**Omnibus Type** *(Smith #48 only)*
- Buenos Aires-based collective | GitHub: [Omnibus-Type](https://github.com/Omnibus-Type) | omnibus-type.com
- 515B+ Google Fonts views
- Display/editorial fonts: Faustina, Saira
- **Confidence: HIGH**

**Primary Foundry** *(Smith #48 only)*
- Los Angeles; dual model: commercial + open-source
- Open-source section includes: General Idea, Robert Brownjohn, Technodelic, Municipal Grotesque
- **Confidence: HIGH**

**Fontworks (Japanese)** *(Smith #48 only)*
- Acquired by Monotype September 2023
- OFL releases on GitHub: [fontworks-fonts](https://github.com/fontworks-fonts)
- Example: **Rampart** at [fontworks-fonts/Rampart](https://github.com/fontworks-fonts/Rampart)
- **Confidence: HIGH** (for verified OFL projects specifically)

### No OFL Releases — Confirmed Negatives (Smith #43)
| Foundry | Notes |
|---|---|
| **Grilli Type** | Commercial only, proprietary licensing | Confidence: HIGH |
| **Klim Type Foundry** | Wellington NZ, Kris Sowersby, retail licenses only (desktop/web/app/broadcast/OEM) | Confidence: HIGH |
| **OH no Type Co.** | Founded 2015 by James Edmondson; via Adobe Fonts and Fontstand; no OFL | Confidence: HIGH |

**Smith #43 Key Finding:** Only 2 of 5 sampled independent foundries (Production Type, DJR) release OFL fonts. Both are engaged with the Google Fonts ecosystem.

---

## THEME 4: CJK Fonts with Latin Support

**Source: Smith #44 (primary), with cross-references from Smith #41, #42, #45**

### Major Open-Source CJK + Latin Fonts

**Noto Sans CJK (Google)** *(cross-ref: Smith #42, #45)*
- Glyph count: **65,535** (OpenType maximum) | Confidence: HIGH
- Character coverage: **44,806 characters** from 55 Unicode blocks | Confidence: HIGH
- Latin source: **Source Sans Pro**, scaled **115%** in normal weight for CJK harmony | Confidence: HIGH
- **Version 2.005 (June 18, 2025)**: Updated Latin glyphs to **Source Sans 3** | Confidence: HIGH
- Noto Sans Mono CJK variants use half-width ASCII glyphs | Confidence: HIGH
- License: SIL OFL 1.1

**Source Han Sans (Adobe + Google)** *(cross-ref: Smith #41)*
- Glyph count: **65,535 per weight** (7 weights) | Confidence: HIGH
- Latin source: **Source Sans Pro**, scaled **115%** | Confidence: HIGH
- **Version 2.005 (June 18, 2025)** | Confidence: HIGH [GitHub adobe-fonts/source-han-sans releases]
- Full Latin, Greek, Cyrillic from Source Sans Pro | Confidence: HIGH
- Regional variants: SC, TC, TW, HK, JP, KR with localized glyph standards | Confidence: HIGH
- License: SIL OFL 1.1

**Noto Serif CJK (Google)**
- Glyph count: **65,535** | Confidence: HIGH
- Character coverage: **43,027 encoded characters** | Confidence: HIGH
- Latin coverage: Source Sans family, same 115% scaling | Confidence: HIGH
- License: SIL OFL 1.1

**Source Han Serif & Source Han Mono (Adobe + Google)**
- Glyph count: **65,535 per weight** | Confidence: HIGH
- Latin: Source Sans family (same as Source Han Sans) | Confidence: HIGH
- License: SIL OFL 1.1

**Sarasa Gothic (be5invis/Sarasa-Gothic)**
- Latin source: **Inter font family** | Confidence: HIGH
- Regional variants: SC, TC, J, K, HC — 6 orthographies | Confidence: HIGH
- Monospace: 1:2 width ratio (Latin:CJK) | Confidence: HIGH
- ~480 variants (8 families × 10 styles × 6 orthographies) | Confidence: MEDIUM

**WenQuanYi Zen Hei** — GPL v2.0 + font exceptions
- Latin source: **UnDotum** (un-fonts project) | Confidence: HIGH
- Coverage: English, Simplified + Traditional Chinese, Japanese, Korean | Confidence: HIGH
- Mono variant (Zen Hei Mono): **M+ M Type-1 Light** for Latin | Confidence: HIGH

**WenQuanYi Micro Hei** — Dual-licensed GPL v3/Apache v2
- Latin coverage: From UnDotum (similar to Zen Hei, not separately documented) | Confidence: MEDIUM
- License flexibility: dual GPL v3/Apache v2 | Confidence: HIGH

### Key Design Pattern (Smith #44)
All major open-source CJK fonts use **Source Sans Pro (→ Source Sans 3)** as Latin baseline:
1. Professional-grade Latin/Greek/Cyrillic glyphs
2. 115% scaling ensures visual balance with CJK
3. Established by Adobe's Source Han Sans (2014); adopted by Google for Noto

### Confirmed Full ASCII (0x00–0x7F) Coverage
- ✅ Noto Sans CJK (all variants, especially Mono) — HIGH
- ✅ Noto Serif CJK — HIGH
- ✅ Source Han Sans — HIGH
- ✅ Source Han Serif — HIGH
- ✅ Source Han Mono — HIGH
- ✅ Sarasa Gothic (all variants) — HIGH
- ✅ WenQuanYi Zen Hei — HIGH
- ✅ WenQuanYi Micro Hei — MEDIUM (derived from Zen Hei coverage)

**Conservative count: 7–8 major open-source CJK fonts with confirmed full ASCII** | Confidence: MEDIUM

*⚠️ Note: Smith #44 report was truncated — potential signal loss in final sections.*

---

## THEME 5: Non-Latin Scripts with Quality Latin Support

**Source: Smith #45 (primary)**

*⚠️ Note: Smith #45 report was truncated — potential signal loss at end.*

### Arabic + Latin

| Font | Style | Designer | License | GitHub | Quality |
|---|---|---|---|---|---|
| **Tajawal** | Geometric sans-serif, 7 weights | Boutros International | OFL 1.1 | [Link](https://github.com/googlefonts/tajawal) | HIGH |
| **Amiri** | Classical Naskh (calligraphic body) | Khaled Hosny | OFL 1.1 | [Link](https://github.com/aliftype/amiri) | HIGH |
| **Noto Naskh Arabic** | Modern formal Naskh | Monotype/Google | OFL 1.1 | Google Fonts | HIGH |
| **Noto Sans Arabic UI** | Utility sans-serif variant | Google/Monotype | OFL 1.1 | Noto project | HIGH |

- **Amiri flag**: Beta release December 2011 (14+ years old), but actively maintained | Confidence: HIGH

### Devanagari + Latin

| Font | Style | Designer | License | GitHub | Quality |
|---|---|---|---|---|---|
| **Poppins** | Geometric sans-serif, multi-weight | Indian Type Foundry + Jonny Pinhorn, Ninad Kale | OFL 1.1 | [Link](https://github.com/itfoundry/Poppins) | HIGH |
| **Kalam** | Handwriting, 3 weights | Indian Type Foundry | OFL 1.1 | [Link](https://github.com/itfoundry/kalam) | HIGH |
| **Archivo Devanagari** | Open foundry design | — | OFL 1.1 | [Link](https://github.com/librefonts/Archivo-Devanagari) | MEDIUM |
| **Shobhika** | Serif (rare), scholarly | Sandhi/IIT Bombay | OFL 1.1 | [Link](https://github.com/Sandhi-IITBombay/Shobhika) | MEDIUM |
| **Noto Sans Devanagari** | Sans-serif modular | Google/Monotype | OFL 1.1 | Noto project | HIGH |

- Poppins design note: Pure geometry (circles) basis; Devanagari base height = Latin ascender height | Launched 2015 | 57 languages | Confidence: HIGH
- Shobhika: Latin component built on **PT Serif** foundation | Confidence: MEDIUM

### Thai + Latin

| Font | Style | Designer | Weights | License | Quality |
|---|---|---|---|---|---|
| **Prompt** | Formal sans-serif | Cadson Demak | **18 weights** (most extensive) | OFL 1.1 | HIGH |
| **Mitr** | Informal sans-serif | Cadson Demak | 6 weights | OFL 1.1 | HIGH |
| **Noto Sans Thai** | Modular sans | Google/Monotype | — | OFL 1.1 | HIGH |

- Prompt: Loopless Thai + geometric Latin; airy proportions; launched 2017 | Confidence: HIGH
- Mitr: Loopless Thai + organic humanist sans Latin; rounded terminals; available since 2016 | Confidence: HIGH

### Hebrew + Latin

| Font | Style | Designer | License | Quality |
|---|---|---|---|---|
| **Heebo** | Sans-serif, extends Roboto Latin | Oded Ezer | OFL 1.1 | HIGH |

- GitHub: [OdedEzer/heebo](https://github.com/OdedEzer/heebo)

### Noto Family (Comprehensive Reference)
- Scale: **800+ languages, 150+ writing systems** | OFL 1.1 | Confidence: HIGH
- Modular design: Latin in base Noto Sans; script-specific variants engineered independently
- Production standard: Google/Monotype; actively maintained
- *(Cited across Smith #42, #44, #45 — consistent details across all three Smiths)*

---

## THEME 6: Monospace Fonts — OFL, Outside Google Fonts

**Source: Smith #46**

### NOT on Google Fonts (Confirmed)

**Iosevka (Original)**
- Status: NOT on Google Fonts — only "Iosevka Charon Mono" variant is available | Confidence: HIGH [GitHub issues #9243, #4728, #10085, 2024–2026]
- License: SIL OFL 1.1
- Download: [GitHub Releases](https://github.com/be5invis/Iosevka/releases) | [SourceForge mirror](https://sourceforge.net/projects/iosevka.mirror/)

**Hack**
- Status: NOT on Google Fonts | Confidence: HIGH
- License: MIT + Bitstream Vera License (Hack Open Font License v2.0)
- Download: [GitHub](https://github.com/source-foundry/Hack) | [sourcefoundry.org/hack/](https://sourcefoundry.org/hack/)

**Fantasque Sans Mono**
- Status: NOT on Google Fonts (Issue #77 requested in 2015; never added) | Confidence: HIGH
- License: SIL OFL
- Download: [GitHub](https://github.com/belluzj/fantasque-sans) | [Font Squirrel](https://www.fontsquirrel.com/fonts/fantasque-sans-mono) | [Font Library](https://fontlibrary.org/en/font/fantasque-sans-mono)

**Monaspace**
- Status: NOT on Google Fonts (GitHub issue #120 requested; pending) | Confidence: HIGH
- License: SIL OFL 1.1
- Download: [GitHub Releases](https://github.com/githubnext/monaspace/releases) (v1.400 latest)
- Includes: variable fonts, static TTFs, frozen fonts (all features enabled), WOFF/WOFF2
- Notable feature: **"Texture healing"** technique for improved monospace legibility | Confidence: HIGH

### Already on Google Fonts (Excluded from gap list)
- **Victor Mono** — [fonts.google.com/specimen/Victor+Mono](https://fonts.google.com/specimen/Victor+Mono) | SIL OFL 1.1 | Confidence: HIGH

---

## THEME 7: Classical/Academic Serif Fonts

**Source: Smith #47**

⚠️ **CORRECTION #2 — Task Mismatch**: Smith #47 was apparently tasked with finding serif fonts NOT on Google Fonts but determined that all four targets ARE on Google Fonts. The Smith flags this explicitly ("Contrary to the premise..."). All findings below confirm Google Fonts presence.

### All Four Fonts ARE on Google Fonts (Confirmed, 2026-04-09)

**EB Garamond**
- Google Fonts: ✅ YES | Confidence: HIGH
- Official source: [GitHub - georgd/EB-Garamond](https://github.com/georgd/EB-Garamond)
- Also: Font Squirrel, Adobe Fonts
- History: Released 2011 by Georg Mayr-Duffner (Austria); later developed by Octavio Pardo for Google
- Design basis: Claude Garamond's 16th-century typeface; Egenolff-Berner specimen (1592)
- License: SIL OFL 1.1

**Libertinus**
- Google Fonts: ✅ YES — [Libertinus Serif](https://fonts.google.com/specimen/Libertinus+Serif) | Confidence: HIGH
- Official source: [GitHub - alerque/libertinus](https://github.com/alerque/libertinus)
- Also: Font Library, Font Squirrel, CTAN (TeX/LaTeX)
- Family: 4 styles (Serif, Sans, Mono, **Math**) × 3 weights
- History: Forked from Linux Libertine in 2012; added OpenType math support
- License: SIL OFL 1.1

**Cardo**
- Google Fonts: ✅ YES | Confidence: HIGH
- Official source: [scholarsfonts.net](http://www.scholarsfonts.net/cardofnt.html) (creator's site)
- Also: Adobe Fonts, Font Squirrel
- Designer: David J. Perry (first released 2002)
- Character set: Large Unicode support for classicists, Biblical scholars, medievalists, linguists
- ⚠️ Warning from Smith #47: Many font sites offer unauthorized reduced-character versions; use official sources for full feature set
- License: SIL OFL 1.1

**Crimson Text**
- Google Fonts: ✅ YES | Confidence: HIGH
- Official source: [GitHub - skosch/Crimson](https://github.com/skosch/Crimson)
- **Crimson Pro** (redesigned): Also on Google Fonts, by Jacques Le Bailly, commissioned by Google
- Designer: Sebastian Kosch (original, released 2010)
- Features: 868 glyphs, oldstyle figures, small caps, fleurons, math characters
- License: SIL OFL 1.1

| Font | Google Fonts | Official Repo | Designer | Year |
|---|---|---|---|---|
| EB Garamond | ✅ | GitHub (georgd) | G. Mayr-Duffner | 2011 |
| Libertinus | ✅ | GitHub (alerque) | Multiple (fork) | 2012 |
| Cardo | ✅ | scholarsfonts.net | David J. Perry | 2002 |
| Crimson Text | ✅ | GitHub (skosch) | Sebastian Kosch | 2010 |

---

## THEME 8: Display & Decorative Fonts

**Sources: Smith #48 (primary), cross-refs: Smith #43 (Bungee), Smith #42 (Velvetyne/League)**

### Confirmed OFL Display Fonts (Examples)

**Exo 2.0** — Geometric sans-serif, modern
- GitHub: [NDISCOVER/Exo-2.0](https://github.com/NDISCOVER/Exo-2.0) | 9 weights + italics | SIL OFL | Confidence: HIGH

**Bungee** *(cross-ref Smith #43)*
- Chromatic display for vertical/horizontal use by David Jonathan Ross
- GitHub: [djrrb/Bungee](https://github.com/djrrb/Bungee)
- Includes: inlines, outlines, shades, ornaments | SIL OFL | Confidence: HIGH (Smith #43 + #48 agree)

**Barlow** — Low-contrast grotesk
- 54 manually-hinted styles (3 widths × 9 weights + obliques); variable font support
- GitHub: [jpt/barlow](https://github.com/jpt/barlow) | SIL OFL | Confidence: HIGH

**Rampart (Fontworks/Japanese)**
- GitHub: [fontworks-fonts/Rampart](https://github.com/fontworks-fonts/Rampart) | OFL | Confidence: HIGH

### Volume Estimates (Smith #48)
- Fontesk: 2,200+ OFL total — Confidence: HIGH (triple-sourced with #42, #49)
- Velvetyne + Primary + Omnibus + League combined: ~100–150 original display fonts — Confidence: LOW (estimated)
- Google Fonts OFL subset: ~800–900 of 1,400+ total Google Fonts — Confidence: MEDIUM

### Coverage Gap Analysis (Smith #48)
- Japanese display fonts (Fontworks, local foundries) — source identified
- Experimental/punk typefaces (Velvetyne) — source identified
- Variable fonts with display weights (Indestructible Type, Omnibus) — emerging source
- Geometric display sans (Exo, Barlow variants) — confirmed available

---

## THEME 9: Handwriting Fonts

**Source: Smith #49 (primary), cross-ref: Smith #45 (Kalam)**

### Google Fonts — Handwriting Category
- **~225 handwriting fonts total** | Confidence: MEDIUM (articles cite 225; not independently reverified for 2026)

**Confirmed OFL families (selected):**
- Dancing Script, Caveat, Caveat Brush, Great Vibes, Courgette, Pacifico, Lobster, Satisfy, Leckerli One
- Pangolin, Mansalva, Indie Flower, Architects Daughter, Amatic SC, Patrick Hand, Patrick Hand SC, Handlee
- Pinyon Script (Nicole Fally, SIL OFL 1.1), Berkshire Swash (Brian J. Bonislawsky/Astigmatic, SIL OFL 1.1)
- Permanent Marker, Gloria Hallelujah, Schoolbell
- **Multi-script handwriting:** Kalam (Devanagari+Latin, Indian Type Foundry) *(cross-ref Smith #45)*
- **Korean:** Gamja Flower, Nanum Brush Script, Nanum Pen Script
- **Japanese:** Yomogi
- **Chinese:** Long Cang, Liu Jian Mao Cao
- Full extended list includes: Seaweed Script, Bad Script, Gochi Hand, Reenie Beanie, Rock Salt, Shadows Into Light (Two), Just Another Hand, Coming Soon, Neucha, Dekko, Just Me Again Down Here, Annie Use Your Telescope, La Belle Aurore, Give You Glory, Walter Turncoat, Nothing You Could Do, Cedarville Cursive, Kristi, Tillana, Sedgwick Ave, Sue Ellen Francisco, Neucha, and more.

### Font Library — OFL Handwriting
- **125 OFL-licensed handwriting fonts** (accessed 2026) | Confidence: HIGH
- URL: https://fontlibrary.org/en/search?license=OFL+%28SIL+Open+Font+License%29&category=handwriting
- Specific examples:
  - **Acro Script** by Muhammad Jauhar Azmi — cursive/script
  - **ComicDragonRunes** — decorative script with fantasy elements (2 styles)
  - **Chilanka** by Santhosh Thottingal — handwriting-style **Malayalam + Latin** (commissioned by Swathanthra Malayalam Computing)

### FontSpace — OFL Handwriting
- **Evan Kurtz Art Handwriting** (evankurtzart, 1,098 downloads)
- **Ruji's Handwriting Font v.2.0** (Ruji C., 5,565 downloads)
- **Terrible Cursive** (GGBotNet, 3,247 downloads)
- 13+ additional OFL fonts; all 100% free for commercial use | Confidence: HIGH

### Style Taxonomy (Smith #49)
- **Formal/flowing:** Great Vibes, Dancing Script, Pinyon Script
- **Casual/organic:** Caveat, Mansalva, Courgette, Indie Flower
- **Upright/structured:** Pangolin, Patrick Hand, Kalam
- **Decorative/artistic:** Berkshire Swash, Lobster, Leckerli One
- **Non-Latin support:** Kalam (Devanagari), Chilanka (Malayalam), Gamja Flower (Korean), Yomogi (Japanese)

---

## THEME 10: Training Dataset Size Benchmarks

**Source: Smith #50**

### Comparative Dataset Sizes

| Model | Dataset Size | Characters | Notes | Source Date | Confidence |
|---|---|---|---|---|---|
| **Current project** | **870 fonts** | quality-filtered | Post-filter | 2026-04-09 | HIGH |
| **VecGlypher** | 41,500 total | English, multiple | 39K Envato (Stage 1, noisy SVG pre-training) + 2.5K Google Fonts (Stage 2, expert-annotated) | Feb 2026 | MEDIUM |
| **HFH-Font** | 3,538 total | 6,763 chars | 3,500 train + 38 test; Chinese | Oct 2024 | HIGH |
| **DeepVecFont-v2** | 8,035 (English) | multiple | +1,425 test fonts separate; Chinese dataset size unknown | CVPR 2023 | HIGH |
| **FontDiffuser** | 424 total | 800 chars/font | 400 train + 24 test; Chinese only | Dec 2023 | HIGH |
| **FLUX-Font** | **Unknown** | Chinese | LoRA fine-tuning of FLUX.1 diffusion transformer; Springer paywall; no arxiv | Nov 2025 | LOW |

### Paper Details

**VecGlypher (CVPR 2026)** — [arxiv 2602.21461](https://arxiv.org/abs/2602.21461)
- Stage 1: 39K Envato fonts (noisy; learns SVG syntax at scale)
- Stage 2: ~2,500 Google Fonts (expert-annotated post-training)
- Published 25 Feb 2026 | Confidence: MEDIUM ("2497" exact number not confirmed from available summaries)

**HFH-Font (ACM TOG 2024)** — [arxiv 2410.06488](https://arxiv.org/abs/2410.06488)
- Large-scale: 3,538 fonts | Small-scale subset: 438 fonts | Both: 6,763 Chinese characters
- Published Oct 2024 | Confidence: HIGH (confirmed 2x)

**DeepVecFont-v2 (CVPR 2023)** — [arxiv 2303.14585](https://arxiv.org/abs/2303.14585)
- 8,035 English training fonts + 1,425 test
- Chinese dataset size: not found | Published CVPR 2023 | **Flag: 3 years old, potentially outdated** | Confidence: HIGH

**FontDiffuser (AAAI 2024)** — [arxiv 2312.12142](https://arxiv.org/abs/2312.12142)
- 424 total Chinese fonts (400 train, 800 chars/font) | Submitted Dec 2023 | Confidence: HIGH

**FLUX-Font (ACPR 2025)** — [Springer](https://link.springer.com/chapter/10.1007/978-981-95-4395-3_23)
- Authors: Zheyu Li, Honglie Wang, Yan-Ming Zhang, Cheng-Lin Liu
- Method: LoRA fine-tuning of FLUX.1 for Chinese fonts
- Dataset size: **Not accessible** (paywall; no arxiv version found) | Confidence: LOW

### Scaling Analysis (Smith #50)
- Project 870 fonts vs. VecGlypher: **47× smaller** (41.5K total)
- Project 870 fonts vs. HFH-Font: **4× smaller** (3.5K training)
- Project 870 fonts vs. DeepVecFont-v2: ~10× smaller (8K English)
- Project 870 fonts vs. FontDiffuser: **2× larger** (but Chinese-only; less relevant)

**Key insight from Smith #50:** VecGlypher's 39K+ scale is driven by *noisy* data needed for SVG syntax learning. HFH-Font's 3.5K is expert-curated. Quality filtering at 870 fonts implies ~8,700 characters (vs. HFH's 6,763 from 3,538 fonts) — current project's character:font ratio (~10:1) already matches or exceeds HFH-Font density.

**Recommended action (Smith #50):** Contact FLUX-Font authors or check Springer supplementary materials for dataset size.

---

## CORRECTIONS

**CORRECTION #1 — Fontesk Display Count (Smith #48)**
> Smith #48 states: "Fontesk: 2,200+ OFL total | 4,000+ display category."
> **Problem:** If total OFL fonts = 2,200+, a single display subcategory cannot contain 4,000+ OFL fonts. The 4,000+ figure almost certainly refers to Fontesk's *total display category across all licenses* (free + commercial + OFL), not OFL-only display fonts.
> **Corrected reading:** 2,200+ OFL total (all categories); 4,000+ display fonts total (mixed licensing). Do not use 4,000+ as an OFL display count.

**CORRECTION #2 — Smith #47 Task Mismatch**
> Smith #47 was scoped to find serif fonts *not* on Google Fonts. The report itself notes: "Contrary to the premise, all four fonts you listed are already available on Google Fonts." All findings (EB Garamond, Libertinus, Cardo, Crimson Text) document their presence *on* Google Fonts and their independent repos. The finding is useful (confirms OFL status, canonical sources, metadata) but does not fulfill the original discovery goal of identifying OFL serifs *outside* Google Fonts. **Signal is valid; task is incomplete.**

---

## DISPUTES

**⚠️ DISPUTE #1 — Font Library Total Count (Smith #42 vs. Smith #49)**
> - Smith #42 (2024): "927 OFL-licensed fonts; 1,000+ total across all licenses"
> - Smith #49 (2026): Category breakdown = 435 sans-serif + 427 serif + 219 display + 125 handwriting = **1,206 total**
> - **Assessment:** These figures are not necessarily contradictory — the 927 OFL count (Smith #42) may have grown since 2024, or Smith #49's breakdown may include all license types while Smith #42 isolated OFL. The 1,206 sum exceeds Smith #42's "1,000+" total estimate.
> - **Resolution (tentative):** Smith #49 data is more recent (2026 access) and more granular. Prefer Smith #49's 1,206 as current total catalog size; 927 OFL may now be higher. **Flag for Opus as soft discrepancy: likely temporal, not factual.**

**⚠️ DISPUTE #2 — Kalam Style Description (Smith #45 vs. Smith #49)**
> - Smith #45: "Handwriting style, 3 weights"
> - Smith #49: "Brush script"
> - **Assessment:** Not a genuine factual dispute — "handwriting style with brush aesthetics" is internally consistent. Both Smiths agree on core facts (Indian Type Foundry, OFL, Devanagari+Latin). Minor label difference, not contradictory. **Classify as vocabulary divergence, not dispute.**

---

## GAPS

The following topics were not covered by any of the 10 Smiths in this chain:

1. **Variable fonts as a distinct category** — Mentioned in passing (Indestructible Type migrating to variable, Monaspace has variable, Source Han has weights) but no systematic survey of OFL variable font sources or GF variable font coverage
2. **Math fonts** — Libertinus Math noted in passing (Smith #47) but no dedicated coverage; critical for scientific/LaTeX use cases
3. **Color/Chromatic fonts beyond Bungee** — Bungee's chromatic features documented; no survey of other OFL color font families (e.g., COLRv1 fonts)
4. **Scripts not covered in Theme 5** — No data on: Ethiopian/Ge'ez, Armenian, Georgian, Tibetan, Myanmar, Khmer, Sinhala, Tamil, Telugu, Kannada, Malayalam beyond Chilanka (handwriting only), Bengali
5. **FLUX-Font dataset size** — Explicitly flagged as LOW confidence / unknown in Smith #50; Springer paywall prevents access
6. **Font metadata and tagging standards** — No coverage of how fonts are classified (weight, style, use-case tags) for training data organization
7. **Apache 2.0 and MIT font licenses** — Mentioned but not systematically covered alongside OFL; several fonts (WenQuanYi Micro Hei, some Noto variants historically) use these
8. **Rejected/withdrawn Google Fonts submissions as a discovery vector** — Smith #42 identifies this as a method but notes no canonical registry exists; no deep exploration done
9. **Fontsource NPM ecosystem** — Listed once (Smith #42) with 1,500+ fonts but no deeper characterization
10. **DeepVecFont-v2 Chinese dataset** — Smith #50 explicitly notes size was not found; only English (8,035) is confirmed

---

*Anderson — Chain E organization complete. 10 Smiths, 10 themes, 2 corrections, 2 disputes, 10 gaps. All unique signal preserved for Opus synthesis.*

============================================================
## Chain D — Anderson Report
============================================================

# Chain D — Organized Findings for Opus Synthesis
**Smiths #31–40 | Processed: 2026-04-09 | Anderson**

---

## ══ CORRECTIONS (Pre-Read) ══

Apply these before interpreting the findings below.

### CORRECTION-1: Google Fonts Family Count — Smith #39 Figure Likely Wrong
- **Smith #39** reports **1,052 font families** (labeled HIGH) citing developers.google.com docs, March/April 2026
- **Smiths #34 and #40** independently report **1,929 font families** (both HIGH), from direct github.com/google/fonts inspection and Wikipedia respectively, also April 2026
- **Smith #32** reports **1,826 families** (HIGH, May 2025), consistent with growth to 1,929 by April 2026
- **VERDICT:** 1,052 is almost certainly a misread — possibly a filtered API response, cached snapshot, or documentation artifact. Prefer **1,929** (April 2026). Downgrade #39's count to LOW confidence. All other #39 findings unaffected.

### CORRECTION-2: Smith #33 Google Fonts "2,545" — Unit Mismatch
- **Smith #33** cites **2,545 total fonts** (MEDIUM) from service.tib.eu secondary dataset metadata
- This almost certainly counts individual **font files/weight-style variants**, not font *families* — not comparable to family counts in other Smiths
- **VERDICT:** Not a family count. Flag as "variant files" context only. Do not reconcile with 1,929.

### CORRECTION-3: Smith #35 TMNIST Rejection Rate Is a Derived Figure
- The **0.38% rejection rate** is labeled "(calculated)" — arithmetic is correct (7 ÷ 1,819 = 0.385%) but the label of MEDIUM confidence is appropriate since source Smith derived it, not stated in paper directly.

---

## ══ DISPUTES ══

### DISPUTE-1: Google Fonts Family Count (Genuine, Not Stale-vs-Fresh)
| Smith | Count | Source | Date | Confidence |
|---|---|---|---|---|
| #32 | 1,826 | Secondary analysis | May 2025 | HIGH |
| #33 | 2,545 | service.tib.eu dataset | 2022–2025 | MEDIUM |
| #34 | 1,929 | Wikipedia via search | April 2026 | HIGH |
| #39 | 1,052 | developers.google.com docs | Mar/Apr 2026 | HIGH (labeled) → LOW (corrected) |
| #40 | 1,929 | github.com/google/fonts direct | April 2026 | HIGH |

**Anderson assessment:** #34 and #40 converge at 1,929 from independent April 2026 sources. #32 at 1,826 (May 2025) is consistent with +103 additions over 11 months. #39's 1,052 is anomalous. #33's 2,545 is a different unit. **Opus should use 1,929 as canonical April 2026 figure.**

### DISPUTE-2: VQ-Font Training Font Count
- Smith #33 reports **371 fonts** (HIGH) vs. **382 fonts** (MEDIUM, from search results) for VQ-Font AAAI 2024
- Both figures appear in Smith #33 itself — not cross-Smith
- **Anderson assessment:** 371 is the paper-stated figure (HIGH); 382 may be a search result artifact. Flag for Opus to verify against arXiv 2308.14018 directly.

### DISPUTE-3: Font Library vs. Open Font Library — Naming Risk
- Smith #40 distinguishes two entirely separate projects with similar names:
  - **fontlibrary.org** ("Font Library"): 6,000+ fonts, sister to Openclipart
  - **openfont.org** ("Open Font Library"): 1,933 fonts
- No other Smith mentions either; no cross-validation possible
- **Anderson assessment:** Not a numerical dispute but a naming collision risk that could corrupt Opus synthesis. Flag explicitly.

---

## ══ SECTION 1: Font Collection Platforms & Foundries ══

### 1A. Open Foundry (open-foundry.com)
**Source: Smith #31 | Date: 2026-04-09 | Confidence: HIGH (platform description), MEDIUM (count)**

- **Operator:** Magic as a Service™
- **Self-description:** "Curated Fonts for Free" — display/curation platform, NOT a distribution host
- **Model:** Fonts handpicked by taste; second iteration with rebuilt core
- **Font count:** ~25 visible/featured on homepage (MEDIUM); **total collection size NOT publicly disclosed** — no statement found after direct site fetch + searches
- **Access model:** Each font page has "Get Font" button linking to original source:
  - Creator website (e.g., rsms.me/inter/)
  - GitHub releases (e.g., github.com/googlefonts/roboto-2)
  - Google Fonts (fonts.google.com)
- **Google Fonts overlap:** YES — confirmed examples: Roboto, Inter. Open Foundry does not market as exclusive to non-Google sources.
- **License:** OFL v1.1 confirmed on sampled fonts (Roboto, Inter) — HIGH

---

### 1B. Uncut.wtf
**Source: Smith #32 | Date: 2026-04-09 live | Confidence: HIGH (counts), MEDIUM (licensing nuance)**

- **Operator:** Kasper Nordkvist (Danish digital designer); launched 2021
- **Model:** Free, ad-free; accepts community submissions via email/Instagram; copyright remains with creators
- **Philosophy:** "Somewhat contemporary" — experimental, non-mainstream, designer-focused
- **Total fonts: 163 typefaces** (HIGH, live site April 2026)
  - Sans Serif: 66
  - Display: 47
  - Serif: 27
  - Monospace: 23
- **License:** Mixed per creator. OFL 1.1 confirmed on multiple fonts (Uncut Sans, Fraunces, Liga Sans). No master license list published; must check per font page.
- **No attribution required** for OFL fonts in use (but cannot sell fonts standalone; must bundle)
- **Google Fonts comparison:**
  | Metric | Uncut.wtf | Google Fonts |
  |---|---|---|
  | Count | 163 | 1,929 (April 2026) |
  | Philosophy | Experimental, non-mainstream | Mainstream, web-readability focus |
  | Aesthetic | Cutting-edge, distinctive | Conservative, reliable |
  | Target | Designers seeking alternatives | Web developers, broad audience |
  - Uncut: higher novelty per font, lower total coverage (MEDIUM — derived)

---

### 1C. Collletttivo
**Source: Smith #36 | Date: April 2026 | Confidence: HIGH (count, license, GF status), MEDIUM (format)**

- **Founded:** 2017 | **Base:** Milan | **Core team:** 7 designers + distributed contributors
- **Mission:** Open-source type foundry + collaborative network; emphasizes remixable/editable fonts
- **Font count: 16 open-source typefaces** (HIGH — directly stated on collletttivo.it, confirmed via WebFetch April 2026)

**Complete catalog:**
1. Borges (Matteo Bertin)
2. Ronzino (Luigi Gorlero, Nunzio Mazzaferro) — 6 weights
3. Aujournuit (Teo Gaudet) — 5 weights + variable
4. Absans (Valerio Monopoli)
5. Mazius Display (Alberto Casagrande) — 4 weights
6. Ribes (Luigi Gorlero) — 3 weights
7. Mattone (Nunzio Mazzaferro) — 3 weights
8. Coconat (Sara Lavazza) — 3 weights
9. Sinistre (Jules Durand) — 3 weights + variable
10. Apfel Grotezk (Luigi Gorlero) — 5 weights
11. Ortica (Ben Bovani) — 4 weights
12. Messapia (Luca Marsano) — 2 weights
13. Halibut (Matteo Maggi) — 6 weights + variable
14. Sprat (Ethan Nakache) — 18 weights + variable
15. Sneaky Times (Jules Durand)
16. Necto Mono (Marco Condello)

- **License:** All OFL-1.1 (HIGH). Commercial + personal use; modification; redistribution with attribution; cannot claim full credit, sell standalone, or change license. Contact: collletttivo@gmail.com for exceptions.
- **Google Fonts status:** NOT on Google Fonts (HIGH). GitHub issue #2783 (Oct 31, 2020) proposed addition — open/pending with no merge activity as of April 2026. Search returns zero results.
- **Distribution:** Own site (collletttivo.it) + Font Squirrel, No-Code Supply Co, Fontesk
- **File format:** OTF (MEDIUM — confirmed via Font Squirrel listing and GitHub repos; TTF/WOFF/WOFF2 not confirmed from official site directly)

---

### 1D. Fontshare (Indian Type Foundry)
**Source: Smith #40 | Date: April 2026 | Confidence: HIGH**

- **Count:** 100 font families
- **Origin:** All originals created in-house by ITF
- **License:** ITF Free Font License (free for commercial use) — distinct from OFL

---

### 1E. Font Library (fontlibrary.org)
**Source: Smith #40 | Date: April 2026 | Confidence: MEDIUM**

- **Count:** 6,000+ fonts
- **Contributors:** 250+
- **Note:** Sister project to Openclipart; **DISTINCT from Open Font Library (openfont.org)** — see DISPUTE-3

---

### 1F. Open Font Library (openfont.org)
**Source: Smith #40 | Date: April 2026 | Confidence: MEDIUM**

- **Count:** 1,933 fonts
- **Coverage:** 147 supported languages, 10 style varieties
- **Note:** DISTINCT from fontlibrary.org — see DISPUTE-3

---

### 1G. Bunny Fonts
**Source: Smith #40 | Date: April 2026 | Confidence: MEDIUM**

- **Count:** ~1,492 fonts
- **Model:** Privacy-first, GDPR-compliant, drop-in Google Fonts CSS API replacement
- **Philosophy:** Open-source; not a strict superset of Google Fonts — privacy-focused alternative

---

## ══ SECTION 2: Google Fonts — Repository & Infrastructure ══

**Sources: Smiths #34 (primary), #39 (download methods), #40 (count), #32 (count reference)**

### 2A. Canonical Collection Size
- **1,929 font families** (HIGH — Smiths #34 and #40 independently, April 2026)
- **543 variable font families** included (Smith #40 — HIGH)
- Growth trajectory: ~1,826 (May 2025, #32) → 1,929 (April 2026, #34, #40) = +103 in ~11 months
- See CORRECTION-1 and CORRECTION-2 for discrepant figures from #33 and #39

### 2B. Repository Directory Structure
**Source: Smith #34 | Confidence: HIGH**

```
google/fonts/
├── ofl/          # SIL Open Font License (vast majority)
├── apache/       # Apache License 2.0 (47 fonts confirmed)
├── ufl/          # Ubuntu Font License v1.0 (5 fonts: Ubuntu, Ubuntu Condensed, Ubuntu Mono, Ubuntu Sans, Ubuntu Sans Mono)
└── cc-by-sa/     # Creative Commons Attribution-ShareAlike (present, not quantified)
```

### 2C. Per-Family File Structure
**Source: Smith #34 | Confidence: HIGH (from direct file inspection)**

Each font family subdirectory contains:
- `.ttf` font files (all styles/weights) — **TTF is canonical format; NO OTF files in repo**
- `METADATA.pb` — protobuf metadata (absent in Early Access fonts)
- `DESCRIPTION.en_us.html`
- License file (OFL.txt, Apache LICENSE.txt, or UFL.txt)
- `upstream_info.md` / `upstream.yaml` — source tracking

Example from apache/aclonica/:
- Aclonica-Regular.ttf (68.7 KB)
- METADATA.pb (558 B)
- DESCRIPTION.en_us.html (245 B)
- LICENSE.txt (11.4 KB)
- upstream_info.md (4.7 KB)

### 2D. Repository Size
**Source: Smith #34 | Confidence: MEDIUM**
- Full repo with git history: ~1.6 GB
- GitHub ZIP snapshot: >1 GB (confirmed by both #34 and #39 — HIGH)

### 2E. Notable Repository Caveats
**Source: Smith #34 | Confidence: HIGH**
- **No OTF files** — TTF canonical (confirmed in README + direct inspection)
- **Deprecated/renamed families** retained in git history for API compatibility (e.g., `baloo` → `baloo2`)
- **Early Access fonts** lack METADATA.pb files (documented in TRIVIA.md)
- Duplicate families exist in history — ofl/ directory too large to enumerate directly

### 2F. Google Fonts API
**Source: Smith #39 | Confidence: HIGH**
- Endpoint: `https://www.googleapis.com/webfonts/v1/webfonts?key=YOUR-API-KEY`
- Returns JSON metadata: family names, variants, subsets, download URLs
- Requires API key from Google Cloud Console (APIs & Services → Credentials)
- Supports sorting: alphabetically, by date, by style count, by trend/popularity

---

## ══ SECTION 3: Font Download Methods ══

**Sources: Smiths #34 and #39 (overlapping — merged)**

### 3A. Method Comparison Table
| Method | Speed | Confidence | Notes |
|---|---|---|---|
| GitHub ZIP (`/archive/main.zip`) | Slowest — >1 GB | HIGH (#34, #39 agree) | Full download each time; official source |
| `git clone` then `git pull` | Fastest for updates | HIGH | Incremental sync; recommended for bulk local storage |
| Git sparse checkout (subset) | Fast | HIGH | Clone only ofl/ or specific dirs; `--filter=blob:none --sparse` |
| Shallow clone (`--depth 1`) | Fast initial | HIGH | Minimal history; loses git update efficiency |
| Google Fonts API + script | Medium | HIGH | Granular control; selective download; requires API key |
| google-webfonts-helper | Fast (cached) | MEDIUM | May lag latest font revisions |

### 3B. Sparse Checkout Pattern
**Source: Smith #34 | Confidence: HIGH**
```bash
git clone --filter=blob:none --sparse https://github.com/google/fonts.git
cd fonts
git sparse-checkout init --cone
git sparse-checkout set ofl  # Only fetch OFL fonts
```

### 3C. API Bulk Download Pattern
**Source: Smith #39 | Confidence: HIGH**
```python
# 1. GET https://www.googleapis.com/webfonts/v1/webfonts?key=YOUR_KEY
# 2. Parse JSON, extract .files.ttf URLs
# 3. Parallel download via requests + threading
```

### 3D. Third-Party Tools
**Source: Smith #39 | Confidence: MEDIUM (may lag updates)**
- **google-webfonts-helper** (majodev): zipped archive with .eot, .ttf, .svg, .woff, .woff2 + CSS; API available for direct queries
- **google-fonts-downloader** (Muetze42): uses webfonts-helper API for bulk
- **google-font-download** (neverpanic): shell script for self-hosting + CSS generation
- **Fontsource metadata generator**: scrapes Google Fonts API for complete metadata + variant info
- **googlefonts-installer** (PyPI): auto-configures sparse-checkout with shallow history; supports incremental updates

### 3E. Direct Raw File Access
**Source: Smith #34 | Confidence: HIGH**
```
https://raw.githubusercontent.com/google/fonts/main/ofl/[fontname]/[fontname]-Regular.ttf
```

---

## ══ SECTION 4: ML Training Datasets — Sizes & Architectures ══

**Source: Smith #33 (primary) | Confidence levels per finding**

### 4A. VecGlypher (CVPR 2026)
- **arXiv:** 2602.21461 | Updated: 2026-02-25
- **Stage 1:** 39,000 noisy Envato fonts — SVG syntax continuation learning (HIGH)
- **Stage 2:** 2,500 expert-annotated Google Fonts — descriptive tags, post-training (HIGH)
- **Design principle:** Two-stage progression from large-scale noisy → curated expert data
- **Note:** Rationale for 2,500 Google Fonts cutoff not stated in available sources (GAP)

### 4B. FontDiffuser (AAAI 2024)
- **arXiv:** 2312.12142 | Dec 2023
- **Training set:** 400 fonts (HIGH) + 800 Chinese characters (MEDIUM)
- **Test sets:** 100 seen fonts × 272 unseen chars; 24 unseen fonts × 300 unseen chars
- **Context:** Chinese font generation

### 4C. VQ-Font (AAAI 2024)
- **arXiv:** 2308.14018 | Aug 2023
- **Training:** 371 fonts (HIGH) — see DISPUTE-2 for 382-font discrepancy
- **Seen characters:** 2,841 (HIGH)
- **Total chars per font:** 3,499 Chinese characters at 128×128 px
- **Split:** 3,351 training chars | 158 reference chars | 500 unseen test chars
- **Reference approach:** ~100 reference characters, 3 mappings per character

### 4D. Few-Shot Font Generation (clovaai unified repo)
- **GitHub:** clovaai/fewshot-font-generation
- **Methods:** FUNIT (ICCV'19), DM-Font (ECCV'20), LF-Font (AAAI'21), MX-Font (ICCV'21)
- **No single minimum** font/character count specified — flexible by design
- LF-Font noted for instability with "very limited" reference sets

### 4E. LoRA Training Size Guidance
**Source: Smith #33 | Confidence: MEDIUM (general image generation, not font-specific)**
- **Character/Subject LoRA:** 20–40 high-quality images
- **Style LoRA (broader aesthetic):** 50–200 images
- **Font-specific LoRA:** 25–40 images minimum; quality over quantity; overfitting risk with large sets
- **No published ablation** on exact minimum for fonts specifically (GAP)

---

## ══ SECTION 5: Font Dataset Quality Filtering ══

**Source: Smith #35 (primary) | Date: 2022–2026**

### 5A. MyFont Dataset Filters (GRIF-DM, ECAI 2024)
**Confidence: MEDIUM**
- Discard fonts with fewer than **5 impression keywords** (metadata curation)
- Remove fonts with **width-to-height ratio > 2:1** (filters dingbats/special chars)
- Select only **uppercase A-Z** characters

### 5B. Google Fonts Processing Standards
**Confidence: HIGH | Date: 2022–2025**
- **5 style categories:** Sans-serif, Serif, Handwriting, Display, Monospaced
- **4-layer tag features:** Categories, Feeling, Appearance, Technology
- **Raw size in TMNIST study:** 1,355 fonts
- **Standardization:** 300×300 or 32×32 px grayscale images

### 5C. Typography-MNIST (TMNIST) Dataset
**arXiv: 2202.08112 | Confidence: HIGH (dataset facts), MEDIUM (rejection rate — derived)**
- **Initial glyphs:** 1,819 unique glyphs compiled
- **Post-filter:** 1,812 glyphs (7 rejected = 0.38% rejection rate — *derived by Smith #35, not stated in paper*)
- **Coverage:** 1,355 Google fonts, 150+ language scripts
- **Final output:** 565,292 images at 28×28 px

### 5D. Chinese Character Coverage Standards
**Confidence: HIGH | Date: 2024–2025 | Status: Industry standard**
- **GB2312 completeness threshold:** 6,763 characters (Level 1+2)
- **Incomplete font strategy:** Select top 300 highest-frequency chars + 2,000 from Modern Chinese Common Use table

### 5E. Large-Scale Vector Font Dataset
**arXiv: 2404.06779 | Confidence: HIGH | Date: 2024**
- **Scale:** 90,000+ characters with component/layout information
- **Layout types tracked:** 6 (Left-Right, Top-Bottom, Enclosed, etc.)
- **Efficiency gain vs. manual:** ~30× speedup in generation

### 5F. Glyph Preprocessing Standards
**Confidence: HIGH | Date: 2024–2025 | Status: Standard pipeline**
- **Image standardization:** 64×64 px (standard in glyph datasets)
- **SVG path filtering:** Keep valid paths only; discard malformed geometry
- **Quantization:** Round to 1 decimal place for vector-based generation
- **Format conversion:** TTF/OTF → SVG/vector for generation tasks

### 5G. Known Dataset Quality Issues
**Confidence: MEDIUM | Source: LTTR/FACE research | Date: 2024**
- **"Curve dislocation problem":** Arbitrary Bézier curve sequence lengths in datasets
  - Solution: Normalize curve sequences per glyph; standardize to fixed count
- **Internet-sourced dataset (14M chars):** Flagged for questionable quality, licensing, and authorship

### 5H. Annotation Quality Benchmarks (General ML)
**Confidence: HIGH | Date: 2024**
- Survey of 591 dataset papers: 30% rated "subpar" quality management (MIT COLI 2024)
- Average annotation error rate across search tasks: **10%** (Apple ML Research 2024)
- ImageNet gold-standard: **6% error rate** (discovered 2024)
- OCR CER targets: <1% (high-quality scans), <5% (handwritten)
- Font-specific CER variation: 3.14% (Times New Roman) → 15.14% (Arial)

### 5I. FontUse Quality Framework (Cutting-Edge)
**arXiv: 2603.06038 | Confidence: MEDIUM | Date: 2026**
- **CER:** 2.18% for MLLMs vs. traditional OCR
- **Annotation:** Structured JSON metadata for fonts + use-cases
- **Evaluation:** Fine-tuned Long-CLIP embeddings + MLLM preference scoring
- **Legibility metric:** Character error rate via human transcription

### 5J. FLUX Data Pipeline
**arXiv: 2603.13972 | Confidence: HIGH | Date: 2026**
- **4-stage pipeline:** text extraction → heuristic filtering → deduplication → model-based classification
- Each stage measured for aggregate score gains; all 4 stages confirmed beneficial
- *(Smith #35 was truncated — additional details from this source not available)*

---

## ══ SECTION 6: Font Diversity Metrics ══

**Source: Smith #33 | Confidence: HIGH (axes 1–4), MEDIUM (axes 5–7)**

### 6A. Standard Design Space Axes
Per CSS Fonts Module Level 4 and variable fonts research:

1. **Weight:** Thin → Regular → Bold (typically 3–9 levels) — HIGH
2. **Width:** Condensed → Normal → Extended — HIGH
3. **Slant/Italic:** Normal, italic, oblique — HIGH
4. **Style Category (4-way):** Serif, Sans-serif, Handwriting/Script, Display — HIGH
   - Used explicitly in Google Fonts classification
5. **Serif Details:** Shape, contrast (low to medium), stroke variation — MEDIUM (per LTTR/SET taxonomy, WACV 2024)
6. **Character Structure (CJK):** ~12 structure types; VQ-Font uses structure tagging for style matching — HIGH
7. **Letter Variants:** Single vs. double-storey 'a', different stroke counts — MEDIUM

---

## ══ SECTION 7: Licensing & ML Training Legal Landscape ══

**Sources: Smiths #32, #37, #38 (heavily overlapping on OFL — merged)**

### 7A. SIL Open Font License (OFL) 1.1 — Core Rules
**Confidence: HIGH | Sources: #32, #36, #37, #38 — converge on all points**

✅ Permitted:
- Commercial use
- Modification
- Redistribution (with attribution)
- Bundling in commercial software

❌ Prohibited:
- Selling fonts standalone (must bundle)
- Changing license terms on derivative fonts
- Claiming full credit

⚠️ Reserved Font Name (RFN) clause:
- Cannot rename derivative fonts without explicit written permission from original authors
- Applies to ~45 of 70 Nerd Fonts base fonts (Smith #37)

### 7B. OFL + ML Training — Official Position
**Confidence: HIGH | Sources: Smiths #32, #37, #38 — all three independently cite OFL-FAQ, all agree**

**Official OFL-FAQ ruling (no date specified — current):**

> "A font released under the OFL cannot be used as a source by an AI, ML model, neural network, or similar system to create a new font and release it under a different license."

- Any font produced from ML systems whose **input/training data contains OFL source** = **derivative work** = must remain OFL
- **Exception:** Using OFL fonts *within* AI design tools to produce **non-font outputs** is permitted (treated as normal usage)
- Requires explicit written permission from original authors to release OFL-derived fonts under different licenses

**Practical implications (per Smith #37):**
- Training on OFL fonts to produce image generation model outputs: ✅ likely permitted
- Training on OFL fonts to produce/distribute derivative fonts under non-OFL license: ❌ prohibited
- Commercial use of trained models (not outputting fonts): ✅ permitted if not selling fonts themselves

### 7C. US Copyright Law on Typefaces
**Confidence: HIGH | Source: Smith #38 | Established law**

- **Typefaces themselves:** NO copyright protection since 1992 (Code of Federal Regulations)
- Legal principle established: **1978** (*Eltra Corp. v. Ringer*)
- **Font programs** (software code): CAN be copyrighted
- **Font designs** (letter shapes): Design patent possible (rare; post-2015: 15-year term)
- **Font names:** Trademarkable

**Key implication for ML training:**
- Cannot infringe US font copyright through ML training *because typeface designs lack copyright*
- However, **OFL license obligations are enforceable independently** of copyright status
- OFL is a contract; breach = contract liability, not copyright infringement

### 7D. Active Font Litigation (Non-ML)
**Confidence: HIGH | Source: Smith #38 | Date: April 2026**

| Case | Year | Details |
|---|---|---|
| Laatz v. Zazzle | 2022–2024 | Font copyright validity directly analyzed; Nov 2024 motion to dismiss based on invalid copyrights. First court to directly analyze Adobe's reasoning on font copyrightability. |
| Production Type v. Nike | Feb 2023 | Unauthorized use of Kreuz Light in videos/social media; only 2 desktop + 1 audio license purchased |

### 7E. Font ML Training Litigation — Status
**Confidence: HIGH | Source: Smith #38 | Date: April 2026**

- **ZERO identified cases** of font-specific ML training litigation as of April 2026
- No precedent exists for font-as-training-data legal claims

### 7F. Broader ML Training Copyright Litigation (Context)
**Confidence: HIGH | Source: Smith #38 | Date: 2024–2025**

- Kadrey v. Meta, Bartz v. Anthropic, Salesforce LLM Litigation — book/text training cases
- Thomson Reuters v. Ross Intelligence (2024): using Westlaw headnotes to train legal AI = **NOT fair use**
- 2025 federal rulings: Two judges ruled copying books to derive statistical relationships for LLM training **IS fair use**; permanent reference library copies **NOT fair use**
- Courts actively split; no consensus as of April 2026

### 7G. Fonts vs. Images/Text — Critical Legal Distinction
**Confidence: HIGH | Source: Smith #38**

| Aspect | Fonts (US) | Images/Text ML Training |
|---|---|---|
| Copyright Status | Excluded (since 1992) | Fully copyrighted |
| Litigation Risk | Low (no copyright to infringe) | HIGH (active suits, split rulings) |
| Fair Use Defense | N/A (no copyright) | Disputed; courts split in 2025 |
| OFL License Binding | YES — enforceable | License obligations also apply |
| Precedent Status | Settled law (1978+) | Unsettled; 2025 rulings contradictory |

### 7H. Additional License Types (Nerd Fonts Context)
**Confidence: HIGH | Source: Smith #37**

| License | Fonts | ML Training Notes |
|---|---|---|
| Apache-2.0 | Arimo, Cousine, Droid Sans Mono, Meslo, Roboto Mono, Tinos | Most permissive; any use including commercial |
| MIT | Agave, Comic Shanns Mono, ProFont, ProggyClean, Symbols Only | Most permissive |
| CC BY-SA 4.0 | BigBlue Terminal | Share-alike required for derivatives; attribution required |
| Ubuntu Font License | Ubuntu (3 variants) | Attribution + license notice required; ambiguous RFN compliance |
| LGPL/WTFPL/Custom | Overpass, Gohu, Monofur, Heavy Data | Varies |
| BSD-3-Clause | IBM 3270 | Permissive |
| Bitstream Vera | Bitstream Vera Sans Mono, DejaVu Sans Mono, OpenDyslexic | Permissive |
| CC BY 4.0 | Glyph sources (Font Awesome, Material Design Icons) | Attribution required |

**Legal counsel recommendation (Smith #37):** Consult before ML training pipeline deployment if model outputs font files for distribution, training involves commercial deployment, or model modifies/merges multiple licensed fonts. Licenses designed for font redistribution — ML training outputs are an untested legal area.

---

## ══ SECTION 8: Nerd Fonts Project ══

**Source: Smith #37 | Date: 2026-04-09 (repo last push: 2026-03-17) | Confidence: MEDIUM (count), HIGH (license audit)**

### 8A. Overview
- **Repo:** github.com/ryanoasis/nerd-fonts
- **Function:** Iconic font aggregator/patcher — adds developer icon glyphs to base fonts
- **Glyph sources added:** Font Awesome, Devicons, Octicons, Material Design Icons, Powerline Symbols, Weather Icons, Font Logos, Pomicons, Codicons, IEC Power Symbols

### 8B. Patched Font Count
- **70 patched base fonts** (MEDIUM — counted from /patched-fonts/ directory, 2026-04-09)

**Full list:** 0xProto, 3270, AdwaitaMono, Agave, Anonymous Pro, Arimo, Atkinson Hyperlegible Mono, Aurulent Sans Mono, BigBlue Terminal, Bitstream Vera Sans Mono, Cascadia Code, Cascadia Mono, Code New Roman, Comic Shanns Mono, Commit Mono, Cousine, D2Coding, DaddyTime Mono, DejaVu Sans Mono, Departure Mono, Droid Sans Mono, Envy Code R, Fantasque Sans Mono, Fira Code, Fira Mono, Geist Mono, Go Mono, Gohu, Hack, Hasklig, Heavy Data, Hermit, IBM Plex Mono, Inconsolata (3 variants), Intel One Mono, Iosevka (3 variants), JetBrains Mono, Lekton, Liberation Mono, Lilex, M+, Martian Mono, Meslo, Monaspace, Monofur, Monoid, Mononoki, Nerd Fonts Symbols Only, Noto, OpenDyslexic, Overpass, ProFont, ProggyClean, Recursive, Roboto Mono, Share Tech Mono, Source Code Pro, Space Mono, Terminus, Tinos, Ubuntu (3 variants), Victor Mono, Zed Mono, iA Writer

### 8C. Open-Source Status of Base Fonts
- **All original unpatched base fonts are open-source** (HIGH — from license-audit.md, commit 6b41a31, 2026-04-09)
- License breakdown: ~45 SIL OFL 1.1 | 6 Apache-2.0 | 5 MIT | 3 Bitstream Vera | 1 BSD-3-Clause | 1 CC BY-SA 4.0 | 3 Ubuntu Font License | others LGPL/WTFPL/Custom

---

## ══ SECTION 9: Font Package Managers & Registries ══

**Source: Smith #40 | Date: April 2026**

### 9A. Registry Summary Table
| Registry | Count | Confidence | Date | Notes |
|---|---|---|---|---|
| Google Fonts | 1,929 families (543 variable) | HIGH | April 2026 | Baseline |
| Font Library (fontlibrary.org) | 6,000+ | MEDIUM | 2026 | ~3.1× Google Fonts; sister to Openclipart |
| Open Font Library (openfont.org) | 1,933 | MEDIUM | 2026 | ≈ Google Fonts size; distinct project |
| Bunny Fonts | ~1,492 | MEDIUM | 2026 | Privacy-first GF alternative; subset |
| Fontshare | 100 | HIGH | 2026 | All ITF originals; ITF Free Font License |
| Homebrew Cask | 2,000+ | MEDIUM | Pre-2023 | Migrated to main homebrew/cask 2023; no 2026 count |
| APT (Debian/Ubuntu) | 100+ packages | MEDIUM | 2026 | Varies by distro version |
| Arch/AUR | Hundreds | LOW | 2026 | No exact enumeration |
| Fedora/DNF | Not specified | INSUFFICIENT | 2026 | RPM Fusion hosts some GF packages |

### 9B. Key Structural Findings
- **Package managers (apt, pacman, Homebrew) abstract over existing registries** rather than hosting original fonts
- **Bunny Fonts** is a privacy-first *alternative* to Google Fonts, not a strict superset
- **No complete enumeration** exists for Arch/Fedora/APT — cumulative from multiple upstreams
- **Homebrew:** No current 2026 count; pre-2023 figure of 2,000+ may be stale

---

## ══ GAPS — Uncovered Topics ══

Themes not addressed by any Smith #31–40:

1. **EU vs. US legal framework for fonts and ML training** — Smith #38 was *truncated* mid-section on EU; EU analysis is missing from corpus
2. **VecGlypher 2.5K cutoff rationale** — explicitly flagged as unknown in Smith #33; no source explains why 2,500 Google Fonts were chosen for Stage 2
3. **Collletttivo file formats** — OTF confirmed via Font Squirrel, but TTF/WOFF/WOFF2 availability from official site is unconfirmed (MEDIUM confidence only)
4. **Open Foundry total collection size** — explicitly undisclosed on site; no Smith found a figure
5. **Nerd Fonts patched font ML licensing** — #37 covers base font licenses but does NOT address whether the *patched* versions (which add icon glyphs from separately-licensed sources like Font Awesome CC BY 4.0) create compounded licensing obligations for ML training
6. **CJK-specific open-source font collections** — covered in research dataset context (#33, #35) but no standalone curated CJK open-source collections surveyed
7. **Variable font collections specifically** — 543 variable families in Google Fonts noted (#40) but no dedicated variable font resource surveyed
8. **Adobe Fonts, DaFont, 1001Fonts (free tier)** — not covered
9. **Individual type designer GitHub repos** — beyond major foundries, not surveyed
10. **LoRA font training ablation data** — no published minimum-size ablation for font-specific LoRA exists; 25–40 figure from #33 is general image generation guidance extrapolated
11. **Homebrew Cask 2026 count** — pre-2023 figure only; current count requires `brew search font-` query
12. **Uncut.wtf licensing diversity** — OFL confirmed on several fonts but no complete license audit; "must check each font page" per #32

---

## ══ CONFIDENCE CONVERGENCE SUMMARY ══

*For Opus: findings where multiple Smiths independently agree (highest reliability)*

| Finding | Smiths Agreeing | Confidence |
|---|---|---|
| Google Fonts = 1,929 families (April 2026) | #34, #40 | ★★★ HIGHEST |
| OFL prohibits ML-trained font derivatives under non-OFL | #32, #37, #38 | ★★★ HIGHEST |
| OFL non-font AI outputs (images, design tools) are permitted | #32, #38 | ★★★ HIGH |
| GitHub ZIP is >1GB | #34, #39 | ★★★ HIGH |
| git clone + pull is recommended for bulk local sync | #34, #39 | ★★★ HIGH |
| All Nerd Fonts base fonts are open-source | #37 (license-audit.md) | ★★★ HIGH |
| US typefaces have no copyright protection since 1992 | #38 (established law) | ★★★ HIGH |
| Zero ML-training-specific font lawsuits as of April 2026 | #38 | ★★★ HIGH |
| TTF is canonical format in google/fonts (no OTF) | #34 | ★★ HIGH (single Smith, direct inspection) |
| Collletttivo: 16 fonts, all OFL, not on Google Fonts | #36 | ★★ HIGH (single Smith, direct fetch) |
| Uncut.wtf: 163 fonts total | #32 | ★★ HIGH (live site) |

---

*Anderson — Chain D complete. 10 Smiths organized. All unique signal preserved. Corrections applied. Disputes flagged. Gaps catalogued. Ready for Opus synthesis.*

============================================================
## Chain C — Anderson Report
============================================================

# CHAIN C — STRUCTURED FINDINGS FOR OPUS SYNTHESIS
**Smiths #21–#30 | Organized by Anderson | 2026-04-09**
**Source rounds: 21 complete | Triage: DEDUP · RECENCY · AGREE · DISAGREE · GAPS · CORRECT**

---

## SECTION 1 — LEGAL FRAMEWORK: ML TRAINING & FONT COPYRIGHT

### 1.1 US Copyright Law: Typeface vs. Font Software Distinction
**Source: Smith #21** | **Confidence: HIGH**

- **Typefaces** (the visual design) = NOT copyrightable in the United States. Precedent: *Eltra Corp. v. Ringer* (1978).
- **Font software** (the computer program rendering the typeface) = IS copyrightable.
- **ML training implication**: Using a font file for ML training may violate copyright on the *program* (the `.ttf`/`.otf` file itself), even when the underlying typeface design is unprotected.
- Source: [U.S. Copyright Office Circular 33](https://www.copyright.gov/circs/circ33.pdf); [Wikipedia on typeface IP](https://en.wikipedia.org/wiki/Intellectual_property_protection_of_typefaces)

---

### 1.2 US Copyright Office AI Report — Fair Use & ML Training
**Source: Smith #21** | **Confidence: HIGH** | **Date: May 2025 — MOST RECENT AUTHORITATIVE GUIDANCE IN THIS CHAIN**

- The U.S. Copyright Office concluded: **"Training [models] is not inherently transformative"** and may not qualify as fair use.
- Copyright law is explicitly "implicated" in AI training datasets.
- Source: [U.S. Copyright Office AI Report Part 3 (May 2025)](https://www.copyright.gov/ai/Copyright-and-Artificial-Intelligence-Part-3-Generative-Generative-AI-Training-Report-Pre-Publication-Version.pdf); [Wiley legal alert](https://www.wiley.law/alert-Copyright-Office-Issues-Key-Guidance-on-Fair-Use-in-Generative-AI-Training)
- **Note for Opus**: This is the freshest binding guidance in this Chain (published ~11 months before research date). Supersedes any earlier informal community consensus about "likely fair use."

---

### 1.3 OFL (SIL Open Font License) and ML Training — Ambiguity
**Sources: Smith #21, Smith #26, Smith #28** | **AGREE across 3 Smiths** | **Confidence: HIGH that ambiguity exists; LOW on whether training is permitted**

All three Smiths independently converge on the same legal gray area:

- OFL 1.1 **does not explicitly address** ML model training, derived model weights, or dataset use.
- OFL permits: use, modification, redistribution of the font files; documents created using OFL fonts are NOT covered by OFL.
- OFL FAQ and official text are silent on ML scenarios.
- **Practical community consensus** (Smith #26, Smith #28): Training likely permissible as it resembles "internal use," but no case law or explicit license clause confirms this.
- The Copyright Office May 2025 report (Smith #21) complicates this consensus — if training is not inherently transformative, OFL's silence is not a safe harbor.
- Source confirmations: [OFL FAQ](https://openfontlicense.org/ofl-faq/); [OFL official text](https://openfontlicense.org/open-font-license-official-text/)

---

### 1.4 GPL + Font Exception and ML Training
**Source: Smith #28** | **Confidence: MEDIUM**

- GNU FreeFont uses `GPL-3.0-or-later WITH Font-exception-2.0`.
- The Font Exception covers document embedding only; it does **not** mention training, derivative works, or dataset use.
- Broader GPL+ML training analysis (Smith #28):
  - No classic FOSS licenses mention "AI" or "training" explicitly. (Source: [Terms.Law, Dec 2025](https://www.terms.law/2025/12/05/training-on-open-source-code-what-gpl-mit-and-other-licenses-actually-say-about-ai/))
  - ML training is typically internal use (not distribution), potentially outside GPL's copyleft trigger.
  - Community assessment: Training on GPL material likely fair use; claim that "model is GPL because trained on GPL code" described as "at best a long shot, at worst counter-productive." (Source: [mjg59 blog](https://mjg59.dreamwidth.org/57615.html))
  - FSF is developing "free ML application" criteria (requires raw training data + scripts to be free) — **no final guidance yet as of April 2026**. (Source: [FSF News](https://www.fsf.org/news/fsf-is-working-on-freedom-in-machine-learning-applications))
- **Note for Opus**: The May 2025 Copyright Office report (Smith #21) is more authoritative than community blog posts; weight accordingly.

---

### 1.5 DaFont License Ambiguity (Platform-Specific Risk)
**Source: Smith #21** | **Confidence: HIGH (risk assessment); MEDIUM (quantitative estimates)**

- ~70% of DaFont fonts uploaded before ~2015 lack explicit license files. Copyright default applies to all unlicensed font software. (Source: [Nature Machine Intelligence dataset audit, 2024](https://www.nature.com/articles/s42256-024-00878-8) — flagged >70% license omission rates across popular datasets; applied here by inference.)
- "Free for Personal Use" fonts on DaFont explicitly prohibit commercial/derivative use. Training an ML model + commercially deploying the trained model likely violates this.
- No DaFont font explicitly permits "training ML models" or "synthetic data generation" as a use case. All DaFont licenses predate modern ML use cases (2012–2018 era).
- Redistribution/derivative restrictions on many DaFont fonts may be triggered if an ML-trained model generates new glyphs or variants = potential derivative work.
- **DaFont publishes no public statistics** on font counts by license category. Total collection size unknown (confirmed absence of API or public breakdown).

**DaFont License Risk Table (Smith #21):**

| Scenario | Legal Risk |
|---|---|
| "100% Free" / "Public Domain" / OFL/GPL fonts | Lower risk (still OFL ambiguity per §1.3) |
| "Free for Personal Use" fonts | HIGH — commercial model deployment likely violates |
| Unlicensed fonts (pre-2015, ~70%) | HIGH — copyright default |
| "Shareware/Demo" fonts | HIGH — trial restrictions likely violated |
| "Donationware" | MEDIUM — check individual terms |

---

## SECTION 2 — LICENSE TYPES: CATEGORIES & ML IMPLICATIONS

### 2.1 DaFont's Six Primary License Classifications
**Source: Smith #21** | **Confidence: HIGH**

| Category | ML Training Implication |
|---|---|
| Free / 100% Free | No explicit restriction, but no redistribution/modification |
| Free for Personal Use | HIGH RISK — commercial model deployment violates |
| Donationware | MEDIUM — individually check terms |
| Shareware/Demo | HIGH RISK — trial restrictions likely violated |
| Public Domain | Low risk — no copyright |
| GPL/OFL | Low-medium risk — OFL ambiguity (§1.3 above) |

---

### 2.2 Proprietary System Font Licenses — ML Training PROHIBITED
**Sources: Smith #26** | **Confidence: HIGH** | **AGREE across named fonts**

| Font | Licensor | ML Training Status |
|---|---|---|
| Arial | Monotype (licensed by Microsoft) | ❌ Prohibited — derivative works forbidden, redistribution requires separate Monotype license |
| Times New Roman | Monotype (licensed by Microsoft) | ❌ Prohibited — same as Arial |
| Segoe UI | Microsoft/Monotype | ❌ Prohibited — redistribution generally prohibited |
| San Francisco | Apple | ❌ Prohibited — licensed only for Apple platform UI mockups by registered developers |
| Helvetica Neue (pre-macOS El Capitan) | Linotype/Monotype | ❌ Prohibited — proprietary, not open source (MEDIUM confidence) |

Sources: [Microsoft Typography FAQ](https://learn.microsoft.com/en-us/typography/fonts/font-faq); [Microsoft Q&A on Arial/Times New Roman](https://learn.microsoft.com/en-us/answers/questions/5450988/font-license-arial-and-times-new-roman); [Wikipedia — San Francisco typeface](https://en.wikipedia.org/wiki/San_Francisco_(sans-serif_typeface))

---

### 2.3 Open/Permissive Font Licenses — Summary Status
**Sources: Smith #26, Smith #27, Smith #28, Smith #29** | **AGREE across 4 Smiths**

| License | Font Examples | Redistribution | ML Training |
|---|---|---|---|
| SIL OFL 1.1 | Liberation (v2+), Cascadia Code, Omnibus-Type, Paratype PT, Inter, Fraunces, most Google Fonts | ✅ Yes | ⚠️ Ambiguous (§1.3) |
| Bitstream Vera / Extended MIT | DejaVu | ✅ Yes | ⚠️ Ambiguous — no explicit ML clause |
| GPL-3.0+ WITH Font-exception-2.0 | GNU FreeFont | ✅ (under GPL) | ⚠️ Ambiguous (§1.4) |
| Apache 2.0 | Roboto Flex | ✅ Yes | ⚠️ No explicit ML clause, but Apache 2.0 is generally permissive |
| ITF Free Font License (proprietary) | Fontshare | ✅ Commercial use | ❌ Not explicitly permitted — contact ITF |
| Atipo Custom Proprietary | Atipo Foundry free fonts | ✅ Commercial use | ⚠️ "No derivative works" clause creates risk |

---

## SECTION 3 — FOUNDRY PROFILES: FREE/OPEN COLLECTIONS

### 3.1 Fontshare by Indian Type Foundry (ITF)
**Source: Smith #22** | **Confidence: MEDIUM (counts); HIGH (license terms)**

- **What**: Free font service launched 2021 by ITF (Indian Type Foundry). Professional-grade curated typefaces for personal and commercial use at no cost.
- **Size**: ~100 font families (launched with 50 in 2021, expanded to ~100 by 2025–2026). Sources: [Abduzeedo](https://abduzeedo.com/fontshare-free-fonts-100-quality-typefaces-designers), [Mainstream.dev](https://mainstream.dev/fontshare)
- **License**: ITF Free Font License (proprietary — NOT OFL/GPL/CC0)
  - ✅ Commercial use permitted without restriction
  - ✅ Client work, products, marketing, websites, apps: all allowed
  - ❌ Resale of font files prohibited
  - ❌ Redistribution on other font platforms prohibited
  - ❌ Modification and re-release under different name prohibited
  - ❌ **ML Training: No explicit permission. License does not address training datasets. Contact ITF directly for clarification.**
  - Source: [ITF FFL License](https://www.fontshare.com/licenses/itf-ffl)
- **Download**: No registration required. ZIP contains OTF (desktop) + WOFF2 (web).
- **Notable families**: Satoshi (most popular, variable + 10+ styles), General Sans (9 weights + italics), Clash Display (6 weights), Clash Grotesk, Boska (display serif), Gambetta (serif), JetBrains Mono (monospaced)
- **Pairing resources**: 59 pre-curated editorial font combinations available on-site.
- Source: [fontshare.com](https://fontshare.com/); [ITF News](https://www.indiantypefoundry.com/news/introducing-fontshare)

---

### 3.2 Atipo Foundry
**Source: Smith #23** | **Confidence: HIGH (inventory); MEDIUM (license interpretation for ML)**

- **What**: Spanish foundry based in Gijón, established 2009. Founders: Raúl García del Pomar & Ismael González.
- **Free font families**: 37 families with free weights, available via "pay what you want" model (optional social share).
  - Full list: Alcyone, Archia, Argesta, Bariol, Bariol Icons, Bariol Serif, Basier, Basier Mono, Basier Narrow, Borna, Bould, Brockmann, Calendas Plus, Cassannet Plus, Chaney, Doumbar, Geomanist, Gottak, Knile, N27, Novela, Noway, Noway Round, Nudica, Nudica Mono, Quablo, Rawest, Rouna, Safiro, Salomé, Sawton, Sharphy, Silka, Silka Mono, Strawford, Swiza, Wotfard
- **License**: Custom proprietary (NOT OFL, GPL, or CC0)
  - ✅ Personal and commercial use allowed
  - ❌ Max 5 workstations at single location
  - ❌ No modification/adaptation of font files
  - ❌ No reverse engineering, decompiling, or derivative works
  - Separate webfont license required for web embedding
  - License is perpetual (no renewal needed)
  - **ML Training**: NOT explicitly permitted. "No derivative works" and "no modification" clauses are ambiguous regarding ML training. License predates ML use cases. **Contact required**: info@atipo.es
- **Download locations**:
  - Primary: [atipofoundry.com](https://www.atipofoundry.com) (direct download)
  - Mirror: [FontsArena](https://fontsarena.com/created-by/atipo-foundry/)
  - Mirror: [OnlineWebFonts](https://www.onlinewebfonts.com/fonts/atipo_foundry)
- Source: [atipofoundry.com](https://www.atipofoundry.com); [License page](https://www.atipofoundry.com/license); [FontsArena](https://fontsarena.com/created-by/atipo-foundry/)

---

### 3.3 Omnibus-Type
**Source: Smith #24** | **Confidence: HIGH (license); MEDIUM/LOW (exact family count)**

- **What**: Collective type foundry and creative studio, based in Buenos Aires, Argentina. Focus on print and screen fonts.
- **License**: **SIL Open Font License (OFL) — ALL fonts** | HIGH confidence. Fully free for personal and commercial use.
- **Size**: ~20–27+ font families. Most comprehensive source (Fonts In Use database) lists 12 documented + 15+ additional typefaces = ~27 distinct typefaces. Note: some entries may be sub-families/variants (e.g., Archivo Black, Archivo Narrow, Chivo Mono) rather than independent families. | MEDIUM/LOW confidence
- **Distribution channels**: GitHub ([omnibus-type org](https://github.com/omnibus-type)), Google Fonts, Font Squirrel, Adobe Fonts, official website (omnibus-type.com)
- **Notable families**:
  - *Press Series*: Faustina (8 styles, editorial serif), Manuale (8 styles), Rosario (transitional serif), Saira (126 total styles: 9 weights × 7 widths — MEDIUM confidence on count), Texturina (36 styles: 18 display + 18 text — MEDIUM)
  - *Core Sans-Serif*: Archivo (grotesque, 200+ languages), Archivo Narrow, Archivo Black, Asap (8 styles), Chivo (14 styles: 7 weights + italics)
  - *Display & Decorative*: Ballet (Spencerian script), MuseoModerno (geometric, created for Buenos Aires Museum of Modern Art), Grenze (9 weights + italics, Roman/Blackletter hybrid), Grenze Gotisch (9 weights), Sansita (6 weights + italics), Sansita Swashed (6 weights)
  - *Specialized*: Unna (8 styles), Labrada (contemporary serif, woodcut-inspired), Pragati Narrow (Devanagari/Indic script)
  - *Additional (LOW confidence)*: Bahiana, Bahianita, Barriecito, Barrio, Chivo Mono, Jaldi, Leluja Original, Rigby, Saira Stencil One, Truculenta
- Source: [omnibus-type.com](https://www.omnibus-type.com/); [GitHub](https://github.com/omnibus-type); [Google Fonts](https://fonts.google.com/?query=Omnibus-Type); [Fonts In Use](https://fontsinuse.com/foundry/1865/omnibus-type)

---

### 3.4 GNU FreeFont
**Source: Smith #28** | **Confidence: HIGH (structure, license); MEDIUM (glyph counts — data from 2012)**

- **What**: Three free Unicode outline font families. Initiated 2002 by Primož Peterlin; maintained by Steve White.
- **Three families × 4 styles = 12 font files total**:
  - FreeSans (sans-serif), FreeSerif (serif), FreeMono (monospace)
  - Each in: Regular, Bold, Italic/Oblique, Bold Italic/Oblique
- **License**: `GPL-3.0-or-later WITH Font-exception-2.0` (SPDX identifier)
  - Font Exception permits: embedding unmodified font in documents, creating/publishing/redistributing/displaying documents using font, commercial & non-commercial use
  - GPL still requires: distributing font software *separately* from documents → full GPL compliance
  - ML Training: NOT addressed by exception (exception scope = document embedding only). See §1.4.
- **Glyph counts** (⚠️ DATA FROM 2012-05-03 RELEASE — potentially outdated):
  - FreeSerif: 10,537 glyphs
  - FreeSans: 6,272 glyphs
  - FreeMono: 4,178 glyphs
- **Script coverage**: Latin, Cyrillic, Arabic, Greek, Hebrew, Armenian, Georgian, Thaana, Syriac, Devanagari, Bengali, Gujarati, Gurmukhi, Sinhala, Tamil, Malayalam, Thai, Tai Le, Kayah Li, Hanunóo, Buginese, Cherokee, Unified Canadian Aboriginal Syllabics, Ethiopian, Tifnagh, Vai, Osmanya, Coptic, Glagolitic, Gothic, Runic, Ugaritic, Old Persian, Phoenician, Old Italic, Braille, IPA, currency symbols, diacritics, TeX math symbols
- **Download**: [GNU FTP](ftp://ftp.gnu.org/gnu/freefont/); [GNU Savannah](https://savannah.gnu.org/projects/freefont/)
- Source: [Wikipedia — GNU FreeFont](https://en.wikipedia.org/wiki/GNU_FreeFont); [GNU FreeFont License](https://www.gnu.org/software/freefont/license.html); [SPDX Font-exception-2.0](https://spdx.org/licenses/Font-exception-2.0.html)

---

### 3.5 Paratype PT Fonts
**Source: Smith #29** | **Confidence: HIGH (license, Google Fonts presence); MEDIUM (weights, character counts)**

- **What**: Three-family set commissioned by Rospechat (Russian Ministry of Communications) for Peter the Great orthography reform 300th anniversary.
- **Release**: PT Sans + PT Serif: 2009–2010; PT Mono: end of 2011 | MEDIUM confidence
- **License**: SIL Open Font License (OFL) v1.1 | HIGH confidence (also originally released under ParaType's own Free Font License for PT Sans)
- **Google Fonts**: YES — all three families present | HIGH confidence (confirmed April 2026)
- **Styles/Weights**:
  - PT Sans: 4 styles (Regular, Bold, Italic, Bold Italic) | MEDIUM confidence
  - PT Serif: 4 styles (Regular, Bold, Italic, Bold Italic) | MEDIUM confidence
  - PT Mono: 2 styles (Regular, Bold) | MEDIUM confidence
  - Note: Commercial PT Sans Pro / PT Serif Pro (not free): 6+ weights with extended styles (light–black, condensed, extra-condensed, caption variants)
- **Character coverage**: ~1,400 characters total per font | MEDIUM confidence
  - Basic Latin (full ASCII), Latin-1 Supplement, Latin Extended-A/B, Latin Extended Additional, Cyrillic
  - Supports all 54 title languages of Russian Federation + minority scripts
  - Includes Cyrillic small caps, lining/old-style figures, fractions, indices
- **Official repository**: [paratype.com](https://www.paratype.com); GitHub references available
- Source: [PT Fonts Wikipedia](https://en.wikipedia.org/wiki/PT_Fonts); [PT Sans Google Fonts](https://fonts.google.com/specimen/PT+Sans); [PT Serif Google Fonts](https://fonts.google.com/specimen/PT+Serif); [PT Mono Google Fonts](https://fonts.google.com/specimen/PT+Mono); [TUGboat overview](https://www.tug.org/TUGboat/tb32-1/tb100farar.pdf)

---

## SECTION 4 — SYSTEM/BUNDLED FONTS

### 4.1 DejaVu Fonts
**Sources: Smith #26, Smith #27** | **AGREE on all core facts** | **Confidence: HIGH**

- **What**: Three-family set (Sans, Serif, Mono) descended directly from Bitstream Vera. Created by Štěpán Roh to expand character coverage.
- **Lineage**: DejaVu = Bitstream Vera (sans) + Bitstream Charter (serif) + expanded glyphs from Olwen, Bepa, Arev, and SUSE Linux fonts. Bitstream Vera was limited to Basic Latin + Latin-1 (~256 chars); DejaVu expanded to MES-1/MES-2/MES-3 Unicode subsets.
- **License**: Extended MIT (Bitstream Vera license + public domain for DejaVu additions)
  - Bitstream Vera license: permits modifications if renamed (no "Bitstream" or "Vera" in name); redistribution free but cannot be sold standalone
  - DejaVu's added changes: deeded to public domain
- **Total font files**: 23 | HIGH confidence (from GitHub repo)
  - Sans: 8 variants (Regular, Bold, Oblique, Bold Oblique, ExtraLight + others)
  - Serif: 8 variants
  - Mono: 4 variants
  - Math TeX Gyre: 1
  - Plus LGC subset versions (Latin/Greek/Cyrillic only)
- **ASCII coverage**: 100% | HIGH confidence
  - Full Unicode support including: Latin, Greek, Cyrillic, Armenian, Georgian, Hebrew, Arabic, Lao, math symbols, arrows, braille
- **Platform bundling** (Smith #26): Ubuntu, Debian, Fedora, RHEL bundle DejaVu. Note: Ubuntu 23.10+ began replacing some DejaVu variants with Noto fonts, but **DejaVu Mono remains** in Ubuntu as of Oct 2023. | HIGH confidence
- **Latest version**: 2.37 (July 30, 2016) | HIGH confidence — note: **no updates in 10+ years**
- **Download**: [dejavu-fonts.github.io](https://dejavu-fonts.github.io/); [GitHub](https://github.com/dejavu-fonts/dejavu-fonts) (TTF + SFD/FontForge source)
- Source: [DejaVu License](https://dejavu-fonts.github.io/License.html); [GitHub](https://github.com/dejavu-fonts/dejavu-fonts); [Wikipedia — DejaVu](https://en.wikipedia.org/wiki/DejaVu_fonts); [OMG Ubuntu Ubuntu 23.10](https://www.omgubuntu.co.uk/2023/07/ubuntu-noto-fonts-change-mantic)

---

### 4.2 Liberation Fonts
**Sources: Smith #26, Smith #27** | **AGREE on core facts; ⚠️ DATE CONFLICT — see §DISPUTES**

- **What**: Three-family set (Sans, Serif, Mono) created by Red Hat (contracted to Ascender Corp.) as metrically compatible free replacements for Microsoft's core fonts.
- **Metric equivalence**: Liberation Sans = Arial; Liberation Serif = Times New Roman; Liberation Mono = Courier New (identical character widths/heights = drop-in document substitution)
- **License**: SIL Open Font License (OFL) v1.1 | HIGH confidence
- **Total styles**: ~12 (3 families × 4 weights each: Regular, Bold, Italic, Bold Italic) | MEDIUM confidence (exact count not explicitly stated in primary sources)
- **ASCII coverage**: 100% | HIGH confidence
  - Total ~2,299 Unicode characters per font | HIGH confidence (Smith #27)
  - Additional coverage: Latin-1 Supplement (96), Latin Extended-A (128), Latin Extended-B (11), Greek/Coptic (73), Cyrillic (94), mathematical operators, box drawing, geometric shapes
- **Relationship to Bitstream Vera**: None — separate lineage. Liberation 2.x was based on Google's Croscore fonts.
- **Latest version**: 2.1.5 (September 30, 2021) | HIGH confidence (Smith #27)
- **Download**: [GitHub — liberation-fonts](https://github.com/liberationfonts/liberation-fonts) (TTF + source)
- Source: [Wikipedia — Liberation fonts](https://en.wikipedia.org/wiki/Liberation_fonts); [GitHub](https://github.com/liberationfonts/liberation-fonts); [FOSSA on OFL](https://fossa.com/blog/open-source-licenses-101-sil-open-font-license-ofl/)

---

### 4.3 Bitstream Vera (Parent Font — Reference)
**Source: Smith #27** | **Confidence: HIGH**

- **License**: Custom free license (2003)
  - Permits derivatives if renamed (no "Bitstream"/"Vera" in name); free redistribution; no standalone sale
  - **Historical significance**: Directly inspired creation of SIL Open Font License (OFL) in 2005
- **Coverage**: Basic Latin (ASCII) + Latin-1 Supplement only (~256 chars — intentionally limited, driving DejaVu's creation)

---

### 4.4 Cascadia Code (Windows)
**Source: Smith #26** | **Confidence: HIGH**

- **License**: SIL OFL 1.1
- **Bundling**: Included in Windows Terminal since v0.5.2762.0; included in Windows 11
- **ML Training**: ⚠️ Ambiguous (OFL gray area per §1.3)
- Source: [Microsoft Learn — Cascadia Code](https://learn.microsoft.com/en-us/windows/terminal/cascadia-code); [GitHub — microsoft/cascadia-code](https://github.com/microsoft/cascadia-code)

---

## SECTION 5 — ACADEMIC DATASETS: FONT RESEARCH PAPERS

**Source: Smith #25** | All data HIGH confidence unless noted

### 5.1 FontDiffuser (AAAI 2024 — arXiv 2312.12142)
**Date: December 2023 (arXiv) / February 2024 (AAAI) — ~2 years old**

| Metric | Value | Confidence |
|---|---|---|
| Total fonts collected | 424 | HIGH |
| Training fonts ("seen fonts") | 400 | HIGH |
| Training characters | 800 Chinese | HIGH |
| Test set 1 (SFUC) | 100 seen fonts + 272 unseen chars | HIGH |
| Test set 2 (UFUC) | 24 unseen fonts + 300 unseen chars | HIGH |
| Dataset source | NOT explicitly stated | LOW |
| Public release | ❌ No | HIGH |

- GitHub: [yeungchenwa/FontDiffuser](https://github.com/yeungchenwa/FontDiffuser)
- AAAI: [proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/28482)

---

### 5.2 HFH-Font (ACM ToG 2024 — arXiv 2410.06488)
**Date: October 2024 (arXiv) / December 2024 (ACM ToG) — ~6 months old**

| Metric | Value | Confidence |
|---|---|---|
| Total characters | 6,763 Chinese | HIGH |
| Large dataset fonts | 3,538 fonts | HIGH |
| Small dataset fonts | 438 fonts | HIGH |
| Training fonts (used) | 3,500 | HIGH |
| Training characters | 5,500 | HIGH |
| Test characters (seen) | 640 | HIGH |
| Test characters (unseen) | 488 | HIGH |
| Dataset source | NOT stated — appears internal Chinese collection | LOW |
| Public release | ❌ No | HIGH |

- GitHub: [grovessss/HFH-Font](https://github.com/grovessss/HFH-Font)
- ACM ToG: [doi.org/10.1145/3687994](https://dl.acm.org/doi/10.1145/3687994)

---

### 5.3 VecGlypher (CVPR 2026 — arXiv 2602.21461)
**Date: February 2026 — CURRENT. Note: Memory context flags Ref2Font beats VecGlypher.**

| Metric | Value | Confidence |
|---|---|---|
| Stage 1 source | Envato Elements | HIGH |
| Stage 1 fonts | 39,000 | HIGH |
| Stage 1 tag quality | Noisy, marketing-oriented; <15 tags/font | HIGH |
| Stage 2 source | Google Fonts | HIGH |
| Stage 2 fonts | 2,500 | HIGH |
| Stage 2 tag quality | Expert-curated, appearance-focused | HIGH |
| Public access | ✅ BOTH sources publicly accessible | HIGH |

- Envato Elements: ~25,000+ fonts via paid subscription — [elements.envato.com/fonts](https://elements.envato.com/fonts)
- Google Fonts: 1,929 families (April 2026); 543 variable families — FREE, open-source — [fonts.google.com](https://fonts.google.com/); [GitHub google/fonts](https://github.com/google/fonts)
- VecGlypher: [arXiv](https://arxiv.org/abs/2602.21461); [Project page](https://xk-huang.github.io/VecGlypher/); [GitHub](https://github.com/xk-huang/VecGlypher); [HuggingFace](https://huggingface.co/VecGlypher)

---

### 5.4 DeepVecFont (SIGGRAPH Asia 2021 — arXiv 2110.06688)
**Date: October 2021 — ~4.5 years old ⚠️ FLAG: Potentially outdated**

| Metric | Value | Confidence |
|---|---|---|
| English training fonts | 8,035 | HIGH |
| English test fonts | 1,425 | HIGH |
| Chinese training fonts | 212 | HIGH |
| Chinese test fonts | 34 | HIGH |
| Dataset origin | Subset of SVG-VAE (ICCV 2019) | HIGH |
| SVG-VAE foundation | 14 million examples of 62-char set | HIGH |
| Public release | ⚠️ Partial — access verification required | MEDIUM |

- SVG-VAE source: [Magenta/SVG-VAE](https://magenta.tensorflow.org/svg-vae)
- Data access: Google Drive (link in repo), Kaggle mirror ([deepvecfont-dataset](https://www.kaggle.com/datasets/rainei/deepvecfont-dataset)), DeepVecFont-v2 (2023) via OneDrive or Baiduyun (password: pmr2)
- GitHub: [yizhiwang96/deepvecfont](https://github.com/yizhiwang96/deepvecfont); [yizhiwang96/deepvecfont-v2](https://github.com/yizhiwang96/deepvecfont-v2)

---

### 5.5 Academic Dataset Summary
**Source: Smith #25**

| Paper | Year | Total Fonts | Data Source | Publicly Accessible? |
|---|---|---|---|---|
| FontDiffuser | 2023/2024 | 424 | Internal | ❌ No |
| HFH-Font | 2024 | 3,538 + 438 | Internal Chinese | ❌ No |
| VecGlypher | 2026 | 39,000 + 2,500 | Envato (paid) + Google Fonts (free) | ✅ Yes (with caveats) |
| DeepVecFont | 2021 | 9,460 English + 246 Chinese | SVG-VAE subset | ⚠️ Partial |

**Notable**: All Chinese font datasets are internal/proprietary. No open-source large Chinese font dataset identified.

---

## SECTION 6 — VARIABLE FONTS: MULTI-AXIS INVENTORY

**Source: Smith #30** | All SIL OFL unless noted | Confidence HIGH unless noted

### 6.1 3-Axis Variable Fonts

| Font | Axes | License | Source/Download |
|---|---|---|---|
| **Inter** | Weight (100–900), Slant (−10°–0°), Optical Size (6–72pt) | SIL OFL 1.1 | [rsms.me/inter](https://rsms.me/inter/); [Google Fonts](https://fonts.google.com/specimen/Inter) |
| **Bricolage Grotesque** | Weight, Width (condensed–expanded), Optical Size | SIL OFL 1.1 | [GitHub](https://github.com/ateliertriay/bricolage); [Google Fonts](https://fonts.google.com/specimen/Bricolage+Grotesque) |
| **Source Serif 4** | Weight (200–900), Optical Size (8–60pt), Italic (0–1) | SIL OFL | [GitHub adobe-fonts/source-serif](https://github.com/adobe-fonts/source-serif); [Adobe Fonts](https://fonts.adobe.com/fonts/source-serif-4-variable) |
| **Newsreader** | Weight (200–800), Optical Size (6–72pt), Italic (0–1) | Open-source (Google commissioned) | [Google Fonts](https://fonts.google.com/specimen/Newsreader); [GitHub](https://github.com/productiontype/NewsReader) |
| **Playfair Display** | Weight (400–900), Width (semi-condensed–semi-expanded), Optical Size | SIL OFL | [GitHub clauseggers/Playfair](https://github.com/clauseggers/Playfair); [Google Fonts](https://fonts.google.com/specimen/Playfair) |
| **Instrument Sans** | Weight (400–900), Width (75–100), Italic (0–1) | Open-source | [GitHub Instrument/instrument-sans](https://github.com/Instrument/instrument-sans) | MEDIUM confidence |

---

### 6.2 4-Axis Variable Fonts (including custom axes)

| Font | Axes | Custom Axes | License | Download |
|---|---|---|---|---|
| **Mona Sans** | Weight, Width (condensed–expanded), Slant, Optical Size (1–100pt) | None (all registered) | SIL OFL 1.1 | [GitHub github/mona-sans](https://github.com/github/mona-sans) — v2.0.8+ adds optical size |
| **Recursive** | Weight (300–1000), Slant (0°–−15°), **Casual** (0–1), **Monospace** (0–1) | Casual, Monospace | SIL OFL | [Google Fonts](https://fonts.google.com/specimen/Recursive) — morphs sans-serif → handwriting → monospace |
| **Fraunces** | Weight, **Softness** (serif inkiness/wetness, 0–100), **Wonk** (wonky character substitution, 0–1), Optical Size | Softness, Wonk | SIL OFL | [GitHub undercasetype/Fraunces](https://github.com/undercasetype/Fraunces); [Google Fonts](https://fonts.google.com/specimen/Fraunces) |

---

### 6.3 6-Axis Variable Font

| Font | Axes | Custom Axes | License | Date | Download |
|---|---|---|---|---|---|
| **Google Sans Flex** | Weight, Width, Optical Size, Slant, **Grade** (0–1), **Roundedness** (crisp–soft) | Grade, Roundedness | SIL OFL | November 2025 open-source release | [Google Fonts](https://fonts.google.com/specimen/Google+Sans+Flex) |

**Note**: Google Sans Flex was previously proprietary; open-sourced November 2025. HIGH confidence.

---

### 6.4 12+ Axis (Parametric) Variable Fonts

**Roboto Flex**
- **Axes**: Weight, Width, Slant, Optical Size (8–144pt), Grade + 8 parametric axes: XOPQ, XTRA, YOPQ, YTAS, YTDE, YTFI, YTLC, YTUC = **12–13 axes total**
- **License**: Apache 2.0 (open-source — more permissive than OFL on ML training; no explicit ML clause but generally permissive)
- **Launch**: May 2022
- **Download**: [Google Fonts](https://fonts.google.com/specimen/Roboto+Flex); [GitHub TypeNetwork/Roboto-Flex](https://github.com/TypeNetwork/Roboto-Flex)

**Amstelvar**
- **Axes**: Weight (100–1000), Width (60–200), Optical Size (8–144pt), Grade (−60 to +60) + additional parametric axes = **4 registered + parametric**
- **License**: Open-source (Type Network) | HIGH confidence
- **Note**: Described as early variable font pioneer
- **Download**: [v-fonts.com/fonts/amstelvar](https://v-fonts.com/fonts/amstelvar)

---

## SECTION 7 — CORRECTIONS

### CORRECTION C-1: Liberation Fonts — Version/Date Discrepancy
**Smiths involved: #26, #27** | **⚠️ FLAG FOR OPUS**

- Smith #26 states: Liberation fonts moved to SIL OFL "as of v2.00.0, **Dec 2018**"
- Smith #27 states: "Liberation **2.00.0 (2012)** was based on Google's Croscore fonts to overcome licensing restrictions"
- These are **mutually incompatible** date attributions for the same version number.
- Smith #27 also gives latest version as 2.1.5 (September 30, 2021), which implies v2.00.0 predates 2021, favoring 2012.
- **Best current assessment**: v2.00.0 was likely released around 2012 (Smith #27 MEDIUM confidence), not Dec 2018. The Dec 2018 date in Smith #26 may refer to a different milestone or may be an error. Both Smiths agree the *current* license is SIL OFL 1.1 (HIGH confidence).
- **Recommendation for Opus**: Verify Liberation v2.00.0 release date against [GitHub release history](https://github.com/liberationfonts/liberation-fonts/releases). Do not cite "Dec 2018" for v2.00.0 without verification.

---

### CORRECTION C-2: Cascadia Code Inclusion — Clarification Needed
**Source: Smith #26** | MEDIUM priority

- Smith #26 says Cascadia Code "BUNDLED since Windows Terminal 0.5.2762.0; included in Windows 11."
- This is accurate but may need clarification: Cascadia Code is bundled with *Windows Terminal*, not with Windows 11 OS itself (it's the default terminal font, not a system UI font like Segoe UI). Opus should not conflate these — Cascadia Code is separately downloadable under OFL regardless.

---

### CORRECTION C-3: GNU FreeFont Glyph Counts — Staleness Flag
**Source: Smith #28** | MEDIUM priority

- Glyph counts (FreeSerif: 10,537; FreeSans: 6,272; FreeMono: 4,178) derive from the 2012-05-03 release.
- Latest version may differ. Smith #28 explicitly flags this as ⚠️ POTENTIALLY OUTDATED.
- **Recommendation**: Treat as approximate lower bounds. Do not present as current precise figures without fresh verification from [GNU Savannah](https://savannah.gnu.org/projects/freefont/).

---

### CORRECTION C-4: VecGlypher Google Fonts Count
**Source: Smith #25** | LOW priority

- Smith #25 states Google Fonts has "2,500 fonts" (VecGlypher Stage 2 training set) but separately notes "1,929 font families (April 2026)."
- The 2,500 figure = VecGlypher's internal training corpus (may include style variants counted as separate fonts), not the publicly visible family count.
- The 1,929 figure = current Google Fonts public catalog count (April 2026, HIGH confidence).
- These figures are not contradictory but should not be conflated. VecGlypher's "2,500" likely counts individual style files, not families.

---

## SECTION 8 — DISPUTES

### DISPUTE D-1: OFL ML Training — "Likely Permissible" vs. "Legally Uncertain"
**Smiths: #26 vs. #21 (+ Copyright Office May 2025)** | **⚠️ GENUINE DISPUTE**

- Smith #26 and Smith #28 lean toward "likely permissible" based on community ML consensus and "internal use" reasoning.
- Smith #21 introduces the May 2025 U.S. Copyright Office finding that training "is not inherently transformative" and may not be fair use — directly cutting against the community consensus position.
- **Resolution guidance**: The Copyright Office report (May 2025, Smith #21) is the most authoritative and recent source. Smiths #26 and #28 predate or do not cite this report. Opus should apply RECENCY rule and weight the Copyright Office position heavily.
- **Not resolved by this Chain**: Whether OFL's structure (as a specific proprietary software license, not a general copyright restriction) changes the fair use analysis. Requires legal expert input.

---

### DISPUTE D-2: GPL Font ML Training — "Likely Fair Use" vs. "Uncertain"
**Smiths: #28 (internal)** | **MEDIUM priority — internal tension, not a cross-Smith dispute**

- Smith #28 presents both positions within a single report:
  - Community view: "likely fair use, NOT a derivative work" (MEDIUM confidence)
  - FSF view: Developing new "free ML application" criteria — suggests current GPL framework is inadequate/unsettled for ML
- The Copyright Office May 2025 finding (from Smith #21, which Smith #28 does not cite) further undermines the "likely fair use" position.
- **Status**: Genuinely unsettled. Flag for Opus.

---

### DISPUTE D-3: Fontshare ML Training — Not a Dispute, But a Gap
**Source: Smith #22** | LOW priority (noting for completeness)

- Smith #22 correctly identifies no explicit permission and recommends contacting ITF.
- No conflicting Smith asserts permission exists.
- **Status**: Absence of permission ≠ prohibition, but ITF license predates ML use cases. Non-dispute; actionable gap.

---

## SECTION 9 — GAPS (Uncovered Topics)

### GAP-1: Noto Fonts
- Smith #26 mentions Ubuntu 23.10+ replacing some DejaVu variants with **Noto fonts**, but no Smith in Chain C covers Noto's license, family count, script coverage, or ML training status.
- Noto is a major open-source font project (Google) with comprehensive Unicode coverage. HIGH priority gap.

### GAP-2: Adobe Source Fonts Family (Beyond Source Serif 4)
- Smith #30 covers Source Serif 4 as a variable font.
- No Smith covers Source Sans 3, Source Code Pro, Source Han (CJK) — all open-source under SIL OFL or Adobe's open licenses.
- Source Han in particular would be the only major open-source CJK font family not covered.

### GAP-3: CJK / Non-Latin Font Sources
- Academic dataset Smiths (#25) show large Chinese font datasets exist but are all internal/proprietary.
- No Chain C Smith covers open-source CJK repositories (Google Noto CJK, Source Han, CJKOS, etc.) for training dataset assembly.

### GAP-4: Font Squirrel Licensing Terms
- Smith #24 mentions Omnibus-Type fonts on Font Squirrel (MEDIUM confidence).
- No Smith covers Font Squirrel's platform-level licensing terms for ML training use.

### GAP-5: Monotype / Adobe Commercial Font ML Licensing
- Chain C covers open/free sources comprehensively. No coverage of Monotype's or Adobe's paid ML licensing tiers or agreements for commercial dataset use.

### GAP-6: Envato Elements Licensing for ML Training
- Smith #25 identifies Envato as VecGlypher's 39,000-font Stage 1 source (paid subscription).
- No Smith covers Envato's terms of service regarding ML training dataset use — this is the single largest font pool identified in Chain C and its ML licensing status is unknown.

### GAP-7: Variable Font Counts for Foundry Profiles
- Sections 3.1–3.5 (Fontshare, Atipo, Omnibus-Type, GNU FreeFont, Paratype) do not specify which fonts are available as variable fonts with multiple axes.
- Only Section 6 (Smith #30) covers variable fonts, but exclusively as standalone inventory — not cross-referenced to foundry profiles.

### GAP-8: Current DaFont Total Collection Size
- Smith #21 confirms no public count or API exists. Total collection remains unknown.
- Stated only: "thousands of fonts across ~20 years of operation."

### GAP-9: Fontshare / Atipo Unicode Coverage
- Neither Smith #22 (Fontshare) nor Smith #23 (Atipo) includes glyph counts, Unicode block coverage, or language support data.

### GAP-10: Inter Font Foundry/License Deep-Dive
- Smith #30 covers Inter as a variable font. No Chain C Smith profiles Inter as a foundry/collection (creator: Rasmus Andersson; license: SIL OFL 1.1; ~3,895 glyphs per weight; Latin + Cyrillic + Greek + Vietnamese).

---

## META-NOTES FOR OPUS

1. **Most Authoritative Recent Source in Chain**: U.S. Copyright Office AI Report Part 3 (May 2025), cited in Smith #21. Changes the legal landscape for the OFL/GPL "likely permissible" community consensus claims in Smiths #26 and #28.

2. **Freshest Data**: Smith #30 (variable fonts, April 2026 research), Smith #23 (Atipo April 2026), Smith #24 (Omnibus-Type April 2026) — all current. VecGlypher data (Smith #25) from February 2026 paper — also current.

3. **Stalest Data Requiring Caution**: 
   - GNU FreeFont glyph counts (Smith #28): 2012 data
   - Liberation fonts v2.00.0 date (Smiths #26/#27): conflicting, needs verification
   - DeepVecFont datasets (Smith #25): 2021 paper, access status should be re-verified

4. **Memory Context Integration Note**: Project MEMORY.md confirms VecGlypher is deprioritized in favor of FLUX.2 + Ref2Font approach. Smith #25's VecGlypher dataset details remain useful for understanding the dataset landscape even if the model is not primary.

5. **Chain C Coverage Profile**: This chain covers (a) legal/licensing framework for ML training, (b) specific free/open foundries as acquisition targets, (c) academic paper dataset sizes for benchmarking, (d) system fonts legality, and (e) variable font axis inventory. CJK, Noto, Adobe commercial tiers, and Envato licensing are the principal remaining gaps for Chain D or subsequent rounds.

---
*Anderson — Chain C organized. 10 Smiths, 6 themes, 4 corrections, 3 disputes, 10 gaps. All unique signal preserved. Ready for Opus synthesis.*

============================================================
## Chain B — Anderson Report
============================================================

# Anderson Briefing — Chain B Organized Findings (Smiths #11–#20)
*Prepared for Opus synthesis. All unique signal preserved. Organized, not compressed.*

---

## PART I: STRUCTURED FINDINGS BY THEME

---

### THEME A: MOZILLA-COMMISSIONED FONTS
*Source: Smith #11 exclusively*

#### A.1 — Confirmed Mozilla-Commissioned Typefaces

| Font | Designers | Year Commissioned | Commissioned By | License | Confidence |
|---|---|---|---|---|---|
| Fira Sans | Erik Spiekermann, Ralph du Carrois, Anja Meiners, Botio Nikoltchev (Carrois Type Design), Patryk Adamczyk | 2013 | Mozilla & Telefónica (Firefox OS) | OFL 1.1 | HIGH — Mozilla Blog May 2014, primary source |
| Fira Mono | Same team as Fira Sans | 2013 | Mozilla (concurrent with Fira Sans) | OFL 1.1 | HIGH |
| Zilla Slab | Peter Biľak, Nikola Djurek (Typotheque) | 2016–2017 | Mozilla (rebranding initiative) | OFL 1.1 | MEDIUM on year (Wikipedia); HIGH on license (GitHub) |
| Mozilla Headline | Studio DRAMA | 2024 | Mozilla ("Reclaim the Internet" rebrand) | OFL 1.1 | HIGH — Adobe Fonts + GitHub |
| Mozilla Text | Studio DRAMA | 2024 | Mozilla (rebranding) | OFL 1.1 | HIGH — GitHub + Adobe Fonts |

**Mozilla Text → Google Fonts:** Added 2025. [MEDIUM — WebSearch result, not primary source]

#### A.2 — Explicitly NOT Mozilla-Commissioned (Important Clarifications)

| Font | True Origin | Note |
|---|---|---|
| **Fira Code** | Nikita Prokopov (@tonsky), independent | Extends Fira Mono; released 2016; OFL 1.1; repo: github.com/tonsky/FiraCode |
| **FiraGO** | bBox Type GmbH | Commissioned by **Here Technologies** (geographic data provider), 2016; multilingual extension of Fira Sans |

#### A.3 — Download Locations for Mozilla Fonts

| Font | Primary Download | Alternates |
|---|---|---|
| Fira Sans / Fira Mono | github.com/mozilla/Fira/tree/master/ttf; /releases/latest | Google Fonts, Font Squirrel, Adobe Fonts |
| Zilla Slab | github.com/mozilla/zilla-slab/releases/latest | Google Fonts (fonts.google.com/specimen/Zilla+Slab); Mozilla CDN CSS ref |
| Mozilla Headline | github.com/mozilla/mozilla-headline-type; /releases | Adobe Fonts, Font Squirrel |
| Mozilla Text | github.com/mozilla/mozilla-text-type; /releases | Adobe Fonts; Google Fonts (2025+) |

---

### THEME B: MAJOR OPEN-SOURCE FONT FAMILIES — STRUCTURE & METADATA

#### B.1 — IBM Plex Family
*Source: Smith #12 | Date: 2026-04-09 | Repo: github.com/IBM/plex*

**Package count:** 16 font packages [HIGH]

**Core families (3):**
- IBM Plex Sans — 8 weights × 2 styles (Roman + Italic) = 16 static TTFs
- IBM Plex Serif — same structure = 16 static TTFs
- IBM Plex Mono — same structure = 16 static TTFs

**Width variant (1):** IBM Plex Sans Condensed — 8 weights × 2 styles = 16 static TTFs

**Variable fonts (2):** IBM Plex Sans Variable; IBM Plex Serif Variable [HIGH]

**Specialized (1):** IBM Plex Math — 1 weight (Regular only), 5,000+ mathematical symbols [HIGH]

**Script-specific variants (9):**
- Arabic, Devanagari, Hebrew, Japanese (JP — hinted + unhinted variants), Korean (KR), Chinese Traditional (TC), Chinese Simplified (SC), Thai, Thai Looped

**Total TTF files (core 4 families):** 16 + 16 + 16 + 16 + 1 = 65 confirmed TTFs [HIGH]
**Script variant file counts:** ~8–12 each [MEDIUM — structure varies; Japanese has hinted/unhinted split]
**Estimated grand total (all formats × all packages):** ~1,200–1,500+ files [MEDIUM]

**Output formats per package:** TTF, OTF, WOFF, WOFF2, EOT (5 formats)

**Script coverage:** Extended Latin, Arabic, Chinese (Traditional + Simplified), Cyrillic, Devanagari, Greek, Hebrew, Japanese, Korean, Thai [HIGH]

**License:** SIL OFL 1.1. Copyright © 2017 IBM Corp. Reserved Font Name: "Plex" [HIGH]

**Repository metadata:** Created Oct 3, 2017; last updated Apr 9, 2026 (master branch pushed Feb 12, 2026); active monorepo using Lerna [HIGH]

**Download:**
- GitHub Releases: github.com/IBM/plex/releases
- NPM: @ibm/plex-sans, @ibm/plex-serif, @ibm/plex-mono, @ibm/plex-sans-arabic, @ibm/plex-sans-condensed, @ibm/plex-sans-devanagari, @ibm/plex-sans-hebrew, @ibm/plex-sans-jp, @ibm/plex-sans-kr, @ibm/plex-sans-tc, @ibm/plex-sans-sc, @ibm/plex-sans-thai, @ibm/plex-sans-thai-looped, @ibm/plex-math [HIGH — verified in README]
- Official site: ibm.com/plex/

⚠️ *Smith #12 flags: exact file counts for Arabic, Hebrew, Devanagari, etc. require per-package inspection. Variable font file formats not explicitly counted. "Complete" vs "split" subdirectories for web use have different file organizations.* [MEDIUM]

---

#### B.2 — Inter Font Family
*Source: Smith #13 | Last repo commit: Nov 19, 2024 | Repo: github.com/rsms/inter*

**Designer:** Rasmus Andersson. Released 2017. Neo-grotesque sans-serif, screen-optimized.

**Weights & styles:** 9 weights (Thin 100 → Black 900) × 2 styles (Roman + Italic) = **18 total static styles** [HIGH]

**License:** SIL OFL 1.1. Reserved Font Name: "Inter" (vendor code: RSMS). Permissive: free to use, modify, redistribute, embed, bundle. Not saleable standalone. [HIGH]

**Variable font:** YES [HIGH]
- Weight axis (wght): 100–900 continuous
- Optical Size axis (opsz): 14–32 [HIGH]
- Italic axis (ital): 0° or 9.4° [MEDIUM]
- Both static files AND variable files provided in releases.

**Screen-optimization features:**
- Tall x-height — improves readability of lowercase at small sizes [HIGH]
- Optical size axis — auto-adjusts glyphs for 14–32px; includes ink traps and bridges for <12px [HIGH]
- At <12px: horizontal/vertical stems rendered with two semi-opaque pixels instead of one solid, for higher-density displays [HIGH]
- OpenType features: contextual alternates, slashed zero, tabular numbers, case-sensitive punctuation, tabular figures [HIGH]

**Notable adopters:** Figma, Elementary OS, GitLab, Mozilla, NASA, ISO, Guggenheim, Zurich Airport, Unity [HIGH]

**Download:**
- Official: github.com/rsms/inter/releases/latest [HIGH]
- CDN: rsms.me/inter/inter.css [HIGH]
- NPM: inter-ui; Homebrew: font-inter; Ubuntu: fonts-inter [HIGH]
- ⚠️ Google Fonts version: README explicitly states it is **outdated and lacks italics**

---

#### B.3 — Recursive Font Family
*Source: Smith #14 | Date: 2026-04-09 | Repo: github.com/arrowtype/recursive*

**Designers:** Stephen Nixon (lead), Lisa Huang, Katja Schimmel, Rafał Buchner — Arrow Type. Originated as thesis project bridging programming and brush lettering.

**Classification:** Variable type family for code & UI, inspired by casual script signpainting.

**Variable axes: 5** [HIGH]

| Axis | Tag | Range | Default | Notes |
|---|---|---|---|---|
| Monospace | MONO | 0–1 | 0 | 0 = proportional (Sans), 1 = fixed-width (Mono) |
| Casual | CASL | 0–1 | 0 | 0 = linear/rationalized, 1 = signpainting-inspired |
| Weight | wght | 300–1000 | 300 | Light → ExtraBlack |
| Slant | slnt | 0 to −15 | 0 | Upright → ~15° slant |
| Cursive | CRSV | 0, 0.5, or 1 | 0.5 | Roman, auto, or always cursive |

**Key structural property:** "Superplexed" metrics — all styles (Sans and Mono) share identical horizontal spacing, enabling fluid transitions without text reflow [HIGH]

**Static instances: 64** [HIGH]
- Calculation confirmed: 2 subfamilies (Sans + Mono) × 2 styles (Linear + Casual) × 8 weights (Light 300 → ExtraBlack 1000) × 2 (Upright + Italic) = 64

**License:** SIL OFL 1.1 [HIGH]

**Language support:** Google Fonts Latin Expert + 100+ additional languages (Afrikaans, Chinese, Cyrillic variants, etc.)

**Download:**
- GitHub Releases: github.com/arrowtype/recursive/releases — latest v1.085
- Google Fonts: partial family
- Release zip includes: Variable fonts (Recursive_Desktop), Rec Mono with ligatures pre-applied (Recursive_Code), static OTF/TTF instances

**Tooling:** UFO sources, Python mastering scripts (open-source). Code editor setup docs for VS Code, Sublime Text, Atom.

---

#### B.4 — JetBrains Mono
*Source: Smith #15 | Repo: github.com/JetBrains/JetBrainsMono*

**Classification:** Professional monospace typeface for developers. 

**Weights & styles:** 8 weights (Thin 100, ExtraLight **250** ⚠️, Light 300, Regular 400, Medium 500, SemiBold 600, Bold 700, ExtraBold 800) × 2 styles (Roman + Italic) = **16 total static styles** [HIGH]

> ⚠️ **NOTE:** ExtraLight weight value is **250**, not 200 as is conventional in many other families. This is correct for JetBrains Mono specifically.

**Variable font:** YES [HIGH]

**Ligatures:** YES — **138 code-specific ligatures** [MEDIUM — derived from WebSearch, not directly verified]. Examples: `===`, `=>`, `->`, `-->`, `<==`, `<--`, `<->`. No-ligatures variant: **JetBrains Mono NL** [HIGH]

**License:** SIL OFL 1.1 [HIGH]. Permissive; free for commercial and non-commercial; derivative works allowed.

**Unicode/Language coverage:**
- Scripts: Latin, Greek (from v2.200), Cyrillic, APL symbols (v2.304), math operators
- **143 languages supported** [LOW — WebSearch claim, unverified against glyph database]
- Scope is code/programming domain; narrower than general-purpose fonts

**Download:**
- GitHub Releases: github.com/JetBrains/JetBrainsMono/releases/latest [HIGH]
- Google Fonts: fonts.google.com/specimen/JetBrains+Mono [HIGH]
- Homebrew: `brew install --cask font-jetbrains-mono` [MEDIUM]
- Linux: Arch: `ttf-jetbrains-mono`; Debian: `fonts-jetbrains-mono` [MEDIUM]
- Bundled in all JetBrains IDEs [HIGH]
- Full Glyphs source files + build scripts in repo [HIGH]

**ML training assessment (from Smith #15):**
- **Suitable as supplementary data** for code-focused font generation, monospace models, weight/width interpolation, Latin-script models
- **Not suitable as primary dataset** — limited scripts, narrower Unicode coverage, uniform design philosophy across weights reduces stylistic diversity

---

#### B.5 — Ubuntu Font Family
*Source: Smith #16 | Date: 2026-04-09 | Repo: github.com/google/fonts (UFL directory)*

**Family components: 5** (Ubuntu, Ubuntu Mono, Ubuntu Condensed, Ubuntu Sans, Ubuntu Sans Mono)

**File counts (Google Fonts repo, main branch):**

| Family | Font Files | Metadata Files | Total |
|---|---|---|---|
| Ubuntu | 8 | 11 | 19 |
| Ubuntu Condensed | 1 | 10 | 12 |
| Ubuntu Mono | 4 | 11 | 15 |
| Ubuntu Sans | 2 | 3 | 5 |
| Ubuntu Sans Mono | 2 | 3 | 5 |
| **TOTAL** | **17** | **38** | **56** |

**[HIGH confidence — direct inventory from Google Fonts repo, confirmed via SHA hashes]**

**Variable font note:** Ubuntu Sans and Ubuntu Sans Mono are variable fonts (weight + width axes for Sans; weight axis only for Sans Mono) [HIGH]

**Ubuntu Condensed:** Regular only — single weight [HIGH]

**License: UBUNTU FONT LICENCE (UFL) v1.0** — *NOT OFL* [HIGH]
- All 5 variants confirmed UFL exclusively (SHA: ae78a8f94eae372cb1ca4e14b67244342fce604e across all directories)
- UFL is a distinct license designed by Canonical specifically for Ubuntu fonts
- UFL created ~2010; predates modern ML concerns
- Full text: assets.ubuntu.com/v1/81e5605d-ubuntu-font-licence-1.0.txt

---

### THEME C: LICENSING — STRUCTURE & ML TRAINING IMPLICATIONS

*Sources: Smith #17 (OFL), Smith #18 (Apache 2.0), Smith #16 (UFL), Smith #19 (CC0), Smith #20 (Font Squirrel aggregation)*

#### C.1 — OFL 1.1 and ML Training
*Primary sources: Smith #17, corroborated by Smith #18 and #20*

**Three-way agreement (HIGH confidence):** Smiths #17, #18, and #20 all cite OFL-FAQ 1.25 (November 2023, update 7) consistently.

**Core rule:** Any font produced from ML systems whose input or training data contains any OFL-licensed source file **must be considered a derivative work** and must remain under OFL 1.1. [HIGH — OFL-FAQ 1.25, Nov 2023]

**Exact language (OFL-FAQ 1.25):**
> "Any font produced from such systems whose input or training data contains any source file from a font project licensed under the OFL should be considered a derivative work."

**OFL-FAQ 1.26 distinction:**
- **Font output from AI trained on OFL data = derivative work → must stay OFL** [HIGH]
- **Non-font graphical output from AI (designs, graphics) = normal usage → no restriction** [HIGH]

**Full OFL 1.1 permissions (unchanged since Feb 2007):** Use, study, copy, merge, embed, modify, redistribute, sell modified/unmodified copies. No attribution required for end-users (though appreciated). Can embed in commercial software bundles. [HIGH]

**OFL restrictions:**
- Cannot sell standalone font files
- Cannot use Reserved Font Names without permission
- Cannot redistribute under different licenses
- Derivative works must remain OFL (and this now explicitly covers ML-trained font outputs)

**Permission override:** Different license for ML-output font requires **explicit written consent from original authors** [HIGH — OFL 1.1 § 3]

#### C.2 — Apache 2.0 and ML Training
*Source: Smith #18, corroborated by Smith #20*

**Apache 2.0 permits ML font training with zero output constraints.** [HIGH — Apache Foundation official text]
- Grants unrestricted "Derivative Works" rights: reproduce, prepare derivatives, publicly display/perform, sublicense, distribute
- No copyleft clause — trained fonts can be released under any license (proprietary, MIT, OFL, etc.)
- Apache 2.0 text (2004) does not mention training data explicitly, but permissive "sublicense and distribute" language covers ML uses [HIGH]

**Attribution requirements for Apache 2.0 fonts:**
1. Include license copy when redistributing font files
2. If original includes NOTICE file: reproduce relevant notices in derivative works (in NOTICE file, source docs, or display output)
3. Mark modified files with prominent notices
4. No visible credit required in finished products unless NOTICE file specifies [HIGH — Apache License v2.0 Section 4]

#### C.3 — OFL vs Apache 2.0 Comparison for ML
*Source: Smith #18 (primary), confirmed by Smith #20*

| Aspect | Apache 2.0 | OFL 1.1 |
|---|---|---|
| ML Training Use | **Permitted** — permissive language | **Restricted** — output font = derivative work |
| Output Font License | **Freedom** — any license | **Mandatory OFL** |
| AI Design Tools (non-font output) | Unrestricted | Permitted (OFL FAQ 1.26) |
| Copyleft | **None** | **Weak copyleft** (fonts only) |
| Attribution | License copy + NOTICE file (if exists) | Copyright notice + license + OFL copy |

#### C.4 — Ubuntu Font Licence (UFL) and ML Training
*Source: Smith #16*

**ML training status: UNCLEAR** — UFL does not explicitly address ML training or model extraction. [HIGH that UFL is silent; LOW confidence on whether training is permitted]

**Key details:**
- UFL defines "Propagate" narrowly (copying, distribution, making available); ML training not mentioned
- No explicit prohibition — but absence of permission ≠ implicit permission under copyright law
- UFL FAQ covers: redistribution, embedding, derivative modifications, trademark — not ML [HIGH]
- UFL created ~2010; modern ML concerns postdate the license
- Smith #16 recommendation: Contact Canonical Legal directly

#### C.5 — CC0 / Public Domain
*Source: Smith #19*

**CC0 v1.0:** No rights reserved. No attribution required. No restrictions on any use including ML training. [Implied HIGH — CC0 is well-established]

---

### THEME D: PUBLIC DOMAIN & CC0 FONT COLLECTIONS

*Source: Smith #19 exclusively*

#### D.1 — Verified CC0/Public Domain Repositories

| Repository | Fonts | Source Date | Confidence |
|---|---|---|---|
| Typodermic Fonts | 729 fonts (306 typefaces) | Apr 2024 | HIGH |
| FontSpace (CC0 + PD collection) | 409 fonts | Mar 2026 | HIGH |
| OpenGameArt.org | 100+ fonts | Current | MEDIUM |
| GGBotNet CC0 Pack | 45 fonts | Current | HIGH |
| Font Library (CC-0 only filter) | 10 fonts | Current | HIGH |
| itch.io CC0 Collection | Various (curated) | Current | MEDIUM |

**Aggregate total across major repositories:** 1,283+ fonts [MEDIUM — OpenGameArt count approximate]

**Largest single source:** Typodermic (729) | Apr 2024 update
**Most current aggregate source:** FontSpace (409) | Mar 2026

#### D.2 — Download Details

**Typodermic (729 fonts):** typodermicfonts.com/public-domain/ — OTF, WOFF2, FontLab source; CC0 v1.0

**FontSpace (409 fonts):** fontspace.com/collection/public-domain-and-cc0-fonts-c3p38ee — per-font downloads with preview; all "100% Free" + commercial use

**GGBotNet (45 fonts):** ggbot.itch.io/ggbotnet-fonts-cc0 — single zip; TTF, OTF, WOFF, WOFF2; CC0 v1.0 Universal

**OpenGameArt (100+):** opengameart.org/content/cc0-public-domain-fonts-0 — browse + individual downloads; mixed styles (bitmap, pixel, serif, display, handwritten)

**Font Library (10 fonts):** fontlibrary.org/en/search?license=CC-0&order= — web-embeddable + downloadable

**FishlandicFishy GitHub:** github.com/FishlandicFishy/public-domain-fonts — curated list with licensing validation; emphasis on CJK; exact count not published [HIGH on curation quality]

#### D.3 — Critical Distinctions (Smith #19 Warnings)

⚠️ **Google Fonts are NOT CC0/public domain.** Licensed under OFL 1.1 or Apache 2.0. Retain some attribution requirements. Not equivalent to CC0. [HIGH — Smith #19, corroborated by Smith #20]

⚠️ **Wikimedia Commons "16,580 public domain images of fonts"** — These are scanned images/samples of historic typefaces, NOT downloadable font files.

⚠️ **FontAwesome** — MIT licensed (not CC0); includes CC0-depicting icons but is not itself CC0.

---

### THEME E: FONT AGGREGATORS / REPOSITORIES

#### E.1 — Font Squirrel
*Source: Smith #20 | Date: Apr 2026 (current, except API docs from 2010)*

**Purpose:** Hand-picked, free, high-quality fonts with legitimate commercial-use licenses. Curation over quantity.

**Font count:** ~400 font families [HIGH, multiple citations] OR ~1,275 web fonts [MEDIUM — may count individual weights/styles separately]
⚠️ Discrepancy = families vs. individual font files. Official site does not publish exact current count (2026).

**License types present:**
- SIL OFL (most common)
- Apache 2.0
- Font Squirrel proprietary license indicators:
  - Z = Commercial Desktop Use
  - Y = @font-face Embedding (webfonts)
  - M = Ebooks/PDFs
  - m = Applications

**ML Training:** NOT permitted for OFL fonts (same rule as Theme C.1 above). Apache 2.0 fonts on the platform: permitted with no output constraints.

**Bulk download:** No official bulk download feature (redistribution restrictions on some fonts)

**API (2010):**
- `GET /api/fontlist/all` — list all families
- `GET /api/familyinfo/{family_urlname}` — font details (glyph count, formats)
- `GET /fontfacekit/{family_urlname}` — download kit (TTF/WOFF/SVG/EOT)
- ⚠️ **OUTDATED — documented 2010; current functionality unverified**

**Third-party tools:**
- Python: github.com/vfrico/fontsquirrel_dl (unofficial scraper)
- WordPress: github.com/1nterval/wp-fontsquirrel

**Font Squirrel vs. Google Fonts:**

| Aspect | Font Squirrel | Google Fonts |
|---|---|---|
| Size | ~400 families (curated) | ~1,000+ families (Apr 2026: 1,929 confirmed by Smith #19) |
| Curation philosophy | "We don't have the most, but we do have the best" | Algorithmic, quantity-focused |
| Commercial use | Most fonts free for commercial | All open-source |
| Integration | Download + manual setup | Simple `@import`/`<link>`; CDN-optimized |
| Licensing | Mixed (OFL, Apache, proprietary) | Consistent (OFL/Apache) |
| Tooling | Webfont Generator, Matcherator | Browser integration |

---

### THEME F: VARIABLE FONT SUPPORT ACROSS REVIEWED FAMILIES

*Cross-referenced from Smiths #12–#16*

| Font | Variable? | Axes | Confidence |
|---|---|---|---|
| IBM Plex Sans | YES (Sans Variable + Serif Variable packages) | Weight | HIGH |
| IBM Plex Serif | YES (Serif Variable package) | Weight | HIGH |
| IBM Plex Mono | Not confirmed as variable | — | Not stated |
| Inter | YES | wght (100–900), opsz (14–32), ital (0/9.4°) | HIGH |
| Recursive | YES — 5 axes | MONO, CASL, wght, slnt, CRSV | HIGH |
| JetBrains Mono | YES | Not specified | HIGH |
| Ubuntu Sans | YES (variable format) | Weight + Width | HIGH |
| Ubuntu Sans Mono | YES (variable format) | Weight only | HIGH |
| Ubuntu (core) | Not confirmed as variable | — | Not stated |
| Fira Sans | Not covered in Smith #11 | — | Gap |

---

## PART II: CORRECTIONS

**CORRECTION 1 — JetBrains Mono ExtraLight weight value**
Smith #15 correctly notes ExtraLight is weight **250**, not the conventional 200. This is intentional JetBrains design choice. No error — flagged for Opus awareness since it deviates from CSS/OpenType conventions.

**CORRECTION 2 — Ubuntu fonts are NOT OFL**
Smiths #17 and #18 discuss OFL at length. Smiths #11–#15 all use OFL. Smith #16 correctly identifies Ubuntu as **UFL**, not OFL. Risk of cross-contamination: if any downstream analysis groups Ubuntu with OFL fonts for ML training purposes, that is incorrect. The ML training implications are categorically different (OFL = clear derivative rule; UFL = silent/unclear).

**CORRECTION 3 — Google Fonts count (minor)**
Smith #20 states Google Fonts has "~1,000+ families." Smith #19 provides a more precise figure: **1,929 font families (Apr 2026)** [HIGH confidence]. Use 1,929 as current figure.

**CORRECTION 4 — Font Squirrel OFL citation accuracy**
Smith #20 quotes OFL restriction for ML training. The citation is accurate (OFL-FAQ 1.25), and consistent with Smiths #17 and #18.

---

## PART III: DISPUTES

**DISPUTE 1 — OFL ML training: "restricted" vs. "prohibited" framing**
- Smith #17: Frames it as "NO — with restrictions on output" — implies training is permitted if output stays OFL.
- Smith #18: Frames it as "Restricted" in comparison table.
- Smith #20: Frames it as "NOT PERMITTED" (for ML training broadly).
- **Assessment:** This is a framing dispute, not a factual one. The underlying OFL-FAQ 1.25 text is consistent across all three. Smith #20's "NOT PERMITTED" language is slightly misleading — training itself is not prohibited; what is restricted is the output license of any resulting font. **Opus should clarify framing for end-readers.**

**DISPUTE 2 — Font Squirrel family count**
- Smith #20 gives two figures: ~400 families [HIGH] and ~1,275 web fonts [MEDIUM].
- Smith #20 itself acknowledges this is a families-vs-files discrepancy, not conflicting data.
- **Assessment:** Not a genuine dispute. Both figures may be correct at different levels of granularity. Smith #20 flags it explicitly.

**DISPUTE 3 — Inter on Google Fonts (staleness)**
- Smith #13 states the Google Fonts version of Inter is **outdated and lacks italics** (per Inter's own README).
- No other Smith addresses this.
- **Assessment:** This is a temporal issue, not a Smith-vs-Smith conflict. The README statement dates to Nov 2024 (last commit). If Google Fonts has since updated Inter, this may be stale. Flagged as a verification gap.

---

## PART IV: GAPS — UNCOVERED TOPICS

**G1 — No Noto coverage.** Google's Noto font project (designed for universal script coverage, ~150+ scripts) is entirely absent from Chain B. Critical for multilingual training data context.

**G2 — No Source fonts coverage.** Adobe's Source Sans, Source Serif, Source Code Pro (Apache 2.0; major open-source family) not covered.

**G3 — No MIT-licensed fonts.** MIT license implications for ML training not analyzed. Several significant fonts use MIT (e.g., FontAwesome, some icon fonts).

**G4 — No Creative Commons BY / BY-SA font analysis.** CC-BY and CC-BY-SA licensing for fonts and ML training not addressed.

**G5 — Font Squirrel API current status unverified.** API documentation dates to 2010. Smith #20 flags this explicitly but does not verify current functionality. No Smith tested the endpoints.

**G6 — IBM Plex script variant file counts unverified.** Smith #12 provides ~8–12 estimate per script variant. Exact counts for Arabic, Hebrew, Devanagari, JP (hinted vs. unhinted), KR, TC, SC, Thai, Thai Looped not directly confirmed. [MEDIUM]

**G7 — Inter Google Fonts staleness unverified.** Inter README (Nov 2024) says GF version lacks italics and is outdated. No Smith checked current Google Fonts Inter state as of 2026-04-09.

**G8 — JetBrains Mono ligature count unverified.** "138 ligatures" is LOW confidence per Smith #15 (derived from WebSearch). Not directly counted from OT feature tables or repo.

**G9 — JetBrains Mono "143 languages" claim unverified.** Smith #15 explicitly rates this LOW confidence. Not verified against glyph database.

**G10 — UFL legal opinion gap.** Smith #16 flags that ML training use of Ubuntu fonts (UFL) is legally unclear and recommends contacting Canonical Legal. No resolution in Chain B.

**G11 — No coverage of Monaspace or other recent monospace families.** GitHub's Monaspace (2022), Cascadia Code (Microsoft), or Commit Mono not covered.

**G12 — No font file size data.** Relevant for training data storage, bandwidth, and dataset composition planning. No Smith covers file sizes for any family.

**G13 — No coverage of variable font axis registries.** OpenType registered axes vs. custom axes (MONO, CASL, CRSV in Recursive are custom) not analyzed at the standard level.

**G14 — Zilla Slab commissioning year uncertainty.** Smith #11 gives "2016–2017" with MEDIUM confidence (Wikipedia source). No primary Typotheque or Mozilla source confirmed for commissioning year.

**G15 — Mozilla Text Google Fonts addition year.** Smith #11 states Mozilla Text added to Google Fonts in 2025 [MEDIUM — WebSearch only]. Not confirmed against Google Fonts changelog.

**G16 — No Recursive OpenType feature inventory.** Smith #14 mentions "multiple stylistic sets, ligatures, alternate forms" but does not enumerate specific OT features as thoroughly as Inter (Smith #13) or JetBrains Mono (Smith #15).

---

## PART V: QUICK-REFERENCE SUMMARY TABLE

| Font | Designer/Org | Year | License | Variable? | Weights | ML Training (font output) |
|---|---|---|---|---|---|---|
| Fira Sans | Carrois / Mozilla | 2013 | OFL 1.1 | — | Not specified | OFL derivative rule applies |
| Fira Mono | Carrois / Mozilla | 2013 | OFL 1.1 | — | Not specified | OFL derivative rule applies |
| Zilla Slab | Typotheque / Mozilla | 2016–17 | OFL 1.1 | — | Not specified | OFL derivative rule applies |
| Mozilla Headline | Studio DRAMA / Mozilla | 2024 | OFL 1.1 | — | Not specified | OFL derivative rule applies |
| Mozilla Text | Studio DRAMA / Mozilla | 2024 | OFL 1.1 | — | Not specified | OFL derivative rule applies |
| IBM Plex (core) | IBM | 2017 | OFL 1.1 | Partial (Sans, Serif) | 8 | OFL derivative rule applies |
| Inter | Rasmus Andersson | 2017 | OFL 1.1 | YES (3 axes) | 9 | OFL derivative rule applies |
| Recursive | Arrow Type | — | OFL 1.1 | YES (5 axes) | 8 | OFL derivative rule applies |
| JetBrains Mono | JetBrains | — | OFL 1.1 | YES | 8 | OFL derivative rule applies |
| Ubuntu family | Canonical | ~2010 | **UFL 1.0** | Partial (Sans, Sans Mono) | Varies | **UNCLEAR — legal opinion needed** |
| Fira Code | Nikita Prokopov | 2016 | OFL 1.1 | — | Not specified | OFL derivative rule applies |
| FiraGO | bBox Type / Here Tech | 2016 | — | — | Not specified | Not covered |
| Typodermic (729) | Various | Apr 2024 | **CC0** | — | — | **Unrestricted** |
| FontSpace CC0 (409) | Various | Mar 2026 | **CC0/PD** | — | — | **Unrestricted** |

---

*End of Anderson Chain B Briefing — 10 Smiths (#11–#20) organized. All unique signal preserved. Ready for Opus synthesis.*

============================================================
## Chain A — Anderson Report
============================================================

# CHAIN A — STRUCTURED FINDINGS FOR OPUS SYNTHESIS
**Organized by Anderson | 10 Smiths | April 9, 2026**
**Triage applied: DEDUP · RECENCY · AGREE · DISAGREE · GAPS · CORRECT**

---

## ═══ SECTION 1: GOOGLE FONTS — CATALOG SIZE & GROWTH ═══

### 1.1 Total Family Count (DISPUTE — see note)

| Figure | Source Smith | Date of Data | Confidence |
|--------|-------------|--------------|------------|
| **1,929 families** | Smith #1 | April 2026 | HIGH |
| **1,911 fonts** | Smith #2 | 2026 (unspecified month) | HIGH |
| **1,382 families** | Smith #5 | December 2023 | HIGH (but stale — see CORRECTIONS) |

**RECENCY WINNER:** Smith #1 (1,929, April 2026) is the most precisely dated 2026 figure.

**⚠️ GENUINE DISPUTE — Smith #1 vs Smith #2:** Both claim 2026 data. 1,929 (Smith #1) vs 1,911 (Smith #2) is an 18-family gap. This is *not* a stale-vs-fresh conflict — both are 2026 figures from different sources. Possible explanations: different snapshot dates within 2026, different counting methodology (e.g., whether draft/beta families are included), or source disagreement. Opus should flag for resolution.

**Historical growth trajectory (Smith #1, HIGH confidence):**
- End of 2024: 1,790 families
- May 2025: 1,826 families
- April 2026: 1,929 families
- Growth rate: ~139 families added in ~16 months (≈ 8.7/month)

### 1.2 Variable Font Subfamilies

- **543 variable font families** as of April 2026 = **28% of total** | Smith #1 | HIGH confidence
- **468 variable font families** as of May 2025 | Smith #1 (citing Photutorial) | HIGH confidence
- Growth: +75 variable families in ~11 months (May 2025 → April 2026)
- Smith #2 does not address variable fonts specifically — no conflict, gap in that report

### 1.3 Total Individual Font Files (TTF/OTF)

- **NOT FOUND** — no aggregate published count | Smith #1 | confirmed gap
- Partial data points (Smith #1):
  - 1,128 TTF files with "Regular" in filename (partial study only)
  - 1,074 TTF files meeting specific character set criteria (subset only)
  - Repository total: >1GB download size per GitHub README
- **Note from Smith #1:** Exact count would require programmatic enumeration of `/ofl`, `/apache`, and `/ufl` directories in google/fonts GitHub repo

---

## ═══ SECTION 2: GOOGLE FONTS — CATEGORY DISTRIBUTION ═══

### 2.1 Category Breakdown (Smith #2, HIGH confidence, 2025–2026 data)

*Basis: 1,911 total (Smith #2's figure — note dispute with 1,929 in Section 1.1)*

| Category | Count | Percentage | Notes |
|----------|-------|------------|-------|
| **Sans-serif** | 705 | 36.9% | Heavily dominant |
| **Display** | 464 | 24.3% | Large secondary category |
| **Handwriting** | 348 | 18.2% | High quantity, low utility |
| **Serif** | 343 | 17.9% | Underrepresented vs. sans-serif |
| **Monospace** | 51 | **2.7%** | Most severely underrepresented |

Sources: Google Fonts Directory 2026 (serbyte.net/fonts), Kinsta, Lexington Themes 2026 | Smith #2

### 2.2 Font Library (fontlibrary.org) Category Breakdown (Smith #3, HIGH confidence, 2026)

*Provided for comparison — different catalog*

| Category | Count |
|----------|-------|
| Sans-serif | 435 |
| Serif | 427 |
| Display | 219 |
| Handwriting | 125 |
| Monospaced | 103 |
| Dingbat | 53 |
| Blackletter | 37 |

**Cross-Smith observation (Anderson):** Font Library has a far more balanced sans/serif ratio (435 vs 427 = 1.02:1) compared to Google Fonts (705 vs 343 = 2.06:1). Monospace is also better represented on Font Library proportionally (103/1,399 = 7.4%) vs Google Fonts (51/1,911 = 2.7%).

---

## ═══ SECTION 3: GOOGLE FONTS — LICENSE BREAKDOWN ═══

### 3.1 License Types Present (Smith #1, MEDIUM confidence — no exact counts published)

| License | Status | Notes |
|---------|--------|-------|
| **OFL (SIL Open Font License v1.1)** | "Overwhelming majority" | Google Fonts README: "Most of the fonts… use the SIL Open Font License" |
| **Apache 2.0** | "Smaller number" | Examples: Roboto family and variants |
| **UFL (Ubuntu Font License)** | Present — legacy | Confirmed in `/ufl` directory; count unknown |

**Policy note (Smith #1):** Only OFL accepted for *new* submissions in recent years. Apache and UFL are legacy licenses. Exact counts by license type are not exposed in the public API and are not stated in any source found.

**Gap flagged (Smith #1):** License breakdown by exact count is proprietary/unstated data.

---

## ═══ SECTION 4: GOOGLE FONTS — QUALITY & GAP ANALYSIS ═══

### 4.1 Identified Gaps by Category (Smith #2)

**Monospace — Most Critical Gap** | HIGH confidence | 2025–2026
- 2.7% of library vs. industry demand for development tools
- Lacks box drawing characters (U+2500–257F) for terminal/code use
- Incomplete glyph coverage for special characters
- Limited weight options in many monospace fonts
- Interface challenges for browsing monospace specifically
- Sources: GitHub Discussion MkDocs Material #7449; Google Fonts Knowledge glossary

**Serif — Secondary Gap** | HIGH confidence | 2025–2026
- 343 fonts vs. 705 sans-serif = **2.06:1 ratio** (sans dominance)
- Reflects web design trends but limits typographic diversity
- Recent improvement: Google funded high-quality serifs (Spectral, Noto Serif) with optical size axes and expanded language coverage (2022–2024)
- Still lags foundry depth for niche serif styles
- Sources: Design by Reese, FontFYI 2026

**Handwriting — Utility Gap** | MEDIUM confidence | 2024–2026
- 348 fonts but severely limited practical use
- Issue: high-quality handwriting fonts are rare; most in library are low-quality
- Constraint: best used only as display accents, not body text
- Cannot pair with other handwriting fonts (creates visual noise)
- Sources: Design Shack, Design by Reese

### 4.2 Quality Issues Beyond Category Count (Smith #2)

| Issue | Confidence |
|-------|------------|
| Character completeness: missing special symbols, box drawing, accents (widely noted in monospace & serif) | HIGH |
| Weight parity: some fonts available in only 1 weight, limiting design flexibility | MEDIUM |
| Glyph density: display fonts with high contrast often unusable below 30px | MEDIUM |
| Ubiquity problem: designers default to same 5–10 safe fonts despite 1,900+ options | MEDIUM |

Source for ubiquity problem: Monotype comparison results (saashub.com) | Smith #2

---

## ═══ SECTION 5: COMMERCIAL COMPARISON ═══

(Smith #2, HIGH confidence, 2024–2026)

| Provider | Font Count | Source Date |
|----------|-----------|-------------|
| **Google Fonts** | ~1,911–1,929 | 2026 |
| **Adobe Fonts (Typekit)** | ~30,000 | November 2024 |
| **Linotype/Monotype** | ~150,000 (from 1,000+ foundries) | 2026 |

**Coverage ratios (Google Fonts = 1.0x baseline):**
- Adobe = 15.7× Google Fonts
- Monotype = 78.5× Google Fonts

**Smith #2 framing:** "Google Fonts' breadth advantage (free, 1,900+ fonts) trades depth against specialty foundries (10,000–150,000 fonts with niche variants)."

---

## ═══ SECTION 6: FONT LIBRARY (fontlibrary.org) ═══

### 6.1 Identity & History (Smith #3, HIGH confidence)
- Free, open-source font repository and **501(c)3 nonprofit**
- Founded 2006 by Jon Phillips & Alexandre Prokoudine as "Open Font Library"
- Relaunched 2011
- 2024 tagline/rebranding: "FONTLIBRARY — Free Fonts Forever"
- Sister project to Openclipart
- **771 contributors** (fontlibrary.org direct count, 2026 | MEDIUM confidence)

### 6.2 Font Count (Smith #3 — INTERNAL CONFLICT flagged)

| Figure | Type | Source | Confidence | Date |
|--------|------|--------|------------|------|
| **2,172** | Uploaded font families | fontlibrary.org WebFetch | MEDIUM | 2026 |
| **29,776** | Uploaded font files | fontlibrary.org WebFetch | MEDIUM | 2026 |
| **6,000+** | Total fonts | Wikipedia + multiple | MEDIUM | ~2023–2024 |

**RECENCY + DISAGREE:** The 6,000+ figure from Wikipedia (~2023–2024) conflicts with the 2,172 families from direct site fetch (2026). Smith #3 explains this as counting methodology (families vs files). Anderson note: 6,000+ likely counted individual font files or included legacy/de-duplicated entries. Prefer 2,172 families as current-state (2026) for family count; 29,776 for file count.

### 6.3 License Breakdown (Smith #3, HIGH confidence — direct site search)

| License | Count |
|---------|-------|
| OFL (SIL Open Font License) | 927 |
| GNU General Public License | 138 |
| MIT (X11) License | 48 |
| Freeware | 47 |
| CC-BY | 39 |
| Apache 2.0 | 30 |
| Public Domain | 25 |
| Bitstream Vera License | 25 |
| CC-BY-SA | 22 |
| Other (Arphic, M+, GUST, Aladdin, etc.) | ~55 |
| **TOTAL classified** | **~1,356** |

**OFL dominance: ~68% of classified fonts.** All fonts are free to use, study, modify, redistribute, embed, subset, and derive from.

### 6.4 File Formats (Smith #3)

| Format | Status | Confidence |
|--------|--------|------------|
| TTF | Confirmed (gist analysis of fontlibrary.org data) | HIGH |
| OTF | Confirmed (gist analysis) | HIGH |
| WOFF | Mentioned in site description but NOT directly verified in download options | LOW |
| WOFF2 | **Not found** — gap confirmed | — |
| .dfont | Rare — detected in gist analysis | MEDIUM |

### 6.5 Bulk Download / ML Training (Smith #3)

- ✗ No official bulk download API documented
- ✗ No official "export all fonts" feature published
- ✓ Community tool: GitHub gist "fontlibrary.org fonts tables" (Python script, fontTools-based scraping + analysis)
- ✓ All fonts free/open-licensed → **legally downloadable for ML training**
- ✗ Scraping required for bulk automation
- **May 2024:** Font Library announced "strategy for how to work with artificial intelligence technology and fonts" — specific bulk-download policy not yet public (Smith #3)

### 6.6 Technical Status (Smith #3)
- 2024 development: Platform rebuild in Docker; modernization of legacy Aiki framework
- Multilingual support: Arabic, Cyrillic, Thai, and other scripts confirmed

---

## ═══ SECTION 7: ADOBE ORIGINALS OPEN SOURCE FONTS ═══

### 7.1 Full Catalog (Smith #4, HIGH confidence unless noted)

**All Adobe Originals open source fonts use SIL OFL 1.1** — AGREE across Smith #4 and confirmed via GitHub LICENSE.md citations.

---

**Source Sans 3** (formerly Source Sans Pro)
- Designer: Paul D. Hunt
- First released: 2012
- Latest version: 3.52.0 (~January 2026) | MEDIUM confidence
- Formats: TTF, OTF, VF (Variable), WOFF, WOFF2
- Available: GitHub releases, Google Fonts, Adobe Fonts

**Source Code Pro**
- Designer: Paul D. Hunt
- Latest version: 2.42.0 (~February 2026) | MEDIUM confidence
- Formats: OTF, TTF, Variable fonts, WOFF, WOFF2
- Available: GitHub releases, SourceForge mirror, Adobe Fonts

**Source Serif 4** (formerly Source Serif Pro)
- Designer: Frank Grießhammer
- Version 4 released: January 2021
- Weights: 6 weights across 5 optical sizes (Caption, SmallText, Text, Subhead, Display), Roman and Italic
- Formats: TTF, OTF, VAR (Variable), WOFF, WOFF2
- Available: GitHub releases, Adobe Fonts

**Source Han Sans** (Pan-CJK)
- Collaboration: Adobe + Google + Monotype + Sandoll Communications (Korea) + Iwata Corporation (Japan) + Changzhou SinoType (China)
- Latest version: 2.005R
- License note: Upgraded from Apache 2.0 to OFL at v1.002
- Languages: Simplified Chinese, Traditional Chinese, Japanese, Korean, Latin
- Formats: OTF, OTC, Super OTC, Variable formats
- Available: GitHub releases, SourceForge mirror, Adobe Fonts

**Source Han Serif** (Pan-CJK)
- Collaboration: Adobe + Google + partner foundries (same as Source Han Sans)
- Features: 7 weights, **65,535 glyphs per font**, 4 East Asian languages (Simplified Chinese, Traditional Chinese, Japanese, Korean)
- Formats: GitHub releases
- Available: GitHub releases, Adobe Fonts (per-language variants)

### 7.2 Key Download Notes (Smith #4)

- All Adobe Originals fonts available from GitHub releases in both TTF and OTF
- Primary: GitHub; convenience mirrors: Google Fonts (Source Sans 3), Adobe Fonts, SourceForge
- Paul D. Hunt designed Source Pro family (Sans, Code Pro) — HIGH confidence

### 7.3 Scope Clarification (Smith #4)

- **Noto fonts (Google/Monotype) are NOT Adobe Originals** — while Adobe collaborates on CJK variants, Noto is a Google/Monotype project [Note: Smith #4 was truncated here; Opus should note incomplete text]

---

## ═══ SECTION 8: GITHUB FONT REPOSITORIES ═══

### 8.1 Major Collections (500+ Stars) (Smith #5, HIGH confidence — April 2026)

| Repository | Stars | Font Count | License | Notes |
|------------|-------|-----------|---------|-------|
| **google/fonts** | 18,400 | 1,382 families* | OFL/Apache | *Dec 2023 count — stale; see CORRECTIONS |
| **ryanoasis/nerd-fonts** | 62,226 | 50+ patched | OFL | Patcher/aggregator, not pure font families |
| **powerline/fonts** | 26,200 | 50+ fonts | OFL/Apache | Specialized for statusline plugins |
| **adobe-fonts/source-code-pro** | 20,386 | 1 family | OFL-1.1 | |
| **source-foundry/Hack** | 16,900–17,200 | 1 family | OFL | |
| **adobe-fonts/source-sans** | 3,600 | 1 family | OFL-1.1 | |

*Star counts: HIGH confidence (direct GitHub API/authoritative source, April 2026)*
*Font counts: MEDIUM for powerline/fonts (50+ estimated, not explicitly counted)*

### 8.2 Near-Threshold / Notable Collections (Smith #5)

- **fontsource/font-files** — 405 stars (95 below 500-star threshold), 2000+ fonts, OFL/Apache | LOW confidence on star count
  - **Largest collection by count** among repos surveyed, despite being sub-threshold

### 8.3 Repository Notes (Smith #5)

- **googlefonts/roboto-2** archived April 1, 2025 (3.8k stars before archive)
- **ryanoasis/nerd-fonts** leads by stars (62.2k) but is a patcher/aggregator — should not be conflated with original font repositories
- Adobe Source fonts: 3 repos total ~26.3k stars combined (Code Pro + Sans + Serif)

---

## ═══ SECTION 9: FONTSOURCE ═══

### 9.1 What Is Fontsource (Smith #6, HIGH confidence)

- Monorepo providing **1,500+ self-hostable open-source fonts** bundled as individual NPM packages
- Includes Google Fonts but **not limited to them**
- Maintains separate `google-font-metadata` repo that fetches and parses the Google Fonts API to auto-sync
- Explicitly supports non-Google fonts: `"Support for fonts outside the Google Font ecosystem. This repository is constantly evolving with other Open Source fonts."`

### 9.2 Non-Google Font Examples (Smith #6, HIGH confidence — from API)

Fonts marked `type: "other"` in API (sample):
- Aileron (CC0-1.0)
- Apfel Grotezk (OFL-1.1)
- Argentum Sans (OFL-1.1)
- Bagnard & Bagnard Sans (OFL-1.1)
- Bluu Next (OFL-1.1)
- Clear Sans (Apache-2.0)
- Commit Mono (OFL-1.1)
- Cooper Hewitt (OFL-1.1)

### 9.3 Font Count (Smith #6 — INTERNAL CONFLICT noted)

| Source | Count | Confidence |
|--------|-------|------------|
| Official docs / README | 1,500+ | HIGH |
| Website (fontsource.org, ~April 2026) | 2,077 font families | MEDIUM |
| API response sample | 1,000+ (truncated/paginated) | MEDIUM |

**Smith #6 explanation:** Variation reflects different counting methods (families vs. variants) or update frequency differences. Authoritative current count: query `https://api.fontsource.org/v1/fonts`.

**Cross-Smith note (Anderson):** Smith #5 cites fontsource/font-files at 2,000+ fonts; Smith #6 cites 1,500+ (README) and 2,077 (website). These are broadly consistent — both point to a 2,000-range figure.

### 9.4 Programmatic Download of TTF/OTF (Smith #6, HIGH confidence)

Three access methods:

1. **NPM packages:** `npm install @fontsource/[font-id]` → files in `node_modules/@fontsource/[font-id]/files/`
2. **TTF via API:** Available since February 5, 2022 (PR #401, resolving issue #371)
3. **jsDelivr CDN:**
   - Static: `https://cdn.jsdelivr.net/fontsource/fonts/{id}@{version}/{subset}-{weight}-{style}.{extension}`
   - Variable: `https://cdn.jsdelivr.net/fontsource/fonts/{id}:vf@{version}/{subset}-{axes}-{style}.woff2`

**Formats confirmed available:** WOFF, WOFF2, TTF (HIGH confidence)
**OTF status:** Unclear from documentation — issue #371 resolved TTF specifically, not OTF explicitly (Smith #6)

---

## ═══ SECTION 10: SIL INTERNATIONAL FONTS ═══

### 10.1 Latin-Primary Font Families (Smith #7, HIGH confidence — official SIL pages, April–August 2025)

| Font | Script Coverage | Latin Detail | Version | Release Date |
|------|----------------|--------------|---------|--------------|
| **Charis SIL** | Latin, Cyrillic, Greek | Complete Latin Extended-A/B, 3,900+ glyphs | 7.000 | June 2, 2025 |
| **Doulos SIL** | Latin, Cyrillic | Complete Latin Extended, IPA phonetic symbols | 7.000 | June 2, 2025 |
| **Gentium** | Latin, Cyrillic, Greek | Latin Extended-A/B + diacritics, 4,600+ glyphs | 7.000 | June 3, 2025 |
| **Andika** | Latin, Cyrillic | Latin Extended + literacy variants, sans-serif | 7.000 | June 2025 |
| **Galatia SIL** | Greek (primary), Latin | Latin-1 + Extended-A/B (minimal: 5+1 chars) | 1.1 | 2004 |

**Character set details (HIGH confidence from SIL docs):**
- Basic Latin: U+0020–U+007F (94 chars)
- Latin-1 Supplement: U+00A0–U+00FF (95 chars)
- Latin Extended-A: U+0100–U+017F (128 chars)
- Latin Extended-B: U+0180–U+024F (208 chars)
- IPA Extensions: U+0250–U+02AD (supported in Doulos, Charis)

### 10.2 Arabic Script Fonts (Smith #7, HIGH confidence)

Latin coverage note (HIGH confidence, SIL official): Arabic fonts include "basic Latin repertoire as a convenience, e.g., for use in menus or displaying markup in text files; these fonts are not intended for extensive Latin script use."

| Font | Style | Version | Release |
|------|-------|---------|---------|
| **Scheherazade New** | Naskh | 4.400 | Aug 2025 |
| **Harmattan** | Warsh (Ajami) | 4.400 | Aug 2025 |
| **Lateef** | Sindhi style | current | — |
| **Alkalami** | Rubutun Kano | current | — |
| **Ruwudu** | Rubutun Kano | current | — |
| **Awami Nastaliq** | Nastaliq (Urdu+) | current | — |

### 10.3 Other-Script Fonts (Smith #7, HIGH confidence for existence; version/date MEDIUM where unspecified)

| Font | Script |
|------|--------|
| Abyssinica SIL | Ethiopic |
| Ezra SIL | Biblical Hebrew |
| Padauk | Myanmar |
| Nuosu SIL | Yi script |
| Annapurna SIL | Devanagari |
| Namdhinggo | Limbu |
| Tai Heritage Pro | Tai Viet |
| Shimenkan | Miao/Pollard |
| Kanchenjunga | Kirat Rai |
| Mingzat | Lepcha |
| Narnoor | Gunjala Gondi |
| Busra | Khmer |
| Idiqlat | Syriac |
| Akatab | Tifinagh |
| BJCree | Canadian Syllabics |

### 10.4 Download (Smith #7, HIGH confidence)

- Primary: [https://software.sil.org/fonts/](https://software.sil.org/fonts/) — master catalog organized by script region
- All fonts available as TTF + WOFF/WOFF2
- All licensed OFL

---

## ═══ SECTION 11: LEAGUE OF MOVEABLE TYPE ═══

### 11.1 Identity (Smith #8, HIGH confidence)

- "The first open-source font foundry" — established February 2009
- Philosophy: curated, hand-picked typefaces; quality over quantity; no mass-inclusion
- Managed by professional typographers

### 11.2 Font Count (Smith #8 — INTERNAL CONFLICT noted)

| Platform | Count | Date |
|----------|-------|------|
| Main website (theleagueofmoveabletype.com) | **24 fonts** | April 9, 2026 |
| Font Squirrel | 9 families | current |
| 1001 Fonts | 13 fonts | current |
| GitHub organization | 20+ repositories | current |

**Smith #8 explanation:** Discrepancy due to platforms subsetting the collection, variable fonts counted separately, or discontinued fonts archived on some platforms. Prefer 24 (main site, April 2026) as authoritative.

### 11.3 License (Smith #8, HIGH confidence)

**All fonts: SIL Open Font License (OFL)** — Commercial use permitted, no fee. Derivatives must retain OFL. League maintains OFL FAQ & license repository at github.com/theleagueof/licenses.

### 11.4 Complete Font Families (Smith #8)

| # | Font | Type | Glyph/Character Detail |
|---|------|------|----------------------|
| 1 | League Spartan | Geometric Sans | 562 glyphs, 16 character sets, 127 languages |
| 2 | League Gothic | Display/Headline | 202–322 glyphs (variant-dependent); revival of Alternate Gothic #1 (1903) |
| 3 | Raleway | Variable Sans | 406 characters, 285 glyphs, Latin Extended A/B |
| 4 | Fanwood | Serif | 416 characters, 308 glyphs, comprehensive Latin |
| 5 | Linden Hill | Serif | 395 characters, 268 glyphs, Latin Extended |
| 6 | Sorts Mill Goudy | Serif | 391 characters, 288 glyphs, Latin Extended, small caps/alternates |
| 7 | Goudy Bookletter 1911 | Serif | 303 characters, vintage revival |
| 8 | League Mono | Monospace | Multi-language: Afrikaans–Vietnamese |
| 9 | League Script | Script | Ligatures, alternates (detailed specs unavailable) |
| 10 | Ostrich Sans | Display Sans | 116–208 glyphs (variant), 8 Unicode blocks |
| 11 | Chunk (ChunkFive) | Slab Serif | Originally ASCII, extended to full Unicode |
| 12 | Blackout | Stencil Display | Reduced glyph set (exact count unavailable) |
| 13 | Junction | Geometric Sans | 3 styles (specs unavailable) |
| 14 | Knewave | Display | Specs unavailable |
| 15 | The Neue Black | Display Sans | 25+ ligatures |
| 16 | Orbitron | Geometric Display | Futuristic display typeface (specs unavailable) |
| 17 | Prociono | Serif/Blackletter | Blend of Latin & blackletter (specs unavailable) |
| 18 | Sniglet | Decorative | Full character set, supports Icelandic/French |
| 19–24 | (5 more) | TBD | **Not individually verified in searches** — gap within Smith #8 |

### 11.5 Download Locations (Smith #8)

| Platform | URL | Formats | Coverage |
|----------|-----|---------|----------|
| Official Site | theleagueofmoveabletype.com | TTF, OTF | All 24 fonts |
| GitHub | github.com/theleagueof | TTF, OTF, Variable | All fonts + source files |
| Font Squirrel | fontsquirrel.com | TTF, OTF | 9 families (subset) |
| Adobe Fonts | fonts.adobe.com/foundries/the-league-of-movable-type | Web fonts | Library integration |
| Google Fonts | fonts.google.com | Web fonts | League Spartan, League Gothic, Raleway, etc. |
| 1001 Fonts | 1001fonts.com | TTF, OTF | 13 fonts (subset) |

---

## ═══ SECTION 12: VELVETYNE TYPE FOUNDRY ═══

### 12.1 Identity (Smith #9, HIGH confidence — retrieved April 9, 2026)

- Association and collective dedicated to researching and disseminating typography
- Founded: **2010**, Paris-based non-profit
- Mission: opposes proprietary fonts; supports "experimental projects with high aesthetic or technical value but limited commercial appeal"
- Services: workshops, custom font design, community channels (Mastodon, Telegram, email)

### 12.2 Font Count (Smith #9)

| Figure | Type | Confidence | Date/Note |
|--------|------|------------|-----------|
| **40+ active typefaces** | Primary collection | HIGH | April 9, 2026 (velvetyne.fr/download/) |
| **90+ total documented** | All historical | MEDIUM | Fonts In Use (fontsinuse.com) |
| **29 retired** | Archived Nov 2023 | HIGH | Website redesign / editorial scope narrowing |

**Anderson math check:** 90+ total − 29 retired ≈ 61 active (derived, LOW confidence per Smith #9), but website states ~43 were seen initially. The 40+ figure from the downloads page is the most current and directly observed.

### 12.3 License (Smith #9, HIGH confidence)

**All Velvetyne fonts: SIL Open Font License (OFL)**
Four freedoms: Use (personal & commercial), Modify (for specific needs), Redistribute (original), Redistribute modified (must retain OFL).
Attribution required; exception for physically impossible credit situations.

### 12.4 ML Training Policy (Smith #9, HIGH confidence — confirmed absence)

**NO explicit ML training policy found.** FAQ, about page, and licensing docs are silent on ML/training/dataset use. OFL license likely permits it (fonts redistributable for any purpose), but foundry may have preferences. Smith #9 recommendation: contact team@velvetyne.fr or vtf1554@gmail.com before use.

### 12.5 Bulk Download (Smith #9)

| Method | Status |
|--------|--------|
| Individual `.zip` per font page | ✓ Available |
| Git clone from GitLab (gitlab.com/velvetyne, one repo per font) | ✓ Available |
| Single-archive bulk download (official) | ✗ None found |
| Community mirror (asimmkhan/fonts on GitHub) | ⚠️ Unofficial; last updated 2021-09-09 — may be outdated |

**GitLab repos confirmed (sample):** fungal, avara, mess, grotesk, le-murmure, sligoil
**Clone format:** `git clone https://gitlab.com/velvetyne/{font-name}.git`

### 12.6 Commercial Use (Smith #9, HIGH confidence)
- Explicitly permitted under OFL
- Listed among "15 Best Free Font Websites for Commercial Use in 2026" (purshology.com, 2026-03-15)

---

## ═══ SECTION 13: TeX/CTAN FONTS ═══

### 13.1 TeX Gyre Collection (Smith #10, HIGH confidence — CTAN, 2025)

- **8 families:** Adventor, Bonum, Chorus, Cursor, Heros, Pagella, Schola, Termes
- **Formats:** OpenType (OTF), Type 1
- **License:** GUST Font License (GFL) — legally equivalent to LPPL 1.3c or later
- **Character coverage:** ~1,250 glyphs per family (core); extended ~3,000 across all styles; Latin, Greek, Cyrillic, extended European diacritics | MEDIUM confidence
- **ASCII coverage:** Full | HIGH confidence
- **Note:** GFL is less common than OFL/Apache — relevant for ML training license analysis

### 13.2 DejaVu Font Family (Smith #10, HIGH confidence — CTAN, 2025)

- **Families:** DejaVu Sans, DejaVu Serif, DejaVu Sans Mono
- **Formats:** TrueType (TTF), Type 1 converted
- **License:** DejaVu modifications = Public Domain; CTAN package = LPPL 1.3
- **Character coverage:** >4,000 glyphs in BMP (Sans); Latin, Greek, Cyrillic; derived from Bitstream Vera/Charter | MEDIUM confidence
- **ASCII coverage:** Full

### 13.3 Libertinus Font Family (Smith #10, HIGH confidence — CTAN, 2025)

- **Families:** Libertinus Serif, Libertinus Sans, Libertinus Mono, **Libertinus Math**
- **Formats:** OpenType (OTF)
- **License:** SIL OFL 1.1
- **Origin:** Fork of Linux Libertine (addressing bugs)
- **Coverage:** Western Latin, Greek, Cyrillic | MEDIUM confidence
- **ASCII coverage:** Full

### 13.4 Linux Libertine & Biolinum (Smith #10, HIGH confidence — CTAN, 2025)

- **Formats:** OTF, TTF, Type 1
- **License:** GNU GPL v2 (with font exception) + SIL OFL (dual)
- **Coverage:** Western Latin, Greek, Cyrillic; intended as Times New Roman alternative
- **ASCII coverage:** Full
- **Note:** Dual license (GPL + OFL) is unusual — relevant for downstream use analysis

### 13.5 Liberation Fonts (Smith #10, HIGH confidence — CTAN, 2025)

- **Families:** Liberation Sans, Liberation Sans Narrow, Liberation Serif, Liberation Mono (4 total)
- **Formats:** TrueType (TTF)
- **License:** SIL OFL 1.1 (v2.0.0+); older versions: GPL v2 with exceptions
- **Notable property:** Metrically compatible with MS Office fonts (Arial, Times New Roman, Courier)
- **ASCII coverage:** Full

### 13.6 Open Sans (Smith #10, HIGH confidence — CTAN, 2025)

- **Format:** TrueType-flavored OpenType (TTF)
- **License:** Apache License 2.0 (fonts); LPPL 1.3c+ (LaTeX support package)
- **Coverage:** Humanist sans-serif with extensive language support
- **ASCII coverage:** Full
- **Cross-Smith note:** Open Sans also appears in Google Fonts (Smith #1/#2), Adobe Fonts (Smith #2 comparison). CTAN package is a LaTeX wrapper for the same underlying font.

### 13.7 GNU FreeFont (Smith #10)

- **Families:** FreeSans, FreeSerif, FreeMono (3 total)
- **Formats:** OTF, TTF, WOFF
- **License:** GNU GPL 3.0+ with Font Exception 2.0
- **Glyph counts:** FreeSerif: 10,537 glyphs | FreeSans: 6,272 glyphs | FreeMono: 4,178 glyphs | MEDIUM confidence
- **⚠️ FLAG (Smith #10):** Glyph count data from Wikipedia — release date listed as 2012-05-03 (>12 years old). May not reflect current version.
- **ASCII coverage:** Full

### 13.8 Serif Families Table (Smith #10, HIGH confidence — CTAN, 2025)

| Family | Format | License | ASCII Coverage |
|--------|--------|---------|----------------|
| EB Garamond | OTF, TTF | SIL OFL 1.1 | Full |
| Alegreya | OTF | SIL OFL 1.1 | Full |
| Merriweather | TTF | Open License | Full |
| Old Standard | OTF | SIL OFL | Full |
| Crimson | OTF/TTF | SIL OFL | Full |

*(Smith #10 was truncated at this point — additional serif families may have been listed)*

---

## ═══ SECTION 14: LICENSE ECOSYSTEM OVERVIEW ═══

*Cross-Smith synthesis (Anderson) — converging signal across all 10 reports*

| License | Sources Confirming | Confidence |
|---------|--------------------|-----------|
| **SIL OFL dominates open font ecosystem** | Smith #1 (Google Fonts), #3 (Font Library ~68%), #4 (Adobe Originals — all), #6 (Fontsource non-Google examples), #7 (SIL — all), #8 (League of Moveable Type — all), #9 (Velvetyne — all), #10 (Libertinus, Liberation, EB Garamond, Alegreya, etc.) | **HIGHEST — 8 of 10 Smiths confirm OFL dominance** |
| **Apache 2.0** | Smith #1 (Google Fonts minority), #3 (Font Library: 30 fonts), #5 (github repos), #6 (Fontsource: Clear Sans example), #10 (Open Sans) | HIGH |
| **GNU GPL (with/without font exception)** | Smith #3 (Font Library: 138 fonts), #10 (Linux Libertine, GNU FreeFont) | HIGH |
| **MIT/X11** | Smith #3 (Font Library: 48 fonts) | MEDIUM |
| **GUST Font License (GFL)** | Smith #10 (TeX Gyre only) | HIGH (narrow) |
| **CC-BY / CC-BY-SA** | Smith #3 (Font Library only: 39 + 22 fonts) | MEDIUM |
| **UFL (Ubuntu Font License)** | Smith #1 (Google Fonts legacy only) | MEDIUM |
| **Public Domain / CC0** | Smith #3 (Font Library: 25 fonts), Smith #6 (Fontsource: Aileron CC0-1.0) | MEDIUM |

**Anderson synthesis:** OFL is the de facto standard for open font licensing. For ML training data collection, OFL is the most permissive and clear; GPL (even with font exception) and CC licenses have more complex downstream implications.

---

## ═══ SECTION 15: ML TRAINING / BULK DOWNLOAD COVERAGE ═══

*Cross-Smith summary*

| Source | ML Legality | Bulk Download | Notes |
|--------|-------------|---------------|-------|
| **Google Fonts** | ✓ (OFL/Apache) | Partially (GitHub enumerable, no single archive) | Smith #1 |
| **Font Library** | ✓ (all open licenses) | ✗ official; scraping required; community Python tool exists | Smith #3 |
| **Adobe Originals** | ✓ (OFL) | ✓ GitHub releases per font | Smith #4 |
| **Fontsource** | ✓ (OFL/Apache) | ✓ NPM, jsDelivr CDN, API | Smith #6 |
| **SIL Fonts** | ✓ (OFL) | ✓ software.sil.org/fonts/ | Smith #7 |
| **League of Moveable Type** | ✓ (OFL) | ✓ GitHub org (per font repos) | Smith #8 |
| **Velvetyne** | ✓ likely (OFL) | ✗ no official archive; GitLab per-repo clone only; unofficial 2021 mirror | Smith #9 — recommend confirming with foundry |
| **TeX/CTAN** | Mixed (OFL, GPL, GFL, LPPL) | ✓ CTAN packages | Smith #10 — GFL and dual-GPL require closer review |

---

## ═══ CORRECTIONS ═══

**CORRECTION C-1 (Smith #5 — google/fonts family count):**
Smith #5 cites 1,382 families for google/fonts "from Dec 2023 issue #7121." This is **16+ months stale** as of April 2026. The correct current figure is 1,929 families (Smith #1, April 2026, HIGH confidence). Smith #5's star count (18,400) is current (April 2026), but the font count should not be used for current-state analysis.

**CORRECTION C-2 (Smith #10 — GNU FreeFont glyph counts):**
Smith #10 flags its own data: GNU FreeFont glyph count sourced from a Wikipedia article dated to the 2012-05-03 release. This is 14-year-old data. The counts (FreeSerif: 10,537; FreeSans: 6,272; FreeMono: 4,178) should be treated as historical baselines, not current values.

**CORRECTION C-3 (Smith #4 — truncation):**
Smith #4's findings were truncated mid-sentence at the Noto fonts clarification. The full statement appears to have been: Noto fonts are *not* Adobe Originals — while Adobe collaborates on CJK variants, Noto is a Google/Monotype project. This is consistent with Smith #7 (SIL) and other context. The truncated content is noted; Opus should treat the Noto-is-not-Adobe-Originals statement as HIGH confidence based on convergent knowledge, but acknowledge the source was cut.

**CORRECTION C-4 (Smith #8 — font count platform variance):**
Platform counts for League of Moveable Type (Font Squirrel: 9, 1001 Fonts: 13, GitHub: 20+, official: 24) are not errors per se, but Smith #8's explanation is correct: these reflect subsetting and archival by third-party platforms, not contradictions. The authoritative count is 24 (official site, April 9, 2026).

---

## ═══ DISPUTES ═══

**DISPUTE D-1 (HIGH PRIORITY): Google Fonts Total Family Count**
- Smith #1: **1,929 families** | April 2026 | HIGH confidence | Source: multiple recent sources citing April 2026 data
- Smith #2: **1,911 fonts** | 2026 (month unspecified) | HIGH confidence | Source: multiple 2026 sources

**Nature of dispute:** Not stale vs. fresh — both are 2026 figures. 18-family gap. Possible causes: different snapshot dates within 2026 (Smith #1 is specifically April; Smith #2 may be earlier in 2026), counting methodology differences (whether draft/beta families counted), or source disagreement between serbyte.net/Kinsta (Smith #2) vs. Kinsta/devstars/photutorial (Smith #1). **Opus needs to resolve or adjudicate.**

**DISPUTE D-2 (MEDIUM): Font Library Total Count — Families vs. Legacy Figure**
- Smith #3 (direct site, 2026): **2,172 families**
- Smith #3 (Wikipedia, ~2023–2024): **6,000+**

**Anderson assessment:** This is likely NOT a genuine dispute — different definitions (families vs. files vs. historical accumulation). The 6,000+ figure from Wikipedia may count individual font files (consistent with the 29,776 file count), or may include de-duplicated/legacy entries. However, the source dates are also different. Anderson recommends treating 2,172 (families, 2026) as the operative current figure while noting the Wikipedia figure and its likely basis.

**DISPUTE D-3 (LOW): Fontsource Font Count**
- Smith #5 (fontsource/font-files GitHub): 2,000+
- Smith #6 (official README): 1,500+
- Smith #6 (website ~April 2026): 2,077

**Anderson assessment:** Not a genuine conflict. README figure (1,500+) is a conservative floor, likely outdated or undercounted. Website figure (2,077) and GitHub repo count (2,000+) are consistent. Operational figure: ~2,077 families as of April 2026.

---

## ═══ GAPS ═══

**GAP G-1: Noto Fonts (Google/Monotype) Not Covered**
No Smith provided a dedicated report on the Noto font project — arguably the most extensive multilingual open-source font effort (100+ scripts, 1,000+ languages). Smith #4 mentions it only to clarify it is NOT an Adobe Original. Given the project's scale and relevance to ML training data, this is a significant research gap.

**GAP G-2: Google Fonts — Exact License Count Breakdown**
Smith #1 confirmed this data is not publicly available: no exact counts of OFL vs. Apache vs. UFL families are exposed in the Google Fonts public API or GitHub README. Would require programmatic enumeration of `/ofl`, `/apache`, `/ufl` directories.

**GAP G-3: Google Fonts — Total Individual Font Files**
Smith #1 confirmed no aggregate published count of TTF/OTF files across all weights/styles exists. Would require enumerating all 1,929 families' weight/style variants.

**GAP G-4: Variable Font Depth Across Non-Google Sources**
Smiths #3 (Font Library), #7 (SIL), #8 (League), #9 (Velvetyne), #10 (CTAN) do not report on variable font availability within their catalogs. Variable font coverage is only quantified for Google Fonts (Smith #1: 543 families).

**GAP G-5: DaFont, Font Squirrel as Standalone Repositories**
Neither DaFont nor Font Squirrel was covered as a primary subject. Both are major font distribution platforms with millions of downloads; their license policies, bulk download options, and ML-training suitability are unaddressed across all 10 Smiths.

**GAP G-6: Microsoft Open Source Fonts**
No Smith covered Microsoft's open-source font contributions (e.g., Cascadia Code, Fluent Emoji fonts, historical contributions like Verdana/Georgia under open licenses). This is a gap given Microsoft's significant open-source font activity.

**GAP G-7: CTAN/Smith #10 Truncation**
Smith #10 was truncated mid-table in the Serif Families section. The full list of CTAN fonts was not captured. Additional serif families (and potentially monospace, sans-serif, math) may exist in the original report.

**GAP G-8: ML Training Policies — Explicit vs. Implied**
Most sources rely on implicit OFL permissiveness for ML training. Only Font Library (Smith #3) documented an explicit (though not yet published) AI policy (May 2024 announcement). Velvetyne (Smith #9) confirmed no explicit policy. No other Smith addressed ML training permissions directly for their respective sources.

**GAP G-9: OTF Availability on Fontsource**
Smith #6 confirms TTF/WOFF/WOFF2 availability on Fontsource but leaves OTF status explicitly unclear. OTF is relevant for training pipelines that prefer OTF over TTF.

**GAP G-10: League of Moveable Type — Fonts #19–24**
Smith #8 explicitly notes 5 of the 24 official League of Moveable Type fonts were "not individually verified in searches." Their names, types, glyph counts, and individual specs are unknown from this Chain.

**GAP G-11: CJK / Non-Latin Coverage Beyond SIL and Adobe**
SIL (Smith #7) and Adobe (Smith #4, Source Han) provide CJK coverage. No other Smith addresses CJK or non-Latin font availability in other repositories (Font Library, League, Velvetyne, CTAN, Fontsource).

**GAP G-12: Star Count / Popularity for Non-GitHub Sources**
Smiths #3, #7, #8, #9, #10 cover sources that are not primarily GitHub-hosted (fontlibrary.org, software.sil.org, theleagueofmoveabletype.com, velvetyne.fr, ctan.org). No cross-source popularity/usage metrics are available for these.

---

## ═══ ANDERSON TRIAGE SUMMARY ═══

| Category | Count | Primary Items |
|----------|-------|---------------|
| Sources organized | 10 Smiths | #1–#10 |
| Thematic sections | 15 | Google Fonts (4 sections), Font Library, Adobe, GitHub repos, Fontsource, SIL, League, Velvetyne, CTAN, License ecosystem, ML/Bulk |
| Corrections issued | 4 | C-1 (stale count), C-2 (stale glyph data), C-3 (truncation), C-4 (platform variance clarification) |
| Disputes flagged | 3 | D-1 HIGH (GF count 1,929 vs 1,911), D-2 MEDIUM (Font Library 2,172 vs 6,000+), D-3 LOW (Fontsource 1,500+ vs 2,077) |
| Gaps identified | 12 | G-1 (Noto) through G-12 (non-GitHub popularity) |
| Cross-Smith convergence | 1 major | OFL dominance confirmed by 8 of 10 Smiths — HIGHEST confidence finding |

**Highest-confidence finding across Chain A:** SIL OFL is the dominant license for open-source fonts, confirmed by Google Fonts, Font Library, Adobe Originals, Fontsource (non-Google), SIL International, League of Moveable Type, Velvetyne, and CTAN (partially). This is the most robust signal in the dataset.

**Most contested finding:** Google Fonts total family count (1,929 vs 1,911) — both 2026, both HIGH confidence, 18-family gap. Requires Opus adjudication or fresh verification.

**Largest signal gap:** Noto fonts entirely uncovered. Given Noto's scope (100+ scripts), this is Chain A's most significant blind spot for any task involving multilingual font coverage.

---
*Anderson — Chain A complete. All unique signal preserved. Opus: no editorial compression has been applied; all findings, including minor details and confidence qualifiers, are passed through intact.*

---
**Oracle SDK Execution Metrics**
- Architecture: 50 Smiths -> 5 Andersons -> Opus (you)
- Total time: 514s
- Total tokens: 367,077 (in: 105,893 | out: 261,184)
- Quota: 0.66% weekly (5.0% session)
- Smiths: 50 (0 errors)
- Andersons: 5 (0 errors)
- Phase timing: scout: 207s | compress: 307s
- Phase costs: decompose: 0.00% | scout: 0.26% | compress: 0.40%

