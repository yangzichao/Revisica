# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Revisica Python backend.

Driven by `scripts/build-python-backend.sh`. Kept as a `.spec` rather than
inline CLI flags so the hidden-import widening — which always happens after
running the bundle on a clean machine and hitting a fresh ModuleNotFoundError —
stays reviewable in version control.

Rebuild after editing: `bash scripts/build-python-backend.sh`.
"""

import os
import pathlib

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# --- modules that PyInstaller's static analyzer misses ---------------------
#
# langgraph / langchain / pydantic-core route through lazy loaders and
# `if TYPE_CHECKING` imports. Pull the whole trees to avoid runtime
# ModuleNotFoundError. Adds ~30-40 MB but the alternative is whack-a-mole
# when users hit a codepath we didn't exercise locally.
_third_party_hidden = (
    # `langgraph.checkpoint` and `langgraph.prebuilt` are subpackages of
    # `langgraph`, so collecting `langgraph` covers them.
    collect_submodules("langgraph")
    + collect_submodules("langchain_core")
    + collect_submodules("langsmith")
    + collect_submodules("pydantic")
    + collect_submodules("pydantic_core")
)

# --- modules revisica imports via registry -----------------------------------
#
# The parser registry uses static `from ... import` at module load, so
# PyInstaller's analyzer traces them. Listing the leaves anyway so a future
# refactor that moves to dynamic import doesn't silently break the frozen
# build — the build fails loudly at bundle time instead.
_revisica_hidden = [
    "revisica.ingestion.markdown_parser",
    "revisica.ingestion.tex_parser",
    "revisica.ingestion.pandoc_parser",
    "revisica.ingestion.mineru_parser",
    "revisica.ingestion.mathpix_parser",
    # `marker_parser` is intentionally absent — the registry references it but
    # tolerates ImportError (see ADR 0001). Listing it here would fail the
    # PyInstaller analysis at build time.
]

# --- uvicorn auto-detected protocol / loop loaders --------------------------
_uvicorn_hidden = [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    # `uvicorn.loops.uvloop`, `uvicorn.protocols.http.httptools_impl`, and
    # `uvicorn.protocols.websockets.*` require optional wheels (uvloop,
    # httptools, websockets/wsproto) that are NOT in our dep graph. Uvicorn's
    # `auto` loaders pick h11 + the asyncio loop when those packages are
    # absent, so we only list the impls whose dependencies we ship.
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
]

hiddenimports = sorted(set(_third_party_hidden + _revisica_hidden + _uvicorn_hidden))

# --- data files -------------------------------------------------------------
datas = []
datas += collect_data_files("revisica")
datas += collect_data_files("langchain_core")

# Also pick up any *non-binary* data pypandoc ships (e.g. default templates)
# so that only the binary takes the `binaries` fast path below.
datas += [
    (src, dst)
    for src, dst in collect_data_files("pypandoc")
    if not os.path.basename(src).lower().startswith("pandoc")
]

# --- native binaries ---------------------------------------------------------
#
# The bundled pandoc executable lives at `<site-packages>/pypandoc/files/pandoc`.
# Listing it under `binaries` (not `datas`) matters for two reasons:
#   1. PyInstaller's binary pipeline preserves executability and runs otool on
#      macOS binaries, so any future codesign sweep treats it as something to
#      sign rather than as opaque data.
#   2. `pypandoc._ensure_pandoc_path` *runs* the binary to read `--version`.
#      If copy semantics strip +x, that check silently falls back to a path
#      that doesn't exist, and `.tex` ingestion dies on a clean Mac.
import pypandoc as _pypandoc_for_path   # resolved against the build venv
_pandoc_bin = pathlib.Path(_pypandoc_for_path.__file__).parent / "files" / "pandoc"
if not _pandoc_bin.is_file():
    raise FileNotFoundError(
        f"Expected pypandoc-binary wheel at {_pandoc_bin}. "
        "Run `pip install .[bundle]` before building."
    )
binaries = [(str(_pandoc_bin), "pypandoc/files")]

block_cipher = None


a = Analysis(
    ["python_backend_entry.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # These parsers are opt-in (users `pip install` them separately). Keep
        # them out of the bundle to avoid a ~2 GB PyTorch pull and the GPU
        # dependency chain.
        "mineru",
        "marker",
        "torch",
        "torchvision",
        "transformers",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="python-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,            # UPX breaks codesign on macOS
    console=True,         # prints to Electron stdout/stderr; users never see it
    disable_windowed_traceback=False,
    target_arch="arm64",
    codesign_identity=None,      # Signing is driven by electron-builder over
    entitlements_file=None,      # the whole .app — not by PyInstaller here.
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="python-backend",
)
