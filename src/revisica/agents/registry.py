"""Central registry for agent definitions."""

from __future__ import annotations

from .types import AgentDefinition

# Import all agent definitions
from .definitions.writing_basic import AGENT as WRITING_BASIC
from .definitions.writing_structure import AGENT as WRITING_STRUCTURE
from .definitions.writing_venue import AGENT as WRITING_VENUE
from .definitions.writing_judge import AGENT as WRITING_JUDGE
from .definitions.proof_reviewer import ALL_VERSIONS as PROOF_REVIEWER_VERSIONS
from .definitions.proof_reviewer import AGENT as PROOF_REVIEWER
from .definitions.proof_self_checker import AGENT as PROOF_SELF_CHECKER
from .definitions.proof_adjudicator import AGENT as PROOF_ADJUDICATOR
from .definitions.claim_verifier import AGENT as CLAIM_VERIFIER
from .definitions.notation_tracker import AGENT as NOTATION_TRACKER
from .definitions.formula_cross_checker import AGENT as FORMULA_CROSS_CHECKER
from .definitions.polish_agent import AGENT as POLISH_AGENT
from .definitions.writing_self_checker import AGENT as WRITING_SELF_CHECKER
from .definitions.refine_eval_judge import AGENT as REFINE_EVAL_JUDGE

_ALL_AGENTS: dict[str, AgentDefinition] = {
    agent.name: agent
    for agent in [
        WRITING_BASIC,
        WRITING_STRUCTURE,
        WRITING_VENUE,
        WRITING_JUDGE,
        *PROOF_REVIEWER_VERSIONS,
        PROOF_SELF_CHECKER,
        PROOF_ADJUDICATOR,
        CLAIM_VERIFIER,
        NOTATION_TRACKER,
        FORMULA_CROSS_CHECKER,
        POLISH_AGENT,
        WRITING_SELF_CHECKER,
        REFINE_EVAL_JUDGE,
    ]
}


def get_agent(name: str) -> AgentDefinition:
    """Look up an agent definition by name."""
    agent = _ALL_AGENTS.get(name)
    if agent is None:
        available_names = sorted(_ALL_AGENTS.keys())
        raise ValueError(
            f"Unknown agent '{name}'. Available: {available_names}"
        )
    return agent


def list_agents() -> list[AgentDefinition]:
    """Return all registered agent definitions."""
    return list(_ALL_AGENTS.values())
