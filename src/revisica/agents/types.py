"""Core type for unified agent definitions."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentDefinition:
    """A provider-agnostic agent definition.

    Defined once, then translated to each provider's native format
    by the translators in :mod:`revisica.agents.translators`.

    Attributes:
        name: Unique identifier, e.g. "writing-basic-reviewer".
        role: Model-router role, e.g. "basic", "proof-reviewer".
        description: One-line summary for display.
        system_prompt: Full system instructions (provider-agnostic).
        tools: Abstract tool names the agent needs, e.g. ["Read", "Glob", "Grep"].
        output_format: "json" for structured findings, "markdown" for free-form.
        categories: Allowed finding categories for this agent.
        temperature: Model temperature hint.
        version: Prompt version tag for benchmark tracking, e.g. "v0", "v1".
    """

    name: str
    role: str
    description: str
    system_prompt: str
    tools: list[str] = field(default_factory=lambda: ["Read", "Glob", "Grep"])
    output_format: str = "json"
    categories: list[str] = field(default_factory=list)
    temperature: float = 0.0
    version: str = "v0"
