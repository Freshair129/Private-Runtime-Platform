#!/usr/bin/env python3
"""Tie a running candidate process to a physical GPU UUID for WP24 EV02, run ON the GPU host while
the runtime is up (docs/WP24-EXPERIMENT-PROCEDURE.md, gate PRP-FR-010..015).

Runs two ``nvidia-smi`` CSV queries and joins them:
  nvidia-smi --query-gpu=uuid,index --format=csv,noheader
  nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader

Deviation from a literal pid/process_name/used_memory-only compute-apps query: nvidia-smi's
compute-apps rows carry no GPU-identifying field unless one is requested, so a join against the
per-GPU uuid/index list would have no shared key. ``gpu_uuid`` is added to the compute-apps query
for the join to be meaningful; pid, process_name and used_memory are otherwise unchanged.

Rows whose process name matches --process-pattern (default: vllm|xinference|python, case
insensitive) are the ones the operator ties a runtime process to a GPU. Everything else is
counted only, never named, per the privacy requirement in the task brief.

Standard library only; computes no verdict.

Usage:
  python tools/wp24/ev02_gpu_binding.py --host-id A --out wp24-out
  python tools/wp24/ev02_gpu_binding.py --host-id B --process-pattern "vllm" --out wp24-out
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import wp24_common as common

GPU_QUERY_FIELDS = ("uuid", "index")
COMPUTE_APPS_FIELDS = ("gpu_uuid", "pid", "process_name", "used_memory")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host-id", required=True, choices=["A", "B"])
    parser.add_argument(
        "--process-pattern",
        default="vllm|xinference|python",
        help="case-insensitive regex matched against process_name",
    )
    parser.add_argument(
        "--out", default="./wp24-out", help="output directory (default: ./wp24-out)"
    )
    return parser.parse_args(argv)


def query_gpu_list(observations: list[str]) -> list[dict[str, str]]:
    result = common.run_command(
        ["nvidia-smi", f"--query-gpu={','.join(GPU_QUERY_FIELDS)}", "--format=csv,noheader"]
    )
    if not result["found"]:
        observations.append("nvidia-smi not found on this host (nvidia-smi --query-gpu)")
        return []
    if result["return_code"] != 0:
        stderr = common.redact_text(result["stderr"].strip())
        observations.append(f"nvidia-smi --query-gpu exited {result['return_code']}: {stderr}")
        return []
    return common.parse_nvidia_smi_csv(result["stdout"], GPU_QUERY_FIELDS)


def query_compute_apps(observations: list[str]) -> list[dict[str, str]]:
    result = common.run_command(
        [
            "nvidia-smi",
            f"--query-compute-apps={','.join(COMPUTE_APPS_FIELDS)}",
            "--format=csv,noheader",
        ]
    )
    if not result["found"]:
        observations.append("nvidia-smi not found on this host (nvidia-smi --query-compute-apps)")
        return []
    if result["return_code"] != 0:
        stderr = common.redact_text(result["stderr"].strip())
        code = result["return_code"]
        observations.append(f"nvidia-smi --query-compute-apps exited {code}: {stderr}")
        return []
    return common.parse_nvidia_smi_csv(result["stdout"], COMPUTE_APPS_FIELDS)


def join_and_classify(
    gpu_list: list[dict[str, str]],
    compute_apps: list[dict[str, str]],
    process_pattern: str,
) -> tuple[list[dict[str, str]], int]:
    index_by_uuid = {row["uuid"]: row["index"] for row in gpu_list}
    matcher = re.compile(process_pattern, re.IGNORECASE)
    matched: list[dict[str, str]] = []
    unrelated_count = 0
    for row in compute_apps:
        process_name = row.get("process_name", "")
        if matcher.search(process_name):
            matched.append(
                {
                    "pid": row.get("pid", ""),
                    "process_name": process_name,
                    "gpu_uuid": row.get("gpu_uuid", ""),
                    "gpu_index": index_by_uuid.get(row.get("gpu_uuid", "")),
                    "used_memory": row.get("used_memory", ""),
                }
            )
        else:
            unrelated_count += 1
    return matched, unrelated_count


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    observations: list[str] = []

    gpu_list = query_gpu_list(observations)
    compute_apps = query_compute_apps(observations)
    matched_processes, unrelated_count = join_and_classify(
        gpu_list, compute_apps, args.process_pattern
    )

    for process in matched_processes:
        if process["gpu_index"] is None:
            observations.append(
                f"pid {process['pid']} ({process['process_name']}): gpu_uuid "
                f"{process['gpu_uuid']} did not match any row of --query-gpu=uuid,index"
            )

    measurements = [
        {"name": "gpu_count", "value": len(gpu_list)},
        {"name": "matched_process_count", "value": len(matched_processes)},
        {"name": "unrelated_process_count", "value": unrelated_count},
    ]

    timestamp = common.utc_now_iso().replace(":", "").replace("-", "")
    filename = f"ev02_gpu_binding_{args.host_id}_{timestamp}.json"
    payload = {
        "kind": "WP24_EV02_GPU_BINDING",
        "generated_at_utc": common.utc_now_iso(),
        "command_line": common.command_line(),
        "host_id": args.host_id,
        "process_pattern": args.process_pattern,
        "gpu_list": gpu_list,
        "matched_processes": matched_processes,
        "unrelated_process_count": unrelated_count,
        "measurements": measurements,
        "observations": observations,
        "source_observations": [],
        "artifacts": [filename],
    }
    path = common.write_json(Path(args.out), filename, common.redact_json(payload))
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
