#!/usr/bin/env python3
"""EV03 target-binding probe for the WP24 LiteLLM sub-spike (candidate B key/proxy layer).

Scope (owner decision 2026-09-20, docs/WP24-EXPERIMENT-PROCEDURE.md section 5 EV03 "LiteLLM
sub-spike" paragraph -- "ส่วนของ LiteLLM ในข้อ 2-4 รันเฉพาะภายใน sub-spike ที่กำหนดใน EV04 (time box
ร่วมกัน)"): this script covers EV03 steps 2-4 with retry/fallback/routing switched off per
litellm_config.template.yaml -- it sends N requests to one model alias and records, per request,
which physical deployment answered, so the operator can see whether every request actually reached
the host it was addressed to.

Against a running proxy configured from litellm_config.template.yaml (retries, fallbacks, cooldowns
and weighted failover all disabled), this script:

  - sends --count requests (default 5) to POST /v1/chat/completions with a fixed small prompt
    against one model alias (--alias, one of the two model_name values in
    litellm_config.template.yaml);
  - reads, per response, the headers LiteLLM's own docs say identify which deployment served the
    request: ``x-litellm-model-id`` (the deployment's model_info.id), ``x-litellm-model-api-base``
    (the upstream base URL) and ``x-litellm-model-group`` (the model_name/alias routed to) --
    https://docs.litellm.ai/docs/proxy/response_headers#litellm-specific-headers -- plus the
    retry/fallback accounting headers ``x-litellm-attempted-retries``,
    ``x-litellm-attempted-fallbacks`` and ``x-litellm-max-fallbacks`` from the same page ("Retry,
    Fallback Headers");
  - if none of those headers are present on a response (older/different proxy build), records the
    raw response headers instead (Authorization-shaped values redacted) and says so in
    observations, rather than guessing;
  - accepts --expect-deployment so the operator can name which x-litellm-model-id or
    x-litellm-model-api-base value they expect (e.g. the host-A model_info.id from
    litellm_config.template.yaml) and get a mismatch flagged per request;
  - accepts --mode {normal,stalled,down} purely as a label recorded in the output. Actually
    throttling or stopping host A between runs is a MANUAL step the operator performs outside this
    script -- see README.md "EV03 --mode" for the exact manual procedure; this flag only tags which
    manual condition was in effect while this run's requests were sent.

Never stores or prints the virtual key or any Authorization header value; the key is read from the
environment variable named by --key-env and used only in-memory.

Usage:
  PYTHONUTF8=1 python tools/wp24/litellm_subspike/ev03_retry_probe.py \\
      --base-url http://127.0.0.1:4000 --key-env WP24_LITELLM_VIRTUAL_KEY \\
      --alias wp24-litellm-subspike-host-a --count 5 --mode normal --out DIR

Standard library only: urllib.request, json, time, argparse, re (via _common).
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
from _common import measurement, redact_argv, redact_mapping, utc_now_iso  # noqa: E402

# Documented per https://docs.litellm.ai/docs/proxy/response_headers#litellm-specific-headers and
# "Retry, Fallback Headers" on the same page.
DEPLOYMENT_HEADERS = ("x-litellm-model-id", "x-litellm-model-api-base", "x-litellm-model-group")
RETRY_HEADERS = (
    "x-litellm-attempted-retries",
    "x-litellm-attempted-fallbacks",
    "x-litellm-max-fallbacks",
)
_REDACT_HEADER_PREFIXES = ("authorization", "x-litellm-api-key", "cookie")


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    return {
        k: ("<redacted>" if k.lower().startswith(_REDACT_HEADER_PREFIXES) else v)
        for k, v in headers.items()
    }


def send_one(
    base_url: str, key: str, alias: str, prompt: str, timeout_s: float = 30.0
) -> dict[str, Any]:
    body = {
        "model": alias,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1,
        # Per-request disable, belt and suspenders on top of the config-level settings:
        # https://docs.litellm.ai/docs/proxy/reliability#disable-fallbacks-per-requestkey
        "disable_fallbacks": True,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            status = resp.status
            headers = dict(resp.headers.items())
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        headers = dict(exc.headers.items()) if exc.headers else {}
        raw = exc.read()
    except urllib.error.URLError as exc:
        elapsed_ms = (time.monotonic() - start) * 1000
        return {
            "status": 0,
            "latency_ms": round(elapsed_ms, 1),
            "error": str(exc.reason),
            "deployment_headers": {},
            "retry_headers": {},
            "raw_headers": {},
        }
    elapsed_ms = (time.monotonic() - start) * 1000
    try:
        body_json = json.loads(raw.decode("utf-8")) if raw else {}
    except json.JSONDecodeError:
        body_json = {"raw_text_len": len(raw)}
    lower_headers = {k.lower(): v for k, v in headers.items()}
    deployment_headers = {h: lower_headers[h] for h in DEPLOYMENT_HEADERS if h in lower_headers}
    retry_headers = {h: lower_headers[h] for h in RETRY_HEADERS if h in lower_headers}
    return {
        "status": status,
        "latency_ms": round(elapsed_ms, 1),
        "deployment_headers": deployment_headers,
        "retry_headers": retry_headers,
        "raw_headers": redact_headers(headers) if not deployment_headers else {},
        "response_model_field": body_json.get("model") if isinstance(body_json, dict) else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--base-url", required=True, help="LiteLLM proxy base URL, e.g. http://127.0.0.1:4000"
    )
    parser.add_argument(
        "--key-env",
        required=True,
        help="Name of the env var holding a LiteLLM virtual key (never the value itself)",
    )
    parser.add_argument(
        "--alias", required=True, help="model_name alias to call, e.g. wp24-litellm-subspike-host-a"
    )
    parser.add_argument(
        "--count", type=int, default=5, help="Number of requests to send (default 5)"
    )
    parser.add_argument(
        "--prompt", default="Reply with the single word: ack.", help="Fixed small prompt"
    )
    parser.add_argument(
        "--expect-deployment",
        default=None,
        help="Expected x-litellm-model-id or x-litellm-model-api-base value; flags mismatches",
    )
    parser.add_argument(
        "--mode",
        choices=["normal", "stalled", "down"],
        default="normal",
        help="Label for the manual host-A condition during this run (see README.md); not automated",
    )
    parser.add_argument("--out", required=True, help="Output directory for the result JSON")
    args = parser.parse_args(argv)

    raw_argv = argv if argv is not None else sys.argv[1:]
    started_at = utc_now_iso()

    key = os.environ.get(args.key_env)
    if not key:
        print(f"error: environment variable {args.key_env} is not set", file=sys.stderr)
        return 2

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    per_request: list[dict[str, Any]] = []
    for i in range(args.count):
        r = send_one(args.base_url, key, args.alias, args.prompt)
        r["request_index"] = i
        if args.expect_deployment is not None:
            seen = set(r["deployment_headers"].values())
            r["deployment_mismatch"] = bool(seen) and args.expect_deployment not in seen
        per_request.append(r)

    (out_dir / "ev03_retry_probe.requests.json").write_text(
        json.dumps(redact_mapping(per_request), indent=2, sort_keys=True), encoding="utf-8"
    )

    statuses = [r["status"] for r in per_request]
    success_count = sum(1 for s in statuses if s == 200)
    deployment_ids_seen = sorted(
        {
            r["deployment_headers"]["x-litellm-model-id"]
            for r in per_request
            if "x-litellm-model-id" in r["deployment_headers"]
        }
    )
    latencies = [r["latency_ms"] for r in per_request]

    measurements = [
        measurement("request_count", args.count),
        measurement("success_count", success_count),
        measurement("distinct_x_litellm_model_id_seen", len(deployment_ids_seen)),
        measurement("latency_ms_min", min(latencies) if latencies else None),
        measurement("latency_ms_max", max(latencies) if latencies else None),
    ]
    if args.expect_deployment is not None:
        mismatches = sum(1 for r in per_request if r.get("deployment_mismatch"))
        measurements.append(measurement("expect_deployment_mismatch_count", mismatches))

    observations: list[str] = [
        f"Sent {args.count} request(s) to alias '{args.alias}' in --mode {args.mode} (manual "
        "host-A condition; see README.md EV03 section for what this mode means operationally).",
    ]
    if deployment_ids_seen:
        observations.append(
            "x-litellm-model-id values observed: "
            + ", ".join(deployment_ids_seen)
            + ". https://docs.litellm.ai/docs/proxy/response_headers#litellm-specific-headers"
        )
        if len(deployment_ids_seen) > 1:
            observations.append(
                "More than one deployment id answered this single-alias run; with "
                "retries/fallbacks/weighted-failover disabled in litellm_config.template.yaml this "
                "should not happen. Record as an EV03 gate finding, not as an environment error, "
                "unless independently explained (e.g. operator changed --alias mid-run)."
            )
    else:
        observations.append(
            "No response carried the documented x-litellm-model-id / x-litellm-model-api-base / "
            "x-litellm-model-group headers (https://docs.litellm.ai/docs/proxy/response_headers). "
            "Raw response headers were recorded per request (Authorization-shaped values redacted) "
            "in ev03_retry_probe.requests.json instead; unverified which proxy build/version this "
            "is -- observe at run time."
        )
    if success_count < args.count:
        observations.append(
            f"{args.count - success_count} of {args.count} request(s) did not return status 200."
        )

    result = {
        "kind": "WP24_EV03_RETRY_PROBE_RESULT",
        "started_at": started_at,
        "finished_at": utc_now_iso(),
        "base_url": args.base_url,
        "alias": args.alias,
        "mode": args.mode,
        "expect_deployment": args.expect_deployment,
        "command_line": redact_argv(raw_argv),
        "measurements": measurements,
        "observations": observations,
        "artifacts": ["ev03_retry_probe.requests.json"],
    }
    (out_dir / "ev03_retry_probe.result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"Wrote ev03_retry_probe.result.json and ev03_retry_probe.requests.json to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
