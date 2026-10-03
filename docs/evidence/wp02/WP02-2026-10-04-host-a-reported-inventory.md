# WP02 Host A inventory — operator-provided summary

**Captured (reported):** 2026-10-04 03:04 Asia/Bangkok (`2026-10-03T20:04:00Z`)

**Status:** Partial discovery only; raw source artifacts were not available in this checkout when this summary was recorded.

**Provenance:** The repository owner supplied the measurements and reported five receipt files under `D:\prp\docs\evidence\wp02\WP02-20261003T200400Z-local-inventory\`. The owner reports that all four JSON files passed validation, hashes were checked, no tracked-file diff was present, and the three pre-existing WIP-file hashes were unchanged. This checkout has no `D:` drive, so those artifacts and checks could not be independently verified or linked here.

The reported hostname, `DESKTOP-8UR61U8`, matches the expected Host A worker name recorded in the WP24 run 1 owner decision. This local inventory alone does not confirm the current physical host-to-role assignment or A/B network topology.

## Reported measurements

| Area | Reported observation |
|---|---|
| Host | `DESKTOP-8UR61U8` |
| OS | Windows 10 Pro 22H2, build `19045.7725`, 64-bit |
| CPU | Intel Core i7-8700K, 6 cores / 12 threads |
| RAM | 32 GiB total; 13.94 GiB available |
| GPU | NVIDIA RTX 3060, 12 GiB VRAM; driver `616.92`; `nvidia-smi` reports CUDA UMD `13.4` |
| Network | Ethernet, `192.168.1.172/24`, DHCP enabled, 100 Mbps, Private profile |
| Gateway / DNS | Gateway `192.168.1.1`; DNS `115.178.58.26`, `115.178.58.10` |
| Local tooling | Python `3.13.7`; uv `0.11.2`; Ollama CLI `0.35.1` |

## Unavailable or unresolved

- Model path and F: volume capacity were not established.
- The summary supplied in chat does not include the Ethernet adapter model/interface index or the complete volume inventory; check the raw receipt before treating those fields as verified.
- Docker client/server versions were unavailable.
- `ollama list` through loopback returned exit code `1`; installed model names remain unknown. The CLI version alone does not establish a usable model runtime.
- Current A/B reachability and physical/network topology remain unverified. Host B's cited snapshot reports `192.168.88.225/24`, collected at a different time. The separate-subnet observations do not establish routing, VLANs, or current peer reachability.
- The raw inventory files and their reported validation/hashes must be made available in this repository before they can serve as locally verified structured evidence.

This report records the owner-provided summary, not a runtime qualification. WP02 remains open and RG0 remains gated on the other required entry evidence.
