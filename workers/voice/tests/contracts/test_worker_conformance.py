"""Server surface equals contracts/openapi/prp-worker.yaml and fails closed without an engine.

Inventory must match exactly; parameters, JSON request bodies and the first JSON success response
FastAPI derives from the generated models must conform to the contract after normalization
(ADR-PRP-013 rule 8). Strictness: string numbers and unknown fields are rejected, JSON strings for
UUID and date-time fields are accepted.
"""

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from prp_voice.contract.models import CancelResult, Error, Readiness
from prp_voice.lifecycle import Lifecycle
from prp_voice.server.app import create_app

METHODS = {"get", "post", "put", "delete", "patch"}
ATTEMPT = "00000000-0000-4000-8000-000000000001"
INVOCATION = "00000000-0000-4000-8000-000000000002"
CONSTRAINT_KEYS = (
    "const",
    "format",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
    "pattern",
)

pytestmark = [
    pytest.mark.req("PRP-NFR-024"),
    pytest.mark.req("PRP-FR-021"),
    pytest.mark.req("PRP-FR-042"),
]


def inventory(paths: dict[str, Any]) -> set[tuple[str, str, str]]:
    return {
        (method.upper(), path, operation["operationId"])
        for path, item in paths.items()
        for method, operation in item.items()
        if method in METHODS
    }


def resolve(doc: dict[str, Any], schema: Any) -> Any:
    while isinstance(schema, dict) and "$ref" in schema:
        schema = doc["components"]["schemas"][schema["$ref"].rsplit("/", 1)[1]]
    return schema


def normalize(doc: dict[str, Any], schema: Any, *, required: bool = True) -> Any:
    node = resolve(doc, schema)
    if not isinstance(node, dict):
        return node
    variants = node.get("oneOf") or node.get("anyOf")
    if variants:
        non_null = [v for v in variants if resolve(doc, v).get("type") != "null"]
        nullable = len(non_null) != len(variants)
        if len(non_null) == 1:
            inner = normalize(doc, non_null[0], required=required)
            if nullable and required and isinstance(inner, dict):
                inner = {**inner, "nullable": True}
            return inner
        return {"oneOf": [normalize(doc, v) for v in non_null]}
    out: dict[str, Any] = {}
    kind = node.get("type")
    if isinstance(kind, list):
        kinds = [k for k in kind if k != "null"]
        if "null" in kind and required:
            out["nullable"] = True
        kind = kinds[0] if len(kinds) == 1 else kinds
    if kind is not None and "const" not in node:
        out["type"] = kind
    for key in CONSTRAINT_KEYS:
        if key in node:
            out[key] = node[key]
    if "enum" in node:
        out["enum"] = sorted(str(v) for v in node["enum"] if v is not None)
    if "properties" in node:
        required_names = set(node.get("required", []))
        out["required"] = sorted(required_names)
        out["properties"] = {
            name: normalize(doc, sub, required=name in required_names)
            for name, sub in node["properties"].items()
        }
        out["additionalProperties"] = node.get("additionalProperties", True)
    if "items" in node:
        out["items"] = normalize(doc, node["items"])
    return out


def conforms(expected: Any, actual: Any) -> bool:
    try:
        assert_conforms(expected, actual, "")
    except AssertionError:
        return False
    return True


def assert_conforms(expected: Any, actual: Any, where: str) -> None:
    if not isinstance(expected, dict):
        assert expected == actual, f"{where}: contract {expected!r} != app {actual!r}"
        return
    assert isinstance(actual, dict), f"{where}: app side is {actual!r}"
    for key, value in expected.items():
        assert key in actual, f"{where}: app schema lacks {key}={value!r}"
        if key == "properties":
            assert set(value) == set(actual[key]), (
                f"{where}: property set differs by {set(value) ^ set(actual[key])}"
            )
            for name, sub in value.items():
                assert_conforms(sub, actual[key][name], f"{where}.{name}")
        elif key == "oneOf":
            remaining = list(actual[key])
            assert len(value) == len(remaining), (
                f"{where}: oneOf arity {len(value)} != {len(remaining)}"
            )
            for variant in value:
                match = next(
                    (i for i, cand in enumerate(remaining) if conforms(variant, cand)), None
                )
                assert match is not None, f"{where}: no app variant matches {variant!r}"
                remaining.pop(match)
        elif key == "items":
            assert_conforms(value, actual[key], f"{where}[]")
        else:
            assert value == actual[key], f"{where}.{key}: contract {value!r} != app {actual[key]!r}"


def operations(doc: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    found: dict[tuple[str, str], dict[str, Any]] = {}
    for path, item in doc["paths"].items():
        shared = item.get("parameters", [])
        for method, operation in item.items():
            if method in METHODS:
                found[(method.upper(), path)] = {
                    **operation,
                    "parameters": shared + operation.get("parameters", []),
                }
    return found


def test_route_inventory_equals_worker_contract(app: FastAPI, contract: dict[str, Any]) -> None:
    assert inventory(app.openapi()["paths"]) == inventory(contract["paths"])


def test_parameters_bodies_and_responses_conform_to_contract(
    app: FastAPI, contract: dict[str, Any]
) -> None:
    generated = app.openapi()
    for key, expected in operations(contract).items():
        actual = operations(generated)[key]
        where = expected["operationId"]
        expected_params = {
            (p["name"], p["in"], bool(p.get("required"))) for p in expected["parameters"]
        }
        actual_params = {
            (p["name"], p["in"], bool(p.get("required"))) for p in actual["parameters"]
        }
        assert expected_params == actual_params, (
            f"{where}: parameters {expected_params ^ actual_params}"
        )
        for parameter in expected["parameters"]:
            twin = next(
                p
                for p in actual["parameters"]
                if (p["name"], p["in"]) == (parameter["name"], parameter["in"])
            )
            assert_conforms(
                normalize(contract, parameter["schema"], required=bool(parameter.get("required"))),
                normalize(generated, twin["schema"], required=bool(parameter.get("required"))),
                f"{where}.param.{parameter['name']}",
            )
        body = expected.get("requestBody", {}).get("content", {})
        if "application/json" in body:
            actual_body = actual.get("requestBody", {}).get("content", {}).get("application/json")
            assert actual_body is not None, f"{where}: JSON request body not bound"
            assert_conforms(
                normalize(contract, body["application/json"]["schema"]),
                normalize(generated, actual_body["schema"]),
                f"{where}.requestBody",
            )
        for code, response in expected["responses"].items():
            if not code.startswith("2"):
                continue
            assert code in actual["responses"], f"{where}: success status {code} not declared"
            json_response = response.get("content", {}).get("application/json")
            if json_response is None:
                continue
            actual_json = actual["responses"][code].get("content", {}).get("application/json")
            assert actual_json is not None, f"{where}: JSON response {code} not bound"
            assert_conforms(
                normalize(contract, json_response["schema"]),
                normalize(generated, actual_json["schema"]),
                f"{where}.response.{code}",
            )
            break


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
    assert (
        client.get(
            "/prp/worker/v1/readiness", params={"profile_epoch": -1}, headers=auth
        ).status_code
        == 400
    )


def invocation(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "invocation_id": INVOCATION,
        "attempt_id": ATTEMPT,
        "profile_epoch": 3,
        "fence_token": "fence-0123456789abcdef",
        "deadline_at": "2026-09-20T12:03:00Z",
        "payload": {
            "kind": "tts",
            "profile_id": "p",
            "input": "สวัสดี",
            "voice": "v",
            "response_format": "mp3",
        },
    }
    body.update(overrides)
    return body


def test_describe_and_valid_invoke_fail_closed_without_engine(
    client: TestClient, auth: dict[str, str]
) -> None:
    describe = client.get("/prp/worker/v1/describe", headers=auth)
    assert describe.status_code == 503
    invoke = client.post("/prp/worker/v1/invocations", json=invocation(), headers=auth)
    assert invoke.status_code == 503, invoke.text
    assert Error.model_validate(invoke.json()).error.code == "RUNTIME_UNAVAILABLE"


@pytest.mark.parametrize(
    "body",
    [
        invocation(profile_epoch="3"),
        invocation(deadline_at="2026-09-20T12:03:00"),
        invocation(shell="rm -rf /"),
        invocation(payload={"kind": "video", "profile_id": "p"}),
        invocation(fence_token="short"),
    ],
    ids=["string_int", "naive_datetime", "unknown_field", "bad_discriminator", "short_fence"],
)
def test_invoke_rejects_contract_violations_before_the_handler(
    client: TestClient, auth: dict[str, str], body: dict[str, Any]
) -> None:
    response = client.post("/prp/worker/v1/invocations", json=body, headers=auth)
    assert response.status_code == 400, response.text
    assert Error.model_validate(response.json()).error.code == "INVALID_REQUEST"


def test_cancel_reports_unsupported_and_evidence_is_501(
    client: TestClient, auth: dict[str, str]
) -> None:
    cancel = client.post(
        f"/prp/worker/v1/invocations/{ATTEMPT}/cancel",
        json={"fence_token": "fence-0123456789abcdef"},
        headers=auth,
    )
    assert cancel.status_code == 200
    assert str(CancelResult.model_validate(cancel.json()).attempt_id) == ATTEMPT
    assert CancelResult.model_validate(cancel.json()).disposition == "UNSUPPORTED"
    evidence = client.get(
        f"/prp/worker/v1/invocations/{ATTEMPT}", params={"runtime_epoch": 2}, headers=auth
    )
    assert evidence.status_code == 501
    assert Error.model_validate(evidence.json()).error.code == "UNSUPPORTED"
    assert (
        client.get(
            "/prp/worker/v1/invocations/not-a-uuid", params={"runtime_epoch": 2}, headers=auth
        ).status_code
        == 400
    )


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
