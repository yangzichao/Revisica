"""Pure math analysis: extraction, symbolic checking, artifact rendering.

No LLM runtime dependencies — LLM result dataclasses are defined here
for shared typing, but all LLM calls live in ``math_llm``.
"""

from .artifacts import render_math_report, render_summary, write_math_artifacts
from .deterministic import analyze_blueprints, analyze_claims, issue_sort_key
from .extraction import (
    build_proof_blueprints,
    extract_claims,
    extract_functions,
    extract_proof_blocks,
    extract_theorem_blocks,
)
from .types import (
    FunctionDefinition,
    LLMAdjudicationArtifact,
    LLMProofReviewArtifact,
    LLMSelfCheckArtifact,
    MathClaim,
    MathIssue,
    MathReviewRun,
    ProofBlock,
    ProofBlueprint,
    ProofObligation,
    TheoremBlock,
)

__all__ = [
    # types
    "FunctionDefinition",
    "LLMAdjudicationArtifact",
    "LLMProofReviewArtifact",
    "LLMSelfCheckArtifact",
    "MathClaim",
    "MathIssue",
    "MathReviewRun",
    "ProofBlock",
    "ProofBlueprint",
    "ProofObligation",
    "TheoremBlock",
    # extraction
    "build_proof_blueprints",
    "extract_claims",
    "extract_functions",
    "extract_proof_blocks",
    "extract_theorem_blocks",
    # deterministic
    "analyze_blueprints",
    "analyze_claims",
    "issue_sort_key",
    # artifacts
    "render_math_report",
    "render_summary",
    "write_math_artifacts",
]
