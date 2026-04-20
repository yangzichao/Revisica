from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .core_types import ProviderModelSpec
from .math_review import MathReviewRun
from .run_dir_helpers import copy_source_into_run_dir
from .writing_review import WritingReviewRun


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
    # new: review mode
    mode: str = "review",
    # new: explicit parser selection (defaults to auto)
    parser: str = "auto",
    # new: Codex reasoning effort override
    # (none|minimal|low|medium|high|xhigh; None = agent default).
    codex_reasoning_effort: str | None = None,
) -> UnifiedReviewRun:
    """Run unified review via LangGraph."""
    from .graphs.unified import compile_unified_graph
    from .profiles.config import ReviewConfig, ReviewMode

    source = Path(file_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Input file does not exist: {source}")
    if not source.is_file():
        raise IsADirectoryError(f"Input path is not a file: {source}")

    run_dir = _make_output_dir(source, output_dir)
    copy_source_into_run_dir(source, run_dir)

    mode_enum = ReviewMode.POLISH if mode == "polish" else ReviewMode.REVIEW
    config = ReviewConfig(
        mode=mode_enum,
        venue_profile=venue_profile,
        providers=reviewer_specs or [],
        judge_spec=judge_spec,
        llm_proof_review=llm_proof_review,
        force_bootstrap=force_bootstrap,
        timeout_seconds=timeout_seconds,
        math_targets=targets,
        math_reviewer_specs=math_reviewer_specs,
        self_check_spec=self_check_spec,
        adjudicator_spec=adjudicator_spec,
        codex_reasoning_effort=codex_reasoning_effort,
    )

    graph = compile_unified_graph()
    final_state = graph.invoke({
        "source_path": str(source),
        "run_dir": str(run_dir),
        "config": config,
        "parser": parser,
        "warnings": [],
    })

    run = final_state.get("unified_review_run")
    if run is None:
        warnings = final_state.get("warnings", [])
        return UnifiedReviewRun(
            source=source,
            run_dir=run_dir,
            writing=None,
            math=None,
            warnings=list(warnings),
        )
    return run


def _make_output_dir(source: Path, output_dir: str | None) -> Path:
    if output_dir:
        run_dir = Path(output_dir).expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = Path.cwd() / "reviews" / f"{source.stem}-unified-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
