---
document_id: PROP-2026-09-29-WP03
title: "WP03 contract and authority freeze proposal"
version: 0.1.0-draft
status: approved
created_at: 2026-09-29
complexity: C-3
risk: HIGH
implementation_status: IN_PROGRESS
owner_decision: APPROVED_BY_REPOSITORY_OWNER_ON_2026-09-29
---

# WP03 contract and authority freeze proposal

## 1. Purpose and boundary

Record WP03's contract, authority, and secret-custody decisions approved by the repository owner on 2026-09-29. This approval authorizes the scoped documentation, canonical contract, and generated-model updates; it is not a formal WP03 freeze, runtime implementation approval, server-access approval, or production release approval. No application code or acceptance-test status changes are included.

## 2. Verified entry evidence

- WP24 run 1's decision receipt is approved on 2026-09-24, selects candidate A (Xinference-managed runtimes) on capability evidence, and explicitly states that its approval satisfies the WP24 gate for WP03. It records nine conditions and names PRP as the client-key authority. Source: `docs/evidence/wp24/WP24-2026-09-20-run1.json`.
- WP24 run 2 was measurement-only under the owner's instruction. It did not alter run 1's selection or acceptance statuses. DEV-07 was narrowed to DEV-09; cache-derived capacity figures are not a like-for-like A/B comparison because the vLLM builds differ. Source: `docs/evidence/wp24/WP24-2026-09-24-run2/A/FINDINGS.md` and `docs/CHANGELOG-PRP.md`.
- The roadmap still records WP01 and WP24 as `NOT_STARTED`. WP03 depends on both. WP01's scope/ownership closure therefore needs an owner-backed receipt before WP03 can be recorded as formally ready.
- All 92 acceptance tests remain `NOT_RUN`. Fit-gap dispositions and the WP24 decision receipt are not runtime acceptance evidence.

## 3. Approved decision set

### D1 — Candidate binding

Preserve WP24 run 1's conditional selection of candidate A. Treat run 2 as supplementary measurements only; retain DEV-09 as a limitation and exclude non-comparable cache/concurrency figures from selection or capacity claims. A same-version comparison is required only if the owner reopens the A/B selection based on performance. Exact OS, engine backend, image digest, and supported artifact versions remain release-profile decisions for WP02/WP25/DEV; the WP03 contract stays vendor-neutral.

### D2 — Key and admission authority

Keep PRP as the sole client-key authority with verifier-only storage. Neither Xinference nor LiteLLM stores or verifies client keys. Keep PRP Router as selector and PRP Admission as the single authority that atomically reserves quota, queue, and physical-resource capacity. Candidate A owns runtime lifecycle only through the adapter; vendor placement, retries, relocation, and cancellation must not bypass PRP's reservation and fencing rules.

This records an architecture boundary, not evidence that the durable admission implementation or its PostgreSQL/fault behavior is complete.

### D3 — Secret-custody design

Approve this logical design for contract freeze:

- Client keys are shown once; PRP stores only a verifier and non-secret prefix.
- Candidate A's administrative/service credentials are a separate credential class from client keys. Management contracts carry an opaque `credential_ref`, never credential material.
- Recoverable manager credentials and `XINFERENCE_HOME` are treated as sensitive. Secret-store encryption and backup-recovery keys remain in separate custody boundaries; credentials are excluded from source, image, browser, logs, exports, and ordinary backups.
- Rotation/revocation is explicit and audited. Secret-store product, deployment topology, provisioning egress, and recovery procedure remain unselected and must be approved before the applicable WP04/DEV or production gate.

### D4 — Worker contract consistency

Apply the already-approved ADR-PRP-014 at WP03:

- `ExecutionEvidence.runtime_epoch` and the runtime-epoch query parameter become opaque strings with length 1–128 and equality-only comparison.
- `InvocationRequest.profile_epoch` remains the PRP-minted integer reservation epoch; do not describe it as the runtime's actual epoch.
- Align API-PRP readiness prose with the machine contract: `READY`, `NOT_READY`, or `UNKNOWN`. `NOT_READY` means a known ineligible/loading/draining/mismatch state; `UNKNOWN` means the adapter cannot make a fresh, trustworthy observation. Only current `READY` observations may be dispatched.
- Add an explicit expected target binding to invocation semantics (`runtime_uid`, `physical_resource_id`, and `runtime_epoch`). The adapter must validate the reserved target before dispatch and fail closed when the manager cannot enforce or prove that binding.
- Preserve the existing rules that invocation is already admitted, cancellation acknowledgement is not proof of termination, and ambiguous execution remains `UNKNOWN`/quarantined.

### D5 — Management key and policy schemas

Align the management contract with SRS PRP-FR-003..009:

- Encode organization and owning principal/application, capability grants, model-alias grants, expiry, and quota-policy binding as validated fields. Replace unrestricted scope strings with the documented capability vocabulary; keep management permissions distinct from inference capabilities.
- Add reversible suspension semantics required by PRP-FR-006; revocation remains terminal. Every state mutation remains version-guarded and audited.
- Preserve one-time plaintext issuance while defining idempotency replay: the first successful response contains the secret; a replay returns a stable issuance receipt without plaintext and explicitly reports that the secret is unavailable. The operator must revoke/reissue if the first response was lost. Do not cache or recover the plaintext to satisfy replay.
- Keep key issuance and rotation responses separate from ordinary mutation receipts so the one-time-secret rule is machine-checkable.

## 4. Required document and generated-artifact updates after approval

1. Reconcile ADR-PRP-004 and ARCH-PRP §3/§11 with the conditional candidate-A binding and run 1 receipt; preserve the remaining candidate/DEV limitations.
2. Close ADR-PRP-002's authority decision for one PRP Admission authority, keeping implementation qualification separate.
3. Update `contracts/openapi/prp-worker.yaml`, `contracts/openapi/prp-management.yaml`, and API-PRP prose to the approved decisions above. Keep the client contract vendor-neutral unless a reviewed requirement proves otherwise.
4. Regenerate contract JSON twins and generated models from canonical YAML per ADR-PRP-013; do not hand-edit generated outputs.
5. Update contract/ADR versions and freeze metadata only after approval. Any breaking contract-version choice must follow API-PRP §10 and include a migration note.
6. Reconcile WP24's roadmap status to its approved receipt. Keep WP01 open until its scope/ownership receipt is approved; only then may WP03 be marked formally ready or completed.

## 5. Parent and peer impact

- Parent authority: PRD/SRS requirements remain normative; no requirement ID or product boundary changes are proposed.
- Peer contracts: worker target/epoch and readiness semantics; management key grants, suspension, and idempotency; security credential references and secret custody.
- Generated models and JSON are derived from canonical YAML. Tests and traceability may be updated after approval, but no acceptance test changes from `NOT_RUN` without execution evidence.
- Out of scope: service/backend implementation, PostgreSQL migrations, secret-store deployment, target-host access, runtime qualification, DEV deployment, and production activity.

## 6. WP03 acceptance and exit evidence

- WP01 scope/ownership receipt and WP24 run 1 selection receipt are linked and reconciled.
- Owner and Security approve D1–D5 or record explicit replacements.
- ADR-PRP-004/002, ARCH-PRP, API-PRP, canonical YAML, generated models/JSON, and traceability agree on the same decisions.
- Contract generation and schema validation pass; no runtime acceptance claim is made.
- WP03 status changes only with the approved decision record. WP25/WP04 remain gated by WP03/RG0.

## 7. Proposed version diff

| Artifact | Current | Proposed after approval |
|---|---|---|
| WP03 proposal | — | `0.1.0-draft` |
| `prp-worker.yaml` | `0.4.0-draft` | First frozen revision; select version under API-PRP §10 after reviewing the breaking runtime-epoch and target-binding changes |
| `prp-management.yaml` | `0.4.0-draft` | First frozen revision; select version under API-PRP §10 after reviewing key-schema/idempotency changes |
| `prp-client.yaml` | `0.3.0` | No change proposed |
| ADR-PRP / ARCH-PRP / API-PRP | `0.4.0-draft` | Update only the affected decision and contract prose; preserve unrelated open decisions |

## 8. Owner review

The repository owner approved D1–D5 on 2026-09-29 in the task conversation. WP01 scope/ownership closure must also be recorded before WP03 is marked formally ready. Apply the approved documentation and contract changes, regenerate derived artifacts, and run the required documentation/schema checks. Runtime implementation remains a separate step.
