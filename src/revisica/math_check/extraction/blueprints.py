from __future__ import annotations

import re

from ..types import ProofBlock, ProofBlueprint, ProofObligation, TheoremBlock
from .latex_utils import compact_text


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
