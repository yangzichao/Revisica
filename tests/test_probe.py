"""Tests for numeric counterexample probing (math_check/probe.py)."""

from __future__ import annotations

import sympy as sp

from revisica.math_check.deterministic import analyze_claims
from revisica.math_check.extraction.claims import extract_math_claims
from revisica.math_check.probe import (
    find_inequality_counterexample,
    numeric_integral_matches,
    prove_inequality_on_interval,
)

X = sp.Symbol("x", real=True)


class TestFindInequalityCounterexample:
    def test_finds_witness_for_false_bound(self):
        # x^3 <= x fails on (1, 2]; the endpoint x=2 is sampled first.
        witness = find_inequality_counterexample(
            X**3, X, "<=", X, sp.Integer(0), sp.Integer(2)
        )
        assert witness is not None
        assert witness.lhs_value > witness.rhs_value
        assert "fails" in witness.describe(X, "<=")

    def test_true_inequality_has_no_witness(self):
        witness = find_inequality_counterexample(
            X**2 + 1, 2 * X, ">=", X, sp.Integer(-3), sp.Integer(3)
        )
        assert witness is None

    def test_exact_equality_refutes_strict_relation(self):
        # x^2 - 1 > 0 fails exactly at x = 1 — a float-only check would
        # miss it or report noise; the witness must be the exact point.
        witness = find_inequality_counterexample(
            X**2 - 1, sp.Integer(0), ">", X, sp.Integer(1), sp.Integer(4)
        )
        assert witness is not None
        assert witness.point == 1
        assert witness.lhs_value == 0

    def test_equality_does_not_refute_non_strict_relation(self):
        # (x-1)^2 >= 0 touches zero at x=1; that satisfies >=.
        witness = find_inequality_counterexample(
            (X - 1) ** 2, sp.Integer(0), ">=", X, sp.Integer(0), sp.Integer(2)
        )
        assert witness is None


class TestProveInequalityOnInterval:
    def test_proves_amgm_style_bound(self):
        assert prove_inequality_on_interval(
            X**2 + 1, 2 * X, ">=", X, sp.Integer(-3), sp.Integer(3)
        )

    def test_strict_bound_with_positive_gap(self):
        assert prove_inequality_on_interval(
            1 / (1 + X**2), sp.Integer(0), ">", X, sp.Integer(-5), sp.Integer(5)
        )

    def test_inconclusive_returns_none(self):
        # A second free symbol makes the extremum computation fail.
        y = sp.Symbol("y", real=True)
        assert (
            prove_inequality_on_interval(
                X + y, sp.Integer(0), ">=", X, sp.Integer(0), sp.Integer(1)
            )
            is None
        )


class TestNumericIntegralMatches:
    def test_matches_correct_value(self):
        integrand = sp.exp(sp.sin(X))  # no elementary antiderivative
        stated = sp.Integral(integrand, (X, 0, 1)).evalf()
        assert numeric_integral_matches(integrand, X, sp.Integer(0), sp.Integer(1), stated)

    def test_rejects_wrong_value(self):
        integrand = sp.exp(sp.sin(X))
        stated = sp.Integral(integrand, (X, 0, 1)).evalf() * 2
        result = numeric_integral_matches(
            integrand, X, sp.Integer(0), sp.Integer(1), stated
        )
        assert result is False


class TestBoundedInequalityEndToEnd:
    DOC = r"""
We claim that
\[
x^3 \le x \quad \text{for all } x \in [0, 2].
\]
Also, $x^2 + 1 \ge 2x$ for all $x \in [-3, 3]$.
An unquantified bound like $x \le x^2$ appears here without an interval.
"""

    def test_extraction_requires_explicit_interval(self):
        claims = extract_math_claims(self.DOC, [])
        inequalities = [c for c in claims if c.kind == "bounded_inequality"]
        assert len(inequalities) == 2
        assert inequalities[0].details["relation"] == "<="
        assert inequalities[1].details["relation"] == ">="

    def test_analysis_refutes_and_verifies(self):
        claims = extract_math_claims(self.DOC, [])
        issues = analyze_claims(claims, [])
        by_status = {issue.status: issue for issue in issues}
        refuted = by_status["machine-refuted"]
        assert refuted.title == "Inequality fails on the stated interval"
        assert "left side is" in refuted.evidence
        verified = by_status["machine-verified"]
        assert verified.title == "Inequality verified on the stated interval"
