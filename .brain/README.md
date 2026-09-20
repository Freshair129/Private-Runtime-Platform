# .brain — governance working memory

โฟลเดอร์นี้ commit เข้า git ตาม Git-Standards ("RCA or Spec docs committed alongside the code")

| โฟลเดอร์ | ใช้สำหรับ | อ้างอิง |
|---|---|---|
| `rca/` | Root Cause Analysis ทุกครั้งที่แก้ bug ตั้งชื่อ `RCA-<YYYY-MM-DD>-<slug>.md` ใช้ template Symptom → Evidence → Root Cause → Escape Analysis → Prevention | AGENTS.md R6, `docs/standards/RCA-Standard.md` |
| `proposals/` | ร่าง ADR/SDD/spec ที่รออนุมัติ เมื่อได้ APPROVED ให้ย้ายเข้า `docs/` แล้วลบร่างที่นี่ | AGENTS.md R5, DDD SOP approval gate |
| `status/` | สรุปสถานะ repository ตอนปิด session ตั้งชื่อ `STATUS-<YYYY-MM-DD>.md` เป็น working memory ไม่ใช่ canonical doc (ความจริงอยู่ใน `docs/` และ CHANGELOG) | — |
