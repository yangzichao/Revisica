"""What the writing lane hands the judge and reports when roles fail.

Regression coverage for four bugs:

- the judge read role files written *before* self-check, so findings the
  self-check removed still reached the final report;
- two reviewers with the same provider:model wrote the same files, so the
  judge saw only one of them;
- when every role failed, no ``final_report.md`` was written;
- the unified summary said "Writing: completed" with none of the lane's
  warnings, and counted only basic/structure/venue findings.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

import revisica.graphs.nodes.writing as writing_nodes
import revisica.graphs.unified as unified
import revisica.graphs.writing as writing_graph_module
import revisica.providers as providers_package
from revisica.bootstrap import PlatformStatus
from revisica.core_types import AgentSpec, ProviderModelSpec, ReviewResult
from revisica.writing import review_writing_file
from revisica.writing.types import WritingReviewRun, WritingRoleArtifact

_EXAMPLE_PAPER = Path(__file__).resolve().parents[1] / "examples" / "minimal_paper.tex"

_DRAFT_FINDINGS = [
    {"category": "clarity", "severity": "minor", "title": "kept", "snippet": "", "explanation": "", "fix": ""},
    {"category": "clarity", "severity": "minor", "title": "false positive", "snippet": "", "explanation": "", "fix": ""},
]


class ScriptedProvider:
    """Reviewers report two findings, self-check keeps one, judge records its task."""

    def __init__(self, reviewers_fail: bool = False) -> None:
        self.reviewers_fail = reviewers_fail
        self.judge_tasks: list[str] = []

    def run_agent(self, task_prompt: str, agent_spec: AgentSpec, **kwargs) -> ReviewResult:
        if agent_spec.name == "writing-judge":
            self.judge_tasks.append(task_prompt)
            return self._result(0, "# Final report\n")
        if agent_spec.name == "writing-self-checker":
            return self._result(0, json.dumps({"findings": _DRAFT_FINDINGS[:1]}))
        if self.reviewers_fail:
            return self._result(1, "", stderr="Error: not logged in")
        return self._result(0, json.dumps({"findings": _DRAFT_FINDINGS}))

    @staticmethod
    def _result(returncode: int, output: str, stderr: str = "") -> ReviewResult:
        return ReviewResult("claude", "haiku", ["fake-claude"], returncode, output, stderr)


@pytest.fixture
def paper_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fake_platforms = {
        "claude": PlatformStatus("claude", "/fake/bin/claude", tmp_path / "claude-plugin", tmp_path / "agent.json"),
        "codex": PlatformStatus("codex", None, tmp_path / "codex-plugin", tmp_path / "agent.txt"),
    }
    monkeypatch.setattr(writing_nodes, "detect_platforms", lambda: fake_platforms)
    monkeypatch.setattr(writing_nodes, "bootstrap", lambda *args, **kwargs: [])
    copied_paper = tmp_path / "paper.tex"
    shutil.copy(_EXAMPLE_PAPER, copied_paper)
    return copied_paper


def run_review(paper_path: Path, provider: ScriptedProvider, monkeypatch, reviewer_count: int = 1) -> WritingReviewRun:
    monkeypatch.setattr(providers_package, "get_provider", lambda name: provider)
    return review_writing_file(
        str(paper_path),
        output_dir=str(paper_path.parent / "run"),
        reviewer_specs=[ProviderModelSpec("claude", "haiku")] * reviewer_count,
        judge_spec=ProviderModelSpec("claude", "haiku"),
    )


def files_given_to_judge(judge_task: str) -> list[Path]:
    return [Path(path) for path in re.findall(r"^- `(.+\.json)`$", judge_task, re.MULTILINE)]


def test_judge_reads_findings_after_self_check(paper_path: Path, monkeypatch) -> None:
    provider = ScriptedProvider()
    run_review(paper_path, provider, monkeypatch)

    judge_files = files_given_to_judge(provider.judge_tasks[0])
    assert judge_files
    for judge_file in judge_files:
        titles = [finding["title"] for finding in json.loads(judge_file.read_text())["findings"]]
        assert titles == ["kept"], judge_file.name


def test_identical_reviewers_keep_separate_files(paper_path: Path, monkeypatch) -> None:
    provider = ScriptedProvider()
    run = run_review(paper_path, provider, monkeypatch, reviewer_count=2)

    basic_files = sorted(path.name for path in run.run_dir.glob("basic_*.json"))
    assert basic_files == ["basic_claude_haiku.json", "basic_claude_haiku_2.json"]
    judge_file_names = {path.name for path in files_given_to_judge(provider.judge_tasks[0])}
    assert {"basic_claude_haiku.json", "basic_claude_haiku_2.json"} <= judge_file_names


def test_all_roles_failing_still_writes_a_failed_final_report(paper_path: Path, monkeypatch) -> None:
    run = run_review(paper_path, ScriptedProvider(reviewers_fail=True), monkeypatch)

    assert run.final_report is not None
    assert not run.final_report.success
    report = (run.run_dir / "final_report.md").read_text()
    assert report.startswith("# Writing review failed")
    assert "`basic` via `claude:haiku`: exit 1: Error: not logged in" in report


def make_writing_run(run_dir: Path, artifacts: list[WritingRoleArtifact], warnings: list[str]) -> WritingReviewRun:
    return WritingReviewRun(
        source=run_dir / "paper.tex", run_dir=run_dir, venue_profile="general-academic",
        detected_providers=["claude"], reviewer_specs=[ProviderModelSpec("claude")], judge_spec=None,
        mode="single-provider", artifacts=artifacts, final_report=None, warnings=warnings,
    )


def make_artifact(role: str, findings_count: int | None, returncode: int = 0) -> WritingRoleArtifact:
    output = "" if findings_count is None else json.dumps({"findings": []})
    findings = None if findings_count is None else [{"title": f"t{index}"} for index in range(findings_count)]
    result = ReviewResult("claude", None, [], returncode, output, "")
    return WritingRoleArtifact(role=role, provider="claude", model=None, result=result, findings=findings)


def test_unified_review_reports_writing_lane_warnings(tmp_path: Path, monkeypatch) -> None:
    writing_run = make_writing_run(tmp_path, [make_artifact("basic", None, returncode=1)], ["Role `basic` failed."])

    class FinishedWritingGraph:
        def invoke(self, state: dict) -> dict:
            return {"writing_review_run": writing_run}

    monkeypatch.setattr(writing_graph_module, "compile_writing_graph", lambda: FinishedWritingGraph())
    paper = tmp_path / "paper.tex"
    paper.write_text("text", encoding="utf-8")

    lane_update = unified.run_writing_lane({"source_path": str(paper), "run_dir": str(tmp_path), "config": None})

    assert lane_update["warnings"] == ["Writing: Role `basic` failed."]


def test_unified_summary_marks_writing_failed_when_no_role_succeeded(tmp_path: Path) -> None:
    writing_run = make_writing_run(tmp_path, [make_artifact("basic", None, returncode=1)], [])

    unified._write_summary(tmp_path, tmp_path / "paper.tex", writing_run, None, [])

    summary = (tmp_path / "summary.md").read_text()
    assert "- Writing: failed (none of 1 role runs produced usable output; see warnings)" in summary


def test_unified_summary_counts_findings_from_every_role(tmp_path: Path) -> None:
    artifacts = [
        make_artifact("basic", 2),
        make_artifact("notation-tracker", 3),
        make_artifact("section-xcheck-0", 1),
        make_artifact("section-xcheck-1", 1),
    ]
    writing_run = make_writing_run(tmp_path, artifacts, [])

    unified._write_summary(tmp_path, tmp_path / "paper.tex", writing_run, None, [])

    summary = (tmp_path / "summary.md").read_text()
    assert "- Writing: completed (7 findings from 4 of 4 role runs)" in summary
    assert "  - Findings by role: basic=2, notation-tracker=3, section cross-check=2" in summary
