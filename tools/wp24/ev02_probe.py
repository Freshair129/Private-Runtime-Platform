#!/usr/bin/env python3
"""Probe a candidate's runtime endpoints for WP24 EV02 (docs/WP24-EXPERIMENT-PROCEDURE.md, gate
PRP-FR-010..015).

Run from the control machine against a runtime already launched on host A or B. For every
configured endpoint this performs the request twice — once with no credential and once with the
bearer token read from the environment variable named by --token-env, if it is set — and records
status code, whether a WWW-Authenticate (or equivalent) challenge header is present, response
size, latency, and a redacted JSON body sample capped at 4 KB. Model IDs/revisions and anything
that looks like a GPU UUID, worker identifier, or restart epoch are extracted heuristically from
the body so the operator can compare them before/after a restart with ev02_restart_identity.py.

Endpoint defaults and their documentation citations:

Candidate B (vLLM OpenAI-compatible server):
  GET /v1/models  -- https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/
  GET /metrics    -- https://docs.vllm.ai/en/latest/usage/metrics.html
                     (Prometheus text; NOT covered by --api-key per
                     https://docs.vllm.ai/en/latest/usage/security/, which states --api-key only
                     authenticates the /v1, /v2, /inference and /cohere path prefixes)

Candidate A (Xinference REST API):
  GET /v1/models                       -- https://inference.readthedocs.io/en/latest/getting_started/using_xinference.html
  GET /v1/model_registrations/LLM      -- https://inference.readthedocs.io/en/latest/getting_started/using_xinference.html
  GET /v1/workers                      -- https://inference.readthedocs.io/en/stable/_modules/xinference/client/restful/restful_client.html
                                           (confirmed from the shipped client source; the narrative
                                           docs page above does not enumerate this path)
  GET /v1/supervisor                   -- same source as /v1/workers, same caveat
  GET /v1/cluster/auth                 -- same source as /v1/workers, same caveat
  GET /v1/admin/setup/status           -- https://inference.readthedocs.io/en/latest/user_guide/auth_system.html
                                           (documented as unauthenticated by design: bootstrap)

An endpoint list not confirmed against vendor documentation must be supplied via --endpoints and is
marked unverified in the output rather than assumed. This script computes no PASS/FAIL/BLOCKED
verdict; docs/WP24-EXPERIMENT-PROCEDURE.md section 3 item 4 reserves that for the reviewer.
Standard library only; credentials are read only from the environment and never printed —
Authorization is always logged as "Authorization: <redacted>".

Usage:
  python tools/wp24/ev02_probe.py --candidate B --base-url http://10.0.0.2:8000 --host-id B \\
      --token-env WP24_RUNTIME_TOKEN --out wp24-out
  python tools/wp24/ev02_probe.py --candidate A --base-url http://10.0.0.1:9997 --host-id A \\
      --endpoints endpoints.json --out wp24-out
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

import wp24_common as common

READ_CAP_BYTES = 65536
BODY_SAMPLE_CAP_BYTES = 4096

DEFAULT_ENDPOINTS_B: list[dict[str, Any]] = [
    {
        "name": "list_models",
        "method": "GET",
        "path": "/v1/models",
        "doc_url": "https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/",
        "verified": True,
    },
    {
        "name": "metrics",
        "method": "GET",
        "path": "/metrics",
        "doc_url": "https://docs.vllm.ai/en/latest/usage/metrics.html",
        "verified": True,
        "note": "Prometheus text, not JSON; not covered by --api-key per https://docs.vllm.ai/en/latest/usage/security/",
    },
]

DEFAULT_ENDPOINTS_A: list[dict[str, Any]] = [
    {
        "name": "list_running_models",
        "method": "GET",
        "path": "/v1/models",
        "doc_url": "https://inference.readthedocs.io/en/latest/getting_started/using_xinference.html",
        "verified": True,
    },
    {
        "name": "list_model_registrations_llm",
        "method": "GET",
        "path": "/v1/model_registrations/LLM",
        "doc_url": "https://inference.readthedocs.io/en/latest/getting_started/using_xinference.html",
        "verified": True,
    },
    {
        "name": "workers_info",
        "method": "GET",
        "path": "/v1/workers",
        "doc_url": "https://inference.readthedocs.io/en/stable/_modules/xinference/client/restful/restful_client.html",
        "verified": True,
        "note": "confirmed from the shipped client source, not the narrative docs page",
    },
    {
        "name": "supervisor_info",
        "method": "GET",
        "path": "/v1/supervisor",
        "doc_url": "https://inference.readthedocs.io/en/stable/_modules/xinference/client/restful/restful_client.html",
        "verified": True,
        "note": "confirmed from the shipped client source, not the narrative docs page",
    },
    {
        "name": "cluster_auth",
        "method": "GET",
        "path": "/v1/cluster/auth",
        "doc_url": "https://inference.readthedocs.io/en/stable/_modules/xinference/client/restful/restful_client.html",
        "verified": True,
        "note": "confirmed from the shipped client source, not the narrative docs page",
    },
    {
        "name": "admin_setup_status",
        "method": "GET",
        "path": "/v1/admin/setup/status",
        "doc_url": "https://inference.readthedocs.io/en/latest/user_guide/auth_system.html",
        "verified": True,
        "note": "documented as unauthenticated by design (bootstrap status check)",
    },
]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--candidate", required=True, choices=["A", "B"])
    parser.add_argument("--base-url", required=True, help="e.g. http://10.0.0.2:8000")
    parser.add_argument(
        "--token-env",
        default=None,
        help="name of an env var holding a bearer token; never pass the token itself",
    )
    parser.add_argument(
        "--endpoints", default=None, help="path to a JSON file overriding the default endpoint list"
    )
    parser.add_argument(
        "--host-id", required=True, help="A or B: which GPU host base-url points at"
    )
    parser.add_argument(
        "--out", default="./wp24-out", help="output directory (default: ./wp24-out)"
    )
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    return parser.parse_args(argv)


def load_endpoints(
    candidate: str, endpoints_file: str | None, observations: list[str]
) -> list[dict[str, Any]]:
    if endpoints_file is None:
        return DEFAULT_ENDPOINTS_A if candidate == "A" else DEFAULT_ENDPOINTS_B
    data = json.loads(Path(endpoints_file).read_text(encoding="utf-8"))
    normalized: list[dict[str, Any]] = []
    for item in data.get("endpoints", []):
        entry: dict[str, Any] = {
            "name": item["name"],
            "method": item.get("method", "GET").upper(),
            "path": item["path"],
        }
        if item.get("doc_url"):
            entry["doc_url"] = item["doc_url"]
            entry["verified"] = bool(item.get("verified", True))
            if item.get("note"):
                entry["note"] = item["note"]
        else:
            entry["doc_url"] = None
            entry["verified"] = False
            entry["note"] = (
                "operator-provided via --endpoints; unverified, to be observed at run time"
            )
            observations.append(f"{entry['name']}: {entry['note']}")
        normalized.append(entry)
    return normalized


def perform_request(
    url: str, method: str, headers: dict[str, str], timeout_seconds: float
) -> dict[str, Any]:
    request = urllib.request.Request(url, method=method, headers=headers)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read(READ_CAP_BYTES)
            return {
                "status_code": response.status,
                "response_headers": dict(response.headers.items()),
                "body_bytes": body,
                "elapsed_ms": (time.perf_counter() - start) * 1000,
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read(READ_CAP_BYTES) if exc.fp else b""
        return {
            "status_code": exc.code,
            "response_headers": dict(exc.headers.items()) if exc.headers else {},
            "body_bytes": body,
            "elapsed_ms": (time.perf_counter() - start) * 1000,
            "error": None,
        }
    except urllib.error.URLError as exc:
        return {
            "status_code": None,
            "response_headers": {},
            "body_bytes": b"",
            "elapsed_ms": (time.perf_counter() - start) * 1000,
            "error": str(exc.reason),
        }
    except OSError as exc:
        return {
            "status_code": None,
            "response_headers": {},
            "body_bytes": b"",
            "elapsed_ms": (time.perf_counter() - start) * 1000,
            "error": str(exc),
        }


def process_variant(
    url: str, method: str, headers: dict[str, str], timeout_seconds: float
) -> dict[str, Any]:
    result = perform_request(url, method, headers, timeout_seconds)
    body_bytes: bytes = result["body_bytes"]
    body_text = body_bytes.decode("utf-8", errors="replace")
    parsed: Any = None
    try:
        parsed = json.loads(body_text)
    except (json.JSONDecodeError, ValueError):
        parsed = None
    response_headers: dict[str, str] = result["response_headers"]
    www_authenticate_present = any(key.lower() == "www-authenticate" for key in response_headers)
    content_length = response_headers.get("Content-Length") or response_headers.get(
        "content-length"
    )
    response_size = (
        int(content_length) if content_length and content_length.isdigit() else len(body_bytes)
    )
    return {
        "status_code": result["status_code"],
        "error": result["error"],
        "www_authenticate_present": www_authenticate_present,
        "response_size_bytes": response_size,
        "latency_ms": round(result["elapsed_ms"], 2),
        "body_sample": common.redact_text(body_text[:BODY_SAMPLE_CAP_BYTES]),
        "identifiers": common.extract_candidate_identifiers(parsed) if parsed is not None else {},
        "request_headers_sent": common.redacted_header_lines(headers),
    }


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    observations: list[str] = []
    measurements: list[dict[str, Any]] = []
    endpoints = load_endpoints(args.candidate, args.endpoints, observations)

    token_available = bool(args.token_env and os.environ.get(args.token_env))
    if not args.token_env:
        observations.append(
            "--token-env not provided; every endpoint was probed without credential only"
        )
    elif not token_available:
        observations.append(
            f"env var {args.token_env} is not set or empty; every endpoint probed "
            "without credential only"
        )

    results: list[dict[str, Any]] = []
    extracted_identifiers: dict[str, str] = {}
    saw_gpu_uuid = False

    for endpoint in endpoints:
        url = args.base_url.rstrip("/") + endpoint["path"]
        variants: dict[str, dict[str, Any]] = {
            "no_credential": process_variant(url, endpoint["method"], {}, args.timeout_seconds)
        }
        if token_available:
            auth_headers = {"Authorization": f"Bearer {os.environ[args.token_env]}"}
            variants["with_credential"] = process_variant(
                url, endpoint["method"], auth_headers, args.timeout_seconds
            )

        for variant_name, variant in variants.items():
            prefix = f"{endpoint['name']}.{variant_name}"
            measurements.append({"name": f"{prefix}.status_code", "value": variant["status_code"]})
            measurements.append({"name": f"{prefix}.latency_ms", "value": variant["latency_ms"]})
            measurements.append(
                {"name": f"{prefix}.response_size_bytes", "value": variant["response_size_bytes"]}
            )
            if variant["status_code"] in (401, 403) and not variant["www_authenticate_present"]:
                observations.append(
                    f"{prefix}: returned {variant['status_code']} without a WWW-Authenticate "
                    "(or equivalent) challenge header"
                )
            if variant["error"]:
                observations.append(
                    f"{prefix}: request error: {common.redact_text(variant['error'])}"
                )
            for identifier_path, identifier_value in variant["identifiers"].items():
                extracted_identifiers[f"{prefix}.{identifier_path}"] = identifier_value
                if common.looks_like_gpu_uuid(identifier_value):
                    saw_gpu_uuid = True

        if endpoint.get("note") and endpoint.get("verified", True):
            observations.append(f"{endpoint['name']}: {endpoint['note']}")
        results.append({"endpoint": endpoint, "variants": variants})

    if not saw_gpu_uuid:
        observations.append(
            "no probed endpoint's response exposed a physical GPU UUID mapping; per "
            "WP24-EXPERIMENT-PROCEDURE.md EV02 step 2 this absence is itself a finding for the "
            "reviewer, not an error of this tool"
        )

    timestamp = common.utc_now_iso().replace(":", "").replace("-", "")
    filename = f"ev02_probe_{args.candidate}_{args.host_id}_{timestamp}.json"
    payload = {
        "kind": "WP24_EV02_PROBE",
        "generated_at_utc": common.utc_now_iso(),
        "command_line": common.command_line(),
        "candidate": args.candidate,
        "host_id": args.host_id,
        "base_url": args.base_url,
        "results": results,
        "extracted_identifiers": extracted_identifiers,
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
