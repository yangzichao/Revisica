"""Writing review node functions for LangGraph.

Each function reads from WritingState and returns a partial dict update.
Helper functions are imported from writing_review.py (the library).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ...agents import get_agent, to_agent_spec
from ...bootstrap import detect_platforms, bootstrap
from ...claim_extractor import (
    build_claim_verification_task,
    extract_claims,
)
from ...core_types import ProviderModelSpec
from ...model_router import resolve_model_for_role
from ...section_combiner import (
    build_section_combo_task,
    extract_sections,
    generate_combinations,
)
from ...templates import SUPPORTED_VENUE_PROFILES
from ...writing_review import (
    WRITING_ROLES,
    MATH_VERIFICATION_ROLES,
    WritingRoleArtifact,
    WritingReviewRun,
    _MAX_PARALLEL_WORKERS,
    _resolve_reviewer_specs,
    _make_output_dir,
    _find_codex_file,
    _build_agent_spec,
    _build_agent_task,
    _run_single_role_task,
    _run_writing_self_checks,
    _generate_final_report_agent,
    _write_role_artifact,
    _write_final_report,
    _write_summary,
)
from ..state import WritingState


def bootstrap_and_extract(state: WritingState) -> dict:
    """Validate source, detect platforms, resolve specs, extract structure."""
    config = state.get("config")
    source_path = state["source_path"]

    source = Path(source_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Input file does not exist: {source}")
    if not source.is_file():
        raise IsADirectoryError(f"Input path is not a file: {source}")

    venue_profile = config.venue_profile if config else "general-academic"
    if venue_profile not in SUPPORTED_VENUE_PROFILES:
        raise ValueError(
            "venue_profile must be one of: " + ", ".join(SUPPORTED_VENUE_PROFILES)
        )

    force_bootstrap = config.force_bootstrap if config else False
    reviewer_specs = config.providers if config else None
    judge_spec = config.judge_spec if config else None
    timeout_seconds = config.timeout_seconds if config else 120

    platforms = detect_platforms()
    detected = [name for name, p in platforms.items() if p.available]
    selected_specs, warnings = _resolve_reviewer_specs(platforms, reviewer_specs)
    mode = "cross-check" if len(selected_specs) >= 2 else "single-provider"

    # Bootstrap missing assets
    required = list(selected_specs)
    if judge_spec is not None:
        required.append(judge_spec)
    missing_assets = sorted(
        {
            spec.provider
            for spec in required
            if spec.provider in platforms
            and platforms[spec.provider].available
            and not platforms[spec.provider].installed
        }
    )
    if missing_assets:
        bootstrap(missing_assets, force=force_bootstrap)
        platforms = detect_platforms()

    content = source.read_text(encoding="utf-8")
    run_dir_str = state.get("run_dir", "")
    run_dir = _make_output_dir(source, run_dir_str or None)
    working_dir = str(source.parent)
    schema_path = _find_codex_file("findings.schema.json")

    # Extract sections, combinations, and claims
    sections = extract_sections(content)
    section_combos = generate_combinations(sections)
    extracted_claims = extract_claims(content)

    return {
        "source_path": str(source),
        "content": content,
        "run_dir": str(run_dir),
        "sections": sections,
        "section_combos": section_combos,
        "claims": extracted_claims,
        "platforms": platforms,
        "selected_specs": selected_specs,
        "detected_providers": detected,
        "mode": mode,
        "schema_path": schema_path,
        "working_dir": working_dir,
        "venue_profile": venue_profile,
        "judge_spec": judge_spec,
        "warnings": warnings,
    }


def run_parallel_roles(state: WritingState) -> dict:
    """Run all writing/math roles, section combos, and claims in parallel."""
    config = state.get("config")
    selected_specs = state["selected_specs"]
    platforms = state["platforms"]
    schema_path = state.get("schema_path")
    working_dir = state["working_dir"]
    source_path = state["source_path"]
    venue_profile = state["venue_profile"]
    section_combos = state.get("section_combos", [])
    extracted_claims = state.get("claims", [])
    run_dir = Path(state["run_dir"])
    timeout_seconds = config.timeout_seconds if config else 120
    codex_reasoning_effort = config.codex_reasoning_effort if config else None

    artifacts: list[WritingRoleArtifact] = []
    warnings: list[str] = []
    all_roles = list(WRITING_ROLES) + list(MATH_VERIFICATION_ROLES)

    with ThreadPoolExecutor(max_workers=_MAX_PARALLEL_WORKERS) as pool:
        futures: dict[object, tuple[str, str]] = {}

        # Submit all standard role × provider tasks
        for role in all_roles:
            agent_spec = _build_agent_spec(role, schema_path)
            task_prompt = _build_agent_task(role, source_path, venue_profile)
            for spec in selected_specs:
                routed_spec = resolve_model_for_role(spec, role)
                future = pool.submit(
                    _run_single_role_task,
                    role=role,
                    spec=routed_spec,
                    task_prompt=task_prompt,
                    agent_spec=agent_spec,
                    timeout_seconds=timeout_seconds,
                    working_dir=working_dir,
                    codex_reasoning_effort=codex_reasoning_effort,
                )
                futures[future] = (role, routed_spec.label)

        # Submit section-combination cross-check tasks
        if section_combos:
            combo_agent_spec = to_agent_spec(
                get_agent("formula-cross-checker"), schema_path=schema_path,
            )
            for combo_idx, combo in enumerate(section_combos):
                combo_task = build_section_combo_task(combo, source_path)
                for spec in selected_specs:
                    routed_spec = resolve_model_for_role(spec, "section-cross-checker")
                    combo_role = f"section-xcheck-{combo_idx}"
                    future = pool.submit(
                        _run_single_role_task,
                        role=combo_role,
                        spec=routed_spec,
                        task_prompt=combo_task,
                        agent_spec=combo_agent_spec,
                        timeout_seconds=timeout_seconds,
                        working_dir=working_dir,
                        codex_reasoning_effort=codex_reasoning_effort,
                    )
                    futures[future] = (combo_role, routed_spec.label)

        # Submit per-claim verification tasks
        if extracted_claims:
            claim_agent_spec = to_agent_spec(
                get_agent("math-claim-verifier"), schema_path=schema_path,
            )
            for claim in extracted_claims:
                claim_task = build_claim_verification_task(claim, source_path)
                for spec in selected_specs:
                    routed_spec = resolve_model_for_role(spec, "math-claim-verifier")
                    claim_role = f"claim-verify-{claim.claim_id}"
                    future = pool.submit(
                        _run_single_role_task,
                        role=claim_role,
                        spec=routed_spec,
                        task_prompt=claim_task,
                        agent_spec=claim_agent_spec,
                        timeout_seconds=timeout_seconds,
                        working_dir=working_dir,
                        codex_reasoning_effort=codex_reasoning_effort,
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

    return {
        "artifacts": artifacts,
        "warnings": warnings,
    }


def run_self_checks(state: WritingState) -> dict:
    """Filter false positives from role findings via self-check."""
    config = state.get("config")
    source = Path(state["source_path"])
    artifacts = state.get("artifacts", [])
    platforms = state["platforms"]
    selected_specs = state["selected_specs"]
    schema_path = state.get("schema_path")
    working_dir = state["working_dir"]
    timeout_seconds = config.timeout_seconds if config else 120
    codex_reasoning_effort = config.codex_reasoning_effort if config else None

    # _run_writing_self_checks mutates its own warnings list;
    # we pass a local list and return it via the reducer.
    local_warnings: list[str] = []
    checked = _run_writing_self_checks(
        source=source,
        artifacts=artifacts,
        platforms=platforms,
        selected_specs=selected_specs,
        schema_path=schema_path,
        timeout_seconds=timeout_seconds,
        working_dir=working_dir,
        warnings=local_warnings,
        codex_reasoning_effort=codex_reasoning_effort,
    )
    return {
        "artifacts": checked,
        "warnings": local_warnings,
    }


def run_judge(state: WritingState) -> dict:
    """Generate final report by aggregating all role findings."""
    config = state.get("config")
    source = Path(state["source_path"])
    run_dir = Path(state["run_dir"])
    venue_profile = state["venue_profile"]
    platforms = state["platforms"]
    artifacts = state.get("artifacts", [])
    judge_spec = state.get("judge_spec")
    schema_path = state.get("schema_path")
    timeout_seconds = config.timeout_seconds if config else 120
    codex_reasoning_effort = config.codex_reasoning_effort if config else None

    local_warnings: list[str] = []
    final_report = _generate_final_report_agent(
        source=source,
        run_dir=run_dir,
        venue_profile=venue_profile,
        platforms=platforms,
        artifacts=artifacts,
        judge_spec=judge_spec,
        schema_path=schema_path,
        timeout_seconds=timeout_seconds,
        warnings=local_warnings,
        codex_reasoning_effort=codex_reasoning_effort,
    )
    if final_report is not None:
        _write_final_report(run_dir, final_report)

    return {
        "final_report": final_report,
        "warnings": local_warnings,
    }


def write_summary(state: WritingState) -> dict:
    """Write summary file and construct WritingReviewRun."""
    source = Path(state["source_path"])
    run_dir = Path(state["run_dir"])
    venue_profile = state["venue_profile"]
    detected_providers = state.get("detected_providers", [])
    selected_specs = state.get("selected_specs", [])
    judge_spec = state.get("judge_spec")
    mode = state.get("mode", "single-provider")
    artifacts = state.get("artifacts", [])
    final_report = state.get("final_report")
    warnings = state.get("warnings", [])

    _write_summary(
        run_dir=run_dir,
        source=source,
        venue_profile=venue_profile,
        detected_providers=detected_providers,
        reviewer_specs=selected_specs,
        judge_spec=judge_spec,
        mode=mode,
        artifacts=artifacts,
        final_report=final_report,
        warnings=warnings,
    )

    run = WritingReviewRun(
        source=source,
        run_dir=run_dir,
        venue_profile=venue_profile,
        detected_providers=detected_providers,
        reviewer_specs=selected_specs,
        judge_spec=judge_spec,
        mode=mode,
        artifacts=artifacts,
        final_report=final_report,
        warnings=warnings,
    )
    return {"writing_review_run": run}
