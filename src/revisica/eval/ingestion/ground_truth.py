"""Fetch ground-truth title/authors/abstract from the arxiv API.

Every call for a given arxiv ID is cached to disk so repeat benchmark
runs are offline and deterministic. The network request only happens on
the first encounter.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

from ._arxiv_throttle import wait_for_next_request_slot

logger = logging.getLogger(__name__)


# ── data shape ─────────────────────────────────────────────────────────


@dataclass
class ArxivMetadata:
    """Ground-truth bibliographic data for a single paper."""

    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str


# ── public API ─────────────────────────────────────────────────────────


def fetch_arxiv_metadata(
    arxiv_id: str,
    cache_dir: Path,
    *,
    request_interval_sec: float = 4.0,
    allow_network: bool = True,
) -> ArxivMetadata | None:
    """Return ground-truth metadata for *arxiv_id*, using the local cache
    if available.

    When ``allow_network`` is False and no cache hit is present, returns
    ``None``.
    """
    cache_path = cache_dir / f"{arxiv_id}.json"
    if cache_path.exists():
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            return ArxivMetadata(**payload)
        except (json.JSONDecodeError, TypeError) as error:
            logger.warning("Corrupt ground-truth cache for %s: %s", arxiv_id, error)

    if not allow_network:
        return None

    metadata = _query_arxiv_api(arxiv_id, request_interval_sec=request_interval_sec)
    if metadata is None:
        return None

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(asdict(metadata), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return metadata


# ── arxiv API client ───────────────────────────────────────────────────


_ARXIV_QUERY_URL = "http://export.arxiv.org/api/query?id_list={id}"


def _query_arxiv_api(
    arxiv_id: str,
    *,
    request_interval_sec: float,
    max_attempts: int = 2,
) -> ArxivMetadata | None:
    url = _ARXIV_QUERY_URL.format(id=arxiv_id)
    for attempt_number in range(1, max_attempts + 1):
        wait_for_next_request_slot(request_interval_sec)
        try:
            raw = _http_get(url)
        except urllib.error.URLError as error:
            logger.warning(
                "arXiv API request failed (attempt %d/%d) for %s: %s",
                attempt_number, max_attempts, arxiv_id, error,
            )
            if attempt_number < max_attempts:
                continue
            return None

        parsed = _parse_atom_entry(raw)
        if parsed is None:
            logger.warning(
                "arXiv API returned no entry for %s (attempt %d/%d)",
                arxiv_id, attempt_number, max_attempts,
            )
            if attempt_number < max_attempts:
                continue
            return None

        title, authors, abstract = parsed
        return ArxivMetadata(
            arxiv_id=arxiv_id,
            title=title,
            authors=authors,
            abstract=abstract,
        )
    return None


def _http_get(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "revisica-benchmark/0.1 (ingestion parser evaluation)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise urllib.error.URLError(f"HTTP {response.status}")
        return response.read().decode("utf-8")


# ── Atom feed parser ───────────────────────────────────────────────────


_ATOM_ENTRY_RE = re.compile(r"<entry>(.*?)</entry>", re.DOTALL)
_ATOM_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL)
_ATOM_SUMMARY_RE = re.compile(r"<summary>(.*?)</summary>", re.DOTALL)
_ATOM_AUTHOR_NAME_RE = re.compile(
    r"<author>\s*<name>(.*?)</name>", re.DOTALL
)


def _parse_atom_entry(feed: str) -> tuple[str, list[str], str] | None:
    """Extract (title, authors, abstract) from the first Atom entry.

    The arxiv API wraps everything in XML but we only need three fields,
    so a small regex reader avoids pulling in an XML dependency.
    """
    entry_match = _ATOM_ENTRY_RE.search(feed)
    if entry_match is None:
        return None
    entry = entry_match.group(1)

    title_match = _ATOM_TITLE_RE.search(entry)
    summary_match = _ATOM_SUMMARY_RE.search(entry)
    author_names = _ATOM_AUTHOR_NAME_RE.findall(entry)

    if title_match is None or summary_match is None:
        return None

    title = _collapse_whitespace(_decode_entities(title_match.group(1)))
    abstract = _collapse_whitespace(_decode_entities(summary_match.group(1)))
    authors = [_collapse_whitespace(_decode_entities(name)) for name in author_names]
    return title, authors, abstract


_XML_ENTITY_MAP = {
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&apos;": "'",
}


def _decode_entities(text: str) -> str:
    for entity, replacement in _XML_ENTITY_MAP.items():
        text = text.replace(entity, replacement)
    return text


_WHITESPACE_RUN_RE = re.compile(r"\s+")


def _collapse_whitespace(text: str) -> str:
    return _WHITESPACE_RUN_RE.sub(" ", text).strip()
