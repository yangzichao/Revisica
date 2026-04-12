from __future__ import annotations

import re

from ..types import FunctionDefinition, MathClaim
from .latex_utils import line_number, normalize_latex, strip_group


def extract_claims(content: str, functions: list[FunctionDefinition]) -> list[MathClaim]:
    claims: list[MathClaim] = []
    claims.extend(_extract_integral_claims(content))
    claims.extend(_extract_average_value_claims(content))
    claims.extend(_extract_continuity_claims(content, functions))
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
