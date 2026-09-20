from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

from prp.api.app import Dependencies, create_app
from prp.core.access.model import AuthContext, Scope
from prp.settings import Settings

TEST_KEY = "valid-test-key"


class FakeVerifier:
    """Test double for the KeyVerifier port: accepts one secret, never stores or returns it."""

    def verify(self, presented_secret: str, *, now: datetime) -> AuthContext | None:
        if presented_secret != TEST_KEY:
            return None
        return AuthContext(
            organization_id="o1", principal_id="u1", key_id="k1", scopes=frozenset(Scope)
        )


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


@pytest.fixture
def authed_client(settings: Settings) -> TestClient:
    """Client whose key verifies, so requests reach contract validation and fail-closed handlers."""
    verified = TestClient(
        create_app(settings, Dependencies(key_verifier=FakeVerifier())),
        raise_server_exceptions=True,
    )
    verified.headers.update({"Authorization": f"Bearer {TEST_KEY}"})
    return verified
