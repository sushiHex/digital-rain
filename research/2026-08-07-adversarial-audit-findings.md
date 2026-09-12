# Adversarial audit: what the headline claims actually say (2026-08-07)

Eight parallel adversarial reviews were dispatched at max reasoning effort
(Codex gpt-5.6-sol, repo mounted read-only). **Three returned; five hit a 900 s
timeout and one of those was refused outright** by a safety filter because the
pre-publication prompt asked it to scan for credentials — that reads as security
work. So this records 3 of 8 audits, not a clean sweep; the untouched areas are
listed at the end so nobody mistakes silence for a pass.

Every finding below was **re-verified locally before being accepted**. One was
rejected on verification; it is recorded too.

---

## 1. IDENTITY 0.9936 is not 94-class accuracy (CRITICAL — headline claim)

The README led with: *"I built a font-invariant single-glyph classifier
(94-class CNN) … The model produces the correct letter **99.4%** of the time."*

That inference does not hold. Reproduced with
`analysis/verify_identity_definitions.py` on the committed
`eval_runs/prompt_trained_short/per_cell.json`:

| definition | on the 4,400 gated cells | on all 4,700 |
|---|---|---|
| **exact 94-class** | **0.9355** | **0.9243** |
| case-insensitive | 0.9889 | 0.9785 |
| case + `EQUIV` (**the reported 0.9936**) | 0.9936 | 0.9879 |

Two transformations stand between "94-class CNN" and 99.4%:

1. **Lenient matching.** `identity_score.reads_as(..., lenient=True)` folds case,
   then `EQUIV` merges `0/o/O`, `1/l/L/i/I/|`, `5/s/S`, `2/z/Z`, `8/b/B`,
   `9/g/G`, `u/U/v/V`. Of the 284 exact disagreements, ~90% are relabelled
   correct by these two steps.
2. **A GT gate that removes the hard cells.** 300 of 4,700 are dropped because
   the classifier cannot read the *ground truth* glyph confidently. Those cells
   are materially harder — char_acc 0.4000 vs 0.7116, R-ACC 0.4833 vs 0.7445,
   LPIPS 0.2024 vs 0.1418 — so the gate lifts the number.

**Both steps are individually defensible.** An isolated `O` and `0` genuinely are
undecidable without word context, and a reader that cannot identify the GT glyph
cannot fairly judge the generation. What is not defensible is stacking them and
then describing the result as 94-class identity.

**The two-axis conclusion is untouched**: identity is 0.92–0.99 on every
definition against char_acc 0.69, so char_acc still is not measuring letter
correctness. Only the number's *description* was wrong. Corrected in
`README.md` and `CLAUDE.md`, with the tool committed so the table regenerates
rather than being trusted.

---

## 2. Training and inference use different quantizers (HIGH)

- `train_lora_kg.py:364` — `quantize(transformer, weights=qint8)` (INT8)
- `generation_lib.py:124` — `quantize(pipe.transformer, weights=qfloat8)` (FP8)

The adapter is trained against INT8-quantized weights and served against FP8
ones. `generation_lib`'s own comments call the FP8 path "INT8 (quanto
qfloat8)", and `README.md`, `CLAUDE.md` and `app.py` all advertised `qint8`.

Not changed, deliberately: every result in this repo was produced with this
combination, so they are internally consistent, and swapping the inference
quantizer now would invalidate the comparison set without measuring anything.
Recorded as a limitation instead.

---

## 3. A claim of mine that verification KILLED

The reviewer asserted, and I had written into `app.py`, its tests and a commit
message, that *"a LoRA trained on the 4B loads against the 9B without erroring
and produces silent garbage."*

**False.** Reading the adapter tensors directly:

| checkpoint | `x_embedder.weight` | a `lora_B.weight` |
|---|---|---|
| `training_glyph_4b_r32_5000` | (3072, 256) | (3072, 32) |
| `training_glyph_r32_5000` | (4096, 256) | (4096, 32) |

Different hidden dims, so crossing them raises a shape error — loud, not
silent. I asserted a mechanism without testing it and then wrote it into three
places as justification.

`resolve_base_model` still earns its keep, for the *right* reason: it resolves
the correct base instead of surfacing a shape traceback, and a
**dimension-compatible** mismatch — another revision, or a distilled variant of
the same size — would be genuinely silent. Corrected everywhere.

---

## 4. Provenance and caching hazards (HIGH, not yet fixed)

From the conditioning audit, each verified against source:

- **`--skip-existing` trusts any PNG already in `<out>/generated/`.** The
  filename is the only key; `scores.json` records the *current* CLI checkpoint,
  not the one that produced the images. `--skip-generate --checkpoint B` will
  happily score A's outputs as B.
- **`candidate_gen`'s cache key omits checkpoint, base, prompt, template and
  steps**, and its own comment says it skips a file "regardless of how it got
  there".
- **Conditioning metadata is mutable and inherited.** `train_config.json` /
  `conditioning.json` are written once per *run*, not per checkpoint, and
  rewritten on resume; `_search_dirs` walks upward, so a checkpoint nested under
  another run can inherit the wrong ancestor's record.
- **Unknown conditioning passes `--strict-conditioning`** — it is only a note.
- **Template contents are never hashed.** A same-shaped replacement is silent.
- **R-ACC's GT-OCR cache is keyed on model id + cell count only**, not on the
  holdout's identity or image hashes.

These are the highest-value fixes still outstanding. None has fired that we know
of, but several would be invisible if they had.

---

## What was NOT audited

Five dispatches returned nothing. Do not read this document as coverage of:

- **`audit-headline-claims`** — the sweep of every numeric claim in `research/`
- **`audit-font-output`** — `atlas_to_font`, glyph naming, OTF validity, and the
  spacing/kerning design
- **`audit-tests`** — which of the 122 tests would fail if their subject broke
- **`audit-prepublication`** — secrets, licence coherence, publish readiness
  (refused by a safety filter; needs rephrasing away from "scan for credentials")
- **`attack-strategy`** — where the project should go next

Re-dispatch these individually rather than in a batch of eight; the 900 s
timeout appears to bind under concurrency.
