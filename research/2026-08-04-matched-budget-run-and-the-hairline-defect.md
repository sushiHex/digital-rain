# Matched budget made it worse, and the cause was a defect in my instance selection (2026-08-04)

**What ran.** `dataset_v3` (1,113 fonts) at **6,016 steps** — chosen to restore
the per-font gradient budget the 5,000-step run had cut (5.405 steps/font, v2's
exact figure). Everything else identical. This was meant to isolate "more data"
from "less training per font".

**It regressed further.**

| run | fonts | steps | char_acc | dinov2 | lpips | composite | identity |
|---|---|---|---|---|---|---|---|
| v2 baseline | 925 | 5000 | **0.6460** | **0.8485** | **0.1381** | 0.8158 | **0.9893** |
| v3 | 1,113 | 5000 | 0.6081 | 0.8314 | 0.1331 | **0.8186** | 0.9855 |
| v3 matched | 1,113 | 6016 | **0.5668** | 0.8418 | **0.1814** | 0.7824 | 0.9807 |

Against the baseline, the matched-budget run is significantly worse on
char_acc, racc, lpips **and** identity (r = 0.43–0.66). dinov2 alone shows no
difference.

## Training was healthy; the failure is in what the model learned to draw

The loss curve gives no warning at all — the 6,016-step run has the *lowest*
final-1000 mean of the three:

| run | min loss | last-1000 mean |
|---|---|---|
| v2 | 0.0264 | 0.0418 |
| v3 @5000 | 0.0268 | 0.0425 |
| v3 @6016 | 0.0269 | **0.0410** |

Conditioning was verified correct (`prompt_style=trained-short`, guard passed).

The tell is in the pixels. Mean ink coverage of generated atlases:

| | ink fraction |
|---|---|
| ground truth | 0.0719 |
| v2 | 0.0737 |
| v3 @5000 | 0.0743 |
| **v3 @6016** | **0.0527 (−27%)** |

The model learned to draw **systematically thinner strokes**. That explains the
whole metric pattern: lpips and char_acc punish a global weight shift, dinov2
is comparatively robust to stroke weight (hence "no diff"), and identity stays
at 0.98 because the letters are still the right letters.

## The cause: centroid distance cannot tell "distinctive" from "degenerate"

Instance selection maximised DINOv2 distance from the corpus centroid. **The
cheapest way to be far from a centroid is to be nearly blank.** Amstelvar's
`XOPQ` axis is *x-opaque* — literally stem thickness — and the axis-grid
sampled it at its minimum.

Four near-hairline instances reached `dataset_v3`:

| instance | ink | vs corpus median 0.0564 |
|---|---|---|
| `AmstelvarAlpha XOPQ=5,XTRA=402,YOPQ=4` | 0.0058 | 10x thinner |
| `ScienceGothic Thin Italic` | 0.0081 | 7x thinner |
| `Doto Thin` | 0.0112 | 5x thinner |
| `AmstelvarAlpha XOPQ=5,XTRA=42,YOPQ=4` | 0.0133 | 4x thinner |

For scale: the thinnest of the 925 real corpus fonts is 0.0191, so the worst
synthetic instance was **3x thinner than anything a real typeface designer
shipped**.

**A second, structural miss:** static fonts are gated by
`build_dataset.font_supports_charset`, which includes `check_render_visibility`.
`pipeline/build_expansion.py` renders instances directly and **bypasses that
gate entirely**. Every corpus font had to prove it was visible; generated
instances did not.

## Why 0.36% of the corpus did this — and why only at 6,016 steps

Four fonts out of 1,113 is 0.36%, which cannot shift global ink 27% by
averaging. The mechanism is convergence, not proportion: at 5,000 steps
generated ink was **normal (0.0743)**; the same corpus at 6,016 steps
collapsed. The extra 1,016 steps gave the model the opportunity to fit the
degenerate examples, and near-blank targets are a strong "draw almost nothing"
signal.

So both factors were necessary, and the two runs fail for *different* reasons —
which is why neither is a clean test.

## What this does and does not establish

- **Established:** the matched-budget run is invalid. Its corpus contained
  degenerate targets and longer training amplified them.
- **Established:** the v3 @5000 regression is *not* explained by hairlines —
  its generated ink was normal. Corpus expansion at 5,000 steps genuinely
  regressed char_acc and dinov2.
- **NOT established:** whether corpus expansion helps at matched per-font
  budget on a clean corpus. Both attempts are confounded, by different defects.
- **Standing:** in v3 @5000 the targeted faces still moved toward the 9B —
  BitcountPropDoubleInk 0.181 -> 0.255 against the 9B's 0.266.

## The fix, applied

`select_expansion_set.py` now enforces an ink floor on every candidate
instance, relative to the corpus median (default 0.5x–3.0x, i.e.
0.0282–0.1692). It **rejected 60 instances**, including all four hairlines.

New set: 168 static + 9 instances = 177 additions, distinctive tail 93 -> 118
(1.27x). Built as `dataset_v3c` (1,102 fonts) in a fresh directory rather than
pruned, so no stale atlas survives. All 9 surviving instances fall in
[0.034, 0.167].

## Addendum (2026-08-06): a THIRD defect, larger than the hairlines

A `/simplify` review of the expansion tooling found the atlas/reference pair
was rendered through two different loaders, so most additions were internally
inconsistent:

- `build_dataset.render_atlas` defaults to `load_truetype_pinned`, which pins a
  variable font to its **"Regular" named instance**.
- `build_dataset.render_reference` calls `ImageFont.truetype` directly, i.e.
  the font's **axis defaults**.

For a variable font those disagree. `build_expansion.py` let each renderer pick
its own default, so the atlas showed one instance and the reference another —
and the reference is the style-conditioning input the model is trained to copy.
**101 of the 168 static expansion fonts are variable**, plus all 9 instances
(where the monkeypatch reached only the atlas; all four Workbench instance
references were byte-identical while their atlases differed). So roughly
**110 of 177 additions taught "this reference -> a different style"**.

Measured divergence between the two conventions: mean 3.3/255 on the
weight/width-axis families (Anek*), 17.6/255 on `Doto[ROND,wght]`.

There is a further wrinkle worth recording: **`dataset_v2` predates the
"Regular" pin.** A plain `ImageFont.truetype` render of `Doto[ROND,wght]` is
byte-identical to `dataset_v2/atlases/Doto[ROND,wght].png`, while the pinned
render differs. So the additions were not merely self-inconsistent, they also
used a *different convention from the 925 fonts they were being added to*.

Fixed: `render_atlas`/`render_reference` take an explicit `loader`,
`build_expansion.loader_for()` supplies one loader for both halves, and
non-instance entries use `corpus_default_loader` so additions match the corpus.
`dataset_v3c` has been fully re-rendered and re-cached under the single
convention.

**What this does to the conclusions above:** the corpus-expansion regression
now has three candidate causes, not one — the per-font budget cut, the
hairline instances, and this pair mismatch across ~62% of the additions. None
of the three runs isolated any of them. The recorded verdict stands as "corpus
expansion regressed as run", not "corpus expansion does not work", and the
result is weaker evidence against the lever than it first appeared.

## Cost so far

Two full training runs (~26 h GPU) on this lever, no clean result. A third —
`dataset_v3c` at 6,016 steps — would be the first uncontaminated test. That is
a judgement call about whether a lever whose ceiling is a **+27% distinctive
tail** is worth a further ~14 h, given it has regressed twice.

## Artifacts

- `eval_runs/glyph_4b_v3_6016/`, `training_glyph_4b_v3_6016/`
- `research/2026-08-04-wilcoxon_glyph_4b_r32_5000_vs_glyph_4b_v3_6016.json`
- `dataset_v3c/`, regenerated `research/expansion_set.json`
