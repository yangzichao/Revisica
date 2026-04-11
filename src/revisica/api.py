"""FastAPI server wrapping graph execution.

Start with: ``revisica serve`` or ``python -m revisica.api``
"""

from __future__ import annotations

import argparse
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .ingestion import parse_document
from .providers import get_registry
from .providers.provider_config import load_config, save_config
from .unified_review import review_unified

app = FastAPI(title="Revisica API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── in-memory run state ─────────────────────────────────────────────


class RunState:
    """Tracks a single review run's progress."""

    def __init__(self, run_id: str, config: dict[str, Any]):
        self.run_id = run_id
        self.config = config
        self.state = "running"
        self.started_at = datetime.now().isoformat()
        self.completed_at: str | None = None
        self.run_dir: str | None = None
        self.tasks: list[dict[str, str]] = []
        self.error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "state": self.state,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "run_dir": self.run_dir,
            "tasks": self.tasks,
            "error": self.error,
        }


_runs: dict[str, RunState] = {}


# ── request/response models ──────────────────���──────────────────────


class ReviewRequest(BaseModel):
    file_path: str
    mode: str = "review"
    venue_profile: str = "general-academic"
    custom_instructions: str | None = None
    llm_proof_review: bool = False
    timeout_seconds: int = 120


class ProviderConfigUpdate(BaseModel):
    api_key: str | None = None
    enabled: bool | None = None
    base_url: str | None = None
    default_model: str | None = None


class IngestRequest(BaseModel):
    file_path: str
    parser: str = "auto"


# ── endpoints ───────────────────────────────────────────────────────


@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/providers")
def list_providers():
    registry = get_registry()
    providers = []
    for provider in registry.list_all():
        providers.append({
            "name": provider.name,
            "display_name": provider.display_name,
            "model_family": provider.model_family,
            "available": provider.is_available(),
        })
    return {"providers": providers}


@app.put("/api/providers/{provider_name}/config")
def update_provider_config(provider_name: str, update: ProviderConfigUpdate):
    config = load_config()
    provider_section = config.setdefault("providers", {}).setdefault(provider_name, {})
    if update.api_key is not None:
        provider_section["api_key"] = update.api_key
    if update.enabled is not None:
        provider_section["enabled"] = update.enabled
    if update.base_url is not None:
        provider_section["base_url"] = update.base_url
    if update.default_model is not None:
        provider_section["default_model"] = update.default_model
    save_config(config)
    return {"status": "updated", "provider": provider_name}


@app.post("/api/providers/{provider_name}/test")
def test_provider(provider_name: str):
    try:
        registry = get_registry()
        provider = registry.get(provider_name)
        if not provider.is_available():
            return {"status": "unavailable", "message": f"{provider_name} is not configured."}
        result = provider.run_prompt("Say 'hello' in one word.", timeout_seconds=30)
        return {
            "status": "ok" if result.success else "failed",
            "output_preview": result.output[:200],
        }
    except Exception as error:
        return {"status": "error", "message": str(error)}


@app.post("/api/ingest")
def ingest_document(request: IngestRequest):
    try:
        document = parse_document(request.file_path, parser=request.parser)
        return {
            "parser_used": document.parser_used,
            "title": document.metadata.title,
            "authors": document.metadata.authors,
            "section_count": len(document.sections),
            "sections": [
                {"id": section.id, "title": section.title, "level": section.level}
                for section in _flatten_sections(document.sections)
            ],
        }
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/api/review")
def start_review(request: ReviewRequest):
    run_id = str(uuid.uuid4())[:8]
    run_state = RunState(run_id, request.model_dump())
    _runs[run_id] = run_state

    thread = threading.Thread(
        target=_execute_review,
        args=(run_id, request),
        daemon=True,
    )
    thread.start()

    return {"run_id": run_id, "status": "started"}


@app.get("/api/status/{run_id}")
def get_run_status(run_id: str):
    run_state = _runs.get(run_id)
    if run_state is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return run_state.to_dict()


@app.get("/api/results/{run_id}")
def get_run_results(run_id: str):
    run_state = _runs.get(run_id)
    if run_state is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    if run_state.state != "completed":
        raise HTTPException(status_code=409, detail=f"Run is still {run_state.state}.")

    run_dir = Path(run_state.run_dir) if run_state.run_dir else None
    if not run_dir or not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run directory not found.")

    summary = ""
    summary_path = run_dir / "summary.md"
    if summary_path.exists():
        summary = summary_path.read_text(encoding="utf-8")

    writing_report = ""
    writing_report_path = run_dir / "writing" / "final_report.md"
    if writing_report_path.exists():
        writing_report = writing_report_path.read_text(encoding="utf-8")

    math_report = ""
    math_report_path = run_dir / "math" / "math_report.md"
    if math_report_path.exists():
        math_report = math_report_path.read_text(encoding="utf-8")

    return {
        "run_id": run_id,
        "summary": summary,
        "writing_report": writing_report,
        "math_report": math_report,
        "run_dir": str(run_dir),
    }


# ── background execution ────────────────────────────────────────────


def _execute_review(run_id: str, request: ReviewRequest) -> None:
    """Run a review in a background thread."""
    run_state = _runs[run_id]

    try:
        run_state.tasks.append({"name": "review", "status": "running"})

        review_result = review_unified(
            file_path=request.file_path,
            venue_profile=request.venue_profile,
            llm_proof_review=request.llm_proof_review,
            timeout_seconds=request.timeout_seconds,
        )

        run_state.run_dir = str(review_result.run_dir)
        run_state.state = "completed"
        run_state.completed_at = datetime.now().isoformat()
        run_state.tasks = [{"name": "review", "status": "completed"}]

    except Exception as error:
        run_state.state = "failed"
        run_state.error = str(error)
        run_state.completed_at = datetime.now().isoformat()
        run_state.tasks = [{"name": "review", "status": "failed", "detail": str(error)[:200]}]


# ── helpers ─────────────────────────────────────────────────────────


def _flatten_sections(sections) -> list:
    """Flatten a nested section tree for API response."""
    result = []
    for section in sections:
        result.append(section)
        result.extend(_flatten_sections(section.children))
    return result


# ── CLI entry point ─────────────────────────────────────────────────


def main() -> None:
    """Run the API server (called by ``revisica serve``)."""
    import uvicorn

    parser = argparse.ArgumentParser(description="Revisica API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18321)
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
