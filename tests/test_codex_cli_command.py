"""The ``codex exec`` command must be accepted by current Codex CLIs.

Regression coverage for two failures seen with codex-cli 0.162:
``--full-auto`` was rejected outright ("unexpected argument"), and papers
outside a git repo were refused ("Not inside a trusted directory").
"""

from __future__ import annotations

import subprocess

import pytest

from revisica.agents import findings_schema_path, get_agent, to_agent_spec
from revisica.providers.cli_codex import CodexCliProvider


def _run_agent_and_capture_command(
    monkeypatch: pytest.MonkeyPatch,
    agent_name: str,
) -> list[str]:
    captured_commands: list[list[str]] = []

    def capture_run(command, **_kwargs):
        captured_commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout='{"findings": []}', stderr="")

    monkeypatch.setattr(CodexCliProvider, "_cli_path", lambda self: "codex")
    monkeypatch.setattr(subprocess, "run", capture_run)

    agent_spec = to_agent_spec(get_agent(agent_name), schema_path=findings_schema_path())
    CodexCliProvider().run_agent("Review step 1.", agent_spec, working_dir="/papers/draft")
    return captured_commands[0]


def test_agent_command_drops_removed_full_auto_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    command = _run_agent_and_capture_command(monkeypatch, "writing-basic-reviewer")

    assert "--full-auto" not in command


def test_agent_command_runs_outside_git_repos(monkeypatch: pytest.MonkeyPatch) -> None:
    command = _run_agent_and_capture_command(monkeypatch, "writing-basic-reviewer")

    assert "--skip-git-repo-check" in command
    assert command[command.index("-C") + 1] == "/papers/draft"


def test_agent_command_never_waits_for_approval(monkeypatch: pytest.MonkeyPatch) -> None:
    command = _run_agent_and_capture_command(monkeypatch, "writing-basic-reviewer")

    config_overrides = [command[index + 1] for index, arg in enumerate(command) if arg == "-c"]
    assert 'approval_policy="never"' in config_overrides


@pytest.mark.parametrize(
    ("agent_name", "expected_sandbox"),
    [
        ("writing-basic-reviewer", "read-only"),
        # Runs SymPy through Bash, so it needs a writable workspace.
        ("math-claim-verifier", "workspace-write"),
    ],
)
def test_agent_command_uses_agent_sandbox(
    monkeypatch: pytest.MonkeyPatch,
    agent_name: str,
    expected_sandbox: str,
) -> None:
    command = _run_agent_and_capture_command(monkeypatch, agent_name)

    assert command[command.index("--sandbox") + 1] == expected_sandbox
