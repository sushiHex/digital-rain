#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
rm -f GLYPH_CLF_DONE
python glyph_classifier.py --n-train 700 --n-val 60 --epochs 20 > run_glyph_clf.log 2>&1
echo "exit=$?" > GLYPH_CLF_DONE
