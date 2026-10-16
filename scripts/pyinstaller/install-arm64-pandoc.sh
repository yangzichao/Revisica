#!/usr/bin/env bash
# Replace the pandoc binary inside the active venv's `pypandoc` package with
# the official arm64 build from jgm/pandoc.
#
# Every `pypandoc-binary` wheel tagged macosx_11_0_arm64 (checked 1.13
# through 1.17) ships an x86_64 pandoc. On a Mac without Rosetta it fails
# with "Bad CPU type in executable", and .tex ingestion silently falls back
# to tex-basic. PyInstaller collects pypandoc/files/pandoc as-is, so the
# swap has to happen in the venv before freezing.
#
# The version matches what pypandoc-binary 1.17 bundles (pandoc 3.9), so only
# the architecture changes. The SHA-256 is the asset digest GitHub reports
# for the release download.
#
# Usage (with the build venv active):
#   bash scripts/pyinstaller/install-arm64-pandoc.sh

set -euo pipefail

PANDOC_VERSION="3.9"
PANDOC_ARM64_ZIP_SHA256="7d56ac6fe6fad0a7407bcd776aa142f61ca41838f286165f79d0584fa57b24d1"
PANDOC_ARM64_ZIP_URL="https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-arm64-macOS.zip"

pypandoc_pandoc_path=$(python -c '
import importlib.util, pathlib
spec = importlib.util.find_spec("pypandoc")
if spec is None:
    raise SystemExit("pypandoc is not installed in this environment")
print(pathlib.Path(spec.origin).parent / "files" / "pandoc")
')

download_dir=$(mktemp -d)
trap 'rm -rf "$download_dir"' EXIT

echo "▶ downloading pandoc ${PANDOC_VERSION} (arm64)"
curl -fsSL -o "$download_dir/pandoc.zip" "$PANDOC_ARM64_ZIP_URL"
echo "${PANDOC_ARM64_ZIP_SHA256}  $download_dir/pandoc.zip" | shasum -a 256 -c -
unzip -q "$download_dir/pandoc.zip" -d "$download_dir"

arm64_pandoc="$download_dir/pandoc-${PANDOC_VERSION}-arm64/bin/pandoc"
if [[ "$(lipo -archs "$arm64_pandoc")" != *arm64* ]]; then
  echo "ERROR: $arm64_pandoc is not an arm64 binary" >&2
  exit 1
fi

mkdir -p "$(dirname "$pypandoc_pandoc_path")"
install -m 0755 "$arm64_pandoc" "$pypandoc_pandoc_path"
echo "▶ $("$pypandoc_pandoc_path" --version | head -n 1) installed at $pypandoc_pandoc_path"
