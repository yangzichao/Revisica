"""Translate AgentDefinition → legacy AgentSpec for provider execution.

This is the bridge between the new unified agent system and the existing
provider execution layer.  Once the old system is fully replaced, this
module can be simplified or removed.
"""

from __future__ import annotations

from pathlib import Path

from ..core_types import AgentSpec
from .types import AgentDefinition


def to_agent_spec(
    agent_definition: AgentDefinition,
    schema_path: str | None = None,
) -> AgentSpec:
    """Convert a unified AgentDefinition to the legacy AgentSpec format.

    Args:
        agent_definition: The unified agent definition.
        schema_path: Optional path to a JSON schema file for structured output
                     (used by Codex ``--output-schema``).  Ignored for agents
                     with ``output_format="markdown"``.
    """
    codex_instructions_path = _find_codex_instructions(agent_definition.name)
    effective_schema = (
        schema_path
        if agent_definition.output_format == "json"
        else None
    )

    return AgentSpec(
        name=agent_definition.name,
        claude_agent_def={
            "instructions": agent_definition.system_prompt,
            "tools": agent_definition.tools,
        },
        codex_instructions_path=codex_instructions_path,
        codex_output_schema=effective_schema,
        codex_sandbox="read-only",
    )


def _find_codex_instructions(agent_name: str) -> str | None:
    """Locate the Codex Markdown instructions file for an agent.

    Searches ``agents/codex/<agent-name>.md`` relative to the project root.
    Returns the absolute path if found, None otherwise.
    """
    candidates = [
        Path.cwd() / "agents" / "codex" / f"{agent_name}.md",
        Path(__file__).resolve().parent.parent.parent.parent / "agents" / "codex" / f"{agent_name}.md",
    ]
    for candidate_path in candidates:
        if candidate_path.exists():
            return str(candidate_path)
    return None
