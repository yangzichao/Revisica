"""PRMBench adapter — import step-level error detection cases.

PRMBench provides math solutions with injected errors across 9 categories:
step_contradiction, circular, redundancy, confidence, domain_inconsistency,
counterfactual, missing_condition, deception, multi_solutions.

Each case has a modified solution with labeled error steps and classification.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re


PRMBENCH_LOCAL_PATH = "benchmarks/prmbench/raw"

PRMBENCH_CLASSIFICATIONS = {
    "step_contradiction",
    "circular",
    "redundancy",
    "confidence",
    "domain_inconsistency",
    "counterfactual",
    "missing_condition",
    "deception",
    "multi_solutions",
}


@dataclass
class PRMBenchImportResult:
    classification: str | None
    imported: int
    manifest_path: Path
    output_dir: Path


def import_prmbench_cases(
    classification: str | None = None,
    limit: int = 10,
    output_dir: str | None = None,
) -> PRMBenchImportResult:
    """Import PRMBench cases, optionally filtered by error classification.

    Args:
        classification: Filter to a specific error type (e.g. "circular").
                        None imports all types.
        limit: Maximum number of cases to import.
        output_dir: Override output directory.
    """
    if classification and classification not in PRMBENCH_CLASSIFICATIONS:
        raise ValueError(
            f"classification must be one of: {', '.join(sorted(PRMBENCH_CLASSIFICATIONS))}"
        )

    local_path = Path.cwd() / PRMBENCH_LOCAL_PATH
    if not local_path.exists():
        raise FileNotFoundError(
            f"PRMBench data not found at {local_path}. "
            "Download with: datasets.load_dataset('hitsmy/PRMBench_Preview').save_to_disk(...)"
        )

    from datasets import load_from_disk
    ds = load_from_disk(str(local_path))
    all_examples = list(ds["train"])

    if classification:
        all_examples = [ex for ex in all_examples if ex["classification"] == classification]
        examples = all_examples[:limit]
    else:
        # Stratified sampling: take equal number from each classification
        from collections import defaultdict
        by_cls: dict[str, list] = defaultdict(list)
        for ex in all_examples:
            by_cls[ex["classification"]].append(ex)
        per_cls = max(1, limit // len(by_cls)) if by_cls else limit
        examples = []
        for cls in sorted(by_cls):
            examples.extend(by_cls[cls][:per_cls])
        examples = examples[:limit]

    label = classification or "all"
    target_dir = (
        Path(output_dir).expanduser().resolve()
        if output_dir
        else Path.cwd() / "benchmarks" / "prmbench" / label
    )
    target_dir.mkdir(parents=True, exist_ok=True)

    cases: list[dict[str, object]] = []
    for index, ex in enumerate(examples, start=1):
        case_id = str(ex.get("idx", f"prmbench-{index}"))
        tex_name = f"{index:03d}_{_slugify(case_id)}.tex"
        tex_path = target_dir / tex_name
        tex_path.write_text(_render_prmbench_tex(ex), encoding="utf-8")

        error_steps = ex.get("error_steps", [])
        first_error = min(error_steps) if error_steps else -1

        cases.append(
            {
                "id": case_id,
                "file": tex_name,
                "classification": ex["classification"],
                "error_steps": error_steps,
                "modified_steps": ex.get("modified_steps", []),
                "reason": ex.get("reason", ""),
                "total_steps": len(ex.get("modified_process", [])),
                "expected": {
                    "expected_first_issue_step_zero_based": first_error - 1 if first_error > 0 else -1,
                },
            }
        )

    manifest = {
        "source": "PRMBench",
        "dataset": "hitsmy/PRMBench_Preview",
        "classification": classification,
        "imported_at": datetime.now().isoformat(timespec="seconds"),
        "cases": cases,
    }
    manifest_path = target_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    return PRMBenchImportResult(
        classification=classification,
        imported=len(cases),
        manifest_path=manifest_path,
        output_dir=target_dir,
    )


def _slugify(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return slug[:120] or "prmbench_case"


def _render_prmbench_tex(record: dict[str, object]) -> str:
    question = str(record.get("modified_question") or record.get("original_question", ""))
    steps = record.get("modified_process", [])
    rendered_steps = []
    for index, step in enumerate(steps):
        rendered_steps.append(f"Step {index}: {str(step).strip()}")
    proof_body = "\n".join(rendered_steps) if rendered_steps else "No reasoning steps provided."
    return "\n".join(
        [
            r"\documentclass{article}",
            r"\usepackage{amsmath}",
            r"\usepackage{amsthm}",
            "",
            r"\newtheorem{theorem}{Problem}",
            "",
            r"\begin{document}",
            "",
            r"\begin{theorem}",
            question.strip(),
            r"\end{theorem}",
            "",
            r"\begin{proof}",
            proof_body,
            r"\end{proof}",
            "",
            r"\end{document}",
            "",
        ]
    )
