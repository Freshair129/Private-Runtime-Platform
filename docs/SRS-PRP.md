---
document_id: SRS-PRP
title: "SRS | PRP Software Requirements"
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

# SRS | PRP Software Requirements

**PRP — Private Runtime Platform | v0.3.0 | 2026-09-20 | Draft for review**

เอกสารที่เกี่ยวข้อง: [PRD](PRD-PRP.md) · [API](API-PRP.md) · [Tests](TEST-PRP.md) · [Roadmap](ROADMAP-PRP.md) · [Sources](SOURCES-PRP.md)

## 1. Scope, authority และ normative language
SRS นี้เป็น requirement authority ของ PRP v0.3.0 draft และแยก core platform ออกจาก integration adapters คำว่า ต้อง/ห้าม คือ proposed MUST เมื่อ baseline ถูกอนุมัติ คำว่า candidate/target/default ต้องยืนยันก่อน formal qualification ไม่ใช่ผล benchmark

เอกสาร SRS-Self-Hosted-Inference-Pool-Chat-Voice-v0.1.0 เป็น historical input [SRC-B01] ส่วนที่เคยให้ Zuri Identity/Integration/Agent ถือสิทธิ์หรือ GPU lease ถูกแทนด้วย PRP-owned contracts ในร่างนี้ การเปลี่ยนนี้ไม่แก้ย้อนหลังหรือถอนการอนุมัติของเอกสาร Zuri เก่า และไม่จองเลขใน Zuri registry

รหัส PRP-FR/NFR/SEC/P2 เป็น stable IDs ของชุด PRP เท่านั้น Markdown นี้เป็น canonical requirement source; registry JSON, traceability, Word และภาพเป็น derived views ไม่แก้ข้อความข้อกำหนดแยกกัน

## 2. Operating context
มี compute hosts A (12 GB nominal VRAM) และ B (16 GB nominal VRAM) ใน LAN เดียวกัน เป็น independent full-model replicas ไม่รวม VRAM Control services ใช้ CPU/RAM/disk ของเครื่องที่จัดสรร ไม่จำเป็นต้องซื้อเครื่องที่สาม แต่การอยู่ A หมายถึง A เป็น control-plane SPOF

P1 deployment: หนึ่ง trusted PRP organization หลาย teams/applications; identity schema ต้องรองรับ isolation fixture ข้าม organization แต่ไม่เปิด untrusted customer sharing บน engine เดียว Production รุ่น GPU/CPU/RAM/OS/network/model ยังไม่ confirmed

P1-A chat foundation, P1-B ASR/TTS + async jobs/artifacts + independent playground, P1-C qualification/pilot; P2 generative image/video เป็น envelope เท่านั้น ไม่รวม call/full duplex/voice cloning/music โดยปริยาย

## 3. Ownership และ acceptance boundaries
| Concern | Owner | ข้อห้าม |
|---|---|---|
| Routing candidates | PRP Router | ไม่ bypass Admission ไม่เป็น GPU engine |
| Quota/physical capacity | PRP Admission Coordinator | ไม่ใช้ process-local counters เป็น authority |
| Job/attempt/outbox | PRP Execution/Jobs | ไม่ส่ง LINE หรือ execute business tools |
| Model compute/local batching | vLLM / Speech Runtime | ไม่มี LINE token/CRM root credential |
| Conversation/ASR->LLM->TTS | Client app / reference playground | ไม่เขียน PRP resource tables โดยตรง |
| LINE ingress/delivery | External LINE adapter (Zuri candidate) | ไม่เป็น dependency ของ core PRP |
| Registry/secrets/ops | PRP control modules | operator ไม่ได้ raw content access โดยปริยาย |

Core readiness และ integration readiness แยกกัน ต้องมี independent client test แม้ integrated LINE canary ยัง blocked

PRP control เป็น Python-first; runtime libraries/processes เป็น implementation ที่เปลี่ยนได้ Model loading/batching ไม่อยู่ใน HTTP handler Ownership ในตารางหมายถึงผู้รับผิดชอบ contract ซึ่งอาจ delegate ไปยังเครื่องมือที่ผ่าน tests ไม่บังคับสร้าง database หรือ service ซ้ำ รายละเอียด PRP-NFR-019..024

## 4. Definitions และ invariants
I01: ไม่มี upstream dispatch ที่ไม่เคยได้รับ current authorization และ durable attempt identity
I02: การจองทรัพยากรในทุก gateway process ใช้ database-backed authority เดียวต่อ physical GPU/runtime
I03: resident model memory ไม่ถูกคืนเพียงเพราะ request lease จบ
I04: client timeout/cancel/DB lease expiry ไม่ใช่หลักฐานว่า GPU หยุด
I05: async 202 หมายถึง durable accepted ไม่ใช่ compute complete และไม่ใช่ delivered
I06: model output/tool call ไม่มอบสิทธิ์ให้ execute side effects
I07: ชื่อ alias เดียวกันไม่รับประกัน profile/model เดียวกัน ต้องผ่าน qualification
I08: metadata user tag ไม่เป็น identity และ signed URL เป็น bearer capability ไม่ใช่ private-by-default
I09: PRP core ไม่มี business conversation state; external voice-turn PARTIAL_SUCCESS ไม่ใช่สถานะรวมของ atomic inference job
I10: cloud inference fallback ปิดในทุก happy/failure path ของ P1
I11: ownership ของ PRP เป็น contract authority ไม่ใช่ข้อบังคับให้สร้าง implementation ซ้ำ
I12: framework ต้องไม่ย้ายหรือ retry งานโดยไม่มี resource admission ที่ตรง actual execution

## 5. Functional requirements
แต่ละรายการระบุ observable acceptance, phase, owner, epic และ test หลัก รายละเอียด API อยู่ API-PRP แต่ห้ามขัด SRS; แบบ internal tables ใน ARCH-PRP เป็น logical design ไม่ใช่ migration ที่รันแล้ว

### 5.1 Identity, keys และ quotas

<a id="PRP-FR-001"></a>

#### PRP-FR-001 — Independent bootstrap
PRP ต้องติดตั้ง bootstrap ผู้ดูแล ออกคีย์ และให้บริการได้โดยไม่มี Zuri, FUNG, Lalin Studio หรือฐานข้อมูลธุรกิจของแอปเหล่านั้น

**รับมอบ:** ติดตั้ง PRP ใน environment ที่ไม่มีแอปดังกล่าว; client HTTP ธรรมดาใช้ models/chat ได้ และเมื่อเพิ่ม speech worker ใช้ ASR/TTS ได้

**Trace:** P1-A / E01 / owner Core / PRP-AT-001 / D01

<a id="PRP-FR-002"></a>

#### PRP-FR-002 — Application-neutral boundary
Public API และ schema หลักต้องไม่บังคับ Zuri business/thread/MSP/LINE ID; external_reference เป็น opaque metadata ที่ไม่ให้สิทธิ์

**รับมอบ:** schema lint และ contract test ปฏิเสธการอาศัย metadata เป็น authorization; ตัวอย่าง client ไม่ import SDK ของแอป

**Trace:** P1-A / E01 / owner Core / PRP-AT-002 / D03

<a id="PRP-FR-003"></a>

#### PRP-FR-003 — PRP-owned organization isolation
ทุก key, job, quota และ artifact ต้องมี PRP organization และ owning principal ที่ resolve จาก verified identity; P1 ใช้หนึ่ง trusted organization หลายทีม/แอปแต่ schema รองรับการแยก organization

**รับมอบ:** ปลอม org_id/team/job/artifact ใน request ไม่ข้ามสิทธิ์; fixture อีก organization ถูกปฏิเสธ; ไม่เปิดใช้ hostile multi-tenant engine sharing

**Trace:** P1-A / E01 / owner Identity / PRP-AT-003 / D17

<a id="PRP-FR-004"></a>

#### PRP-FR-004 — Roles and delegated management
ต้องแยก platform operator, organization admin, member และ application service principal; admin ไม่ยกระดับเกิน grant ของผู้มอบ; operator ไม่ได้ content-read โดยปริยาย

**รับมอบ:** ทดสอบ role/action matrix รวมผู้ดูแลอ่าน raw audio ไม่ได้โดยไม่มี grant; negative cases ผ่านทั้งหมด

**Trace:** P1-A / E01 / owner Identity / PRP-AT-004 / D05

<a id="PRP-FR-005"></a>

#### PRP-FR-005 — Scoped key issuance
ออก inference key แยกรายคน/แอป มี capability/model grants, expiry, quota policy; plaintext แสดงครั้งเดียว; เก็บ verifier และ key prefix ไม่เก็บคีย์อ่านคืนได้

**รับมอบ:** สร้างคีย์ ใช้แล้วตรวจ DB/API/log ไม่พบ plaintext; chat-only key ใช้ speech/admin ไม่ได้

**Trace:** P1-A / E01 / owner Identity / PRP-AT-005 / D08

<a id="PRP-FR-006"></a>

#### PRP-FR-006 — Key rotation and revocation
ต้อง rotate แบบจำกัดช่วง overlap ระงับ revoke และ expire ได้; ลดสิทธิ์แล้วตรวจใหม่ก่อน dispatch/result access; ไม่เปลี่ยนคีย์เก่าให้ได้ scope เพิ่มอัตโนมัติ

**รับมอบ:** revoke มีผลตาม NFR-002; งานค้างถูกยกเลิกหรือ fence; overlap default 24h เป็นค่าสูงสุดที่ปรับลดได้

**Trace:** P1-A / E01 / owner Identity / PRP-AT-006 / D08

<a id="PRP-FR-007"></a>

#### PRP-FR-007 — Capability and model grants
ต้องมี chat:invoke, asr:invoke, tts:invoke, jobs:read/cancel, artifacts:read/delete และ management permissions แยก; listing เห็นเฉพาะสิ่งที่คีย์ใช้ได้

**รับมอบ:** listing ไม่เผย node IP/secret; job read/cancel และ artifact read ยังตรวจ object ownership เพิ่มจาก scope

**Trace:** P1-A / E01 / owner Identity / PRP-AT-007 / D05

<a id="PRP-FR-008"></a>

#### PRP-FR-008 — Atomic quotas and honest usage
ต้องจอง requests, token budget, audio seconds, queued/active jobs และ storage allowance ตาม policy ที่เข้มที่สุดแบบ atomic; แยก reserved/actual/estimated/unavailable

**รับมอบ:** หลายคีย์ของคนเดียวและหลาย gateway process แข่งกันไม่เกิน principal/org budget; usage ไม่ทราบไม่ถูกบันทึกเป็นศูนย์จริง

**Trace:** P1-A / E01 / owner Admission / PRP-AT-008 / D09

<a id="PRP-FR-009"></a>

#### PRP-FR-009 — Service-account accountability
แอปต้องใช้ service key แยกจากคีย์คน; client-provided user tag ใช้แสดง usage ได้แต่ไม่ลด quota หลักหรือมอบสิทธิ์; trusted end-user limits ต้องมี delegated identity contract แยก

**รับมอบ:** เปลี่ยน user tag ไม่ bypass service/org cap; P1 ไม่มี delegated identity ที่ผ่าน review ต้องบังคับ service-key quota เท่านั้น

**Trace:** P1-A / E01 / owner Identity / PRP-AT-009 / D17

### 5.2 Registry และ PRP Router

<a id="PRP-FR-010"></a>

#### PRP-FR-010 — Controlled node enrollment
operator ลงทะเบียน origin/ports, node_id, runtime_id, physical resource IDs และ secret reference ผ่าน allowlist; client ทั่วไปไม่เลือก upstream URL เอง

**รับมอบ:** ปฏิเสธ metadata IP, redirect, DNS rebinding และ endpoint นอก allowlist ก่อนเชื่อมต่อ; mutation มี version guard

**Trace:** P1-A / E02 / owner Registry / PRP-AT-010 / D10

<a id="PRP-FR-011"></a>

#### PRP-FR-011 — Qualification receipt
node จะรับงานได้หลังพิสูจน์ verified private transport, good/wrong/missing credentials, model discovery และ synthetic capability test; receipt ผูก config/credential/model epoch

**รับมอบ:** health 200 แต่ protected API ใช้คีย์ผิดแล้วยังผ่าน ต้อง qualification fail; เปลี่ยน epoch แล้ว receipt เก่าใช้ไม่ได้

**Trace:** P1-A / E02 / owner Registry / PRP-AT-011 / D10

<a id="PRP-FR-012"></a>

#### PRP-FR-012 — Pinned capability profiles
ต้อง pin engine image/release, model artifact/tokenizer/template revisions, quantization, context, language, tool parser และ resource profile; alias ไม่ใช่หลักฐาน weights ตรงกัน

**รับมอบ:** node สองตัวที่ alias เหมือนแต่ profile ไม่ตรงไม่อยู่ replica set เดียวกัน; ไม่ยืนยัน 9B พอดี VRAM โดยดูขนาดชื่อโมเดล

**Trace:** P1-A / E02 / owner Registry / PRP-AT-012 / D18

<a id="PRP-FR-013"></a>

#### PRP-FR-013 — Physical resource deduplication
origin หลายชื่อที่ชี้ runtime/GPU เดียวกันต้องแชร์ physical budget เดียว; CPU/RAM/VRAM และ model-residency reservation แยกจาก per-request lease

**รับมอบ:** เพิ่ม alias URL แล้ว capacity ไม่เพิ่ม; worker restart เปลี่ยน instance epoch แต่ไม่สร้าง GPU สมมติใบใหม่

**Trace:** P1-A / E02 / owner Admission / PRP-AT-013 / D18

<a id="PRP-FR-014"></a>

#### PRP-FR-014 — Fresh health observations
observer ต้องบันทึก observed_at/received_at, epoch, readiness และ evidence quality; missing/stale metrics เป็น UNKNOWN ไม่ใช่ zero utilization

**รับมอบ:** out-of-order/old epoch ไม่ทับใหม่; observation age เกิน policy หยุด admission; dashboard ปิดแต่ observer ยังทำงาน

**Trace:** P1-A / E02 / owner Observability / PRP-AT-014 / D14

<a id="PRP-FR-015"></a>

#### PRP-FR-015 — Safe runtime lifecycle
ต้องมี REGISTERED, QUALIFYING, READY, DEGRADED, DRAINING, QUARANTINED, OFFLINE, DISABLED; drain ไม่รับใหม่และไม่ฆ่างานเดิม; resume ต้องตรวจ qualification ปัจจุบัน

**รับมอบ:** drain ระหว่าง stream ไม่ตัดงานเอง; stale enable ถูกปฏิเสธ; restore binding เริ่ม DISABLED

**Trace:** P1-A / E02 / owner Registry / PRP-AT-015 / D14

<a id="PRP-FR-016"></a>

#### PRP-FR-016 — PRP Router selection
Router เลือกเฉพาะ candidate ที่สิทธิ์/profile/freshness/deadline ผ่าน แล้วให้ Admission จองทรัพยากรแบบ atomic ก่อน dispatch; P1 prefer A แล้ว spill B เมื่อปลอดภัย

**รับมอบ:** A เต็มหรือช้าเกิน budget ให้งานใหม่ไป B; ไม่มี active KV migration; B ไม่ถูกเลือกเพียงเพราะ VRAM มากกว่า

**Trace:** P1-A / E02 / owner Router / PRP-AT-016 / D09

### 5.3 Admission, execution และ uncertainty

<a id="PRP-FR-017"></a>

#### PRP-FR-017 — Durable admission transaction
ต้อง commit invocation/job, quota hold, queue slot และ outbox ใน transaction หรือกลไกเทียบเท่าก่อน 202; sync request ต้องมี attempt record ก่อน provider send

**รับมอบ:** kill ก่อน/หลัง commit ไม่ทำให้ accepted job หาย; duplicate outbox delivery ไม่สร้าง second logical admission

**Trace:** P1-A / E02 / owner Admission / PRP-AT-017 / D09

<a id="PRP-FR-018"></a>

#### PRP-FR-018 — Shared GPU reservation authority
PRP เป็นผู้อนุมัติ resource lease ข้าม chat/voice ทั้งหมด; runtime local batching ยังอยู่ที่ engine; speech แชร์ GPU ได้เฉพาะ resident-envelope ที่วัดแล้ว

**รับมอบ:** vLLM และ speech process แข่งกันไม่เกิน envelope; ไม่มีการใช้ free VRAM snapshot เป็น guarantee หรือปล่อย model-residency เมื่องานจบ

**Trace:** P1-B / E02 / owner Admission / PRP-AT-018 / D04

<a id="PRP-FR-019"></a>

#### PRP-FR-019 — Bounded fair queues
ต้องมี interactive-chat กับ speech queue ที่มี org/principal caps, max wait และ starvation protection; queue ไม่ใช่จำนวน concurrent GPU slots

**รับมอบ:** flood จาก app A ไม่ขัดการรับงาน app B ที่มี grant ภายใต้ fair-share policy; งานหมด wait ออกด้วยเหตุผลไม่ค้างไม่จำกัด

**Trace:** P1-A / E02 / owner Admission / PRP-AT-019 / D09

<a id="PRP-FR-020"></a>

#### PRP-FR-020 — Uncertain execution fencing
connection loss หลัง dispatch ต้องเก็บ UNKNOWN execution และ quarantine resource จนยืนยันจบหรือ supervisor ที่อนุญาตพิสูจน์ termination; lease expiry ลำพังไม่พอ

**รับมอบ:** kill coordinator/timeout client ขณะ worker รัน: ไม่มี capacity ถูกคืนก่อนหลักฐาน; late result ไม่ข้าม deletion/revocation fence

**Trace:** P1-A / E02 / owner Execution / PRP-AT-020 / D13

<a id="PRP-FR-021"></a>

#### PRP-FR-021 — Absolute deadlines and cancellation
ทุก operation มี absolute deadline ไม่ reset ตอน retry; queued cancel จบได้ทันที; dispatched cancel เป็น request จนยืนยันหยุด; timeout outcome แยกจาก execution status

**รับมอบ:** cancel ซ้ำ idempotent; CANCEL_REQUESTED ไม่แสดงเป็น compute stopped; stream/worker ที่ไม่ abort ได้ถูก quarantine อย่างตรงไปตรงมา

**Trace:** P1-A / E02 / owner Execution / PRP-AT-021 / D12

<a id="PRP-FR-022"></a>

#### PRP-FR-022 — Retry classification
retry อัตโนมัติได้เฉพาะก่อน transmission หรือหลังยืนยัน attempt เดิมจบและอยู่ใน policy; ไม่ hedged request ใน P1; tool execution และ channel send ไม่อยู่ใน retry ของ PRP

**รับมอบ:** inject uncertain post-dispatch error แล้วไม่มีการเรียก node B ซ้ำเงียบ ๆ; error ระบุ safe_to_retry และ job/request reference

**Trace:** P1-A / E02 / owner Execution / PRP-AT-022 / D13

### 5.4 Chat API

<a id="PRP-FR-023"></a>

#### PRP-FR-023 — Model catalog
GET /v1/models ต้องคืน aliases ที่ใช้ได้พร้อม qualified capabilities ผ่าน PRP metadata endpoint; model identity ในผลต้อง trace profile revision ได้

**รับมอบ:** คีย์ chat ไม่เห็น ASR/TTS ที่ไม่ได้ grant; unready deployment ไม่ถูกโฆษณาว่าพร้อมใช้

**Trace:** P1-A / E03 / owner API / PRP-AT-023 / D06

<a id="PRP-FR-024"></a>

#### PRP-FR-024 — Chat completion and context budget
POST /v1/chat/completions ต้องรองรับ text messages, JSON/non-stream และ documented fields; tokenize input+template+tools+reserved output ก่อนส่ง; field ไม่รองรับต้อง reject

**รับมอบ:** context เกินคืน 422 ก่อน dispatch; ไม่ตัด system/tool rules เงียบ ๆ; JSON response ผ่าน published schema

**Trace:** P1-A / E03 / owner Chat Adapter / PRP-AT-024 / D06

<a id="PRP-FR-025"></a>

#### PRP-FR-025 — Streaming honesty
SSE ต้องคง request/attempt identity และ terminal outcome; stream ขาดหลังมี output ห้ามต่อคำตอบจาก node ใหม่เป็น stream เดิม

**รับมอบ:** interrupted SSE ส่ง error event ถ้ายังเชื่อมต่อได้แล้วปิด; ไม่มี successful DONE สำหรับ failure; client disconnect trigger cancel/fence

**Trace:** P1-A / E03 / owner Chat Adapter / PRP-AT-025 / D06

<a id="PRP-FR-026"></a>

#### PRP-FR-026 — Tools as data only
รับ tool schema/คืน tool calls ได้เฉพาะ qualified profile; PRP ห้าม execute business tools, MCP, shell, RAG fetch หรือ agent loop จาก model output

**รับมอบ:** model ขอ tool write หรือ URL fetch ไม่เกิด side effect ที่ PRP; unsupported tool parser ปฏิเสธก่อน dispatch

**Trace:** P1-A / E03 / owner Chat Adapter / PRP-AT-026 / D03

<a id="PRP-FR-027"></a>

#### PRP-FR-027 — Usage receipts
คืน token/audio usage ที่วัดจริงหรือระบุ estimated/unavailable พร้อม units, profile และ attempt; internal retries ไม่ถูกนับเป็นคำขอ client ใหม่แต่ต้องเห็น compute cost ภายใน

**รับมอบ:** runtime ไม่ส่ง usage แล้ว receipt ไม่แต่ง actual; reconciliation ซ้ำไม่ double charge reservation/usage

**Trace:** P1-A / E03 / owner Accounting / PRP-AT-027 / D16

<a id="PRP-FR-028"></a>

#### PRP-FR-028 — Stateless inference default
PRP ไม่เก็บ conversation memory หรือแอบอ่านฐานข้อมูลแอป; sync chat prompt/result ไม่ persist เป็น default ยกเว้น encrypted ephemeral retry record ที่ explicitly enabled

**รับมอบ:** แชตครั้งถัดไปโดยไม่มี history ไม่ดึงข้อความครั้งก่อน; audit/log default ไม่มี raw content; native async payload มี TTL ตาม DATA

**Trace:** P1-A / E03 / owner Core / PRP-AT-028 / D19

### 5.5 ASR/TTS

<a id="PRP-FR-029"></a>

#### PRP-FR-029 — Bounded audio upload
รับ WAV, MP3, M4A/AAC, WebM/Opus ตาม decoder profile ที่ qualification แล้ว; จำกัด 10 MiB และ 60s เป็น pilot default ทั้ง encoded/decoded

**รับมอบ:** extension spoof, file too large, actual duration เกิน, empty upload และ codec ไม่รองรับมี distinct errors; preflight จำกัด streaming read

**Trace:** P1-B / E04 / owner Artifact / PRP-AT-029 / D07

<a id="PRP-FR-030"></a>

#### PRP-FR-030 — Sandboxed media decoding
decode ด้วย low-privilege process ที่ไม่มี network และกำหนด CPU/RAM/decoded-size/time budget; normalize ตาม ASR profile โดยเก็บ original hash

**รับมอบ:** malformed/bomb/polyglot ไม่ค้าง worker ไม่ออก network; decoded cap และ timeout ทำงาน; temp files ถูก cleanup

**Trace:** P1-B / E04 / owner Speech Adapter / PRP-AT-030 / D20

<a id="PRP-FR-031"></a>

#### PRP-FR-031 — ASR contract
รองรับไทย อังกฤษ และ language hint/auto-detect ใน model profile; คืน transcript, detected language, duration, segment timestamps เมื่อมี; ไม่แปลอัตโนมัติ

**รับมอบ:** corpus ผ่าน NFR-008; language probability ไม่ถูกคืนเป็น confidence ของ transcript; ไม่มี timestamp/confidence ที่แต่งขึ้น

**Trace:** P1-B / E04 / owner Speech Adapter / PRP-AT-031 / D07

<a id="PRP-FR-032"></a>

#### PRP-FR-032 — No-speech and unclear outcome
ต้องแยก NO_SPEECH กับ AUDIO_UNINTELLIGIBLE/unclear เมื่อมีหลักฐานตาม profile; ไม่สร้างคำตอบ LLM จาก silence โดยอัตโนมัติ

**รับมอบ:** silence/noise suite ไม่กระตุ้น downstream chat ใน reference client; ล้มเหลวต้องมีเหตุผลที่คนใช้แก้ไขได้

**Trace:** P1-B / E04 / owner Speech Adapter / PRP-AT-032 / D07

<a id="PRP-FR-033"></a>

#### PRP-FR-033 — Approved TTS voices
TTS ใช้ approved preset registry ที่มี model/voice revision, language และ license/voice-rights evidence; P1 ไม่มี upload voice reference หรือ clone API สำหรับผู้ใช้

**รับมอบ:** unapproved voice/model path/URL ถูกปฏิเสธ; preset ที่ภายในใช้ reference audio ต้องเป็น asset ที่ได้รับสิทธิ์และตรึงแล้ว

**Trace:** P1-B / E04 / owner Speech Adapter / PRP-AT-033 / D07

<a id="PRP-FR-034"></a>

#### PRP-FR-034 — Speech text fidelity
normalization ต้อง versioned และรักษาความหมายสำคัญ; จำกัด 800 code points หลัง normalization และ output ไม่เกิน 60s เป็น defaults; ไม่สรุปข้อความแทนต้นฉบับเงียบ ๆ

**รับมอบ:** เงิน วันที่ ชื่อสินค้าและตัวเลขตรงกับ golden cases; oversized request ได้ 422 ไม่ถูกตัดโดยไม่แจ้ง

**Trace:** P1-B / E04 / owner Speech Adapter / PRP-AT-034 / D07

<a id="PRP-FR-035"></a>

#### PRP-FR-035 — Speech response contracts
sync ASR คืน JSON และ sync TTS คืน WAV/MP3 bytes ที่ validate แล้ว; เกิน estimated sync budget ให้ ASYNC_REQUIRED ก่อน dispatch; ไม่คืน job JSON แทน audio 200

**รับมอบ:** MIME/header/sample metadata ตรงไฟล์; async route ใช้ 202 แยก; TTS fail ไม่สร้างไฟล์สำเร็จ 0 bytes

**Trace:** P1-B / E04 / owner API / PRP-AT-035 / D07

### 5.6 Jobs และ artifacts

<a id="PRP-FR-036"></a>

#### PRP-FR-036 — Native asynchronous operations
POST /prp/v1/jobs รับเฉพาะ job kind ที่อนุญาตใน phase; P1 รองรับ asr และ tts เท่านั้น; payload+policy snapshot+deadline durable ก่อน 202

**รับมอบ:** รีสตาร์ตแล้วยังอ่าน job/state ได้; ไม่รับ arbitrary DAG, voice-turn agent หรือ generative image/video ใน P1

**Trace:** P1-B / E05 / owner Jobs / PRP-AT-036 / D12

<a id="PRP-FR-037"></a>

#### PRP-FR-037 — Idempotent job creation
native job ใช้ Idempotency-Key ผูก org+principal+route+canonical payload digest; ซ้ำ same payload คืน job เดิม ต่าง payload 409; เก็บ dedupe ไม่น้อยกว่า job horizon+24h

**รับมอบ:** สอง process ส่งพร้อมกันได้ logical job เดียว; เปลี่ยนคีย์แต่ principal เดิมไม่เลี่ยง dedupe; deleted job คืน tombstone ไม่ resurrect

**Trace:** P1-B / E05 / owner Jobs / PRP-AT-037 / D12

<a id="PRP-FR-038"></a>

#### PRP-FR-038 — Job visibility and control
GET/list/cancel ต้องตรวจ scope+owner/team grant ทุกครั้ง; job outcome, execution state, resource state และ artifact state แยกกัน; paginated list ห้าม cross-org

**รับมอบ:** เดา job_id หรือรับ id จากอีกคนยังเข้าไม่ได้; TIMEOUT+UNKNOWN ปรากฏตรงจริง; cancel-after-terminal ไม่เปลี่ยนผลเดิม

**Trace:** P1-B / E05 / owner Jobs / PRP-AT-038 / D12

<a id="PRP-FR-039"></a>

#### PRP-FR-039 — Artifact ownership
input/output/temp artifact ต้องมี internal UUID, org/principal, checksum, MIME, duration, lineage, expiry และ storage port; ไม่รับ arbitrary filesystem path

**รับมอบ:** job A อ้าง artifact B ที่ไม่ grant ได้ 404; list/download/delete authorize ใหม่; worker รับ scoped artifact reference ไม่ได้ storage master key

**Trace:** P1-B / E05 / owner Artifact / PRP-AT-039 / D19

<a id="PRP-FR-040"></a>

#### PRP-FR-040 — Controlled delivery grants
authenticated artifact read เป็น default; grant แบบ HTTPS bearer link ทำได้เฉพาะ principal มี share grant และ policy อนุญาต พร้อม TTL/revoke และไม่ใส่ PII/key ใน URL

**รับมอบ:** expired/revoked link ใช้ไม่ได้; multi-fetch ทำได้ใน TTL; highly-private policy ไม่ออก bearer link; PRP ไม่ส่ง LINE เอง

**Trace:** P1-B / E05 / owner Artifact / PRP-AT-040 / D11

<a id="PRP-FR-041"></a>

#### PRP-FR-041 — Retention and erasure
ต้องลบ orphan/raw/output ตาม TTL และคำสั่งผู้มีสิทธิ์; erasure tombstone ป้องกัน late result และ restore resurrect; metadata/content มี retention แยก

**รับมอบ:** delete ระหว่าง execution แล้วผลลัพธ์ไม่กลับมา; restore reconcile erasure ledger ก่อนเปิด read; document backup expiry residuals

**Trace:** P1-B / E05 / owner Artifact / PRP-AT-041 / D19

### 5.7 Worker contract และ residency

<a id="PRP-FR-042"></a>

#### PRP-FR-042 — Worker adapter contract
adapter ต้องมี describe, readiness, invoke, cancellation-capability และ normalize-result/error; registration/observation อาจทำโดย supervisor ไม่ต้องแก้ vLLM ให้มี custom handshake

**รับมอบ:** fake worker กับ vLLM/speech adapter ผ่าน contract เดียวกัน; runtime ที่ไม่ abort ได้รายงาน unsupported และใช้ quarantine

**Trace:** P1-A / E02 / owner Worker Adapter / PRP-AT-042 / D18

<a id="PRP-FR-043"></a>

#### PRP-FR-043 — Lalin-derived voice isolation
voice implementation แรกอาจใช้ ASR/TTS จาก Lalin แต่ต้องมี headless voice-worker profile ไม่ import Desktop/Studio state และไม่ mount brain/fs/plugins/clone/music routes

**รับมอบ:** ปิด/ไม่ติดตั้ง Lalin Studio แล้วยังใช้ speech ได้; route allowlist และ egress tests ผ่าน; engine เปลี่ยนได้โดย client contract ไม่เปลี่ยน

**Trace:** P1-B / E04 / owner Speech Adapter / PRP-AT-043 / D03

<a id="PRP-FR-044"></a>

#### PRP-FR-044 — Safe model residency
การ load/unload/model switch เป็น management action ที่ตรวจสิทธิ์และ calibrated placement; P1 ไม่ unload LLM อัตโนมัติเพื่อเสียง; model references ยังอยู่ต้องไม่รายงานคืน VRAM แล้ว

**รับมอบ:** runtime cache ยัง resident ต้องคง reservation; model swap ต้อง drain/qualify; speech-only B ต้องประกาศ chat capacity ลดและผ่าน change review

**Trace:** P1-B / E02 / owner Admission / PRP-AT-044 / D14

### 5.8 Operations และ client experience

<a id="PRP-FR-045"></a>

#### PRP-FR-045 — Operational telemetry
ต้องแสดง running/waiting, observation age, readiness, queue wait, TTFT, ASR/TTS RTF, latency, failures และ quota usage แยก org/route/profile; GPU exporter เป็น optional

**รับมอบ:** ไม่มี temperature/power เป็น unavailable; metrics ไม่บรรจุ raw prompts/user IDs เป็น high-cardinality labels; dashboard loss ไม่หยุด correctness

**Trace:** P1-A / E06 / owner Observability / PRP-AT-045 / D21

<a id="PRP-FR-046"></a>

#### PRP-FR-046 — Actionable alerts
สร้าง redacted deduplicated events สำหรับ all-nodes-down, stale observer, disk full, queue saturation, repeated ASR/TTS fail และ credential fail

**รับมอบ:** fault suite ได้ event พร้อม scope/time; notification destination ไม่มีแสดง NOT_CONFIGURED ไม่อ้างว่าส่งแล้ว

**Trace:** P1-C / E06 / owner Observability / PRP-AT-046 / D21

<a id="PRP-FR-047"></a>

#### PRP-FR-047 — Auditable management
key/node/profile/policy/retention/drain/restore actions ต้องมี append-only audit receipt actor/scope/version/redacted diff; content access ที่ privileged ต้อง trace ได้

**รับมอบ:** สำรวจ logs/DB/API/export ไม่มี plaintext secret/signed URL/raw audio/transcript; repeated settlement ไม่เขียน usage ซ้ำ

**Trace:** P1-A / E06 / owner Audit / PRP-AT-047 / D17

<a id="PRP-FR-048"></a>

#### PRP-FR-048 — Independent operator console
console ต้องจัดการ key/pool/profile/qualification/drain และดู jobs/usage ตาม role ได้โดยไม่ต้องเปิด Zuri; protected management ใช้ session auth แยกจาก inference key

**รับมอบ:** operator และ org admin มีมุมมองคนละขอบเขต; native local admin bootstrap และ recovery procedure ใช้ได้

**Trace:** P1-A / E06 / owner Console / PRP-AT-048 / D05

<a id="PRP-FR-049"></a>

#### PRP-FR-049 — Minimal independent playground
ต้องมี authenticated text chat กับ record-and-send/upload/playback ใน P1-B; reference client ถือ conversation workflow ของตัวเอง ไม่สร้าง memory API ใน PRP

**รับมอบ:** mic denied ยังพิมพ์/upload ได้; stop playback ไม่แอบอ้าง cancel GPU; TTS fail รักษาคำตอบข้อความและ retry เฉพาะ TTS

**Trace:** P1-B / E07 / owner Reference Client / PRP-AT-049 / D07

### 5.9 Deployment, integrations และ extensions

<a id="PRP-FR-050"></a>

#### PRP-FR-050 — Reproducible independent deployment
ต้องมี per-host deploy/config schemas, pinned manifests และ start/stop/health procedure; control plane modular monolith ได้ ไม่บังคับ Kubernetes หรือ Vercel

**รับมอบ:** install clean environment โดยไม่มีแอปธุรกิจ/remote control plane dependency; manifest ไม่มี latest/secrets; ports ตรง inventory

**Trace:** P1-A / E01 / owner Operations / PRP-AT-050 / D04

<a id="PRP-FR-051"></a>

#### PRP-FR-051 — Backup and recovery
ต้อง backup config/job/usage/audit/erasure metadata และ policy-selected artifacts พร้อม recovery keys ที่แยก; restore เริ่ม binding DISABLED แล้ว reconcile in-flight work

**รับมอบ:** restore test ผ่าน RPO/RTO target ที่อนุมัติ; ไม่ถือ backup แทน HA; explicit residual data policy สำหรับ immutable backup

**Trace:** P1-C / E06 / owner Operations / PRP-AT-051 / D22

<a id="PRP-FR-052"></a>

#### PRP-FR-052 — Canary and rollback
rollout ต้องผ่าน flags และ canary ต่อ org/capability; rollback API/profile แบบ forward-safe ไม่ลบ unsettled attempts; speech off ไม่เปลี่ยน chat เป็น external provider

**รับมอบ:** switch voice off แล้ว chat ยังใช้เดิม; rollback ไม่เปลี่ยน channel sender; release evidence กับ rollback approver ถูกบันทึก

**Trace:** P1-C / E06 / owner Operations / PRP-AT-052 / D23

<a id="PRP-FR-053"></a>

#### PRP-FR-053 — Compatibility and exit path
ต้อง publish versioned OpenAPI subset, worker contract, metadata export และ conformance suite; เปลี่ยน chat/voice adapter ได้โดยไม่แก้ client schema

**รับมอบ:** ทดสอบ two independent clients + fake replacement adapter; export config/profile/job/usage เป็น documented JSON โดยไม่ export plaintext keys

**Trace:** P1-C / E07 / owner API / PRP-AT-053 / D26

<a id="PRP-FR-054"></a>

#### PRP-FR-054 — No mandatory LINE dependency
PRP core ห้าม require LINE token/webhook/Zuri identity; LINE integration เป็น external consumer และอาจไม่ได้ deploy เลย

**รับมอบ:** ปิด Zuri/LINE adapter แล้ว HTTP clients ยังผ่าน core acceptance; PRP package scan ไม่มี imports ไป business modules

**Trace:** P1-A / E07 / owner Core / PRP-AT-054 / D01

<a id="PRP-FR-055"></a>

#### PRP-FR-055 — External LINE integration contract
reference integration ต้องถือ verified webhook, durable conversation workflow, content fetch และ delivery outbox ภายนอก PRP; ส่งให้ PRP เฉพาะ authorized content

**รับมอบ:** integration suite ตรวจ dedupe/signature/ACK/reply-push/uncertain send ตาม INT-LINE; core release แยกจาก connector release และ live canary

**Trace:** P1-C / E07 / owner Integration Adapter / PRP-AT-055 / D11

<a id="PRP-FR-056"></a>

#### PRP-FR-056 — Phase-boundary enforcement
P1 ต้อง deny image/video/clone/arbitrary plugin/model download จาก inference keys; P2 เปิดด้วย new grants/profile/qualification เท่านั้น

**รับมอบ:** เก่าทุกคีย์ไม่มี media scope อัตโนมัติ; extension ผ่าน chat/voice regression; ไม่ต้องเปลี่ยน core identity หรือ client business schema

**Trace:** P1-A / E08 / owner Core / PRP-AT-056 / D24

## 6. Non-functional requirements
ตัวเลขด้านประสิทธิภาพและ recovery เป็น proposed acceptance targets ต้อง freeze ก่อนทดสอบ ไม่ใช่ SLA ที่มีผลทดสอบแล้ว

<a id="PRP-NFR-001"></a>

### PRP-NFR-001 — Isolation correctness
ทุก negative authorization และ artifact ownership case ต้องผ่าน ไม่มี unauthorized content หรือ action ที่ยอมรับได้แม้หนึ่งครั้ง

**Proof:** SECURITY / P1-A / PRP-AT-057

<a id="PRP-NFR-002"></a>

### PRP-NFR-002 — Revocation bound
งานใหม่/dispatch/result-read ต้องสะท้อน revoke ภายใน 60s; cache invalidation test ที่หลาย process และกรณี identity store unavailable ต้อง fail closed

**Proof:** security integration / P1-A / PRP-AT-058

<a id="PRP-NFR-003"></a>

### PRP-NFR-003 — Admission overhead
p95 <=250ms ที่ 10 requests/s นาน 5min ด้วย mocked backend; วัด auth+quota+reservation ไม่รวม queue/model; report sample count และ p99

**Proof:** load mock / P1-A / PRP-AT-059

<a id="PRP-NFR-004"></a>

### PRP-NFR-004 — Warm chat latency
W1: TTFT p95 <=5s และ completed-request failure <=1%; output actual length ต้องรายงาน ไม่ถือ max_tokens ว่า output จริง

**Proof:** hardware W1 / P1-C / PRP-AT-060

<a id="PRP-NFR-005"></a>

### PRP-NFR-005 — Voice pipeline latency
W2 reference client audio->ASR->LLM->TTS: p95 <=45s สำหรับ 15s clip/<=128 output tokens/<=15s synthesized audio; ไม่รวม upload/LINE network

**Proof:** hardware W2 / P1-C / PRP-AT-061

<a id="PRP-NFR-006"></a>

### PRP-NFR-006 — Mixed-workload protection
W3: chat TTFT p95 <=2x isolated baseline และ <=5s, ไม่มี admitted OOM; report rejected/deadline/partial jobs ไม่ตัดออกเพื่อทำ percentile สวย

**Proof:** hardware W3 / P1-C / PRP-AT-062

<a id="PRP-NFR-007"></a>

### PRP-NFR-007 — Durability and settlement
หลัง 202 accepted ต้องมี durable record ภายใต้ process restart; committed logical result settle ได้ครั้งเดียว; ไม่อ้าง exactly-once GPU computation

**Proof:** fault injection / P1-B / PRP-AT-063

<a id="PRP-NFR-008"></a>

### PRP-NFR-008 — ASR quality
corpus versioned 120 clips/12 speakers: Thai clean CER<=15%, noisy<=25%, English WER<=20%; code-switch report แยก; critical-entity accuracy>=90% clean

**Proof:** audio quality / P1-B / PRP-AT-064

<a id="PRP-NFR-009"></a>

### PRP-NFR-009 — TTS quality
อย่างน้อย 40 texts ไทย30/อังกฤษ10, raters>=3; per-language median intelligibility>=4/5 และ critical-entity pronunciation>=95%; >=1 approved voice/ภาษา

**Proof:** audio quality / P1-B / PRP-AT-065

<a id="PRP-NFR-010"></a>

### PRP-NFR-010 — No-speech gate
silence/noise-only >=20 clips; >=95% คืน no-speech/unclear และไม่มี downstream auto action ใน reference integration

**Proof:** audio quality / P1-B / PRP-AT-066

<a id="PRP-NFR-011"></a>

### PRP-NFR-011 — Observability freshness
poll default5s stale15s; dashboard แสดงอายุจริง; out-of-order/unknown metrics tests ต้องไม่สร้าง capacity ที่ไม่มีหลักฐาน

**Proof:** fault injection / P1-A / PRP-AT-067

<a id="PRP-NFR-012"></a>

### PRP-NFR-012 — Recovery objectives
candidate RPO<=24h สำหรับ host/disk disaster และ RTO<=4h; process restart ไม่สูญเสีย DB committed jobs; แยกสอง failure models ชัดเจน

**Proof:** restore rehearsal / P1-C / PRP-AT-068

<a id="PRP-NFR-013"></a>

### PRP-NFR-013 — Accessible client flow
keyboard path, visible focus/status, Thai rendering, mic-denied/upload fallback; ไม่มี forced autoplay; screen-reader labels สำหรับ record/stop/cancel

**Proof:** browser manual + e2e / P1-B / PRP-AT-069

<a id="PRP-NFR-014"></a>

### PRP-NFR-014 — Bounded resource use
API/decoder/queue/temp/storage limits ต้องบังคับได้และ cleanup orphan <=24h; malformed media ต้องไม่ exhaust control plane

**Proof:** adversarial load / P1-B / PRP-AT-070

<a id="PRP-NFR-015"></a>

### PRP-NFR-015 — Reproducible configuration
production pins runtime digest + model/profile revision + hardware calibration; change ต้อง requalify; rollback evidence ผูก exact manifest

**Proof:** release rehearsal / P1-C / PRP-AT-071

<a id="PRP-NFR-016"></a>

### PRP-NFR-016 — Independent operation
CI/runbooks/core acceptance ต้องรันโดยไม่มี Zuri; gateway และ metadata export ไม่บังคับ vendor cloud subscription; isolate two client applications

**Proof:** portability / P1-A / PRP-AT-072

<a id="PRP-NFR-017"></a>

### PRP-NFR-017 — No hidden content egress
P1 default deny third-party inference/telemetry payload egress; model downloads อยู่ install stage ที่ audit; network capture happy+failure ไม่มี content ออกนอก approved boundary

**Proof:** egress capture / P1-C / PRP-AT-073

<a id="PRP-NFR-018"></a>

### PRP-NFR-018 — Service honesty
ไม่มี uptime/throughput/HA claim จากชื่อ pool; all-node/control-plane failure และ job UNKNOWN ต้องมองเห็น; SLO report รวม errors/timeouts/rejections

**Proof:** operations review / P1-C / PRP-AT-074


### 6.1 Python-first และ framework reuse constraints

ข้อกำหนดใหม่เพิ่มต่อท้าย NFR เดิม ไม่เปลี่ยนความหมายของ PRP-FR-001..056 หรือผลรับมอบเดิม

<a id="PRP-NFR-019"></a>

### PRP-NFR-019 — Python-first control plane
PRP-owned control/API/policy/adapters ต้องใช้ Python เป็น baseline และไม่บังคับ Rust/Tauri หรือ desktop shell เพื่อ build/run core; native code ภายใน runtime dependency ใช้ได้ ข้อยกเว้น first-party native module ต้องมี ADR พร้อม profiling หรือข้อจำกัดที่พิสูจน์แล้ว

**รับมอบ:** clean CPU-only control environment build/import/health ได้โดยไม่มี desktop หรือ GPU runtime; review dependency graph และ ADR ข้อยกเว้น; ไม่ตีความภาษาเป็นผล benchmark

**Proof:** build + dependency isolation / P1-A / PRP-AT-087

<a id="PRP-NFR-020"></a>

### PRP-NFR-020 — Evidence-based reuse before build
ก่อนสร้าง runtime lifecycle, key store, router หรือ scheduler แบบ custom ต้องมี fit-gap ของ candidate A/B ต่อข้อกำหนดและหลักฐานทดลอง; ทุก custom gap ต้องระบุเหตุผลว่าทำไม configure/adapter ของระบบเดิมไม่พอ ห้ามมีผู้ชนะที่ประกาศจาก feature list โดยไม่ทดสอบ

**รับมอบ:** WP24 มีเอกสารเปรียบเทียบ A/B, exact versions, evidence/NOT_RUN/BLOCKED และ approved gap budget ก่อน G0 exit; C-Ray ประเมินเมื่อมี trigger เท่านั้น; security gap ไม่ถูกลดเกณฑ์เพื่อเลือกเครื่องมือ

**Proof:** design evidence + isolated spikes / G0 / PRP-AT-088

<a id="PRP-NFR-021"></a>

### PRP-NFR-021 — API and model process isolation
control web workers ต้องไม่โหลด model weights หรือ initialize CUDA/ASR/TTS ตอน import/startup; blocking inference/decoding อยู่ใน dedicated bounded worker process/service ที่มี lifecycle owner แยก เพิ่ม API workers ต้องไม่เพิ่ม model replicas โดยไม่อนุมัติ

**รับมอบ:** เพิ่ม API process count แล้ว model PID/count/residency ไม่เปลี่ยน; no-GPU/import smoke ผ่าน; API ตอบ health/cancel ได้ระหว่าง worker งานยาว; cancel thread/future ไม่ถูกนับเป็น compute stopped

**Proof:** process integration + real runtime / P1-A / PRP-AT-089

<a id="PRP-NFR-022"></a>

### PRP-NFR-022 — Reproducible isolated Python environments
control, LLM และ speech ต้องมี dependency/lock หรือ immutable vendor-image boundary แยกตาม compatibility; pin Python/runtime/model/driver manifest และ tool versions ที่ทดสอบ ห้ามแก้ dependency ตอน production start หรือโหลดโมเดลจาก unpinned remote source ข้อมูล secret ต้องอยู่นอก manifest

**รับมอบ:** สร้างซ้ำจาก clean environment และ lock/image digest ได้; control image ไม่มี ML model payload; SBOM/license/egress review และ upgrade/rollback tests มีหลักฐาน; source template ไม่ถูกอ้างเป็น actual lock

**Proof:** build + supply-chain review / P1-A / PRP-AT-090

<a id="PRP-NFR-023"></a>

### PRP-NFR-023 — Delegated framework authority conformance
การ delegate key/routing/lifecycle ให้ framework ต้องระบุ authority และ enforce PRP policy ทุกเส้นทาง; physical lease ผูก actual runtime/resource epoch ก่อน compute; ห้าม downstream retry/reroute/replica relocation หรือ user-key bypass ที่หลุด lease, quota, deadline หรือ result fence

**รับมอบ:** ทดสอบ auth spoof/revoke, framework internal retry, hidden route change, two-process race และ supervisor restart; ไม่พิสูจน์ placement ได้ต้องปิด profile หรือใช้ approved conservative envelope ที่ผ่าน gate; encrypted recoverable user key ไม่ผ่าน FR-005

**Proof:** framework contract + race + fault / P1-A / PRP-AT-091

<a id="PRP-NFR-024"></a>

### PRP-NFR-024 — Portable framework binding and exit
public PRP contract ต้องไม่เปิดเผย vendor model IDs, manager schemas หรือ vendor database เป็น business dependency; bindings แปลง alias/profile/attempt identity และ export declarative config ได้ การเปลี่ยน framework ไม่บังคับ client schema change แต่ต้อง requalify model/voice/security และ rotate keys เมื่อ verifier ย้ายอย่างปลอดภัยไม่ได้

**รับมอบ:** fake adapter replacement ผ่าน client conformance; replay approved synthetic workloads ผ่าน candidate replacement เมื่อมี; export excludes plaintext keys; รักษางาน uncertain/erasure และบันทึกขั้น key rotation แทนการอ้าง portable secret ที่อ่านคืนไม่ได้

**Proof:** portability + migration rehearsal / P1-C / PRP-AT-092


## 7. Security requirements
Security cases เป็น release blockers แม้ aggregate pass rate สูง; ผู้ดูแลเครื่องเป็นส่วนของ trust boundary ไม่อ้าง confidential computing

<a id="PRP-SEC-001"></a>

### PRP-SEC-001 — Private transport
ใช้ TLS ที่ verify identity หรือ authenticated encrypted tunnel; API/worker/admin/metrics เปิดเฉพาะ permitted callers; runtime API key ลำพังไม่พอ [SRC-02]

**รับมอบ:** negative route scan, wrong TLS identity และ unauthenticated engine routes ถูกบล็อก | PRP-AT-075 / D20

<a id="PRP-SEC-002"></a>

### PRP-SEC-002 — Secret custody
คีย์ client เก็บ verifier; upstream credentials ที่ต้องอ่านใช้ encrypted secret reference; encryption keys/backup recovery keys อยู่คนละ boundary; ห้ามใส่ใน image/git/frontend

**รับมอบ:** secret scan ของ artifact/image/log/API/backup พร้อม rotation/recovery rehearsal | PRP-AT-076 / D08

<a id="PRP-SEC-003"></a>

### PRP-SEC-003 — SSRF and egress
node origins ตรวจ allowlist, DNS resolution ตอนเชื่อม, deny redirect/metadata/link-local/unapproved loopback; model request ไม่มี arbitrary URL/file/plugin execution

**รับมอบ:** SSRF fixture IPv4/IPv6/redirect/rebind และ network capture ต้องผ่าน | PRP-AT-077 / D20

<a id="PRP-SEC-004"></a>

### PRP-SEC-004 — Object authorization
ทุก job/artifact/list/export ใช้ trusted principal/org และ explicit grant; unpredictable UUID ไม่ใช่ authorization; cache isolation ตาม org/conversation sensitivity

**รับมอบ:** cross-org/principal ID swap และ list filter tests ผ่าน | PRP-AT-078 / D17

<a id="PRP-SEC-005"></a>

### PRP-SEC-005 — Untrusted input
prompt/transcript/tool output เป็นข้อมูล ไม่ใช่ permission; user parameter ไม่กำหนด shell/model file/runtime URL; bounded media decode ใช้ sandbox

**รับมอบ:** model/tool/codec injection cases ไม่มี side effect หรือ privilege gain | PRP-AT-079 / D20

<a id="PRP-SEC-006"></a>

### PRP-SEC-006 — Secure administration
management ใช้ separate session auth, CSRF protection ที่เกี่ยวข้อง, secure cookie, rate limit และ audit; bootstrap token one-time แล้วปิด; inference key ไม่เป็น admin

**รับมอบ:** CSRF/role escalation/bootstrap reuse/weak default credential negative tests | PRP-AT-080 / D05

<a id="PRP-SEC-007"></a>

### PRP-SEC-007 — Voice rights and model provenance
ต้องมี license manifest แยก code/weights/vocoder/reference voice และ intended use; ไม่มี user cloning ใน P1; review license ไม่เท่ากับ legal certification

**รับมอบ:** release artifact ทุกชิ้นมี provenance/approval; missing license receipt block activation | PRP-AT-081 / D18

<a id="PRP-SEC-008"></a>

### PRP-SEC-008 — Content minimization
default logs/metrics/audit ไม่มี raw prompt/transcript/audio/secret/full signed URL; privileged diagnostics เป็น opt-in จำกัดผู้ดู/TTL และ audit

**รับมอบ:** trace/request/error paths ถูก scan รวม crash traces; sample metadata ไม่แฝง content | PRP-AT-082 / D21

<a id="PRP-SEC-009"></a>

### PRP-SEC-009 — Deletion and cache boundary
delete ต้อง fence queued/late result/grants และ purge temp/cache references; backup retention disclosed และ reconcile tombstones ก่อน restore serves traffic

**รับมอบ:** delete-during-run, link revoke, restore-after-delete ผ่าน | PRP-AT-083 / D19

<a id="PRP-SEC-010"></a>

### PRP-SEC-010 — Supply-chain pinning
dependencies/model code ต้อง reviewed/pinned; ไม่ auto execute remote model code หรือ install plugins จาก inference request; release มี inventory/SBOM และ checksum

**รับมอบ:** reproducible build และ artifact tampering negative test | PRP-AT-084 / D23

<a id="PRP-SEC-011"></a>

### PRP-SEC-011 — Trust-owner limitation
P1 shared engines จำกัด trusted organization; host administrator อาจเข้าถึง process memory ได้ จึงไม่อ้าง cryptographic isolation/hardware attestation หรือ confidential compute

**รับมอบ:** deployment trust statement และ tests ไม่เปิด cross-customer/hostile tenants โดยอัตโนมัติ | PRP-AT-085 / D20

<a id="PRP-SEC-012"></a>

### PRP-SEC-012 — Service credential boundary
worker ไม่มี LINE token/business DB/cloud admin credential; artifact access เป็น scoped short-lived grant; client app compromise จำกัดผลด้วย service quota/scopes

**รับมอบ:** inspect worker environment + denied network access + stolen low-scope key test | PRP-AT-086 / D03

## 8. API contract baseline
| Interface | Success | Scope / semantics |
|---|---|---|
| GET /v1/models | 200 JSON | granted aliases only |
| GET /prp/v1/capabilities | 200 JSON | profile capabilities/limits; no physical addresses |
| POST /v1/chat/completions | 200 JSON/SSE | text subset; stream terminal errors explicit |
| POST /v1/audio/transcriptions | 200 JSON | multipart file/model/language; bounded synchronous ASR |
| POST /v1/audio/speech | 200 WAV/MP3 | approved preset; bounded synchronous TTS |
| POST /prp/v1/artifacts | 201 JSON | authenticated audio upload; bounded stream |
| POST /prp/v1/jobs | 202 JSON | native ASR/TTS job; Idempotency-Key required |
| GET /prp/v1/jobs | 200 JSON | paginated scoped metadata |
| GET /prp/v1/jobs/{id} | 200 JSON | outcome + execution status + artifacts |
| POST /prp/v1/jobs/{id}/cancel | 202/200 | request cancellation / already terminal |
| GET /prp/v1/artifacts/{id} | 200 audio bytes | authenticated ownership check |
| DELETE /prp/v1/artifacts/{id} | 204 | tombstone + cleanup; no resurrection |
| POST /prp/v1/artifacts/{id}/grants | 201 JSON | explicit share permission; bounded HTTPS bearer link |
| DELETE /prp/v1/grants/{id} | 204 | revoke grant |

OpenAI-compatible เป็น subset ของชื่อ route/request/response ไม่อ้าง full OpenAI product parity ไม่รวม Responses/Realtime/Assistants/embeddings ใน P1; vLLM รองรับ compatible serving แต่ endpoint/security behavior ขึ้นกับ release [SRC-01][SRC-02]

## 9. Outcome และ state contracts
| Dimension | Values / interpretation |
|---|---|
| Job outcome | PENDING, SUCCEEDED, FAILED, TIMED_OUT, CANCELLED; terminal เปลี่ยนไม่ได้ |
| Execution | QUEUED, RESERVED, DISPATCHED, RUNNING, UNKNOWN, FINISHED |
| Capacity lease | HELD, QUARANTINED, RELEASED; release ต้องมี termination evidence |
| Artifact | STAGING, AVAILABLE, TOMBSTONED, DELETED, EXPIRED |
| Client voice turn | RECEIVED, ASR, CHAT, TTS, COMPLETE, PARTIAL_SUCCESS, FAILED; อยู่ app |
| LINE delivery | NOT_READY, READY, SENDING, ACCEPTED, FAILED, UNKNOWN, EXPIRED; อยู่ adapter |

Job TIMED_OUT พร้อม execution UNKNOWN และ resource QUARANTINED เป็นสถานะที่ถูกต้อง ไม่ต้องปลอม terminal compute state ให้ UI ดูง่าย หลังผลลัพธ์มาถึงช้าให้บันทึก FINISHED เพื่อ reconcile แต่ไม่เปลี่ยน user outcome หรือคืน erased content

Idempotency: job duplicate key+same payload คืน logical job เดิม; different payload 409; ไม่รับประกัน identical GPU output หรือ exactly-once compute การ retry sync inference ที่ขาดกลางทางต้อง explicit และไม่ต่อ stream เดิม

## 10. Pilot policy defaults
| Parameter | Proposed default | Rule |
|---|---|---|
| Audio upload | <=60s AND <=10 MiB | ตรวจ actual content ทั้งสองเงื่อนไข |
| Decoder | <=64 MiB normalized PCM, <=30s wall time | เพิ่มได้เฉพาะ reviewed profile; sandbox memory hard limit separate |
| TTS input/output | <=800 code points / <=60s | no silent truncation |
| Sync audio budget | 30s queue+compute | predicted over budget -> ASYNC_REQUIRED before dispatch |
| Chat queue/deadline | max queue wait10s / operation60s | client ลดได้ ไม่เพิ่มเกิน profile |
| Native speech job | queue wait30s / operation180s | absolute deadline ตั้งแต่ accepted |
| Per principal | active1 / queued3 | application quota แยกตาม policy; GPU slots calibrated separately |
| Queue ceiling | chat20 / speech10 per deployment pool | reject before durable acceptance เมื่อเต็ม |
| Observation | poll5s / stale15s | unknown not zero |
| Client key lifetime | 90d, overlap<=24h | no privileged permanent default key |
| Raw/orphan audio | max24h from upload | running job ไม่ยืด unlimited retention |
| Generated audio | 7d from creation | authorized delete ทำให้หมดเร็วกว่านี้ |
| Async content payload | 24h after terminal; max48h from creation | encrypted store; early erase overrides |
| Job/usage/audit metadata | 90d; operation logs30d | exclude raw content; policy may shorten |
| Share grant | max24h, <=artifact expiry | explicit consent/policy; multi-fetch within TTL |
| Dedupe records | job horizon + >=24h | content digest scoped; tombstone on erased job |

ไม่มี default GPU concurrency ที่รับรองแล้ว เริ่ม calibration ที่หนึ่ง invocation ต่อ node แล้วเพิ่มตามผลทดสอบ ต้องรวม resident model, KV cache, speech peak workspace และ headroom ไม่ใช้ nominal VRAM ลบ cache% เพื่อสร้าง guaranteed token budget

## 11. Qualification workloads
| Workload | Definition | Evidence |
|---|---|---|
| W0 Control | 10 req/s 5min mocked runtime, 2 gateway processes | auth/admission p50/p95/p99, atomic quotas |
| W1 Chat | warm, input1024 actual tokens, output budget128; 2 concurrent total; >=200 completed | per-node profile, actual length, TTFT, errors/rejections/deadlines |
| W2 Voice | >=50 turns, Thai15s clip, <=128 answer tokens, <=15s TTS; one turn at a time | ASR/LLM/TTS/storage/client durations and partials |
| W3 Mixed | W1 + recurring W2 for >=30min on production placement | baseline delta, OOM, backlog, fairness and actual admissions |
| W4 Fault/boundary | max context/audio, queue full, A/B/DB/observer failure, revoke/delete/restart | no unsafe lease release, no unauthorized output/egress |

Quality corpus: >=120 licensed clips, >=12 speakers, Thai clean40/noisy40, English20/code-switch20; human reference and fixed Unicode/number/punctuation scoring protocol before test. English WER และ Thai CER ใช้ normalization ที่ documented; code-switch รายงาน CER และ critical entities แยกไม่ซ่อนด้วยค่าเฉลี่ยรวม TTS corpus ตาม NFR-009; Thai preset quality ต้องผ่านจริง ไม่ถือ README demo เป็น production proof [SRC-08]

## 12. Failure contract
| Event | Required outcome |
|---|---|
| A offline, B eligible | new request ใช้ B; A unknown attempt ยังคง fenced |
| Both runtimes unavailable | bounded 503/queue deadline ไม่ส่ง cloud |
| DB/identity store unavailable | no new admission; active stream status uncertain ต้อง reconcile; ไม่ใช้ local counters แทน |
| Client disconnect | propagate cancel best-effort; result/content fence; retain lease until proven stopped |
| ASR no speech | 422/failed job reason; reference client ไม่เรียก LLM ต่อ |
| TTS fails after client got chat | PRP TTS operation FAILED; client voice turn PARTIAL_SUCCESS; preserve text |
| Media store full/corrupt | fail artifact stage, no zero-byte success; bounded cleanup |
| LINE delivery unknown | adapter reconciles outbox; PRP ไม่ compute/send ใหม่ |
| Control host outage | availability may cease despite live GPU B; no HA claim |
| Delete/revoke while running | block future read/settle/publish, allow safe compute reconciliation only |

## 13. P2 requirements envelope
P2 ไม่ใช่ requirement-ready acceptance baseline; ต้องเพิ่มรายละเอียด model/workflow quality, hardware, safety, quotas และ test evidence ก่อนเริ่ม implementation ของ phase นั้น

<a id="PRP-P2-001"></a>

### PRP-P2-001 — Media capability grants
image generation/edit และ video generation ต้อง explicit grants; chat/voice keys ไม่ได้สิทธิ์เพิ่ม

<a id="PRP-P2-002"></a>

### PRP-P2-002 — Allowlisted media workflows
รองรับเฉพาะ pinned model/workflow/codec พร้อม licensed input/output provenance; ไม่มี arbitrary ComfyUI JSON/plugin

<a id="PRP-P2-003"></a>

### PRP-P2-003 — Asynchronous media jobs
ทุก media operation ใช้ 202/job/status/cancel/retention และ bounded queue; ไม่บังคับ long HTTP render

<a id="PRP-P2-004"></a>

### PRP-P2-004 — Media quota units
meter image count/pixels/steps, output video seconds/resolution และ compute-time แยกจาก token quota

<a id="PRP-P2-005"></a>

### PRP-P2-005 — Protected chat reservation
กำหนด reserved chat capacity; model swap/manual mode change ต้อง drain/requalify และแจ้ง degraded service

<a id="PRP-P2-006"></a>

### PRP-P2-006 — Artifact lineage and moderation hooks
input/edit/output มี lineage/checksum/consent policy/safety hooks และ scoped share grants; no training reuse default

<a id="PRP-P2-007"></a>

### PRP-P2-007 — Media qualification
กำหนด hardware/model/resolution/duration/workload/SLO ที่วัดใหม่; ไม่ยกตัวเลข chat มาอ้าง video capacity

<a id="PRP-P2-008"></a>

### PRP-P2-008 — P1 regression and independent clients
image/video additive APIs/adapters ต้องผ่าน P1 regression + two-client isolation; ไม่เพิ่ม dependency ต่อ Zuri

## 14. Release gates และ unresolved decisions
Core P1 acceptance ต้องมี FR/NFR/SEC ทุก MUST ที่เกี่ยวข้องพร้อม implementation/test evidence; test ไม่ได้รันเป็น NOT_RUN/blocked ไม่ใช่ PASS Security isolation, secret leakage, unsafe uncertain release และ unapproved egress เป็น blockers

G0: Python-first / A-B fit-gap / authority binding / locked-environment decision;  approve ownership/API/state/defaults + hardware inventory + selected gateway authority chain
G1: independent chat service + two qualified replicas + negative security and atomic race tests
G2: ASR/TTS contracts + licensed preset + async jobs/artifacts + Thai/English quality + placement decision
G3: mixed workload/restore/rollback/fault/evidence + two independent clients + operator handoff
Integration-LINE: separate authorized live canary + reply/push/URL/mobile playback evidence

Open decisions ก่อน production: exact GPU/OS/driver, pinned LLM/ASR/TTS artifacts, candidate A/B runtime-management และ gateway/key authority จาก WP24, database/secret-store deployment, capacity profiles, retention/egress approvals, service-user mapping policy และ LINE native bearer-link permission ไม่มี decision ใดถูกเปลี่ยนเป็น approved เพียงเพราะเอกสารนี้มีข้อความละเอียด

## 15. Traceability และ change control
PRD goal -> Epic -> SRS requirement -> API/architecture/diagram -> acceptance test -> roadmap gate -> implementation/evidence มีรหัสเชื่อมใน TRACEABILITY-PRP และ registry JSON แบบ generated เมื่อ scope ใหม่เปลี่ยนความหมาย requirement ให้ retire/supersede ID เดิม ไม่ recycle

คำว่า source reviewed, document generated และ runtime verified เป็นคนละสถานะ ชุดนี้เขียนเอกสารและตรวจ consistency เท่านั้น ไม่ได้เพิ่ม source code, deploy, ออกคีย์จริง, เปลี่ยน network หรือส่ง LINE

## 16. Implementation strategy clarification for v0.3.0
ใช้ framework ที่มีอยู่ก่อนสร้าง custom infrastructure: vLLM เป็น initial LLM engine, FastAPI/Pydantic เป็น candidate ของ thin Python API, Xinference-managed runtimes และ independent services เป็นแบบที่ต้องเทียบ ส่วน LiteLLM เป็น optional key/routing implementation และ Ray Serve เป็น conditional alternative [SRC-01][SRC-03][SRC-09][SRC-11][SRC-13]

ชื่อ PRP Router/Admission/Registry ไม่ได้สั่งให้เขียนใหม่ทั้งหมด ต้องมี implementation mapping ระบุ REUSE/CONFIGURE/ADAPT/BUILD-GAP ต่อ requirement; ให้ใช้ primitive ที่มีอยู่เมื่อรักษา atomicity, identity, cancellation และ observable execution ได้

API contract 12 paths / 14 operations ของ v0.2.0 คงเดิมในรุ่นเอกสารนี้ ไม่มี endpoint vendor ใหม่ใน public contract Management API ยังเป็น draft: G0 ต้อง freeze ขอบเขตกับ authority ที่เลือกก่อน implementation ไม่ใช้ private vendor tables เป็น integration API

การเลือก framework ไม่อนุมัติ model eviction, extra replicas, third-party inference, cluster ports สู่ public หรือ voice cloning อัตโนมัติ แผนภาพทุกภาพเป็น logical responsibility; ไม่ใช่จำนวน microservices หรือ custom modules ที่ต้องสร้างใหม่
