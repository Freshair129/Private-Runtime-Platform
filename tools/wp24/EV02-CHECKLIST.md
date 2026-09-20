# EV02 Checklist — Real A/B registration

เอกสารนี้เป็น checklist ปฏิบัติงานสำหรับ operator ที่รัน `docs/WP24-EXPERIMENT-PROCEDURE.md` หัวข้อ EV02 (gate `PRP-FR-010`..`PRP-FR-015`) จริง โดยจับคู่ขั้นตอนที่เอกสารกำหนดไว้ (ขั้นตอน 1–4) เข้ากับสคริปต์ใน `tools/wp24/` เอกสารนี้**ไม่ใช่** run record และไม่คำนวณ verdict — สคริปต์ทุกตัวผลิตแค่ `measurements` / `observations` / `artifacts` ให้ reviewer ตัดสิน `PASS` / `FAIL` / `BLOCKED` เองตามเกณฑ์ใน procedure §5

ก่อนเริ่ม อ่าน `tools/wp24/README.md` (ข้อจำกัด, ชื่อ env var, endpoint ที่ใช้) และเตรียม `record_id` (`WP24-<YYYY-MM-DD>-run<n>`) ตาม procedure §7

## Reset ก่อนเริ่ม candidate ใหม่ (procedure §3 ข้อ 1)

ก่อนเริ่ม EV02 ของ candidate B ต้องรัน A ให้จบทุก EV ก่อน แล้ว reset host:

1. Stop services / container ของ candidate A บนทั้งสอง GPU host
2. ลบ container หรือ venv ของ candidate A (weights cache **อนุญาตให้คงไว้ได้** แต่ต้องบันทึกว่าคง)
3. ยืนยันว่า `nvidia-smi` ไม่มี process ค้าง: รัน `tools/wp24/ev02_gpu_binding.py --host-id <A|B>` บนแต่ละ GPU host หลัง stop แล้วตรวจว่า `matched_processes` ว่างเปล่า (ใช้ `--process-pattern` ให้ตรงกับ process ของ candidate ที่เพิ่ง stop เช่น `xinference`)
4. บันทึกผลข้อ 1–3 ลง `candidates[].reset_between_candidates.{performed, nvidia_smi_clean, notes}` ของ run record — เป็นคนละ field จาก `experiments.EV02.per_candidate` ห้ามปนกัน

## ขั้นตอน 1 — Launch LLM runtime บน A และ B (manual)

Launch runtime ของ candidate เอง (A: Xinference supervisor + workers [SRC-09]; B: vLLM service ต่อเครื่อง [SRC-01]) ด้วย `shared_revision` เดียวกันตามที่ owner ระบุใน §2 ของ procedure ขั้นตอนนี้ไม่มีสคริปต์ใน `tools/wp24/` ทำแทน — เป็นคำสั่ง launch ของ candidate เอง log คำสั่งและ stdout/stderr ไว้เป็น artifact ตาม procedure §3 ข้อ 3

หลัง launch แล้ว รัน `tools/wp24/host_inventory.py --host-id <A|B>` บนแต่ละ GPU host เพื่อบันทึก driver / CUDA / GPU UUID ปัจจุบัน — ผลไปที่ `environment.gpu_hosts[]` ของ run record (ไม่ใช่ `experiments.EV02` โดยตรง แต่เป็นหลักฐานประกอบการ join GPU UUID ในขั้นตอน 2)

## ขั้นตอน 2 — ดึงสิ่งที่ candidate รายงาน

| สคริปต์ | รันที่ไหน | ดึงอะไร |
|---|---|---|
| `ev02_probe.py --candidate <A\|B> --base-url <URL> --host-id <A\|B>` | control machine | model ID / revision, ตัวระบุที่คล้าย restart epoch, worker/GPU identifier ที่ API เปิดเผย (ถ้ามี) |
| `ev02_gpu_binding.py --host-id <A\|B>` | บน GPU host ขณะ runtime ทำงานอยู่ | join PID ของ process runtime กับ GPU UUID จริงจาก `nvidia-smi` |

รัน `ev02_probe.py` ซ้ำตามจำนวนที่ต้องการเห็น pattern แล้วบันทึกจำนวนครั้งลง `sample_count` ของ record ด้วยตนเอง (สคริปต์ไม่คำนวณให้) ถ้า response ของ candidate ไม่มี field ที่คล้าย GPU UUID เลย สคริปต์จะเติม observation ให้อัตโนมัติว่า "no probed endpoint's response exposed a physical GPU UUID mapping" — เป็น finding ของ EV02 ขั้นตอน 2 เอง ไม่ใช่ error ของเครื่องมือ ให้ operator ใช้ `ev02_gpu_binding.py` ควบคู่เพื่อ join เองแล้วลง `disposition_hint: ADAPT`

**Restart identity (บันทึกไว้เพื่อ EV02 ขั้นตอน 2 และเชื่อมกับ EV06):** รัน `ev02_probe.py` ก่อน restart runtime หนึ่งครั้ง (`--out .../before`), restart runtime ตามวิธีของ candidate ด้วยมือ, แล้วรัน `ev02_probe.py` อีกครั้งด้วย argument เดิม (`--out .../after`) จากนั้นรัน `ev02_restart_identity.py --before <ไฟล์แรก> --after <ไฟล์ที่สอง>` เพื่อดู diff ของ identifier ทั้งหมด

## ขั้นตอน 3 — Negative test (ต้องสังเกตด้วยมือ)

ขั้นตอนนี้เป็นการสังเกตพฤติกรรมของ candidate โดยตรง **ไม่มีสคริปต์ใดตัดสินผลแทน operator** — สคริปต์ใช้เพียงจับภาพ listing ก่อน/หลังให้ operator เทียบเอง:

1. **Alias เดียวกัน profile ต่างกันบน B**: launch model alias เดิมด้วย profile ที่ต่างกันบน candidate B ด้วยมือ แล้วรัน `ev02_probe.py --candidate B ...` อีกครั้ง เทียบ `results[].variants.*.identifiers` และ `body_sample` ของ endpoint listing (`list_models` / `list_model_registrations_llm`) กับก่อนหน้า — operator เป็นผู้สรุปด้วยสายตาว่า candidate แยกให้เห็นเป็นสอง entry หรือรวมเป็นตัวเดียว แล้วเขียนผลสรุปนั้นเป็นประโยคลง `experiments.EV02.per_candidate.B.observations` เอง (ไฟล์ JSON ของสคริปต์เป็นแค่หลักฐานอ้างอิง ไม่ใช่ข้อสรุป)
2. **สอง origin ชี้ runtime เดียวกัน**: ตั้ง origin สองชื่อให้ชี้ runtime เดียวกันด้วยมือ แล้วรัน `ev02_probe.py` ซ้ำอีกครั้งต่อ origin ทั้งสอง เทียบว่า candidate นับเป็นสอง capacity หรือหนึ่ง — เขียนผลสรุปด้วยมือลง observations เช่นเดียวกับข้อ 1

เก็บไฟล์ output ของ `ev02_probe.py` ทั้งก่อนและหลัง negative test แต่ละกรณีไว้เป็น artifact แยกกัน (ชื่อไฟล์มี timestamp ต่างกันอยู่แล้ว)

## ขั้นตอน 4 — ตรวจว่าทุก endpoint ต้องมี credential

`ev02_probe.py` ทำขั้นตอนนี้ให้โดยอัตโนมัติในทุกครั้งที่รัน: ยิงแต่ละ endpoint สองครั้ง (ไม่มี credential / มี credential จาก env var ที่ `--token-env` ระบุ) แล้วบันทึก status code และว่ามี header `WWW-Authenticate` (หรือเทียบเท่า) หรือไม่ ถ้า endpoint ใดตอบสำเร็จ (`2xx`) โดยไม่มี credential เลย หรือตอบ `401`/`403` โดยไม่มี `WWW-Authenticate` ให้ดูใน `observations` ของไฟล์ output — สคริปต์เติมข้อความเตือนให้อัตโนมัติ นำรายชื่อ endpoint ที่ไม่มี auth ไปลง `experiments.EV02.per_candidate.<X>.observations` และแถว fit-gap ที่เกี่ยวกับ SRC-02 (B) / SRC-10 (A) ตาม procedure §3 ข้อ 7 (บันทึกทั้งสองที่ ไม่ใช่ที่เดียว)

## จะ copy ไฟล์ไปไหนและ field ไหนใน record ใช้ไฟล์ไหน

คัดลอกไฟล์ output ทุกไฟล์ที่ `tools/wp24/*.py` เขียน (ค่าเริ่มต้นอยู่ที่ `--out`) ไปที่:

```
docs/evidence/wp24/<record_id>/<candidate>/EV02/
```

โดย `<candidate>` คือ `A` หรือ `B` (host_inventory ของ control host ไม่ใช่ EV02 — เก็บไว้ที่ `docs/evidence/wp24/<record_id>/control/EV01/` ตาม EV01 แทน)

| ไฟล์ output | ไปที่ field ของ `experiments.EV02.per_candidate.<X>` |
|---|---|
| `ev02_probe_<X>_*.json` → `measurements` | ต่อท้าย (append) เข้า `.measurements` |
| `ev02_probe_<X>_*.json` → `observations` | ต่อท้ายเข้า `.observations` |
| `ev02_probe_<X>_*.json` → `artifacts` (ชื่อไฟล์ตัวเอง) | ต่อท้ายเข้า `.artifacts` |
| `ev02_gpu_binding_<X>_*.json` → `measurements` / `observations` / `artifacts` | ต่อท้ายเข้า field เดียวกัน |
| `ev02_restart_identity_<X>_*.json` → `measurements` / `observations` / `artifacts` | ต่อท้ายเข้า field เดียวกัน (เกี่ยวโยงกับ EV06 ด้วยแต่บันทึกซ้ำที่ EV02 ตาม §3 ข้อ 7) |
| `host_inventory_<X>_*.json` | ไม่ลง `experiments.EV02` โดยตรง — ใช้กรอก `environment.gpu_hosts[]` (`gpu_model`, `gpu_uuid`, `driver`, `cuda`, `os`, `kernel`, `container_runtime`) |

ทุกไฟล์มี `source_observations: []` เสมอ — เป็นช่องว่างโดยตั้งใจ operator ต้องกรอกเอง (เช่น finding ที่อ้าง SRC-01/SRC-02/SRC-09/SRC-10 จาก `docs/STACK-EVALUATION-PRP.md` §4) ไม่ใช่สิ่งที่สคริปต์วัดจริง

`sample_count`, `cold_or_warm`, `started_at`, `finished_at`, `commands_log`, `disposition_hint`, `gate_verdicts` เป็น field ที่ operator กรอกเองจาก timestamp/`command_line` ที่อยู่ในแต่ละไฟล์ output — สคริปต์ไม่กรอกให้เพราะเป็นการตัดสินใจของ reviewer ตาม procedure §3 ข้อ 4

## LiteLLM sub-spike (EV03/EV04)

Sub-spike ของ LiteLLM (ตาม procedure §5 EV04 "LiteLLM sub-spike" และ EV03 ข้อ 2–4 ที่รันร่วมกันภายใน candidate B, time box ไม่เกิน 1 วันทำงาน) เตรียมแยกต่างหากที่ `tools/wp24/litellm_subspike/` โดยงานอื่น ไม่ได้อยู่ในขอบเขตของ checklist นี้และไม่ได้สร้างไว้ที่นี่
