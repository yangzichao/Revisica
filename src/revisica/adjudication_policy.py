"""Provider preference for adjudication and judging roles.

When several providers produced results and no explicit judge/adjudicator
spec was given, Revisica must pick one provider to do the final merge.
The default preference is ``claude``: on ProcessBench (math proof error
detection) Claude scored 58% vs Codex 27%, and adjudication is dominated
by exactly that kind of careful step-checking.

Override with the ``REVISICA_PREFERRED_ADJUDICATOR`` environment variable
(e.g. ``REVISICA_PREFERRED_ADJUDICATOR=codex``), or pass ``preferred=``
explicitly at the call site.
"""

from __future__ import annotations

import os
from typing import Callable, Iterable, Sequence, TypeVar


T = TypeVar("T")

DEFAULT_PREFERRED_PROVIDER = "claude"
PREFERRED_PROVIDER_ENV_VAR = "REVISICA_PREFERRED_ADJUDICATOR"


def preferred_adjudication_provider() -> str:
    """The provider to prefer for adjudication, honoring the env override."""
    return os.environ.get(PREFERRED_PROVIDER_ENV_VAR, "").strip() or DEFAULT_PREFERRED_PROVIDER


def pick_preferred_provider(
    providers: Iterable[str],
    preferred: str | None = None,
) -> str:
    """Pick ``preferred`` from ``providers`` if present, else the first one."""
    if preferred is None:
        preferred = preferred_adjudication_provider()
    ordered = list(dict.fromkeys(providers))
    if not ordered:
        raise ValueError("at least one provider is required")
    if preferred in ordered:
        return preferred
    return ordered[0]


def pick_preferred_item(
    items: Sequence[T],
    provider_getter: Callable[[T], str],
    preferred: str | None = None,
) -> T:
    """Pick the first item whose provider matches the preferred provider."""
    if not items:
        raise ValueError("at least one item is required")
    preferred_provider = pick_preferred_provider(
        (provider_getter(item) for item in items),
        preferred=preferred,
    )
    for item in items:
        if provider_getter(item) == preferred_provider:
            return item
    return items[0]
