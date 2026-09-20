# WP24 LiteLLM sub-spike — EV04 key semantics + EV03 retry-off (candidate B)

**สถานะ:** เตรียมชุดเครื่องมือเท่านั้น (C-2 / H2) — ยังไม่มีการ deploy หรือรันจริงในการเตรียมนี้ ไฟล์ใน
`tools/wp24/litellm_subspike/` ทั้งหมดเป็น TEMPLATE / NOT_QUALIFIED ต้องผ่านการรันจริงก่อนจึงจะมีผล

## Scope — ทำไมมีแค่ EV04 + EV03 ของ LiteLLM

Owner ตัดสินใจ 2026-09-20 ([docs/WP24-EXPERIMENT-PROCEDURE.md](../../../docs/WP24-EXPERIMENT-PROCEDURE.md)
หมวด 5 EV04 บล็อก "LiteLLM sub-spike";
[docs/registry/wp24-run-record-template.json](../../../docs/registry/wp24-run-record-template.json)
`scope_decisions.litellm`): LiteLLM อยู่ใน WP24 **เฉพาะ**ในฐานะ key / proxy layer ของ candidate B
([STACK-EVALUATION-PRP.md](../../../docs/STACK-EVALUATION-PRP.md) หมวด 2;
[SOURCES-PRP.md](../../../docs/SOURCES-PRP.md) SRC-03) และรันเฉพาะ:

- **EV04** (identity / key semantics — gate PRP-FR-003..009) ข้อ 1–3 เท่านั้น
- **EV03** (target binding — gate PRP-NFR-023) ข้อ 2–4 เท่านั้น โดยปิด retry / fallback / smart routing
  ให้หมดก่อน (`litellm_config.template.yaml`)

ภายใน **time box รวมไม่เกิน 1 วันทำงาน** หมดเวลาแล้วส่วนที่ไม่เสร็จลง `BLOCKED` **ไม่ต่อเวลา** เครื่องมือในโฟลเดอร์
นี้ไม่คำนวณ verdict ใด ๆ — PASS / FAIL / BLOCKED ทุกค่าเป็นการตัดสินของผู้ทดลอง/ผู้ตรวจตามเกณฑ์ใน
WP24-EXPERIMENT-PROCEDURE.md เท่านั้น

**ข้อความที่ต้องย้ำเสมอ (NFR-023):** routing ของ LiteLLM **ไม่แทน** PRP Router ไม่ว่ากรณีใด แม้ candidate B จะ
ผ่านทุกข้อของ sub-spike นี้ LiteLLM ก็ยังเป็นแค่ key/proxy layer ที่ PRP เรียกใช้ ไม่ใช่ตัวตัดสินใจ routing แทน
Scheduling context ของ PRP — และตาม
[WP24-EXPERIMENT-PROCEDURE.md](../../../docs/WP24-EXPERIMENT-PROCEDURE.md) หมวด 5 EV04: "ไม่รัน LiteLLM ใน
EV05–EV08 และไม่ใช้ routing ของมันแทน PRP Router ในทุกกรณี"

## สามคำถามที่ sub-spike ต้องตอบ

ตาม WP24-EXPERIMENT-PROCEDURE.md หมวด 5 EV04 บล็อก "LiteLLM sub-spike":

1. **Key เก็บเป็น hash และอ่านกลับไม่ได้จากทุกช่องทางหรือไม่** — `ev04_keys.py` ตรวจ `/key/info` และ `/key/list`;
   `ev04_readback_checklist.md` ตรวจ DB table, proxy log, config dump และ Admin UI ที่ script เข้าไม่ถึง
2. **Revoke มีผลภายในเวลาเท่าใด** — `ev04_keys.py` วัดจริงด้วยการ poll `GET /v1/models` ด้วย key ที่ revoke แล้ว
   ทุก 200ms นานสุด 30s
3. **Retry / fallback / smart routing ปิดได้ครบด้วย config หรือไม่** — `litellm_config.template.yaml` ตั้งค่า
   disable ทุกตัวที่เอกสารมีสวิตช์ให้ (พร้อม citation ต่อรายการ) แล้ว `ev03_retry_probe.py` ยืนยันด้วยการยิง
   request จริงและอ่าน header ที่เอกสารบอกว่าระบุ deployment ที่ตอบ

**ผ่านครบทั้งสามข้อ → disposition `CONFIGURE` พร้อม operator cost ที่วัดได้ (ดูหัวข้อ "Operator cost" ด้านล่าง);
ไม่ผ่านข้อใดข้อหนึ่ง → disposition `BUILD-GAP` ที่ PRP เป็น verifier และ router เองพร้อมหลักฐาน** (เกณฑ์เดียวกับใน
WP24-EXPERIMENT-PROCEDURE.md)

## แผนหนึ่งวันทำงาน (ลำดับ)

1. **Bring up proxy** — เติมค่าใน `docker-compose.litellm.template.yml` (image tag ที่ verify แล้ว, digest,
   `LITELLM_MASTER_KEY`, `DATABASE_URL`, `VLLM_HOST_A_BASE_URL`, `VLLM_HOST_B_BASE_URL` และ API key ถ้ามี) และ
   `<served-model-name>` ทั้งสองจุดใน `litellm_config.template.yaml` แล้ว `docker compose -f
   docker-compose.litellm.template.yml config` เพื่อ validate ก่อนรันจริง (ดูหัวข้อ "การ validate YAML" ด้านล่าง)
   จากนั้น `docker compose -f docker-compose.litellm.template.yml up -d` แล้วรอ healthcheck ทั้งสอง service
2. **EV04 ข้อ 1–3** — `PYTHONUTF8=1 python ev04_keys.py --base-url http://127.0.0.1:4000 --master-key-env
   LITELLM_MASTER_KEY --out <artifact-dir>` ตามด้วย `ev04_readback_checklist.md` ทีละขั้นตอนด้วยมือ
3. **EV03 ข้อ 2–4 โดยปิด retry ไว้แล้ว** — สร้าง virtual key แยกสำหรับ EV03 (เช่นด้วย curl ตาม
   `ev04_readback_checklist.md` ขั้นตอน 1 แต่ตั้ง `key_alias` เป็น `wp24-litellm-subspike-ev03`) เก็บไว้ใน env
   var เช่น `WP24_LITELLM_VIRTUAL_KEY` แล้ว `PYTHONUTF8=1 python ev03_retry_probe.py --base-url
   http://127.0.0.1:4000 --key-env WP24_LITELLM_VIRTUAL_KEY --alias wp24-litellm-subspike-host-a --count 5
   --mode normal --expect-deployment wp24-host-a --out <artifact-dir>`
4. **สังเกต fallback ตอน host A down** (EV03 ข้อ 2) — ดูหัวข้อ "`--mode stalled|down`" ด้านล่างสำหรับขั้นตอนที่
   operator ทำด้วยมือ แล้วรัน `ev03_retry_probe.py` ซ้ำด้วย `--mode down` (หรือ `--mode stalled`) เพื่อบันทึกว่า
   request ถูกปฏิเสธตรง ๆ (ตามที่ retry/fallback ถูกปิด) หรือมีการ reroute ไป host B โดย PRP ไม่รู้
5. **Tear down** — `docker compose -f docker-compose.litellm.template.yml down -v` ลบ volume
   `litellm_subspike_pgdata` ด้วย (ห้ามค้าง virtual key หรือข้อมูล spend log ของการทดลองไว้)

## `--mode stalled|down` (คู่มือขั้นตอนที่ operator ทำด้วยมือ)

`ev03_retry_probe.py --mode` **ไม่ throttle หรือหยุด host A ให้เอง** — เป็นแค่ label ที่ script แนบไว้ในผลลัพธ์ว่า
ระหว่างรันชุดนี้ host A อยู่ในสภาพใด ขั้นตอนจริงที่ operator ต้องทำเองบน host A (นอก proxy):

- **`stalled`**: throttle การตอบของ vLLM บน host A ให้ช้าลงมาก (เช่น จำกัด CPU/GPU ของ process หรือใส่ iptables
  rule หน่วง traffic ที่ port ของ vLLM) แล้วรัน `ev03_retry_probe.py --mode stalled` ระหว่างที่ยังหน่วงอยู่
- **`down`**: หยุด process ของ vLLM บน host A จริง ๆ (`kill` หรือหยุด service) แล้วรัน `ev03_retry_probe.py --mode
  down` ระหว่างที่ยังหยุดอยู่ รอผลว่า request ที่เรียก alias `wp24-litellm-subspike-host-a` ได้ error กลับมาตรง ๆ
  (retry/fallback ปิดแล้วตาม `litellm_config.template.yaml`) หรือมี header `x-litellm-model-id` ที่ชี้ไป host B
  ปรากฏขึ้นทั้งที่เรียก alias ของ host A (แปลว่ามีการ reroute ที่ config ปิดไม่ได้ — บันทึกเป็น known gap)
- อย่าลืมคืนสภาพ host A (เลิก throttle / เริ่ม process ใหม่) ก่อนไปขั้นตอนถัดไป

## สิ่งที่ต้อง copy ไปที่ไหน

| จากไฟล์ | ไปที่ |
|---|---|
| `ev04_keys.py` output (`ev04_keys.result.json` และ artifact `.redacted.json` ทั้งหมดใน `--out`) | `docs/evidence/wp24/<record_id>/B/EV04/` |
| ผลของแต่ละขั้นตอนใน `ev04_readback_checklist.md` (เป็นข้อความบรรยาย ไม่ใช่ค่า key) | `docs/evidence/wp24/<record_id>/B/EV04/` และ
  `experiments.EV04.per_candidate.B.observations` ของ run record |
| `ev03_retry_probe.py` output (`ev03_retry_probe.result.json`, `ev03_retry_probe.requests.json`) ทุกรอบ
  (`normal`, `stalled`/`down`) | `docs/evidence/wp24/<record_id>/B/EV03/` |
| `docker compose config` output ที่ validate แล้ว, `docker inspect` digest ของ image ที่ใช้จริง | `docs/evidence/wp24/<record_id>/B/EV04/` (หรือไฟล์ระดับ candidate) และ
  `candidates[B].version_manifest.images` ของ run record |

Run record คือ `docs/evidence/wp24/<record_id>.json` (สำเนาโครงจาก
[`docs/registry/wp24-run-record-template.json`](../../../docs/registry/wp24-run-record-template.json)) —
ดูตัวอย่างรูปแบบจริงที่ `docs/evidence/wp24/WP24-2026-09-20-run1.json` (EV01 run) `record_id` รูปแบบ
`WP24-<YYYY-MM-DD>-run<n>`

## Operator cost ที่ต้องบันทึก (STACK-EVALUATION-PRP.md หมวด 7)

บันทึกเฉพาะที่วัดหรือนับได้จริงหลังรัน ลงใน
`candidates[B].operator_cost_measurements` ของ run record:

- **Services ที่เพิ่ม**: LiteLLM proxy container (1), PostgreSQL container (1) — `services_to_operate`
- **Datastores ที่เพิ่ม**: PostgreSQL database `litellm` (virtual keys, spend logs) — `datastores_to_operate`
  (ดู [ev04_readback_checklist.md](ev04_readback_checklist.md) และ
  <https://docs.litellm.ai/docs/proxy/db_info> สำหรับตารางที่ database เก็บ)
- **Config lines ที่ต้องเขียน**: จำนวนบรรทัดจริงใน `litellm_config.template.yaml` ที่ operator ต้องแก้ให้เป็นค่า
  จริง (ไม่รวม comment) — นับตอนรัน ไม่เดา
- **Upgrade steps ที่ลองจริง**: เปลี่ยน image tag เป็นเวอร์ชันถัดไปแล้วรัน `docker compose up -d` ซ้ำ บันทึกว่า
  migration ของ DB (Prisma) รันเองหรือต้องสั่งแยก
- **Rollback steps ที่ลองจริง**: กลับไป tag เดิม บันทึกว่า schema ของ DB ที่ migrate ไปแล้วใช้กับ image เก่าได้
  หรือไม่
- **Licenses**: LiteLLM proxy เป็น MIT ผ่าน pip/Docker image สาธารณะ — ยืนยัน license จริงของ tag ที่ใช้ตอนรัน
  ไม่ใช่ตอนเตรียมเอกสารนี้
- **ทักษะที่ต้องมี**: Postgres operations (migration, backup), Docker Compose, การอ่าน LiteLLM router config

ห้ามสรุปเป็นเปอร์เซ็นต์ประหยัดเวลาหรือค่าที่ไม่ได้วัดจริง (STACK-EVALUATION-PRP.md หมวด 7)

## การ validate YAML (แทนการ parse ด้วย PyYAML)

Repository นี้ไม่มี PyYAML ใน stdlib ดังนั้น `tests/test_litellm_subspike.py` ตรวจได้แค่ว่าทั้งสองไฟล์ YAML อ่าน
เป็น text ได้และมี key/anchor ที่คาดไว้ปรากฏอยู่ (string match) **ไม่ใช่การ validate schema จริง** การ validate
จริงก่อนรันคือ:

```bash
docker compose -f docker-compose.litellm.template.yml config
```

ซึ่งจะ parse ทั้งสองไฟล์ (compose เองและ `litellm_config.template.yaml` ที่ mount เข้าไป จะถูก LiteLLM เอง parse
ตอน container start) รันคำสั่งนี้เสมอก่อนใช้งานจริง

## No secrets

`docker-compose.litellm.template.yml`, `litellm_config.template.yaml` และ scripts ทั้งสองมีเฉพาะ**ชื่อ**
environment variable (`LITELLM_MASTER_KEY`, `DATABASE_URL`, `VLLM_HOST_A_BASE_URL`, ฯลฯ) พร้อม placeholder
`<set-at-run-time>` **ห้าม commit หรือ paste ค่าจริงลงไฟล์ใดในโฟลเดอร์นี้ หรือใน run record** `ev04_keys.py` และ
`ev03_retry_probe.py` ไม่ print และไม่เก็บ master key / virtual key ใด ๆ ลงดิสก์ — output มีเฉพาะ
`sha256:<12 hex แรก>` fingerprint ที่คำนวณในหน่วยความจำ (ดู `_common.py`)

## Doc facts ที่ตรวจสอบไม่ได้จาก official docs (ต้อง observe ตอนรันจริง)

- **`token` field ใน `/key/info` และ `/key/list` เป็น hash หรือ plaintext** — เอกสารขัดแย้งกันเอง (ดูรายละเอียดใน
  header comment ของ `ev04_keys.py` และ `ev04_readback_checklist.md` ข้อ 2)
- **Hedging / speculative parallel requests** — ไม่มีสวิตช์ปิดที่มีเอกสารรองรับ (ค้นแล้วไม่พบใน
  <https://docs.litellm.ai/docs/routing>, <https://docs.litellm.ai/docs/proxy/config_settings>,
  <https://docs.litellm.ai/docs/proxy/reliability> ณ 2026-09-20)
- **`key_name` masking** ใน response ของ management endpoint ต่าง ๆ — ไม่มีข้อความยืนยันรูปแบบ mask ที่ชัดเจนใน
  หน้าเอกสารที่ตรวจ
