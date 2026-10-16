"""Changing a setting must not write env-only values into config.json.

The config endpoints started from ``load_config()``, which overlays
``ANTHROPIC_API_KEY`` / ``OPENAI_API_KEY`` / ``MATHPIX_API_KEY`` and
``REVISICA_BACKEND_MODE`` from the environment, then saved the result.
Saving Mathpix credentials with ``ANTHROPIC_API_KEY`` exported wrote that
key to ``~/.revisica/config.json`` in plain text, and the env backend mode
stayed in effect after the env var was gone.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import revisica.api as api
from revisica.providers import provider_config

_FAKE_TOKEN = "test-token-for-config-endpoints"
_AUTH_HEADERS = {"Authorization": f"Bearer {_FAKE_TOKEN}"}


@pytest.fixture
def config_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / ".revisica" / "config.json"
    monkeypatch.setattr(provider_config, "CONFIG_DIR", path.parent)
    monkeypatch.setattr(provider_config, "CONFIG_PATH", path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-env-only")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-from-env-only")
    monkeypatch.setenv("MATHPIX_API_KEY", "mathpix-from-env-only")
    monkeypatch.setenv("REVISICA_BACKEND_MODE", "api")
    return path


@pytest.fixture
def api_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(api, "_API_TOKEN", _FAKE_TOKEN)
    return TestClient(api.app)


def assert_no_env_values_saved(config_path: Path) -> dict:
    saved_text = config_path.read_text(encoding="utf-8")
    assert "from-env-only" not in saved_text
    saved = json.loads(saved_text)
    assert saved["backend_mode"] == "auto"
    return saved


@pytest.mark.parametrize(
    ("method", "url", "body"),
    [
        ("put", "/api/config/parsers/mathpix/credentials", {"app_id": "id", "app_key": "key"}),
        ("put", "/api/providers/openai-api/config", {"default_model": "gpt-6.1-sol"}),
    ],
)
def test_config_endpoints_save_only_what_was_set(
    config_path: Path, api_client: TestClient, method: str, url: str, body: dict
) -> None:
    response = getattr(api_client, method)(url, json=body, headers=_AUTH_HEADERS)

    assert response.status_code == 200
    assert_no_env_values_saved(config_path)


def test_setting_the_backend_mode_saves_the_requested_mode_only(
    config_path: Path, api_client: TestClient
) -> None:
    response = api_client.put("/api/config/backend-mode", json={"backend_mode": "cli"}, headers=_AUTH_HEADERS)

    assert response.status_code == 200
    saved_text = config_path.read_text(encoding="utf-8")
    assert "from-env-only" not in saved_text
    assert json.loads(saved_text)["backend_mode"] == "cli"


def test_env_values_still_apply_when_loading(config_path: Path) -> None:
    config = provider_config.load_config()

    assert config["backend_mode"] == "api"
    assert config["providers"]["anthropic-api"]["api_key"] == "sk-ant-from-env-only"
