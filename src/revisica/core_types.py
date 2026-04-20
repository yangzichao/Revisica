from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReviewResult:
    provider: str
    model: str | None
    command: list[str]
    returncode: int
    output: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0 and bool(self.output.strip())


@dataclass
class FinalReportResult:
    strategy: str
    result: ReviewResult


@dataclass(frozen=True)
class ProviderModelSpec:
    provider: str
    model: str | None = None

    @property
    def label(self) -> str:
        if self.model:
            return f"{self.provider}:{self.model}"
        return self.provider


@dataclass
class AgentSpec:
    """Defines a real agent invocation with tool access."""

    name: str
    claude_agent_def: dict[str, object] | None = None
    codex_instructions_path: str | None = None
    codex_output_schema: str | None = None
    codex_sandbox: str = "read-only"
    # Optional Codex reasoning effort. Accepted values:
    # none, minimal, low, medium, high, xhigh. When unset, Codex uses the
    # user's ~/.codex/config.toml default. Runtime overrides (e.g. the
    # --codex-reasoning CLI flag) take precedence over this agent-level default.
    codex_reasoning_effort: str | None = None
