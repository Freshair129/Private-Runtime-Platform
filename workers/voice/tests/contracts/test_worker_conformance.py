"""Server surface equals contracts/openapi/prp-worker.yaml and fails closed without an engine."""

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from prp_voice.contract.models import CancelResult, Error, Readiness
from prp_voice.lifecycle import Lifecycle
from prp_voice.server.app import create_app

METHODS = {"get", "post", "put", "delete", "patch"}
ATTEMPT = "00000000-0000-4000-8000-000000000001"

pytestmark = [pytest.mark.req("PRP-NFR-024"), pytest.mark.req("PRP-FR-021")]


def inventory(paths: dict[str, Any]) -> set[tuple[str, str, str]]:
    return {
        (method.upper(), path, operation["operationId"])
        for path, item in paths.items()
        for method, operation in item.items()
        if method in METHODS
    }


def test_route_inventory_equals_worker_contract(app: FastAPI, contract: dict[str, Any]) -> None:
    assert inventory(app.openapi()["paths"]) == inventory(contract["paths"])


def test_missing_credential_is_rejected_on_every_operation(
    client: TestClient, contract: dict[str, Any]
) -> None:
    for method, path, _operation in sorted(inventory(contract["paths"])):
        response = client.request(method, path.replace("{attempt_id}", ATTEMPT))
        assert response.status_code == 401, (method, path)
        body = Error.model_validate(response.json())
        assert response.headers["X-Request-ID"] == body.request_id


def test_wrong_credential_is_rejected(client: TestClient) -> None:
    response = client.get(
        "/prp/worker/v1/readiness",
        params={"profile_epoch": 2},
        headers={"Authorization": "Bearer nope"},
    )
    assert response.status_code == 401


def test_unconfigured_credential_fails_closed(lifecycle: Lifecycle) -> None:
    client = TestClient(create_app(lifecycle, service_token=None))
    response = client.get(
        "/prp/worker/v1/readiness",
        params={"profile_epoch": 2},
        headers={"Authorization": "Bearer x"},
    )
    assert response.status_code == 503
    assert Error.model_validate(response.json()).error.code == "RUNTIME_UNAVAILABLE"


def test_readiness_reports_not_ready_without_engine(
    client: TestClient, auth: dict[str, str]
) -> None:
    response = client.get("/prp/worker/v1/readiness", params={"profile_epoch": 2}, headers=auth)
    assert response.status_code == 200
    readiness = Readiness.model_validate(response.json())
    assert readiness.state == "NOT_READY" and readiness.profile_epoch == 2


def test_describe_and_invoke_fail_closed_without_engine(
    client: TestClient, auth: dict[str, str]
) -> None:
    for method, path in (
        ("GET", "/prp/worker/v1/describe"),
        ("POST", "/prp/worker/v1/invocations"),
    ):
        response = client.request(method, path, headers=auth)
        assert response.status_code == 503, path
        assert Error.model_validate(response.json()).error.code == "RUNTIME_UNAVAILABLE"


def test_cancel_reports_unsupported_and_evidence_is_501(
    client: TestClient, auth: dict[str, str]
) -> None:
    cancel = client.post(
        f"/prp/worker/v1/invocations/{ATTEMPT}/cancel",
        json={"fence_token": "fence-0123456789abcdef"},
        headers=auth,
    )
    assert cancel.status_code == 200
    assert CancelResult.model_validate(cancel.json()).disposition == "UNSUPPORTED"
    evidence = client.get(
        f"/prp/worker/v1/invocations/{ATTEMPT}", params={"runtime_epoch": 2}, headers=auth
    )
    assert evidence.status_code == 501
    assert Error.model_validate(evidence.json()).error.code == "UNSUPPORTED"


def test_cancel_rejects_unknown_fields_and_short_fence(
    client: TestClient, auth: dict[str, str]
) -> None:
    bad_fence = client.post(
        f"/prp/worker/v1/invocations/{ATTEMPT}/cancel", json={"fence_token": "short"}, headers=auth
    )
    extra = client.post(
        f"/prp/worker/v1/invocations/{ATTEMPT}/cancel",
        json={"fence_token": "fence-0123456789abcdef", "shell": "rm -rf /"},
        headers=auth,
    )
    assert bad_fence.status_code == 400 and extra.status_code == 400
    assert Error.model_validate(extra.json()).error.code == "INVALID_REQUEST"
