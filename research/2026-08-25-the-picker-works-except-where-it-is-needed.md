# The picker works, except where it is needed most (2026-08-25)

**Registered primary passes: within-description spread is 0.518 of
between-description spread, permutation p = 0.0005.** Four seeds of one
description are a real choice. And the per-description column, registered as
descriptive, says something the headline hides: **spread is narrowest exactly
where the generator is known to fail.**

Tool: `analysis/within_prompt_diversity.py`, committed at `1d1b64d` **before**
the images were looked at. Data: `research/within_prompt_diversity.json`.
Figure: `viz/candidate_options.py`.

## Why it was blocking

The interface shows several candidates for one description and lets the user
pick and iterate. Nothing in this project had ever measured whether N seeds of
one description *differ*. Four near-identical candidates make the choice
meaningless and the whole design pointless — cheap to find out, and better found
before an interface is built on it.

`audit_diversity.py` measures the analogous thing for the model track and does
not transfer: it needs a ground-truth atlas, and the product has none.

## The primary

48 candidates, 12 descriptions, 4 seeds each. **48 usable of 48, none rejected.**

```
WITHIN  mean 1.302   n=72 pairs
BETWEEN mean 2.514   n=1056 pairs
RATIO   0.518        permutation p = 0.0005   (null mean 1.003)
BANDS   <0.15 collapse, >0.85 description not controlling style
```

Both registered failure modes are avoided. The description controls the style —
otherwise the ratio would sit near 1, where the null is — and the seeds still
move, which is what makes a picker worth building.

**A human-scale anchor, registered as descriptive:** the gate rejects a
reference whose *own two glyphs* sit more than 1.875 apart in this same space.
**15% of within-description pairs exceed that** — roughly one pair in seven is
as different as a pair the gate calls inconsistent. Real choice, not noise.

## The finding the average hides

| description | spread | recorded 2026-08-23 |
|---|---|---|
| an ultra-light hairline sans | **0.454** | reinterpreted as an outline |
| **a stencil sans with deliberate breaks** | **0.572** | **MISS — came back solid** |
| a heavy geometric sans serif | 0.679 | hit |
| a high-contrast didone | 0.844 | hit |
| a wedge-serif face, flared terminals | 0.897 | — |
| a wide low-contrast monospace | 0.916 | **MISS** |
| a rounded soft sans | 0.935 | hit |
| a humanist sans, open apertures | 1.034 | — |
| a condensed grotesque | 1.584 | hit |
| a chunky slab serif | 1.764 | hit |
| a heavy angular blackletter-influenced sans | 1.984 | — |
| **an inline face with a white stripe** | **3.960** | hit |

**An 8.7× range, and the two recorded misses sit at 0.572 and 0.916 — both in
the bottom half.** Four seeds of *"a stencil sans with deliberate breaks"*
produce four solid faces with no break anywhere.

**So re-rolling cannot rescue a prompt the model systematically misses.** That is
a real limit on options-and-iterate, and it was invisible in the headline: the
average passes while the specific case that motivated the entire adherence
programme is second-narrowest in the set.

The corollary is the useful half. Where the model *can* do the thing, it offers
genuine variety — inline at 3.960 gives four visibly different treatments to
choose between. **The picker amplifies capability; it does not create it.**

## What this does not establish

- **Diversity is not the same as useful options.** A description could score
  wide because the model is *unstable* rather than because it offers
  alternatives. The figure is the only check on that here, and it is an
  eyeball.
- **n=4 seeds, 12 descriptions, one backend, one step count.** The twelve
  prompts are mine and were written knowing what the model is good at.
- **The spread↔miss relationship is n=2 misses.** It is a striking pattern and
  it is two data points; the mechanism (a model that cannot draw a break draws
  the same non-break every time) is more convincing than the count.
- **No claim that 0.518 is a good number.** The bands were set to catch the two
  failure modes, not to grade the middle.

## A note on the run

The generation was contended twice on the shared 3090. Throughput fell from
1.3 s/step to 281 s/step at worst — one image took 2,937 s — and recovered both
times. Mean 168.2 s per image against the 25.4 s recorded on 2026-08-23; the
difference is contention, not the model.

**A process-management error is worth recording**: `TaskStop` killed the wrapper
shell and **not** the Python child, so a run I reported as stopped kept going
and kept holding the card. It finished, which is lucky rather than correct. Kill
by process, and verify, when a GPU is shared.

## Where this leaves the four steps

1. **`--n` on the candidate generator** — done. At `n=1` labels are unchanged so
   every cross-reference to the 2026-08-23 run still resolves.
2. **Within-prompt diversity** — done, above.
3. **Reference → atlas style transfer** — the last one, and it needs GPU.
4. **Reference-stage adherence** — done: 9/11, p=0.0327, exactly at the bar
   ([note](2026-08-25-two-glyphs-are-enough.md)).
