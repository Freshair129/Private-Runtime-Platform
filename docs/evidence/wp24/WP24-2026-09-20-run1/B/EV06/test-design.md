# EV06 test design on a single GPU host

Gates `PRP-FR-020` / `021` / `022`. Procedure: `docs/WP24-EXPERIMENT-PROCEDURE.md` EV06, steps 1–3.
The runtime is candidate B launched as in `../EV05/launch-command.txt`: EV02's launch plus
`VLLM_WSL2_ENABLE_PIN_MEMORY=1` and `--max-num-seqs 4`. The limit is kept only so case (d) can
build a queue with four fillers; DEV-05 already covers it. Requests go straight to vLLM; LiteLLM is
not in the path (sub-spike decision).

## What each case must answer

For every case the record needs:

- what the client sees (HTTP status, whether the stream ends with a `finish_reason` or `[DONE]`, any error chunk);
- whether compute actually stopped, rather than the connection alone being cut;
- what state the runtime reports afterwards;
- whether any interrupted request was **re-run without a client asking** (blind replay);
- the measured time until the runtime accepts work again, marked cold or warm.

## Cases

| case | procedure step | how it is done | what shows whether compute stopped |
|---|---|---|---|
| (a) client cancel, streaming | 1(ก) | a streaming request with `max_tokens` 2000 and `ignore_eos`; the client closes the socket after 3 s | `vllm:num_requests_running` falls to 0; `vllm:generation_tokens_total` stops rising; the engine logs an abort |
| (b) client cancel, non-streaming | 1(ก) | the same request with `stream: false`; the client closes the socket after 3 s | the same, to see whether vLLM notices a disconnect when it has nothing to write yet |
| (c) kill the engine process | 1(ข) | `kill -9` of the EngineCore process inside the container, 3 s into a streaming request | what the API server does (exits, stays up but unhealthy, or restarts the engine), then `docker start` if the container stopped |
| (d) cancel a queued request | FR-021 "queued cancel ends immediately" | 4 fillers occupy the limit; a fifth request waits; the client closes it after 2 s | `vllm:num_requests_waiting` falls by one at once; the fifth request never produces tokens |
| (e) restart the service | 1(ค) | `docker restart` (SIGTERM, then start) 3 s into a streaming request | the same client-side and state observations as (c); ready time is **warm**, since the container keeps its compile cache |

Docker is the supervisor here: the container has no restart policy, so it does not come back by
itself. The tool records whether the container stopped before issuing `docker start`, and the ready
time is measured from that command. This is the honest reading of "restart supervisor / service"
on a Docker host.

## Blind replay check

After each interrupt, and after the runtime is ready again, the tool watches the runtime for **30 s
with no client request in flight**. Blind replay shows up as any of:

- `num_requests_running` or `num_requests_waiting` above 0;
- a rise in `generation_tokens_total` (the counter restarts at 0 on a process restart, so it is
  compared inside one process lifetime, using `process_start_time_seconds`);
- a new completed-request access-log line with no client call behind it.

## Step 3 — "unknown" versus "failed for certain"

The tool records the exact client-visible ending in each case. It also checks two things by
observation, not from documentation:

- whether the runtime offers any way to ask what became of a request afterwards: `/openapi.json`
  is searched for any cancel, abort or status route;
- whether a request id the client could reconcile on is returned (an `x-request-id` response
  header, or the completion `id`).

The expected answer, stated here so the run can contradict it: vLLM has no request-status or
cancel API, so it cannot tell PRP "unknown" apart from "failed". PRP would then have to reconcile
by itself, recording UNKNOWN and holding the lease QUARANTINED under ARCH §11 until the process is
proven gone.

## Tooling

`tools/wp24/ev06_interrupt_probe.py` (design approved by the owner 2026-09-22), one case per
invocation (`--case cancel-stream|cancel-nonstream|kill-engine|cancel-queued|restart`):

- stdlib only, the same conventions as `ev05_admission_load.py`;
- a `/metrics` poller at 250 ms that also reads `generation_tokens_total` and
  `process_start_time_seconds`;
- the interrupt at `--interrupt-after` seconds, driven through `docker exec` / `docker restart`
  for (c) and (e);
- readiness polling on `/health`, then the 30 s replay window, then an excerpt of `docker logs`
  from the case's start;
- no verdict.

Unit tests cover the pure parts: detecting a counter rise inside one process lifetime, classifying
the stream ending, and searching `/openapi.json` for routes.

Two details were added while writing the tool:

- **Readiness after an interrupt means `/health` failed first and then recovered.** A 200 right
  after a kill does not count, because the API server can answer before it notices the engine is
  gone. If `/health` never fails within 20 s, that is recorded as `health_never_failed`.
- **The engine PID is found with `grep -l '[E]ngineCore'`**, so the grep does not list its own
  command line. PID 1 (the API server) is never killed.

### Dry run (validates the tool only; not evidence about vLLM)

All five cases were dry-run against a stdlib fake server in a `python:3.12-alpine` container. The
fake has a limit of 4, aborts a request on client disconnect, and runs a child process named
`EngineCore` whose death makes the server exit. That dry run caught two bugs, both fixed before
this commit:

- cancel did nothing, because `http.client` drops `conn.sock` once a `Connection: close` response
  starts;
- idle time was computed before the poller's next sample.

| case | ending seen | notes |
|---|---|---|
| cancel-stream | `client_cancelled` after 59 chunks | idle 0.19 s later |
| cancel-nonstream | `client_cancelled_before_response` | idle 0.21 s later |
| cancel-queued | target never started; fillers `client_cancelled` | `waiting` 0 after 0.037 s |
| kill-engine | `cut_without_finish_reason` | only PID 7 was killed; container stopped; `docker start`, ready 2.3 s later |
| restart | `cut_without_finish_reason` | ready 12.6 s after the restart was issued (the fake ignores SIGTERM, so Docker waited 10 s) |

Every case had a replay-window token rise of 0.

## What this cannot reach

- **PRP's own UNKNOWN / QUARANTINED state machine** and the absolute-deadline rule of FR-021 are
  PRP code (M4). This run only answers what the candidate reports and does.
- **A hard kill of the whole GPU host** or a driver reset is not attempted.
- **One host (DEV-03):** there is no second replica to test whether a restart moves work between
  hosts. EV03 already showed no failover on the proxy side.

## Run precondition

The GPU must be free (about 11 GB at `--gpu-memory-utilization 0.70`). Start the container only on
the owner's go-ahead, and stop it afterwards.
