"""Tests for the math_check.extraction subpackage."""

from __future__ import annotations

import textwrap

from hypothesis import given, settings, assume
from hypothesis import strategies as st
import pytest
import sympy as sp

from revisica.math_check.extraction.latex_utils import (
    compact_text,
    extract_math_segments,
    find_variable_names,
    line_number,
    normalize_latex,
    parse_expr,
    replace_latex_fractions,
    strip_group,
)
from revisica.math_check.extraction.claims import (
    extract_claims,
    nearest_function_before,
)
from revisica.math_check.extraction.structures import (
    extract_functions,
    extract_proof_blocks,
    extract_theorem_blocks,
)
from revisica.math_check.extraction.blueprints import (
    build_proof_blueprints,
    classify_obligation,
    extract_proof_obligations,
    find_proof_for_theorem,
    is_meaningful_proof_segment,
    normalize_math_block,
    split_proof_steps,
    split_proof_text,
)
from revisica.math_check.extraction import (
    extract_claims as extract_claims_reexport,
    parse_expr as parse_expr_reexport,
    compact_text as compact_text_reexport,
)


# ═══════════════════════════════════════════════════════════════════════
# latex_utils
# ═══════════════════════════════════════════════════════════════════════


class TestCompactText:
    def test_collapses_whitespace(self):
        assert compact_text("  hello   world  ") == "hello world"

    def test_collapses_newlines(self):
        assert compact_text("hello\n\n  world") == "hello world"

    def test_empty_string(self):
        assert compact_text("") == ""

    def test_single_word(self):
        assert compact_text("  x  ") == "x"


class TestLineNumber:
    def test_first_char(self):
        assert line_number("abc\ndef\nghi", 0) == 1

    def test_second_line(self):
        assert line_number("abc\ndef\nghi", 4) == 2

    def test_third_line(self):
        assert line_number("abc\ndef\nghi", 8) == 3

    def test_at_newline(self):
        assert line_number("abc\ndef", 3) == 1


class TestStripGroup:
    def test_braces(self):
        assert strip_group("{hello}") == "hello"

    def test_no_braces(self):
        assert strip_group("hello") == "hello"

    def test_nested_braces(self):
        assert strip_group("{a+b}") == "a+b"

    def test_whitespace(self):
        assert strip_group("  {x}  ") == "x"

    def test_empty_braces(self):
        assert strip_group("{}") == ""

    def test_only_opening(self):
        assert strip_group("{hello") == "{hello"


class TestNormalizeLatex:
    def test_removes_thin_space(self):
        assert "," not in normalize_latex(r"x \, dx")

    def test_removes_left_right(self):
        result = normalize_latex(r"\left( x \right)")
        assert "\\left" not in result
        assert "\\right" not in result

    def test_collapses_whitespace(self):
        assert normalize_latex("x    +   y") == "x + y"

    def test_removes_newlines(self):
        assert normalize_latex("x\n+\ny") == "x + y"


class TestReplaceLaTexFractions:
    def test_simple_frac(self):
        assert replace_latex_fractions(r"\frac{1}{2}") == "((1)/(2))"

    def test_dfrac(self):
        assert replace_latex_fractions(r"\dfrac{a}{b}") == "((a)/(b))"

    def test_tfrac(self):
        assert replace_latex_fractions(r"\tfrac{x}{y}") == "((x)/(y))"

    def test_nested_fracs(self):
        result = replace_latex_fractions(r"\frac{\frac{1}{2}}{3}")
        assert "\\frac" not in result

    def test_no_frac(self):
        assert replace_latex_fractions("x + y") == "x + y"


class TestFindVariableNames:
    def test_single_variable(self):
        assert find_variable_names("x + 1") == ["x"]

    def test_multiple_variables(self):
        result = find_variable_names("x + y + z")
        assert "x" in result
        assert "y" in result
        assert "z" in result

    def test_blocks_d_and_e(self):
        result = find_variable_names("d x + e y")
        assert "d" not in result
        assert "e" not in result
        assert "x" in result
        assert "y" in result

    def test_no_variables(self):
        assert find_variable_names("123 + 456") == []

    def test_multichar_words_excluded(self):
        # Only single-char matches; "sin" has no single-char word boundary match
        result = find_variable_names("sin(x)")
        assert "x" in result


class TestParseExpr:
    def test_simple_polynomial(self):
        x = sp.Symbol("x", real=True)
        result = parse_expr("x**2 + 1", variable_names=["x"])
        assert sp.simplify(result - (x**2 + 1)) == 0

    def test_latex_power(self):
        x = sp.Symbol("x", real=True)
        result = parse_expr("x^2", variable_names=["x"])
        assert sp.simplify(result - x**2) == 0

    def test_latex_frac(self):
        result = parse_expr(r"\frac{1}{2}", variable_names=[])
        assert result == sp.Rational(1, 2)

    def test_latex_sqrt(self):
        x = sp.Symbol("x", real=True)
        result = parse_expr(r"\sqrt{x}", variable_names=["x"])
        assert sp.simplify(result - sp.sqrt(x)) == 0

    def test_latex_pi(self):
        result = parse_expr(r"\pi", variable_names=[])
        assert result == sp.pi

    def test_latex_infty(self):
        result = parse_expr(r"\infty", variable_names=[])
        assert result == sp.oo

    def test_latex_cdot(self):
        x = sp.Symbol("x", real=True)
        result = parse_expr(r"2 \cdot x", variable_names=["x"])
        assert sp.simplify(result - 2 * x) == 0

    def test_strips_trailing_punctuation(self):
        x = sp.Symbol("x", real=True)
        result = parse_expr("x^2.", variable_names=["x"])
        assert sp.simplify(result - x**2) == 0

    def test_complex_frac_expression(self):
        x = sp.Symbol("x", real=True)
        result = parse_expr(r"\frac{x^2 + 1}{2}", variable_names=["x"])
        expected = (x**2 + 1) / 2
        assert sp.simplify(result - expected) == 0

    def test_auto_detects_variables(self):
        # "t" not passed in variable_names but should be auto-detected
        result = parse_expr("t^2", variable_names=[])
        t = sp.Symbol("t", real=True)
        assert sp.simplify(result - t**2) == 0

    def test_latex_thin_space_ignored(self):
        x = sp.Symbol("x", real=True)
        result = parse_expr(r"x^2 \, + \, 1", variable_names=["x"])
        assert sp.simplify(result - (x**2 + 1)) == 0


class TestExtractMathSegments:
    def test_inline_math(self):
        content = "The value $x^2$ is positive."
        segments = extract_math_segments(content)
        assert len(segments) == 1
        assert segments[0]["text"] == "x^2"

    def test_display_math(self):
        content = "We compute\n\\[\nx^2 + 1\n\\]\nwhich is positive."
        segments = extract_math_segments(content)
        assert len(segments) == 1
        assert "x^2 + 1" in segments[0]["text"]

    def test_multiple_segments(self):
        content = "Let $a = 1$ and $b = 2$."
        segments = extract_math_segments(content)
        assert len(segments) == 2

    def test_line_numbers(self):
        content = "line1\nline2 $x$\nline3\n\\[\ny\n\\]"
        segments = extract_math_segments(content)
        assert segments[0]["line_number"] == 2  # $x$ on line 2
        assert segments[1]["line_number"] == 4  # \[ on line 4

    def test_no_math(self):
        segments = extract_math_segments("Just plain text.")
        assert segments == []

    def test_sorted_by_line(self):
        content = "\\[\nalpha\n\\]\n$beta$"
        segments = extract_math_segments(content)
        assert int(segments[0]["line_number"]) <= int(segments[1]["line_number"])


# ═══════════════════════════════════════════════════════════════════════
# claims
# ═══════════════════════════════════════════════════════════════════════


class TestExtractIntegralClaims:
    def test_correct_integral(self):
        content = textwrap.dedent(r"""
            We compute
            \[
            \int_0^1 x^2 \, dx = \frac{1}{3}
            \]
        """)
        claims = extract_claims(content, [])
        integral_claims = [c for c in claims if c.kind == "integral_equality"]
        assert len(integral_claims) == 1
        claim = integral_claims[0]
        assert claim.details["a"] == "0"
        assert claim.details["b"] == "1"
        assert claim.details["variable"] == "x"

    def test_wrong_integral(self):
        content = textwrap.dedent(r"""
            \[
            \int_0^1 x^2 \, dx = \frac{1}{2}
            \]
        """)
        claims = extract_claims(content, [])
        assert len(claims) == 1
        assert claims[0].kind == "integral_equality"
        assert "1" in claims[0].details["rhs"]

    def test_integral_with_braces(self):
        content = textwrap.dedent(r"""
            \[
            \int_{-1}^{1} x^3 \, dx = 0
            \]
        """)
        claims = extract_claims(content, [])
        integral_claims = [c for c in claims if c.kind == "integral_equality"]
        assert len(integral_claims) == 1
        assert integral_claims[0].details["a"] == "-1"
        assert integral_claims[0].details["b"] == "1"

    def test_non_integral_display_math_not_matched(self):
        content = textwrap.dedent(r"""
            \[
            x^2 + y^2 = 1
            \]
        """)
        claims = extract_claims(content, [])
        integral_claims = [c for c in claims if c.kind == "integral_equality"]
        assert len(integral_claims) == 0

    def test_multiple_integrals(self):
        content = textwrap.dedent(r"""
            \[
            \int_0^1 x \, dx = \frac{1}{2}
            \]
            \[
            \int_0^2 x \, dx = 2
            \]
        """)
        claims = extract_claims(content, [])
        integral_claims = [c for c in claims if c.kind == "integral_equality"]
        assert len(integral_claims) == 2


class TestExtractAverageValueClaims:
    def test_basic_average(self):
        content = "The average value of $x^2$ on $[0,1]$ is $\\frac{1}{3}$."
        claims = extract_claims(content, [])
        avg_claims = [c for c in claims if c.kind == "average_value"]
        assert len(avg_claims) == 1
        assert avg_claims[0].details["a"] == "0"
        assert avg_claims[0].details["b"] == "1"

    def test_average_with_also(self):
        content = "The average value of $f(x)$ on $[0,2]$ is also $4$."
        claims = extract_claims(content, [])
        avg_claims = [c for c in claims if c.kind == "average_value"]
        assert len(avg_claims) == 1

    def test_no_average_claims(self):
        content = "The maximum value of f on [0,1] is 5."
        claims = extract_claims(content, [])
        avg_claims = [c for c in claims if c.kind == "average_value"]
        assert len(avg_claims) == 0


class TestExtractContinuityClaims:
    def test_basic_continuity(self):
        content = textwrap.dedent(r"""
            $f(x) = x^2$

            This function is continuous on $[0,1]$ so we can safely integrate it on this interval.
        """)
        functions = extract_functions(content)
        claims = extract_claims(content, functions)
        cont_claims = [c for c in claims if c.kind == "continuity_integrability"]
        assert len(cont_claims) == 1
        assert cont_claims[0].details["function_name"] == "f"
        assert cont_claims[0].details["a"] == "0"
        assert cont_claims[0].details["b"] == "1"

    def test_no_function_before(self):
        content = "This function is continuous on $[0,1]$ so we can safely integrate it on this interval."
        claims = extract_claims(content, [])
        cont_claims = [c for c in claims if c.kind == "continuity_integrability"]
        assert len(cont_claims) == 0


class TestNearestFunctionBefore:
    def test_returns_closest(self):
        from revisica.math_check.types import FunctionDefinition

        f1 = FunctionDefinition(
            name="f", variable="x", expression_text="x^2",
            expression=sp.Symbol("x") ** 2, line_number=5, snippet="$f(x) = x^2$",
        )
        f2 = FunctionDefinition(
            name="g", variable="x", expression_text="x^3",
            expression=sp.Symbol("x") ** 3, line_number=10, snippet="$g(x) = x^3$",
        )
        result = nearest_function_before([f1, f2], 12)
        assert result.name == "g"

    def test_returns_none_if_all_after(self):
        from revisica.math_check.types import FunctionDefinition

        f1 = FunctionDefinition(
            name="f", variable="x", expression_text="x^2",
            expression=sp.Symbol("x") ** 2, line_number=10, snippet="$f(x) = x^2$",
        )
        assert nearest_function_before([f1], 5) is None


# ═══════════════════════════════════════════════════════════════════════
# structures
# ═══════════════════════════════════════════════════════════════════════


class TestExtractFunctions:
    def test_simple_function(self):
        content = "Let $f(x) = x^2$ be a function."
        functions = extract_functions(content)
        assert len(functions) == 1
        assert functions[0].name == "f"
        assert functions[0].variable == "x"

    def test_different_variable(self):
        content = "Define $g(t) = t^3 + 1$."
        functions = extract_functions(content)
        assert len(functions) == 1
        assert functions[0].name == "g"
        assert functions[0].variable == "t"

    def test_multiple_functions(self):
        content = "Let $f(x) = x^2$ and $g(x) = x^3$."
        functions = extract_functions(content)
        assert len(functions) == 2

    def test_no_functions(self):
        content = "There are no function definitions here."
        functions = extract_functions(content)
        assert functions == []

    def test_function_with_fraction(self):
        content = r"Define $h(x) = \frac{1}{x}$."
        functions = extract_functions(content)
        assert len(functions) == 1
        assert functions[0].name == "h"

    def test_display_math_function(self):
        content = "We define\n\\[\nf(x) = x^2 + 1\n\\]\nas our function."
        functions = extract_functions(content)
        assert len(functions) == 1
        assert functions[0].name == "f"


class TestExtractTheoremBlocks:
    def test_single_theorem(self):
        content = textwrap.dedent(r"""
            \begin{theorem}
            For all $x > 0$, we have $x^2 > 0$.
            \end{theorem}
        """)
        blocks = extract_theorem_blocks(content)
        assert len(blocks) == 1
        assert blocks[0].env_name == "theorem"
        assert "x^2 > 0" in blocks[0].statement

    def test_theorem_with_title(self):
        content = textwrap.dedent(r"""
            \begin{theorem}[Main Result]
            Something important.
            \end{theorem}
        """)
        blocks = extract_theorem_blocks(content)
        assert len(blocks) == 1
        assert blocks[0].title == "Main Result"

    def test_lemma(self):
        content = textwrap.dedent(r"""
            \begin{lemma}
            A helpful lemma.
            \end{lemma}
        """)
        blocks = extract_theorem_blocks(content)
        assert len(blocks) == 1
        assert blocks[0].env_name == "lemma"

    def test_proposition(self):
        content = "\\begin{proposition}\nSome proposition.\n\\end{proposition}"
        blocks = extract_theorem_blocks(content)
        assert len(blocks) == 1
        assert blocks[0].env_name == "proposition"

    def test_corollary(self):
        content = "\\begin{corollary}\nA corollary.\n\\end{corollary}"
        blocks = extract_theorem_blocks(content)
        assert len(blocks) == 1
        assert blocks[0].env_name == "corollary"

    def test_claim_env(self):
        content = "\\begin{claim}\nA claim.\n\\end{claim}"
        blocks = extract_theorem_blocks(content)
        assert len(blocks) == 1
        assert blocks[0].env_name == "claim"

    def test_multiple_theorems(self):
        content = textwrap.dedent(r"""
            \begin{theorem}
            First theorem.
            \end{theorem}

            \begin{lemma}
            A lemma.
            \end{lemma}

            \begin{theorem}
            Second theorem.
            \end{theorem}
        """)
        blocks = extract_theorem_blocks(content)
        assert len(blocks) == 3

    def test_no_theorems(self):
        content = "Just some text with no theorems."
        assert extract_theorem_blocks(content) == []

    def test_line_number_tracked(self):
        content = "line1\nline2\n\\begin{theorem}\nStatement.\n\\end{theorem}"
        blocks = extract_theorem_blocks(content)
        assert blocks[0].line_number == 3


class TestExtractProofBlocks:
    def test_single_proof(self):
        content = textwrap.dedent(r"""
            \begin{proof}
            We proceed by induction.
            \end{proof}
        """)
        blocks = extract_proof_blocks(content)
        assert len(blocks) == 1
        assert "induction" in blocks[0].body

    def test_proof_with_title(self):
        content = textwrap.dedent(r"""
            \begin{proof}[Proof of Theorem 1]
            The proof is clear.
            \end{proof}
        """)
        blocks = extract_proof_blocks(content)
        assert len(blocks) == 1
        assert blocks[0].title == "Proof of Theorem 1"

    def test_no_proofs(self):
        assert extract_proof_blocks("No proofs here.") == []

    def test_multiple_proofs(self):
        content = textwrap.dedent(r"""
            \begin{proof}
            First proof.
            \end{proof}

            \begin{proof}
            Second proof.
            \end{proof}
        """)
        blocks = extract_proof_blocks(content)
        assert len(blocks) == 2


# ═══════════════════════════════════════════════════════════════════════
# blueprints
# ═══════════════════════════════════════════════════════════════════════


class TestBuildProofBlueprints:
    def test_theorem_with_proof(self):
        content = textwrap.dedent(r"""
            \begin{theorem}
            Statement.
            \end{theorem}

            \begin{proof}
            The proof is obvious.
            \end{proof}
        """)
        theorems = extract_theorem_blocks(content)
        proofs = extract_proof_blocks(content)
        blueprints = build_proof_blueprints(theorems, proofs)
        assert len(blueprints) == 1
        assert blueprints[0].proof is not None
        assert len(blueprints[0].obligations) > 0

    def test_theorem_without_proof(self):
        content = textwrap.dedent(r"""
            \begin{theorem}
            Statement without proof.
            \end{theorem}
        """)
        theorems = extract_theorem_blocks(content)
        proofs = extract_proof_blocks(content)
        blueprints = build_proof_blueprints(theorems, proofs)
        assert len(blueprints) == 1
        assert blueprints[0].proof is None
        assert blueprints[0].obligations == []

    def test_two_theorems_two_proofs(self):
        content = textwrap.dedent(r"""
            \begin{theorem}
            First statement.
            \end{theorem}
            \begin{proof}
            First proof.
            \end{proof}

            \begin{theorem}
            Second statement.
            \end{theorem}
            \begin{proof}
            Second proof.
            \end{proof}
        """)
        theorems = extract_theorem_blocks(content)
        proofs = extract_proof_blocks(content)
        blueprints = build_proof_blueprints(theorems, proofs)
        assert len(blueprints) == 2
        assert all(bp.proof is not None for bp in blueprints)

    def test_proof_not_stolen_by_earlier_theorem(self):
        content = textwrap.dedent(r"""
            \begin{theorem}
            First.
            \end{theorem}
            \begin{proof}
            Proof of first.
            \end{proof}

            \begin{theorem}
            Second, no proof.
            \end{theorem}
        """)
        theorems = extract_theorem_blocks(content)
        proofs = extract_proof_blocks(content)
        blueprints = build_proof_blueprints(theorems, proofs)
        assert blueprints[0].proof is not None
        assert blueprints[1].proof is None


class TestFindProofForTheorem:
    def test_finds_next_proof(self):
        from revisica.math_check.types import ProofBlock

        proofs = [
            ProofBlock(line_number=10, title=None, body="proof body", snippet="..."),
        ]
        result = find_proof_for_theorem(proofs, theorem_line_number=5, next_theorem_line=None)
        assert result is not None
        assert result.line_number == 10

    def test_skips_proof_before_theorem(self):
        from revisica.math_check.types import ProofBlock

        proofs = [
            ProofBlock(line_number=3, title=None, body="early proof", snippet="..."),
        ]
        result = find_proof_for_theorem(proofs, theorem_line_number=5, next_theorem_line=None)
        assert result is None

    def test_respects_next_theorem_boundary(self):
        from revisica.math_check.types import ProofBlock

        proofs = [
            ProofBlock(line_number=20, title=None, body="late proof", snippet="..."),
        ]
        result = find_proof_for_theorem(proofs, theorem_line_number=5, next_theorem_line=15)
        assert result is None


class TestSplitProofSteps:
    def test_sentences(self):
        text = "We start with x. Then we apply the theorem. The result follows."
        steps = split_proof_steps(text)
        assert len(steps) == 3

    def test_display_math_extracted(self):
        text = r"Consider \[ x^2 + 1 \] which is positive."
        steps = split_proof_steps(text)
        assert any("x^2 + 1" in s for s in steps)

    def test_therefore_merged_with_next(self):
        text = "We know x > 0. Therefore x^2 > 0."
        steps = split_proof_steps(text)
        merged = [s for s in steps if "Therefore" in s]
        assert len(merged) == 1
        assert "x^2 > 0" in merged[0]

    def test_step_numbered(self):
        text = "Step 1: Do something.\nStep 2: Do another thing."
        steps = split_proof_steps(text)
        assert any("Step 1:" in s for s in steps)
        assert any("Step 2:" in s for s in steps)

    def test_empty_text(self):
        assert split_proof_steps("") == []

    def test_double_dollar_math(self):
        text = "We have $$x + y = z$$ as desired."
        steps = split_proof_steps(text)
        assert any("x + y = z" in s for s in steps)


class TestSplitProofText:
    def test_sentence_splitting(self):
        text = "First sentence. Second sentence."
        segments = split_proof_text(text)
        assert len(segments) == 2

    def test_double_backslash_split(self):
        text = r"Line one\\Line two"
        segments = split_proof_text(text)
        assert len(segments) == 2

    def test_empty_lines_collapsed(self):
        text = "Hello.\n\n\nWorld."
        segments = split_proof_text(text)
        assert len(segments) == 2


class TestNormalizeMathBlock:
    def test_strip_display_delimiters(self):
        assert normalize_math_block(r"\[ x^2 \]") == "x^2"

    def test_strip_double_dollar(self):
        assert normalize_math_block("$$ y + 1 $$") == "y + 1"

    def test_plain_text(self):
        assert normalize_math_block("  hello  ") == "hello"


class TestIsMeaningfulProofSegment:
    def test_text_is_meaningful(self):
        assert is_meaningful_proof_segment("We apply the theorem.") is True

    def test_empty_not_meaningful(self):
        assert is_meaningful_proof_segment("") is False

    def test_only_brackets_not_meaningful(self):
        assert is_meaningful_proof_segment("${}[]()") is False

    def test_math_is_meaningful(self):
        assert is_meaningful_proof_segment(r"\int_0^1 x") is True


class TestClassifyObligation:
    def test_inference(self):
        assert classify_obligation("Therefore x > 0") == "inference"
        assert classify_obligation("Hence the result") == "inference"
        assert classify_obligation("Thus we conclude") == "inference"
        assert classify_obligation("It follows that y = 1") == "inference"

    def test_definition_use(self):
        assert classify_obligation("By definition of continuity") == "definition-use"

    def test_calculation(self):
        assert classify_obligation("x = 2 + 3") == "calculation"
        assert classify_obligation(r"The integral \int is finite") == "calculation"

    def test_assertion(self):
        assert classify_obligation("We claim this is true") == "assertion"


# ═══════════════════════════════════════════════════════════════════════
# __init__ re-exports
# ═══════════════════════════════════════════════════════════════════════


class TestReexports:
    def test_parse_expr_reexport(self):
        assert parse_expr_reexport is parse_expr

    def test_extract_claims_reexport(self):
        assert extract_claims_reexport is extract_claims

    def test_compact_text_reexport(self):
        assert compact_text_reexport is compact_text


# ═══════════════════════════════════════════════════════════════════════
# integration: full LaTeX documents
# ═══════════════════════════════════════════════════════════════════════


class TestFullDocument:
    """End-to-end tests using realistic LaTeX snippets."""

    PAPER_CORRECT_INTEGRAL = textwrap.dedent(r"""
        \documentclass{article}
        \usepackage{amsmath}
        \begin{document}
        We compute
        \[
        \int_0^1 x^2 \, dx = \frac{1}{3}.
        \]
        \end{document}
    """)

    PAPER_WRONG_INTEGRAL = textwrap.dedent(r"""
        \documentclass{article}
        \usepackage{amsmath}
        \begin{document}
        We compute
        \[
        \int_0^1 x^2 \, dx = \frac{1}{2}.
        \]
        \end{document}
    """)

    PAPER_WITH_THEOREM_AND_PROOF = textwrap.dedent(r"""
        \documentclass{article}
        \usepackage{amsmath,amsthm}
        \newtheorem{theorem}{Theorem}
        \begin{document}

        \begin{theorem}
        We have
        \[
        \int_0^1 x^2 \, dx = \frac{1}{2}.
        \]
        \end{theorem}

        \begin{proof}
        Clearly, the antiderivative of $x^2$ is $x^2/2$.
        Therefore
        \[
        \int_0^1 x^2 \, dx = \frac{1}{2}.
        \]
        Thus the theorem follows.
        \end{proof}

        \end{document}
    """)

    PAPER_CONTINUITY = textwrap.dedent(r"""
        \documentclass{article}
        \usepackage{amsmath}
        \begin{document}
        Define $f(x) = \frac{1}{x}$.
        This function is continuous on $[-1, 1]$ so we can safely integrate it on this interval.
        \end{document}
    """)

    def test_correct_integral_claims(self):
        claims = extract_claims(self.PAPER_CORRECT_INTEGRAL, [])
        integral_claims = [c for c in claims if c.kind == "integral_equality"]
        assert len(integral_claims) == 1
        assert integral_claims[0].details["variable"] == "x"

    def test_wrong_integral_claims(self):
        claims = extract_claims(self.PAPER_WRONG_INTEGRAL, [])
        integral_claims = [c for c in claims if c.kind == "integral_equality"]
        assert len(integral_claims) == 1

    def test_theorem_proof_blueprint(self):
        content = self.PAPER_WITH_THEOREM_AND_PROOF
        theorems = extract_theorem_blocks(content)
        proofs = extract_proof_blocks(content)
        assert len(theorems) == 1
        assert len(proofs) == 1
        blueprints = build_proof_blueprints(theorems, proofs)
        assert len(blueprints) == 1
        bp = blueprints[0]
        assert bp.proof is not None
        assert len(bp.obligations) >= 2
        # Should have at least one inference obligation (from "Therefore"/"Thus")
        obligation_types = [o.obligation_type for o in bp.obligations]
        assert "inference" in obligation_types

    def test_continuity_claim_extracted(self):
        content = self.PAPER_CONTINUITY
        functions = extract_functions(content)
        assert len(functions) == 1
        assert functions[0].name == "f"
        claims = extract_claims(content, functions)
        cont_claims = [c for c in claims if c.kind == "continuity_integrability"]
        assert len(cont_claims) == 1
        assert cont_claims[0].details["function_name"] == "f"
        assert cont_claims[0].details["a"] == "-1"
        assert cont_claims[0].details["b"] == "1"

    def test_extract_all_from_complex_document(self):
        content = textwrap.dedent(r"""
            \documentclass{article}
            \usepackage{amsmath,amsthm}
            \newtheorem{theorem}{Theorem}
            \newtheorem{lemma}{Lemma}
            \begin{document}

            Define $f(x) = x^2 + 1$.

            \begin{lemma}
            The function $f$ is continuous everywhere.
            \end{lemma}
            \begin{proof}
            This follows from the fact that polynomials are continuous.
            \end{proof}

            \begin{theorem}[Main Result]
            We have
            \[
            \int_0^1 f(x) \, dx = \frac{4}{3}.
            \]
            \end{theorem}
            \begin{proof}
            By direct computation,
            \[
            \int_0^1 (x^2 + 1) \, dx = \frac{1}{3} + 1 = \frac{4}{3}.
            \]
            Hence the result.
            \end{proof}

            \end{document}
        """)
        functions = extract_functions(content)
        assert len(functions) >= 1

        theorems = extract_theorem_blocks(content)
        assert len(theorems) == 2  # lemma + theorem

        proofs = extract_proof_blocks(content)
        assert len(proofs) == 2

        blueprints = build_proof_blueprints(theorems, proofs)
        assert len(blueprints) == 2
        assert all(bp.proof is not None for bp in blueprints)

        claims = extract_claims(content, functions)
        integral_claims = [c for c in claims if c.kind == "integral_equality"]
        assert len(integral_claims) >= 1


# ═══════════════════════════════════════════════════════════════════════
# Parametrized: parse_expr with many LaTeX → SymPy pairs
# ═══════════════════════════════════════════════════════════════════════

_x = sp.Symbol("x", real=True)
_t = sp.Symbol("t", real=True)
_y = sp.Symbol("y", real=True)


class TestParseExprParametrized:
    """Bulk LaTeX→SymPy verification covering common textbook patterns."""

    @pytest.mark.parametrize(
        "latex, vars, expected",
        [
            # --- polynomials ---
            ("x", ["x"], _x),
            ("3", [], sp.Integer(3)),
            ("x + 1", ["x"], _x + 1),
            ("x^3 - x", ["x"], _x**3 - _x),
            ("2*x^2 + 3*x + 1", ["x"], 2 * _x**2 + 3 * _x + 1),
            # --- fractions ---
            (r"\frac{1}{3}", [], sp.Rational(1, 3)),
            (r"\frac{x}{2}", ["x"], _x / 2),
            (r"\dfrac{3}{4}", [], sp.Rational(3, 4)),
            (r"\tfrac{5}{6}", [], sp.Rational(5, 6)),
            (r"\frac{x^2 + 1}{x - 1}", ["x"], (_x**2 + 1) / (_x - 1)),
            # nested fractions
            (r"\frac{\frac{1}{2}}{3}", [], sp.Rational(1, 6)),
            (r"\frac{1}{\frac{2}{3}}", [], sp.Rational(3, 2)),
            # --- sqrt ---
            (r"\sqrt{4}", [], sp.Integer(2)),
            (r"\sqrt{x}", ["x"], sp.sqrt(_x)),
            (r"\sqrt{x^2 + 1}", ["x"], sp.sqrt(_x**2 + 1)),
            # --- pi / infinity ---
            (r"2 \cdot \pi", [], 2 * sp.pi),
            (r"\pi^2", [], sp.pi**2),
            (r"\frac{\pi}{2}", [], sp.pi / 2),
            # --- cdot multiplication ---
            (r"3 \cdot 5", [], sp.Integer(15)),
            (r"x \cdot x", ["x"], _x**2),
            # --- combined ---
            (r"\frac{1}{2} + \frac{1}{3}", [], sp.Rational(5, 6)),
            (r"x^2 + \frac{1}{x}", ["x"], _x**2 + 1 / _x),
            # --- trailing punctuation ---
            ("x^2;", ["x"], _x**2),
            ("x + 1,", ["x"], _x + 1),
            (r"\frac{1}{2}.", [], sp.Rational(1, 2)),
            # --- \left / \right ignored ---
            (r"\left( x + 1 \right)^2", ["x"], (_x + 1) ** 2),
            # --- different variable ---
            ("t^2 + t", ["t"], _t**2 + _t),
        ],
        ids=lambda val: str(val)[:40],
    )
    def test_parse(self, latex: str, vars: list[str], expected: sp.Expr):
        result = parse_expr(latex, variable_names=vars)
        assert sp.simplify(result - expected) == 0, (
            f"parse_expr({latex!r}) = {result}, expected {expected}"
        )


# ═══════════════════════════════════════════════════════════════════════
# Parametrized: integral claim extraction
# ═══════════════════════════════════════════════════════════════════════


class TestIntegralClaimVariants:
    """Verify integral claim extraction against many common integral forms."""

    @pytest.mark.parametrize(
        "body, a, b, var",
        [
            # basic
            (r"\int_0^1 x^2 \, dx = \frac{1}{3}", "0", "1", "x"),
            # braced bounds
            (r"\int_{-1}^{1} x^3 \, dx = 0", "-1", "1", "x"),
            # higher power
            (r"\int_0^2 t^4 \, dt = \frac{32}{5}", "0", "2", "t"),
            # fraction bounds
            (r"\int_0^{\pi} x \, dx = \frac{\pi^2}{2}", "0", r"\pi", "x"),
            # constant integrand
            (r"\int_1^3 5 \, dx = 10", "1", "3", "x"),
            # different variable
            (r"\int_0^1 s^2 \, ds = \frac{1}{3}", "0", "1", "s"),
        ],
    )
    def test_extraction(self, body: str, a: str, b: str, var: str):
        content = f"\\[\n{body}\n\\]"
        claims = extract_claims(content, [])
        integral_claims = [c for c in claims if c.kind == "integral_equality"]
        assert len(integral_claims) == 1, f"Expected 1 integral claim, got {len(integral_claims)}"
        claim = integral_claims[0]
        assert claim.details["a"] == a
        assert claim.details["b"] == b
        assert claim.details["variable"] == var

    def test_inline_math_not_matched(self):
        """Integral claims only come from display math \\[...\\]."""
        content = r"We know $\int_0^1 x \, dx = \frac{1}{2}$ is true."
        claims = extract_claims(content, [])
        integral_claims = [c for c in claims if c.kind == "integral_equality"]
        assert len(integral_claims) == 0


# ═══════════════════════════════════════════════════════════════════════
# Parametrized: classify_obligation
# ═══════════════════════════════════════════════════════════════════════


class TestClassifyObligationParametrized:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Therefore x > 0.", "inference"),
            ("hence the claim follows", "inference"),
            ("Thus we are done.", "inference"),
            ("It follows from the above.", "inference"),
            ("By definition, f is continuous.", "definition-use"),
            ("The definition of compactness gives us.", "definition-use"),
            ("We compute x = 2 + 3.", "calculation"),
            ("Evaluating the integral gives 5.", "calculation"),
            (r"We use \int_0^1 f(x) dx.", "calculation"),
            ("Suppose x > 0.", "assertion"),
            ("Let epsilon > 0 be given.", "assertion"),
            ("We claim that A is true.", "assertion"),
            ("Consider the set S.", "assertion"),
        ],
    )
    def test_classify(self, text: str, expected: str):
        assert classify_obligation(text) == expected


# ═══════════════════════════════════════════════════════════════════════
# Property-based tests (hypothesis)
# ═══════════════════════════════════════════════════════════════════════


class TestPropertyBased:
    """Invariants that should hold for any input."""

    @given(st.text(max_size=200))
    @settings(max_examples=100)
    def test_compact_text_idempotent(self, text: str):
        once = compact_text(text)
        twice = compact_text(once)
        assert once == twice

    @given(st.text(max_size=200))
    @settings(max_examples=100)
    def test_normalize_latex_idempotent(self, text: str):
        once = normalize_latex(text)
        twice = normalize_latex(once)
        assert once == twice

    @given(st.text(max_size=200))
    @settings(max_examples=100)
    def test_compact_text_no_leading_trailing_whitespace(self, text: str):
        result = compact_text(text)
        assert result == result.strip()

    @given(st.text(max_size=200))
    @settings(max_examples=100)
    def test_compact_text_no_double_spaces(self, text: str):
        result = compact_text(text)
        assert "  " not in result

    @given(st.text(max_size=300))
    @settings(max_examples=50)
    def test_normalize_latex_no_double_spaces(self, text: str):
        result = normalize_latex(text)
        assert "  " not in result

    @given(st.integers(min_value=1, max_value=5))
    def test_find_variable_names_never_returns_d_or_e(self, n: int):
        text = " ".join(chr(ord("a") + i) for i in range(n))
        result = find_variable_names(text)
        assert "d" not in result
        assert "e" not in result

    @given(
        st.integers(min_value=0, max_value=5),
        st.integers(min_value=0, max_value=5),
    )
    def test_replace_latex_fractions_idempotent_after_full_pass(self, a: int, b: int):
        assume(b != 0)
        text = rf"\frac{{{a}}}{{{b}}}"
        once = replace_latex_fractions(text)
        twice = replace_latex_fractions(once)
        assert once == twice
        assert "\\frac" not in once

    @given(st.text(alphabet=st.characters(whitelist_categories=("L", "N", "P")), max_size=80))
    @settings(max_examples=50)
    def test_is_meaningful_never_crashes(self, text: str):
        # Should never raise, regardless of input.
        result = is_meaningful_proof_segment(text)
        assert isinstance(result, bool)

    @given(st.text(max_size=100))
    @settings(max_examples=50)
    def test_classify_obligation_always_valid_category(self, text: str):
        result = classify_obligation(text)
        assert result in {"inference", "definition-use", "calculation", "assertion"}


class TestPropertyBasedBlueprints:
    """Structural invariants on blueprint construction."""

    @given(
        st.integers(min_value=1, max_value=5),
        st.integers(min_value=0, max_value=5),
    )
    @settings(max_examples=30)
    def test_blueprint_count_equals_theorem_count(self, n_theorems: int, n_proofs: int):
        """Number of blueprints always equals number of theorems."""
        doc_parts = []
        for i in range(n_theorems):
            doc_parts.append(
                f"\\begin{{theorem}}\nTheorem {i}.\n\\end{{theorem}}\n"
            )
            if i < n_proofs:
                doc_parts.append(
                    f"\\begin{{proof}}\nProof of theorem {i}.\n\\end{{proof}}\n"
                )
        content = "\n".join(doc_parts)
        theorems = extract_theorem_blocks(content)
        proofs = extract_proof_blocks(content)
        blueprints = build_proof_blueprints(theorems, proofs)
        assert len(blueprints) == len(theorems)

    @given(st.integers(min_value=1, max_value=4))
    @settings(max_examples=20)
    def test_matched_blueprints_never_exceed_proofs(self, n: int):
        """Blueprints with a matched proof can't exceed total proof count."""
        doc_parts = []
        for i in range(n):
            doc_parts.append(f"\\begin{{theorem}}\nT{i}.\n\\end{{theorem}}\n")
            doc_parts.append(f"\\begin{{proof}}\nP{i}.\n\\end{{proof}}\n")
        # One extra theorem with no proof.
        doc_parts.append("\\begin{theorem}\nExtra.\n\\end{theorem}\n")
        content = "\n".join(doc_parts)
        theorems = extract_theorem_blocks(content)
        proofs = extract_proof_blocks(content)
        blueprints = build_proof_blueprints(theorems, proofs)
        matched = sum(1 for bp in blueprints if bp.proof is not None)
        assert matched <= len(proofs)


class TestPropertyBasedParseExpr:
    """parse_expr should handle arbitrary integer polynomials without crashing."""

    @given(
        st.integers(min_value=-50, max_value=50).filter(lambda n: n != 0),
        st.integers(min_value=-50, max_value=50).filter(lambda n: n != 0),
        st.integers(min_value=-50, max_value=50),
    )
    @settings(max_examples=50)
    def test_polynomial_roundtrip(self, a: int, b: int, c: int):
        x = sp.Symbol("x", real=True)
        # Use explicit multiplication to avoid implicit-mult parse errors.
        latex = f"{a}*x^2 + {b}*x + {c}"
        result = parse_expr(latex, variable_names=["x"])
        assert isinstance(result, sp.Basic)
        # Evaluate at x=0 to verify constant term.
        val_at_0 = result.subs(x, 0)
        assert val_at_0 == c

    @given(
        st.integers(min_value=1, max_value=20),
        st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=30)
    def test_frac_produces_rational(self, num: int, denom: int):
        latex = rf"\frac{{{num}}}{{{denom}}}"
        result = parse_expr(latex, variable_names=[])
        expected = sp.Rational(num, denom)
        assert sp.simplify(result - expected) == 0


# ═══════════════════════════════════════════════════════════════════════
# Edge cases & robustness
# ═══════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_empty_document(self):
        assert extract_functions("") == []
        assert extract_theorem_blocks("") == []
        assert extract_proof_blocks("") == []
        assert extract_claims("", []) == []

    def test_only_preamble_no_body(self):
        content = textwrap.dedent(r"""
            \documentclass{article}
            \usepackage{amsmath}
            \usepackage{amsthm}
        """)
        assert extract_theorem_blocks(content) == []
        assert extract_proof_blocks(content) == []

    def test_theorem_with_display_math_inside(self):
        content = textwrap.dedent(r"""
            \begin{theorem}
            For all $n \geq 1$ we have
            \[
            \sum_{k=1}^{n} k = \frac{n(n+1)}{2}.
            \]
            \end{theorem}
        """)
        blocks = extract_theorem_blocks(content)
        assert len(blocks) == 1
        assert r"\sum" in blocks[0].statement

    def test_proof_with_multiple_display_blocks(self):
        content = textwrap.dedent(r"""
            \begin{proof}
            First we note
            \[
            a = b + c
            \]
            and then
            \[
            b = d - e
            \]
            which gives us $a = d - e + c$.
            \end{proof}
        """)
        proofs = extract_proof_blocks(content)
        assert len(proofs) == 1
        steps = split_proof_steps(proofs[0].body)
        # Should extract the two display math blocks as steps.
        math_steps = [s for s in steps if "=" in s]
        assert len(math_steps) >= 2

    def test_proof_with_itemize(self):
        content = textwrap.dedent(r"""
            \begin{proof}
            We consider two cases.
            Case 1: $x > 0$. Then $x^2 > 0$.
            Case 2: $x < 0$. Then $x^2 > 0$ also.
            Hence $x^2 > 0$ for all $x \neq 0$.
            \end{proof}
        """)
        proofs = extract_proof_blocks(content)
        steps = split_proof_steps(proofs[0].body)
        assert len(steps) >= 3
        # The "Hence" step should be merged with the following content.
        inference_steps = [s for s in steps if "Hence" in s]
        assert len(inference_steps) >= 1

    def test_adjacent_inline_math_segments(self):
        content = "We have $a = 1$, $b = 2$, and $c = 3$."
        segments = extract_math_segments(content)
        assert len(segments) == 3

    def test_function_def_in_display_math(self):
        content = "Define\n\\[\ng(x) = \\sqrt{x} + 1\n\\]\nfor $x \\geq 0$."
        functions = extract_functions(content)
        assert len(functions) == 1
        assert functions[0].name == "g"

    def test_multiline_theorem_body(self):
        content = textwrap.dedent(r"""
            \begin{theorem}[Fundamental Theorem of Calculus]
            Let $f$ be continuous on $[a, b]$ and let $F$ be an antiderivative of $f$.
            Then
            \[
            \int_a^b f(x) \, dx = F(b) - F(a).
            \]
            \end{theorem}
        """)
        blocks = extract_theorem_blocks(content)
        assert len(blocks) == 1
        assert blocks[0].title == "Fundamental Theorem of Calculus"
        assert "antiderivative" in blocks[0].statement

    def test_line_number_across_large_gap(self):
        lines = [""] * 99 + ["$x$"]
        content = "\n".join(lines)
        segments = extract_math_segments(content)
        assert len(segments) == 1
        assert segments[0]["line_number"] == 100

    def test_strip_group_nested_not_stripped(self):
        # Only outermost pair stripped.
        assert strip_group("{a{b}c}") == "a{b}c"


# ═══════════════════════════════════════════════════════════════════════
# Realistic paper-length documents
# ═══════════════════════════════════════════════════════════════════════


class TestRealisticDocuments:
    """Full-document tests modeled after common academic paper structures."""

    REAL_ANALYSIS_EXCERPT = textwrap.dedent(r"""
        \documentclass{article}
        \usepackage{amsmath,amsthm}
        \newtheorem{theorem}{Theorem}
        \newtheorem{lemma}[theorem]{Lemma}
        \newtheorem{corollary}[theorem]{Corollary}
        \begin{document}

        \section{Preliminary Results}

        Define $f(x) = x^2$ on $[0, \infty)$.

        \begin{lemma}
        The function $f$ is continuous on $[0, \infty)$.
        \end{lemma}
        \begin{proof}
        Since $f$ is a polynomial, it is continuous everywhere.
        \end{proof}

        \begin{theorem}[Integration of Monomials]
        For any integer $n \geq 0$,
        \[
        \int_0^1 x^n \, dx = \frac{1}{n+1}.
        \]
        \end{theorem}
        \begin{proof}
        The antiderivative of $x^n$ is $\frac{x^{n+1}}{n+1}$.
        Therefore
        \[
        \int_0^1 x^n \, dx = \frac{1^{n+1}}{n+1} - \frac{0^{n+1}}{n+1} = \frac{1}{n+1}.
        \]
        \end{proof}

        \begin{corollary}
        We have
        \[
        \int_0^1 x^2 \, dx = \frac{1}{3}.
        \]
        \end{corollary}
        \begin{proof}
        This is the case $n = 2$ of the above theorem.
        \end{proof}

        \end{document}
    """)

    def test_real_analysis_structure(self):
        content = self.REAL_ANALYSIS_EXCERPT
        theorems = extract_theorem_blocks(content)
        proofs = extract_proof_blocks(content)
        assert len(theorems) == 3  # lemma, theorem, corollary
        assert len(proofs) == 3
        blueprints = build_proof_blueprints(theorems, proofs)
        assert len(blueprints) == 3
        assert all(bp.proof is not None for bp in blueprints)

    def test_real_analysis_claims(self):
        content = self.REAL_ANALYSIS_EXCERPT
        functions = extract_functions(content)
        assert any(f.name == "f" for f in functions)
        claims = extract_claims(content, functions)
        integral_claims = [c for c in claims if c.kind == "integral_equality"]
        # There are multiple \int display blocks.
        assert len(integral_claims) >= 1

    def test_real_analysis_obligation_types(self):
        content = self.REAL_ANALYSIS_EXCERPT
        theorems = extract_theorem_blocks(content)
        proofs = extract_proof_blocks(content)
        blueprints = build_proof_blueprints(theorems, proofs)
        # The theorem's proof has "Therefore" → inference.
        theorem_bp = [bp for bp in blueprints if bp.theorem.env_name == "theorem"][0]
        types = {o.obligation_type for o in theorem_bp.obligations}
        assert "inference" in types

    ABSTRACT_ALGEBRA_PROOF = textwrap.dedent(r"""
        \documentclass{article}
        \usepackage{amsmath,amsthm}
        \newtheorem{proposition}{Proposition}
        \begin{document}

        \begin{proposition}
        Let $G$ be a group. If $g^2 = e$ for every $g \in G$, then $G$ is abelian.
        \end{proposition}
        \begin{proof}
        Let $a, b \in G$. By definition of the group operation,
        \[
        (ab)^2 = e.
        \]
        Hence $abab = e$. Multiplying on the left by $a$ and on the right by $b$ gives $ba = ab$.
        Thus $G$ is abelian.
        \end{proof}

        \end{document}
    """)

    def test_abstract_algebra_structure(self):
        content = self.ABSTRACT_ALGEBRA_PROOF
        theorems = extract_theorem_blocks(content)
        proofs = extract_proof_blocks(content)
        assert len(theorems) == 1
        assert theorems[0].env_name == "proposition"
        assert len(proofs) == 1
        blueprints = build_proof_blueprints(theorems, proofs)
        bp = blueprints[0]
        assert bp.proof is not None
        assert len(bp.obligations) >= 3
        types = [o.obligation_type for o in bp.obligations]
        assert "inference" in types  # "Hence" and "Thus"

    STACKED_THEOREMS = textwrap.dedent(r"""
        \begin{theorem}
        First.
        \end{theorem}

        \begin{theorem}
        Second.
        \end{theorem}

        \begin{theorem}
        Third.
        \end{theorem}

        \begin{proof}
        This proves the third theorem only.
        \end{proof}
    """)

    def test_stacked_theorems_pairing(self):
        """Only the third theorem should be paired with the proof."""
        content = self.STACKED_THEOREMS
        theorems = extract_theorem_blocks(content)
        proofs = extract_proof_blocks(content)
        blueprints = build_proof_blueprints(theorems, proofs)
        assert len(blueprints) == 3
        assert blueprints[0].proof is None
        assert blueprints[1].proof is None
        assert blueprints[2].proof is not None

    MIXED_ENVS = textwrap.dedent(r"""
        \begin{lemma}
        A useful lemma.
        \end{lemma}
        \begin{proof}
        Immediate from the definitions.
        \end{proof}

        \begin{proposition}
        A proposition.
        \end{proposition}
        \begin{proof}
        By the lemma above.
        \end{proof}

        \begin{corollary}
        A corollary.
        \end{corollary}
    """)

    def test_mixed_environments(self):
        content = self.MIXED_ENVS
        theorems = extract_theorem_blocks(content)
        proofs = extract_proof_blocks(content)
        assert len(theorems) == 3
        assert len(proofs) == 2
        blueprints = build_proof_blueprints(theorems, proofs)
        assert blueprints[0].proof is not None  # lemma → proof
        assert blueprints[1].proof is not None  # proposition → proof
        assert blueprints[2].proof is None  # corollary → no proof


# ═══════════════════════════════════════════════════════════════════════
# Proof-step splitting: diverse patterns
# ═══════════════════════════════════════════════════════════════════════


class TestSplitProofStepsAdvanced:
    def test_hence_merged(self):
        text = "We know f is continuous. Hence f is integrable."
        steps = split_proof_steps(text)
        merged = [s for s in steps if "Hence" in s]
        assert len(merged) == 1
        assert "integrable" in merged[0]

    def test_thus_at_end(self):
        text = "We verified each case. Thus the theorem holds."
        steps = split_proof_steps(text)
        merged = [s for s in steps if "Thus" in s]
        assert len(merged) == 1

    def test_it_follows_merged(self):
        text = "Both sides equal 5. It follows that a = b."
        steps = split_proof_steps(text)
        merged = [s for s in steps if "It follows" in s]
        assert len(merged) == 1
        assert "a = b" in merged[0]

    def test_multiple_display_math(self):
        text = (
            "We have\n"
            r"\[ a = b \]" "\n"
            "and\n"
            r"\[ c = d \]" "\n"
            "which completes the proof."
        )
        steps = split_proof_steps(text)
        math_steps = [s for s in steps if "=" in s and len(s) < 20]
        assert len(math_steps) >= 2

    def test_numbered_steps_preserved(self):
        text = (
            "Step 1: Define f.\n"
            "Step 2: Show f is continuous.\n"
            "Step 3: Apply the intermediate value theorem."
        )
        steps = split_proof_steps(text)
        assert len(steps) == 3
        assert all("Step" in s for s in steps)

    def test_question_mark_splits(self):
        text = "Is x > 0? Yes, because x is positive."
        steps = split_proof_steps(text)
        assert len(steps) >= 2

    def test_whitespace_only(self):
        assert split_proof_steps("   \n\n   ") == []

    def test_single_word(self):
        # "QED" alone is meaningful.
        steps = split_proof_steps("QED")
        assert len(steps) == 1


# ═══════════════════════════════════════════════════════════════════════
# extract_math_segments edge cases
# ═══════════════════════════════════════════════════════════════════════


class TestExtractMathSegmentsAdvanced:
    def test_empty_inline_math(self):
        # $$ is display math, not empty inline. Plain $ $ should not match.
        segments = extract_math_segments("text $$ text")
        # The regex requires non-empty body for inline, so $$ won't match inline.
        # It will match display math with empty body only via \[...\].
        assert all(s["text"] != "" for s in segments)

    def test_nested_dollar_signs_not_confused(self):
        content = "We have $x = 1$ and also $y = 2$."
        segments = extract_math_segments(content)
        assert len(segments) == 2
        texts = [s["text"] for s in segments]
        assert "x = 1" in texts
        assert "y = 2" in texts

    def test_display_math_multiline(self):
        content = "Text\n\\[\na + b\n= c + d\n\\]\nmore text"
        segments = extract_math_segments(content)
        assert len(segments) == 1
        assert "a + b" in segments[0]["text"]
        assert "c + d" in segments[0]["text"]

    def test_mixed_inline_and_display(self):
        content = "Inline $x$ and display\n\\[\ny^2\n\\]\nthen $z$."
        segments = extract_math_segments(content)
        assert len(segments) == 3
        # Should be sorted by line number.
        line_nums = [int(s["line_number"]) for s in segments]
        assert line_nums == sorted(line_nums)


# ═══════════════════════════════════════════════════════════════════════
# Average value claim variants
# ═══════════════════════════════════════════════════════════════════════


class TestAverageValueClaimVariants:
    @pytest.mark.parametrize(
        "sentence",
        [
            "The average value of $x^2$ on $[0,1]$ is $\\frac{1}{3}$.",
            "The average value of $x^3$ on $[0,2]$ is $2$.",
            "The average value of $f(x)$ on $[1,4]$ is also $7$.",
        ],
    )
    def test_matched(self, sentence: str):
        claims = extract_claims(sentence, [])
        avg_claims = [c for c in claims if c.kind == "average_value"]
        assert len(avg_claims) == 1

    @pytest.mark.parametrize(
        "sentence",
        [
            "The maximum value of $f$ on $[0,1]$ is $5$.",
            "The minimum of $g$ on $[0,1]$ is $0$.",
            "Some random sentence without average.",
        ],
    )
    def test_not_matched(self, sentence: str):
        claims = extract_claims(sentence, [])
        avg_claims = [c for c in claims if c.kind == "average_value"]
        assert len(avg_claims) == 0


# ═══════════════════════════════════════════════════════════════════════
# Review fixes: extract_proof_obligations direct tests
# ═══════════════════════════════════════════════════════════════════════


class TestExtractProofObligations:
    def test_none_proof_returns_empty(self):
        from revisica.math_check.types import TheoremBlock

        theorem = TheoremBlock(
            env_name="theorem", line_number=1, title=None,
            statement="Statement.", snippet="...",
        )
        assert extract_proof_obligations(theorem, None) == []

    def test_single_step_proof(self):
        from revisica.math_check.types import ProofBlock, TheoremBlock

        theorem = TheoremBlock(
            env_name="theorem", line_number=1, title=None,
            statement="Statement.", snippet="...",
        )
        proof = ProofBlock(
            line_number=5, title=None,
            body="This is obvious.", snippet="...",
        )
        obligations = extract_proof_obligations(theorem, proof)
        assert len(obligations) >= 1
        assert obligations[0].step_index == 1
        assert obligations[0].theorem_env == "theorem"
        assert obligations[0].theorem_line_number == 1
        assert obligations[0].proof_line_number == 5

    def test_multi_step_mixed_types(self):
        from revisica.math_check.types import ProofBlock, TheoremBlock

        theorem = TheoremBlock(
            env_name="lemma", line_number=3, title=None,
            statement="A lemma.", snippet="...",
        )
        proof = ProofBlock(
            line_number=7, title=None,
            body="By definition, f is continuous. Therefore f is integrable.",
            snippet="...",
        )
        obligations = extract_proof_obligations(theorem, proof)
        assert len(obligations) >= 2
        types = {o.obligation_type for o in obligations}
        assert "definition-use" in types
        assert "inference" in types
        # Step indices are sequential starting from 1.
        indices = [o.step_index for o in obligations]
        assert indices == list(range(1, len(obligations) + 1))


# ═══════════════════════════════════════════════════════════════════════
# Review fixes: $$ display math regex
# ═══════════════════════════════════════════════════════════════════════


class TestDoubleDollarMathSegments:
    def test_double_dollar_not_confused_with_inline(self):
        content = "Define $$f(x)=x^2$$ and $g(x)=x$."
        segments = extract_math_segments(content)
        assert len(segments) == 2
        texts = [s["text"] for s in segments]
        assert "f(x)=x^2" in texts
        assert "g(x)=x" in texts

    def test_double_dollar_extracted_as_display(self):
        content = "We have $$a + b = c$$ as desired."
        segments = extract_math_segments(content)
        assert len(segments) == 1
        assert segments[0]["text"] == "a + b = c"

    def test_mixed_double_dollar_and_bracket(self):
        content = "First $$x$$ then\n\\[\ny\n\\]\nand $z$."
        segments = extract_math_segments(content)
        assert len(segments) == 3
        texts = [s["text"] for s in segments]
        assert "x" in texts
        assert "y" in texts
        assert "z" in texts


class TestNearestFunctionBeforeUnsorted:
    def test_unsorted_input_returns_closest(self):
        from revisica.math_check.types import FunctionDefinition

        f1 = FunctionDefinition(
            name="f", variable="x", expression_text="x^2",
            expression=sp.Symbol("x") ** 2, line_number=10, snippet="...",
        )
        f2 = FunctionDefinition(
            name="g", variable="x", expression_text="x^3",
            expression=sp.Symbol("x") ** 3, line_number=5, snippet="...",
        )
        # Unsorted: line 10 before line 5 in list.
        result = nearest_function_before([f1, f2], 12)
        assert result.name == "f"  # line 10 is closest, not line 5


# ═══════════════════════════════════════════════════════════════════════
# Markdown / plain-text structure extraction
# ═══════════════════════════════════════════════════════════════════════


class TestExtractTheoremBlocksMarkdown:
    """The public extract_theorem_blocks should cover Markdown papers too."""

    def test_all_caps_header_with_colon(self):
        content = textwrap.dedent("""
            Some intro paragraph.

            THEOREM 1: Suppose Assumptions 1-3 hold. Then the optimal
            intervention places weight on the top principal component.

            The rest of the paper discusses implications.
        """)
        blocks = extract_theorem_blocks(content)
        assert len(blocks) == 1
        assert blocks[0].env_name == "theorem"
        assert blocks[0].title == "1"
        assert "Assumptions" in blocks[0].statement

    def test_titlecase_with_period_and_named_title(self):
        content = textwrap.dedent("""
            Introduction.

            Theorem 2 (Main Result). For every epsilon greater than zero,
            the bound holds.

            Remark 1. This is a remark, not a theorem.
        """)
        blocks = extract_theorem_blocks(content)
        # "Theorem 2 (Main Result)." should be picked up; "Remark" is not
        # in the supported environment set.
        theorem_blocks = [b for b in blocks if b.env_name == "theorem"]
        assert len(theorem_blocks) == 1
        assert theorem_blocks[0].title == "2 — Main Result"

    def test_multiple_markdown_theorems(self):
        content = textwrap.dedent("""
            PROPOSITION 1: The first claim.

            Body of prop 1.

            LEMMA 3: The second claim.

            Body of lemma 3.

            COROLLARY 2: The third claim.
        """)
        blocks = extract_theorem_blocks(content)
        env_names = [b.env_name for b in blocks]
        assert env_names == ["proposition", "lemma", "corollary"]

    def test_bold_markdown_header(self):
        content = textwrap.dedent("""
            **Theorem 1.** For every positive real x, we have x > 0.

            End of content.
        """)
        blocks = extract_theorem_blocks(content)
        assert len(blocks) == 1
        assert blocks[0].env_name == "theorem"

    def test_running_prose_mention_not_matched(self):
        """'In Theorem 1 we proved ...' should NOT count as a theorem header."""
        content = "As discussed, Theorem 1: is referenced here in running text."
        blocks = extract_theorem_blocks(content)
        assert blocks == []

    def test_markdown_and_latex_coexist(self):
        content = textwrap.dedent(r"""
            \begin{theorem}
            First theorem in LaTeX.
            \end{theorem}

            THEOREM 2: Second theorem in markdown.

            More text.
        """)
        blocks = extract_theorem_blocks(content)
        assert len(blocks) == 2
        # Ordered by line number.
        line_numbers = [b.line_number for b in blocks]
        assert line_numbers == sorted(line_numbers)

    def test_body_stops_at_next_header(self):
        content = textwrap.dedent("""
            THEOREM 1: First statement.

            This belongs to theorem 1.

            LEMMA 2: Second statement.

            This belongs to lemma 2.
        """)
        blocks = extract_theorem_blocks(content)
        theorem_one = next(b for b in blocks if b.env_name == "theorem")
        assert "belongs to theorem 1" in theorem_one.statement
        assert "LEMMA 2" not in theorem_one.statement
        assert "belongs to lemma 2" not in theorem_one.statement

    def test_body_stops_at_proof_header(self):
        content = textwrap.dedent("""
            THEOREM 1: Suppose the assumptions hold.

            This is the theorem body.

            PROOF: We wish to solve.

            This is the proof.
        """)
        blocks = extract_theorem_blocks(content)
        assert len(blocks) == 1
        assert "PROOF" not in blocks[0].statement
        assert "wish to solve" not in blocks[0].statement


class TestExtractProofBlocksMarkdown:
    def test_proof_with_qed(self):
        content = textwrap.dedent("""
            THEOREM 1: Some statement.

            PROOF: We argue as follows. First step. Second step. Q.E.D.

            The paper continues.
        """)
        blocks = extract_proof_blocks(content)
        assert len(blocks) == 1
        assert "First step" in blocks[0].body
        assert "continues" not in blocks[0].body

    def test_proof_of_theorem_1_header(self):
        content = textwrap.dedent("""
            APPENDIX: PROOFS

            PROOF OF THEOREM 1: We wish to solve the optimization problem.
            More detailed argument here. Q.E.D.

            PROOF OF PROPOSITION 1: Part 1 shows.
            Part 2 shows. Q.E.D.
        """)
        blocks = extract_proof_blocks(content)
        assert len(blocks) == 2
        assert blocks[0].title == "Proof of THEOREM 1"
        assert blocks[1].title == "Proof of PROPOSITION 1"

    def test_markdown_proof_with_blacksquare(self):
        content = textwrap.dedent(r"""
            **Proof.** We expand and simplify. $\blacksquare$

            Next section.
        """)
        blocks = extract_proof_blocks(content)
        assert len(blocks) == 1
        assert "expand and simplify" in blocks[0].body

    def test_markdown_proof_without_qed_stops_at_next_theorem(self):
        content = textwrap.dedent("""
            Proof. We derive the result step by step.

            Step one claim. Step two claim.

            THEOREM 5: Next theorem.
        """)
        blocks = extract_proof_blocks(content)
        assert len(blocks) == 1
        assert "step by step" in blocks[0].body
        assert "THEOREM 5" not in blocks[0].body

    def test_markdown_proof_without_terminator(self):
        """Missing QED but ended by EOF should still produce a block."""
        content = "PROOF: The result follows from the two lemmas."
        blocks = extract_proof_blocks(content)
        assert len(blocks) == 1
        assert "lemmas" in blocks[0].body

    def test_blueprint_pairs_markdown_theorem_and_proof(self):
        content = textwrap.dedent("""
            THEOREM 1: First claim with body.

            PROOF OF THEOREM 1: The argument goes here. Q.E.D.

            THEOREM 2: Second claim.
        """)
        theorems = extract_theorem_blocks(content)
        proofs = extract_proof_blocks(content)
        blueprints = build_proof_blueprints(theorems, proofs)
        assert len(blueprints) == 2
        assert blueprints[0].proof is not None
        assert "argument goes here" in blueprints[0].proof.body
        assert blueprints[1].proof is None


class TestExtractFunctionsMarkdown:
    def test_type_signature_produces_entry_without_expression(self):
        content = textwrap.dedent("""
            Let f : X → Y be a continuous map.

            Body of text.
        """)
        functions = extract_functions(content)
        names = [f.name for f in functions]
        assert "f" in names
        signature_entry = next(f for f in functions if f.name == "f")
        assert signature_entry.expression is None
        assert "X → Y" in signature_entry.expression_text

    def test_type_signature_with_backslash_to(self):
        content = r"Define $g : \mathbb{R} \to \mathbb{R}$, actually written plainly: g : R \to R."
        functions = extract_functions(content)
        plain_entries = [f for f in functions if f.name == "g" and f.expression is None]
        assert len(plain_entries) == 1

    def test_plain_text_function_def_extracted(self):
        content = "Define h(x) = x + 1 outside of math delimiters."
        functions = extract_functions(content)
        assert any(f.name == "h" and f.variable == "x" for f in functions)

    def test_function_inside_math_not_duplicated(self):
        content = "We set $f(x) = x^2$ and then mention f(x) = x^2 again in prose."
        functions = extract_functions(content)
        # One from the LaTeX extractor, the markdown extractor should skip
        # the line covered by LaTeX and may still add the prose line.
        names_and_variables = [(f.name, f.variable) for f in functions]
        assert ("f", "x") in names_and_variables

    def test_noise_labels_like_proof_not_treated_as_signature(self):
        content = "Proof : we use induction → derive the result."
        functions = extract_functions(content)
        assert not any(f.name.lower() == "proof" for f in functions)
