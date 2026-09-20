---
document_id: ARCH-PRP
title: "Architecture | PRP Boundaries & Runtime Design"
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

# Architecture | PRP Boundaries & Runtime Design

**PRP — Private Runtime Platform | v0.3.0 | 2026-09-20 | Draft for review**

เอกสารที่เกี่ยวข้อง: [SRS](SRS-PRP.md) · [API](API-PRP.md) · [ADR](ADR-PRP.md) · [Data & Security](SECURITY-DATA-PRP.md)

## 1. Architecture drivers
Independent install/runtime/release; one authority for physical resource admission; two heterogeneous LAN hosts; clip-based voice; explicit uncertainty; minimal disclosure; no automatic public-cloud inference; adapters replaceable without forcing client schema changes

ดู D01 context, D02 containers, D03 components/dependencies และ D04 deployment ภาพเป็น target design ไม่ใช่การค้นพบ service ที่ deploy แล้ว

## 2. Logical modules and ownership
| Module | Owns | Interface boundary |
|---|---|---|
| API Gateway | TLS ingress, authentication facade, schema limits, request correlation | public HTTP only; no direct GPU routing bypass |
| Identity & Policy | org/principal/team/grants, client-key verifier, RBAC | trusted auth context; no business entity import |
| Registry & Qualification | node/runtime/physical IDs, profile hashes, credentials refs, readiness evidence | operator-controlled enrollment; current epochs |
| PRP Router | eligible candidates and ranked route plan | select only; commit requires Admission |
| Admission Coordinator | atomic quota/queue/resource holds and fairness | DB transaction/leases keyed by physical resource |
| Execution & Jobs | attempt/outbox dispatch, sync/SSE/native jobs, fences and cancellation | worker adapters; no channel delivery |
| Artifact Service | uploads, TTL, lineage, grants/erasure | storage port; authorized reads only |
| Observer & Audit | normalized observations, usage/audit facts, alerts | critical observer independent of dashboard |
| Console / Reference Client | management UX / own demo voice-turn state | HTTP contracts only |
| Worker adapters | runtime invoke/result normalization and cancellation reporting | vLLM or headless speech engine; no product data |

Initial packaging proposal: one control-plane application with explicit modules plus worker/observer processes and database. This is not a mandate for ten microservices. Python-first direction อยู่ใน ADR-PRP-009; exact framework/versions ยังเลือกใน ADR-PRP-004 ตาม WP24 กล่องแต่ละกล่องอาจเป็น configuration/adapter ของเครื่องมือที่มีอยู่ ไม่ใช่ custom service ใหม่

## 3. Python-first baseline and reuse candidates
**Direction selected for this revision:** PRP-owned control/API/policy/adapters ใช้ Python; frontend React/TypeScript แยก optional client; Rust/Tauri ไม่เป็นข้อบังคับ Native kernels ของ third-party runtime ไม่ขัด Python-first

| Layer | First evaluation | Constraint |
|---|---|---|
| Thin control API | FastAPI + Pydantic candidate | validation/OpenAPI; no model loading in API processes [SRC-13] |
| Runtime lifecycle | A: Xinference supervisor/workers; B: independent services with existing process supervisor | evaluate exact versions; no hand-built loader/scheduler by default [SRC-09] |
| Initial LLM engine | vLLM independent A/B deployments | no cross-host tensor parallel / KV migration |
| Gateway keys and routing | selected conforming framework; LiteLLM optional | exactly one client-key authority; retries cannot bypass admission [SRC-03] |
| Speech runtime | faster-whisper / approved TTS; headless Lalin-derived adapter candidate | isolated environment, no full Studio/brain/fs/plugin routes |
| Distributed-serving alternative | Ray Serve / Serve LLM, candidate C | conditional trigger, not stacked on Xinference by default [SRC-11] |
| Persistence / artifacts | PostgreSQL proposed + storage port | logical ownership, not duplicate vendor key/model tables |
| Build quality | uv lock, Ruff, type checker, pytest proposed baseline | pin exact toolchain and compatible Python per service at G0 [SRC-16][SRC-17] |

การเลือก framework ยัง OPEN_FOR_G0_SELECTION; A/B spikes ใน WP24 ยัง NOT_RUN ชื่อ library ไม่ใช่ certificate ว่ารองรับ model/driver/voice ของเราแล้ว อ่าน [Stack Evaluation](STACK-EVALUATION-PRP.md) และ [Coding Standards](standards/Coding-Standards.md)

Xinference auth ที่อ่านมี encrypted/reveal-able API keys จึงไม่ถือว่าตรง FR-005 (non-recoverable client keys) โดยอัตโนมัติ ใช้เฉพาะ internal service credentials ได้เมื่อจำกัดสิทธิ์ หรือเลือก key authority ที่ผ่านข้อกำหนด; ห้ามลดเกณฑ์เพราะอยาก reuse [SRC-10]

## 4. Deployment on two computers
Control plane/database may co-locate on CPU of A with an independent service lifecycle. A and B each run a full compatible chat model instance. Speech is CPU-first qualification candidate or measured resident headroom on B; if neither meets targets, revise placement/model or explicitly change replica baseline. Do not silently turn B into speech-only and still claim two chat replicas.

Each host uses private management/worker ports; user clients only reach gateway. Remote teams use approved VPN/private TLS. LINE adapter has its own public webhook; optional artifact share ingress is separate and deliberately enabled. A public inbound tunnel does not establish route from a cloud app to LAN GPU by itself.

No public worker/admin/metrics, cross-host tensor parallelism, arbitrary dynamic model loader or Internet-exposed filesystem route in P1. Ray is not a baseline dependency; candidate C requires a separate G0 decision and private control/RPC network qualification. Exact ports are configuration values, not client-visible identities.

## 5. Resource model
PhysicalResource = host+GPU UUID (or verified host-local identity) / CPU pool. ModelResidency = runtime/profile/epoch + calibrated baseline memory held while model remains loaded. InvocationLease = slots + conservative token/workspace budget for the specific attempt. These are distinct objects; request completion releases InvocationLease, not ModelResidency.

Router reads authorized candidates and fresh observations, ranks preferred A then B, and asks Admission to reserve. Admission uses transaction locks/CAS and unique idempotency constraints across gateway processes. Candidate may become busy before reserve; retry candidate selection within remaining deadline, not send optimistically.

Admission does not estimate exact free tokens by nominal VRAM minus percentage. Budgets are measured profiles plus active reservations; engine metrics are pressure signals. Each multi-stage client operation asks for a new stage-specific reservation; ASR must not hold LLM slots while waiting.

## 6. Dispatch and failure model
DB transaction: create/confirm invocation, hold quota/queue/resources, write dispatch outbox with epoch. Dispatcher atomically claims record and marks DISPATCHING before network send. Failure in the claim/send ambiguity window is conservative UNKNOWN until evidence proves no send/termination; a second dispatcher must not blindly resend.

Provider execution is not transactional with PRP DB. Exactly-once compute is not promised. Each result must match invocation/attempt/runtime epoch and unrevoked content fence before settlement. Result accepted once; duplicate callback/poll result is ignored or reconciled, never double-metered.

State dimensionality: logical job outcome can be TIMED_OUT while execution UNKNOWN and lease QUARANTINED. Hard deadline is user experience bound; hard execution horizon is runtime/supervisor-enforced cessation bound. Database TTL alone cannot implement the latter.

## 7. Client-owned voice workflow
Independent playground and Zuri independently own ASR -> chat -> TTS flow. PRP native jobs are atomic ASR/TTS operations in P1, not business voice-turn jobs. Client persists answer before requesting TTS; TTS failure permits text fallback and TTS-only retry. Tools/RAG/memory and actions stay client-side, with app-specific authorization/confirmation.

Optional generic workflow/DAG execution is deferred. Do not ship a hidden `voice_turn` job kind that makes all apps depend on Zuri or on one agent framework.

## 8. Data model and consistency
Logical ERD D16/D17 is design-level. Core entities: Organization, Principal, TeamMembership, Application, AccessKeyGrant, Pool, PoolGrant, Node, RuntimeDeployment, ModelProfile, QualificationReceipt, Observation, ModelResidency, ResourceLease, Invocation, Attempt, Job, DispatchOutbox, QuotaReservation, UsageReceipt, Artifact, ArtifactGrant, ErasureTombstone, AuditEvent.

All business references are opaque metadata with no cross-database foreign key. Mutable records use version/updated_at; node/profile and attempt epochs fence stale writes. Job -> payload/artifact access uses org and principal grants, not filename hashes. Shared storage does not imply shared authorization.

Audit/usage metadata avoids raw content. Sync text normally remains ephemeral; async job payload must survive process restart so it is encrypted and short-lived. Keys are separate from encrypted backups. Host admin and database administrator remain privileged within declared trust model.

## 9. Adapter and protocol portability
Public protocol stable; adapter translates to runtime-specific schema. vLLM extra parameters default rejected unless published as namespaced qualified capability. Lalin worker exposes only approved ASR/TTS contract and cannot change global Brain/cloud config. Provider-specific errors normalize to stable codes while redacting upstream bodies.

Describe advertises model/profile/languages/formats/limits/cancel capability and evidence revision. Standard engine need not implement PRP control endpoints: an external adapter/supervisor provides qualification and observation. Portability test uses fake replacement plus real runtime conformance; semantic quality separately qualified.

## 10. No premature HA
Two GPU endpoints improve placement choices, not control-plane/database/network/power redundancy. Control/database loss fails admission closed. DR backups cover declared RPO/RTO, not zero downtime or zero host-disaster data loss. HA upgrade requires separate quorum/storage/network design and updated tests.

## 11. Runtime manager A/B topology and route binding
**A — Managed lifecycle:** PRP control delegates launch/list/drain/terminate to a selected Xinference adapter. Runtime A/B still load complete independent models. The runtime manager is not silently authorized to relocate replicas or unload chat for speech. Describe/observation binds manager UID + runtime UID + physical GPU + profile + epoch. Xinference lifecycle/cluster primitives are documented; exact PRP-safe targeting is a spike requirement, not a supported-feature claim [SRC-09].

**B — Independent services:** vLLM A/B and speech services have explicit service bindings managed through reviewed container/system-service tooling. Thin Python adapters reconcile state and policy; do not rebuild an OS process supervisor or model engine. This is a valid selection when it has fewer unresolved gaps and lower operator burden.

**Route-binding gate:** ก่อน network dispatch ต้องรู้ actual eligible resource ที่จอง หาก manager endpoint เลือก worker ข้างในโดยบังคับ binding ไม่ได้ ห้ามเอา lease ของ A ไปครอบงานที่อาจไปรัน B ต้องใช้ supported bound endpoint/manager reservation contract ที่ตรวจได้ มิฉะนั้น A-profile นี้ไม่ผ่าน; optional conservative whole-pool reservation ต้องมี ADR และวัดว่าไม่ deadlock/เกิน budget ก่อนใช้

Automatic provider retry/fallback and manager auto-replication are disabled by default until their attempts, resources, epochs and deadlines can be accounted for. Native engine batching is allowed within its assigned resident envelope and invocation budget. Ray logical fractions are scheduling tokens, not VRAM caps [SRC-12].

## 12. Authority chain without duplicate stores
Client-key authority เลือกหนึ่งตัว; PRP policy/identity contract อาจ delegate verifier ให้ framework ผ่าน supported interface ข้อมูล job/artifact เพิ่มเฉพาะ domain ที่ framework ไม่มี การมี internal service key อีกชั้นเป็น service-to-service authentication ไม่ใช่ duplicate user-key database

PRP Admission เป็น contract authority ของ global holds; implement ด้วย primitive ที่พิสูจน์ atomicity ได้ ไม่ mirror authoritative balances/queues แล้วมีผู้เขียนสองชุด Logical ERDs D16/D17 ไม่สั่งสร้าง table ซ้ำกับ framework ถ้ามอบหมาย entity ไปให้ framework ต้องบันทึก mapping, transaction/failure boundary และ tests

PRP database transaction กับ vendor API ไม่เป็น distributed atomic transaction โดยปริยาย ต้องใช้ durable intent + reconciliation/fencing และยอม UNKNOWN เมื่อ acknowledge สูญหาย ห้ามใช้ callback-only glue แล้วอ้างว่า exactly-once หรือ hard cancellation

## 13. API process versus model process
Thin control environment ไม่มี torch/CUDA/model payload; ASGI web worker เพิ่มได้ตาม CPU qualification โดยไม่ spawn model processes เพิ่ม Model environments แยก LLM กับ speech ตาม dependency compatibility มี owner ของ restart/readiness/shutdown แน่นอน

Python async ใช้กับ I/O; ไม่รัน synchronous ML/decoder งานหนักบน control event loop Thread/process offload ต้องมีขอบคิวและ cancellation contract ไม่ถือว่าการ cancel Future ฆ่า GPU ได้ หลักการ memory-per-process ใน FastAPI และ multiprocessing ของ vLLM ต้องตรวจตาม release ที่เลือก [SRC-14][SRC-15]

## 14. Python package direction (proposed, not generated application code)
`apps/control-api/src/prp/` สำหรับ Python API/application/policy/ports/adapters; `workers/voice/` เป็น Python worker แยก environment; LLM ใช้ pinned vendor runtime image/service ไม่ต้องคัด implementation มาไว้ใน repo; `apps/console` และ `apps/playground` เป็น optional TypeScript clients; `contracts/` เป็น public protocol กลาง

การแชร์ schemas ผ่าน generated code ต้องไม่บังคับ client import internal Python classes ไม่มี dependency บังคับจาก core ไปหา Zuri/FUNG/Lalin Studio รูป D30/D32 เป็นแนวทาง package ไม่ใช่รายงานว่ามี application files เหล่านี้แล้ว
