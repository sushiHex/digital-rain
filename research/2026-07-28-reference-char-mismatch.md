# Train/eval reference-character mismatch: the model trains on `Rg` but is evaluated on `Kg` (2026-07-28)

**Question asked:** would we have better success using `Rg` instead of `Kg` as the reference characters?

**Answer: training already uses `Rg`. Evaluation uses `Kg`. They disagree — and every headline number in this project was measured under that mismatch.**

## The evidence

Verified by direct visual inspection of both corpora (`viz/ref_chars_mismatch_evidence.png`):

| corpus | built by | `REF_CHARS` | reference image shows |
|---|---|---|---|
| `dataset_v2/references/` (**training**) | `build_dataset.py` (module default) | `"Rg"` | **R** and **g** |
| `eval_holdout/references/` (**evaluation**) | `eval_build_holdout.py --reference-chars Kg` | `"Kg"` | **K** and **g** |

Mechanism:
- `build_dataset.py:24` — `REF_CHARS = "Rg"`, and `render_reference()`'s docstring explicitly reasons about it: *"R is taller than g and o, g has a descender, o shows x-height. This proportional relationship is critical style information for the model."*
- `eval_build_holdout.py:51-52` — overrides it: `build_dataset.REF_CHARS = args.reference_chars`, `REF_COLS = len(args.reference_chars)`.
- `eval_checkpoint.py:967` — `--reference-chars` defaults to `"Kg"`.
- `eval_holdout/manifest.json` records `"reference_chars": "Kg"`, confirming the holdout was built that way.

So the model was trained with an **R** in the left reference slot and is evaluated with a **K** there. Confirmed visually: `dataset_v2/references/ABeeZee-Regular.png` shows R+g; `eval_holdout/references/AlikeAngular-Regular.png` shows K+g.

Note the ink-profile trap: both K and R are cap-height with no descender, so column ink bounding boxes are **identical** between the two variants. This mismatch is invisible to any automated shape/bbox check — it can only be caught by looking at the images or reading the two constants.

Secondary inconsistency: `--reference-chars` also feeds `atlas_constants.make_prompt()`, which embeds the literal string in the text prompt. So the prompt has been asserting "Kg" while the training images showed "Rg". Low impact (the prompt is constant across all samples, so it carries no discriminative signal and is cached once as `cached_prompt_embeds`), but it is the same root confusion.

## Why this matters

Every number in the project — char_acc 0.688, IDENTITY 0.978, the disambig significance (p=0.048), all the paired-Wilcoxon comparisons, the Stage A regressions, the best-of-N ceilings — was measured with the evaluation reference **out of the training distribution**. Because the mismatch is *uniform across every arm*, all A/B comparisons remain internally valid (both arms saw the same `Kg` holdout). What is potentially wrong is the **absolute level**: the model may be systematically handicapped at eval time.

## The cheap test

This is inference-only and requires **no retraining**:

1. Rebuild the holdout references with `Rg` (CPU, seconds): `python eval_build_holdout.py --reference-chars Rg --out eval_holdout_rg` (verify the atlases/GT stay identical — only `references/` should change).
2. Regenerate on a 10-font subset with the existing best checkpoint (~20 min GPU) — or all 50 (~1.7h).
3. Rescore and compare paired, same-fonts, against `eval_runs/glyph_r32_disambig50_mild`.

**Interpretation:**
- If scores **improve**, the project's headline quality has been understated all along, and the fix is free — just rebuild the holdout. Given the model's whole style signal comes from that reference, a meaningful jump is plausible.
- If scores are **flat**, the model is robust to reference-glyph identity (it extracts style, not letter identity, from the reference), which is itself a useful robustness result worth stating.

Either outcome is publishable-quality detail for the writeup, and the experiment is hours not days.

## On the original question — is some *other* subset better?

Separate from the mismatch, "would a different reference subset help?" is **genuinely unablated**. What we do know:

- **Reference font identity matters a lot.** Prior ablation (`research/2026-05-02-ref_ablation_analysis.json`) shows oracle (font's own TTF) beats a generic Times reference decisively on hard fonts — e.g. BitcountGridDoubleInk DINOv2 0.552 (times) → **0.877** (oracle).
- **Adding a second reference image is a wash.** (`research/2026-05-02-multiref_analysis.json`): 1×`Kg` → LPIPS 0.3704 / DINOv2 0.8088; 2×`Kg,Mn` → 0.3676 / 0.7918 (DINOv2 slightly *worse*). More reference images did not help.
- **Which characters within one reference: never tested.**

On theory, `R` should carry strictly more style information than `K`: R contributes a stem, a **bowl** (curve + closed counter), and a diagonal leg, whereas K contributes a stem and two diagonals with **no curve and no counter**. Whoever set `REF_CHARS = "Rg"` had the right instinct, and the docstring shows the reasoning was deliberate.

But the residual failures actually observed (see `viz/showcase_grids.py` output) are **texture and weight errors, not structural ones** — Rubik's distress too light, Bitcount's dots too heavy, Kavoon's strokes too thin, Fascinate Inline's interior stripe filling in. Reference-*character* choice plausibly does little for those; they look like capacity/quantization-of-texture issues. So the expected payoff from further character-subset search is modest.

**Caveat on testing alternatives fairly:** the model was *trained* on `Rg`, so swapping in `Ho`, `no`, or `Hno` at inference is out-of-distribution — a degradation there would confound "worse characters" with "unfamiliar characters." A fair comparison of alternative subsets requires retraining per variant, which is expensive. Fixing the `Rg`/`Kg` mismatch is the exception: it moves eval *toward* the training distribution, so it is a clean, cheap win to test.

---

## RESULT (2026-07-28): the mismatch is real but **harmless** — the model is robust to reference glyph identity

Ran the test: `eval_holdout_rg` (references re-rendered with `Rg`, GT atlases byte-identical — verified 50/50 identical, 50/50 references changed), generated 10 fonts with the banked best checkpoint, prompt left at `"Kg"` so the reference *image* was the only variable.

**Paired, same-fonts, 940 cells:**

| metric | Kg (as-shipped) | Rg (matches training) | delta |
|---|---|---|---|
| char_acc | 0.5766 | 0.5787 | **+0.0021** |
| dinov2 | 0.8707 | 0.8705 | −0.0002 |
| lpips (lower better) | 0.1495 | 0.1521 | +0.0025 |

Cell-level: **54 lost, 56 gained, net +2 of 940.**

**Paired Wilcoxon over the 10 fonts (per-font char_acc): W=8.0, p=0.6250, median delta exactly 0.0000.** Three fonts better, three worse, four bit-identical. Nowhere near the project's p<0.05 ∧ r≥0.3 bar. (An effect size computed here is not meaningful — four fonts tie exactly, so the effective n is 6 and the normal approximation does not apply. The p-value and the zero median are the honest summary.)

**Conclusion: the hypothesis was wrong, and that is informative.** Swapping the reference's cap-height glyph from K to R changes nothing measurable. The model extracts **style** from the reference — weight, contrast, texture, terminal treatment — and does not key on the *identity* of the reference glyph. The train/eval mismatch was real, but it cost nothing.

**Consequences:**
- **No free win.** Headline numbers were not understated; every existing measurement stands exactly as reported. No 50-font re-run or Wilcoxon redo is needed.
- **A genuine robustness property, worth stating in the writeup:** reference-glyph identity is not a sensitive hyperparameter. That also retroactively explains why the multi-reference ablation was a wash — if identity doesn't matter, adding a second glyph adds little.
- **It reinforces where the real problems are.** The residual failures are texture/weight (Rubik's distress too light, Bitcount's dots too heavy, Kavoon too thin, Fascinate's inline filling in), not anything the reference *character* controls.
- **Cheap cleanup still worth doing:** align `eval_checkpoint.py`'s `--reference-chars` default and `build_dataset.REF_CHARS` so the two stop disagreeing, and fix the hardcoded training prompt's `"Kg"` string — purely to remove a latent trap for the next person, not for a quality gain.

**Caveat on scope:** this tested K→R, two structurally similar cap-height letters. It does **not** establish that *any* reference choice works — a reference lacking a descender or lowercase entirely (e.g. `HO`) could still matter, and testing that fairly needs retraining, since it would be out of distribution.

---

## FOLLOW-ON (2026-07-28): a SECOND, larger train/eval mismatch — the *prompt* — and it is asymmetric between the two models

While cleaning up the `Rg`/`Kg` confusion, confirming "what did training actually use" surfaced a bigger one.

**The two models were trained by different scripts with different prompts:**

| model | trained by | training prompt | evaluated with | match? |
|---|---|---|---|---|
| baseline `experiments/20260412-215340_Kg_structured_prompt_5000` | `train_lora.py:268-269` → `make_prompt(args.reference_chars)` | **534 chars, structured** — includes `Characters share a baseline per row.` and a full `Layout:` block listing all 8 rows | `make_prompt()` | ✅ **matched** |
| glyph `training_glyph_r32_5000` (the banked best generator) | `train_lora_kg.py:270-273` — hardcoded string | **208 chars** — 3 sentences, **no** layout block, no baseline sentence | `make_prompt()` | ❌ **mismatched** |

`eval_checkpoint.py` → `generation_lib.load_generation_pipe()` → `make_prompt(reference_chars)` produces the **structured** prompt for *both* models. Evidence: `train_lora.py` calls `make_prompt`, `train_lora_kg.py` does not (`grep -l make_prompt` lists the former, not the latter); the baseline's `train_config.json` records a `reference_chars` key, which only `train_lora.py` writes.

**Why this is worse than the `Rg`/`Kg` issue.** That one changed a single reference glyph and measured at exactly zero (p=0.625). This changes the text conditioning from 208→534 characters, adding a whole layout enumeration the glyph model has never seen. And critically it is **asymmetric**: the baseline gets its native prompt while the glyph model gets a foreign one, so it does not cancel across arms the way the `Kg` holdout did.

**Every glyph-vs-baseline comparison in this project inherits that asymmetry** — char_acc 0.6883 vs 0.6677, the p=0.048 significance, the SIG DINOv2 win (r=0.76), the LPIPS win. The direction of the bias is *against* the glyph model, so its true standing may be **better** than measured. (All the glyph-vs-glyph comparisons — disambig variants, Stage A arms, best-of-N — are unaffected, since both arms used the same structured prompt.)

**Test (cheap, inference-only, same shape as the Rg test):** generate the glyph model with its *trained* 208-char prompt instead of `make_prompt`'s, on the same holdout fonts, and compare paired. If scores rise, the banked generator has been systematically underrated and the headline numbers should be restated. If flat, the model is as robust to prompt as it proved to be to reference identity — which would itself be a strong, publishable robustness claim covering both conditioning channels.

**Not yet run.** Requires a small eval flag to select the trained prompt verbatim.

### Prompt test, first pass (n=10): directionally positive on every metric, but underpowered

Same holdout, same checkpoint, same disambig template — the prompt was the only variable.

| metric | structured (as-shipped) | trained-short | delta |
|---|---|---|---|
| **IDENTITY** (GT-gated, 810 cells scored in both) | 0.9654 | **0.9852** | **+0.0198** — 19 gained, 3 lost |
| char_acc | 0.5766 | 0.5883 | +0.0117 (67 lost, 78 gained) |
| dinov2 | 0.8707 | 0.8806 | +0.0099 |
| lpips (lower better) | 0.1495 | 0.1413 | −0.0082 |

Paired Wilcoxon on per-font char_acc: **W=14.5, p=0.3711, median delta +0.0213** (5 fonts better, 4 worse, 1 flat). **Not significant** — n=10 cannot resolve an effect this size.

**Read:** unlike the `Rg` test (median delta exactly 0.0000, p=0.625 — a clean null), this shows all four metrics moving the same direction, and the identity gain/loss ratio is 19:3. That is suggestive rather than conclusive. Notably AveriaSerifLibre +0.096 and BitcountGrid +0.043 against BitcountProp −0.053 — high per-font variance, which is exactly why n=10 is inadequate.

**For scale:** the glyph-vs-baseline margin this project reports is +0.0206 char_acc at p=0.048 (marginal). If a ~+0.012 prompt effect held up, it would be over half that margin — and since it applies *only to the glyph model*, it would materially change that comparison's standing.

**Escalated to the full 50-font holdout** to reach the project's standard bar (n=50, p<0.05 ∧ r≥0.3).

### Prompt test, FULL 50-font result: char_acc unchanged, **IDENTITY improves on all 50 fonts (p<1e-6, r=0.870)**

The n=10 char_acc signal was noise. The n=10 IDENTITY signal was real and got stronger.

| metric | structured (as-shipped) | trained-short | delta | paired Wilcoxon (n=50) |
|---|---|---|---|---|
| char_acc | 0.6883 | 0.6917 | +0.0034 | **p=0.948, r=0.010 — dead null** (median 0.0000; 24 better, 22 worse, 4 flat) |
| **IDENTITY** | **0.9780** | **0.9936** | **+0.0157** | **W=0.0, p<1e-6, r=0.870 — 50/50 fonts better, 0 worse** |
| dinov2 | 0.8777 | 0.8788 | +0.0011 | — |
| lpips (lower better) | 0.1515 | 0.1457 | −0.0058 | — |

Cell-level identity: **73 gained, 4 lost** over 4400 GT-gated cells. `W=0.0` means *every single font* improved — there was not one negative rank.

**Why this is coherent rather than surprising.** The structured prompt's extra content is a `Layout:` block enumerating **which character belongs in which grid cell** — i.e. pure *identity* information. The glyph model never saw it in training; it learned character identity from the **template channel** instead. Feeding it a foreign textual layout spec at eval time evidently interfered with exactly that: letter correctness. Removing it repairs identity (+0.0157, universal) and leaves style-match untouched (char_acc null, dinov2 flat).

That is the project's own two-axis separation showing up mechanistically: the prompt mismatch was an **IDENTITY** bug, and char_acc — being STYLE FIDELITY — was structurally incapable of detecting it. Had we only tracked char_acc, this would have been invisible (p=0.948).

**Biggest gains land on the hardest fonts:** BitcountGridDoubleInk 0.929→**1.000**, BitcountProp 0.831→0.873, KosugiMaru 0.968→**1.000**, FascinateInline 0.936→0.962, PlaywriteMXGuides 0.950→0.975, RubikDistressed 0.976→**1.000**.

**Corrected headline for the banked generator:** IDENTITY **0.9936** (not 0.978), when evaluated with the prompt it was actually trained on. char_acc stands at 0.688–0.692 either way.

**Action:** evaluate each model with *its own* trained prompt — `--prompt-style trained-short` for anything from `train_lora_kg.py` (the glyph line), `structured` for the `train_lora.py` baseline. The flag default stays `structured` deliberately, because the correct value is **model-dependent**; flipping it blindly would break baseline evals the same way in reverse.

**Caveat:** this does not change any glyph-vs-glyph comparison (disambig, Stage A, best-of-N) — those shared the structured prompt on both arms. It does mean the glyph-vs-baseline comparison was run with the glyph model handicapped on the identity axis.

### FAIR HEAD-TO-HEAD: with each model on its own trained prompt, the glyph model now PASSES the gate

Neither half needed new generation — the baseline's existing eval already used the structured prompt it was trained on, and the glyph model's `trained-short` run now exists. Paired, same 50 fonts, 4700 cells:

| metric | baseline (own prompt) | glyph (own prompt) | d_mean | p | r | gate |
|---|---|---|---|---|---|---|
| char_acc | 0.6677 | **0.6917** | **+0.0240** | **0.0156** | **0.353** | ✅ **PASS** |
| dinov2 | 0.8487 | **0.8788** | +0.0301 | <1e-5 | 0.768 | ✅ PASS (large) |
| lpips (lower better) | 0.1514 | 0.1457 | −0.0057 | 0.372 | 0.126 | ns (glyph better) |

**This upgrades the project's headline claim.** As previously reported — with the glyph model evaluated on a prompt it never trained on — char_acc was **+0.0206, p=0.048, r=0.266**: it scraped past p<0.05 but **failed the r≥0.3 half of the gate**, and the decision doc recorded it as a near-miss/marginal. Corrected, it is **+0.0240, p=0.0156, r=0.353 — passing both criteria**.

So glyph-latent conditioning + disambiguated template is not "parity with a structural edge"; on a fair comparison it is a **gate-passing char_acc win over the baseline, plus a large DINOv2 win (r=0.768), with LPIPS directionally better.**

The identity axis is pending: the baseline's eval predates the `--identity` wiring, so its per-cell records carry no identity fields. Re-scoring it is generation-free (`--skip-generate --identity`, reusing the 50 existing atlases) and is running. The glyph model's identity on its own prompt is **0.9936**.

### The identity axis completes the picture — and it cuts the other way

Baseline re-scored with `--identity` (generation-free). Fair head-to-head, both models on their own trained prompt, 4400 GT-gated cells:

| metric | baseline | glyph | delta | p | r | winner |
|---|---|---|---|---|---|---|
| char_acc | 0.6677 | **0.6917** | +0.0240 | 0.0156 | 0.353 | **glyph** (PASS) |
| dinov2 | 0.8487 | **0.8788** | +0.0301 | <1e-5 | 0.768 | **glyph** (large) |
| lpips | 0.1514 | **0.1457** | −0.0057 | 0.372 | 0.126 | glyph (ns) |
| **IDENTITY** | **0.9968** | 0.9936 | **−0.0032** | **0.0051** | **0.886** | **baseline** (PASS) |

Glyph gains 4 identity cells and loses 18; 0 fonts better, 10 worse, 40 exactly tied.

**Honest reading — the two models trade off along exactly the two axes this project separated:**
- On **STYLE FIDELITY** (char_acc, DINOv2) the glyph model wins decisively — that was its whole design purpose, conditioning on letterform templates to fix structure.
- On **IDENTITY** (is it the right letter) the **baseline is significantly better** — but by 0.0032, i.e. **18 cells out of 4400 (0.4%)**, with both models above 99.3%. Statistically clean (all 10 non-tied fonts favour the baseline, r=0.886), practically negligible.

This is a case where statistical significance and practical significance diverge sharply, and both should be reported. A one-line "the glyph model wins" claim would be wrong; so would "the baseline has better identity, therefore it's better."

**Fair summary for the README:** *glyph-cond + disambiguated template beats the structured baseline on style fidelity (char_acc +0.024, p=0.016, r=0.353; DINOv2 +0.030, r=0.768) while both models sit at >99.3% letter identity — the baseline holding a statistically-real but practically-negligible 0.3pp identity edge.*

**Caveat on my own earlier framing in this document:** the section above records the char_acc gate pass as upgrading the project's headline claim. That stands, but it is incomplete without this table — the glyph model is not uniformly better, and the identity metric this project itself elevated as "the one that matters" slightly favours the baseline.
