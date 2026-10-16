"""Pull a JSON object out of free-form LLM output.

Agents are asked to return JSON, but real outputs wrap it in prose, put
it in a fenced block (sometimes without the closing fence), and write
LaTeX with single backslashes (``\\{``, ``\\pi``) that strict JSON
rejects. The writing lane, math lane and refine judge all go through
``extract_json_object`` so they share one set of recovery strategies.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator

_CLOSED_FENCE_PATTERN = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL)
# One backslash escape: a \uXXXX escape or a backslash plus any single char.
# Matching pairs as a unit keeps an already-escaped ``\\`` intact.
_BACKSLASH_ESCAPE_PATTERN = re.compile(r"\\(u[0-9a-fA-F]{4}|.)", re.DOTALL)
_VALID_SINGLE_CHAR_ESCAPES = frozenset('"\\/bfnrt')
_JSON_DECODER = json.JSONDecoder()
# RecursionError: pathologically deep nesting must not crash a review lane.
_DECODE_ERRORS = (ValueError, RecursionError)


def extract_json_object(
    text: str,
    required_key: str,
    value_type: type | None = None,
) -> dict[str, object] | None:
    """Return the first JSON object in ``text`` that contains ``required_key``.

    When ``value_type`` is given, the key's value must also be an instance
    of it. Returns None when nothing qualifies, including when the output
    was truncated mid-object.

    Candidates, in order: the whole output, each fenced block, then every
    ``{`` in the text decoded in place (covers prose around the JSON and
    an unclosed fence). Each candidate is retried with stray LaTeX
    backslashes escaped when strict parsing fails.
    """
    for parsed_value in _iter_parsed_candidates(text.strip()):
        if not isinstance(parsed_value, dict) or required_key not in parsed_value:
            continue
        if value_type is not None and not isinstance(parsed_value[required_key], value_type):
            continue
        return parsed_value
    return None


def _iter_parsed_candidates(text: str) -> Iterator[object]:
    yield from _loads_strict_then_repaired(text)
    for fence_match in _CLOSED_FENCE_PATTERN.finditer(text):
        yield from _loads_strict_then_repaired(fence_match.group(1).strip())
    yield from _iter_objects_embedded_in_prose(text)
    repaired_text = _escape_stray_backslashes(text)
    if repaired_text != text:
        yield from _iter_objects_embedded_in_prose(repaired_text)


def _loads_strict_then_repaired(candidate: str) -> Iterator[object]:
    try:
        parsed_value = json.loads(candidate)
    except _DECODE_ERRORS:
        pass
    else:
        yield parsed_value
        return
    repaired_candidate = _escape_stray_backslashes(candidate)
    if repaired_candidate == candidate:
        return
    try:
        parsed_value = json.loads(repaired_candidate)
    except _DECODE_ERRORS:
        return
    yield parsed_value


def _iter_objects_embedded_in_prose(text: str) -> Iterator[object]:
    """Decode a JSON value starting at each ``{``, ignoring what follows it."""
    brace_index = text.find("{")
    while brace_index != -1:
        try:
            parsed_value, _ = _JSON_DECODER.raw_decode(text, brace_index)
        except _DECODE_ERRORS:
            pass
        else:
            yield parsed_value
        brace_index = text.find("{", brace_index + 1)


def _escape_stray_backslashes(text: str) -> str:
    """Turn backslashes that are not valid JSON escapes into literal ones.

    ``"$\\{x\\}$"`` written with single backslashes is invalid JSON; this
    makes it ``"$\\\\{x\\\\}$"`` so the LaTeX survives as text. Valid
    escapes (``\\n``, ``\\"``, ``\\\\``, ``\\u00e9``) are left alone.
    """

    def escape_if_invalid(escape_match: re.Match[str]) -> str:
        escaped = escape_match.group(1)
        is_unicode_escape = len(escaped) == 5
        if is_unicode_escape or escaped in _VALID_SINGLE_CHAR_ESCAPES:
            return escape_match.group(0)
        return "\\\\" + escaped

    return _BACKSLASH_ESCAPE_PATTERN.sub(escape_if_invalid, text)
