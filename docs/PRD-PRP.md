---
document_id: PRD-PRP
title: "PRD | PRP Product Requirements"
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

# PRD | PRP Product Requirements

**PRP — Private Runtime Platform | v0.3.0 | 2026-09-20 | Draft for review**

เอกสารที่เกี่ยวข้อง: [SRS](SRS-PRP.md) · [Roadmap](ROADMAP-PRP.md) · [Architecture](ARCH-PRP.md) · [Diagrams](DIAGRAMS-PRP.md)

## 1. Product thesis
PRP (Private Runtime Platform) คือแพลตฟอร์ม self-hosted สำหรับให้ทีมและหลายแอปใช้ inference ผ่านสัญญา API เดียว โดยรวมเครื่องประมวลผลเป็น resource pool ควบคุมคีย์ สิทธิ์ โควตา readiness และงานที่ต้องรอคิว ชื่อ PRP Router หมายถึงโมดูลเลือกเส้นทาง ไม่ใช่ทั้งแพลตฟอร์มและไม่ใช่ model engine

เริ่มจากเครื่องสองเครื่องใน LAN: A nominal VRAM 12 GB และ B 16 GB แต่ละเครื่องรันโมเดลของตัวเอง การกระจายคำขอไม่ใช่การรวม VRAM เป็น 28 GB เป้าหมายเดิมประมาณ 9B เป็น candidate เท่านั้น รุ่น GPU/OS/RAM/โมเดลและ capacity จริงต้อง qualification ก่อนรับภาระงาน

ประโยชน์หลักคือให้ผู้ใช้เรียกบริการโดยไม่ต้องรู้ว่าโมเดลอยู่เครื่องไหน และให้ operator ควบคุมว่าใครใช้อะไรได้เมื่อใด แทนการแจกพอร์ต GPU หรือ credential ของ runtime โดยตรง

## 2. ปัญหาที่ต้องแก้และสิ่งที่ไม่อ้าง
ปัญหา P01: แต่ละแอปตั้งค่า model endpoint/secret เอง ทำให้ควบคุมสิทธิ์และ revoke ยาก
ปัญหา P02: งานแชตกับเสียงแย่งทรัพยากรโดยไม่มีผู้จองร่วมกัน และ free-VRAM snapshot ไม่บอก capacity ที่ปลอดภัยทั้งหมด
ปัญหา P03: งานยาว timeout แต่ worker อาจยังทำต่อ ผู้ใช้เห็น error โดย operator ไม่เห็นทรัพยากรที่ยังถูกใช้
ปัญหา P04: การใส่ gateway ใน Zuri ทำให้แอปอื่นต้องพึ่ง business platform ที่ไม่เกี่ยวกับ inference
ปัญหา P05: การตอบเสียงต้องแยก ASR/LLM/TTS failures ไม่ให้เรียก LLM หรือส่งข้อความใหม่ซ้ำเมื่อเสียเฉพาะเสียง

PRP ไม่รับประกัน latency จากจำนวน GB ของการ์ด ไม่อ้าง high availability จากการมีสองเครื่อง และไม่อ้างว่าข้อมูลไม่เคยออกอินเทอร์เน็ตเมื่อแอปเลือกใช้ LINE หรือ share link

## 3. Goals และ success evidence
| Goal | ผลลัพธ์ที่ต้องการ | หลักฐานรับมอบ |
|---|---|---|
| G01 Independence | เปิดใช้ PRP ได้โดยไม่มี Zuri/FUNG/Lalin Studio | clean install + two independent HTTP clients + stop-Zuri test |
| G02 Controlled capacity | ไม่มี oversubscription จาก competing admissions | real PostgreSQL races + mixed-load GPU evidence |
| G03 Portable chat | แชตไทย/อังกฤษแบบ JSON/SSE ผ่าน API subset | conformance suite + actual runtime profile |
| G04 Useful voice | ASR/TTS ภาษาไทยและอังกฤษใช้ได้จริง | corpus และ blind listening score แยกรายภาษา |
| G05 Operability | แยก failures และกู้ state ได้อย่างซื่อตรง | uncertainty/restore/revoke/erase/rollback rehearsal |
| G06 Extensibility | เพิ่ม image/video โดยไม่เพิ่ม app dependency | P2 grant/profile contract และ P1 regression |

เป้าตัวเลขและวิธีวัด canonical อยู่ใน SRS เท่านั้น PRD ไม่เก็บตัวเลขฉบับที่สอง หากข้อกำหนดเปลี่ยนต้องปรับ traceability และ acceptance พร้อมกัน ไม่ใช้เปอร์เซ็นต์ฟีเจอร์เสร็จแทน security gate

## 4. Users, jobs-to-be-done และ role boundaries
| Persona | งานที่ต้องทำ | ไม่ใช่สิทธิ์โดยปริยาย |
|---|---|---|
| Team member | ใช้ chat/upload voice/TTS ตาม quota และดูงานของตน | อ่านงาน/เสียงของคนอื่นหรือเพิ่ม model |
| Application developer | ใช้ service key, standard HTTP, test adapter portability | เปลี่ยน org จาก request body หรือเปิด runtime port |
| Organization admin | จัดการสมาชิก app key grants และ quota ในขอบเขตตน | ตั้ง physical node หรืออ่าน content ของทุกคน |
| Platform operator | qualify node/profile, monitor, drain, restore | inspect raw customer content โดยไม่มี explicit grant |
| Reviewer/security owner | อนุมัติ deployment/license/egress/retention และ release gate | ประกาศผ่านจาก mock tests แทน GPU/live channel |

P1 deployment มีหนึ่ง trusted organization หลาย team/principal/app; schema และ negative tests ต้องแยก organization ได้ แต่การแชร์ engine ระหว่างลูกค้าหรือ trust owner ที่ไม่ไว้ใจกันยังไม่เปิดใน P1 Host administrator เป็นส่วนหนึ่งของ trust boundary ไม่ใช่คู่แข่งที่ระบบนี้ป้องกัน memory inspection ได้

## 5. Scope matrix
| Capability | P1-A | P1-B | P1-C | P2 |
|---|---|---|---|---|
| Independent bootstrap / keys / quotas | Required | Maintain | Qualify | Maintain |
| Two-node chat routing / JSON / SSE | Required | Maintain | Mixed-load proof | Regression |
| ASR / preset TTS | Interface seams | Required | Quality + pilot | Maintain |
| Async ASR/TTS jobs / artifacts | State foundation | Required | Restore/erasure proof | Extend media kinds |
| Console / independent playground | Text + ops basics | Record-send/playback | Usability/security proof | Extend capabilities |
| Zuri/LINE integration | Contract only | Adapter implementation may run in parallel | Separate integration acceptance | Media transport extension |
| Image/video generation/editing | Denied | Denied | Denied | Async allowlisted workflows |
| Realtime calls / voice cloning / music | Out | Out | Out | Separate future decision; not automatic |

P1-B voice หมายถึงส่งคลิปเป็นรอบ (record-and-send) และอ่านคำตอบด้วย approved preset ไม่ใช่ full-duplex, barge-in, wake word, LINE call หรือ speaker identification TTS สำหรับการสนทนาอยู่ P1 แม้ทางเทคนิคเป็น generative audio

## 6. Product journeys
### J01 ออกคีย์แล้วเรียกแชต
ผู้ดูแลสร้าง app หรือ member grant -> แสดง secret ครั้งเดียว -> client เรียก models -> ส่ง chat -> ได้คำตอบ/usage -> ดู quota/receipt การ revoke ต้องมีผลต่อ admission และผลลัพธ์ที่ยังไม่อนุญาต ไม่เพียงลบแถวบน UI

### J02 แบ่งงานสองเครื่อง
request เข้า -> policy/profile filter -> Router rank A/B -> Admission จอง quota/resource atomic -> worker ประมวลผล -> settle result/usage -> release เมื่อพิสูจน์จบ ถ้า A ไม่ทัน deadline ใช้ B ที่ผ่าน qualification ไม่ migrate generation ที่เริ่มแล้ว

### J03 คุยด้วยเสียงแบบเป็นรอบ
reference client หรือ Zuri รับคลิป -> PRP ASR -> client ตรวจ transcript/ประกอบ context -> PRP chat -> client เก็บ canonical answer -> PRP TTS -> client แสดงข้อความและเล่นเสียง หาก TTS ล้ม client คงข้อความและให้ retry เฉพาะเสียง; PRP ไม่เป็นเจ้าของบทสนทนานี้

### J04 ดูงานยาว
client upload -> create native ASR/TTS job ด้วย Idempotency-Key -> ได้ 202 หลัง durable commit -> poll status -> อ่าน artifact ตามสิทธิ์ -> ลบ/หมดอายุ หาก cancel ระหว่างทำต้องเห็น request กับ execution state แยกกัน

### J05 ใช้กับ LINE
LINE -> external adapter ตรวจ signature/dedupe/persist -> เรียก PRP primitives -> adapter ส่ง reply/push ตาม channel policy PRP ไม่มี LINE token และไม่เรียก channel API เอง ข้อจำกัด upstream ยืนยันจากเอกสาร LINE [SRC-04][SRC-05][SRC-06]

## 7. Product boundaries และ anti-lock-in
Core owns: PRP identities/grants, physical/resource profiles, inference admission, operation state, compute usage และ temporary artifacts
Apps own: conversation context, business permissions, tools/RAG/memory, customer records, voice-turn orchestration และ final channel delivery
Runtimes own: weights, tensors, local batching และ verified inference execution ภายใต้ resource envelope ที่ PRP อนุมัติ

ทดสอบ independence ที่ขอบเขต install, runtime, API, data และ release lifecycle ไม่ใช้แค่การแยก repository เป็นหลักฐาน การเปลี่ยน adapter ไม่เปลี่ยน client schema แต่ยังต้องวัดคุณภาพ output/latency ของโมเดลใหม่

PRP ไม่มี training/fine-tuning, billing marketplace, Kubernetes/Ray requirement, cross-host tensor parallelism, arbitrary worker shell, central customer memory หรือ automatic cloud fallback ใน P1

## 8. Prioritization และ release policy
Must: Python-first/reuse evidence, independence, deny-by-default access, shared admission, text/SSE, ASR/TTS ไทยอังกฤษ, durable jobs, artifact isolation, observable uncertainty, reproducible deployment, restore/rollback
Should after core correctness: convenient model selection, dashboard refinements, richer report exports ไม่ข้าม security/recovery เพื่อ UI
Deferred: realtime speech, cross-customer tenancy, cloud failover, advanced autoscaling, distributed model serving, image/video quality commitments

Core P1 release ไม่ต้องรอ LINE account authorization แต่ integrated LINE release ต้องผ่าน live channel gate แยก จึงรายงานได้ว่า core ready/integration pending โดยไม่เรียกว่าทั้งแพลตฟอร์มผ่าน LINE แล้ว

## 9. Constraints, risks และ open decisions
| Decision/risk | Proposed handling | Closure gate |
|---|---|---|
| GPU details/OS/driver unknown | inventory และ qualification per host | G0/G1 |
| LLM approx 9B อาจแชร์ speech ไม่ไหว | CPU speech trial หรือ calibrated resident headroom; no silent unload | G2/G3 |
| Thai TTS/license/voice rights | candidate adapter ไม่เท่ากับ approved model | G2 |
| Runtime / gateway selection | Python-first; A/B fit-gap และ key/admission ownership ก่อนเลือก framework | G0 / WP24 |
| Control plane single host | disclose SPOF + tested backups; no HA promise | G3 |
| User count/daily load unknown | pilot quotas; capacity commitment หลัง mixed load | G3 |
| Retention/LINE bearer URL exposure | explicit policy approval, authenticated playback fallback | G2/LINE gate |

ไม่มีสมมติฐานว่าขนาด repo, จำนวน feature หรือภาษา Rust/Python เป็นหลักฐานว่า runtime พร้อม production

## 10. Acceptance ownership
Product owner ยืนยัน scope และ proposed SLO; technical owner รับรอง contracts/profile; security owner รับรอง isolation/egress/rights; operator รับรอง deploy/restore; QA บันทึก evidence ตาม TEST-PRP; integration owner รับรอง external app/channel

ทุก requirement ในร่างเริ่ม PROPOSED ทุก runtime test เริ่ม NOT_RUN คำขอให้เขียนเอกสารและการเลือกชื่อ PRP ไม่ถือเป็นการอนุมัติ production หรือการผ่านเกณฑ์เหล่านี้

## 11. Python-first และ reuse-before-build
ทิศทางแก้ไขที่ผู้ใช้ร้องขอ: ใช้ Python เป็นภาษาหลักของ PRP control/API/adapters และใช้ runtime/serving libraries ที่มีอยู่ก่อนเขียน infrastructure ใหม่ Frontend ใช้ React/TypeScript ได้; Rust/Tauri ไม่เป็น runtime หรือ build requirement ของ PRP core การใช้ C++/CUDA/Rust ภายใน dependency ไม่ขัดกับทิศทางนี้

PRP เป็นเจ้าของ product contract และ policy ไม่จำเป็นต้องเขียนทุกกล่องใน Diagram เอง การส่งมอบโมดูลจึงอาจเป็น configuration, integration adapter และ contract tests ของระบบสำเร็จรูป แทนการสร้าง engine, router, key store หรือ scheduler ใหม่

**G07 Maintainable reuse:** มี fit-gap register อ้าง requirement ทุกข้อและระบุ REUSE / CONFIGURE / ADAPT / BUILD-GAP / DEFER; custom work ทุกชิ้นต้องมีช่องว่างที่พิสูจน์แล้ว ไม่มีเป้าเปอร์เซ็นต์ reuse ที่แต่งขึ้น และไม่ลด security/quality เพื่อให้ใช้ library ได้

ก่อนเลือก stack ต้องเทียบแบบ A (Xinference-managed runtimes) กับแบบ B (independent vLLM/speech services + gateway) บน workload เดียวกัน ส่วน Ray Serve เป็นตัวเลือก C เมื่อมีเหตุผลด้าน distributed serving และ operator cost ที่ชัด ไม่เพิ่มทั้ง Xinference, Ray และ LiteLLM โดยอัตโนมัติ [SRC-09][SRC-11]

Gate G0 ต้องส่ง evidence/known gaps, key authority, physical-placement mapping, retry/cancel policy และต้นทุนส่วนที่ต้องดูแลก่อนเริ่ม custom implementation แบบถาวร รายละเอียดอยู่ [Stack Evaluation](STACK-EVALUATION-PRP.md); ค่าบังคับอ้าง [SRS](SRS-PRP.md) PRP-NFR-019..024

การประเมิน framework และ hardware ในฉบับนี้ยัง NOT_RUN; การอนุมัติให้แก้เอกสารไม่ใช่การเลือก Xinference, LiteLLM หรือ Ray เป็น production stack
