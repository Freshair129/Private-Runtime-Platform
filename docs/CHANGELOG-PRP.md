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

### Trace tooling · SDD §9 ข้อ 3–5 (2026-09-20, C-2 / H3)
- เพิ่ม `tools/trace/collect_trace.py` (stdlib) รัน `uv run --locked pytest --collect-only` ในทุก project ใต้ `apps/*` และ `workers/*` ผ่าน plugin `tools/trace/pytest_trace_plugin.py` แล้วเขียน `docs/registry/code-trace.json` (requirement → tests, acceptance → tests + tiers) แบบ deterministic; `--check` ปฏิเสธไฟล์ค้างและ marker ที่อ้าง ID ไม่มีในทะเบียนหรือ test ที่อ้าง AT มากกว่าหนึ่ง
- validator เปลี่ยนจาก "ห้าม PASS ทุกกรณี" เป็น **status gate**: AT ที่ไม่ใช่ NOT_RUN ต้องมี test ที่ collect ได้ใน code-trace.json และ receipt ครบ (`evidence_id`, `commit`, `reviewer`, `status` ตรง) ใน `docs/evidence/`; PASS จาก tier unit/contracts ได้เฉพาะ proof ที่เป็น contract / packaging / portability / design evidence / operations review / load mock ล้วน มิฉะนั้นต้องมี tier integration หรือ hardware; receipt `status: NOT_RUN` ถูกปฏิเสธ
- `document-validation.json` เพิ่ม `acceptance_status`, `evidence_receipts`, `code_trace_tests`; `runtime_test_status` คำนวณจากสถานะจริงแทน hard-code
- เพิ่ม `docs/evidence/README.md` (รูปแบบ receipt, ชื่อไฟล์, ขั้นตอนเปลี่ยนสถานะ) และ `.github/workflows/trace.yml` (sync ทุก project → `collect_trace.py --check` → validator)
- สถานะยังคง NOT_RUN ทั้ง 92 กรณี ไม่มี receipt

### WP24 fit-gap preparation (2026-09-20, C-2 / H2)
- `registry/reuse-fit-gap-template.json` เติมคอลัมน์ derived ต่อแถว: `title`, `srs_section`, `phase`, `epic`, `acceptance_test`, `proof` (จาก requirements registry), `stack_eval_reuse_rows` (STACK-EVALUATION §3 ตาม SRS section 5.x), `evaluation_experiments` (gate ของ EV01–EV08 จาก §6) และ `source_review` (finding ที่เอกสารระบุไว้แล้วพร้อม SRC ID, `doc_ref`, สถานะ SOURCE_REVIEWED_NOT_RUNTIME_TESTED) รวม 21 requirements / 37 findings; เพิ่มคอลัมน์ผลลัพธ์ตาม §5 ที่ยังเป็น null (`observed_capability`, `limitation`, `maintenance_exit_risk`) และ `experiments` + `record_fields_required_at_wp24` ระดับไฟล์
- ทุกแถวคง `disposition: UNASSESSED`, `runtime_test_status: NOT_RUN`; ไม่มี version pin, คะแนน หรือผล runtime; version template เป็น 0.4.0-draft
- `registry/stack-evaluation-template.json` เพิ่ม known source-only gaps: SRC-09 (A, NFR-023 bound routing untested), SRC-03 (A/B, NFR-023 gateway retries ต้อง readmit), SRC-12 (C, FR-044 logical fraction ไม่ใช่ VRAM cap) ตาม STACK §4
- validator ตรวจ template: คอลัมน์ derived ต้องตรง requirements.json, `evaluation_experiments` ต้องตรง gate ของ EV01–EV08, ทุก `source_review.source` ต้องอยู่ใน SOURCES-PRP register, คอลัมน์ผลลัพธ์ต้องเป็น null, และ stack-evaluation ต้องไม่ประกาศผู้ชนะ; เพิ่ม `fitgap_source_findings` ใน document-validation.json
- STACK-EVALUATION-PRP §5 เพิ่มย่อหน้า WP24 preparation และ bump เป็น 0.4.0-draft

### ADR-PRP-013 ACCEPTED + contract naming pass (2026-09-20, C-2 / H2)
- เพิ่ม ADR-PRP-013 ใน ADR-PRP.md: contract models ต้อง generate จาก OpenAPI YAML ด้วย `datamodel-code-generator` ที่ pin ไว้ (flags กำหนดใน ADR, base class `extra="forbid" + frozen`, `--strict-types int float bool`) เป็น derived file ที่ commit และ `--check` ใน CI ห้ามเขียนมือยกเว้น escape hatch ที่มี conformance test; owner อนุมัติพร้อมคำแนะนำทั้งสามข้อ (เก็บ description, frozen, generate management ตั้งแต่ DRAFT) หลักฐาน spike อยู่ใน ADR
- Action item 1 ทำแล้ว: promote inline object schema เป็น named component ในทั้งสาม YAML (client 21→29, worker 22→32, management 16→19 components เช่น `ErrorBody`, `ChatChoice`, `NamedToolChoice`, `TtsJobResult`, `ChatDelta`, `EvidenceDetail`, `CancellationSupport`, `PolicyScope`, `AcceptanceTestId`) พิสูจน์ด้วย dereference ว่า paths, components เดิม และส่วนอื่นเท่ากันทุก byte เชิงความหมาย; inventory 12 paths / 14 operations เท่าเดิม; JSON regenerate; generator ไม่ตั้งชื่อเองอีก
- test conformance ของ control-api resolve `$ref` ใน Error envelope แทนอ่าน inline
- action items 2–5 ของ ADR-013 (gen_models tool, generate + wire, FastAPI binding, docs) รอ M4 kickoff

### ADR-PRP-013 action item 2 · generator wrapper (2026-09-20, C-2 / H3)
- เพิ่ม `tools/contracts/gen_models.py`: ตาราง contract → project → module → base class, flags ตาม ADR rule 3, post-step `ruff check --fix --select I` และ `ruff format` ของ project เป้าหมายผ่าน `uv run --locked` ให้ output canonical, `--check` regenerate แล้วเทียบ; pin `datamodel-code-generator==0.82.0` ใน `tools/contracts/requirements.txt`; `contracts.yml` sync ทุก project แล้วรัน `gen_models.py --check`
- generated modules: `apps/control-api/src/prp/contracts/{client_v1,worker_v1,management_v1}.py` และ `workers/voice/src/prp_voice/contract/generated.py` (307 / 434 / 267 / 434 บรรทัด) พร้อม base class `ContractModel` (`extra="forbid"`, `frozen=True`) ที่เขียนมือหนึ่งไฟล์ต่อ project; regenerate ซ้ำไม่มี diff
- ปรับ placement จาก ADR-013 rule 5: control-api รวม generated modules ใน package `prp.contracts` (layer ใต้ `api | adapters` เหนือ `core`) เพราะ base class เดียวต่อ project (rule 4) ต้องถูก import จากทั้ง api และ adapters ซึ่ง layer rule ห้าม import กัน; import-linter เพิ่ม layer นี้และ contract ห้าม `prp.contracts` import อะไรนอกจาก Pydantic; per-file-ignores E501 เฉพาะ generated modules
- gates ผ่านทั้งสอง project (mypy --strict 45 / 12 files, lint-imports 4 / 2 contracts kept, pytest 36 / 14); ยังไม่ wire เข้า route และ `prp_voice.contract.models` ที่เขียนมือยังอยู่จน action item 3; SDD §5–§6 อัปเดตที่ action item 5

### ADR-PRP-013 action items 3–4 · generated models wired into routes (2026-09-20, C-2 / H3)
- control-api: ทั้ง 14 routes ผูก body / parameters / success response กับ generated models (`ChatRequest`, `JobRequest` + header `Idempotency-Key`, `GrantRequest`, `SpeechRequest`; path `UUID`; query `limit` 1–100; status 201 / 202 / 204; `cancelJob` ประกาศทั้ง 200 และ 202) handler ยัง fail closed 503 จนกว่าจะมี adapter; multipart ของ `transcribeAudio` / `uploadArtifact` ยังไม่ผูกจนมี upload path (ต้อง python-multipart) test บันทึกข้อยกเว้นนี้ไว้ชัดเจน
- voice worker: `prp_voice.contract.models` เปลี่ยนเป็น re-export จาก `generated.py` เหลือเฉพาะ Literal aliases 4 ตัวที่มี test กัน drift; server ผูก `InvocationRequest` / `CancelRequest`, path `attempt_id: UUID`, query `ge=0`; response_model ครบ 5 operations
- conformance tests ใหม่ทั้งสอง project เทียบ `app.openapi()` กับ contract ต่อ operation หลัง normalize (type, property set, required, enum, const, format, bounds, oneOf) ตาม ADR-013 rule 8 และ strictness tests: string number / bool และ unknown field → 400 INVALID_REQUEST, UUID / date-time เป็น string → ผ่าน validation แล้วจึง 503, naive datetime → 400, ยืนยันคำอธิบายใน ADR rule 4 บน FastAPI path จริง
- contract: promote response inline ของ `listCapabilities` เป็น component `CapabilityList` (client 29→30) และเปลี่ยน `format: uri` เป็น `type: string` + `pattern: ^https://` ใน 4 field (`Grant.url`, `AsrPayload.artifact_grant_url`, `NodeRegistration.origin`, `NodeUpdate.origin`) เพราะ Pydantic `AnyUrl` รับ pattern ไม่ได้ทำให้ generator ทิ้ง https constraint; พิสูจน์ด้วย dereference ว่า wire format เท่าเดิม ต่างเฉพาะ metadata `format`
- gates ผ่าน: pytest 50 / 22, mypy --strict 45 / 12, lint-imports 4 / 2, `gen_models --check` เสถียร; `code-trace.json` regenerate; ทุก AT ยัง NOT_RUN

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