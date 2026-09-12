# Training-loop audit: three confirmed defects that training loss cannot show

2026-08-08. Adversarial audit of `train_lora_kg.py` (codex, max effort), with
every load-bearing claim re-verified locally before acceptance. The loop had
never been reviewed, and it produced every checkpoint in the project.

The audit's framing question was the right one: *which defect would most
plausibly have degraded every checkpoint without appearing in the loss curve?*
This project has twice been bitten by exactly that shape — the −27% hairline
collapse and the +15% over-ink, both with healthy loss.

**Sound, and worth recording as sound:** the flow-matching target
(`noise - atlas_latents` against `x_σ = (1-σ)x + σε`) and its sign against the
scheduler; the channel-concat ordering, identical between training and the
inference hook; the zero-init of the widened `x_embedder`'s new 128 columns;
its serialization through `modules_to_save` (verified by opening the
safetensors — `[3072,256]` on the 4B, `[4096,256]` on the 9B, new half
non-zero); and the distinctiveness sampler's weights against all 925 stems.

## 1. The LR schedule never anneals — CONFIRMED, and universal

`global_step` increments once per **microbatch** (`train_lora_kg.py:601`), but
the optimizer and LR scheduler step only on the accumulation boundary
(`train_lora_kg.py:585`). The cosine schedule, however, uses `args.steps` as
its horizon in **optimizer-step** units (`train_lora_kg.py:415`).

Every run in the repo uses `batch_size=1, grad_accum=2, steps=5000`:

| intended | actual |
|---|---|
| 5,000 optimizer updates | **2,500** |
| cosine decays to ~0 | stops at **51.6% of peak** |
| warmup 100 updates | 100 updates = 200 logged steps |
| `checkpoint-1000` = 1,000 updates | **500** updates |

Derived from the schedule: `progress = (2500-100)/(5000-100) = 0.4898`, giving
a final LR of `1e-4 × 0.5(1+cos(π·0.4898))` = **5.1603e-05**. The training log's
last recorded LR is **5.16e-05** (`glyph_4b.log`). Exact match — this is not an
inference, it is arithmetic that reproduces the observed value.

**A declining loss curve is fully compatible with this.** The model simply
never gets its annealing phase.

**It does not invalidate any A/B in this repo** — `training_glyph_r32_5000`,
`training_glyph_4b_r32_5000` and `training_glyph_4b_r64_5000` all carry the
identical `steps/accum/warmup`, so every arm was handicapped equally. What it
means is that there is likely **unclaimed quality in every checkpoint**, which
is more interesting than any lever tried so far: the levers moved composite by
~0.003, and a schedule that actually finishes is a bigger intervention than
that.

## 2. The SNR loss weighting is a no-op — CONFIRMED

`compute_snr_weights` normalizes by the batch mean:

    weights = (1.0 - sigmas.clamp(max=0.999)) ** (-2.0)
    weights = weights / weights.mean()

With `batch_size=1` the tensor has one element, so `w / mean(w) == 1.0`
identically. Gradient accumulation does not help — normalization happens per
microbatch. **The actual objective in every checkpoint is unweighted velocity
MSE**, not the SNR-weighted loss the docstring advertises.

The audit adds a second point I have *not* independently verified against the
cited paper: that under this code's σ convention (σ = noise fraction),
`(1-σ)^-2` upweights **high**-noise samples, the opposite of the docstring's
stated intent, and an SNR-equivalent multiplier would go as `(1-σ)^2`. Flagged,
not accepted — the sign convention needs checking against arXiv 2603.06454
before anyone acts on it.

Related and also unverified by me: logit-normal timestep sampling
(`sigmoid(N(0,1))`) puts only ~0.16% of draws below σ=0.05 — about 8 samples in
a 5,000-microbatch run — while a 20-step inference trajectory does evaluate that
endpoint. Plausible mechanism for weak final-detail correction that barely moves
aggregate loss. Unmeasured.

## 3. Template drift, invisible to the conditioning validator — CONFIRMED, FIXED

The checkpoints record `dataset_v2\cache\template.pt`. The standard eval path
(`run_glyph_4b_r32.sh`) passes `template_disambig_mild.pt`. Measured directly:

| | |
|---|---|
| elements differing | **79.93%** |
| RMS difference | 0.05061 |
| RMS of the template itself | 0.73838 |
| cosine similarity | **0.997589** |

So it is a **mild perturbation** (~7% relative RMS), not a different
conditioning — "disambig-mild" is doing what its name says. But
`check_eval_conditioning` compared prompt style and reference chars and **never
looked at the template at all**, so an eval could print *"conditioning OK: eval
matches training"* while feeding a tensor that differs in four fifths of its
elements.

That is the same class of silent drift as the prompt-style mismatch, which cost
IDENTITY 0.9936 → 0.9780 with all 50 fonts worse *while char_acc barely moved* —
precisely the regression shape this project's headline metric is blind to.

**Fixed**: the validator now takes `template_pt` and reports drift;
`eval_checkpoint` passes the template it is actually using. Reported as a NOTE
rather than a `--strict-conditioning` failure, because the impact is unmeasured
and gating on it would break every existing eval command. `tests/test_conditioning_template_drift.py`
pins it, including the backslash/forward-slash equivalence.

## Also reported, not yet verified by me

- **qint8 train / qfloat8 infer** — already known and documented in CLAUDE.md.
  The audit ranks it the top silent risk, since it is universal through
  `load_generation_pipe` and cannot appear in training loss.
- **Resume is not reproducible.** RNG, sampler position and pending gradients
  are not persisted, and the metrics file is opened in write mode *before*
  resume handling, truncating the prior loss curve and hiding the discontinuity.
- **No provenance.** `from_pretrained` without a revision; the latent cache
  records dimensions but not model revision, VAE hash or Diffusers version;
  `requirements.txt` is lower bounds, not a lockfile. The historical 9B
  scheduler/VAE identity cannot be reconstructed from a checkpoint.
- **`replacement=True` sampling** means a nominal 925-draw epoch touches only
  ~559 distinct fonts. Correct for maintaining the weighting; worth knowing.
- A correction to my own framing: `--rank` defaults to **16**, not 32.

## What to do

Fixing (1) and (2) changes the training semantics of every future run and
breaks comparability with all 180-odd commits of prior results. **That is a
call for the project owner, not a quiet patch** — the options are to fix and
re-baseline, or to pin the current behaviour and document it as the definition.

My recommendation is to fix (1) only, and re-run the 4B r32 baseline: it is a
single ~5 h run, it is the one defect with a clean prediction attached (the
model has never had an annealing phase), and it would be measured against a
holdout comparison that is now six-seed and can actually resolve a difference
of the size at stake.
