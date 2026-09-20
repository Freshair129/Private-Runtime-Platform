# prp-control — PRP control plane

Python control plane ของ PRP ตาม [SDD-PRP-REPO §6](../../docs/SDD-PRP-REPO.md) และ ADR-PRP-009/011 หนึ่ง codebase สาม process: `prp-api` (ASGI), `prp-dispatcher` (outbox claim → send), `prp-observer` (critical observer)

**สถานะ M3 (WP25 baseline): skeleton ที่ fail closed** มี `platform/`, `core/*` (domain types + ports), `api/` ที่ผูก route ครบ 14 operations ของ `contracts/openapi/prp-client.yaml` และ entrypoint ทั้งสาม แต่ **ยังไม่มี adapter** ทุก request ที่ผ่าน auth header ได้ตอบ `503 STATE_STORE_UNAVAILABLE` และ dispatcher/observer ปฏิเสธการ start จนกว่า M4 จะเพิ่ม adapters ตาม disposition ของ WP24 ไม่มี acceptance test ใดเปลี่ยนจาก NOT_RUN

## คำสั่ง (Coding-Standards §10)

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
uv run --locked mypy --strict src/prp
```

```sh
uv run --locked pytest tests/unit tests/contracts
```

```sh
uv run --locked lint-imports
```

`lint-imports` บังคับกติกา import ของ SDD §6.3: `core`/`platform` ไม่ import framework หรือ vendor SDK; `api` ไม่ import `adapters`; ทุก package ห้าม import torch/CUDA/engine (NFR-021) test `tests/contracts/test_no_ml_import.py` ตรวจซ้ำที่ runtime และตรวจว่า `uv.lock` ไม่มี ML package

## Layout

| Package | บทบาท | import ได้จาก |
|---|---|---|
| `prp.platform` | shared kernel: ids, UTC clock, typed errors + envelope, redacting JSON logger | stdlib |
| `prp.core.access` | Identity & Policy: Organization, Principal, AccessKeyGrant, AuthContext; `KeyVerifier` port (verifier-only, FR-005) | platform |
| `prp.core.fleet` | Registry & Qualification: Node, ModelProfile, RuntimeDeployment, QualificationReceipt; eligibility rule | platform |
| `prp.core.scheduling` | Router (select only) + Admission port; QuotaReservation / ModelResidency / InvocationLease เป็นคนละ object (ARCH §5) | platform, observability.model |
| `prp.core.execution` | Invocation, Attempt, Job, DispatchOutbox; settlement fence และ state rules (ADR-005) | platform, scheduling |
| `prp.core.content` | Artifact, ArtifactGrant, ErasureTombstone; read/grant rules (API-PRP §6) | platform, access.model |
| `prp.core.observability` | Observation, AuditEvent, UsageReceipt; sink ports | platform |
| `prp.adapters` | port implementations (ว่างใน M3; M4 เติมตาม fit-gap) | core ports, platform, vendor SDK |
| `prp.api` | FastAPI app, request id, error envelope, auth facade, routes ตาม contract | core, platform |
| `prp.entrypoints` | composition root และ process mains | ทุกอย่าง |

Python 3.12 pinned ใน `.python-version`; dependencies lock ใน `uv.lock` (แยกจาก `workers/voice`) ห้าม `pip install -U` ตอน start
