#!/usr/bin/env python3
"""Record a host's environment for WP24 (docs/WP24-EXPERIMENT-PROCEDURE.md section 2 and EV01/EV02).

Run this on the control host and on each GPU host (A, B) before an EV02 run. It collects OS /
kernel / Python version, GPU inventory and driver/CUDA version from ``nvidia-smi`` (recorded as
"nvidia-smi not found" rather than failing when the binary is missing; a GPU driver on the control
host is recorded, never disqualifying, per procedure section 2), disk free space for a candidate's
weights path, two optional clock checks, and whether a container runtime is present (version check
only, nothing is started).

Clock checks. ``--reference-time`` compares an ISO time the operator fetched earlier with the local
clock at measurement time; the result therefore includes every second spent between fetching and
running and is reported as ``reference_time_delta_seconds``, not as skew. ``--ntp-check`` queries an
NTP server directly (``w32tm /stripchart`` on Windows, ``chronyc tracking`` or ``ntpdate -q`` on
other systems, whichever is installed) and reports ``offsets_seconds`` as local minus server. Both
are read-only; the clock is never adjusted.

This script computes no verdict and makes no candidate claim; it only shapes host facts into the
measurements/observations/artifacts fields that docs/registry/wp24-run-record-template.json
expects under ``environment.control_host`` / ``environment.gpu_hosts[]``. Standard library only.

Usage:
  python tools/wp24/host_inventory.py --host-id A --weights-path D:/models --ntp-check
  python tools/wp24/host_inventory.py --host-id control --ntp-check --ntp-server time.windows.com
"""

from __future__ import annotations

import argparse
import platform
import re
import shutil
import statistics
import sys
from datetime import UTC, datetime
from pathlib import Path

import wp24_common as common

# Linux drivers print "CUDA Version: 12.4"; recent Windows drivers print "CUDA UMD Version: 13.4".
CUDA_VERSION_RE = re.compile(r"(CUDA(?: UMD)? Version):\s*([\d.]+)")
CUDA_LABELS = ("CUDA Version:", "CUDA UMD Version:")
GPU_L_LINE_RE = re.compile(r"^GPU (\d+):\s*(.*?)\s*\(UUID:\s*(GPU-[0-9a-fA-F-]+)\)\s*$")
GPU_QUERY_FIELDS = ("name", "memory.total", "driver_version", "uuid")

# w32tm /stripchart ... /dataonly lines: "23:44:07, -00.6247612s" (offset = local - server).
W32TM_OFFSET_RE = re.compile(r",\s*([+-]?\d+\.\d+)s")
# chronyc tracking: "System time     : 0.000012 seconds fast of NTP time"
CHRONYC_SYSTEM_TIME_RE = re.compile(
    r"System time\s*:\s*([\d.]+)\s+seconds\s+(fast|slow)\s+of NTP time"
)
# ntpdate -q: "server 1.2.3.4, stratum 2, offset -0.001234, delay 0.02567" (offset = server - local)
NTPDATE_OFFSET_RE = re.compile(r"offset\s+([+-]?\d+\.\d+)")

DEFAULT_NTP_SERVER_WINDOWS = "time.windows.com"
DEFAULT_NTP_SERVER_OTHER = "pool.ntp.org"


def default_ntp_server(system: str | None = None) -> str:
    system = system or platform.system()
    return DEFAULT_NTP_SERVER_WINDOWS if system == "Windows" else DEFAULT_NTP_SERVER_OTHER


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
        help=(
            "ISO-8601 UTC time fetched earlier by the operator; the reported delta includes the "
            "fetch-to-measure latency (prefer --ntp-check for an offset)"
        ),
    )
    parser.add_argument(
        "--ntp-check",
        action="store_true",
        help="query an NTP server read-only (w32tm on Windows, chronyc/ntpdate elsewhere)",
    )
    parser.add_argument(
        "--ntp-server",
        default=None,
        help=(
            f"NTP server for --ntp-check (default {DEFAULT_NTP_SERVER_WINDOWS} on Windows, "
            f"{DEFAULT_NTP_SERVER_OTHER} elsewhere)"
        ),
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


def parse_cuda_version(header_text: str) -> tuple[str, str] | None:
    """Return ``(label, version)`` from a bare ``nvidia-smi`` header, or None when absent.

    Accepts the Linux label ``CUDA Version:`` and the Windows label ``CUDA UMD Version:``.
    """
    match = CUDA_VERSION_RE.search(header_text)
    if not match:
        return None
    return f"{match.group(1)}:", match.group(2)


def collect_cuda_version(
    observations: list[str], gpu_driver_present: bool
) -> dict[str, str] | None:
    if not gpu_driver_present:
        return None
    result = common.run_command(["nvidia-smi"])
    if not result["found"] or result["return_code"] != 0:
        observations.append("could not read CUDA version from bare `nvidia-smi` header")
        return None
    parsed = parse_cuda_version(result["stdout"])
    if parsed is None:
        labels = " or ".join(f"'{label}'" for label in CUDA_LABELS)
        observations.append(f"`nvidia-smi` header did not contain a {labels} field")
        return None
    label, version = parsed
    observations.append(f"CUDA version read from the `nvidia-smi` header label '{label}'")
    return {"version": version, "header_label": label}


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


def collect_reference_time_delta(
    reference_time: str | None, observations: list[str]
) -> dict[str, object] | None:
    """Compare an operator-supplied reference time with the local clock.

    The delta includes the seconds between fetching the reference and running this script, so it
    bounds, but does not measure, the host's clock skew. ``collect_ntp_offset`` is the measurement.
    """
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
    observations.append(
        "reference_time_delta_seconds includes the latency between fetching --reference-time and "
        "this measurement; it is an upper bound, not a skew measurement (use --ntp-check)"
    )
    return {
        "reference_time_utc": reference.isoformat(),
        "measured_at_utc": now.isoformat(),
        "reference_time_delta_seconds": (now - reference).total_seconds(),
    }


def parse_w32tm_stripchart(text: str) -> list[float]:
    """Offsets (local minus server, seconds) from ``w32tm /stripchart ... /dataonly`` output."""
    return [float(value) for value in W32TM_OFFSET_RE.findall(text)]


def parse_chronyc_tracking(text: str) -> list[float]:
    """Offset (local minus server, seconds) from ``chronyc tracking``; 'fast' = local ahead."""
    match = CHRONYC_SYSTEM_TIME_RE.search(text)
    if not match:
        return []
    magnitude = float(match.group(1))
    return [magnitude if match.group(2) == "fast" else -magnitude]


def parse_ntpdate_query(text: str) -> list[float]:
    """Offsets (local minus server, seconds) from ``ntpdate -q`` (its offset is server - local)."""
    return [-float(value) for value in NTPDATE_OFFSET_RE.findall(text)]


def collect_ntp_offset(
    enabled: bool, server: str | None, observations: list[str], system: str | None = None
) -> dict[str, object] | None:
    """Query an NTP server read-only and report offsets as local minus server seconds."""
    if not enabled:
        return None
    system = system or platform.system()
    server = server or default_ntp_server(system)
    attempts: list[tuple[str, list[str], object]] = []
    if system == "Windows":
        attempts.append(
            (
                "w32tm",
                [
                    "w32tm",
                    "/stripchart",
                    f"/computer:{server}",
                    "/samples:3",
                    "/period:2",
                    "/dataonly",
                ],
                parse_w32tm_stripchart,
            )
        )
    else:
        attempts.append(("chronyc", ["chronyc", "tracking"], parse_chronyc_tracking))
        attempts.append(("ntpdate", ["ntpdate", "-q", server], parse_ntpdate_query))

    tried: list[str] = []
    for tool, args, parser in attempts:
        result = common.run_command(args, timeout_seconds=30.0)
        tried.append(tool)
        if not result["found"]:
            continue
        stdout = common.redact_text(result["stdout"])
        offsets = parser(stdout)
        if not offsets:
            observations.append(
                f"{tool} ran (exit {result['return_code']}) but no offset could be parsed from its output"
            )
            continue
        return {
            "tool": tool,
            "server": server,
            "command": " ".join(args),
            "offsets_seconds": offsets,
            "median_offset_seconds": statistics.median(offsets),
            "sign_convention": "local minus server",
            "raw_output": stdout.strip(),
            "return_code": result["return_code"],
        }
    observations.append(
        "no NTP query tool available or none produced an offset "
        f"(tried: {', '.join(tried)}); clock offset not measured, clock not adjusted"
    )
    return None


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
    cuda = collect_cuda_version(observations, gpu_driver_present)
    disk_free = collect_disk_free(args.weights_path, observations)
    reference_delta = collect_reference_time_delta(args.reference_time, observations)
    ntp_offset = collect_ntp_offset(args.ntp_check, args.ntp_server, observations)
    container_runtime = collect_container_runtime(observations)

    measurements.append({"name": "gpu_driver_present", "value": gpu_driver_present})
    measurements.append({"name": "gpu_count", "value": len(gpu_list)})
    if cuda is not None:
        measurements.append({"name": "cuda_version", "value": cuda["version"]})
        measurements.append({"name": "cuda_version_header_label", "value": cuda["header_label"]})
    if disk_free is not None:
        measurements.append({"name": "weights_path_free_bytes", "value": disk_free["free_bytes"]})
    if reference_delta is not None:
        measurements.append(
            {
                "name": "reference_time_delta_seconds",
                "value": reference_delta["reference_time_delta_seconds"],
            }
        )
    if ntp_offset is not None:
        measurements.append(
            {"name": "ntp_offset_seconds_median", "value": ntp_offset["median_offset_seconds"]}
        )
        measurements.append({"name": "ntp_offsets_seconds", "value": ntp_offset["offsets_seconds"]})
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
        "cuda": cuda,
        "disk_free": disk_free,
        "reference_time_delta": reference_delta,
        "ntp_offset": ntp_offset,
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
