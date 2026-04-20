"""FastAPI server wrapping graph execution.

Start with: ``revisica serve`` or ``python -m revisica.api``
"""

from __future__ import annotations

import argparse
import os
import secrets
import threading
import time
import uuid
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .core_types import ProviderModelSpec
from .ingestion import parse_document
from .ingestion.storage import (
    delete_parsed_document,
    list_parsed_documents,
    load_parsed_document,
    normalized_markdown_path,
    save_parsed_document,
)
from .providers import get_registry
from .providers.provider_config import load_config, save_config
from .unified_review import review_unified


def _load_or_create_api_token() -> str:
    """Return the shared API token, generating one if none is supplied.

    Honors ``REVISICA_API_TOKEN`` when the caller (e.g. the Electron launcher)
    minted one. Otherwise reuses the token at ``~/.revisica/api-token`` when
    present so concurrent ``revisica serve`` processes do not invalidate each
    other, and only mints a fresh one when the file is missing or empty.
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
    try:
        existing = token_path.read_text(encoding="utf-8").strip()
    except (FileNotFoundError, OSError):
        existing = ""
    if existing:
        return existing
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
                "config": self.config,
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
            # Safe: we `break` immediately after the single `pop`, so we never
            # continue iterating a mutated dict within the same `for` pass.
            for rid, state in _runs.items():
                if state.state in ("completed", "failed"):
                    _runs.pop(rid)
                    break
            else:
                break


def _get_run(run_id: str) -> Optional[RunState]:
    with _runs_lock:
        return _runs.get(run_id)


# ── request/response models ─────────────────────────────────────────


class ReviewRequest(BaseModel):
    file_path: Optional[str] = None
    parsed_document_id: Optional[str] = None
    mode: str = "review"
    venue_profile: str = "general-academic"
    custom_instructions: Optional[str] = None
    llm_proof_review: bool = False
    timeout_seconds: int = 120
    parser: str = "auto"
    writing_model: Optional[str] = None
    math_model: Optional[str] = None


class ProviderConfigUpdate(BaseModel):
    api_key: Optional[str] = None
    enabled: Optional[bool] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None


class IngestRequest(BaseModel):
    file_path: str
    parser: str = "auto"


class BackendModeUpdate(BaseModel):
    backend_mode: str


class MathpixCredentialsUpdate(BaseModel):
    app_id: str
    app_key: str


class BenchmarkIngestionStartRequest(BaseModel):
    parsers: list[str] = ["all"]
    limit: int = 3
    paper_ids: Optional[list[str]] = None
    skip_ground_truth: bool = False
    no_pdf_download: bool = False
    timeout_seconds: int = 900


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


@app.get("/api/config/backend-mode", dependencies=AUTH)
def get_backend_mode_endpoint():
    config = load_config()
    mode = config.get("backend_mode", "auto")
    if mode not in ("cli", "api", "auto"):
        mode = "auto"
    return {"backend_mode": mode}


@app.put("/api/config/backend-mode", dependencies=AUTH)
def set_backend_mode_endpoint(update: BackendModeUpdate):
    if update.backend_mode not in ("cli", "api", "auto"):
        raise HTTPException(
            status_code=400,
            detail="backend_mode must be one of 'cli', 'api', 'auto'.",
        )
    config = load_config()
    config["backend_mode"] = update.backend_mode
    save_config(config)
    return {"status": "updated", "backend_mode": update.backend_mode}


@app.get("/api/config/parsers", dependencies=AUTH)
def list_parsers_endpoint():
    """Report the set of PDF/TeX/MD parsers Revisica can use."""
    parser_specs: list[dict[str, Any]] = []

    parser_specs.append(_parser_spec_pandoc())
    parser_specs.append(_parser_spec_tex_basic())
    parser_specs.append(_parser_spec_markdown())
    parser_specs.append(_parser_spec_mineru())
    parser_specs.append(_parser_spec_mathpix())

    return {"parsers": parser_specs}


def _parser_spec_pandoc() -> dict[str, Any]:
    from .ingestion.pandoc_parser import PandocParser
    return {
        "name": "pandoc",
        "display_name": "Pandoc",
        "available": PandocParser.is_available(),
        "requires": ["pandoc CLI on PATH"],
        "handles": [".tex"],
        "install_hint": "brew install pandoc   # or apt-get install pandoc",
    }


def _parser_spec_tex_basic() -> dict[str, Any]:
    return {
        "name": "tex-basic",
        "display_name": "TeX (basic)",
        "available": True,
        "requires": [],
        "handles": [".tex"],
        "install_hint": "",
    }


def _parser_spec_markdown() -> dict[str, Any]:
    return {
        "name": "markdown",
        "display_name": "Markdown (passthrough)",
        "available": True,
        "requires": [],
        "handles": [".md", ".mmd", ".markdown"],
        "install_hint": "",
    }


def _parser_spec_mineru() -> dict[str, Any]:
    from .ingestion.mineru_parser import MineruParser
    return {
        "name": "mineru",
        "display_name": "MinerU",
        "available": MineruParser.is_available(),
        "requires": ["mineru CLI on PATH"],
        "handles": [".pdf"],
        "install_hint": "pip install 'mineru[all]'",
    }


def _parser_spec_mathpix() -> dict[str, Any]:
    from .ingestion.mathpix_parser import MathpixParser
    return {
        "name": "mathpix",
        "display_name": "Mathpix",
        "available": MathpixParser.is_available(),
        "requires": ["MATHPIX_APP_ID and MATHPIX_APP_KEY"],
        "handles": [".pdf", ".png", ".jpg", ".jpeg"],
        "install_hint": "Sign up at accounts.mathpix.com",
    }


@app.get("/api/config/parsers/mineru/models", dependencies=AUTH)
def list_mineru_models():
    """Return MinerU model install status and on-disk size per model type."""
    from .ingestion.mineru_models import list_all_models
    return {"models": list_all_models()}


@app.post(
    "/api/config/parsers/mineru/models/{model_type}/download",
    dependencies=AUTH,
)
def download_mineru_model(model_type: str):
    """Kick off a background download of a MinerU model."""
    from .ingestion.mineru_models import start_download
    try:
        job = start_download(model_type)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": job.status, "model_type": model_type}


@app.delete(
    "/api/config/parsers/mineru/models/{model_type}",
    dependencies=AUTH,
)
def delete_mineru_model(model_type: str):
    """Remove the cached model directory for a MinerU model type."""
    from .ingestion.mineru_models import delete_model
    try:
        result = delete_model(model_type)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"status": "deleted", "model_type": model_type, **result}


@app.get("/api/benchmark/ingestion/parsers", dependencies=AUTH)
def list_ingestion_benchmark_parsers():
    """Return every adapter key the ingestion benchmark understands,
    with availability so the UI can grey out unready parsers."""
    from .api_benchmark_ingestion import list_available_parsers
    return {"parsers": list_available_parsers()}


@app.get("/api/benchmark/ingestion/status", dependencies=AUTH)
def get_ingestion_benchmark_status():
    """Return the current or most recent ingestion benchmark state.

    Returns ``{"state": null}`` when no run has ever been started in
    this server's lifetime. The UI polls this endpoint for progress.
    """
    from dataclasses import asdict
    from .api_benchmark_ingestion import snapshot_state
    state = snapshot_state()
    if state is None:
        return {"state": None}
    return {"state": asdict(state)}


@app.post("/api/benchmark/ingestion/start", dependencies=AUTH)
def start_ingestion_benchmark(request: BenchmarkIngestionStartRequest):
    """Start a new ingestion benchmark run.

    If a run is already in progress, returns that run unchanged rather
    than queuing another, so double-clicks in the UI do nothing.
    """
    from dataclasses import asdict
    from .api_benchmark_ingestion import start_benchmark
    try:
        state = start_benchmark(request.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return {"state": asdict(state)}


@app.put("/api/config/parsers/mathpix/credentials", dependencies=AUTH)
def set_mathpix_credentials(update: MathpixCredentialsUpdate):
    if not update.app_id.strip() or not update.app_key.strip():
        raise HTTPException(
            status_code=400,
            detail="Both app_id and app_key are required.",
        )
    config = load_config()
    mathpix_section = config.setdefault("providers", {}).setdefault("mathpix", {})
    mathpix_section["app_id"] = update.app_id.strip()
    mathpix_section["app_key"] = update.app_key.strip()
    save_config(config)
    return {"status": "updated"}


@app.get("/api/config/model-routes", dependencies=AUTH)
def list_model_routes():
    """Return model choices grouped by role, under the active backend mode."""
    from .model_router import (
        _ANTHROPIC_API_ROUTES,
        _CLAUDE_ROUTES,
        _GPT_ROUTES,
        _OPENAI_API_ROUTES,
    )

    config = load_config()
    mode = config.get("backend_mode", "auto")
    if mode not in ("cli", "api", "auto"):
        mode = "auto"

    writing_choices: list[dict[str, str]] = []
    math_choices: list[dict[str, str]] = []
    writing_seen: set[str] = set()
    math_seen: set[str] = set()

    def add(
        bucket: list[dict[str, str]],
        seen: set[str],
        provider: str,
        model: str,
    ) -> None:
        key = f"{provider}:{model}"
        if key in seen:
            return
        seen.add(key)
        bucket.append({"value": key, "label": _pretty_label(provider, model)})

    # The candidate sets below vary by backend mode so users only see what's
    # actually available to them on their installation.
    if mode in ("cli", "auto"):
        add(writing_choices, writing_seen, "claude", _CLAUDE_ROUTES["writing-basic"])
        add(writing_choices, writing_seen, "claude", _CLAUDE_ROUTES["writing-self-check"])
        add(writing_choices, writing_seen, "codex", _GPT_ROUTES["writing-basic"])
        add(math_choices, math_seen, "claude", _CLAUDE_ROUTES["math-reasoning"])
        add(math_choices, math_seen, "codex", _GPT_ROUTES["math-reasoning"])
    if mode in ("api", "auto"):
        add(writing_choices, writing_seen, "anthropic-api", _ANTHROPIC_API_ROUTES["writing-basic"])
        add(writing_choices, writing_seen, "openai-api", _OPENAI_API_ROUTES["writing-basic"])
        add(math_choices, math_seen, "anthropic-api", _ANTHROPIC_API_ROUTES["math-reasoning"])
        add(math_choices, math_seen, "openai-api", _OPENAI_API_ROUTES["math-reasoning"])

    return {
        "backend_mode": mode,
        "writing": writing_choices,
        "math": math_choices,
    }


def _pretty_label(provider: str, model: str) -> str:
    provider_label = {
        "claude": "Claude",
        "claude-cli": "Claude",
        "codex": "Codex",
        "codex-cli": "Codex",
        "anthropic-api": "Anthropic",
        "openai-api": "OpenAI",
    }.get(provider, provider)
    return f"{provider_label} · {model}"


@app.post("/api/ingest", dependencies=AUTH)
def ingest_document(request: IngestRequest):
    try:
        start = time.perf_counter()
        document = parse_document(request.file_path, parser=request.parser)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        manifest = save_parsed_document(document, elapsed_ms)
        return {
            "id": manifest["id"],
            "parsed_at": manifest["parsed_at"],
            "elapsed_ms": manifest["elapsed_ms"],
            "parser_used": document.parser_used,
            "source_path": document.source_path,
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


@app.get("/api/parsed-documents", dependencies=AUTH)
def list_parsed_documents_endpoint():
    return {"parsed_documents": list_parsed_documents()}


@app.get("/api/parsed-documents/{parsed_document_id}", dependencies=AUTH)
def get_parsed_document_endpoint(parsed_document_id: str):
    try:
        manifest = load_parsed_document(parsed_document_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    document = manifest.get("document") or {}
    metadata = document.get("metadata") or {}
    return {
        "id": manifest.get("id"),
        "parsed_at": manifest.get("parsed_at"),
        "elapsed_ms": manifest.get("elapsed_ms"),
        "parser_used": manifest.get("parser_used"),
        "source_path": manifest.get("source_path"),
        "markdown": document.get("markdown", ""),
        "title": metadata.get("title", ""),
        "authors": metadata.get("authors", []),
        "abstract": metadata.get("abstract", ""),
        "section_count": len(document.get("sections", [])),
        "sections": _flatten_section_dicts(document.get("sections", [])),
    }


@app.delete("/api/parsed-documents/{parsed_document_id}", dependencies=AUTH)
def delete_parsed_document_endpoint(parsed_document_id: str):
    try:
        delete_parsed_document(parsed_document_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return {"status": "deleted", "id": parsed_document_id}


@app.post("/api/review", dependencies=AUTH)
def start_review(request: ReviewRequest):
    if not request.file_path and not request.parsed_document_id:
        raise HTTPException(
            status_code=400,
            detail="Either file_path or parsed_document_id is required.",
        )
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


def _parse_model_spec(raw: Optional[str]) -> Optional[ProviderModelSpec]:
    """Parse a ``provider[:model]`` string into a :class:`ProviderModelSpec`."""
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None
    if ":" in raw:
        provider, model = raw.split(":", 1)
        return ProviderModelSpec(provider=provider.strip(), model=model.strip())
    return ProviderModelSpec(provider=raw)


def _resolve_review_source(request: ReviewRequest) -> dict[str, Optional[str]]:
    """Pick the file path and parser for a review.

    When ``parsed_document_id`` is provided, we feed ``normalized.md`` back
    through the markdown passthrough parser — the parse has already happened,
    so re-parsing is essentially free. We also steer ``output_dir`` so the
    review artefacts use the *original* source stem rather than "normalized".
    """
    if request.parsed_document_id:
        manifest = load_parsed_document(request.parsed_document_id)
        normalized_path = normalized_markdown_path(request.parsed_document_id)
        if not normalized_path.exists():
            raise FileNotFoundError(
                f"Normalized markdown missing for parse {request.parsed_document_id!r}"
            )
        original_stem = Path(manifest.get("source_path") or "document").stem or "document"
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir = str(Path.cwd() / "reviews" / f"{original_stem}-unified-{stamp}")
        return {
            "file_path": str(normalized_path),
            "parser": "markdown",
            "output_dir": output_dir,
        }
    return {
        "file_path": request.file_path,
        "parser": request.parser,
        "output_dir": None,
    }


def _execute_review(run_id: str, request: ReviewRequest) -> None:
    """Run a review in a background thread."""
    run_state = _get_run(run_id)
    if run_state is None:
        return

    try:
        run_state.append_task({"name": "review", "status": "running"})

        writing_spec = _parse_model_spec(request.writing_model)
        math_spec = _parse_model_spec(request.math_model)

        resolved = _resolve_review_source(request)

        review_result = review_unified(
            file_path=resolved["file_path"],
            output_dir=resolved["output_dir"],
            venue_profile=request.venue_profile,
            llm_proof_review=request.llm_proof_review,
            timeout_seconds=request.timeout_seconds,
            mode=request.mode,
            parser=resolved["parser"],
            reviewer_specs=[writing_spec] if writing_spec else None,
            math_reviewer_specs=[math_spec] if math_spec else None,
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


def _flatten_section_dicts(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten a nested section tree that was serialized to plain dicts."""
    result: list[dict[str, Any]] = []
    for section in sections:
        result.append({
            "id": section.get("id"),
            "title": section.get("title", ""),
            "level": section.get("level", 0),
            "content": section.get("content", ""),
        })
        result.extend(_flatten_section_dicts(section.get("children", []) or []))
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
