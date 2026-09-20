---
document_id: WP24-PROCEDURE
title: "WP24 | ขั้นตอนทดลอง fit-gap และ A/B spikes"
product: PRP - Private Runtime Platform
version: 0.4.0-draft
status: approved
created_at: 2026-09-20
language: th-TH
source_authority: authored-proposal
implementation_status: NOT_IMPLEMENTED
runtime_verification: NOT_RUN
decision: APPROVED 2026-09-20 by the repository owner; run records go to docs/evidence/wp24/
governance:
  complexity: C-2
  access_scope: H4
  w_scale: N/A
  risk: MEDIUM
---

# WP24 | ขั้นตอนทดลอง fit-gap และ A/B spikes

**PRP — Private Runtime Platform | v0.4.0-draft | 2026-09-20 | APPROVED 2026-09-20 โดย owner; ยังไม่มีการรัน ไม่มี run record**

เอกสารที่เกี่ยวข้อง: STACK-EVALUATION-PRP §2–§8 · ROADMAP-PRP WP24 / WP03 / WP10 · SRS-PRP NFR-019..024, FR-003..022, FR-042..044 · `registry/reuse-fit-gap-template.json` · `registry/stack-evaluation-template.json` · `evidence/README.md` · SOURCES-PRP

## 1. เอกสารนี้เป็นอะไรและไม่เป็นอะไร

เป็น **ขั้นตอน** สำหรับผู้ทดลองและผู้ตรวจของ WP24 เพื่อให้ผลออกมาเป็นหลักฐานที่ WP03 ใช้ตัดสิน candidate ได้ ทุกข้อในนี้ผูกกับ gate ที่ STACK-EVALUATION §6 กำหนดไว้แล้ว ไม่เพิ่ม experiment ใหม่

ไม่เป็นผลการทดลอง ไม่มีตัวเลขใดในเอกสารนี้ ตัวเลขทุกตัวต้องมาจาก run record ที่วัดจริง (§7) กติกาที่บังคับตลอด:

- **ห้าม stub เป็น proof** โดยเฉพาะคุณภาพเสียง (STACK §6) และห้ามใส่ benchmark ที่ไม่ได้วัด (STACK §7)
- **ห้าม DEFER requirement ระดับ P1 Must แล้วประกาศว่า P1 ผ่าน** (STACK §5) สิ่งที่ยังทดลองไม่ได้ให้ลง `BLOCKED` พร้อม blocker
- **ห้ามแก้ code ของ PRP ระหว่างรัน** สิ่งที่พบว่าขาดให้ลงคอลัมน์ `custom_gap` ของ fit-gap ไม่ใช่ patch (NFR-020)
- **ผลของ WP24 คือหลักฐานเรื่อง candidate** ไม่ใช่การพิสูจน์ PRP end-to-end acceptance test ทั้ง 92 กรณียัง NOT_RUN หลัง WP24 จบ เพราะ PRP ยังไม่มี adapter (M4)

## 2. เงื่อนไขก่อนเริ่ม (owner / ops จัดหา)

| รายการ | ผู้จัดหา | บันทึกลง record ที่ |
|---|---|---|
| Host A (nominal VRAM 12 GB) และ Host B (16 GB) ใน LAN เดียวกัน พร้อม driver / CUDA ที่ติดตั้งแล้ว และเครื่องที่ control processes จะรัน (ตาม SRS host topology และ ARCH §3 control co-locate บน CPU ของ A ได้ ไม่ต้องมีเครื่องที่สาม) การมี GPU driver บนเครื่องเดียวกันเป็นสิ่งที่ **บันทึก** ไม่ใช่สิ่งต้องห้าม ข้อกำหนดจริงคือ control process ต้องไม่แตะ GPU (NFR-021) และมี lock แยก (NFR-022) | ops | `environment.gpu_hosts[]`, `environment.control_host` |
| Network boundary: LAN เท่านั้น ไม่ expose สู่ public, egress policy ระบุชัด (ARCH §1 ไม่มี automatic public-cloud) | ops | `environment.network_boundary` |
| Test corpus: ข้อความและเสียงที่เตรียมไว้เพื่อทดสอบเท่านั้น ห้ามใช้ข้อมูลหรือเสียงลูกค้า (Coding-Standards §10) พร้อม data-retention rule | owner | `environment.test_corpus`, `environment.data_retention` |
| LLM model ที่จะใช้ทดลอง: ชื่อ, revision, tokenizer, chat template, context length, license ตรวจแล้ว **ชุดเดียวใช้กับทั้ง A และ B** (STACK §6) โมเดลเป็น BYOM: owner นำมาเองและรับผิดชอบสิทธิ์ แต่ license receipt ตาม SEC-007 / SECURITY-DATA §8 ยังต้องมีก่อน activation | owner | `shared_revision` |
| Speech candidate (ถ้าจะรวมใน WP24): faster-whisper รุ่นใด, TTS ใด (F5-TTS-THAI ต้องผ่าน license/voice-rights gate [SRC-08]) หรือตัดสินว่า EV07 เป็น BLOCKED โดยตั้งใจจน WP10 | owner | `shared_revision.asr_model`, `shared_revision.tts_model`, `experiments.EV07` |
| Version pin ของ candidate ก่อนเริ่ม: image digest หรือ package lock ของ Xinference / vLLM / LiteLLM / Ray ที่จะทดลอง | operator | `candidates[].version_manifest` |
| PRP repository ที่ commit ใดใช้เป็น reference สำหรับ EV01 และ contract | operator | `prepared_from.prp_commit` |
| ผู้ทดลอง 1 คน ผู้ตรวจ 1 คน (คนเดียวกันไม่ได้) และ time box ต่อ candidate | owner | `people`, `run_window` |
| ตัดสินว่า candidate C (Ray Serve) อยู่ใน scope หรือไม่ (STACK §7: ไม่บังคับเพิ่ม C เมื่อ A/B ยังไม่ผ่าน) LiteLLM **ตัดสินแล้ว 2026-09-20**: อยู่ใน scope เฉพาะ EV04 + EV03 ภายใน candidate B, time box รวมไม่เกิน 1 วันทำงาน (ดู EV04) | owner | `candidates[].in_scope`, `scope_decisions` |

ถ้ารายการใดยังไม่มี ให้เริ่มเฉพาะ EV01 (ไม่ต้องใช้ GPU) และบันทึกส่วนที่เหลือเป็น `BLOCKED` พร้อมชื่อรายการที่ขาด

## 3. กติกาการรันร่วมทุก experiment

1. **ฮาร์ดแวร์และ revision เดียวกัน** สำหรับทุก candidate: รัน A ให้จบทุก EV แล้ว reset host ก่อนเริ่ม B (stop services, ลบ container / venv, ยืนยัน `nvidia-smi` ไม่มี process ค้าง) อนุญาตให้คง model weights cache ไว้ได้ แต่ต้องบันทึกว่าคง
2. **แยก cold / warm** ทุกการวัดระบุว่าเป็น cold start หรือ warm และแยก "สิ่งที่อ่านจากเอกสาร" (source observation) ออกจาก "สิ่งที่วัดได้" (measurement) เป็นสองรายการเสมอ
3. **log ทุกคำสั่ง** ที่รันพร้อม stdout / stderr ลง `docs/evidence/wp24/<record_id>/<candidate>/<EVnn>/` ไฟล์ config ที่ใช้จริงเก็บเป็น artifact ไม่ใช่เขียนบรรยาย
4. **สถานะต่อ gate requirement** มีค่าได้เฉพาะ `PASS` / `FAIL` / `BLOCKED` / `NOT_RUN` `PASS` หมายถึง candidate แสดงพฤติกรรมที่ requirement ต้องการโดยไม่ต้องมี code ของ PRP เพิ่ม ถ้าต้องมี glue ให้ `PASS` พร้อม disposition `CONFIGURE` หรือ `ADAPT` และระบุสิ่งที่ต้องเขียน
5. **ลำดับ mandatory gates ก่อน** (STACK §7): EV04 identity → EV03 binding → EV05 admission → EV06 uncertainty ต้องมีผลก่อนจึงบันทึก operator cost และเปรียบเทียบความสะดวก
6. **ไม่มี secret จริง** token ที่ใช้เป็นค่าทดลองใน environment variable ของ host ทดลองเท่านั้น ห้ามลง record หรือ artifact
7. ทุกข้อสังเกตที่กระทบ requirement ลงทั้ง `experiments.EVnn.per_candidate.<X>.observations` และแถว requirement นั้นใน fit-gap copy (§7) ไม่บันทึกที่เดียว

## 4. ลำดับการรัน

```text
EV01 (control host, ไม่มี GPU, ครั้งเดียวสำหรับ PRP + ต่อ candidate สำหรับ SDK ของมัน)
  └─ candidate A: EV02 → EV04 → EV03 → EV05 → EV06 → EV07 (หรือ BLOCKED) → EV08 → operator cost
       └─ reset hosts
  └─ candidate B: ลำดับเดียวกัน
  └─ candidate C: เฉพาะเมื่อ owner ให้อยู่ใน scope
→ full requirement mapping (92 แถว) → decision recommendation → reviewer sign-off → WP03
```

EV04 ขึ้นก่อน EV03 ในลำดับปฏิบัติเพราะทุก endpoint ต้องมี auth ก่อนจึงทดสอบ binding ได้อย่างมีความหมาย gate ทั้งสองยังเป็นอิสระต่อกันตาม §6

## 5. รายละเอียด EV01–EV08

รูปแบบเดียวกันทุกข้อ: gate → คำถามที่ต้องตอบ → ขั้นตอน → สิ่งที่ต้องบันทึก → เกณฑ์

### EV01 Clean control install — gate PRP-NFR-019 / 021 / 022

**คำถาม:** control plane ติดตั้งและ import ได้โดยไม่มี desktop shell, ไม่โหลด ML และไม่แตะ GPU ของเครื่องหรือไม่ (เครื่องมี GPU ได้ตาม topology สองเครื่อง) และ SDK ที่ candidate ต้องการฝั่ง control ดึง ML dependency เข้ามาหรือไม่

**ขั้นตอน**
1. บน control host: clone PRP ที่ `prepared_from.prp_commit`, `uv sync --locked --group dev` ทั้ง `apps/control-api` และ `workers/voice`, รันชุดคำสั่ง Coding-Standards §10 ทั้งหมด เก็บ output
2. รัน `prp-api` แล้วยิง request ที่มี bearer ทดลอง ต้องได้ 503 `STATE_STORE_UNAVAILABLE` (fail closed) ไม่ใช่ traceback; รัน `prp-dispatcher` และ `prp-observer` ต้อง exit 3 พร้อมข้อความชัด
3. ต่อ candidate: สร้าง scratch venv แยก ติดตั้งเฉพาะ client SDK ที่ adapter ฝั่ง control จะต้องใช้ (เช่น Xinference client, LiteLLM SDK, Ray client) แล้ว import และตรวจ `sys.modules` ด้วยวิธีเดียวกับ `tests/contracts/test_no_ml_import.py` บันทึกว่า SDK ดึง torch / CUDA เข้ามาหรือไม่ และขนาด dependency tree

**บันทึก:** Python version, lock digests, รายชื่อ package ที่ SDK ติดตั้ง, ผล import check, เวลาติดตั้ง (วัดจริง, cold), ว่าเครื่องมี GPU driver หรือไม่ และรายชื่อ compute process จาก `nvidia-smi` ขณะ `prp-api` ให้บริการ (ถ้าเครื่องมี GPU)

**เกณฑ์:** `PASS` เมื่อ PRP ผ่านทั้งข้อ 1–2 โดยไม่มี ML module ใน `sys.modules` หลัง import ทุก module ของ control และ process ของ `prp-api` ไม่ปรากฏใน GPU process list (เมื่อเครื่องมี GPU) และ SDK ของ candidate import ได้โดยไม่มี ML module; `FAIL` เมื่อ SDK ดึง ML เข้ามาและไม่มีทางเลือก HTTP-only; disposition ที่เป็นไปได้: REUSE (HTTP only), ADAPT (เขียน thin HTTP client เอง) การรันบนเครื่องที่ไม่มี driver เป็นหลักฐานเสริมที่เลือกได้ ไม่ใช่ precondition

### EV02 Real A/B registration — gate PRP-FR-010..015

**คำถาม:** candidate เปิด LLM runtime บน host A และ B เป็น replica อิสระ พร้อมข้อมูลพอให้ PRP ผูก node กับ physical GPU, model profile และ epoch ได้หรือไม่

**ขั้นตอน**
1. Launch LLM runtime บน A และ B ตามวิธีของ candidate (A: Xinference supervisor + workers [SRC-09]; B: vLLM service ต่อเครื่อง [SRC-01]) ด้วย `shared_revision` เดียวกัน
2. ดึงสิ่งที่ candidate รายงานเกี่ยวกับแต่ละ runtime: model ID / revision, process ID, GPU ที่ผูก (เทียบกับ `nvidia-smi -L` UUID จริง), เวลาเริ่ม, ตัวระบุที่เปลี่ยนเมื่อ restart (มี epoch หรือเทียบเท่าหรือไม่)
3. ทดสอบ negative ตาม SRS: launch alias เดียวกันแต่ profile ต่างกันบน B แล้วดูว่า candidate แยกให้เห็นหรือรวมเป็นตัวเดียว; ตั้ง origin สองชื่อชี้ runtime เดียวกันแล้วดูว่า candidate นับเป็นสอง capacity หรือหนึ่ง
4. ตรวจว่าทุก endpoint ที่ใช้ในข้อ 1–3 ต้องมี credential (vLLM api-key อย่างเดียวไม่พอตาม [SRC-02]; Xinference auth ตาม [SRC-10])

**บันทึก:** payload จริงที่ candidate คืน (redact secret), mapping runtime → GPU UUID, พฤติกรรมข้อ 3 ทั้งสองกรณี, รายการ endpoint ที่เปิดโดยไม่มี auth

**เกณฑ์:** `PASS` เมื่อระบุ physical GPU และ restart identity ได้จากข้อมูลของ candidate; `PASS + ADAPT` เมื่อต้องอ่านจาก `nvidia-smi` เองแล้ว join; `FAIL` เมื่อ candidate ซ่อน placement หรือรวม alias ต่าง profile เข้าด้วยกันโดยไม่มีทางแยก

### EV03 Target binding — gate PRP-NFR-023

**คำถาม:** เมื่อสั่งให้ request ไป runtime A จริง ๆ มันไป A หรือไม่ และ candidate มี retry / failover / hedging ที่แอบส่งไป B โดย PRP ไม่รู้หรือไม่

**ขั้นตอน**
1. ส่ง request ที่ระบุเป้าหมาย A ผ่านทางที่ candidate ให้ (direct endpoint, model alias ที่ผูก A, หรือ routing layer) แล้วยืนยันจาก engine log / GPU utilization / request id ว่า A เป็นผู้ประมวลผล ทำซ้ำหลายครั้งพอให้เห็น pattern (จำนวนครั้งบันทึกใน `sample_count`)
2. ระหว่าง request ค้างอยู่บน A: ทำให้ A ช้า (throttle) และอีกรอบทำให้ A ตาย (kill process) แล้วสังเกตว่า candidate หรือ gateway ส่งซ้ำไป B เอง หรือคืน error ให้ผู้เรียก
3. ค้นหาและบันทึก config ทุกตัวที่ควบคุม retry / fallback / hedging (LiteLLM [SRC-03], Xinference routing [SRC-09]) พร้อมค่าที่ต้องตั้งเพื่อปิด แล้วรันข้อ 2 ซ้ำหลังปิด
4. ถ้า candidate มี routing layer: ตรวจว่า attempt ที่สองมี deadline เดิมและถูก readmit ได้หรือไม่ (ARCH §11: attempt เพิ่มต้อง account ได้)

**บันทึก:** หลักฐาน binding ต่อ request (log excerpt), จำนวน request ที่วิ่งผิดเครื่อง, config ที่ปิด retry, พฤติกรรมหลังปิด

**เกณฑ์:** `PASS` เมื่อ binding ตรงทุกครั้งและ retry ปิดได้ครบด้วย config; `PASS + CONFIGURE` เมื่อต้องตั้งค่าเฉพาะ; `FAIL` เมื่อยังมี implicit retry ที่ปิดไม่ได้ ซึ่งเป็น known gap SRC-03 / SRC-09 ที่ต้องได้คำตอบจากการรัน

ส่วนของ LiteLLM ในข้อ 2–4 รันเฉพาะภายใน sub-spike ที่กำหนดใน EV04 (time box ร่วมกัน)

### EV04 Identity / key semantics — gate PRP-FR-003..009

**คำถาม:** ระบบ key ของ candidate เป็น verifier-only (เก็บ hash เท่านั้น, เปิดดูภายหลังไม่ได้) และ scope key ตาม org / app / capability / model / expiry / quota / revoke ได้ครบตาม FR-003..009 หรือไม่ หรือ PRP ต้องเป็น key authority เอง

**ขั้นตอน**
1. สร้าง key ด้วยกลไกของ candidate (Xinference auth [SRC-10]; LiteLLM virtual keys [SRC-03]) แล้วพยายามอ่านค่า key กลับผ่านทุกช่องทาง (API, UI, DB, config dump, log) บันทึกว่าอ่านได้หรือไม่
2. ตรวจว่า key ผูกกับ organization / application / model / capability / expiry / quota ได้ระดับใด และการ list เห็นเฉพาะ scope ของตัวเองหรือเห็นทั้งหมด
3. Revoke key แล้ววัดว่า request ถัดไปถูกปฏิเสธภายในเวลาเท่าใด (วัดจริง) และ token ที่ออกก่อน revoke ใช้ต่อได้หรือไม่
4. ตรวจ first-admin bootstrap: ทำได้โดยไม่มี Zuri / FUNG / Lalin Studio หรือฐานข้อมูลธุรกิจอื่น (FR-001)

**บันทึก:** ทุกช่องทางที่ key ถูกอ่านกลับได้, ตาราง scope ที่รองรับ / ไม่รองรับต่อ FR, เวลา revoke ที่วัด

**เกณฑ์:** FR-005 `FAIL` ทันทีถ้า key อ่านกลับได้หลังออก (นี่คือ known gap ของ A ตาม SRC-10 ที่ต้องยืนยันด้วยการรัน); ผลรวมของ EV04 ตัดสินว่า key authority เป็น REUSE / CONFIGURE ของ candidate หรือ BUILD-GAP ที่ PRP เป็น verifier เอง (ADR-PRP: exactly one client-key authority)

**LiteLLM sub-spike (owner ตัดสิน 2026-09-20):** LiteLLM [SRC-03] อยู่ใน WP24 เฉพาะในฐานะ key / proxy layer ของ candidate B และรันเฉพาะ EV04 ข้อ 1–3 กับ EV03 ข้อ 2–4 รวมกัน **ไม่เกิน 1 วันทำงาน** หมดเวลาแล้วส่วนที่ไม่เสร็จลง `BLOCKED` ไม่ต่อเวลา ต้องได้คำตอบสามข้อ: (1) key เก็บเป็น hash และอ่านกลับไม่ได้จากทุกช่องทางหรือไม่ (2) revoke มีผลภายในเวลาเท่าใด (3) retry / fallback / smart routing ปิดได้ครบด้วย config หรือไม่ ผ่านครบ → `CONFIGURE` พร้อม operator cost ที่วัดได้ (service + datastore ที่เพิ่ม); ไม่ผ่านข้อใด → `BUILD-GAP` ที่ PRP เป็น verifier และ router เองพร้อมหลักฐาน ไม่รัน LiteLLM ใน EV05–EV08 และไม่ใช้ routing ของมันแทน PRP Router ในทุกกรณี (NFR-023)

### EV05 Atomic multi-process load — gate PRP-FR-017 / 018

**คำถาม:** เมื่อ PRP เป็นผู้จอง lease เอง candidate ยอมให้ปิดทางลัดตรงไปหา worker ได้หรือไม่ และ accounting ของ candidate ไม่นับ capacity ซ้ำเมื่อมีหลาย process เรียกพร้อมกันหรือไม่

ข้อจำกัดที่ต้องเขียนใน record: FR-017 (durable admission transaction) ต้องพิสูจน์ด้วย PostgreSQL จริง + fault injection ซึ่งเป็นฝั่ง PRP ที่ยังไม่มี adapter (M4) WP24 ตรวจได้เฉพาะฝั่ง candidate; แถว FR-017 ใน fit-gap จึงจบที่ disposition ของ candidate ได้ แต่ `runtime_test_status` ของ AT-017 ยัง NOT_RUN

**ขั้นตอน**
1. ตั้ง runtime ของ candidate ให้รับ traffic เฉพาะจาก control network / process ที่กำหนด (bind address, auth, network policy) แล้วพยายามเรียก worker ตรงจากเครื่องอื่นใน LAN ต้องถูกปฏิเสธ
2. จากหลาย process พร้อมกัน (จำนวนบันทึกใน `sample_count`) ส่ง request เกิน concurrency ที่ runtime ตั้งไว้ สังเกตว่า candidate queue, reject หรือรับเกิน และ metric ของมันนับ in-flight ตรงกับความจริงหรือไม่
3. บันทึก config ที่ควบคุม concurrency / queue ของ runtime (เช่น `max_num_seqs` ของ vLLM) และว่าอ่านค่าปัจจุบันจาก API ได้หรือไม่ เพื่อให้ Admission ของ PRP ใช้เป็น pressure signal (ARCH §5: metrics เป็น signal ไม่ใช่ guarantee)

**บันทึก:** ผล bypass test, พฤติกรรมเมื่อเกิน concurrency, ความตรงของ metric, config ที่เกี่ยว

**เกณฑ์:** `PASS` เมื่อปิดทางลัดได้และ metric ไม่ over-count; `FAIL` เมื่อ worker รับ traffic ตรงโดยปิดไม่ได้

### EV06 Timeout / restart — gate PRP-FR-020..022

**คำถาม:** เมื่อ runtime ตาย / restart / หมดเวลากลางคัน candidate บอกอะไรได้บ้าง และมัน "เล่นซ้ำ" inference ที่ค้างเองโดยไม่มีใครสั่งหรือไม่

**ขั้นตอน**
1. เริ่ม generation ยาว แล้ว (ก) ยกเลิกจากฝั่ง client, (ข) kill engine process, (ค) restart supervisor / service ทีละกรณี
2. ในแต่ละกรณีบันทึก: candidate มี cancel API หรือไม่และผลจริงเป็นอะไร (หยุด compute จริงหรือแค่ตัด connection), state ที่รายงานหลัง restart, request ที่ค้างถูกรันซ้ำอัตโนมัติหรือไม่ (blind replay ต้องไม่มี), เวลาจาก kill ถึง runtime พร้อมรับงานอีก (วัดจริง, ระบุ cold / warm)
3. ตรวจว่า candidate แยก "ไม่รู้ว่าเสร็จหรือไม่" ออกจาก "ล้มเหลวแน่" ได้หรือไม่ เพื่อให้ PRP map เป็น UNKNOWN / QUARANTINED ตาม ARCH §11 (timeout / cancel / lease expiry ไม่พิสูจน์ว่า compute หยุด)

**บันทึก:** ตารางกรณี × สิ่งที่ candidate รายงาน, หลักฐาน replay ถ้ามี, ความสามารถ cancel จริง

**เกณฑ์:** `PASS` เมื่อไม่มี blind replay และ state หลัง restart อ่านได้; `PASS + ADAPT` เมื่อ PRP ต้อง reconcile เอง; `FAIL` เมื่อ candidate replay งานค้างและปิดไม่ได้

### EV07 Mixed chat / speech — gate PRP-FR-018 / 044

**เงื่อนไข:** รันได้เฉพาะเมื่อ owner ตัดสินใน §2 ว่ามี speech candidate ที่พร้อมและผ่าน license gate ถ้ายัง ให้บันทึก `BLOCKED` พร้อม blocker "speech runtime ยังไม่ผ่าน WP10 / voice-rights" ทั้ง A และ B ไม่ใช้ stub ใด ๆ แทน

**ขั้นตอน (เมื่อรันได้)**
1. ให้ LLM resident บน host เดียวกับ speech runtime แล้วส่ง admitted load ผสม chat + ASR + TTS ภายใน envelope ที่ตั้งไว้ (เริ่มที่หนึ่ง invocation ต่อ node ตาม SRS: ไม่มี default GPU concurrency ที่รับรอง)
2. เก็บ VRAM / utilization ตามเวลา (`nvidia-smi --query-gpu ... -l`) ตลอดการรัน
3. สังเกตว่า candidate unload / relocate model เองหรือไม่ (A: Xinference auto-management ต้องปิดได้ เพราะ P1 ไม่ unload LLM อัตโนมัติ), มี OOM หรือไม่, และ speech ใช้ GPU เกิน resident envelope ที่วัดไว้หรือไม่

**บันทึก:** time series ของ VRAM, เหตุการณ์ unload / OOM, config ที่ปิด auto-management

**เกณฑ์:** `PASS` เมื่อไม่มี silent unload และไม่มี OOM ภายใต้ admitted load; `FAIL` เมื่อ candidate จัดการ residency เองโดยปิดไม่ได้

### EV08 Adapter / exit — gate PRP-NFR-024

**คำถาม:** ถ้าเลือก candidate นี้แล้ววันหนึ่งต้องออก public contract ของ PRP ต้องเปลี่ยนหรือไม่ และ config / key / artifact ย้ายออกได้หรือไม่

**ขั้นตอน**
1. เขียน mapping ระหว่าง model ID / alias ของ candidate กับ `ModelProfile` ของ PRP โดยไม่ให้ vendor ID โผล่ใน `prp-client.yaml` (ตรวจด้วย `validate_docs.py` ว่า contract ไม่เปลี่ยน)
2. Export config ทั้งหมดของ candidate เป็นไฟล์ redacted แล้วตรวจว่า import กลับได้บน host สะอาด
3. เขียน key-rotation plan: ถ้า key authority อยู่ที่ candidate (ผล EV04) จะ rotate / migrate อย่างไรโดย client ไม่ต้องรู้ vendor
4. ตรวจว่า artifact / job data ไม่ไปอยู่ใน datastore ของ vendor ที่ PRP ควบคุม deletion fence ไม่ได้

**บันทึก:** mapping table, export / import log, rotation plan, รายชื่อ datastore ที่ vendor ถือ

**เกณฑ์:** `PASS` เมื่อ public schema ไม่เปลี่ยนและทุกอย่าง export ได้; `FAIL` เมื่อ vendor schema หรือ ID ต้องรั่วเข้า public contract

### Operator cost (หลัง mandatory gates ครบ; STACK §7)

บันทึกเฉพาะที่วัดหรือนับได้จริง: จำนวนขั้นตอน deploy และเวลาที่ใช้ (cold, จาก host สะอาด), services และ datastores ที่ต้องดูแล, code ที่ต้องเขียนเพิ่ม (custom gap) ต่อ requirement, ขั้นตอน upgrade และ rollback ที่ลองทำจริง, licenses ที่ต้องมี, ทักษะที่ผู้ดูแลต้องมี ห้ามสรุปเป็นเปอร์เซ็นต์ประหยัดเวลา

## 6. Speech candidate และความสัมพันธ์กับ WP10

เอกสารชุดนี้ระบุว่า voice implementation แรก **อาจ** นำ ASR / TTS pipeline มาจาก Lalin-AI [SRC-07] (`apps/api/app/pipelines/asr.py`, `pipelines/tts.py`, `jobs/manager.py` ที่ commit `512e5c4`) แต่ต้องอยู่ใน headless voice-worker profile: ไม่ import Desktop / Studio state, ไม่ mount brain / fs / plugins / clone / music routes (FR-043, AT-043) ใน repository นี้ที่วางไว้แล้วคือ shell `workers/voice` (contract, lifecycle, server) ส่วน engine จาก Lalin จะเข้าที่ `prp_voice.engines` เท่านั้น

สำหรับ WP24 หมายความว่า

- Lalin-AI เป็น **reuse candidate ระดับ engine** ที่ต้องผ่าน fit-gap เหมือน candidate อื่น ไม่ใช่ผู้ส่งมอบ voice worker ทั้งตัว การเปรียบเทียบ "existing speech runtime กับ headless Lalin extraction" เป็น deliverable ของ WP10 (P1-B) ไม่ใช่ WP24
- ที่ WP24 ทำได้คือ source review ของ SRC-07 (ตรวจว่า pipeline แยกจาก Studio ได้จริงหรือผูก state) และ isolated spike ที่รัน faster-whisper / TTS แยกเครื่องเพื่อวัด resident envelope สำหรับ EV07 ถ้า owner อนุมัติ license ของ model
- ถ้ายังไม่ถึงเวลา ให้ EV07 และแถว FR-031 / 033 / 043 เป็น `BLOCKED` โดยระบุ blocker เป็น WP10 ไม่ใช้ DEFER

owner ตัดสินใจเมื่อ 2026-09-20 ว่า speech ไม่อยู่ใน scope ของ WP24 และให้ EV07 เป็น `BLOCKED` จนกว่า WP10 จะส่งมอบ speech candidate ที่มี license ครบ

## 7. การบันทึกผล

| สิ่งที่ผลิต | ที่เก็บ | ต้นแบบ |
|---|---|---|
| Run record หนึ่งไฟล์ต่อรอบ | `docs/evidence/wp24/<record_id>.json` | [`registry/wp24-run-record-template.json`](registry/wp24-run-record-template.json) |
| Artifact ของทุกคำสั่งและ log | `docs/evidence/wp24/<record_id>/<candidate>/<EVnn>/` | — |
| fit-gap ที่เติมผลจริง 92 แถว | `docs/registry/reuse-fit-gap.<record_id>.json` **copy** จาก template; template เดิมห้ามแก้ (validator ปฏิเสธ) | `registry/reuse-fit-gap-template.json` |
| candidate-level evidence + decision receipt | ส่วน `candidates` และ `decision_receipt` ใน run record ตามโครง `stack-evaluation-template.json` และ STACK §8 | `registry/stack-evaluation-template.json` |

`record_id` รูปแบบ `WP24-<YYYY-MM-DD>-run<n>` ทุกไฟล์อ้าง `record_id` เดียวกัน ค่าที่ต้องไม่เป็น null ตอนส่งตรวจ: `people.operator`, `people.reviewer`, `prepared_from.prp_commit`, `shared_revision.*` ที่ใช้จริง, `candidates[].version_manifest` ของทุก candidate ที่รัน, สถานะทุก gate ของทุก EV ที่ไม่ใช่ NOT_RUN ต้องมี `artifacts` อย่างน้อยหนึ่งรายการ

งาน tooling ที่ตามมา (ไม่อยู่ในเอกสารนี้): ขยาย `tools/docs/validate_docs.py` ให้ตรวจ run record กับ template (ชื่อ gate ตรง §6, ไม่มี PASS ที่ไม่มี artifact, fit-gap copy มี 92 แถวและ disposition ไม่ใช่ UNASSESSED) เมื่อมีไฟล์แรกจริง

## 8. เกณฑ์จบ WP24 (ตาม deliverable ใน `registry/roadmap.json`)

1. หลักฐาน A เทียบ B ครบทุก EV ที่รันได้ และ EV ที่รันไม่ได้มี `BLOCKED` พร้อม blocker ทั้งคู่
2. C มีผลเฉพาะเมื่ออยู่ใน scope ไม่บังคับ
3. Full requirement mapping: ทั้ง 92 แถวมี disposition ไม่ใช่ UNASSESSED หรือมี blocker ระบุ; ไม่มี P1 Must ที่เป็น DEFER
4. key-recovery gap (FR-005 ของ A) มีคำตอบจากการรันจริง
5. target-binding / retry / cancel (EV03, EV06) มีหลักฐานต่อ candidate
6. `decision_receipt` ตาม STACK §8 ครบทุก field พร้อม `rejected_alternatives` และ `rollback_exit_plan` ไม่มีตัวเลขที่ไม่ได้วัด
7. reviewer ลงชื่อ; owner อนุมัติวันที่ใด → เปิด WP03

## 9. สิ่งที่ owner ต้องตัดสินก่อนเริ่ม

1. รายการ LLM model และ license ที่จะใช้เป็น `shared_revision`
2. speech อยู่ใน WP24 หรือให้ EV07 เป็น BLOCKED จน WP10 (ถ้ารวม ต้องอนุมัติ voice rights ของ TTS ก่อน) — ตัดสินแล้ว 2026-09-20: speech ไม่อยู่ใน scope ของ WP24; EV07 เป็น BLOCKED จนกว่า WP10 (speech extraction spike) จะส่งมอบ speech candidate ที่มี license ครบ ไม่ใช้ stub เป็นหลักฐาน
3. C อยู่ใน scope หรือไม่ — ตัดสินแล้ว 2026-09-20: C ไม่อยู่ใน scope ของ WP24 (สองเครื่องไม่มีความจำเป็นต้องมี replica, STACK-EVALUATION-PRP หมวด 7 ไม่บังคับ C เมื่อ A/B อยู่ระหว่างประเมิน) (LiteLLM ตัดสินแล้ว 2026-09-20: เฉพาะ EV04 + EV03 ภายใน B, time box ไม่เกิน 1 วันทำงาน)
4. time box ต่อ candidate และชื่อ operator / reviewer — ตัดสินแล้ว 2026-09-20: time box = 3 วันทำงาน (8 ชั่วโมง/วัน) ต่อ candidate สำหรับ EV01–EV08 ไม่รวมเวลาดาวน์โหลด model weight, experiment ที่ยังไม่เสร็จเมื่อหมดเวลาเป็น BLOCKED ไม่ต่อเวลา; reviewer = Freshair129 เจ้าของ repository คนเดียวกับ operator เพราะไม่มีผู้ตรวจสอบอิสระคนที่สอง
