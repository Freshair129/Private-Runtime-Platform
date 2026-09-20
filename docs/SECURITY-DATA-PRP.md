---
document_id: SECURITY-DATA-PRP
title: "Security & Data | Trust, Privacy and Failure Boundaries"
product: PRP - Private Runtime Platform
version: 0.3.0
status: draft-for-review
created_at: 2026-09-20
language: th-TH
source_authority: authored-proposal
implementation_status: NOT_IMPLEMENTED_IN_THIS_DELIVERY
runtime_verification: NOT_RUN
repository_integration: NOT_PERFORMED
---

# Security & Data | Trust, Privacy and Failure Boundaries

**PRP — Private Runtime Platform | v0.3.0 | 2026-09-20 | Draft for review**

เอกสารที่เกี่ยวข้อง: [SRS](SRS-PRP.md) · [API](API-PRP.md) · [Ops](OPS-PRP.md) · [Tests](TEST-PRP.md)

## 1. Security posture
Private means controlled identity/network/data boundary, not automatic confidentiality merely from self-hosting. P1 prohibits third-party inference fallback. LINE is outside the private compute boundary and can receive content by caller policy. Host/root operators remain trusted; no hardware attestation or hostile co-tenant isolation claim.

Threat model assets: client keys/upstream credentials, prompts/transcripts/audio, job state, result grants, GPU capacity, model profiles and audit/erasure evidence. Actors: legitimate members/apps, compromised low-scope app, unauthenticated LAN caller, malicious payload, stale worker, mistaken operator, external content provider.

## 2. Trust boundary table
| Boundary | Identity | Allowed data | Main risks/controls |
|---|---|---|---|
| Client -> API | user/service key or console session | bounded text/audio/correlation | spoofed org, quota abuse; verified auth/object grants |
| Console -> management | operator/org admin session | versioned config | CSRF/escalation; least privilege + audit |
| PRP -> worker | service identity/private TLS | scoped payload + profile/attempt | rogue endpoint/SSRF; origin allowlist + epoch qualification |
| Worker -> artifact | scoped grant | authorized input/output | storage traversal; UUID/sandbox/short TTL |
| Artifact -> third party | explicitly minted grant | one bounded artifact | link disclosure; revoke/TTL/no-PII policy |
| PRP -> diagnostics | telemetry identity | redacted operational metadata | content leakage; default omission and bounded opt-in |

## 3. STRIDE-inspired threat register
| ID | Threat | Scenario | Required mitigation | Evidence |
|---|---|---|---|---|
| TH01 | Spoofing | caller supplies another org_id | identity from key only | AT003/004 |
| TH02 | Tampering | stale worker writes result after delete | epoch/tombstone/CAS | AT020/041 |
| TH03 | Repudiation | unaudited key/capacity change | immutable audit metadata | AT047 |
| TH04 | Information disclosure | global job list or guessed artifact | object ACL/scoped queries | AT038/039 |
| TH05 | Denial of service | oversized audio/decoder bomb | stream limits/sandbox/deadline | AT029/030 |
| TH06 | Elevation | inference key invokes admin | separate roles/routes | AT004/005 |
| TH07 | SSRF | node origin targets metadata/internal admin | verified allowlist/DNS/redirect block | AT010/077 |
| TH08 | Resource duplication | alias URLs count same GPU twice | physical identity/residency ledger | AT013/018 |
| TH09 | Ambiguous execution | timeout releases slot while GPU running | unknown execution/quarantine | AT020/021 |
| TH10 | Secret/content logging | debug dumps body/env | redaction/default no payload | AT047/082 |
| TH11 | Supply chain | untrusted model code auto executes | pinned reviewed assets/manifest | AT084 |
| TH12 | Voice rights | arbitrary uploaded clone reference | preset allowlist/rights receipt | AT033/081 |

Labels identify analysis categories, not a certification. Exact tests use full PRP-AT IDs in TEST-PRP. Every threat maps to at least one normative requirement; changes update trace and diagram D20.

## 4. Role/action matrix
| Action | Member | App service | Org admin | Platform operator |
|---|---|---|---|---|
| Invoke granted model | granted | granted | own grant | own grant only |
| Read/cancel own job | granted | granted | only delegated data grant | metadata by ops role; content explicit |
| Read other's artifact | no default | no default | explicit grant only | explicit grant only |
| Create member/app key | no | no | within org grant | bootstrap/platform policy |
| Raise own org quota | no | no | within delegated ceiling | deployment ceiling control |
| Register/drain node | no | no | no default | yes |
| Approve model/voice | no | no | request only | technical/license approval workflow |
| Export usage/audit | own metadata | own metadata | scoped org | scoped operations |

Service user tags do not grant membership. Team sharing needs explicit team grant and current membership on each read. Secret references must not be serialized into a public model listing.

## 5. Data inventory and retention
| Data class | Storage form | Default retention | Owner |
|---|---|---|---|
| Sync prompt/answer | memory; no content logging | request lifetime | calling app owns long-term copy |
| Async content payload | encrypted DB/blob ref | 24h after terminal; max48h age | PRP Job service |
| Raw/orphan audio | private object/file | max24h age | PRP Artifact service |
| Generated audio | private object/file | 7d age or earlier delete | PRP Artifact service |
| Job/usage/audit metadata | DB, no raw content | 90d | PRP |
| Operational logs | redacted bounded logs | 30d | PRP Ops |
| Client key | verifier + prefix | grant lifecycle; revoke tombstone | Identity |
| Worker secret | encrypted secret store reference | explicit rotate/revoke | Operator |
| Share grant | hashed token/grant metadata | <=24h and artifact expiry | Artifact service |
| Backup | encrypted policy-selected snapshot | proposed 30d rotation; review before production | Operations |

Targets are proposed policy, not a legal compliance assertion. Backup retention may outlive active objects; erasure tombstone ledger must be available to restore and block deleted data before serving. Copies already delivered to third parties are outside PRP erasure guarantee and must be disclosed.

## 6. Data lineage
Artifact lineage tracks original checksum -> normalized audio -> ASR result -> caller-owned answer reference -> TTS artifact. PRP does not reconstruct a business conversation from lineage. A caller correlation can join operations for its own authorized workflow, not read another app's transcripts.

Filename/content hash alone cannot authorize cross-user reuse. Deduplication and cache reuse must be scoped to authorized boundary. Prefix caching must be disabled or use release-tested isolation that does not replace authorization.

## 7. Incident handling
Contain: stop new admission for affected key/profile/node without destroying evidence. Assess: inspect redacted request/attempt/epoch/lease and content-access grants. Reconcile: verify running tasks stopped before resource release. Recover: rotate secrets, requalify bindings, clear unauthorized grants and verify deletion fences. Close: record impact, actions and rollback evidence, not raw customer content.

No autonomous GPU restart, process-kill or filesystem cleanup of unrelated apps is authorized by an alert. Emergency supervisor termination must be configured/approved beforehand and produce evidence of actual termination.

## 8. License/provenance gate
Review code license, model weights, tokenizer/vocoder, voice asset and intended commercial/internal use separately. Model card claims are input evidence, not legal certification. Candidate F5 Thai model card describes Thai/English and limitations on long/some words [SRC-08]; this does not waive quality/voice-rights tests.

Download/install can have approved egress in provisioning; inference should use staged pinned assets without implicit model downloads or telemetry. Signature/checksum mismatch blocks readiness.

## 9. Framework delegation and Python isolation
Keep FR-005 verifier-only user keys unchanged. Xinference authentication documentation checked for this revision describes encrypted stored keys and reveal operations; this is not equivalent to a non-recoverable key verifier. Use a conforming client-key authority or record a blocker; Xinference may still be evaluated for internal lifecycle under separately protected service credentials [SRC-10]. Do not duplicate every user's key into another service.

Vendor bootstrap/admin/model-install/debug/RPC routes stay private, distinct from inference API. Complete first-admin setup on an operator-only network before wider access. A framework exposing encrypted/reveal-able internal credentials does not authorize those routes or credentials to inference clients. External identity headers are stripped and reconstructed from trusted verification.

One physical-admission contract across framework and custom voice workers; vendor retry, failover and relocation cannot escape leases. Reconcile vendor job IDs/epochs without reading or writing undocumented vendor tables. Root/host access remains privileged, so framework adoption is not hostile co-tenant isolation.

Control API does not ship model weights and avoids ML import side effects. Per-runtime lock/image/dependency scans and staged model assets apply to the complete dependency tree; model remote code/plugin execution denied unless separately reviewed. Provisioning downloads are distinguished from offline inference. Pinning alone is not a security audit.

Additional threat evidence: TH13 (recoverable client-key mismatch) -> AT005/091; TH14 (hidden vendor reroute/retry) -> AT018/020/091; TH15 (API process multiplies resident models) -> AT089/090. Existing TH01..12 remain in force.
