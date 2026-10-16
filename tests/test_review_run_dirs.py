"""Where review runs land when no output dir is given.

Before: always ``<cwd>/reviews``. The desktop backend runs with the app
bundle's Resources dir as cwd, so reviews were written inside
Revisica.app. Run dirs were also named to the second, so two runs of the
same paper started in the same second shared one directory.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from revisica.run_dir_helpers import REVIEWS_DIR_ENV_VAR, create_review_run_dir
from revisica.unified_review import review_unified


def test_reviews_dir_env_var_wins_over_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(REVIEWS_DIR_ENV_VAR, str(tmp_path / "user-data" / "reviews"))

    run_dir = create_review_run_dir("paper-unified")

    assert run_dir.parent == tmp_path / "user-data" / "reviews"
    assert not (tmp_path / "reviews").exists()


def test_cli_default_is_still_cwd_reviews(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(REVIEWS_DIR_ENV_VAR, raising=False)

    assert create_review_run_dir("paper-math").parent == tmp_path / "reviews"


def test_runs_started_in_the_same_second_get_separate_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(REVIEWS_DIR_ENV_VAR, str(tmp_path))

    run_dirs = [create_review_run_dir("paper-unified") for _ in range(3)]

    assert len(set(run_dirs)) == 3
    assert all(run_dir.is_dir() for run_dir in run_dirs)


def test_unified_review_uses_the_reviews_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import revisica.graphs.unified as unified

    monkeypatch.setenv(REVIEWS_DIR_ENV_VAR, str(tmp_path / "reviews-home"))
    monkeypatch.setattr(unified, "run_writing_lane", lambda state: {"writing_result": None, "warnings": []})
    monkeypatch.setattr(unified, "run_math_lane", lambda state: {"math_result": None, "warnings": []})
    paper = tmp_path / "paper.md"
    paper.write_text("# Title\n\nText.\n", encoding="utf-8")

    run = review_unified(str(paper))

    assert run.run_dir.parent == tmp_path / "reviews-home"
    assert run.run_dir.name.startswith("paper-unified-")
