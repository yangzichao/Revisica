"""Claude CLI provider — runs prompts/agents via the ``claude`` CLI tool."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from ..core_types import AgentSpec, ReviewResult
from ..bootstrap_assets import CLAUDE_AGENT_NAME
from .base import BaseProvider
from .rate_limit_retry import mentions_rate_limit, run_with_rate_limit_retry, timeout_stream_text
from .subprocess_env import subprocess_env

# Every agent's instructions travel in the --agents payload. Keep the
# operator's CLAUDE.md files (~/.claude, and any in the paper's directory)
# and auto-memory out of the run: they would otherwise set the report's
# language and style, and make benchmark results depend on whose machine
# ran them. Settings files still load, so auth and proxy config keep working.
_CLAUDE_INSTRUCTION_ISOLATION_ENV = {
    "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1",
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
}


def claude_subprocess_env() -> dict[str, str]:
    """Subprocess env for the Claude CLI, without the operator's instructions."""
    env = subprocess_env()
    env.update(_CLAUDE_INSTRUCTION_ISOLATION_ENV)
    return env


class ClaudeCliProvider(BaseProvider):
    """Access Claude models via the Claude Code CLI (requires subscription)."""

    def __init__(self, agent_path: Path | None = None):
        self._agent_path = agent_path

    @property
    def name(self) -> str:
        return "claude-cli"

    @property
    def display_name(self) -> str:
        return "Claude (CLI)"

    @property
    def model_family(self) -> str:
        return "claude"

    def is_available(self) -> bool:
        return shutil.which("claude") is not None

    def _cli_path(self) -> str:
        cli_path = shutil.which("claude")
        if cli_path is None:
            raise RuntimeError("claude CLI not found on PATH")
        return cli_path

    def run_prompt(
        self,
        prompt: str,
        model: str | None = None,
        timeout_seconds: int = 120,
        codex_reasoning_effort: str | None = None,
    ) -> ReviewResult:
        # codex_reasoning_effort is Codex-specific; Claude CLI ignores it.
        del codex_reasoning_effort
        cli_path = self._cli_path()

        command = [
            cli_path, "-p",
            "--output-format", "text",
            "--permission-mode", "dontAsk",
            "--tools", "",
        ]

        if self._agent_path and self._agent_path.exists():
            agents_json = self._agent_path.read_text(encoding="utf-8")
            command.extend(["--agents", agents_json, "--agent", CLAUDE_AGENT_NAME])

        if model:
            command.extend(["--model", model])

        try:
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout_seconds,
                env=claude_subprocess_env(),
            )
            return ReviewResult(
                provider="claude",
                model=model,
                command=command,
                returncode=completed.returncode,
                output=completed.stdout,
                stderr=completed.stderr,
            )
        except subprocess.TimeoutExpired as error:
            return _timed_out_result(command, model, timeout_seconds, error)

    def run_agent(
        self,
        task_prompt: str,
        agent_spec: AgentSpec,
        model: str | None = None,
        timeout_seconds: int = 120,
        working_dir: str | None = None,
        codex_reasoning_effort: str | None = None,
    ) -> ReviewResult:
        del codex_reasoning_effort  # Codex-specific; no-op for Claude.
        cli_path = self._cli_path()

        # Claude Code's --agents schema requires "description" and "prompt";
        # it rejects the whole invocation when either is missing.
        agent_def: dict[str, object] = {
            "description": agent_spec.description or agent_spec.name,
            "prompt": agent_spec.system_prompt,
        }
        if agent_spec.tools:
            agent_def["tools"] = agent_spec.tools
        agents_json = json.dumps({agent_spec.name: agent_def})

        command = [
            cli_path, "-p",
            "--output-format", "text",
            "--permission-mode", "bypassPermissions",
            "--agents", agents_json,
            "--agent", agent_spec.name,
        ]
        if model:
            command.extend(["--model", model])

        def run_once() -> subprocess.CompletedProcess:
            return subprocess.run(
                command,
                input=task_prompt,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout_seconds,
                cwd=working_dir,
                env=claude_subprocess_env(),
            )

        try:
            completed = run_with_rate_limit_retry(run_once, _is_rate_limited, "Claude CLI")
        except subprocess.TimeoutExpired as error:
            return _timed_out_result(command, model, timeout_seconds, error)
        return ReviewResult(
            provider="claude",
            model=model,
            command=command,
            returncode=completed.returncode,
            output=completed.stdout,
            stderr=completed.stderr,
        )


def _is_rate_limited(completed: subprocess.CompletedProcess) -> bool:
    # In print mode the CLI prints the user-facing error ("API Error: 429
    # ...", "usage limit reached") on stdout and a tag on stderr; it never
    # echoes the prompt.
    return mentions_rate_limit(f"{completed.stdout}\n{completed.stderr}")


def _timed_out_result(
    command: list[str],
    model: str | None,
    timeout_seconds: int,
    error: subprocess.TimeoutExpired,
) -> ReviewResult:
    stderr = f"Timed out after {timeout_seconds} seconds."
    captured_stderr = timeout_stream_text(error.stderr)
    if captured_stderr:
        stderr = f"{stderr}\n{captured_stderr}"
    return ReviewResult(
        provider="claude",
        model=model,
        command=command,
        returncode=124,
        output=timeout_stream_text(error.stdout),
        stderr=stderr,
    )
