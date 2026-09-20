# prp-voice — PRP speech worker

Python worker สำหรับ ASR/TTS ใน environment แยกจาก control plane ตาม [SDD-PRP-REPO §7](../../docs/SDD-PRP-REPO.md) และ ADR-PRP-011 implement contract `contracts/openapi/prp-worker.yaml` เท่านั้น ไม่มี business credential, ไม่มี Brain/cloud config, ไม่มี client-key database

**สถานะ M3: skeleton ที่ fail closed** มี contract models, lifecycle state machine (epoch, readiness) และ server ที่ผูก route ครบ 5 operations แต่ **ยังไม่มี engine** describe/invoke ตอบ `503 RUNTIME_UNAVAILABLE`, readiness ตอบ `NOT_READY`, cancel ตอบ `UNSUPPORTED`, execution evidence ตอบ `501 UNSUPPORTED` ค่าเหล่านี้คือคำตอบที่ซื่อตรงเมื่อไม่มี engine ไม่ใช่ placeholder ที่แต่งว่า READY

Python 3.12 เป็นค่าตั้งต้นของ skeleton; รุ่นจริงและ ML dependencies (faster-whisper / approved TTS) จะ pin ที่ M4 ตาม engine/CUDA compatibility ที่ WP25 เลือก (คำตัดสิน owner 2026-09-20) lock แยกจาก `apps/control-api`

## คำสั่ง

```sh
uv sync --locked --group dev
```

```sh
uv run --locked ruff check .
```

```sh
uv run --locked ruff format --check .
```

```sh
uv run --locked mypy --strict src/prp_voice
```

```sh
uv run --locked pytest tests/unit tests/contracts
```

```sh
uv run --locked lint-imports
```

`tests/hardware/` สำหรับ physical GPU / voice quality tests รันเฉพาะ self-hosted runner ไม่รันใน cloud CI (Coding-Standards §10)

## Layout

| Package | บทบาท |
|---|---|
| `prp_voice.contract` | Pydantic models ของ worker contract (`extra="forbid"`) |
| `prp_voice.engines` | ports `AsrEngine` / `TtsEngine`; ที่เดียวที่จะ import ML ได้ (M4) |
| `prp_voice.lifecycle` | identity, profile epoch, readiness gate, drain (ARCH §11: binding runtime UID + physical resource + profile + epoch) |
| `prp_voice.server` | FastAPI app + service-credential check + main |

Service credential: worker ตรวจ bearer ของ control plane ด้วย constant-time compare กับค่าจาก environment variable `PRP_VOICE_SERVICE_TOKEN` (ชื่อเท่านั้นใน source) หากไม่ตั้งค่า worker ปฏิเสธทุก request ด้วย 503 แหล่ง credential ถาวร (secret store reference) freeze ที่ WP03
