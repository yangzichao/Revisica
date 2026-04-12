from __future__ import annotations

import logging
import re

from ..types import FunctionDefinition, ProofBlock, TheoremBlock
from .latex_utils import extract_math_segments, line_number, parse_expr


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
