"""Parsing of agent output into a structured findings list.

Real agents may wrap JSON in narrative text or fenced code blocks, so
extraction tries multiple strategies before giving up.
"""

from __future__ import annotations

import json
import re


def extract_findings_payload(output: str) -> list[dict[str, object]] | None:
    """Extract a JSON findings array from agent output.

    Strategies, in order: direct parse, fenced-block extraction, and
    scanning for the first ``{ ... }`` containing ``"findings"``.
    """
    text = output.strip()
    if not text:
        return None

    # Strategy 1: direct JSON parse
    parsed = _try_parse_findings(text)
    if parsed is not None:
        return parsed

    # Strategy 2: extract from fenced code block (```json ... ```)
    for match in re.finditer(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL):
        parsed = _try_parse_findings(match.group(1).strip())
        if parsed is not None:
            return parsed

    # Strategy 3: find first { that contains "findings"
    start = text.find('{"findings"')
    if start == -1:
        start = text.find('"findings"')
        if start != -1:
            # backtrack to opening brace
            start = text.rfind("{", 0, start)
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    parsed = _try_parse_findings(text[start : i + 1])
                    if parsed is not None:
                        return parsed
                    break

    return None


def _try_parse_findings(text: str) -> list[dict[str, object]] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    findings = payload.get("findings")
    if not isinstance(findings, list):
        return None
    return [f for f in findings if isinstance(f, dict)]
