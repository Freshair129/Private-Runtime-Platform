# EV06 — timeout / restart, candidate B

Gates `PRP-FR-020` / `021` / `022`. These are operator observations only; no verdict is computed
here. The design is in `test-design.md`.

The runtime was launched as in `launch-command.txt`, which is identical to EV05's launch. It came up
cold in about 260 s. The image is `vllm/vllm-openai@sha256:c2914767…51ae1`. Every request went
straight to vLLM; LiteLLM was not in the path. The container was stopped and removed at
2026-09-22T14:16:31Z.

## Cases

| case | client-visible ending | did compute stop | back to taking work | replay |
|---|---|---|---|---|
| (a) cancel, streaming | cut by the client after 139 chunks | **yes**: `running` 0 and `generation_tokens_total` flat **0.19 s** after the close | no downtime | none |
| (b) cancel, non-streaming | client closed before any response | **yes**: idle **0.19 s** after the close, so vLLM notices a disconnect even with nothing written yet | no downtime | none |
| (c) `kill -9` EngineCore (PID 72) | HTTP 200, **an `error` object in the stream** (`InternalServerError`, `code` 500, "EngineCore encountered an issue"), then `[DONE]`; no `finish_reason` | the API server logged `EngineDeadError`, shut itself down, and the **container exited** | only after `docker start`: **73.2 s** from start (first run 78.6 s) | none |
| (d) cancel a queued request | the fifth request never got a token | **yes**: `waiting` 0 after **0.084 s**; the four running fillers were unaffected until they were cancelled | no downtime | none |
| (e) `docker restart` | HTTP 200, stream ended with **no `finish_reason`**, no error object, no `[DONE]` (the first run did end with `[DONE]`) | the container restarted. On SIGTERM vLLM logs `stopping engine client mode=abort timeout=0s` and force-kills EngineCore: in-flight work is **aborted, not drained** | **93.2 s** after the restart was issued (first run 98.1 s); warm | none |

- **No blind replay anywhere.** In every case the 30 s window after the client requests ended had
  `running` 0, `waiting` 0 and no rise in `generation_tokens_total` within one process lifetime.
- **In the restart and kill cases, nothing survives the process.** After the restart the counters
  started from a new `process_start_time_seconds`, and nothing was running or waiting.
- **Readiness after a kill needs a supervisor.** vLLM does not restart its own engine. The API
  server exits, and on this host only an operator or a Docker restart policy brings it back.
  `/health` fails within about 1 s of the kill.
- vLLM logs no line for an abort at INFO level. The evidence that compute stopped is the metrics,
  not the log.

## Step 3 — "unknown" versus "failed for certain"

What a client can tell once the HTTP 200 has been sent:

| ending | what the client can tell |
|---|---|
| a `finish_reason` arrives | finished |
| an `error` object in the stream | failed; the runtime says so itself (seen on the engine kill) |
| the stream stops with no `finish_reason` and no error (seen on a restart) | **nothing**: the runtime was going down, and the client cannot know how far compute got |
| the connection breaks before a response (non-streaming) | **nothing** |

- The status line is always 200 on a stream that has started, so the HTTP status never carries the
  failure.
- **Chat completions has no request-status or cancel API.** No `x-request-id` header was returned.
  A completion `id` appears in the stream, but nothing can look it up afterwards.
- **The Responses API has one, turned off by default.** `/openapi.json` lists `GET
  /v1/responses/{response_id}` and `POST /v1/responses/{response_id}/cancel`. A background request
  was refused with 400: *"This vLLM engine does not support `store=True` … set the environment
  variable `VLLM_ENABLE_RESPONSES_API_STORE=1`"* (`step3-responses-api-probe.txt`). Enabling it
  changes the launch config and is outside the approved design. Whether that store survives a
  restart, which it cannot if it lives in the API server's memory, is a proposed follow-up and not
  a result.

For PRP this means that on chat completions only the explicit error object says "failed for
certain". A stream cut with no `finish_reason`, or a lost connection, must be recorded as UNKNOWN,
with the lease QUARANTINED until the supervisor proves the process is gone (ARCH §11, FR-020). For
this runtime the proof is available: after a kill or restart, the container state and a new
`process_start_time_seconds` show that the old process is gone.

## Limits of this run

- PRP's UNKNOWN / QUARANTINED state machine and FR-021's absolute deadline are PRP code (M4).
- A kill of the whole host or a GPU driver reset was not attempted.
- There was one host (DEV-03) and a shared machine (DEV-04), so the times are indicative.
- Docker has no restart policy on this container. Automatic recovery after a kill was therefore not
  observed; with one configured, the recovery time would be the same start time.
