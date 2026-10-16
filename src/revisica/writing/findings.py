"""Parsing of agent output into a structured findings list."""

from __future__ import annotations

from ..llm_output import extract_json_object


def extract_findings_payload(output: str) -> list[dict[str, object]] | None:
    """Extract the ``findings`` array from agent output.

    Returns None when no ``{"findings": [...]}`` object can be recovered;
    see ``extract_json_object`` for the recovery strategies.
    """
    payload = extract_json_object(output, "findings", list)
    if payload is None:
        return None
    return [finding for finding in payload["findings"] if isinstance(finding, dict)]
