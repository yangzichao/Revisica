"""Codex CLI provider — runs prompts/agents via the ``codex`` CLI tool."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from ..core_types import AgentSpec, ReviewResult
from .base import BaseProvider
from .rate_limit_retry import (
    codex_error_lines,
    mentions_rate_limit,
    run_with_rate_limit_retry,
    timeout_stream_text,
)
from .codex_home import codex_subprocess_env


# Codex memories summarize past sessions and feed them into later ones,
# so one review would carry over into the next. `--disable <name>` exits
# with "Unknown feature flag" on a CLI without that feature; the `-c`
# form does not (checked on codex-cli 0.162).
_NO_MEMORIES = ("-c", "features.memories=false")


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
            *_NO_MEMORIES,
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
                env=codex_subprocess_env(),
            )
            return _completed_result(command, model, completed, output_path)
        except subprocess.TimeoutExpired as error:
            return _timed_out_result(command, model, timeout_seconds, error, output_path)
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

        # `codex exec` has no system-prompt flag, so the agent's system
        # prompt is prepended to the task. It is the same text Claude gets.
        full_prompt = task_prompt
        if agent_spec.system_prompt:
            full_prompt = (
                f"{agent_spec.system_prompt}\n\n---\n\n## Task\n\n{task_prompt}"
            )

        with tempfile.NamedTemporaryFile(
            prefix="revisica-codex-", suffix=".md", delete=False,
        ) as handle:
            output_path = Path(handle.name)

        command = [
            cli_path, "exec",
            # Papers usually live outside a git repo; without this flag
            # Codex refuses to start ("Not inside a trusted directory").
            "--skip-git-repo-check",
            *_NO_MEMORIES,
            # Headless run: never block on an approval prompt. This used to
            # come from `--full-auto`, which newer CLIs reject (0.162 does);
            # `exec` also has no `--ask-for-approval`, so set the config key.
            "-c", 'approval_policy="never"',
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

        def run_once() -> subprocess.CompletedProcess:
            return subprocess.run(
                command,
                input=full_prompt,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout_seconds,
                env=codex_subprocess_env(),
            )

        try:
            completed = run_with_rate_limit_retry(run_once, _is_rate_limited, "Codex CLI")
            return _completed_result(command, model, completed, output_path)
        except subprocess.TimeoutExpired as error:
            return _timed_out_result(command, model, timeout_seconds, error, output_path)
        finally:
            output_path.unlink(missing_ok=True)


def _is_rate_limited(completed: subprocess.CompletedProcess) -> bool:
    # stderr also carries the banner and the whole prompt echo; only the
    # ERROR lines are the failure.
    return mentions_rate_limit(codex_error_lines(completed.stderr))


def _last_message(output_path: Path, fallback: str) -> str:
    # The temp file exists from the start; it stays empty when Codex fails
    # before writing its last message.
    last_message = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    return last_message if last_message.strip() else fallback


def _completed_result(
    command: list[str],
    model: str | None,
    completed: subprocess.CompletedProcess,
    output_path: Path,
) -> ReviewResult:
    return ReviewResult(
        provider="codex",
        model=model,
        command=command,
        returncode=completed.returncode,
        output=_last_message(output_path, completed.stdout),
        stderr=completed.stderr,
    )


def _timed_out_result(
    command: list[str],
    model: str | None,
    timeout_seconds: int,
    error: subprocess.TimeoutExpired,
    output_path: Path,
) -> ReviewResult:
    stderr = f"Timed out after {timeout_seconds} seconds."
    captured_stderr = timeout_stream_text(error.stderr)
    if captured_stderr:
        stderr = f"{stderr}\n{captured_stderr}"
    return ReviewResult(
        provider="codex",
        model=model,
        command=command,
        returncode=124,
        output=_last_message(output_path, ""),
        stderr=stderr,
    )


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
