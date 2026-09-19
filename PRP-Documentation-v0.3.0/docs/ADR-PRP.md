---
document_id: ADR-PRP
title: "Architecture Decisions | Proposed PRP Baseline"
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

# Architecture Decisions | Proposed PRP Baseline

**PRP — Private Runtime Platform | v0.3.0 | 2026-09-20 | Draft for review**

เอกสารที่เกี่ยวข้อง: [SRS](SRS-PRP.md) · [Architecture](ARCH-PRP.md) · [Roadmap](ROADMAP-PRP.md)

## ADR-PRP-001 — Independent platform ownership
Status: PROPOSED implementation decision; name and independent direction were selected in conversation. Context: historical SRS tied identity/admission to Zuri. Decision: PRP owns identities/quotas/resource leases/inference jobs; apps own conversation/tools/channel delivery. No import, database foreign key, bootstrap or release dependency on Zuri.
Alternatives: Zuri module (simpler reuse, unacceptable mandatory product dependency); generic third-party proxy alone (does not cover shared custom speech resources). Consequence: PRP needs its own control state and migration mapping; reuse code only behind neutral adapters. Verification: FR-001/002/053/054 and D01/D03/D26.

## ADR-PRP-002 — One physical admission authority, Router is not engine
Status: PROPOSED. Decision: Router filters/ranks; Admission atomically reserves quota/queue/physical budgets; dispatcher sends only reserved attempts. Engine retains local batching. Resident model budget separate from invocation lease. No hedging or KV migration in P1.
Alternatives: direct round-robin, independent app schedulers, free-VRAM-only selection. Rejected because they cannot account for shared resources/failure ambiguity. Consequence: central state availability matters; fail closed during DB/observer failure. Verification: FR-013/016..022/044.

## ADR-PRP-003 — Atomic speech services, client owns voice turn
Status: PROPOSED. Decision: PRP exposes ASR and preset TTS as independent sync/native-async operations. Client app/reference UI owns ASR->chat->TTS and text fallback. No business voice-turn job kind or generic DAG in P1.
Alternatives: Zuri agent in pool; central ASR/LLM/TTS orchestrator. Deferred to avoid business ownership/agent lock-in. Consequence: reference client demonstrates workflow and preserves answer before TTS; job IDs connect stages without shared business DB. Verification: FR-028/031..038/049/055.

## ADR-PRP-004 — Modular control plane and replaceable implementations
Status: OPEN_FOR_G0_SELECTION (revised in v0.3.0). Direction: Python-first is fixed for this documentation revision via ADR-PRP-009; framework/product selection is not fixed. Compare A Xinference-managed runtimes with B independent vLLM/speech services; C Ray Serve only when its trigger is documented. LiteLLM may implement gateway/keys/routing, not an obligatory additional scheduler.

Selection input: WP24 fit-gap, conformance spikes, current feature-tier/license evidence, key storage/reveal semantics, worker binding, retry/cancel/restart evidence, operator cost, export/exit. No candidate passes on README claims alone. Use supported extension/config interfaces before custom services; BUILD-GAP needs a named requirement and approved owner.

One client-key authority and one physical admission contract; vendor runtime/key state is not duplicated in a competing PRP store. Client key verifier-only constraint FR-005 remains: documented Xinference recoverable/reveal-able keys are a gap for direct client-key delegation [SRC-10].

Consequence: extra G0 evaluation work, but lower risk of implementing already-solved infrastructure. Existing FRs remain normative; framework selection cannot waive resource fencing or privacy. Verification: FR-005/017/018/042/043/050/053 and NFR-019..024. Decision receipt must name selected build/profile and unresolved blockers before production.

## ADR-PRP-005 — Unknown execution is a first-class state
Status: PROPOSED. Decision: user outcome, execution and capacity dimensions separate. Timeout/cancel/lease expiry never prove compute stopped. Unknown attempt quarantines resource until evidence/supervisor recovery; late result cannot reopen terminal outcome/deleted content.
Consequence: temporary lower availability rather than hidden oversubscription. No automatic retry after ambiguous send. Verification: FR-020/021/022/038/041 and D12/D13/D22.

## ADR-PRP-006 — Clip voice and calibrated two-node deployment
Status: PROPOSED. Decision: two full-model chat replicas, speech CPU trial or measured GPU resident headroom, no silent LLM unload. Voice P1 is record-and-send with approved preset; live calling/cloning/music deferred. If hardware cannot meet targets, revise model/context/placement and expose reduced capacity rather than falsify readiness.
Verification: FR-018/029..035/044 and W1-W4. Release gate: exact models/rights/profile approved before G2/G3.

## ADR-PRP-007 — Explicit content retention and bearer-link boundary
Status: PROPOSED. Decision: authenticated artifact access default; native delivery grant is optional, explicitly permissioned, revocable and time-bound. Async durable payload encrypted with finite TTL; sync text no persistent memory by default. Erasure ledger applies before restore read.
Consequence: some LINE use cases must use authenticated app playback instead of native audio attachment; third-party downloaded copies cannot be erased by PRP. Verification: FR-028/039..041 and SEC-008/009.

## ADR-PRP-008 — P2 additive media, not implicit Phase 1 expansion
Status: PROPOSED. Decision: P2 image/video use same identity/admission/job/artifact primitives but new grants, metering units and qualified profiles. No arbitrary workflow/plugin installs, no unapproved chat preemption. Realtime speech, cloud fallback and hostile multi-tenancy require separate decisions.
Verification: FR-056/P2-001..008 and P1 regression. P2 envelope has no approved throughput/resolution/duration promises.

## ADR-PRP-009 — Python-first, no mandatory desktop backend
Status: DIRECTION_SELECTED_FOR_DOCUMENT_REVISION by the user request to revise; runtime NOT_RUN. PRP-owned control/API/policy/adapters use Python. FastAPI/Pydantic are first evaluation choices for the thin API, not a mandate to wrap every vendor API with redundant endpoints [SRC-13]. React/TypeScript clients remain independent. Rust/Tauri screenshot standards do not govern PRP backend.

Native dependency kernels are allowed. A first-party Rust/C++ module needs evidence of a measured bottleneck or unavoidable integration boundary plus an ADR; a general claim that Python is slow is insufficient. Verification: NFR-019/021/022 and coding standards. Consequence: separate model processes/environments are mandatory; no single giant Python environment.

## ADR-PRP-010 — Reuse evidence before custom infrastructure
Status: DIRECTION_SELECTED_FOR_DOCUMENT_REVISION; candidate selection OPEN. Requirements describe outcomes; logical module ownership does not require first-party code. Evaluate existing runtime manager, gateway, scheduler and process-supervisor capabilities before building equivalents.

A/B are alternative evaluated compositions, not cumulative dependencies. Candidate C Ray Serve is conditional. Fit-gap rows retain source evidence separate from runtime evidence and track REUSE/CONFIGURE/ADAPT/BUILD-GAP/DEFER. A critical gap blocks G0 exit or produces a reviewed narrower design; never redefine security to declare a candidate passed. Verification: NFR-020/023/024; WP24.

## ADR-PRP-011 — Thin API and isolated model lifecycles
Status: DIRECTION_SELECTED_FOR_DOCUMENT_REVISION; exact environment pins pending WP25. API processes must not load models or initialize GPU drivers through import side effects. Dedicated runtime/worker services own weights, batching and termination. Package/image locks are isolated for control, LLM and speech when dependency requirements differ.

Automatic cross-engine retries/relocation must respect current admission and execution fences. Standard serving frameworks may implement lifecycle, but actual resource mapping must be observable; no unexplained second scheduler. Client timeout is not native compute cancellation. Verification: NFR-021..024, existing FR-020/021/044, D32/D33/D34.
