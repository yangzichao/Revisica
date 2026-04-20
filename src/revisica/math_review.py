from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .core_types import ProviderModelSpec
from .math_check import (
    FunctionDefinition,
    LLMAdjudicationArtifact,
    LLMProofReviewArtifact,
    LLMSelfCheckArtifact,
    MathClaim,
    MathIssue,
    MathReviewRun,
    ProofBlueprint,
    ProofBlock,
    TheoremBlock,
    analyze_blueprints,
    analyze_claims,
    build_proof_blueprints,
    extract_claims,
    extract_functions,
    extract_proof_blocks,
    extract_theorem_blocks,
    issue_sort_key,
    write_math_artifacts,
)
from .math_llm import run_llm_proof_review
from .run_dir_helpers import copy_source_into_run_dir


def review_math_file(
    file_path: str,
    output_dir: str | None = None,
    deterministic_checks: bool = True,
    llm_proof_review: bool = False,
    targets: list[str] | None = None,
    proof_review_mode: str = "auto",
    reviewer_specs: list[ProviderModelSpec] | None = None,
    self_check_spec: ProviderModelSpec | None = None,
    adjudicator_spec: ProviderModelSpec | None = None,
    force_bootstrap: bool = False,
    timeout_seconds: int = 120,
    agent_version: str | None = None,
    codex_reasoning_effort: str | None = None,
    content_override: str | None = None,
) -> MathReviewRun:
    """Run the math review pipeline on a file.

    ``content_override`` lets callers pass pre-parsed / normalized text
    (for example, Markdown produced by the ingestion layer for a PDF),
    so the extractors work on the normalized representation instead of
    the raw bytes on disk.
    """
    source = Path(file_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Input file does not exist: {source}")
    if not source.is_file():
        raise IsADirectoryError(f"Input path is not a file: {source}")

    content = content_override if content_override is not None else source.read_text(encoding="utf-8")
    run_dir = _make_output_dir(source, output_dir)
    copy_source_into_run_dir(source, run_dir)
    functions = extract_functions(content)
    claims = extract_claims(content, functions)
    theorems = extract_theorem_blocks(content)
    proofs = extract_proof_blocks(content)
    blueprints = build_proof_blueprints(theorems, proofs)
    issues: list[MathIssue] = []
    if deterministic_checks:
        issues.extend(analyze_claims(claims, functions))
        issues.extend(analyze_blueprints(blueprints, proofs))

    llm_provider_results: list[LLMProofReviewArtifact] = []
    llm_self_check_results: list[LLMSelfCheckArtifact] = []
    llm_adjudication_results: list[LLMAdjudicationArtifact] = []
    warnings: list[str] = []
    if llm_proof_review:
        (
            llm_issues,
            llm_provider_results,
            llm_self_check_results,
            llm_adjudication_results,
            llm_warnings,
        ) = run_llm_proof_review(
            source=source,
            blueprints=blueprints,
            targets=targets,
            proof_review_mode=proof_review_mode,
            reviewer_specs=reviewer_specs,
            self_check_spec=self_check_spec,
            adjudicator_spec=adjudicator_spec,
            force_bootstrap=force_bootstrap,
            timeout_seconds=timeout_seconds,
            agent_version=agent_version,
            codex_reasoning_effort=codex_reasoning_effort,
        )
        issues.extend(llm_issues)
        warnings.extend(llm_warnings)

    issues.sort(key=issue_sort_key)
    write_math_artifacts(
        run_dir,
        source,
        functions,
        claims,
        theorems,
        proofs,
        blueprints,
        issues,
        llm_provider_results,
        llm_self_check_results,
        llm_adjudication_results,
        warnings,
    )
    return MathReviewRun(
        source=source,
        run_dir=run_dir,
        functions=functions,
        claims=claims,
        theorems=theorems,
        proofs=proofs,
        blueprints=blueprints,
        issues=issues,
        llm_provider_results=llm_provider_results,
        llm_self_check_results=llm_self_check_results,
        llm_adjudication_results=llm_adjudication_results,
        warnings=warnings,
    )


def _make_output_dir(source: Path, output_dir: str | None) -> Path:
    if output_dir:
        run_dir = Path(output_dir).expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = Path.cwd() / "reviews" / f"{source.stem}-math-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
