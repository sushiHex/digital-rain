#!/usr/bin/env bash
# Matched multi-seed 4B vs 9B on the 50-font holdout: 6 inference seeds each.
#
# WHY, in one line: the headline gap is 1.2 SE. `analysis/seed_variance.py`
# decomposes four same-model 4B seeds and finds the SEED MAIN EFFECT (SD 0.0248)
# is 91% of a run's holdout-mean variance and does NOT average out across fonts,
# so a single-seed A/B carries SE ~0.037 against an observed 0.0457 char_acc
# gap. compare_runs' p=0.0001 pairs by FONT and is structurally blind to that
# term. 6 seeds/model takes the gap to ~3.1 SE (86% power on the main effect,
# 90% on the difficulty interaction).
#
# Reuses the four seeds already in bestofn_4b/ -- candidate_gen skips any
# candidate whose PNG exists -- so the 4B arm only generates seeds 4 and 5.
#
# Cost, from the two prior run logs (NOT symmetric; the 9B is ~2x slower):
#   4B  ~65 s/atlas  ->  100 new atlases ~ 1.8 h
#   9B ~119 s/atlas  ->  300 new atlases ~ 9.9 h
#   total ~11.7 h + scoring
#
# Both arms use the shipped eval conditioning: candidate_gen derives
# prompt_style/reference_chars from each checkpoint (f93b233) and uses the
# disambig-mild template, matching eval_checkpoint's protocol. The pre-fix
# 9B candidates in dpo_holdout_bestofn/ are mis-conditioned and are NOT reused.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root
MARKER=${MARKER:-MULTISEED}
rm -f "${MARKER}_DONE" "${MARKER}_FAIL"

SEEDS=${SEEDS:-6}
LOG=${LOG:-multiseed_4b_vs_9b.log}
GATE_MB=${GATE_MB:-12000}

OUT_4B=${OUT_4B:-bestofn_4b}
CKPT_4B=${CKPT_4B:-training_glyph_4b_r32_5000/final}
BASE_4B=${BASE_4B:-black-forest-labs/FLUX.2-klein-base-4B}

OUT_9B=${OUT_9B:-bestofn_9b}
CKPT_9B=${CKPT_9B:-training_glyph_r32_5000/final}
BASE_9B=${BASE_9B:-black-forest-labs/FLUX.2-klein-base-9B}

fail() { echo "=== MULTISEED FAIL at $1 (exit $2) @ $(date '+%H:%M:%S') ==="; \
         echo "$1 exit=$2" > "${MARKER}_FAIL"; exit 1; }

gate() {
  echo "=== waiting for >=${GATE_MB}MB free VRAM @ $(date '+%H:%M:%S') ==="
  free=0
  for i in $(seq 1 960); do   # up to 8h; the 9B arm can queue behind other work
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1)
    free=${free:-0}
    [ "$free" -ge "$GATE_MB" ] && break
    [ $((i % 20)) -eq 0 ] && echo "  waiting: ${free}MB free @ $(date '+%H:%M:%S')"
    sleep 30
  done
  [ "$free" -ge "$GATE_MB" ] || return 1
  echo "=== gate passed: ${free}MB free @ $(date '+%H:%M:%S') ==="
}

arm() {   # arm <label> <out> <ckpt> <base>
  echo "=== [$1] ${SEEDS} seeds -> $2 @ $(date '+%H:%M:%S') ==="
  gate || fail "vram_gate_$1" 1
  python candidate_gen.py --fonts-manifest eval_holdout/manifest.json \
    --out-dir "$2" --models glyph --glyph-seeds "$SEEDS" --steps 20 \
    --glyph-checkpoint "$3" --base-model "$4" || fail "candidate_gen_$1" $?
  echo "=== [$1] scoring against holdout GT @ $(date '+%H:%M:%S') ==="
  python score_candidates.py --candidates-dir "$2/candidates" \
    --gt-atlas-dir eval_holdout/atlases --out "$2/scores.json" \
    || fail "score_$1" $?
  echo "=== [$1] per-seed summary @ $(date '+%H:%M:%S') ==="
  python analysis/analyze_holdout_bestofn.py "$2/scores.json" || fail "analyze_$1" $?
}

{
  # 4B first: it is the short arm and tops up an existing directory, so a
  # failure there is cheap to diagnose before committing ~10h to the 9B.
  arm 4B "$OUT_4B" "$CKPT_4B" "$BASE_4B"
  arm 9B "$OUT_9B" "$CKPT_9B" "$BASE_9B"

  echo "=== variance decomposition, both arms @ $(date '+%H:%M:%S') ==="
  python analysis/seed_variance.py "$OUT_4B/scores.json" || true
  python analysis/seed_variance.py "$OUT_9B/scores.json" || true

  echo "=== MULTISEED DONE @ $(date '+%H:%M:%S') ==="
  echo "ok" > "${MARKER}_DONE"
} >> "$LOG" 2>&1
