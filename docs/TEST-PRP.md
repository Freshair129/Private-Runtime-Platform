---
document_id: TEST-PRP
title: "Verification | Acceptance Cases & Evidence Plan"
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

# Verification | Acceptance Cases & Evidence Plan

**PRP — Private Runtime Platform | v0.3.0 | 2026-09-20 | Draft for review**

เอกสารที่เกี่ยวข้อง: [SRS](SRS-PRP.md) · [Traceability](TRACEABILITY-PRP.md) · [Roadmap](ROADMAP-PRP.md)

## 1. Verification levels and status
This is an executable-test specification and trace register, not a test-run report. Every case is NOT_RUN. A file existing or a diagram rendering does not mean functional/GPU/security tests passed. PASS requires evidence_id, exact runtime/config and observed assertions. SKIPPED/BLOCKED is not PASS.

Proof levels: schema/static; unit; API contract; integration; real PostgreSQL concurrency; fault injection; pinned runtime; physical GPU workload; audio corpus; browser e2e; restore/release rehearsal; authorized live LINE. Mock success does not satisfy physical runtime or channel gates.

## 2. General fixture rules
Use two organizations in negative fixtures even though P1 production enables one trusted organization. Use at least two principals, two apps and two gateway processes. Generate ephemeral credentials; redact all evidence. Runtime tests pin image/model/tokenizer/voice/template/hardware. Files/audio are synthetic or explicitly licensed; no user voice cloning test data without separate rights.

Persist request/attempt/epoch and assert state invariants after every injected fault. For TTS/ASR test actual decoded waveform and text quality, not just HTTP200. For tool calls assert absence of business side effects in PRP. For LINE use sandbox/test OA and explicit channel-owner authorization.

## 3. Requirement acceptance cases
Each case inherits the exact setup/limits from its linked SRS requirement and workload section. Where the requirement is a quality target, its stated sample size/corpus is mandatory. Evidence must include negative assertions and failure counts, not only happy-path screenshots.

<a id="PRP-AT-001"></a>

### PRP-AT-001 — Independent bootstrap
**Requirement:** [PRP-FR-001](SRS-PRP.md#PRP-FR-001) | **Phase:** P1-A | **Proof:** deployment

**Stimulus / expected assertions:** ติดตั้ง PRP ใน environment ที่ไม่มีแอปดังกล่าว; client HTTP ธรรมดาใช้ models/chat ได้ และเมื่อเพิ่ม speech worker ใช้ ASR/TTS ได้

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Core

<a id="PRP-AT-002"></a>

### PRP-AT-002 — Application-neutral boundary
**Requirement:** [PRP-FR-002](SRS-PRP.md#PRP-FR-002) | **Phase:** P1-A | **Proof:** integration

**Stimulus / expected assertions:** schema lint และ contract test ปฏิเสธการอาศัย metadata เป็น authorization; ตัวอย่าง client ไม่ import SDK ของแอป

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Core

<a id="PRP-AT-003"></a>

### PRP-AT-003 — PRP-owned organization isolation
**Requirement:** [PRP-FR-003](SRS-PRP.md#PRP-FR-003) | **Phase:** P1-A | **Proof:** integration

**Stimulus / expected assertions:** ปลอม org_id/team/job/artifact ใน request ไม่ข้ามสิทธิ์; fixture อีก organization ถูกปฏิเสธ; ไม่เปิดใช้ hostile multi-tenant engine sharing

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Identity

<a id="PRP-AT-004"></a>

### PRP-AT-004 — Roles and delegated management
**Requirement:** [PRP-FR-004](SRS-PRP.md#PRP-FR-004) | **Phase:** P1-A | **Proof:** integration

**Stimulus / expected assertions:** ทดสอบ role/action matrix รวมผู้ดูแลอ่าน raw audio ไม่ได้โดยไม่มี grant; negative cases ผ่านทั้งหมด

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Identity

<a id="PRP-AT-005"></a>

### PRP-AT-005 — Scoped key issuance
**Requirement:** [PRP-FR-005](SRS-PRP.md#PRP-FR-005) | **Phase:** P1-A | **Proof:** integration

**Stimulus / expected assertions:** สร้างคีย์ ใช้แล้วตรวจ DB/API/log ไม่พบ plaintext; chat-only key ใช้ speech/admin ไม่ได้

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Identity

<a id="PRP-AT-006"></a>

### PRP-AT-006 — Key rotation and revocation
**Requirement:** [PRP-FR-006](SRS-PRP.md#PRP-FR-006) | **Phase:** P1-A | **Proof:** integration

**Stimulus / expected assertions:** revoke มีผลตาม NFR-002; งานค้างถูกยกเลิกหรือ fence; overlap default 24h เป็นค่าสูงสุดที่ปรับลดได้

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Identity

<a id="PRP-AT-007"></a>

### PRP-AT-007 — Capability and model grants
**Requirement:** [PRP-FR-007](SRS-PRP.md#PRP-FR-007) | **Phase:** P1-A | **Proof:** integration

**Stimulus / expected assertions:** listing ไม่เผย node IP/secret; job read/cancel และ artifact read ยังตรวจ object ownership เพิ่มจาก scope

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Identity

<a id="PRP-AT-008"></a>

### PRP-AT-008 — Atomic quotas and honest usage
**Requirement:** [PRP-FR-008](SRS-PRP.md#PRP-FR-008) | **Phase:** P1-A | **Proof:** real PostgreSQL

**Stimulus / expected assertions:** หลายคีย์ของคนเดียวและหลาย gateway process แข่งกันไม่เกิน principal/org budget; usage ไม่ทราบไม่ถูกบันทึกเป็นศูนย์จริง

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Admission

<a id="PRP-AT-009"></a>

### PRP-AT-009 — Service-account accountability
**Requirement:** [PRP-FR-009](SRS-PRP.md#PRP-FR-009) | **Phase:** P1-A | **Proof:** integration

**Stimulus / expected assertions:** เปลี่ยน user tag ไม่ bypass service/org cap; P1 ไม่มี delegated identity ที่ผ่าน review ต้องบังคับ service-key quota เท่านั้น

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Identity

<a id="PRP-AT-010"></a>

### PRP-AT-010 — Controlled node enrollment
**Requirement:** [PRP-FR-010](SRS-PRP.md#PRP-FR-010) | **Phase:** P1-A | **Proof:** integration

**Stimulus / expected assertions:** ปฏิเสธ metadata IP, redirect, DNS rebinding และ endpoint นอก allowlist ก่อนเชื่อมต่อ; mutation มี version guard

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Registry

<a id="PRP-AT-011"></a>

### PRP-AT-011 — Qualification receipt
**Requirement:** [PRP-FR-011](SRS-PRP.md#PRP-FR-011) | **Phase:** P1-A | **Proof:** pinned runtime + hardware

**Stimulus / expected assertions:** health 200 แต่ protected API ใช้คีย์ผิดแล้วยังผ่าน ต้อง qualification fail; เปลี่ยน epoch แล้ว receipt เก่าใช้ไม่ได้

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Registry

<a id="PRP-AT-012"></a>

### PRP-AT-012 — Pinned capability profiles
**Requirement:** [PRP-FR-012](SRS-PRP.md#PRP-FR-012) | **Phase:** P1-A | **Proof:** pinned runtime

**Stimulus / expected assertions:** node สองตัวที่ alias เหมือนแต่ profile ไม่ตรงไม่อยู่ replica set เดียวกัน; ไม่ยืนยัน 9B พอดี VRAM โดยดูขนาดชื่อโมเดล

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Registry

<a id="PRP-AT-013"></a>

### PRP-AT-013 — Physical resource deduplication
**Requirement:** [PRP-FR-013](SRS-PRP.md#PRP-FR-013) | **Phase:** P1-A | **Proof:** real PostgreSQL

**Stimulus / expected assertions:** เพิ่ม alias URL แล้ว capacity ไม่เพิ่ม; worker restart เปลี่ยน instance epoch แต่ไม่สร้าง GPU สมมติใบใหม่

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Admission

<a id="PRP-AT-014"></a>

### PRP-AT-014 — Fresh health observations
**Requirement:** [PRP-FR-014](SRS-PRP.md#PRP-FR-014) | **Phase:** P1-A | **Proof:** integration

**Stimulus / expected assertions:** out-of-order/old epoch ไม่ทับใหม่; observation age เกิน policy หยุด admission; dashboard ปิดแต่ observer ยังทำงาน

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Observability

<a id="PRP-AT-015"></a>

### PRP-AT-015 — Safe runtime lifecycle
**Requirement:** [PRP-FR-015](SRS-PRP.md#PRP-FR-015) | **Phase:** P1-A | **Proof:** integration

**Stimulus / expected assertions:** drain ระหว่าง stream ไม่ตัดงานเอง; stale enable ถูกปฏิเสธ; restore binding เริ่ม DISABLED

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Registry

<a id="PRP-AT-016"></a>

### PRP-AT-016 — PRP Router selection
**Requirement:** [PRP-FR-016](SRS-PRP.md#PRP-FR-016) | **Phase:** P1-A | **Proof:** integration + hardware

**Stimulus / expected assertions:** A เต็มหรือช้าเกิน budget ให้งานใหม่ไป B; ไม่มี active KV migration; B ไม่ถูกเลือกเพียงเพราะ VRAM มากกว่า

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Router

<a id="PRP-AT-017"></a>

### PRP-AT-017 — Durable admission transaction
**Requirement:** [PRP-FR-017](SRS-PRP.md#PRP-FR-017) | **Phase:** P1-A | **Proof:** real PostgreSQL + fault injection

**Stimulus / expected assertions:** kill ก่อน/หลัง commit ไม่ทำให้ accepted job หาย; duplicate outbox delivery ไม่สร้าง second logical admission

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Admission

<a id="PRP-AT-018"></a>

### PRP-AT-018 — Shared GPU reservation authority
**Requirement:** [PRP-FR-018](SRS-PRP.md#PRP-FR-018) | **Phase:** P1-B | **Proof:** hardware + concurrency

**Stimulus / expected assertions:** vLLM และ speech process แข่งกันไม่เกิน envelope; ไม่มีการใช้ free VRAM snapshot เป็น guarantee หรือปล่อย model-residency เมื่องานจบ

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Admission

<a id="PRP-AT-019"></a>

### PRP-AT-019 — Bounded fair queues
**Requirement:** [PRP-FR-019](SRS-PRP.md#PRP-FR-019) | **Phase:** P1-A | **Proof:** integration

**Stimulus / expected assertions:** flood จาก app A ไม่ขัดการรับงาน app B ที่มี grant ภายใต้ fair-share policy; งานหมด wait ออกด้วยเหตุผลไม่ค้างไม่จำกัด

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Admission

<a id="PRP-AT-020"></a>

### PRP-AT-020 — Uncertain execution fencing
**Requirement:** [PRP-FR-020](SRS-PRP.md#PRP-FR-020) | **Phase:** P1-A | **Proof:** fault injection + hardware

**Stimulus / expected assertions:** kill coordinator/timeout client ขณะ worker รัน: ไม่มี capacity ถูกคืนก่อนหลักฐาน; late result ไม่ข้าม deletion/revocation fence

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Execution

<a id="PRP-AT-021"></a>

### PRP-AT-021 — Absolute deadlines and cancellation
**Requirement:** [PRP-FR-021](SRS-PRP.md#PRP-FR-021) | **Phase:** P1-A | **Proof:** integration

**Stimulus / expected assertions:** cancel ซ้ำ idempotent; CANCEL_REQUESTED ไม่แสดงเป็น compute stopped; stream/worker ที่ไม่ abort ได้ถูก quarantine อย่างตรงไปตรงมา

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Execution

<a id="PRP-AT-022"></a>

### PRP-AT-022 — Retry classification
**Requirement:** [PRP-FR-022](SRS-PRP.md#PRP-FR-022) | **Phase:** P1-A | **Proof:** integration

**Stimulus / expected assertions:** inject uncertain post-dispatch error แล้วไม่มีการเรียก node B ซ้ำเงียบ ๆ; error ระบุ safe_to_retry และ job/request reference

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Execution

<a id="PRP-AT-023"></a>

### PRP-AT-023 — Model catalog
**Requirement:** [PRP-FR-023](SRS-PRP.md#PRP-FR-023) | **Phase:** P1-A | **Proof:** contract

**Stimulus / expected assertions:** คีย์ chat ไม่เห็น ASR/TTS ที่ไม่ได้ grant; unready deployment ไม่ถูกโฆษณาว่าพร้อมใช้

**Status:** NOT_RUN | **Evidence:** none | **Owner:** API

<a id="PRP-AT-024"></a>

### PRP-AT-024 — Chat completion and context budget
**Requirement:** [PRP-FR-024](SRS-PRP.md#PRP-FR-024) | **Phase:** P1-A | **Proof:** contract + runtime

**Stimulus / expected assertions:** context เกินคืน 422 ก่อน dispatch; ไม่ตัด system/tool rules เงียบ ๆ; JSON response ผ่าน published schema

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Chat Adapter

<a id="PRP-AT-025"></a>

### PRP-AT-025 — Streaming honesty
**Requirement:** [PRP-FR-025](SRS-PRP.md#PRP-FR-025) | **Phase:** P1-A | **Proof:** contract + fault injection

**Stimulus / expected assertions:** interrupted SSE ส่ง error event ถ้ายังเชื่อมต่อได้แล้วปิด; ไม่มี successful DONE สำหรับ failure; client disconnect trigger cancel/fence

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Chat Adapter

<a id="PRP-AT-026"></a>

### PRP-AT-026 — Tools as data only
**Requirement:** [PRP-FR-026](SRS-PRP.md#PRP-FR-026) | **Phase:** P1-A | **Proof:** contract

**Stimulus / expected assertions:** model ขอ tool write หรือ URL fetch ไม่เกิด side effect ที่ PRP; unsupported tool parser ปฏิเสธก่อน dispatch

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Chat Adapter

<a id="PRP-AT-027"></a>

### PRP-AT-027 — Usage receipts
**Requirement:** [PRP-FR-027](SRS-PRP.md#PRP-FR-027) | **Phase:** P1-A | **Proof:** integration

**Stimulus / expected assertions:** runtime ไม่ส่ง usage แล้ว receipt ไม่แต่ง actual; reconciliation ซ้ำไม่ double charge reservation/usage

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Accounting

<a id="PRP-AT-028"></a>

### PRP-AT-028 — Stateless inference default
**Requirement:** [PRP-FR-028](SRS-PRP.md#PRP-FR-028) | **Phase:** P1-A | **Proof:** privacy integration

**Stimulus / expected assertions:** แชตครั้งถัดไปโดยไม่มี history ไม่ดึงข้อความครั้งก่อน; audit/log default ไม่มี raw content; native async payload มี TTL ตาม DATA

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Core

<a id="PRP-AT-029"></a>

### PRP-AT-029 — Bounded audio upload
**Requirement:** [PRP-FR-029](SRS-PRP.md#PRP-FR-029) | **Phase:** P1-B | **Proof:** integration

**Stimulus / expected assertions:** extension spoof, file too large, actual duration เกิน, empty upload และ codec ไม่รองรับมี distinct errors; preflight จำกัด streaming read

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Artifact

<a id="PRP-AT-030"></a>

### PRP-AT-030 — Sandboxed media decoding
**Requirement:** [PRP-FR-030](SRS-PRP.md#PRP-FR-030) | **Phase:** P1-B | **Proof:** sandbox + fault injection

**Stimulus / expected assertions:** malformed/bomb/polyglot ไม่ค้าง worker ไม่ออก network; decoded cap และ timeout ทำงาน; temp files ถูก cleanup

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Speech Adapter

<a id="PRP-AT-031"></a>

### PRP-AT-031 — ASR contract
**Requirement:** [PRP-FR-031](SRS-PRP.md#PRP-FR-031) | **Phase:** P1-B | **Proof:** runtime + audio corpus

**Stimulus / expected assertions:** corpus ผ่าน NFR-008; language probability ไม่ถูกคืนเป็น confidence ของ transcript; ไม่มี timestamp/confidence ที่แต่งขึ้น

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Speech Adapter

<a id="PRP-AT-032"></a>

### PRP-AT-032 — No-speech and unclear outcome
**Requirement:** [PRP-FR-032](SRS-PRP.md#PRP-FR-032) | **Phase:** P1-B | **Proof:** audio corpus

**Stimulus / expected assertions:** silence/noise suite ไม่กระตุ้น downstream chat ใน reference client; ล้มเหลวต้องมีเหตุผลที่คนใช้แก้ไขได้

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Speech Adapter

<a id="PRP-AT-033"></a>

### PRP-AT-033 — Approved TTS voices
**Requirement:** [PRP-FR-033](SRS-PRP.md#PRP-FR-033) | **Phase:** P1-B | **Proof:** runtime + policy

**Stimulus / expected assertions:** unapproved voice/model path/URL ถูกปฏิเสธ; preset ที่ภายในใช้ reference audio ต้องเป็น asset ที่ได้รับสิทธิ์และตรึงแล้ว

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Speech Adapter

<a id="PRP-AT-034"></a>

### PRP-AT-034 — Speech text fidelity
**Requirement:** [PRP-FR-034](SRS-PRP.md#PRP-FR-034) | **Phase:** P1-B | **Proof:** audio corpus

**Stimulus / expected assertions:** เงิน วันที่ ชื่อสินค้าและตัวเลขตรงกับ golden cases; oversized request ได้ 422 ไม่ถูกตัดโดยไม่แจ้ง

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Speech Adapter

<a id="PRP-AT-035"></a>

### PRP-AT-035 — Speech response contracts
**Requirement:** [PRP-FR-035](SRS-PRP.md#PRP-FR-035) | **Phase:** P1-B | **Proof:** contract + runtime

**Stimulus / expected assertions:** MIME/header/sample metadata ตรงไฟล์; async route ใช้ 202 แยก; TTS fail ไม่สร้างไฟล์สำเร็จ 0 bytes

**Status:** NOT_RUN | **Evidence:** none | **Owner:** API

<a id="PRP-AT-036"></a>

### PRP-AT-036 — Native asynchronous operations
**Requirement:** [PRP-FR-036](SRS-PRP.md#PRP-FR-036) | **Phase:** P1-B | **Proof:** integration

**Stimulus / expected assertions:** รีสตาร์ตแล้วยังอ่าน job/state ได้; ไม่รับ arbitrary DAG, voice-turn agent หรือ generative image/video ใน P1

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Jobs

<a id="PRP-AT-037"></a>

### PRP-AT-037 — Idempotent job creation
**Requirement:** [PRP-FR-037](SRS-PRP.md#PRP-FR-037) | **Phase:** P1-B | **Proof:** real PostgreSQL

**Stimulus / expected assertions:** สอง process ส่งพร้อมกันได้ logical job เดียว; เปลี่ยนคีย์แต่ principal เดิมไม่เลี่ยง dedupe; deleted job คืน tombstone ไม่ resurrect

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Jobs

<a id="PRP-AT-038"></a>

### PRP-AT-038 — Job visibility and control
**Requirement:** [PRP-FR-038](SRS-PRP.md#PRP-FR-038) | **Phase:** P1-B | **Proof:** integration

**Stimulus / expected assertions:** เดา job_id หรือรับ id จากอีกคนยังเข้าไม่ได้; TIMEOUT+UNKNOWN ปรากฏตรงจริง; cancel-after-terminal ไม่เปลี่ยนผลเดิม

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Jobs

<a id="PRP-AT-039"></a>

### PRP-AT-039 — Artifact ownership
**Requirement:** [PRP-FR-039](SRS-PRP.md#PRP-FR-039) | **Phase:** P1-B | **Proof:** integration

**Stimulus / expected assertions:** job A อ้าง artifact B ที่ไม่ grant ได้ 404; list/download/delete authorize ใหม่; worker รับ scoped artifact reference ไม่ได้ storage master key

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Artifact

<a id="PRP-AT-040"></a>

### PRP-AT-040 — Controlled delivery grants
**Requirement:** [PRP-FR-040](SRS-PRP.md#PRP-FR-040) | **Phase:** P1-B | **Proof:** integration

**Stimulus / expected assertions:** expired/revoked link ใช้ไม่ได้; multi-fetch ทำได้ใน TTL; highly-private policy ไม่ออก bearer link; PRP ไม่ส่ง LINE เอง

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Artifact

<a id="PRP-AT-041"></a>

### PRP-AT-041 — Retention and erasure
**Requirement:** [PRP-FR-041](SRS-PRP.md#PRP-FR-041) | **Phase:** P1-B | **Proof:** fault injection + restore

**Stimulus / expected assertions:** delete ระหว่าง execution แล้วผลลัพธ์ไม่กลับมา; restore reconcile erasure ledger ก่อนเปิด read; document backup expiry residuals

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Artifact

<a id="PRP-AT-042"></a>

### PRP-AT-042 — Worker adapter contract
**Requirement:** [PRP-FR-042](SRS-PRP.md#PRP-FR-042) | **Phase:** P1-A | **Proof:** contract

**Stimulus / expected assertions:** fake worker กับ vLLM/speech adapter ผ่าน contract เดียวกัน; runtime ที่ไม่ abort ได้รายงาน unsupported และใช้ quarantine

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Worker Adapter

<a id="PRP-AT-043"></a>

### PRP-AT-043 — Lalin-derived voice isolation
**Requirement:** [PRP-FR-043](SRS-PRP.md#PRP-FR-043) | **Phase:** P1-B | **Proof:** contract + packaging

**Stimulus / expected assertions:** ปิด/ไม่ติดตั้ง Lalin Studio แล้วยังใช้ speech ได้; route allowlist และ egress tests ผ่าน; engine เปลี่ยนได้โดย client contract ไม่เปลี่ยน

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Speech Adapter

<a id="PRP-AT-044"></a>

### PRP-AT-044 — Safe model residency
**Requirement:** [PRP-FR-044](SRS-PRP.md#PRP-FR-044) | **Phase:** P1-B | **Proof:** hardware

**Stimulus / expected assertions:** runtime cache ยัง resident ต้องคง reservation; model swap ต้อง drain/qualify; speech-only B ต้องประกาศ chat capacity ลดและผ่าน change review

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Admission

<a id="PRP-AT-045"></a>

### PRP-AT-045 — Operational telemetry
**Requirement:** [PRP-FR-045](SRS-PRP.md#PRP-FR-045) | **Phase:** P1-A | **Proof:** integration

**Stimulus / expected assertions:** ไม่มี temperature/power เป็น unavailable; metrics ไม่บรรจุ raw prompts/user IDs เป็น high-cardinality labels; dashboard loss ไม่หยุด correctness

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Observability

<a id="PRP-AT-046"></a>

### PRP-AT-046 — Actionable alerts
**Requirement:** [PRP-FR-046](SRS-PRP.md#PRP-FR-046) | **Phase:** P1-C | **Proof:** integration

**Stimulus / expected assertions:** fault suite ได้ event พร้อม scope/time; notification destination ไม่มีแสดง NOT_CONFIGURED ไม่อ้างว่าส่งแล้ว

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Observability

<a id="PRP-AT-047"></a>

### PRP-AT-047 — Auditable management
**Requirement:** [PRP-FR-047](SRS-PRP.md#PRP-FR-047) | **Phase:** P1-A | **Proof:** security integration

**Stimulus / expected assertions:** สำรวจ logs/DB/API/export ไม่มี plaintext secret/signed URL/raw audio/transcript; repeated settlement ไม่เขียน usage ซ้ำ

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Audit

<a id="PRP-AT-048"></a>

### PRP-AT-048 — Independent operator console
**Requirement:** [PRP-FR-048](SRS-PRP.md#PRP-FR-048) | **Phase:** P1-A | **Proof:** browser e2e

**Stimulus / expected assertions:** operator และ org admin มีมุมมองคนละขอบเขต; native local admin bootstrap และ recovery procedure ใช้ได้

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Console

<a id="PRP-AT-049"></a>

### PRP-AT-049 — Minimal independent playground
**Requirement:** [PRP-FR-049](SRS-PRP.md#PRP-FR-049) | **Phase:** P1-B | **Proof:** browser e2e

**Stimulus / expected assertions:** mic denied ยังพิมพ์/upload ได้; stop playback ไม่แอบอ้าง cancel GPU; TTS fail รักษาคำตอบข้อความและ retry เฉพาะ TTS

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Reference Client

<a id="PRP-AT-050"></a>

### PRP-AT-050 — Reproducible independent deployment
**Requirement:** [PRP-FR-050](SRS-PRP.md#PRP-FR-050) | **Phase:** P1-A | **Proof:** deployment

**Stimulus / expected assertions:** install clean environment โดยไม่มีแอปธุรกิจ/remote control plane dependency; manifest ไม่มี latest/secrets; ports ตรง inventory

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Operations

<a id="PRP-AT-051"></a>

### PRP-AT-051 — Backup and recovery
**Requirement:** [PRP-FR-051](SRS-PRP.md#PRP-FR-051) | **Phase:** P1-C | **Proof:** restore rehearsal

**Stimulus / expected assertions:** restore test ผ่าน RPO/RTO target ที่อนุมัติ; ไม่ถือ backup แทน HA; explicit residual data policy สำหรับ immutable backup

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Operations

<a id="PRP-AT-052"></a>

### PRP-AT-052 — Canary and rollback
**Requirement:** [PRP-FR-052](SRS-PRP.md#PRP-FR-052) | **Phase:** P1-C | **Proof:** rehearsal

**Stimulus / expected assertions:** switch voice off แล้ว chat ยังใช้เดิม; rollback ไม่เปลี่ยน channel sender; release evidence กับ rollback approver ถูกบันทึก

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Operations

<a id="PRP-AT-053"></a>

### PRP-AT-053 — Compatibility and exit path
**Requirement:** [PRP-FR-053](SRS-PRP.md#PRP-FR-053) | **Phase:** P1-C | **Proof:** contract + portability

**Stimulus / expected assertions:** ทดสอบ two independent clients + fake replacement adapter; export config/profile/job/usage เป็น documented JSON โดยไม่ export plaintext keys

**Status:** NOT_RUN | **Evidence:** none | **Owner:** API

<a id="PRP-AT-054"></a>

### PRP-AT-054 — No mandatory LINE dependency
**Requirement:** [PRP-FR-054](SRS-PRP.md#PRP-FR-054) | **Phase:** P1-A | **Proof:** deployment + contract

**Stimulus / expected assertions:** ปิด Zuri/LINE adapter แล้ว HTTP clients ยังผ่าน core acceptance; PRP package scan ไม่มี imports ไป business modules

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Core

<a id="PRP-AT-055"></a>

### PRP-AT-055 — External LINE integration contract
**Requirement:** [PRP-FR-055](SRS-PRP.md#PRP-FR-055) | **Phase:** P1-C | **Proof:** integration + authorized live LINE

**Stimulus / expected assertions:** integration suite ตรวจ dedupe/signature/ACK/reply-push/uncertain send ตาม INT-LINE; core release แยกจาก connector release และ live canary

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Integration Adapter

<a id="PRP-AT-056"></a>

### PRP-AT-056 — Phase-boundary enforcement
**Requirement:** [PRP-FR-056](SRS-PRP.md#PRP-FR-056) | **Phase:** P1-A | **Proof:** contract

**Stimulus / expected assertions:** เก่าทุกคีย์ไม่มี media scope อัตโนมัติ; extension ผ่าน chat/voice regression; ไม่ต้องเปลี่ยน core identity หรือ client business schema

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Core

<a id="PRP-AT-057"></a>

### PRP-AT-057 — Isolation correctness
**Requirement:** [PRP-NFR-001](SRS-PRP.md#PRP-NFR-001) | **Phase:** P1-A | **Proof:** SECURITY

**Stimulus / expected assertions:** ทุก negative authorization และ artifact ownership case ต้องผ่าน ไม่มี unauthorized content หรือ action ที่ยอมรับได้แม้หนึ่งครั้ง

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-058"></a>

### PRP-AT-058 — Revocation bound
**Requirement:** [PRP-NFR-002](SRS-PRP.md#PRP-NFR-002) | **Phase:** P1-A | **Proof:** security integration

**Stimulus / expected assertions:** งานใหม่/dispatch/result-read ต้องสะท้อน revoke ภายใน 60s; cache invalidation test ที่หลาย process และกรณี identity store unavailable ต้อง fail closed

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-059"></a>

### PRP-AT-059 — Admission overhead
**Requirement:** [PRP-NFR-003](SRS-PRP.md#PRP-NFR-003) | **Phase:** P1-A | **Proof:** load mock

**Stimulus / expected assertions:** p95 <=250ms ที่ 10 requests/s นาน 5min ด้วย mocked backend; วัด auth+quota+reservation ไม่รวม queue/model; report sample count และ p99

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-060"></a>

### PRP-AT-060 — Warm chat latency
**Requirement:** [PRP-NFR-004](SRS-PRP.md#PRP-NFR-004) | **Phase:** P1-C | **Proof:** hardware W1

**Stimulus / expected assertions:** W1: TTFT p95 <=5s และ completed-request failure <=1%; output actual length ต้องรายงาน ไม่ถือ max_tokens ว่า output จริง

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-061"></a>

### PRP-AT-061 — Voice pipeline latency
**Requirement:** [PRP-NFR-005](SRS-PRP.md#PRP-NFR-005) | **Phase:** P1-C | **Proof:** hardware W2

**Stimulus / expected assertions:** W2 reference client audio->ASR->LLM->TTS: p95 <=45s สำหรับ 15s clip/<=128 output tokens/<=15s synthesized audio; ไม่รวม upload/LINE network

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-062"></a>

### PRP-AT-062 — Mixed-workload protection
**Requirement:** [PRP-NFR-006](SRS-PRP.md#PRP-NFR-006) | **Phase:** P1-C | **Proof:** hardware W3

**Stimulus / expected assertions:** W3: chat TTFT p95 <=2x isolated baseline และ <=5s, ไม่มี admitted OOM; report rejected/deadline/partial jobs ไม่ตัดออกเพื่อทำ percentile สวย

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-063"></a>

### PRP-AT-063 — Durability and settlement
**Requirement:** [PRP-NFR-007](SRS-PRP.md#PRP-NFR-007) | **Phase:** P1-B | **Proof:** fault injection

**Stimulus / expected assertions:** หลัง 202 accepted ต้องมี durable record ภายใต้ process restart; committed logical result settle ได้ครั้งเดียว; ไม่อ้าง exactly-once GPU computation

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-064"></a>

### PRP-AT-064 — ASR quality
**Requirement:** [PRP-NFR-008](SRS-PRP.md#PRP-NFR-008) | **Phase:** P1-B | **Proof:** audio quality

**Stimulus / expected assertions:** corpus versioned 120 clips/12 speakers: Thai clean CER<=15%, noisy<=25%, English WER<=20%; code-switch report แยก; critical-entity accuracy>=90% clean

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-065"></a>

### PRP-AT-065 — TTS quality
**Requirement:** [PRP-NFR-009](SRS-PRP.md#PRP-NFR-009) | **Phase:** P1-B | **Proof:** audio quality

**Stimulus / expected assertions:** อย่างน้อย 40 texts ไทย30/อังกฤษ10, raters>=3; per-language median intelligibility>=4/5 และ critical-entity pronunciation>=95%; >=1 approved voice/ภาษา

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-066"></a>

### PRP-AT-066 — No-speech gate
**Requirement:** [PRP-NFR-010](SRS-PRP.md#PRP-NFR-010) | **Phase:** P1-B | **Proof:** audio quality

**Stimulus / expected assertions:** silence/noise-only >=20 clips; >=95% คืน no-speech/unclear และไม่มี downstream auto action ใน reference integration

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-067"></a>

### PRP-AT-067 — Observability freshness
**Requirement:** [PRP-NFR-011](SRS-PRP.md#PRP-NFR-011) | **Phase:** P1-A | **Proof:** fault injection

**Stimulus / expected assertions:** poll default5s stale15s; dashboard แสดงอายุจริง; out-of-order/unknown metrics tests ต้องไม่สร้าง capacity ที่ไม่มีหลักฐาน

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-068"></a>

### PRP-AT-068 — Recovery objectives
**Requirement:** [PRP-NFR-012](SRS-PRP.md#PRP-NFR-012) | **Phase:** P1-C | **Proof:** restore rehearsal

**Stimulus / expected assertions:** candidate RPO<=24h สำหรับ host/disk disaster และ RTO<=4h; process restart ไม่สูญเสีย DB committed jobs; แยกสอง failure models ชัดเจน

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-069"></a>

### PRP-AT-069 — Accessible client flow
**Requirement:** [PRP-NFR-013](SRS-PRP.md#PRP-NFR-013) | **Phase:** P1-B | **Proof:** browser manual + e2e

**Stimulus / expected assertions:** keyboard path, visible focus/status, Thai rendering, mic-denied/upload fallback; ไม่มี forced autoplay; screen-reader labels สำหรับ record/stop/cancel

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-070"></a>

### PRP-AT-070 — Bounded resource use
**Requirement:** [PRP-NFR-014](SRS-PRP.md#PRP-NFR-014) | **Phase:** P1-B | **Proof:** adversarial load

**Stimulus / expected assertions:** API/decoder/queue/temp/storage limits ต้องบังคับได้และ cleanup orphan <=24h; malformed media ต้องไม่ exhaust control plane

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-071"></a>

### PRP-AT-071 — Reproducible configuration
**Requirement:** [PRP-NFR-015](SRS-PRP.md#PRP-NFR-015) | **Phase:** P1-C | **Proof:** release rehearsal

**Stimulus / expected assertions:** production pins runtime digest + model/profile revision + hardware calibration; change ต้อง requalify; rollback evidence ผูก exact manifest

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-072"></a>

### PRP-AT-072 — Independent operation
**Requirement:** [PRP-NFR-016](SRS-PRP.md#PRP-NFR-016) | **Phase:** P1-A | **Proof:** portability

**Stimulus / expected assertions:** CI/runbooks/core acceptance ต้องรันโดยไม่มี Zuri; gateway และ metadata export ไม่บังคับ vendor cloud subscription; isolate two client applications

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-073"></a>

### PRP-AT-073 — No hidden content egress
**Requirement:** [PRP-NFR-017](SRS-PRP.md#PRP-NFR-017) | **Phase:** P1-C | **Proof:** egress capture

**Stimulus / expected assertions:** P1 default deny third-party inference/telemetry payload egress; model downloads อยู่ install stage ที่ audit; network capture happy+failure ไม่มี content ออกนอก approved boundary

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-074"></a>

### PRP-AT-074 — Service honesty
**Requirement:** [PRP-NFR-018](SRS-PRP.md#PRP-NFR-018) | **Phase:** P1-C | **Proof:** operations review

**Stimulus / expected assertions:** ไม่มี uptime/throughput/HA claim จากชื่อ pool; all-node/control-plane failure และ job UNKNOWN ต้องมองเห็น; SLO report รวม errors/timeouts/rejections

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Quality

<a id="PRP-AT-075"></a>

### PRP-AT-075 — Private transport
**Requirement:** [PRP-SEC-001](SRS-PRP.md#PRP-SEC-001) | **Phase:** P1-A | **Proof:** security integration

**Stimulus / expected assertions:** negative route scan, wrong TLS identity และ unauthenticated engine routes ถูกบล็อก

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Security

<a id="PRP-AT-076"></a>

### PRP-AT-076 — Secret custody
**Requirement:** [PRP-SEC-002](SRS-PRP.md#PRP-SEC-002) | **Phase:** P1-A | **Proof:** security integration

**Stimulus / expected assertions:** secret scan ของ artifact/image/log/API/backup พร้อม rotation/recovery rehearsal

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Security

<a id="PRP-AT-077"></a>

### PRP-AT-077 — SSRF and egress
**Requirement:** [PRP-SEC-003](SRS-PRP.md#PRP-SEC-003) | **Phase:** P1-A | **Proof:** security integration

**Stimulus / expected assertions:** SSRF fixture IPv4/IPv6/redirect/rebind และ network capture ต้องผ่าน

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Security

<a id="PRP-AT-078"></a>

### PRP-AT-078 — Object authorization
**Requirement:** [PRP-SEC-004](SRS-PRP.md#PRP-SEC-004) | **Phase:** P1-A | **Proof:** security integration

**Stimulus / expected assertions:** cross-org/principal ID swap และ list filter tests ผ่าน

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Security

<a id="PRP-AT-079"></a>

### PRP-AT-079 — Untrusted input
**Requirement:** [PRP-SEC-005](SRS-PRP.md#PRP-SEC-005) | **Phase:** P1-A | **Proof:** security integration

**Stimulus / expected assertions:** model/tool/codec injection cases ไม่มี side effect หรือ privilege gain

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Security

<a id="PRP-AT-080"></a>

### PRP-AT-080 — Secure administration
**Requirement:** [PRP-SEC-006](SRS-PRP.md#PRP-SEC-006) | **Phase:** P1-A | **Proof:** security integration

**Stimulus / expected assertions:** CSRF/role escalation/bootstrap reuse/weak default credential negative tests

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Security

<a id="PRP-AT-081"></a>

### PRP-AT-081 — Voice rights and model provenance
**Requirement:** [PRP-SEC-007](SRS-PRP.md#PRP-SEC-007) | **Phase:** P1-B | **Proof:** security integration

**Stimulus / expected assertions:** release artifact ทุกชิ้นมี provenance/approval; missing license receipt block activation

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Security

<a id="PRP-AT-082"></a>

### PRP-AT-082 — Content minimization
**Requirement:** [PRP-SEC-008](SRS-PRP.md#PRP-SEC-008) | **Phase:** P1-A | **Proof:** security integration

**Stimulus / expected assertions:** trace/request/error paths ถูก scan รวม crash traces; sample metadata ไม่แฝง content

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Security

<a id="PRP-AT-083"></a>

### PRP-AT-083 — Deletion and cache boundary
**Requirement:** [PRP-SEC-009](SRS-PRP.md#PRP-SEC-009) | **Phase:** P1-B | **Proof:** security integration

**Stimulus / expected assertions:** delete-during-run, link revoke, restore-after-delete ผ่าน

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Security

<a id="PRP-AT-084"></a>

### PRP-AT-084 — Supply-chain pinning
**Requirement:** [PRP-SEC-010](SRS-PRP.md#PRP-SEC-010) | **Phase:** P1-A | **Proof:** security integration

**Stimulus / expected assertions:** reproducible build และ artifact tampering negative test

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Security

<a id="PRP-AT-085"></a>

### PRP-AT-085 — Trust-owner limitation
**Requirement:** [PRP-SEC-011](SRS-PRP.md#PRP-SEC-011) | **Phase:** P1-A | **Proof:** security integration

**Stimulus / expected assertions:** deployment trust statement และ tests ไม่เปิด cross-customer/hostile tenants โดยอัตโนมัติ

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Security

<a id="PRP-AT-086"></a>

### PRP-AT-086 — Service credential boundary
**Requirement:** [PRP-SEC-012](SRS-PRP.md#PRP-SEC-012) | **Phase:** P1-A | **Proof:** security integration

**Stimulus / expected assertions:** inspect worker environment + denied network access + stolen low-scope key test

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Security

<a id="PRP-AT-087"></a>

### PRP-AT-087 — Python-first control plane
**Requirement:** [PRP-NFR-019](SRS-PRP.md#PRP-NFR-019) | **Phase:** P1-A | **Proof:** build + dependency isolation

**Stimulus / expected assertions:** clean CPU-only control environment build/import/health ได้โดยไม่มี desktop หรือ GPU runtime; review dependency graph และ ADR ข้อยกเว้น; ไม่ตีความภาษาเป็นผล benchmark

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Core

<a id="PRP-AT-088"></a>

### PRP-AT-088 — Evidence-based reuse before build
**Requirement:** [PRP-NFR-020](SRS-PRP.md#PRP-NFR-020) | **Phase:** G0 | **Proof:** design evidence + isolated spikes

**Stimulus / expected assertions:** WP24 มีเอกสารเปรียบเทียบ A/B, exact versions, evidence/NOT_RUN/BLOCKED และ approved gap budget ก่อน G0 exit; C-Ray ประเมินเมื่อมี trigger เท่านั้น; security gap ไม่ถูกลดเกณฑ์เพื่อเลือกเครื่องมือ

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Architecture + QA

<a id="PRP-AT-089"></a>

### PRP-AT-089 — API and model process isolation
**Requirement:** [PRP-NFR-021](SRS-PRP.md#PRP-NFR-021) | **Phase:** P1-A | **Proof:** process integration + real runtime

**Stimulus / expected assertions:** เพิ่ม API process count แล้ว model PID/count/residency ไม่เปลี่ยน; no-GPU/import smoke ผ่าน; API ตอบ health/cancel ได้ระหว่าง worker งานยาว; cancel thread/future ไม่ถูกนับเป็น compute stopped

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Core + Runtime

<a id="PRP-AT-090"></a>

### PRP-AT-090 — Reproducible isolated Python environments
**Requirement:** [PRP-NFR-022](SRS-PRP.md#PRP-NFR-022) | **Phase:** P1-A | **Proof:** build + supply-chain review

**Stimulus / expected assertions:** สร้างซ้ำจาก clean environment และ lock/image digest ได้; control image ไม่มี ML model payload; SBOM/license/egress review และ upgrade/rollback tests มีหลักฐาน; source template ไม่ถูกอ้างเป็น actual lock

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Build + Operations

<a id="PRP-AT-091"></a>

### PRP-AT-091 — Delegated framework authority conformance
**Requirement:** [PRP-NFR-023](SRS-PRP.md#PRP-NFR-023) | **Phase:** P1-A | **Proof:** framework contract + race + fault

**Stimulus / expected assertions:** ทดสอบ auth spoof/revoke, framework internal retry, hidden route change, two-process race และ supervisor restart; ไม่พิสูจน์ placement ได้ต้องปิด profile หรือใช้ approved conservative envelope ที่ผ่าน gate; encrypted recoverable user key ไม่ผ่าน FR-005

**Status:** NOT_RUN | **Evidence:** none | **Owner:** Security + Admission

<a id="PRP-AT-092"></a>

### PRP-AT-092 — Portable framework binding and exit
**Requirement:** [PRP-NFR-024](SRS-PRP.md#PRP-NFR-024) | **Phase:** P1-C | **Proof:** portability + migration rehearsal

**Stimulus / expected assertions:** fake adapter replacement ผ่าน client conformance; replay approved synthetic workloads ผ่าน candidate replacement เมื่อมี; export excludes plaintext keys; รักษางาน uncertain/erasure และบันทึกขั้น key rotation แทนการอ้าง portable secret ที่อ่านคืนไม่ได้

**Status:** NOT_RUN | **Evidence:** none | **Owner:** API + Operations


## 4. Composite release scenarios
RX01 Independence: clean install without Zuri; call from independent script and playground; disable app integrations; prove core continues; no business DB access at network layer.
RX02 Concurrent admission: two control processes race for last quota/resource slot on same GPU and alias URL; only one reservation succeeds; other uses B or bounded failure.
RX03 Ambiguous dispatch: coordinator dies before send, after send, after model finished and before settlement; no blind replay; dedupe result/usage; quarantine only where needed.
RX04 Voice partial: ASR succeeds, chat succeeds, TTS fails; client keeps answer, no repeated chat/tool/channel write, TTS retry creates only speech operation.
RX05 Privacy erase: delete raw/output while queued/running/streaming; late worker finishes; restore old backup; content never reappears without authorization.
RX06 Platform outage: DB/observer/control-host unavailable; no local-counter bypass; active work reconciles; recovery and documented availability limits match evidence.
RX07 LINE delivery: duplicate webhook, ack consumes reply, push timeout/409 accepted, artifact link expiry and data policy refusal; no duplicate sender or inference rerun.
RX08 Media phase deny: Phase1 key invokes image/video/clone/plugin endpoint; deny; add approved P2 grant later only after new qualification and P1 regression.

## 5. Evidence/reporting rules
Metrics report denominators: attempted/admitted/completed/failed/rejected/timeout/cancel/partial and actual output lengths. Percentiles do not erase failure cases. Separate warm/cold and isolated/mixed placement. Include CPU/GPU background workloads.

Corpus versions, scoring normalizer and target thresholds freeze before collection. A reviewer signs actual model/voice rights and outcome. Demo or README timing is not benchmark evidence. If target changes, issue CR with old/new target and rerun; do not relabel an old failure.

## 6. Release gates
Security/object isolation, secret leakage, unsafe uncertain lease release, unsupported egress and duplicate logical settlement failures block core release regardless of overall score. Hardware-dependent NOT_RUN blocks hardware activation. Live LINE NOT_RUN blocks only LINE integration, not independent core install/API acceptance.

Document validation in this delivery checks references and formats; it is explicitly recorded separately in QA-REPORT and does not change the NOT_RUN values above.

## Python/framework test fixture additions
AT087..092 ไม่ใช่ผลทดสอบ ให้ใช้สอง API processes และ actual runtime identity ที่ตรวจได้ ทดสอบ hidden retries ของ gateway/SDK และ manager worker selection ด้วย fault injection การทดสอบ initial keys ต้องตรวจทั้ง persistence และ reveal APIs ของ authority ที่เลือก

AT089 แยก CPU-only API startup proof ออกจากการพิสูจน์ว่า API-worker scaling ไม่เพิ่ม GPU model count; mock process list ไม่เป็น hardware evidence AT088 ต้องมี candidate evidence ก่อน G0 exit ส่วน formal A/B load/voice/recovery tests ยังใช้ workload/corpus เดิม; ไม่เอา source review มาแทน measured PASS
