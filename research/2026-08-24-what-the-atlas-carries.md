# What the atlas carries — four attributes clear a pre-registered bar (2026-08-24)

**Six interpretable features, already written and validated for a different
question, separate four style attributes on held-out font families.** The bar
was committed at `f5ab733` before the tool was ever executed.

Tools: `analysis/attribute_label_supply.py` (the census),
`analysis/attribute_separation.py` (the test). Data:
`research/attribute_label_supply.json`, `research/attribute_separation.json`.

## Why this ran at all

Generic CLIP was ruled out for style adherence at exactly chance
([note](2026-08-24-clip-does-not-read-the-decisive-clause.md)). The registered
alternative was a discriminative per-attribute classifier, justified in three
documents with one sentence I never checked: *"the labels are free because the
fonts' own metadata supplies them."*

Two questions had to be answered before writing a classifier, and both turned
out to have real answers rather than assumed ones.

## 1. The corpus cannot label the attributes that matter

11,383 licence-clean files, 2,223 families.

| attribute | files | **families** | source |
|---|---|---|---|
| weight | 7851 | **679** | `OS/2.usWeightClass` |
| slant | 2051 | **389** | `post.italicAngle` |
| serif vs sans | 1703 | **121** | PANOSE, `bFamilyType==2` only |
| width | 4556 | **59** | `OS/2.usWidthClass` |
| mono | 310 | **52** | family name |
| script/hand | 45 | 38 | family name |
| display | 664 | 30 | family name |
| slab | 26 | 14 | family name |
| **inline** | 14 | **10** | family name |
| **stencil** | 12 | **10** | family name |
| rounded | 12 | 6 | family name |
| shadow | 6 | 6 | family name |
| outline | 3 | 3 | family name |

**The supply splits along the wrong line.** The attributes with hundreds of free
labels are the conventional axes the generator already delivers. **Stencil and
inline — the two the eye caught failing — have ten families each.** The
justification for the classifier was true for five attributes and false for the
two that motivated it.

**Two of my own numbers were wrong, and writing the tool is what found them.**

- **Count families, not files.** Width looked like 4,556 examples. It is **59
  families**: width variants cluster in a few large superfamilies. A holdout
  splits by family, because 32 of this project's 50 holdout fonts share a
  superfamily with a training font.
- **The PANOSE trap.** `bSerifStyle` only indexes serif shapes when
  `bFamilyType == 2` (Latin Text); under Hand Written, Decorative or Symbol the
  same byte means something else. My first pass read it unconditionally and
  reported 6,040 files. Guarded, it is **1,703** — a **3.5× overstatement**, with
  every decorative face mislabelled. `tests/test_attribute_supply.py` pins both.

## 2. What survives the atlas — the pre-registered result

`render_atlas` centres every glyph on its **ink bounding box**
(`build_dataset.py:285`), so advance width is discarded. Weight and slant are ink
properties and had to survive. Width and monospace are advance-derived and might
not.

Logistic regression on six features, ROC AUC under `GroupKFold` **by family**,
2,000-draw label permutation:

| attribute | AUC | p | families | verdict |
|---|---|---|---|---|
| **weight** | **0.970** | 0.0005 | 83 | carried |
| **mono** | **0.946** | 0.0005 | 98 | carried |
| **slant** | **0.915** | 0.0005 | 89 | carried |
| **width** | **0.839** | 0.0005 | 58 | carried |
| serif vs sans | 0.733 | 0.0005 | 100 | **weak** |
| *stencil* | *0.910* | *0.0005* | *20* | *descriptive only* |
| *inline* | *0.860* | *0.0035* | *20* | *descriptive only* |
| *shadow* | *0.778* | *0.0550* | *12* | *descriptive only* |
| *rounded* | *0.722* | *0.1084* | *12* | *descriptive only* |
| *slab* | *0.313* | *0.9450* | *27* | *descriptive only* |
| outline | — | — | 3 | skipped, too few |

Bar as registered: ≥0.75 carried, 0.60–0.75 weak, <0.60 not carried.

### Monospace survives, and I predicted it would not

I reasoned from `render_atlas` that ink-centring destroys the mono signal,
because monospace is defined by equal **advances** and an `i` is narrow ink in
every font. That reasoning is sound and the conclusion is **wrong**: mono scores
**0.946 over 98 families**.

The mechanism is the part worth keeping. Mono designers *compensate in the ink* —
the `i` gets slab serifs, the `m` is squeezed — so the uniformity is drawn into
the glyphs themselves and survives centring.
`analysis/advance_survives_atlas.py`, on four mono and three proportional faces:

| | advance CV | atlas ink CV |
|---|---|---|
| Courier Prime / JetBrains / Roboto / Space Mono | **0.0000** | 0.2086–0.2397 |
| Open Sans / Lato / Merriweather | 0.2976–0.3270 | 0.3259–0.3944 |

Margin **+0.0862**, no overlap. Advance information is destroyed exactly as
predicted. The attribute is not.

**The general lesson generalises past monospace:** an attribute is carried by
whatever a designer *drew* to express it, not by the metric that happens to
define it. Reasoning from the definition to what the image contains is what went
wrong, and it would have dropped a 0.946 attribute from the classifier.

**This matters for the product**, because *"a wide low-contrast monospace"* is
one of the two styles the generator was recorded as missing on 2026-08-23,
before any of this existed.

### serif vs sans is weak, and that is a FEATURE limit, not an atlas limit

0.733 over 100 families at p=0.0005 — a real effect, and a small one. The cause
is not mysterious: **none of the six features measures terminal shape.** They
are stroke thickness, slant, fill, component count, ink-width spread and aspect
ratio. A human reads a serif instantly; this feature vector has no way to.

**The registration forbids fixing that here.** Its own words: an attribute below
the bar is *"dropped from the classifier rather than rescued with a different
feature set on the same data."* Adding a terminal-shape feature and re-running
would be precisely the goalpost-move the CLIP retraction was about. A
terminal-shape feature is the obvious untested candidate, and it needs its own
registration and its own run.

### slab scores BELOW chance, and that is the census warning arriving

0.313, p=0.945. Descriptive only, n=27 families — but the direction is a useful
reminder that **name keywords are not labels**. A font named "Slab" is whatever
a foundry chose to call it, and 27 such families are not a class. The four
attributes that cleared the bar are the four with *table*-derived labels, plus
mono. That correlation is not an accident.

## What this does and does not establish

**Does.** Six existing interpretable features, computed from a rendered atlas,
carry weight, monospace, slant and width well enough to build on. No GPU, no
download, no new dependency, and the features were written for a different
question — so they were not tuned to this one.

**Does not.**

- **Separating real fonts is an easier problem than scoring a generation.**
  "Is this real font monospace" is not "did this generation obey the word
  monospace". The transfer is untested and it is the next thing to register.
- **The rare attributes carry no conclusion.** Stencil at 0.910 and inline at
  0.860 look excellent and are ten families a side. Registered as descriptive
  only, and they stay that way.
- **The negative sets are the alphabetically-first families**, not a random
  sample — deterministic, as registered, and a random-sample replication would
  strengthen every row.
- **Nothing here is calibrated.** An AUC is a ranking; a gate needs a threshold
  and error rates on held-out data, and this has neither.

## Next

1. **Test transfer.** Score the twelve candidate atlases from
   `2026-08-23-the-loop-closes.md`, where the misses were recorded *before* this
   instrument existed. Two positives out of twelve is a sanity check, not a
   validation — but the git timestamp proves the labels preceded the measure.
2. **Synthesize the rare attributes.** A stencil face is a real face with bands
   erased; an inline face is one with a medial stripe removed. This repository
   already manipulates outlines. Train on synthetic, **test on the ten real
   stencil families held out entirely** — that transfer test is the whole value,
   and a classifier that learns "grid-aligned gaps" will fail it.
3. **Register a terminal-shape feature** for serif vs sans, separately.

## Status of the three axes

| axis | instrument | state |
|---|---|---|
| coherence | `reference_gate.py`, `style_coherence.py` | validated |
| identity | `glyph_classifier.py` | validated |
| adherence | — | **still none.** Four attributes are now known to be *readable*, which is a precondition, not an instrument |
