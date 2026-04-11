from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path


def find_agent_file(provider: str, filename: str) -> str | None:
    candidates = [
        Path.cwd() / "agents" / provider / filename,
        Path(__file__).resolve().parent.parent.parent / "agents" / provider / filename,
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return None


@lru_cache(maxsize=None)
def load_agent_json(provider: str, filename: str) -> dict[str, object]:
    path = find_agent_file(provider, filename)
    if path is None:
        raise FileNotFoundError(f"Agent definition not found: agents/{provider}/{filename}")
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Agent definition must be a JSON object: agents/{provider}/{filename}")
    return payload
