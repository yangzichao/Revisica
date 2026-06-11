"""Agent spec + task prompt construction for writing-lane roles.

Static system prompts live in ``agents/definitions/``; the dynamic task
prompts built here carry per-run context (file path, venue profile).
"""

from __future__ import annotations

from pathlib import Path

from ..agents import get_agent, to_agent_spec
from ..core_types import AgentSpec, ProviderModelSpec
from ..providers.execution import run_provider_agent
from .findings import extract_findings_payload
from .types import WritingRoleArtifact

# Map role names to agent definition names in the unified registry
ROLE_TO_AGENT_NAME = {
    "basic": "writing-basic-reviewer",
    "structure": "writing-structure-reviewer",
    "venue": "writing-venue-reviewer",
    "judge": "writing-judge",
    "math-claim-verifier": "math-claim-verifier",
    "notation-tracker": "notation-tracker",
    "formula-cross-checker": "formula-cross-checker",
}


def find_codex_file(filename: str) -> str | None:
    candidates = [
        Path.cwd() / "agents" / "codex" / filename,
        Path(__file__).resolve().parent.parent.parent.parent / "agents" / "codex" / filename,
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return None


def build_agent_spec(role: str, schema_path: str | None) -> AgentSpec:
    """Build an AgentSpec for a writing-review or math-verification role."""
    agent_name = ROLE_TO_AGENT_NAME.get(role, role)
    agent_definition = get_agent(agent_name)
    return to_agent_spec(agent_definition, schema_path=schema_path)


def build_agent_task(role: str, file_path: str, venue_profile: str) -> str:
    """Build a task prompt that gives the agent a file path (not the content)."""
    if role == "basic":
        return (
            f"Review the academic draft at `{file_path}` for basic language hygiene. "
            f"Read the file, find typos, grammar errors, clarity issues, and "
            f"terminology inconsistencies. Return JSON with a 'findings' array."
        )
    if role == "structure":
        return (
            f"Review the academic draft at `{file_path}` for structure and scholarly rhetoric. "
            f"Read the file, evaluate paragraph flow, section logic, argument progression, "
            f"contribution framing, and claim/evidence alignment. Return JSON with a 'findings' array."
        )
    if role == "venue":
        return (
            f"Review the academic draft at `{file_path}` for venue/style alignment. "
            f"The target venue profile is `{venue_profile}`. "
            f"Read the file, diagnose whether style and framing match the target profile. "
            f"Return JSON with a 'findings' array."
        )
    if role == "math-claim-verifier":
        return (
            f"Read the academic draft at `{file_path}`. "
            f"Identify every mathematical claim that can be checked computationally: "
            f"integrals, comparative statics, sign claims, algebraic identities, "
            f"FOC/Lagrangian consistency, eigenvalue properties. "
            f"For each, write a Python/SymPy script, run it, and compare the result "
            f"with the paper's claim. Return JSON with a 'findings' array."
        )
    if role == "notation-tracker":
        return (
            f"Read the academic draft at `{file_path}`. "
            f"Build a symbol table of every mathematical symbol and its definition. "
            f"Then scan the entire document for inconsistencies: undefined symbols, "
            f"redefined symbols, notation drift between propositions and proofs, "
            f"sign/ordering inconsistencies in denominators or subscripts. "
            f"Return JSON with a 'findings' array."
        )
    if role == "formula-cross-checker":
        return (
            f"Read the academic draft at `{file_path}`. "
            f"Cross-check every formula that appears in multiple locations: "
            f"proposition vs proof, proposition vs discussion, objective vs Lagrangian vs FOC. "
            f"Flag any discrepancy: wrong sign, missing exponent, swapped subscripts, "
            f"min/max vs minimizer/maximizer mismatch. "
            f"Return JSON with a 'findings' array."
        )
    return (
        f"Review the academic draft at `{file_path}`. "
        f"Return JSON with a 'findings' array."
    )


def run_single_role_task(
    role: str,
    spec: ProviderModelSpec,
    task_prompt: str,
    agent_spec: AgentSpec,
    timeout_seconds: int,
    working_dir: str,
    codex_reasoning_effort: str | None = None,
) -> WritingRoleArtifact:
    """Execute a single (role, provider) task — designed to run in a thread."""
    result = run_provider_agent(
        spec.provider,
        task_prompt,
        agent_spec,
        timeout_seconds,
        model=spec.model,
        working_dir=working_dir,
        codex_reasoning_effort=codex_reasoning_effort,
    )
    findings = extract_findings_payload(result.output)
    return WritingRoleArtifact(
        role=role,
        provider=spec.provider,
        model=spec.model,
        result=result,
        findings=findings,
    )
