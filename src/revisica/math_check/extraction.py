from __future__ import annotations

import logging
import re

import sympy as sp

from .types import (
    FunctionDefinition,
    MathClaim,
    ProofBlock,
    ProofBlueprint,
    ProofObligation,
    TheoremBlock,
)


def extract_functions(content: str) -> list[FunctionDefinition]:
    functions: list[FunctionDefinition] = []
    math_segments = extract_math_segments(content)
    for segment in math_segments:
        match = re.search(r"([A-Za-z]+)\(([A-Za-z])\)\s*=\s*(.+)", segment["text"])
        if not match:
            continue
        name = match.group(1)
        variable = match.group(2)
        expression_text = match.group(3).strip()
        try:
            expression = parse_expr(expression_text, variable_names=[variable])
        except Exception:
            logging.getLogger(__name__).warning(
                "Failed to parse LaTeX expression: %.100s", expression_text, exc_info=True,
            )
            continue
        functions.append(
            FunctionDefinition(
                name=name,
                variable=variable,
                expression_text=expression_text,
                expression=expression,
                line_number=int(segment["line_number"]),
                snippet=str(segment["raw"]),
            )
        )
    return functions


def extract_claims(content: str, functions: list[FunctionDefinition]) -> list[MathClaim]:
    claims: list[MathClaim] = []
    claims.extend(_extract_integral_claims(content))
    claims.extend(_extract_average_value_claims(content))
    claims.extend(_extract_continuity_claims(content, functions))
    return claims


def extract_theorem_blocks(content: str) -> list[TheoremBlock]:
    theorem_envs = ("theorem", "lemma", "proposition", "corollary", "claim")
    pattern = re.compile(
        r"\\begin\{(?P<env>" + "|".join(theorem_envs) + r")\}(?:\[(?P<title>[^\]]+)\])?\s*(?P<body>.*?)\s*\\end\{(?P=env)\}",
        re.DOTALL,
    )
    blocks: list[TheoremBlock] = []
    for match in pattern.finditer(content):
        blocks.append(
            TheoremBlock(
                env_name=match.group("env"),
                line_number=line_number(content, match.start()),
                title=match.group("title"),
                statement=match.group("body").strip(),
                snippet=match.group(0).strip(),
            )
        )
    return blocks


def extract_proof_blocks(content: str) -> list[ProofBlock]:
    pattern = re.compile(
        r"\\begin\{proof\}(?:\[(?P<title>[^\]]+)\])?\s*(?P<body>.*?)\s*\\end\{proof\}",
        re.DOTALL,
    )
    blocks: list[ProofBlock] = []
    for match in pattern.finditer(content):
        blocks.append(
            ProofBlock(
                line_number=line_number(content, match.start()),
                title=match.group("title"),
                body=match.group("body").strip(),
                snippet=match.group(0).strip(),
            )
        )
    return blocks


def build_proof_blueprints(
    theorems: list[TheoremBlock],
    proofs: list[ProofBlock],
) -> list[ProofBlueprint]:
    blueprints: list[ProofBlueprint] = []
    sorted_theorems = sorted(theorems, key=lambda item: item.line_number)
    sorted_proofs = sorted(proofs, key=lambda item: item.line_number)
    for index, theorem in enumerate(sorted_theorems):
        next_theorem_line = (
            sorted_theorems[index + 1].line_number
            if index + 1 < len(sorted_theorems)
            else None
        )
        proof = find_proof_for_theorem(sorted_proofs, theorem.line_number, next_theorem_line)
        obligations = extract_proof_obligations(theorem, proof)
        blueprints.append(
            ProofBlueprint(
                theorem=theorem,
                proof=proof,
                obligations=obligations,
            )
        )
    return blueprints


def compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


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


def line_number(content: str, index: int) -> int:
    return content.count("\n", 0, index) + 1


def nearest_function_before(
    functions: list[FunctionDefinition],
    line_number_value: int,
) -> FunctionDefinition | None:
    candidates = [item for item in functions if item.line_number <= line_number_value]
    if not candidates:
        return None
    return candidates[-1]


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


def find_proof_for_theorem(
    proofs: list[ProofBlock],
    theorem_line_number: int,
    next_theorem_line: int | None,
) -> ProofBlock | None:
    for proof in proofs:
        if proof.line_number <= theorem_line_number:
            continue
        if next_theorem_line is not None and proof.line_number >= next_theorem_line:
            continue
        return proof
    return None


def extract_proof_obligations(
    theorem: TheoremBlock,
    proof: ProofBlock | None,
) -> list[ProofObligation]:
    if proof is None:
        return []
    segments = split_proof_steps(proof.body)
    obligations: list[ProofObligation] = []
    for index, segment in enumerate(segments, start=1):
        obligations.append(
            ProofObligation(
                theorem_env=theorem.env_name,
                theorem_line_number=theorem.line_number,
                proof_line_number=proof.line_number,
                step_index=index,
                text=segment,
                obligation_type=classify_obligation(segment),
            )
        )
    return obligations


def split_proof_steps(text: str) -> list[str]:
    segments: list[str] = []
    cursor = 0
    for match in re.finditer(r"\\\[.*?\\\]|\$\$.*?\$\$", text, re.DOTALL):
        prefix = text[cursor:match.start()]
        segments.extend(split_proof_text(prefix))
        math_block = normalize_math_block(match.group(0))
        if math_block and is_meaningful_proof_segment(math_block):
            segments.append(math_block)
        cursor = match.end()
    segments.extend(split_proof_text(text[cursor:]))

    merged: list[str] = []
    pending_prefix: str | None = None
    for segment in segments:
        lowered = segment.lower()
        if lowered in {"therefore", "thus", "hence", "it follows"}:
            pending_prefix = segment
            continue
        if pending_prefix is not None:
            merged.append(f"{pending_prefix} {segment}".strip())
            pending_prefix = None
            continue
        if is_meaningful_proof_segment(segment):
            merged.append(segment)
    if pending_prefix is not None and is_meaningful_proof_segment(pending_prefix):
        merged.append(pending_prefix)
    return [segment for segment in merged if is_meaningful_proof_segment(segment)]


def split_proof_text(text: str) -> list[str]:
    working = text.replace("\n\n", "\n")
    segments: list[str] = []
    for raw_line in working.splitlines():
        line = compact_text(raw_line)
        if not line:
            continue
        if re.match(r"Step \d+:", line):
            segments.append(line)
            continue
        pieces = re.split(r"(?<=[.?!])\s+|\\\\", line)
        segments.extend(compact_text(piece) for piece in pieces if compact_text(piece))
    return segments


def normalize_math_block(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith(r"\[") and stripped.endswith(r"\]"):
        stripped = stripped[2:-2]
    elif stripped.startswith("$$") and stripped.endswith("$$"):
        stripped = stripped[2:-2]
    return compact_text(stripped)


def is_meaningful_proof_segment(text: str) -> bool:
    candidate = compact_text(text)
    if not candidate:
        return False
    if re.fullmatch(r"[\$\{\}\[\]\(\)\s]+", candidate):
        return False
    return bool(re.search(r"[A-Za-z0-9\\]", candidate))


def classify_obligation(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("therefore", "hence", "thus", "it follows")):
        return "inference"
    if any(token in lowered for token in ("by definition", "definition")):
        return "definition-use"
    if any(token in lowered for token in ("integral", "\\int", "=")):
        return "calculation"
    return "assertion"


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
