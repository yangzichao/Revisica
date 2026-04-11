from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re

from .hf_datasets import fetch_dataset_rows


PROCESSBENCH_DATASET = "Qwen/ProcessBench"
PROCESSBENCH_CONFIG = "default"


@dataclass
class ProcessBenchImportResult:
    split: str
    imported: int
    manifest_path: Path
    output_dir: Path


def import_processbench_cases(
    split: str = "math",
    limit: int = 10,
    output_dir: str | None = None,
) -> ProcessBenchImportResult:
    normalized_split = _normalize_split(split)
    target_dir = (
        Path(output_dir).expanduser().resolve()
        if output_dir
        else Path.cwd() / "benchmarks" / "processbench" / normalized_split
    )
    target_dir.mkdir(parents=True, exist_ok=True)

    records = fetch_dataset_rows(
        dataset=PROCESSBENCH_DATASET,
        config=PROCESSBENCH_CONFIG,
        split=normalized_split,
        offset=0,
        length=limit,
    )
    cases: list[dict[str, object]] = []
    for index, record in enumerate(records, start=1):
        case_id = str(record["id"])
        tex_name = f"{index:03d}_{_slugify(case_id)}.tex"
        tex_path = target_dir / tex_name
        tex_path.write_text(_render_processbench_tex(record), encoding="utf-8")
        cases.append(
            {
                "id": case_id,
                "file": tex_name,
                "generator": record["generator"],
                "label": int(record["label"]),
                "final_answer_correct": bool(record["final_answer_correct"]),
                "steps": len(record.get("steps", [])),
                "expected": {
                    "expected_first_issue_step_zero_based": int(record["label"]),
                },
            }
        )

    manifest = {
        "source": "ProcessBench",
        "dataset": PROCESSBENCH_DATASET,
        "config": PROCESSBENCH_CONFIG,
        "split": normalized_split,
        "imported_at": datetime.now().isoformat(timespec="seconds"),
        "cases": cases,
    }
    manifest_path = target_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return ProcessBenchImportResult(
        split=normalized_split,
        imported=len(cases),
        manifest_path=manifest_path,
        output_dir=target_dir,
    )


def _normalize_split(split: str) -> str:
    lowered = split.lower()
    if lowered not in {"gsm8k", "math", "olympiadbench", "omnimath"}:
        raise ValueError("ProcessBench split must be one of gsm8k, math, olympiadbench, omnimath.")
    return lowered


def _slugify(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return slug[:120] or "processbench_case"


def _render_processbench_tex(record: dict[str, object]) -> str:
    problem = str(record.get("problem", "")).strip() or "No problem statement provided."
    steps = record.get("steps", [])
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
            problem,
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
