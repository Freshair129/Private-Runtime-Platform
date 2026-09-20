"""Routes for every operation in contracts/openapi/prp-client.yaml.

M3: the route inventory (paths, methods, operationIds) is bound to the contract and verified by
tests/contracts/test_openapi_conformance.py. Handlers fail closed with 503 STATE_STORE_UNAVAILABLE
until M4 wires persistence and runtime adapters. Request/response models follow at M4 together with
the decision on generated versus hand-written contract models.
"""

from typing import NoReturn

from fastapi import APIRouter, Depends

from prp.api.security import ClientKeyAuth
from prp.platform.errors import ErrorCode, PrpError


def _not_configured() -> NoReturn:
    raise PrpError(
        ErrorCode.STATE_STORE_UNAVAILABLE,
        "control plane has no persistence or runtime adapter configured",
        safe_to_retry=False,
    )


def build_router(auth: ClientKeyAuth) -> APIRouter:
    router = APIRouter(dependencies=[Depends(auth)])

    @router.get("/v1/models", operation_id="listModels")
    def list_models() -> None:
        _not_configured()

    @router.get("/prp/v1/capabilities", operation_id="listCapabilities")
    def list_capabilities() -> None:
        _not_configured()

    @router.post("/v1/chat/completions", operation_id="chatCompletion")
    def chat_completion() -> None:
        _not_configured()

    @router.post("/v1/audio/transcriptions", operation_id="transcribeAudio")
    def transcribe_audio() -> None:
        _not_configured()

    @router.post("/v1/audio/speech", operation_id="synthesizeSpeech")
    def synthesize_speech() -> None:
        _not_configured()

    @router.post("/prp/v1/artifacts", operation_id="uploadArtifact")
    def upload_artifact() -> None:
        _not_configured()

    @router.post("/prp/v1/jobs", operation_id="createJob")
    def create_job() -> None:
        _not_configured()

    @router.get("/prp/v1/jobs", operation_id="listJobs")
    def list_jobs() -> None:
        _not_configured()

    @router.get("/prp/v1/jobs/{id}", operation_id="getJob")
    def get_job(id: str) -> None:
        _not_configured()

    @router.post("/prp/v1/jobs/{id}/cancel", operation_id="cancelJob")
    def cancel_job(id: str) -> None:
        _not_configured()

    @router.get("/prp/v1/artifacts/{id}", operation_id="readArtifact")
    def read_artifact(id: str) -> None:
        _not_configured()

    @router.delete("/prp/v1/artifacts/{id}", operation_id="deleteArtifact")
    def delete_artifact(id: str) -> None:
        _not_configured()

    @router.post("/prp/v1/artifacts/{id}/grants", operation_id="createArtifactGrant")
    def create_artifact_grant(id: str) -> None:
        _not_configured()

    @router.delete("/prp/v1/grants/{id}", operation_id="revokeGrant")
    def revoke_grant(id: str) -> None:
        _not_configured()

    return router
