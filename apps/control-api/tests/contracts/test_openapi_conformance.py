"""The API surface equals contracts/openapi/prp-client.yaml and fails closed with the envelope.

Inventory (paths, methods, operationIds) must match exactly. For every operation the request body,
parameters and first JSON success response that FastAPI derives from the generated contract models
must conform to the contract after normalization (ADR-PRP-013 rule 8): titles, descriptions,
defaults and $defs names are ignored; types, property sets, required lists, enums, consts, formats
and bounds must agree. An endpoint is still not implemented merely because FastAPI renders it
(API-PRP addendum); success paths arrive with adapters in M4.
"""

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

METHODS = {"get", "post", "put", "delete", "patch"}
SAMPLE_ID = "00000000-0000-4000-8000-000000000001"
# multipart/form-data bodies are bound together with the upload path in M4 (needs python-multipart).
UNBOUND_MULTIPART = {"transcribeAudio", "uploadArtifact"}
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

pytestmark = [pytest.mark.req("PRP-FR-002"), pytest.mark.req("PRP-NFR-019")]


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
    """Reduce an OpenAPI/JSON-Schema node to the parts the contract governs."""
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
    """Every contract-governed key must be present and equal on the application side."""
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


def test_route_inventory_equals_client_contract(app: FastAPI, contract: dict[str, Any]) -> None:
    expected = inventory(contract["paths"])
    actual = inventory(app.openapi()["paths"])
    assert actual == expected
    assert len(contract["paths"]) == 12 and len(expected) == 14


def test_parameters_bodies_and_responses_conform_to_contract(
    app: FastAPI, contract: dict[str, Any]
) -> None:
    generated = app.openapi()
    unbound: set[str] = set()
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
        elif body:
            unbound.add(where)

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
    assert unbound == UNBOUND_MULTIPART


def assert_envelope(body: dict[str, Any], contract: dict[str, Any]) -> None:
    schema = contract["components"]["schemas"]["Error"]
    error_schema = resolve(contract, schema["properties"]["error"])
    assert set(body) == set(schema["properties"])
    assert set(body["error"]) <= set(error_schema["properties"])
    assert set(error_schema["required"]) <= set(body["error"])
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
