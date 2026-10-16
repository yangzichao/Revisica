"""The writing graph must run every node to completion.

``test_writing_summary_node.py`` covers the summary node alone; this runs
the whole graph through ``review_writing_file``, so a break in any node
(like the summary node once calling itself after every agent had already
run) fails here. Only the provider call is faked.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import revisica.graphs.nodes.writing as writing_nodes
import revisica.providers as providers_package
from revisica.bootstrap import PlatformStatus
from revisica.core_types import AgentSpec, ProviderModelSpec, ReviewResult
from revisica.writing import review_writing_file

_EXAMPLE_PAPER = Path(__file__).resolve().parents[1] / "examples" / "minimal_paper.tex"


class _FakeProvider:
    """Answers every agent call with an empty, well-formed findings payload."""

    def __init__(self) -> None:
        self.agent_names: list[str] = []

    def run_agent(self, task_prompt: str, agent_spec: AgentSpec, **kwargs) -> ReviewResult:
        self.agent_names.append(agent_spec.name)
        return ReviewResult(
            provider="claude",
            model=kwargs.get("model"),
            command=["fake-claude"],
            returncode=0,
            output=json.dumps({"findings": []}),
            stderr="",
        )


def test_writing_review_completes_and_writes_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_platforms = {
        "claude": PlatformStatus(
            name="claude",
            cli_path="/fake/bin/claude",
            plugin_dir=tmp_path / "claude-plugin",
            agent_path=tmp_path / "claude-plugin" / "agent.json",
        ),
        "codex": PlatformStatus(
            name="codex",
            cli_path=None,
            plugin_dir=tmp_path / "codex-plugin",
            agent_path=tmp_path / "codex-plugin" / "agent.txt",
        ),
    }
    fake_provider = _FakeProvider()
    monkeypatch.setattr(writing_nodes, "detect_platforms", lambda: fake_platforms)
    # Never touch the real ~/.claude while bootstrapping assets.
    monkeypatch.setattr(writing_nodes, "bootstrap", lambda *args, **kwargs: [])
    monkeypatch.setattr(providers_package, "get_provider", lambda name: fake_provider)

    paper_path = tmp_path / "paper.tex"
    shutil.copy(_EXAMPLE_PAPER, paper_path)
    run_dir = tmp_path / "run"

    run = review_writing_file(
        str(paper_path),
        output_dir=str(run_dir),
        reviewer_specs=[ProviderModelSpec(provider="claude", model="haiku")],
        judge_spec=ProviderModelSpec(provider="claude", model="haiku"),
    )

    assert run.run_dir == run_dir
    assert (run_dir / "summary.md").is_file()
    assert "writing-basic-reviewer" in fake_provider.agent_names
