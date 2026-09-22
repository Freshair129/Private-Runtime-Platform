#!/usr/bin/env python3
"""EV06 timeout / restart probe for WP24 candidate B (vLLM), one interrupt case per run.

Design: docs/evidence/wp24/WP24-2026-09-20-run1/B/EV06/test-design.md (approved 2026-09-22).
Procedure: docs/WP24-EXPERIMENT-PROCEDURE.md EV06 (gate PRP-FR-020 / 021 / 022).

Cases (--case):
  cancel-stream     a long streaming request; the client closes the socket after --interrupt-after
  cancel-nonstream  the same with stream false
  kill-engine       kill -9 of the EngineCore process inside --container during a streaming request
  cancel-queued     --limit fillers occupy the runtime; one more request waits and is closed
  restart           docker restart of --container during a streaming request

For every case the script records the client-visible ending of each request, samples /metrics every
--poll-interval seconds (running, waiting, generation_tokens_total, process_start_time_seconds),
waits for /health after a kill or restart (issuing docker start only if the container stopped), then
watches --replay-window seconds with no client request in flight for signs of blind replay. It also
searches /openapi.json for cancel / abort / status routes and keeps an excerpt of docker logs.

No verdict is computed (docs/WP24-EXPERIMENT-PROCEDURE.md section 3 item 4). The API key is read
from the environment variable named by --token-env and never printed or written.

Usage:
  python tools/wp24/ev06_interrupt_probe.py --case kill-engine --container prp-wp24-vllm-b
      --token-env VLLM_API_KEY --model typhoon2.5-qwen3-4b --out DIR

Standard library only.
"""

from __future__ import annotations

import argparse
import contextlib
import http.client
import json
import os
import re
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import wp24_common as common
from ev05_admission_load import parse_prometheus

CASES = ("cancel-stream", "cancel-nonstream", "kill-engine", "cancel-queued", "restart")
RUNNING = "vllm:num_requests_running"
WAITING = "vllm:num_requests_waiting"
GEN_TOKENS = "vllm:generation_tokens_total"
PROC_START = "process_start_time_seconds"
PROMPT = "เล่าประวัติศาสตร์ของกรุงเทพมหานครอย่างละเอียดที่สุดเท่าที่ทำได้"
_ROUTE_RE = re.compile(r"cancel|abort|status|request", re.IGNORECASE)
_LOG_RE = re.compile(r"abort|died|error|exception|shutdown|shutting|started server|POST ", re.I)


# --- pure functions (unit tested) -------------------------------------------------------------


def classify_ending(record: dict[str, Any]) -> str:
    """Name how one request ended, from the client's point of view."""
    if record.get("status") is None:
        return (
            "client_cancelled_before_response" if record.get("client_cancel_at") else "no_response"
        )
    if record["status"] != 200:
        return f"http_{record['status']}"
    if record.get("finish_reason"):
        return "completed"
    if record.get("client_cancel_at"):
        return "client_cancelled"
    if record.get("error_chunk"):
        return "error_chunk_in_stream"
    return "cut_without_finish_reason"


def counter_rise(samples: list[dict[str, Any]], t_from: float, t_to: float) -> float:
    """Total rise of generation_tokens_total inside [t_from, t_to], within each process lifetime.

    Samples are grouped by process_start_time_seconds, so a restart that resets the counter to zero
    is not read as a fall or a rise.
    """
    last: dict[Any, float] = {}
    rise = 0.0
    for sample in samples:
        if not t_from <= sample["t"] <= t_to or sample.get("gen_tokens") is None:
            continue
        key = sample.get("proc_start")
        if key in last and sample["gen_tokens"] > last[key]:
            rise += sample["gen_tokens"] - last[key]
        last[key] = sample["gen_tokens"]
    return rise


def first_idle_after(samples: list[dict[str, Any]], t_from: float) -> float | None:
    """Time of the first sample at or after ``t_from`` with nothing running and nothing waiting."""
    for sample in samples:
        if sample["t"] >= t_from and sample.get("running") == 0 and sample.get("waiting") == 0:
            return sample["t"]
    return None


def engine_pids(grep_output: str) -> list[int]:
    """PIDs from ``grep -l`` output of /proc/<pid>/cmdline or /proc/<pid>/comm paths."""
    return sorted({int(m) for m in re.findall(r"/proc/(\d+)/", grep_output)})


def find_routes(openapi: dict[str, Any]) -> list[str]:
    """OpenAPI paths whose name suggests cancel, abort, status or request lookup."""
    return sorted(path for path in openapi.get("paths", {}) if _ROUTE_RE.search(path))


# --- client ---------------------------------------------------------------------------------------


class Call:
    """One chat completion over a raw connection the probe can close at any moment."""

    def __init__(self, base_url: str, token: str | None, body: dict[str, Any], name: str) -> None:
        parsed = urllib.parse.urlsplit(base_url)
        self.host, self.port = parsed.hostname or "127.0.0.1", parsed.port or 80
        self.token, self.body, self.stream = token, body, bool(body.get("stream"))
        # http.client drops conn.sock once a Connection: close response starts, so the probe keeps
        # its own reference to the socket to be able to cut it mid-stream.
        self.sock: socket.socket | None = None
        self.record: dict[str, Any] = {
            "name": name,
            "stream": self.stream,
            "sent": None,
            "status": None,
            "request_id_header": None,
            "completion_id": None,
            "first_token": None,
            "chunks": 0,
            "finish_reason": None,
            "saw_done": False,
            "client_cancel_at": None,
            "ended": None,
            "end_error": None,
            "error_chunk": None,
        }
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def cancel(self) -> None:
        self.record["client_cancel_at"] = time.time()
        sock = self.sock
        if sock is not None:
            with contextlib.suppress(OSError):
                sock.shutdown(socket.SHUT_RDWR)
            sock.close()

    def _run(self) -> None:
        rec = self.record
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            conn = http.client.HTTPConnection(self.host, self.port, timeout=600)
            conn.connect()
            self.sock = conn.sock
            rec["sent"] = time.time()
            conn.request("POST", "/v1/chat/completions", json.dumps(self.body), headers)
            resp = conn.getresponse()
            rec["status"] = resp.status
            rec["request_id_header"] = resp.getheader("x-request-id")
            if not self.stream:
                self._take(json.loads(resp.read() or b"{}"))
            else:
                for raw in resp:
                    line = raw.decode("utf-8", "replace").strip()
                    if line == "data: [DONE]":
                        rec["saw_done"] = True
                    elif line.startswith("data:"):
                        try:
                            self._take(json.loads(line[5:]))
                        except ValueError:
                            continue
        except (OSError, http.client.HTTPException, ValueError) as exc:
            rec["end_error"] = f"{type(exc).__name__}: {exc}"[:200]
        rec["ended"] = time.time()

    def _take(self, chunk: dict[str, Any]) -> None:
        rec = self.record
        rec["completion_id"] = rec["completion_id"] or chunk.get("id")
        if chunk.get("error") is not None:
            rec["error_chunk"] = common.redact_text(json.dumps(chunk["error"]))[:400]
        for choice in chunk.get("choices") or []:
            content = (choice.get("delta") or choice.get("message") or {}).get("content")
            if content:
                rec["first_token"] = rec["first_token"] or time.time()
                rec["chunks"] += 1
            rec["finish_reason"] = choice.get("finish_reason") or rec["finish_reason"]


def _get(url: str, token: str | None, timeout: float = 3.0) -> tuple[int | None, str]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, ""
    except (urllib.error.URLError, OSError) as exc:
        return None, type(exc).__name__


def _poll(base: str, token: str | None, every: float, stop: threading.Event, out: list) -> None:
    while not stop.is_set():
        t = time.time()
        status, text = _get(f"{base}/metrics", token)
        m = parse_prometheus(text) if status == 200 else {}
        out.append(
            {
                "t": t,
                "status": status,
                "running": m.get(RUNNING),
                "waiting": m.get(WAITING),
                "gen_tokens": m.get(GEN_TOKENS),
                "proc_start": m.get(PROC_START),
            }
        )
        stop.wait(max(0.0, every - (time.time() - t)))


def _docker(*args: str, timeout: float = 120) -> dict[str, Any]:
    return common.run_command(["docker", *args], timeout_seconds=timeout)


def _container_running(container: str) -> bool | None:
    out = _docker("inspect", "-f", "{{.State.Running}}", container, timeout=15)
    return None if out["return_code"] != 0 else out["stdout"].strip() == "true"


def _wait_ready(base: str, token: str | None, container: str | None, timeout: float) -> dict:
    """Poll /health until it has failed at least once and then answers 200 again.

    A /health 200 right after the interrupt is not readiness: the API server can still answer
    before it notices the engine is gone. If /health never fails within ``never_down_after``
    seconds, that is recorded (``health_never_failed``) instead of a ready time. docker start is
    issued once, only if the container is found stopped.
    """
    t0 = time.time()
    never_down_after = 20.0
    info: dict[str, Any] = {
        "health_down_at": None,
        "docker_start_issued_at": None,
        "ready_at": None,
        "container_stopped": None,
        "health_never_failed": None,
    }
    while time.time() - t0 < timeout:
        healthy = _get(f"{base}/health", token)[0] == 200
        if not healthy and info["health_down_at"] is None:
            info["health_down_at"] = time.time()
        if healthy and info["health_down_at"] is not None:
            info["ready_at"] = time.time()
            return info
        if healthy and time.time() - t0 > never_down_after:
            info["health_never_failed"] = True
            return info
        stopped = container is not None and info["docker_start_issued_at"] is None
        if stopped and _container_running(container or "") is False:
            info["container_stopped"] = True
            info["docker_start_issued_at"] = time.time()
            info["docker_start"] = _docker("start", container or "")["return_code"]
        time.sleep(0.5)
    return info


# --- main ---------------------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--case", required=True, choices=CASES)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--token-env", default=None, help="NAME of the env var holding the key")
    parser.add_argument("--model", required=True)
    parser.add_argument("--container", default=None)
    parser.add_argument("--interrupt-after", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=2000)
    parser.add_argument("--limit", type=int, default=4, help="fillers for cancel-queued")
    parser.add_argument("--poll-interval", type=float, default=0.25)
    parser.add_argument("--replay-window", type=float, default=30.0)
    parser.add_argument("--ready-timeout", type=float, default=600.0)
    parser.add_argument("--candidate", default="B")
    parser.add_argument("--out", default="wp24-out")
    args = parser.parse_args()
    if args.case in ("kill-engine", "restart") and not args.container:
        parser.error(f"--case {args.case} needs --container")

    base = args.base_url.rstrip("/")
    token = os.environ.get(args.token_env) if args.token_env else None
    after = args.interrupt_after or (2.0 if args.case == "cancel-queued" else 3.0)
    body = {
        "model": args.model,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": args.max_tokens,
        "ignore_eos": True,
        "stream": args.case != "cancel-nonstream",
    }
    if body["stream"]:
        body["stream_options"] = {"include_usage": True}

    started_at, case_t0 = common.utc_now_iso(), time.time()
    samples: list[dict[str, Any]] = []
    stop = threading.Event()
    poller = threading.Thread(target=_poll, args=(base, token, args.poll_interval, stop, samples))
    poller.start()
    time.sleep(1.0)

    fillers = [Call(base, token, body, f"filler-{i}") for i in range(args.limit)]
    if args.case == "cancel-queued":
        for call in fillers:
            call.start()
        deadline = time.time() + 30
        while time.time() < deadline and not (samples and samples[-1].get("running") == args.limit):
            time.sleep(0.1)
    else:
        fillers = []
    target = Call(base, token, body, "target")
    target.start()
    time.sleep(after)

    action: dict[str, Any] = {"case": args.case, "at": time.time()}
    if args.case in ("cancel-stream", "cancel-nonstream", "cancel-queued"):
        target.cancel()
    elif args.case == "kill-engine":
        found = _docker(
            "exec",
            args.container,
            "sh",
            "-c",
            "grep -l '[E]ngineCore' /proc/[0-9]*/cmdline /proc/[0-9]*/comm 2>/dev/null",
            timeout=15,
        )
        pids = [p for p in engine_pids(found["stdout"]) if p != 1]
        action["engine_pids"] = pids
        for pid in pids:
            action[f"kill_{pid}"] = _docker("exec", args.container, "kill", "-9", str(pid))[
                "return_code"
            ]
    elif args.case == "restart":
        issued = time.time()
        action["docker_restart"] = _docker("restart", "-t", "10", args.container)["return_code"]
        action["docker_restart_returned_s"] = round(time.time() - issued, 3)

    if args.case == "cancel-queued":
        time.sleep(3.0)  # watch the queue shrink with the fillers still running
        action["fillers_cancelled_at"] = time.time()
        for call in fillers:
            call.cancel()

    ready: dict[str, Any] = {}
    if args.case in ("kill-engine", "restart"):
        ready = _wait_ready(base, token, args.container, args.ready_timeout)
    for call in [target, *fillers]:
        call.thread.join(timeout=30)
    settle = time.time()
    time.sleep(args.replay_window)
    window = (settle, time.time())
    stop.set()
    poller.join()
    idle_at = first_idle_after(samples, action["at"])
    queue_empty_at = next(
        (s["t"] for s in samples if s["t"] >= action["at"] and s.get("waiting") == 0), None
    )

    in_window = [
        s for s in samples if window[0] <= s["t"] <= window[1] and s["running"] is not None
    ]
    status, text = _get(f"{base}/openapi.json", token, timeout=10)
    try:
        routes = find_routes(json.loads(text)) if status == 200 else None
    except ValueError:
        routes = None
    logs: list[str] = []
    if args.container:
        since = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(case_t0 - 1))
        out = _docker("logs", "--since", since, args.container, timeout=30)
        logs = [
            line for line in (out["stdout"] + out["stderr"]).splitlines() if _LOG_RE.search(line)
        ]

    calls = [target, *fillers]
    for call in calls:
        call.record["ending"] = classify_ending(call.record)
    reference = ready.get("docker_start_issued_at") or action["at"]
    measurements = [
        {"name": "case", "value": args.case},
        {"name": "interrupt_after_s", "value": after},
        {"name": "target_ending", "value": target.record["ending"]},
        {"name": "target_chunks_before_interrupt", "value": target.record["chunks"]},
        {"name": "target_request_id_header", "value": target.record["request_id_header"]},
        {"name": "target_completion_id_seen", "value": target.record["completion_id"] is not None},
        {"name": "filler_endings", "value": [c.record["ending"] for c in fillers]},
        {
            "name": "waiting_zero_s_after_interrupt",
            "value": None if queue_empty_at is None else round(queue_empty_at - action["at"], 3),
        },
        {
            "name": "idle_s_after_interrupt",
            "value": None if idle_at is None else round(idle_at - action["at"], 3),
        },
        {
            "name": "gen_tokens_rise_after_idle",
            "value": None if idle_at is None else counter_rise(samples, idle_at, window[1]),
        },
        {"name": "container_stopped_after_interrupt", "value": ready.get("container_stopped")},
        {
            "name": "ready_s_from_reference",
            "value": None if not ready.get("ready_at") else round(ready["ready_at"] - reference, 3),
        },
        {
            "name": "ready_reference",
            "value": "docker start"
            if ready.get("docker_start_issued_at")
            else ("interrupt" if ready else None),
        },
        {"name": "replay_window_s", "value": args.replay_window},
        {
            "name": "replay_window_max_running",
            "value": max((s["running"] for s in in_window), default=None),
        },
        {
            "name": "replay_window_max_waiting",
            "value": max((s["waiting"] for s in in_window), default=None),
        },
        {"name": "replay_window_gen_tokens_rise", "value": counter_rise(samples, *window)},
        {"name": "openapi_cancel_abort_status_routes", "value": routes},
        {
            "name": "access_log_posts_in_case",
            "value": sum("POST /v1/chat/completions" in x for x in logs),
        },
    ]
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    name = f"ev06_interrupt_{args.candidate}_{args.case}_{stamp}.json"
    payload = common.redact_json(
        {
            "generated_at_utc": common.utc_now_iso(),
            "command_line": common.command_line(),
            "candidate": args.candidate,
            "ev": "EV06",
            "case": args.case,
            "started_at": started_at,
            "finished_at": common.utc_now_iso(),
            "base_url": base,
            "request_body": body,
            "measurements": measurements,
            "observations": [
                "LiteLLM is not in this path; requests go straight to the vLLM server.",
                "The replay window starts once every client request has ended; any running or "
                "waiting request, or any token-counter rise inside one process lifetime, in that "
                "window has no client behind it.",
            ],
            "source_observations": [],
            "action": action,
            "readiness": ready,
            "requests": [c.record for c in calls],
            "docker_log_excerpt": [common.redact_text(x)[:400] for x in logs[:120]],
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
