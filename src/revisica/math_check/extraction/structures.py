from __future__ import annotations

import logging
import re

from ..types import FunctionDefinition, ProofBlock, TheoremBlock
from .latex_utils import extract_math_segments, line_number, parse_expr
from .structures_markdown import (
    extract_functions_markdown,
    extract_proof_blocks_markdown,
    extract_theorem_blocks_markdown,
)


def extract_functions(content: str) -> list[FunctionDefinition]:
    latex_functions = _extract_functions_latex(content)
    covered_lines = [item.line_number for item in latex_functions]
    markdown_functions = extract_functions_markdown(content, already_covered=covered_lines)
    return _merge_functions(latex_functions, markdown_functions)


def extract_theorem_blocks(content: str) -> list[TheoremBlock]:
    latex_blocks = _extract_theorem_blocks_latex(content)
    markdown_blocks = extract_theorem_blocks_markdown(content)
    return _merge_theorem_blocks(latex_blocks, markdown_blocks)


def extract_proof_blocks(content: str) -> list[ProofBlock]:
    latex_blocks = _extract_proof_blocks_latex(content)
    markdown_blocks = extract_proof_blocks_markdown(content)
    return _merge_proof_blocks(latex_blocks, markdown_blocks)


# ── LaTeX-native extractors ─────────────────────────────────────────────


def _extract_functions_latex(content: str) -> list[FunctionDefinition]:
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


def _extract_theorem_blocks_latex(content: str) -> list[TheoremBlock]:
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


def _extract_proof_blocks_latex(content: str) -> list[ProofBlock]:
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


# ── merge helpers ───────────────────────────────────────────────────────


def _merge_functions(
    latex_functions: list[FunctionDefinition],
    markdown_functions: list[FunctionDefinition],
) -> list[FunctionDefinition]:
    seen_keys: set[tuple[int, str, str]] = set()
    merged: list[FunctionDefinition] = []
    for item in latex_functions + markdown_functions:
        key = (item.line_number, item.name, item.expression_text)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        merged.append(item)
    merged.sort(key=lambda item: item.line_number)
    return merged


def _merge_theorem_blocks(
    latex_blocks: list[TheoremBlock],
    markdown_blocks: list[TheoremBlock],
) -> list[TheoremBlock]:
    merged: list[TheoremBlock] = list(latex_blocks)
    latex_line_numbers = {item.line_number for item in latex_blocks}
    for block in markdown_blocks:
        if block.line_number in latex_line_numbers:
            continue
        merged.append(block)
    merged.sort(key=lambda item: item.line_number)
    return merged


def _merge_proof_blocks(
    latex_blocks: list[ProofBlock],
    markdown_blocks: list[ProofBlock],
) -> list[ProofBlock]:
    merged: list[ProofBlock] = list(latex_blocks)
    latex_line_numbers = {item.line_number for item in latex_blocks}
    for block in markdown_blocks:
        if block.line_number in latex_line_numbers:
            continue
        merged.append(block)
    merged.sort(key=lambda item: item.line_number)
    return merged
