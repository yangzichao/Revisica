"""Codex CLI provider — runs prompts/agents via the ``codex`` CLI tool."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from ..core_types import AgentSpec, ReviewResult
from .base import BaseProvider
from .subprocess_env import subprocess_env


class CodexCliProvider(BaseProvider):
    """Access GPT models via the Codex CLI (requires subscription)."""

    @property
    def name(self) -> str:
        return "codex-cli"

    @property
    def display_name(self) -> str:
        return "Codex (CLI)"

    @property
    def model_family(self) -> str:
        return "gpt"

    def is_available(self) -> bool:
        return shutil.which("codex") is not None

    def _cli_path(self) -> str:
        cli_path = shutil.which("codex")
        if cli_path is None:
            raise RuntimeError("codex CLI not found on PATH")
        return cli_path

    def run_prompt(
        self,
        prompt: str,
        model: str | None = None,
        timeout_seconds: int = 120,
        codex_reasoning_effort: str | None = None,
    ) -> ReviewResult:
        cli_path = self._cli_path()

        with tempfile.NamedTemporaryFile(
            prefix="revisica-codex-", suffix=".md", delete=False,
        ) as handle:
            output_path = Path(handle.name)

        command = [
            cli_path, "exec",
            "--skip-git-repo-check",
            "--color", "never",
            "--output-last-message", str(output_path),
        ]
        _append_reasoning_effort(command, codex_reasoning_effort)
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
            output = (
                output_path.read_text(encoding="utf-8")
                if output_path.exists()
                else completed.stdout
            )
            return ReviewResult(
                provider="codex",
                model=model,
                command=command,
                returncode=completed.returncode,
                output=output,
                stderr=completed.stderr,
            )
        except subprocess.TimeoutExpired as error:
            output = (
                output_path.read_text(encoding="utf-8")
                if output_path.exists()
                else ""
            )
            stderr = f"Timed out after {timeout_seconds} seconds."
            if error.stderr:
                stderr = f"{stderr}\n{error.stderr}"
            return ReviewResult(
                provider="codex",
                model=model,
                command=command,
                returncode=124,
                output=output,
                stderr=stderr,
            )
        finally:
            output_path.unlink(missing_ok=True)

    def run_agent(
        self,
        task_prompt: str,
        agent_spec: AgentSpec,
        model: str | None = None,
        timeout_seconds: int = 120,
        working_dir: str | None = None,
        codex_reasoning_effort: str | None = None,
    ) -> ReviewResult:
        cli_path = self._cli_path()

        full_prompt = task_prompt
        if agent_spec.codex_instructions_path:
            instructions_path = Path(agent_spec.codex_instructions_path)
            if instructions_path.exists():
                instructions = instructions_path.read_text(encoding="utf-8")
                full_prompt = (
                    f"{instructions}\n\n---\n\n## Task\n\n{task_prompt}"
                )

        with tempfile.NamedTemporaryFile(
            prefix="revisica-codex-", suffix=".md", delete=False,
        ) as handle:
            output_path = Path(handle.name)

        command = [
            cli_path, "exec",
            "--full-auto",
            "--sandbox", agent_spec.codex_sandbox,
            "--color", "never",
            "--output-last-message", str(output_path),
        ]
        # Runtime override wins over agent-level default.
        effective_effort = codex_reasoning_effort or agent_spec.codex_reasoning_effort
        _append_reasoning_effort(command, effective_effort)
        if working_dir:
            command.extend(["-C", working_dir])
        if agent_spec.codex_output_schema:
            command.extend(["--output-schema", agent_spec.codex_output_schema])
        if model:
            command.extend(["--model", model])

        max_retries = 20
        retry_wait = 600  # 10 minutes between retries on rate limit

        try:
            for attempt in range(max_retries + 1):
                try:
                    completed = subprocess.run(
                        command,
                        input=full_prompt,
                        text=True,
                        capture_output=True,
                        check=False,
                        timeout=timeout_seconds,
                        env=subprocess_env(),
                    )
                    is_rate_limited = (
                        completed.returncode != 0
                        and ("rate" in completed.stderr.lower() or "overloaded" in completed.stderr.lower())
                    )
                    if is_rate_limited and attempt < max_retries:
                        import logging
                        import time
                        logging.getLogger(__name__).warning(
                            "Codex CLI rate-limited (attempt %d/%d), waiting %ds before retry...",
                            attempt + 1, max_retries, retry_wait,
                        )
                        time.sleep(retry_wait)
                        continue

                    output = (
                        output_path.read_text(encoding="utf-8")
                        if output_path.exists()
                        else completed.stdout
                    )
                    return ReviewResult(
                        provider="codex",
                        model=model,
                        command=command,
                        returncode=completed.returncode,
                        output=output,
                        stderr=completed.stderr,
                    )
                except subprocess.TimeoutExpired as error:
                    if attempt < max_retries:
                        import logging
                        import time
                        logging.getLogger(__name__).warning(
                            "Codex CLI timed out after %ds (attempt %d/%d), waiting %ds before retry...",
                            timeout_seconds, attempt + 1, max_retries, retry_wait,
                        )
                        time.sleep(retry_wait)
                        continue
                    output = (
                        output_path.read_text(encoding="utf-8")
                        if output_path.exists()
                        else ""
                    )
                    stderr = f"Timed out after {timeout_seconds} seconds ({max_retries + 1} attempts)."
                    if error.stderr:
                        stderr = f"{stderr}\n{error.stderr}"
                    return ReviewResult(
                        provider="codex",
                        model=model,
                        command=command,
                        returncode=124,
                        output=output,
                        stderr=stderr,
                    )
            # All retries exhausted without timeout or rate limit
            return ReviewResult(
                provider="codex", model=model, command=command,
                returncode=1, output="", stderr="All retries exhausted.",
            )
        finally:
            output_path.unlink(missing_ok=True)


_VALID_REASONING_EFFORTS = {"none", "minimal", "low", "medium", "high", "xhigh"}


def _append_reasoning_effort(command: list[str], effort: str | None) -> None:
    """Append ``-c model_reasoning_effort="..."`` to the command if set.

    Unknown values are silently skipped so a stale agent default can't
    break the whole run — Codex would reject the config at launch.
    """
    if not effort:
        return
    if effort not in _VALID_REASONING_EFFORTS:
        return
    command.extend(["-c", f'model_reasoning_effort="{effort}"'])
