---
document_id: BASELINE-CHANGES-PRP
title: "Baseline Changes | From Zuri Pool to Independent PRP"
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

# Baseline Changes | From Zuri Pool to Independent PRP

**PRP — Private Runtime Platform | v0.3.0 | 2026-09-20 | Draft for review**

เอกสารที่เกี่ยวข้อง: [PRD](PRD-PRP.md) · [SRS](SRS-PRP.md) · [ADR](ADR-PRP.md)

## 1. Change basis
Historical file [SRC-B01] assumed Zuri-owned identities, Integration/Agent resource leases and a required platform voice-turn path. Later conversation selected independent PRP and PRP Router. This package proposes the corresponding ownership/API/state rewrite; it does not edit original Zuri documents, data, Edge devices or approvals.

Name history SLP/SHP/SAAN is discussion only; current product name PRP (Private Runtime Platform), routing module PRP Router. Repository `prp` remains a proposed name; no repository has been created in this delivery and no name/license/domain clearance is claimed.

## 2. Legacy requirement intent mapping
| Old SIP suffix | New PRP requirement | Disposition |
|---|---|---|
| 001–004 | FR-003..009 | Replace Zuri Identity/Business grants with PRP org/principal/service grants |
| 005–008 | FR-010..015/042 | Retain qualification but owner becomes PRP Registry |
| 009–012 | FR-016..022/044 | Retain safe admission/fencing; PRP owns physical resources |
| 013–015 | FR-023..027 | Compatible subset, token budget and streaming retained |
| 016–017 | FR-026/028/054 | Zuri memory/tool/conversation policy remains external; PRP tools-as-data |
| 018–020 | FR-029..032 | ASR/audio safety retained; app handles business confirmation |
| 021 | FR-036..038/049 | Remove mandatory platform voice-turn; atomic speech jobs + client workflow |
| 022–024 | FR-033..035/049 | Preset TTS retained; PARTIAL_SUCCESS belongs client voice workflow |
| 025–029 | FR-055 + API external LINE section | Move LINE signature/content/reply/push/outbox/audience into external adapter |
| 030 | FR-017/020/036..038 | PRP durable jobs separate from app/LINE conversation jobs |
| 031–033 | FR-039..041 + SEC-009 | PRP artifact/erasure; external channel delivery boundary |
| 034–036 | FR-045..047 | Independent observer/audit/alerts not Zuri control module |
| 037 | FR-048/049 | Independent console/playground; no mandatory Zuri UI |
| 038–039 | FR-050..053 | PRP deployment/recovery/canary independent of business release |
| 040 + P2-001..008 | FR-056 + PRP-P2-001..008 | Phase boundary preserved; new PRP namespaces |
| NFR-001..016 | PRP-NFR-001..018 + SEC-001..012 | Preserve safety/quality intent; split core versus LINE acceptance and add portability |

## 3. Breaking semantic changes to review
Old `business_id` is not renamed blindly to org_id; PRP principals/grants have independent lifecycle and app mapping is external. Old voice-turn route is not retained in core: clients orchestrate ASR/chat/TTS primitives; generic workflow engine deferred. Old Zuri job table is not PRP job storage; correlation is opaque request references across APIs.

Old LINE acceptance as condition for whole pool becomes separate integration gate. Old registry/ledger instructions apply only within Zuri repo when writing its adapter; PRP IDs belong to a new product registry and must not be allocated in Zuri.

## 4. Implementation migration plan
Inventory actual callers/routes/state first. Introduce neutral adapter behind old app interface; deploy isolated PRP and qualify without production switching. Mirror synthetic/authorized non-sensitive requests only; do not duplicate business tools/delivery. Canary one approved app binding. Preserve old app jobs/outbox and Edge capabilities. Rollback binding without opening second LINE sender.

Any data/key migration requires separate authorized plan, key rotation and erasure/backup implications. This draft grants no permission to read .env, copy secrets, delete Edge, alter shared volumes or update production webhook.

## v0.3.0 additive engineering revision
The historical Zuri-to-PRP ownership migration remains unchanged. See [Change Log](CHANGELOG-PRP.md) for v0.2.0 -> v0.3.0 differences: Python-first, reuse-first, A/B evaluation, thin API/model process isolation, candidate gateway authority and new NFR-019..024. Existing PRP-FR/NFR/SEC subject IDs are not renumbered; screenshot Rust/Tauri standards do not govern PRP core.
