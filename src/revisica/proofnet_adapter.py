from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
from urllib.request import urlopen

from .math_review import review_math_file


PROOFNET_RAW_BASE = "https://raw.githubusercontent.com/zhangir-azerbayev/ProofNet/main/benchmark"


@dataclass
class ProofNetImportResult:
    split: str
    imported: int
    manifest_path: Path
    output_dir: Path


@dataclass
class ProofNetBenchmarkCaseResult:
    case_id: str
    run_dir: Path
    blueprints: int
    machine_refuted: int
    machine_verified: int
    llm_suspected: int
    needs_human_check: int
    llm_provider_reviews: int
    llm_adjudications: int


@dataclass
class ProofNetBenchmarkResult:
    split: str
    manifest_path: Path
    report_dir: Path
    imported_cases: int
    case_results: list[ProofNetBenchmarkCaseResult]


def import_proofnet_cases(
    split: str = "test",
    limit: int = 10,
    output_dir: str | None = None,
) -> ProofNetImportResult:
    split = _normalize_split(split)
    target_dir = Path(output_dir).expanduser().resolve() if output_dir else Path.cwd() / "benchmarks" / "proofnet" / split
    target_dir.mkdir(parents=True, exist_ok=True)

    records = _download_proofnet_split(split)
    selected = records[:limit]
    cases = []
    for index, record in enumerate(selected, start=1):
        case_id = str(record["id"])
        safe_name = _slugify(case_id)
        tex_name = f"{index:03d}_{safe_name}.tex"
        tex_path = target_dir / tex_name
        tex_path.write_text(_render_proofnet_tex(record), encoding="utf-8")
        cases.append(
            {
                "id": case_id,
                "file": tex_name,
                "nl_statement": record.get("nl_statement", ""),
                "has_proof": bool(record.get("nl_proof", "").strip()),
            }
        )

    manifest = {
        "source": "ProofNet",
        "source_url": f"{PROOFNET_RAW_BASE}/{split}.jsonl",
        "split": split,
        "imported_at": datetime.now().isoformat(timespec="seconds"),
        "cases": cases,
    }
    manifest_path = target_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return ProofNetImportResult(
        split=split,
        imported=len(cases),
        manifest_path=manifest_path,
        output_dir=target_dir,
    )


def benchmark_proofnet(
    split: str = "test",
    limit: int = 10,
    output_dir: str | None = None,
    llm_proof_review: bool = False,
    targets: list[str] | None = None,
    force_bootstrap: bool = False,
    timeout_seconds: int = 120,
) -> ProofNetBenchmarkResult:
    imported = import_proofnet_cases(split=split, limit=limit, output_dir=output_dir)
    manifest = json.loads(imported.manifest_path.read_text(encoding="utf-8"))
    report_dir = imported.output_dir / "runs"
    report_dir.mkdir(parents=True, exist_ok=True)
    case_results: list[ProofNetBenchmarkCaseResult] = []

    for case in manifest["cases"]:
        source = imported.output_dir / case["file"]
        run = review_math_file(
            str(source),
            output_dir=str(report_dir / Path(case["file"]).stem),
            llm_proof_review=llm_proof_review,
            targets=targets,
            force_bootstrap=force_bootstrap,
            timeout_seconds=timeout_seconds,
        )
        case_results.append(
            ProofNetBenchmarkCaseResult(
                case_id=case["id"],
                run_dir=run.run_dir,
                blueprints=len(run.blueprints),
                machine_refuted=sum(1 for item in run.issues if item.status == "machine-refuted"),
                machine_verified=sum(1 for item in run.issues if item.status == "machine-verified"),
                llm_suspected=sum(1 for item in run.issues if item.status == "llm-suspected"),
                needs_human_check=sum(1 for item in run.issues if item.status == "needs-human-check"),
                llm_provider_reviews=len(run.llm_provider_results),
                llm_adjudications=len(run.llm_adjudication_results),
            )
        )

    summary = {
        "source": "ProofNet",
        "source_url": manifest["source_url"],
        "split": split,
        "imported_cases": len(case_results),
        "llm_proof_review": llm_proof_review,
        "targets": targets or [],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "aggregate": {
            "cases_with_blueprint": sum(1 for item in case_results if item.blueprints > 0),
            "cases_with_machine_refutation": sum(1 for item in case_results if item.machine_refuted > 0),
            "cases_with_llm_suspected": sum(1 for item in case_results if item.llm_suspected > 0),
            "cases_with_needs_human_check": sum(1 for item in case_results if item.needs_human_check > 0),
            "total_llm_provider_reviews": sum(item.llm_provider_reviews for item in case_results),
            "total_llm_adjudications": sum(item.llm_adjudications for item in case_results),
        },
        "cases": [
            {
                "case_id": item.case_id,
                "run_dir": str(item.run_dir),
                "blueprints": item.blueprints,
                "machine_refuted": item.machine_refuted,
                "machine_verified": item.machine_verified,
                "llm_suspected": item.llm_suspected,
                "needs_human_check": item.needs_human_check,
                "llm_provider_reviews": item.llm_provider_reviews,
                "llm_adjudications": item.llm_adjudications,
            }
            for item in case_results
        ],
    }
    (report_dir / "proofnet_benchmark_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    (report_dir / "proofnet_benchmark_summary.md").write_text(
        _render_proofnet_summary(summary),
        encoding="utf-8",
    )
    return ProofNetBenchmarkResult(
        split=split,
        manifest_path=imported.manifest_path,
        report_dir=report_dir,
        imported_cases=len(case_results),
        case_results=case_results,
    )


def _normalize_split(split: str) -> str:
    lowered = split.lower()
    if lowered not in {"test", "valid"}:
        raise ValueError("ProofNet split must be `test` or `valid`.")
    return lowered


def _download_proofnet_split(split: str) -> list[dict[str, object]]:
    url = f"{PROOFNET_RAW_BASE}/{split}.jsonl"
    with urlopen(url) as response:
        payload = response.read().decode("utf-8")
    records = []
    for line in payload.splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def _slugify(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return slug[:100] or "proofnet_case"


def _render_proofnet_tex(record: dict[str, object]) -> str:
    statement = str(record.get("nl_statement", "")).strip()
    proof = str(record.get("nl_proof", "")).strip()
    theorem_body = statement if statement else "No natural-language statement provided."
    proof_body = proof if proof else "No natural-language proof provided."
    return "\n".join(
        [
            r"\documentclass{article}",
            r"\usepackage{amsmath}",
            r"\usepackage{amsthm}",
            "",
            r"\newtheorem{theorem}{Theorem}",
            "",
            r"\begin{document}",
            "",
            r"\begin{theorem}",
            theorem_body,
            r"\end{theorem}",
            "",
            proof_body,
            "",
            r"\end{document}",
            "",
        ]
    )


def _render_proofnet_summary(summary: dict[str, object]) -> str:
    aggregate = summary["aggregate"]
    lines = [
        "# Revisica ProofNet Benchmark",
        "",
        f"- Source: `{summary['source_url']}`",
        f"- Split: `{summary['split']}`",
        f"- Imported cases: `{summary['imported_cases']}`",
        f"- LLM proof review: `{summary['llm_proof_review']}`",
        f"- Targets: `{', '.join(summary['targets']) if summary['targets'] else 'none'}`",
        f"- Cases with blueprint: `{aggregate['cases_with_blueprint']}`",
        f"- Cases with machine refutation: `{aggregate['cases_with_machine_refutation']}`",
        f"- Cases with LLM-suspected issues: `{aggregate['cases_with_llm_suspected']}`",
        f"- Cases with needs-human-check: `{aggregate['cases_with_needs_human_check']}`",
        f"- Total LLM provider reviews: `{aggregate['total_llm_provider_reviews']}`",
        f"- Total LLM adjudications: `{aggregate['total_llm_adjudications']}`",
        "",
        "## Cases",
        "",
    ]
    for case in summary["cases"]:
        lines.append(
            f"- `{case['case_id']}`: blueprints={case['blueprints']}, "
            f"machine_refuted={case['machine_refuted']}, "
            f"llm_suspected={case['llm_suspected']}, "
            f"needs_human_check={case['needs_human_check']}, "
            f"llm_provider_reviews={case['llm_provider_reviews']}, "
            f"llm_adjudications={case['llm_adjudications']} "
            f"(`{case['run_dir']}`)"
        )
    return "\n".join(lines) + "\n"
