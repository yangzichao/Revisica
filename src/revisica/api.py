"""FastAPI server wrapping graph execution.

Start with: ``revisica serve`` or ``python -m revisica.api``
"""

from __future__ import annotations

import argparse
import os
import secrets
import threading
import uuid
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .ingestion import parse_document
from .providers import get_registry
from .providers.provider_config import load_config, save_config
from .unified_review import review_unified


def _load_or_create_api_token() -> str:
    """Return the shared API token, generating one if none is supplied.

    Honors ``REVISICA_API_TOKEN`` when the caller (e.g. the Electron launcher)
    minted one. Otherwise mints a fresh token and persists it at
    ``~/.revisica/api-token`` with 0600 perms for standalone ``revisica serve``.
    """
    env_token = os.environ.get("REVISICA_API_TOKEN")
    if env_token:
        return env_token
    token_dir = Path.home() / ".revisica"
    token_dir.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(token_dir, 0o700)
    except OSError:
        pass
    token_path = token_dir / "api-token"
    token = secrets.token_urlsafe(32)
    fd = os.open(str(token_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(token)
    return token


_API_TOKEN = _load_or_create_api_token()


def require_api_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Malformed Authorization header.")
    if not secrets.compare_digest(parts[1].strip(), _API_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid token.")


AUTH = [Depends(require_api_token)]


app = FastAPI(title="Revisica API", version="0.1.0")

# Token auth is the primary defense against CSRF from the user's browser;
# CORS is also tightened so cross-origin preflights are refused outright.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=(
        r"^(null|file://.*|https?://localhost(:\d+)?|https?://127\.0\.0\.1(:\d+)?)$"
    ),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── in-memory run state ─────────────────────────────────────────────


class RunState:
    """Tracks a single review run's progress. Thread-safe via internal lock."""

    def __init__(self, run_id: str, config: dict[str, Any]):
        self.run_id = run_id
        self.config = config
        self.state = "running"
        self.started_at = datetime.now().isoformat()
        self.completed_at: Optional[str] = None
        self.run_dir: Optional[str] = None
        self.tasks: list[dict[str, str]] = []
        self.error: Optional[str] = None
        self._lock = threading.Lock()

    def update(self, **fields: Any) -> None:
        with self._lock:
            for key, value in fields.items():
                setattr(self, key, value)

    def append_task(self, task: dict[str, str]) -> None:
        with self._lock:
            self.tasks.append(task)

    def to_dict(self) -> dict[str, Any]:
        with self._lock:
            return {
                "run_id": self.run_id,
                "state": self.state,
                "started_at": self.started_at,
                "completed_at": self.completed_at,
                "run_dir": self.run_dir,
                "tasks": list(self.tasks),
                "error": self.error,
            }


# Cap retained runs so a long-lived server cannot grow `_runs` without bound.
_MAX_RETAINED_RUNS = 100
_runs: "OrderedDict[str, RunState]" = OrderedDict()
_runs_lock = threading.Lock()


def _register_run(run_state: RunState) -> None:
    with _runs_lock:
        _runs[run_state.run_id] = run_state
        while len(_runs) > _MAX_RETAINED_RUNS:
            for rid, state in _runs.items():
                if state.state in ("completed", "failed"):
                    _runs.pop(rid)
                    break
            else:
                break


def _get_run(run_id: str) -> Optional[RunState]:
    with _runs_lock:
        return _runs.get(run_id)


# ── request/response models ──────────────────���──────────────────────


class ReviewRequest(BaseModel):
    file_path: str
    mode: str = "review"
    venue_profile: str = "general-academic"
    custom_instructions: Optional[str] = None
    llm_proof_review: bool = False
    timeout_seconds: int = 120


class ProviderConfigUpdate(BaseModel):
    api_key: Optional[str] = None
    enabled: Optional[bool] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None


class IngestRequest(BaseModel):
    file_path: str
    parser: str = "auto"


# ── endpoints ───────────────────────────────────────────────────────


@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/providers", dependencies=AUTH)
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


@app.put("/api/providers/{provider_name}/config", dependencies=AUTH)
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


@app.post("/api/providers/{provider_name}/test", dependencies=AUTH)
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


@app.post("/api/ingest", dependencies=AUTH)
def ingest_document(request: IngestRequest):
    try:
        document = parse_document(request.file_path, parser=request.parser)
        return {
            "parser_used": document.parser_used,
            "markdown": document.markdown,
            "title": document.metadata.title,
            "authors": document.metadata.authors,
            "abstract": document.metadata.abstract,
            "section_count": len(document.sections),
            "sections": [
                {
                    "id": section.id,
                    "title": section.title,
                    "level": section.level,
                    "content": section.content,
                }
                for section in _flatten_sections(document.sections)
            ],
        }
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/api/review", dependencies=AUTH)
def start_review(request: ReviewRequest):
    run_id = str(uuid.uuid4())[:8]
    run_state = RunState(run_id, request.model_dump())
    _register_run(run_state)

    thread = threading.Thread(
        target=_execute_review,
        args=(run_id, request),
        daemon=True,
    )
    thread.start()

    return {"run_id": run_id, "status": "started"}


@app.get("/api/status/{run_id}", dependencies=AUTH)
def get_run_status(run_id: str):
    run_state = _get_run(run_id)
    if run_state is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return run_state.to_dict()


@app.get("/api/results/{run_id}", dependencies=AUTH)
def get_run_results(run_id: str):
    run_state = _get_run(run_id)
    if run_state is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    snapshot = run_state.to_dict()
    if snapshot["state"] != "completed":
        raise HTTPException(status_code=409, detail=f"Run is still {snapshot['state']}.")

    run_dir = Path(snapshot["run_dir"]) if snapshot["run_dir"] else None
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
    run_state = _get_run(run_id)
    if run_state is None:
        return

    try:
        run_state.append_task({"name": "review", "status": "running"})

        review_result = review_unified(
            file_path=request.file_path,
            venue_profile=request.venue_profile,
            llm_proof_review=request.llm_proof_review,
            timeout_seconds=request.timeout_seconds,
        )

        run_state.update(
            run_dir=str(review_result.run_dir),
            state="completed",
            completed_at=datetime.now().isoformat(),
            tasks=[{"name": "review", "status": "completed"}],
        )

    except Exception as error:
        run_state.update(
            state="failed",
            error=str(error),
            completed_at=datetime.now().isoformat(),
            tasks=[{"name": "review", "status": "failed", "detail": str(error)[:200]}],
        )


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
