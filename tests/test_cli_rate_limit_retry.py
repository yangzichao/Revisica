"""CLI providers retry real rate limits only, and never retry timeouts.

Before: any failed Codex run whose stderr contained "rate" was retried 20
times, 10 minutes apart. ``codex exec`` echoes the prompt into stderr, and
three agent prompts contain "accurate"/"strategy", so an invalid model name
hung a review for ~3.3 hours. Timeouts were retried the same way (~6.8
hours at ``--timeout-seconds 600``).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from revisica.agents import get_agent, to_agent_spec
from revisica.providers import rate_limit_retry
from revisica.providers.cli_claude import ClaudeCliProvider
from revisica.providers.cli_codex import CodexCliProvider

# Real stderr of `codex exec --model no-such-model-xyz` (codex-cli 0.162),
# with a prompt that contains "accurate" and "strategy".
CODEX_INVALID_MODEL_STDERR = """Reading prompt from stdin...
OpenAI Codex v0.162.0-alpha.17.2
--------
model: no-such-model-xyz
--------
user
Check that the step is accurate; the proof strategy is to integrate twice.
ERROR: {"type":"error","status":400,"error":{"type":"invalid_request_error","message":"The 'no-such-model-xyz' model is not supported when using Codex with a ChatGPT account."}}
"""

CODEX_RATE_LIMITED_STDERR = """Reading prompt from stdin...
user
Review the draft.
ERROR: exceeded retry limit, last status: 429 Too Many Requests
"""

# Real stdout of `claude -p --model no-such-model-xyz` (Claude Code 2.1).
CLAUDE_INVALID_MODEL_STDOUT = (
    "There's an issue with the selected model (no-such-model-xyz). It may not exist "
    "or you may not have access to it. Run --model to pick a different model."
)


class ScriptedSubprocess:
    """Stands in for ``subprocess.run``: plays back results in order."""

    def __init__(self, results: list[subprocess.CompletedProcess | subprocess.TimeoutExpired]):
        self.results = list(results)
        self.calls = 0

    def __call__(self, command, **_kwargs):
        self.calls += 1
        result = self.results.pop(0) if len(self.results) > 1 else self.results[0]
        if isinstance(result, subprocess.TimeoutExpired):
            raise result
        return result


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    recorded: list[float] = []
    monkeypatch.setattr(rate_limit_retry.time, "sleep", recorded.append)
    monkeypatch.setattr(CodexCliProvider, "_cli_path", lambda self: "codex")
    monkeypatch.setattr(ClaudeCliProvider, "_cli_path", lambda self: "claude")
    return recorded


def failed(stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(["cli"], 1, stdout=stdout, stderr=stderr)


def succeeded(stdout: str) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(["cli"], 0, stdout=stdout, stderr="")


def agent_spec():
    return to_agent_spec(get_agent("writing-self-checker"))


def test_codex_prompt_echo_is_not_a_rate_limit(monkeypatch, sleeps) -> None:
    scripted = ScriptedSubprocess([failed(stderr=CODEX_INVALID_MODEL_STDERR)])
    monkeypatch.setattr(subprocess, "run", scripted)

    result = CodexCliProvider().run_agent("Review.", agent_spec(), model="no-such-model-xyz")

    assert scripted.calls == 1
    assert sleeps == []
    assert result.returncode == 1


def test_codex_429_error_is_retried(monkeypatch, sleeps) -> None:
    scripted = ScriptedSubprocess([failed(stderr=CODEX_RATE_LIMITED_STDERR), succeeded('{"findings": []}')])
    monkeypatch.setattr(subprocess, "run", scripted)

    result = CodexCliProvider().run_agent("Review.", agent_spec())

    assert scripted.calls == 2
    assert sleeps == [rate_limit_retry.RATE_LIMIT_RETRY_WAIT_SECONDS]
    assert result.returncode == 0


def test_codex_gives_up_after_the_retry_budget(monkeypatch, sleeps) -> None:
    scripted = ScriptedSubprocess([failed(stderr=CODEX_RATE_LIMITED_STDERR)])
    monkeypatch.setattr(subprocess, "run", scripted)

    result = CodexCliProvider().run_agent("Review.", agent_spec())

    assert scripted.calls == rate_limit_retry.RATE_LIMIT_RETRY_ATTEMPTS + 1
    assert result.returncode == 1


def test_claude_invalid_model_is_not_retried(monkeypatch, sleeps) -> None:
    scripted = ScriptedSubprocess([
        failed(stdout=CLAUDE_INVALID_MODEL_STDOUT, stderr='[claude-code:unrecognized_model] {"model":"x"}'),
    ])
    monkeypatch.setattr(subprocess, "run", scripted)

    ClaudeCliProvider().run_agent("Review.", agent_spec(), model="no-such-model-xyz")

    assert scripted.calls == 1
    assert sleeps == []


def test_claude_rate_limit_on_stdout_is_retried(monkeypatch, sleeps) -> None:
    rate_limited = failed(stdout='API Error: 429 {"type":"error","error":{"type":"rate_limit_error"}}')
    scripted = ScriptedSubprocess([rate_limited, succeeded('{"findings": []}')])
    monkeypatch.setattr(subprocess, "run", scripted)

    result = ClaudeCliProvider().run_agent("Review.", agent_spec())

    assert scripted.calls == 2
    assert result.returncode == 0


@pytest.mark.parametrize("provider_class", [ClaudeCliProvider, CodexCliProvider])
def test_timeout_is_returned_after_one_attempt(monkeypatch, sleeps, provider_class) -> None:
    timeout = subprocess.TimeoutExpired(["cli"], 600, output=b"", stderr=b"progress\n")
    scripted = ScriptedSubprocess([timeout])
    monkeypatch.setattr(subprocess, "run", scripted)

    result = provider_class().run_agent("Review.", agent_spec(), timeout_seconds=600)

    assert scripted.calls == 1
    assert sleeps == []
    assert result.returncode == 124
    # TimeoutExpired carries bytes even under text=True; report text.
    assert result.stderr == "Timed out after 600 seconds.\nprogress\n"
    assert isinstance(result.output, str)


def test_codex_falls_back_to_stdout_when_last_message_file_is_empty(monkeypatch, sleeps) -> None:
    scripted = ScriptedSubprocess([succeeded("final answer on stdout")])
    monkeypatch.setattr(subprocess, "run", scripted)

    result = CodexCliProvider().run_prompt("Judge.")

    assert result.output == "final answer on stdout"


def test_codex_prefers_last_message_file(monkeypatch, sleeps) -> None:
    def run_writing_last_message(command, **_kwargs):
        Path(command[command.index("--output-last-message") + 1]).write_text("from file", encoding="utf-8")
        return succeeded("from stdout")

    monkeypatch.setattr(subprocess, "run", run_writing_last_message)

    result = CodexCliProvider().run_prompt("Judge.")

    assert result.output == "from file"
