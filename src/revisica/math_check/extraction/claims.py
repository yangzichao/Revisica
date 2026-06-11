from __future__ import annotations

import re

from ..types import FunctionDefinition, MathClaim
from .latex_utils import line_number, normalize_latex, strip_group


def extract_math_claims(content: str, functions: list[FunctionDefinition]) -> list[MathClaim]:
    claims: list[MathClaim] = []
    claims.extend(_extract_integral_claims(content))
    claims.extend(_extract_average_value_claims(content))
    claims.extend(_extract_continuity_claims(content, functions))
    claims.extend(_extract_bounded_inequality_claims(content))
    return claims


def nearest_function_before(
    functions: list[FunctionDefinition],
    line_number_value: int,
) -> FunctionDefinition | None:
    candidates = [item for item in functions if item.line_number <= line_number_value]
    if not candidates:
        return None
    return max(candidates, key=lambda f: f.line_number)


def _extract_integral_claims(content: str) -> list[MathClaim]:
    claims: list[MathClaim] = []
    pattern = re.compile(r"\\\[\s*(?P<body>.*?)\s*\\\]", re.DOTALL)
    for match in pattern.finditer(content):
        body = match.group("body").strip()
        normalized = normalize_latex(body)
        integral_match = re.search(
            r"\\int_(?P<a>\{[^}]+\}|[^\s^]+)\^(?P<b>\{[^}]+\}|[^\s]+)\s*(?P<integrand>.*?)\s*d(?P<var>[A-Za-z])\s*=\s*(?P<rhs>.+)",
            normalized,
            re.DOTALL,
        )
        if not integral_match:
            continue
        claims.append(
            MathClaim(
                kind="integral_equality",
                line_number=line_number(content, match.start()),
                snippet=match.group(0).strip(),
                details={
                    "a": strip_group(integral_match.group("a")),
                    "b": strip_group(integral_match.group("b")),
                    "integrand": integral_match.group("integrand").strip(),
                    "variable": integral_match.group("var"),
                    "rhs": integral_match.group("rhs").strip(),
                },
            )
        )
    return claims


def _extract_average_value_claims(content: str) -> list[MathClaim]:
    claims: list[MathClaim] = []
    pattern = re.compile(
        r"average value of (?P<expr>\$[^$]+\$|[^.\n]+?) on (?P<interval>\$?\[[^\]]+\]\$?) is (?:also )?(?P<rhs>[^.\n]+)",
        re.IGNORECASE,
    )
    for match in pattern.finditer(content):
        interval = match.group("interval").replace("$", "")
        interval_match = re.match(r"\[(?P<a>[^,]+),(?P<b>[^\]]+)\]", interval)
        if not interval_match:
            continue
        claims.append(
            MathClaim(
                kind="average_value",
                line_number=line_number(content, match.start()),
                snippet=match.group(0).strip(),
                details={
                    "expr": match.group("expr").strip().strip("$"),
                    "a": interval_match.group("a").strip(),
                    "b": interval_match.group("b").strip(),
                    "rhs": match.group("rhs").strip().strip("$"),
                },
            )
        )
    return claims


# Inequality claims are only extracted when the quantified interval is
# explicit — an unbounded "f(x) <= g(x)" may rely on assumptions stated
# elsewhere, and probing it numerically would produce false refutations.
_INEQUALITY_RELATIONS = {
    r"\le": "<=",
    r"\leq": "<=",
    r"\ge": ">=",
    r"\geq": ">=",
    "<": "<",
    ">": ">",
}

_DISPLAY_INEQUALITY_PATTERN = re.compile(
    r"(?P<lhs>[^<>=]+?)\s*(?P<op>\\le(?:q)?\b|\\ge(?:q)?\b|<|>)\s*(?P<rhs>[^<>=]+?)"
    r"\s*(?:\\quad|\\qquad|,)?\s*\\text\{\s*for all\s*\}\s*"
    r"(?P<var>[A-Za-z])\s*\\in\s*\[(?P<a>[^,\]]+),(?P<b>[^\]]+)\]",
)

_INLINE_INEQUALITY_PATTERN = re.compile(
    r"\$(?P<lhs>[^$<>=]+?)\s*(?P<op>\\le(?:q)?\b|\\ge(?:q)?\b|<|>)\s*(?P<rhs>[^$<>=]+?)\$"
    r"\s*(?:holds\s*)?for all\s*\$(?P<var>[A-Za-z])\s*\\in\s*\[(?P<a>[^,\]]+),(?P<b>[^\]]+)\]\$",
    re.IGNORECASE,
)


def _extract_bounded_inequality_claims(content: str) -> list[MathClaim]:
    claims: list[MathClaim] = []
    display_pattern = re.compile(r"\\\[\s*(?P<body>.*?)\s*\\\]", re.DOTALL)
    for match in display_pattern.finditer(content):
        body = normalize_latex(match.group("body"))
        inequality = _DISPLAY_INEQUALITY_PATTERN.search(body)
        if not inequality:
            continue
        claims.append(
            _bounded_inequality_claim(
                inequality, line_number(content, match.start()), match.group(0).strip()
            )
        )
    for match in _INLINE_INEQUALITY_PATTERN.finditer(content):
        claims.append(
            _bounded_inequality_claim(
                match, line_number(content, match.start()), match.group(0).strip()
            )
        )
    return claims


def _bounded_inequality_claim(
    match: re.Match[str],
    claim_line_number: int,
    snippet: str,
) -> MathClaim:
    relation = _INEQUALITY_RELATIONS[match.group("op").strip()]
    return MathClaim(
        kind="bounded_inequality",
        line_number=claim_line_number,
        snippet=snippet,
        details={
            "lhs": match.group("lhs").strip().rstrip(".,;:"),
            "rhs": match.group("rhs").strip().rstrip(".,;:"),
            "relation": relation,
            "variable": match.group("var").strip(),
            "a": match.group("a").strip(),
            "b": match.group("b").strip(),
        },
    )


def _extract_continuity_claims(
    content: str,
    functions: list[FunctionDefinition],
) -> list[MathClaim]:
    claims: list[MathClaim] = []
    pattern = re.compile(
        r"This function is continuous on (?P<interval>\$?\[[^\]]+\]\$?) so we can safely integrate it on this interval\.",
        re.IGNORECASE,
    )
    sorted_functions = sorted(functions, key=lambda item: item.line_number)
    for match in pattern.finditer(content):
        claim_line_number = line_number(content, match.start())
        function = nearest_function_before(sorted_functions, claim_line_number)
        if function is None:
            continue
        interval = match.group("interval").replace("$", "")
        interval_match = re.match(r"\[(?P<a>[^,]+),(?P<b>[^\]]+)\]", interval)
        if not interval_match:
            continue
        claims.append(
            MathClaim(
                kind="continuity_integrability",
                line_number=claim_line_number,
                snippet=match.group(0).strip(),
                details={
                    "function_name": function.name,
                    "function_expr": function.expression_text,
                    "variable": function.variable,
                    "a": interval_match.group("a").strip(),
                    "b": interval_match.group("b").strip(),
                },
            )
        )
    return claims
