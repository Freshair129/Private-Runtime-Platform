# EV05 test design on a single GPU host

Gates `PRP-FR-017` / `PRP-FR-018`. Procedure: `docs/WP24-EXPERIMENT-PROCEDURE.md` EV05, steps 1–3.
Runtime: the same vLLM container as EV02 (`prp-wp24-vllm-b`, `launch-command.txt` in `../EV02`).
Per the LiteLLM sub-spike decision, **LiteLLM is not in this path**: every request goes straight to
vLLM, because EV05 asks about the runtime, not the proxy.

## Step 1 — bypass (done, `step1-reachability-matrix.txt`)

vLLM is published on `127.0.0.1:8000` only. That was tested from the host itself and from an
unrelated container on the same Docker host. Results:

- The LAN and tailnet addresses are refused.
- Any process on this host, including any container through `host.docker.internal`, **can** reach it.
- EV03 showed `POST /invocations` answers **without** the API key (`../EV03/invocations-no-credential.txt`).

So on this host the only barrier is "not on this machine". Step 1b below adds the LAN peer the procedure names.

- **1b (still to run).** From the second machine (DESKTOP-8UR61U8, a different LAN host), try
  `192.168.1.100:8000` and `100.76.19.65:8000`. The operator on that machine runs it; the result
  goes into `step1b-lan-peer.txt`.

## Step 2 — over-concurrency load from several processes

| item | value |
|---|---|
| concurrency limit under test | `--max-num-seqs 4`, added to the EV02 launch. **Deviation DEV-05**: the default is too high to exceed on one small GPU with stdlib clients. |
| clients | 3 OS processes × 4 concurrent streaming requests = **12 in flight**, 3 × the limit |
| request | fixed prompt, `max_tokens: 256`, `ignore_eos: true`, so every request runs the same length |
| runs | run A at the limit (1 process × 4), run B over it (3 × 4). `sample_count` = 4 and 12 |
| per request, client side | send time, first-token time, done time, HTTP status, tokens received |
| metrics poller | `GET /metrics` every 250 ms: `vllm:num_requests_running`, `vllm:num_requests_waiting` |

**What gets compared.** From the client timestamps, the tool rebuilds at each poll instant:

- *client in-flight* = requests sent and not yet done;
- *client streaming* = first token received and not yet done.

It then reports, per sample, `running − client streaming` and `running + waiting − client in-flight`.
**Over-count** means the metric reports more work than exists. A positive gap larger than one poll
interval's skew, or `running > 4`, is the finding FR-018 cares about. Whether excess requests
queue, get rejected or are admitted beyond the limit is read from the HTTP statuses plus
`running` / `waiting`.

## Step 3 — can PRP read the limit back?

The tool records where `max_num_seqs` is visible: the engine's startup log line, `/metrics` (any
config-info gauge), `/v1/models`, `/version`. It notes which of these exist on this build. The
answer is taken from observation, not from documentation.

## Tooling

`tools/wp24/ev05_admission_load.py` (design approved by the owner 2026-09-22): stdlib only, same
conventions as the EV02 scripts (redaction, `--token-env`, one JSON output, no verdict). Unit
tests in `tools/wp24/tests/` cover the Prometheus text parser, the client-bound reconstruction,
the over-count and limit checks, and the `max_num_seqs` search.

Before any GPU run, the script was dry-run against a stdlib fake server that enforces a limit of 4
with a FIFO queue. That run only validates the tool, so it is **not evidence** about vLLM:

- honest metrics, 12 requests: first tokens arrived in 3 waves of 4, `max_running` 4,
  `max_waiting` 8, **0** samples flagged;
- a fake that over-reports `waiting` by 2: **28 of 28** samples flagged
  `total_above_client_upper`.

## What this cannot reach

- **FR-017 durable admission** needs PRP's PostgreSQL admission plus fault injection (M4). AT-017
  stays `NOT_RUN`. This EV only answers the candidate side.
- **Duplicate capacity holds across two hosts**: one GPU host only (the 3060 runs Ollama, not this
  candidate).

## Run precondition

The GPU must be free of other heavy work: `--gpu-memory-utilization 0.70` is about 11 GB of 16 GB.
Start the container only with the owner's go-ahead.
