"""Parser adapter layer for the ingestion benchmark.

Each adapter exposes a uniform surface so the runner can treat every
parser — tex-basic, Pandoc, MinerU (per-backend), Mathpix — as a single
unit. MinerU's three backends are registered as distinct adapters so the
leaderboard ranks them separately.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal

# Intentional lazy imports inside helpers: parser modules may fail to
# import when their optional deps (pypandoc, mineru, mathpix creds) are
# missing. The adapter layer reports those as ``unavailable``, not errors.


InputFormat = Literal["tex", "pdf"]


# ── adapter type ───────────────────────────────────────────────────────


@dataclass
class ParserAdapter:
    """Uniform handle on one parser configuration.

    Attributes:
        key: Stable identifier used on the leaderboard (e.g. ``"pandoc"``,
             ``"mineru:vlm"``).
        family: Human-readable grouping (e.g. ``"mineru"``), used by
             :func:`expand_parser_selection` to resolve ``mineru`` into all
             three backends.
        requires_format: Which corpus input this parser consumes.
        parse: Callable that takes the input path and returns raw Markdown.
        availability_check: Callable returning ``(ok, reason)``. ``reason``
             is a short human-readable string when ``ok`` is False,
             shown in the leaderboard in place of metrics.
    """

    key: str
    family: str
    requires_format: InputFormat
    parse: Callable[[Path], str]
    availability_check: Callable[[], tuple[bool, str | None]] = field(
        default_factory=lambda: lambda: (True, None)
    )

    def availability(self) -> tuple[bool, str | None]:
        return self.availability_check()


# ── adapter factories ──────────────────────────────────────────────────


def _pandoc_adapter() -> ParserAdapter:
    def check() -> tuple[bool, str | None]:
        try:
            from revisica.ingestion.pandoc_parser import PandocParser
        except ImportError as error:
            return False, f"import failed: {error}"
        if not PandocParser.is_available():
            return False, "pandoc binary not on PATH"
        return True, None

    def parse(path: Path) -> str:
        from revisica.ingestion.pandoc_parser import PandocParser
        return PandocParser().parse(path)

    return ParserAdapter(
        key="pandoc",
        family="pandoc",
        requires_format="tex",
        parse=parse,
        availability_check=check,
    )


def _tex_basic_adapter() -> ParserAdapter:
    def check() -> tuple[bool, str | None]:
        try:
            from revisica.ingestion.tex_parser import TexParser  # noqa: F401
        except ImportError as error:
            return False, f"import failed: {error}"
        return True, None

    def parse(path: Path) -> str:
        from revisica.ingestion.tex_parser import TexParser
        return TexParser().parse(path)

    return ParserAdapter(
        key="tex-basic",
        family="tex-basic",
        requires_format="tex",
        parse=parse,
        availability_check=check,
    )


def _mineru_adapter(backend: str, timeout_seconds: int = 900) -> ParserAdapter:
    """Build a MinerU adapter bound to a single backend.

    Checks for both the ``mineru`` CLI and the required Hugging Face
    models so a missing VLM download surfaces as a skip reason rather
    than a mid-run failure.
    """
    required_model_types = _required_model_types_for_backend(backend)

    def check() -> tuple[bool, str | None]:
        try:
            from revisica.ingestion.mineru_parser import MineruParser
        except ImportError as error:
            return False, f"import failed: {error}"
        if not MineruParser.is_available():
            return False, "mineru CLI not on PATH"
        try:
            from revisica.ingestion.mineru_models import get_model_status
        except ImportError as error:
            return False, f"mineru_models import failed: {error}"
        missing: list[str] = []
        for model_type in required_model_types:
            status = get_model_status(model_type)
            if not status.get("installed"):
                missing.append(model_type)
        if missing:
            return False, f"missing model(s): {', '.join(missing)}"
        return True, None

    def parse(path: Path) -> str:
        from revisica.ingestion.mineru_parser import MineruParser
        return MineruParser(backend=backend, timeout_seconds=timeout_seconds).parse(path)

    return ParserAdapter(
        key=f"mineru:{backend}",
        family="mineru",
        requires_format="pdf",
        parse=parse,
        availability_check=check,
    )


def _required_model_types_for_backend(backend: str) -> list[str]:
    if backend == "pipeline":
        return ["pipeline"]
    if backend == "vlm":
        return ["vlm"]
    if backend in ("hybrid", "auto"):
        # hybrid-auto-engine needs both; ``auto`` maps to the same
        # default, so require both here too.
        return ["pipeline", "vlm"]
    raise ValueError(f"Unknown mineru backend: {backend}")


def _mathpix_adapter() -> ParserAdapter:
    def check() -> tuple[bool, str | None]:
        try:
            from revisica.ingestion.mathpix_parser import MathpixParser
        except ImportError as error:
            return False, f"import failed: {error}"
        if not MathpixParser.is_available():
            return False, "MATHPIX_APP_ID / MATHPIX_APP_KEY env vars not set"
        return True, None

    def parse(path: Path) -> str:
        from revisica.ingestion.mathpix_parser import MathpixParser
        return MathpixParser().parse(path)

    return ParserAdapter(
        key="mathpix",
        family="mathpix",
        requires_format="pdf",
        parse=parse,
        availability_check=check,
    )


# ── default registry ───────────────────────────────────────────────────


def build_default_adapters(*, mineru_timeout_seconds: int = 900) -> list[ParserAdapter]:
    """Return every adapter the benchmark knows about.

    Availability is **not** checked here — the runner records skip
    reasons in the final report so users can see *why* a parser didn't
    run. Callers pick which adapters to use via
    :func:`expand_parser_selection`.
    """
    return [
        _pandoc_adapter(),
        _tex_basic_adapter(),
        _mineru_adapter("pipeline", mineru_timeout_seconds),
        _mineru_adapter("vlm", mineru_timeout_seconds),
        _mineru_adapter("hybrid", mineru_timeout_seconds),
        _mathpix_adapter(),
    ]


# ── selection language ────────────────────────────────────────────────


_DEFAULT_FAMILIES_FOR_ALL: frozenset[str] = frozenset({
    "pandoc", "tex-basic", "mineru",
})


def expand_parser_selection(
    selection: list[str],
    *,
    all_adapters: list[ParserAdapter],
) -> list[ParserAdapter]:
    """Resolve a user-facing ``--parsers`` selection into concrete adapters.

    Accepted tokens:
      - ``all`` — every default adapter except Mathpix (which costs
        money and must be opted into explicitly).
      - ``mineru`` (family alias) — every registered MinerU backend.
      - ``mineru:<backend>``, ``pandoc``, ``tex-basic``, ``mathpix``
        (exact adapter keys).

    Unknown tokens raise ``ValueError`` with a helpful message listing
    available choices. Preserves the order the user typed and dedupes.
    """
    by_key: dict[str, ParserAdapter] = {adapter.key: adapter for adapter in all_adapters}
    by_family: dict[str, list[ParserAdapter]] = {}
    for adapter in all_adapters:
        by_family.setdefault(adapter.family, []).append(adapter)

    resolved: list[ParserAdapter] = []
    seen_keys: set[str] = set()

    for token in selection:
        token = token.strip()
        if not token:
            continue
        if token == "all":
            selected = [
                adapter for adapter in all_adapters
                if adapter.family in _DEFAULT_FAMILIES_FOR_ALL
            ]
        elif token in by_key:
            selected = [by_key[token]]
        elif token in by_family:
            selected = list(by_family[token])
        else:
            valid_tokens = sorted({"all", *by_key.keys(), *by_family.keys()})
            raise ValueError(
                f"Unknown parser selection '{token}'. "
                f"Valid options: {', '.join(valid_tokens)}"
            )

        for adapter in selected:
            if adapter.key not in seen_keys:
                resolved.append(adapter)
                seen_keys.add(adapter.key)

    return resolved
