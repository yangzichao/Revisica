from __future__ import annotations

import re

import sympy as sp


def compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def line_number(content: str, index: int) -> int:
    return content.count("\n", 0, index) + 1


def strip_group(text: str) -> str:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text[1:-1]
    return text


def normalize_latex(text: str) -> str:
    normalized = text
    for needle in ("\\,", "\\!", "\\left", "\\right", "\n"):
        normalized = normalized.replace(needle, " ")
    return re.sub(r"\s+", " ", normalized).strip()


def parse_expr(text: str, variable_names: list[str]) -> sp.Expr:
    normalized = normalize_latex(text)
    normalized = normalized.rstrip(".,;:")
    normalized = replace_latex_fractions(normalized)
    normalized = normalized.replace("{", "(").replace("}", ")")
    normalized = normalized.replace("^", "**")
    normalized = normalized.replace("\\cdot", "*")
    normalized = normalized.replace("\\sqrt", "sqrt")
    normalized = normalized.replace("\\pi", "pi")
    normalized = normalized.replace("\\infty", "oo")
    locals_map: dict[str, object] = {
        "sqrt": sp.sqrt,
        "pi": sp.pi,
        "oo": sp.oo,
    }
    for name in set(variable_names):
        locals_map[name] = sp.Symbol(name, real=True)
    for name in find_variable_names(normalized):
        locals_map.setdefault(name, sp.Symbol(name, real=True))
    return sp.sympify(normalized, locals=locals_map)


def replace_latex_fractions(text: str) -> str:
    pattern = re.compile(r"\\(?:d?frac|tfrac)\{([^{}]+)\}\{([^{}]+)\}")
    previous = None
    current = text
    while previous != current:
        previous = current
        current = pattern.sub(r"((\1)/(\2))", current)
    return current


def find_variable_names(text: str) -> list[str]:
    candidates = re.findall(r"\b[a-zA-Z]\b", text)
    blocked = {"d", "e"}
    return [item for item in candidates if item not in blocked]


def extract_math_segments(content: str) -> list[dict[str, object]]:
    segments: list[dict[str, object]] = []
    patterns = [
        re.compile(r"\$(?P<body>[^$]+)\$"),
        re.compile(r"\\\[(?P<body>.*?)\\\]", re.DOTALL),
    ]
    for pattern in patterns:
        for match in pattern.finditer(content):
            segments.append(
                {
                    "text": match.group("body").strip(),
                    "raw": match.group(0).strip(),
                    "line_number": line_number(content, match.start()),
                }
            )
    segments.sort(key=lambda item: int(item["line_number"]))
    return segments
