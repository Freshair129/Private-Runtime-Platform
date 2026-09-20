"""Shared, pure-function helpers for the WP24 EV02 operator scripts.

Standard library only (see tools/wp24/README.md). Nothing here performs network I/O or touches a
GPU; the functions are kept pure so tools/wp24/tests/test_wp24_tools.py can exercise them with
fixture strings instead of real hardware or a live runtime.

None of these tools compute a PASS/FAIL/BLOCKED verdict (docs/WP24-EXPERIMENT-PROCEDURE.md section
3 item 4 reserves that for the reviewer); they only shape raw command output into the
measurements/observations/source_observations/artifacts fields that
docs/registry/wp24-run-record-template.json expects.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# --- redaction ---------------------------------------------------------------------------------
# Outputs must not carry usernames or home-directory paths (task constraint). Only structural,
# drive/prefix-based patterns are rewritten so unrelated text is left alone.
_HOME_PATTERNS = (
    re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/:*?\"<>|\r\n]+"),
    re.compile(r"/home/[^/\s]+"),
    re.compile(r"/Users/[^/\s]+"),
)
REDACTED = "<home>"
REDACTED_HEADER_VALUE = "<redacted>"


def redact_text(text: str) -> str:
    """Replace Windows/POSIX home-directory prefixes in ``text`` with ``<home>``."""
    if not text:
        return text
    redacted = text
    for pattern in _HOME_PATTERNS:
        redacted = pattern.sub(REDACTED, redacted)
    return redacted


def redact_json(value: Any) -> Any:
    """Recursively apply :func:`redact_text` to every string leaf of a JSON-like structure."""
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {key: redact_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_json(item) for item in value]
    return value


def redacted_header_lines(headers: dict[str, str]) -> list[str]:
    """Render request headers for logging with ``Authorization`` masked (never the value)."""
    lines = []
    for key, header_value in headers.items():
        shown = REDACTED_HEADER_VALUE if key.lower() == "authorization" else header_value
        lines.append(f"{key}: {shown}")
    return lines


# --- nvidia-smi CSV parsing ---------------------------------------------------------------------


def parse_nvidia_smi_csv(text: str, fields: Sequence[str]) -> list[dict[str, str]]:
    """Parse ``nvidia-smi --query-... --format=csv,noheader`` stdout into a list of dicts.

    nvidia-smi separates fields with ``", "`` and emits no header line in this mode. Blank lines
    are skipped. A line whose field count does not match ``fields`` (even after retrying with a
    bare comma split) is skipped rather than raised, since a stray driver warning occasionally
    leaks onto stdout ahead of the CSV rows.
    """
    rows: list[dict[str, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(", ")]
        if len(parts) != len(fields):
            parts = [part.strip() for part in line.split(",")]
        if len(parts) != len(fields):
            continue
        rows.append(dict(zip(fields, parts, strict=True)))
    return rows


GPU_UUID_RE = re.compile(r"GPU-[0-9a-fA-F-]{8,}")


def looks_like_gpu_uuid(value: str) -> bool:
    """True when ``value`` contains an nvidia-smi-style physical GPU UUID."""
    return bool(GPU_UUID_RE.search(value))


# --- identifier extraction / diffing --------------------------------------------------------
# Vendor-agnostic on purpose: SRC-01/SRC-09 confirm only that these APIs return model/worker
# identifying fields in a JSON body, not a fixed schema PRP can assume ahead of a real run.
IDENTIFIER_KEY_ALLOWLIST = {
    "id",
    "model_uid",
    "model_name",
    "model",
    "object",
    "gpu_idx",
    "gpu_uuid",
    "node_ip",
    "worker_ip",
    "address",
    "pid",
    "epoch",
    "revision",
    "created",
    "created_at",
    "started_at",
    "uptime",
    "owned_by",
}


def extract_candidate_identifiers(parsed: Any, *, max_items: int = 50) -> dict[str, str]:
    """Walk a parsed JSON response and collect a flat ``{path: value}`` map of likely identifiers.

    Only keys in :data:`IDENTIFIER_KEY_ALLOWLIST` are collected. This is a heuristic aid for the
    operator, not a claim about what any candidate's API guarantees to return.
    """
    found: dict[str, str] = {}

    def walk(node: Any, path: str) -> None:
        if len(found) >= max_items:
            return
        if isinstance(node, dict):
            for key, item in node.items():
                if len(found) >= max_items:
                    return
                child_path = f"{path}.{key}" if path else str(key)
                if (
                    isinstance(key, str)
                    and key.lower() in IDENTIFIER_KEY_ALLOWLIST
                    and isinstance(item, str | int | float | bool)
                ):
                    found[child_path] = str(item)
                if isinstance(item, dict | list):
                    walk(item, child_path)
        elif isinstance(node, list):
            for index, item in enumerate(node):
                if len(found) >= max_items:
                    return
                walk(item, f"{path}[{index}]")

    walk(parsed, "")
    return found


def diff_identifiers(before: dict[str, str], after: dict[str, str]) -> dict[str, dict[str, Any]]:
    """Pure structural diff between two flat ``{identifier_key: value}`` maps."""
    before_keys = set(before)
    after_keys = set(after)
    added = {key: after[key] for key in sorted(after_keys - before_keys)}
    removed = {key: before[key] for key in sorted(before_keys - after_keys)}
    common = sorted(before_keys & after_keys)
    changed = {
        key: {"before": before[key], "after": after[key]}
        for key in common
        if before[key] != after[key]
    }
    unchanged = {key: before[key] for key in common if before[key] == after[key]}
    return {"added": added, "removed": removed, "changed": changed, "unchanged": unchanged}


# --- misc small helpers --------------------------------------------------------------------


def utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string with a ``Z`` suffix, second precision."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def command_line() -> str:
    """The exact command line this process was invoked with, redacted of home-directory paths."""
    return redact_text(" ".join(sys.argv))


def write_json(out_dir: Path, filename: str, payload: dict[str, Any]) -> Path:
    """Write ``payload`` (already redacted by the caller) as pretty JSON under ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def run_command(args: list[str], *, timeout_seconds: float = 15.0) -> dict[str, Any]:
    """Run ``args`` and describe the outcome; never raises for a missing binary or a timeout."""
    command = " ".join(args)
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout_seconds)
    except FileNotFoundError:
        return {
            "command": command,
            "found": False,
            "return_code": None,
            "stdout": "",
            "stderr": f"{args[0]} not found",
        }
    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "found": True,
            "return_code": None,
            "stdout": "",
            "stderr": f"{args[0]} timed out after {timeout_seconds}s",
        }
    return {
        "command": command,
        "found": True,
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
