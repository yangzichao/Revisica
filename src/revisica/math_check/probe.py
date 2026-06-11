"""Numeric counterexample probing for claims symbolic analysis can't settle.

The deterministic lane prefers exact symbolic answers, but two situations
need a numeric fallback:

- **Bounded inequality claims** ("f(x) <= g(x) for all x in [a,b]").
  We sample the interval on a rational grid and confirm any violation by
  exact substitution, so a reported counterexample is a machine-checkable
  witness, never floating-point noise. When sampling finds nothing we try
  to *prove* the inequality via the symbolic minimum of the gap; if that
  is inconclusive the claim is left alone (no noise).
- **Definite integrals SymPy can't evaluate in closed form.** Comparing
  a numeric quadrature value against the stated right-hand side avoids
  refuting a claim just because ``integrate`` returned unevaluated.
"""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

# Grid density for interval sampling. Endpoints are always included; a
# denominator this size also lands on common critical points (halves,
# thirds, quarters...).
SAMPLE_COUNT = 60

# Relative tolerance for the fast numeric pre-filter; candidates are
# confirmed exactly before being reported.
NUMERIC_TOLERANCE = 1e-9

RELATION_OPERATORS = ("<=", ">=", "<", ">")


@dataclass
class CounterexampleWitness:
    """An exact point where a claimed inequality fails."""

    point: sp.Expr  # exact (rational or symbolic) value of the variable
    lhs_value: sp.Expr
    rhs_value: sp.Expr

    def describe(self, variable: sp.Symbol, relation: str) -> str:
        return (
            f"At {variable} = {sp.nsimplify(self.point)}, the left side is "
            f"{self.lhs_value} and the right side is {self.rhs_value}, so "
            f"`{relation}` fails."
        )


def find_inequality_counterexample(
    lhs: sp.Expr,
    rhs: sp.Expr,
    relation: str,
    variable: sp.Symbol,
    lower: sp.Expr,
    upper: sp.Expr,
) -> CounterexampleWitness | None:
    """Search [lower, upper] for an exact witness violating ``lhs rel rhs``.

    Sampling order: interval endpoints first (where bound claims most
    often fail), then a uniform rational grid. Every numeric hit is
    re-checked by exact substitution before being reported.
    """
    if relation not in RELATION_OPERATORS:
        raise ValueError(f"Unsupported relation: {relation!r}")
    gap = sp.simplify(rhs - lhs)  # claim holds iff gap (rel-adjusted) >= 0
    for point in _sample_points(lower, upper):
        violated = _violates_exactly(gap, relation, variable, point)
        if violated:
            lhs_value = sp.simplify(lhs.subs(variable, point))
            rhs_value = sp.simplify(rhs.subs(variable, point))
            return CounterexampleWitness(
                point=point, lhs_value=lhs_value, rhs_value=rhs_value
            )
    return None


def prove_inequality_on_interval(
    lhs: sp.Expr,
    rhs: sp.Expr,
    relation: str,
    variable: sp.Symbol,
    lower: sp.Expr,
    upper: sp.Expr,
) -> bool | None:
    """Try to prove ``lhs rel rhs`` on [lower, upper] symbolically.

    Returns True when proven, None when inconclusive. (Refutation is the
    job of :func:`find_inequality_counterexample` — a failed proof is not
    evidence of falsity.)
    """
    gap = _oriented_gap(lhs, rhs, relation)
    try:
        extremum = sp.minimum(gap, variable, sp.Interval(lower, upper))
    except Exception:
        return None
    strict = relation in ("<", ">")
    try:
        if strict and (extremum > 0) is sp.true:
            return True
        if not strict and (extremum >= 0) is sp.true:
            return True
    except TypeError:
        return None
    return None


def numeric_integral_matches(
    integrand: sp.Expr,
    variable: sp.Symbol,
    lower: sp.Expr,
    upper: sp.Expr,
    stated: sp.Expr,
    relative_tolerance: float = 1e-6,
) -> bool | None:
    """Compare a definite integral numerically against a stated value.

    Returns True/False on a clear numeric verdict, None when quadrature
    or the stated value fails to evaluate to a real number.
    """
    try:
        computed = sp.Integral(integrand, (variable, lower, upper)).evalf()
        stated_value = sp.sympify(stated).evalf()
    except Exception:
        return None
    if not (computed.is_real and stated_value.is_real):
        return None
    scale = max(abs(float(computed)), abs(float(stated_value)), 1.0)
    return abs(float(computed) - float(stated_value)) <= relative_tolerance * scale


# ── internals ───────────────────────────────────────────────────────


def _oriented_gap(lhs: sp.Expr, rhs: sp.Expr, relation: str) -> sp.Expr:
    """Expression that must be >= 0 (or > 0 for strict) for the claim."""
    if relation in ("<=", "<"):
        return sp.simplify(rhs - lhs)
    return sp.simplify(lhs - rhs)


def _sample_points(lower: sp.Expr, upper: sp.Expr) -> list[sp.Expr]:
    span = sp.nsimplify(upper - lower)
    points: list[sp.Expr] = [sp.nsimplify(lower), sp.nsimplify(upper)]
    for index in range(1, SAMPLE_COUNT):
        points.append(sp.nsimplify(lower) + span * sp.Rational(index, SAMPLE_COUNT))
    return points


def _violates_exactly(
    gap: sp.Expr,
    relation: str,
    variable: sp.Symbol,
    point: sp.Expr,
) -> bool:
    """Numeric pre-filter, then exact confirmation at the sample point."""
    oriented = gap if relation in ("<=", "<") else -gap
    try:
        approx = oriented.subs(variable, point).evalf()
    except Exception:
        return False
    if not approx.is_real:
        return False
    if float(approx) > NUMERIC_TOLERANCE:
        return False
    # Numerically suspicious — confirm exactly so float noise never
    # produces a counterexample, and exact equality refutes only strict
    # relations (it satisfies <=/>=).
    exact = sp.simplify(oriented.subs(variable, point))
    if relation in ("<", ">"):
        return bool(exact.is_negative or exact == 0)
    return bool(exact.is_negative)
