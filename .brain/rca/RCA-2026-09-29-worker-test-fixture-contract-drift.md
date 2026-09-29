# RCA-2026-09-29 — Worker conformance fixture omitted newly required binding fields

**Date:** 2026-09-29
**Status:** RESOLVED_LOCALLY; independent review PASS; pending merge
**Scope:** B0 contract parity, `workers/voice` conformance fixture
**Risk:** LOW; test input only

## Symptom

After the generated worker models and route parameter binding were synchronized, the valid invocation conformance test still receives `400 INVALID_REQUEST` instead of the expected fail-closed `503 RUNTIME_UNAVAILABLE` response.

## Evidence

- `contracts/openapi/prp-worker.yaml` requires `runtime_uid`, `physical_resource_id`, and opaque `runtime_epoch` in `InvocationRequest`.
- Regenerated `workers/voice/src/prp_voice/contract/generated.py` reflects those three required fields.
- `workers/voice/tests/contracts/test_worker_conformance.py::invocation` does not include those fields, so the request is invalid before the handler runs.
- The route handler intentionally raises `RUNTIME_UNAVAILABLE`; it cannot be reached with an invalid fixture.

## Root Cause

The conformance fixture was not updated when the contract added explicit target-binding fields. The fixture remained valid for the previous request shape but no longer represents a valid reservation-bound invocation.

## Why the issue escaped detection

The fixture and contract were reviewed at different times, and the prior generated model was stale. The test expected the handler's fail-closed result without first validating that its input still satisfied the current canonical request schema.

## Proposed prevention

1. Treat canonical required-field changes and positive conformance fixtures as one review unit.
2. Keep one valid fixture assertion that reaches the handler and separate invalid-fixture cases for contract rejection.
3. Run route conformance after generator parity and inspect the first validation failure before interpreting handler status failures.

## Proposed targeted fix

Add stable non-secret values for `runtime_uid`, `physical_resource_id`, and `runtime_epoch` to the shared valid invocation fixture. No production behavior or runtime engine is changed.

## Resolution in the isolated B0 worktree

The valid invocation fixture now includes stable non-secret values for all newly required target-binding fields. The targeted conformance test and full voice suite pass locally. The change remains uncommitted pending independent review.
