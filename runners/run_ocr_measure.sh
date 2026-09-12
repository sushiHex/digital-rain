#!/usr/bin/env bash
# Detached runner for the focused OCR symbol measurement. Marker: OCR_MEASURE_DONE.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f OCR_MEASURE_DONE
python studies/measure_ocr_symbols.py > run_ocr_measure.log 2>&1
echo "exit=$?" > OCR_MEASURE_DONE
