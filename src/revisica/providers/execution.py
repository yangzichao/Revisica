"""Single entry point for running review agents on a provider.

Every LLM call in the review engine — writing roles, claim verification,
proof review, self-checks, adjudication — funnels through
:func:`run_provider_agent` so provider selection, model overrides, and
reasoning-effort plumbing live in exactly one place.

(Historically this lived in ``review.py`` next to a since-removed v0
single-shot review pipeline; only this function survived.)
"""

from __future__ import annotations

from ..core_types import AgentSpec, ReviewResult


def run_provider_agent(
    provider_name: str,
    task_prompt: str,
    agent_spec: AgentSpec,
    timeout_seconds: int,
    model: str | None = None,
    working_dir: str | None = None,
    codex_reasoning_effort: str | None = None,
) -> ReviewResult:
    """Run an agent with tool access. Delegates to the provider registry.

    ``codex_reasoning_effort`` overrides the agent-level default set on
    ``agent_spec``. Non-Codex providers ignore it.
    """
    from . import get_provider

    provider = get_provider(provider_name)
    return provider.run_agent(
        task_prompt, agent_spec,
        model=model, timeout_seconds=timeout_seconds, working_dir=working_dir,
        codex_reasoning_effort=codex_reasoning_effort,
    )
