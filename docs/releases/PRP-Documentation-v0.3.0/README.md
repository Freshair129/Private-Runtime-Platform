# PRP — Private Runtime Platform

## Documentation package · v0.3.0 · 20 September 2026

**Python-first / Reuse-before-build. Draft for review. Runtime tests: NOT_RUN.**

PRP เป็นแพลตฟอร์มอิสระสำหรับทีมและหลายแอป ไม่ต้องติดตั้ง Zuri, FUNG หรือ Lalin Studio การแก้ไขนี้นำทิศทาง Python-first มาใส่ใน PRD/SRS/Roadmap/ADR และ Coding Standards พร้อมการประเมินของสำเร็จรูปก่อนเขียน infrastructure เอง ไม่ใช่การเลือก framework หรืออนุมัติ production โดยอัตโนมัติ

## เริ่มอ่าน

แตก ZIP โดยรักษาโครงสร้างโฟลเดอร์ แล้วเปิด **[PRP-Documentation.html](PRP-Documentation.html)** เพื่ออ่านเอกสาร 15 ฉบับในหน้าเดียว หรือ **[PRP-Diagram-Atlas.html](PRP-Diagram-Atlas.html)** เพื่อค้นหา/กรอง/ขยาย 34 แผนภาพและบันทึก SVG เนื้อหาและภาพฝังใน HTML ไม่ต้องใช้ CDN; ลิงก์อ้างอิงภายนอกยังต้องใช้อินเทอร์เน็ต

**[Diagram Atlas PDF — 36 หน้า](PRP-Diagram-Atlas.pdf)**: สารบัญ/บุ๊กมาร์ก และ 34 ภาพแบบเวกเตอร์บนหน้า A3 ที่เลือกแนวตามสัดส่วนภาพ คำอธิบายภาษาไทยเพิ่มเติมอยู่ใน HTML/Markdown

## สิ่งที่เปลี่ยนจาก v0.2.0

ใช้ Python เป็น baseline ของ first-party control/API/policy/adapters; ไม่มีข้อบังคับ Rust/Tauri สำหรับ core (native C++/CUDA/Rust ภายใน dependency ยังใช้ได้) ประเมิน **A: Xinference-managed runtimes** เทียบ **B: independent vLLM/speech services + gateway** ก่อนเลือก stack ส่วน **C: Ray Serve** ประเมินเมื่อมีเหตุผล ไม่ติดตั้งทับกันโดยอัตโนมัติ

ชื่อโมดูล PRP แสดง contract ownership ไม่ใช่คำสั่งให้เขียนทุกอย่างเอง ใช้ REUSE / CONFIGURE / ADAPT / BUILD-GAP / DEFER ต่อ requirement และต้องมีหลักฐานรองรับ custom gap ทุกจุด คงสิทธิ์/โควตา/physical resource admission/uncertain execution เดิม ไม่ลด security เพื่อเลือก library

แยก control web process ออกจาก model process/env; เพิ่ม API workers ไม่เพิ่ม model copies โดยอัตโนมัติ Framework ต้องไม่ retry/ย้ายโหนดโดยไม่ผูก resource admission เข้ากับ actual execution ปรับ Roadmap ให้มี WP24 fit-gap และ WP25 Python environment baseline ก่อน implementation

เก็บ 86 requirement IDs และเนื้อหาข้อกำหนดเดิม เพิ่ม PRP-NFR-019..024 และ AT-087..092 รวม **92 ข้อ / 92 acceptance specifications**; API subset เดิม 12 paths / 14 operations ไม่เปลี่ยนเชิงโครงสร้าง (อัปเดตเฉพาะ version)

รายละเอียด: **[Change Log](docs/CHANGELOG-PRP.md)** และ **[Stack Evaluation](docs/STACK-EVALUATION-PRP.md)**

## เอกสาร

| เอกสาร | หน้าที่ | Word |
|---|---|---|
| [PRD-PRP](docs/PRD-PRP.md) | Product goals, users, journeys, scope และ reuse objective | [9 หน้า](word/PRD-PRP-v0.3.0.docx) |
| [SRS-PRP](docs/SRS-PRP.md) | 56 FR + 24 NFR + 12 SEC = 92 P1 requirements; 8 P2 envelopes | [28 หน้า](word/SRS-PRP-v0.3.0.docx) |
| [ROADMAP-PRP](docs/ROADMAP-PRP.md) | 25 work packages, dependencies, gates และ A/B evaluation | [12 หน้า](word/ROADMAP-PRP-v0.3.0.docx) |
| [ARCH-PRP](docs/ARCH-PRP.md) | Python-first composition, framework bindings, resource/state boundaries | — |
| [API-PRP](docs/API-PRP.md) | Client subset, worker adapter และ private management contract boundaries | — |
| [STACK-EVALUATION-PRP](docs/STACK-EVALUATION-PRP.md) | A/B/C candidates, fit-gap, experiments และ decision receipt | — |
| [Coding Standards](standards/Coding-Standards.md) | Python/typing/async/process/dependency/test/TS frontend standards | — |
| [SECURITY-DATA-PRP](docs/SECURITY-DATA-PRP.md) | Keys, roles, threats, framework-private routes, retention/erasure | — |
| [OPS-PRP](docs/OPS-PRP.md) | Qualification, drain, restart, recovery, isolated environments และ migration | — |
| [ADR-PRP](docs/ADR-PRP.md) | 11 decisions; Python direction revised, framework choice remains open | — |
| [TEST-PRP](docs/TEST-PRP.md) | 92 acceptance specifications; ทุกกรณี NOT_RUN | — |
| [TRACEABILITY-PRP](docs/TRACEABILITY-PRP.md) | Requirement → epic/owner/phase/test/diagram | — |
| [BASELINE-CHANGES-PRP](docs/BASELINE-CHANGES-PRP.md) | Historical Zuri-owned → independent PRP ownership migration | — |
| [CHANGELOG-PRP](docs/CHANGELOG-PRP.md) | Exact v0.2.0 → v0.3.0 change register | — |
| [SOURCES-PRP](docs/SOURCES-PRP.md) | Upstream sources, dates, provenance และ limits | — |
| [DIAGRAMS-PRP](docs/DIAGRAMS-PRP.md) | 34 diagram descriptions, editable sources และ export links | — |
| [QA-REPORT-PRP](docs/QA-REPORT-PRP.md) | ผลตรวจเอกสารจริง แยกจาก runtime ที่ยังไม่ทดสอบ | — |

## Phase boundaries และลำดับเริ่มงาน

**WP01/WP02 → WP24 → WP03 → WP25 → WP04**: scope/hardware → A/B evidence → architecture/authority selection → isolated Python baseline → control-plane integration. Prototype ที่แยกจาก production ทำได้ก่อน แต่ห้ามนับ spike เป็น production implementation

G0 design/reuse selection → P1-A keys + two independent chat nodes + console → P1-B ASR/TTS + jobs/artifacts + independent playground → P1-C measured qualification/restore/mixed-load/pilot. LINE integration เป็น gate แยก ไม่ใช่ dependency ของ core. P2-A image และ P2-B video ต้อง freeze model/quality/resources แยก

ไม่มีวันเสร็จหรือจำนวนทีมที่สมมติขึ้น ทุก implementation work package ยังคง NOT_STARTED ทุก runtime acceptance ยังคง NOT_RUN

## Source authority และไฟล์ประกอบ

- `docs/SRS-PRP.md` เป็นแหล่งข้อกำหนด; PRD/Roadmap/Architecture/Diagram ไม่ใช่ข้อกำหนดชุดใหม่ที่แก้แยกได้
- `standards/Coding-Standards.md` เป็นมาตรฐาน PRP โดยเฉพาะ ไม่เขียนทับไฟล์ Rust/Tauri ที่ถอดจากภาพเดิม
- `word/` และ HTML/PDF เป็น reading views; มี DOCX 3 เล่ม รวม 49 หน้า
- `diagrams/` มี 34 SVG + 34 PNG พร้อม DOT หรือ sequence JSON/Mermaid ต้นฉบับ ไม่รวม font files
- `contracts/` มี OpenAPI JSON/YAML 12 paths / 14 operations / 21 schemas, ตัวอย่าง jobs และ runtime environment manifest **TEMPLATE / NOT_QUALIFIED** ไม่ใช่ไฟล์ deploy พร้อมใช้
- `registry/` มี requirements/roadmap, evidence templates, fit-gap template ครบ 92 ข้อ และ stack evaluation template; ช่องว่างหลักฐานคง UNASSESSED/NOT_RUN ไม่ใส่คะแนนหรือ benchmark สมมติ
- `tools/` มี document validator, HTML builder และ sequence renderer; ไม่ใช่ application implementation
- `MANIFEST.sha256` เป็น checksum ของ package files ยกเว้น manifest เอง

ตรวจโครงสร้างเอกสาร (Python standard library):

```sh
python tools/validate_docs.py
```

สร้าง HTML ใหม่หลังแก้ Markdown/catalog (ต้องมี `markdown-it-py`, `beautifulsoup4`):

```sh
python tools/build_html_views.py
```

Graphviz: `dot -Tsvg diagrams/source/D01.dot -o D01.svg`; sequence: ใช้ `tools/render_sequence.py` กับ `.sequence.json` ตาม CLI ของสคริปต์ Mermaid `.mmd` เป็น equivalent editable source ที่ต้อง reconcile กับ JSON ไม่แก้แยกจน drift

## ขอบเขตที่ต้องรักษา

Client ถือ voice-turn/agent/RAG/memory/LINE delivery; PRP ให้ atomic chat/ASR/TTS; worker ไม่มี credential ของ business app ไม่มี cloud inference fallback โดยปริยาย; timeout/cancel/lease expiry ไม่เท่ากับ compute stopped; request จบไม่เท่ากับ resident model memory ถูกคืน

มี key authority เพียงชุดเดียวสำหรับ client; credential ไป runtime เป็นคนละประเภท ข้อมูลที่เข้ารหัสแต่ยังอ่าน key กลับได้ไม่ตรง FR-005 ซึ่งต้อง verifier-only: บันทึกข้อจำกัด auth ของ Xinference เป็น source-reviewed gap ไม่อ้างว่าเลือกแล้ว compliance ครบ

Framework selection, exact versions/model/voice licenses, GPU placement/capacity, admin API freeze และค่าประสิทธิภาพยังต้องตัดสิน/ทดสอบ การอนุมัติแก้เอกสารไม่ใช่ runtime PASS ไม่มีการแก้ repository, โหลดโมเดล, deploy หรือส่ง LINE ในชุดงานนี้

## ประวัติ

v0.2.0: แยก PRP ออกจาก Zuri-owned design.

v0.3.0: Python-first/reuse-first revision ของ v0.2.0; คง original package และ Coding-Standards เดิม ไม่แก้ย้อนหลัง ดู CHANGELOG และ QA report สำหรับรายละเอียด
