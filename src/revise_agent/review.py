from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import tempfile

from .adjudication_policy import pick_preferred_item
from .bootstrap import PlatformStatus, bootstrap, detect_platforms
from .core_types import AgentSpec, FinalReportResult, ProviderModelSpec, ReviewResult
from .templates import (
    CLAUDE_AGENT_NAME,
    build_final_adjudication_prompt,
    build_review_prompt,
    build_self_verification_prompt,
)


@dataclass
class ReviewRun:
    source: Path
    run_dir: Path
    detected_providers: list[str]
    selected_providers: list[str]
    mode: str
    warnings: list[str]
    provider_results: list[ReviewResult]
    final_report: FinalReportResult | None


def review_file(
    file_path: str,
    targets: list[str] | None = None,
    output_dir: str | None = None,
    force_bootstrap: bool = False,
    timeout_seconds: int = 90,
) -> ReviewRun:
    source = Path(file_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Input file does not exist: {source}")
    if not source.is_file():
        raise IsADirectoryError(f"Input path is not a file: {source}")

    platforms = detect_platforms()
    detected_providers = [name for name, platform in platforms.items() if platform.available]
    selected, warnings = _resolve_targets(platforms, targets)
    mode = _review_mode(selected)

    missing_assets = [name for name in selected if not platforms[name].installed]
    if missing_assets:
        bootstrap(missing_assets, force=force_bootstrap)
        platforms = detect_platforms()

    content = source.read_text(encoding="utf-8")
    review_prompt = build_review_prompt(str(source), content)
    run_dir = _make_output_dir(source, output_dir)
    provider_results: list[ReviewResult] = []

    for name in selected:
        result = _run_provider(name, platforms[name], review_prompt, timeout_seconds)
        provider_results.append(result)
        _write_provider_artifacts(run_dir, result)

    final_report, final_warnings = _generate_final_report(
        source=source,
        content=content,
        platforms=platforms,
        provider_results=provider_results,
        mode=mode,
        timeout_seconds=timeout_seconds,
    )
    warnings.extend(final_warnings)
    if final_report is not None:
        _write_final_report_artifacts(run_dir, final_report)

    _write_summary(
        run_dir=run_dir,
        source=source,
        mode=mode,
        detected_providers=detected_providers,
        selected_providers=selected,
        warnings=warnings,
        provider_results=provider_results,
        final_report=final_report,
    )
    return ReviewRun(
        source=source,
        run_dir=run_dir,
        detected_providers=detected_providers,
        selected_providers=selected,
        mode=mode,
        warnings=warnings,
        provider_results=provider_results,
        final_report=final_report,
    )


def _resolve_targets(
    platforms: dict[str, PlatformStatus],
    targets: list[str] | None,
) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    if targets:
        available_selected = [name for name in targets if platforms[name].available]
        missing_requested = [name for name in targets if not platforms[name].available]
        if available_selected:
            if missing_requested:
                warnings.append(
                    "Requested provider(s) not installed: "
                    f"{', '.join(missing_requested)}. Falling back to available provider(s): "
                    f"{', '.join(available_selected)}."
                )
            selected = available_selected
        else:
            detected = [name for name, platform in platforms.items() if platform.available]
            detected_text = ", ".join(detected) if detected else "none"
            raise RuntimeError(
                "Requested provider(s) not installed: "
                f"{', '.join(missing_requested)}. Detected available providers: {detected_text}. "
                "Install codex and/or claude, then run `revise-agent bootstrap`."
            )
    else:
        selected = [name for name, platform in platforms.items() if platform.available]

    if not selected:
        raise RuntimeError(
            "No supported provider detected in the current environment. "
            "Install codex and/or claude first, then run `revise-agent bootstrap`."
        )

    if len(selected) == 1:
        warnings.append(
            "Only one provider is active for this run, so ReviseAgent is switching to "
            "single-provider self-verification mode. Final report quality may be lower "
            "than cross-provider review."
        )

    return selected, warnings


def _review_mode(selected: list[str]) -> str:
    if len(selected) >= 2:
        return "cross-provider"
    return "single-provider-self-verify"


def _make_output_dir(source: Path, output_dir: str | None) -> Path:
    if output_dir:
        run_dir = Path(output_dir).expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = Path.cwd() / "reviews" / f"{source.stem}-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _run_provider(
    provider_name: str,
    platform: PlatformStatus,
    prompt: str,
    timeout_seconds: int,
    model: str | None = None,
) -> ReviewResult:
    if provider_name == "codex":
        return _run_codex(platform.cli_path, prompt, timeout_seconds, model=model)
    return _run_claude(platform.cli_path, platform.agent_path, prompt, timeout_seconds, model=model)


def _run_provider_agent(
    provider_name: str,
    platform: PlatformStatus,
    task_prompt: str,
    agent_spec: AgentSpec,
    timeout_seconds: int,
    model: str | None = None,
    working_dir: str | None = None,
) -> ReviewResult:
    """Run a real agent with tool access (not just a prompt pipe)."""
    if provider_name == "codex":
        return _run_codex_agent(
            platform.cli_path, task_prompt, agent_spec,
            timeout_seconds, model=model, working_dir=working_dir,
        )
    return _run_claude_agent(
        platform.cli_path, task_prompt, agent_spec,
        timeout_seconds, model=model, working_dir=working_dir,
    )


def _run_codex(
    cli_path: str | None,
    prompt: str,
    timeout_seconds: int,
    model: str | None = None,
) -> ReviewResult:
    if cli_path is None:
        raise RuntimeError("codex CLI not found")

    with tempfile.NamedTemporaryFile(prefix="revise-agent-codex-", suffix=".md", delete=False) as handle:
        output_path = Path(handle.name)

    cmd = [
        cli_path,
        "exec",
        "--skip-git-repo-check",
        "--color",
        "never",
        "--output-last-message",
        str(output_path),
    ]
    if model:
        cmd.extend(["--model", model])
    try:
        completed = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
            env=_subprocess_env(),
        )
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else completed.stdout
        return ReviewResult(
            provider="codex",
            model=model,
            command=cmd,
            returncode=completed.returncode,
            output=output,
            stderr=completed.stderr,
        )
    except subprocess.TimeoutExpired as error:
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        stderr = f"Timed out after {timeout_seconds} seconds."
        if error.stderr:
            stderr = f"{stderr}\n{error.stderr}"
        return ReviewResult(
            provider="codex",
            model=model,
            command=cmd,
            returncode=124,
            output=output,
            stderr=stderr,
        )
    finally:
        output_path.unlink(missing_ok=True)


def _run_claude(
    cli_path: str | None,
    agent_path: Path,
    prompt: str,
    timeout_seconds: int,
    model: str | None = None,
) -> ReviewResult:
    if cli_path is None:
        raise RuntimeError("claude CLI not found")

    agents_json = agent_path.read_text(encoding="utf-8")
    cmd = [
        cli_path,
        "-p",
        "--output-format",
        "text",
        "--permission-mode",
        "dontAsk",
        "--tools",
        "",
        "--agents",
        agents_json,
        "--agent",
        CLAUDE_AGENT_NAME,
    ]
    if model:
        cmd.extend(["--model", model])
    try:
        completed = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
            env=_subprocess_env(),
        )
        return ReviewResult(
            provider="claude",
            model=model,
            command=cmd,
            returncode=completed.returncode,
            output=completed.stdout,
            stderr=completed.stderr,
        )
    except subprocess.TimeoutExpired as error:
        stderr = f"Timed out after {timeout_seconds} seconds."
        if error.stderr:
            stderr = f"{stderr}\n{error.stderr}"
        output = error.stdout or ""
        return ReviewResult(
            provider="claude",
            model=model,
            command=cmd,
            returncode=124,
            output=output,
            stderr=stderr,
        )


def _run_claude_agent(
    cli_path: str | None,
    task_prompt: str,
    agent_spec: AgentSpec,
    timeout_seconds: int,
    model: str | None = None,
    working_dir: str | None = None,
) -> ReviewResult:
    """Run a Claude Code agent with real tool access."""
    if cli_path is None:
        raise RuntimeError("claude CLI not found")

    agent_def = agent_spec.claude_agent_def or {}
    agents_json = json.dumps({agent_spec.name: agent_def})

    cmd = [
        cli_path,
        "-p",
        "--output-format", "text",
        "--permission-mode", "bypassPermissions",
        "--agents", agents_json,
        "--agent", agent_spec.name,
    ]
    if model:
        cmd.extend(["--model", model])

    try:
        completed = subprocess.run(
            cmd,
            input=task_prompt,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
            cwd=working_dir,
            env=_subprocess_env(),
        )
        return ReviewResult(
            provider="claude",
            model=model,
            command=cmd,
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
            command=cmd,
            returncode=124,
            output=error.stdout or "",
            stderr=stderr,
        )


def _run_codex_agent(
    cli_path: str | None,
    task_prompt: str,
    agent_spec: AgentSpec,
    timeout_seconds: int,
    model: str | None = None,
    working_dir: str | None = None,
) -> ReviewResult:
    """Run a Codex agent with sandbox, instructions file, and optional output schema."""
    if cli_path is None:
        raise RuntimeError("codex CLI not found")

    # Load agent instructions and prepend to task prompt
    full_prompt = task_prompt
    if agent_spec.codex_instructions_path:
        instructions_path = Path(agent_spec.codex_instructions_path)
        if instructions_path.exists():
            instructions = instructions_path.read_text(encoding="utf-8")
            full_prompt = f"{instructions}\n\n---\n\n## Task\n\n{task_prompt}"

    with tempfile.NamedTemporaryFile(prefix="revise-agent-codex-", suffix=".md", delete=False) as handle:
        output_path = Path(handle.name)

    cmd = [
        cli_path,
        "exec",
        "--full-auto",
        "--sandbox", agent_spec.codex_sandbox,
        "--color", "never",
        "--output-last-message", str(output_path),
    ]
    if working_dir:
        cmd.extend(["-C", working_dir])
    if agent_spec.codex_output_schema:
        cmd.extend(["--output-schema", agent_spec.codex_output_schema])
    if model:
        cmd.extend(["--model", model])

    try:
        completed = subprocess.run(
            cmd,
            input=full_prompt,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
            env=_subprocess_env(),
        )
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else completed.stdout
        return ReviewResult(
            provider="codex",
            model=model,
            command=cmd,
            returncode=completed.returncode,
            output=output,
            stderr=completed.stderr,
        )
    except subprocess.TimeoutExpired as error:
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        stderr = f"Timed out after {timeout_seconds} seconds."
        if error.stderr:
            stderr = f"{stderr}\n{error.stderr}"
        return ReviewResult(
            provider="codex",
            model=model,
            command=cmd,
            returncode=124,
            output=output,
            stderr=stderr,
        )
    finally:
        output_path.unlink(missing_ok=True)


def _generate_final_report(
    source: Path,
    content: str,
    platforms: dict[str, PlatformStatus],
    provider_results: list[ReviewResult],
    mode: str,
    timeout_seconds: int,
) -> tuple[FinalReportResult | None, list[str]]:
    warnings: list[str] = []
    successful_results = [result for result in provider_results if result.success]
    if not successful_results:
        warnings.append("No provider produced a usable review, so no final report was generated.")
        return None, warnings

    if len(successful_results) == 1:
        provider_name = successful_results[0].provider
        prompt = build_self_verification_prompt(
            file_path=str(source),
            content=content,
            draft_report=successful_results[0].output,
            provider_name=provider_name,
        )
        verified = _run_provider(provider_name, platforms[provider_name], prompt, timeout_seconds)
        if verified.success:
            return FinalReportResult(
                strategy="single-provider-self-verify",
                result=verified,
            ), warnings

        warnings.append(
            "Self-verification failed, so ReviseAgent is falling back to the original single-provider review."
        )
        fallback = _fallback_final_report(
            strategy="single-provider-fallback",
            provider_results=successful_results,
            warning_text="Self-verification failed. This final report is the unverified provider review.",
        )
        return fallback, warnings

    adjudicator_provider = pick_preferred_item(
        successful_results,
        provider_getter=lambda result: result.provider,
    ).provider
    prompt = build_final_adjudication_prompt(
        file_path=str(source),
        content=content,
        provider_reports=[(result.provider, result.output) for result in successful_results],
    )
    adjudicated = _run_provider(
        adjudicator_provider,
        platforms[adjudicator_provider],
        prompt,
        timeout_seconds,
    )
    if adjudicated.success:
        return FinalReportResult(
            strategy="cross-provider-adjudication",
            result=adjudicated,
        ), warnings

    warnings.append(
        "Cross-provider adjudication failed, so ReviseAgent is falling back to a merged raw provider report."
    )
    fallback = _fallback_final_report(
        strategy="cross-provider-fallback",
        provider_results=successful_results,
        warning_text="Cross-provider adjudication failed. This final report is a raw merged fallback.",
    )
    return fallback, warnings
def _fallback_final_report(
    strategy: str,
    provider_results: list[ReviewResult],
    warning_text: str,
) -> FinalReportResult:
    merged_sections = []
    for result in provider_results:
        merged_sections.append(f"## Provider: {result.provider}\n\n{result.output}")
    output = "\n".join(
        [
            "# Executive Summary",
            warning_text,
            "",
            "## Raw Provider Reports",
            "",
            "\n\n".join(merged_sections),
        ]
    )
    result = ReviewResult(
        provider=provider_results[0].provider,
        model=provider_results[0].model,
        command=[],
        returncode=0,
        output=output,
        stderr="",
    )
    return FinalReportResult(strategy=strategy, result=result)


def _write_provider_artifacts(run_dir: Path, result: ReviewResult) -> None:
    (run_dir / f"{result.provider}.md").write_text(result.output, encoding="utf-8")
    if result.stderr.strip():
        (run_dir / f"{result.provider}.stderr.txt").write_text(result.stderr, encoding="utf-8")
    metadata = {
        "provider": result.provider,
        "model": result.model,
        "returncode": result.returncode,
        "success": result.success,
        "command": result.command,
    }
    (run_dir / f"{result.provider}.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _write_final_report_artifacts(run_dir: Path, final_report: FinalReportResult) -> None:
    (run_dir / "final_report.md").write_text(final_report.result.output, encoding="utf-8")
    metadata = {
        "strategy": final_report.strategy,
        "provider": final_report.result.provider,
        "model": final_report.result.model,
        "returncode": final_report.result.returncode,
        "success": final_report.result.success,
        "command": final_report.result.command,
    }
    (run_dir / "final_report.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    if final_report.result.stderr.strip():
        (run_dir / "final_report.stderr.txt").write_text(
            final_report.result.stderr,
            encoding="utf-8",
        )


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    runtime_home = env.get("REVISE_AGENT_RUNTIME_HOME")
    if runtime_home:
        env["HOME"] = runtime_home
    return env


def _write_summary(
    run_dir: Path,
    source: Path,
    mode: str,
    detected_providers: list[str],
    selected_providers: list[str],
    warnings: list[str],
    provider_results: list[ReviewResult],
    final_report: FinalReportResult | None,
) -> None:
    lines = [
        "# ReviseAgent Review Run",
        "",
        f"- Source: `{source}`",
        f"- Timestamp: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Detected providers: `{', '.join(detected_providers) if detected_providers else 'none'}`",
        f"- Selected providers: `{', '.join(selected_providers)}`",
        f"- Mode: `{mode}`",
        "",
        "## Providers",
        "",
    ]

    for result in provider_results:
        status = "ok" if result.success else "failed"
        label = result.provider if not result.model else f"{result.provider}:{result.model}"
        lines.append(f"- `{label}`: {status} (exit={result.returncode})")

    if warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")

    lines.extend(["", "## Files", ""])
    for result in provider_results:
        lines.append(f"- `{result.provider}.md`")
        lines.append(f"- `{result.provider}.json`")
        if result.stderr.strip():
            lines.append(f"- `{result.provider}.stderr.txt`")

    if final_report is not None:
        lines.append("- `final_report.md`")
        lines.append("- `final_report.json`")
        if final_report.result.stderr.strip():
            lines.append("- `final_report.stderr.txt`")

    (run_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
