from __future__ import annotations

import json
from urllib.parse import quote
from urllib.request import urlopen


HF_DATASETS_SERVER = "https://datasets-server.huggingface.co"


def fetch_dataset_splits(dataset: str) -> list[dict[str, object]]:
    payload = _fetch_json(f"/splits?dataset={quote(dataset, safe='')}")
    return list(payload.get("splits", []))


def fetch_dataset_rows(
    dataset: str,
    config: str,
    split: str,
    offset: int = 0,
    length: int = 10,
) -> list[dict[str, object]]:
    payload = _fetch_json(
        "/rows?"
        f"dataset={quote(dataset, safe='')}&config={quote(config, safe='')}"
        f"&split={quote(split, safe='')}&offset={offset}&length={length}"
    )
    return [dict(item["row"]) for item in payload.get("rows", [])]


def _fetch_json(path: str) -> dict[str, object]:
    with urlopen(f"{HF_DATASETS_SERVER}{path}") as response:
        return json.loads(response.read().decode("utf-8"))
