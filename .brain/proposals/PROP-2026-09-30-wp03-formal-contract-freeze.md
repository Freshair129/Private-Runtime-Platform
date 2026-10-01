---
document_id: PROP-2026-09-30-WP03-FREEZE
title: "WP03 formal contract freeze receipt"
version: 0.1.0
status: approved
created_at: 2026-09-30
complexity: C-3
risk: HIGH
decision_status: APPROVED
implementation_status: NOT_STARTED
owner_decision: "APPROVED_BY_REPOSITORY_OWNER_ON_2026-09-30"
---

# WP03 formal contract freeze receipt

## 1. Decision and scope

The repository owner approved the formal WP03 freeze on 2026-09-30. This receipt freezes only the current canonical worker and management contracts as the first supported WP03 baseline. It does not approve application implementation, runtime qualification, DEV deployment, or production release.

The frozen artifacts are `contracts/openapi/prp-worker.yaml` and `contracts/openapi/prp-management.yaml`, with their generated JSON exports and Pydantic models. The public client contract `prp-client` remains at `0.3.0`, `DRAFT`, and outside this WP03 freeze; this receipt does not approve its schema. Any client-contract approval or freeze requires a separate owner decision. Worker and management route paths remain under `/prp/worker/v1` and `/prp/admin/v1`; no route or schema shape changes are introduced by this freeze.

## 2. Freeze metadata

1. Promote worker and management `info.version` from `0.4.0-draft` to `0.4.0`.
2. Set `x-prp-status` to `FROZEN` and remove `x-prp-freeze-gate` from both contracts.
3. Keep YAML canonical; regenerate the JSON twins and generated model artifacts from source.
4. Correct contract descriptions and supporting documentation to point to this freeze receipt and remove stale WP01-blocker language.

## 3. Version and migration record

This is the first frozen WP03 baseline recorded in the repository. The D1-D6 schema decisions were made while the contracts were explicitly DRAFT; the freeze itself changes metadata and descriptions only. No earlier frozen worker or management version is recorded, so this receipt defines no migration from a prior frozen baseline. The route families remain version `v1`.

The contract `x-prp-consumers` lists planned in-repository consumers and does not establish the external consumer inventory. External use is unverified. This receipt does not claim that external consumers migrated or that any server implements these contracts. Before implementation is deployed to DEV, the work package must identify any external consumers and reconcile them with this baseline. Any later breaking change to a frozen contract requires the major route/version and migration note required by API-PRP §10.

## 4. Gate boundary

- **WP03 decision:** satisfied by this receipt. D1-D6 authority, worker, management, and secret-custody contract decisions are recorded in [the WP03 contract proposal](PROP-2026-09-29-wp03-contract-authority-freeze.md) and [the D6 management closure](PROP-2026-09-29-wp03-management-schema-closure.md).
- **RG0:** remains a separate implementation-entry gate. WP03 freezes the approved contract-level admission/key-authority chain and secret/rights design; RG0 still requires the hardware/runtime inventory assigned to WP02 and evidence that the approved design is ready for the selected environment. WP02 remains `NOT_STARTED`; the planning host context is not qualified hardware evidence. No adapter implementation starts before RG0 passes.
- Secret-store product/topology and actual model/voice license receipts remain downstream deployment/activation evidence; the logical custody and rights-policy boundaries in the WP03 decision are frozen here.
- API-PRP and SECURITY-DATA-PRP retain their overall `draft-for-review` status. This receipt approves the WP03 contract decision scope only; it is not whole-document approval.

## 5. Parent, peer, risk, and scope

- **Parent:** the approved PRD/SRS baseline and WP01 scope/ownership receipt.
- **Peers:** API-PRP §§1, 7-10; SECURITY-DATA-PRP §§4-5; ADR-PRP authority decisions; canonical worker and management YAML.
- **Risk:** HIGH. The freeze establishes the supported worker and management contract baseline for internal integrations.
- **Out of scope:** client-contract approval or freeze, application implementation, database migrations, secret-store deployment, external consumer migration, hardware qualification, runtime acceptance, DEV, and PROD.

## 6. Acceptance and exit evidence

- Owner approval is recorded in this receipt.
- Worker and management YAML identify version `0.4.0`, status `FROZEN`, and no pending WP03 freeze gate; their route paths and schema shapes are unchanged by the freeze operation.
- The public client contract remains `0.3.0` / `DRAFT` and is not approved by this WP03 decision.
- JSON exports and generated models match canonical YAML; examples and documentation validation pass.
- WP03 is decision-complete; WP02, RG0, WP25, and WP04 implementation/runtime work remain governed by their own gates.
- All 92 runtime acceptance cases remain `NOT_RUN`; no implementation, runtime exercise, DEV deployment, or production activity is claimed.

## 7. Version diff

| Artifact | Before | After approval |
|---|---|---|
| Worker / management YAML | `0.4.0-draft`, `DRAFT`, gate `WP03` | `0.4.0`, `FROZEN`, gate removed; routes and schema shapes unchanged |
| Worker / management JSON | Generated from DRAFT YAML | Regenerated from frozen YAML |
| Generated Pydantic models | Derived from DRAFT YAML | Regenerated from canonical frozen YAML |
| Public client contract | `0.3.0` / `DRAFT`, outside WP03 scope | Unchanged; separate owner decision required for approval or freeze |
| API-PRP / SECURITY-DATA-PRP | `draft-for-review` | Overall status unchanged |
| Runtime acceptance | 92 `NOT_RUN` | Unchanged |

## 8. Owner review

The repository owner approved the WP03 formal contract freeze on 2026-09-30. WP03 decision status is `APPROVED`; implementation status remains `NOT_STARTED`. RG0 and all runtime, DEV, and PROD gates remain independently controlled.
