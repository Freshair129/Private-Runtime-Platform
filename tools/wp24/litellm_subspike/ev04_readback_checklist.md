# EV04 readback checklist (manual) — WP24 LiteLLM sub-spike, candidate B

เอกสารนี้เป็นส่วนเสริมของ `ev04_keys.py` เฉพาะ**ช่องทางที่ script อัตโนมัติเข้าไม่ถึง** `ev04_keys.py` ตรวจ `GET
/key/info` และ `GET /key/list` เท่านั้น (ดู comment ในไฟล์นั้นอ้างอิง
<https://docs.litellm.ai/docs/proxy/virtual_keys>) ส่วนใน checklist นี้คือ: ตาราง database โดยตรง, log ของ
proxy container, config dump และ Admin UI (ถ้าเปิดใช้) ทั้งหมดยังอยู่ใน scope ของ WP24-EXPERIMENT-PROCEDURE.md
หมวด 5 EV04 ข้อ 1 ("พยายามอ่านค่า key กลับผ่านทุกช่องทาง (API, UI, DB, config dump, log)")

`ev04_keys.py` **ไม่เคย** print หรือเก็บ plaintext key ของมันเอง (เก็บเฉพาะ fingerprint ในหน่วยความจำชั่วคราว)
ดังนั้น checklist นี้ให้ operator **สร้าง key ทดลองแยกต่างหากด้วยมือ** เพื่อให้มี plaintext อยู่ใน terminal ของ
ตัวเองไว้เทียบ ห้ามนำค่า plaintext นั้นไปวางในไฟล์ใด ๆ ที่จะ commit หรือใน run record เด็ดขาด (กติกา "ไม่มี secret
จริง" WP24-EXPERIMENT-PROCEDURE.md หมวด 3 ข้อ 6)

## 0. ก่อนเริ่ม

ต้องเข้าถึงได้ทั้งสี่อย่างนี้จาก host ที่รัน `docker-compose.litellm.template.yml`:

- `psql` (หรือ client Postgres อื่น) ต่อ `DATABASE_URL` เดียวกับที่ proxy ใช้
- `docker compose logs litellm` ของ container proxy
- ไฟล์ `litellm_config.template.yaml` ที่ mount เข้า container จริง (ไม่ใช่ไฟล์ในเครื่อง)
- Admin UI ของ LiteLLM (ถ้า operator เลือกเปิด) — ลิงก์ตามเอกสาร:
  <https://docs.litellm.ai/docs/proxy/virtual_keys> มีหัวข้อ "UI to Generate, Edit, Delete Keys (with SSO)"
  ชี้ไปที่ <https://docs.litellm.ai/docs/proxy/ui>

## 1. สร้าง key ทดลองด้วยมือ (แยกจาก ev04_keys.py)

```bash
curl 'http://127.0.0.1:4000/key/generate' \
  --header "Authorization: Bearer $LITELLM_MASTER_KEY" \
  --header 'Content-Type: application/json' \
  --data-raw '{"models": ["wp24-litellm-subspike-host-a"], "max_budget": 0.01, "duration": "10m", "key_alias": "wp24-litellm-subspike-ev04-manual"}'
```

(รูปแบบตาม <https://docs.litellm.ai/docs/proxy/virtual_keys#quick-start---generate-a-key>) response จะมี field
`key` เป็น plaintext — **เก็บค่านี้ไว้ในหน่วยความจำของ terminal เท่านั้น** อย่า `echo` ค่าไปไฟล์ อย่า paste ลง
editor ที่ save งานไว้ อย่าวางใน commit message หรือ PR description

## 2. ตรวจตาราง database โดยตรง

Table ที่เก็บ virtual key คือ `LiteLLM_VerificationToken` (คอลัมน์ `token` เป็น primary key) ตาม schema จริงของ
LiteLLM: <https://github.com/BerriAI/litellm/blob/main/schema.prisma> (`model LiteLLM_VerificationToken { token
String @id ... }`) และรายชื่อ table ตามหน้าที่ที่เอกสารอธิบาย: <https://docs.litellm.ai/docs/proxy/db_info>
("LiteLLM_VerificationToken | Manages Virtual Keys and their permissions...")

```bash
psql "$DATABASE_URL" -c "SELECT token, key_name, key_alias, expires FROM \"LiteLLM_VerificationToken\" WHERE key_alias = 'wp24-litellm-subspike-ev04-manual';"
```

**สิ่งที่ต้องดู:** ค่าในคอลัมน์ `token` เป็น sha256 hex (64 ตัวอักษร hex, ไม่มี prefix `sk-`) หรือเป็นค่าเดียวกับ
plaintext `key` ที่เห็นในขั้นตอน 1 เทียบด้วยตาเปล่าใน terminal เดียวกัน (อย่า copy ค่าออกไปที่อื่น) — ข้อความในเอกสาร
เองก็ไม่ตรงกันชัดเจน: หัวข้อ "Overwrite outgoing user with the key hash" บนหน้าเดียวกันบอกว่า "the value is the
key's sha256 token hash" ซึ่งบอกเป็นนัยว่า `token` คือ hash แต่ยังไม่มีข้อความยืนยันตรง ๆ ว่าคอลัมน์นี้เก็บ hash
เสมอ — ต้องดูของจริงจาก query นี้

## 3. ตรวจ log ของ proxy container

```bash
docker compose -f docker-compose.litellm.template.yml logs litellm | grep -F 'wp24-litellm-subspike-ev04-manual'
```

ดูว่าบรรทัดใดใน log มี plaintext key (เทียบกับค่าที่เห็นในขั้นตอน 1 ในใจ/ตาเปล่า ไม่ copy ไปที่ไหน) หลุดออกมาหรือไม่
เช่นใน request/response body ที่ debug logging อาจพิมพ์ออกมา

## 4. ตรวจ config dump

`litellm_config.template.yaml` ที่ mount เข้า container ไม่มี key ของ user อยู่แล้ว (เป็น model list + router
settings) — ข้อนี้ตรวจว่า LiteLLM ไม่เขียน key ที่สร้างขึ้นภายหลังกลับลงไฟล์ config หรือ dump อื่นบน container เอง
(`docker compose exec litellm cat /app/config.yaml` แล้วยืนยันว่าไม่มี key ปรากฏ)

## 5. ตรวจ Admin UI (เฉพาะถ้า operator เปิดใช้)

เปิดหน้า Keys ตาม <https://docs.litellm.ai/docs/proxy/ui> แล้วดูว่า key ที่สร้างในขั้นตอน 1 แสดงเป็น plaintext เต็ม
หรือ masked (เช่น `sk-...abcd`) บันทึกว่าเห็นแบบไหน ไม่ screenshot ค่า plaintext เต็ม

## 6. ลบ key ทดลองทันทีหลังตรวจเสร็จ

```bash
curl -X POST 'http://127.0.0.1:4000/key/delete' \
  --header "Authorization: Bearer $LITELLM_MASTER_KEY" \
  --header 'Content-Type: application/json' \
  --data-raw '{"keys": ["<the plaintext key from step 1, typed by hand, never pasted from a saved file>"]}'
```

## 7. บันทึกผลลง run record

ใส่ผลของทั้งห้าช่องทาง (DB, log, config dump, UI, และผลจาก `ev04_keys.py` เอง) เป็นข้อความบรรยายลงใน
`experiments.EV04.per_candidate.B.observations` ของ `docs/evidence/wp24/<record_id>.json`
(`registry/wp24-run-record-template.json`) — ตัวอย่างข้อความ: "DB table LiteLLM_VerificationToken.token: hash
(64 hex, ไม่ตรงกับ plaintext) — PASS ช่องทางนี้", "docker compose logs: ไม่พบ plaintext — PASS ช่องทางนี้" ไม่ใส่
ค่า key เอง ใส่เฉพาะผลลัพธ์บรรยาย

**เกณฑ์ FR-005** (WP24-EXPERIMENT-PROCEDURE.md หมวด 5 EV04): ถ้า plaintext อ่านกลับได้จากช่องทางใดช่องทางหนึ่งก็ตาม
(DB, log, config dump, UI, หรือจาก `/key/info` / `/key/list` ที่ `ev04_keys.py` ตรวจ) ให้ตั้ง
`experiments.EV04.per_candidate.B.gate_verdicts.PRP-FR-005` เป็น `FAIL` ทันที ("FR-005 `FAIL` ทันทีถ้า key อ่าน
กลับได้หลังออก") ไม่มีการเฉลี่ยหรือ "ผ่านบางช่องทาง" — ช่องทางเดียวที่รั่วก็พอให้ FAIL ถ้าทุกช่องทางไม่รั่วเลย
(รวมทั้งห้าช่องทางในไฟล์นี้และสองช่องทางใน `ev04_keys.py`) จึงบันทึก `PASS` ได้ ค่าที่ไม่ใช่ `PASS` / `FAIL` /
`BLOCKED` / `NOT_RUN` ใช้ไม่ได้ (WP24-EXPERIMENT-PROCEDURE.md หมวด 3 ข้อ 4)
