"""Translate AgentDefinition → AgentSpec for provider execution.

This is the bridge between the unified agent system and the provider
execution layer. Every provider reads ``AgentSpec.system_prompt``, so the
Python definition in ``agents/definitions/`` is the only prompt source.
"""

from __future__ import annotations

from ..core_types import AgentSpec
from .types import AgentDefinition


def to_agent_spec(
    agent_definition: AgentDefinition,
    schema_path: str | None = None,
) -> AgentSpec:
    """Convert a unified AgentDefinition to an AgentSpec.

    Args:
        agent_definition: The unified agent definition.
        schema_path: Optional path to a JSON schema file for structured output
                     (used by Codex ``--output-schema``).  Ignored for agents
                     with ``output_format="markdown"``.
    """
    effective_schema = (
        schema_path
        if agent_definition.output_format == "json"
        else None
    )

    # Agents with Bash/WebSearch need write access for code execution
    needs_execution = any(t in agent_definition.tools for t in ("Bash", "WebSearch", "WebFetch"))
    codex_sandbox = "workspace-write" if needs_execution else "read-only"

    return AgentSpec(
        name=agent_definition.name,
        description=agent_definition.description,
        system_prompt=agent_definition.system_prompt,
        tools=list(agent_definition.tools),
        codex_output_schema=effective_schema,
        codex_sandbox=codex_sandbox,
        codex_reasoning_effort=agent_definition.codex_reasoning_effort,
    )
