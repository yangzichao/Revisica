from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re

from .adjudication_policy import pick_preferred_item
from .agent_assets import find_agent_file
from .agents import get_agent, to_agent_spec
from .bootstrap import PlatformStatus, bootstrap, detect_platforms
from .claim_extractor import (
    build_claim_verification_task,
    extract_claims,
)
from .core_types import AgentSpec, ProviderModelSpec, ReviewResult
from .model_router import resolve_model_for_role
from .review import _run_provider_agent
from .section_combiner import (
    build_section_combo_task,
    extract_sections,
    generate_combinations,
)
from .templates import (
    SUPPORTED_VENUE_PROFILES,
    build_basic_writing_review_prompt,
    build_structure_writing_review_prompt,
    build_venue_style_review_prompt,
    build_writing_adjudication_prompt,
)


WRITING_ROLES = ("basic", "structure", "venue")
MATH_VERIFICATION_ROLES = ("math-claim-verifier", "notation-tracker", "formula-cross-checker")

# Maximum parallel workers for role/section-combo tasks
_MAX_PARALLEL_WORKERS = 12


@dataclass
class WritingRoleArtifact:
    role: str
    provider: str
    model: str | None
    result: ReviewResult
    findings: list[dict[str, object]] | None


@dataclass
class WritingReviewRun:
    source: Path
    run_dir: Path
    venue_profile: str
    detected_providers: list[str]
    reviewer_specs: list[ProviderModelSpec]
    judge_spec: ProviderModelSpec | None
    mode: str
    artifacts: list[WritingRoleArtifact]
    final_report: ReviewResult | None
    warnings: list[str]


def review_writing_file(
    file_path: str,
    output_dir: str | None = None,
    venue_profile: str = "general-academic",
    reviewer_specs: list[ProviderModelSpec] | None = None,
    judge_spec: ProviderModelSpec | None = None,
    force_bootstrap: bool = False,
    timeout_seconds: int = 120,
) -> WritingReviewRun:
    source = Path(file_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Input file does not exist: {source}")
    if not source.is_file():
        raise IsADirectoryError(f"Input path is not a file: {source}")
    if venue_profile not in SUPPORTED_VENUE_PROFILES:
        raise ValueError(
            "venue_profile must be one of: " + ", ".join(SUPPORTED_VENUE_PROFILES)
        )

    platforms = detect_platforms()
    detected = [name for name, platform in platforms.items() if platform.available]
    selected_specs, warnings = _resolve_reviewer_specs(platforms, reviewer_specs)
    mode = "cross-check" if len(selected_specs) >= 2 else "single-provider"

    required = list(selected_specs)
    if judge_spec is not None:
        required.append(judge_spec)
    missing_assets = sorted(
        {
            spec.provider
            for spec in required
            if spec.provider in platforms and platforms[spec.provider].available and not platforms[spec.provider].installed
        }
    )
    if missing_assets:
        bootstrap(missing_assets, force=force_bootstrap)
        platforms = detect_platforms()

    content = source.read_text(encoding="utf-8")
    run_dir = _make_output_dir(source, output_dir)
    working_dir = str(source.parent)
    schema_path = _find_codex_file("findings.schema.json")

    # ── Phase 1: Parallel role execution ─────────────────────────────
    # All writing roles, math verification roles, and section-combo
    # workers run concurrently.

    artifacts: list[WritingRoleArtifact] = []
    all_roles = list(WRITING_ROLES) + list(MATH_VERIFICATION_ROLES)

    # Generate section combinations for focused cross-analysis
    sections = extract_sections(content)
    section_combos = generate_combinations(sections)

    # Extract individual verifiable claims for per-claim verification
    extracted_claims = extract_claims(content)

    with ThreadPoolExecutor(max_workers=_MAX_PARALLEL_WORKERS) as pool:
        futures: dict[object, tuple[str, str]] = {}  # future → (role, spec_label)

        # Submit all standard role × provider tasks
        for role in all_roles:
            agent_spec = _build_agent_spec(role, schema_path)
            task_prompt = _build_agent_task(role, str(source), venue_profile)
            for spec in selected_specs:
                routed_spec = resolve_model_for_role(spec, role)
                platform = platforms[routed_spec.provider]
                future = pool.submit(
                    _run_single_role_task,
                    role=role,
                    spec=routed_spec,
                    platform=platform,
                    task_prompt=task_prompt,
                    agent_spec=agent_spec,
                    timeout_seconds=timeout_seconds,
                    working_dir=working_dir,
                )
                futures[future] = (role, routed_spec.label)

        # Submit section-combination cross-check tasks
        if section_combos:
            combo_agent_spec = to_agent_spec(
                get_agent("formula-cross-checker"), schema_path=schema_path,
            )
            for combo_idx, combo in enumerate(section_combos):
                combo_task = build_section_combo_task(combo, str(source))
                for spec in selected_specs:
                    routed_spec = resolve_model_for_role(spec, "section-cross-checker")
                    platform = platforms[routed_spec.provider]
                    combo_role = f"section-xcheck-{combo_idx}"
                    future = pool.submit(
                        _run_single_role_task,
                        role=combo_role,
                        spec=routed_spec,
                        platform=platform,
                        task_prompt=combo_task,
                        agent_spec=combo_agent_spec,
                        timeout_seconds=timeout_seconds,
                        working_dir=working_dir,
                    )
                    futures[future] = (combo_role, routed_spec.label)

        # Submit per-claim verification tasks (each claim gets its own SymPy worker)
        if extracted_claims:
            claim_agent_spec = to_agent_spec(
                get_agent("math-claim-verifier"), schema_path=schema_path,
            )
            for claim in extracted_claims:
                claim_task = build_claim_verification_task(claim, str(source))
                for spec in selected_specs:
                    routed_spec = resolve_model_for_role(spec, "math-claim-verifier")
                    platform = platforms[routed_spec.provider]
                    claim_role = f"claim-verify-{claim.claim_id}"
                    future = pool.submit(
                        _run_single_role_task,
                        role=claim_role,
                        spec=routed_spec,
                        platform=platform,
                        task_prompt=claim_task,
                        agent_spec=claim_agent_spec,
                        timeout_seconds=timeout_seconds,
                        working_dir=working_dir,
                    )
                    futures[future] = (claim_role, routed_spec.label)

        # Collect results as they complete
        for future in as_completed(futures):
            role, spec_label = futures[future]
            try:
                artifact = future.result()
                artifacts.append(artifact)
                _write_role_artifact(run_dir, artifact)
                if not artifact.result.success:
                    warnings.append(f"Role `{role}` failed for provider `{spec_label}`.")
            except Exception as exc:
                warnings.append(f"Role `{role}` raised exception for `{spec_label}`: {exc}")

    # ── Phase 2: Self-check (filter false positives) ─────────────────
    # Run a self-check on each role's findings to reduce noise.
    # This happens in parallel across all artifacts that have findings.

    checked_artifacts = _run_writing_self_checks(
        source=source,
        artifacts=artifacts,
        platforms=platforms,
        selected_specs=selected_specs,
        schema_path=schema_path,
        timeout_seconds=timeout_seconds,
        working_dir=working_dir,
        warnings=warnings,
    )

    # ── Phase 3: Judge (aggregate and distill) ───────────────────────
    final_report = _generate_final_report_agent(
        source=source,
        run_dir=run_dir,
        venue_profile=venue_profile,
        platforms=platforms,
        artifacts=checked_artifacts,
        judge_spec=judge_spec,
        schema_path=schema_path,
        timeout_seconds=timeout_seconds,
        warnings=warnings,
    )
    if final_report is not None:
        _write_final_report(run_dir, final_report)

    _write_summary(
        run_dir=run_dir,
        source=source,
        venue_profile=venue_profile,
        detected_providers=detected,
        reviewer_specs=selected_specs,
        judge_spec=judge_spec,
        mode=mode,
        artifacts=checked_artifacts,
        final_report=final_report,
        warnings=warnings,
    )
    return WritingReviewRun(
        source=source,
        run_dir=run_dir,
        venue_profile=venue_profile,
        detected_providers=detected,
        reviewer_specs=selected_specs,
        judge_spec=judge_spec,
        mode=mode,
        artifacts=checked_artifacts,
        final_report=final_report,
        warnings=warnings,
    )


# ── parallel task helper ─────────────────────────────────────────────


def _run_single_role_task(
    role: str,
    spec: ProviderModelSpec,
    platform: PlatformStatus,
    task_prompt: str,
    agent_spec: AgentSpec,
    timeout_seconds: int,
    working_dir: str,
) -> WritingRoleArtifact:
    """Execute a single (role, provider) task — designed to run in a thread."""
    result = _run_provider_agent(
        spec.provider,
        platform,
        task_prompt,
        agent_spec,
        timeout_seconds,
        model=spec.model,
        working_dir=working_dir,
    )
    findings = _extract_findings_payload(result.output)
    return WritingRoleArtifact(
        role=role,
        provider=spec.provider,
        model=spec.model,
        result=result,
        findings=findings,
    )


# ── writing self-check layer ─────────────────────────────────────────


def _run_writing_self_checks(
    source: Path,
    artifacts: list[WritingRoleArtifact],
    platforms: dict[str, PlatformStatus],
    selected_specs: list[ProviderModelSpec],
    schema_path: str | None,
    timeout_seconds: int,
    working_dir: str,
    warnings: list[str],
) -> list[WritingRoleArtifact]:
    """Run self-check on each artifact's findings to filter false positives.

    Returns the original artifacts list with findings replaced by
    self-checked versions where the self-check succeeds.
    """
    checkable = [
        (idx, a) for idx, a in enumerate(artifacts)
        if a.result.success and a.findings and len(a.findings) > 0
    ]
    if not checkable:
        return artifacts

    result_artifacts = list(artifacts)  # shallow copy

    checker_agent_spec = to_agent_spec(
        get_agent("writing-self-checker"), schema_path=schema_path,
    )

    with ThreadPoolExecutor(max_workers=_MAX_PARALLEL_WORKERS) as pool:
        futures: dict[object, int] = {}

        for idx, artifact in checkable:
            # Use the same provider that produced the findings for self-check
            spec = ProviderModelSpec(provider=artifact.provider, model=artifact.model)
            routed_spec = resolve_model_for_role(spec, "writing-self-checker")
            platform = platforms[routed_spec.provider]

            task_prompt = _build_writing_self_check_task(
                file_path=str(source),
                role=artifact.role,
                reviewer_label=artifact.provider if not artifact.model else f"{artifact.provider}:{artifact.model}",
                draft_findings=artifact.findings or [],
            )
            future = pool.submit(
                _run_provider_agent,
                routed_spec.provider,
                platform,
                task_prompt,
                checker_agent_spec,
                timeout_seconds,
                model=routed_spec.model,
                working_dir=working_dir,
            )
            futures[future] = idx

        for future in as_completed(futures):
            idx = futures[future]
            original = result_artifacts[idx]
            try:
                check_result: ReviewResult = future.result()
                if check_result.success:
                    checked_findings = _extract_findings_payload(check_result.output)
                    if checked_findings is not None:
                        original_count = len(original.findings or [])
                        filtered_count = len(checked_findings)
                        if filtered_count < original_count:
                            warnings.append(
                                f"Self-check filtered {original_count - filtered_count} "
                                f"false positive(s) from `{original.role}` ({original.provider})."
                            )
                        result_artifacts[idx] = WritingRoleArtifact(
                            role=original.role,
                            provider=original.provider,
                            model=original.model,
                            result=original.result,
                            findings=checked_findings,
                        )
            except Exception:
                # Self-check failed — keep original findings
                pass

    return result_artifacts


def _build_writing_self_check_task(
    file_path: str,
    role: str,
    reviewer_label: str,
    draft_findings: list[dict[str, object]],
) -> str:
    findings_json = json.dumps(draft_findings, indent=2, ensure_ascii=True)
    return (
        f"Self-check the writing review findings for the LaTeX draft at `{file_path}`.\n\n"
        f"These findings were produced by the `{role}` reviewer ({reviewer_label}).\n\n"
        f"Draft findings:\n```json\n{findings_json}\n```\n\n"
        f"Read the original LaTeX file, verify each finding against the source text, "
        f"and remove false positives, duplicates, and stylistic preferences. "
        f"Return JSON with a 'findings' array containing only the surviving findings."
    )


# ── reviewer spec resolution ─────────────────────────────────────────


def _resolve_reviewer_specs(
    platforms: dict[str, PlatformStatus],
    reviewer_specs: list[ProviderModelSpec] | None,
) -> tuple[list[ProviderModelSpec], list[str]]:
    warnings: list[str] = []
    if reviewer_specs:
        selected = [spec for spec in reviewer_specs if platforms[spec.provider].available]
        missing = [spec.label for spec in reviewer_specs if not platforms[spec.provider].available]
        if missing:
            warnings.append(
                "Requested writing-review provider(s) not installed: " + ", ".join(missing) + "."
            )
    else:
        selected = [
            ProviderModelSpec(provider=name)
            for name, platform in platforms.items()
            if platform.available
        ]
    if not selected:
        raise RuntimeError(
            "No supported provider detected in the current environment. "
            "Install codex and/or claude first, then run `revisica bootstrap`."
        )
    if len(selected) == 1:
        warnings.append(
            "Only one provider is active for writing review, so Revisica will run specialized roles "
            "and final judging on a single provider. Cross-check quality may be lower."
        )
    return selected, warnings


def _make_output_dir(source: Path, output_dir: str | None) -> Path:
    if output_dir:
        target = Path(output_dir).expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        target = Path.cwd() / "reviews" / f"{source.stem}-writing-{stamp}"
    target.mkdir(parents=True, exist_ok=True)
    return target


# ── real agent infrastructure ────────────────────────────────────────

def _find_codex_file(filename: str) -> str | None:
    return find_agent_file("codex", filename)


# Map role names to agent definition names in the unified registry
_ROLE_TO_AGENT_NAME = {
    "basic": "writing-basic-reviewer",
    "structure": "writing-structure-reviewer",
    "venue": "writing-venue-reviewer",
    "judge": "writing-judge",
    "math-claim-verifier": "math-claim-verifier",
    "notation-tracker": "notation-tracker",
    "formula-cross-checker": "formula-cross-checker",
}


def _build_agent_spec(role: str, schema_path: str | None) -> AgentSpec:
    """Build an AgentSpec for a writing-review or math-verification role."""
    agent_name = _ROLE_TO_AGENT_NAME.get(role, role)
    agent_definition = get_agent(agent_name)
    return to_agent_spec(agent_definition, schema_path=schema_path)


def _build_agent_task(role: str, file_path: str, venue_profile: str) -> str:
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


def _extract_findings_payload(output: str) -> list[dict[str, object]] | None:
    """Extract a JSON findings array from agent output.

    Real agents may wrap JSON in narrative text or fenced code blocks.
    We try multiple strategies: direct parse, fenced-block extraction,
    and scanning for the first { ... } containing "findings".
    """
    text = output.strip()
    if not text:
        return None

    # Strategy 1: direct JSON parse
    parsed = _try_parse_findings(text)
    if parsed is not None:
        return parsed

    # Strategy 2: extract from fenced code block (```json ... ```)
    for match in re.finditer(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL):
        parsed = _try_parse_findings(match.group(1).strip())
        if parsed is not None:
            return parsed

    # Strategy 3: find first { that contains "findings"
    start = text.find('{"findings"')
    if start == -1:
        start = text.find('"findings"')
        if start != -1:
            # backtrack to opening brace
            start = text.rfind("{", 0, start)
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    parsed = _try_parse_findings(text[start : i + 1])
                    if parsed is not None:
                        return parsed
                    break

    return None


def _try_parse_findings(text: str) -> list[dict[str, object]] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    findings = payload.get("findings")
    if not isinstance(findings, list):
        return None
    return [f for f in findings if isinstance(f, dict)]


def _generate_final_report_agent(
    source: Path,
    run_dir: Path,
    venue_profile: str,
    platforms: dict[str, PlatformStatus],
    artifacts: list[WritingRoleArtifact],
    judge_spec: ProviderModelSpec | None,
    schema_path: str | None,
    timeout_seconds: int,
    warnings: list[str],
) -> ReviewResult | None:
    """Generate final report using a real judge agent that reads findings files."""
    usable = [a for a in artifacts if a.result.success and a.findings is not None]
    if not usable:
        warnings.append("No writing-review role produced a usable structured output.")
        return None

    judge = judge_spec or _default_judge_spec(usable)
    judge = resolve_model_for_role(judge, "judge")
    platform = platforms[judge.provider]

    # Build file list for the judge to read
    findings_files = []
    for artifact in usable:
        base = f"{artifact.role}_{_artifact_label(artifact.provider, artifact.model)}"
        json_path = run_dir / f"{base}.json"
        if json_path.exists():
            findings_files.append(str(json_path))

    agent_spec = to_agent_spec(get_agent("writing-judge"))
    task_prompt = (
        f"You are the final judge for a writing review.\n\n"
        f"Original LaTeX draft: `{source}`\n"
        f"Target venue profile: `{venue_profile}`\n\n"
        f"Read the original LaTeX file and then read these findings files:\n"
        + "\n".join(f"- `{fp}`" for fp in findings_files)
        + "\n\nMerge duplicates, keep only the strongest actionable points. "
        f"Produce a single Markdown report with sections: "
        f"Executive Summary, Basic Language Issues, Structure and Logic Issues, "
        f"Scholarly Rhetoric Issues, Venue-Style Gap, Suggested Rewrites, "
        f"Needs Human Check, Revision Priorities."
    )

    result = _run_provider_agent(
        judge.provider,
        platform,
        task_prompt,
        agent_spec,
        timeout_seconds,
        model=judge.model,
        working_dir=str(source.parent),
    )
    if result.success:
        return result

    warnings.append("Writing-review final adjudication failed, falling back to merged raw report.")
    return ReviewResult(
        provider=judge.provider,
        model=judge.model,
        command=[],
        returncode=0,
        output=_fallback_final_report(usable, venue_profile),
        stderr="",
    )


def _default_judge_spec(artifacts: list[WritingRoleArtifact]) -> ProviderModelSpec:
    selected = pick_preferred_item(
        artifacts,
        provider_getter=lambda artifact: artifact.provider,
    )
    return ProviderModelSpec(provider=selected.provider, model=selected.model)


def _fallback_final_report(artifacts: list[WritingRoleArtifact], venue_profile: str) -> str:
    sections = [
        "# Executive Summary",
        "Writing-review adjudication failed. This fallback report preserves raw role outputs.",
        "",
        "## Basic Language Issues",
        "",
        "See raw role outputs below.",
        "",
        "## Structure and Logic Issues",
        "",
        "See raw role outputs below.",
        "",
        "## Scholarly Rhetoric Issues",
        "",
        "See raw role outputs below.",
        "",
        "## Venue-Style Gap",
        "",
        f"Target profile: `{venue_profile}`.",
        "",
        "## Suggested Rewrites",
        "",
        "Inspect raw role outputs for rewrite suggestions.",
        "",
        "## Needs Human Check",
        "",
        "The final judge did not complete successfully.",
        "",
        "## Revision Priorities",
        "",
        "1. Inspect raw role outputs below.",
        "",
        "## Raw Role Outputs",
        "",
    ]
    for artifact in artifacts:
        label = artifact.provider if not artifact.model else f"{artifact.provider}:{artifact.model}"
        sections.append(f"### {artifact.role} from {label}")
        sections.append("")
        sections.append("```json")
        sections.append(json.dumps(artifact.findings, indent=2, ensure_ascii=True))
        sections.append("```")
        sections.append("")
    return "\n".join(sections).strip() + "\n"


def _write_role_artifact(run_dir: Path, artifact: WritingRoleArtifact) -> None:
    base = f"{artifact.role}_{_artifact_label(artifact.provider, artifact.model)}"
    (run_dir / f"{base}.md").write_text(artifact.result.output, encoding="utf-8")
    metadata = {
        "role": artifact.role,
        "provider": artifact.provider,
        "model": artifact.model,
        "returncode": artifact.result.returncode,
        "success": artifact.result.success,
        "findings": artifact.findings,
    }
    (run_dir / f"{base}.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    if artifact.result.stderr.strip():
        (run_dir / f"{base}.stderr.txt").write_text(artifact.result.stderr, encoding="utf-8")


def _write_final_report(run_dir: Path, result: ReviewResult) -> None:
    (run_dir / "final_report.md").write_text(result.output, encoding="utf-8")
    payload = {
        "provider": result.provider,
        "model": result.model,
        "returncode": result.returncode,
        "success": result.success,
        "command": result.command,
    }
    (run_dir / "final_report.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    if result.stderr.strip():
        (run_dir / "final_report.stderr.txt").write_text(result.stderr, encoding="utf-8")


def _write_summary(
    run_dir: Path,
    source: Path,
    venue_profile: str,
    detected_providers: list[str],
    reviewer_specs: list[ProviderModelSpec],
    judge_spec: ProviderModelSpec | None,
    mode: str,
    artifacts: list[WritingRoleArtifact],
    final_report: ReviewResult | None,
    warnings: list[str],
) -> None:
    all_roles = list(WRITING_ROLES) + list(MATH_VERIFICATION_ROLES)
    issues_by_role: dict[str, int] = {role: 0 for role in all_roles}
    for artifact in artifacts:
        if artifact.findings is not None:
            issues_by_role.setdefault(artifact.role, 0)
            issues_by_role[artifact.role] += len(artifact.findings)

    # Count section cross-check and claim verification findings
    section_xcheck_count = sum(
        len(a.findings) for a in artifacts
        if a.role.startswith("section-xcheck-") and a.findings is not None
    )

    lines = [
        "# Revisica Writing Review Run",
        "",
        f"- Source: `{source}`",
        f"- Timestamp: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Venue profile: `{venue_profile}`",
        f"- Detected providers: `{', '.join(detected_providers) if detected_providers else 'none'}`",
        f"- Reviewers: `{', '.join(spec.label for spec in reviewer_specs)}`",
        f"- Judge: `{judge_spec.label if judge_spec is not None else 'auto'}`",
        f"- Mode: `{mode}`",
        f"- Basic findings: `{issues_by_role['basic']}`",
        f"- Structure findings: `{issues_by_role['structure']}`",
        f"- Venue findings: `{issues_by_role['venue']}`",
        f"- Math-claim-verifier findings: `{issues_by_role.get('math-claim-verifier', 0)}`",
        f"- Notation-tracker findings: `{issues_by_role.get('notation-tracker', 0)}`",
        f"- Formula-cross-checker findings: `{issues_by_role.get('formula-cross-checker', 0)}`",
        f"- Section cross-check findings: `{section_xcheck_count}`",
        f"- Claim verification findings: `{sum(len(a.findings) for a in artifacts if a.role.startswith('claim-verify-') and a.findings is not None)}`",
        "",
        "## Role Runs",
        "",
    ]
    for artifact in artifacts:
        status = "ok" if artifact.result.success else "failed"
        label = artifact.provider if not artifact.model else f"{artifact.provider}:{artifact.model}"
        lines.append(f"- `{artifact.role}` via `{label}`: {status} (exit={artifact.result.returncode})")
    if warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
    lines.extend(["", "## Files", ""])
    for artifact in artifacts:
        base = f"{artifact.role}_{_artifact_label(artifact.provider, artifact.model)}"
        lines.append(f"- `{base}.md`")
        lines.append(f"- `{base}.json`")
        if artifact.result.stderr.strip():
            lines.append(f"- `{base}.stderr.txt`")
    if final_report is not None:
        lines.append("- `final_report.md`")
        lines.append("- `final_report.json`")
        if final_report.stderr.strip():
            lines.append("- `final_report.stderr.txt`")
    (run_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _artifact_label(provider: str, model: str | None) -> str:
    if not model:
        return provider
    cleaned = "".join(char if char.isalnum() else "_" for char in model).strip("_")
    return f"{provider}_{cleaned}" if cleaned else provider
