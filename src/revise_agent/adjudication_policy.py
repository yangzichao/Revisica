from __future__ import annotations

from typing import Callable, Iterable, Sequence, TypeVar


T = TypeVar("T")


def pick_preferred_provider(
    providers: Iterable[str],
    preferred: str = "codex",
) -> str:
    ordered = list(dict.fromkeys(providers))
    if not ordered:
        raise ValueError("at least one provider is required")
    if preferred in ordered:
        return preferred
    return ordered[0]


def pick_preferred_item(
    items: Sequence[T],
    provider_getter: Callable[[T], str],
    preferred: str = "codex",
) -> T:
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
