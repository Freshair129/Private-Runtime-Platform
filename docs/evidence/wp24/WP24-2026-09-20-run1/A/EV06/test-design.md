# EV06 test design for candidate A (Xinference)

Gate `PRP-FR-020`..`PRP-FR-022`. Procedure: `docs/WP24-EXPERIMENT-PROCEDURE.md` EV06, steps 1–3.
Candidate B's EV06 (`../../B/EV06/`) is the comparison point: there, a client cancel stopped compute
within 0.19 s, no blind replay appeared in any case, and vLLM did not restart its own engine.

Runtime: the EV02 deployment, `shared_revision`, one replica, `XINFERENCE_HOME=F:/prp-xinference-a/home`.
Auth is disabled for this run (`XINFERENCE_AUTH_ADVANCED=0`) because none of EV06's questions touch
authentication and EV05 already recorded both postures. No new deviation is needed.

## What the shipped code says, to be confirmed by running

- `ModelActor` mixes in `CancelMixin`, which tracks running asyncio tasks per `request_id` and has an
  `abort_block` cancel task.
- `restful_api.py` catches `asyncio.CancelledError` on a disconnected client and calls
  `model_ref.abort_request(request_id)` under `asyncio.shield`, so a client disconnect is **meant**
  to abort the work rather than merely drop the socket.
- There is an `abort_request(model_uid, request_id, block_duration)` handler with a
  `XINFERENCE_DEFAULT_CANCEL_BLOCK_DURATION`. Its HTTP path is not visible in the route table by
  inspection, so the run reads `/openapi.json` from the live server to find it.

EV03 already observed part of case (b): killing the replica that was serving a streaming request
ended the stream with **HTTP 200 after one chunk**, with no error object, and the supervisor
relaunched the replica by itself. EV06 measures that case properly and adds the other two.

## Step 1 and 2 — the three cases

Each case runs against a long generation and records the same columns: what the client sees, whether
compute actually stopped, whether anything was replayed, the state the candidate reports afterwards,
and the measured time until the model serves again.

**Evidence of "compute actually stopped" and "no replay"** comes from the worker metrics exporter
(EV05 located it; it needs no credential): `xinference:model_serve_count` for in-flight work and
`xinference:generate_tokens_total` for produced tokens. After the client is gone, the run watches
both for **30 s**, the same window candidate B used. A rising token counter with no client attached
is replay; a flat counter with `serve_count` back to 0 is a genuine stop.

| case | what is done |
|---|---|
| **(a) client cancel** | start a long streaming generation, read a few chunks, then close the socket. Repeated for a non-streaming request. |
| **(a2) explicit abort** | if `/openapi.json` exposes the abort path, call it with the `request_id` of a running generation and measure the same things. |
| **(b) kill the engine process** | kill the model replica process mid-generation, then measure: client-visible ending, replay, what `/v1/models` and `/v1/workers` report, and **the time until the UID serves a request again** (EV03 saw an unrequested relaunch of roughly 35–40 s; here it is timed deliberately). |
| **(c) restart the supervisor** | stop the whole `xinference-local` process and start it again. Record what survives: is the model still loaded, does the custom registration survive (it was registered with `persist: false`), is anything replayed, and how long until the service accepts requests. |

## Step 3 — can PRP tell "unknown" from "definitely failed"

The client-visible ending of each case is tabulated against what actually happened on the server, to
answer the ARCH §11 question: which endings let PRP conclude `FAILED`, and which force `UNKNOWN`.
EV03 already suggests the hard case — a killed replica produced a **200 with a truncated stream and
no error** — so the run checks specifically whether a successful-looking ending can be told apart
from a real completion, for streaming and non-streaming alike.

## What this cannot reach

- **One GPU host (DEV-03)** and **DEV-07** (Windows-native transformers), so timings are not
  comparable with candidate B's containerised vLLM.
- Lease and quota reconciliation are PRP-side and do not exist before M4; this run only records what
  the candidate reports.
- A supervisor crash (as opposed to a clean stop) is not simulated beyond killing the process.
