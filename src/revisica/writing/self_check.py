"""Self-check pass: each reviewer's findings are re-verified to filter
false positives before they reach the judge."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ..agents import get_agent, to_agent_spec
from ..bootstrap import PlatformStatus
from ..core_types import ProviderModelSpec, ReviewResult
from ..model_router import resolve_model_for_role
from ..providers.execution import run_provider_agent
from .findings import extract_findings_payload
from .types import MAX_PARALLEL_WORKERS, WritingRoleArtifact

logger = logging.getLogger(__name__)


def run_writing_self_checks(
    source: Path,
    artifacts: list[WritingRoleArtifact],
    platforms: dict[str, PlatformStatus],
    selected_specs: list[ProviderModelSpec],
    schema_path: str | None,
    timeout_seconds: int,
    working_dir: str,
    warnings: list[str],
    codex_reasoning_effort: str | None = None,
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

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as pool:
        futures: dict[object, int] = {}

        for idx, artifact in checkable:
            # Use the same provider that produced the findings for self-check
            spec = ProviderModelSpec(provider=artifact.provider, model=artifact.model)
            routed_spec = resolve_model_for_role(spec, "writing-self-checker")

            task_prompt = build_writing_self_check_task(
                file_path=str(source),
                role=artifact.role,
                reviewer_label=artifact.provider if not artifact.model else f"{artifact.provider}:{artifact.model}",
                draft_findings=artifact.findings or [],
            )
            future = pool.submit(
                run_provider_agent,
                routed_spec.provider,
                task_prompt,
                checker_agent_spec,
                timeout_seconds,
                model=routed_spec.model,
                working_dir=working_dir,
                codex_reasoning_effort=codex_reasoning_effort,
            )
            futures[future] = idx

        for future in as_completed(futures):
            idx = futures[future]
            original = result_artifacts[idx]
            try:
                check_result: ReviewResult = future.result()
                if check_result.success:
                    checked_findings = extract_findings_payload(check_result.output)
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
                logger.warning(
                    "Writing self-check failed for %s/%s — keeping original findings",
                    original.provider, original.role, exc_info=True,
                )

    return result_artifacts


def build_writing_self_check_task(
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
