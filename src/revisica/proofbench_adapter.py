from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re

from .hf_datasets import fetch_dataset_rows


PROOFBENCH_DATASET = "wenjiema02/ProofBench"
PROOFBENCH_CONFIG = "default"


@dataclass
class ProofBenchImportResult:
    split: str
    imported: int
    manifest_path: Path
    output_dir: Path


def import_proofbench_cases(
    split: str = "train",
    limit: int = 10,
    output_dir: str | None = None,
) -> ProofBenchImportResult:
    normalized_split = _normalize_split(split)
    target_dir = (
        Path(output_dir).expanduser().resolve()
        if output_dir
        else Path.cwd() / "benchmarks" / "proofbench" / normalized_split
    )
    target_dir.mkdir(parents=True, exist_ok=True)

    records = fetch_dataset_rows(
        dataset=PROOFBENCH_DATASET,
        config=PROOFBENCH_CONFIG,
        split=normalized_split,
        offset=0,
        length=limit,
    )
    cases: list[dict[str, object]] = []
    for index, record in enumerate(records, start=1):
        case_id = f"{record['problem_id']}|{record['generator']}|{record['response_number']}"
        tex_name = f"{index:03d}_{_slugify(case_id)}.tex"
        tex_path = target_dir / tex_name
        tex_path.write_text(_render_proofbench_tex(record), encoding="utf-8")
        cases.append(
            {
                "id": case_id,
                "file": tex_name,
                "problem_id": record["problem_id"],
                "generator": record["generator"],
                "response_number": record["response_number"],
                "expert_rating": record["expert_rating"],
                "contest": record.get("metadata", {}).get("contest", ""),
                "contest_year": record.get("metadata", {}).get("contest_year", ""),
            }
        )

    manifest = {
        "source": "ProofBench",
        "dataset": PROOFBENCH_DATASET,
        "config": PROOFBENCH_CONFIG,
        "split": normalized_split,
        "imported_at": datetime.now().isoformat(timespec="seconds"),
        "cases": cases,
    }
    manifest_path = target_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return ProofBenchImportResult(
        split=normalized_split,
        imported=len(cases),
        manifest_path=manifest_path,
        output_dir=target_dir,
    )


def _normalize_split(split: str) -> str:
    lowered = split.lower()
    if lowered not in {"train", "best_of_n"}:
        raise ValueError("ProofBench split must be `train` or `best_of_n`.")
    return lowered


def _slugify(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return slug[:120] or "proofbench_case"


def _render_proofbench_tex(record: dict[str, object]) -> str:
    problem = str(record.get("problem", "")).strip()
    solution = str(record.get("model_solution", "")).strip()
    if not problem:
        problem = "No problem statement provided."
    if not solution:
        solution = "No model-generated proof provided."
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
            solution,
            r"\end{proof}",
            "",
            r"\end{document}",
            "",
        ]
    )
