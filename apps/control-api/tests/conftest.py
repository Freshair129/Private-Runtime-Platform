from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

from prp.api.app import Dependencies, create_app
from prp.settings import Settings

REPO_ROOT = Path(__file__).resolve().parents[3]
CLIENT_CONTRACT = REPO_ROOT / "contracts" / "openapi" / "prp-client.yaml"
LOCK_FILE = Path(__file__).resolve().parents[1] / "uv.lock"


@pytest.fixture(scope="session")
def contract() -> dict[str, Any]:
    loaded: dict[str, Any] = yaml.safe_load(CLIENT_CONTRACT.read_text(encoding="utf-8"))
    return loaded


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings, Dependencies())


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=True)
