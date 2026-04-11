"""Task-model auto-routing for Revisica.

When a ProviderModelSpec has no explicit model, this module selects an
appropriate model based on the task category. The defaults should stay
compatible with the provider account actually running the agent, not an
idealized model menu.

The defaults are conservative — they only kick in when no model is
explicitly specified.  Users can always override via --reviewer-a, etc.
"""
from __future__ import annotations

from .core_types import ProviderModelSpec


# ── task categories ──────────────────────────────────────────────────

TASK_MATH_REASONING = "math-reasoning"
TASK_MATH_SELF_CHECK = "math-self-check"
TASK_MATH_ADJUDICATION = "math-adjudication"
TASK_WRITING_BASIC = "writing-basic"
TASK_WRITING_STRUCTURE = "writing-structure"
TASK_WRITING_VENUE = "writing-venue"
TASK_WRITING_SELF_CHECK = "writing-self-check"
TASK_WRITING_JUDGE = "writing-judge"
TASK_MATH_CLAIM_VERIFY = "math-claim-verify"
TASK_NOTATION_TRACK = "notation-track"
TASK_FORMULA_CROSS_CHECK = "formula-cross-check"
TASK_SECTION_CROSS_CHECK = "section-cross-check"


# ── role → task category mapping ─────────────────────────────────────

ROLE_TASK_MAP: dict[str, str] = {
    "proof-reviewer": TASK_MATH_REASONING,
    "self-checker": TASK_MATH_SELF_CHECK,
    "adjudicator": TASK_MATH_ADJUDICATION,
    "basic": TASK_WRITING_BASIC,
    "structure": TASK_WRITING_STRUCTURE,
    "venue": TASK_WRITING_VENUE,
    "writing-self-checker": TASK_WRITING_SELF_CHECK,
    "judge": TASK_WRITING_JUDGE,
    "math-claim-verifier": TASK_MATH_CLAIM_VERIFY,
    "notation-tracker": TASK_NOTATION_TRACK,
    "formula-cross-checker": TASK_FORMULA_CROSS_CHECK,
    "section-cross-checker": TASK_SECTION_CROSS_CHECK,
}


# ── default model routes per provider ────────────────────────────────
#
# For Codex, route to models that are both strong and broadly supported by
# the current account setup. We intentionally avoid older unsupported routes
# like `o3` and `gpt-4.1`, which caused real benchmark runs to fail.
#
# These are suggestions. Users can still override them explicitly.

_DEFAULT_ROUTES: dict[str, dict[str, str]] = {
    "codex": {
        # Use one strong compatible default until we have account-aware routing.
        TASK_MATH_REASONING: "gpt-5",
        TASK_MATH_SELF_CHECK: "gpt-5",
        TASK_MATH_ADJUDICATION: "gpt-5",
        TASK_MATH_CLAIM_VERIFY: "gpt-5",
        TASK_WRITING_BASIC: "gpt-5",
        TASK_WRITING_STRUCTURE: "gpt-5",
        TASK_WRITING_VENUE: "gpt-5",
        TASK_WRITING_SELF_CHECK: "gpt-5",
        TASK_WRITING_JUDGE: "gpt-5",
        TASK_NOTATION_TRACK: "gpt-5",
        TASK_FORMULA_CROSS_CHECK: "gpt-5",
        TASK_SECTION_CROSS_CHECK: "gpt-5",
    },
    "claude": {
        # Reasoning tasks → opus (strongest reasoning)
        TASK_MATH_REASONING: "opus",
        TASK_MATH_SELF_CHECK: "opus",
        TASK_MATH_ADJUDICATION: "opus",
        TASK_MATH_CLAIM_VERIFY: "opus",
        # Writing tasks → sonnet (fast, strong at language)
        TASK_WRITING_BASIC: "sonnet",
        TASK_WRITING_STRUCTURE: "sonnet",
        TASK_WRITING_VENUE: "sonnet",
        TASK_WRITING_SELF_CHECK: "opus",
        TASK_WRITING_JUDGE: "sonnet",
        # Cross-checks
        TASK_NOTATION_TRACK: "opus",
        TASK_FORMULA_CROSS_CHECK: "opus",
        TASK_SECTION_CROSS_CHECK: "sonnet",
    },
}


def resolve_model_for_task(
    spec: ProviderModelSpec,
    task_type: str,
) -> ProviderModelSpec:
    """Return a spec with an auto-selected model if none was explicitly set.

    If the spec already has a model, it is returned unchanged.
    """
    if spec.model is not None:
        return spec
    routes = _DEFAULT_ROUTES.get(spec.provider, {})
    model = routes.get(task_type)
    if model is not None:
        return ProviderModelSpec(provider=spec.provider, model=model)
    return spec


def resolve_model_for_role(
    spec: ProviderModelSpec,
    role: str,
) -> ProviderModelSpec:
    """Convenience wrapper — looks up the task type from a role name."""
    task_type = ROLE_TASK_MAP.get(role)
    if task_type is None:
        return spec
    return resolve_model_for_task(spec, task_type)
