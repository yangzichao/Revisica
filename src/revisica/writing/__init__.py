"""Writing review lane.

Decomposed by responsibility:

- ``entry``               — public ``review_writing_file`` entry point (LangGraph invocation)
- ``types``               — role constants and run/artifact dataclasses
- ``reviewer_resolution`` — provider selection and run-directory setup
- ``agent_tasks``         — agent specs and dynamic task prompts per role
- ``findings``            — parsing agent output into structured findings
- ``self_check``          — false-positive filtering pass over reviewer findings
- ``judge``               — final adjudication and fallback report
- ``artifacts``           — on-disk outputs (per-role files, final report, summary)
"""

from .entry import review_writing_file
from .types import (
    MATH_VERIFICATION_ROLES,
    WRITING_ROLES,
    WritingReviewRun,
    WritingRoleArtifact,
)

__all__ = [
    "MATH_VERIFICATION_ROLES",
    "WRITING_ROLES",
    "WritingReviewRun",
    "WritingRoleArtifact",
    "review_writing_file",
]
