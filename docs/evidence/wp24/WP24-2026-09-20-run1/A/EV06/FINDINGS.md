# EV06 — timeout / restart, candidate A (Xinference)

Gate `PRP-FR-020`..`PRP-FR-022`. Operator observations only; no verdict is computed here. The design
is in `test-design.md`. Candidate B's EV06 is the comparison point.

Runtime: the EV02 deployment, `shared_revision`, one replica, auth disabled for this run
(`XINFERENCE_AUTH_ADVANCED=0`), no new deviation. Evidence of "compute really stopped" and "nothing
was replayed" comes from the worker metrics exporter EV05 located:
`xinference:model_serve_count` for in-flight work and `xinference:generate_tokens_total` for tokens
produced. A control request confirmed the token counter responds at all: an 11-token completion
moved it from 0 to 11, so a flat counter afterwards is meaningful evidence.

## The case table

| case | what the client saw | did compute stop | replay | recovery |
|---|---|---|---|---|
| **(a) streaming cancel** | socket closed by the client | **yes**, `serve_count` → 0 in **3.53 s** | none | n/a |
| **(a) non-streaming cancel** | socket closed by the client | **no.** The model ran **61.5 s more** and produced the full **900 tokens** | none | n/a |
| **(a2) explicit abort** | `POST /v1/models/{uid}/requests/{rid}/abort` → `200 {"msg":"DONE"}` in **2.295 s** | **yes**, `serve_count` → 0 in **0.5 s** | none | n/a |
| **(b) kill the engine process** | **HTTP 200**, one chunk, then the stream simply ends: no `[DONE]`, no error object | the process died | none (counter flat over 30 s) | the UID served again **131.8 s** after the kill, unrequested |
| **(c) restart the supervisor** | `ConnectionResetError` (WinError 10054) | the process died | none | API answered again after **52.8 s**, but **empty** |

## Step 1 and 2 — what each case showed

**Cancel works, but only for streaming.** This is the finding that matters most. Closing the socket
on a streaming generation stopped the work within 3.53 s, as the code suggests
(`restful_api.py` catches `asyncio.CancelledError` and calls `abort_request` under
`asyncio.shield`). Closing the socket on a **non-streaming** request did not stop anything: the
model kept generating for **61.5 s** after the client was gone and produced all 900 tokens it had
been given, then finished into a socket nobody was reading. The GPU work was spent in full.

Candidate B stopped compute within 0.19 s for streaming **and** non-streaming alike. Candidate A
matches it for streaming and fails to for non-streaming.

**The explicit abort endpoint works and is the reliable path.** It is not in the route table by
inspection; it was found at runtime in `/openapi.json` as
`POST /v1/models/{model_uid}/requests/{request_id}/abort`. Called against a running generation with
a client-supplied `request_id`, it returned `{"msg":"DONE"}` in 2.295 s and the model was idle 0.5 s
later. For PRP this is the dependable cancel: it does not depend on the transport, and it works for
the non-streaming case the socket close cannot touch.

**No blind replay in any case.** In every window after the client ended, `generate_tokens_total`
stayed flat, including 30 s after the engine kill. Nothing re-ran work by itself.

**But the in-flight gauge goes stale after a crash.** Thirty seconds after the engine process was
killed, `model_serve_count` still read **1** with nothing running and the process gone. Under normal
load EV05 measured that gauge as never over-counting across 384 scrapes; across a crash it is
**wrong and stays wrong**. PRP cannot use it to decide whether work survived a fault.

**Unrequested recovery, again, and slower.** As in EV03, the supervisor relaunched the dead replica
without being asked. With the 4B `shared_revision` it took **131.8 s** from kill to serving again
(EV03's 0.6B model took 35–40 s). During that window requests failed with
`500 Model prp-a-llm-rep0 is in stopping state` and then `400 Model not found in the model list`.

**A supervisor restart loses everything.** After stopping and restarting the process:

- the API answered again after **52.8 s**;
- the custom registration was **gone** (`['prp-typhoon25-qwen3-4b']` → `[]`), which is consistent
  with it having been registered with `persist: false`;
- **no models were loaded** (`['prp-a-llm']` → `[]`);
- a request for the UID returned `404 Model not found in the model list, uid: prp-a-llm.
  Available model uids: []`.

Nothing was replayed, and nothing came back on its own. PRP must re-register and re-launch after a
supervisor restart, and must expect a cold load on top of the 52.8 s.

**The supervisor takes its bookkeeping down with it, but not its processes.** After the restart the
cluster was empty, yet the model was still on the GPU. Force-killing the supervisor left its
**worker** process orphaned (`python.exe -c "from multiprocessing.spawn import spawn_main;
spawn_main(parent_pid=45848 ...)"`, the pid that writes the worker's own log lines), and that
orphaned worker kept doing its job: it held the model actor sub-pool
(`xoscar.backends.indigen start_sub_pool`) with **10 610 MiB of VRAM**, and when that sub-pool was
killed by hand it **recreated it within about a minute**, taking the VRAM again. This is the
unbounded auto-recreate EV03 documented (`XINFERENCE_MODEL_ACTOR_AUTO_RECOVER_LIMIT`, default
unbounded) still running with no supervisor above it.

Stopping the listener on port 9997 does not stop the cluster: it kills the API process only. Ending
the run needed the orphaned worker killed first, after which VRAM fell to 2 753 MiB and stayed there
with nothing respawning. An operator who restarts Xinference without reaping that worker meets a GPU
that is already occupied by a model no supervisor knows about.

## Step 3 — can PRP tell `UNKNOWN` from `FAILED`

| ending the client sees | what actually happened | what PRP may conclude |
|---|---|---|
| `data: [DONE]` with a `finish_reason` | the work completed | **FINISHED** |
| `200` then the stream stops with no `[DONE]` and no error | **the engine was killed mid-generation** | **UNKNOWN.** The HTTP status is 200 and there is no error object, so this is indistinguishable from success by status alone |
| `ConnectionResetError` | the supervisor died | **UNKNOWN**, leaning failed: the socket broke, but nothing proves where generation stopped |
| `429` | rejected over `request_limits` (EV05) | **FAILED**, no compute was spent |
| `500 is in stopping state` / `400 not found` | the replica is down or recovering | **FAILED** to admit |

**The dangerous ending is the second row**: a truncated stream under HTTP 200 with no error object.
A client that only checks the status code reads a killed generation as a success. PRP must treat any
stream that ends without an explicit `[DONE]` as `UNKNOWN`, exactly as ARCH §11 requires, and must
not trust the transport-level status. Candidate B produced a comparable ambiguity on restart, but
on an engine kill it at least emitted an in-stream error object; candidate A emitted nothing.

## What PRP has to carry

- Use the **explicit abort endpoint** with a PRP-generated `request_id` rather than relying on a
  socket close, because the socket close does nothing for non-streaming work.
- Treat a stream that ends without `[DONE]` as `UNKNOWN`, never as success.
- Do not trust `model_serve_count` across a fault; it stayed at 1 after the engine died.
- Expect an **unrequested replica relaunch** (131.8 s here) and reconcile after it, as EV03 also
  found.
- After a supervisor restart, **reap the orphaned worker process** before relaunching. Killing the
  API listener is not enough: the worker survives, holds 10.6 GiB of VRAM and recreates the model
  actor when it is killed.
- After a supervisor restart, **re-register and re-launch**: registrations made with
  `persist: false` and all loaded models are gone, and the empty API answers in 52.8 s while a cold
  load still has to follow.

## Limits of this run

- **One GPU host (DEV-03)** and **DEV-07** (Windows-native transformers), so no timing comparison
  with candidate B's containerised vLLM is valid.
- A supervisor **crash** was simulated by force-killing the process; no power-loss or disk-fault
  case was attempted.
- `persist: true` registrations were not tested, so how much a restart would preserve with them is
  unmeasured.
- Lease and quota reconciliation are PRP-side and do not exist before M4.
