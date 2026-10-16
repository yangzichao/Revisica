"""A review that produced nothing usable must not finish as "completed".

Before: with every agent failing (simulated "Error: not logged in"),
``_execute_review`` marked both review and polish jobs completed with no
error. The desktop app then showed an empty review, or a polish report
saying "No polish suggestions generated.", and no Retry button.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import revisica.api as api
import revisica.graphs.nodes.writing as writing_nodes
import revisica.graphs.polish as polish_graph
import revisica.providers as providers_package
from revisica.bootstrap import PlatformStatus
from revisica.core_types import AgentSpec, ReviewResult
from revisica.jobs import RunState, get_run, register_run, reset_registry_for_tests

_EXAMPLE_PAPER = Path(__file__).resolve().parents[1] / "examples" / "minimal_paper.tex"


class ScriptedProvider:
    def __init__(self, agents_fail: bool) -> None:
        self.agents_fail = agents_fail

    def run_agent(self, task_prompt: str, agent_spec: AgentSpec, **kwargs) -> ReviewResult:
        if self.agents_fail:
            return ReviewResult("claude", "sonnet", ["fake-claude"], 1, "", "Error: not logged in")
        if agent_spec.name == "polish-agent":
            return ReviewResult("claude", "sonnet", ["fake-claude"], 0, "Tighten the abstract.", "")
        if agent_spec.name == "writing-judge":
            return ReviewResult("claude", "sonnet", ["fake-claude"], 0, "# Final report\n", "")
        return ReviewResult("claude", "sonnet", ["fake-claude"], 0, json.dumps({"findings": []}), "")


@pytest.fixture
def paper_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fake_platforms = {
        "claude": PlatformStatus("claude", "/fake/bin/claude", tmp_path / "claude-plugin", tmp_path / "agent.json"),
        "codex": PlatformStatus("codex", None, tmp_path / "codex-plugin", tmp_path / "agent.txt"),
    }
    monkeypatch.setattr(writing_nodes, "detect_platforms", lambda: fake_platforms)
    monkeypatch.setattr(writing_nodes, "bootstrap", lambda *args, **kwargs: [])
    monkeypatch.setattr(polish_graph, "detect_platforms", lambda: fake_platforms)
    monkeypatch.setenv("REVISICA_JOBS_DIR", str(tmp_path / "jobs"))
    monkeypatch.setenv("REVISICA_REVIEWS_DIR", str(tmp_path / "reviews"))
    reset_registry_for_tests()
    copied_paper = tmp_path / "paper.tex"
    shutil.copy(_EXAMPLE_PAPER, copied_paper)
    yield copied_paper
    reset_registry_for_tests()


def run_job(paper_path: Path, mode: str, agents_fail: bool, monkeypatch: pytest.MonkeyPatch) -> RunState:
    monkeypatch.setattr(providers_package, "get_provider", lambda name: ScriptedProvider(agents_fail))
    request = api.ReviewRequest(file_path=str(paper_path), mode=mode, writing_model="claude:sonnet")
    register_run(RunState("job-1", request.model_dump()))

    api._execute_review("job-1", request)

    return get_run("job-1")


@pytest.mark.parametrize("mode", ["review", "polish"])
def test_job_fails_with_the_reason_when_every_agent_fails(
    paper_path: Path, mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_state = run_job(paper_path, mode, agents_fail=True, monkeypatch=monkeypatch)

    assert run_state.state == "failed"
    assert "Error: not logged in" in run_state.error
    assert run_state.run_dir is not None


def test_failed_polish_report_says_it_failed(paper_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_state = run_job(paper_path, "polish", agents_fail=True, monkeypatch=monkeypatch)

    polish_report = (Path(run_state.run_dir) / "polish_report.md").read_text(encoding="utf-8")
    assert polish_report.startswith("# Polish failed")
    assert "No polish suggestions generated." not in polish_report


@pytest.mark.parametrize("mode", ["review", "polish"])
def test_job_with_usable_output_still_completes(
    paper_path: Path, mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_state = run_job(paper_path, mode, agents_fail=False, monkeypatch=monkeypatch)

    assert run_state.state == "completed"
    assert run_state.error is None
