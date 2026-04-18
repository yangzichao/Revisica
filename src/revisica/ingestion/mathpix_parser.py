"""PDF / image → Markdown parser via the Mathpix API.

Requires environment variables:

- ``MATHPIX_APP_ID``  — Mathpix application ID
- ``MATHPIX_APP_KEY`` — Mathpix application key

Sign up at https://accounts.mathpix.com to obtain credentials.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .base import BaseParser

_API_BASE = "https://api.mathpix.com/v3"
_PDF_ENDPOINT = f"{_API_BASE}/pdf"
_TEXT_ENDPOINT = f"{_API_BASE}/text"

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}
_PDF_EXTENSIONS = {".pdf"}
_SUPPORTED_EXTENSIONS = _PDF_EXTENSIONS | _IMAGE_EXTENSIONS

# Polling parameters for async PDF processing
_POLL_INTERVAL_SECONDS = 3
_MAX_POLL_SECONDS = 600
_POLL_MAX_TRANSIENT_RETRIES = 3


def _is_transient_http_error(exc: BaseException) -> bool:
    if isinstance(exc, HTTPError):
        return exc.code >= 500
    if isinstance(exc, (URLError, TimeoutError, OSError)):
        return True
    return False


def _load_credentials_from_config() -> tuple[str, str]:
    """Read mathpix app_id / app_key from ``~/.revisica/config.json``.

    Returns a pair of empty strings when the section is absent or malformed.
    """
    try:
        from ..providers.provider_config import load_config
        config = load_config()
    except Exception:
        return "", ""
    mathpix_section = (config.get("providers") or {}).get("mathpix") or {}
    app_id = str(mathpix_section.get("app_id", "") or "")
    app_key = str(mathpix_section.get("app_key", "") or "")
    return app_id, app_key


def _get_credentials() -> tuple[str, str]:
    app_id = os.environ.get("MATHPIX_APP_ID", "")
    app_key = os.environ.get("MATHPIX_APP_KEY", "")
    if not app_id or not app_key:
        config_id, config_key = _load_credentials_from_config()
        app_id = app_id or config_id
        app_key = app_key or config_key
    if not app_id or not app_key:
        raise RuntimeError(
            "Mathpix credentials not configured. Set MATHPIX_APP_ID and "
            "MATHPIX_APP_KEY environment variables, or save them via the "
            "New Job wizard."
        )
    return app_id, app_key


def _headers() -> dict[str, str]:
    app_id, app_key = _get_credentials()
    return {
        "app_id": app_id,
        "app_key": app_key,
    }


# ── image (single-shot) ───────────────────────────────────────────────


def _parse_image(path: Path) -> str:
    """Convert a single image to Markdown via /v3/text."""
    import base64

    image_data = base64.b64encode(path.read_bytes()).decode("ascii")
    suffix = path.suffix.lower().lstrip(".")
    mime = f"image/{suffix}" if suffix != "jpg" else "image/jpeg"
    data_uri = f"data:{mime};base64,{image_data}"

    payload = json.dumps({
        "src": data_uri,
        "formats": ["mmd"],
        "math_inline_delimiters": ["$", "$"],
        "math_display_delimiters": ["$$", "$$"],
    }).encode()

    req = Request(
        _TEXT_ENDPOINT,
        data=payload,
        headers={**_headers(), "Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())

    if "mmd" in result:
        return result["mmd"]
    if "text" in result:
        return result["text"]
    raise RuntimeError(f"Mathpix returned unexpected response: {result}")


# ── PDF (async processing) ────────────────────────────────────────────


def _parse_pdf(path: Path) -> str:
    """Convert a PDF to Markdown via /v3/pdf (async upload + poll)."""
    # 1. Upload PDF
    pdf_bytes = path.read_bytes()

    boundary = "----RevisicaMathpixBoundary"
    body_parts = [
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n",
    ]
    body = (
        body_parts[0].encode()
        + pdf_bytes
        + f"\r\n--{boundary}\r\n".encode()
        + f'Content-Disposition: form-data; name="conversion_formats"\r\n\r\n'.encode()
        + b"mmd"
        + f"\r\n--{boundary}--\r\n".encode()
    )

    req = Request(
        _PDF_ENDPOINT,
        data=body,
        headers={
            **_headers(),
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    with urlopen(req, timeout=120) as resp:
        upload_result = json.loads(resp.read())

    pdf_id = upload_result.get("pdf_id")
    if not pdf_id:
        raise RuntimeError(
            f"Mathpix PDF upload failed: {upload_result}"
        )

    # 2. Poll until processing completes, retrying transient network errors.
    poll_url = f"{_PDF_ENDPOINT}/{pdf_id}"
    elapsed = 0.0
    transient_failures = 0
    while elapsed < _MAX_POLL_SECONDS:
        poll_req = Request(poll_url, headers=_headers(), method="GET")
        try:
            with urlopen(poll_req, timeout=30) as resp:
                status_result = json.loads(resp.read())
        except Exception as exc:
            if _is_transient_http_error(exc) and transient_failures < _POLL_MAX_TRANSIENT_RETRIES:
                transient_failures += 1
                backoff = min(_POLL_INTERVAL_SECONDS * (2 ** transient_failures), 30)
                logging.getLogger(__name__).warning(
                    "Mathpix poll transient failure (%s); retry %d/%d after %ds",
                    exc, transient_failures, _POLL_MAX_TRANSIENT_RETRIES, backoff,
                )
                time.sleep(backoff)
                elapsed += backoff
                continue
            raise

        status = status_result.get("status", "")
        if status == "completed":
            break
        if status == "error":
            raise RuntimeError(
                f"Mathpix PDF processing error: {status_result}"
            )
        time.sleep(_POLL_INTERVAL_SECONDS)
        elapsed += _POLL_INTERVAL_SECONDS
    else:
        raise TimeoutError(
            f"Mathpix PDF processing timed out after {_MAX_POLL_SECONDS}s"
        )

    # 3. Download the MMD result
    mmd_url = f"{_PDF_ENDPOINT}/{pdf_id}.mmd"
    mmd_req = Request(mmd_url, headers=_headers(), method="GET")
    try:
        with urlopen(mmd_req, timeout=60) as resp:
            return resp.read().decode("utf-8")
    except HTTPError as exc:
        raise RuntimeError(
            f"Failed to download Mathpix MMD output: {exc}"
        ) from exc


# ── parser class ───────────────────────────────────────────────────────


class MathpixParser(BaseParser):
    """Convert PDF or images to Markdown via the Mathpix API."""

    name = "mathpix"

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in _SUPPORTED_EXTENSIONS

    @classmethod
    def is_available(cls) -> bool:
        app_id = os.environ.get("MATHPIX_APP_ID", "")
        app_key = os.environ.get("MATHPIX_APP_KEY", "")
        if not app_id or not app_key:
            config_id, config_key = _load_credentials_from_config()
            app_id = app_id or config_id
            app_key = app_key or config_key
        return bool(app_id and app_key)

    def parse(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in _PDF_EXTENSIONS:
            return _parse_pdf(path)
        if suffix in _IMAGE_EXTENSIONS:
            return _parse_image(path)
        raise ValueError(f"Unsupported file type: {suffix}")
