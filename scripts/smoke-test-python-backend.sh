#!/usr/bin/env bash
# Smoke-test the PyInstaller-frozen backend as a standalone process — no
# venv, no PYTHONPATH, no Electron wrapper. Mirrors the acceptance criteria
# in `docs/specs/dmg-packaging.md`.
#
# Run this BEFORE wiring the frozen binary into Electron. Failures here
# surface hidden-import gaps that the dev-mode run never exercises.
#
# Usage: bash scripts/smoke-test-python-backend.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="${REPO_ROOT}/desktop/resources/python-backend/python-backend"
PORT="${REVISICA_SMOKE_PORT:-18999}"
BASE="http://127.0.0.1:${PORT}"
TMP_DIR=$(mktemp -d)
LOG="$TMP_DIR/backend.log"

if [[ ! -x "$BACKEND" ]]; then
  echo "ERROR: $BACKEND not found. Run scripts/build-python-backend.sh first." >&2
  exit 1
fi

# Run the frozen binary with a *minimal* env — PATH without Homebrew, no
# PYTHONPATH, no PYTHONHOME — so any dev-venv leakage surfaces here rather
# than on a user's machine.
env -i \
  HOME="$TMP_DIR/home" \
  TMPDIR="$TMP_DIR" \
  PATH="/usr/bin:/bin" \
  REVISICA_API_TOKEN="smoke-test-token" \
  "$BACKEND" --port "$PORT" >"$LOG" 2>&1 &
BACKEND_PID=$!

cleanup() {
  if kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
    sleep 1
    kill -9 "$BACKEND_PID" 2>/dev/null || true
  fi
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

# `api.py` uses `Authorization: Bearer <token>` (see require_api_token).
# `/api/health` is unauthenticated, but /api/ingest + /api/review require
# the bearer header.
AUTH=(-H "Authorization: Bearer smoke-test-token")

# ── 1. Health check within 30 s ───────────────────────────────────────────
# Warm starts take 1-2 s. The first launch of a freshly built bundle has
# taken longer than 5 s locally, so the budget leaves room for that.
echo "▶ waiting for $BASE/api/health"
for attempt in $(seq 1 60); do
  if curl -sf "${AUTH[@]}" "$BASE/api/health" >/dev/null 2>&1; then
    echo "  ok (~$((attempt * 500)) ms)"
    break
  fi
  sleep 0.5
  if [[ "$attempt" -eq 60 ]]; then
    echo "ERROR: backend did not come up within 30 s. Log:" >&2
    cat "$LOG" >&2
    exit 1
  fi
done

# Ingest is asynchronous: POST /api/ingest returns a run_id, a worker thread
# parses the file, and /api/results/{run_id} serves the parsed document once
# /api/status/{run_id} reports "completed". The `|| true` on each lookup
# keeps `set -e` from exiting on a failed request before the explicit error
# messages below can report it.
json_field() {
  python3 -c 'import json, sys; print(json.load(sys.stdin).get(sys.argv[1], ""))' "$1"
}

ingest_and_expect_parser() {
  local fixture="$1"
  local expected_parser="$2"
  local run_id run_state parser_used

  run_id=$(curl -sf "${AUTH[@]}" -X POST "$BASE/api/ingest" \
    -H 'Content-Type: application/json' \
    -d "{\"file_path\": \"$fixture\"}" | json_field run_id) || true
  if [[ -z "$run_id" ]]; then
    echo "ERROR: /api/ingest returned no run_id for $fixture" >&2
    exit 1
  fi

  run_state=""
  for _ in $(seq 1 120); do
    run_state=$(curl -sf "${AUTH[@]}" "$BASE/api/status/$run_id" | json_field state) || true
    if [[ "$run_state" == "completed" || "$run_state" == "failed" ]]; then
      break
    fi
    sleep 0.5
  done
  if [[ "$run_state" != "completed" ]]; then
    echo "ERROR: parse run $run_id for $fixture ended as '${run_state:-unknown}'" >&2
    curl -s "${AUTH[@]}" "$BASE/api/status/$run_id" >&2 || true
    echo >&2
    tail -50 "$LOG" >&2
    exit 1
  fi

  parser_used=$(curl -sf "${AUTH[@]}" "$BASE/api/results/$run_id" | json_field parser_used) || true
  if [[ "$parser_used" != "$expected_parser" ]]; then
    echo "ERROR: $fixture parsed with '$parser_used', expected '$expected_parser'" >&2
    exit 1
  fi
  echo "  ok (parser_used=$parser_used)"
}

# ── 2. Ingest a .md fixture ──────────────────────────────────────────────
# Request schema: `{"file_path": "...", "parser": "auto"}` — see IngestRequest
# in src/revisica/api.py. Using the wrong key returns 422 and masks whatever
# real bug the smoke test was meant to catch.
MD_FIXTURE="${REPO_ROOT}/tests/fixtures/sample_paper.md"
if [[ -f "$MD_FIXTURE" ]]; then
  echo "▶ ingest .md"
  ingest_and_expect_parser "$MD_FIXTURE" markdown
fi

# ── 3. Ingest a .tex fixture — exercises bundled pandoc ──────────────────
TEX_FIXTURE="${REPO_ROOT}/examples/minimal_paper.tex"
if [[ -f "$TEX_FIXTURE" ]]; then
  echo "▶ ingest .tex (pandoc path)"
  ingest_and_expect_parser "$TEX_FIXTURE" pandoc
fi

# ── 4. Kick off a review — must not crash with ModuleNotFoundError ───────
if [[ -f "$MD_FIXTURE" ]]; then
  echo "▶ /api/review kickoff"
  resp=$(curl -sf "${AUTH[@]}" -X POST "$BASE/api/review" \
    -H 'Content-Type: application/json' \
    -d "{\"file_path\": \"$MD_FIXTURE\"}" || true)
  # The call may legitimately fail (missing provider keys) but must not
  # crash the server; so we accept any JSON response with a status field.
  if echo "$resp" | grep -qE '"(run_id|status|error|detail)"'; then
    echo "  ok"
  else
    echo "ERROR: /api/review returned non-JSON or crashed: $resp" >&2
    echo "--- backend log ---" >&2
    tail -50 "$LOG" >&2
    exit 1
  fi
fi

# ── 5. Scan log for ModuleNotFoundError (hidden-import holes) ────────────
if grep -q "ModuleNotFoundError" "$LOG"; then
  echo "ERROR: ModuleNotFoundError in backend log — widen hiddenimports." >&2
  grep "ModuleNotFoundError" "$LOG" >&2
  exit 1
fi

echo "✔ smoke test passed"
