# Private-Runtime-Platform (PRP)

PRP คือ self-hosted inference platform สำหรับ chat / ASR / TTS บนสองเครื่อง GPU ใน LAN เดียวกัน repository นี้เป็น **monorepo** ที่เก็บเอกสารออกแบบ (canonical), protocol contracts และ code ของ PRP ไว้ด้วยกันตาม [ADR-PRP-012](docs/ADR-PRP.md#ADR-PRP-012) และ [SDD-PRP-REPO](docs/SDD-PRP-REPO.md)

สถานะปัจจุบัน: เอกสาร v0.4.0-draft; implementation ยัง NOT_STARTED; acceptance test ทุกรายการ NOT_RUN

## โครงสร้าง

| ตำแหน่ง | บทบาท | สถานะ |
|---|---|---|
| [`docs/`](docs/README.md) | living documentation: SRS (requirement authority), PRD, Roadmap, ARCH, API, ADR, Test Plan, standards, diagrams, derived registry | มีแล้ว (M1) |
| [`docs/releases/`](docs/releases/) | release package ที่ frozen พร้อม `MANIFEST.sha256` ห้ามแก้ | v0.3.0 |
| [`contracts/`](contracts/) | protocol source of truth: OpenAPI client contract (`openapi/prp-client.yaml`), ตัวอย่าง payload/manifest | มีแล้ว (M1); worker/management contract ที่ M2 |
| [`tools/`](tools/) | repo tooling เท่านั้น: `docs/` validator, HTML builder, sequence renderer | มีแล้ว (M1) |
| `apps/control-api/` | Python control plane (`src/prp`) | M3 (= WP25) |
| `workers/voice/` | Python ASR/TTS worker ใน environment แยก | M3 |
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
