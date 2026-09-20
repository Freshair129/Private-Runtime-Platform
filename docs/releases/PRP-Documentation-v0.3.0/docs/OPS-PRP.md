---
document_id: OPS-PRP
title: "Operations | Deployment, Recovery & Release Runbooks"
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

# Operations | Deployment, Recovery & Release Runbooks

**PRP — Private Runtime Platform | v0.3.0 | 2026-09-20 | Draft for review**

เอกสารที่เกี่ยวข้อง: [Roadmap](ROADMAP-PRP.md) · [SRS](SRS-PRP.md) · [Tests](TEST-PRP.md)

## 1. Operational prerequisites
Confirm exact host/GPU/CPU/RAM/OS/driver, private network reachability, available disk, time synchronization and recovery access. Record runtime image/model/profile/voice revisions and license receipts. No production command or credential is provided in this draft; version-pinned manifests are implementation deliverables.

P1-A deploy control application + PostgreSQL + private worker adapters and two independent vLLM nodes. Console and reference client use public contracts only. Speech worker joins only after model/rights/placement qualification. Do not install full Lalin Studio or expose its broad route set as PRP voice API.

## 2. RB01 Bootstrap and access
Create the first operator through isolated local bootstrap flow; no shared default password or permanent bootstrap token. Configure org/team/service principals. Issue least-privilege test keys and prove wrong/missing/revoked key rejection. Export redacted policy manifest and store recovery material separately.

Exit: clean installation works without Zuri or application databases; client cannot reach raw worker/admin ports; key verifier storage and operational logs pass secret scan.

## 3. RB02 Enroll and qualify A/B
Register allowed origin, physical GPU identity, runtime identity, credential reference and desired profile. Validate endpoint identity, auth negative cases, model metadata and small synthetic generation. Measure one invocation then controlled concurrency/context levels. Bind qualification receipt to exact config/model/credential epochs.

Mark READY only after measurement and current observation. Registering a second URL of A does not add budget. A and B can have different limits under the same semantic profile. Record cold and warm metrics separately.

## 4. RB03 Speech residency qualification
Test CPU placement first as candidate, not assumed acceptable. Test B GPU sharing only with explicit resident envelope including LLM model/KV reservation plus ASR/TTS peak usage. Validate workload W3. TTS completion does not automatically unload cached weights.

If target fails: reduce context/model budget via approved change, choose another speech profile, or explicitly change deployment mode. A speech-only B changes the two-chat-replica baseline and must be visible in model catalog/ops status. No automatic stop/unload of LLM to hide lack of memory.

## 5. RB04 Saturation and node failure
Inspect freshness/profile/grants before interpreting GPU utilization. When A unavailable, stop new dispatch to A, fence its unknown attempts, and route only new eligible work to B. When both unavailable, bounded reject/timeout. A dead dashboard is not a dead observer; a dead observer makes observation stale and blocks unsafe admission.

Never clear lease rows because they look old. Follow RB05 for uncertain execution.

## 6. RB05 UNKNOWN execution reconciliation
Identify request/job/attempt/runtime epoch and pre/post-dispatch evidence. If no send can be proven, release reservation with receipt. If runtime reports finished, validate settlement fence, meter once, discard unauthorized/late output and release invocation lease. If running or no proof: quarantine resource and prevent new conflicting jobs.

A pre-authorized supervisor may terminate runaway process under a recorded policy. Verify actual termination, requalify any reset runtime and preserve model-residency ledger correctness. Database TTL or client cancel ACK never substitutes for termination proof.

## 7. RB06 Delete, revoke and artifact leakage
Revoke exposed key/grant; apply object tombstone; prevent new publish/read and fence running result. Cleanup PRP bytes/temp/cache references according to policy. Do not claim third-party copies vanished. Reconcile erasure ledger before any restored database serves traffic.

Investigate with IDs/metadata, not raw audio unless approved diagnostic grant exists. Resetting the whole storage volume is not a permitted cleanup shortcut.

## 8. RB07 Disaster backup/restore
Backup DB configuration, durable jobs/attempts/usage/audit/erasure, profile manifests and policy-selected artifact bytes. Keep recovery encryption keys separate. Test host-disaster RPO<=24h and RTO<=4h targets in isolated environment before production; process-restart durability is a different invariant.

Restore sequence: isolate traffic -> verify backup checksum/key -> restore schema/state -> replay erasure/tombstones -> mark node bindings DISABLED -> reconcile unknown attempts and quota holds -> requalify engines/current secrets -> run canary -> reopen admission -> record evidence. No restored stale grant or deleted artifact may become readable before reconciliation.

## 9. RB08 Release/canary/rollback
Release packet includes commit/image/schema/profile hashes, migration compatibility, test evidence, limits, known risks and rollback approver. Canary uses synthetic or authorized non-sensitive requests in one scope. Gradual activation per capability, not global switch.

Rollback voice flag/adapter without changing chat data policy; keep unresolved attempts until settled. Prefer additive forward-safe migrations; no down migration that drops audit/leases or active job data. Channel adapter rollout is separate; never create a second LINE sender.

## 10. RB09 External LINE handoff
Integration owner holds channel credentials and outbox. Verify signature/dedupe/ACK under storage failure, reply lifetime and delayed push authorization. Keep native audio share grants bounded and consented; record playback tests on actual approved devices. Distinguish API acceptance from delivery/read [SRC-04..06].

PRP core can pass G3 while LINE gate is blocked for missing credentials. Report this split explicitly; do not edit production webhook or issue push messages without owner authorization.

## 11. SLO/alert reporting
Track success/error/timeout/rejection count beside percentiles; report cold model load separately. Key dashboards: readiness and observation age; queue/resource held/quarantined/resident; per-profile TTFT/RTF; artifact/disk/cleanup; auth/secret rotation; uncertain jobs and dead-letter/outbox.

Notifications have configured/delivered/failed states and dedup; NOT_CONFIGURED is not notified. Prometheus/Grafana optional; correctness relies on observer+database, not dashboard rendering.

## 12. Evidence packet schema
Every run records evidence_id, requirement/test IDs, exact commit/image/profile/runtime/driver/hardware, start/end, workload version, sample count, metrics/error distribution, pass/fail/blocked reason, logs path (redacted), operator/reviewer and rollback references. Templates in registry/evidence-template.json contain no fabricated measurements.

## 13. RB10 Framework evaluation and selection
Before implementation freeze, run WP24 using isolated configurations for A and B with the same model revision, context and synthetic workload. Record Python/runtime/image versions, topology, runtime count, key/permission semantics, actual resource binding, persistence and retry settings. C-Ray is optional only with a recorded trigger.

Publish fit-gap and evidence in registry/stack-evaluation-template.json after copying it to a real run record. The supplied template is NOT_RUN. No score replaces mandatory gates; model/cancellation/permissions failure is a blocker even if setup is convenient. Source-read facts and measured results must remain separately labeled.

## 14. RB11 Python environment and launch boundaries
Establish independent locked control, LLM and speech environments or pinned vendor images. Select exact compatible Python/CUDA/driver versions from a clean install, not the latest version by assumption. Proposed uv workflow verifies lock freshness before install; do not auto-upgrade in startup [SRC-16].

Start persistence/secret access, then selected manager/supervisor privately, then qualified runtimes, then admission-enabled API. Readiness stays false until auth/profile/load checks pass. Increase only API workers during AT089 and verify model PID/residency counts do not increase. Do not use developer reload mode in serving qualification.

A runtime service has one lifecycle owner. Operator drain/restart goes through that owner; application exceptions never launch an extra supervisor. Replacing a framework must preserve unknown-attempt and erasure ledgers, not merely restore the previous process count.

## 15. RB12 Native retries, relocation and key migration
Inventory every retry/restart/fallback mechanism (client SDK, gateway, manager, engine, worker). Disable unaccounted generation retries. Delayed/uncertain compute keeps reservations fenced until verified termination/reconciliation; exact-once execution is not guaranteed by a retry library.

Map a delegated job to physical runtime epoch before compute, and check mapping again before settlement. Unexplained relocation disables that profile. Keep backup/restore ownership for both PRP state and delegated state; deployment-wide recovery does not assume their snapshots are transactionally simultaneous.

Export declarative policy/profile bindings through supported APIs. Do not export raw keys or copy a vendor database blindly. When non-recoverable key verifiers cannot migrate, schedule authorized rotation and disclose client credential changes; public request schemas remain unchanged.
