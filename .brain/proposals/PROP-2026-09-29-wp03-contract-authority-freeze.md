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

Record WP03's contract, authority, and secret-custody decisions approved by the repository owner on 2026-09-29. That scoped approval was not itself a formal WP03 freeze, runtime implementation approval, server-access approval, or production release approval. The separate WP03 formal freeze was approved on 2026-09-30 and is recorded in [the freeze receipt](PROP-2026-09-30-wp03-formal-contract-freeze.md). No application code or acceptance-test status changes are included.

## 2. Verified entry evidence

- WP24 run 1's decision receipt is approved on 2026-09-24, selects candidate A (Xinference-managed runtimes) on capability evidence, and explicitly states that its approval satisfies the WP24 gate for WP03. It records nine conditions and names PRP as the client-key authority. Source: `docs/evidence/wp24/WP24-2026-09-20-run1.json`.
- WP24 run 2 was measurement-only under the owner's instruction. It did not alter run 1's selection or acceptance statuses. DEV-07 was narrowed to DEV-09; cache-derived capacity figures are not a like-for-like A/B comparison because the vLLM builds differ. Source: `docs/evidence/wp24/WP24-2026-09-24-run2/A/FINDINGS.md` and `docs/CHANGELOG-PRP.md`.
- The roadmap records WP24 implementation as `NOT_STARTED`, while its approved run 1 decision receipt explicitly satisfies the WP24 decision prerequisite for WP03. At the time of this proposal, WP01 and formal WP03 freeze were pending; both owner decisions were later recorded on 2026-09-30 in their respective receipts.
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
- `runtime_epoch` is the adapter-reported token: runtime-provided when available, otherwise synthesized by the adapter per ADR-PRP-014 and recorded with its derivation.
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

## 4. Applied document and generated-artifact updates

1. Reconciled ADR-PRP-004 and ARCH-PRP §3/§11 with the conditional candidate-A binding and run 1 receipt; retained DEV-09 and exact runtime-profile qualification as open limitations.
2. Recorded ADR-PRP-002's approved single PRP Admission authority boundary; implementation and PostgreSQL/fault qualification remain `NOT_RUN`.
3. Updated worker and management YAML and matching API-PRP prose to D1–D5; D6 later completed the approved and owner-delegated management policy lifecycle, quota, and rotation decisions. The public client contract remains unchanged.
4. Regenerated JSON twins and all four generated model modules from canonical YAML per ADR-PRP-013.
5. Kept worker and management contracts at `0.4.0-draft`, `x-prp-status: DRAFT`, `x-prp-freeze-gate: WP03` through the D1-D6 review. The owner later approved the first frozen `0.4.0` baseline with unchanged route families; external consumer inventory remains unverified and is recorded in the freeze receipt.
6. Reconciled the roadmap and DAG to the approved WP24 and WP01 receipts. WP03 is now decision-complete; RG0 remains a separate implementation-entry gate with WP02 hardware/runtime inventory still pending.

## 5. Parent and peer impact

- Parent authority: PRD/SRS requirements remain normative; no requirement ID or product boundary changes are proposed.
- Peer contracts: worker target/epoch and readiness semantics; management key grants, suspension, and idempotency; security credential references and secret custody.
- Generated models and JSON are derived from canonical YAML. Tests and traceability may be updated after approval, but no acceptance test changes from `NOT_RUN` without execution evidence.
- Out of scope: service/backend implementation, PostgreSQL migrations, secret-store deployment, target-host access, runtime qualification, DEV deployment, and production activity.

## 6. WP03 acceptance and exit evidence

- **Satisfied:** WP24 run 1 selection receipt is linked and reconciled; WP01 scope/ownership receipt was approved on 2026-09-30; owner approved D1–D6 and delegated the remaining management design choices; ADR-PRP-004/002/014, ARCH-PRP, API-PRP, SECURITY-DATA-PRP, canonical YAML, generated models/JSON, and roadmap/DAG agree on the recorded decisions; contract generation, example validation, documentation validation, and generated-artifact drift checks pass.
- **WP03 freeze:** approved on 2026-09-30; see the formal freeze receipt. **Open before RG0 implementation entry:** WP02 hardware/runtime inventory and remaining owner/security evidence; WP25/WP04 remain behind RG0. All 92 runtime acceptance cases remain `NOT_RUN`.

## 7. Version diff for this approved work

| Artifact | Before this work | After this work |
|---|---|---|
| WP03 proposal | — | `0.1.0-draft`, D1-D6 owner decisions approved; separate freeze receipt approved 2026-09-30 |
| `prp-worker.yaml` + JSON | `0.4.0-draft`, DRAFT, WP03 | `0.4.0`, FROZEN; route family and schema shape unchanged at freeze |
| `prp-management.yaml` + JSON | `0.4.0-draft`, DRAFT, WP03 | `0.4.0`, FROZEN; route family and schema shape unchanged at freeze |
| `prp-client.yaml` + JSON | `0.3.0` | Unchanged |
| ADR-PRP / ARCH-PRP / API-PRP | `0.4.0-draft` | Content updated; document versions unchanged |
| Generated Pydantic modules | Prior generated contract shapes | Regenerated from the updated canonical YAML; derived files have no independent version |

## 8. Owner review

The repository owner approved D1–D5 and the scoped D6 decisions, then delegated the remaining D6 design choices on 2026-09-29. WP01 scope/ownership and the WP03 formal contract freeze were approved on 2026-09-30. WP03 is decision-complete; RG0 implementation entry still awaits WP02 hardware/runtime inventory and remaining owner/security evidence. Runtime implementation remains a separate step.
