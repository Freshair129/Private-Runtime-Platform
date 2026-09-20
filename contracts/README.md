# contracts/ — PRP protocol source of truth

Protocol ของ PRP ที่ code ทุกส่วน (control plane, workers, clients, docs) ต้องอ้างถึง ไม่มีไฟล์ใดในโฟลเดอร์นี้พิสูจน์ว่ามี server implement แล้ว (API-PRP §1) กติกา authority ตาม [SDD-PRP-REPO §5](../docs/SDD-PRP-REPO.md)

## ไฟล์

| ไฟล์ | บทบาท | สถานะ | Freeze gate |
|---|---|---|---|
| `openapi/prp-client.yaml` | public client contract: `/v1` compatible chat/audio subset + `/prp/v1` capabilities, artifacts, async jobs (API-PRP §3–§6) | proposed, `info.version` 0.3.0; 12 paths / 14 operations ไม่เปลี่ยนจาก v0.2.0; components 30 หลังตั้งชื่อ inline schema ตาม ADR-PRP-013 (wire format เท่าเดิม) | breaking change ต้องมี route/version ใหม่ (API-PRP §10) |
| `openapi/prp-worker.yaml` | internal worker adapter contract: describe / readiness / invoke / cancel / execution evidence (API-PRP §7) | **DRAFT** 0.4.0-draft | WP03 |
| `openapi/prp-management.yaml` | private management inventory: grants, keys, pools/nodes lifecycle, profile approval, policies, redacted exports, backup/restore (API-PRP §8) | **DRAFT** 0.4.0-draft; field schemas จะ freeze ที่ G0 | WP03 |
| `openapi/*.json` | export ของ YAML ข้างต้น สำหรับ consumer ที่ใช้ stdlib เท่านั้น เช่น `tools/docs/validate_docs.py` | **derived** ห้ามแก้ด้วยมือ | — |
| `schemas/runtime-environment-manifest.schema.json` | JSON Schema ของ runtime environment manifest (control / LLM A,B / speech) | DRAFT | WP25 |
| `examples/*.example.*` | ตัวอย่าง payload และ manifest ทุกไฟล์เป็น TEMPLATE / NOT_QUALIFIED ไม่ใช่ resource ที่ลงทะเบียนจริง | — | — |
| `examples/index.json` | map ตัวอย่าง → schema ที่ใช้ validate | — | — |

## กติกา

- **YAML คือ canonical; JSON คือ generated** แก้ `.yaml` แล้วรัน export; CI ปฏิเสธ JSON ที่ค้าง
- ทุก `$ref` เป็น local (`#/components/...`) ไม่มี cross-file reference; schema ที่ใช้ร่วม (เช่น `Error`, `Message`) คัดลอกไว้ในแต่ละไฟล์โดยตั้งใจ เพราะแต่ละ boundary มี trust และ credential ต่างกัน
- ทุก operation ต้องมี security; client key ไม่เคย authorize worker/admin routes (API-PRP §1)
- Version อยู่ใน `info.version` ไม่อยู่ในชื่อไฟล์ ไฟล์ DRAFT มี `x-prp-status: DRAFT` และ `x-prp-freeze-gate`
- Field ที่ยังไม่ freeze ให้เขียนแบบ minimal พร้อม description ระบุ gate แทนการแต่ง field เพิ่ม (DDD: no hallucination)
- Engine-specific field ต้อง namespaced และ profile-qualified ไม่ปล่อย `provider_config` เป็น dictionary เปิด (API-PRP §10)
- ทุก object schema ต้องเป็น named component ไม่เขียน inline (รวม response ระดับ path) เพราะ Python models ถูก **generate** จากไฟล์นี้ (ADR-PRP-013) และชื่อ component คือชื่อ class; ห้ามเขียน contract model ด้วยมือยกเว้น escape hatch ที่มี conformance test
- URL field ใช้ `type: string` + `pattern: '^https://'` ไม่ใช้ `format: uri` เพราะ Pydantic `AnyUrl` รับ `pattern` ไม่ได้ generator จะทิ้ง constraint แล้ว app จะหลวมกว่า contract
- ทุก operation ที่มี JSON body หรือ JSON success response ต้องผูกกับ generated model ใน route; `tests/contracts/test_openapi_conformance.py` ของแต่ละ project เทียบ `app.openapi()` กับไฟล์นี้ต่อ operation หลัง normalize

## คำสั่ง

```sh
pip install -r tools/contracts/requirements.txt
```

```sh
python tools/contracts/export_json.py --check
```

```sh
python tools/contracts/export_json.py
```

```sh
python tools/contracts/validate_examples.py
```

```sh
python tools/contracts/gen_models.py --check
```

```sh
python tools/contracts/gen_models.py
```

`gen_models.py` สร้าง Pydantic models ตาม ADR-PRP-013 ลง `apps/control-api/src/prp/contracts/{client_v1,worker_v1,management_v1}.py` และ `workers/voice/src/prp_voice/contract/generated.py` ต้อง sync ทั้งสอง project ด้วย uv ก่อน เพราะ output ถูก format ด้วย ruff ของ project นั้น

```sh
python tools/docs/validate_docs.py
```

Validator ตรวจทุก `openapi/*.json`: local refs resolve, operationId ไม่ซ้ำ, security ครบ และ inventory ของ client contract คงเดิม CI: `.github/workflows/contracts.yml`
