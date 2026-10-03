# WP02 Host A inventory — operator-provided summary

**Captured (reported):** 2026-10-04 03:04 Asia/Bangkok (`2026-10-03T20:04:00Z`)

**Status:** Partial discovery only; raw source artifacts were not available in this checkout when this summary was recorded.

**Provenance:** The repository owner supplied the measurements and reported five receipt files under `D:\prp\docs\evidence\wp02\WP02-20261003T200400Z-local-inventory\`. The owner reports that all four JSON files passed validation, hashes were checked, no tracked-file diff was present, and the three pre-existing WIP-file hashes were unchanged. This checkout has no `D:` drive, so those artifacts and checks could not be independently verified or linked here.

The reported hostname, `DESKTOP-8UR61U8`, matches the expected Host A worker name recorded in the WP24 run 1 owner decision. This local inventory alone does not confirm the current physical host-to-role assignment or A/B network topology.

The owner separately confirmed on 2026-10-04 that Host A and Host B are at different physical locations and on different networks. This is an owner-reported high-level topology fact. It does not establish whether a routed path or tunnel exists, what network boundary is approved, or whether runtime/control endpoints are reachable. The [WP24 experiment procedure](../../WP24-EXPERIMENT-PROCEDURE.md) requires both GPU hosts on one LAN with a LAN-only boundary; that precondition is not met by the currently described arrangement unless the hosts are brought onto the required LAN or the procedure is formally reviewed and revised.

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
- From Host B (`192.168.88.225`, Public, gateway `192.168.88.1`), `Find-NetRoute` at `2026-10-03T21:53:22Z` selected source `.88.225`, interface index `7`, and default gateway `192.168.88.1` for the reported Host A address. One ICMP echo to that address timed out at `2026-10-03T21:48:51Z`; a TCP connection attempt to `192.168.1.172:445` at `2026-10-03T21:49:35Z` returned `TcpTestSucceeded: false`. No SMB authentication was attempted and the historical `.33` address was not contacted. These negative one-way probes do not distinguish host unavailability from routing or filtering and do not establish physical/network topology.
- The owner-confirmed separation of locations/networks does not determine current A/B reachability. Host B's snapshot reports `192.168.88.225/24`, collected at a different time; the separate-subnet observations and failed one-way probes do not establish an approved route, tunnel, or VLAN configuration.
- The raw inventory files and their reported validation/hashes must be made available in this repository before they can serve as locally verified structured evidence.

This report records owner-provided inventory and topology statements, not runtime qualification. WP02 remains open pending locally reviewable Host A receipts and the unresolved inventory fields. RG0 remains gated on evidence that the selected environment satisfies its approved network boundary and the other entry requirements.
