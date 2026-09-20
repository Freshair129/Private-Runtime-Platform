# docs/evidence — acceptance receipts

โฟลเดอร์นี้เก็บ **receipt ของการรันจริง** หนึ่งไฟล์ต่อหนึ่งการรัน ตาม template [`../registry/evidence-template.json`](../registry/evidence-template.json) ว่างจนกว่าจะมี runtime test บน environment ที่ qualified

## กติกา (SDD-PRP-REPO §9 ข้อ 4, ADR-PRP-012 action 5)

- สถานะของ acceptance case ใน [`TEST-PRP.md`](../TEST-PRP.md) เปลี่ยนจาก `NOT_RUN` ได้ **เฉพาะ** เมื่อมีทั้ง (1) test ที่ collect ได้ใน [`registry/code-trace.json`](../registry/code-trace.json) ผ่าน marker `@pytest.mark.at("PRP-AT-nnn")` และ (2) receipt ในโฟลเดอร์นี้ที่ `test_id` ตรงกันและ `status` เท่ากัน `tools/docs/validate_docs.py` ปฏิเสธถ้าขาดอย่างใดอย่างหนึ่ง
- receipt ที่ "complete" ต้องมี `evidence_id`, `commit`, `reviewer` ไม่เป็น null และ `status` เป็น `PASS` / `FAIL` / `BLOCKED` เท่านั้น receipt ที่ `status: NOT_RUN` ไม่ใช่หลักฐานและถูกปฏิเสธ
- **PASS จาก mock ไม่นับ**: ถ้า `proof` ของ requirement ไม่ได้อยู่ในชุด `contract`, `packaging`, `portability`, `design evidence`, `operations review`, `load mock` ล้วน test ที่ collect ต้องมาจาก tier `integration` หรือ `hardware` ไม่ใช่ `unit`/`contracts` เท่านั้น
- receipt ต้องระบุ environment จริง: `commit`, `image_digest` หรือ lock digest, `model_profile_hash`, `hardware` และ `result_files` ที่ชี้ไป artifact ที่เก็บไว้ ไม่ใส่ตัวเลข benchmark ที่ไม่ได้วัด

## ชื่อไฟล์

`PRP-AT-nnn.<evidence_id>.json` เช่น `PRP-AT-089.2026-10-01-hostA-run1.json` หนึ่ง AT มีหลาย receipt ได้ (รันซ้ำ, หลาย host); validator ใช้ receipt ที่ `status` ตรงกับ TEST-PRP

## ขั้นตอนเปลี่ยนสถานะ

1. รัน test บน environment ที่ qualified และเก็บ result files
2. เขียน receipt ตาม template ลงโฟลเดอร์นี้
3. แก้ `**Status:**` และ `**Evidence:**` ของ AT นั้นใน TEST-PRP.md ให้ชี้ `evidence_id`
4. รัน `python tools/trace/collect_trace.py` แล้ว `python tools/docs/validate_docs.py` ต้อง `errors: []`
5. commit ทั้งสามอย่างใน PR เดียว (Git-Standards: evidence required)

## WP24 run records (`wp24/`)

`wp24/<record_id>.json` และโฟลเดอร์ artifact `wp24/<record_id>/<candidate>/<EVnn>/` เก็บผลของ WP24 fit-gap และ A/B spikes ตาม [`../WP24-EXPERIMENT-PROCEDURE.md`](../WP24-EXPERIMENT-PROCEDURE.md) และ template [`../registry/wp24-run-record-template.json`](../registry/wp24-run-record-template.json) ไฟล์เหล่านี้เป็นหลักฐานระดับ candidate ไม่ใช่ acceptance receipt validator ไม่นับเป็น receipt และไม่เปลี่ยนสถานะ AT ใด ห้ามใส่ secret, เสียง / ข้อความลูกค้า หรือ model weights
