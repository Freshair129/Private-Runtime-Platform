#!/usr/bin/env python3
"""EV05 atomic multi-process load probe for WP24 candidate B (vLLM), steps 2-3.

Design: docs/evidence/wp24/WP24-2026-09-20-run1/B/EV05/test-design.md (approved 2026-09-22).
Procedure: docs/WP24-EXPERIMENT-PROCEDURE.md EV05 (gate PRP-FR-017 / PRP-FR-018).

Against a running vLLM OpenAI-compatible server (called directly, never through LiteLLM), this
script:

  - starts --processes OS processes, each opening --per-process concurrent streaming
    POST /v1/chat/completions requests of identical length (max_tokens + ignore_eos), released
    together by one shared start event;
  - records per request, client side: send time, first-token time, done time, HTTP status and the
    number of content chunks received;
  - polls GET /metrics every --poll-interval seconds for vllm:num_requests_running and
    vllm:num_requests_waiting, recording the window [t0, t1] each scrape took;
  - rebuilds, for every scrape window, the client-side bounds on requests that could have been
    inside the server, and reports where the metric exceeded them (over-count) or exceeded --limit;
  - for step 3, looks for max_num_seqs in /metrics, /v1/models, /version and (with --container)
    the container's startup log, and records where it was found.

No verdict is computed (docs/WP24-EXPERIMENT-PROCEDURE.md section 3 item 4). The API key is read
from the environment variable named by --token-env and never printed or written.

Usage:
  python tools/wp24/ev05_admission_load.py --base-url http://127.0.0.1:8000
      --token-env VLLM_API_KEY --model typhoon2.5-qwen3-4b --limit 4
      --processes 3 --per-process 4 --label run-B --container prp-wp24-vllm-b --out DIR

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import wp24_common as common

RUNNING = "vllm:num_requests_running"
WAITING = "vllm:num_requests_waiting"
PROMPT = "เล่าประวัติศาสตร์ของกรุงเทพมหานครอย่างละเอียด"
_SAMPLE_RE = re.compile(r"^([a-zA-Z_:][a-zA-Z0-9_:]*)(\{[^}]*\})?\s+(\S+)")
_MAX_NUM_SEQS_RE = re.compile(r"max_num_seqs\W{0,3}(\d+)")


# --- pure functions (unit tested) -------------------------------------------------------------


def parse_prometheus(text: str) -> dict[str, float]:
    """Sum every sample of each metric name in Prometheus text format, across all label sets.

    Comment lines and unparsable values are skipped. Summing is right for the two gauges this
    script reads: one vLLM server exposes one series per served model.
    """
    totals: dict[str, float] = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        match = _SAMPLE_RE.match(line.strip())
        if not match:
            continue
        try:
            value = float(match.group(3))
        except ValueError:
            continue
        totals[match.group(1)] = totals.get(match.group(1), 0.0) + value
    return totals


def client_bounds(requests: list[dict[str, Any]], t0: float, t1: float) -> dict[str, int]:
    """Client-side bounds on requests inside the server during the scrape window [t0, t1].

    upper: sent no later than t1 and not finished before t0 (could have been in the server).
    lower: sent before t0 and finished after t1 (must have been in the server throughout).
    streaming_upper: as upper, but counted from the first token instead of the send.
    A request with no done time (failed before any response) counts as done at its send time.
    """
    upper = lower = streaming_upper = 0
    for req in requests:
        sent = req["sent"]
        if sent is None:
            continue
        done = req["done"] if req["done"] is not None else sent
        first = req["first_token"]
        if sent <= t1 and done >= t0:
            upper += 1
        if sent < t0 and done > t1:
            lower += 1
        if first is not None and first <= t1 and done >= t0:
            streaming_upper += 1
    return {"upper": upper, "lower": lower, "streaming_upper": streaming_upper}


def compare(
    samples: list[dict[str, Any]], requests: list[dict[str, Any]], limit: int | None
) -> dict[str, Any]:
    """Compare every scrape with the client bounds; return counts and the offending samples."""
    over_total: list[dict[str, Any]] = []
    over_running: list[dict[str, Any]] = []
    above_limit: list[dict[str, Any]] = []
    under_total = 0
    scored = [s for s in samples if s.get("running") is not None and s.get("waiting") is not None]
    for sample in scored:
        bounds = client_bounds(requests, sample["t0"], sample["t1"])
        total = sample["running"] + sample["waiting"]
        row = {**sample, **bounds}
        if total > bounds["upper"]:
            over_total.append(row)
        if sample["running"] > bounds["upper"]:
            over_running.append(row)
        if total < bounds["lower"]:
            under_total += 1
        if limit is not None and sample["running"] > limit:
            above_limit.append(row)
    return {
        "samples_scored": len(scored),
        "max_running": max((s["running"] for s in scored), default=None),
        "max_waiting": max((s["waiting"] for s in scored), default=None),
        "samples_total_above_client_upper": len(over_total),
        "samples_running_above_client_upper": len(over_running),
        "samples_total_below_client_lower": under_total,
        "samples_running_above_limit": len(above_limit),
        "offending_samples": (over_total + over_running + above_limit)[:20],
    }


def find_max_num_seqs(text: str) -> list[int]:
    """Every integer that follows a ``max_num_seqs`` token in ``text`` (log line, JSON, metrics)."""
    return [int(value) for value in _MAX_NUM_SEQS_RE.findall(text)]


# --- network ------------------------------------------------------------------------------------


def _headers(token: str | None) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get(url: str, token: str | None, timeout: float = 5.0) -> tuple[int | None, str]:
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=_headers(token)), timeout=timeout
        ) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _one_request(base_url: str, token: str | None, body: bytes, record: dict[str, Any]) -> None:
    request = urllib.request.Request(
        f"{base_url}/v1/chat/completions", body, _headers(token), method="POST"
    )
    record["sent"] = time.time()
    try:
        with urllib.request.urlopen(request, timeout=600) as resp:
            record["status"] = resp.status
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:") or line == "data: [DONE]":
                    continue
                try:
                    chunk = json.loads(line[5:])
                except ValueError:
                    continue
                choices = chunk.get("choices") or []
                if choices and (choices[0].get("delta") or {}).get("content"):
                    if record["first_token"] is None:
                        record["first_token"] = time.time()
                    record["chunks"] += 1
                if chunk.get("usage"):
                    record["completion_tokens"] = chunk["usage"].get("completion_tokens")
    except urllib.error.HTTPError as exc:
        record["status"] = exc.code
        record["error"] = exc.read().decode("utf-8", "replace")[:300]
    except (urllib.error.URLError, OSError) as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"[:300]
    record["done"] = time.time()


def _worker(
    process_index: int,
    per_process: int,
    base_url: str,
    token_env: str | None,
    body: bytes,
    start: Any,
    results: Any,
) -> None:
    token = os.environ.get(token_env) if token_env else None
    records = [
        {
            "process": process_index,
            "slot": slot,
            "pid": os.getpid(),
            "sent": None,
            "first_token": None,
            "done": None,
            "status": None,
            "chunks": 0,
            "completion_tokens": None,
            "error": None,
        }
        for slot in range(per_process)
    ]
    threads = [
        threading.Thread(target=_one_request, args=(base_url, token, body, rec)) for rec in records
    ]
    start.wait()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    results.put(records)


def _poll(
    base_url: str,
    token: str | None,
    interval: float,
    stop: threading.Event,
    out: list[dict[str, Any]],
) -> None:
    while not stop.is_set():
        t0 = time.time()
        status, text = _get(f"{base_url}/metrics", token)
        t1 = time.time()
        metrics = parse_prometheus(text) if status == 200 else {}
        out.append(
            {
                "t0": t0,
                "t1": t1,
                "status": status,
                "running": metrics.get(RUNNING),
                "waiting": metrics.get(WAITING),
            }
        )
        stop.wait(max(0.0, interval - (t1 - t0)))


def readback(base_url: str, token: str | None, container: str | None) -> dict[str, Any]:
    """Step 3: where, if anywhere, max_num_seqs can be read from the running server."""
    found: dict[str, Any] = {}
    for path in ("/metrics", "/v1/models", "/version"):
        status, text = _get(f"{base_url}{path}", token)
        found[path] = {"status": status, "max_num_seqs": find_max_num_seqs(text)}
    if container:
        logs = common.run_command(["docker", "logs", container], timeout_seconds=30)
        text = logs["stdout"] + logs["stderr"]
        lines = [line for line in text.splitlines() if "max_num_seqs" in line]
        found[f"docker logs {container}"] = {
            "return_code": logs["return_code"],
            "max_num_seqs": find_max_num_seqs(text),
            "lines": [common.redact_text(line)[:400] for line in lines[:3]],
        }
    return found


# --- main ---------------------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--token-env", default=None, help="NAME of the env var holding the key")
    parser.add_argument("--model", required=True)
    parser.add_argument("--processes", type=int, default=3)
    parser.add_argument("--per-process", type=int, default=4)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--poll-interval", type=float, default=0.25)
    parser.add_argument("--limit", type=int, default=None, help="max_num_seqs the server was given")
    parser.add_argument("--label", default="run")
    parser.add_argument("--container", default=None, help="docker container to read startup log")
    parser.add_argument("--candidate", default="B")
    parser.add_argument("--out", default="wp24-out")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    token = os.environ.get(args.token_env) if args.token_env else None
    body = json.dumps(
        {
            "model": args.model,
            "messages": [{"role": "user", "content": PROMPT}],
            "max_tokens": args.max_tokens,
            "ignore_eos": True,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
    ).encode("utf-8")

    started_at = common.utc_now_iso()
    samples: list[dict[str, Any]] = []
    stop = threading.Event()
    poller = threading.Thread(
        target=_poll, args=(base_url, token, args.poll_interval, stop, samples)
    )
    poller.start()
    time.sleep(1.0)  # idle baseline scrapes before the burst

    start = mp.Event()
    results: Any = mp.Queue()
    procs = [
        mp.Process(
            target=_worker,
            args=(i, args.per_process, base_url, args.token_env, body, start, results),
        )
        for i in range(args.processes)
    ]
    for proc in procs:
        proc.start()
    time.sleep(2.0)  # let every process build its threads before the shared release
    burst_at = time.time()
    start.set()
    requests: list[dict[str, Any]] = []
    for _ in procs:
        requests.extend(results.get())
    for proc in procs:
        proc.join()
    time.sleep(1.0)  # idle scrapes after the burst
    stop.set()
    poller.join()
    finished_at = common.utc_now_iso()

    requests.sort(key=lambda r: (r["process"], r["slot"]))
    stats = compare(samples, requests, args.limit)
    statuses: dict[str, int] = {}
    for req in requests:
        statuses[str(req["status"])] = statuses.get(str(req["status"]), 0) + 1
    first_tokens = sorted(r["first_token"] - burst_at for r in requests if r["first_token"])

    measurements = [
        {"name": "sample_count", "value": len(requests)},
        {"name": "processes", "value": args.processes},
        {"name": "distinct_client_pids", "value": len({r["pid"] for r in requests})},
        {"name": "per_process_concurrency", "value": args.per_process},
        {"name": "limit_max_num_seqs_given", "value": args.limit},
        {"name": "http_status_counts", "value": statuses},
        {
            "name": "completion_tokens_distinct",
            "value": sorted({str(r["completion_tokens"]) for r in requests}),
        },
        {"name": "first_token_s_after_release", "value": [round(t, 3) for t in first_tokens]},
        {"name": "metric_scrapes", "value": len(samples)},
        *(
            {"name": key, "value": value}
            for key, value in stats.items()
            if key != "offending_samples"
        ),
    ]
    observations = [
        "LiteLLM is not in this path; requests go straight to the vLLM server "
        "(sub-spike decision).",
        "Bounds are client-side: upper counts a request from its send to its last byte, so a "
        "metric above upper reports work the server cannot have had.",
    ]
    if any(s["status"] != 200 for s in samples):
        observations.append("Some /metrics scrapes did not return 200; they are not scored.")

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    name = f"ev05_admission_load_{args.candidate}_{args.label}_{stamp}.json"
    payload = common.redact_json(
        {
            "generated_at_utc": common.utc_now_iso(),
            "command_line": common.command_line(),
            "candidate": args.candidate,
            "ev": "EV05",
            "label": args.label,
            "started_at": started_at,
            "finished_at": finished_at,
            "base_url": base_url,
            "model": args.model,
            "request_body": json.loads(body),
            "measurements": measurements,
            "observations": observations,
            "source_observations": [],
            "readback_max_num_seqs": readback(base_url, token, args.container),
            "offending_samples": stats["offending_samples"],
            "burst_released_at": burst_at,
            "requests": requests,
            "samples": samples,
            "artifacts": [name],
        }
    )
    path = common.write_json(Path(args.out), name, payload)
    print(f"wrote {path}")
    for item in measurements:
        print(f"  {item['name']}: {item['value']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
