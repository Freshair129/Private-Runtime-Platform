---
document_id: CHANGELOG-PRP
title: "Change Log | v0.2.0 to v0.3.0"
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

# Change Log | v0.2.0 to v0.3.0

**PRP — Private Runtime Platform | v0.3.0 | 2026-09-20 | Draft for review**

## Unreleased — v0.4.0-draft

### M1 · Monorepo layout (2026-09-20, ADR-PRP-012 ACCEPTED)
- ย้าย package `PRP-Documentation-v0.3.0/` ไป `docs/releases/` ทั้งก้อนโดยไม่แก้ไข; `MANIFEST.sha256` ยัง verify ได้ 150 ไฟล์
- สร้าง living docs ที่ `docs/` (Markdown 16 ฉบับ, `standards/`, `diagrams/`, `registry/`) แก้ relative link จาก `../x/` เป็น `x/` และใน `standards/` จาก `../docs/` เป็น `../`
- ย้าย contracts ขึ้น `contracts/`: `openapi-prp-v0.3.0.{yaml,json}` → `openapi/prp-client.{yaml,json}` (version อยู่ใน `info.version`); ตัวอย่างไป `examples/`; inventory 12 paths / 14 operations / 21 schemas ไม่เปลี่ยน
- ย้าย tools ไป `tools/docs/`; validator อ่าน `docs/` และ `contracts/`, ข้าม `docs/releases/`; HTML builder เขียนลง `docs/` และเพิ่ม SDD-PRP-REPO ใน reading order
- เพิ่ม ADR-PRP-012 (monorepo layout, ACCEPTED) ใน ADR-PRP.md และ `SDD-PRP-REPO.md`; ADR-PRP.md bump เป็น 0.4.0-draft
- ลบ `github-setting/` (เอกสาร Playwright ของโปรเจกต์ GoVibe ไม่เกี่ยวกับ PRP และไม่อยู่ใน MANIFEST)
- เพิ่ม root `README.md`, `docs/README.md`, `.brain/README.md`, `.gitignore`, `.github/workflows/docs.yml`; แก้ link `standards/` ใน AGENTS.md
- แก้ `build_html_views.py` ให้ `read_text(encoding='utf-8')` ทุกจุด (เดิมล้มบน Windows locale cp874 เมื่ออ่าน catalog/SVG); verify แล้ว: validator `errors: []` 602 links, HTML views สร้างได้ 16 documents / 34 diagrams
- ไม่มีการเปลี่ยนข้อความ requirement, acceptance status หรือ roadmap status; ทุก AT ยัง NOT_RUN
- ค้างไว้: header ใน HTML builder ยังพิมพ์ "v0.3.0" (แก้ตอน bump version); `render_sequence.py` ยัง `write_text()` ไม่ระบุ encoding (แก้เมื่อต้อง render ใหม่); `Definition-of-Done` / `Risk-Assessment` / `Verification-Standards` ยังอ้าง Rust/Tauri/Vitest ต้อง map เป็น toolchain ตาม Coding-Standards §10 ใน task แยก

### M2 · Contracts (2026-09-20)
- เพิ่ม `contracts/openapi/prp-worker.yaml` (DRAFT, 5 operations: describe / readiness / invoke / execution evidence / cancel ตาม API-PRP §7, ARCH-PRP §9/§11, ADR-PRP-005) และ `contracts/openapi/prp-management.yaml` (DRAFT, 19 operations ตาม inventory API-PRP §8; field schemas freeze ที่ G0) ทั้งคู่มี `x-prp-status: DRAFT`, `x-prp-freeze-gate: WP03`
- YAML เป็น canonical; `tools/contracts/export_json.py` สร้าง `.json` และ `--check` ปฏิเสธไฟล์ค้าง `prp-client.json` regenerate แล้วเท่ากับเดิมเชิงความหมาย (deep-compare ก่อนเขียนทับ); inventory 12 paths / 14 operations / 21 schemas คงเดิม
- เพิ่ม `contracts/schemas/runtime-environment-manifest.schema.json` (encode NFR-021: control `model_loading_allowed` และ `cuda_initialization_allowed` เป็น const false; status QUALIFIED บังคับทุก service qualified) และ `contracts/examples/index.json`; `tools/contracts/validate_examples.py` ตรวจตัวอย่างทั้งสามผ่าน job payload validate กับ component ใน prp-client โดยตรง ไม่ทำ schema ซ้ำ
- validator ตรวจ OpenAPI ทุกไฟล์ใน `contracts/openapi/` (local refs, operationId ไม่ซ้ำ, security, `x-prp-status` สำหรับไฟล์ที่ไม่ใช่ client) และ YAML/JSON pairing; เพิ่ม `openapi_documents` ใน document-validation.json
- เพิ่ม `contracts/README.md`, `tools/contracts/requirements.txt` (pyyaml, jsonschema pin ตามที่ verify), `.github/workflows/contracts.yml`
- API-PRP §1 ชี้ไปยัง draft contracts และ bump เป็น 0.4.0-draft
- ค้างไว้ให้ WP03 ตัดสิน: Readiness เพิ่มค่า NOT_READY เกินตาราง API-PRP §7 (ระบุใน description); `PolicyUpdate.settings` ของ management ยังเป็น opaque object; security scheme ของ management (OperatorSession + OperatorKey) ต้องยืนยัน; TTS invocation คืน audio เป็น binary body พร้อม `X-PRP-*` headers

### M3 · Python skeleton = WP25 baseline (2026-09-20, C-3 / H4)
- คำตัดสิน owner: Python 3.12 สำหรับ control plane (speech ตาม engine compatibility ที่ M4), FastAPI + Pydantic เป็น candidate ของ `api/` ตาม ARCH §3, persistence/adapters เลื่อนไป M4 (skeleton มีเฉพาะ ports)
- `apps/control-api` (`prp-control` 0.4.0a0, `uv.lock` 35 packages ไม่มี ML/CUDA): `platform/` (ids, UTC clock, error codes + envelope ตาม API-PRP §2, redacting logger), `core/` 6 bounded contexts ตรงตาราง ARCH §2 พร้อม ports และ state rules (settlement fence, deadline → UNKNOWN, cancel semantics, outbox claim, lease quarantine, eligibility, artifact grant TTL), `api/` ผูก route ครบ 14 operations ของ `prp-client.yaml` (verify ด้วย conformance test) ทุก request ตอบ envelope: ไม่มี bearer → 401, มี bearer แต่ไม่มี verifier → 503 fail closed, `entrypoints/` สาม process โดย dispatcher/observer ปฏิเสธ start (exit 3) เมื่อไม่มี adapter
- `workers/voice` (`prp-voice` 0.4.0a0, lock แยก): contract models `extra="forbid"`, lifecycle (identity, epoch bump, readiness READY/NOT_READY/UNKNOWN ตามจริง), server ผูก 5 operations ของ `prp-worker.yaml`: describe/invoke 503, readiness NOT_READY, cancel UNSUPPORTED, evidence 501; service credential ตรวจ constant-time จาก env `PRP_VOICE_SERVICE_TOKEN` ไม่ตั้งค่า = 503
- Gates ผ่านทั้งสอง project: `ruff check`, `ruff format --check`, `mypy --strict` (40 / 10 files), `pytest` (36 / 14 tests), `lint-imports` (3 / 2 contracts kept: layers, core ไม่ import framework, ห้าม ML ทุก package); test `test_no_ml_import` ตรวจทั้ง `sys.modules` และ `uv.lock`
- Tests ติด marker `req(...)` ตาม SDD §9; `test_no_ml_import` ติด `at("PRP-AT-089")` เฉพาะส่วน import smoke; **ทุก acceptance ยัง NOT_RUN** ไม่มี receipt ใน `docs/evidence/`
- เพิ่ม `.github/workflows/control-api.yml`, `voice-worker.yml` (uv, path-filtered; `tests/hardware` ไม่ถูก collect ใน cloud)
- ค้างไว้: request/response Pydantic models ของ client API และคำตัดสิน generated-vs-handwritten ไป M4; ค่า `error.type` category ยัง draft (freeze WP03); `PYTHONUTF8=1` จำเป็นสำหรับ `lint-imports` บน Windows console cp874; `tools/trace/collect_trace.py` ยังไม่มี (SDD §9 ข้อ 3)

## Revision intent
ปรับชุด PRP ตามคำขอให้ใช้ Python ecosystem และประเมินของสำเร็จรูปก่อนเขียนเอง ไม่เปลี่ยนชื่อผลิตภัณฑ์ ไม่ย้าย PRP กลับเข้า Zuri ไม่เพิ่ม scope Phase 1 และไม่เลือก production framework แบบไม่มีหลักฐาน

| Area | v0.2.0 | v0.3.0 |
|---|---|---|
| Language | framework/language open | Python-first first-party control/adapters; no mandatory Rust/Tauri |
| Runtime strategy | vLLM + native-or-LiteLLM facade candidates | explicit A-Xinference / B-independent services fit-gap; Ray conditional C |
| Meaning of module boxes | logical responsibilities, easy to read as custom services | explicit REUSE/CONFIGURE/ADAPT/BUILD-GAP implementation map |
| Coding standards | screenshot was outside PRP package | new standards/Coding-Standards.md for Python/TS/process/security/CI |
| Requirements | 56 FR + 18 NFR + 12 SEC | existing IDs/subjects preserved; NFR-019..024 added (92 total P1) |
| Acceptance | AT001..086 NOT_RUN | AT087..092 added; all runtime tests still NOT_RUN |
| Roadmap | WP01..23 | WP24 A/B evaluation and WP25 Python engineering; dependencies updated |
| ADR | 001..008 | 004 selection envelope revised; 009..011 added |
| Diagram | D01..30 | originals retained/reconciled; D31..34 added for reuse/process/authority/binding |
| Public API | 12 paths / 14 operations | schemas/paths/operation IDs preserved; spec revision updated |

## Important findings incorporated
Xinference native auth described in current docs can reveal encrypted API keys; that is a gap against FR-005, not automatic compliance. Manager routing or hidden retries must not send work to a resource that lacks the matching lease. API worker replication must not multiply resident models. Ray logical GPU fractions do not prove VRAM isolation.

## Preserved guarantees
Independent PRP core; one physical-admission contract; full independent A/B chat replicas unless explicitly revised; separate resident/invocation resources; no automatic cloud fallback; client-owned voice workflow; no LINE credentials in workers; verifier-only client keys; object-level artifact access; uncertain-execution fencing; P2 image/video separate.

## Provenance and status
Original v0.2.0 ZIP and screenshot-derived Coding-Standards.md remain unchanged. This is a new documentation package, not a repository commit, migration, deployment or working runtime selection. New framework comparison evidence templates contain NOT_RUN/UNASSESSED, not test results. Numerical SLO targets from v0.2.0 were not weakened.

## ID / source authority
Canonical requirement statements remain in SRS-PRP.md. Registry/tests/trace are regenerated and checked against it. No ID was recycled. Existing subject anchors are retained. The package contains no PRP application implementation or production lockfile; sample manifests are labeled templates.