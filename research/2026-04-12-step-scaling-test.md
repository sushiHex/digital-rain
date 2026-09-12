# Inference Step Scaling Test

Tested 2026-04-12. Baseline checkpoint-3500 rendered at 20, 35, 50, 75 inference steps.

## Visual comparison (Times reference)

All 4 step counts produced visually identical Times-style atlases. No visible quality difference.

## Quantitative comparison (10 holdout fonts, 20 vs 50 steps)

Same checkpoint, same seed, only step count differs.

| Font | 20s composite | 50s composite | delta |
|------|--------------|--------------|-------|
| AkayaTelivigala-Regular | 0.7919 | 0.7791 | -0.013 |
| AlikeAngular-Regular | 0.8182 | 0.8374 | +0.019 |
| AveriaLibre-Regular | 0.8519 | 0.8518 | -0.000 |
| AveriaSansLibre-Regular | 0.8495 | 0.8649 | +0.015 |
| AveriaSerifLibre-Regular | 0.8559 | 0.8534 | -0.003 |
| BitcountGridDoubleInk | 0.6055 | 0.5891 | -0.016 |
| BitcountPropDoubleInk | 0.7272 | 0.7183 | -0.009 |
| Dangrek-Regular | 0.8545 | 0.8529 | -0.002 |
| EncodeSansSemiExpanded | 0.8406 | 0.8305 | -0.010 |
| FascinateInline-Regular | 0.7095 | 0.7021 | -0.007 |

**Mean delta: -0.0025** (50 steps slightly worse)
- Improved: 2 fonts
- Regressed: 5 fonts
- Stable: 3 fonts

## Conclusion

More inference steps does NOT help. The 26% char-acc failure rate is baked into the LoRA weights, not an inference budget issue. The model doesn't "know the right answer but runs out of time" — it genuinely hasn't learned the correct glyph-position mapping for ~36% of font-glyph combinations.

This rules out inference-time optimizations and points toward training-time changes (structured prompt, extended schedule).
