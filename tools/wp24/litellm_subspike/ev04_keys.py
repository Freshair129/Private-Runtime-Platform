#!/usr/bin/env python3
"""EV04 key/identity semantics probe for the WP24 LiteLLM sub-spike (candidate B key/proxy layer).

Scope (owner decision 2026-09-20, docs/WP24-EXPERIMENT-PROCEDURE.md section 5 EV04 "LiteLLM
sub-spike", docs/registry/wp24-run-record-template.json scope_decisions.litellm): EV04 steps 1-3
only. Against a *running* LiteLLM proxy this script:

  (a) creates a virtual key with a small budget, a model restriction and an expiry, via the
      documented ``POST /key/generate`` endpoint
      (https://docs.litellm.ai/docs/proxy/virtual_keys#quick-start---generate-a-key);
  (b) attempts to read the key back through every documented management endpoint this script can
      reach without a browser -- ``GET /key/info`` and ``GET /key/list`` -- and records whether
      the plaintext key value ever reappears (never the value itself, only where it reappeared);
  (c) calls the OpenAI-compatible ``GET /v1/models`` with the virtual key to prove it
      authenticates (https://docs.litellm.ai/docs/proxy/model_access#view-available-fallback-models
      -- the same endpoint and Authorization header shape used there to inspect what a key can
      see);
  (d) revokes the key with the documented ``POST /key/delete``
      (https://docs.litellm.ai/docs/proxy/virtual_keys#endpoint-reference-spec points at the
      Swagger reference for the full key-management surface; ``POST /key/delete`` and its
      ``KeyRequest`` body -- ``{"keys": [<key>]}`` -- are listed there, confirmed against the live
      spec served from that same Swagger UI at https://litellm-api.up.railway.app/openapi.json on
      2026-09-20) and then polls ``GET /v1/models`` with the revoked key every 200 ms for up to
      30 s to measure how long revocation takes to become effective;
  (e) writes one JSON result file shaped as ``measurements`` / ``observations`` / ``artifacts``
      plus ISO-8601 UTC timestamps and the redacted command line (task brief hard constraints).

Why (b) checks exactly ``token`` and not just "the key field":
docs.litellm.ai/docs/proxy/virtual_keys "Overwrite outgoing user with the key hash" says a virtual
key's sha256 token hash is "the same value stored as user_api_key_hash in spend logs" -- i.e. the
*hash* is what LiteLLM calls the key's identity internally. But the same page's own "Key Spend"
example response for ``GET /key/info`` shows a field literally named ``token`` holding a value
shaped like the plaintext key (``"token": "sk-tXL0wt5-lOOVK9sfY2UacA"``), and the live OpenAPI
schema for ``GenerateKeyResponse`` and ``UserAPIKeyAuth`` both have a ``token`` field typed as a
plain string with no documented guarantee of which representation (plaintext vs. hash) it holds.
That mismatch between the "hash is the identity" statement and the "token" field's own example is
exactly the FR-005 question WP24 must answer by running the proxy, not by reading the docs further
-- so this script's readback step treats ``token`` (and ``key``, ``api_key``, ``key_name``) as
unverified and reports what it actually observes.

Never stores or prints the master key, the virtual key, or any Authorization header value. The
generated key lives only in a local variable for the lifetime of this process; every artifact and
the result JSON carry a ``sha256:<first 12 hex>`` fingerprint instead (see _common.py).

Usage:
  PYTHONUTF8=1 python tools/wp24/litellm_subspike/ev04_keys.py \\
      --base-url http://127.0.0.1:4000 --master-key-env LITELLM_MASTER_KEY --out DIR

Requires the LiteLLM master key in the environment variable named by --master-key-env (default
LITELLM_MASTER_KEY) -- never pass the key value itself on the command line. Standard library only:
urllib.request, json, time, argparse, re (via _common).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    find_plaintext_locations,
    fingerprint,
    measurement,
    poll_until,
    redact_argv,
    redact_mapping,
    utc_now_iso,
)

DEFAULT_TIMEOUT_S = 15.0
POLL_INTERVAL_S = 0.2
POLL_TIMEOUT_S = 30.0


class HttpResult:
    """One HTTP call's outcome: status code, elapsed ms, parsed JSON body (or raw text)."""

    def __init__(self, status: int, elapsed_ms: float, body: Any, headers: dict[str, str]) -> None:
        self.status = status
        self.elapsed_ms = elapsed_ms
        self.body = body
        self.headers = headers


def http_call(
    method: str,
    url: str,
    *,
    bearer: str | None = None,
    json_body: dict[str, Any] | None = None,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> HttpResult:
    data = json.dumps(json_body).encode("utf-8") if json_body is not None else None
    headers = {"Content-Type": "application/json"}
    if bearer is not None:
        headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read()
            status = resp.status
            resp_headers = dict(resp.headers.items())
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
        resp_headers = dict(exc.headers.items()) if exc.headers else {}
    except urllib.error.URLError as exc:
        elapsed_ms = (time.monotonic() - start) * 1000
        return HttpResult(0, elapsed_ms, {"error": str(exc.reason)}, {})
    elapsed_ms = (time.monotonic() - start) * 1000
    try:
        body: Any = json.loads(raw.decode("utf-8")) if raw else {}
    except json.JSONDecodeError:
        body = {"raw_text_len": len(raw)}
    return HttpResult(status, elapsed_ms, body, resp_headers)


def generate_key(base_url: str, master_key: str, models: list[str], key_alias: str) -> HttpResult:
    # POST /key/generate:
    # https://docs.litellm.ai/docs/proxy/virtual_keys#quick-start---generate-a-key
    # duration format ("Xm"/"Xh"/"Xd") and max_budget/models fields:
    # https://docs.litellm.ai/docs/proxy/virtual_keys#scheduled-key-rotations
    # https://docs.litellm.ai/docs/proxy/model_access#restrict-models-by-virtual-key
    body = {
        "models": models,
        "max_budget": 0.01,
        "duration": "10m",
        "key_alias": key_alias,
        "metadata": {"purpose": "WP24-litellm-subspike-EV04"},
    }
    return http_call("POST", f"{base_url}/key/generate", bearer=master_key, json_body=body)


def readback_attempts(
    base_url: str, master_key: str, plaintext_key: str, key_alias: str
) -> list[dict[str, Any]]:
    attempts: list[dict[str, Any]] = []

    # GET /key/info?key=<key>: https://docs.litellm.ai/docs/proxy/virtual_keys#key-spend
    info = http_call("GET", f"{base_url}/key/info?key={plaintext_key}", bearer=master_key)
    hits = find_plaintext_locations(info.body, plaintext_key) if isinstance(info.body, dict) else []
    attempts.append(
        {
            "endpoint": "GET /key/info",
            "doc_url": "https://docs.litellm.ai/docs/proxy/virtual_keys#key-spend",
            "status": info.status,
            "plaintext_reappeared": bool(hits),
            "plaintext_locations": hits,
            "redacted_body": redact_mapping(info.body, plaintext_key),
        }
    )

    # GET /key/list?key_alias=<alias>&return_full_object=true : live OpenAPI spec
    # (https://litellm-api.up.railway.app/openapi.json, reached from the "API REFERENCE DOCS" link
    # on https://docs.litellm.ai/docs/proxy/virtual_keys#endpoint-reference-spec);
    # return_full_object is a documented query parameter of GET /key/list on that spec.
    listing = http_call(
        "GET",
        f"{base_url}/key/list?key_alias={key_alias}&return_full_object=true",
        bearer=master_key,
    )
    hits2 = (
        find_plaintext_locations(listing.body, plaintext_key)
        if isinstance(listing.body, dict)
        else []
    )
    attempts.append(
        {
            "endpoint": "GET /key/list",
            "doc_url": "https://docs.litellm.ai/docs/proxy/virtual_keys#endpoint-reference-spec",
            "status": listing.status,
            "plaintext_reappeared": bool(hits2),
            "plaintext_locations": hits2,
            "redacted_body": redact_mapping(listing.body, plaintext_key),
        }
    )
    return attempts


def call_v1_models(base_url: str, key: str) -> HttpResult:
    # GET /v1/models with Authorization: Bearer <key> :
    # https://docs.litellm.ai/docs/proxy/model_access#view-available-fallback-models
    return http_call("GET", f"{base_url}/v1/models", bearer=key)


def revoke_key(base_url: str, master_key: str, plaintext_key: str) -> HttpResult:
    # POST /key/delete, KeyRequest body {"keys": [<key>]} :
    # https://docs.litellm.ai/docs/proxy/virtual_keys#endpoint-reference-spec (Swagger reference);
    # confirmed against the live spec at https://litellm-api.up.railway.app/openapi.json (path
    # "/key/delete", requestBody schema "KeyRequest" with a "keys" array field) on 2026-09-20.
    return http_call(
        "POST", f"{base_url}/key/delete", bearer=master_key, json_body={"keys": [plaintext_key]}
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--base-url", required=True, help="LiteLLM proxy base URL, e.g. http://127.0.0.1:4000"
    )
    parser.add_argument(
        "--master-key-env",
        default="LITELLM_MASTER_KEY",
        help="Name of the env var holding the LiteLLM master key (never the value itself)",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=["wp24-litellm-subspike-host-a"],
        help="Model alias(es) to restrict the key to (litellm_config.template.yaml model_name)",
    )
    parser.add_argument(
        "--key-alias", default="wp24-litellm-subspike-ev04", help="key_alias for the generated key"
    )
    parser.add_argument("--out", required=True, help="Output directory for the result JSON")
    args = parser.parse_args(argv)

    raw_argv = argv if argv is not None else sys.argv[1:]
    started_at = utc_now_iso()

    master_key = os.environ.get(args.master_key_env)
    if not master_key:
        print(f"error: environment variable {args.master_key_env} is not set", file=sys.stderr)
        return 2

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    measurements: list[dict[str, Any]] = []
    observations: list[str] = []
    artifacts: list[str] = []

    # (a) generate
    gen = generate_key(args.base_url, master_key, args.models, args.key_alias)
    gen_redacted = redact_mapping(gen.body)
    (out_dir / "ev04_key_generate.redacted.json").write_text(
        json.dumps(gen_redacted, indent=2, sort_keys=True), encoding="utf-8"
    )
    artifacts.append("ev04_key_generate.redacted.json")
    measurements.append(measurement("key_generate_status", gen.status))
    measurements.append(measurement("key_generate_latency_ms", round(gen.elapsed_ms, 1)))

    plaintext_key = (
        gen.body.get("key") if gen.status == 200 and isinstance(gen.body, dict) else None
    )
    if not plaintext_key:
        observations.append(
            "POST /key/generate did not return status 200 with a 'key' field; readback, "
            "/v1/models and revoke steps skipped. See ev04_key_generate.redacted.json for the "
            "(redacted) response."
        )
        result = {
            "kind": "WP24_EV04_KEYS_RESULT",
            "started_at": started_at,
            "finished_at": utc_now_iso(),
            "base_url": args.base_url,
            "command_line": redact_argv(raw_argv),
            "measurements": measurements,
            "observations": observations,
            "artifacts": artifacts,
        }
        (out_dir / "ev04_keys.result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
        )
        return 1

    key_fp = fingerprint(plaintext_key)
    observations.append(f"Generated virtual key fingerprint {key_fp} (key_alias={args.key_alias}).")

    # (b) readback
    attempts = readback_attempts(args.base_url, master_key, plaintext_key, args.key_alias)
    (out_dir / "ev04_readback_attempts.redacted.json").write_text(
        json.dumps(attempts, indent=2, sort_keys=True), encoding="utf-8"
    )
    artifacts.append("ev04_readback_attempts.redacted.json")
    any_reappeared = any(a["plaintext_reappeared"] for a in attempts)
    measurements.append(measurement("plaintext_reappeared_any_channel", any_reappeared))
    for a in attempts:
        loc = ", ".join(a["plaintext_locations"]) if a["plaintext_locations"] else "none"
        observations.append(
            f"{a['endpoint']} (status {a['status']}): "
            f"plaintext reappeared={a['plaintext_reappeared']} at [{loc}]. Doc: {a['doc_url']}"
        )
    if any_reappeared:
        observations.append(
            "FR-005 gate: plaintext reappeared through at least one management endpoint after "
            "issuance -> FAIL per WP24-EXPERIMENT-PROCEDURE.md section 5 EV04 criteria ('FR-005 "
            "FAIL ทันทีถ้า key อ่านกลับได้หลังออก')."
        )
    else:
        observations.append(
            "No plaintext reappeared through GET /key/info or GET /key/list in this run. This "
            "does not clear FR-005 by itself: docs/evidence/wp24/<record_id>/B/EV04/ must also "
            "record the manual checks in ev04_readback_checklist.md (DB table, proxy logs, config "
            "dump, Admin UI) before the gate can be marked PASS."
        )

    # (c) /v1/models with the virtual key
    models_call = call_v1_models(args.base_url, plaintext_key)
    measurements.append(measurement("v1_models_with_virtual_key_status", models_call.status))
    measurements.append(
        measurement("v1_models_with_virtual_key_latency_ms", round(models_call.elapsed_ms, 1))
    )
    observations.append(
        f"GET /v1/models with the newly generated virtual key returned status "
        f"{models_call.status} (expected 200 to prove the key authenticates)."
    )

    # (d) revoke, then poll /v1/models until rejected
    revoke = revoke_key(args.base_url, master_key, plaintext_key)
    revoke_redacted = redact_mapping(revoke.body, plaintext_key)
    (out_dir / "ev04_key_delete.redacted.json").write_text(
        json.dumps(revoke_redacted, indent=2, sort_keys=True), encoding="utf-8"
    )
    artifacts.append("ev04_key_delete.redacted.json")
    measurements.append(measurement("key_delete_status", revoke.status))
    observations.append(f"POST /key/delete returned status {revoke.status}.")

    def still_accepted() -> bool:
        r = call_v1_models(args.base_url, plaintext_key)
        return r.status != 200

    poll_result = poll_until(
        still_accepted,
        interval_s=POLL_INTERVAL_S,
        timeout_s=POLL_TIMEOUT_S,
        clock=time.monotonic,
        sleep=time.sleep,
    )
    measurements.append(measurement("revoke_rejected_within_timeout", poll_result["rejected"]))
    measurements.append(
        measurement("revoke_to_rejected_seconds", round(poll_result["elapsed_seconds"], 3))
    )
    measurements.append(measurement("revoke_poll_attempts", poll_result["attempts"]))
    if poll_result["rejected"]:
        observations.append(
            f"Revoked key stopped being accepted by GET /v1/models after "
            f"{poll_result['elapsed_seconds']:.3f}s ({poll_result['attempts']} polls at "
            f"{POLL_INTERVAL_S}s intervals)."
        )
    else:
        observations.append(
            f"Revoked key was STILL accepted by GET /v1/models after the {POLL_TIMEOUT_S}s poll "
            f"budget ({poll_result['attempts']} polls). Record this as a candidate-B gap for "
            "NFR/FR-005 revoke timing, not as BLOCKED."
        )

    result = {
        "kind": "WP24_EV04_KEYS_RESULT",
        "started_at": started_at,
        "finished_at": utc_now_iso(),
        "base_url": args.base_url,
        "key_alias": args.key_alias,
        "key_fingerprint": key_fp,
        "command_line": redact_argv(raw_argv),
        "measurements": measurements,
        "observations": observations,
        "artifacts": artifacts,
    }
    (out_dir / "ev04_keys.result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    artifacts_msg = ", ".join(artifacts)
    print(f"Wrote ev04_keys.result.json and artifacts ({artifacts_msg}) to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
