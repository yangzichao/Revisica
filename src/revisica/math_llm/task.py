from __future__ import annotations

import json
from pathlib import Path

from ..agents import get_agent, to_agent_spec
from ..core_types import AgentSpec
from ..math_check import LLMProofReviewArtifact, ProofBlueprint


def find_codex_file(filename: str) -> str | None:
    candidates = [
        Path.cwd() / "agents" / "codex" / filename,
        Path(__file__).resolve().parent.parent.parent.parent / "agents" / "codex" / filename,
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return None


_MATH_ROLE_TO_AGENT_NAME = {
    "proof-reviewer": "math-proof-reviewer",
    "self-checker": "math-self-checker",
    "adjudicator": "math-adjudicator",
}


def build_math_agent_spec(
    role: str,
    schema_path: str | None,
    agent_version: str | None = None,
) -> AgentSpec:
    """Build an AgentSpec for a math review role using the unified agent registry.

    If *agent_version* is given (e.g. ``"v0"``), the versioned agent name is
    used (e.g. ``math-proof-reviewer-v0``).  Otherwise the default (latest) is
    used.
    """
    base_name = _MATH_ROLE_TO_AGENT_NAME.get(role, f"math-{role}")
    agent_name = f"{base_name}-{agent_version}" if agent_version else base_name
    agent_definition = get_agent(agent_name)
    return to_agent_spec(agent_definition, schema_path=schema_path)


def build_proof_review_task(
    file_path: str,
    blueprint: ProofBlueprint,
) -> str:
    obligations_text = json.dumps(
        [
            {
                "step_index": item.step_index,
                "obligation_type": item.obligation_type,
                "text": item.text,
            }
            for item in blueprint.obligations
        ],
        indent=2,
    )
    proof_line = blueprint.proof.line_number if blueprint.proof is not None else "N/A"
    return (
        f"Review the proof obligations in the LaTeX draft at `{file_path}`.\n\n"
        f"Theorem type: {blueprint.theorem.env_name}\n"
        f"Theorem line: {blueprint.theorem.line_number}\n"
        f"Theorem statement:\n{blueprint.theorem.statement}\n\n"
        f"Proof line: {proof_line}\n\n"
        f"Proof obligations:\n{obligations_text}\n\n"
        f"Read the file, assess each obligation, and return JSON with a 'findings' array."
    )


def build_self_check_task(
    file_path: str,
    blueprint: ProofBlueprint,
    reviewer_provider: str,
    reviewer_model: str | None,
    draft_findings: list[dict[str, object]],
) -> str:
    proof_line = blueprint.proof.line_number if blueprint.proof is not None else "N/A"
    reviewer_label = reviewer_provider if not reviewer_model else f"{reviewer_provider}:{reviewer_model}"
    obligations_text = json.dumps(
        [
            {
                "step_index": item.step_index,
                "obligation_type": item.obligation_type,
                "text": item.text,
            }
            for item in blueprint.obligations
        ],
        indent=2,
    )
    findings_text = json.dumps(draft_findings, indent=2)
    return (
        f"Self-check the proof review findings for the LaTeX draft at `{file_path}`.\n\n"
        f"Theorem type: {blueprint.theorem.env_name}\n"
        f"Theorem line: {blueprint.theorem.line_number}\n"
        f"Theorem statement:\n{blueprint.theorem.statement}\n\n"
        f"Proof line: {proof_line}\n\n"
        f"Proof obligations:\n{obligations_text}\n\n"
        f"Original reviewer: {reviewer_label}\n"
        f"Draft findings:\n{findings_text}\n\n"
        f"Read the file, verify each finding, remove false positives, and return JSON "
        f"with a 'findings' array."
    )


def build_adjudication_task(
    file_path: str,
    blueprint: ProofBlueprint,
    provider_artifacts: list[LLMProofReviewArtifact],
) -> str:
    proof_line = blueprint.proof.line_number if blueprint.proof is not None else "N/A"
    obligations_text = json.dumps(
        [
            {
                "step_index": item.step_index,
                "obligation_type": item.obligation_type,
                "text": item.text,
            }
            for item in blueprint.obligations
        ],
        indent=2,
    )
    provider_findings_text = json.dumps(
        [
            {
                "provider": artifact.provider,
                "model": artifact.model,
                "findings": artifact.findings,
            }
            for artifact in provider_artifacts
        ],
        indent=2,
    )
    return (
        f"Adjudicate proof review findings for the LaTeX draft at `{file_path}`.\n\n"
        f"Theorem type: {blueprint.theorem.env_name}\n"
        f"Theorem line: {blueprint.theorem.line_number}\n"
        f"Theorem statement:\n{blueprint.theorem.statement}\n\n"
        f"Proof line: {proof_line}\n\n"
        f"Proof obligations:\n{obligations_text}\n\n"
        f"Provider findings:\n{provider_findings_text}\n\n"
        f"Read the file, compare findings across reviewers, and return JSON "
        f"with a merged 'findings' array."
    )
