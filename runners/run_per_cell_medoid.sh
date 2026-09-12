#!/usr/bin/env bash
# Queued behind the non-oracle eval: per-cell medoid selection in DINOv2 space.
#
# Needs no generation and no training -- bestofn_4b/ already holds 6 seeds x 50
# fonts of generated atlases. The only GPU cost is DINOv2 embeddings, so this
# waits politely rather than competing with whatever is training.
set -u
cd "$(dirname "$0")/.." || exit 1   # runners live in runners/; work from the repo root

MARKER=${MARKER:-PERCELL}
WAIT_FOR=${WAIT_FOR:-NONORACLE_DONE}
WAIT_TIMEOUT=${WAIT_TIMEOUT:-28800}      # 8h
rm -f "${MARKER}_DONE" "${MARKER}_FAIL"

if [ -n "$WAIT_FOR" ]; then
  echo "=== waiting for $WAIT_FOR @ $(date '+%H:%M:%S') ==="
  waited=0
  while [ ! -f "$WAIT_FOR" ]; do
    if [ -f "${WAIT_FOR%_DONE}_FAIL" ]; then
      echo "=== predecessor FAILED; running anyway (independent analysis) ==="
      break
    fi
    if [ "$waited" -ge "$WAIT_TIMEOUT" ]; then
      echo "=== timed out waiting @ $(date '+%H:%M:%S') ==="
      echo "wait_timeout" > "${MARKER}_FAIL"; exit 1
    fi
    sleep 60
    waited=$((waited + 60))
  done
fi

echo "=== per-cell medoid @ $(date '+%H:%M:%S') ==="
python analysis/per_cell_medoid.py \
  --candidates "${CANDIDATES:-bestofn_4b/candidates}" \
  --out "${OUT:-research/per_cell_medoid.json}"
rc=$?
echo "=== per-cell medoid exit $rc @ $(date '+%H:%M:%S') ==="
[ "$rc" -eq 0 ] && echo ok > "${MARKER}_DONE" || echo "$rc" > "${MARKER}_FAIL"
exit $rc
