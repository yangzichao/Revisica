"""Claude CLI provider — runs prompts/agents via the ``claude`` CLI tool."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from ..core_types import AgentSpec, ReviewResult
from ..templates import CLAUDE_AGENT_NAME
from .base import BaseProvider
from .subprocess_env import subprocess_env


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
                env=subprocess_env(),
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
            stderr = f"Timed out after {timeout_seconds} seconds."
            if error.stderr:
                stderr = f"{stderr}\n{error.stderr}"
            return ReviewResult(
                provider="claude",
                model=model,
                command=command,
                returncode=124,
                output=error.stdout or "",
                stderr=stderr,
            )

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

        agent_def = agent_spec.claude_agent_def or {}
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

        max_retries = 20
        retry_wait = 600  # 10 minutes between retries on rate limit

        for attempt in range(max_retries + 1):
            try:
                completed = subprocess.run(
                    command,
                    input=task_prompt,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=timeout_seconds,
                    cwd=working_dir,
                    env=subprocess_env(),
                )
                # Check for rate limiting (exit code 1 with rate limit text)
                is_rate_limited = (
                    completed.returncode != 0
                    and ("rate" in completed.stderr.lower() or "overloaded" in completed.stderr.lower())
                )
                if is_rate_limited and attempt < max_retries:
                    import logging
                    import time
                    logging.getLogger(__name__).warning(
                        "Claude CLI rate-limited (attempt %d/%d), waiting %ds before retry...",
                        attempt + 1, max_retries, retry_wait,
                    )
                    time.sleep(retry_wait)
                    continue

                return ReviewResult(
                    provider="claude",
                    model=model,
                    command=command,
                    returncode=completed.returncode,
                    output=completed.stdout,
                    stderr=completed.stderr,
                )
            except subprocess.TimeoutExpired as error:
                if attempt < max_retries:
                    import logging
                    import time
                    logging.getLogger(__name__).warning(
                        "Claude CLI timed out after %ds (attempt %d/%d), waiting %ds before retry...",
                        timeout_seconds, attempt + 1, max_retries, retry_wait,
                    )
                    time.sleep(retry_wait)
                    continue
                stderr = f"Timed out after {timeout_seconds} seconds ({max_retries + 1} attempts)."
                if error.stderr:
                    stderr = f"{stderr}\n{error.stderr}"
                return ReviewResult(
                    provider="claude",
                    model=model,
                    command=command,
                    returncode=124,
                    output=error.stdout or "",
                    stderr=stderr,
                )
        # Should not reach here, but just in case
        return ReviewResult(
            provider="claude", model=model, command=command,
            returncode=1, output="", stderr="All retries exhausted.",
        )
