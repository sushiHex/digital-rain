# The 4B has the 9B's sampling headroom, and no selector can harvest it (2026-08-02)

**Question.** The 4B trails the 9B by 0.0457 char_acc (0.6460 vs 0.6917). That
is small next to the 9B's own best-of-4 sampling headroom (+0.1628), so the
quality may already be inside the 4B's sample distribution — a *selection*
problem, not a capacity problem. Does best-of-N plus a no-GT selector close the
gap on the Apache-2.0 path?

**Answer: the headroom is there, in full, and nothing available can harvest it.**

## The headroom replicates exactly

50-font holdout, 4 seeds, 20 steps, correctly conditioned (see the conditioning
note below).

| | seed spread | best seed | best-of-4 oracle | within-run headroom |
|---|---|---|---|---|
| 9B glyph | 0.6653–0.6738 | 0.6738 | 0.8366 | **+0.1628** |
| 4B glyph | 0.5770–0.6304 | 0.6304 | 0.7943 | **+0.1638** |

The 4B's recoverable headroom is **identical** to the 9B's — 3.6× its entire
deficit to the 9B. The premise was right: the quality is in the distribution.

## No selector can reach it

| selector | 9B capture | 4B capture |
|---|---|---|
| DINOv2 medoid | **+14.1%** | **−4.9%** |
| ref-anchor per-cell | 4.6% | 0.8% |
| hybrid medoid+ref (best lam) | 11.1% | −2.6% |
| ref-best-seed (font-level) | −10.2% | −17.0% |

On the 4B every selector lands at or below zero. **The 14.1% that motivated
this experiment is 9B-specific and does not transfer.**

### Why, and it is not just noise

The two runs differ in seed spread by 6×:

- 9B seeds span 0.0085 — all four are equally good, so per-cell mixing is
  nearly free and a weak per-cell signal can pay off.
- 4B seeds span 0.0534, and seed0 (0.6304) is the best by 0.0034 over seed3 and
  by 0.0534 over seed1. A per-cell selector must beat a lucky seed while
  drawing three quarters of its candidates from genuinely worse ones.

Against the operationally honest baseline — a *random* seed, which is what
production gets — medoid is positive on both:

| baseline | 9B | 4B |
|---|---|---|
| mean single seed | 0.6697 | 0.6072 |
| medoid best-of-4 | 0.6968 (+0.0271, 16.2% capture) | 0.6223 (**+0.0151**, 8.1% capture) |
| best single seed | 0.6738 | 0.6304 |

So medoid does work on the 4B — it beats a random seed by +0.0151. It just does
not beat the *best* seed, and it never approaches the 0.0457 gap.

## The number that closes the path

**4B medoid best-of-4 = 0.6223, against the 4B's shipped single-seed eval of
0.6460.**

Four times the inference cost, and the result is *worse* than generating one
atlas at seed 42. Best-of-N with any selector tested does not improve the
shipped 4B. **The path is closed with current selectors.**

This does not close best-of-N in principle: the oracle at 0.7943 sits well
above the 9B's shipped 0.6917, so a selector capturing even ~35% of the 4B's
headroom would beat the 9B outright. Nothing tested comes close, and the
remaining candidate (a learned per-cell predictor) is now the only one
`research/2026-08-02-reference-anchored-selection-fails.md` does not rule out.

## Two caveats, stated plainly

1. **The 9B dev candidates were mis-conditioned.** `candidate_gen.py` never
   passed `prompt_style`, silently using `load_generation_pipe`'s "structured"
   default while both glyph checkpoints train on "trained-short" (fixed in
   f93b233). The 9B columns above come from that pre-fix data; the 4B columns
   do not. So the **cross-model capture comparison (14.1% vs −4.9%) is
   confounded** and the 9B's absolute values are depressed relative to its
   shipped 0.6917. Every *within-run* number — the headroom, and every 4B
   result — is unaffected, because all arms of each run share candidates.
   Re-deriving the 9B arm cleanly costs ~4 h of GPU.
2. **Seed 42 is lucky on the 4B.** The shipped 0.6460 sits 0.039 above the mean
   of four fresh seeds (0.6072) — near the top of the observed spread. Seed 42
   was fixed a priori rather than chosen, so this is chance, not selection
   bias. But it means the 4B's headline number is optimistic by roughly the
   size of its gap to the 9B, and single-seed A/B on this model is even noisier
   than previously assumed.

## Artifacts

- `bestofn_4b/` (candidates, scores), `bestofn_4b.sh`
- `research/2026-08-02-selector-4b.json`, `research/2026-08-02-selector-dev-9b.json`
- `analysis/analyze_holdout_bestofn.py` — now reports within-run headroom and
  takes `--official-single-seed`; the 0.6883 comparison baseline used to be
  hardcoded to the 9B and was silently applied to the 4B run.
