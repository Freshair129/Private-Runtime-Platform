---
document_id: ROADMAP-PRP
title: "Roadmap | PRP Delivery & Release Gates"
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

# Roadmap | PRP Delivery & Release Gates

**PRP — Private Runtime Platform | v0.3.0 | 2026-09-20 | Draft for review**

เอกสารที่เกี่ยวข้อง: [PRD](PRD-PRP.md) · [SRS](SRS-PRP.md) · [Tests](TEST-PRP.md) · [Operations](OPS-PRP.md)

## 1. Planning model
Roadmap นี้เป็น dependency/gate-based plan ไม่ใช่คำมั่นกำหนดวันส่งมอบ เพราะยังไม่ทราบจำนวนผู้พัฒนาและ configuration จริง ไม่มี estimate จากจำนวน GB ของ GPU และไม่มีวันเริ่มผลิตที่สมมติขึ้น ผู้รับผิดชอบเป็น role ไม่ใช่การมอบหมายคนที่ยังไม่ยืนยัน

สถานะทุก work package เริ่ม NOT_STARTED เฉพาะ documentation package ชุดนี้เป็น DELIVERED_DRAFT ไม่ใช่ application implementation การอนุมัติ scope/model/license/quotas/SLO เป็น deliverable ของ G0/G2 ไม่ใช่สิ่งที่ทำเสร็จแล้ว

## 2. Milestones และ exit gates
| Milestone | Outcome | Entry | Exit evidence |
|---|---|---|---|
| G0 Design & qualification plan | independent platform baseline | request/old SRS reviewed | approved ownership, A/B fit-gap evidence (WP24), selected authority binding, API/state, threat model, inventory, candidate licenses |
| P1-A / G1 Chat foundation | keys + Router + two vLLM replicas + console | G0 frozen | clean install, compatible JSON/SSE, isolated principals, atomic admission/fault basics |
| P1-B / G2 Voice foundation | ASR/TTS + native jobs + artifact lifecycle | G1 core seams; speech spike may parallel | quality corpora, preset rights, headless worker, safe resident placement, client fallback |
| P1-C / G3 Core pilot | production-qualified core under approved load | G1/G2 evidence | W0-W4, restore/erasure/rollback, two-client isolation, operator signoff |
| LINE integration gate | selected OA adapter works safely | contracts + channel permission | separate authorized live canary; not needed to install/use core |
| P2-A Image | allowlisted image generation/edit | G3 + P2 SRS/quality freeze | media budgets/provenance/P1 regression + model qualification |
| P2-B Video | async video under measured envelope | image foundation + resource decision | actual duration/resolution/latency tests + chat reservation protection |

G1 ไม่เท่ากับจบ P1 ทั้งหมด G3 ไม่เท่ากับ LINE delivery ผ่านแล้ว ต้องรายงานสองสถานะแยกกัน Full-duplex, cloud provider fallback, customer-isolated multi-tenancy และ cluster HA เป็น future proposals ไม่แอบรวมไว้ P2

## 3. Work breakdown และ dependencies

### WP01 — Scope & ownership freeze
**Stage:** G0 | **Owner:** Product + Architecture | **Depends on:** None

**ส่งมอบ:** PRD/SRS boundaries, requirement IDs, job dimensions

**Trace:** G01/G02/G05 | Diagram D01,D03,D12 | สถานะ NOT_STARTED

### WP02 — Hardware & runtime discovery
**Stage:** G0 | **Owner:** Operations | **Depends on:** None

**ส่งมอบ:** GPU/CPU/RAM/OS/network inventory; model/license candidates

**Trace:** E02/E04 | Diagram D04,D18 | สถานะ NOT_STARTED

### WP24 — Runtime reuse fit-gap and A/B spikes
**Stage:** G0 | **Owner:** Architecture + Runtime + Security + QA | **Depends on:** WP01,WP02

**ส่งมอบ:** A-Xinference vs B-independent services evidence; conditional C-Ray; full requirement mapping; key-recovery gap; target-binding/retry/cancel tests; decision recommendation without fabricated benchmarks

**Trace:** NFR-020/023/024; FR-005/017/018/042 | Diagram D31,D33,D34 | สถานะ NOT_STARTED

### WP03 — Contracts & authority decision
**Stage:** G0 | **Owner:** API + Security | **Depends on:** WP01,WP24

**ส่งมอบ:** freeze public/management contracts, selected A/B binding, single key/admission authority, approved gaps and secret design

**Trace:** E01/E03/E05; NFR-020/023 | Diagram D08,D17,D31,D33 | สถานะ NOT_STARTED

### WP25 — Python engineering and environment baseline
**Stage:** P1-A | **Owner:** Build + Core + Operations | **Depends on:** WP03

**ส่งมอบ:** compatible pinned Python/toolchain and separate control/LLM/speech locks/images, typed ports, no-model-import tests and CI gates per Coding Standards

**Trace:** NFR-019/021/022 | Diagram D23,D30,D32 | สถานะ NOT_STARTED

### WP04 — Standalone control plane
**Stage:** P1-A | **Owner:** Core | **Depends on:** WP01,WP03,WP25

**ส่งมอบ:** thin Python control package, framework configuration/adapter seams, health and independent release; no duplicated vendor services

**Trace:** FR-001/002/050/054; NFR-019/021/022 | Diagram D02,D04,D32 | สถานะ NOT_STARTED

### WP05 — Identity/key/quota
**Stage:** P1-A | **Owner:** Identity | **Depends on:** WP03,WP04

**ส่งมอบ:** configure conforming key/RBAC authority and quota primitives; custom verifier/ledger only for approved gaps; object grants and revoke tests

**Trace:** FR-003..009/047 | Diagram D08,D17 | สถานะ NOT_STARTED

### WP06 — Registry/qualification
**Stage:** P1-A | **Owner:** Registry | **Depends on:** WP02,WP04

**ส่งมอบ:** reuse selected manager/service inventory with PRP profile/qualification mapping, actual resource identity and readiness receipts

**Trace:** FR-010..015/042 | Diagram D10,D14 | สถานะ NOT_STARTED

### WP07 — Router/admission/execution
**Stage:** P1-A | **Owner:** Router + Admission | **Depends on:** WP05,WP06

**ส่งมอบ:** configure/reuse router and admission primitives; implement only approved binding/atomicity/uncertainty gaps; test hidden retries and races

**Trace:** FR-016..022 | Diagram D09,D13 | สถานะ NOT_STARTED

### WP08 — Chat/stream contracts
**Stage:** P1-A | **Owner:** API + Chat Adapter | **Depends on:** WP03,WP07

**ส่งมอบ:** thin stable chat contract and selected runtime adapter, tokenizer budgets, JSON/SSE/tools-as-data; disable unaccounted retries

**Trace:** FR-023..028 | Diagram D06 | สถานะ NOT_STARTED

### WP09 — Text console & negative tests
**Stage:** P1-A | **Owner:** Console + QA | **Depends on:** WP05,WP08

**ส่งมอบ:** independent key/health UI; mock+DB races+isolation tests

**Trace:** FR-045/048/056 | Diagram D05,D21 | สถานะ NOT_STARTED

### WP10 — Speech extraction spike
**Stage:** P1-B | **Owner:** Speech | **Depends on:** WP02,WP03

**ส่งมอบ:** compare existing speech runtime with headless Lalin extraction; reuse engine pipeline, restrict routes, approve voice rights

**Trace:** FR-031/033/043 | Diagram D03,D18 | สถานะ NOT_STARTED

### WP11 — Artifacts/decode
**Stage:** P1-B | **Owner:** Artifact + Security | **Depends on:** WP05

**ส่งมอบ:** bounded upload, sandbox, checksums, ACL, TTL/erasure/share grants

**Trace:** FR-029/030/039..041 | Diagram D19,D20 | สถานะ NOT_STARTED

### WP12 — Native durable speech jobs
**Stage:** P1-B | **Owner:** Jobs | **Depends on:** WP07,WP11

**ส่งมอบ:** reuse durable job primitives or approved gap implementation; native ASR/TTS kinds, idempotency, state/cancel/recovery tests

**Trace:** FR-036..038 | Diagram D12 | สถานะ NOT_STARTED

### WP13 — ASR/TTS integration
**Stage:** P1-B | **Owner:** Speech + API | **Depends on:** WP10,WP11,WP12

**ส่งมอบ:** sync/async adapters, fidelity, no-speech and model manifest

**Trace:** FR-031..035/043 | Diagram D07 | สถานะ NOT_STARTED

### WP14 — Physical placement qualification
**Stage:** P1-B | **Owner:** Operations + QA | **Depends on:** WP06,WP13

**ส่งมอบ:** CPU speech or measured B headroom; resident budgets, no silent swaps

**Trace:** FR-018/044 | Diagram D04,D14 | สถานะ NOT_STARTED

### WP15 — Independent voice playground
**Stage:** P1-B | **Owner:** Client | **Depends on:** WP08,WP13

**ส่งมอบ:** record-send/upload, own voice-turn state, text fallback/TTS-only retry

**Trace:** FR-049 | Diagram D07 | สถานะ NOT_STARTED

### WP16 — Speech quality evidence
**Stage:** P1-B | **Owner:** QA + Product | **Depends on:** WP13

**ส่งมอบ:** fixed corpus/scorers, ASR CER/WER/entity and TTS listening evidence

**Trace:** NFR-008..010 | Diagram D25 | สถานะ NOT_STARTED

### WP17 — Mixed/fault/security qualification
**Stage:** P1-C | **Owner:** QA + Security | **Depends on:** WP09,WP14,WP15,WP16

**ส่งมอบ:** W0-W4, node/DB/observer failures, revoke/delete/uncertain execution

**Trace:** NFR/SEC | Diagram D13,D20,D25 | สถานะ NOT_STARTED

### WP18 — Operations and recovery
**Stage:** P1-C | **Owner:** Operations | **Depends on:** WP17

**ส่งมอบ:** alerts/runbooks, disaster restore, forward-safe rollback, release evidence

**Trace:** FR-046/051/052 | Diagram D21,D22,D23 | สถานะ NOT_STARTED

### WP19 — Portability & multi-app pilot
**Stage:** P1-C | **Owner:** API + QA | **Depends on:** WP18

**ส่งมอบ:** two clients, vendor-neutral replacement conformance, config export, pending-job/erasure preservation and key-rotation rehearsal

**Trace:** FR-053/054; NFR-024 | Diagram D26,D34 | สถานะ NOT_STARTED

### WP20 — External LINE adapter
**Stage:** LINE | **Owner:** Integration owner | **Depends on:** WP08,WP13

**ส่งมอบ:** signature/dedupe/content/ASR-chat-TTS/outbox/push/URL adapter

**Trace:** FR-055 | Diagram D11,D15 | สถานะ NOT_STARTED

### WP21 — Authorized LINE canary
**Stage:** LINE | **Owner:** Integration owner + QA | **Depends on:** WP20,WP17

**ส่งมอบ:** real channel permissions, quota, device playback, unknown-send recovery

**Trace:** INT-LINE gate | Diagram D11,D15 | สถานะ NOT_STARTED

### WP22 — Image contract & implementation
**Stage:** P2-A | **Owner:** Media + Security | **Depends on:** G3 complete + P2 scope freeze

**ส่งมอบ:** approved workflow/model, pixel/step quotas, async lineage

**Trace:** P2-001..008 | Diagram D24 | สถานะ NOT_STARTED

### WP23 — Video qualification & rollout
**Stage:** P2-B | **Owner:** Media + Operations | **Depends on:** WP22 + hardware evidence

**ส่งมอบ:** duration/resolution envelopes, reserved chat capacity, video safety/test

**Trace:** P2-001..008 | Diagram D24 | สถานะ NOT_STARTED

## 4. Parallel work และ critical path
Critical path: ownership/contracts -> access/registry -> admission/fencing -> chat -> speech jobs/placement/quality -> mixed load -> restore/rollback -> core pilot

ทำขนานได้: hardware/license discovery กับ API drafting; speech-runtime extraction กับ chat integration หลัง contract freeze; voice UI กับ artifact/worker contract mocks; LINE adapter development กับ core hardening โดยไม่ถือว่า mock/live result เท่ากัน

ห้ามทำขนานโดยไม่มี coordinator: เปลี่ยน SRS identity/state contracts, migrate shared schema, เปลี่ยน GPU resident budget และเปิด runtime ports; designated integrator ต้อง reconcile baseline แล้ว regenerate trace views เพียงรอบที่ควบคุมได้

## 5. Gate checklists
G0: ยืนยัน independent ownership, no Zuri dependency, one admission authority, P1 voice semantics, supported interfaces, error/state model, threat/retention assumptions, host inventory, stack choices
G1: real two-node qualification, wrong/missing auth refusal, physical ID dedupe, resource race, bounded queue, streaming interruption, no cloud egress, operator can revoke key
G2: approved ASR/TTS/preset manifests, corpus gates, upload/decode limits, async durable state, delete/late-result fencing, CPU/GPU resident placement, independent client voice cycle
G3: mixed chat protection, no admitted OOM, simulated host/coordinator failure, tested restore with erasure, release rollback, limited-content observability, two apps quota isolation, docs/config handoff
LINE: verified webhook/dedup, channel permission, ACK budget, reply token policy, push idempotency and quota, signed audio URL lifecycle, mobile/desktop playback

ไม่มี security waiver แบบเงียบ ๆ; scope/secret/uncertain resource/egress defect เป็น BLOCKED และห้ามรวมเป็น passed percentage หาก target performance ไม่ผ่าน ให้ปรับ profile/limits ด้วย change record และทดสอบใหม่ ไม่แก้เกณฑ์ย้อนหลังแล้วอ้างผลเก่าผ่าน

## 6. Team interfaces และ RACI
| Activity | Accountable | Responsible | Consulted |
|---|---|---|---|
| Product scope/targets | Product owner | Architect | QA/Operations |
| API/state/ownership | Technical owner | Core/API | Client/Integration |
| Keys/tenant/egress | Security owner | Identity/Core | Operations |
| Runtime/model/voice | Technical owner | Speech/LLM engineer | Product/license reviewer |
| Hardware qualification | Operations owner | QA + Runtime engineer | Admission engineer |
| Acceptance evidence | QA owner | Test maintainers | Security/Product |
| Production/rollback | Release owner | Operator | QA/Integration |
| LINE channel rollout | Integration owner | LINE adapter maintainer | Channel owner |

ทีมเล็กอาจเป็นคนเดียวหลาย role แต่ผู้อนุมัติและผู้ลงมือในหลักฐานต้องระบุจริงก่อน rollout ไม่มีการตั้งชื่อบุคคลหรือให้สิทธิ์ production ในเอกสารนี้

## 7. Risk burn-down และ decision triggers
| Risk | First proof | Stop / decision trigger |
|---|---|---|
| Model does not fit alongside speech | WP02/WP14 measured profile | เปลี่ยน model/context/CPU placement หรือประกาศ reduced chat replica; ห้าม silent swap |
| Voice quality below target | WP10/WP16 corpus | เปลี่ยน preset/engine; G2 blocked |
| Gateway/native scheduler conflict | WP03/WP07 race test | เลือก single authority chain ก่อน implementation |
| Storage/tombstone mismatch | WP11/WP18 restore test | หยุด artifact reads จน reconcile |
| Hidden desktop dependency | WP10 clean headless package | extract adapter/service profile แทนยกทั้ง Studio |
| LINE account access unavailable | WP20 contract tests | core G3 ยังประเมินได้ แต่ LINE gate BLOCKED |
| Two hosts share outage domain | WP18 failure drill | disclose SPOF; เพิ่ม HA เป็น requirement ใหม่หากจำเป็น |

## 8. Backlog policy และ definition of ready/done
Ready: linked requirement IDs, owner, dependency status, approved acceptance, data/privacy impact, API/schema diff, rollback approach และ test level
Done: implementation exists, exact commit/image/profile identified, applicable test evidence PASS, docs/trace updated, deployment reversible และไม่มี unresolved critical issue

Documentation-only task done ไม่เปลี่ยน runtime test เป็น PASS Contract stub ไม่เป็น implementation completion Endpoint screenshot ไม่พิสูจน์ concurrency หรือ safe restart

## 9. Handoff package และ next execution order
Integrator เริ่ม WP01/WP02 -> WP24 -> WP03 ก่อน แล้ว WP25 -> WP04 ไม่สร้าง repository หรือส่ง credential จริงจากไฟล์นี้ เปิด implementation issue ต่อ work package โดย link PRP IDs และ evidence placeholder ใช้ branch/PR ตาม workflow ของ repository PRP ที่เลือก ไม่ยืม registry หรือ requirement number ของ Zuri

Deliverables ก่อน core pilot: pinned deployment manifests, model/voice rights receipts, executable contract tests, benchmark fixtures/results, admin/bootstrap/key/runbook, backup/restore receipts, API schema export และ known-limitations sheet

## 10. Reuse-first gate refinement — v0.3.0
G0 ไม่ผ่านเพียงเพราะมี diagram: ต้องมี WP24 fit-gap ครบ 92 P1 requirements, source/experiment evidence แยกกัน, actual target/epoch binding, key-verifier conformance, cancellation และ framework retry policy ก่อน WP03 เลือก stack

WP25 สร้าง engineering baseline หลัง stack contract ตกลงแล้วและก่อน WP04 production code; isolated throwaway spike ใน WP24 อนุญาตก่อนหน้าได้ ไม่อ้างเป็น production implementation

เส้นทางหลักที่เพิ่ม: WP01/WP02 -> WP24 -> WP03 -> WP25 -> WP04 -> WP05/WP06 -> WP07 -> WP08/WP09 จากนั้น voice และ qualification ตามเดิม WP20 ทำขนานกับ WP17 ได้หลัง WP08/WP13; WP21 ยังรอ core qualification และ authorization

Work package ชื่อ Identity/Registry/Router/Jobs หมายถึงส่งมอบ capability ไม่ใช่สั่งเขียน service ใหม่โดยอัตโนมัติ issue implementation ต้องระบุ disposition REUSE/CONFIGURE/ADAPT/BUILD-GAP พร้อม requirement/evidence และขอบเขตการทดสอบ

เมื่อ A/B ไม่ผ่าน ให้บันทึก BLOCKED พร้อม gap แล้วตัดสินใจ reduce scope/เปลี่ยน candidate/อนุมัติ gap code ด้วย change control ไม่เพิ่ม framework อีกตัวโดยไม่มี owner แผนไม่มีวันเสร็จที่สมมติและไม่เปลี่ยนการมีสองเครื่องเป็น HA
