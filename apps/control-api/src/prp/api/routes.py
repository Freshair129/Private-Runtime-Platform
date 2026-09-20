"""Routes for every operation in contracts/openapi/prp-client.yaml.

Request bodies, path/query/header parameters and success responses are bound to the generated
contract models (ADR-PRP-013), so FastAPI validates every JSON request against the contract before
a handler runs: unknown fields, string numbers and out-of-range values end as 400 INVALID_REQUEST.
Handlers still fail closed with 503 STATE_STORE_UNAVAILABLE until M4 wires persistence and runtime
adapters. The two multipart operations (transcribeAudio, uploadArtifact) stay unbound until the
upload path exists; tests/contracts/test_openapi_conformance.py records that exception explicitly.
"""

from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query

from prp.api.security import ClientKeyAuth
from prp.contracts.client_v1 import (
    Artifact,
    CapabilityList,
    ChatRequest,
    ChatResponse,
    Grant,
    GrantRequest,
    Job,
    JobList,
    JobRequest,
    ModelList,
    SpeechRequest,
    Transcript,
)
from prp.platform.errors import ErrorCode, PrpError

IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)]


def _not_configured() -> NoReturn:
    raise PrpError(
        ErrorCode.STATE_STORE_UNAVAILABLE,
        "control plane has no persistence or runtime adapter configured",
        safe_to_retry=False,
    )


def build_router(auth: ClientKeyAuth) -> APIRouter:
    router = APIRouter(dependencies=[Depends(auth)])

    @router.get("/v1/models", operation_id="listModels", response_model=ModelList)
    def list_models() -> ModelList:
        _not_configured()

    @router.get(
        "/prp/v1/capabilities", operation_id="listCapabilities", response_model=CapabilityList
    )
    def list_capabilities() -> CapabilityList:
        _not_configured()

    @router.post("/v1/chat/completions", operation_id="chatCompletion", response_model=ChatResponse)
    def chat_completion(body: ChatRequest) -> ChatResponse:
        _not_configured()

    @router.post(
        "/v1/audio/transcriptions", operation_id="transcribeAudio", response_model=Transcript
    )
    def transcribe_audio() -> Transcript:
        _not_configured()

    @router.post("/v1/audio/speech", operation_id="synthesizeSpeech")
    def synthesize_speech(body: SpeechRequest) -> None:
        _not_configured()

    @router.post(
        "/prp/v1/artifacts", operation_id="uploadArtifact", response_model=Artifact, status_code=201
    )
    def upload_artifact() -> Artifact:
        _not_configured()

    @router.post("/prp/v1/jobs", operation_id="createJob", response_model=Job, status_code=202)
    def create_job(body: JobRequest, idempotency_key: IdempotencyKey) -> Job:
        _not_configured()

    @router.get("/prp/v1/jobs", operation_id="listJobs", response_model=JobList)
    def list_jobs(
        limit: Annotated[int, Query(ge=1, le=100)] = 20, cursor: str | None = None
    ) -> JobList:
        _not_configured()

    @router.get("/prp/v1/jobs/{id}", operation_id="getJob", response_model=Job)
    def get_job(id: UUID) -> Job:
        _not_configured()

    @router.post(
        "/prp/v1/jobs/{id}/cancel",
        operation_id="cancelJob",
        response_model=Job,
        responses={
            202: {"model": Job, "description": "Cancellation requested; cessation not yet verified"}
        },
    )
    def cancel_job(id: UUID) -> Job:
        _not_configured()

    @router.get("/prp/v1/artifacts/{id}", operation_id="readArtifact")
    def read_artifact(id: UUID) -> None:
        _not_configured()

    @router.delete("/prp/v1/artifacts/{id}", operation_id="deleteArtifact", status_code=204)
    def delete_artifact(id: UUID) -> None:
        _not_configured()

    @router.post(
        "/prp/v1/artifacts/{id}/grants",
        operation_id="createArtifactGrant",
        response_model=Grant,
        status_code=201,
    )
    def create_artifact_grant(id: UUID, body: GrantRequest) -> Grant:
        _not_configured()

    @router.delete("/prp/v1/grants/{id}", operation_id="revokeGrant", status_code=204)
    def revoke_grant(id: UUID) -> None:
        _not_configured()

    return router
