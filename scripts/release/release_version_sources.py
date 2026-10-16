"""Every file that records Revisica's release version, and how to read or write it.

The Python package and the desktop app each have one source of truth:
``src/revisica/__init__.py`` (pyproject.toml reads it) and
``desktop/package.json`` (the renderer reads it at build time). The npm
lockfile mirrors the desktop version in two places. A release tag ``vX.Y.Z``
must match all of them.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PYTHON_VERSION_FILE = Path("src/revisica/__init__.py")
DESKTOP_PACKAGE_FILE = Path("desktop/package.json")
DESKTOP_LOCK_FILE = Path("desktop/package-lock.json")

# MAJOR.MINOR.PATCH with an optional -alpha.N / -beta.N / -rc.N suffix. Both
# npm (semver) and pip (PEP 440, after normalization) accept this shape.
RELEASE_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:-(?:alpha|beta|rc)\.\d+)?$")

_PYTHON_VERSION_LINE = re.compile(r'^__version__ = "([^"]+)"$', re.MULTILINE)


def is_valid_release_version(version: str) -> bool:
    return RELEASE_VERSION_PATTERN.fullmatch(version) is not None


def read_recorded_versions(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    """Map each version-bearing location to the version it records."""
    python_source = (repo_root / PYTHON_VERSION_FILE).read_text(encoding="utf-8")
    python_matches = _PYTHON_VERSION_LINE.findall(python_source)
    if len(python_matches) != 1:
        raise ValueError(
            f"{PYTHON_VERSION_FILE}: expected exactly one `__version__ = \"...\"` line, "
            f"found {len(python_matches)}"
        )

    desktop_package = _read_json(repo_root / DESKTOP_PACKAGE_FILE)
    desktop_lock = _read_json(repo_root / DESKTOP_LOCK_FILE)
    return {
        str(PYTHON_VERSION_FILE): python_matches[0],
        str(DESKTOP_PACKAGE_FILE): desktop_package["version"],
        str(DESKTOP_LOCK_FILE): desktop_lock["version"],
        f'{DESKTOP_LOCK_FILE} packages[""]': desktop_lock["packages"][""]["version"],
    }


def write_release_version(new_version: str, repo_root: Path = REPO_ROOT) -> None:
    """Set every version-bearing location to ``new_version``."""
    if not is_valid_release_version(new_version):
        raise ValueError(
            f"{new_version!r} is not a release version (expected X.Y.Z or X.Y.Z-rc.N)"
        )

    python_path = repo_root / PYTHON_VERSION_FILE
    python_source = python_path.read_text(encoding="utf-8")
    updated_source, replacement_count = _PYTHON_VERSION_LINE.subn(
        f'__version__ = "{new_version}"', python_source,
    )
    if replacement_count != 1:
        raise ValueError(
            f"{PYTHON_VERSION_FILE}: expected exactly one `__version__ = \"...\"` line, "
            f"found {replacement_count}"
        )
    python_path.write_text(updated_source, encoding="utf-8")

    desktop_package = _read_json(repo_root / DESKTOP_PACKAGE_FILE)
    desktop_package["version"] = new_version
    _write_json_like_npm(repo_root / DESKTOP_PACKAGE_FILE, desktop_package)

    desktop_lock = _read_json(repo_root / DESKTOP_LOCK_FILE)
    desktop_lock["version"] = new_version
    desktop_lock["packages"][""]["version"] = new_version
    _write_json_like_npm(repo_root / DESKTOP_LOCK_FILE, desktop_lock)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json_like_npm(path: Path, payload: dict) -> None:
    # Matches npm's JSON.stringify(payload, null, 2) + "\n", so a version bump
    # only changes the version lines.
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
