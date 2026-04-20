"""Model management for the MinerU PDF parser.

MinerU ships as a Python package (``pip install 'mineru[all]'``) but its
large parsing models are downloaded separately via ``mineru-models-download``
and stored in the shared HuggingFace hub cache. This module exposes:

- Install status and on-disk size for each model type.
- A non-blocking download job runner that shells out to the CLI.
- Safe deletion of the cached model directory.

Two model types are supported, matching ``mineru-models-download -m``:
``pipeline`` (PDF-Extract-Kit, ~1.1 GB) and ``vlm`` (MinerU2.5-Pro, ~2.2 GB).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


HUGGINGFACE_REPO_BY_MODEL_TYPE: dict[str, str] = {
    "pipeline": "opendatalab/PDF-Extract-Kit-1.0",
    "vlm": "opendatalab/MinerU2.5-Pro-2604-1.2B",
}

DISPLAY_NAME_BY_MODEL_TYPE: dict[str, str] = {
    "pipeline": "Pipeline model",
    "vlm": "VLM model (higher accuracy)",
}


def _huggingface_hub_cache_dir() -> Path:
    """Return the HuggingFace hub cache directory, honoring ``HF_HOME``."""
    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        return Path(hf_home).expanduser() / "hub"
    return Path.home() / ".cache" / "huggingface" / "hub"


def _model_cache_dir(model_type: str) -> Path:
    repo_id = HUGGINGFACE_REPO_BY_MODEL_TYPE[model_type]
    return _huggingface_hub_cache_dir() / f"models--{repo_id.replace('/', '--')}"


def _directory_size_bytes(path: Path) -> int:
    total = 0
    for entry in path.rglob("*"):
        if entry.is_file() and not entry.is_symlink():
            try:
                total += entry.stat().st_size
            except OSError:
                pass
    return total


@dataclass
class DownloadJob:
    """In-memory record of a running or finished download subprocess."""

    model_type: str
    status: str = "running"  # running | succeeded | failed
    started_at: float = 0.0
    finished_at: Optional[float] = None
    error: Optional[str] = None
    process: Optional[subprocess.Popen] = field(default=None, repr=False)


_download_jobs: dict[str, DownloadJob] = {}
_download_jobs_lock = threading.Lock()


def _current_job_snapshot(model_type: str) -> Optional[DownloadJob]:
    with _download_jobs_lock:
        return _download_jobs.get(model_type)


def get_model_status(model_type: str) -> dict:
    if model_type not in HUGGINGFACE_REPO_BY_MODEL_TYPE:
        raise ValueError(f"Unknown MinerU model type: {model_type}")

    cache_dir = _model_cache_dir(model_type)
    installed = cache_dir.exists() and any(cache_dir.iterdir())
    size_bytes = _directory_size_bytes(cache_dir) if cache_dir.exists() else 0
    job = _current_job_snapshot(model_type)

    return {
        "model_type": model_type,
        "display_name": DISPLAY_NAME_BY_MODEL_TYPE[model_type],
        "repo_id": HUGGINGFACE_REPO_BY_MODEL_TYPE[model_type],
        "installed": installed,
        "downloading": job is not None and job.status == "running",
        "size_bytes": size_bytes,
        "last_error": job.error if job and job.status == "failed" else None,
        "cache_path": str(cache_dir),
    }


def list_all_models() -> list[dict]:
    return [get_model_status(t) for t in HUGGINGFACE_REPO_BY_MODEL_TYPE]


def start_download(model_type: str, source: str = "huggingface") -> DownloadJob:
    """Kick off a background ``mineru-models-download`` subprocess.

    If a download for this model type is already running, the existing job is
    returned unchanged (idempotent). The subprocess writes straight to the HF
    cache; we only track lifecycle state.
    """
    if model_type not in HUGGINGFACE_REPO_BY_MODEL_TYPE:
        raise ValueError(f"Unknown MinerU model type: {model_type}")
    if source not in ("huggingface", "modelscope"):
        raise ValueError(f"Unknown model source: {source}")

    mineru_download_bin = shutil.which("mineru-models-download")
    if mineru_download_bin is None:
        raise RuntimeError(
            "mineru-models-download CLI not found. Install with: pip install 'mineru[all]'"
        )

    with _download_jobs_lock:
        existing = _download_jobs.get(model_type)
        if existing is not None and existing.status == "running":
            return existing
        job = DownloadJob(
            model_type=model_type,
            status="running",
            started_at=time.time(),
        )
        _download_jobs[model_type] = job

    def _run_download() -> None:
        try:
            process = subprocess.Popen(
                [mineru_download_bin, "-s", source, "-m", model_type],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            with _download_jobs_lock:
                job.process = process
            _, stderr_bytes = process.communicate()
            with _download_jobs_lock:
                if process.returncode == 0:
                    job.status = "succeeded"
                else:
                    job.status = "failed"
                    message = (stderr_bytes.decode(errors="replace") if stderr_bytes else "").strip()
                    job.error = message[-500:] or f"exit code {process.returncode}"
                job.finished_at = time.time()
        except Exception as exc:  # pragma: no cover — defensive
            with _download_jobs_lock:
                job.status = "failed"
                job.error = str(exc)[-500:]
                job.finished_at = time.time()

    thread = threading.Thread(target=_run_download, daemon=True)
    thread.start()
    return job


def delete_model(model_type: str) -> dict:
    """Remove the cached model directory from disk."""
    if model_type not in HUGGINGFACE_REPO_BY_MODEL_TYPE:
        raise ValueError(f"Unknown MinerU model type: {model_type}")

    job = _current_job_snapshot(model_type)
    if job is not None and job.status == "running":
        raise RuntimeError(
            f"Cannot delete {model_type} model while a download is in progress."
        )

    cache_dir = _model_cache_dir(model_type)
    freed_bytes = _directory_size_bytes(cache_dir) if cache_dir.exists() else 0
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    with _download_jobs_lock:
        _download_jobs.pop(model_type, None)
    return {"deleted": cache_dir.exists() is False, "freed_bytes": freed_bytes}
