---
document_id: WP02-HARDWARE-RUNTIME-INVENTORY
title: "WP02 | Hardware & Runtime Inventory Procedure"
product: PRP - Private Runtime Platform
version: 0.1.0
status: approved
created_at: 2026-10-03
language: th-TH
source_authority: authored-proposal
decision: APPROVED_IN_CURRENT_TASK_2026-10-03
complexity: C-3
risk: HIGH
implementation_status: NOT_STARTED
runtime_verification: NOT_RUN
repository_integration: NOT_PERFORMED
---

# WP02 | Hardware & Runtime Inventory Procedure

เอกสารนี้กำหนดวิธีเก็บหลักฐานของ WP02 เพื่อใช้ประกอบ RG0 เท่านั้น ไม่ใช่การรับรอง runtime, ไม่ใช่ acceptance receipt และไม่อนุญาต DEV/PROD deployment

## 1. Parent, peer และขอบเขต

- **Parent:** [SRS-PRP](SRS-PRP.md) §2, [ROADMAP-PRP](ROADMAP-PRP.md) §3, [EXECUTION-DAG-PRP](EXECUTION-DAG-PRP.md) §§2–6
- **Peers:** [OPS-PRP](OPS-PRP.md) §§1, 3, 11, [ARCH-PRP](ARCH-PRP.md) §§4–5, 13, [runtime manifest schema](../contracts/schemas/runtime-environment-manifest.schema.json)
- **Deliverable:** inventory ของ GPU/CPU/RAM/OS/network/time-sync/storage/runtime และ model/license candidates ตาม WP02
- **Out of scope:** model activation, benchmark, runtime qualification, database migration, secret issuance, server access ที่ยังไม่ได้รับอนุญาต, DEV และ PROD

WP02 จะยังเป็น `NOT_STARTED` จนกว่าจะมีหลักฐานจริงของ host ที่อยู่ใน topology ที่เลือกครบ และมี Operations/QA review ตาม gate ที่เกี่ยวข้อง การมี planning hardware หรือ local unit tests ไม่ใช่หลักฐานปิด WP02

## 2. Minimum inventory fields

| Area | ต้องบันทึก | Boundary |
|---|---|---|
| Host identity | stable host ID (`control`, `A`, `B`), capture time, source commit | ห้ามใช้ชื่อที่เปลี่ยนได้เป็น physical identity เดียวโดยไม่มีหลักฐาน |
| Compute | CPU model/core/thread, RAM, OS/build/architecture | ค่าต้องมาจาก host จริง |
| GPU | vendor/model, GPU UUID, VRAM, driver, CUDA/UMD version, current usage | UUID/physical resource ต้องตรวจซ้ำกับ runtime binding ก่อน qualify |
| Network/storage/time | private interface/reachability, gateway or route evidence, free disk at candidate path, time-sync offset, recovery access | ไม่เก็บ credential และไม่เปิด public ingress |
| Toolchain/runtime | Python/uv, container runtime or service manager, exact runtime version/image digest | version tag อย่างเดียวไม่ใช่ qualification |
| Model/voice/licence | model revision/hash, candidate A/B runtime mapping, licence/voice-rights receipt | receipt ต้องอ้าง revision จริง; ห้าม activation ก่อน rights gate |
| Secrets | secret-store reference and owner only | ห้ามบันทึก key bytes, password, token หรือ private key |

## 3. Read-only collection procedure

1. Record the exact repository commit and the host role being measured. Run independently on every authorized host; do not infer host B from host A.
2. Use the existing read-only collector for OS, Python, GPU, driver/CUDA, disk, clock and container-runtime facts:

   ```text
   python tools/wp24/host_inventory.py --host-id <control|A|B> --ntp-check --out <wp02-artifacts>
   ```

   Add `--weights-path <actual-candidate-path>` only when that path is known; the option measures disk usage and does not install or start anything. `--ntp-check` must not adjust the clock.
3. Record network reachability and recovery-access facts at the level needed to prove the private two-host topology. Do not probe or access an external host unless the development-server/Operations owner authorized that action.
4. Build a candidate matrix for A (Xinference-managed) and B (independent service/vLLM) using exact runtime version, image digest or lock, model revision, physical resource ID and licence receipt. Keep source observations separate from measured runtime results.
5. Reconcile the inventory against SRS §2, ARCH resource boundaries, OPS prerequisites, WP24's approved candidate decision and the frozen WP03 authority contracts.
6. Have Operations/QA review the dossier and record each missing field as `BLOCKED` with an owner. Do not convert missing evidence into `PASS` or `QUALIFIED`.

No step in this procedure launches a model, starts a container, changes firewall/network state, issues credentials or changes an acceptance status.

## 4. Evidence dossier and status rules

Raw host outputs belong under `docs/evidence/wp02/<record_id>/` with a redacted summary alongside them. These are WP02/RG0 qualification-plan artifacts, not `PRP-AT-nnn` acceptance receipts. They must not change the 92 acceptance cases from `NOT_RUN` and must not be used as runtime PASS evidence.

The dossier is complete only when:

- authorized control/A/B host roles are identified and all mandatory inventory fields are present or explicitly `BLOCKED`;
- exact runtime/model/licence candidates and unresolved compatibility risks are recorded;
- Operations/QA review and the selected-environment readiness decision are recorded; and
- the reviewer can trace every claim to a raw artifact without exposing secrets.

RG0 may join only after this dossier and the remaining owner/security evidence are reviewed. WP25 and WP04 remain gated until then.

## 5. Initial preflight finding

The 2026-10-03 local preflight observed one RTX 3060 host with 12 GiB VRAM, approximately 32 GiB RAM, Windows 10, driver 616.92 and D: free space of approximately 684.89 GiB. `uv` supplied CPython 3.12.11; Docker was not available on PATH. This is local preflight evidence only: the second host, exact selected runtime/image and model/voice licence receipts were not available, so WP02 and RG0 remain `NOT_STARTED`/open.

## 6. Version diff and owner review

| Artifact | Before | After |
|---|---|---|
| WP02 procedure | No canonical collection procedure | This read-only collection procedure and evidence boundary |
| Execution DAG | WP02 requirement existed only in RG0 prose | Explicit `WP02 → RG0` edge |
| Roadmap/registry | WP25 depended on `WP03` only | WP25 depends on `WP03, RG0` |
| Runtime acceptance | 92 cases `NOT_RUN` | Unchanged |
| Deployment/production | Not authorized | Unchanged; still not authorized |

The repository owner approved this documentation in the current task on 2026-10-03. Approval covers the procedure and dependency reconciliation only; it does not approve implementation, credentials, server access, DEV, or PROD.
