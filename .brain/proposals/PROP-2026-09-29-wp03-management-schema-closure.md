---
document_id: PROP-2026-09-29-WP03-D6
title: "WP03 D6 management schema closure proposal"
version: 0.1.0-draft
status: approved
created_at: 2026-09-29
complexity: C-3
risk: HIGH
implementation_status: COMPLETE
owner_decision: APPROVED_WITH_REMAINING_CHOICES_DELEGATED_ON_2026-09-29
---

# WP03 D6 management schema closure proposal

## 1. Purpose and boundary

Record the D6 management-contract decisions approved by the repository owner on 2026-09-29, plus the owner's later instruction to decide the remaining contract details. D6 closed the management policy lifecycle, quota composition/window behavior, deployment-ceiling boundary, and key-rotation semantics while the contract was DRAFT. WP01 scope/ownership and the separate WP03 formal freeze were approved on 2026-09-30; see [the formal freeze receipt](PROP-2026-09-30-wp03-formal-contract-freeze.md).

The repository owner approved the scoped D6 recommendations and later delegated the remaining design choices on 2026-09-29. The selected decisions, application, and verification are recorded below.

## 2. Evidence and authority status

- The approved WP03 D1–D5 proposal records WP01 scope/ownership evidence as missing and leaves the three management items open: [PROP-2026-09-29-wp03-contract-authority-freeze.md](PROP-2026-09-29-wp03-contract-authority-freeze.md).
- As of the D6 review on 2026-09-29, [SRS-PRP.md](../../docs/SRS-PRP.md) PRP-FR-004 required separate platform-operator, organization-admin, member, and application-service roles; administrators cannot exceed delegated grants, and operators have no default content-read privilege. PRP-FR-006 requires bounded rotation overlap and specifies a 24-hour default that can be reduced. PRP-FR-008 names request, token, audio-second, active/queued-job, and storage budgets. WP01 later approved the SRS baseline on 2026-09-30.
- [SECURITY-DATA-PRP.md](../../docs/SECURITY-DATA-PRP.md) §4 already contains the role/action matrix; §5 contains retention targets. Its front matter also remains `draft-for-review`, and §5 calls the targets proposed policy rather than a compliance assertion.
- [API-PRP.md](../../docs/API-PRP.md) §8 requires role plus scope, optimistic version checks, idempotency where retryable, and redacted audit. Its management-freeze paragraph identifies the fields and role/rotation decisions still to be frozen.
- Before D6, [prp-management.yaml](../../contracts/openapi/prp-management.yaml) authenticated through `OperatorSession` or `OperatorKey` and left policy settings untyped. D6 applies typed quota/retention fields, a typed organization/subject scope, and the resource lifecycle decisions in §5.3.
- No WP01 scope/ownership receipt was found in `.brain/` during this review.

At the D6 review time, the SRS and SECURITY-DATA baselines were drafts. WP01 approved the PRD/SRS baseline on 2026-09-30; SECURITY-DATA remains `draft-for-review`, and that approval does not change its status.

## 3. Approved management authorization contract

1. Adopt the action matrix in `SECURITY-DATA-PRP.md` §4 without changing its permissions. Every management operation evaluates the authenticated actor's role and the requested organization/object scope against that matrix.
2. `OperatorSession` remains the interactive console credential with CSRF protection. `OperatorKey` remains an automation credential. Authentication scheme alone grants no role or scope; the resolved actor record supplies explicit, non-escalating role and scope for either credential.
3. Content reads remain grant-based. A platform-operator role alone grants metadata access only where the matrix permits it; reading raw audio, prompts, transcripts, or artifact content requires an explicit data grant.
4. Denied operations return the existing `403` contract and create the redacted audit evidence required by API-PRP §8.

The owner approved the referenced role/action matrix as the WP03 baseline on 2026-09-29. D6 also records the platform operator's deployment ceiling as versioned operator configuration outside the management API. `SECURITY-DATA-PRP.md` remains `draft-for-review`; this decision does not change that source document's status.

## 4. Approved key-rotation overlap contract

Add an optional `overlap_seconds` integer to the rotate-key request:

- Omitted value defaults to `86400` seconds (24 hours).
- Valid range is `1..86400`; the caller may shorten, but never extend, the overlap.
- The old verifier remains valid only for the requested interval and then becomes unusable. A separate revoke operation remains immediate and terminal.
- Rotation continues to return the new plaintext secret only on the first successful response. A replay with the same idempotency key and canonical payload returns the existing non-secret receipt before rechecking `If-Match` or current-key eligibility; it never resurrects either key or restarts/extends overlap. A different canonical payload with that key, including a changed `overlap_seconds`, returns `409 IDEMPOTENCY_CONFLICT`.

This makes the SRS default and maximum machine-checkable. Only active, unexpired keys may rotate; suspended, revoked, and expired keys cannot rotate. The new key inherits the old key's organization, subject, capabilities, model aliases, quota policy, label, and exact `expires_at`. The old verifier becomes unusable at the earlier of its original expiry and rotation time plus `overlap_seconds`; a null original expiry is bounded by the overlap deadline. Rotation never extends expiry or grants.

## 5. Approved typed policy fields and resource lifecycle

### 5.1 Quota settings

Replace the unrestricted quota `settings` object with a closed schema containing the resource dimensions in PRP-FR-008:

```yaml
requests:
  limit: integer
  window_seconds: integer
tokens:
  limit: integer
  window_seconds: integer
audio_seconds:
  limit: integer
  window_seconds: integer
active_jobs: integer
queued_jobs: integer
storage_bytes: integer
```

- All values are non-negative integers; each `window_seconds` is positive. Zero means no capacity for that dimension. The explicit window prevents implicit daily/hourly reset assumptions.
- `window_seconds` defines a trailing rolling interval `(now - window_seconds, now]` using the PRP admission authority's timestamp; events exactly at the lower boundary are excluded.
- Requests, token, and audio reservations count immediately. Settlement replaces a reservation with actual usage at the original admission time; unavailable actual usage retains the conservative reservation until it ages out. If actual usage exceeds its reservation, record the actual amount and deny new admissions until the interval permits them.
- The full settings object replaces the prior settings under the existing `If-Match` version guard; omission is not treated as unlimited or as an implicit unchanged field.
- Admission must pass both applicable organization and principal/application policy limits atomically. Multiple keys for one subject share the subject counters, preserving PRP-FR-008's no-bypass requirement, with reserved/actual/estimated/unavailable usage kept distinct.

The approved policy scope requires `organization_id` and may include a typed subject object with `subject_type` `principal` or `application` plus `subject_id`; absence of the subject means organization-wide policy. Exactly one policy exists for each `(policy_kind, canonical scope)`. Organization policies apply to all subjects in that organization. Subject policies apply to all keys for that principal/application, whose counters are shared so creating additional keys cannot increase the budget. Both scopes must pass atomically. `quota_policy_id` is the stable resource ID of the key's exact subject quota policy; it is not a separate per-key counter. Create the subject policy before issuing keys.

### 5.2 Retention settings

Replace the unrestricted retention `settings` object with named duration fields, all expressed in integer seconds or days as named. The approved initial values come from the draft SRS and Security Data inventory:

| Field | D6 default | D6 bound / rule | Source |
|---|---:|---|---|
| `async_payload_terminal_ttl_seconds` | 86400 | at most 86400 after terminal | SRS pilot defaults; Security Data §5 |
| `async_payload_max_age_seconds` | 172800 | absolute maximum age 48h | SRS pilot defaults; Security Data §5 |
| `raw_audio_max_age_seconds` | 86400 | absolute maximum age 24h | SRS pilot defaults; Security Data §5 |
| `generated_audio_retention_seconds` | 604800 | default 7d; earlier deletion always allowed | SRS pilot defaults; Security Data §5 |
| `job_usage_audit_metadata_retention_days` | 90 | default 90d; may be shortened | SRS pilot defaults; Security Data §5 |
| `operational_log_retention_days` | 30 | default 30d; logs remain redacted | SRS pilot defaults; Security Data §5 |
| `share_grant_max_ttl_seconds` | 86400 | also bounded by artifact expiry | SRS pilot defaults; Security Data §5 |

`backup_retention` is excluded: the security document labels its 30-day value proposed and requires production review. Only values explicitly identified above as a maximum are hard schema bounds; the other durations are defaults and may be changed by policy. Authorized deletion may shorten any retained object.

The SRS also requires dedupe records to remain available for at least the job horizon plus 24 hours. This is a fixed retention invariant outside `RetentionPolicySettings`, not an editable policy field.

### 5.3 Request shape and validation

Define separate `QuotaPolicySettings` and `RetentionPolicySettings` schemas and a common `PolicyWrite` body. Policy resources are unique by `(policy_kind, canonical scope)`: organization scope is `organization_id` alone; subject scope adds `subject_type` and `subject_id`.

- `POST /prp/admin/v1/policies/{policy_kind}` creates the unique scope resource with `Idempotency-Key`; the `201 MutationReceipt.resource_id` is stable and its opaque `version` is the initial version. Replays return the original receipt; a different key targeting an occupied scope returns `409 POLICY_EXISTS`.
- `GET` on that path reads by `organization_id` plus either both subject query fields or neither. It returns `PolicyResource` with the same stable ID and current opaque version.
- `PATCH` updates an existing resource only, requires its scope and current `If-Match`, replaces all settings, and returns the next opaque version in `MutationReceipt`. The route cannot create or change identity. Policy resources are not deleted by this API.
- A key's `quota_policy_id` must identify a quota policy for that exact organization and subject. Organization quota policy, when configured, composes with the subject policy. Deployment-wide quota ceilings remain in versioned platform-operator configuration outside this HTTP API; organization policy mutations above that ceiling fail with `403 POLICY_DENIED`.

## 6. Parent/peer impact and scope boundary

- Parent sources: PRP-FR-004, FR-006 and FR-008; SECURITY-DATA-PRP §4–5; API-PRP §8. No requirement ID changes are proposed.
- Peer contract: `prp-management.yaml` and matching API-PRP prose. JSON and four generated Python modules are derived outputs from canonical YAML.
- No client contract or worker contract change is proposed.
- Out of scope: implementing authorization, quota accounting, retention enforcement, database migrations, production policy values, DEV deployment, and production activity.

## 7. Acceptance and exit criteria for D6

- Owner approved the role matrix baseline and `OperatorSession` / `OperatorKey` mapping on 2026-09-29.
- Owner approved per-rotation overlap with a 24-hour default and maximum on 2026-09-29.
- Owner approved typed quota dimensions, principal/application scope and strictest applicable budget composition, explicit window duration, and full-settings replacement semantics on 2026-09-29. The owner later delegated the remaining choices; this proposal records stable policy identity/lifecycle, shared subject counters, trailing rolling-window accounting, and the deployment-ceiling boundary.
- Owner approved the retention fields, explicit maxima, and default-only values as written in §5.2 on 2026-09-29.
- Canonical YAML, API-PRP prose, JSON twin, and generated Pydantic models agree; contract/schema/example/documentation checks pass.
- **D6 complete:** policy identity/provision/read/version semantics and `quota_policy_id` binding; deployment-wide quota-ceiling disposition; key-rotation grant/expiry/eligibility semantics; quota-window rolling/accounting behavior.
- **WP03 freeze:** approved on 2026-09-30; see the formal freeze receipt. **Still open before RG0 implementation entry:** WP02 hardware/runtime inventory and remaining owner/security evidence. D6 does not authorize application implementation, DEV deployment, or production release.

## 8. Applied changes and verification

1. Added `KeyRotationRequest.overlap_seconds` with an optional request body, a 1–86400-second range, and a 86400-second default. Replay does not restart or extend the overlap; immediate revocation remains separate.
2. Replaced opaque policy settings with closed quota and retention schemas; added policy create/read/update semantics, unique `(kind, scope)` identity, stable IDs and opaque versions; bound each key to its exact subject quota policy and shared subject counters.
3. Clarified that both management authentication schemes resolve an actor and then apply the same role/action matrix; neither credential alone grants a role.
4. Updated API-PRP prose and regenerated the management JSON and derived Pydantic modules. The public client contract and worker contract did not change in D6.
5. Kept management contract metadata at `0.4.0-draft`, `DRAFT`, freeze gate `WP03` while D6 was applied; the later formal WP03 freeze approved version `0.4.0` / `FROZEN` with route and schema shapes unchanged.
6. Verification passed: JSON export check (3 contracts); generated-model check (4 modules); example validation (3 examples); documentation validation (626 relative links, 327 OpenAPI references, 0 errors). All 92 runtime acceptance cases remain `NOT_RUN`; no application tests, runtime exercise, DEV deployment, or production activity was performed.

## 9. Version diff

| Artifact | Before D6 | After D6 |
|---|---|---|
| D6 proposal | `0.1.0-draft`, draft-for-review | `0.1.0-draft`, approved; D6 contract slice complete |
| `prp-management.yaml` / JSON | `0.4.0-draft`, `DRAFT`, gate `WP03` | Added policy GET/POST, closed lifecycle/quota/rotation semantics; version and freeze metadata unchanged |
| Generated management models | D1–D5 shapes | Regenerated from canonical YAML; no independent version |
| Public client contract | `0.3.0` | Unchanged |
| Worker contract | `0.4.0-draft`, `DRAFT`, gate `WP03` | Unchanged in D6 |

## 10. Delegated decision record

The repository owner explicitly delegated the remaining choices on 2026-09-29. The selected defaults and rationale are:

| Decision | Selected behavior | Rationale |
|---|---|---|
| Policy identity and lifecycle | One resource per `(policy_kind, canonical scope)`; `POST` creates, `GET` reads by scope, `PATCH` replaces under `If-Match`; stable `resource_id`, initial/current opaque version in receipts/read response | Preserves scope-oriented updates, makes `quota_policy_id` resolvable, and avoids a second identity system |
| Quota policy binding | Each key references its exact subject policy; all keys for that subject share counters; organization policy also applies when configured | Prevents extra keys from increasing the principal/application budget and matches PRP-FR-008 |
| Deployment ceiling | Versioned platform-operator configuration outside the management API; over-ceiling organization policy writes return `403 POLICY_DENIED` | Keeps deployment capacity control outside organization-scoped policy resources |
| Quota windows | Trailing rolling interval with reservations counted at admission; settlement uses actual usage at the original admission time; unknown actual usage retains the reservation through expiry | Avoids boundary bursts and treats unavailable usage conservatively |
| Key rotation | Only active, unexpired keys rotate; new key inherits exact grants and expiry; old verifier overlap is capped by old expiry | Rotation changes the secret without increasing privilege or extending key lifetime |

## 11. Owner review

The owner approved the scoped D6 recommendations and delegated the remaining design choices on 2026-09-29. D6 is complete as a documentation/contract slice. WP01 scope/ownership and the WP03 formal contract freeze were approved on 2026-09-30. RG0, application implementation, runtime acceptance, DEV, and PROD remain separate gates.
