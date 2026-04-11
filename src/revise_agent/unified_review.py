from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

from .math_review import MathReviewRun, review_math_file
from .core_types import ProviderModelSpec
from .writing_review import WritingReviewRun, review_writing_file


@dataclass
class UnifiedReviewRun:
    source: Path
    run_dir: Path
    writing: WritingReviewRun | None
    math: MathReviewRun | None
    warnings: list[str]


def review_unified(
    file_path: str,
    output_dir: str | None = None,
    # writing-lane options
    venue_profile: str = "general-academic",
    reviewer_specs: list[ProviderModelSpec] | None = None,
    judge_spec: ProviderModelSpec | None = None,
    # math-lane options
    llm_proof_review: bool = False,
    targets: list[str] | None = None,
    math_reviewer_specs: list[ProviderModelSpec] | None = None,
    self_check_spec: ProviderModelSpec | None = None,
    adjudicator_spec: ProviderModelSpec | None = None,
    # shared options
    force_bootstrap: bool = False,
    timeout_seconds: int = 120,
) -> UnifiedReviewRun:
    source = Path(file_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Input file does not exist: {source}")
    if not source.is_file():
        raise IsADirectoryError(f"Input path is not a file: {source}")

    run_dir = _make_output_dir(source, output_dir)
    warnings: list[str] = []

    writing_dir = str(run_dir / "writing")
    math_dir = str(run_dir / "math")

    with ThreadPoolExecutor(max_workers=2) as pool:
        writing_future: Future[WritingReviewRun] = pool.submit(
            review_writing_file,
            file_path=file_path,
            output_dir=writing_dir,
            venue_profile=venue_profile,
            reviewer_specs=reviewer_specs,
            judge_spec=judge_spec,
            force_bootstrap=force_bootstrap,
            timeout_seconds=timeout_seconds,
        )
        math_future: Future[MathReviewRun] = pool.submit(
            review_math_file,
            file_path=file_path,
            output_dir=math_dir,
            llm_proof_review=llm_proof_review,
            targets=targets,
            reviewer_specs=math_reviewer_specs,
            self_check_spec=self_check_spec,
            adjudicator_spec=adjudicator_spec,
            force_bootstrap=force_bootstrap,
            timeout_seconds=timeout_seconds,
        )

        writing_result: WritingReviewRun | None = None
        math_result: MathReviewRun | None = None

        try:
            writing_result = writing_future.result()
        except Exception as exc:
            warnings.append(f"Writing review lane failed: {exc}")

        try:
            math_result = math_future.result()
        except Exception as exc:
            warnings.append(f"Math review lane failed: {exc}")

    _write_summary(run_dir, source, writing_result, math_result, warnings)

    return UnifiedReviewRun(
        source=source,
        run_dir=run_dir,
        writing=writing_result,
        math=math_result,
        warnings=warnings,
    )


def _make_output_dir(source: Path, output_dir: str | None) -> Path:
    if output_dir:
        run_dir = Path(output_dir).expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = Path.cwd() / "reviews" / f"{source.stem}-unified-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _write_summary(
    run_dir: Path,
    source: Path,
    writing: WritingReviewRun | None,
    math: MathReviewRun | None,
    warnings: list[str],
) -> None:
    lines = [
        "# ReviseAgent Unified Review",
        "",
        f"- Source: `{source}`",
        f"- Timestamp: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Lanes",
        "",
    ]

    if writing is not None:
        basic = sum(
            len(a.findings) for a in writing.artifacts if a.findings is not None and a.role == "basic"
        )
        structure = sum(
            len(a.findings) for a in writing.artifacts if a.findings is not None and a.role == "structure"
        )
        venue = sum(
            len(a.findings) for a in writing.artifacts if a.findings is not None and a.role == "venue"
        )
        lines.append(f"- Writing: completed (basic={basic}, structure={structure}, venue={venue})")
        lines.append(f"  - Venue profile: `{writing.venue_profile}`")
        lines.append(f"  - Mode: `{writing.mode}`")
        lines.append(f"  - Artifacts dir: `{writing.run_dir}`")
        if writing.final_report is not None:
            lines.append(f"  - Final report: `{writing.run_dir / 'final_report.md'}`")
    else:
        lines.append("- Writing: failed (see warnings)")

    lines.append("")

    if math is not None:
        refuted = sum(1 for i in math.issues if i.status == "machine-refuted")
        verified = sum(1 for i in math.issues if i.status == "machine-verified")
        suspected = sum(1 for i in math.issues if i.status == "llm-suspected")
        pending = sum(1 for i in math.issues if i.status == "needs-human-check")
        lines.append(
            f"- Math: completed (refuted={refuted}, verified={verified}, "
            f"suspected={suspected}, pending={pending}, blueprints={len(math.blueprints)})"
        )
        lines.append(f"  - Artifacts dir: `{math.run_dir}`")
        lines.append(f"  - Math report: `{math.run_dir / 'math_report.md'}`")
    else:
        lines.append("- Math: failed (see warnings)")

    if warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")

    (run_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    metadata = {
        "source": str(source),
        "writing_dir": str(writing.run_dir) if writing else None,
        "math_dir": str(math.run_dir) if math else None,
        "warnings": warnings,
    }
    (run_dir / "summary.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
