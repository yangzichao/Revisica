"""Extraction subpackage: LaTeX parsing, claim/structure extraction, blueprint construction."""

from .blueprints import (
    build_proof_blueprints,
    classify_obligation,
    extract_proof_obligations,
    find_proof_for_theorem,
    is_meaningful_proof_segment,
    normalize_math_block,
    split_proof_steps,
    split_proof_text,
)
from .claims import (
    extract_claims,
    nearest_function_before,
)
from .latex_utils import (
    compact_text,
    extract_math_segments,
    find_variable_names,
    line_number,
    normalize_latex,
    parse_expr,
    replace_latex_fractions,
    strip_group,
)
from .structures import (
    extract_functions,
    extract_proof_blocks,
    extract_theorem_blocks,
)

__all__ = [
    # latex_utils
    "compact_text",
    "extract_math_segments",
    "find_variable_names",
    "line_number",
    "normalize_latex",
    "parse_expr",
    "replace_latex_fractions",
    "strip_group",
    # claims
    "extract_claims",
    "nearest_function_before",
    # structures
    "extract_functions",
    "extract_proof_blocks",
    "extract_theorem_blocks",
    # blueprints
    "build_proof_blueprints",
    "classify_obligation",
    "extract_proof_obligations",
    "find_proof_for_theorem",
    "is_meaningful_proof_segment",
    "normalize_math_block",
    "split_proof_steps",
    "split_proof_text",
]
