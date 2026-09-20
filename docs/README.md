# PRP — Private Runtime Platform · Living documentation

**v0.4.0-draft · 2026-09-20 · Python-first / Reuse-before-build · Runtime tests: NOT_RUN · Implementation: NOT_STARTED**

โฟลเดอร์นี้คือเอกสาร **ที่มีชีวิต** ของ PRP แก้ไขได้ทุกวันโดยไม่ต้องออก package ใหม่ ส่วน package ที่ส่งมอบแล้วอยู่ใต้ [`releases/`](releases/) และห้ามแก้ โครงสร้างนี้กำหนดโดย [ADR-PRP-012](ADR-PRP.md#ADR-PRP-012) และ [SDD-PRP-REPO](SDD-PRP-REPO.md)

## อะไรเป็น authority

| ประเภท | ไฟล์ | กติกา |
|---|---|---|
| **Canonical** | [SRS-PRP.md](SRS-PRP.md) (requirements), [ROADMAP-PRP.md](ROADMAP-PRP.md) (work packages), [ADR-PRP.md](ADR-PRP.md) (decisions), [TEST-PRP.md](TEST-PRP.md) (acceptance status), [`../contracts/openapi/*.yaml`](../contracts/) (protocol) | แก้ที่นี่ที่เดียว |
| **Derived** | [`registry/`](registry/) (requirements/roadmap JSON, validation output, templates), HTML reading views | ห้ามแก้ด้วยมือ; regenerate ด้วย `tools/docs/` แล้วตรวจว่าไม่มี diff (gen_registry ยังไม่มี: ระหว่างนี้ validator ตรวจว่า JSON ตรงกับ Markdown แบบคำต่อคำ) |
| **Frozen** | [`releases/PRP-Documentation-v0.3.0/`](releases/PRP-Documentation-v0.3.0/README.md) | ตรวจด้วย `sha256sum -c MANIFEST.sha256`; มี Word/HTML/PDF ของ v0.3.0 อยู่ที่นั่น |

Requirement IDs (PRP-FR/NFR/SEC/P2), acceptance IDs (PRP-AT-nnn), work packages (WP01–WP25) และ diagram IDs (D01–D34) เป็น stable IDs; registry, traceability และภาพเป็น derived views ของ SRS

## เอกสาร

| เอกสาร | หน้าที่ |
|---|---|
| [PRD-PRP](PRD-PRP.md) | Product goals, users, journeys, scope และ reuse objective |
| [SRS-PRP](SRS-PRP.md) | 56 FR + 24 NFR + 12 SEC = 92 P1 requirements; 8 P2 envelopes |
| [ROADMAP-PRP](ROADMAP-PRP.md) | 25 work packages, dependencies, gates และ A/B evaluation |
| [ARCH-PRP](ARCH-PRP.md) | Python-first composition, framework bindings, resource/state boundaries |
| [SDD-PRP-REPO](SDD-PRP-REPO.md) | โครงสร้าง repository, เอกสาร และ code; migration plan M1–M4 |
| [API-PRP](API-PRP.md) | Client subset, worker adapter และ private management contract boundaries |
| [STACK-EVALUATION-PRP](STACK-EVALUATION-PRP.md) | A/B/C candidates, fit-gap, experiments และ decision receipt |
| [Coding Standards](standards/Coding-Standards.md) | Python/typing/async/process/dependency/test/TS frontend standards |
| [SECURITY-DATA-PRP](SECURITY-DATA-PRP.md) | Keys, roles, threats, framework-private routes, retention/erasure |
| [OPS-PRP](OPS-PRP.md) | Qualification, drain, restart, recovery, isolated environments และ migration |
| [ADR-PRP](ADR-PRP.md) | 12 decisions; Python direction revised, framework choice remains open, monorepo layout accepted |
| [TEST-PRP](TEST-PRP.md) | 92 acceptance specifications; ทุกกรณี NOT_RUN |
| [TRACEABILITY-PRP](TRACEABILITY-PRP.md) | Requirement → epic/owner/phase/test/diagram |
| [BASELINE-CHANGES-PRP](BASELINE-CHANGES-PRP.md) | Historical Zuri-owned → independent PRP ownership migration |
| [CHANGELOG-PRP](CHANGELOG-PRP.md) | Change register (v0.2.0 → v0.3.0 และ unreleased) |
| [SOURCES-PRP](SOURCES-PRP.md) | Upstream sources, dates, provenance และ limits |
| [DIAGRAMS-PRP](DIAGRAMS-PRP.md) | 34 diagram descriptions, editable sources และ export links |
| [QA-REPORT-PRP](QA-REPORT-PRP.md) | ผลตรวจเอกสาร v0.3.0 (historical) แยกจาก runtime ที่ยังไม่ทดสอบ |
| [standards/](standards/) | Execution governance (C/H/W), Git, DoD, Risk, RCA, Verification, DDD/Diagram SSOT |

## เครื่องมือ

```sh
python tools/docs/validate_docs.py
```

ตรวจโครงสร้าง (stdlib เท่านั้น): SRS anchors ↔ registry, 92 acceptance anchors, roadmap dependencies, diagram sources/exports, relative links, OpenAPI local refs ผลอยู่ใน [registry/document-validation.json](registry/document-validation.json) การตรวจนี้เป็น DOCUMENT_STRUCTURE_ONLY ไม่ใช่ runtime PASS

```sh
python tools/docs/build_html_views.py
```

สร้าง `PRP-Documentation.html` และ `PRP-Diagram-Atlas.html` ในโฟลเดอร์นี้ (ต้องมี `markdown-it-py`, `beautifulsoup4`) ไฟล์ที่สร้างถูก gitignore; CI อัปโหลดเป็น artifact และจะ commit เฉพาะตอน snapshot เป็น release

Graphviz: `dot -Tsvg diagrams/source/D01.dot -o diagrams/svg/D01.svg`; sequence diagram: `python tools/docs/render_sequence.py diagrams/source/D07.sequence.json --out <dir>` แล้ว copy กลับ `.mmd` เป็น editable source คู่กับ `.sequence.json` ต้อง reconcile กัน

## การออก release

snapshot ทุกอย่างในโฟลเดอร์นี้ยกเว้น `releases/` → rebuild HTML → export Word/PDF → เขียน `MANIFEST.sha256` → วางเป็น `releases/PRP-Documentation-vX.Y.Z/` → bump `version` ใน frontmatter และ CHANGELOG

## ประวัติ

- v0.2.0: แยก PRP ออกจาก Zuri-owned design
- v0.3.0: Python-first / reuse-first revision; frozen ที่ `releases/PRP-Documentation-v0.3.0/`
- v0.4.0-draft: monorepo layout (ADR-PRP-012, M1) — เอกสารย้ายมาที่นี่, contracts และ tools ขึ้น repo root
