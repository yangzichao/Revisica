"""Benchmark corpus loading and on-demand PDF fetching.

Papers live under ``tests/fixtures/arxiv/<id>/`` with their ``.tex`` source
already checked in. The matching PDF is fetched from arxiv on first use
and cached alongside the tex so subsequent runs are fully offline.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from ._arxiv_throttle import wait_for_next_request_slot

logger = logging.getLogger(__name__)


# ── data shape ─────────────────────────────────────────────────────────


@dataclass
class CorpusEntry:
    """One paper in the benchmark corpus."""

    arxiv_id: str
    tex_filename: str
    field: str
    multi_file: bool
    paper_dir: Path

    @property
    def tex_path(self) -> Path:
        return self.paper_dir / self.tex_filename

    @property
    def pdf_path(self) -> Path:
        return self.paper_dir / f"{self.arxiv_id}.pdf"


# ── manifest loader ────────────────────────────────────────────────────


def load_corpus(
    fixtures_root: Path,
    *,
    limit: int | None = None,
    paper_ids: list[str] | None = None,
) -> list[CorpusEntry]:
    """Load benchmark entries from ``<fixtures_root>/manifest.json``.

    Either ``limit`` (take first N in manifest order) or ``paper_ids``
    (filter to specific IDs) may be supplied; ``paper_ids`` wins when
    both are set.
    """
    manifest_path = fixtures_root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Corpus manifest not found at {manifest_path}. Expected the "
            f"existing tests/fixtures/arxiv/manifest.json."
        )

    records = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries: list[CorpusEntry] = []
    for record in records:
        entries.append(
            CorpusEntry(
                arxiv_id=record["id"],
                tex_filename=record["tex"],
                field=record.get("field", ""),
                multi_file=record.get("multi_file", False),
                paper_dir=fixtures_root / record["id"],
            )
        )

    if paper_ids:
        wanted = set(paper_ids)
        entries = [entry for entry in entries if entry.arxiv_id in wanted]
    elif limit is not None:
        entries = entries[:limit]

    return entries


# ── file availability helpers ──────────────────────────────────────────


def ensure_tex_for_entry(entry: CorpusEntry) -> Path | None:
    """Return the tex file path if present on disk, else ``None``."""
    if entry.tex_path.exists():
        return entry.tex_path
    logger.warning("tex source missing for %s: %s", entry.arxiv_id, entry.tex_path)
    return None


def ensure_pdf_for_entry(
    entry: CorpusEntry,
    *,
    request_interval_sec: float = 4.0,
    max_attempts: int = 2,
) -> Path | None:
    """Ensure the arxiv PDF for *entry* exists on disk, downloading if needed.

    Returns the local path on success. Returns ``None`` and logs a warning
    if the download failed (so the caller can skip this row gracefully).

    arXiv requests a minimum 3 s gap between automated hits; we enforce
    4 s through :func:`_throttle`.
    """
    if entry.pdf_path.exists() and entry.pdf_path.stat().st_size > 0:
        return entry.pdf_path

    entry.paper_dir.mkdir(parents=True, exist_ok=True)

    url = f"https://arxiv.org/pdf/{entry.arxiv_id}.pdf"
    for attempt_number in range(1, max_attempts + 1):
        wait_for_next_request_slot(request_interval_sec)
        try:
            _download_binary(url, entry.pdf_path)
        except urllib.error.URLError as error:
            logger.warning(
                "arXiv PDF download failed (attempt %d/%d) for %s: %s",
                attempt_number, max_attempts, entry.arxiv_id, error,
            )
            if attempt_number < max_attempts:
                continue
            return None
        else:
            logger.info("Downloaded %s PDF to %s", entry.arxiv_id, entry.pdf_path)
            return entry.pdf_path
    return None


# ── internals ──────────────────────────────────────────────────────────


def _download_binary(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "revisica-benchmark/0.1 (ingestion parser evaluation)"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        if response.status != 200:
            raise urllib.error.URLError(f"HTTP {response.status}")
        payload = response.read()
    temporary_path = destination.with_suffix(destination.suffix + ".partial")
    temporary_path.write_bytes(payload)
    temporary_path.replace(destination)
