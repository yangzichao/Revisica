#!/usr/bin/env bash
# Freeze the Revisica Python backend into a self-contained directory for the
# desktop DMG.
#
# Output: `desktop/resources/python-backend/` — consumed by electron-builder
# via `extraResources` and launched by `desktop/src/main/index.ts` in
# production.
#
# Usage:
#   bash scripts/build-python-backend.sh            # build into desktop/resources
#   REVISICA_BUILD_PY=python3.12 bash scripts/...   # pin interpreter
#   REVISICA_KEEP_BUILD_VENV=1 bash scripts/...     # skip venv recreate (faster)
#
# The build uses a dedicated `.build-venv` so stray packages from `.venv`
# cannot leak into the bundle. That venv is recreated every run unless
# REVISICA_KEEP_BUILD_VENV is set.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

BUILD_VENV="${REPO_ROOT}/.build-venv"
SPEC_FILE="${REPO_ROOT}/scripts/pyinstaller/python-backend.spec"
# PyInstaller writes dist/ and build/ *next to the spec file*, not the cwd.
DIST_DIR="${REPO_ROOT}/scripts/pyinstaller/dist/python-backend"
OUTPUT_DIR="${REPO_ROOT}/desktop/resources/python-backend"
PYINSTALLER_WORK="${REPO_ROOT}/scripts/pyinstaller/build"

# Prefer 3.12: langchain / langgraph / pydantic-core ship arm64 wheels for
# 3.11 and 3.12 on first-day releases; 3.13 wheels sometimes lag. Allow an
# override via REVISICA_BUILD_PY for CI or future migrations.
PY_BIN="${REVISICA_BUILD_PY:-}"
if [[ -z "$PY_BIN" ]]; then
  for candidate in python3.12 /opt/homebrew/bin/python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      PY_BIN="$candidate"
      break
    fi
  done
fi
if [[ -z "$PY_BIN" ]]; then
  echo "ERROR: no Python interpreter found. Set REVISICA_BUILD_PY." >&2
  exit 1
fi

py_version=$("$PY_BIN" -c "import sys; print('%d.%d' % sys.version_info[:2])")
echo "▶ build interpreter: $PY_BIN ($py_version)"

# ── 1. Build venv ─────────────────────────────────────────────────────────
if [[ -d "$BUILD_VENV" && "${REVISICA_KEEP_BUILD_VENV:-0}" != "1" ]]; then
  echo "▶ removing stale build venv"
  rm -rf "$BUILD_VENV"
fi
if [[ ! -d "$BUILD_VENV" ]]; then
  echo "▶ creating build venv"
  "$PY_BIN" -m venv "$BUILD_VENV"
fi
# shellcheck source=/dev/null
source "$BUILD_VENV/bin/activate"

python -m pip install --quiet --upgrade pip wheel
echo "▶ installing revisica[all,bundle] + pyinstaller"
# `.[all]` pulls the api + serve extras; `.[bundle]` adds pypandoc-binary.
pip install --quiet -e ".[all,bundle]"
pip install --quiet "pyinstaller>=6.5"

# ── 2. Clean previous build artifacts ────────────────────────────────────
echo "▶ cleaning previous outputs"
rm -rf "$DIST_DIR" "$PYINSTALLER_WORK" "$OUTPUT_DIR"

# ── 3. Run PyInstaller ───────────────────────────────────────────────────
echo "▶ running pyinstaller"
# `--distpath` and `--workpath` are resolved relative to the spec's dir, so
# use absolute paths to keep behavior stable.
pyinstaller \
  --noconfirm \
  --distpath "${REPO_ROOT}/scripts/pyinstaller/dist" \
  --workpath "${PYINSTALLER_WORK}" \
  "$SPEC_FILE"

if [[ ! -x "$DIST_DIR/python-backend" ]]; then
  echo "ERROR: PyInstaller did not produce $DIST_DIR/python-backend" >&2
  exit 1
fi

# ── 4. Copy into desktop/resources ───────────────────────────────────────
echo "▶ copying to $OUTPUT_DIR"
mkdir -p "$(dirname "$OUTPUT_DIR")"
# `cp -R` preserves the onedir layout. Use `--reflink=auto` on Linux for
# speed; skip on macOS (APFS clone is automatic).
cp -R "$DIST_DIR" "$OUTPUT_DIR"

# ── 5. Sanity check: report size and presence of pandoc ──────────────────
bundle_size=$(du -sh "$OUTPUT_DIR" | awk '{print $1}')
echo "▶ bundle size: $bundle_size"

if find "$OUTPUT_DIR" -name "pandoc*" -print -quit | grep -q .; then
  echo "▶ bundled pandoc: present"
else
  echo "⚠ bundled pandoc: NOT FOUND — re-check pypandoc_binary collect_data_files" >&2
fi

echo "✔ frozen backend ready at $OUTPUT_DIR"
echo "  next: bash scripts/smoke-test-python-backend.sh"
