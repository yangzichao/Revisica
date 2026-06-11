"""Venue profiles a writing review can target.

A venue profile steers the writing-venue reviewer agent toward the
expectations of a publication tier (e.g. econ top-5 journals). The
profile string is passed through to the agent task; the supported set is
validated at the CLI boundary.
"""

from __future__ import annotations

SUPPORTED_VENUE_PROFILES = (
    "general-academic",
    "econ-general-top",
    "econ-top5",
    "econ-theory",
    "econ-empirical",
    "econ-applied",
)
