---
document_id: STACK-EVALUATION-PRP
title: "Stack Evaluation | Python-first & Reuse-before-build"
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

# Stack Evaluation | Python-first & Reuse-before-build

**PRP — Private Runtime Platform | v0.3.0 | 2026-09-20 | Draft for review**

เอกสารที่เกี่ยวข้อง: [SRS](SRS-PRP.md) · [ADR](ADR-PRP.md) · [Roadmap](ROADMAP-PRP.md) · [Coding Standards](../standards/Coding-Standards.md)

## 1. Decision state
Python-first/reuse-before-build เป็นทิศทางเอกสารที่ผู้ใช้ร้องขอ ส่วน runtime manager, gateway และ exact versions ยังไม่เลือก ไม่มี A/B benchmark, clean install หรือ GPU test ในงานจัดเอกสารนี้ ทุก candidate evidence เป็น NOT_RUN หรือ SOURCE_REVIEWED เท่านั้น

เป้าหมายคือ reuse ของที่แก้ปัญหานี้อยู่แล้ว ไม่ใช่สร้าง runtime engine ใหม่หรือเพิ่ม middleware หลายชั้นจนตรวจสอบไม่ได้

## 2. Candidate compositions (alternatives, not a shopping list)
| Candidate | Composition | สิ่งที่ต้องพิสูจน์ก่อนเลือก |
|---|---|---|
| A — Managed runtimes | Thin Python PRP + Xinference supervisor/workers + vLLM A/B; speech ผ่าน supported adapter หรือ isolated worker | exact GPU binding, lifecycle reconciliation, auth gap, retries and speech compatibility |
| B — Independent services | Thin Python PRP + independently supervised vLLM A/B + speech worker; gateway ที่ผ่าน conformance | operator effort, minimal lifecycle adapter, shared admission and key authority |
| C — Distributed serving alternative | Ray Serve/Serve LLM แทน management layer ที่ซ้อนกัน; vLLM เป็น engine ได้ | ใช้เมื่อ replica/serving needs เพิ่มและมี owner; private control network and logical-vs-physical budgets |

FastAPI/Pydantic ใช้สำหรับ thin API/schema เมื่อ framework เดิมไม่ครอบคลุม public contract LiteLLM อาจเป็น key/router layer ของ A หรือ B เมื่อ fit-gap ผ่าน ไม่ใช่ dependency บังคับ และไม่ใช่เหตุผลให้สร้าง user-key store อีกชุด [SRC-03][SRC-09][SRC-11][SRC-13]

## 3. Reuse boundaries
| Capability | Reuse candidate | PRP retains | Unverified gap |
|---|---|---|---|
| Inference batching/KV/weights | vLLM | profile/permissions/deadline envelope | actual GPU capacity and cancellation |
| Launch/list/terminate | Xinference or existing service supervisor | qualification/policy/current resource mapping | manager placement/restart behavior |
| Keys/model access/routing | conforming gateway; LiteLLM optional | org/object grants and global limits | non-recoverable key storage, audio quota, retry boundaries |
| ASR/TTS | faster-whisper / approved TTS / Lalin-derived worker | public speech contract and quality gate | model/env/license/Thai quality |
| Job persistence | selected durable job primitive | outcomes/attempt/fence/idempotency contract | exactly which states survive restart |
| Artifact storage | existing filesystem/object API | UUID ACL/TTL/erasure/grants | access through vendor callbacks |
| Serving replicas | selected manager; Ray conditional | two approved A/B replicas and accounting | automatic replica relocation |

ข้อกำหนดเก่าไม่ต้องถูกเขียนใหม่เมื่อ framework ทำได้ คง acceptance tests แล้ว map implementation owner เดียวต่อ concern ห้ามสร้าง mirror authoritative store เพียงเพื่อให้ชื่อ table ขึ้น PRP

## 4. Source-reviewed findings (not qualification results)
Xinference มี lifecycle commands และ supervisor/worker topology; support ขึ้นกับ engine/model combinations [SRC-09]. รูปแบบนี้ไม่ใช่หลักฐานว่าป้องกัน bypass หรือเปิด targeted execution ตามที่ lease ของ PRP ต้องการได้ ต้องทดลองจริง

Xinference auth page ที่ตรวจอธิบาย encrypted key storage และ reveal operations จึงมี documented mismatch กับ FR-005 สำหรับ client keys ที่ต้องอ่านคืนไม่ได้ [SRC-10]. ใช้ manager เฉพาะ internal lifecycle ยังเป็น candidate ได้ โดยให้ client-key authority อีกขอบเขตที่ผ่านเกณฑ์ ไม่ copy user keys ระหว่างสอง store

Ray resource allocation เป็น logical scheduling ไม่ใช่การบังคับ VRAM cap จาก fractional GPU [SRC-12]. Candidate C จึงยังต้องวัด residency และ enforce physical admission เหมือนแบบอื่น

FastAPI multiple processes มี memory แยก; จึงไม่วาง model globals ใน web worker แล้วเพิ่ม workers เพื่อแก้ concurrency [SRC-14]. Python-first ไม่ใช่ single process และไม่เปลี่ยน native GPU computation ให้เป็น Python loops

## 5. Mandatory fit-gap record
สำหรับแต่ละ PRP requirement ระบุ candidate, pinned version/image, official source, observed capability, test ID, test result, limitation, disposition, missing code, owner และ maintenance/exit risk

Disposition: REUSE = ใช้ได้ผ่าน test; CONFIGURE = ตั้งค่าให้ผ่าน; ADAPT = wrapper/protocol glue; BUILD-GAP = ช่องว่างที่อนุมัติพร้อมเหตุผล; DEFER = อยู่นอก phase หรือ blocker ที่ยังรับมอบไม่ได้ ไม่ใช้ DEFER กับ P1 Must แล้วประกาศ P1 ผ่าน

`registry/reuse-fit-gap-template.json` มีแถวครบทุก P1 requirement แต่ยัง UNASSESSED / NOT_RUN ส่วน `registry/stack-evaluation-template.json` เก็บ candidate-level evidence templates ไม่มีคะแนนหรือเวลาที่แต่งขึ้น

## 6. A/B experiment protocol
ใช้ model/tokenizer/template/context revision และฮาร์ดแวร์ชุดเดียวกัน กำหนด traffic/data-retention และ network boundary เหมือนกัน แยก warm/cold และ source observations ออกจากตัวเลขจริง

| Experiment | Expected evidence | Gate |
|---|---|---|
| EV01 Clean control install | Python version/lock, no desktop dependency, control import without ML/GPU | NFR-019/021/022 |
| EV02 Real A/B registration | protected endpoint auth, model profile, distinct physical GPUs and epochs | FR-010..015 |
| EV03 Target binding | request lease matches actual node, including framework routing/retry | NFR-023 |
| EV04 Identity/key semantics | hash/verifier or conforming authority, no reveal, scoped listing/jobs/files/revoke | FR-003..009 |
| EV05 Atomic multi-process load | no duplicated capacity/quota holds; no bypass direct worker | FR-017/018 |
| EV06 Timeout/restart | UNKNOWN/QUARANTINED evidence, no blind inference replay | FR-020..022 |
| EV07 Mixed chat/speech | resident profile + actual placement, no silent unload or OOM under admitted load | FR-018/044 |
| EV08 Adapter/exit | public schemas unchanged; config export; key rotation plan; deletion fences preserved | NFR-024 |

EV01..08 เป็น experiment plan ไม่ใช่ test results และไม่แทน AT/W corpus ของ baseline Candidate ที่ speech ยังไม่พร้อมให้แสดง BLOCKED ก่อน G2 ไม่ใช้ stub เป็น proof คุณภาพเสียง

## 7. Selection rule and operator cost
Mandatory security/identity/capacity/uncertainty gates ต้องผ่านก่อนเปรียบเทียบความสะดวก จากนั้นบันทึก deploy steps, services/datastores ที่ต้องดูแล, custom gap code, upgrade/rollback effort, required licenses และทักษะผู้ดูแล ไม่ประกาศผู้ชนะหรือเปอร์เซ็นต์ประหยัดเวลาถ้าไม่ได้วัด

เริ่ม A/B evaluation ก่อน production code; B สามารถเป็นตัวเลือกสุดท้ายได้เมื่อเหมาะกับสองเครื่องมากกว่า A ไม่บังคับเลือก framework ที่ feature เยอะกว่า และไม่บังคับเพิ่ม C-Ray เมื่อ A/B ยังไม่ผ่านโดยอัตโนมัติ

## 8. Approval artifact
Decision receipt ต้องมี selected_candidate, rejected alternatives/reasons, key authority, lifecycle owner, route binding, retry policy, datastore ownership, immutable version matrix, gap-code owner, tests/blocked items, reviewer และ rollback/exit plan ระบุว่าใครอนุมัติและวันใด

สิ่งที่ยังไม่มีในชุดนี้: actual pinned production versions, measured framework comparison, working deployment, applied secrets, launched models หรือ passed runtime tests