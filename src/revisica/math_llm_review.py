from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re

from .adjudication_policy import pick_preferred_item
from .agents import get_agent, to_agent_spec
from .bootstrap import PlatformStatus, bootstrap, detect_platforms
from .core_types import AgentSpec, ProviderModelSpec
from .model_router import resolve_model_for_role
from .math_types import (
    LLMAdjudicationArtifact,
    LLMProofReviewArtifact,
    LLMSelfCheckArtifact,
    MathIssue,
    ProofBlueprint,
    ProofObligation,
)
from .review import _run_provider_agent


_MAX_PARALLEL_WORKERS = 10


def run_llm_proof_review(
    source: Path,
    blueprints: list[ProofBlueprint],
    targets: list[str] | None,
    proof_review_mode: str,
    reviewer_specs: list[ProviderModelSpec] | None,
    self_check_spec: ProviderModelSpec | None,
    adjudicator_spec: ProviderModelSpec | None,
    force_bootstrap: bool,
    timeout_seconds: int,
) -> tuple[
    list[MathIssue],
    list[LLMProofReviewArtifact],
    list[LLMSelfCheckArtifact],
    list[LLMAdjudicationArtifact],
    list[str],
]:
    warnings: list[str] = []
    if not blueprints:
        warnings.append("LLM proof review was requested, but no theorem/proof blueprints were extracted.")
        return [], [], [], [], warnings

    platforms = detect_platforms()
    selected_specs, selection_warnings = _resolve_math_reviewer_specs(platforms, targets, reviewer_specs)
    warnings.extend(selection_warnings)
    if not selected_specs:
        warnings.append(
            "LLM proof review was requested, but no supported provider is available. "
            "Continuing with deterministic math checks only."
        )
        return [], [], [], [], warnings

    resolved_mode = _normalize_proof_review_mode(proof_review_mode, selected_specs)

    required_specs = list(selected_specs)
    if self_check_spec is not None:
        required_specs.append(self_check_spec)
    if adjudicator_spec is not None:
        required_specs.append(adjudicator_spec)
    missing_assets = sorted(
        {
            spec.provider
            for spec in required_specs
            if spec.provider in platforms
            and platforms[spec.provider].available
            and not platforms[spec.provider].installed
        }
    )
    if missing_assets:
        bootstrap(missing_assets, force=force_bootstrap)
        platforms = detect_platforms()

    schema_path = find_codex_file("findings.schema.json")
    artifacts: list[LLMProofReviewArtifact] = []

    with ThreadPoolExecutor(max_workers=_MAX_PARALLEL_WORKERS) as pool:
        futures: dict[object, tuple[ProviderModelSpec, ProofBlueprint]] = {}
        for spec in selected_specs:
            routed_spec = resolve_model_for_role(spec, "proof-reviewer")
            platform = platforms[routed_spec.provider]
            for blueprint in blueprints:
                agent_spec = build_math_agent_spec("proof-reviewer", schema_path)
                task_prompt = build_proof_review_task(str(source), blueprint)
                future = pool.submit(
                    _run_provider_agent,
                    routed_spec.provider,
                    task_prompt,
                    agent_spec,
                    timeout_seconds,
                    routed_spec.model,
                    str(source.parent),
                )
                futures[future] = (routed_spec, blueprint)

        for future in as_completed(futures):
            routed_spec, blueprint = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                warnings.append(
                    f"LLM proof review raised exception for `{routed_spec.label}` on "
                    f"theorem line {blueprint.theorem.line_number}: {exc}"
                )
                continue
            findings = extract_findings_payload(result.output)
            artifacts.append(
                LLMProofReviewArtifact(
                    provider=routed_spec.provider,
                    model=routed_spec.model,
                    theorem_line_number=blueprint.theorem.line_number,
                    result=result,
                    findings=findings,
                )
            )
            if not result.success:
                warnings.append(
                    f"LLM proof review failed for provider `{routed_spec.label}` on theorem line "
                    f"{blueprint.theorem.line_number}."
                )

    issues, self_checks, adjudications, adjudication_warnings = _finalize_llm_reviews(
        source=source,
        blueprints=blueprints,
        platforms=platforms,
        artifacts=artifacts,
        mode=resolved_mode,
        self_check_spec=self_check_spec,
        adjudicator_spec=adjudicator_spec,
        timeout_seconds=timeout_seconds,
    )
    warnings.extend(adjudication_warnings)
    return issues, artifacts, self_checks, adjudications, warnings


_MATH_ROLE_TO_AGENT_NAME = {
    "proof-reviewer": "math-proof-reviewer",
    "self-checker": "math-self-checker",
    "adjudicator": "math-adjudicator",
}


def build_math_agent_spec(role: str, schema_path: str | None) -> AgentSpec:
    """Build an AgentSpec for a math review role using the unified agent registry."""
    agent_name = _MATH_ROLE_TO_AGENT_NAME.get(role, f"math-{role}")
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


def _resolve_math_reviewer_specs(
    platforms: dict[str, PlatformStatus],
    targets: list[str] | None,
    reviewer_specs: list[ProviderModelSpec] | None,
) -> tuple[list[ProviderModelSpec], list[str]]:
    warnings: list[str] = []
    if reviewer_specs:
        selected = [spec for spec in reviewer_specs if platforms[spec.provider].available]
        missing = [spec.label for spec in reviewer_specs if not platforms[spec.provider].available]
        if missing:
            warnings.append(f"Requested math-review provider(s) not installed: {', '.join(missing)}.")
        return selected, warnings
    if targets:
        selected = [ProviderModelSpec(provider=name) for name in targets if platforms[name].available]
        missing = [name for name in targets if not platforms[name].available]
        if missing:
            warnings.append(f"Requested math-review provider(s) not installed: {', '.join(missing)}.")
        return selected, warnings
    return [
        ProviderModelSpec(provider=name)
        for name, platform in platforms.items()
        if platform.available
    ], warnings


def _normalize_proof_review_mode(
    requested_mode: str,
    reviewer_specs: list[ProviderModelSpec],
) -> str:
    if requested_mode == "auto":
        if len(reviewer_specs) >= 2:
            return "multi-agent-cross-check"
        return "single-agent"
    allowed = {
        "single-agent",
        "single-agent-self-check",
        "multi-agent-cross-check",
    }
    if requested_mode not in allowed:
        raise ValueError(
            "proof_review_mode must be one of `auto`, `single-agent`, "
            "`single-agent-self-check`, or `multi-agent-cross-check`."
        )
    return requested_mode


def _finalize_llm_reviews(
    source: Path,
    blueprints: list[ProofBlueprint],
    platforms: dict[str, PlatformStatus],
    artifacts: list[LLMProofReviewArtifact],
    mode: str,
    self_check_spec: ProviderModelSpec | None,
    adjudicator_spec: ProviderModelSpec | None,
    timeout_seconds: int,
) -> tuple[list[MathIssue], list[LLMSelfCheckArtifact], list[LLMAdjudicationArtifact], list[str]]:
    warnings: list[str] = []
    issues: list[MathIssue] = []
    self_checks: list[LLMSelfCheckArtifact] = []
    adjudications: list[LLMAdjudicationArtifact] = []
    artifacts_by_theorem: dict[int, list[LLMProofReviewArtifact]] = {}
    blueprint_by_theorem = {item.theorem.line_number: item for item in blueprints}

    for artifact in artifacts:
        if not artifact.result.success:
            continue
        artifacts_by_theorem.setdefault(artifact.theorem_line_number, []).append(artifact)

    for blueprint in blueprints:
        theorem_line_number = blueprint.theorem.line_number
        if theorem_line_number not in artifacts_by_theorem:
            warnings.append(
                f"All LLM providers failed for {blueprint.theorem.env_name} on line {theorem_line_number}; "
                f"no proof review results are available for this theorem."
            )
            issues.append(
                MathIssue(
                    line_number=theorem_line_number,
                    status="needs-human-check",
                    severity="major",
                    title=f"LLM proof review unavailable for {blueprint.theorem.env_name}",
                    snippet=blueprint.theorem.snippet[:200],
                    explanation="All LLM providers failed to produce a review for this theorem. Manual review is needed.",
                    fix="Inspect this theorem and its proof manually.",
                    evidence=f"All provider results for theorem line {theorem_line_number} returned errors.",
                )
            )

    if mode == "single-agent":
        for theorem_line_number, theorem_artifacts in artifacts_by_theorem.items():
            blueprint = blueprint_by_theorem[theorem_line_number]
            artifact = theorem_artifacts[0]
            issues.extend(parse_llm_math_issues(artifact.findings, artifact.provider, artifact.model, blueprint))
        return issues, self_checks, adjudications, warnings

    if mode == "single-agent-self-check":
        with ThreadPoolExecutor(max_workers=_MAX_PARALLEL_WORKERS) as pool:
            futures: dict[object, tuple[int, LLMProofReviewArtifact]] = {}
            for theorem_line_number, theorem_artifacts in artifacts_by_theorem.items():
                artifact = theorem_artifacts[0]
                future = pool.submit(
                    _run_math_self_check,
                    source=source,
                    blueprint=blueprint_by_theorem[theorem_line_number],
                    reviewer_artifact=artifact,
                    platforms=platforms,
                    self_check_spec=self_check_spec,
                    timeout_seconds=timeout_seconds,
                )
                futures[future] = (theorem_line_number, artifact)

            for future in as_completed(futures):
                theorem_line_number, artifact = futures[future]
                blueprint = blueprint_by_theorem[theorem_line_number]
                try:
                    self_check = future.result()
                except Exception:
                    logging.getLogger(__name__).warning(
                        "Math self-check failed for theorem L%s — using unchecked findings",
                        theorem_line_number, exc_info=True,
                    )
                    issues.extend(parse_llm_math_issues(artifact.findings, artifact.provider, artifact.model, blueprint))
                    continue
                self_checks.append(self_check)
                if self_check.result.success and self_check.findings is not None:
                    issues.extend(
                        parse_self_checked_llm_math_issues(
                            self_check.findings,
                            self_check.provider,
                            self_check.model,
                            artifact.provider,
                            artifact.model,
                            blueprint,
                        )
                    )
                else:
                    warnings.append(
                        f"Math proof self-check failed on theorem line {theorem_line_number}; "
                        "falling back to the first-pass provider finding."
                    )
                    issues.extend(parse_llm_math_issues(artifact.findings, artifact.provider, artifact.model, blueprint))

        return issues, self_checks, adjudications, warnings

    needs_adjudication: list[tuple[int, list[LLMProofReviewArtifact]]] = []
    for theorem_line_number, theorem_artifacts in artifacts_by_theorem.items():
        successful_providers = {
            artifact.provider for artifact in theorem_artifacts if artifact.findings is not None
        }
        if len(successful_providers) >= 2:
            needs_adjudication.append((theorem_line_number, theorem_artifacts))
        else:
            blueprint = blueprint_by_theorem[theorem_line_number]
            for artifact in theorem_artifacts:
                issues.extend(parse_llm_math_issues(artifact.findings, artifact.provider, artifact.model, blueprint))

    if needs_adjudication:
        with ThreadPoolExecutor(max_workers=_MAX_PARALLEL_WORKERS) as pool:
            futures: dict[object, tuple[int, list[LLMProofReviewArtifact]]] = {}
            for theorem_line_number, theorem_artifacts in needs_adjudication:
                adjudicator = _resolve_math_adjudicator_spec(adjudicator_spec, theorem_artifacts)
                future = pool.submit(
                    _run_math_adjudication,
                    source=source,
                    blueprint=blueprint_by_theorem[theorem_line_number],
                    platforms=platforms,
                    adjudicator_spec=adjudicator,
                    provider_artifacts=theorem_artifacts,
                    timeout_seconds=timeout_seconds,
                )
                futures[future] = (theorem_line_number, theorem_artifacts)

            for future in as_completed(futures):
                theorem_line_number, theorem_artifacts = futures[future]
                blueprint = blueprint_by_theorem[theorem_line_number]
                try:
                    adjudication = future.result()
                except Exception:
                    logging.getLogger(__name__).warning(
                        "Math adjudication failed for theorem L%s — using raw findings",
                        theorem_line_number, exc_info=True,
                    )
                    for artifact in theorem_artifacts:
                        issues.extend(parse_llm_math_issues(artifact.findings, artifact.provider, artifact.model, blueprint))
                    continue
                adjudications.append(adjudication)
                if adjudication.result.success and adjudication.findings is not None:
                    issues.extend(
                        parse_adjudicated_llm_math_issues(
                            adjudication.findings,
                            adjudication.adjudicator_provider,
                            adjudication.model,
                            blueprint,
                        )
                    )
                else:
                    warnings.append(
                        f"Math proof adjudication failed on theorem line {theorem_line_number}; "
                        "falling back to raw provider findings."
                    )
                    for artifact in theorem_artifacts:
                        issues.extend(parse_llm_math_issues(artifact.findings, artifact.provider, artifact.model, blueprint))

    return issues, self_checks, adjudications, warnings
def _resolve_math_adjudicator_spec(
    adjudicator_spec: ProviderModelSpec | None,
    artifacts: list[LLMProofReviewArtifact],
) -> ProviderModelSpec:
    if adjudicator_spec is not None:
        return adjudicator_spec
    selected = pick_preferred_item(
        artifacts,
        provider_getter=lambda artifact: artifact.provider,
    )
    return ProviderModelSpec(provider=selected.provider, model=selected.model)


def _run_math_adjudication(
    source: Path,
    blueprint: ProofBlueprint,
    platforms: dict[str, PlatformStatus],
    adjudicator_spec: ProviderModelSpec,
    provider_artifacts: list[LLMProofReviewArtifact],
    timeout_seconds: int,
) -> LLMAdjudicationArtifact:
    routed = resolve_model_for_role(adjudicator_spec, "adjudicator")
    platform = platforms[routed.provider]
    schema_path = find_codex_file("findings.schema.json")
    agent_spec = build_math_agent_spec("adjudicator", schema_path)
    task_prompt = build_adjudication_task(str(source), blueprint, provider_artifacts)
    result = _run_provider_agent(
        routed.provider,
        task_prompt,
        agent_spec,
        timeout_seconds,
        model=routed.model,
        working_dir=str(source.parent),
    )
    findings = extract_findings_payload(result.output)
    return LLMAdjudicationArtifact(
        adjudicator_provider=routed.provider,
        model=routed.model,
        theorem_line_number=blueprint.theorem.line_number,
        result=result,
        findings=findings,
    )


def _run_math_self_check(
    source: Path,
    blueprint: ProofBlueprint,
    reviewer_artifact: LLMProofReviewArtifact,
    platforms: dict[str, PlatformStatus],
    self_check_spec: ProviderModelSpec | None,
    timeout_seconds: int,
) -> LLMSelfCheckArtifact:
    checker = self_check_spec or ProviderModelSpec(
        provider=reviewer_artifact.provider,
        model=reviewer_artifact.model,
    )
    routed = resolve_model_for_role(checker, "self-checker")
    platform = platforms[routed.provider]
    schema_path = find_codex_file("findings.schema.json")
    agent_spec = build_math_agent_spec("self-checker", schema_path)
    task_prompt = build_self_check_task(
        str(source),
        blueprint,
        reviewer_artifact.provider,
        reviewer_artifact.model,
        reviewer_artifact.findings or [],
    )
    result = _run_provider_agent(
        routed.provider,
        task_prompt,
        agent_spec,
        timeout_seconds,
        model=routed.model,
        working_dir=str(source.parent),
    )
    findings = extract_findings_payload(result.output)
    return LLMSelfCheckArtifact(
        provider=routed.provider,
        model=routed.model,
        theorem_line_number=blueprint.theorem.line_number,
        result=result,
        findings=findings,
    )


def parse_llm_math_issues(
    findings: list[dict[str, object]] | None,
    provider_name: str,
    model: str | None,
    blueprint: ProofBlueprint,
) -> list[MathIssue]:
    provider_label = provider_name if not model else f"{provider_name}:{model}"
    if findings is None:
        return [
            MathIssue(
                line_number=blueprint.proof.line_number if blueprint.proof is not None else blueprint.theorem.line_number,
                status="needs-human-check",
                severity="major",
                title=f"Unparseable LLM proof review from {provider_label}",
                snippet="provider output could not be parsed",
                explanation="The LLM proof reviewer returned output that could not be parsed as JSON.",
                fix="Inspect the raw provider output manually before relying on this proof review.",
                evidence=f"Provider `{provider_label}` returned non-JSON output for theorem line {blueprint.theorem.line_number}.",
            )
        ]

    issues: list[MathIssue] = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        step_index = int(finding.get("step_index", 0) or 0)
        obligation = _find_obligation(blueprint.obligations, step_index)
        snippet = obligation.text if obligation is not None else f"proof step {step_index}"
        verdict = str(finding.get("verdict", "needs_human_check"))
        status = "llm-suspected" if verdict == "likely_error" else "needs-human-check"
        severity = str(finding.get("severity", "major"))
        issues.append(
            MathIssue(
                line_number=blueprint.proof.line_number if blueprint.proof is not None else blueprint.theorem.line_number,
                status=status,
                severity=severity,
                title=f"{provider_label} proof review: {finding.get('title', 'Suspicious proof step')}",
                snippet=snippet,
                explanation=str(finding.get("explanation", "The provider flagged this proof step as suspicious.")),
                fix=str(finding.get("fix", "Expand or verify this proof step manually.")),
                evidence=(
                    f"Provider `{provider_label}` flagged theorem line {blueprint.theorem.line_number}, "
                    f"step {step_index}."
                ),
            )
        )
    return issues


def parse_adjudicated_llm_math_issues(
    findings: list[dict[str, object]] | None,
    adjudicator_provider: str,
    adjudicator_model: str | None,
    blueprint: ProofBlueprint,
) -> list[MathIssue]:
    adjudicator_label = (
        adjudicator_provider if not adjudicator_model else f"{adjudicator_provider}:{adjudicator_model}"
    )
    if findings is None:
        return [
            MathIssue(
                line_number=blueprint.proof.line_number if blueprint.proof is not None else blueprint.theorem.line_number,
                status="needs-human-check",
                severity="major",
                title=f"Unparseable adjudicated proof review from {adjudicator_label}",
                snippet="adjudication output could not be parsed",
                explanation="The adjudicated proof review returned output that could not be parsed as JSON.",
                fix="Inspect the raw adjudication output manually.",
                evidence=f"Adjudicator `{adjudicator_label}` returned non-JSON output for theorem line {blueprint.theorem.line_number}.",
            )
        ]

    issues: list[MathIssue] = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        step_index = int(finding.get("step_index", 0) or 0)
        obligation = _find_obligation(blueprint.obligations, step_index)
        snippet = obligation.text if obligation is not None else f"proof step {step_index}"
        verdict = str(finding.get("verdict", "needs_human_check"))
        status = "llm-suspected" if verdict == "likely_error" else "needs-human-check"
        providers = finding.get("providers", [])
        provider_text = ", ".join(providers) if isinstance(providers, list) and providers else adjudicator_label
        issues.append(
            MathIssue(
                line_number=blueprint.proof.line_number if blueprint.proof is not None else blueprint.theorem.line_number,
                status=status,
                severity=str(finding.get("severity", "major")),
                title=f"adjudicated proof review: {finding.get('title', 'Suspicious proof step')}",
                snippet=snippet,
                explanation=str(finding.get("explanation", "The adjudicator preserved this proof issue.")),
                fix=str(finding.get("fix", "Expand or verify this proof step manually.")),
                evidence=(
                    f"Adjudicated by `{adjudicator_label}` using provider findings from {provider_text} "
                    f"for theorem line {blueprint.theorem.line_number}, step {step_index}."
                ),
            )
        )
    return issues


def parse_self_checked_llm_math_issues(
    findings: list[dict[str, object]] | None,
    checker_provider: str,
    checker_model: str | None,
    reviewer_provider: str,
    reviewer_model: str | None,
    blueprint: ProofBlueprint,
) -> list[MathIssue]:
    checker_label = checker_provider if not checker_model else f"{checker_provider}:{checker_model}"
    reviewer_label = reviewer_provider if not reviewer_model else f"{reviewer_provider}:{reviewer_model}"
    if findings is None:
        return [
            MathIssue(
                line_number=blueprint.proof.line_number if blueprint.proof is not None else blueprint.theorem.line_number,
                status="needs-human-check",
                severity="major",
                title=f"Unparseable self-check proof review from {checker_label}",
                snippet="self-check output could not be parsed",
                explanation="The self-check proof review returned output that could not be parsed as JSON.",
                fix="Inspect the raw self-check output manually.",
                evidence=f"Self-checker `{checker_label}` returned non-JSON output for theorem line {blueprint.theorem.line_number}.",
            )
        ]

    issues: list[MathIssue] = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        step_index = int(finding.get("step_index", 0) or 0)
        obligation = _find_obligation(blueprint.obligations, step_index)
        snippet = obligation.text if obligation is not None else f"proof step {step_index}"
        verdict = str(finding.get("verdict", "needs_human_check"))
        status = "llm-suspected" if verdict == "likely_error" else "needs-human-check"
        issues.append(
            MathIssue(
                line_number=blueprint.proof.line_number if blueprint.proof is not None else blueprint.theorem.line_number,
                status=status,
                severity=str(finding.get("severity", "major")),
                title=f"self-checked proof review: {finding.get('title', 'Suspicious proof step')}",
                snippet=snippet,
                explanation=str(finding.get("explanation", "The self-check preserved this proof issue.")),
                fix=str(finding.get("fix", "Expand or verify this proof step manually.")),
                evidence=(
                    f"Reviewed by `{reviewer_label}` and self-checked by `{checker_label}` "
                    f"for theorem line {blueprint.theorem.line_number}, step {step_index}."
                ),
            )
        )
    return issues


def extract_json_payload(text: str) -> dict[str, object] | None:
    stripped = text.strip()
    candidates = [stripped]
    fence_match = re.search(r"```json\s*(\{.*?\})\s*```", stripped, re.DOTALL)
    if fence_match:
        candidates.insert(0, fence_match.group(1))
    brace_match = re.search(r"(\{.*\})", stripped, re.DOTALL)
    if brace_match:
        candidates.append(brace_match.group(1))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except Exception:
            logging.getLogger(__name__).debug("JSON parse attempt failed for candidate: %.120s", candidate)
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def extract_findings_payload(text: str) -> list[dict[str, object]] | None:
    payload = extract_json_payload(text)
    if payload is None:
        return None
    findings = payload.get("findings", [])
    if isinstance(findings, list):
        return findings
    return None


def _find_obligation(
    obligations: list[ProofObligation],
    step_index: int,
) -> ProofObligation | None:
    for obligation in obligations:
        if obligation.step_index == step_index:
            return obligation
    return None
