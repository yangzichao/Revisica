"""The release version must agree everywhere it is recorded.

The release workflow refuses a tag whose version disagrees with any of these
files; this test catches the drift on every pull request instead.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RELEASE_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "release"


def _load_release_version_sources():
    module_spec = importlib.util.spec_from_file_location(
        "release_version_sources", _RELEASE_SCRIPTS_DIR / "release_version_sources.py",
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


release_version_sources = _load_release_version_sources()


def _copy_version_files(destination_root: Path) -> None:
    for relative_path in (
        release_version_sources.PYTHON_VERSION_FILE,
        release_version_sources.DESKTOP_PACKAGE_FILE,
        release_version_sources.DESKTOP_LOCK_FILE,
    ):
        target = destination_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(_REPO_ROOT / relative_path, target)


def test_recorded_versions_agree() -> None:
    recorded_versions = release_version_sources.read_recorded_versions()

    assert len(set(recorded_versions.values())) == 1, recorded_versions


def test_python_package_version_matches_recorded_version() -> None:
    import revisica

    recorded_versions = release_version_sources.read_recorded_versions()

    assert revisica.__version__ == recorded_versions["src/revisica/__init__.py"]


def test_rewriting_the_current_version_leaves_files_byte_identical(tmp_path: Path) -> None:
    _copy_version_files(tmp_path)
    current_version = release_version_sources.read_recorded_versions(tmp_path)[
        "desktop/package.json"
    ]

    release_version_sources.write_release_version(current_version, tmp_path)

    for relative_path in (
        release_version_sources.PYTHON_VERSION_FILE,
        release_version_sources.DESKTOP_PACKAGE_FILE,
        release_version_sources.DESKTOP_LOCK_FILE,
    ):
        assert (tmp_path / relative_path).read_bytes() == (_REPO_ROOT / relative_path).read_bytes()


def test_setting_a_version_changes_only_the_version_lines(tmp_path: Path) -> None:
    _copy_version_files(tmp_path)

    release_version_sources.write_release_version("9.8.7-rc.1", tmp_path)

    assert set(release_version_sources.read_recorded_versions(tmp_path).values()) == {"9.8.7-rc.1"}
    expected_changed_line_counts = {
        release_version_sources.PYTHON_VERSION_FILE: 1,
        release_version_sources.DESKTOP_PACKAGE_FILE: 1,
        release_version_sources.DESKTOP_LOCK_FILE: 2,
    }
    for relative_path, expected_count in expected_changed_line_counts.items():
        original_lines = (_REPO_ROOT / relative_path).read_text(encoding="utf-8").splitlines()
        updated_lines = (tmp_path / relative_path).read_text(encoding="utf-8").splitlines()
        assert len(original_lines) == len(updated_lines)
        changed_lines = [
            (before, after)
            for before, after in zip(original_lines, updated_lines)
            if before != after
        ]
        assert len(changed_lines) == expected_count, (relative_path, changed_lines)


@pytest.mark.parametrize("bad_version", ["v1.2.3", "1.2", "1.2.3.4", "1.2.3-dev", "1.2.3rc1", ""])
def test_malformed_versions_are_rejected(tmp_path: Path, bad_version: str) -> None:
    _copy_version_files(tmp_path)

    with pytest.raises(ValueError):
        release_version_sources.write_release_version(bad_version, tmp_path)


def test_check_script_accepts_the_matching_tag_and_rejects_others() -> None:
    check_script = _RELEASE_SCRIPTS_DIR / "check_release_version.py"
    recorded_version = release_version_sources.read_recorded_versions()["desktop/package.json"]

    matching_run = subprocess.run(
        [sys.executable, str(check_script), f"v{recorded_version}"],
        capture_output=True, text=True, check=False,
    )
    mismatched_run = subprocess.run(
        [sys.executable, str(check_script), "v999.0.0"],
        capture_output=True, text=True, check=False,
    )

    assert matching_run.returncode == 0, matching_run.stderr
    assert mismatched_run.returncode == 1
    assert "does not match" in mismatched_run.stderr
