# EV03 — target binding, candidate A (Xinference)

Gate `PRP-NFR-023`. Operator observations only; no verdict is computed here. The design is in
`test-design.md`. Candidate B's EV03 used LiteLLM as the routing layer; for candidate A the routing
layer is **Xinference's own supervisor**, with no proxy involved.

Topology (**DEV-08**): two live targets of the built-in `qwen3` 0.6B model, because two copies of
the 4B `shared_revision` do not fit in 16 GiB. Auth was disabled for this run
(`XINFERENCE_AUTH_ADVANCED=0`), as in EV02 steps 1–3.

## How a request was attributed to a runtime

Neither the response nor any header names the runtime that served a request, and **the server's own
log does not attribute a request to a replica address** either — the access log lines carry the
client's address, not the worker's. That is the same gap candidate B had, where LiteLLM sent none of
its documented routing headers.

What does attribute is the **worker metrics exporter** (a separate port, `127.0.0.1:59771` here,
announced only in the log): `xinference:generate_tokens_total` carries
`model_uid`, `replica_index`, `gpu_index` and `worker_address` labels. Every per-request attribution
below is taken from deltas of that counter. One limitation, measured: **the counter moves only when
a request finishes**, so it cannot identify the replica serving an in-flight request.

## Step 1 — a request addressed to a target lands on that target

Two UIDs, `prp-a-t1` and `prp-a-t2`, one replica each, at distinct addresses
(`127.0.0.1:53737` and `:53943`). **40 requests, 20 per UID**:

| measurement | result |
|---|---|
| responses whose `model` field equals the UID addressed | **40 / 40** |
| distinct completion ids | 40 |
| token counters that moved | only the addressed UID's, for every request |

No request crossed to the other UID.

## Step 2 — two replicas under one UID: the client cannot choose

`prp-a-dual` launched with `replica: 2` gave `prp-a-dual-rep0` and `prp-a-dual-rep1` at separate
addresses. **20 requests to that one UID:**

| measurement | result |
|---|---|
| replica sequence | `0,1,0,1,0,1,…` — **strict alternation**, matching `itertools.cycle` in `supervisor.get_model()` |
| token split | replica0 48, replica1 51 |
| requests attributed to exactly one replica | 20 / 20 |
| any response field naming the replica | **none** |
| `/v1/models` view | shows **one** address for the UID even though two replicas exist |

So the client addresses a UID; the supervisor alone decides the replica, and the client is not told
which one ran. For PRP that means **binding is only as fine as a UID**: if PRP wants one physical
runtime per lease, it must run one replica per UID and treat the UID as the target.

The UID namespace has a reserved suffix: a UID ending in `-rep<number>` is refused with a clear
error, because that form names replicas internally.

## Step 3 — kill the replica that is serving

**Mid-flight kill** (the serving replica predicted from the round-robin order, then its process
killed 3.9 s into a streaming request):

| observation | value |
|---|---|
| what the client saw | **HTTP 200, stream closed after 1 chunk**, as though it had ended normally |
| token counter of the killed replica | **no growth** |
| token counter of the other replica | **no growth** |
| conclusion | the work was **not re-run anywhere**. No blind replay, and no silent failover to the healthy replica |

**What happens to the UID afterwards** (also observed when a replica was killed while idle):

- requests that round-robin sends to the dead replica **fail**: `400 Model not found in the model
  list, uid: prp-a-dual-rep0`, and during shutdown `500 Model prp-a-dual-rep0 is in stopping state`.
  They are **not** re-routed to the healthy replica;
- **the supervisor relaunches the dead replica by itself.** The log shows `Launch started:
  model_name=qwen3, model_uid=prp-a-dual-rep0` seconds after the death, and the replica came back
  ~35 s later, then ~40 s in the second case;
- **each recovery gives the replica a new address**: `54535` → `59967` → `60162`.

That last point is the finding NFR-023 cares about most. The requirement forbids "downstream retry,
reroute or **replica relocation**" that escapes the lease. Candidate A does not retry a request, but
it **does relocate a replica on its own**, with no request from PRP, and the address PRP might have
recorded is no longer valid afterwards.

The code confirms the mechanism and gives exactly one knob:
`XINFERENCE_MODEL_ACTOR_AUTO_RECOVER_LIMIT`, documented in `constants.py` as "None (default) =
unbounded retry; int N = recreate up to N times, then evict the replica on the next death". The
worker also notifies the supervisor through `mark_replica_dead` to evict a dead replica from the
round-robin.

## Step 4 — retry / failover / hedging configuration

Searching the request path (`supervisor.py`, `worker.py`, `model.py`, `restful_api.py`) for retry,
failover, hedge, reroute or fallback finds **nothing that re-sends a client request**. The matches
are about *launching* models: autostart `max_retries` / `retry_interval_seconds`, a persistence
retry counter, and a launch-strategy fallback.

| control | default | can it be switched off |
|---|---|---|
| request-level retry / failover / hedging | **does not exist** | nothing to disable |
| replica selection | round-robin over active replicas | not configurable; use one replica per UID instead |
| replica auto-recreate after death | **unbounded** | `XINFERENCE_MODEL_ACTOR_AUTO_RECOVER_LIMIT=N`; the smallest value bounds it, it cannot be disabled outright |
| autostart of persisted models | `max_retries` 3, `retry_interval_seconds` 30 | per entry |

Step 4's second question — whether a second attempt keeps the original deadline and is readmitted —
**did not arise**: there was no second attempt to observe, because the candidate never re-sent the
request.

## What PRP has to carry

- Run **one replica per UID** if a lease must bind to one runtime, since the client cannot select a
  replica and cannot see which one served.
- Treat the replica address as **unstable**: it changes on every automatic recovery, which is also
  the restart signal EV02 found.
- Bound the auto-recreate with `XINFERENCE_MODEL_ACTOR_AUTO_RECOVER_LIMIT` and reconcile after it,
  because a relocation happens without PRP asking.
- Scrape the **worker metrics exporter** for per-replica attribution; it is the only channel that
  provides it, it lives on a separate port announced only in the log, and it only counts completed
  requests.

## Limits of this run

- **One GPU host (DEV-03)**: this is replica binding on one machine, not host binding.
- **DEV-07**: Windows-native transformers backend.
- **DEV-08**: a 0.6B model instead of `shared_revision`, for this experiment only.
- The throttled-target variant of step 3 (slow rather than dead) was not run: the kill case already
  answered the re-routing question, and the queue behaviour belongs to EV05.
