#!/bin/bash
# Caption A/B probe: test if Qwen3 text encoder responds to style descriptors.
# 4 prompt variants × 3 reference fonts = 12 renders on existing best checkpoint.
set -e
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root

CKPT="experiments/20260412-215340_Kg_structured_prompt_5000/checkpoints/checkpoint-5000"
OUT="experiments/caption_probe"
mkdir -p "$OUT"

declare -A PREFIXES
PREFIXES["A_control"]=""
PREFIXES["B_match"]="A regular serif typeface."
PREFIXES["C_clash"]="A thin script handwriting font."
PREFIXES["D_null"]="abc xyz qrs."

declare -A FONTS
FONTS["times"]="C:/Windows/Fonts/times.ttf"
FONTS["arial"]="C:/Windows/Fonts/arial.ttf"
FONTS["consol"]="C:/Windows/Fonts/consola.ttf"

for variant in A_control B_match C_clash D_null; do
  for fontname in times arial consol; do
    out_path="$OUT/${fontname}_${variant}.png"
    if [ -f "$out_path" ]; then
      echo "SKIP $out_path (exists)"
      continue
    fi
    echo "=== $fontname / $variant ==="
    python pipeline/render_checkpoint.py "$CKPT" \
      --out "$out_path" \
      --reference-chars Kg \
      --reference-font "${FONTS[$fontname]}" \
      --steps 20 \
      --seed 42 \
      --prompt-prefix "${PREFIXES[$variant]}" 2>&1 | grep -E "Saved|Generating"
  done
done

echo "All done. Outputs in $OUT/"
