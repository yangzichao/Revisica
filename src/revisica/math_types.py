from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import sympy as sp

from .core_types import ReviewResult


@dataclass
class FunctionDefinition:
    name: str
    variable: str
    expression_text: str
    expression: sp.Expr
    line_number: int
    snippet: str


@dataclass
class MathClaim:
    kind: str
    line_number: int
    snippet: str
    details: dict[str, str]


@dataclass
class MathIssue:
    line_number: int
    status: str
    severity: str
    title: str
    snippet: str
    explanation: str
    fix: str
    evidence: str


@dataclass
class TheoremBlock:
    env_name: str
    line_number: int
    title: str | None
    statement: str
    snippet: str


@dataclass
class ProofBlock:
    line_number: int
    title: str | None
    body: str
    snippet: str


@dataclass
class ProofObligation:
    theorem_env: str
    theorem_line_number: int
    proof_line_number: int
    step_index: int
    text: str
    obligation_type: str


@dataclass
class ProofBlueprint:
    theorem: TheoremBlock
    proof: ProofBlock | None
    obligations: list[ProofObligation]


@dataclass
class LLMProofReviewArtifact:
    provider: str
    model: str | None
    theorem_line_number: int
    result: ReviewResult
    findings: list[dict[str, object]] | None


@dataclass
class LLMAdjudicationArtifact:
    adjudicator_provider: str
    model: str | None
    theorem_line_number: int
    result: ReviewResult
    findings: list[dict[str, object]] | None


@dataclass
class LLMSelfCheckArtifact:
    provider: str
    model: str | None
    theorem_line_number: int
    result: ReviewResult
    findings: list[dict[str, object]] | None


@dataclass
class MathReviewRun:
    source: Path
    run_dir: Path
    functions: list[FunctionDefinition]
    claims: list[MathClaim]
    theorems: list[TheoremBlock]
    proofs: list[ProofBlock]
    blueprints: list[ProofBlueprint]
    issues: list[MathIssue]
    llm_provider_results: list[LLMProofReviewArtifact]
    llm_self_check_results: list[LLMSelfCheckArtifact]
    llm_adjudication_results: list[LLMAdjudicationArtifact]
    warnings: list[str]
