from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

from prp_voice.lifecycle import Identity, Lifecycle
from prp_voice.server.app import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKER_CONTRACT = REPO_ROOT / "contracts" / "openapi" / "prp-worker.yaml"
NOW = datetime(2026, 9, 20, 12, 0, 0, tzinfo=UTC)
TOKEN = "test-service-token-0123456789"


@pytest.fixture(scope="session")
def contract() -> dict[str, Any]:
    loaded: dict[str, Any] = yaml.safe_load(WORKER_CONTRACT.read_text(encoding="utf-8"))
    return loaded


@pytest.fixture
def identity() -> Identity:
    return Identity(
        runtime_uid="rt-speech-1",
        physical_resource_id="hostB/cpu-pool",
        profile_hash="sha256:profile",
        profile_epoch=2,
    )


@pytest.fixture
def lifecycle(identity: Identity) -> Lifecycle:
    return Lifecycle(identity, clock=lambda: NOW)


@pytest.fixture
def app(lifecycle: Lifecycle) -> FastAPI:
    return create_app(lifecycle, service_token=TOKEN)


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}
