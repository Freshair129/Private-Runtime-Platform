# EV05 — atomic multi-process load, candidate A (Xinference)

Gate `PRP-FR-017` / `PRP-FR-018`. Operator observations only; no verdict is computed here. The design
is in `test-design.md`. Candidate B's EV05 is the comparison point.

As the procedure states, **FR-017's durable admission transaction is PRP-side** and needs PostgreSQL
with fault injection, which does not exist before M4. Only the candidate's side is examined here, so
`AT-017` stays `NOT_RUN` whatever this run shows.

Runtime: the EV02 deployment with `shared_revision` (the 4B model), one replica, a **fresh
`XINFERENCE_HOME`** so a per-run administrator could be bootstrapped, and **auth left at the 3.4.0
default (on)**, which is the posture an operator actually gets. Per-run credentials stayed in
environment variables, never reached an artifact and were deleted afterwards.

## Step 1 — what can reach the runtime

The deployment opens **four** listeners, not one:

| listener | port in this run | bound to |
|---|---|---|
| REST API | 9997 | `127.0.0.1` |
| worker actor (xoscar) | 37149 | `127.0.0.1` |
| model replica actor | 60421 | `127.0.0.1` |
| **worker metrics exporter** | 60308 | `127.0.0.1` |

**Every one refused every non-loopback address.** TCP connects were attempted from the host's LAN
address (192.168.1.100), its tailnet address (100.76.19.65) and the WSL switch address
(172.20.192.1): all four listeners answered `ConnectionRefusedError 10061` on all three, and
connected only on loopback. `--host 127.0.0.1` therefore binds the actor ports and the exporter too,
not just the API. Candidate B's vLLM behaved the same way for its own port, but was reachable from
an unrelated container through `host.docker.internal`; candidate A opens no such path because
nothing is containerised.

**The authentication boundary is not the same as the network boundary.** With auth on:

| path | no credential |
|---|---|
| `GET /v1/models`, `/v1/workers` (port 9997) | **401** |
| **`GET /metrics` on port 9997** | **200** |
| **the whole worker metrics exporter (60308)** | **200** |
| `/docs`, `/openapi.json` | 200 |
| `/v1/cluster/auth`, `/v1/admin/setup/status` | 200, by design |

So any process on the host can read the telemetry without a credential, and that telemetry is not
empty: it carries `model_name`, `model_uid`, `worker_address`, `gpu_index`, `replica_index`,
`xinference_home` and the load duration — the model's identity and its placement. This is the same
class of gap as candidate B, whose `/metrics` and `POST /invocations` answered unauthenticated,
though A exposes telemetry only, not an inference path.

Speaking raw HTTP to the worker or replica actor port gets `RemoteDisconnected`: the actor protocol
is not HTTP, so there is no trivial bypass of the supervisor over that port. It is still an open
local socket, so isolation from other local processes rests on the host, not on the candidate.

## Step 2 — twelve concurrent requests from three processes

Three OS processes, four requests each, released together. Measured twice.

**(a) Default configuration.** All **12 returned 200** and finished together at 29.7 s: the
transformers backend put all twelve in one batch. Nothing was queued in waves and nothing was
rejected. The in-flight gauge `xinference:model_serve_count` reached exactly **12**, and across
**199 scrapes it never exceeded the client-side upper bound** of requests sent but not yet returned.
`xinference:model_request_limit` read **-1**, meaning unlimited.

Candidate B, with `max_num_seqs 4`, ran the same 12 requests in three waves of four and queued the
excess. Candidate A's default admits everything at once instead. **No timing comparison between the
two is valid (DEV-07)**, but the admission *shape* differs: B queues, A (by default) accepts.

**(b) Relaunched with `request_limits: 4`.** The same 12 requests gave **4 × 200 and 8 × 429**:

```
{"detail":"Rate limit reached for the model. Request limit 4 for the model: prp-a-llm"}
```

The gauge peaked at exactly **4** and again **never over-counted** (0 of 185 scrapes). So the
candidate can be made to **reject** rather than queue, and its own counter agrees with reality —
which is what FR-018 asks of a pressure signal.

**The rejection is deferred, not immediate.** Four long requests were left in flight and one small
extra request was sent 2.5 s later. It did not fail fast: it returned **429 after 6.525 s**, exactly
when the running batch completed. The caller pays the full wait before learning it was refused, so
the 429 is a correctness signal, not a fast backpressure signal. For PRP this means a rejected
attempt still consumes the caller's deadline.

## Step 3 — the controls, and whether PRP can read them back

| control | default | set by | readable back |
|---|---|---|---|
| `request_limits` (per model, concurrent requests) | `None` → infinity, reported as `-1` | a launch parameter on `POST /v1/models` | **only in the metrics exporter** (`xinference:model_request_limit`), **not** in `/v1/models` |
| `XINFERENCE_BATCH_SIZE` | 32 | environment | not exposed |
| `XINFERENCE_BATCH_INTERVAL` | 0.003 s | environment | not exposed |
| `XINFERENCE_MAX_CONCURRENT_LAUNCHES` (worker launch semaphore, the `active: N/5` in the log) | 5 | environment | log only |

`/v1/models` returns 21 fields for the running model and `request_limits` is not among them. The
value is readable only from the exporter — the endpoint that needs no credential. Candidate B was
worse in one respect (`max_num_seqs` was in the startup log only) and better in another (its limit
was not exposed on an unauthenticated port).

## What PRP has to carry

- Set `request_limits` explicitly at launch: the default is unlimited, so without it the runtime
  accepts every concurrent request PRP sends and the capacity signal never fires.
- Read the limit and the in-flight count from the **metrics exporter**, and put that exporter behind
  the host firewall, because it needs no credential and reveals model identity and placement.
- Treat `model_serve_count` as trustworthy for over-count purposes: it did not over-report in 384
  scrapes across both runs.
- Do not rely on the 429 as a fast rejection: it can take as long as the work in flight.

## Limits of this run

- **FR-017 durable admission** is PRP-side and out of scope before M4, as the procedure states.
- **One GPU host (DEV-03)**: the non-loopback probes were made from this host's own addresses, which
  shows a listener refuses them; it does not prove isolation between two machines. Candidate B's
  equivalent second-machine probe was deferred for the same reason.
- **DEV-07**: Windows-native transformers backend, so the batching behaviour is that backend's.
- No bound on any internal queue was probed, and the rate-limit rejection was not driven past the
  429 into the per-key rate limiter measured in EV04.
