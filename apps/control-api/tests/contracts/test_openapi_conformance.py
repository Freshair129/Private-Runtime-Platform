"""The API surface equals contracts/openapi/prp-client.yaml and fails closed with the envelope.

An endpoint is not implemented merely because FastAPI renders it (API-PRP addendum); these tests
check inventory and error behaviour only. Success paths arrive with adapters in M4.
"""

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

METHODS = {"get", "post", "put", "delete", "patch"}
SAMPLE_ID = "00000000-0000-4000-8000-000000000001"

pytestmark = [pytest.mark.req("PRP-FR-002"), pytest.mark.req("PRP-NFR-019")]


def inventory(paths: dict[str, Any]) -> set[tuple[str, str, str]]:
    return {
        (method.upper(), path, operation["operationId"])
        for path, item in paths.items()
        for method, operation in item.items()
        if method in METHODS
    }


def test_route_inventory_equals_client_contract(app: FastAPI, contract: dict[str, Any]) -> None:
    expected = inventory(contract["paths"])
    actual = inventory(app.openapi()["paths"])
    assert actual == expected
    assert len(contract["paths"]) == 12 and len(expected) == 14


def assert_envelope(body: dict[str, Any], contract: dict[str, Any]) -> None:
    schema = contract["components"]["schemas"]["Error"]
    assert set(body) == set(schema["properties"])
    assert set(body["error"]) <= set(schema["properties"]["error"]["properties"])
    assert set(schema["properties"]["error"]["required"]) <= set(body["error"])
    assert isinstance(body["request_id"], str) and body["request_id"]
    assert isinstance(body["safe_to_retry"], bool)


def test_missing_credential_yields_401_envelope_on_every_operation(
    client: TestClient, contract: dict[str, Any]
) -> None:
    for method, path, _operation in sorted(inventory(contract["paths"])):
        response = client.request(method, path.replace("{id}", SAMPLE_ID))
        assert response.status_code == 401, (method, path, response.text)
        body = response.json()
        assert_envelope(body, contract)
        assert body["error"]["code"] == "INVALID_KEY"
        assert response.headers["X-Request-ID"] == body["request_id"]


def test_bearer_without_configured_verifier_fails_closed(
    client: TestClient, contract: dict[str, Any]
) -> None:
    response = client.get("/v1/models", headers={"Authorization": "Bearer not-a-real-key"})
    assert response.status_code == 503
    body = response.json()
    assert_envelope(body, contract)
    assert body["error"]["code"] == "STATE_STORE_UNAVAILABLE"
    assert body["safe_to_retry"] is False


def test_unknown_route_and_wrong_method_use_not_found_envelope(
    client: TestClient, contract: dict[str, Any]
) -> None:
    for response in (client.get("/v1/does-not-exist"), client.put("/v1/models")):
        assert response.status_code == 404
        body = response.json()
        assert_envelope(body, contract)
        assert body["error"]["code"] == "NOT_FOUND"


def test_no_interactive_docs_are_exposed(client: TestClient) -> None:
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 404
