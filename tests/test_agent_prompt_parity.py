"""Every provider must send the same system prompt for the same agent.

Regression coverage for the split where Codex read stale
``agents/codex/*.md`` copies (or nothing, for versioned agents) while
Claude read ``agents/definitions/*.py``, and where the Claude CLI was
handed an ``--agents`` payload that Claude Code rejects.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from revisica.agents import findings_schema_path, get_agent, list_agents, to_agent_spec
from revisica.providers.cli_claude import ClaudeCliProvider
from revisica.providers.cli_codex import CodexCliProvider

_ALL_AGENT_NAMES = [agent.name for agent in list_agents()]


def _fake_completed_process(command, **_kwargs):
    return subprocess.CompletedProcess(command, 0, stdout='{"findings": []}', stderr="")


@pytest.mark.parametrize("agent_name", _ALL_AGENT_NAMES)
def test_agent_spec_carries_definition_prompt(agent_name: str) -> None:
    definition = get_agent(agent_name)
    spec = to_agent_spec(definition, schema_path=findings_schema_path())

    assert spec.system_prompt == definition.system_prompt
    assert spec.system_prompt.strip()
    assert spec.description
    assert spec.tools == list(definition.tools)


def test_findings_schema_ships_inside_package() -> None:
    schema_path = Path(findings_schema_path())

    assert schema_path.is_file()
    assert "revisica" in schema_path.parts
    assert json.loads(schema_path.read_text(encoding="utf-8"))["required"] == ["findings"]


def test_claude_cli_sends_valid_agents_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_commands: list[list[str]] = []

    def capture_run(command, **kwargs):
        captured_commands.append(command)
        return _fake_completed_process(command, **kwargs)

    monkeypatch.setattr(ClaudeCliProvider, "_cli_path", lambda self: "claude")
    monkeypatch.setattr(subprocess, "run", capture_run)

    definition = get_agent("math-proof-reviewer")
    ClaudeCliProvider().run_agent("Review step 1.", to_agent_spec(definition))

    command = captured_commands[0]
    agents_payload = json.loads(command[command.index("--agents") + 1])
    agent_entry = agents_payload[definition.name]
    # Claude Code requires both keys; a missing one fails the whole call.
    assert agent_entry["description"] == definition.description
    assert agent_entry["prompt"] == definition.system_prompt
    assert command[command.index("--agent") + 1] == definition.name


@pytest.mark.parametrize("agent_name", ["math-proof-reviewer", "math-proof-reviewer-v5"])
def test_codex_cli_prepends_definition_prompt(
    monkeypatch: pytest.MonkeyPatch,
    agent_name: str,
) -> None:
    captured_inputs: list[str] = []

    def capture_run(command, **kwargs):
        captured_inputs.append(kwargs["input"])
        return _fake_completed_process(command, **kwargs)

    monkeypatch.setattr(CodexCliProvider, "_cli_path", lambda self: "codex")
    monkeypatch.setattr(subprocess, "run", capture_run)

    definition = get_agent(agent_name)
    CodexCliProvider().run_agent("Review step 1.", to_agent_spec(definition))

    sent_prompt = captured_inputs[0]
    assert sent_prompt.startswith(definition.system_prompt)
    assert sent_prompt.endswith("Review step 1.")
