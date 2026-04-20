"""Markdown / plain-text structure extractors.

These extractors recognize theorem/proof/function patterns that appear in
Markdown papers (e.g. converted from PDF via Mathpix, MinerU, Marker, or
produced directly in .md). They complement the LaTeX-native extractors in
``structures.py``; the two sets are merged by the public extractor API.

Patterns supported here:

- Theorem-like headers:   ``THEOREM 1:``, ``Theorem 1.``, ``**Lemma 3.**``,
  ``Proposition (Main):``, and Markdown section headings
  ``## Theorem 4``.
- Proof headers:          ``PROOF:``, ``PROOF OF THEOREM 1:``, ``Proof.``,
  ``**Proof of Lemma 2.**``.
- Proof end markers:      ``Q.E.D.``, ``QED``, ``∎``, ``\\blacksquare``,
  or the start of the next theorem/proof header.
- Function definitions:   ``f(x) = ...`` outside math delimiters,
  ``f(x) := ...``, and type signatures ``f : X → Y``.

End-of-block detection for theorems without explicit ``\\end{...}`` is
heuristic: we stop at the next theorem-like header, the next ``Proof``
header, a Markdown section heading, or an ``APPENDIX`` / ``REFERENCES``
marker — whichever comes first.
"""

from __future__ import annotations

import logging
import re

from ..types import FunctionDefinition, ProofBlock, TheoremBlock
from .latex_utils import line_number, parse_expr


# ── shared regex building blocks ────────────────────────────────────────

_THEOREM_ENV_NAMES = ("theorem", "proposition", "lemma", "corollary", "claim", "definition")

# Anchors a theorem-like header at the start of a line, tolerant of
# leading Markdown decorations (``>``, ``>>``, ``- ``, ``* ``, ``** **``,
# leading ``#`` for section headings), optional number, optional
# parenthesized title, and terminating ``.``, ``:``, or end-of-line.
_THEOREM_HEADER_PATTERN = re.compile(
    r"""
    ^[ \t]*                                    # optional indentation
    (?:\#{1,6}[ \t]+)?                         # optional heading marker
    (?:[>\-*][ \t]+)?                          # optional blockquote/list
    (?:\*{1,3}|_{1,3})?                        # optional bold/italic open
    (?P<env>THEOREM|PROPOSITION|LEMMA|COROLLARY|CLAIM|DEFINITION
            |Theorem|Proposition|Lemma|Corollary|Claim|Definition)
    [ \t]*                                     # spaces
    (?P<number>\d+(?:\.\d+)*)?                 # optional "1" or "3.2"
    (?:                                        # optional title block:
        [ \t]*\((?P<title_paren>[^)]{1,120})\) # "(Named Result)" or
        |[ \t]*[—\-–]\s*(?P<title_dash>[^.:\n]{1,120}?) # "—Named Result"
    )?
    (?:\*{1,3}|_{1,3})?                        # optional bold/italic close
    [ \t]*(?P<terminator>[.:])                 # must terminate with "." or ":"
    """,
    re.VERBOSE | re.MULTILINE,
)

# "PROOF:" / "PROOF OF THEOREM 1:" / "Proof." / "**Proof of Lemma 2.**".
_PROOF_HEADER_PATTERN = re.compile(
    r"""
    ^[ \t]*
    (?:\#{1,6}[ \t]+)?
    (?:[>\-*][ \t]+)?
    (?:\*{1,3}|_{1,3})?
    (?P<label>PROOF|Proof)
    (?:[ \t]+(?:OF|of)[ \t]+
        (?P<target>[A-Za-z]+(?:[ \t]+\d+(?:\.\d+)*)?)
    )?
    (?:\*{1,3}|_{1,3})?
    [ \t]*(?P<terminator>[.:])
    """,
    re.VERBOSE | re.MULTILINE,
)

# Section heading that should terminate a theorem body (e.g. "## 3. Method").
_SECTION_HEADING_PATTERN = re.compile(r"^[ \t]*#{1,6}[ \t]+\S", re.MULTILINE)

# Phrases that mark the end of the appendix/bibliography area.
_APPENDIX_MARKER_PATTERN = re.compile(
    r"^[ \t]*(?:APPENDIX|REFERENCES|BIBLIOGRAPHY|Appendix|References|Bibliography)\b",
    re.MULTILINE,
)

# QED / end-of-proof markers.
_PROOF_END_PATTERN = re.compile(
    r"(?:Q\.?\s*E\.?\s*D\.?|∎|\\blacksquare\b|\\qed\b|\\square\b)",
    re.IGNORECASE,
)


# ── theorem extraction ─────────────────────────────────────────────────


def extract_theorem_blocks_markdown(content: str) -> list[TheoremBlock]:
    """Find theorem-like headers in Markdown / plain text.

    Body extends until the next theorem/proof header, the next Markdown
    section heading, an APPENDIX/REFERENCES marker, or EOF.
    """
    headers = _find_theorem_headers(content)
    if not headers:
        return []
    proof_header_starts = [match.start() for match in _PROOF_HEADER_PATTERN.finditer(content)]
    section_starts = [match.start() for match in _SECTION_HEADING_PATTERN.finditer(content)]
    appendix_starts = [match.start() for match in _APPENDIX_MARKER_PATTERN.finditer(content)]

    blocks: list[TheoremBlock] = []
    for index, header in enumerate(headers):
        body_start = header.end()
        next_boundaries = [
            # Next theorem header.
            *(h.start() for h in headers[index + 1:]),
            # Next proof header after the body starts.
            *(pos for pos in proof_header_starts if pos > body_start),
            # Next section heading after the body starts (but not the
            # heading that IS the theorem header itself).
            *(pos for pos in section_starts if pos > body_start),
            # Appendix / references.
            *(pos for pos in appendix_starts if pos > body_start),
        ]
        body_end = min(next_boundaries, default=len(content))
        body = content[body_start:body_end].strip()
        if not body:
            continue
        snippet_end = min(body_end, header.start() + 800)
        blocks.append(
            TheoremBlock(
                env_name=_canonicalize_env_name(header.group("env")),
                line_number=line_number(content, header.start()),
                title=_build_theorem_title(header),
                statement=body,
                snippet=content[header.start():snippet_end].strip(),
            )
        )
    return blocks


def _find_theorem_headers(content: str) -> list[re.Match[str]]:
    matches: list[re.Match[str]] = []
    for match in _THEOREM_HEADER_PATTERN.finditer(content):
        # Guard against matching running prose like "Theorem 1:" in the
        # middle of a line: the pattern already anchors to ^, but we also
        # require that the header be on its own visual line by confirming
        # no non-whitespace precedes it on that line.
        line_start = content.rfind("\n", 0, match.start()) + 1
        prefix = content[line_start:match.start()]
        if prefix.strip():
            continue
        matches.append(match)
    return matches


def _canonicalize_env_name(raw: str) -> str:
    return raw.lower()


def _build_theorem_title(match: re.Match[str]) -> str | None:
    number = match.group("number")
    title = match.group("title_paren") or match.group("title_dash")
    if number and title:
        return f"{number} — {title.strip()}"
    if number:
        return number
    if title:
        return title.strip()
    return None


# ── proof extraction ───────────────────────────────────────────────────


def extract_proof_blocks_markdown(content: str) -> list[ProofBlock]:
    """Find proof headers and their bodies in Markdown / plain text.

    Body extends until a QED marker, the next theorem/proof header, a
    Markdown section heading, an APPENDIX/REFERENCES marker, or EOF.
    """
    proof_headers = list(_PROOF_HEADER_PATTERN.finditer(content))
    if not proof_headers:
        return []
    theorem_header_starts = [match.start() for match in _find_theorem_headers(content)]
    section_starts = [match.start() for match in _SECTION_HEADING_PATTERN.finditer(content)]
    appendix_starts = [match.start() for match in _APPENDIX_MARKER_PATTERN.finditer(content)]

    blocks: list[ProofBlock] = []
    for index, header in enumerate(proof_headers):
        body_start = header.end()
        qed_match = _PROOF_END_PATTERN.search(content, body_start)
        qed_end = qed_match.end() if qed_match else None
        next_header_start = (
            proof_headers[index + 1].start() if index + 1 < len(proof_headers) else None
        )
        next_theorem_start = next(
            (pos for pos in theorem_header_starts if pos > body_start), None
        )
        next_section_start = next(
            (pos for pos in section_starts if pos > body_start), None
        )
        next_appendix_start = next(
            (pos for pos in appendix_starts if pos > body_start), None
        )
        candidate_ends = [
            pos for pos in (
                qed_end,
                next_header_start,
                next_theorem_start,
                next_section_start,
                next_appendix_start,
            )
            if pos is not None
        ]
        body_end = min(candidate_ends) if candidate_ends else len(content)
        body = content[body_start:body_end].strip()
        if not body:
            continue
        snippet_end = min(body_end, header.start() + 800)
        blocks.append(
            ProofBlock(
                line_number=line_number(content, header.start()),
                title=_build_proof_title(header),
                body=body,
                snippet=content[header.start():snippet_end].strip(),
            )
        )
    return blocks


def _build_proof_title(match: re.Match[str]) -> str | None:
    target = match.group("target")
    if target:
        return f"Proof of {target.strip()}"
    return None


# ── function extraction ────────────────────────────────────────────────


_FUNCTION_DEF_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])(?P<name>[A-Za-z][A-Za-z0-9_]*)"
    r"\((?P<var>[A-Za-z][A-Za-z0-9_]*)\)"
    r"\s*(?::?=)\s*"
    r"(?P<expr>[^\n.,;:]+)"
)

# A function signature is written as "<name> : <domain> → <codomain>".
# We anchor on a short identifier followed by whitespace-colon-whitespace
# to avoid matching regular prose colons, and restrict the domain /
# codomain to a single identifier-like token (optionally decorated with
# subscripts, superscripts, or a LaTeX macro like \mathbb{R}^n) so we
# don't swallow whole sentences.
_FUNCTION_SIGNATURE_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"(?P<name>[A-Za-z][A-Za-z0-9]{0,2})"
    r"[ \t]*:[ \t]+"
    r"(?P<domain>(?:\\[A-Za-z]+\{[^{}]+\}|[A-Za-z][\w]*)(?:\^\{?[\w+\-]+\}?)?)"
    r"[ \t]*(?:→|\\to\b|->)[ \t]*"
    r"(?P<codomain>(?:\\[A-Za-z]+\{[^{}]+\}|[A-Za-z][\w]*)(?:\^\{?[\w+\-]+\}?)?)"
)


def extract_functions_markdown(
    content: str,
    already_covered: list[int] | None = None,
) -> list[FunctionDefinition]:
    """Find function definitions outside math delimiters and type signatures.

    ``already_covered`` is an iterable of line numbers already returned by
    the LaTeX-based extractor; matches on those lines are skipped so we do
    not produce duplicates.
    """
    covered = set(already_covered or [])
    results: list[FunctionDefinition] = []
    results.extend(_extract_plain_function_defs(content, covered))
    results.extend(_extract_function_signatures(content, covered))
    return results


def _extract_plain_function_defs(
    content: str,
    covered: set[int],
) -> list[FunctionDefinition]:
    results: list[FunctionDefinition] = []
    math_spans = _math_delimiter_spans(content)
    for match in _FUNCTION_DEF_PATTERN.finditer(content):
        if _within_any_span(match.start(), math_spans):
            continue
        line = line_number(content, match.start())
        if line in covered:
            continue
        name = match.group("name")
        variable = match.group("var")
        expression_text = match.group("expr").strip()
        if not expression_text or expression_text.endswith("="):
            continue
        expression = _safe_parse_expression(expression_text, variable)
        snippet = _snippet_around(content, match.start(), match.end())
        results.append(
            FunctionDefinition(
                name=name,
                variable=variable,
                expression_text=expression_text,
                expression=expression,
                line_number=line,
                snippet=snippet,
            )
        )
    return results


def _extract_function_signatures(
    content: str,
    covered: set[int],
) -> list[FunctionDefinition]:
    results: list[FunctionDefinition] = []
    math_spans = _math_delimiter_spans(content)
    for match in _FUNCTION_SIGNATURE_PATTERN.finditer(content):
        if _within_any_span(match.start(), math_spans):
            continue
        name = match.group("name")
        # Filter out common non-function labels that accidentally match
        # the "Name : domain → codomain" pattern.
        if name.lower() in {"note", "remark", "example", "figure", "table", "proof", "theorem"}:
            continue
        line = line_number(content, match.start())
        if line in covered:
            continue
        domain = match.group("domain").strip()
        codomain = match.group("codomain").strip()
        expression_text = f"{domain} → {codomain}"
        snippet = _snippet_around(content, match.start(), match.end())
        results.append(
            FunctionDefinition(
                name=name,
                variable="",
                expression_text=expression_text,
                expression=None,
                line_number=line,
                snippet=snippet,
            )
        )
    return results


def _safe_parse_expression(expression_text: str, variable: str):
    try:
        return parse_expr(expression_text, variable_names=[variable])
    except Exception:
        logging.getLogger(__name__).debug(
            "Failed to parse markdown function expression: %.100s",
            expression_text,
            exc_info=True,
        )
        return None


def _math_delimiter_spans(content: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for pattern in (
        re.compile(r"\$\$[^$]+\$\$", re.DOTALL),
        re.compile(r"(?<!\$)\$(?!\$)[^$]+\$(?!\$)"),
        re.compile(r"\\\[.*?\\\]", re.DOTALL),
        re.compile(r"\\\(.*?\\\)", re.DOTALL),
    ):
        for match in pattern.finditer(content):
            spans.append((match.start(), match.end()))
    return spans


def _within_any_span(position: int, spans: list[tuple[int, int]]) -> bool:
    for start, end in spans:
        if start <= position < end:
            return True
    return False


def _snippet_around(content: str, start: int, end: int) -> str:
    line_start = content.rfind("\n", 0, start) + 1
    line_end = content.find("\n", end)
    if line_end == -1:
        line_end = len(content)
    return content[line_start:line_end].strip()
