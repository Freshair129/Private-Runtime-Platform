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

### ADR-PRP-013 action item 5 · SDD-PRP-REPO สะท้อน generated contract models (2026-09-20, C-1 / H2)
- SDD-PRP-REPO §5: contract models เป็น derived code ที่ generate ด้วย `gen_models.py`; กติกาผู้เขียน YAML (named component ทุก object, URL ใช้ `pattern: ^https://`, ทุก JSON operation ผูก route กับ generated model, escape hatch `_manual.py`); inventory ระบุ 12 paths / 14 operations และอธิบายว่าจำนวน component เปลี่ยนได้เฉพาะแบบ wire-equivalent (21 → 30)
- §6.1 / §6.3: เพิ่ม package `contracts/` ใน tree และ layer diagram (import Pydantic เท่านั้น; forbidden ไป core / platform / api / adapters); บันทึก W-Scale `src/prp` 5 → 6 = W3 พร้อมเหตุผลจาก ADR-PRP-013 item 2 ทั้งใน governance frontmatter และ §6.1; หัวข้อ §6.3 ระบุว่าใช้ import-linter ตั้งแต่ M3 (§12 ข้อ 6 ตัดสินแล้ว)
- §7: `contract/` = `generated.py` + `base.py` + `models.py` (re-export); §9: เพิ่ม YAML → JSON / generated models → routes → conformance test เข้า traceability diagram, ข้อ 5 ระบุ `--check` ทุกตัว, ข้อ 6 ใหม่กำหนดสิ่งที่ conformance test ต้องตรวจและวิธีบันทึกข้อยกเว้น; §10: tier conformance ครอบคลุม voice และ `contracts.yml` ระบุ step จริง
- header สถานะ: M1–M3 เสร็จ, ADR-PRP-013 ผสานแล้ว, M4 รอ WP24; ADR-PRP-013 action items ครบ 5/5; ไม่มี code เปลี่ยน

### CI · required status checks บน `main` (2026-09-20, C-1 / H4)
- owner สั่งหลัง merge PR #1: branch protection ของ `main` กำหนด job ทั้งห้า (`Validate documentation structure`, `YAML is canonical, JSON is derived, examples conform`, `Coding-Standards 10 gates (no-ML control plane)`, `Coding-Standards 10 gates (no hardware tier in cloud CI)`, `Markers -> code-trace.json -> acceptance status gate`) เป็น required status checks; ไม่บังคับ up-to-date (`strict: false`), ไม่บังคับ review (owner คนเดียว), admin bypass ได้ตาม Hotfix rule ใน AGENTS.md, ห้าม force-push และห้ามลบ branch
- ทั้งห้า workflows เปลี่ยน trigger `pull_request` จาก `paths` เป็น `branches: [main, develop]` เพื่อให้รันทุก PR (required check ที่ไม่รันจะทำให้ PR ค้าง "Expected" ตลอดไป); `push` ยังใช้ path filter เดิม; ต้นทุนเพิ่มราว 20 วินาทีต่อ job ต่อ PR
- CLAUDE.md และ SDD-PRP-REPO §10 อธิบายกติกานี้และเตือนว่าการเปลี่ยนชื่อ job ต้องอัปเดต protection rule คู่กัน

### AGENTS.md cleanup (2026-09-20, C-1 / H2)
- ลบส่วน "Mobile Testing Mindset (ARTEMIS Integration)" ออกจาก `AGENTS.md` (docs(agents): remove unrelated ARTEMIS section inherited from the initial commit) — เป็นกฎ Android UI-automation ที่ไม่เกี่ยวกับ PRP อยู่นอก R1–R10; ไม่มีไฟล์อื่นอ้างอิงส่วนนี้

### WP24 experiment procedure และ run-record template (2026-09-20, C-2 / H4 เมื่อรัน; เอกสาร C-1)
- owner อนุมัติ 2026-09-20: เพิ่ม `docs/WP24-EXPERIMENT-PROCEDURE.md` ขั้นตอนทดลอง EV01–EV08 ต่อ candidate A / B (C เฉพาะเมื่ออยู่ใน scope) ผูกกับ gate ของ STACK-EVALUATION §6 ทุกข้อ: เงื่อนไขก่อนเริ่มที่ owner / ops จัดหา, กติการันร่วม (revision เดียว, cold / warm แยก, log ทุกคำสั่ง, mandatory gates ก่อน operator cost), เกณฑ์ PASS / FAIL / BLOCKED ต่อ requirement, การบันทึกผล และเกณฑ์จบ WP24 ตาม deliverable ใน roadmap.json ไม่มีผลการรัน, version pin หรือตัวเลขใด
- เพิ่ม `registry/wp24-run-record-template.json` สร้างจาก gate EV01–EV08 ใน `reuse-fit-gap-template.json` โดยตรง: environment, `shared_revision`, candidates ตามโครง `stack-evaluation-template.json` + `operator_cost_measurements` (STACK §7), `gate_verdicts` ต่อ requirement ต่อ candidate, `source_observations` แยกจาก `measurements`, `decision_receipt` ครบ field ตาม STACK §8; run record จริงจะอยู่ที่ `docs/evidence/wp24/<record_id>.json` และ fit-gap copy ที่ `registry/reuse-fit-gap.<record_id>.json` (template เดิมไม่แก้)
- Lalin-AI [SRC-07] จัดเป็น reuse candidate ระดับ engine ของ speech worker ตาม FR-043 / WP10 ไม่ใช่ผู้ส่งมอบ worker ทั้งตัว; EV07 เป็น BLOCKED จน speech candidate ผ่าน license / voice-rights gate
- STACK-EVALUATION §6 ชี้ไปยัง procedure; `docs/README.md` เพิ่มแถว; `evidence/README.md` อธิบายโฟลเดอร์ `wp24/` ว่าไม่ใช่ acceptance receipt; HTML builder ORDER เพิ่มเอกสารหลัง STACK-EVALUATION; ทุก AT ยัง NOT_RUN
- owner ตัดสิน 2026-09-20 (บันทึกใน procedure §2 / EV03 / EV04 / §9 และ `scope_decisions` ของ template): LiteLLM อยู่ใน WP24 เฉพาะ EV04 + EV03 ในฐานะ key / proxy layer ของ candidate B time box รวมไม่เกิน 1 วันทำงาน routing ของมันไม่แทน PRP Router; โมเดลเป็น BYOM โดย license receipt ตาม SEC-007 ยังต้องมีก่อน activation; C และ speech ยังไม่ตัดสิน

### WP24 EV01 run record · WP24-2026-09-20-run1 (2026-09-20, C-2 / H4)
- รัน EV01 (Clean control install; gate NFR-019 / 021 / 022) จริงครั้งแรก operator = owner บันทึกที่ `docs/evidence/wp24/WP24-2026-09-20-run1.json` พร้อม artifact ใน `docs/evidence/wp24/WP24-2026-09-20-run1/{PRP,A}/EV01/` ทุกตัวเลขในการ record มาจาก log ที่แนบ ไม่มีตัวเลขพิมพ์มือ; reviewer ยังไม่ลงชื่อ (`people.reviewer: null`) ทุก EV อื่นยัง NOT_RUN
- ผล shared PRP ที่ `30a7d39`: fresh checkout + `uv sync --locked` ทั้งสอง project ผ่าน, gates §10 ผ่านครบ (pytest 50 / 22, mypy 45 / 12 files, lint-imports 4 / 2), `prp-api` โดยไม่ตั้ง `PRP_*` ตอบ 401 `INVALID_KEY` เมื่อไม่มี credential และ 503 `STATE_STORE_UNAVAILABLE` เมื่อมี bearer, dispatcher / observer exit 3, import ทุก module ของ `prp` (44) ไม่มี ML module ใน `sys.modules`, process ของ `prp-api` ไม่อยู่ในรายชื่อ compute process ของ `nvidia-smi`; verdict PASS ทั้งสาม gate
- candidate A: `xinference-client` 3.4.0 ติดตั้ง 20 packages และ import โดยไม่มี ML module → PASS; ข้อสังเกตสำหรับ adapter: module path `restful.restful_client` จากเอกสารเก่าไม่มีแล้ว export อยู่ที่ top level (`RESTfulClient`, `AsyncRESTfulClient`) candidate B: ไม่ต้องมี SDK ฝั่ง control (HTTP only; LiteLLM อยู่นอก EV01 ตามคำตัดสิน) → PASS; candidate C: BLOCKED เพราะ scope ยังไม่ตัดสิน
- **Deviation DEV-01**: control host ที่ใช้มี NVIDIA driver (RTX 5060 Ti) ไม่ตรง precondition §2 ของ procedure หลักฐาน NFR-021 จึงอาศัย `sys.modules` + GPU process list บันทึกให้ reviewer ตัดสินว่ารับได้หรือต้องรันซ้ำบน host ที่ไม่มี driver; เวลาที่วัดเป็น wall clock บน workstation ที่มี process อื่นรันอยู่และ uv cache warm เป็นค่าอ้างอิงไม่ใช่ benchmark
- `registry/wp24-run-record-template.json` เพิ่มโครง `experiments.EV01.shared_prp` (ส่วนของ PRP เองที่รันครั้งเดียวต่อ record) และ `deviations` เพื่อให้ record ทุกรอบบันทึกได้ในที่เดียวกัน; fit-gap copy ยังไม่สร้างจนกว่า candidate แรกจะครบ EV01–EV08 (ระบุใน record)

### แก้ precondition EV01 ที่เขียนเกินข้อกำหนด (2026-09-20, C-1 / H2, RCA-2026-09-20-ev01-host-precondition)
- owner ถามว่าทำไมห้ามมี GPU บน control host ทั้งที่มีสองเครื่องและทั้งคู่เป็นทั้ง control และ GPU worker; ตรวจแล้ว SRS host topology และ ARCH §3 ให้ control co-locate บน CPU ของ A ได้ NFR-021 / 022 ต้องการเพียง process และ dependency isolation precondition "control host ไม่มี GPU driver" ใน procedure §2 / EV01 จึงเป็นข้อผิดพลาดของ procedure (RCA ใน `.brain/rca/`)
- procedure §2 และ EV01 แก้ให้ GPU driver บนเครื่อง control เป็นสิ่งที่บันทึก ไม่ใช่สิ่งต้องห้าม เกณฑ์ PASS ของ NFR-021 ระบุหลักฐานจริง: ไม่มี ML module ใน `sys.modules` หลัง import ทุก module ของ control และ process ของ `prp-api` ไม่อยู่ใน GPU process list; host ไม่มี driver เป็นหลักฐานเสริมที่เลือกได้
- record `WP24-2026-09-20-run1`: DEV-01 คงไว้เพื่อประวัติพร้อม `resolution` และสถานะ RESOLVED_PROCEDURE_CORRECTED; verdict และ artifact ของ EV01 ไม่เปลี่ยน; template `control_host.gpu_driver_present` default เป็น null

### WP24 owner decisions ชุดที่สอง · reviewer, time box, C out of scope, EV07 blocked until WP10 (2026-09-20, C-1 / H2)
- owner ให้คำตัดสินด้วยวาจากับ main session เมื่อ 2026-09-20 สี่ข้อ บันทึกลง `docs/evidence/wp24/WP24-2026-09-20-run1.json`, `docs/registry/wp24-run-record-template.json` (โครงเท่านั้น) และ `docs/WP24-EXPERIMENT-PROCEDURE.md` §6 / §9
- **Reviewer**: owner ทำหน้าที่ reviewer เองด้วยเพราะไม่มีบุคคลที่สอง — `people.reviewer` = "Freshair129 (repository owner; same person as operator, no independent reviewer available)"; `decision_receipt.tests_and_blocked_items` บันทึกข้อจำกัดนี้ไว้
- **Time box**: 3 วันทำงาน (8 ชั่วโมง) ต่อ candidate สำหรับ EV01–EV08 ไม่รวมเวลาดาวน์โหลด model weight — `run_window.time_box_hours_per_candidate` = 24 พร้อม field ใหม่ `time_box_note`; experiment ที่ยังไม่เสร็จเมื่อหมดเวลาเป็น BLOCKED ไม่ต่อเวลา; template เพิ่ม `time_box_note: null` ข้าง `time_box_hours_per_candidate` เป็นโครงสร้างเท่านั้น (ไม่ใส่ค่า)
- **Candidate C**: ตัดสินไม่อยู่ใน scope ของ WP24 (สองเครื่องไม่มีความจำเป็นต้องมี replica, STACK-EVALUATION-PRP หมวด 7 ไม่บังคับ C เมื่อ A/B อยู่ระหว่างประเมิน) — `scope_decisions.candidate_C_in_scope` เป็น object พร้อมเหตุผล; `candidates[C]` เป็น `in_scope: false`, `status: BLOCKED`; ทุก EV01–EV08 `per_candidate.C` เป็น BLOCKED พร้อม blocker และ `gate_verdicts` เป็น BLOCKED ทั้งหมด
- **Speech**: ตัดสินไม่อยู่ใน scope ของ WP24; EV07 เป็น BLOCKED จนกว่า WP10 (speech extraction spike) จะส่งมอบ speech candidate ที่มี license — `scope_decisions.speech_in_scope` เป็น object เดียวกัน; EV07 ของ candidate A / B เป็น BLOCKED พร้อม blocker และ `gate_verdicts` เป็น BLOCKED (candidate C ของ EV07 ใช้ blocker ของ C แทน)
- ไม่มีการรัน experiment ใหม่ ไม่มีตัวเลข benchmark ใหม่ และไม่แตะ `docs/registry/reuse-fit-gap-template.json` / `stack-evaluation-template.json`

### WP24 EV02 operator tooling (2026-09-20, C-2 / H2)
- เพิ่ม `tools/wp24/`: `host_inventory.py`, `ev02_probe.py`, `ev02_gpu_binding.py`, `ev02_restart_identity.py` (Python 3.12, stdlib เท่านั้น, ไม่มี ML import) ให้ owner รันบน GPU host A/B และจาก control machine เพื่อผลิตหลักฐานของ EV02 "Real A/B registration" (gate `PRP-FR-010`..`PRP-FR-015`) ตาม `docs/WP24-EXPERIMENT-PROCEDURE.md`; ทุกสคริปต์เขียน JSON ที่มี `measurements`, `observations`, `source_observations` (ว่างเสมอ, operator เติมเอง), `artifacts`, timestamp ISO-8601 UTC และ `command_line` ที่ผ่านการ redact — **ไม่คำนวณ verdict** PASS/FAIL/BLOCKED เป็นของ reviewer เท่านั้น
- credential มาจาก env var ที่ `--token-env` ระบุชื่อเท่านั้น ไม่เคยอยู่ใน CLI argument หรือถูกพิมพ์ออก; `Authorization` header ที่ปรากฏใน log เขียนเป็น `Authorization: <redacted>` เสมอ; ทุก output ถูก redact home-directory path (`C:\Users\<name>\...`, `/home/<name>/...`, `/Users/<name>/...`) เป็น `<home>` ก่อนเขียนไฟล์
- default endpoint ของแต่ละ candidate อ้างอิง official docs ที่ตรวจแล้ว: candidate B (vLLM) `GET /v1/models` และ `GET /metrics` ([SRC-01], `docs.vllm.ai/.../openai_compatible_server/`, `docs.vllm.ai/.../usage/metrics.html`, `docs.vllm.ai/.../usage/security/` สำหรับขอบเขตของ `--api-key`); candidate A (Xinference) `GET /v1/models`, `GET /v1/model_registrations/LLM` ([SRC-09]), `GET /v1/workers`, `GET /v1/supervisor`, `GET /v1/cluster/auth` (ยืนยันจาก official client source เพราะหน้า narrative docs ไม่ได้ระบุ path เหล่านี้), `GET /v1/admin/setup/status` ([SRC-10]) endpoint ที่ยืนยันไม่ได้ต้องมาจาก `--endpoints endpoints.json` และถูกทำเครื่องหมาย unverified เสมอ
- เพิ่ม `tools/wp24/EV02-CHECKLIST.md` (Thai prose, English identifiers): จับคู่ EV02 ขั้นตอน 1–4 กับสคริปต์ข้างต้น รวม negative test ของขั้นตอน 3 ที่ต้องสังเกตด้วยมือ, reset-between-candidates checklist จาก procedure §3 ข้อ 1, ตำแหน่งที่ copy ไฟล์ (`docs/evidence/wp24/<record_id>/<candidate>/EV02/`) และ mapping ไปยัง `experiments.EV02.per_candidate.<X>.{measurements,observations,artifacts}`; ระบุว่า LiteLLM sub-spike (EV03/EV04) เตรียมแยกที่ `tools/wp24/litellm_subspike/` โดยงานอื่น ไม่ได้สร้างไว้ในที่นี้
- เพิ่ม `tools/wp24/tests/test_wp24_tools.py` (`unittest`, stdlib) ครอบคลุม pure function: CSV parsing ของ `nvidia-smi`, redaction, และ identifier diffing; ยืนยันด้วย `python -m unittest discover`, `python -m py_compile`, และ `uv run --locked ruff check`/`format --check` จาก `apps/control-api` ชี้ไปที่ `../../tools/wp24`
- CLAUDE.md เพิ่มแถว `tools/wp24/` ในตาราง layout; SDD-PRP-REPO §3 เพิ่ม `tools/wp24/` ใน repository tree และหมายเหตุ W-Scale ของ `tools/` (4 รายการ, W2, อยู่ในช่วง 3–5)
- ไม่มีการรันจริงต่อ candidate ในงานนี้ (C-2/H2, tooling เท่านั้น); ไม่มีการแก้ registry template หรือเปลี่ยนสถานะ acceptance ใด ๆ

### WP24 LiteLLM sub-spike kit (2026-09-20, C-2 / H2)
- เพิ่ม `tools/wp24/litellm_subspike/` ตามคำตัดสิน owner 2026-09-20 (`docs/registry/wp24-run-record-template.json` `scope_decisions.litellm`; WP24-EXPERIMENT-PROCEDURE.md หมวด 5 EV04 บล็อก "LiteLLM sub-spike"): ชุดเครื่องมือเตรียมการเท่านั้น ยังไม่ deploy หรือรันจริง — `docker-compose.litellm.template.yml` (LiteLLM proxy + PostgreSQL, bind 127.0.0.1 เท่านั้น, TEMPLATE / NOT_QUALIFIED เหมือน `contracts/examples/`), `litellm_config.template.yaml` (model list สอง alias หนึ่งต่อ host พร้อม `router_settings` ที่ปิด retry / fallback / cooldown / weighted-failover ทุกตัวที่เอกสารมีสวิตช์ให้), `ev04_keys.py` และ `ev03_retry_probe.py` (Python 3.12 stdlib เท่านั้น ไม่ print หรือเก็บ plaintext key ใด ๆ ลงดิสก์ output เป็น `sha256:<12 hex แรก>` fingerprint เท่านั้น), `ev04_readback_checklist.md` (ภาษาไทย ขั้นตอน manual สำหรับ DB table / proxy log / config dump / Admin UI ที่ script เข้าไม่ถึง), `README.md` (แผนหนึ่งวันทำงาน, สามคำถามที่ต้องตอบ, operator cost, ที่เก็บ evidence) และ `tests/test_litellm_subspike.py` (`unittest`, 28 เคสผ่าน)
- ทุกข้อเท็จจริงเกี่ยวกับ LiteLLM ตรวจกับเอกสารทางการก่อนเขียน พร้อม cite URL ไว้ใน comment ของแต่ละไฟล์: `docs.litellm.ai/docs/proxy/virtual_keys` (ต้องมี PostgreSQL + `DATABASE_URL` สำหรับ virtual keys, endpoint `/key/generate`, `/key/info`, ข้อความเรื่อง key hash), `docs.litellm.ai/docs/proxy/model_access` (`/v1/models` กับ virtual key), `docs.litellm.ai/docs/proxy/response_headers` (`x-litellm-model-id` ฯลฯ ที่ระบุ deployment ที่ตอบ), `docs.litellm.ai/docs/routing` และ `docs.litellm.ai/docs/proxy/config_settings` (ตาราง reference ของ `router_settings`: `num_retries`, `disable_cooldowns`, `enable_weighted_failover` ฯลฯ พร้อม default), `docs.litellm.ai/docs/proxy/reliability` (`disable_fallbacks` ต่อ request/key), `docs.litellm.ai/docs/proxy/db_info` และ `github.com/BerriAI/litellm/blob/main/schema.prisma` (ตาราง `LiteLLM_VerificationToken`), `docs.litellm.ai/docs/proxy/deploy` และ `github.com/BerriAI/litellm/blob/main/docker-compose.yml` (pin image tag, PostgreSQL 16), `docs.litellm.ai/docs/providers/vllm` (`hosted_vllm/` provider route); endpoint `/key/delete` และ `/key/list` ยืนยันจาก live OpenAPI spec ที่ `litellm-api.up.railway.app/openapi.json` (ลิงก์จากหน้า virtual_keys เอง) เพราะไม่มีหัวข้อบรรยายตรง ๆ ในหน้า markdown
- จุดที่เอกสารไม่ชัดหรือขัดแย้งกันเอง (เช่น field `token` ใน `/key/info` เป็น hash หรือ plaintext, hedging / parallel-request switch ที่ไม่มีเอกสารรองรับ) บันทึกเป็น "unverified; observe at run time" ไม่เดา เครื่องมือทุกชิ้นไม่เขียน verdict PASS/FAIL ใด ๆ เอง — เป็นหน้าที่ของผู้ทดลอง/ผู้ตรวจตาม WP24-EXPERIMENT-PROCEDURE.md เท่านั้น
- gates ที่รันผ่าน: `python -m py_compile` ทั้งสอง script, `python -m unittest discover -s tools/wp24/litellm_subspike/tests` (28/28 ผ่าน), `uv run --locked ruff check` และ `ruff format --check` จากภายใน `apps/control-api` (ใช้ config เดียวกับ control-api: line-length 100, target py312)
- ไม่แตะไฟล์อื่นใต้ `tools/wp24/` (`README.md` ระดับบน, `EV02-CHECKLIST.md`, EV02 scripts เป็นของ agent อื่น) และไม่แก้ `CLAUDE.md` หรือ `docs/SDD-PRP-REPO.md`; ไม่มีการ deploy หรือรันจริงใน task นี้

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