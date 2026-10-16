"""``custom_instructions`` must reach the polish agent.

``POST /api/review`` accepted it, but ``_execute_review`` never passed it
on, so the polish graph's "Additional instructions" branch never ran.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import revisica.graphs.polish as polish_graph_module
from revisica.bootstrap import PlatformStatus
from revisica.core_types import ReviewResult
from revisica.unified_review import review_unified


def test_custom_instructions_reach_the_polish_task(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    platforms = {
        "claude": PlatformStatus("claude", "/fake/bin/claude", tmp_path / "plugin", tmp_path / "agent.json"),
        "codex": PlatformStatus("codex", None, tmp_path / "plugin", tmp_path / "agent.txt"),
    }
    monkeypatch.setattr(polish_graph_module, "detect_platforms", lambda: platforms)
    polish_tasks: list[str] = []

    def fake_run_provider_agent(provider_name, task_prompt, **kwargs):
        polish_tasks.append(task_prompt)
        return ReviewResult(provider_name, kwargs.get("model"), [], 0, "Polished.", "")

    monkeypatch.setattr(polish_graph_module, "run_provider_agent", fake_run_provider_agent)
    paper = tmp_path / "paper.md"
    paper.write_text("# Title\n\nSome draft text.\n", encoding="utf-8")

    review_unified(
        str(paper),
        output_dir=str(tmp_path / "run"),
        mode="polish",
        custom_instructions="Keep British spelling.",
    )

    assert polish_tasks[0].endswith("Additional instructions: Keep British spelling.")
