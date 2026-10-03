# WP02 current host inventory — Host B

**Captured:** 2026-10-03 (Asia/Bangkok); latest structured host-tool receipt: `2026-10-03T09:17:41Z`; latest Windows host receipt: `2026-10-03T09:20:30Z`

**Status:** Partial discovery only; this does not close WP02 or RG0.

**Owner review:** APPROVED 2026-10-03 for the preliminary Host B discovery; the new receipts refresh observations and do not approve WP02 closure.

**Collection:** Read-only local inventory. No services, firewall, network settings, containers, or models were changed or started.

## Host assignment and evidence boundary

The existing [WP24 run 1 record](../wp24/WP24-2026-09-20-run1.json) identifies `DESKTOP-VETATMQ` as Host B and the control/main host by the owner's 2026-09-21 decision. This snapshot was collected on that hostname. It is a new dated observation; it does not replace the historical WP24 record or establish runtime qualification. The current Windows host measurements are in [the structured Windows receipt](host_inventory_B_windows_20261003T092030Z.json); GPU, CUDA, Python, Docker, and model-runtime observations are in [the latest structured host-tool receipt](host_inventory_B_20261003T091741Z.json).

The owner supplied a local inventory summary for `DESKTOP-8UR61U8`, captured 2026-10-04 03:04 Asia/Bangkok. Its hostname matches the expected Host A worker name in WP24 run 1; the summary is recorded in [the Host A inventory report](WP02-2026-10-04-host-a-reported-inventory.md). The raw Host A files remain on `D:\prp` and were not accessible from this checkout, so their JSON contents and reported hashes were not independently verified here.

The Host A summary reports `192.168.1.172/24`; the Host B snapshot reports `192.168.88.225/24` at a different collection time. The owner confirmed on 2026-10-04 that the machines are at different physical locations and on different networks. This resolves the high-level topology as owner-reported, but not the existence or approval of a route/tunnel or current endpoint reachability. The earlier PC-2 report gave `192.168.1.33/24`, but that historical address was not contacted. Bounded DNS checks from Host B at `2026-10-03T09:21:59Z` and `2026-10-03T18:18:03Z` returned no DNS records or echo reply for the peer hostname. One later Host B→`192.168.1.172` ICMP attempt at `2026-10-03T21:48:51Z` timed out and one TCP/445 attempt at `2026-10-03T21:49:35Z` did not connect. `Find-NetRoute` at `2026-10-03T21:53:22Z` selected Host B's default gateway `192.168.88.1` and source `192.168.88.225` for that destination. These one-way negative results do not prove Host A is down or identify whether routing or filtering blocked the probes.

The [WP24 experiment procedure](../../WP24-EXPERIMENT-PROCEDURE.md) requires the two GPU hosts to be on one LAN with a LAN-only boundary. The currently owner-described separate-location/network arrangement does not meet that precondition; a route/tunnel cannot be assumed to satisfy it.

## Host B snapshot

| Area | Current observation |
|---|---|
| Host | `DESKTOP-VETATMQ`; ASUS system |
| OS | Windows 11 Pro, version `10.0.26300`, build `26300`, 64-bit |
| CPU | Intel Core i7-14700KF, 20 cores / 28 logical processors |
| RAM | 31.8 GiB total; 14.0 GiB free at `2026-10-03T09:20:30Z` |
| GPU | NVIDIA GeForce RTX 5060 Ti, 16,311 MiB; driver `617.14`; `nvidia-smi` reports CUDA UMD `13.4` |
| Storage | C: 952.9 GiB total / 258.4 GiB free; F: 476.9 GiB total / 175.1 GiB free. Both structured receipts set `path_existed: true` for the requested `F:\models`; the earlier narrative claim that it did not exist was incorrect. See [RCA](../../../.brain/rca/RCA-2026-10-03-wp02-disk-path-summary.md). |
| Network adapter | Ethernet, Realtek Gaming 2.5GbE Family Controller, interface index `7`, Up, negotiated at `1 Gbps` |
| Network profile | Public; DHCP enabled; `192.168.88.225/24`; gateway and DNS: `192.168.88.1` |
| Local tooling | Python `3.12.10`; uv `0.12.8`; Docker client/server `29.8.1`; Ollama CLI `0.35.1`; `nvcc`, vLLM, and Xinference executables were not found on the Windows PATH |
| Model/runtime observations | `ollama list` returned `qwen3:4b` (2.5 GB) at `2026-10-03T09:21:59Z`; it was listed only and not run by this inventory. It is not the WP24-selected Typhoon revision; its rights have not been assessed. Docker client/server responded at collection time. Container ports and tunnel reachability were not inspected. |

Structured GPU/OS/runtime/disk evidence is in the dated host-tool receipts linked above. CPU, RAM, NIC, network-profile, DHCP, and disk-volume observations are recorded in the structured Windows receipt and were collected with read-only CIM/NetTCPIP queries. Absence of a Windows CLI does not establish absence inside WSL or a container.

## Differences from the 2026-09-20 record

The earlier WP24 record reports OS build `26200`, GPU driver `616.92`, Docker `29.8.0`, and 217.2 GiB free on F:. This snapshot reports build `26300`, driver `617.14`, Docker `29.8.1`, and 175.1 GiB free on F:. Preserve both observations with their dates; do not treat the older values as current.

The previous PC-1 network report was `192.168.1.34/24` with a 100 Mbps link; an earlier live observation recorded the profile as Private. The current snapshot is `192.168.88.225/24` with a 1 Gbps link and Public profile. Preserve these as time-separated observations; this snapshot does not establish when or why the network/profile changed.

The Host A summary reports `192.168.1.172/24` at 100 Mbps with a Private profile. This differs from the earlier PC-2 `.33/24` report, but the dates, non-simultaneous observations, and unavailable raw files do not establish when or why the address/profile changed or how either host is connected.

## Outstanding WP02 evidence

1. Integrate the Host A raw receipt files into an accessible repository path so their structured measurements, verification output, and hashes can be reviewed. The supplied summary leaves the model path, F: capacity, Ethernet model/interface index, complete volume inventory, Docker client/server, and installed Ollama models unresolved or unverified.
2. Resolve the mismatch between the owner-confirmed separate-site/network arrangement and the WP24 same-LAN precondition. Operations must document the intended boundary and any approved route/tunnel, and the owner must decide whether to place both hosts on the required LAN or formally review a procedure/architecture change. Do not infer endpoint reachability from the reported IPs or the failed one-way probes.

The selected model and license-source assessment are recorded in [SEC-007](../../SEC-007-MODEL-LICENSE-REVIEW.md); that document identifies unresolved rights and intended-use decisions. The formal license receipt is a separate activation gate, not a substitute for Host A inventory. This local `qwen3:4b` listing is an unreviewed installed model and is not adopted as the PRP candidate.

WP02 remains open with partial discovery evidence: Host B has dated structured receipts and Host A has an owner-provided inventory summary whose raw files are not yet available in this checkout. The owner confirms separate physical locations and networks; endpoint reachability and the approved boundary remain unresolved, and the WP24 same-LAN precondition is unmet for the described arrangement. Do not infer qualification from these observations. RG0 also has separate environment-readiness and operations evidence requirements; see the [execution DAG](../../EXECUTION-DAG-PRP.md).

The roadmap implementation status remains `NOT_STARTED`; discovery evidence is `PARTIAL`. WP25/WP04 entry remains gated; all 92 runtime acceptance cases remain `NOT_RUN`.
