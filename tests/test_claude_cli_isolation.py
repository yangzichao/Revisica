"""Claude CLI runs must not pick up the operator's CLAUDE.md or auto-memory.

Without isolation, a reviewer's personal ``~/.claude/CLAUDE.md`` (e.g. "reply
in Chinese") set the language and style of every Revisica report.
"""

from __future__ import annotations

import subprocess

import pytest

from revisica.agents import get_agent, to_agent_spec
from revisica.providers.cli_claude import ClaudeCliProvider


def _capture_subprocess_envs(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    captured_envs: list[dict[str, str]] = []

    def capture_run(command, **kwargs):
        captured_envs.append(kwargs["env"])
        return subprocess.CompletedProcess(command, 0, stdout='{"findings": []}', stderr="")

    monkeypatch.setattr(ClaudeCliProvider, "_cli_path", lambda self: "claude")
    monkeypatch.setattr(subprocess, "run", capture_run)
    return captured_envs


def _assert_operator_instructions_disabled(env: dict[str, str]) -> None:
    assert env["CLAUDE_CODE_DISABLE_CLAUDE_MDS"] == "1"
    assert env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] == "1"


def test_run_agent_disables_claude_md_and_auto_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_envs = _capture_subprocess_envs(monkeypatch)

    ClaudeCliProvider().run_agent("Review step 1.", to_agent_spec(get_agent("writing-basic-reviewer")))

    _assert_operator_instructions_disabled(captured_envs[0])


def test_run_prompt_disables_claude_md_and_auto_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_envs = _capture_subprocess_envs(monkeypatch)

    ClaudeCliProvider().run_prompt("Judge these findings.")

    _assert_operator_instructions_disabled(captured_envs[0])


def test_runtime_home_override_still_applies(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("REVISICA_RUNTIME_HOME", str(tmp_path))
    captured_envs = _capture_subprocess_envs(monkeypatch)

    ClaudeCliProvider().run_prompt("Judge these findings.")

    assert captured_envs[0]["HOME"] == str(tmp_path)
    _assert_operator_instructions_disabled(captured_envs[0])
