#!/usr/bin/env python3
"""Record a host's environment for WP24 (docs/WP24-EXPERIMENT-PROCEDURE.md section 2 and EV01/EV02).

Run this on the control host and on each GPU host (A, B) before an EV02 run. It collects OS /
kernel / Python version, GPU inventory and driver/CUDA version from ``nvidia-smi`` (recorded as
"nvidia-smi not found" rather than failing when the binary is missing, since the control host is
allowed to have no GPU driver at all), disk free space for a candidate's weights path, an optional
clock-skew check against a reference time, and whether a container runtime is present (version
check only, nothing is started).

This script computes no verdict and makes no candidate claim; it only shapes host facts into the
measurements/observations/artifacts fields that docs/registry/wp24-run-record-template.json
expects under ``environment.control_host`` / ``environment.gpu_hosts[]``. Standard library only.

Usage:
  python tools/wp24/host_inventory.py --host-id A --weights-path D:/models --out wp24-out
  python tools/wp24/host_inventory.py --host-id control --reference-time 2026-09-20T12:00:00Z
"""

from __future__ import annotations

import argparse
import platform
import re
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import wp24_common as common

CUDA_VERSION_RE = re.compile(r"CUDA Version:\s*([\d.]+)")
GPU_L_LINE_RE = re.compile(r"^GPU (\d+):\s*(.*?)\s*\(UUID:\s*(GPU-[0-9a-fA-F-]+)\)\s*$")
GPU_QUERY_FIELDS = ("name", "memory.total", "driver_version", "uuid")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--host-id", required=True, help="stable identifier for this host, e.g. A, B or control"
    )
    parser.add_argument(
        "--weights-path",
        default=None,
        help="path to check free disk space for (need not exist yet)",
    )
    parser.add_argument(
        "--reference-time",
        default=None,
        help="ISO-8601 UTC time to compare this host's clock against",
    )
    parser.add_argument(
        "--out", default="./wp24-out", help="output directory (default: ./wp24-out)"
    )
    return parser.parse_args(argv)


def collect_os_python(measurements: list[dict[str, object]]) -> None:
    measurements.append({"name": "os_system", "value": platform.system()})
    measurements.append({"name": "os_release", "value": platform.release()})
    measurements.append({"name": "os_version", "value": common.redact_text(platform.version())})
    measurements.append({"name": "kernel_or_platform_release", "value": platform.release()})
    measurements.append({"name": "machine", "value": platform.machine()})
    measurements.append({"name": "python_version", "value": platform.python_version()})
    measurements.append(
        {"name": "python_implementation", "value": platform.python_implementation()}
    )


def collect_gpu_list(observations: list[str]) -> tuple[list[dict[str, str]], bool]:
    result = common.run_command(["nvidia-smi", "-L"])
    if not result["found"]:
        observations.append("nvidia-smi not found on this host (nvidia-smi -L)")
        return [], False
    if result["return_code"] != 0:
        stderr = common.redact_text(result["stderr"].strip())
        observations.append(f"nvidia-smi -L exited {result['return_code']}: {stderr}")
        return [], True
    gpus: list[dict[str, str]] = []
    for line in result["stdout"].splitlines():
        match = GPU_L_LINE_RE.match(line.strip())
        if match:
            gpus.append({"index": match.group(1), "name": match.group(2), "uuid": match.group(3)})
    return gpus, True


def collect_gpu_query(observations: list[str], gpu_driver_present: bool) -> list[dict[str, str]]:
    if not gpu_driver_present:
        return []
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


def collect_cuda_version(observations: list[str], gpu_driver_present: bool) -> str | None:
    if not gpu_driver_present:
        return None
    result = common.run_command(["nvidia-smi"])
    if not result["found"] or result["return_code"] != 0:
        observations.append("could not read CUDA version from bare `nvidia-smi` header")
        return None
    match = CUDA_VERSION_RE.search(result["stdout"])
    if not match:
        observations.append("`nvidia-smi` header did not contain a 'CUDA Version:' field")
        return None
    return match.group(1)


def collect_disk_free(
    weights_path: str | None, observations: list[str]
) -> dict[str, object] | None:
    if weights_path is None:
        return None
    target = Path(weights_path)
    probe = target
    while not probe.exists():
        if probe.parent == probe:
            safe_path = common.redact_text(weights_path)
            observations.append(
                f"no existing ancestor for --weights-path {safe_path}; disk free not measured"
            )
            return None
        probe = probe.parent
    usage = shutil.disk_usage(probe)
    return {
        "checked_path": common.redact_text(str(probe)),
        "requested_path": common.redact_text(str(target)),
        "path_existed": probe == target,
        "free_bytes": usage.free,
        "total_bytes": usage.total,
    }


def collect_clock_skew(
    reference_time: str | None, observations: list[str]
) -> dict[str, object] | None:
    if reference_time is None:
        return None
    try:
        reference = datetime.fromisoformat(reference_time.replace("Z", "+00:00"))
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=UTC)
    except ValueError:
        observations.append(f"--reference-time {reference_time!r} is not valid ISO-8601")
        return None
    now = datetime.now(UTC)
    skew_seconds = (now - reference).total_seconds()
    return {
        "reference_time_utc": reference.isoformat(),
        "measured_at_utc": now.isoformat(),
        "skew_seconds": skew_seconds,
    }


def collect_container_runtime(observations: list[str]) -> dict[str, object]:
    docker = common.run_command(["docker", "--version"])
    systemctl = common.run_command(["systemctl", "--version"])
    if not docker["found"]:
        observations.append("docker not found on this host (version check only, nothing started)")
    if not systemctl["found"]:
        observations.append(
            "systemctl not found on this host (version check only, nothing started)"
        )
    return {
        "docker": {
            "present": docker["found"],
            "version_output": common.redact_text(docker["stdout"].strip()),
        },
        "systemctl": {
            "present": systemctl["found"],
            "version_output": common.redact_text(systemctl["stdout"].strip()),
        },
    }


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    measurements: list[dict[str, object]] = []
    observations: list[str] = []

    collect_os_python(measurements)
    gpu_list, gpu_driver_present = collect_gpu_list(observations)
    gpu_query_rows = collect_gpu_query(observations, gpu_driver_present)
    cuda_version = collect_cuda_version(observations, gpu_driver_present)
    disk_free = collect_disk_free(args.weights_path, observations)
    clock_skew = collect_clock_skew(args.reference_time, observations)
    container_runtime = collect_container_runtime(observations)

    measurements.append({"name": "gpu_driver_present", "value": gpu_driver_present})
    measurements.append({"name": "gpu_count", "value": len(gpu_list)})
    if cuda_version is not None:
        measurements.append({"name": "cuda_version", "value": cuda_version})
    if disk_free is not None:
        measurements.append({"name": "weights_path_free_bytes", "value": disk_free["free_bytes"]})
    if clock_skew is not None:
        measurements.append({"name": "clock_skew_seconds", "value": clock_skew["skew_seconds"]})
    measurements.append({"name": "docker_present", "value": container_runtime["docker"]["present"]})
    measurements.append(
        {"name": "systemctl_present", "value": container_runtime["systemctl"]["present"]}
    )

    if not gpu_driver_present:
        observations.append(
            "host has no GPU driver; per WP24-EXPERIMENT-PROCEDURE.md section 2 this is "
            "recorded, not disqualifying, for a control host"
        )

    timestamp = common.utc_now_iso().replace(":", "").replace("-", "")
    filename = f"host_inventory_{args.host_id}_{timestamp}.json"
    payload = {
        "kind": "WP24_HOST_INVENTORY",
        "generated_at_utc": common.utc_now_iso(),
        "command_line": common.command_line(),
        "host_id": args.host_id,
        "gpu_list": gpu_list,
        "gpu_query_rows": gpu_query_rows,
        "disk_free": disk_free,
        "clock_skew": clock_skew,
        "container_runtime": container_runtime,
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
