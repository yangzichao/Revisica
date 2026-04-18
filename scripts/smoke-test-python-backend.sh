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

# ── 1. Health check within 5 s ────────────────────────────────────────────
echo "▶ waiting for $BASE/api/health"
for attempt in $(seq 1 10); do
  if curl -sf "${AUTH[@]}" "$BASE/api/health" >/dev/null 2>&1; then
    echo "  ok ($((attempt * 500)) ms)"
    break
  fi
  sleep 0.5
  if [[ "$attempt" -eq 10 ]]; then
    echo "ERROR: backend did not come up. Log:" >&2
    cat "$LOG" >&2
    exit 1
  fi
done

# ── 2. Ingest a .md fixture ──────────────────────────────────────────────
# Request schema: `{"file_path": "...", "parser": "auto"}` — see IngestRequest
# in src/revisica/api.py. Using the wrong key returns 422 and masks whatever
# real bug the smoke test was meant to catch.
MD_FIXTURE="${REPO_ROOT}/tests/fixtures/sample_paper.md"
if [[ -f "$MD_FIXTURE" ]]; then
  echo "▶ ingest .md"
  resp=$(curl -sf "${AUTH[@]}" -X POST "$BASE/api/ingest" \
    -H 'Content-Type: application/json' \
    -d "{\"file_path\": \"$MD_FIXTURE\"}")
  if echo "$resp" | grep -q '"parser_used"[[:space:]]*:[[:space:]]*"markdown"'; then
    echo "  ok (parser_used=markdown)"
  else
    echo "ERROR: markdown ingest returned unexpected payload: $resp" >&2
    exit 1
  fi
fi

# ── 3. Ingest a .tex fixture — exercises bundled pandoc ──────────────────
TEX_FIXTURE="${REPO_ROOT}/examples/minimal_paper.tex"
if [[ -f "$TEX_FIXTURE" ]]; then
  echo "▶ ingest .tex (pandoc path)"
  resp=$(curl -sf "${AUTH[@]}" -X POST "$BASE/api/ingest" \
    -H 'Content-Type: application/json' \
    -d "{\"file_path\": \"$TEX_FIXTURE\"}")
  if echo "$resp" | grep -q '"parser_used"[[:space:]]*:[[:space:]]*"pandoc"'; then
    echo "  ok (parser_used=pandoc)"
  else
    echo "ERROR: pandoc ingest returned unexpected payload: $resp" >&2
    exit 1
  fi
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
