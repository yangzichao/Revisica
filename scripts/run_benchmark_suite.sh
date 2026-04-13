#!/bin/bash
# ProcessBench benchmark suite: v3/v4 × Opus/Sonnet/Haiku
# Runs in pairs (2 parallel) to balance speed vs rate limiting.
#
# Usage:
#   ./scripts/run_benchmark_suite.sh
#
# Config:
#   CASES=50, per-case timeout=1200s, retry=20×10min

set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate

LIMIT=50
TIMEOUT=1200
SUITE=processbench
SPLIT=math
MODE=single-agent
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_DIR="benchmarks/runs/_suite_${TIMESTAMP}"
mkdir -p "$LOG_DIR"

echo "=== ProcessBench Benchmark Suite ==="
echo "Started: $(date)"
echo "Cases: $LIMIT, Timeout: ${TIMEOUT}s, Split: $SPLIT"
echo "Parallelism: 2"
echo "Log dir: $LOG_DIR"
echo ""

run_one() {
  local out_dir="$1" version="$2" reviewer="$3" label="$4"
  local RUN_DIR="benchmarks/runs/${out_dir}"
  local START_TIME=$(date +%s)

  echo "[START] $label  ($(date))"

  revisica benchmark-run \
    --suite "$SUITE" \
    --split "$SPLIT" \
    --limit "$LIMIT" \
    --mode "$MODE" \
    --reviewer "$reviewer" \
    --timeout-seconds "$TIMEOUT" \
    --agent-version "$version" \
    --output-dir "$RUN_DIR" \
    > "${LOG_DIR}/${out_dir}.log" 2>&1

  local END_TIME=$(date +%s)
  local DURATION=$((END_TIME - START_TIME))

  if [ -f "${RUN_DIR}/benchmark_summary.json" ]; then
    local ACC=$(python3 -c "
import json
d = json.load(open('${RUN_DIR}/benchmark_summary.json'))
acc = d.get('suite_metrics',{}).get('exact_first_error_accuracy','?')
p = d['aggregate']['passed']; c = d['aggregate']['cases']
print(f'{p}/{c} = {acc}')
")
    echo "[DONE]  $label  ${DURATION}s ($((DURATION/60))min)  => $ACC"
  else
    echo "[FAIL]  $label  ${DURATION}s ($((DURATION/60))min)  => no summary"
  fi
}

# ── Batch 1: v4-opus + v3-sonnet (different models, safe to parallel) ──
echo "── Batch 1/3 ──"
run_one "pb-v4-opus-${TIMESTAMP}"     v4 claude         "v4/opus"   &
run_one "pb-v3-sonnet-${TIMESTAMP}"   v3 claude:sonnet   "v3/sonnet" &
wait
echo ""

# ── Batch 2: v4-sonnet + v3-haiku ──
echo "── Batch 2/3 ──"
run_one "pb-v4-sonnet-${TIMESTAMP}"   v4 claude:sonnet   "v4/sonnet" &
run_one "pb-v3-haiku-${TIMESTAMP}"    v3 claude:haiku    "v3/haiku"  &
wait
echo ""

# ── Batch 3: v4-haiku (solo) ──
echo "── Batch 3/3 ──"
run_one "pb-v4-haiku-${TIMESTAMP}"    v4 claude:haiku    "v4/haiku"
echo ""

# ── Final comparison ──
echo "════════════════════════════════════════"
echo "Suite complete: $(date)"
echo ""
echo "=== COMPARISON ==="
python3 -c "
import json
from pathlib import Path

results = []
for run_dir in sorted(Path('benchmarks/runs').glob('pb-*-${TIMESTAMP}')):
    summary = run_dir / 'benchmark_summary.json'
    if not summary.exists():
        continue
    d = json.load(open(summary))
    ver = d.get('agent_version', '?')
    reviewer = d.get('roles', {}).get('reviewer', {})
    model = reviewer.get('model', '') if reviewer else ''
    provider = reviewer.get('provider', '') if reviewer else ''
    label = f'{provider}:{model}' if model else provider
    acc = d.get('suite_metrics', {}).get('exact_first_error_accuracy', '?')
    passed = d['aggregate']['passed']
    cases = d['aggregate']['cases']
    results.append((ver, label, passed, cases, acc))

print(f'{'Version':<8} {'Model':<16} {'Passed':>8} {'Accuracy':>10}')
print('-' * 45)
for ver, label, passed, cases, acc in results:
    print(f'{ver:<8} {label:<16} {passed:>4}/{cases:<4} {acc:>10}')
"
