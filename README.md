# Private-Runtime-Platform (PRP)

PRP คือ self-hosted inference platform สำหรับ chat / ASR / TTS บนสองเครื่อง GPU ใน LAN เดียวกัน repository นี้เป็น **monorepo** ที่เก็บเอกสารออกแบบ (canonical), protocol contracts และ code ของ PRP ไว้ด้วยกันตาม [ADR-PRP-012](docs/ADR-PRP.md#ADR-PRP-012) และ [SDD-PRP-REPO](docs/SDD-PRP-REPO.md)

สถานะปัจจุบัน: เอกสาร v0.4.0-draft; implementation ยัง NOT_STARTED; acceptance test ทุกรายการ NOT_RUN

## โครงสร้าง

| ตำแหน่ง | บทบาท | สถานะ |
|---|---|---|
| [`docs/`](docs/README.md) | living documentation: SRS (requirement authority), PRD, Roadmap, ARCH, API, ADR, Test Plan, standards, diagrams, derived registry | มีแล้ว (M1) |
| [`docs/releases/`](docs/releases/) | release package ที่ frozen พร้อม `MANIFEST.sha256` ห้ามแก้ | v0.3.0 |
| [`contracts/`](contracts/README.md) | protocol source of truth: OpenAPI client / worker / management contracts, JSON Schema ของ runtime manifest, ตัวอย่าง payload | มีแล้ว (M1–M2); worker และ management เป็น DRAFT freeze ที่ WP03 |
| [`tools/`](tools/) | repo tooling เท่านั้น: `docs/` validator, HTML builder, sequence renderer; `contracts/` YAML→JSON export และ example validation; `trace/` รวม pytest markers เป็น `code-trace.json` | มีแล้ว |
| [`docs/evidence/`](docs/evidence/README.md) | receipt ของการรันจริง ต้องมีคู่กับ test ที่ collect ได้ก่อน acceptance status จะออกจาก NOT_RUN | ว่าง (ยังไม่มี runtime test) |
| [`apps/control-api/`](apps/control-api/README.md) | Python control plane (`src/prp`): platform, 6 core contexts + ports, api ผูก 14 operations, 3 entrypoints | มีแล้ว (M3) skeleton fail closed; adapters ที่ M4 |
| [`workers/voice/`](workers/voice/README.md) | Python ASR/TTS worker ใน environment แยก: contract, lifecycle, server 5 operations | มีแล้ว (M3) skeleton fail closed; engines ที่ M4 |
| `deploy/` | host A/B composition templates, pinned vendor images | M4 |
| [`.brain/`](.brain/README.md) | RCA และ proposal drafts ตาม AGENTS.md | มีแล้ว |

## ตรวจสอบ

```sh
python tools/docs/validate_docs.py
```

ตรวจโครงสร้างเอกสารใน `docs/` และ contract ใน `contracts/` (stdlib เท่านั้น; exit 1 เมื่อพบข้อผิดพลาด) ผลจริงอยู่ที่ `docs/registry/document-validation.json`

```sh
python tools/docs/build_html_views.py
```

สร้าง `docs/PRP-Documentation.html` และ `docs/PRP-Diagram-Atlas.html` (ต้องมี `markdown-it-py`, `beautifulsoup4`) ไฟล์ที่สร้างไม่ commit ใน living tree; CI อัปโหลดเป็น artifact

## กติกาการทำงาน

- [AGENTS.md](AGENTS.md): R1–R10 (assumptions ก่อนลงมือ, doc-first รออนุมัติ, surgical change, RCA ก่อนแก้ bug, complexity classification)
- [docs/standards/STD-Execution-Governance.md](docs/standards/STD-Execution-Governance.md): C-0..C-3, Access Scope H0–H4, W-Scale และ header ที่ทุก task ต้องประกาศ
- [docs/standards/Git-Standards.md](docs/standards/Git-Standards.md): Conventional Commits, หนึ่ง task ต่อ PR, spec/RCA commit พร้อม code
