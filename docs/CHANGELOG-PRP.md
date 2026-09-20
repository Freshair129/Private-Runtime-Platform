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