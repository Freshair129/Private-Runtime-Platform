---
document_id: CODING-STANDARDS-PRP
title: "Coding Standards | PRP Python-first"
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

# Coding Standards | PRP Python-first

**PRP — Private Runtime Platform | v0.3.0 | 2026-09-20 | Draft for review**

เอกสารที่เกี่ยวข้อง: [SRS](../docs/SRS-PRP.md) · [Architecture](../docs/ARCH-PRP.md) · [Stack Evaluation](../docs/STACK-EVALUATION-PRP.md)

## 1. Scope and authority
มาตรฐานนี้ใช้กับ PRP เท่านั้น แทนการนำ screenshot-based Rust/Tauri standards มาเป็นข้อบังคับ backend ไม่แก้หรือลบ Coding-Standards.md ต้นฉบับที่ถอดจากภาพ PRP SRS เป็น requirement source; ไฟล์นี้กำหนดแนวปฏิบัติให้ผ่าน NFR-019..024 ไม่สร้าง product scope เพิ่ม

Python เป็น baseline สำหรับ first-party control/API/ports/adapters; React/TypeScript สำหรับ optional frontend; model engines/native kernels ใช้ implementation ของผู้พัฒนาเดิมได้ Rust/Tauri ไม่เป็น build/runtime requirement ของ core; native optimization ต้องมี profiling/ADR ข้อยกเว้น

## 2. Reuse before implementation
ก่อนเพิ่ม component ให้ระบุ requirement IDs และ disposition REUSE/CONFIGURE/ADAPT/BUILD-GAP จาก WP24 ใช้ documented extension points ของ library ก่อน fork ห้ามเขียน inference engine, batching, key database หรือ process supervisor ซ้ำเพียงเพราะ diagram มีกล่องนั้น

Framework-specific objects อยู่ใน adapter เท่านั้น Core domain ไม่ import Zuri/FUNG/Lalin Studio และไม่ส่ง vendor state classes ออก public API ไม่แก้ undocumented vendor DB tables ถ้าต้องแก้ upstream ให้แยก patch provenance, tests และ upgrade/exit plan

## 3. Python package and type rules
ใช้ `src/` layout สำหรับ Python packages และแยก API/application/domain/ports/adapters เท่าที่ complexity จำเป็น Public functions, adapters และ message envelopes ต้องมี type hints; ใช้ Protocol/dataclass หรือ validated schema ตามหน้าที่ เลี่ยง Any ที่ public boundary; third-party untyped interface ต้อง narrow/validate ที่ adapter พร้อมคำอธิบาย

Pydantic/validation เป็น candidate สำหรับ request/response/config; field/extra handling ต้องตรง API contract ห้าม silent coercion ที่เปลี่ยน quota/identity ใช้ stable enums สำหรับ outcome/execution/resource states และ timezone-aware UTC ใน persisted timestamps

## 4. Async, process and resource rules
ใช้ async สำหรับ network/storage I/O ที่มี async driver; อย่าเรียก synchronous model inference, ffmpeg งานยาว หรือ blocking SDK ตรง control event loop ใช้ dedicated bounded worker service/process ไม่ใช่ thread pool ไม่จำกัด

ห้าม import/load torch, CUDA, Whisper, TTS weights ใน control startup path เพิ่ม web workers ต้องไม่เพิ่ม runtime replicas แต่ละ runtime/process มี lifecycle owner, restart policy และ readiness gate ของตัวเอง

ไม่ใช้ module-global dict/asyncio.Lock เป็น quota/capacity authority ข้าม process; ใช้ selected durable primitives ที่ผ่าน race tests การ cancel coroutine/thread future ไม่ใช่ hard termination; ต้องเคารพ UNKNOWN/QUARANTINED และไม่ catch cancellation แล้วรายงาน success

## 5. Adapter and HTTP contracts
ใช้ shared bounded HTTP clients, verified TLS, explicit timeouts และ absolute request deadline; validate approved target ก่อน connect และไม่ follow redirects ไป endpoint นอก allowlist ค่า retry/fallback ของ SDK/gateway ต้อง configure ชัดและไม่ replay post-dispatch ambiguous inference

Adapter report capability/readiness/physical identity/epoch/usage provenance จริง ไม่แต่ง confidence, throughput, free-capacity หรือ termination เมื่อไม่ทราบ ข้อผิดพลาดให้ typed stable error code พร้อม trace ID; sanitize vendor bodies/stack traces ก่อนออกนอก boundary

## 6. Persistence and consistency
Database access ผ่าน repository/transaction ports ข้อมูล authoritative แต่ละชุดมี writer contract เดียว Logical model ไม่เท่ากับต้องสร้างตารางซ้ำกับ frameworkที่มอบหมาย owner ไปแล้ว

Idempotency keys ผูก scope+route+payload digest; unique constraints/fencing รองรับ parallel processes ไม่ใช้ in-memory dedupe แทน durable guarantee Preserve attempt evidence, erasure tombstones และ quota reservations ระหว่าง deployment/restore

## 7. Dependencies, environments and model assets
Control, LLM และ speech มี lock/image boundaries แยกเมื่อ dependency ขัดกัน เลือก exact Python/engine/CUDA compatibility ใน WP25 ไม่บังคับ Python รุ่นใหม่สุดกับทุก model environment Vendor image ต้อง pin digest และบันทึก provenance; repo-owned Python project เสนอ uv เป็น lock/build tooling [SRC-16]

Dev/production installs ใช้ lock ที่ตรวจแล้ว ไม่ `pip install -U` ตอน start ห้าม blanket all-extras เมื่อดึง ML stack ที่ไม่จำเป็น ห้ามดาวน์โหลด weights จาก API request; stage assets ด้วย revision/checksum และ approved license/voice record ก่อน ready

Secrets ไม่อยู่ใน pyproject, lock, examples, notebooks, logs หรือ source `.env`; เสนอเฉพาะชื่อ environment variables ไม่มีค่าจริง Export config ต้องไม่กู้ client key plaintext กลับมา

## 8. Logging and observability
Structured metadata logs มี request/job/attempt/profile IDs, timestamps, duration, status และ owner scope ที่ปลอดภัย ไม่ log raw prompt/transcript/audio/Authorization/signed URL โดย default Metrics ที่ไม่มีเป็น unavailable พร้อม observed_at ไม่เป็นศูนย์ความจุ

## 9. Frontend rules
React functional components และ TypeScript strict; domain-independent UI logic แยกจาก DOM; state library เป็น implementation choice ไม่บังคับ Zustand หรือ glassmorphism จากเอกสารภาพเดิม

UI ใช้ public/management API ตามสิทธิ์ ไม่อ่าน vendor DB หรือ worker port โดยตรง ไม่เก็บ API/master key ใน localStorage ใช้ session ที่ป้องกัน CSRF หรือ credential flow ที่ได้รับ review localStorage ใช้กับ non-sensitive preferences เท่านั้น Transcript/artifact lifetime ไม่ขึ้นกับ browser cache

## 10. Testing and CI
แยก unit, API conformance, real database concurrency, framework integration, physical GPU/voice quality และ live external channel tests ชื่อ mock PASS ไม่ครอบคลุม GPU/live gate Fixture ไม่ใช้ customer secrets/audio โดยไม่มีสิทธิ์

Required cases เพิ่ม: control no-ML import, API-worker multiplication, hidden manager reroute/retry, restart ambiguity, recoverable-key rejection, vendor binding export/rotation ผ่าน NFR-019..024 Tests ต้องรายงาน collected/executed/skipped; zero tests หรือ mandatory gate skipped ไม่ถือว่า complete

Proposed Python toolchain: Ruff lint/format [SRC-17], mypy strict สำหรับ first-party packages, pytest และ dependency/license/security scans ที่เลือกใน WP25 Frontend มี TypeScript typecheck และ UI test gates แยก

คำสั่งตัวอย่างหลัง repository มี `pyproject.toml`, lock, package และ tests จริงแล้ว (ไม่ได้รันกับเอกสารล้วนชุดนี้):

```sh
uv sync --locked --group dev
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy --strict src/prp
uv run --locked pytest tests/unit tests/contracts
```

ห้ามใช้ผล `tools/validate_docs.py` แทนคำสั่งข้างต้น เพราะตรวจโครงสร้างเอกสารเท่านั้น Schema/build/import/dependency checks เป็นส่วนหนึ่งของ CI ไม่ใช่ substitute for integration/physical tests

## 11. Definition of done
มี requirement/ADR link, reuse disposition, implementation และ tests ที่มีอยู่จริง, immutable dependency/profile IDs, compatible API, security/resource evidence ตาม gate, updated docs/trace และ rollback plan ไม่มี unresolved critical failures; feature ที่ยังไม่รันให้ระบุ NOT_RUN/BLOCKED

ก่อน merge เปลี่ยน dependencies/framework ต้องทบทวน key/permission defaults, egress, retries, process counts, memory residency และ state migration ใหม่ทุกครั้ง ไม่ย้ายชื่อผลิตภัณฑ์หรือเพิ่ม UI แล้วนับว่า core runtime ผ่าน