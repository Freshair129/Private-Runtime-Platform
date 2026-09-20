"""Shared pure helpers for the WP24 LiteLLM sub-spike scripts (ev04_keys.py, ev03_retry_probe.py).

Standard library only. Nothing here performs network I/O; HTTP calls live in the two entrypoint
scripts so this module stays trivially unit-testable (tests/test_litellm_subspike.py).

Hard constraint (WP24-EXPERIMENT-PROCEDURE.md section 3 item 6; task brief): no secret ever reaches
disk or stdout. A master key or virtual key is used only in-memory for an Authorization header and
is represented everywhere else -- output JSON, redacted command lines, artifact dumps -- as a
``sha256:<first 12 hex>`` fingerprint computed locally.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

# Field names whose value is treated as a secret and never written verbatim to an artifact or the
# result JSON: virtual/master keys, LiteLLM's own "token" field (see ev04_keys.py header comment on
# why that field is exactly the one EV04 must check), and anything Authorization-shaped.
_SECRET_FIELD = re.compile(r"(key|token|authorization|secret)", re.IGNORECASE)

# A LiteLLM virtual key always starts with this prefix (docs.litellm.ai/docs/proxy/virtual_keys
# "Quick Start - Generate a Key" and "Setup": "must start with sk-"). Used only to spot a
# key-shaped value that leaked into a place it should not be (e.g. an argv element).
_KEY_SHAPED = re.compile(r"sk-[A-Za-z0-9_-]{4,}")


def utc_now_iso() -> str:
    """Second-precision UTC timestamp, e.g. 2026-09-20T12:34:56Z."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def fingerprint(secret: str) -> str:
    """``sha256:<first 12 hex>`` of *secret*. Never return or log the secret itself."""
    digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    return f"sha256:{digest[:12]}"


def redact_value(value: Any, plaintext: str | None = None) -> Any:
    """Redact one value for safe storage.

    A string equal to *plaintext* (when given) becomes its fingerprint. Any other string that is
    itself key-shaped (``sk-...``) is redacted without being fingerprinted against a known secret,
    since we do not know what it is a copy of. Non-string values pass through unchanged.
    """
    if isinstance(value, str):
        if plaintext is not None and value == plaintext:
            return fingerprint(value)
        if _KEY_SHAPED.search(value):
            return "<redacted:key-shaped-value>"
    return value


def redact_mapping(obj: Any, plaintext: str | None = None) -> Any:
    """Recursively redact a JSON-shaped structure (dict/list/scalar) for safe artifact storage.

    Any mapping key matching ``key``/``token``/``authorization``/``secret`` (case-insensitive) has
    its value redacted outright, whether or not it matches *plaintext*, because those field names
    are exactly where LiteLLM documents a key or token value being echoed back (e.g.
    GenerateKeyResponse ``key``/``token``: https://docs.litellm.ai/docs/proxy/virtual_keys). Every
    other string value is still checked against *plaintext* and against the key-shaped pattern.
    """
    if isinstance(obj, Mapping):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            if isinstance(k, str) and _SECRET_FIELD.search(k):
                if isinstance(v, str):
                    out[k] = fingerprint(v)
                elif isinstance(v, Mapping | list):
                    out[k] = redact_mapping(v, plaintext)
                else:
                    out[k] = v
            else:
                out[k] = redact_mapping(v, plaintext)
        return out
    if isinstance(obj, list):
        return [redact_mapping(v, plaintext) for v in obj]
    return redact_value(obj, plaintext)


def find_plaintext_locations(obj: Any, plaintext: str, path: str = "$") -> list[str]:
    """Return JSON-path-like locations where a value equals *plaintext* exactly.

    Only the *location* is returned (e.g. ``$.info.token``), never the value, so a caller can log
    "plaintext reappeared at $.info.token" without ever writing the plaintext itself to disk.
    """
    hits: list[str] = []
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            hits.extend(find_plaintext_locations(v, plaintext, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(find_plaintext_locations(v, plaintext, f"{path}[{i}]"))
    elif isinstance(obj, str) and obj == plaintext:
        hits.append(path)
    return hits


def redact_argv(argv: Sequence[str]) -> list[str]:
    """Redact a command-line argument list before it is written into a result JSON.

    The scripts in this kit never accept a secret value directly on the command line (only env var
    *names*, e.g. ``--master-key-env LITELLM_MASTER_KEY``), so this is a defensive second layer in
    case an operator pastes a real ``sk-...`` value in by mistake.
    """
    return ["<redacted:key-shaped-value>" if _KEY_SHAPED.search(a) else a for a in argv]


def poll_until(
    check: Callable[[], bool],
    *,
    interval_s: float,
    timeout_s: float,
    clock: Callable[[], float],
    sleep: Callable[[float], None],
) -> dict[str, Any]:
    """Poll *check* every *interval_s* seconds until it returns True or *timeout_s* elapses.

    Pure with respect to time: *clock* and *sleep* are injected so tests can run this with a fake
    clock and no real delay (tests/test_litellm_subspike.py). Mirrors the polling loop ev04_keys.py
    runs against ``/v1/models`` with a revoked key (task brief item 3(d)).
    """
    start = clock()
    elapsed = 0.0
    attempts = 0
    while True:
        attempts += 1
        if check():
            return {"rejected": True, "elapsed_seconds": elapsed, "attempts": attempts}
        if elapsed >= timeout_s:
            return {"rejected": False, "elapsed_seconds": elapsed, "attempts": attempts}
        sleep(interval_s)
        elapsed = clock() - start


def measurement(name: str, value: Any) -> dict[str, Any]:
    """One ``measurements[]`` entry in the shared output shape (task brief hard constraints)."""
    return {"name": name, "value": value}
