"""Generated contract models validate JSON exactly as the contract says (ADR-PRP-013 rules 3, 4, 8).

With a verifier configured, every request reaches contract validation before the fail-closed
handler. Accepted payloads therefore end in 503 STATE_STORE_UNAVAILABLE; rejected payloads end in
400 INVALID_REQUEST. String numbers and booleans are rejected, JSON strings for UUID and date-time
fields are accepted, unknown fields are rejected.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from prp.contracts.client_v1 import Job, JobRequest, Message

EXAMPLES = Path(__file__).resolve().parents[4] / "contracts" / "examples"
JOB_ID = "00000000-0000-4000-8000-000000000001"
IDEMPOTENCY = {"Idempotency-Key": "idem-0123456789"}

pytestmark = [
    pytest.mark.req("PRP-FR-024"),
    pytest.mark.req("PRP-FR-037"),
    pytest.mark.req("PRP-NFR-019"),
]


def code_of(response: Any) -> tuple[int, str]:
    return response.status_code, response.json()["error"]["code"]


def chat(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": "chat-default",
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 64,
    }
    body.update(overrides)
    return body


def test_valid_chat_request_passes_validation_then_fails_closed(authed_client: TestClient) -> None:
    assert code_of(authed_client.post("/v1/chat/completions", json=chat())) == (
        503,
        "STATE_STORE_UNAVAILABLE",
    )


@pytest.mark.parametrize(
    "body",
    [
        chat(max_tokens="64"),
        chat(stream="true"),
        chat(temperature="0.5"),
        chat(shell="rm -rf /"),
        chat(n=2),
    ],
    ids=["string_int", "string_bool", "string_float", "unknown_field", "n_not_1"],
)
def test_contract_violations_are_rejected_before_any_handler(
    authed_client: TestClient, body: dict[str, Any]
) -> None:
    assert code_of(authed_client.post("/v1/chat/completions", json=body)) == (
        400,
        "INVALID_REQUEST",
    )


def test_wrong_key_is_rejected_by_the_verifier(authed_client: TestClient) -> None:
    response = authed_client.post(
        "/v1/chat/completions", json=chat(), headers={"Authorization": "Bearer wrong"}
    )
    assert code_of(response) == (401, "INVALID_KEY")


@pytest.mark.parametrize("example", ["job-asr.example.json", "job-tts.example.json"])
def test_job_examples_with_uuid_strings_are_accepted(
    authed_client: TestClient, example: str
) -> None:
    payload = json.loads((EXAMPLES / example).read_text(encoding="utf-8"))
    assert code_of(authed_client.post("/prp/v1/jobs", json=payload, headers=IDEMPOTENCY)) == (
        503,
        "STATE_STORE_UNAVAILABLE",
    )


def test_job_creation_requires_the_idempotency_header_and_strict_numbers(
    authed_client: TestClient,
) -> None:
    payload = json.loads((EXAMPLES / "job-asr.example.json").read_text(encoding="utf-8"))
    assert code_of(authed_client.post("/prp/v1/jobs", json=payload)) == (400, "INVALID_REQUEST")
    assert code_of(
        authed_client.post("/prp/v1/jobs", json=payload, headers={"Idempotency-Key": "short"})
    ) == (400, "INVALID_REQUEST")
    assert code_of(
        authed_client.post(
            "/prp/v1/jobs", json={**payload, "deadline_seconds": "180"}, headers=IDEMPOTENCY
        )
    ) == (400, "INVALID_REQUEST")
    assert code_of(
        authed_client.post("/prp/v1/jobs", json={**payload, "kind": "video"}, headers=IDEMPOTENCY)
    ) == (400, "INVALID_REQUEST")


def test_path_and_query_parameters_follow_the_contract(authed_client: TestClient) -> None:
    assert code_of(authed_client.get(f"/prp/v1/jobs/{JOB_ID}")) == (503, "STATE_STORE_UNAVAILABLE")
    assert code_of(authed_client.get("/prp/v1/jobs/not-a-uuid")) == (400, "INVALID_REQUEST")
    assert code_of(authed_client.get("/prp/v1/jobs", params={"limit": 100})) == (
        503,
        "STATE_STORE_UNAVAILABLE",
    )
    assert code_of(authed_client.get("/prp/v1/jobs", params={"limit": 101})) == (
        400,
        "INVALID_REQUEST",
    )


def test_grant_request_bounds_and_strictness(authed_client: TestClient) -> None:
    url = f"/prp/v1/artifacts/{JOB_ID}/grants"
    assert code_of(authed_client.post(url, json={"ttl_seconds": 3600})) == (
        503,
        "STATE_STORE_UNAVAILABLE",
    )
    assert code_of(authed_client.post(url, json={"ttl_seconds": "3600"})) == (
        400,
        "INVALID_REQUEST",
    )
    assert code_of(authed_client.post(url, json={"ttl_seconds": 30})) == (400, "INVALID_REQUEST")


def test_models_are_frozen_and_reject_naive_timestamps() -> None:
    job = Job.model_validate(
        {
            "job_id": JOB_ID,
            "request_id": "r1",
            "kind": "asr",
            "outcome": "PENDING",
            "execution_status": "QUEUED",
            "cancellation_requested": False,
            "status_path": f"/prp/v1/jobs/{JOB_ID}",
            "created_at": "2026-09-20T12:00:00Z",
            "deadline_at": "2026-09-20T12:03:00Z",
        }
    )
    assert job.created_at == datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
    with pytest.raises(ValidationError):
        Job.model_validate({**job.model_dump(mode="json"), "created_at": "2026-09-20T12:00:00"})
    with pytest.raises(ValidationError):
        Message(role="user", content="x").content = "y"  # type: ignore[misc]
    request = JobRequest.model_validate(
        json.loads((EXAMPLES / "job-tts.example.json").read_text(encoding="utf-8"))
    )
    assert request.root.kind == "tts"
