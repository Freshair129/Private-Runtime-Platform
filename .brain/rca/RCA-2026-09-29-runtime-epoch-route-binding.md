# RCA-2026-09-29 — Worker route bound opaque runtime epoch as integer

**Date:** 2026-09-29
**Status:** RESOLVED_LOCALLY; independent review PASS; pending merge
**Scope:** B0 contract parity, `workers/voice` route binding
**Risk:** MEDIUM; isolated public query-parameter type binding

## Symptom

After regenerating the JSON twins and generated models from the canonical worker YAML, voice contract conformance still fails. The `getExecutionEvidence` query parameter `runtime_epoch` is exposed as an integer by FastAPI although the canonical contract requires an opaque string. A valid invocation request is also rejected with `400 INVALID_REQUEST` instead of reaching the fail-closed `503 RUNTIME_UNAVAILABLE` handler.

## Evidence

- `contracts/openapi/prp-worker.yaml` defines `getExecutionEvidence.runtime_epoch` as a required string with length bounds.
- `workers/voice/src/prp_voice/server/app.py` defines one `Epoch = Annotated[int, Query(ge=0)]` alias and uses it for both `readiness(profile_epoch)` and `execution_evidence(runtime_epoch)`.
- The regenerated `workers/voice/src/prp_voice/contract/generated.py` correctly models contract `runtime_epoch` fields as `str`.
- Voice conformance fails at `getExecutionEvidence.param.runtime_epoch`: contract `string`, app schema `integer`.
- Voice conformance also reports the valid invoke test returning `400` because the request's runtime binding does not match the updated contract model.

## Root Cause

The route implementation reused an integer `Epoch` alias for two different contract concepts: the PRP profile-binding epoch (`profile_epoch`, integer) and the opaque runtime restart token (`runtime_epoch`, string). The canonical contract separated these concepts, but the route annotation was not updated with the generated artifacts.

## Why the issue escaped detection

- The earlier route skeleton treated both names as numeric epochs, so the old focused tests did not exercise the new opaque-token distinction.
- Generator parity checks validate generated models, not handwritten FastAPI query annotations.
- The route-level contract-conformance test was the first check comparing the complete parameter schema after the pull.

## Proposed prevention

1. Use separate, descriptive aliases for `ProfileEpoch` and `RuntimeEpoch`.
2. Run route-level contract conformance after every contract regeneration.
3. Do not use a shared primitive alias when two contract fields have different semantics, even if their names both contain `epoch`.
4. Include the route-binding result in the B0 receipt, separately from generated-model parity.

## Proposed targeted fix

Keep `profile_epoch` as `Annotated[int, Query(ge=0)]`; bind `runtime_epoch` as `Annotated[str, Query(min_length=1, max_length=128)]` only on `getExecutionEvidence`. No runtime engine or deployment behavior changes.

## Resolution in the isolated B0 worktree

The route now uses separate `ProfileEpoch` and `RuntimeEpoch` aliases. Route-level worker conformance passes, and the full voice suite passes locally. The change remains uncommitted pending independent review.
